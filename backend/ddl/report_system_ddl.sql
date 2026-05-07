-- =============================================================
-- Report Delivery Tracking System DDL
-- Database: huili
-- =============================================================

USE `huili`;

-- 1. 报告配置表 (Report Configuration Table)
CREATE TABLE IF NOT EXISTS `report_config` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键',
  `frequency` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交付频率 (如 Weekly, Monthly, Ad-Hoc, Annually)',
  `report_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '报告类型 (如 Internal)',
  `report_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '报告名称 / High Level Tasks',
  `deliverable_time` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交付时间要求 (如 Every Friday afternoon, T+12, T+8, February)',
  `is_active` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否上线 (0:功能开发中, 1:已上线)',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `next_deliverable_time` datetime DEFAULT NULL COMMENT '下次交付时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报告配置表';

-- 2. 报告交付记录表 (Report Delivery Record Table)
-- 记录每一次特定报告日期的实际交付情况
CREATE TABLE IF NOT EXISTS `report_record` (
    `id`                 INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `config_id`          INT NOT NULL COMMENT '关联 report_config 表的主键',
    `report_date`        DATE NOT NULL COMMENT '报告对应的数据基准日期 (如月报对应的月底那一天)',
    `delivery_deadline`  DATETIME NOT NULL COMMENT '计算出的实际交付截止时间 (根据 deliverable_time 推算)',
    `status`             VARCHAR(50) NOT NULL DEFAULT 'Pending' COMMENT '交付状态 (Pending, Submitted, Overdue)',
    `submitted_at`       DATETIME COMMENT '实际提交时间',
    `report_link`        VARCHAR(500) COMMENT '生成的报告链接或存放路径',
    `created_at`         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='报告交付记录表';
