"""
MySQL Loader — 适配 MySQL 的幂等入库执行器（优化版）

表名已更新为 lc_report_qw_* 系列：
  lc_report_qw_meta / lc_report_qw_entity / lc_report_qw_size_snapshot / lc_report_qw_performance

子表关联键：(report_id, report_type) 替代原 file_id
"""
from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from .column_mapper import map_column
from .id_gen import gen_id

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _to_float(value: object) -> Optional[float]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text_val = str(value).strip()
    if text_val == "":
        return None
    try:
        return float(text_val)
    except ValueError:
        return None


def _to_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value)


def _is_data_row(first_cell: object) -> bool:
    """判断是否为需要入库的数据行。
    仅跳过首列为空的行，其余全部入库（基金、Benchmark、Peer Group Average/Count）。
    原始数据完整保留，后续视图/SQL 按需筛选。
    """
    t = str(first_cell).strip() if first_cell is not None else ""
    return t != ""


def _normalize_bm_entity_name(entity_name: str) -> str:
    """将 VP_PG 表中的 'Benchmark N: XXX' 格式清洗为纯 BM 名称 'XXX'。
    例：'Benchmark 1: HSI HKD TR + MSCI G. Dragon (20171001)'
      → 'HSI HKD TR + MSCI G. Dragon (20171001)'
    非 Benchmark 行原样返回。
    """
    if not entity_name.startswith("Benchmark"):
        return entity_name
    m = re.match(r'^Benchmark\s*\d*\s*:\s*', entity_name)
    if m:
        return entity_name[m.end():].strip()
    return entity_name


def _detect_entity_type(raw_entity_name: str) -> str:
    """根据原始 entity_name 判断实体类型。
    返回值：'fund' | 'benchmark' | 'peer_avg' | 'peer_count'
    """
    if raw_entity_name == "Peer Group Average":
        return "peer_avg"
    if raw_entity_name == "Peer Group Count":
        return "peer_count"
    if raw_entity_name.startswith("Benchmark"):
        return "benchmark"
    return "fund"


def _extract_fund_codes_from_group(group_name: str) -> List[str]:
    """
    从 peer group 名称中提取 fund_code 列表。
    例：
      'Grt Chn Eq_HKSFC (VPAF & CG)' → ['VPAF', 'CG']
      'Asia ex Japan Eq_HKSFC (VPHY)'  → ['VPHY']
      'China Equity_HKSFC (VPCA & VPMF)' → ['VPCA', 'VPMF']
    """
    match = re.search(r'\(([^)]+)\)', group_name)
    if not match:
        return []
    content = match.group(1)
    return [c.strip() for c in re.split(r'[&,]', content) if c.strip()]


