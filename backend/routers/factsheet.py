from fastapi import APIRouter, BackgroundTasks
from typing import Optional
from database import SessionLocal
from utils.date_resolver import resolve_as_of_date
from models import (
    TopHoldings, GeographicalExposure, SectorExposure, PortfolioCharacteristics,
    FeeStructure, ValuePartnersClassicFundInfo, MonthlyPerformance,
    AnnualPerformance, PeriodPerformance, PeriodPerformanceForCiti,
    ClassicAHistorical, DividendDistribution, ValuePartnersClassicFundNavs
)
from utils.date_utils import get_date_variants
from scheduler_tasks import calc_classic_a_historical_derived_task

router = APIRouter()

@router.get("/top-holdings", summary="获取Top Holdings数据")
def get_top_holdings(as_of_date: Optional[str] = None):
    db = SessionLocal()
    try:
        if as_of_date:
            resolved = resolve_as_of_date(db, "Factsheet", as_of_date)
            as_of_date = resolved if resolved else as_of_date

        if not as_of_date:
            latest = db.query(TopHoldings.as_of_date).order_by(TopHoldings.as_of_date.desc()).first()
            if latest:
                as_of_date = latest[0]

        holdings = []
        if as_of_date:
            holdings = db.query(TopHoldings).filter(TopHoldings.as_of_date.in_(get_date_variants(as_of_date))).order_by(TopHoldings.weight.desc()).all()
            if not holdings:
                latest = db.query(TopHoldings.as_of_date).order_by(TopHoldings.as_of_date.desc()).first()
                if latest:
                    holdings = db.query(TopHoldings).filter(TopHoldings.as_of_date == latest[0]).order_by(TopHoldings.weight.desc()).all()

        return [
            {
                "id": h.id, "as_of_date": h.as_of_date, "company_name": h.company_name,
                "industry": h.industry, "weight": float(h.weight)
            } for h in holdings
        ]
    finally:
        db.close()

@router.get("/geographical-exposure", summary="获取Geographical Exposure数据")
def get_geographical_exposure(as_of_date: Optional[str] = None):
    db = SessionLocal()
    try:
        if as_of_date:
            resolved = resolve_as_of_date(db, "Factsheet", as_of_date)
            as_of_date = resolved if resolved else as_of_date

        if not as_of_date:
            latest = db.query(GeographicalExposure.as_of_date).order_by(GeographicalExposure.as_of_date.desc()).first()
            if latest:
                as_of_date = latest[0]

        exposures = []
        if as_of_date:
            exposures = db.query(GeographicalExposure).filter(GeographicalExposure.as_of_date.in_(get_date_variants(as_of_date))).order_by(GeographicalExposure.weight.desc()).all()
            if not exposures:
                latest = db.query(GeographicalExposure.as_of_date).order_by(GeographicalExposure.as_of_date.desc()).first()
                if latest:
                    exposures = db.query(GeographicalExposure).filter(GeographicalExposure.as_of_date == latest[0]).order_by(GeographicalExposure.weight.desc()).all()

        return [
            {
                "id": h.id, "as_of_date": h.as_of_date, "geography": h.geography, "weight": float(h.weight)
            } for h in exposures
        ]
    finally:
        db.close()

@router.get("/sector-exposure", summary="获取Sector Exposure数据")
def get_sector_exposure(as_of_date: Optional[str] = None):
    db = SessionLocal()
    try:
        if as_of_date:
            resolved = resolve_as_of_date(db, "Factsheet", as_of_date)
            as_of_date = resolved if resolved else as_of_date

        if not as_of_date:
            latest = db.query(SectorExposure.as_of_date).order_by(SectorExposure.as_of_date.desc()).first()
            if latest:
                as_of_date = latest[0]
        exposures = []
        if as_of_date:
            exposures = db.query(SectorExposure).filter(SectorExposure.as_of_date.in_(get_date_variants(as_of_date))).order_by(SectorExposure.weight.desc()).all()
            if not exposures:
                latest = db.query(SectorExposure.as_of_date).order_by(SectorExposure.as_of_date.desc()).first()
                if latest:
                    exposures = db.query(SectorExposure).filter(SectorExposure.as_of_date == latest[0]).order_by(SectorExposure.weight.desc()).all()
        return [
            {
                "id": h.id, "as_of_date": h.as_of_date, "sector": h.sector, "weight": float(h.weight)
            } for h in exposures
        ]
    finally:
        db.close()

