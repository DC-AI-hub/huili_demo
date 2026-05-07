"""
lcReportGeneratorService.py — LC Report 报告生成管线服务

功能：
  generate_report(db, report_id, report_date)
    ├── 前置校验：报告存在且不处于 DELETED/ARCHIVED 状态
    ├── 清理旧数据（幂等）
    ├── Step 2: 填充 lc_fund_performance（每基金各周期收益 + AUM）
    ├── Step 5: 填充 lc_fund_performance_rating（HKSFC 四分位 + A/B 标签）
    ├── Step 6: 填充 lc_fund_performance_summary（KPI 汇总）
    ├── Step 7: 填充 lc_fund_performance_quartile_contribution（四分位 AUM 贡献）
    ├── Step 8: 填充 lc_fund_performance_other_accounts（其他账户）
    └── 更新 lc_report.status → DONE（在同一事务内）

依赖：
  - 视图 v_fund_period_returns / v_fund_quartiles / v_working_sheet
    已在 ddl/LCReport/02_report_generator_views.sql 定义，需先执行
  - lc_fund_code_map 由 Quartile_weekly ETL 上传时自动填充 entity_name/isin，
    benchmark_name 需手工配置（对应 Excel Performance Sheet D列）
  - lc_other_accounts_config 仅需配置 2-3 行（Gold ETF / Real Estate 的 fund_code）

数据源说明：
  收益数据来自 Quartile_weekly（lc_report_qw_performance），
  而非 FundAnalysis（lc_report_fa_performance）。
  这与 Excel 的公式逻辑一致：
    Performance!G4 = VLOOKUP(B4, 'AUM with monthly return'!A:K, 11, 0) / 100

单位说明（⚠ 重要）：
  lc_report_qw_performance.value 的单位取决于 ETL。
  若 ETL 存储为小数（0.0537 = 5.37%），DIVIDE_100 = 1。
  若 ETL 存储为百分比（5.37），DIVIDE_100 = 100。
  默认设为 1（小数），请根据实际数据调整。
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

# 收益率单位换算系数：若 ETL 已存为小数（0.05 = 5%），设为 1；若存为百分比（5.0），设为 100
DIVIDE_100: int = 100


def _get_db():
    """仅供内部单元测试使用"""
    from database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def generate_report(db: Session, report_id: int, report_date: str) -> Dict[str, Any]:
    """
    在单一事务中完成 LC Report 最终报告表的生成。
    report_date: YYYY-MM-DD 格式字符串（如 '2026-04-24'）
    """
    # ─── 前置校验 ────────────────────────────────────────────────────────────
    row = db.execute(
        text("SELECT status FROM lc_report WHERE report_id=:rid"),
        {"rid": report_id},
    ).fetchone()

    if not row:
        raise ValueError(f"report_id={report_id} 不存在")
    if row[0] in ("DELETED", "ARCHIVED"):
        raise PermissionError(f"report_id={report_id} 状态为 {row[0]}，不允许生成报告")

    logger.info(f"[generator] 开始生成报告 report_id={report_id} report_date={report_date}")

    # ─── 清理当日旧数据（幂等重跑）───────────────────────────────────────────
    db.execute(text("DELETE FROM lc_fund_performance WHERE report_date=:d"),                         {"d": report_date})
    db.execute(text("DELETE FROM lc_fund_performance_rating WHERE report_date=:d"),                  {"d": report_date})
    db.execute(text("DELETE FROM lc_fund_performance_summary WHERE report_date=:d"),                 {"d": report_date})
    db.execute(text("DELETE FROM lc_fund_performance_quartile_contribution WHERE report_date=:d"),   {"d": report_date})
    db.execute(text("DELETE FROM lc_fund_performance_other_accounts WHERE report_date=:d"),          {"d": report_date})

    # ─── Step 2: lc_fund_performance ────────────────────────────────────────
    _step2_fund_performance(db, report_id, report_date)

    # ─── Step 5: lc_fund_performance_rating ─────────────────────────────────
    _step5_fund_rating(db, report_date)

    # ─── Step 6: lc_fund_performance_summary ────────────────────────────────
    _step6_fund_summary(db, report_date)

    # ─── Step 7: lc_fund_performance_quartile_contribution ──────────────────
    _step7_quartile_contribution(db, report_date)

    # ─── Step 8: lc_fund_performance_other_accounts ─────────────────────────
    _step8_other_accounts(db, report_id, report_date)

    # ─── 更新报告状态 → DONE ─────────────────────────────────────────────────
    db.execute(
        text("UPDATE lc_report SET status='DONE', updated_at=NOW() WHERE report_id=:rid"),
        {"rid": report_id},
    )

    db.commit()
    logger.info(f"[generator] 报告生成完成 report_id={report_id}")

    return {
        "report_id":   str(report_id),
        "report_date": report_date,
        "status":      "DONE",
        "message":     "报告生成成功",
    }


# ---------------------------------------------------------------------------
# Step 2: lc_fund_performance
#   Excel 对应：Performance 页每行（B:AB 列）
#   驱动：以 lc_report_sales_flow 中当日 fund_code 为基准
#         AUM 来自 sales_flow.est_aum_usd_m
#         各周期收益来自 v_fund_period_returns（Quartile_weekly QW 数据）
#         entity_name 通过 lc_fund_code_map 自动关联
#         基准名称通过 lc_fund_code_map.benchmark_name 配置
#           （对应 Excel Performance Sheet D列，如 "MSCI AC Asia Ex Japan NR USD"）
#         benchmark 收益通过 benchmark_name 在 v_fund_period_returns(metric_kind='bm') 中查找
# ---------------------------------------------------------------------------
_SQL_STEP2 = """
INSERT INTO lc_fund_performance (
    report_date, as_of_date, fund_code, fund_name, benchmark, aum_usd_mn, aum_vp_pct,
    ytd_fund, ytd_bm, ytd_excess,
    `1y_fund`, `1y_bm`, `1y_excess`,
    ann_3y_fund, ann_3y_bm, ann_3y_excess,
    ann_5y_fund, ann_5y_bm, ann_5y_excess,
    ann_10y_fund, ann_10y_bm, ann_10y_excess,
    ann_20y_fund, ann_20y_bm, ann_20y_excess,
    since_inc_fund, since_inc_bm, since_inc_excess,
    inception_date
)
WITH base AS (
    -- 驱动表：当日 SalesReport 中每个基金
    -- entity_name 通过 lc_fund_code_map 自动对应
    -- benchmark_name（显示用）/ bm_entity_name（JOIN 用）通过 lc_fund_code_map 配置
    SELECT
        s.report_date                         AS as_of_date,
        s.fund_code,
        s.fund_name,
        fcm.entity_name,
        fcm.isin                              AS fund_isin,
        fcm.benchmark_name,
        fcm.bm_entity_name,
        s.est_aum_usd_m                       AS aum_usd_mn,
        s.est_aum_usd_m / NULLIF(
            (SELECT est_aum_usd_m FROM lc_report_sales_flow
             WHERE report_id = s.report_id AND fund_code = '__TOTAL__' LIMIT 1), 0
        )                                     AS aum_vp_pct,
        fcm.inception_date                    AS inception_date
    FROM lc_report_sales_flow s
    LEFT JOIN lc_fund_code_map fcm ON fcm.fund_code = s.fund_code
    WHERE s.report_id = :rid AND LEFT(s.fund_code, 2) != '__'
),
fund_ret AS (
    SELECT * FROM v_fund_period_returns
    WHERE metric_kind = 'fund' AND report_id = :rid
),
bm_ret AS (
    SELECT * FROM v_fund_period_returns
    WHERE metric_kind = 'bm' AND report_id = :rid
)
SELECT
    CAST(:d AS DATE) AS report_date, b.as_of_date, b.fund_code, b.fund_name, COALESCE(NULLIF(b.benchmark_name, ''), 'No benchmark'), b.aum_usd_mn, b.aum_vp_pct,
    f.ret_ytd    / :div,  bm.ret_ytd    / :div, (f.ret_ytd    - bm.ret_ytd)    / :div,
    f.ret_1y     / :div,  bm.ret_1y     / :div, (f.ret_1y     - bm.ret_1y)     / :div,
    f.ret_3y_ann / :div,  bm.ret_3y_ann / :div, (f.ret_3y_ann - bm.ret_3y_ann) / :div,
    f.ret_5y_ann / :div,  bm.ret_5y_ann / :div, (f.ret_5y_ann - bm.ret_5y_ann) / :div,
    f.ret_10y_ann/ :div,  bm.ret_10y_ann/ :div, (f.ret_10y_ann- bm.ret_10y_ann)/ :div,
    f.ret_20y_ann/ :div,  bm.ret_20y_ann/ :div, (f.ret_20y_ann- bm.ret_20y_ann)/ :div,
    -- Since Inception: 用 fund_code 精确匹配 inception period (如 "VPHY (inception)")
    (SELECT p.value FROM lc_report_qw_performance p
     JOIN lc_report_qw_entity e ON e.entity_id = p.entity_id
     WHERE p.report_id = :rid AND e.entity_type = 'fund'
       AND e.entity_name = b.entity_name
       AND p.period_type = CONCAT(b.fund_code, ' (inception)')
       AND p.metric = 'return_ann' LIMIT 1) / :div,
    (SELECT p.value FROM lc_report_qw_performance p
     JOIN lc_report_qw_entity e ON e.entity_id = p.entity_id
     WHERE p.report_id = :rid AND e.entity_type = 'benchmark'
       AND e.entity_name = b.bm_entity_name
       AND p.period_type = CONCAT(b.fund_code, ' (inception)')
       AND p.metric = 'return_ann' LIMIT 1) / :div,
    (COALESCE(
        (SELECT p.value FROM lc_report_qw_performance p
         JOIN lc_report_qw_entity e ON e.entity_id = p.entity_id
         WHERE p.report_id = :rid AND e.entity_type = 'fund'
           AND e.entity_name = b.entity_name
           AND p.period_type = CONCAT(b.fund_code, ' (inception)')
           AND p.metric = 'return_ann' LIMIT 1), 0)
     - COALESCE(
        (SELECT p.value FROM lc_report_qw_performance p
         JOIN lc_report_qw_entity e ON e.entity_id = p.entity_id
         WHERE p.report_id = :rid AND e.entity_type = 'benchmark'
           AND e.entity_name = b.bm_entity_name
           AND p.period_type = CONCAT(b.fund_code, ' (inception)')
           AND p.metric = 'return_ann' LIMIT 1), 0)
    ) / :div,
    b.inception_date
