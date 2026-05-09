"""
lcReportService.py — LCReport 业务逻辑层（优化版）

主要变更：
  · 表名更新为 lc_report_qw_* 系列
  · lc_report_file.file_type → report_type
  · 子表关联键由 file_id 改为 (report_id, report_type)
  · 增加 ARCHIVED 状态支持（前端只读判断）
  · 新增 archive_overdue_reports() 供定时任务调用
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

from utils.lcReport.id_gen import gen_id
from utils.lcReport.pipeline import run_pipeline, extract_qw_inception_dates
from utils.lcReport.loader import load_to_mysql
from utils.lcReport.sales_flow_pipeline import run_sales_flow_pipeline
from utils.lcReport.sales_flow_loader import load_sales_flow_to_mysql
from utils.lcReport.fund_analysis_pipeline import run_fund_analysis_pipeline
from utils.lcReport.fund_analysis_loader import load_fa_to_mysql

logger = logging.getLogger(__name__)

FILES_ROOT = Path(__file__).resolve().parent.parent / "files"


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

def _get_db_session() -> Session:
    from database import SessionLocal
    return SessionLocal()


def _report_date_to_str(d) -> str:
    if isinstance(d, (date, datetime)):
        return d.strftime("%Y-%m-%d")
    return str(d)


def _file_data_status_label(status: str) -> str:
    return {
        "NOT_IMPORTED": "未导入",
        "PARSING":      "解析中",
        "UNCHECKED":    "未检查",
        "CHECKED":      "已检查",
    }.get(status, status)


def _report_status_label(status: str) -> str:
    return {
        "PENDING":  "待完成",
        "DONE":     "已完成",
        "ARCHIVED": "已归档",
    }.get(status, status)


# ---------------------------------------------------------------------------
# 自动归档
# ---------------------------------------------------------------------------

def archive_overdue_reports(db: Session) -> int:
    """
    将所有 报告日期 ≤ 最近一个周五 且状态不是 ARCHIVED 的报告更新为 ARCHIVED。
    由定时任务在每周五 18:00 后调用。
    返回更新条数。
    """
    now = datetime.now()
    # 计算最近的（含今天）周五
    days_since_friday = (now.weekday() - 4) % 7   # 周五=4
    last_friday = now.date() - __import__("datetime").timedelta(days=days_since_friday)

    # 只有当前时间已超过本周五 18:00 才归档
    friday_deadline = datetime.combine(last_friday, __import__("datetime").time(18, 0, 0))
    if now < friday_deadline:
        logger.info("[archive] Not yet past Friday 18:00, skip archiving.")
        return 0

    result = db.execute(
        text("""
            UPDATE lc_report
            SET status='ARCHIVED', archived_at=NOW(), updated_at=NOW()
            WHERE report_date <= :cutoff AND status != 'ARCHIVED'
        """),
        {"cutoff": str(last_friday)},
    )
    db.commit()
    count = result.rowcount
    if count:
        logger.info(f"[archive] Archived {count} reports (cutoff={last_friday})")
    return count


# ---------------------------------------------------------------------------
# 查询报告列表
# ---------------------------------------------------------------------------

def get_report_list(
    db: Session,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    查询报告列表，聚合每份报告下各类文件的状态。
    ARCHIVED 状态报告在返回数据中携带 is_readonly=True 标志。
    """
    conditions = "r.status != 'DELETED'"
    params: Dict[str, Any] = {}
    if start_date:
        conditions += " AND r.report_date >= :sd"
        params["sd"] = start_date
    if end_date:
        conditions += " AND r.report_date <= :ed"
        params["ed"] = end_date

    rows = db.execute(
        text(f"""
            SELECT r.report_id, r.report_date, r.status,
                   f.file_id, f.report_type, f.data_status, f.original_name
            FROM lc_report r
            LEFT JOIN lc_report_file f ON f.report_id = r.report_id
            WHERE {conditions}
            ORDER BY r.report_date DESC, f.report_type
        """),
        params,
    ).fetchall()

    report_map: Dict[int, Dict[str, Any]] = {}
    for row in rows:
        rid = row[0]
        if rid not in report_map:
            report_status = row[2]
            report_map[rid] = {
                "report_id":       str(rid),
                "report_date":     _report_date_to_str(row[1]),
                "status":          report_status,
                "status_label":    _report_status_label(report_status),
                "is_readonly":     report_status == "ARCHIVED",
                "items": {
                    "Quartile_weekly":   _empty_item(),
                    "SalesRptByProduct": _empty_item(),
                    "FundAnalysis":      _empty_item(),
                },
            }
        rtype = row[4]
        data_status = row[5]
        original_name = row[6]
        if rtype and rtype in report_map[rid]["items"]:
            report_map[rid]["items"][rtype] = {
                "file_id":           str(row[3]) if row[3] is not None else None,
                "original_name":     original_name,
                "hasData":           data_status in ("PARSING", "UNCHECKED", "CHECKED"),
                "isChecked":         data_status == "CHECKED",
                "data_status":       data_status,
                "data_status_label": _file_data_status_label(data_status or ""),
            }

    return list(report_map.values())