def _upsert_fund_code_map(
    db: Session,
    report_id: int,
    inception_date_map: Optional[Dict[str, str]] = None,
) -> int:
    """
    上传 Quartile_weekly 后，从 lc_report_qw_entity 自动推导
    fund_code -> entity_name -> ISIN 映射并写入 lc_fund_code_map。

    逻辑：
      1. 取当次 report_id 下所有 entity 行（有 ISIN），按 strategy_group + source_row_number 排序
      2. 对每个 strategy_group，提取括号内的 fund_code 列表
      3. 按照 fund_code 顺序 = 实体行顺序 进行一一映射
      4. inception_date 可选中，如提供 inception_date_map 则写入
      5. UPSERT 到 lc_fund_code_map（只要 fund_code 不为空）
      6. 自动查找同 peer group 内无 ISIN 的 BM 实体，填充 bm_entity_name
    """
    inception_date_map = inception_date_map or {}

    # 查询有 ISIN 的基金实体（fund 行）
    rows = db.execute(
        text("""
            SELECT entity_name, isin, strategy_group, source_row_number
            FROM lc_report_qw_entity
            WHERE report_id = :rid AND isin IS NOT NULL AND isin != ''
            ORDER BY strategy_group, source_row_number
        """),
        {"rid": report_id},
    ).fetchall()

    # 按 strategy_group 分组 fund 实体
    groups: Dict[str, List] = defaultdict(list)
    for entity_name, isin, strategy_group, row_num in rows:
        if strategy_group:
            groups[strategy_group].append((entity_name, isin))

    # 查询无 ISIN 的 benchmark 实体（排除 Peer Group 汇总行）
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
        {"rid": report_id},
    ).fetchall()

    # 按 strategy_group 分组 BM 实体
    bm_by_group: Dict[str, List[str]] = defaultdict(list)
    for bm_name, sg in bm_rows:
        if sg:
            bm_by_group[sg].append(bm_name)

    upserted = 0
    for group_name, entities in groups.items():
        fund_codes = _extract_fund_codes_from_group(group_name)
        if not fund_codes:
            continue
        # 取同 peer group 内的第一个 BM 实体名称
        bm_list = bm_by_group.get(group_name, [])
        bm_entity_name = bm_list[0] if bm_list else None

        for i, fund_code in enumerate(fund_codes):
            if i >= len(entities):
                break
            entity_name, isin = entities[i]
            inc_date = inception_date_map.get(fund_code)  # None if not found
            # Note: benchmark_name 字段由手工配置（对应 Excel Performance Sheet D列），
            # ETL 上传时不覆盖该字段，仅更新 entity_name/isin/inception_date/bm_entity_name
            db.execute(
                text("""
                    INSERT INTO lc_fund_code_map (fund_code, entity_name, isin, inception_date, bm_entity_name)
                    VALUES (:fc, :en, :isin, :inc, :bmen)
                    ON DUPLICATE KEY UPDATE
                        entity_name    = VALUES(entity_name),
                        isin           = VALUES(isin),
                        inception_date = COALESCE(VALUES(inception_date), inception_date),
                        bm_entity_name = COALESCE(VALUES(bm_entity_name), bm_entity_name),
                        updated_at     = NOW()
                """),
                {"fc": fund_code, "en": entity_name, "isin": isin or "",
                 "inc": inc_date, "bmen": bm_entity_name},
            )
            upserted += 1
            logger.debug(
                f"[loader] fund_code_map: {fund_code} -> {entity_name} ({isin})"
                f" inception={inc_date} bm_entity={bm_entity_name}"
            )

    if upserted:
        db.commit()
        logger.info(f"[loader] lc_fund_code_map upserted {upserted} rows from report_id={report_id}")
    return upserted


def _first_column_name(df: pd.DataFrame) -> str:
    for column in df.columns:
        if "group/investment" in str(column).lower():
            return column
    raise ValueError("[L2001] missing Group/Investment-like column in parsed DataFrame")


# ---------------------------------------------------------------------------
# 各表幂等写入（lc_report_qw_* 系列）
# ---------------------------------------------------------------------------

def _upsert_report_meta(
    db: Session,
    report_id: int,
    report_type: str,
    row: Dict[str, Any],
) -> int:
    """
    写入 lc_report_qw_meta。
    幂等键：(report_id, report_type, sheet_name)
    """
    existing = db.execute(
        text("""
            SELECT meta_id FROM lc_report_qw_meta
            WHERE report_id=:rid AND report_type=:rt AND sheet_name=:sn
        """),
        {"rid": report_id, "rt": report_type, "sn": row["sheet_name"]},
    ).fetchone()

    if existing:
        mid = existing[0]
        db.execute(
            text("""
                UPDATE lc_report_qw_meta SET
                    report_set=:rs, source_filename=:sf, report_name=:rn,
                    currency=:cur, grouped_by=:gb, calculated_on=:co,
                    exported_on=:eo, etl_run_id=:eid, updated_at=NOW()
                WHERE meta_id=:mid
            """),
            {
                "rs": row["report_set"], "sf": row["source_filename"],
                "rn": row.get("report_name"), "cur": row.get("currency"),
                "gb": row.get("grouped_by"),
                "co": _to_text(row.get("calculated_on")),
                "eo": _to_text(row.get("exported_on")),
                "eid": row.get("etl_run_id"), "mid": mid,
            },
        )
        return mid
    else:
        mid = gen_id()
        db.execute(
            text("""
                INSERT INTO lc_report_qw_meta
                    (meta_id, report_id, report_type, report_set, source_filename, sheet_name,
                     report_name, currency, grouped_by, calculated_on, exported_on, etl_run_id)
                VALUES
                    (:mid, :rid, :rt, :rs, :sf, :sn, :rn, :cur, :gb, :co, :eo, :eid)
            """),
            {
                "mid": mid, "rid": report_id, "rt": report_type,
                "rs": row["report_set"], "sf": row["source_filename"],
                "sn": row["sheet_name"], "rn": row.get("report_name"),
                "cur": row.get("currency"), "gb": row.get("grouped_by"),
                "co": _to_text(row.get("calculated_on")),
                "eo": _to_text(row.get("exported_on")),
                "eid": row.get("etl_run_id"),
            },
        )
        return mid


