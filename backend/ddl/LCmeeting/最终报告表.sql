-- ==========================================================
-- 表1: 基金业绩与晨星评级核心明细表 (主体中间部分)
-- ==========================================================
DROP TABLE IF EXISTS `lc_fund_performance_rating`;
CREATE TABLE `lc_fund_performance_rating` (
    `id` BIGINT AUTO_INCREMENT COMMENT '主键ID',
    `report_date` DATE NOT NULL COMMENT '前端选择的报告日期',
    `as_of_date` DATE NOT NULL COMMENT 'SalesReport中读取到的报告时间',
    `fund_name` VARCHAR(100) NOT NULL COMMENT '基金名称',
    `aum_category` VARCHAR(50) COMMENT 'AUM分类 (如: > USD 100mil, USD 15mil - 100mil)',
    `aum_usd_mn` DECIMAL(30,10) COMMENT '资管规模(百万美元)',
    `aum_vp_pct` DECIMAL(20,10) COMMENT '占VP总AUM百分比 (如27.9%存为0.2790)',
    
    -- Morningstar 评级 (四分位排名 1,2,3,4，空值允许为NULL)
    `ms_rank_ytd` TINYINT COMMENT '晨星排名-YTD',
    `ms_rank_1y` TINYINT COMMENT '晨星排名-1年',
    `ms_rank_3y` TINYINT COMMENT '晨星排名-3年',
    `ms_rank_5y` TINYINT COMMENT '晨星排名-5年',
    `ms_rank_10y` TINYINT COMMENT '晨星排名-10年',
    `ms_rank_20y` TINYINT COMMENT '晨星排名-20年',
    `ms_rank_si` TINYINT COMMENT '晨星排名-成立以来',
    
    -- 跑赢/跑输基准 (A=Above, B=Below, N/A, No BMK)
    `vs_bmk_ytd` VARCHAR(20) COMMENT '基准对比-YTD',
    `vs_bmk_1y` VARCHAR(20) COMMENT '基准对比-1年',
    `vs_bmk_3y` VARCHAR(20) COMMENT '基准对比-3年',
    `vs_bmk_5y` VARCHAR(20) COMMENT '基准对比-5年',
    `vs_bmk_10y` VARCHAR(20) COMMENT '基准对比-10年',
    `vs_bmk_20y` VARCHAR(20) COMMENT '基准对比-20年',
    `vs_bmk_si` VARCHAR(20) COMMENT '基准对比-成立以来',
    
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_report_date_fund` (`report_date`, `fund_name`) -- 唯一索引，防重+覆盖
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='基金评级与基准表现月度明细表';

-- ==========================================================
-- 表2: 基金表现全局摘要表 (顶部 Performance Summary 区域)
-- ==========================================================
DROP TABLE IF EXISTS `lc_fund_performance_summary`;
CREATE TABLE `lc_fund_performance_summary` (
    `id` BIGINT AUTO_INCREMENT COMMENT '主键ID',
    `report_date` DATE NOT NULL COMMENT '前端选择的报告日期',
    `as_of_date` DATE NOT NULL COMMENT 'SalesReport中读取到的报告时间',
    `summary_type` VARCHAR(100) NOT NULL COMMENT '摘要类型(如: Ranked in 1st and 2nd Quartile, Outperform Benchmark)',
    `period` VARCHAR(20) NOT NULL COMMENT '周期 (YTD, 1Y, 3Y, 5Y)',
    `pct_no_of_funds` DECIMAL(20,10) COMMENT '基金数量占比 (如 67% 存为 0.6700)',
    `pct_of_aum` DECIMAL(20,10) COMMENT 'AUM占比 (如 71% 存为 0.7100)',
    
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_summary` (`report_date`, `summary_type`, `period`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='基金整体表现概览表';

-- ==========================================================
-- 表3: 其他资产/账户规模表 (底部 Other Accounts 区域)
-- ==========================================================
DROP TABLE IF EXISTS `lc_fund_performance_other_accounts`;
CREATE TABLE `lc_fund_performance_other_accounts` (
    `id` BIGINT AUTO_INCREMENT COMMENT '主键ID',
    `report_date` DATE NOT NULL COMMENT '前端选择的报告日期',
    `as_of_date` DATE NOT NULL COMMENT 'SalesReport中读取到的报告时间',
    `account_name` VARCHAR(100) NOT NULL COMMENT '账户名称 (如 Gold ETF, Real Estate)',
    `aum_usd_mn` DECIMAL(30,10) COMMENT 'AUM(百万美元)',
    `remarks` VARCHAR(255) COMMENT '备注说明',
    
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_other_accounts` (`report_date`, `account_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='其他账户AUM明细表';



DROP TABLE IF EXISTS `lc_fund_performance_quartile_contribution`;
CREATE TABLE `lc_fund_performance_quartile_contribution` (
    `id` BIGINT AUTO_INCREMENT COMMENT '主键ID',
    `report_date` DATE NOT NULL COMMENT '前端选择的报告日期',
    `as_of_date` DATE NOT NULL COMMENT 'SalesReport中读取到的报告时间',
    `period` VARCHAR(20) NOT NULL COMMENT '表现周期 (枚举值: YTD, 1Y, 3Y, 5Y, 10Y, 20Y)',
    
    `q1_pct` DECIMAL(20,10) NOT NULL DEFAULT '0.0000000000' COMMENT '第1四分位(1st Quartile)占比',
    `q2_pct` DECIMAL(20,10) NOT NULL DEFAULT '0.0000000000' COMMENT '第2四分位(2nd Quartile)占比',
    `q3_pct` DECIMAL(20,10) NOT NULL DEFAULT '0.0000000000' COMMENT '第3四分位(3rd Quartile)占比',
    `q4_pct` DECIMAL(20,10) NOT NULL DEFAULT '0.0000000000' COMMENT '第4四分位(4th Quartile)占比',
    
    `top_half_summary_pct` DECIMAL(20,10) COMMENT '前1/2分位汇总占比(Q1+Q2，供前端直接展示底注)',
    
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    -- 创建联合唯一索引：确保同一报告期内，每个周期只有一条数据，用于实现 Upsert 覆盖更新
    UNIQUE KEY `uk_report_date_period` (`report_date`, `period`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='基金各周期四分位排名及AUM贡献分布表';



DROP TABLE IF EXISTS `lc_fund_performance`;
CREATE TABLE `lc_fund_performance` (
    `id` BIGINT AUTO_INCREMENT COMMENT '主键ID',
    `report_date` DATE NOT NULL COMMENT '前端选择的报告日期',
    `as_of_date` DATE NOT NULL COMMENT 'SalesReport中读取到的报告时间',
    `fund_code` VARCHAR(50) NOT NULL COMMENT '基金代码',
    `fund_name` VARCHAR(255) NOT NULL COMMENT '基金名称',
    `benchmark` VARCHAR(255) COMMENT '比较基准 (Benchmark)',
    `aum_usd_mn` DECIMAL(30,10) COMMENT '资管规模(百万美元)',
    `aum_vp_pct` DECIMAL(20,10) COMMENT '资管规模占比 (如 27.9% 存为 0.2790)',
    
    -- YTD 表现
    `ytd_fund` DECIMAL(20,10) COMMENT 'YTD 基金表现',
    `ytd_bm` DECIMAL(20,10) COMMENT 'YTD 基准表现',
    `ytd_excess` DECIMAL(20,10) COMMENT 'YTD 超额收益',
    
    -- 1Y 表现
    `1y_fund` DECIMAL(20,10) COMMENT '1年 基金表现',
    `1y_bm` DECIMAL(20,10) COMMENT '1年 基准表现',
    `1y_excess` DECIMAL(20,10) COMMENT '1年 超额收益',
    
    -- 年化 3Y 表现
    `ann_3y_fund` DECIMAL(20,10) COMMENT '年化3年 基金表现',
    `ann_3y_bm` DECIMAL(20,10) COMMENT '年化3年 基准表现',
    `ann_3y_excess` DECIMAL(20,10) COMMENT '年化3年 超额收益',
    
    -- 年化 5Y 表现
    `ann_5y_fund` DECIMAL(20,10) COMMENT '年化5年 基金表现',
    `ann_5y_bm` DECIMAL(20,10) COMMENT '年化5年 基准表现',
    `ann_5y_excess` DECIMAL(20,10) COMMENT '年化5年 超额收益',
    
    -- 年化 10Y 表现
    `ann_10y_fund` DECIMAL(20,10) COMMENT '年化10年 基金表现',
    `ann_10y_bm` DECIMAL(20,10) COMMENT '年化10年 基准表现',
    `ann_10y_excess` DECIMAL(20,10) COMMENT '年化10年 超额收益',
    
    -- 年化 20Y 表现
    `ann_20y_fund` DECIMAL(20,10) COMMENT '年化20年 基金表现',
    `ann_20y_bm` DECIMAL(20,10) COMMENT '年化20年 基准表现',
    `ann_20y_excess` DECIMAL(20,10) COMMENT '年化20年 超额收益',
    
    -- 成立以来表现 (Since Inception)
    `since_inc_fund` DECIMAL(20,10) COMMENT '成立以来 基金表现',
    `since_inc_bm` DECIMAL(20,10) COMMENT '成立以来 基准表现',
    `since_inc_excess` DECIMAL(20,10) COMMENT '成立以来 超额收益',
    
    `inception_date` DATE COMMENT '基金成立日期',
    
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    -- 创建唯一索引，用于防重和实现 Upsert 更新
    UNIQUE KEY `uk_as_of_date_fund` (`report_date`, `as_of_date`, `fund_code`, `fund_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='基金月度业绩报告表(原始数据)';