"""
LC Meeting 数据导入 Service
1. 校验飞书文档结构（Sheet 存在性 + 数据非空）
2. 并行执行两个 Sheet 的数据读取脚本
3. 计算 vs_bmk 字段
4. 计算 lc_fund_performance_summary 汇总统计
5. 计算 lc_fund_performance_quartile_contribution 四分位分布
"""
import asyncio
import os
import subprocess
from fastapi import HTTPException
from utils.lcMeeting.get_lc_meeting_sheet_ids import get_lc_meeting_sheet_ids
from database import SessionLocal
from models import (
    LcFundPerformance, LcFundPerformanceRating, LcFundPerformanceSummary, 
    LcFundPerformanceQuartile, ReportRecord, ReportConfig
)
from datetime import date, datetime
from utils.report_utils import calculate_delivery_deadline


# ────────────────────────────────────────────────────────────────
# 工具：判断 Excess 值对应的 vs_bmk 标签
# ────────────────────────────────────────────────────────────────
_EXCESS_FIELDS = [
    ("ytd_excess",     "vs_bmk_ytd"),
    ("one_y_excess",   "vs_bmk_1y"),
    ("ann_3y_excess",  "vs_bmk_3y"),
    ("ann_5y_excess",  "vs_bmk_5y"),
    ("ann_10y_excess", "vs_bmk_10y"),
    ("ann_20y_excess", "vs_bmk_20y"),
    ("since_inc_excess", "vs_bmk_si"),
]


def _excess_to_label(val) -> str:
    """将数值 excess 转成 A / B / N/A"""
    if val is None:
        return "N/A"
    f = float(val)
    if f > 0:
        return "A"
    return "B"  # 0 or negative is B


def compute_vs_bmk(report_date: date):
    """
    根据 as_of_date 将 lc_fund_performance.excess 计算结果
    写回 lc_fund_performance_rating.vs_bmk_* 字段。
    """
    db = SessionLocal()
    try:
        # 取 performance 表的数据（以 fund_name 为 key）
        perf_rows = (
            db.query(LcFundPerformance)
            .filter(LcFundPerformance.as_of_date == report_date)
            .all()
        )
        perf_map: dict[str, LcFundPerformance] = {r.fund_name: r for r in perf_rows}

        rating_rows = (
            db.query(LcFundPerformanceRating)
            .filter(LcFundPerformanceRating.as_of_date == report_date)
            .all()
        )

        for rating in rating_rows:
            perf = perf_map.get(rating.fund_name)

            if perf is None:
                # 没有匹配到 performance 数据 → 每个字段都设为 No BMK
                for _, bmk_field in _EXCESS_FIELDS:
                    setattr(rating, bmk_field, "No BMK")
                continue

            # 检查所有 excess 是否全为 None
            all_none = all(
                getattr(perf, exc_field) is None
                for exc_field, _ in _EXCESS_FIELDS
            )

            for exc_field, bmk_field in _EXCESS_FIELDS:
                if all_none:
                    setattr(rating, bmk_field, "No BMK")
                else:
                    setattr(rating, bmk_field,
                            _excess_to_label(getattr(perf, exc_field)))

        db.commit()
        print(f"✅ vs_bmk 字段计算完成，共处理 {len(rating_rows)} 条 rating 记录")
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"vs_bmk 计算失败: {e}")
    finally:
        db.close()


# ────────────────────────────────────────────────────────────────
# Summary 计算
# ────────────────────────────────────────────────────────────────

# period 名称 → (ms_rank_字段, vs_bmk_字段)
_PERIOD_FIELDS = [
    ("YTD",  "ms_rank_ytd",  "vs_bmk_ytd"),
    ("1Y",   "ms_rank_1y",   "vs_bmk_1y"),
    ("3Y",   "ms_rank_3y",   "vs_bmk_3y"),
    ("5Y",   "ms_rank_5y",   "vs_bmk_5y"),
    ("10Y",  "ms_rank_10y",  "vs_bmk_10y"),
    ("20Y",  "ms_rank_20y",  "vs_bmk_20y"),
    ("SI",   "ms_rank_si",   "vs_bmk_si"),
]


def _safe_div(num, den):
    """安全除法，分母为 0 时返回 None"""
    if den is None or den == 0:
        return None
    return num / den