def _upsert_entity(
    db: Session,
    report_id: int,
    report_type: str,
    payload: Dict[str, Any],
) -> int:
    """
    写入 lc_report_qw_entity。
    幂等键：(report_id, report_type, sheet_name, entity_name, isin)
    """
    isin = _to_text(payload.get("isin"))
    existing = db.execute(
        text("""
            SELECT entity_id FROM lc_report_qw_entity
            WHERE report_id=:rid AND report_type=:rt
              AND sheet_name=:sn AND entity_name=:en
              AND (strategy_group=:sg OR (strategy_group IS NULL AND :sg IS NULL))
        """),
        {"rid": report_id, "rt": report_type,
         "sn": payload["sheet_name"], "en": payload["entity_name"],
         "sg": payload.get("strategy_group")},
    ).fetchone()

    if existing:
        eid = existing[0]
        db.execute(
            text("""
                UPDATE lc_report_qw_entity SET
                    entity_type=:et, isin=:isin,
                    strategy_group=:sg, morningstar_rating=:mr, morningstar_category=:mc,
                    benchmark=:bm, currency=:cur, source_row_number=:srn,
                    etl_run_id=:etl, updated_at=NOW()
                WHERE entity_id=:eid
            """),
            {
                "et": payload.get("entity_type", "fund"), "isin": isin,
                "sg": payload.get("strategy_group"), "mr": payload.get("morningstar_rating"),
                "mc": payload.get("morningstar_category"), "bm": payload.get("benchmark"),
                "cur": payload.get("currency"), "srn": payload.get("source_row_number"),
                "etl": payload.get("etl_run_id"), "eid": eid,
            },
        )
        return eid
    else:
        eid = gen_id()
        db.execute(
            text("""
                INSERT INTO lc_report_qw_entity
                    (entity_id, report_id, report_type, report_set, sheet_name, entity_name,
                     entity_type, isin, strategy_group, morningstar_rating, morningstar_category,
                     benchmark, currency, source_row_number, etl_run_id)
                VALUES
                    (:eid, :rid, :rt, :rs, :sn, :en, :et, :isin, :sg, :mr, :mc, :bm, :cur, :srn, :etl)
            """),
            {
                "eid": eid, "rid": report_id, "rt": report_type,
                "rs": payload["report_set"], "sn": payload["sheet_name"],
                "en": payload["entity_name"], "et": payload.get("entity_type", "fund"),
                "isin": isin,
                "sg": payload.get("strategy_group"), "mr": payload.get("morningstar_rating"),
                "mc": payload.get("morningstar_category"), "bm": payload.get("benchmark"),
                "cur": payload.get("currency"), "srn": payload.get("source_row_number"),
                "etl": payload.get("etl_run_id"),
            },
        )
        return eid


def _upsert_size_snapshots(
    db: Session,
    entity_id: int,
    report_id: int,
    report_type: str,
    row_data: Dict[str, Any],
    mapped_columns: Dict[str, Any],
) -> None:
    """写入 lc_report_qw_size_snapshot。幂等键：(entity_id, size_type, snapshot_date)"""
    for column_name, mapping in mapped_columns.items():
        if mapping.size_type is None or mapping.end_date is None:
            continue
        snapshot_value = _to_float(row_data.get(column_name))
        if snapshot_value is None:
            continue

        existing = db.execute(
            text("""
                SELECT snapshot_id FROM lc_report_qw_size_snapshot
                WHERE entity_id=:eid AND size_type=:st AND snapshot_date=:sd
            """),
            {"eid": entity_id, "st": mapping.size_type, "sd": mapping.end_date},
        ).fetchone()

        if existing:
            db.execute(
                text("""
                    UPDATE lc_report_qw_size_snapshot SET
                        snapshot_value=:sv, source_column_name=:scn, updated_at=NOW()
                    WHERE snapshot_id=:sid
                """),
                {"sv": snapshot_value, "scn": column_name, "sid": existing[0]},
            )
        else:
            db.execute(
                text("""
                    INSERT INTO lc_report_qw_size_snapshot
                        (snapshot_id, entity_id, report_id, report_type,
                         size_type, snapshot_date, snapshot_value, source_column_name)
                    VALUES (:sid, :eid, :rid, :rt, :st, :sd, :sv, :scn)
                """),
                {
                    "sid": gen_id(), "eid": entity_id,
                    "rid": report_id, "rt": report_type,
                    "st": mapping.size_type, "sd": mapping.end_date,
                    "sv": snapshot_value, "scn": column_name,
                },
            )