def _empty_item() -> Dict[str, Any]:
    return {
        "file_id": None,
        "hasData": False,
        "isChecked": False,
        "data_status": None,
        "data_status_label": "",
    }


# ---------------------------------------------------------------------------
# 新增报告
# ---------------------------------------------------------------------------

def create_report(db: Session, report_date: str) -> Dict[str, Any]:
    """在 lc_report 中插入新报告（同日期幂等）"""
    existing = db.execute(
        text("SELECT report_id, report_date, status FROM lc_report WHERE report_date=:d AND status != 'DELETED'"),
        {"d": report_date},
    ).fetchone()

    if existing:
        raise ValueError(f"日期 {report_date} 的报告已存在，无法重复新增")

    rid = gen_id()
    db.execute(
        text("INSERT INTO lc_report (report_id, report_date, status) VALUES (:rid, :d, 'PENDING')"),
        {"rid": rid, "d": report_date},
    )
    db.commit()
    return {
        "report_id":   str(rid),
        "report_date": report_date,
        "status":      "PENDING",
        "is_readonly": False,
        "created":     True,
    }


# ---------------------------------------------------------------------------
# 删除报告
# ---------------------------------------------------------------------------

def delete_report(db: Session, report_id: int) -> bool:
    """软删除报告（更新状态为 DELETED）"""
    row = db.execute(
        text("SELECT status FROM lc_report WHERE report_id=:rid"),
        {"rid": report_id},
    ).fetchone()

    if not row:
        raise ValueError(f"报告 ID={report_id} 不存在")
    
    if row[0] == "ARCHIVED":
        raise PermissionError(f"报告 ID={report_id} 已归档，不可删除")

    db.execute(
        text("UPDATE lc_report SET status='DELETED', updated_at=NOW() WHERE report_id=:rid"),
        {"rid": report_id},
    )
    db.commit()
    return True


# ---------------------------------------------------------------------------
# 上传文件 + 触发解析
# ---------------------------------------------------------------------------