FROM base b
-- Fund 收益：按 entity_name 匹配，回退到 ISIN
LEFT JOIN fund_ret f  ON (
    f.entity_name = b.entity_name
    OR (b.fund_isin IS NOT NULL AND b.fund_isin != '' AND f.isin = b.fund_isin)
)
-- Benchmark 收益：优先用 bm_entity_name（QW实际名），回退到 benchmark_name（Performance显示名）
LEFT JOIN bm_ret   bm ON (
    bm.entity_name = b.bm_entity_name
    OR (b.bm_entity_name IS NULL AND bm.entity_name = b.benchmark_name)
)
"""



def _step2_fund_performance(db: Session, report_id: int, report_date: str) -> None:
    result = db.execute(text(_SQL_STEP2), {"rid": report_id, "d": report_date, "div": DIVIDE_100})
    logger.info(f"[generator] Step2 lc_fund_performance: {result.rowcount} fund rows inserted for {report_date}")


# ---------------------------------------------------------------------------
# Step 5: lc_fund_performance_rating
#   Excel 对应：HKSFC!C13:T38（Top block >100mn + Bottom block 15-100mn）
#   读取 v_working_sheet，筛选两个 AUM 桶，写入四分位和 A/B 标签
# ---------------------------------------------------------------------------
_SQL_STEP5 = """
INSERT IGNORE INTO lc_fund_performance_rating (
    report_date, as_of_date, fund_name, aum_category, aum_usd_mn, aum_vp_pct,
    ms_rank_ytd, ms_rank_1y, ms_rank_3y, ms_rank_5y, ms_rank_10y, ms_rank_20y, ms_rank_si,
    vs_bmk_ytd, vs_bmk_1y, vs_bmk_3y, vs_bmk_5y, vs_bmk_10y, vs_bmk_20y, vs_bmk_si
)
SELECT
    CAST(:d AS DATE) AS report_date, as_of_date, fund_name, aum_category, aum_usd_mn, aum_vp_pct,
    q_ytd, q_1y, q_3y, q_5y, q_10y, q_20y, q_si,
    vs_bmk_ytd, vs_bmk_1y, vs_bmk_3y, vs_bmk_5y, vs_bmk_10y, vs_bmk_20y, vs_bmk_si