@router.get("/portfolio-characteristics", summary="获取Portfolio Characteristics数据")
def get_portfolio_characteristics(as_of_date: Optional[str] = None):
    db = SessionLocal()
    try:
        if as_of_date:
            resolved = resolve_as_of_date(db, "Factsheet", as_of_date)
            as_of_date = resolved if resolved else as_of_date

        if not as_of_date:
            latest = db.query(PortfolioCharacteristics.as_of_date).order_by(PortfolioCharacteristics.as_of_date.desc()).first()
            if latest:
                as_of_date = latest[0]

        char_data = None
        if as_of_date:
            char_data = db.query(PortfolioCharacteristics).filter(PortfolioCharacteristics.as_of_date.in_(get_date_variants(as_of_date))).first()
            if not char_data:
                latest = db.query(PortfolioCharacteristics.as_of_date).order_by(PortfolioCharacteristics.as_of_date.desc()).first()
                if latest:
                    char_data = db.query(PortfolioCharacteristics).filter(PortfolioCharacteristics.as_of_date == latest[0]).first()

        if char_data:
            return {
                "id": char_data.id,
                "as_of_date": char_data.as_of_date,
                "price_earnings_ratio": float(char_data.price_earnings_ratio) if char_data.price_earnings_ratio else None,
                "price_book_ratio": float(char_data.price_book_ratio) if char_data.price_book_ratio else None,
                "portfolio_yield": float(char_data.portfolio_yield) if char_data.portfolio_yield else None,
                "volatility_class_a": float(char_data.volatility_class_a) if char_data.volatility_class_a else None,
                "volatility_class_b": float(char_data.volatility_class_b) if char_data.volatility_class_b else None,
                "volatility_class_c": float(char_data.volatility_class_c) if char_data.volatility_class_c else None,
                "volatility_index": float(char_data.volatility_index) if char_data.volatility_index else None
            }
        return {}
    finally:
        db.close()

@router.get("/fee-structure", summary="获取 Fee Structure 数据")
def get_fee_structure(as_of_date: Optional[str] = None):
    db = SessionLocal()
    try:
        if as_of_date:
            resolved = resolve_as_of_date(db, "Factsheet", as_of_date)
            as_of_date = resolved if resolved else as_of_date

        if not as_of_date:
            latest = db.query(FeeStructure.as_of_date).order_by(FeeStructure.as_of_date.desc()).first()
            if latest:
                as_of_date = latest[0]
        fees = []
        if as_of_date:
            fees = db.query(FeeStructure).filter(FeeStructure.as_of_date.in_(get_date_variants(as_of_date))).all()
            if not fees:
                latest = db.query(FeeStructure.as_of_date).order_by(FeeStructure.as_of_date.desc()).first()
                if latest:
                    fees = db.query(FeeStructure).filter(FeeStructure.as_of_date == latest[0]).all()
        return [
            {
                "fund_class": f.fund_class,
                "min_subscription": f.min_subscription,
                "min_subsequent_subscription": f.min_subsequent_subscription,
                "subscription_fee": f.subscription_fee,
                "management_fee": f.management_fee,
                "performance_fee": f.performance_fee,
                "redemption_fee": f.redemption_fee,
            } for f in fees
        ]
    finally:
        db.close()

@router.get("/classic/info", summary="获取基金固定信息列表")
def get_classic_info(as_of_date: Optional[str] = None):
    db = SessionLocal()
    try:
        if as_of_date:
            resolved = resolve_as_of_date(db, "Factsheet", as_of_date)
            as_of_date = resolved if resolved else as_of_date

        query = db.query(ValuePartnersClassicFundInfo)
        if as_of_date:
            query = query.filter(ValuePartnersClassicFundInfo.as_of_date.in_(get_date_variants(as_of_date)))
        rows = query.order_by(ValuePartnersClassicFundInfo.as_of_date.desc()).all()
        return [
            {
                "id": r.id, "as_of_date": r.as_of_date, "fund_size": r.fund_size,
                "nav_a_unit": r.nav_a_unit, "nav_b_unit": r.nav_b_unit,
                "nav_c_unit": r.nav_c_unit, "nav_c_unit_hkd": r.nav_c_unit_hkd,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            } for r in rows
        ]
    finally:
        db.close()

