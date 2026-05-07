from fastapi import APIRouter
from typing import Optional
from database import SessionLocal
from utils.date_resolver import resolve_as_of_date
from models import (
    LcFundPerformance,
    LcFundPerformanceRating,
    LcFundPerformanceSummary,
    LcFundPerformanceOtherAccounts,
    LcFundPerformanceQuartile,
)

router = APIRouter()


def _fmt_pct(v) -> Optional[str]:
    """将小数转换为带符号的百分比字符串，None 返回 None（前端自行显示 '-'）"""
    if v is None:
        return None
    val = float(v) * 100
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.1f}%"


def _to_float(v) -> Optional[float]:
    return float(v) if v is not None else None


def _pct_display(v) -> Optional[str]:
    """将 0.2762 格式化为 27.62%"""
    if v is None:
        return None
    return f"{float(v) * 100:.2f}%"


def _pct_display_int(v) -> Optional[str]:
    """将 0.2790 格式化为 28% (取整)"""
    if v is None:
        return None
    return f"{round(float(v) * 100)}%"


@router.get("/lc-meeting/fund-performance", summary="获取 LC Meeting 基金业绩数据")
def get_lc_fund_performance(as_of_date: Optional[str] = None):
    db = SessionLocal()
    try:
        query = db.query(LcFundPerformance)
        if as_of_date:
            from datetime import date
            if isinstance(as_of_date, str):
                final_date = date.fromisoformat(as_of_date)
            else:
                final_date = as_of_date
            query = query.filter(LcFundPerformance.report_date == final_date)
        else:
            latest = db.query(LcFundPerformance.report_date).order_by(
                LcFundPerformance.report_date.desc()
            ).first()
            if latest:
                query = query.filter(LcFundPerformance.report_date == latest[0])

        # 排除 inception_date 为空的数据 及 VUAD
        query = query.filter(LcFundPerformance.inception_date.isnot(None))
        query = query.filter(LcFundPerformance.fund_code != 'VUAD')

        rows = query.order_by(LcFundPerformance.aum_usd_mn.desc()).limit(19).all()

        result = []
        for r in rows:
            result.append({
                "id":            r.id,
                "as_of_date":    r.as_of_date.isoformat() if r.as_of_date else None,
                "fund_code":     r.fund_code,
                "fund_name":     r.fund_name,
                "benchmark":     r.benchmark,
                "aum_usd_mn":    _to_float(r.aum_usd_mn),
                "aum_vp_pct":    _to_float(r.aum_vp_pct),
                # YTD
                "ytd_fund":      _fmt_pct(r.ytd_fund),
                "ytd_bm":        _fmt_pct(r.ytd_bm),
                "ytd_excess":    _fmt_pct(r.ytd_excess),
                # 1Y
                "1y_fund":       _fmt_pct(r.one_y_fund),
                "1y_bm":         _fmt_pct(r.one_y_bm),
                "1y_excess":     _fmt_pct(r.one_y_excess),
                # Ann 3Y
                "ann_3y_fund":   _fmt_pct(r.ann_3y_fund),
                "ann_3y_bm":     _fmt_pct(r.ann_3y_bm),
                "ann_3y_excess": _fmt_pct(r.ann_3y_excess),
                # Ann 5Y
                "ann_5y_fund":   _fmt_pct(r.ann_5y_fund),
                "ann_5y_bm":     _fmt_pct(r.ann_5y_bm),
                "ann_5y_excess": _fmt_pct(r.ann_5y_excess),
                # Ann 10Y
                "ann_10y_fund":   _fmt_pct(r.ann_10y_fund),
                "ann_10y_bm":     _fmt_pct(r.ann_10y_bm),
                "ann_10y_excess": _fmt_pct(r.ann_10y_excess),
                # Ann 20Y
                "ann_20y_fund":   _fmt_pct(r.ann_20y_fund),
                "ann_20y_bm":     _fmt_pct(r.ann_20y_bm),
                "ann_20y_excess": _fmt_pct(r.ann_20y_excess),
                # Since Inception
                "since_inc_fund":   _fmt_pct(r.since_inc_fund),
                "since_inc_bm":     _fmt_pct(r.since_inc_bm),
                "since_inc_excess": _fmt_pct(r.since_inc_excess),
                "inception_date":   (
                    f"{r.inception_date.day}-{r.inception_date.strftime('%b')}-{r.inception_date.strftime('%y')}"
                    if r.inception_date else None
                ),
            })

        # ── 计算汇总行（不入库，API 层动态计算）──────────────────────
        total_funds_aum = sum(r.get("aum_usd_mn") or 0 for r in result)
        total_funds_vp_pct = sum(r.get("aum_vp_pct") or 0 for r in result)

        # Total VP's AUM: 从 sales_flow 取 __TOTAL__ 行
        from sqlalchemy import text as sa_text
        report_date_val = final_date if as_of_date else (latest[0] if latest else None)
        total_vp_aum = None
        if report_date_val:
            vp_row = db.execute(sa_text("""
                SELECT s.est_aum_usd_m
                FROM lc_report_sales_flow s
                JOIN lc_report r ON r.report_id = s.report_id
                WHERE r.report_date = :d AND s.fund_code = '__TOTAL__'
                LIMIT 1
            """), {"d": report_date_val}).fetchone()
            if vp_row:
                total_vp_aum = float(vp_row[0])

        result.append({
            "id":           None,
            "as_of_date":   result[0]["as_of_date"] if result else None,
            "fund_code":    "",
            "fund_name":    "Total Funds' AUM (USD, million)",
            "benchmark":    None,
            "aum_usd_mn":   round(total_funds_aum, 2),
            "aum_vp_pct":   round(total_funds_vp_pct, 6),
        })

        result.append({
            "id":           None,
            "as_of_date":   result[0]["as_of_date"] if result else None,
            "fund_code":    "",
            "fund_name":    "Total VP's AUM (USD, million)",
            "benchmark":    None,
            "aum_usd_mn":   total_vp_aum,
            "aum_vp_pct":   None,
        })

        return result
    finally:
        db.close()