FROM v_working_sheet
WHERE report_date = :d
  AND aum_category IN ('> USD 100mil', 'USD 15mil - 100mil')
  AND fund_code IN (SELECT fund_code FROM lc_fund_code_map)
"""


def _step5_fund_rating(db: Session, report_date: str) -> None:
    result = db.execute(text(_SQL_STEP5), {"d": report_date})
    logger.info(f"[generator] Step5 lc_fund_performance_rating: {result.rowcount} rows for {report_date}")


# ---------------------------------------------------------------------------
# Step 6: lc_fund_performance_summary
#   Excel 对应：HKSFC!C3:F9 KPI 汇总区
#   两类 summary_type：
#     'Ranked in 1st and 2nd Quartile'（Q1+Q2 vs 所有有评级的基金）
#     'Outperform Benchmark'（A vs A+B）
#   各跨 YTD/1Y/3Y/5Y 四个周期
# ---------------------------------------------------------------------------
_SQL_STEP6 = """
INSERT IGNORE INTO lc_fund_performance_summary
  (report_date, as_of_date, summary_type, period, pct_no_of_funds, pct_of_aum)

SELECT
    CAST(:d AS DATE) AS report_date,
    as_of_date,
    'Ranked in 1st and 2nd Quartile' AS summary_type,
    period,
    SUM(CASE WHEN q IN (1,2) THEN 1 ELSE 0 END) * 1.0
        / NULLIF(SUM(CASE WHEN q IN (1,2,3,4) THEN 1 ELSE 0 END), 0) AS pct_no_of_funds,
    SUM(CASE WHEN q IN (1,2) THEN aum_usd_mn ELSE 0 END)
        / NULLIF(SUM(CASE WHEN q IN (1,2,3,4) THEN aum_usd_mn ELSE 0 END), 0) AS pct_of_aum
