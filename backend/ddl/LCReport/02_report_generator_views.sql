-- =============================================================
-- LC Report 生成管线 — 辅助表 & 视图定义
-- 执行顺序：本文件先于 Python ETL 执行（deploy-once）
-- =============================================================

-- =============================================================
-- 删除视图和辅助表（先删视图，再删表）
-- =============================================================
DROP VIEW IF EXISTS v_working_sheet;
DROP VIEW IF EXISTS v_fund_quartiles;
DROP VIEW IF EXISTS v_fund_period_returns;


-- =============================================================
-- Views（CREATE OR REPLACE，可重复执行）
-- =============================================================

-- -------------------------------------------------------------
-- View 1: v_fund_period_returns
--   映射：lc_report_qw_performance × lc_report_qw_entity
--   Excel 对应：'AUM with monthly return' 的 Fund / BM 行
--   每行 = 一个 (as_of_date, report_id, entity_name, isin) × 宽列各周期收益
--   metric_kind: 'fund' = ISIN 非空行，'bm' = ISIN 为空的 Benchmark 行
--
--   ⚠ 重要修改：从 lc_report_qw_performance（Quartile_weekly）读取，
--     而非 lc_report_fa_performance（FundAnalysis），与 Excel 逻辑一致
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW v_fund_period_returns AS
SELECT
    r.report_date                          AS as_of_date,
    p.report_id,
    e.entity_name,
    e.isin,
    e.entity_type,
    CASE e.entity_type
        WHEN 'fund' THEN 'fund' COLLATE utf8mb4_general_ci
        WHEN 'benchmark' THEN 'bm' COLLATE utf8mb4_general_ci
        ELSE e.entity_type COLLATE utf8mb4_general_ci
    END AS metric_kind,
    MAX(CASE WHEN p.period_type IN ('YTD')
             AND p.metric IN ('return_cumulative','return_cum')     THEN p.value END) AS ret_ytd,
    MAX(CASE WHEN p.period_type IN ('1y','1Y')
             AND p.metric IN ('return_cumulative','return_cum')     THEN p.value END) AS ret_1y,
    MAX(CASE WHEN p.period_type IN ('3y','3Y')
             AND p.metric IN ('return_ann')                         THEN p.value END) AS ret_3y_ann,
    MAX(CASE WHEN p.period_type IN ('5y','5Y')
             AND p.metric IN ('return_ann')                         THEN p.value END) AS ret_5y_ann,
    MAX(CASE WHEN p.period_type IN ('10y','10Y')
             AND p.metric IN ('return_ann')                         THEN p.value END) AS ret_10y_ann,
    MAX(CASE WHEN p.period_type IN ('20y','20Y')
             AND p.metric IN ('return_ann')                         THEN p.value END) AS ret_20y_ann,
    MAX(CASE WHEN (p.period_type IN ('Since Inception','SI','since_inception') OR p.period_type LIKE '%(inception)%')
             AND p.metric = 'return_ann'                                    THEN p.value END) AS ret_since_inc
FROM lc_report_qw_performance p
JOIN lc_report_qw_entity e ON e.entity_id = p.entity_id
JOIN lc_report r ON r.report_id = p.report_id
WHERE e.entity_type IN ('fund', 'benchmark')
GROUP BY r.report_date, p.report_id, e.entity_name, e.isin, e.entity_type;


-- -------------------------------------------------------------
-- View 2: v_fund_quartiles
--   映射：lc_report_qw_performance × lc_report_qw_entity
--   Excel 对应：Summary HKSFC / Offshore / UCITS 的四分位列
--   每行 = 一个 (as_of_date, entity_name, isin) × 宽列各周期四分位
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW v_fund_quartiles AS
SELECT
    r.report_date                          AS as_of_date,
    e.entity_name,
    e.isin,
    e.benchmark,
    e.morningstar_rating,
    MAX(CASE WHEN p.period_type IN ('YTD')                                        THEN p.peer_group_quartile END) AS q_ytd,
    MAX(CASE WHEN p.period_type IN ('1y','1Y')                                    THEN p.peer_group_quartile END) AS q_1y,
    MAX(CASE WHEN p.period_type IN ('3y','3Y')                                    THEN p.peer_group_quartile END) AS q_3y,
    MAX(CASE WHEN p.period_type IN ('5y','5Y')                                    THEN p.peer_group_quartile END) AS q_5y,
    MAX(CASE WHEN p.period_type IN ('10y','10Y')                                  THEN p.peer_group_quartile END) AS q_10y,
    MAX(CASE WHEN p.period_type IN ('20y','20Y')                                  THEN p.peer_group_quartile END) AS q_20y,
    MAX(CASE WHEN p.period_type IN ('Since Inception','SI','since_inception')     THEN p.peer_group_quartile END) AS q_si
FROM lc_report_qw_performance p
JOIN lc_report_qw_entity e ON e.entity_id = p.entity_id
JOIN lc_report            r ON r.report_id = p.report_id
GROUP BY r.report_date, e.entity_name, e.isin, e.benchmark, e.morningstar_rating;