def compute_summary(report_date: date):
    """
    根据 lc_fund_performance_rating 表中已计算好的 ms_rank_* / vs_bmk_* 字段，
    汇总并写入 lc_fund_performance_summary 表。

    summary_type:
      - "Ranked in 1st and 2nd Quartile"  (基于 ms_rank_*)
      - "Outperform Benchmark"             (基于 vs_bmk_*，排除 No BMK / N/A)
    """
    db = SessionLocal()
    try:
        rating_rows = (
            db.query(LcFundPerformanceRating)
            .filter(LcFundPerformanceRating.as_of_date == report_date)
            .all()
        )

        if not rating_rows:
            print("[compute_summary] ⚠️  无 rating 数据，跳过 summary 计算")
            return

        summary_records = []

        for period, ms_field, bmk_field in _PERIOD_FIELDS:

            # ── Ranked in 1st and 2nd Quartile ───────────────────
            ms_values = [getattr(r, ms_field) for r in rating_rows]

            total_ms  = sum(1 for v in ms_values if v is not None)   # 有排名的总数
            top2_ms   = sum(1 for v in ms_values if v in (1, 2))     # 1 or 2

            # AUM：只算有排名数据的行
            total_aum_ms  = sum(
                float(r.aum_usd_mn) for r in rating_rows
                if getattr(r, ms_field) is not None and r.aum_usd_mn is not None
            )
            top2_aum_ms   = sum(
                float(r.aum_usd_mn) for r in rating_rows
                if getattr(r, ms_field) in (1, 2) and r.aum_usd_mn is not None
            )

            summary_records.append({
                "summary_type":    "Ranked in 1st and 2nd Quartile",
                "period":          period,
                "pct_no_of_funds": _safe_div(top2_ms, total_ms),
                "pct_of_aum":      _safe_div(top2_aum_ms, total_aum_ms),
            })

            # ── Outperform Benchmark ──────────────────────────────
            # 排除 No BMK 和 N/A
            valid_bmk_rows = [
                r for r in rating_rows
                if getattr(r, bmk_field) not in (None, "No BMK", "N/A")
            ]
            outperform_rows = [r for r in valid_bmk_rows if getattr(r, bmk_field) == "A"]

            total_bmk    = len(valid_bmk_rows)
            out_count    = len(outperform_rows)

            total_aum_bmk = sum(
                float(r.aum_usd_mn) for r in valid_bmk_rows if r.aum_usd_mn is not None
            )
            out_aum_bmk   = sum(
                float(r.aum_usd_mn) for r in outperform_rows if r.aum_usd_mn is not None
            )

            summary_records.append({
                "summary_type":    "Outperform Benchmark",
                "period":          period,
                "pct_no_of_funds": _safe_div(out_count, total_bmk),
                "pct_of_aum":      _safe_div(out_aum_bmk, total_aum_bmk),
            })

        # ── Upsert into lc_fund_performance_summary ──────────────
        from decimal import Decimal

        upserted = 0
        for rec in summary_records:
            existing = (
                db.query(LcFundPerformanceSummary)
                .filter(
                    LcFundPerformanceSummary.as_of_date  == report_date,
                    LcFundPerformanceSummary.summary_type == rec["summary_type"],
                    LcFundPerformanceSummary.period       == rec["period"],
                )
                .first()
            )
            pct_funds = Decimal(str(rec["pct_no_of_funds"])) if rec["pct_no_of_funds"] is not None else None
            pct_aum   = Decimal(str(rec["pct_of_aum"]))      if rec["pct_of_aum"]      is not None else None

            if existing:
                existing.pct_no_of_funds = pct_funds
                existing.pct_of_aum      = pct_aum
            else:
                db.add(LcFundPerformanceSummary(
                    as_of_date      = report_date,
                    summary_type    = rec["summary_type"],
                    period          = rec["period"],
                    pct_no_of_funds = pct_funds,
                    pct_of_aum      = pct_aum,
                ))
            upserted += 1

        db.commit()
        print(f"✅ lc_fund_performance_summary 写入完成，共 {upserted} 条记录")

    except Exception as e:
        db.rollback()
        raise RuntimeError(f"summary 计算失败: {e}")
    finally:
        db.close()



# ────────────────────────────────────────────────────────────────
# Quartile Contribution 计算
# ────────────────────────────────────────────────────────────────

