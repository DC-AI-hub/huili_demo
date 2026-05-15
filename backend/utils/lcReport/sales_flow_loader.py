"""
SalesRptByProduct MySQL Loader（迁移自 huili/惠理基金）

将 sales_flow_pipeline 输出的 DataFrame 幂等写入 lc_report_sales_flow 表。
幂等键：(report_date, source_filename, fund_code)
"""
from __future__ import annotations

import logging
from typing import Any, Dict

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
import re
from collections import defaultdict

from .id_gen import gen_id
from .loader import _extract_fund_codes_from_group

logger = logging.getLogger(__name__)


REQUIRED_COLUMNS = {
    "report_date", "source_filename", "fund_code", "fund_name",
    "est_aum_usd_m",
    "daily_gross_sub_usd_k", "daily_gross_red_usd_k", "daily_net_flow_usd_k",
    "mtd_gross_sub_usd_k",   "mtd_gross_red_usd_k",   "mtd_net_flow_usd_k",
    "ytd_gross_sub_usd_k",   "ytd_gross_red_usd_k",   "ytd_net_flow_usd_k",
}


def _to_float(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def load_sales_flow_to_mysql(
    db: Session,
    parsed_df: pd.DataFrame,
    report_id: int,
    report_type: str,
    etl_run_id: str,
) -> Dict[str, int]:
    """
    幂等写入 lc_report_sales_flow。

    Args:
        db:          SQLAlchemy Session
        parsed_df:   run_sales_flow_pipeline 返回的 parsed_df
        report_id:   对应的 lc_report.report_id
        report_type: 报告类型（固定为 "SalesRptByProduct"）
        etl_run_id:  本次 ETL 批次 UUID

    Returns:
        {"sales_flow_rows_changed": int, "sales_flow_input_rows": int}
    """
    if parsed_df.empty:
        logger.warning("[sales_loader] parsed_df is empty, nothing to load.")
        raise ValueError("解析结果为空，没有提取到任何有效数据，请检查文件格式。")

    # 开启事务：先清理该报告的旧数据，防止重复上传时有脏数据残留
    db.execute(
        text("DELETE FROM lc_report_sales_flow WHERE report_id=:rid"),
        {"rid": report_id}
    )

    missing = REQUIRED_COLUMNS - set(parsed_df.columns)
    if missing:
        raise ValueError(f"[S2002] parsed_df missing required columns: {sorted(missing)}")

    changed = 0

    # 预先构建当前系统中最新的 Quartile_weekly 映射
    qw_mapping = {}
    latest_qw = db.execute(
        text("SELECT report_id FROM lc_report_qw_entity ORDER BY updated_at DESC LIMIT 1")
    ).fetchone()
    
    if latest_qw:
        qw_report_id = latest_qw[0]
        # 查询有 ISIN 的基金实体
        qw_rows = db.execute(
            text("""
                SELECT entity_name, isin, strategy_group, benchmark
                FROM lc_report_qw_entity 
                WHERE report_id = :rid AND isin IS NOT NULL AND isin != ''
                ORDER BY strategy_group, source_row_number
            """),
            {"rid": qw_report_id}
        ).fetchall()
        
        groups = defaultdict(list)
        for entity_name, isin, strategy_group, benchmark in qw_rows:
            if strategy_group:
                groups[strategy_group].append((entity_name, isin, benchmark))
                
        # 查询无 ISIN 的 benchmark 实体
        bm_rows = db.execute(
            text("""
                SELECT entity_name, strategy_group
                FROM lc_report_qw_entity
                WHERE report_id = :rid
                  AND (isin IS NULL OR isin = '')
                  AND entity_name NOT LIKE 'Peer Group%%'
                  AND entity_name NOT LIKE 'Benchmark%%'
                ORDER BY strategy_group, source_row_number
            """),
            {"rid": qw_report_id}
        ).fetchall()
        
        bm_by_group = defaultdict(list)
        for bm_name, sg in bm_rows:
            if sg:
                bm_by_group[sg].append(bm_name)
                
        for group_name, entities in groups.items():
            fund_codes = _extract_fund_codes_from_group(group_name)
            if not fund_codes:
                continue
                
            bm_list = bm_by_group.get(group_name, [])
            bm_entity_name = bm_list[0] if bm_list else None
            
            for i, fc in enumerate(fund_codes):
                if i >= len(entities):
                    break
                entity_name, isin, benchmark = entities[i]
                qw_mapping[fc] = {
                    "isin": isin,
                    "entity_name": entity_name,
                    "bm_entity_name": bm_entity_name,
                    "benchmark_name": benchmark
                }

    # 同步维护 lc_fund_code_map (新增 fund_code 和 fund_name)
    fund_map_upserts = 0
    for row in parsed_df.to_dict("records"):
        group_name = row.get("group_name", "")
        if group_name != "All Funds":
            continue
            
        fund_code = str(row["fund_code"])
        fund_name = row.get("fund_name")
        if not fund_code or fund_code.startswith("__"):
            continue
        isin = None
        qw_entity_name = None
        bm_entity_name = None
        benchmark_name = None

        if fund_code in qw_mapping:
            mapping = qw_mapping[fund_code]
            isin = mapping["isin"]
            qw_entity_name = mapping["entity_name"]
            bm_entity_name = mapping["bm_entity_name"]
            benchmark_name = mapping["benchmark_name"]

        db.execute(
            text("""
                INSERT INTO lc_fund_code_map 
                    (fund_code, fund_name, isin, entity_name, bm_entity_name, benchmark_name, is_new)
                VALUES 
                    (:fc, :fn, :isin, :en, :bmen, :bmn, 1)
                ON DUPLICATE KEY UPDATE 
                    fund_name      = COALESCE(NULLIF(fund_name, ''), NULLIF(VALUES(fund_name), '')),
                    isin           = COALESCE(NULLIF(isin, ''), NULLIF(VALUES(isin), '')),
                    entity_name    = COALESCE(NULLIF(entity_name, ''), NULLIF(VALUES(entity_name), '')),
                    bm_entity_name = COALESCE(NULLIF(bm_entity_name, ''), NULLIF(VALUES(bm_entity_name), '')),
                    benchmark_name = COALESCE(NULLIF(benchmark_name, ''), NULLIF(VALUES(benchmark_name), ''))
            """),
            {
                "fc": fund_code, 
                "fn": fund_name,
                "isin": isin,
                "en": qw_entity_name,
                "bmen": bm_entity_name,
                "bmn": benchmark_name
            }
        )
        fund_map_upserts += 1

    if fund_map_upserts > 0:
        logger.info(f"[sales_loader] synced {fund_map_upserts} records to lc_fund_code_map")

    for row in parsed_df.to_dict("records"):
        report_date    = str(row["report_date"])
        source_filename = str(row["source_filename"])
        fund_code      = str(row["fund_code"])

        # ---- 查是否已存在 ----
        existing = db.execute(
            text("""
                SELECT flow_id FROM lc_report_sales_flow
                WHERE report_id=:rid AND report_date=:rd AND source_filename=:sf AND fund_code=:fc
            """),
            {"rid": report_id, "rd": report_date, "sf": source_filename, "fc": fund_code},
        ).fetchone()

        if existing:
            db.execute(
                text("""
                    UPDATE lc_report_sales_flow SET
                        fund_name=:fn,
                        est_aum_usd_m=:aum,
                        daily_gross_sub_usd_k=:dgs, daily_gross_red_usd_k=:dgr, daily_net_flow_usd_k=:dnf,
                        mtd_gross_sub_usd_k=:mgs,   mtd_gross_red_usd_k=:mgr,   mtd_net_flow_usd_k=:mnf,
                        ytd_gross_sub_usd_k=:ygs,   ytd_gross_red_usd_k=:ygr,   ytd_net_flow_usd_k=:ynf,
                        source_row_number=:srn, etl_run_id=:eid, updated_at=NOW()
                    WHERE flow_id=:fid
                """),
                {
                    "fn":  row.get("fund_name"),
                    "aum": _to_float(row.get("est_aum_usd_m")),
                    "dgs": _to_float(row.get("daily_gross_sub_usd_k")),
                    "dgr": _to_float(row.get("daily_gross_red_usd_k")),
                    "dnf": _to_float(row.get("daily_net_flow_usd_k")),
                    "mgs": _to_float(row.get("mtd_gross_sub_usd_k")),
                    "mgr": _to_float(row.get("mtd_gross_red_usd_k")),
                    "mnf": _to_float(row.get("mtd_net_flow_usd_k")),
                    "ygs": _to_float(row.get("ytd_gross_sub_usd_k")),
                    "ygr": _to_float(row.get("ytd_gross_red_usd_k")),
                    "ynf": _to_float(row.get("ytd_net_flow_usd_k")),
                    "srn": row.get("source_row_number"),
                    "eid": etl_run_id,
                    "fid": existing[0],
                },
            )
        else:
            db.execute(
                text("""
                    INSERT INTO lc_report_sales_flow (
                        flow_id, report_id, report_type, report_date, source_filename,
                        fund_code, fund_name, est_aum_usd_m,
                        daily_gross_sub_usd_k, daily_gross_red_usd_k, daily_net_flow_usd_k,
                        mtd_gross_sub_usd_k,   mtd_gross_red_usd_k,   mtd_net_flow_usd_k,
                        ytd_gross_sub_usd_k,   ytd_gross_red_usd_k,   ytd_net_flow_usd_k,
                        source_row_number, etl_run_id
                    ) VALUES (
                        :fid, :rid, :rt, :rd, :sf,
                        :fc, :fn, :aum,
                        :dgs, :dgr, :dnf,
                        :mgs, :mgr, :mnf,
                        :ygs, :ygr, :ynf,
                        :srn, :eid
                    )
                """),
                {
                    "fid": gen_id(), "rid": report_id, "rt": report_type,
                    "rd": report_date, "sf": source_filename,
                    "fc": fund_code, "fn": row.get("fund_name"),
                    "aum": _to_float(row.get("est_aum_usd_m")),
                    "dgs": _to_float(row.get("daily_gross_sub_usd_k")),
                    "dgr": _to_float(row.get("daily_gross_red_usd_k")),
                    "dnf": _to_float(row.get("daily_net_flow_usd_k")),
                    "mgs": _to_float(row.get("mtd_gross_sub_usd_k")),
                    "mgr": _to_float(row.get("mtd_gross_red_usd_k")),
                    "mnf": _to_float(row.get("mtd_net_flow_usd_k")),
                    "ygs": _to_float(row.get("ytd_gross_sub_usd_k")),
                    "ygr": _to_float(row.get("ytd_gross_red_usd_k")),
                    "ynf": _to_float(row.get("ytd_net_flow_usd_k")),
                    "srn": row.get("source_row_number"),
                    "eid": etl_run_id,
                },
            )
        changed += 1

    db.commit()
    logger.info(
        f"[sales_loader] report_id={report_id} done: "
        f"input={len(parsed_df)}, changed={changed}"
    )
    return {
        "sales_flow_rows_changed": changed,
        "sales_flow_input_rows":   int(len(parsed_df)),
    }