@router.get("/lc-meeting/aum-report", summary="获取 AUM Report 聚合数据")
def get_aum_report(as_of_date: Optional[str] = None):
    db = SessionLocal()
    try:
        # ── 确定报告日期 ──────────────────────────────────────────
        if not as_of_date:
            latest = db.query(LcFundPerformanceRating.report_date).order_by(
                LcFundPerformanceRating.report_date.desc()
            ).first()
            report_date = latest[0] if latest else None
        else:
            if isinstance(as_of_date, str):
                from datetime import date
                report_date = date.fromisoformat(as_of_date)
            else:
                report_date = as_of_date

        # 子查询：Performance 接口中实际返回的 fund_name 列表
        perf_fund_names = (
            db.query(LcFundPerformance.fund_name)
            .filter(
                LcFundPerformance.report_date == report_date,
                LcFundPerformance.inception_date.isnot(None),
                LcFundPerformance.fund_code != 'VUAD',
            )
            .subquery()
        )

        ratings_raw = (
            db.query(LcFundPerformanceRating)
            .filter(
                LcFundPerformanceRating.report_date == report_date,
                LcFundPerformanceRating.fund_name.in_(perf_fund_names),
            )
            .order_by(LcFundPerformanceRating.aum_usd_mn.desc())
            .all()
        ) if report_date else []

        ratings = []
        for r in ratings_raw:
            ratings.append({
                "id":           r.id,
                "fund_name":    r.fund_name,
                "aum_category": r.aum_category,
                "aum_usd_mn":   round(float(r.aum_usd_mn), 1) if r.aum_usd_mn is not None else None,
                "aum_vp_pct":   _pct_display(r.aum_vp_pct),
                "ms_rank_ytd":  r.ms_rank_ytd,
                "ms_rank_1y":   r.ms_rank_1y,
                "ms_rank_3y":   r.ms_rank_3y,
                "ms_rank_5y":   r.ms_rank_5y,
                "ms_rank_10y":  r.ms_rank_10y,
                "ms_rank_20y":  r.ms_rank_20y,
                "ms_rank_si":   r.ms_rank_si,
                "vs_bmk_ytd":   r.vs_bmk_ytd,
                "vs_bmk_1y":    r.vs_bmk_1y,
                "vs_bmk_3y":    r.vs_bmk_3y,
                "vs_bmk_5y":    r.vs_bmk_5y,
                "vs_bmk_10y":   r.vs_bmk_10y,
                "vs_bmk_20y":   r.vs_bmk_20y,
                "vs_bmk_si":    r.vs_bmk_si,
            })

        # ── Performance Summary ───────────────────────────────────
        summary_raw = (
            db.query(LcFundPerformanceSummary)
            .filter(LcFundPerformanceSummary.report_date == report_date)
            .all()
        ) if report_date else []

        summary = []
        for s in summary_raw:
            summary.append({
                "summary_type":    s.summary_type,
                "period":          s.period,
                "pct_no_of_funds": _pct_display_int(s.pct_no_of_funds),
                "pct_of_aum":      _pct_display_int(s.pct_of_aum),
            })

        # ── Other Accounts ────────────────────────────────────────
        other_raw = (
            db.query(LcFundPerformanceOtherAccounts)
            .filter(LcFundPerformanceOtherAccounts.report_date == report_date)
            .order_by(LcFundPerformanceOtherAccounts.id)
            .all()
        ) if report_date else []

        # 汇总 ratings 中所有已显示基金的 AUM（= D23 + D39）
        ratings_aum_total = sum(
            float(r.aum_usd_mn) for r in ratings_raw if r.aum_usd_mn is not None
        )

        # 取 VP Total AUM（Performance!E25 = __TOTAL__）
        from sqlalchemy import text as sa_text
        vp_total_aum = 0
        if report_date:
            vp_row = db.execute(sa_text("""
                SELECT s.est_aum_usd_m
                FROM lc_report_sales_flow s
                JOIN lc_report r ON r.report_id = s.report_id
                WHERE r.report_date = :d AND s.fund_code = '__TOTAL__'
                LIMIT 1
            """), {"d": report_date}).fetchone()
            if vp_row:
                vp_total_aum = float(vp_row[0])

        # 构建 other_accounts：named 账户保留，Others 动态计算
        other_accounts = []
        named_aum_total = 0.0
        for o in other_raw:
            if o.account_name == 'Others':
                continue  # 跳过预生成的 Others，后面动态计算
            aum = round(float(o.aum_usd_mn), 2) if o.aum_usd_mn is not None else None
            if aum is not None:
                named_aum_total += aum
            other_accounts.append({
                "account_name": o.account_name,
                "aum_usd_mn":   aum,
                "remarks":      o.remarks,
            })

        # Others = VP Total AUM - ratings AUM total - named accounts AUM
        others_aum = round(vp_total_aum - ratings_aum_total - named_aum_total, 2)
        other_accounts.append({
            "account_name": "Others",
            "aum_usd_mn":   others_aum,
            "remarks":      "Comprised of the rest of other accounts",
        })

        # Get actual as_of_date from the data
        actual_as_of_date_str = None
        if ratings_raw:
            actual_as_of_date_str = ratings_raw[0].as_of_date.isoformat() if ratings_raw[0].as_of_date else None
        if not actual_as_of_date_str and report_date:
            actual_as_of_date_str = report_date.isoformat()

        return {
            "as_of_date":     actual_as_of_date_str,
            "ratings":        ratings,
            "summary":        summary,
            "other_accounts": other_accounts,
        }
    finally:
        db.close()


