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
INSERT INTO lc_fund_code_map (fund_code,fund_name,isin,is_fund,is_new,is_diff,benchmark_name,inception_date,entity_name,bm_entity_name,created_at,updated_at) VALUES
	 ('ACHIE','M&G (ACS) China Equity Fund',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('CG','Greenchip','KYG9317M1033',1,0,0,'MSCI Golden Dragon NR USD','2002-04-09','Value Partners China Greenchip Ltd','MSCI Golden Dragon NR USD',NOW(),NOW()),
	 ('DHCF','Daiwa VP Health Care',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('FOTIC11','FOTIC IA 11',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('FOTIC2','FOTIC IA 2',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('FOTIC8','FOTIC IA 8',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('FOTICAH','FOTIC IA  A+H',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('FOTICF','FOTICF',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('FOTICF1','FOTICF1',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('GF87','Account - GF87',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW());
INSERT INTO lc_fund_code_map (fund_code,fund_name,isin,is_fund,is_new,is_diff,benchmark_name,inception_date,entity_name,bm_entity_name,created_at,updated_at) VALUES
	 ('GWW1','Greatwall Wealth IA 1',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('HDLV','VP HK-US Dividend Low Volatility ETF',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('MTIA','Minsheng Tonghui IA',NULL,1,0,0,'Hang Seng Index TR','2017-01-23','Minsheng Tonghui (23-Jan-17)','Hang Seng Index TR',NOW(),NOW()),
	 ('MVTF','Milltrust Value Partners Taiwan Fund',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('PAIF','Antipodes Asia Income Fund',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('PFM1','VP PFM Neo-China A Share',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('PFM10','VP PFM Visionary China Fund 1',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('PFM11','VP PFM Jing Du China Fund',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('PFM13','VP PFM Feng Tai-China A Share 3',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('PFM14','VP PFM Jia Xiang 1',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW());
INSERT INTO lc_fund_code_map (fund_code,fund_name,isin,is_fund,is_new,is_diff,benchmark_name,inception_date,entity_name,bm_entity_name,created_at,updated_at) VALUES
	 ('PFM4','VP PFM China A Share Platinum',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('PFM8','VP PFM Prudence China 1',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('QDIE1','VP-SV-Tech Fund',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('RM_DAIWA','Daiwa Advisory Mandate',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('SAIA','Sinosafe Assets IA',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VACB','VP All China Bond Fund','HK0000770799',1,0,0,'JPM ACI China TR USD','2021-09-07','Value Partners All CHN Bd A USD Acc Unh','JPM ACI China TR USD',NOW(),NOW()),
	 ('VAIF','Value Partners Asian Income Fund','HK0000352374',1,0,0,'50%MSCI AC Asia ex Jap + 50% JPM Asia Credit Index','2017-12-01','Value Partners Asian Inc A USD Acc','50%MSCI AC Asia ex Jap + 50% JPM Asia Credit Index',NOW(),NOW()),
	 ('VAIO','VP Asian Innovation Opportunities Fund','HK0000475969',1,0,0,'VAIO Custom Benchmark','2019-02-26','Value Partners Asn Innovt OppsAUSDUnhAcc','VAIO Custom Benchmark',NOW(),NOW()),
	 ('VATB','Value Partners Asian Total Return Bond Fund','HK0000402450',1,0,0,'JPM ACI APAC ','2018-04-09','Value Partners Asian TR Bd A USD Acc','JPM Asia Credit TR USD',NOW(),NOW()),
	 ('VCAS','China A-Share Select Fund','HK0000220001',1,0,0,'CSI 300 TR CNY','2014-10-17','Value Partners China A-Share Sel A CHN','CSI 300 Index TR CNY',NOW(),NOW());
INSERT INTO lc_fund_code_map (fund_code,fund_name,isin,is_fund,is_new,is_diff,benchmark_name,inception_date,entity_name,bm_entity_name,created_at,updated_at) VALUES
	 ('VFI3','VP Enhanced Total Return Bond Fund SP',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VGCP','Greater China Preference Shares',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VGSD','VP Global Short Duration IG Bond Fund',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VHCF','Value Partners Health care Fund','IE00BSM8VZ90',1,0,0,'MSCI China All Shares HC 10/40 NR USD','2015-04-03','Value Partners Health Care A USD Acc','MSCI China All Shares HC 10/40 NR USD',NOW(),NOW()),
	 ('VMEH','Value Partners HKD Money Market ETF',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VMER','Value Partners RMB Money Market ETF',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VMEU','Value Partners USD Money Market ETF',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VPAF','Classic Fund','HK0000264868',1,0,0,'MSCI Golden Dragon NR USD','1993-04-02','Value Partners Classic A USD','HSI HKD TR + MSCI G. Dragon (20171001)',NOW(),NOW()),
	 ('VPAPCF','VP Asia Principal Credit Fund',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VPCA','China Convergence Fund','KYG9317Q1047',1,0,0,'VPCA_MSCI China_NR_Factsheet','2000-07-17','Value Partners China Convergence','VPCA_MSCI China_NR_Factsheet',NOW(),NOW());
INSERT INTO lc_fund_code_map (fund_code,fund_name,isin,is_fund,is_new,is_diff,benchmark_name,inception_date,entity_name,bm_entity_name,created_at,updated_at) VALUES
	 ('VPEJ','VP Asia Ex-Japan Equity Fund','IE00BD3HK754',1,0,0,'MSCI AC Asia Ex Japan NR USD','2018-09-01','Value Partners Asia ex-Japan Eq V USDAcc','MSCI AC Asia Ex Japan NR USD',NOW(),NOW()),
	 ('VPGB','Greater China High Yield','KYG9319N1097',1,0,0,'JPM ACI Non Investment Grade TR USD','2012-03-29','Value Partners Grt CHN HY In P Acc USD','JPM ACI Non Investment Grade TR USD',NOW(),NOW()),
	 ('VPGF','Value Gold ETF',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VPHB','China HK Bond and Gold Fund',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VPHF','VP Hedge Fund',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VPHU','Value Partners Hedge Fund (US-feeder)',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VPHY','High-Dividend Stocks Fund','HK0000288735',1,0,0,'MSCI AC Asia Ex Japan NR USD','2002-09-03','Value Partners Hi-Div Stks A1 USD','MSCI AP x J + MSCI AxJ 20160430 (NR)',NOW(),NOW()),
	 ('VPJA','China New Century Fund',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VPJR','Value Partners Japan REIT Fund','HK0000997111',1,0,0,'TSE REIT NR JPY','2024-04-23','Value Partners Japan REIT A JPY UnH MDis','TSE REIT NR JPY',NOW(),NOW()),
	 ('VPLLC','Value Partners Asia Fund, LLC',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW());
INSERT INTO lc_fund_code_map (fund_code,fund_name,isin,is_fund,is_new,is_diff,benchmark_name,inception_date,entity_name,bm_entity_name,created_at,updated_at) VALUES
	 ('VPMA','Multi Asset Fund','HK0000269149',1,0,0,'50% MSCI Golden Dragon + 50% JACI China TR','2015-10-14','Value Partners Multi-Asset A USD','50% MSCI Golden Dragon + 50% JACI China TR',NOW(),NOW()),
	 ('VPMF','Chinese Mainland Focus Fund','KYG9317Q1120',1,0,0,'VPMF_MSCI China_NR_Factsheet','2003-11-28','Val Ptnrs Chns Mnlnd Foc A','VPCA_MSCI China_NR_Factsheet',NOW(),NOW()),
	 ('VPMM','Value Partners USD Money Market Fund','HK0000945037',1,0,0,'US 90 Days Ave SOFR  Secured Overnight Financing Rate','2023-08-19','Value Partners USD Mny Mkt A USD UnH Acc','SOFR Averages 90 Day Yld USD',NOW(),NOW()),
	 ('VPRE','Asia Pacific Real Estate LP',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VPSC','Shenzhen Capital VP Greater Bay Area OP LPF',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VPSDLPF1','VP Silver Dart Apollo LPF1',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VPSDLPF2','VP Silver Dart Helios LPF2',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VPTF','VP Taiwan Fund','KYG9318Y1061',1,0,0,'Taiwan Weighted Index TR Daily','2008-03-04','Value Partners Taiwan A','Taiwan Weighted Index TR Daily',NOW(),NOW()),
	 ('VQAIF','VQAIF',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VQFI3','VQFI3',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW());
INSERT INTO lc_fund_code_map (fund_code,fund_name,isin,is_fund,is_new,is_diff,benchmark_name,inception_date,entity_name,bm_entity_name,created_at,updated_at) VALUES
	 ('VSP1','VP China A-Share Innovation Fund',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VSP2','VP China Energy Shifting Fund SP',NULL,0,0,0,NULL,NULL,NULL,NULL,NOW(),NOW()),
	 ('VUAD','VP Asian Dynamic Bond Fund','IE00BN6JWM76',0,0,0,'JPM Asia Credit TR USD','2021-06-03','Val Ptnrs Asn Dyn Bd V USD UnH Acc','JPM Asia Credit TR USD',NOW(),NOW()),
	 ('VUGB','ICAV VP Greater China High Yield','IE00BKRQZ838',0,0,0,'JPM ACI China TR USD','2019-12-06','Value Partners Grtr CHN HY Bd AUSDAccUnH','JPM ACI China TR USD',NOW(),NOW()),
	 ('VUHD','VP China A Shares High Dividend Fund','IE00BMGYK213',1,0,0,'CSI 300 TR CNY','2020-10-19','Value Partners CHN AShrsHiDiv V USD Acc','CSI 300 Index TR CNY',NOW(),NOW());

-- -------------------------------------------------------------
-- 1.1 Update is_fund = 1 for specified 19 funds
-- -------------------------------------------------------------
UPDATE lc_fund_code_map
SET is_fund = 1
WHERE fund_code IN (
    'VPHY', 'VPAF', 'VAIF', 'VPGB', 'VPMM', 'VPMF', 'VPCA', 'CG', 'VPTF',
    'VPJR', 'VAIO', 'VATB', 'VHCF', 'VPMA', 'VCAS', 'VACB', 'VUHD', 'VPEJ', 'MTIA'
);


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