@router.get("/classic/monthly", summary="获取月度业绩数据")
def get_classic_monthly(year: Optional[int] = None):
    db = SessionLocal()
    try:
        query = db.query(MonthlyPerformance)
        if year:
            query = query.filter(MonthlyPerformance.year == year)
        rows = query.order_by(MonthlyPerformance.year).all()

        def fmt_m(v):
            if v is None: return ""
            val = float(v) * 100
            sign = "+" if val > 0 else ""
            return f"{sign}{val:.1f}%"

        return [
            {
                "id": r.id, "year": r.year,
                "jan": fmt_m(r.jan), "feb": fmt_m(r.feb), "mar": fmt_m(r.mar), "apr": fmt_m(r.apr),
                "may": fmt_m(r.may), "jun": fmt_m(r.jun), "jul": fmt_m(r.jul), "aug": fmt_m(r.aug),
                "sep": fmt_m(r.sep), "oct": fmt_m(r.oct), "nov": fmt_m(r.nov), "dec": fmt_m(r.dec),
                "annual": fmt_m(r.annual),
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            } for r in rows
        ]
    finally:
        db.close()

@router.get("/classic/annual", summary="获取年度业绩数据")
def get_annual_performance(year: Optional[int] = None):
    db = SessionLocal()
    try:
        query = db.query(AnnualPerformance)
        if year:
            query = query.filter(AnnualPerformance.year == year)
        rows = query.order_by(AnnualPerformance.year).all()

        def to_float(v): return float(v) if v is not None else None

        return [
            {
                "id": r.id, "year": r.year, "a_unit": to_float(r.a_unit),
                "c_unit_hkd": to_float(r.c_unit_hkd), "hang_seng_index": to_float(r.hang_seng_index),
                "hang_seng_total_return_index": to_float(r.hang_seng_total_return_index),
                "HSI_MSCI_Golden_Dragon_B_unit": to_float(r.HSI_MSCI_Golden_Dragon_B_unit),
                "b_unit": to_float(r.b_unit), "c_unit": to_float(r.c_unit),
                "subscription_fee": to_float(r.subscription_fee),
                "created_at": r.created_at.isoformat(),
            } for r in rows
        ]
    finally:
        db.close()

@router.get("/period-performance", summary="获取各时段业绩数据")
def get_period_performance(as_of_date: Optional[str] = None, period: Optional[str] = None):
    db = SessionLocal()
    try:
        if as_of_date:
            resolved = resolve_as_of_date(db, "Factsheet", as_of_date)
            as_of_date = resolved if resolved else as_of_date

        if not as_of_date:
            latest = db.query(PeriodPerformance.as_of_date).order_by(PeriodPerformance.as_of_date.desc()).first()
            if not latest: return []
            as_of_date = latest[0]

        query = db.query(PeriodPerformance).filter(PeriodPerformance.as_of_date.in_(get_date_variants(as_of_date)))
        if period:
            query = query.filter(PeriodPerformance.period == period)
        rows = query.order_by(PeriodPerformance.id).all()

        def fmt_pct(v):
            if v is None: return "-"
            val = float(v) * 100
            sign = "+" if val >= 0 else ""
            return f"{sign}{val:,.1f}%"

        period_map = {
            "YTD": "Year-to-date", "1m": "One month", "1y": "One year", "3y": "Three years",
            "5y": "Five years", "Inception": "Total return since launch",
            "Inception (Annualized)": "Annualized return since launch^",
        }

        return [
            {
                "id": r.id, "as_of_date": r.as_of_date, "period": period_map.get(r.period, r.period),
                "a_unit": fmt_pct(r.a_unit), "a_unit_hang_seng_index": fmt_pct(r.a_unit_hang_seng_index),
                "a_unit_hsi_msci_golden_dragon": fmt_pct(r.a_unit_hsi_msci_golden_dragon),
                "b_unit": fmt_pct(r.b_unit), "b_unit_hang_seng_index": fmt_pct(r.b_unit_hang_seng_index),
                "b_unit_hsi_msci_golden_dragon": fmt_pct(r.b_unit_hsi_msci_golden_dragon),
                "c_unit": fmt_pct(r.c_unit), "c_unit_hang_seng_index": fmt_pct(r.c_unit_hang_seng_index),
                "c_unit_hsi_msci_golden_dragon": fmt_pct(r.c_unit_hsi_msci_golden_dragon),
                "z_unit": fmt_pct(r.z_unit), "z_unit_hsi_msci_golden_dragon": fmt_pct(r.z_unit_hsi_msci_golden_dragon),
            } for r in rows
        ]
    finally:
        db.close()

