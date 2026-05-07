-- =============================================================
-- LC Report 初始化 DML — lc_fund_code_map + lc_other_accounts_config
-- 数据来源：
--   entity_name / isin  → Quartile_weekly (HKSFC/Offshore/UCITS) sheets
--   inception_date      → Excel Performance Sheet AB列
--   benchmark_name      → Excel Performance Sheet D列
-- 执行顺序：在 02_report_generator_views.sql 之后执行
-- =============================================================
ALTER TABLE lc_fund_performance                        CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE lc_fund_performance_rating                 CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE lc_fund_performance_summary                CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE lc_fund_performance_other_accounts         CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE lc_fund_performance_quartile_contribution  CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;


-- -------------------------------------------------------------
-- 1. lc_fund_code_map 初始化数据（SalesReport 全部 53 个基金）
--    有 QW peer group 数据的基金：entity_name 和 isin 来自 Morningstar
--    无 QW 数据的基金：entity_name 用 SalesReport fund_name，isin 为空
--    benchmark_name 来自 Performance Sheet D列
-- -------------------------------------------------------------
INSERT INTO lc_fund_code_map (fund_code, entity_name, isin, inception_date, benchmark_name, bm_entity_name) VALUES
-- =====================================================
-- A. 有 QW Morningstar peer group 数据的基金（21个）
--    bm_entity_name = QW 数据中 BM 行的实际 entity_name（用于 JOIN）
--    benchmark_name = Performance Sheet D列的显示名称
-- =====================================================
-- Grt Chn Eq_HKSFC (VPAF & CG)
('VPAF', 'Value Partners Classic A USD',                    'HK0000264868', '1993-04-02', 'MSCI Golden Dragon NR USD', 'HSI HKD TR + MSCI G. Dragon (20171001)'),
('CG',   'Value Partners China Greenchip Ltd',              'KYG9317M1033', '2002-04-09', 'MSCI Golden Dragon NR USD', 'MSCI Golden Dragon NR USD'),
-- China Equity_HKSFC (VPCA & VPMF)
('VPCA', 'Value Partners China Convergence',                'KYG9317Q1047', '2000-07-14', 'VPCA_MSCI China_NR_Factsheet', 'VPCA_MSCI China_NR_Factsheet'),
('VPMF', 'Val Ptnrs Chns Mnlnd Foc A',                     'KYG9317Q1120', '2003-11-27', 'VPMF_MSCI China_NR_Factsheet', 'VPMF_MSCI China_NR_Factsheet'),
-- Asia ex Japan Eq_HKSFC (VPHY)
('VPHY', 'Value Partners Hi-Div Stks A1 USD',               'HK0000288735', '2002-09-03', 'MSCI AC Asia Ex Japan NR USD', 'MSCI AP x J + MSCI Ax) 20160430 (NR)'),
-- China Equity - A Shares (VCAS)
('VCAS', 'Value Partners China A-Share Sel A CHN',           'HK0000220001', '2014-10-17', 'CSI 300 TR CNY', 'CSI 300 TR CNY'),
-- Taiwan SML Cap Eq (VPTF)
('VPTF', 'Value Partners Taiwan A',                          'KYG9318Y1061', '2008-03-04', 'Taiwan Weighted Index TR Daily', 'Taiwan Weighted Index TR Daily'),
-- PG_High Yield Bond (VPGB)
('VPGB', 'Value Partners Grt CHN HY In P Acc USD',          'KYG9319N1097', '2012-03-28', NULL, 'JPM ACI Non Investment Grade TR USD'),
-- Greater China Allocation (VPMA)
('VPMA', 'Value Partners Multi-Asset A USD',                 'HK0000269149', '2015-10-14', NULL, '50% MSCI Golden Dragon + 50% JACI China TR'),
-- Asia Allocation (VAIF & VAIO)
('VAIF', 'Value Partners Asian Inc A USD Acc',               'HK0000352374', '2017-11-13', '50%MSCI AC Asia ex Jap + 50% JPM Asia Credit Index', '50%MSCI AC Asia ex Jap + 50% JPM Asia Credit Index'),
('VAIO', 'Value Partners Asn Innovt OppsAUSDUnhAcc',        'HK0000475969', '2019-02-26', 'VAIO Custom Benchmark', 'VAIO Custom Benchmark'),
-- Asia Bond (VATB)
('VATB', 'Value Partners Asian TR Bd A USD Acc',             'HK0000402450', '2018-04-09', NULL, 'JPM Asia Credit TR USD'),
-- China Bond (VACB)
('VACB', 'Value Partners All CHN Bd A USD Acc Unh',          'HK0000770799', '2021-09-07', NULL, 'JPM ACI China TR USD (VACB)'),
-- Money Market (VPMM)
('VPMM', 'Value Partners USD Mny Mkt A USD UnH Acc',        'HK0000945037', '2023-08-19', 'US 90 Days Ave SOFR', 'US 90 Days Ave SOFR  Secured Overnight Financing Rate'),
-- Japan REIT (VPJR)
('VPJR', 'Value Partners Japan REIT A JPY UnH MDis',         'HK0000997111', '2024-04-23', 'TSE REIT NR JPY', 'TSE REIT NR JPY'),
-- Sector Eq HC China (VHCF)
('VHCF', 'Value Partners Health Care A USD Acc',             'IE00BSM8VZ90', '2015-04-02', 'MSCI China All Shares HC 10/40 NR USD', 'MSCI China All Shares HC 10/40 NR USD'),
-- Asia ex-Japan Equity UCITS (VPEJ)
('VPEJ', 'Value Partners Asia ex-Japan Eq V USDAcc',         'IE00BD3HK754', '2018-09-01', 'MSCI AC Asia Ex Japan NR USD', 'MSCI AC Asia Ex Japan NR USD'),
-- Grt Chn HY Bond UCITS (VUGB)
('VUGB', 'Value Partners Grtr CHN HY Bd AUSDAccUnH',        'IE00BKRQZ838', '2019-12-06', NULL, 'JPM ACI China TR USD (VUGB)'),
-- PG_VUHD (HY Income Custom) UCITS
('VUHD', 'Value Partners CHN AShrsHiDiv V USD Acc',          'IE00BMGYK213', '2020-10-19', 'CSI 300 TR CNY', 'CSI 300 TR CNY (VUHD)'),
-- Asia Bond UCITS (VUAD)
('VUAD', 'Val Ptnrs Asn Dyn Bd V USD UnH Acc',              'IE00BN6JWM76', NULL,          NULL, 'JPM Asia Credit TR USD (VUAD)'),
-- MTIA sub-advisory (Performance Sheet 有，但无 QW 数据)
('MTIA', 'Minsheng Tonghui IA',                              '',             '2017-01-23', 'Hang Seng Index TR', 'Hang Seng Index TR'),