def _upsert_performance(
    db: Session,
    meta_id: int,
    entity_id: int,
    report_id: int,
    report_type: str,
    row_data: Dict[str, Any],
    mapped_columns: Dict[str, Any],
) -> int:
    """
    写入 lc_report_qw_performance。
    幂等键：(entity_id, period_type, period_label, start_date, end_date, metric)
    """
    grouped: Dict[str, Dict[str, Any]] = defaultdict(dict)

    for column_name, mapping in mapped_columns.items():
        if mapping.period_type is None:
            continue
        if mapping.value_role not in {"value", "peer_group_rank", "peer_group_quartile"}:
            continue
        pt = mapping.period_type
        grouped[pt].setdefault("period_label", mapping.period_label)
        grouped[pt].setdefault("start_date", mapping.start_date)
        grouped[pt].setdefault("end_date", mapping.end_date)
        grouped[pt].setdefault("metrics", {})
        grouped[pt].setdefault("peer_group_rank", None)
        grouped[pt].setdefault("peer_group_quartile", None)

        if mapping.value_role == "value":
            grouped[pt]["metrics"][mapping.metric_kind] = (
                _to_float(row_data.get(column_name)), column_name
            )
        elif mapping.value_role == "peer_group_rank":
            grouped[pt]["peer_group_rank"] = _to_float(row_data.get(column_name))
        elif mapping.value_role == "peer_group_quartile":
            grouped[pt]["peer_group_quartile"] = _to_float(row_data.get(column_name))

    changed = 0
    for period_type, payload in grouped.items():
        for metric, metric_info in payload["metrics"].items():
            if metric is None:
                continue
            metric_value, source_column_name = metric_info
            if metric_value is None:
                continue

            period_label = payload["period_label"] or ""
            start_date   = payload["start_date"] or ""
            end_date     = payload["end_date"] or ""

            existing = db.execute(
                text("""
                    SELECT perf_id FROM lc_report_qw_performance
                    WHERE entity_id=:eid AND period_type=:pt AND period_label=:pl
                      AND start_date=:sd AND end_date=:ed AND metric=:m
                """),
                {"eid": entity_id, "pt": period_type, "pl": period_label,
                 "sd": start_date, "ed": end_date, "m": metric},
            ).fetchone()

            if existing:
                db.execute(
                    text("""
                        UPDATE lc_report_qw_performance SET
                            value=:val, peer_group_rank=:pgr, peer_group_quartile=:pgq,
                            source_row_number=:srn, source_column_name=:scn, updated_at=NOW()
                        WHERE perf_id=:pid
                    """),
                    {
                        "val": metric_value,
                        "pgr": payload["peer_group_rank"],
                        "pgq": payload["peer_group_quartile"],
                        "srn": int(row_data["row_number"]),
                        "scn": source_column_name,
                        "pid": existing[0],
                    },
                )
            else:
                db.execute(
                    text("""
                        INSERT INTO lc_report_qw_performance
                            (perf_id, meta_id, entity_id, report_id, report_type,
                             report_set, sheet_name, period_type, period_label,
                             start_date, end_date, metric, value,
                             peer_group_rank, peer_group_quartile,
                             source_row_number, source_column_name)
                        VALUES
                            (:pid, :mid, :eid, :rid, :rt,
                             :rs, :sn, :pt, :pl,
                             :sd, :ed, :m, :val,
                             :pgr, :pgq, :srn, :scn)
                    """),
                    {
                        "pid": gen_id(), "mid": meta_id, "eid": entity_id,
                        "rid": report_id, "rt": report_type,
                        "rs": row_data["report_set"], "sn": row_data["row_source_sheet"],
                        "pt": period_type, "pl": period_label,
                        "sd": start_date, "ed": end_date, "m": metric,
                        "val": metric_value,
                        "pgr": payload["peer_group_rank"],
                        "pgq": payload["peer_group_quartile"],
                        "srn": int(row_data["row_number"]),
                        "scn": source_column_name,
                    },
                )
            changed += 1

    return changed


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def load_to_mysql(
    db: Session,
    parsed_df: pd.DataFrame,
    meta_records: List[Dict[str, Any]],
    report_id: int,
    report_type: str,
    inception_date_map: Optional[Dict[str, str]] = None,
) -> Dict[str, int]:
    """
    阶段二主入口：将 pipeline 输出的 DataFrame 幂等写入 MySQL。

    Args:
        db:                 SQLAlchemy Session
        parsed_df:          run_pipeline 返回的 parsed_df
        meta_records:       run_pipeline 返回的 meta_records
        report_id:          对应的 lc_report.report_id
        report_type:        报告类型（如 Quartile_weekly）
        inception_date_map: {fund_code: 'YYYY-MM-DD'}，来自 pipeline.extract_qw_inception_dates()

    Returns:
        统计字典 {report_meta_rows, entity_rows_processed, performance_rows_changed, fund_map_rows}
    """
    if parsed_df.empty:
        logger.warning("[loader] parsed_df is empty, nothing to load.")
        return {"report_meta_rows": 0, "entity_rows_processed": 0, "performance_rows_changed": 0}

    # 开启事务：先清理该报告的旧数据，防止重复上传时有脏数据残留
    db.execute(text("DELETE FROM lc_report_qw_performance WHERE report_id=:rid"), {"rid": report_id})
    db.execute(text("DELETE FROM lc_report_qw_size_snapshot WHERE report_id=:rid"), {"rid": report_id})
    db.execute(text("DELETE FROM lc_report_qw_entity WHERE report_id=:rid"), {"rid": report_id})
    db.execute(text("DELETE FROM lc_report_qw_meta WHERE report_id=:rid"), {"rid": report_id})

    first_col = _first_column_name(parsed_df)
    mapped_columns = {c: map_column(c) for c in parsed_df.columns}

    # --- 写入元数据，建立 (report_set, sheet_name) -> meta_id 映射 ---
    meta_key_to_id: Dict[tuple, int] = {}
    for record in meta_records:
        mid = _upsert_report_meta(db, report_id, report_type, record)
        meta_key_to_id[(record["report_set"], record["sheet_name"])] = mid

    # --- 预建 sheet_name -> currency 映射 ---
    sheet_currency: Dict[str, str] = {
        r["sheet_name"]: r.get("currency", "") for r in meta_records
    }

    inserted_entities = 0
    inserted_perf = 0

    for row_data in parsed_df.to_dict("records"):
        if not _is_data_row(row_data.get(first_col)):
            continue

        key = (row_data["report_set"], row_data["row_source_sheet"])
        meta_id = meta_key_to_id.get(key)
        if meta_id is None:
            logger.warning(f"[loader] meta_id not found for key={key}, skipping row.")
            continue

        # 检测实体类型并清洗名称
        raw_entity_name = str(row_data.get(first_col, "")).strip()
        entity_type = _detect_entity_type(raw_entity_name)
        is_benchmark = (entity_type == "benchmark")
        entity_name = _normalize_bm_entity_name(raw_entity_name) if is_benchmark else raw_entity_name
        entity_isin = "" if entity_type != "fund" else row_data.get("ISIN")

        entity_payload = {
            "report_set":           row_data["report_set"],
            "sheet_name":           row_data["row_source_sheet"],
            "entity_name":          entity_name,
            "entity_type":          entity_type,
            "isin":                 entity_isin,
            "strategy_group":       row_data.get("group_category"),
            "morningstar_rating":   row_data.get("Morningstar Rating Overall"),
            "morningstar_category": row_data.get("Morningstar Category"),
            "benchmark":            row_data.get("Calculation Benchmark"),
            "currency":             sheet_currency.get(row_data["row_source_sheet"], ""),
            "etl_run_id":           row_data.get("etl_run_id"),
            "source_row_number":    int(row_data.get("row_number", 0)),
        }
        entity_id = _upsert_entity(db, report_id, report_type, entity_payload)
        inserted_entities += 1

        _upsert_size_snapshots(db, entity_id, report_id, report_type, row_data, mapped_columns)
        inserted_perf += _upsert_performance(
            db, meta_id, entity_id, report_id, report_type, row_data, mapped_columns
        )

    db.commit()
    logger.info(
        f"[loader] report_id={report_id} report_type={report_type} done: "
        f"meta={len(meta_records)}, entities={inserted_entities}, perf={inserted_perf}"
    )

    # 自动从 peer group 名称提取 fund_code 映射，无需任何手工配置
    # inception_date 来自 pipeline.extract_qw_inception_dates() 的返回值
    fund_map_rows = _upsert_fund_code_map(db, report_id, inception_date_map)

    return {
        "report_meta_rows": len(meta_records),
        "entity_rows_processed": inserted_entities,
        "performance_rows_changed": inserted_perf,
        "fund_map_rows": fund_map_rows,
    }