@router.get("/period-performance/citi", summary="获取 For Citi 各时段业绩数据")
def get_period_performance_citi(as_of_date: Optional[str] = None, period: Optional[str] = None):
    db = SessionLocal()
    try:
        if as_of_date:
            resolved = resolve_as_of_date(db, "Factsheet", as_of_date)
            as_of_date = resolved if resolved else as_of_date

        query = db.query(PeriodPerformanceForCiti)
        if as_of_date:
            query = query.filter(PeriodPerformanceForCiti.as_of_date.in_(get_date_variants(as_of_date)))
        if period:
            query = query.filter(PeriodPerformanceForCiti.period == period)
        rows = query.order_by(PeriodPerformanceForCiti.as_of_date.desc(), PeriodPerformanceForCiti.period).all()
        def to_float(v): return float(v) if v is not None else None

        return [
            {
                "id": r.id, "as_of_date": r.as_of_date, "period": r.period,
                "hang_seng_index": to_float(r.hang_seng_index), "hsi_msci_golden_dragon": to_float(r.hsi_msci_golden_dragon),
                "a_unit": to_float(r.a_unit), "a_unit_fel_adjusted": to_float(r.a_unit_fel_adjusted),
                "b_unit": to_float(r.b_unit), "b_unit_fel_adjusted": to_float(r.b_unit_fel_adjusted),
                "c_unit": to_float(r.c_unit), "c_unit_fel_adjusted": to_float(r.c_unit_fel_adjusted),
                "z_unit": to_float(r.z_unit),
            } for r in rows
        ]
    finally:
        db.close()

@router.post("/classic/historical/calc-cumulative", summary="在此手动触发计算累计收益率与波动率")
def trigger_calc_cumulative(background_tasks: BackgroundTasks):
    background_tasks.add_task(calc_classic_a_historical_derived_task)
    return {"message": "计算任务已放在后台执行"}


@router.get("/classic/historical", summary="获取 Classic A 历史月度数据")
def get_classic_a_historical(start_date: Optional[str] = None, end_date: Optional[str] = None):
    db = SessionLocal()
    try:
        query = db.query(ClassicAHistorical).order_by(ClassicAHistorical.date)
        if start_date:
            query = query.filter(ClassicAHistorical.date >= start_date)
        if end_date:
            query = query.filter(ClassicAHistorical.date <= end_date)
        rows = query.all()

        def to_float(v): return float(v) if v is not None else None

        results = []
        for r in rows:
            valid_date_str = None
            if hasattr(r.date, "isoformat"):
                valid_date_str = r.date.isoformat()
            elif isinstance(r.date, str):
                try:
                    from datetime import datetime
                    datetime.strptime(r.date, "%Y-%m-%d")
                    valid_date_str = r.date
                except ValueError:
                    pass
            
            if not valid_date_str: continue

            def fmt_c(v):
                if v is None: return ""
                val = float(v) * 100
                s = "+" if val >= 0 else ""
                return f"{s}{val:,.1f}%"

            results.append({
                "id": r.id, "date": valid_date_str, "aum": to_float(r.aum),
                "classic_a_return": to_float(r.classic_a_return),
                "hang_seng_index_return": to_float(r.hang_seng_index_return),
                "hsi_msci_golden_dragon_return": to_float(r.hsi_msci_golden_dragon_return),
                "classic_a_cumulative": to_float(r.classic_a_cumulative), "classic_a_cumulative_fmt": fmt_c(r.classic_a_cumulative),
                "hang_seng_index_cumulative": to_float(r.hang_seng_index_cumulative), "hang_seng_index_cumulative_fmt": fmt_c(r.hang_seng_index_cumulative),
                "hsi_msci_golden_dragon_cumulative": to_float(r.hsi_msci_golden_dragon_cumulative),
                "classic_a_ann_volatility": to_float(r.classic_a_ann_volatility),
                "hang_seng_index_ann_volatility": to_float(r.hang_seng_index_ann_volatility),
                "hsi_msci_golden_dragon_ann_volatility": to_float(r.hsi_msci_golden_dragon_ann_volatility),
            })
        return results
    finally:
        db.close()