def save_uploaded_file(
    db: Session,
    report_id: int,
    report_type: str,
    filename: str,
    file_bytes: bytes,
    report_date: str,
) -> Dict[str, Any]:
    """
    1. 检查报告是否已归档（归档后拒绝上传）
    2. 保存文件到 files/{report_date}/
    3. 写入 lc_report_file（data_status = NOT_IMPORTED）
    4. Quartile_weekly 自动触发后台 ETL
    """
    # 归档保护
    r = db.execute(
        text("SELECT status FROM lc_report WHERE report_id=:rid"),
        {"rid": report_id},
    ).fetchone()
    if r and r[0] == "ARCHIVED":
        raise PermissionError(f"report_id={report_id} 已归档，不允许上传文件")

    # 查是否已有同 (report_id, report_type) 的记录
    existing = db.execute(
        text("SELECT file_id FROM lc_report_file WHERE report_id=:rid AND report_type=:rt"),
        {"rid": report_id, "rt": report_type},
    ).fetchone()

    # 保存文件（严格使用原始文件名，覆盖旧文件）
    date_dir = FILES_ROOT / report_date
    date_dir.mkdir(parents=True, exist_ok=True)
    stored_path = date_dir / filename
    
    # 强制删除可能存在的旧同名物理文件（防止被进程锁定）
    if stored_path.exists():
        try:
            stored_path.unlink()
        except PermissionError:
            raise ValueError(f"文件被占用无法覆盖，请检查后台是否有进程正在使用该文件: {filename}")
        except Exception as e:
            logger.warning(f"Failed to delete old file {stored_path}: {e}")
            
    stored_path.write_bytes(file_bytes)
    stored_rel = str(stored_path.relative_to(FILES_ROOT.parent))

    # 如果是 xls 文件，在同目录下生成同名的 xlsx 文件供前端核对使用
    if filename.lower().endswith('.xls'):
        xlsx_path = date_dir / (filename + 'x')
        # LibreOffice 默认不覆盖文件，必须先删掉旧的 xlsx
        if xlsx_path.exists():
            try:
                xlsx_path.unlink()
            except PermissionError:
                raise ValueError(f"生成的 xlsx 文件被占用无法覆盖，请检查后台进程: {filename}x")
            except Exception:
                pass
                
        try:
            import platform
            
            if platform.system() == "Windows":
                # 开发环境 (Windows)：调用用户指定的 LibreOffice 进行无损转换
                import subprocess
                soffice_path = r"D:\Program Files\LibreOffice\program\soffice.exe"
                process = subprocess.run(
                    [soffice_path, '--headless', '--nologo', '--nofirststartwizard', '--convert-to', 'xlsx', '--outdir', str(date_dir), str(stored_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
                logger.info(f"Successfully converted {filename} to xlsx format via Windows LibreOffice.")
            else:
                # 生产环境 (Linux) 调用 LibreOffice 进行无损转换
                import subprocess
                process = subprocess.run(
                    ['libreoffice', '--headless', '--nologo', '--nofirststartwizard', '--convert-to', 'xlsx', '--outdir', str(date_dir), str(stored_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
                logger.info(f"Successfully converted {filename} to xlsx format via Linux LibreOffice.")
                
        except Exception as e:
            logger.error(f"Failed to generate xlsx for {filename}: {e}")
            try:
                (FILES_ROOT / "win32com_error.txt").write_text(f"Error converting {filename}: {str(e)}", encoding='utf-8')
            except Exception:
                pass

    if existing:
        fid = existing[0]
        db.execute(
            text("""
                UPDATE lc_report_file SET
                    original_name=:on, stored_path=:sp, file_size=:fs,
                    data_status='NOT_IMPORTED', parse_result=NULL,
                    parse_error=NULL, etl_run_id=NULL,
                    uploaded_at=NOW(), updated_at=NOW()
                WHERE file_id=:fid
            """),
            {"on": filename, "sp": stored_rel, "fs": len(file_bytes), "fid": fid},
        )
    else:
        fid = gen_id()
        db.execute(
            text("""
                INSERT INTO lc_report_file
                    (file_id, report_id, report_type, original_name, stored_path,
                     file_size, data_status)
                VALUES (:fid, :rid, :rt, :on, :sp, :fs, 'NOT_IMPORTED')
            """),
            {
                "fid": fid, "rid": report_id, "rt": report_type,
                "on": filename, "sp": stored_rel, "fs": len(file_bytes),
            },
        )
    db.commit()

    # 清理历史残留的同类型 etl_ 目录（同一天只允许一个活跃的同类报告）
    import shutil
    try:
        for p in date_dir.iterdir():
            if p.is_dir():
                if report_type == "Quartile_weekly":
                    if p.name.startswith("etl_") and not p.name.startswith("etl_sales_") and not p.name.startswith("etl_fa_"):
                        if p.name != f"etl_{fid}":
                            shutil.rmtree(p, ignore_errors=True)
                elif report_type == "SalesRptByProduct":
                    if p.name.startswith("etl_sales_") and p.name != f"etl_sales_{fid}":
                        shutil.rmtree(p, ignore_errors=True)
                elif report_type == "FundAnalysis":
                    if p.name.startswith("etl_fa_") and p.name != f"etl_fa_{fid}":
                        shutil.rmtree(p, ignore_errors=True)
    except Exception as e:
        logger.warning(f"Failed to cleanup old etl dirs: {e}")

    if report_type == "Quartile_weekly":
        _trigger_parse_async(fid, report_id, report_type, stored_path)
    elif report_type == "SalesRptByProduct":
        _trigger_sales_parse_async(fid, report_id, report_type, stored_path)
    elif report_type == "FundAnalysis":
        _trigger_fa_parse_async(fid, report_id, report_type, stored_path)

    return {"file_id": str(fid), "stored_path": stored_rel, "data_status": "NOT_IMPORTED"}


# ---------------------------------------------------------------------------
# 异步解析（后台线程）
# ---------------------------------------------------------------------------

def _trigger_parse_async(
    file_id: int,
    report_id: int,
    report_type: str,
    stored_path: Path,
) -> None:
    def _run():
        db = _get_db_session()
        try:
            db.execute(
                text("UPDATE lc_report_file SET data_status='PARSING', updated_at=NOW() WHERE file_id=:fid"),
                {"fid": file_id},
            )
            db.commit()

            output_dir = stored_path.parent / f"etl_{file_id}"
            result = run_pipeline(stored_path, output_dir=output_dir, mode="lenient")

            # 提取 inception_date 映射（fund_code → YYYY-MM-DD）
            inception_date_map = extract_qw_inception_dates(stored_path)

            load_stats = load_to_mysql(
                db=db,
                parsed_df=result["parsed_df"],
                meta_records=result["meta_records"],
                report_id=report_id,
                report_type=report_type,
                inception_date_map=inception_date_map,
            )

            parse_summary = {
                "etl_run_id":       result["etl_run_id"],
                "sheet_count":      result["sheet_count"],
                "row_count_total":  result["row_count_total"],
                "quality_errors":   result["quality"]["errors"],
                "quality_warnings": result["quality"]["warnings"],
                **load_stats,
            }
            db.execute(
                text("""
                    UPDATE lc_report_file SET
                        data_status='UNCHECKED', etl_run_id=:eid,
                        parse_result=:pr, parse_error=NULL, updated_at=NOW()
                    WHERE file_id=:fid
                """),
                {
                    "eid": result["etl_run_id"],
                    "pr":  json.dumps(parse_summary, ensure_ascii=False),
                    "fid": file_id,
                },
            )
            db.commit()
            logger.info(f"[parse] file_id={file_id} -> UNCHECKED, stats={parse_summary}")

        except Exception as exc:
            logger.exception(f"[parse] file_id={file_id} FAILED: {exc}")
            try:
                db.rollback()
                db.execute(
                    text("""
                        UPDATE lc_report_file SET
                            data_status='NOT_IMPORTED', parse_error=:err, updated_at=NOW()
                        WHERE file_id=:fid
                    """),
                    {"err": str(exc)[:2000], "fid": file_id},
                )
                db.commit()
            except Exception:
                pass
        finally:
            db.close()

    threading.Thread(target=_run, daemon=True).start()


# ---------------------------------------------------------------------------
# 异步解析（SalesRptByProduct）
# ---------------------------------------------------------------------------

def _trigger_sales_parse_async(
    file_id: int,
    report_id: int,
    report_type: str,
    stored_path: Path,
) -> None:
    """在独立线程中执行 Sales ETL，不阻塞 HTTP 响应"""
    def _run():
        db = _get_db_session()
        try:
            # 1. 标记为 PARSING
            db.execute(
                text("UPDATE lc_report_file SET data_status='PARSING', updated_at=NOW() WHERE file_id=:fid"),
                {"fid": file_id},
            )
            db.commit()

            # 2. 执行 Pipeline
            output_dir = stored_path.parent / f"etl_sales_{file_id}"
            result = run_sales_flow_pipeline(stored_path, output_dir=output_dir)

            # 3. 执行 Loader
            load_stats = load_sales_flow_to_mysql(
                db=db,
                parsed_df=result["parsed_df"],
                report_id=report_id,
                report_type=report_type,
                etl_run_id=result["etl_run_id"],
            )

            # 4. 标记为 UNCHECKED + 保存摘要
            parse_summary = {
                "etl_run_id":                   result["etl_run_id"],
                "report_date":                  result["report_date"],
                "rows_loaded":                  result["rows_loaded"],
                "rows_skipped_non_product":     result["rows_skipped_non_product"],
                "rows_skipped_invalid_numeric": result["rows_skipped_invalid_numeric"],
                **load_stats,
            }
            db.execute(
                text("""
                    UPDATE lc_report_file SET
                        data_status='UNCHECKED', etl_run_id=:eid,
                        parse_result=:pr, parse_error=NULL, updated_at=NOW()
                    WHERE file_id=:fid
                """),
                {
                    "eid": result["etl_run_id"],
                    "pr":  json.dumps(parse_summary, ensure_ascii=False),
                    "fid": file_id,
                },
            )
            db.commit()
            logger.info(f"[sales_parse] file_id={file_id} -> UNCHECKED, stats={parse_summary}")

        except Exception as exc:
            logger.exception(f"[sales_parse] file_id={file_id} FAILED: {exc}")
            try:
                db.rollback()
                db.execute(
                    text("""
                        UPDATE lc_report_file SET
                            data_status='NOT_IMPORTED', parse_error=:err, updated_at=NOW()
                        WHERE file_id=:fid
                    """),
                    {"err": str(exc)[:2000], "fid": file_id},
                )
                db.commit()
            except Exception:
                pass
        finally:
            db.close()

    threading.Thread(target=_run, daemon=True).start()


# ---------------------------------------------------------------------------
# 核对通过
# ---------------------------------------------------------------------------

def check_file(db: Session, file_id: int) -> Dict[str, Any]:
    """将文件状态 UNCHECKED → CHECKED（检查报告未归档）"""
    row = db.execute(
        text("""
            SELECT f.data_status, r.status AS report_status
            FROM lc_report_file f
            JOIN lc_report r ON r.report_id = f.report_id
            WHERE f.file_id=:fid
        """),
        {"fid": file_id},
    ).fetchone()

    if not row:
        raise ValueError(f"file_id={file_id} not found")
    if row[1] == "ARCHIVED":
        raise PermissionError(f"file_id={file_id} 所属报告已归档，不允许修改")

    db.execute(
        text("UPDATE lc_report_file SET data_status='CHECKED', updated_at=NOW() WHERE file_id=:fid"),
        {"fid": file_id},
    )
    db.commit()
    return {"file_id": str(file_id), "data_status": "CHECKED"}


# ---------------------------------------------------------------------------
# 查询文件解析状态（轮询用）
# ---------------------------------------------------------------------------

def get_file_status(db: Session, file_id: int) -> Dict[str, Any]:
    row = db.execute(
        text("""
            SELECT file_id, report_type, data_status, parse_result, parse_error, updated_at
            FROM lc_report_file WHERE file_id=:fid
        """),
        {"fid": file_id},
    ).fetchone()

    if not row:
        raise ValueError(f"file_id={file_id} not found")

    parse_result = None
    if row[3]:
        try:
            parse_result = json.loads(row[3])
        except Exception:
            parse_result = row[3]

    return {
        "file_id":           str(row[0]),
        "report_type":       row[1],
        "data_status":       row[2],
        "data_status_label": _file_data_status_label(row[2] or ""),
        "hasData":           row[2] in ("PARSING", "UNCHECKED", "CHECKED"),
        "isChecked":         row[2] == "CHECKED",
        "parse_result":      parse_result,
        "parse_error":       row[4],
        "updated_at":        str(row[5]) if row[5] else None,
    }


# ---------------------------------------------------------------------------
# 异步解析（FundAnalysis）
# ---------------------------------------------------------------------------

def _trigger_fa_parse_async(
    file_id: int,
    report_id: int,
    report_type: str,
    stored_path: Path,
) -> None:
    """在独立线程中执行 Fund Analysis ETL，不阻塞 HTTP 响应"""
    def _run():
        db = _get_db_session()
        try:
            # 1. 标记为 PARSING
            db.execute(
                text("UPDATE lc_report_file SET data_status='PARSING', updated_at=NOW() WHERE file_id=:fid"),
                {"fid": file_id},
            )
            db.commit()

            # 2. 执行 Pipeline
            output_dir = stored_path.parent / f"etl_fa_{file_id}"
            result = run_fund_analysis_pipeline(stored_path, output_dir=output_dir)

            # 3. 执行 Loader
            load_stats = load_fa_to_mysql(
                db=db,
                meta_df=result["meta_df"],
                perf_df=result["perf_df"],
                report_id=report_id,
                report_type=report_type,
                fund_map_df=result.get("fund_map_df"),  # 自动写入 lc_fund_code_map
            )

            # 4. 标记为 UNCHECKED + 保存摘要
            parse_summary = {
                "etl_run_id":       result["etl_run_id"],
                "report_set":       result["report_set"],
                "sheet_count":      result["sheet_count"],
                "meta_rows":        result["meta_rows"],
                "performance_rows": result["performance_rows"],
                "fund_map_rows":    result.get("fund_map_rows", 0),
                **load_stats,
            }
            db.execute(
                text("""
                    UPDATE lc_report_file SET
                        data_status='UNCHECKED', etl_run_id=:eid,
                        parse_result=:pr, parse_error=NULL, updated_at=NOW()
                    WHERE file_id=:fid
                """),
                {
                    "eid": result["etl_run_id"],
                    "pr":  json.dumps(parse_summary, ensure_ascii=False),
                    "fid": file_id,
                },
            )
            db.commit()
            logger.info(f"[fa_parse] file_id={file_id} -> UNCHECKED, stats={parse_summary}")

        except Exception as exc:
            logger.exception(f"[fa_parse] file_id={file_id} FAILED: {exc}")
            try:
                db.rollback()
                db.execute(
                    text("""
                        UPDATE lc_report_file SET
                            data_status='NOT_IMPORTED', parse_error=:err, updated_at=NOW()
                        WHERE file_id=:fid
                    """),
                    {"err": str(exc)[:2000], "fid": file_id},
                )
                db.commit()
            except Exception:
                pass
        finally:
            db.close()


    threading.Thread(target=_run, daemon=True).start()

