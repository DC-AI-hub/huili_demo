-- =============================================================
-- LC Report 模块 - 表结构定义
-- 数据库：MySQL 8.x
-- 命名规范：
--   · 所有表以 lc_report 开头
--   · 主键格式：YYYYMMDDHHmmss + 3位序号，如 20260430093012001
--   · 去除外键约束，由应用层维护引用完整性
-- =============================================================

-- =============================================================
-- 删表（按依赖逆序：子表在前，主表在后）
-- =============================================================
DROP TABLE IF EXISTS lc_report_fa_performance;
DROP TABLE IF EXISTS lc_report_fa_size_snapshot;
DROP TABLE IF EXISTS lc_report_fa_entity;
DROP TABLE IF EXISTS lc_report_fa_meta;
DROP TABLE IF EXISTS lc_report_sales_flow;
DROP TABLE IF EXISTS lc_report_qw_performance;
DROP TABLE IF EXISTS lc_report_qw_size_snapshot;
DROP TABLE IF EXISTS lc_report_qw_entity;
DROP TABLE IF EXISTS lc_report_qw_meta;
DROP TABLE IF EXISTS lc_report_file;
DROP TABLE IF EXISTS lc_report;

DROP TABLE IF EXISTS lc_other_accounts_config;
DROP TABLE IF EXISTS lc_fund_code_map;