@router.get("/dividend", summary="获取股息分派记录")
def get_dividend_distribution(
    as_of_date: Optional[str] = None, isin_code: Optional[str] = None,
    fund_class: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None
):
    db = SessionLocal()
    try:
        if as_of_date:
            resolved = resolve_as_of_date(db, "Factsheet", as_of_date)
            as_of_date = resolved if resolved else as_of_date

        latest_query = db.query(DividendDistribution.ex_date)
        if as_of_date:
            target_date_str = as_of_date
            try:
                from datetime import datetime
                if '-' not in as_of_date:
                    target_date_str = datetime.strptime(as_of_date, '%d %b %Y').strftime('%Y-%m-%d')
                else:
                    target_date_str = datetime.strptime(as_of_date, '%Y-%m-%d').strftime('%Y-%m-%d')
            except: pass
            latest_query = latest_query.filter(DividendDistribution.ex_date <= target_date_str)
            
        latest = latest_query.order_by(DividendDistribution.ex_date.desc()).first()
        if not latest: return []
            
        target_ex_date = latest[0]
        query = db.query(DividendDistribution).filter(DividendDistribution.ex_date == target_ex_date).order_by(DividendDistribution.ex_date.desc())
        if isin_code: query = query.filter(DividendDistribution.isin_code == isin_code)
        if fund_class: query = query.filter(DividendDistribution.fund_class == fund_class)
        if start_date: query = query.filter(DividendDistribution.ex_date >= start_date)
        if end_date: query = query.filter(DividendDistribution.ex_date <= end_date)
        rows = query.all()

        CLASS_NAME_MAP = {
            "CMDisUSD": "Class C USD MDis", "CMDisHKD": "Class C HKD MDis",
            "CMDisRMB": "Class C RMB MDis", "CMDisHRMB": "Class C RMB Hedged MDis",
            "DMDisUSD": "Class D USD MDis", "DMDisHKD": "Class D HKD MDis",
            "DMDisRMB": "Class D RMB MDis", "DMDisHRMB": "Class D RMB Hedged MDis",
        }
        
        def fmt_class(c): return CLASS_NAME_MAP.get(c, c) if c else c
        def fmt_yield(v): return f"{float(v)*100:.1f}%" if v is not None else "-"
        def fmt_date(d):
            if not d: return "-"
            try:
                from datetime import datetime
                date_obj = d if hasattr(d, "day") else datetime.strptime(str(d).strip(), "%Y-%m-%d")
                return f"{int(date_obj.day)}-{int(date_obj.month)}-{date_obj.year}"
            except: return str(d)
        def to_float(v): return float(v) if v is not None else None

        return [
            {
                "id": r.id, "ex_date": fmt_date(r.ex_date), "payment_date": r.payment_date.isoformat() if r.payment_date else None,
                "isin_code": r.isin_code, "fund_code": r.fund_code, "fund_name": r.fund_name,
                "fund_class": fmt_class(r.fund_class), "fund_class_raw": r.fund_class,
                "currency": r.currency, "ex_date_nav": to_float(r.ex_date_nav),
                "dividend_per_unit": to_float(r.dividend_per_unit), "distribution_per_year": r.distribution_per_year,
                "annualized_yield": fmt_yield(r.annualized_yield), "created_at": r.created_at.isoformat(),
            } for r in rows
        ]
    finally:
        db.close()


@router.get("/navs", summary="获取最新一期各类 NAV")
def get_navs(as_of_date: Optional[str] = None):
    db = SessionLocal()
    try:
        if as_of_date:
            resolved = resolve_as_of_date(db, "Factsheet", as_of_date)
            as_of_date = resolved if resolved else as_of_date

        if not as_of_date:
            latest = db.query(ValuePartnersClassicFundNavs.as_of_date).order_by(ValuePartnersClassicFundNavs.as_of_date.desc()).first()
            if not latest: return []
            as_of_date = latest[0]

        rows = db.query(ValuePartnersClassicFundNavs).filter(ValuePartnersClassicFundNavs.as_of_date.in_(get_date_variants(as_of_date))).order_by(ValuePartnersClassicFundNavs.id).all()
        cls_map = {
            "A Unit": "Class A USD", "B Unit": "Class B USD",
            "C Unit": "Class C USD", "C Unit (HKD)": "Class C HKD³"
        }
        
        import re
        def clean_nav(val):
            if not val: return val
            m = re.search(r'[\d.]+', str(val))
            return m.group() if m else str(val)

        return [
            {
                "id": r.id, "as_of_date": r.as_of_date, "class": cls_map.get(r.fund_class, r.fund_class), "nav": clean_nav(r.nav),
            } for r in rows
        ]
    finally:
        db.close()