FROM (
    SELECT report_date, as_of_date, aum_usd_mn, 'YTD' AS period, q_ytd AS q FROM v_working_sheet UNION ALL
    SELECT report_date, as_of_date, aum_usd_mn, '1Y',             q_1y         FROM v_working_sheet UNION ALL
    SELECT report_date, as_of_date, aum_usd_mn, '3Y',             q_3y         FROM v_working_sheet UNION ALL
    SELECT report_date, as_of_date, aum_usd_mn, '5Y',             q_5y         FROM v_working_sheet
) x
WHERE x.report_date = :d
GROUP BY as_of_date, period

UNION ALL

SELECT
    CAST(:d AS DATE) AS report_date,
    as_of_date,
    'Outperform Benchmark' AS summary_type,
    period,
    SUM(CASE WHEN tag = 'A' THEN 1 ELSE 0 END) * 1.0
        / NULLIF(SUM(CASE WHEN tag IN ('A','B') THEN 1 ELSE 0 END), 0) AS pct_no_of_funds,
    SUM(CASE WHEN tag = 'A' THEN aum_usd_mn ELSE 0 END)
        / NULLIF(SUM(CASE WHEN tag IN ('A','B') THEN aum_usd_mn ELSE 0 END), 0) AS pct_of_aum
FROM (
    SELECT report_date, as_of_date, aum_usd_mn, 'YTD' AS period, vs_bmk_ytd AS tag FROM v_working_sheet UNION ALL
    SELECT report_date, as_of_date, aum_usd_mn, '1Y',             vs_bmk_1y        FROM v_working_sheet UNION ALL
    SELECT report_date, as_of_date, aum_usd_mn, '3Y',             vs_bmk_3y        FROM v_working_sheet UNION ALL
    SELECT report_date, as_of_date, aum_usd_mn, '5Y',             vs_bmk_5y        FROM v_working_sheet
) x
WHERE x.report_date = :d
GROUP BY as_of_date, period
"""


def _step6_fund_summary(db: Session, report_date: str) -> None:
    result = db.execute(text(_SQL_STEP6), {"d": report_date})
    logger.info(f"[generator] Step6 lc_fund_performance_summary: {result.rowcount} rows for {report_date}")


# ---------------------------------------------------------------------------
# Step 7: lc_fund_performance_quartile_contribution
#   Excel 对应：Working Sheet D33:L36
#   每周期（YTD/1Y/3Y/5Y/10Y/20Y）× 四分位（1-4）的 AUM 百分比贡献
# ---------------------------------------------------------------------------
_SQL_STEP7 = """
INSERT IGNORE INTO lc_fund_performance_quartile_contribution
  (report_date, as_of_date, period, q1_pct, q2_pct, q3_pct, q4_pct, top_half_summary_pct)