-- =====================================================
-- B. SalesReport 中无 QW 数据的基金（32个）
--    entity_name = SalesReport fund_name
--    isin = 空（ETL 上传后如有 QW 数据会自动覆盖）
--    bm_entity_name = NULL（无 QW benchmark 数据）
-- =====================================================
-- 标准基金（无 QW peer group）
('VFI3',     'VP Enhanced Total Return Bond Fund SP',                 '', NULL, NULL, NULL),
('VPLLC',    'Value Partners Asia Fund, LLC',                         '', NULL, NULL, NULL),
('VGSD',     'VP Global Short Duration IG Bond Fund',                 '', NULL, NULL, NULL),
('VSP1',     'VP China A-Share Innovation Fund',                      '', NULL, NULL, NULL),
('VSP2',     'VP China Energy Shifting Fund SP',                      '', NULL, NULL, NULL),
-- ETF
('VPGF',     'Value Gold ETF',                                        '', NULL, NULL, NULL),
('VMEH',     'Value Partners HKD Money Market ETF',                   '', NULL, NULL, NULL),
('VMER',     'Value Partners RMB Money Market ETF',                   '', NULL, NULL, NULL),
('VMEU',     'Value Partners USD Money Market ETF',                   '', NULL, NULL, NULL),
('HDLV',     'VP HK-US Dividend Low Volatility ETF',                  '', NULL, NULL, NULL),
-- 外部/子顾问基金
('PAIF',     'Antipodes Asia Income Fund',                             '', NULL, NULL, NULL),
('VPJA',     'China New Century Fund',                                 '', NULL, NULL, NULL),
('MVTF',     'Milltrust Value Partners Taiwan Fund',                   '', NULL, NULL, NULL),
('VQFI3',    'VQFI3',                                                  '', NULL, NULL, NULL),
('QDIE1',    'VP-SV-Tech Fund',                                        '', NULL, NULL, NULL),
-- IA 账户
('GWW1',     'Greatwall Wealth IA 1',                                  '', NULL, NULL, NULL),
('PFM11',    'VP PFM Jing Du China Fund',                              '', NULL, NULL, NULL),
('PFM10',    'VP PFM Visionary China Fund 1',                          '', NULL, NULL, NULL),
('PFM8',     'VP PFM Prudence China 1',                                '', NULL, NULL, NULL),
('PFM13',    'VP PFM Feng Tai-China A Share 3',                        '', NULL, NULL, NULL),
-- FOTIC IA 系列
('FOTIC2',   'FOTIC IA 2',                                             '', NULL, NULL, NULL),
('FOTICF',   'FOTICF',                                                  '', NULL, NULL, NULL),
('FOTICF1',  'FOTICF1',                                                 '', NULL, NULL, NULL),
('FOTICAH',  'FOTIC IA A+H',                                           '', NULL, NULL, NULL),
('FOTIC8',   'FOTIC IA 8',                                             '', NULL, NULL, NULL),
('FOTIC11',  'FOTIC IA 11',                                            '', NULL, NULL, NULL),
-- 委托管理
('RM_DAIWA', 'Daiwa Advisory Mandate',                                 '', NULL, NULL, NULL),
('DHCF',     'Daiwa VP Health Care',                                   '', NULL, NULL, NULL),
-- LP 基金
('VPRE',     'Asia Pacific Real Estate LP',                            '', NULL, NULL, NULL),
('VPSDLPF1', 'VP Silver Dart Apollo LPF1',                             '', NULL, NULL, NULL),
('VPSDLPF2', 'VP Silver Dart Helios LPF2',                             '', NULL, NULL, NULL),
('VPSC',     'Shenzhen Capital VP Greater Bay Area OP LPF',            '', NULL, NULL, NULL),
('VPAPCF',   'VP Asia Principal Credit Fund',                          '', NULL, NULL, NULL)

ON DUPLICATE KEY UPDATE
    entity_name    = VALUES(entity_name),
    isin           = CASE WHEN VALUES(isin) != '' THEN VALUES(isin) ELSE isin END,
    inception_date = COALESCE(VALUES(inception_date), inception_date),
    benchmark_name = COALESCE(VALUES(benchmark_name), benchmark_name),
    bm_entity_name = COALESCE(VALUES(bm_entity_name), bm_entity_name),
    updated_at     = NOW();


-- -------------------------------------------------------------
-- 2. lc_other_accounts_config 初始化数据
--    对应 HKSFC Sheet R42-R44 的 Others 区域：
--      Gold ETF     → SalesReport fund_code=VPGF (Value Gold ETF, AUM=625M)
--      Real Estate  → SalesReport fund_code=VPRE (Asia Pacific Real Estate LP, AUM=235M)
-- -------------------------------------------------------------
INSERT INTO lc_other_accounts_config (account_name, fund_code, display_order) VALUES
('Gold ETF',    'VPGF',  1),
('Real Estate', 'VPRE',  2)
ON DUPLICATE KEY UPDATE
    fund_code     = VALUES(fund_code),
    display_order = VALUES(display_order);
