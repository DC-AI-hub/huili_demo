-- =============================================================
-- Huili Demo - Database DDL
-- Database: huili
-- Generated: 2026-02-27
-- =============================================================

CREATE DATABASE IF NOT EXISTS `huili`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE `huili`;

-- -------------------------------------------------------------
-- Classic Sheet 前 10 行固定基金信息
--   对应 Excel Classic Sheet 的固定 Header 区域：
--   - 基金名称 / As of Date
--   - Fund Size
--   - NAV per unit（A 类 / B 类 / C 类 / C 类 HKD）
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `value_partners_classic_fund_info` (
    `id`             INT          NOT NULL AUTO_INCREMENT COMMENT '主键',
    `as_of_date`     VARCHAR(50)                         COMMENT '数据截止日期，如 2026-01-31',
    `fund_size`      VARCHAR(100)                        COMMENT '基金规模，如 USD 1137.4 million',
    `nav_a_unit`     VARCHAR(50)                         COMMENT 'A 类单位净值，如 USD 527.78',
    `nav_b_unit`     VARCHAR(50)                         COMMENT 'B 类单位净值，如 USD 227.81',
    `nav_c_unit`     VARCHAR(50)                         COMMENT 'C 类单位净值，如 USD 28.68',
    `nav_c_unit_hkd` VARCHAR(50)                         COMMENT 'C 类单位净值（港元），如 HKD 223.1212',
    `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Value Partners Classic Fund Info';

-- -------------------------------------------------------------
-- NAVs
-- NAV是net asset value净资产
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `value_partners_classic_fund_navs` (
    `id`             INT          NOT NULL AUTO_INCREMENT COMMENT '主键',
    `as_of_date`     VARCHAR(50)                         COMMENT '数据截止日期，如 2026-01-31',
    `class`     VARCHAR(50)                         COMMENT '基金类型，如 Class A USD',
    `nav`     VARCHAR(50)                         COMMENT '基金净值，如 227.81',
    `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Value Partners Classic Fund NAVs';

-- -------------------------------------------------------------
-- Classic Sheet 月度业绩表（动态增长）
--   对应 Excel Classic Sheet 的 "Monthly performance from 2000 to present" 表格
--
--   百分比字段说明：
--   - 存储 Excel 底层小数值（pandas 读取百分比格式单元格的原始值）
--   - 例如：2.4% 存储为 0.024000000000000；-2.16% 存储为 -0.021611886537596
--   - 字段类型：DECIMAL(20, 15)
--     · 总位数 20，小数位 15，整数位 5（足够表示 -9.999... 到 9.999...，即 -999.99% 到 999.99%）
--     · 相比 FLOAT/DOUBLE，DECIMAL 无浮点精度损失，适合后续数值计算与累乘操作
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `monthly_performance` (
    `id`         INT              NOT NULL AUTO_INCREMENT   COMMENT '主键',
    `year`       SMALLINT UNSIGNED NOT NULL                 COMMENT '年份，如 2000',
    `jan`        DECIMAL(20, 15)                            COMMENT '1 月收益率（底层小数）',
    `feb`        DECIMAL(20, 15)                            COMMENT '2 月收益率（底层小数）',
    `mar`        DECIMAL(20, 15)                            COMMENT '3 月收益率（底层小数）',
    `apr`        DECIMAL(20, 15)                            COMMENT '4 月收益率（底层小数）',
    `may`        DECIMAL(20, 15)                            COMMENT '5 月收益率（底层小数）',
    `jun`        DECIMAL(20, 15)                            COMMENT '6 月收益率（底层小数）',
    `jul`        DECIMAL(20, 15)                            COMMENT '7 月收益率（底层小数）',
    `aug`        DECIMAL(20, 15)                            COMMENT '8 月收益率（底层小数）',
    `sep`        DECIMAL(20, 15)                            COMMENT '9 月收益率（底层小数）',
    `oct`        DECIMAL(20, 15)                            COMMENT '10 月收益率（底层小数）',
    `nov`        DECIMAL(20, 15)                            COMMENT '11 月收益率（底层小数）',
    `dec`        DECIMAL(20, 15)                            COMMENT '12 月收益率（底层小数）',
    `annual`     DECIMAL(20, 15)                            COMMENT '年度收益率（底层小数）',
    `created_at` DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_classic_monthly_year`      (`year`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='月度业绩表（2000 年至今，每年动态新增）';

-- -------------------------------------------------------------
-- Classic Sheet 年度业绩表（动态增长）
--   对应 Excel Classic Sheet 的 "Annual performance since launch" 表格
--
--   百分比字段说明：
--   - 存储 Excel 底层小数值（pandas 读取百分比格式单元格的原始值）
--   - 例如：2.4% 存储为 0.024000000000000；-2.16% 存储为 -0.021611886537596
--   - 字段类型：DECIMAL(20, 15)
--     · 总位数 20，小数位 15，整数位 5（足够表示 -9.999... 到 9.999...，即 -999.99% 到 999.99%）
--     · 相比 FLOAT/DOUBLE，DECIMAL 无浮点精度损失，适合后续数值计算与累乘操作
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `annual_performance` (
    `id`         INT              NOT NULL AUTO_INCREMENT   COMMENT '主键',
    `year`       SMALLINT UNSIGNED NOT NULL                 COMMENT '年份，如 2000',
    `a_unit`     DECIMAL(20, 15)   COMMENT '收益率（底层小数）',
    `c_unit_hkd` DECIMAL(20, 15)   COMMENT '收益率（底层小数）',
    `hang_seng_index` DECIMAL(20, 15)   COMMENT '收益率（底层小数）',
    `hang_seng_total_return_index` DECIMAL(20, 15)   COMMENT '收益率（底层小数）',
    `HSI_MSCI_Golden_Dragon_B_unit` DECIMAL(20, 15)   COMMENT '收益率（底层小数）',
    `b_unit` DECIMAL(20, 15)   COMMENT '收益率（底层小数）',
    `c_unit` DECIMAL(20, 15)   COMMENT '收益率（底层小数）',
    `subscription_fee` DECIMAL(20, 15)   COMMENT '包年服务费（底层小数）',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_classic_monthly_year`      (`year`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='年度业绩表（2000 年至今，每年动态新增）';

-- -------------------------------------------------------------
-- 各时段业绩与基准对比表
--   对应 Excel Classic Sheet 的 "Performance As of" 区域（图示 Row 79-92）
--
--   行（period）共 12 种时间维度：
--     1m  / 3m  / 6m  / YTD
--     1y  / 3y  / 5y  / 10y
--     inception（成立以来）
--     inception_annualized（成立以来年化）
--     inception_volatility_annualized（成立以来年化波动率）
--     3y_volatility_annualized（3 年年化波动率）
--
--   列：A / B / C / Z 四类净值收益率，及各类对应的基准指数：
--     - 恒生指数（Hang Seng Index）
--     - HSI + MSCI 金龙指数（HSI + MSCI Golden Dragon）
--   注：Z 类（Class Z，成立于 2017-07-14）无单独恒生指数基准列
--
--   百分比字段均使用 DECIMAL(20, 15)，存储底层小数（如 4.0% → 0.040）
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `period_performance` (
    `id`          INT          NOT NULL AUTO_INCREMENT COMMENT '主键',
    `as_of_date`  VARCHAR(50)  NOT NULL               COMMENT '数据截止日期，如 2026-01-31',
    `period`      VARCHAR(50)  NOT NULL               COMMENT '时间段，枚举值：1m/3m/6m/YTD/1y/3y/5y/10y/inception/inception_annualized/inception_volatility_annualized/3y_volatility_annualized',

    -- ── A Unit ──────────────────────────────────────────────────
    `a_unit`                          DECIMAL(20, 15) COMMENT 'A 类净值收益率',
    `a_unit_hang_seng_index`          DECIMAL(20, 15) COMMENT 'A 类基准：恒生指数（Hang Seng Index for A Unit）',
    `a_unit_hsi_msci_golden_dragon`   DECIMAL(20, 15) COMMENT 'A 类基准：HSI + MSCI 金龙指数',

    -- ── B Unit ──────────────────────────────────────────────────
    `b_unit`                          DECIMAL(20, 15) COMMENT 'B 类净值收益率',
    `b_unit_hang_seng_index`          DECIMAL(20, 15) COMMENT 'B 类基准：恒生指数（Hang Seng Index for B Unit）',
    `b_unit_hsi_msci_golden_dragon`   DECIMAL(20, 15) COMMENT 'B 类基准：HSI + MSCI 金龙指数',

    -- ── C Unit ──────────────────────────────────────────────────
    `c_unit`                          DECIMAL(20, 15) COMMENT 'C 类净值收益率',
    `c_unit_hang_seng_index`          DECIMAL(20, 15) COMMENT 'C 类基准：恒生指数（Hang Seng Index for C Unit）',
    `c_unit_hsi_msci_golden_dragon`   DECIMAL(20, 15) COMMENT 'C 类基准：HSI + MSCI 金龙指数',

    -- ── Z Unit（Class Z，成立于 2017-07-14，仅有金龙指数基准）──
    `z_unit`                          DECIMAL(20, 15) COMMENT 'Z 类净值收益率',
    `z_unit_hsi_msci_golden_dragon`   DECIMAL(20, 15) COMMENT 'Z 类基准：HSI + MSCI 金龙指数',

    `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_period_performance_period_date` (`period`, `as_of_date`)
        COMMENT '同一时段同一截止日期只允许一条记录',
    INDEX `idx_period_performance_as_of_date` (`as_of_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='各时段业绩与基准对比表（Performance As of，含 A/B/C/Z 类及恒指/金龙指数基准）';

-- -------------------------------------------------------------
-- For Citi 各时段业绩与基准对比表
--   对应 Excel Classic Sheet 的 "For Citi - Performance As of" 区域（图示 Row 94-108）
--
--   与 period_performance 的核心差异：
--   1. 基准指数【共用】：Hang Seng Index 和 HSI+MSCI Golden Dragon 是所有类别共享的
--      一列，而非每个类别单独对应（如 a_unit_hang_seng_index、b_unit_hang_seng_index）
--   2. 新增 FEL（前收费 Front-End Load）调整后收益率列，对应 A / B / C 三类
--   3. 时间段维度包含：1m / 3m / 6m / YTD / 1y /
--      3y_annualized / 5y_annualized / 10y_annualized /
--      inception / inception_annualized /
--      volatility_annualized / 3y_volatility_annualized
--
--   百分比字段均使用 DECIMAL(20, 15)，存储底层小数（如 4.0% → 0.040）
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `period_performance_for_citi` (
    `id`          INT          NOT NULL AUTO_INCREMENT COMMENT '主键',
    `as_of_date`  VARCHAR(50)  NOT NULL               COMMENT '数据截止日期，如 2026-01-31',
    `period`      VARCHAR(50)  NOT NULL               COMMENT '时间段，枚举值：1m/3m/6m/YTD/1y/3y_annualized/5y_annualized/10y_annualized/inception/inception_annualized/volatility_annualized/3y_volatility_annualized',

    -- ── 共用基准指数（所有类别共享同一列）─────────────────────────────
    `hang_seng_index`        DECIMAL(20, 15) COMMENT '共用基准：恒生指数（Hang Seng Index）',
    `hsi_msci_golden_dragon` DECIMAL(20, 15) COMMENT '共用基准：HSI + MSCI 金龙指数（红色列）',

    -- ── A Unit ──────────────────────────────────────────────────
    `a_unit`                 DECIMAL(20, 15) COMMENT 'A 类净值收益率',
    `a_unit_fel_adjusted`    DECIMAL(20, 15) COMMENT 'A 类 FEL（前收费）调整后收益率',

    -- ── B Unit ──────────────────────────────────────────────────
    `b_unit`                 DECIMAL(20, 15) COMMENT 'B 类净值收益率',
    `b_unit_fel_adjusted`    DECIMAL(20, 15) COMMENT 'B 类 FEL（前收费）调整后收益率',

    -- ── C Unit ──────────────────────────────────────────────────
    `c_unit`                 DECIMAL(20, 15) COMMENT 'C 类净值收益率',
    `c_unit_fel_adjusted`    DECIMAL(20, 15) COMMENT 'C 类 FEL（前收费）调整后收益率',

    -- ── Z Unit（Class Z，成立于 2017-07-14，无 FEL 调整列）────────
    `z_unit`                 DECIMAL(20, 15) COMMENT 'Z 类净值收益率',

    `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_citi_period_date` (`period`, `as_of_date`)
        COMMENT '同一时段同一截止日期只允许一条记录',
    INDEX `idx_citi_period_performance_as_of_date` (`as_of_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='For Citi 各时段业绩与基准对比表（含共用基准指数及 FEL 调整后收益率）';

-- -------------------------------------------------------------
-- Classic A 历史月度数据表
--   对应 Excel 中历史时间序列数据（图示从 1993/4/27 起按月记录至今）
--
--   列分组：
--   ① 规模：AuM（基金净资产规模，美元）
--   ② 当期收益率（period return）：Classic A / 恒生指数 / HSI+MSCI 金龙指数
--      - 存储底层小数（如 2.52% → 0.0252）
--   ③ 成立以来累计收益率（cumulative since inception）：
--      Classic A / 恒生指数 / HSI+MSCI 金龙指数
--      - 数值较大（如 3335.5% → 33.355），仍使用 DECIMAL(20, 15)
--   ④ 年化波动率校验列（annualized volatility checking）：
--      3 列黄色高亮列，用于计算核对，对应 Classic A / 恒生指数 / 金龙指数
--
--   时间维度：按月（DATE 字段存每月数据点的日期，通常为月末）
--   唯一约束：每个日期只允许一条记录
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `classic_a_historical` (
    `id`           INT            NOT NULL AUTO_INCREMENT COMMENT '主键',
    `date`         DATE           NOT NULL               COMMENT '数据日期（月末），如 1993-04-27',

    -- ── ① 基金规模 ──────────────────────────────────────────────
    `aum`          DECIMAL(24, 2)                        COMMENT '基金净资产规模 AuM（美元），如 1,544,840,811.86',

    -- ── ② 当期收益率（Period Return，底层小数） ────────────────────
    `classic_a_return`              DECIMAL(20, 15)      COMMENT 'Classic A 当期收益率（底层小数，如 2.52% → 0.02520）',
    `hang_seng_index_return`        DECIMAL(20, 15)      COMMENT '恒生指数当期收益率（底层小数）',
    `hsi_msci_golden_dragon_return` DECIMAL(20, 15)      COMMENT 'HSI + MSCI 金龙指数当期收益率（底层小数）',

    -- ── ③ 成立以来累计收益率（Cumulative Since Inception，底层小数） ──
    -- 注：累计值可能极大（如 3335.5% 即 33.355），DECIMAL(20,15) 整数位仅 5 位，
    --     此处改用 DECIMAL(24, 10) 以兼容大数值
    `classic_a_cumulative`              DECIMAL(24, 10)  COMMENT 'Classic A 成立以来累计收益率（底层小数）',
    `hang_seng_index_cumulative`        DECIMAL(24, 10)  COMMENT '恒生指数成立以来累计收益率（底层小数）',
    `hsi_msci_golden_dragon_cumulative` DECIMAL(24, 10)  COMMENT 'HSI + MSCI 金龙指数成立以来累计收益率（底层小数）',

    -- ── ④ 年化波动率校验列（Annualized Volatility Checking，底层小数） ──
    `classic_a_ann_volatility`              DECIMAL(20, 15) COMMENT 'Classic A 年化波动率（校验列，底层小数）',
    `hang_seng_index_ann_volatility`        DECIMAL(20, 15) COMMENT '恒生指数年化波动率（校验列，底层小数）',
    `hsi_msci_golden_dragon_ann_volatility` DECIMAL(20, 15) COMMENT 'HSI + MSCI 金龙指数年化波动率（校验列，底层小数）',

    `created_at`  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_classic_a_historical_date` (`date`)
        COMMENT '每个日期只允许一条记录',
    INDEX `idx_classic_a_historical_date` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Classic A 历史月度数据表（1993-04 至今，含 AuM / 当期收益率 / 累计收益率 / 年化波动率）';

-- -------------------------------------------------------------
-- 股息分派记录表
--   对应 Excel 中的 Dividend Distribution 数据区域
--
--   字段说明：
--   - isin_code：基金 ISIN 代码（如 HK0000360898），12 位国际证券识别编号
--   - fund_code：基金简称/内部代号（如 VPAF）
--   - fund_name：基金全称（如 Classic Fund）
--   - class：基金类别代码（如 CMDisHKD / CMDisRMB / CMDisUSD / DMDisHKD / ...）
--     CM = 月派（Monthly），DM = 月派另一档次，Dis = Distribution（派息）
--   - currency：派息货币（HKD / CNY / USD），定长 3 字符
--   - ex_date_nav：除息日净值（NAV on Ex-Date），如 10.88
--   - dividend_per_unit：每单位派息金额（如 0.0194），与 currency 货币单位一致
--   - distribution_per_year：每年派息次数（12 = 每月派息，4 = 季派，1 = 年派）
--   - annualized_yield：年化收益率，底层小数（如 2.1% → 0.021）
--     计算公式：dividend_per_unit × distribution_per_year / ex_date_nav
--
--   唯一约束：同一基金类别（class）同一除息日只允许一条记录
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `dividend_distribution` (
    `id`                    INT          NOT NULL AUTO_INCREMENT COMMENT '主键',

    -- ── 日期 ──────────────────────────────────────────────────────
    `ex_date`               DATE         NOT NULL               COMMENT '除息日（Ex-Date），如 2026-01-30',
    `payment_date`          DATE                                COMMENT '派息日（Payment Date），如 2026-02-09',

    -- ── 基金标识 ───────────────────────────────────────────────────
    `isin_code`             VARCHAR(20)  NOT NULL               COMMENT 'ISIN 基金代码，如 HK0000360898',
    `fund_code`             VARCHAR(20)                         COMMENT '基金内部简称/代号，如 VPAF',
    `fund_name`             VARCHAR(100)                        COMMENT '基金全称，如 Classic Fund',
    `class`                 VARCHAR(50)  NOT NULL               COMMENT '基金类别代码，如 CMDisHKD / DMDisUSD',
    `currency`              CHAR(3)      NOT NULL               COMMENT '派息货币：HKD / CNY / USD',

    -- ── 派息数据 ───────────────────────────────────────────────────
    `ex_date_nav`           DECIMAL(12, 4)                      COMMENT '除息日单位净值（NAV on Ex-Date），如 10.88',
    `dividend_per_unit`     DECIMAL(16, 8)                      COMMENT '每单位派息金额，如 0.01940000（与 currency 单位一致）',
    `distribution_per_year` TINYINT UNSIGNED                    COMMENT '每年派息次数（12=月派 / 4=季派 / 1=年派）',
    `annualized_yield`      DECIMAL(20, 15)                     COMMENT '年化收益率（底层小数），如 2.1% → 0.02100000；计算公式：dividend_per_unit × distribution_per_year / ex_date_nav',

    `created_at`  DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`  DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_dividend_class_ex_date` (`class`, `ex_date`)
        COMMENT '同一基金类别同一除息日只允许一条记录',
    INDEX `idx_dividend_ex_date`    (`ex_date`),
    INDEX `idx_dividend_isin_code`  (`isin_code`),
    INDEX `idx_dividend_class`      (`class`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='股息分派记录表（含 ISIN 代码、除息日净值、每单位派息、年化收益率等）';
