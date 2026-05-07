from sqlalchemy import Column, Integer, SmallInteger, String, Date, DateTime, Numeric, CHAR, TEXT
from datetime import datetime
from database import Base

class ValuePartnersClassicFundInfo(Base):
    __tablename__ = "value_partners_classic_fund_info"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    as_of_date      = Column(String(50))
    fund_size       = Column(String(100))
    nav_a_unit      = Column(String(50))
    nav_b_unit      = Column(String(50))
    nav_c_unit      = Column(String(50))
    nav_c_unit_hkd  = Column(String(50))
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MonthlyPerformance(Base):
    __tablename__ = "monthly_performance"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    year        = Column(SmallInteger, nullable=False, index=True)
    jan         = Column(Numeric(20, 15), nullable=True)
    feb         = Column(Numeric(20, 15), nullable=True)
    mar         = Column(Numeric(20, 15), nullable=True)
    apr         = Column(Numeric(20, 15), nullable=True)
    may         = Column(Numeric(20, 15), nullable=True)
    jun         = Column(Numeric(20, 15), nullable=True)
    jul         = Column(Numeric(20, 15), nullable=True)
    aug         = Column(Numeric(20, 15), nullable=True)
    sep         = Column(Numeric(20, 15), nullable=True)
    oct         = Column(Numeric(20, 15), nullable=True)
    nov         = Column(Numeric(20, 15), nullable=True)
    dec         = Column(Numeric(20, 15), nullable=True)
    annual      = Column(Numeric(20, 15), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AnnualPerformance(Base):
    __tablename__ = "annual_performance"
    id                              = Column(Integer, primary_key=True, autoincrement=True)
    year                            = Column(SmallInteger, nullable=False, index=True)
    a_unit                          = Column(Numeric(20, 15))
    c_unit_hkd                      = Column(Numeric(20, 15))
    hang_seng_index                 = Column(Numeric(20, 15))
    hang_seng_total_return_index    = Column(Numeric(20, 15))
    HSI_MSCI_Golden_Dragon_B_unit   = Column(Numeric(20, 15))
    b_unit                          = Column(Numeric(20, 15))
    c_unit                          = Column(Numeric(20, 15))
    subscription_fee                = Column(Numeric(20, 15))
    created_at                      = Column(DateTime, default=datetime.utcnow)
    updated_at                      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PeriodPerformance(Base):
    __tablename__ = "period_performance"
    id                              = Column(Integer, primary_key=True, autoincrement=True)
    as_of_date                      = Column(String(50), nullable=False)
    period                          = Column(String(50), nullable=False)
    a_unit                          = Column(Numeric(20, 15))
    a_unit_hang_seng_index          = Column(Numeric(20, 15))
    a_unit_hsi_msci_golden_dragon   = Column(Numeric(20, 15))
    b_unit                          = Column(Numeric(20, 15))
    b_unit_hang_seng_index          = Column(Numeric(20, 15))
    b_unit_hsi_msci_golden_dragon   = Column(Numeric(20, 15))
    c_unit                          = Column(Numeric(20, 15))
    c_unit_hang_seng_index          = Column(Numeric(20, 15))
    c_unit_hsi_msci_golden_dragon   = Column(Numeric(20, 15))
    z_unit                          = Column(Numeric(20, 15))
    z_unit_hsi_msci_golden_dragon   = Column(Numeric(20, 15))
    created_at                      = Column(DateTime, default=datetime.utcnow)
    updated_at                      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PeriodPerformanceForCiti(Base):
    __tablename__ = "period_performance_for_citi"
    id                      = Column(Integer, primary_key=True, autoincrement=True)
    as_of_date              = Column(String(50), nullable=False)
    period                  = Column(String(50), nullable=False)
    hang_seng_index         = Column(Numeric(20, 15))
    hsi_msci_golden_dragon  = Column(Numeric(20, 15))
    a_unit                  = Column(Numeric(20, 15))
    a_unit_fel_adjusted     = Column(Numeric(20, 15))
    b_unit                  = Column(Numeric(20, 15))
    b_unit_fel_adjusted     = Column(Numeric(20, 15))
    c_unit                  = Column(Numeric(20, 15))
    c_unit_fel_adjusted     = Column(Numeric(20, 15))
    z_unit                  = Column(Numeric(20, 15))
    created_at              = Column(DateTime, default=datetime.utcnow)
    updated_at              = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ClassicAHistorical(Base):
    __tablename__ = "classic_a_historical"
    id                                      = Column(Integer, primary_key=True, autoincrement=True)
    date                                    = Column(Date, nullable=False, unique=True, index=True)
    aum                                     = Column(Numeric(24, 2))
    classic_a_return                        = Column(Numeric(20, 15))
    hang_seng_index_return                  = Column(Numeric(20, 15))
    hsi_msci_golden_dragon_return           = Column(Numeric(20, 15))
    classic_a_cumulative                    = Column(Numeric(24, 10))
    hang_seng_index_cumulative              = Column(Numeric(24, 10))
    hsi_msci_golden_dragon_cumulative       = Column(Numeric(24, 10))
    classic_a_ann_volatility                = Column(Numeric(20, 15))
    hang_seng_index_ann_volatility          = Column(Numeric(20, 15))
    hsi_msci_golden_dragon_ann_volatility   = Column(Numeric(20, 15))
    created_at                              = Column(DateTime, default=datetime.utcnow)
    updated_at                              = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DividendDistribution(Base):
    __tablename__ = "dividend_distribution"
    id                      = Column(Integer, primary_key=True, autoincrement=True)
    ex_date                 = Column(Date, nullable=False, index=True)
    payment_date            = Column(Date)
    isin_code               = Column(String(20), nullable=False, index=True)
    fund_code               = Column(String(20))
    fund_name               = Column(String(100))
    fund_class              = Column("class", String(50), nullable=False, index=True)
    currency                = Column(CHAR(3), nullable=False)
    ex_date_nav             = Column(Numeric(12, 4))
    dividend_per_unit       = Column(Numeric(16, 8))
    distribution_per_year   = Column(SmallInteger)
    annualized_yield        = Column(Numeric(20, 15))
    created_at              = Column(DateTime, default=datetime.utcnow)
    updated_at              = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ValuePartnersClassicFundNavs(Base):
    __tablename__ = "value_partners_classic_fund_navs"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    as_of_date  = Column(String(50), nullable=False, index=True)
    fund_class  = Column("class", String(50), nullable=False)
    nav         = Column(String(50))
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TopHoldings(Base):
    __tablename__ = "top_holdings"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    as_of_date    = Column(String(50), nullable=False, index=True)
    company_name  = Column(String(100), nullable=False)
    industry      = Column(String(100), nullable=False)
    weight        = Column(Numeric(10, 2), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GeographicalExposure(Base):
    __tablename__ = "geographical_exposure"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    as_of_date    = Column(String(50), nullable=False, index=True)
    geography     = Column(String(100), nullable=False)
    weight        = Column(Numeric(10, 2), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SectorExposure(Base):
    __tablename__ = "sector_exposure"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    as_of_date    = Column(String(50), nullable=False, index=True)
    sector        = Column(String(100), nullable=False)
    weight        = Column(Numeric(10, 2), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PortfolioCharacteristics(Base):
    __tablename__ = "portfolio_characteristics"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    as_of_date    = Column(String(50), nullable=False, index=True)
    price_earnings_ratio = Column(Numeric(10, 2))
    price_book_ratio     = Column(Numeric(10, 2))
    portfolio_yield      = Column(Numeric(10, 2))
    volatility_class_a   = Column(Numeric(10, 2))
    volatility_class_b   = Column(Numeric(10, 2))
    volatility_class_c   = Column(Numeric(10, 2))
    volatility_index     = Column(Numeric(10, 2))
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FeeStructure(Base):
    __tablename__ = "fee_structure"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    as_of_date    = Column(String(50), nullable=False, index=True)
    fund_class    = Column("class", String(50), nullable=False)
    min_subscription = Column(String(100))
    min_subsequent_subscription = Column(String(100))
    subscription_fee = Column(String(100))
    management_fee   = Column(String(100))
    performance_fee  = Column(String(200))
    redemption_fee   = Column(String(100))
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 新增：报告配置模型
class ReportConfig(Base):
    __tablename__ = "report_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    frequency = Column(String(50), nullable=False)
    report_type = Column(String(50), nullable=False)
    report_name = Column(String(255), nullable=False)
    deliverable_time = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    next_deliverable_time = Column(DateTime)
    is_active = Column(Integer, default=0, nullable=False)

# 新增：报告交付记录模型
class ReportRecord(Base):
    __tablename__ = "report_record"
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(Integer, nullable=False)
    report_name = Column(String(255), nullable=True)
    report_date = Column(Date, nullable=False)
    delivery_deadline = Column(DateTime, nullable=False)
    status = Column(String(50), default='Pending', nullable=False)
    submitted_at = Column(DateTime)
    as_of_date = Column(Date)
    report_link = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LcFundPerformance(Base):
    __tablename__ = "lc_fund_performance"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    report_date    = Column(Date, nullable=False)
    as_of_date     = Column(Date, nullable=False)
    fund_code      = Column(String(50), nullable=False)
    fund_name      = Column(String(255), nullable=False)
    benchmark      = Column(String(255))
    aum_usd_mn     = Column(Numeric(14, 2))
    aum_vp_pct     = Column(Numeric(10, 4))
    ytd_fund       = Column(Numeric(10, 4))
    ytd_bm         = Column(Numeric(10, 4))
    ytd_excess     = Column(Numeric(10, 4))
    one_y_fund     = Column("1y_fund",      Numeric(10, 4))
    one_y_bm       = Column("1y_bm",        Numeric(10, 4))
    one_y_excess   = Column("1y_excess",    Numeric(10, 4))
    ann_3y_fund    = Column(Numeric(10, 4))
    ann_3y_bm      = Column(Numeric(10, 4))
    ann_3y_excess  = Column(Numeric(10, 4))
    ann_5y_fund    = Column(Numeric(10, 4))
    ann_5y_bm      = Column(Numeric(10, 4))
    ann_5y_excess  = Column(Numeric(10, 4))
    ann_10y_fund   = Column(Numeric(10, 4))
    ann_10y_bm     = Column(Numeric(10, 4))
    ann_10y_excess = Column(Numeric(10, 4))
    ann_20y_fund   = Column(Numeric(10, 4))
    ann_20y_bm     = Column(Numeric(10, 4))
    ann_20y_excess = Column(Numeric(10, 4))
    since_inc_fund   = Column(Numeric(10, 4))
    since_inc_bm     = Column(Numeric(10, 4))
    since_inc_excess = Column(Numeric(10, 4))
    inception_date   = Column(Date)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LcFundPerformanceRating(Base):
    __tablename__ = "lc_fund_performance_rating"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    report_date   = Column(Date, nullable=False)
    as_of_date    = Column(Date, nullable=False)
    fund_name     = Column(String(100), nullable=False)
    aum_category  = Column(String(50))
    aum_usd_mn    = Column(Numeric(14, 2))
    aum_vp_pct    = Column(Numeric(10, 4))
    ms_rank_ytd   = Column(SmallInteger)
    ms_rank_1y    = Column(SmallInteger)
    ms_rank_3y    = Column(SmallInteger)
    ms_rank_5y    = Column(SmallInteger)
    ms_rank_10y   = Column(SmallInteger)
    ms_rank_20y   = Column(SmallInteger)
    ms_rank_si    = Column(SmallInteger)
    vs_bmk_ytd    = Column(String(20))
    vs_bmk_1y     = Column(String(20))
    vs_bmk_3y     = Column(String(20))
    vs_bmk_5y     = Column(String(20))
    vs_bmk_10y    = Column(String(20))
    vs_bmk_20y    = Column(String(20))
    vs_bmk_si     = Column(String(20))
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LcFundPerformanceSummary(Base):
    __tablename__ = "lc_fund_performance_summary"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    report_date     = Column(Date, nullable=False)
    as_of_date      = Column(Date, nullable=False)
    summary_type    = Column(String(100), nullable=False)
    period          = Column(String(20), nullable=False)
    pct_no_of_funds = Column(Numeric(10, 4))
    pct_of_aum      = Column(Numeric(10, 4))
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LcFundPerformanceOtherAccounts(Base):
    __tablename__ = "lc_fund_performance_other_accounts"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    report_date  = Column(Date, nullable=False)
    as_of_date   = Column(Date, nullable=False)
    account_name = Column(String(100), nullable=False)
    aum_usd_mn   = Column(Numeric(14, 2))
    remarks      = Column(String(255))
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LcFundPerformanceQuartile(Base):
    __tablename__ = "lc_fund_performance_quartile_contribution"
    id                  = Column(Integer, primary_key=True, autoincrement=True)
    report_date         = Column(Date, nullable=False)
    as_of_date          = Column(Date, nullable=False)
    period              = Column(String(20), nullable=False)
    q1_pct              = Column(Numeric(10, 4))
    q2_pct              = Column(Numeric(10, 4))
    q3_pct              = Column(Numeric(10, 4))
    q4_pct              = Column(Numeric(10, 4))
    top_half_summary_pct = Column(Numeric(10, 4))
    created_at          = Column(DateTime, default=datetime.utcnow)
    updated_at          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