def compute_quartile(report_date: date):
    """
    根据 lc_fund_performance_rating 表中 ms_rank_* 字段，
    计算每个 period 的四分位 AUM 占比，写入 lc_fund_performance_quartile_contribution。

    q1_pct  = rank==1 的 aum_usd_mn 之和 / 全部有效 aum_usd_mn 之和
    q2_pct  = rank==2 ...
    q3_pct  = rank==3 ...
    q4_pct  = rank==4 ...
    top_half_summary_pct = (rank==1 + rank==2) / total
    """
    db = SessionLocal()
    try:
        rating_rows = (
            db.query(LcFundPerformanceRating)
            .filter(LcFundPerformanceRating.as_of_date == report_date)
            .all()
        )

        if not rating_rows:
            print("[compute_quartile] ⚠️  无 rating 数据，跳过 quartile 计算")
            return

        from decimal import Decimal

        for period, ms_field, _ in _PERIOD_FIELDS:
            # 只取 ms_rank 不为 NULL 的行（才有有效排名）
            valid_rows = [
                r for r in rating_rows
                if getattr(r, ms_field) is not None and r.aum_usd_mn is not None
            ]

            total_aum = sum(float(r.aum_usd_mn) for r in valid_rows)

            def quartile_aum(rank_val):
                return sum(
                    float(r.aum_usd_mn)
                    for r in valid_rows
                    if getattr(r, ms_field) == rank_val
                )

            q1_aum = quartile_aum(1)
            q2_aum = quartile_aum(2)
            q3_aum = quartile_aum(3)
            q4_aum = quartile_aum(4)

            def pct(num):
                return Decimal(str(_safe_div(num, total_aum))) if total_aum else None

            q1 = pct(q1_aum)
            q2 = pct(q2_aum)
            q3 = pct(q3_aum)
            q4 = pct(q4_aum)
            top_half = pct(q1_aum + q2_aum)

            # Upsert
            existing = (
                db.query(LcFundPerformanceQuartile)
                .filter(
                    LcFundPerformanceQuartile.as_of_date == report_date,
                    LcFundPerformanceQuartile.period     == period,
                )
                .first()
            )
            if existing:
                existing.q1_pct              = q1
                existing.q2_pct              = q2
                existing.q3_pct              = q3
                existing.q4_pct              = q4
                existing.top_half_summary_pct = top_half
            else:
                db.add(LcFundPerformanceQuartile(
                    as_of_date           = report_date,
                    period               = period,
                    q1_pct               = q1,
                    q2_pct               = q2,
                    q3_pct               = q3,
                    q4_pct               = q4,
                    top_half_summary_pct  = top_half,
                ))

        db.commit()
        print(f"✅ lc_fund_performance_quartile_contribution 写入完成 (as_of_date={report_date})")

    except Exception as e:
        db.rollback()
        raise RuntimeError(f"quartile 计算失败: {e}")
    finally:
        db.close()


