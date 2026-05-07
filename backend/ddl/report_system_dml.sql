-- =============================================================
-- Report Delivery Tracking System DML
-- Database: huili
-- Table: report_config
-- =============================================================

USE `huili`;

-- 清空旧数据（可选，如果是重新初始化）
TRUNCATE TABLE `report_config`;

-- 插入初始化对应数据
INSERT INTO `report_config` (
  `frequency`, `report_type`, `report_name`, `deliverable_time`, `system`, `dependency`, `recipient`, `description`
) VALUES 
(
  'Weekly', 
  'Internal', 
  'Fund performance Report for Leadership Committee (LC) meeting', 
  'Every Friday afternoon, the print out + the updated excel must be delivered to Titi.', 
  'Excel', 
  '- Performance Team: To provide the Morningstar Report\n- VIPER Team: Will auto-sent "Sales Report" to a group of recipients. We will obtain the AUM size from this email.', 
  'For LC meeting To: Titi or IMT PAs', 
  'Objective: This report is created for timely reporting of VP funds'' performance in Leadership Committee (LC) meeting.'
),
(
  'Monthly', 
  'Internal', 
  'Investment Performance & Risk (PPT)', 
  'T + 12', 
  'PPT', 
  'Pre-requisite to complete #:\n4a. Performance Reporting\n4b. Risk Reporting\n4c. Liquidity Risk Reporting\n4d. Counterparty Risk Reporting\n4e. Asset Concentration Risk', 
  '- IMT: Norman Ho, Kelly Chung, Gordon Ip, Michelle Yu and Luo Jing\nSales/CS Team: Hardy, Vincent Ching, Clare\nCFO (or Head of Corporate Audit Services): Nikita Ng', 
  'Objective: This report will provide a comprehensive monthly performance and risk of the funds both at the fund level and at VP Group level. It shows not only against the benchmark but also against the peer group. In addition, at VP Group Level, it also show how they performed against the agreed Key Risk Indicators (KRIs).'
),
(
  'Monthly', 
  'Internal', 
  'Performance Reporting', 
  'T + 8', 
  'Excel', 
  'Performance Team: (1) Morningstar Report which contains Performance figures + Quartile Ranking (2) Factsheet files: Fund''s Performance vs Benchmark''s Benchmark (3) AUM File: Funds'' official AUM figures (however, since it is only be ready by 18th calendar days... now we are using estimated AUM figures from VIPER Daily Sales Report', 
  'Refer to #2.', 
  'Objective: to provide analysis on our fund performance not only at the fund level but also at the VPG level. This analysis will be communicated not only to Senior Investment Team Leaders & Mgmt on monthly basis but also report it quarterly to Risk Management Committee and Audit Committee\nAnalysis provided: performance and risk relative to benchmark + peer group.'
),
(
  'Monthly', 
  'Internal', 
  'Risk Reporting', 
  'T + 8', 
  'Excel', 
  'Performance Team: Morningstar Report which contains Std Dev,', 
  'Refer to #2.', 
  'Objective: to provide analysis on our fund ex-post risk not only at the fund level. This analysis will be communicated not only to Senior Investment Team Leaders & Mgmt on monthly basis but also report it quarterly to Risk Management Committee and Audit Committee\nAnalysis provided: Std Deviation, Tracking Error, etc.'
),
(
  'Monthly', 
  'Internal', 
  'Liquidity Risk Reporting', 
  'T + 8', 
  'Excel', 
  'Refer to SOP', 
  'Refer to #2.', 
  'Objective: to provide the liquidity profile of the funds'
),
(
  'Ad-Hoc', 
  'Internal', 
  'Counterparty Risk', 
  'Ad-Hoc', 
  'BBG', 
  'This is dependent on "Market Risk Monitoring". If there is any name or company with significant risk issue, we will highlight in the monthly risk report, or ad-hoc basis', 
  'Refer to #2.', 
  'Objective: to inform the management and any relevant internal stakeholders, if we do have any exposure (and the size of exposure) to a company which has negative news or worsen credit quality.'
),
(
  'Monthly', 
  'Internal', 
  'Asset Concentration Risk', 
  'T + 8', 
  'Excel', 
  '- VIPER Support Team: will send an excel file which contains information all of the funds'' holdings.', 
  'Refer to #2.', 
  'Objective: to provide an insight on the Top 10 securities that have the largest exposure relative to the company''s the overall AUM, including the breakdown of which funds are holding the most of these securities.'
),
(
  'Monthly', 
  'Internal', 
  'VPJR - Risk Monitoring', 
  'T + 5', 
  '- Excel - Aladdin (to be transferred to FactSet)', 
  'Sales Team will obtain Model Portfolio''s T.E. from Daiwa on monthly basis', 
  '- VPJR''s PM: Lucy Liu', 
  'To assist IMT to monitor the risks of VPJR against the agreed thresholds'
),
(
  'Annually', 
  'Internal', 
  'Counterparty Credit Risk Monitoring', 
  'February', 
  '- Excel - Bloomberg', 
  'Middle Office: to provide the confirmed list of approved active brokers.', 
  '- Dealing Team', 
  'Objective: This is to ensure that we are not exposed to any counterparty credit risk from our existing brokers'
);