SELECT
    CAST(:d AS DATE) AS report_date,
    as_of_date,
    period,
    COALESCE(SUM(CASE WHEN q = 1 THEN aum_usd_mn ELSE 0 END)
        / NULLIF(SUM(CASE WHEN q IN (1,2,3,4) THEN aum_usd_mn ELSE 0 END), 0), 0) AS q1_pct,
    COALESCE(SUM(CASE WHEN q = 2 THEN aum_usd_mn ELSE 0 END)
        / NULLIF(SUM(CASE WHEN q IN (1,2,3,4) THEN aum_usd_mn ELSE 0 END), 0), 0) AS q2_pct,
    COALESCE(SUM(CASE WHEN q = 3 THEN aum_usd_mn ELSE 0 END)
        / NULLIF(SUM(CASE WHEN q IN (1,2,3,4) THEN aum_usd_mn ELSE 0 END), 0), 0) AS q3_pct,
    COALESCE(SUM(CASE WHEN q = 4 THEN aum_usd_mn ELSE 0 END)
        / NULLIF(SUM(CASE WHEN q IN (1,2,3,4) THEN aum_usd_mn ELSE 0 END), 0), 0) AS q4_pct,
    COALESCE(SUM(CASE WHEN q IN (1,2) THEN aum_usd_mn ELSE 0 END)
        / NULLIF(SUM(CASE WHEN q IN (1,2,3,4) THEN aum_usd_mn ELSE 0 END), 0), 0) AS top_half_summary_pct
FROM (
    SELECT report_date, as_of_date, aum_usd_mn, 'YTD' AS period, q_ytd  AS q FROM v_working_sheet UNION ALL
    SELECT report_date, as_of_date, aum_usd_mn, '1Y',             q_1y          FROM v_working_sheet UNION ALL
    SELECT report_date, as_of_date, aum_usd_mn, '3Y',             q_3y          FROM v_working_sheet UNION ALL
    SELECT report_date, as_of_date, aum_usd_mn, '5Y',             q_5y          FROM v_working_sheet UNION ALL
    SELECT report_date, as_of_date, aum_usd_mn, '10Y',            q_10y         FROM v_working_sheet UNION ALL
    SELECT report_date, as_of_date, aum_usd_mn, '20Y',            q_20y         FROM v_working_sheet
) x
WHERE x.report_date = :d
GROUP BY as_of_date, period
"""


def _step7_quartile_contribution(db: Session, report_date: str) -> None:
    result = db.execute(text(_SQL_STEP7), {"d": report_date})
    logger.info(f"[generator] Step7 lc_fund_performance_quartile_contribution: {result.rowcount} rows for {report_date}")


# ---------------------------------------------------------------------------
# Step 8: lc_fund_performance_other_accounts
#   Excel 对应：HKSFC!B41:E45 底部 Other Accounts 区域
#   已命名账户：从 lc_other_accounts_config 配置，JOIN sales_flow 取 AUM
#   Others（剩余）：总 VP AUM - Performance 基金 AUM - 已命名账户 AUM
# ---------------------------------------------------------------------------
_SQL_STEP8_NAMED = """
INSERT IGNORE INTO lc_fund_performance_other_accounts (report_date, as_of_date, account_name, aum_usd_mn, remarks)
SELECT
    CAST(:d AS DATE) AS report_date,
    s.report_date AS as_of_date,
    cfg.account_name,
    s.est_aum_usd_m AS aum_usd_mn,
    '' AS remarks
FROM lc_other_accounts_config cfg
JOIN lc_report_sales_flow s ON s.fund_code = cfg.fund_code
WHERE s.report_id = :rid
"""

_SQL_STEP8_OTHERS = """
INSERT IGNORE INTO lc_fund_performance_other_accounts (report_date, as_of_date, account_name, aum_usd_mn, remarks)
SELECT
    CAST(:d AS DATE) AS report_date,
    CAST(:d AS DATE) AS as_of_date,
    'Others' AS account_name,
    COALESCE((SELECT est_aum_usd_m FROM lc_report_sales_flow
              WHERE report_id = :rid AND fund_code = '__TOTAL__' LIMIT 1), 0)
    - COALESCE((SELECT SUM(aum_usd_mn)
                  FROM lc_fund_performance WHERE report_date = :d AND fund_code != ''), 0)
    - COALESCE((SELECT SUM(s.est_aum_usd_m)
                  FROM lc_other_accounts_config c
                  JOIN lc_report_sales_flow s ON s.fund_code = c.fund_code
                 WHERE s.report_id = :rid), 0) AS aum_usd_mn,
    'Residual = total AUM - Performance funds - named other accounts' AS remarks
"""


def _step8_other_accounts(db: Session, report_id: int, report_date: str) -> None:
    result1 = db.execute(text(_SQL_STEP8_NAMED), {"rid": report_id, "d": report_date})
    result2 = db.execute(text(_SQL_STEP8_OTHERS), {"rid": report_id, "d": report_date})
    logger.info(f"[generator] Step8 lc_fund_performance_other_accounts: {result1.rowcount} named, {result2.rowcount} others inserted for {report_date}")