-- -------------------------------------------------------------
-- View 3: v_working_sheet
--   映射：lc_fund_performance JOIN v_fund_quartiles
--   Excel 对应：'Working Sheet' 主汇总页（D:L 四分位 + N:T A/B 标签）
--   每行 = 一个 (as_of_date, fund_code)，包含 AUM / AUM桶 / 四分位 / vs_bmk 标签
-- -------------------------------------------------------------
-- v_working_sheet: 每行 = 一个 (as_of_date, fund_code) 的 AUM / 四分位 / vs_bmk 宽表
-- 修复：通过 lc_fund_code_map 将 fund_code → entity_name（Morningstar长名）
--       再与预去重的 v_fund_quartiles 按 entity_name 关联，避免 OR 条件产生笛卡尔积
CREATE OR REPLACE VIEW v_working_sheet AS
SELECT
    perf.report_date,
    perf.as_of_date,
    perf.fund_code,
    perf.fund_name,
    perf.benchmark,
    perf.aum_usd_mn,
    perf.aum_vp_pct,
    CASE
        WHEN perf.aum_usd_mn > 100                            THEN '> USD 100mil' COLLATE utf8mb4_general_ci
        WHEN perf.aum_usd_mn > 15 AND perf.aum_usd_mn <= 100 THEN 'USD 15mil - 100mil' COLLATE utf8mb4_general_ci
        ELSE '<= USD 15mil' COLLATE utf8mb4_general_ci
    END AS aum_category,
    qr.q_ytd, qr.q_1y, qr.q_3y, qr.q_5y, qr.q_10y, qr.q_20y, qr.q_si,
    CASE WHEN perf.ytd_fund       IS NULL THEN 'N/A' COLLATE utf8mb4_general_ci
         WHEN perf.ytd_bm         IS NULL THEN 'No BMK' COLLATE utf8mb4_general_ci
         WHEN perf.ytd_excess      > 0    THEN 'A' COLLATE utf8mb4_general_ci ELSE 'B' COLLATE utf8mb4_general_ci END AS vs_bmk_ytd,
    CASE WHEN perf.`1y_fund`      IS NULL THEN 'N/A' COLLATE utf8mb4_general_ci
         WHEN perf.`1y_bm`        IS NULL THEN 'No BMK' COLLATE utf8mb4_general_ci
         WHEN perf.`1y_excess`    > 0     THEN 'A' COLLATE utf8mb4_general_ci ELSE 'B' COLLATE utf8mb4_general_ci END AS vs_bmk_1y,
    CASE WHEN perf.ann_3y_fund    IS NULL THEN 'N/A' COLLATE utf8mb4_general_ci
         WHEN perf.ann_3y_bm      IS NULL THEN 'No BMK' COLLATE utf8mb4_general_ci
         WHEN perf.ann_3y_excess  > 0     THEN 'A' COLLATE utf8mb4_general_ci ELSE 'B' COLLATE utf8mb4_general_ci END AS vs_bmk_3y,
    CASE WHEN perf.ann_5y_fund    IS NULL THEN 'N/A' COLLATE utf8mb4_general_ci
         WHEN perf.ann_5y_bm      IS NULL THEN 'No BMK' COLLATE utf8mb4_general_ci
         WHEN perf.ann_5y_excess  > 0     THEN 'A' COLLATE utf8mb4_general_ci ELSE 'B' COLLATE utf8mb4_general_ci END AS vs_bmk_5y,
    CASE WHEN perf.ann_10y_fund   IS NULL THEN 'N/A' COLLATE utf8mb4_general_ci
         WHEN perf.ann_10y_bm     IS NULL THEN 'No BMK' COLLATE utf8mb4_general_ci
         WHEN perf.ann_10y_excess > 0     THEN 'A' COLLATE utf8mb4_general_ci ELSE 'B' COLLATE utf8mb4_general_ci END AS vs_bmk_10y,
    CASE WHEN perf.ann_20y_fund   IS NULL THEN 'N/A' COLLATE utf8mb4_general_ci
         WHEN perf.ann_20y_bm     IS NULL THEN 'No BMK' COLLATE utf8mb4_general_ci
         WHEN perf.ann_20y_excess > 0     THEN 'A' COLLATE utf8mb4_general_ci ELSE 'B' COLLATE utf8mb4_general_ci END AS vs_bmk_20y,
    CASE WHEN perf.since_inc_fund   IS NULL THEN 'N/A' COLLATE utf8mb4_general_ci
         WHEN perf.since_inc_bm     IS NULL THEN 'No BMK' COLLATE utf8mb4_general_ci
         WHEN perf.since_inc_excess > 0     THEN 'A' COLLATE utf8mb4_general_ci ELSE 'B' COLLATE utf8mb4_general_ci END AS vs_bmk_si
FROM lc_fund_performance perf
-- Step 1: 通过 fund_code 查出 Morningstar entity_name
LEFT JOIN lc_fund_code_map fcm ON fcm.fund_code = perf.fund_code COLLATE utf8mb4_general_ci
-- Step 2: 用 entity_name 与按 (as_of_date, entity_name) 预去重的四分位数据关联
--         MAX() 聚合保证每个 entity 只返回一行（避免同一基金多 ISIN 产生重复）
LEFT JOIN (
    SELECT
        as_of_date,
        entity_name,
        MAX(q_ytd)  AS q_ytd,  MAX(q_1y)  AS q_1y,
        MAX(q_3y)   AS q_3y,   MAX(q_5y)  AS q_5y,
        MAX(q_10y)  AS q_10y,  MAX(q_20y) AS q_20y,
        MAX(q_si)   AS q_si
    FROM v_fund_quartiles
    GROUP BY as_of_date, entity_name
) qr ON qr.as_of_date  = perf.report_date
     AND qr.entity_name = COALESCE(fcm.entity_name, perf.fund_name) COLLATE utf8mb4_general_ci;