-- -------------------------------------------------------------
-- 1. lc_report  报告主表
--    作用：记录每一期报告，以报告日期为核心
--    状态流转：PENDING（待完成）→ DONE（已完成）→ ARCHIVED（已归档）
--    归档规则：每周五 18:00 后自动将当期及之前未归档的报告置为 ARCHIVED
--    归档后只读：不允许上传、编辑，只允许查看
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lc_report (
    report_id       BIGINT          NOT NULL COMMENT '主键，格式：YYYYMMDDHHmmss + 3位序号',
    report_date     DATE            NOT NULL COMMENT '报告日期（如 2026-04-24）',
    status          VARCHAR(20)     NOT NULL DEFAULT 'PENDING'
                    COMMENT '报告状态：PENDING-待完成 / DONE-已完成 / ARCHIVED-已归档（只读）/ DELETED-已删除',
    analyst_note    LONGTEXT        NULL     COMMENT '分析师纪要（富文本）',
    archived_at     DATETIME        NULL     COMMENT '归档时间（由定时任务写入）',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    PRIMARY KEY (report_id),
    KEY idx_lc_report_date (report_date),
    KEY idx_lc_report_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='LC报告主表，每期报告一条记录，归档后只读';


-- -------------------------------------------------------------
-- 2. lc_report_file  报告文件关联表
--    作用：记录每期报告上传的原始数据文件及其解析状态
--    一期报告可关联多个文件（Quartile_weekly / SalesRptByProduct 等）
--    report_type 为文件类型标识，与子表 report_type 字段含义一致
--    数据状态流转：NOT_IMPORTED → PARSING → UNCHECKED → CHECKED
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lc_report_file (
    file_id         BIGINT          NOT NULL COMMENT '主键，格式：YYYYMMDDHHmmss + 3位序号',
    report_id       BIGINT          NOT NULL COMMENT '关联的报告ID（对应 lc_report.report_id）',
    report_type     VARCHAR(50)     NOT NULL COMMENT '报告类型标识：Quartile_weekly / SalesRptByProduct 等',
    original_name   VARCHAR(255)    NOT NULL COMMENT '原始文件名',
    stored_path     VARCHAR(500)    NOT NULL COMMENT '服务端存储路径（相对 backend/files/{date}/ 目录）',
    file_size       INT             NULL     COMMENT '文件大小（字节）',
    data_status     VARCHAR(20)     NOT NULL DEFAULT 'NOT_IMPORTED'
                    COMMENT '数据状态：NOT_IMPORTED-未导入 / PARSING-解析中 / UNCHECKED-未检查 / CHECKED-已检查',
    parse_result    TEXT            NULL     COMMENT '解析结果摘要（JSON格式，含行数/错误信息）',
    parse_error     TEXT            NULL     COMMENT '解析失败时的错误详情',
    etl_run_id      VARCHAR(64)     NULL     COMMENT 'ETL运行批次ID（UUID）',
    uploaded_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    PRIMARY KEY (file_id),
    UNIQUE KEY uq_lc_report_file (report_id, report_type),
    KEY idx_lc_report_file_report_id (report_id),
    KEY idx_lc_report_file_type (report_type),
    KEY idx_lc_report_file_status (data_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='报告文件关联表，记录文件上传及解析状态，每期报告每类型一条';


-- -------------------------------------------------------------
-- 3. lc_report_qw_meta  Quartile_weekly 报表元数据表
--    作用：记录 Excel 每张 Sheet 层面的宏观配置信息
--    关联键：(report_id, report_type) 对应 lc_report_file 的记录
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lc_report_qw_meta (
    meta_id         BIGINT          NOT NULL COMMENT '主键，格式：YYYYMMDDHHmmss + 3位序号',
    report_id       BIGINT          NOT NULL COMMENT '关联报告ID（对应 lc_report.report_id）',
    report_type     VARCHAR(50)     NOT NULL COMMENT '报告类型（如 Quartile_weekly）',
    report_set      VARCHAR(100)    NOT NULL COMMENT '报表集合名（通常为文件名去扩展名）',
    source_filename VARCHAR(255)    NOT NULL COMMENT '原始 Excel 文件名',
    sheet_name      VARCHAR(100)    NOT NULL COMMENT 'Sheet 页名称',
    report_name     VARCHAR(255)    NULL     COMMENT '报表名称（Sheet 首行文本）',
    currency        VARCHAR(10)     NULL     COMMENT '货币单位（如 USD / HKD / CNY）',
    grouped_by      VARCHAR(100)    NULL     COMMENT '分组方式（如 Strategy Group）',
    calculated_on   VARCHAR(50)     NOT NULL DEFAULT '' COMMENT 'Calculated on 日期时间（原始文本）',
    exported_on     VARCHAR(50)     NOT NULL DEFAULT '' COMMENT 'Exported on 日期时间（原始文本）',
    etl_run_id      VARCHAR(64)     NULL     COMMENT 'ETL运行批次ID',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    PRIMARY KEY (meta_id),
    UNIQUE KEY uq_lc_report_qw_meta (report_id, report_type, sheet_name),
    KEY idx_lc_report_qw_meta_report (report_id),
    KEY idx_lc_report_qw_meta_set (report_set)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='Quartile_weekly 报表元数据表，每张 Sheet 一条记录';


-- -------------------------------------------------------------
-- 4. lc_report_qw_entity  基金实体主数据表
--    作用：存储基金的主数据，包含 ISIN、评级、基准等信息
--    关联键：(report_id, report_type) 替代原 file_id
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lc_report_qw_entity (
    entity_id           BIGINT          NOT NULL COMMENT '主键，格式：YYYYMMDDHHmmss + 3位序号',
    report_id           BIGINT          NOT NULL COMMENT '关联报告ID（对应 lc_report.report_id）',
    report_type         VARCHAR(50)     NOT NULL COMMENT '报告类型（如 Quartile_weekly）',
    report_set          VARCHAR(100)    NOT NULL COMMENT '报表集合名',
    sheet_name          VARCHAR(100)    NOT NULL COMMENT '来源 Sheet 名',
    entity_name         VARCHAR(255)    NOT NULL COMMENT '基金/实体名称（Group/Investment 列）',
    entity_type         VARCHAR(20)     NOT NULL DEFAULT 'fund' COMMENT '实体类型：fund=基金, benchmark=基准, peer_avg=同组平均, peer_count=同组数量',
    isin                VARCHAR(20)     NOT NULL DEFAULT '' COMMENT 'ISIN 国际证券识别码（为空时存空字符串）',
    strategy_group      VARCHAR(100)    NULL     COMMENT '策略分组（如 China Equities）',
    morningstar_rating  VARCHAR(10)     NULL     COMMENT '晨星评级（如 ★★★★★）',
    morningstar_category VARCHAR(100)  NULL     COMMENT '晨星分类',
    benchmark           VARCHAR(255)   NULL     COMMENT '基准指数',
    currency            VARCHAR(10)    NULL     COMMENT '货币',
    source_row_number   INT            NULL     COMMENT '数据来源行号（溯源用）',
    etl_run_id          VARCHAR(64)    NULL     COMMENT 'ETL运行批次ID',
    created_at          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    PRIMARY KEY (entity_id),
    UNIQUE KEY uq_lc_report_qw_entity (report_id, report_type, sheet_name, entity_name, strategy_group),
    KEY idx_lc_report_qw_entity_report (report_id),
    KEY idx_lc_report_qw_entity_lookup (report_set, sheet_name, entity_name),
    KEY idx_lc_report_qw_entity_type (entity_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='Quartile_weekly 基金实体主数据表';


-- -------------------------------------------------------------
-- 5. lc_report_qw_size_snapshot  基金规模快照表
--    作用：存储基金不同日期的规模数据（daily / monthly 类型）
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lc_report_qw_size_snapshot (
    snapshot_id         BIGINT          NOT NULL COMMENT '主键，格式：YYYYMMDDHHmmss + 3位序号',
    entity_id           BIGINT          NOT NULL COMMENT '关联基金实体ID（对应 lc_report_qw_entity.entity_id）',
    report_id           BIGINT          NOT NULL COMMENT '关联报告ID',
    report_type         VARCHAR(50)     NOT NULL COMMENT '报告类型',
    size_type           VARCHAR(20)     NOT NULL COMMENT '规模类型：daily-日规模 / monthly-月规模',
    snapshot_date       VARCHAR(20)     NOT NULL COMMENT '快照日期（ISO格式，如 2026-04-15）',
    snapshot_value      VARCHAR(100)    NULL     COMMENT '规模数值（原单位 mn USD）或日期格式',
    source_column_name  VARCHAR(200)    NULL     COMMENT '来源列名（溯源用）',
    source_col_number   INT             NULL     COMMENT '数据来源列号（排序/溯源用）',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    PRIMARY KEY (snapshot_id),
    UNIQUE KEY uq_lc_report_qw_snapshot (entity_id, size_type, snapshot_date),
    KEY idx_lc_report_qw_snapshot_entity (entity_id),
    KEY idx_lc_report_qw_snapshot_report (report_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='基金规模快照表，按日期和类型存储规模数据';


-- -------------------------------------------------------------
-- 6. lc_report_qw_performance  表现与排名明细表
--    作用：将多维度组合结构（收益、排名、四分位）降维为行级指标
--    一行 = 一个基金 × 一个周期（YTD/1m/1y...）× 一个指标类型
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lc_report_qw_performance (
    perf_id             BIGINT          NOT NULL COMMENT '主键，格式：YYYYMMDDHHmmss + 3位序号',
    meta_id             BIGINT          NOT NULL COMMENT '关联元数据ID（对应 lc_report_qw_meta.meta_id）',
    entity_id           BIGINT          NOT NULL COMMENT '关联基金实体ID（对应 lc_report_qw_entity.entity_id）',
    report_id           BIGINT          NOT NULL COMMENT '关联报告ID',
    report_type         VARCHAR(50)     NOT NULL COMMENT '报告类型（如 Quartile_weekly）',
    report_set          VARCHAR(100)    NOT NULL COMMENT '报表集合名',
    sheet_name          VARCHAR(100)    NOT NULL COMMENT '来源 Sheet 名',
    period_type         VARCHAR(20)     NOT NULL COMMENT '周期类型（如 YTD / 1m / 1y / 3y / since_inception）',
    period_label        VARCHAR(30)     NOT NULL DEFAULT '' COMMENT '周期标签（列名前缀，如 YTD）',
    start_date          VARCHAR(20)     NOT NULL DEFAULT '' COMMENT '周期开始日期（ISO格式）',
    end_date            VARCHAR(20)     NOT NULL DEFAULT '' COMMENT '周期结束日期（ISO格式）',
    metric              VARCHAR(50)     NOT NULL COMMENT '指标类型（如 return_cum / return_ann）',
    value               DECIMAL(20,10)  NULL     COMMENT '收益值',
    peer_group_rank     DECIMAL(20,10)  NULL     COMMENT '同类排名',
    peer_group_quartile DECIMAL(20,10)  NULL     COMMENT '四分位数',
    source_row_number   INT             NULL     COMMENT '数据来源行号（溯源用）',
    source_column_name  VARCHAR(200)    NULL     COMMENT '数据来源列名（溯源用）',
    source_col_number   INT             NULL     COMMENT '数据来源列号（排序/溯源用）',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    PRIMARY KEY (perf_id),
    UNIQUE KEY uq_lc_report_qw_perf (entity_id, period_type, period_label, start_date, end_date, metric),
    KEY idx_lc_report_qw_perf_report (report_id),
    KEY idx_lc_report_qw_perf_entity (entity_id),
    KEY idx_lc_report_qw_perf_lookup (report_set, sheet_name, period_type, metric)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='基金表现与排名明细表，按周期和指标类型行级存储';


-- -------------------------------------------------------------
-- 7. lc_report_sales_flow  产品销售流量表
--    作用：记录 SalesRptByProduct 每日产品销售流量数据
--    关联键：(report_id, report_type) 对应 lc_report_file 的记录
--    幂等键：(report_date, source_filename, fund_code)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lc_report_sales_flow (
    flow_id                 BIGINT          NOT NULL COMMENT '主键，格式：YYYYMMDDHHmmss + 3位序号',
    report_id               BIGINT          NOT NULL COMMENT '关联报告ID（对应 lc_report.report_id）',
    report_type             VARCHAR(50)     NOT NULL DEFAULT 'SalesRptByProduct' COMMENT '报告类型',
    report_date             VARCHAR(20)     NOT NULL COMMENT '报表业务日期（从标题行 Report Date: 提取）',
    source_filename         VARCHAR(255)    NOT NULL COMMENT '原始文件名（溯源）',
    fund_code               VARCHAR(30)     NOT NULL COMMENT '产品代码（B列）',
    fund_name               VARCHAR(255)    NULL     COMMENT '产品全称（C列）',
    est_aum_usd_m           DECIMAL(30,10)  NULL     COMMENT '估计AUM（D列，单位：百万美元）',
    daily_gross_sub_usd_k   DECIMAL(30,10)  NULL     COMMENT '当日总申购（E列，单位：千美元）',
    daily_gross_red_usd_k   DECIMAL(30,10)  NULL     COMMENT '当日总赎回（F列，单位：千美元，通常为负）',
    daily_net_flow_usd_k    DECIMAL(30,10)  NULL     COMMENT '当日净流量（G列，单位：千美元）',
    mtd_gross_sub_usd_k     DECIMAL(30,10)  NULL     COMMENT '本月总申购（I列，单位：千美元）',
    mtd_gross_red_usd_k     DECIMAL(30,10)  NULL     COMMENT '本月总赎回（J列，单位：千美元）',
    mtd_net_flow_usd_k      DECIMAL(30,10)  NULL     COMMENT '本月净流量（K列，单位：千美元）',
    ytd_gross_sub_usd_k     DECIMAL(30,10)  NULL     COMMENT '年初总申购（M列，单位：千美元）',
    ytd_gross_red_usd_k     DECIMAL(30,10)  NULL     COMMENT '年初总赎回（N列，单位：千美元）',
    ytd_net_flow_usd_k      DECIMAL(30,10)  NULL     COMMENT '年初净流量（O列，单位：千美元）',
    source_row_number       INT             NULL     COMMENT '原始 Excel 行号（溯源）',
    etl_run_id              VARCHAR(64)     NULL     COMMENT 'ETL 运行批次ID（UUID）',
    created_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                            ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    PRIMARY KEY (flow_id),
    UNIQUE KEY uq_lc_report_sales_flow (report_id, report_date, source_filename, fund_code),
    KEY idx_lc_report_sales_flow_report (report_id),
    KEY idx_lc_report_sales_flow_date (report_date),
    KEY idx_lc_report_sales_flow_code (fund_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='SalesRptByProduct 产品销售流量日报，每个产品每日一条';


-- -------------------------------------------------------------
-- 8. lc_report_fa_meta  Fund Analysis 报表元数据表
--    作用：记录 Excel 每张 Sheet 层面的宏观配置信息
--    关联键：(report_id, report_type) 对应 lc_report_file 的记录
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lc_report_fa_meta (
    meta_id         BIGINT          NOT NULL COMMENT '主键，格式：YYYYMMDDHHmmss + 3位序号',
    report_id       BIGINT          NOT NULL COMMENT '关联报告ID（对应 lc_report.report_id）',
    report_type     VARCHAR(50)     NOT NULL DEFAULT 'FundAnalysis' COMMENT '报告类型',
    report_set      VARCHAR(100)    NOT NULL COMMENT '报表集合名（通常为文件名去扩展名）',
    source_filename VARCHAR(255)    NOT NULL COMMENT '原始 Excel 文件名',
    sheet_name      VARCHAR(100)    NOT NULL COMMENT 'Sheet 页名称',
    report_name     VARCHAR(255)    NULL     COMMENT '报表名称（Sheet 首行文本）',
    currency        VARCHAR(10)     NULL     COMMENT '货币单位（如 USD / HKD / CNY）',
    grouped_by      VARCHAR(100)    NULL     COMMENT '分组方式（如 Strategy Group）',
    calculated_on   VARCHAR(50)     NOT NULL DEFAULT '' COMMENT 'Calculated on 日期时间（原始文本）',
    exported_on     VARCHAR(50)     NOT NULL DEFAULT '' COMMENT 'Exported on 日期时间（原始文本）',
    etl_run_id      VARCHAR(64)     NULL     COMMENT 'ETL运行批次ID',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    PRIMARY KEY (meta_id),
    UNIQUE KEY uq_lc_report_fa_meta (report_id, report_type, sheet_name),
    KEY idx_lc_report_fa_meta_report (report_id),
    KEY idx_lc_report_fa_meta_set (report_set)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='FundAnalysis 报表元数据表，每张 Sheet 一条记录';


-- -------------------------------------------------------------
-- 9. lc_report_fa_entity  Fund Analysis 基金实体主数据表
--    作用：存储基金的主数据，包含 ISIN、评级、基准等信息
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lc_report_fa_entity (
    entity_id           BIGINT          NOT NULL COMMENT '主键，格式：YYYYMMDDHHmmss + 3位序号',
    report_id           BIGINT          NOT NULL COMMENT '关联报告ID（对应 lc_report.report_id）',
    report_type         VARCHAR(50)     NOT NULL DEFAULT 'FundAnalysis' COMMENT '报告类型',
    report_set          VARCHAR(100)    NOT NULL COMMENT '报表集合名',
    sheet_name          VARCHAR(100)    NOT NULL COMMENT '来源 Sheet 名',
    entity_name         VARCHAR(255)    NOT NULL COMMENT '基金/实体名称（Group/Investment 列）',
    entity_type         VARCHAR(20)     NOT NULL DEFAULT 'fund' COMMENT '实体类型：fund=基金, benchmark=基准, peer_avg=同组平均, peer_count=同组数量',
    isin                VARCHAR(20)     NOT NULL DEFAULT '' COMMENT 'ISIN 国际证券识别码（为空时存空字符串）',
    strategy_group      VARCHAR(1000)   NULL     COMMENT '策略分组（如 China Equities）',
    morningstar_rating  VARCHAR(10)     NULL     COMMENT '晨星评级（如 ★★★★★）',
    morningstar_category VARCHAR(100)  NULL     COMMENT '晨星分类',
    benchmark           VARCHAR(255)   NULL     COMMENT '基准指数',
    currency            VARCHAR(10)    NULL     COMMENT '货币',
    source_row_number   INT            NULL     COMMENT '数据来源行号（溯源用）',
    etl_run_id          VARCHAR(64)    NULL     COMMENT 'ETL运行批次ID',
    created_at          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    PRIMARY KEY (entity_id),
    KEY idx_lc_report_fa_entity_report (report_id),
    KEY idx_lc_report_fa_entity_lookup (report_set, sheet_name, entity_name),
    KEY idx_lc_report_fa_entity_type (entity_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='FundAnalysis 基金实体主数据表';


-- -------------------------------------------------------------
-- 10. lc_report_fa_size_snapshot  Fund Analysis 基金规模快照表
--    作用：存储基金不同日期的规模数据（daily / monthly 类型）
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lc_report_fa_size_snapshot (
    snapshot_id         BIGINT          NOT NULL COMMENT '主键，格式：YYYYMMDDHHmmss + 3位序号',
    entity_id           BIGINT          NOT NULL COMMENT '关联基金实体ID（对应 lc_report_fa_entity.entity_id）',
    report_id           BIGINT          NOT NULL COMMENT '关联报告ID',
    report_type         VARCHAR(50)     NOT NULL DEFAULT 'FundAnalysis' COMMENT '报告类型',
    size_type           VARCHAR(20)     NOT NULL COMMENT '规模类型：daily-日规模 / monthly-月规模',
    snapshot_date       VARCHAR(20)     NOT NULL COMMENT '快照日期（ISO格式，如 2026-04-15）',
    snapshot_value      VARCHAR(100)    NULL     COMMENT '规模数值（原单位 mn USD）或日期格式',
    source_column_name  VARCHAR(200)    NULL     COMMENT '来源列名（溯源用）',
    source_col_number   INT             NULL     COMMENT '数据来源列号（排序/溯源用）',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    PRIMARY KEY (snapshot_id),
    UNIQUE KEY uq_lc_report_fa_snapshot (entity_id, size_type, snapshot_date),
    KEY idx_lc_report_fa_snapshot_entity (entity_id),
    KEY idx_lc_report_fa_snapshot_report (report_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='FundAnalysis 基金规模快照表，按日期和类型存储规模数据';


-- -------------------------------------------------------------
-- 11. lc_report_fa_performance  Fund Analysis 表现与排名明细表
--    作用：将多维度组合结构（收益、排名、四分位）降维为行级指标
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lc_report_fa_performance (
    perf_id             BIGINT          NOT NULL COMMENT '主键，格式：YYYYMMDDHHmmss + 3位序号',
    meta_id             BIGINT          NOT NULL COMMENT '关联元数据ID（对应 lc_report_fa_meta.meta_id）',
    entity_id           BIGINT          NOT NULL COMMENT '关联基金实体ID（对应 lc_report_fa_entity.entity_id）',
    report_id           BIGINT          NOT NULL COMMENT '关联报告ID',
    report_type         VARCHAR(50)     NOT NULL DEFAULT 'FundAnalysis' COMMENT '报告类型',
    report_set          VARCHAR(100)    NOT NULL COMMENT '报表集合名',
    sheet_name          VARCHAR(100)    NOT NULL COMMENT '来源 Sheet 名',
    period_type         VARCHAR(100)     NOT NULL COMMENT '周期类型（如 YTD / 1m / 1y / 3y / since_inception）',
    period_label        VARCHAR(100)     NOT NULL DEFAULT '' COMMENT '周期标签（列名前缀，如 YTD）',
    start_date          VARCHAR(20)     NOT NULL DEFAULT '' COMMENT '周期开始日期（ISO格式）',
    end_date            VARCHAR(20)     NOT NULL DEFAULT '' COMMENT '周期结束日期（ISO格式）',
    metric              VARCHAR(50)     NOT NULL COMMENT '指标类型（如 return_cum / return_ann）',
    value               DECIMAL(20,10)  NULL     COMMENT '收益值',
    peer_group_rank     DECIMAL(20,10)  NULL     COMMENT '同类排名',
    peer_group_quartile DECIMAL(20,10)  NULL     COMMENT '四分位数',
    source_row_number   INT             NULL     COMMENT '数据来源行号（溯源用）',
    source_column_name  VARCHAR(200)    NULL     COMMENT '数据来源列名（溯源用）',
    source_col_number   INT             NULL     COMMENT '数据来源列号（排序/溯源用）',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    PRIMARY KEY (perf_id),
    KEY idx_lc_report_fa_perf_report (report_id),
    KEY idx_lc_report_fa_perf_entity (entity_id),
    KEY idx_lc_report_fa_perf_lookup (report_set, sheet_name, period_type, metric)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='FundAnalysis 基金表现与排名明细表，按周期和指标类型行级存储';
  

-- -------------------------------------------------------------
-- A. lc_fund_code_map  基金代码映射表（自动/手工维护）
-- -------------------------------------------------------------
CREATE TABLE lc_fund_code_map (
    -- 基础数据
    fund_code       VARCHAR(50)   NOT NULL COMMENT '基金短代码（来自 SalesReport B列，如 VPHY）',
    fund_name       VARCHAR(255)  NULL     COMMENT '基金全称（来自 SalesReport C列）',
    isin            VARCHAR(20)   NULL     COMMENT 'ISIN（来自 Quartile_weekly 文件解析）',
    is_fund         TINYINT       NOT NULL DEFAULT 0 COMMENT '标记是否是Fund，默认是0-否',
    is_new          TINYINT       NOT NULL DEFAULT 0 COMMENT '标记是否新增，默认0',
    is_diff         TINYINT       NOT NULL DEFAULT 0 COMMENT '0表示无差异，大于0表示有差异：1表示entity_name有差异， 2表示bm_entity_name有差异， 3表示两个都有差异',
    
    -- 配置Performance
    benchmark_name  VARCHAR(255)  NULL     COMMENT 'Benchmark显示名称（对应Excel Performance Sheet D列，手工维护）',
    inception_date  DATE          NULL     COMMENT '基金成立日期（来自 QW 文件 inception 列头 row 8，用于Performance收益计算，手工维护）',
    
    -- 配置Morningstar AUM
    entity_name     VARCHAR(255)  NULL     COMMENT 'Morningstar 长名称（对应 Morningstar AUM 中 MS_VP Open End Fund 分组的 entity_name）',
    bm_entity_name  VARCHAR(255)  NULL     COMMENT 'QW数据中BM的实际entity_name（对应 Morningstar AUM 中 BM 分组的 entity_name，用于JOIN匹配benchmark收益行，手工维护）',
    
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (fund_code),
    KEY idx_entity_name (entity_name(64))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='fund_code(短) <-> 各维度自动映射表';


-- -------------------------------------------------------------
-- B. lc_other_accounts_config  其他账户配置表
--    作用：配置 HKSFC 报告底部 "Other Accounts" 区域的 2-3 个命名账户
--    说明：仅需配置 1-2 行（Gold ETF / Real Estate）
--          lc_report_sales_flow.fund_code 精确匹配
-- -------------------------------------------------------------
CREATE TABLE lc_other_accounts_config (
    id            INT           NOT NULL AUTO_INCREMENT COMMENT '主键',
    account_name  VARCHAR(100)  NOT NULL COMMENT '展示名称（如 Gold ETF、Real Estate）',
    fund_code     VARCHAR(50)   NOT NULL COMMENT '与 lc_report_sales_flow.fund_code 精确匹配',
    display_order INT           NOT NULL DEFAULT 0 COMMENT '展示顺序',
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_account_name (account_name),
    KEY idx_fund_code (fund_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='Other Accounts 展示名称 → fund_code 配置表（仅需 2-3 行，实物替代 fund_name 匹配）';



-- =============================================================
-- 表关系说明（无外键约束，应用层维护）
--
--   lc_report (report_id)
--       └── lc_report_file (report_id, report_type)          ← 文件状态管理
--              ├── Quartile_weekly 分支：
--              │     └── lc_report_qw_meta (report_id, report_type, sheet_name)
--              │               └── lc_report_qw_entity (entity_id)
--              │                       ├── lc_report_qw_size_snapshot
--              │                       └── lc_report_qw_performance
--              ├── SalesRptByProduct 分支：
--              │     └── lc_report_sales_flow (report_id, report_type)
--              └── FundAnalysis 分支：
--                    └── lc_report_fa_meta (report_id, report_type)  ← 多快照共存
--                              └── lc_report_fa_performance (meta_id) ← 按快照幂等
--
-- 状态流转：
--   lc_report.status:           PENDING → DONE → ARCHIVED（周五18:00自动归档）
--   lc_report_file.data_status: NOT_IMPORTED → PARSING → UNCHECKED → CHECKED
-- =============================================================