# ────────────────────────────────────────────────────────────────
# 主 Service 函数
# ────────────────────────────────────────────────────────────────
async def generate_lc_meeting(spreadsheet_token: str, report_date_str: str) -> None:
    """
    执行完整的 LC Meeting 数据导入流程：
      1. 校验 Sheet 存在性
      2. 并行读取两个 Sheet 数据并入库
      3. 计算 vs_bmk 字段
      4. 计算 performance summary 汇总
    """

    # ── 1. 获取并校验 Sheet IDs ──────────────────────────────
    try:
        sheet_ids = get_lc_meeting_sheet_ids(spreadsheet_token)
    except ValueError as e:
        # Sheet 缺失 → 用 422 让前端弹提示
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"飞书连接失败: {e}")

    aum_sheet_id  = sheet_ids["Funds Performance & AUM"]
    perf_sheet_id = sheet_ids["Performance"]

    # ── 2. 构建运行环境 ───────────────────────────────────────
    base_dir = os.path.dirname(os.path.dirname(__file__))
    utils_dir = os.path.join(base_dir, "utils", "lcMeeting")

    if os.name == 'nt':
        venv_python = os.path.join(base_dir, "venv", "Scripts", "python.exe")
    else:
        # 兼容 linux 路径
        venv_python = os.path.join(base_dir, "huili_demo_venv", "bin", "python")

    run_env = os.environ.copy()
    run_env["PYTHONIOENCODING"] = "utf-8"
    run_env["PYTHONPATH"] = base_dir

    # ── 3. 定义并行运行子函数 ─────────────────────────────────
    async def run_script(script: str, sheet_id: str) -> str:
        cmd = [venv_python, script, spreadsheet_token, sheet_id]
        print(f"[lc_meeting] Starting: {script} sheet_id={sheet_id}")
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            cwd=utils_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=run_env,
        )
        if result.returncode != 0:
            print(f"[lc_meeting] Error in {script}: {result.stderr}")
            raise RuntimeError(f"Script {script} failed: {result.stderr}")
        print(f"[lc_meeting] Done: {script}")
        return result.stdout

    # ── 4. 并行运行导入脚本 ───────────────────────────────────
    outputs = await asyncio.gather(
        run_script("get_funds_performance_aum.py", aum_sheet_id),
        run_script("get_performance.py", perf_sheet_id)
    )

    # ── 5. 解析 as_of_date ────────────────────────────────────
    import re
    data_as_of_date = None
    for out in outputs:
        match = re.search(r"as_of_date = (\d{4}-\d{2}-\d{2})", out)
        if match:
            data_as_of_date = match.group(1)
            break

    if data_as_of_date:
        # 转为 date 对象供后续函数使用
        from dateutil.parser import parse
        data_date_obj = parse(data_as_of_date).date()

        # ── 6. 计算 vs_bmk 字段 ──────────────────────────────
        try:
            await asyncio.to_thread(compute_vs_bmk, data_date_obj)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

        # ── 7. 计算 performance summary ─────────────────────
        try:
            await asyncio.to_thread(compute_summary, data_date_obj)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

        # ── 8. 计算 quartile contribution ─────────────────
        try:
            await asyncio.to_thread(compute_quartile, data_date_obj)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

        # ── 9. 更新 report_record 状态 ────────────────────
        try:
            await asyncio.to_thread(_update_report_record, report_date_str, data_date_obj)
        except Exception as e:
            print(f"[lc_meeting] ⚠️  更新 report_record 失败: {e}")
    else:
        print("[lc_meeting] ⚠️  未能从脚本输出解析到 as_of_date，尝试从数据库获取最新")
        db = SessionLocal()
        latest = db.query(LcFundPerformanceRating.as_of_date).order_by(LcFundPerformanceRating.as_of_date.desc()).first()
        db.close()
        if latest:
            await asyncio.to_thread(_update_report_record, report_date_str, latest[0])
        else:
            print("[lc_meeting] ⚠️  数据库也无数据，跳过后续更新")


def _update_report_record(report_date_str: str, data_as_of_date: date):
    """
    1. 根据传入的 report_date_str 找到对应的记录
    2. 更新 as_of_date 为飞书脚本读到的 data_as_of_date
    3. 更新 status 为 'Submitted'，更新提交时间
    """
    db = SessionLocal()
    try:
        report_name = "LC meeting"
        # 转换传入的 report_date 为 date 对象
        from dateutil.parser import parse
        intended_date = parse(report_date_str).date()

        record = (
            db.query(ReportRecord)
            .filter(ReportRecord.report_name == report_name)
            .filter(ReportRecord.report_date == intended_date)
            .order_by(ReportRecord.report_date.desc())
            .first()
        )

        if record:
            now = datetime.now()
            record.as_of_date = data_as_of_date
            record.submitted_at = now
            record.status = "Submitted"
            record.updated_at = now
            db.commit()
            print(f"✅ report_record 更新成功: {report_name} (report_date={intended_date}) -> as_of_date={data_as_of_date}")
        else:
            print(f"⚠️  未找到匹配的 report_record (report_name={report_name}, report_date={intended_date})，正在自动创建...")
            # 1. 找到该 Report 的 Config
            config = db.query(ReportConfig).filter(ReportConfig.report_name == report_name).first()
            if not config:
                print(f"❌ 自动创建失败：未找到 {report_name} 的配置")
                return

            # 2. 计算 delivery_deadline
            deadline = calculate_delivery_deadline(config.frequency, config.deliverable_time, intended_date)
            
            # 3. 插入新记录
            now = datetime.now()
            new_record = ReportRecord(
                config_id=config.id,
                report_name=report_name,
                report_date=intended_date,
                delivery_deadline=deadline,
                as_of_date=data_as_of_date,
                submitted_at=now,
                status="Submitted",
                updated_at=now,
                created_at=now
            )
            db.add(new_record)
            db.commit()
            print(f"✅ report_record 创建并提交成功: {report_name} (report_date={intended_date}) -> as_of_date={data_as_of_date}")
    except Exception as e:
        db.rollback()
        print(f"❌ _update_report_record 异常: {e}")
    finally:
        db.close()