@router.get("/lc-meeting/quartile-report", summary="获取 Quartile Report 数据")
def get_quartile_report(as_of_date: Optional[str] = None):
    db = SessionLocal()
    try:
        if not as_of_date:
            latest = db.query(LcFundPerformanceQuartile.report_date).order_by(
                LcFundPerformanceQuartile.report_date.desc()
            ).first()
            report_date = latest[0] if latest else None
        else:
            if isinstance(as_of_date, str):
                from datetime import date
                report_date = date.fromisoformat(as_of_date)
            else:
                report_date = as_of_date

        rows = (
            db.query(LcFundPerformanceQuartile)
            .filter(LcFundPerformanceQuartile.report_date == report_date)
            .order_by(LcFundPerformanceQuartile.id)
            .all()
        ) if report_date else []

        result = []
        for r in rows:
            result.append({
                "period":               r.period,
                "q1_pct":               _to_float(r.q1_pct),
                "q2_pct":               _to_float(r.q2_pct),
                "q3_pct":               _to_float(r.q3_pct),
                "q4_pct":               _to_float(r.q4_pct),
                "q1_display":           _pct_display(r.q1_pct),
                "q2_display":           _pct_display(r.q2_pct),
                "q3_display":           _pct_display(r.q3_pct),
                "q4_display":           _pct_display(r.q4_pct),
                "top_half_summary_pct": _pct_display_int(r.top_half_summary_pct),
            })

        actual_as_of_date_str = None
        if rows:
            actual_as_of_date_str = rows[0].as_of_date.strftime("%Y-%m-%d") if rows[0].as_of_date else None
        if not actual_as_of_date_str and report_date:
            actual_as_of_date_str = report_date.isoformat()

        return {
            "as_of_date": actual_as_of_date_str,
            "data": result
        }
    finally:
        db.close()
