"""
lcReport.py — LCReport API 路由层

接口列表：
  GET    /api/lc-report/reports                       查询报告列表（支持日期范围过滤）
  POST   /api/lc-report/reports                       新增报告
  DELETE /api/lc-report/reports/{report_id}           软删除报告
  POST   /api/lc-report/reports/{report_id}/generate  生成最终报告表
  POST   /api/lc-report/files/upload                  上传文件（存盘 + 触发解析，归档报告拒绝）
  GET    /api/lc-report/files/{file_id}/status        查询文件解析状态（轮询）
  POST   /api/lc-report/files/{file_id}/check         核对通过（归档报告拒绝）
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from service.lcReportService import (
    get_report_list,
    create_report,
    delete_report,
    save_uploaded_file,
    get_file_status,
    check_file,
)
from service.lcReportGeneratorService import generate_report

router = APIRouter(prefix="/lc-report", tags=["LCReport"])


# ---------------------------------------------------------------------------
# 辅助格式化函数（Quartile_weekly 数据重组用）
# ---------------------------------------------------------------------------

def _raw(v):
    """Decimal/None → raw Python number or empty string, no formatting."""
    if v is None:
        return ""
    try:
        return float(v)
    except (TypeError, ValueError):
        return str(v)


def _perf_col_header(period_label: str, start_date: str, end_date: str, metric: str, sub: str) -> str:
    """构造 Performance 列头。
    sub: 'value' | 'rank' | 'quartile'
    示例: 'YTD Return (Cumulative) (2026-01-01~2026-04-16)'
    """
    metric_label = {
        "return_cum":          "Return (Cumulative)",
        "return_ann":          "Return (Annualized)",
        "return_cumulative":   "Return (Cumulative)",
        "return_annualized":   "Return (Annualized)",
    }.get(metric, metric or "Return")
    sub_label = {
        "value":    metric_label,
        "rank":     "Peer group rank",
        "quartile": "Peer group quartile",
    }.get(sub, sub)
    label = period_label or ""
    date_range = ""
    if start_date and end_date:
        date_range = f" ({start_date}~{end_date})"
    elif end_date:
        date_range = f" (~{end_date})"
    return f"{label} {sub_label}{date_range}".strip()



# ---------------------------------------------------------------------------
# DB 依赖
# ---------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Request / Response 模型
# ---------------------------------------------------------------------------

class CreateReportRequest(BaseModel):
    report_date: str   # YYYY-MM-DD


class CheckFileRequest(BaseModel):
    pass   # 无 body，file_id 由路径传入


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------


class UpdateNoteRequest(BaseModel):
    analyst_note: str


@router.get("/note", summary="按日期查询分析师注释及FA文件信息")
def api_get_note(date: str, db: Session = Depends(get_db)):
    """
    按日期查询 analyst_note 及关联的 FundAnalysis 文件 ID。
    精确匹配 report_date = :d 且有 FundAnalysis 文件
    """
    from sqlalchemy import text as _t

    def _fa_for_report(rid):
        return db.execute(
            _t("SELECT file_id FROM lc_report_file "
               "WHERE report_id = :rid AND report_type = 'FundAnalysis' LIMIT 1"),
            {"rid": rid}
        ).fetchone()
    
    row = db.execute(
        _t("SELECT report_id, analyst_note, status FROM lc_report "
           "WHERE report_date = :d and status != 'DELETED' LIMIT 1"),
        {"d": date}
    ).fetchone()
    if row:
        fa = _fa_for_report(row[0])
        return {"success": True, "report_id": str(row[0]),
                "analyst_note": row[1] or "", "status": row[2],
                "fa_file_id": str(fa[0]) if fa else None}
            
    else:
        raise HTTPException(status_code=404, detail="未找到报告")



@router.patch("/reports/{report_id}/note", summary="保存分析师注释")
def api_update_note(
    report_id: int,
    body: UpdateNoteRequest,
    db: Session = Depends(get_db),
):
    """
    保存富文本注释到 lc_report.analyst_note。
    已归档（ARCHIVED）的报告返回 403。
    """
    from sqlalchemy import text as _t
    row = db.execute(
        _t("SELECT status FROM lc_report WHERE report_id = :rid"),
        {"rid": report_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="报告不存在")
    if row[0] == "ARCHIVED":
        raise HTTPException(status_code=403, detail="已归档的报告不能编辑")
    db.execute(
        _t("UPDATE lc_report SET analyst_note = :note WHERE report_id = :rid"),
        {"note": body.analyst_note, "rid": report_id}
    )
    db.commit()
    return {"success": True}


@router.get("/reports", summary="查询报告列表")
def api_get_reports(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    查询报告列表，可按日期范围过滤。
    返回每份报告及其下 Quartile_weekly / SalesRptByProduct 文件的状态。
    """
    try:
        data = get_report_list(db, start_date=start_date, end_date=end_date)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports", summary="新增报告")
def api_create_report(
    body: CreateReportRequest,
    db: Session = Depends(get_db),
):
    """
    在报告主表中插入一条新记录（以日期为唯一键，重复创建幂等返回现有记录）。
    """
    try:
        result = create_report(db, report_date=body.report_date)
        return {"success": True, "data": result}
    except ValueError as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reports/{report_id}", summary="删除报告")
def api_delete_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    """
    软删除指定的报告，状态变为 DELETED。已归档的报告不允许删除。
    """
    try:
        delete_report(db, report_id)
        return {"success": True, "message": "删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/{report_id}/generate", summary="生成最终报告表")
def api_generate_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    """
    触发 LC Report 最终报告生成管线：
    1. 从 lc_report_sales_flow / lc_report_fa_performance / lc_report_qw_performance 读取原始数据
    2. 依次填充 lc_fund_performance → rating → summary → quartile_contribution → other_accounts
    3. 将 lc_report.status 更新为 DONE
    前置条件：三个文件类型均已通过核对（CHECKED）。
    """
    # 先查询报告日期
    from sqlalchemy import text
    row = db.execute(
        text("SELECT report_date FROM lc_report WHERE report_id=:rid"),
        {"rid": report_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"report_id={report_id} 不存在")

    report_date = str(row[0])  # date → str (YYYY-MM-DD)
    try:
        result = generate_report(db, report_id=report_id, report_date=report_date)
        return {"success": True, "data": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/files/upload", summary="上传文件并触发解析")
async def api_upload_file(
    report_id: int = Form(..., description="报告ID"),
    report_date: str = Form(..., description="报告日期，用于确定存储目录 YYYY-MM-DD"),
    report_type: str = Form(..., description="报告类型：Quartile_weekly | SalesRptByProduct"),
    file: UploadFile = File(..., description="上传的 Excel 文件"),
    db: Session = Depends(get_db),
):
    """
    上传原始数据文件：
    1. 检查报告是否已归档（ARCHIVED 状态返回 403）
    2. 保存到 backend/files/{report_date}/ 目录
    3. 写入 lc_report_file 记录（data_status = NOT_IMPORTED）
    4. 若 report_type=Quartile_weekly，自动触发后台 ETL 解析（PARSING → UNCHECKED）
    """
    allowed_types = {"Quartile_weekly", "SalesRptByProduct", "FundAnalysis"}
    if report_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"report_type 不合法，允许：{allowed_types}")

    try:
        content = await file.read()
        result = save_uploaded_file(
            db=db,
            report_id=report_id,
            report_type=report_type,
            filename=file.filename,
            file_bytes=content,
            report_date=report_date,
        )
        return {
            "success": True,
            "data": result,
            "message": "文件已上传，正在后台解析导入，请稍后刷新状态",
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{file_id}/status", summary="查询文件解析状态")
def api_get_file_status(
    file_id: int,
    db: Session = Depends(get_db),
):
    """
    轮询接口：返回单个文件的当前 data_status 及解析摘要。
    前端上传后可每 3 秒调用一次，直至 data_status 变为 UNCHECKED 或出错。
    """
    try:
        data = get_file_status(db, file_id)
        return {"success": True, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{file_id}/download", summary="下载原始文件")
def api_download_file(
    file_id: int,
    db: Session = Depends(get_db),
):
    """返回原始 Excel 文件（如果原文件是 xls，则优先返回同名 xlsx）"""
    from sqlalchemy import text
    import os
    row = db.execute(
        text("SELECT stored_path, original_name FROM lc_report_file WHERE file_id=:fid"),
        {"fid": file_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    stored_path, original_name = row
    abs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), stored_path)
    
    # 核对加载源文件时，判断如果是 xls 格式的文件，在同目录下找同名的 xlsx 进行加载
    if abs_path.lower().endswith('.xls'):
        xlsx_path = abs_path + 'x'
        if os.path.exists(xlsx_path):
            abs_path = xlsx_path
            original_name = original_name + 'x'

    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="文件实体已丢失")
        
    return FileResponse(abs_path, filename=original_name)

@router.get("/files/{file_id}/parsed-data", summary="获取文件解析后入库的数据")
def api_get_parsed_data(
    file_id: int,
    db: Session = Depends(get_db),
):
    """根据文件的 report_type 返回解析后的数据供比对使用"""
    from sqlalchemy import text
    file_row = db.execute(
        text("SELECT report_id, report_type FROM lc_report_file WHERE file_id=:fid"),
        {"fid": file_id}
    ).fetchone()
    
    if not file_row:
        raise HTTPException(status_code=404, detail="文件不存在")
        
    report_id, report_type = file_row
    
    if report_type == "SalesRptByProduct":
        rows = db.execute(
            text("SELECT * FROM lc_report_sales_flow WHERE report_id=:rid"),
            {"rid": report_id}
        ).fetchall()
        keys = ["fund_code", "fund_name", "est_aum_usd_m", 
                "daily_gross_sub_usd_k", "daily_gross_red_usd_k", "daily_net_flow_usd_k",
                "mtd_gross_sub_usd_k", "mtd_gross_red_usd_k", "mtd_net_flow_usd_k",
                "ytd_gross_sub_usd_k", "ytd_gross_red_usd_k", "ytd_net_flow_usd_k"]
    elif report_type == "Quartile_weekly":
        # ── Step 1: 获取该报告下所有 sheet 的元数据（按 sheet_name 排序）──
        meta_rows = db.execute(
            text("""
                SELECT meta_id, sheet_name, currency, grouped_by, calculated_on, exported_on, report_name
                FROM lc_report_qw_meta
                WHERE report_id = :rid
                ORDER BY meta_id
            """),
            {"rid": report_id}
        ).fetchall()

        if not meta_rows:
            return {"success": True, "report_type": report_type, "sheets": []}

        # ── Step 2: 按 sheet 逐一重组数据 ──────────────────────────────────
        sheets_result = []

        for meta_row in meta_rows:
            meta_id    = meta_row[0]
            sheet_name = meta_row[1]
            currency   = meta_row[2] or ""
            grouped_by = meta_row[3] or ""
            calc_on    = meta_row[4] or ""
            exp_on     = meta_row[5] or ""

            # ── Step 2a: 拉取该 sheet 下所有实体（保持原始行顺序）──────────
            entity_rows = db.execute(
                text("""
                    SELECT entity_id, entity_name, entity_type,
                           isin, strategy_group,
                           morningstar_rating, morningstar_category,
                           benchmark, currency AS entity_currency,
                           source_row_number
                    FROM lc_report_qw_entity
                    WHERE report_id = :rid AND sheet_name = :sn
                    ORDER BY source_row_number
                """),
                {"rid": report_id, "sn": sheet_name}
            ).fetchall()

            if not entity_rows:
                sheets_result.append({
                    "sheet_name": sheet_name,
                    "meta": {
                        "currency": currency, "grouped_by": grouped_by,
                        "calculated_on": calc_on, "exported_on": exp_on,
                    },
                    "columns": [],
                    "rows": []
                })
                continue

            entity_ids = [r[0] for r in entity_rows]

            # ── Step 2b: 按 source_row_number 最小值确定 period 列顺序 ─────────
            period_col_keys = []
            period_order_rows = db.execute(
                text("""
                    SELECT period_type, period_label, start_date, end_date, metric,
                           MIN(source_row_number) AS min_row
                    FROM lc_report_qw_performance
                    WHERE report_id = :rid AND sheet_name = :sn
                    GROUP BY period_type, period_label, start_date, end_date, metric
                    ORDER BY min_row, period_type, metric
                """),
                {"rid": report_id, "sn": sheet_name}
            ).fetchall()

            # Two-pass build:
            #   Pass 1 — group period_order_rows by (period_label, start_date, end_date)
            #            to find all metrics per date-group, preserving encounter order.
            #   Pass 2 — emit columns:  [metric1_value, metric2_value, ..., rank, quartile]
            #            rank/quartile appear only ONCE per (period_label, start_date, end_date).
            pg_info_map: dict = {}   # (period_label, start_date, end_date) -> {period_type, metrics[]}
            for pr in period_order_rows:
                pg_key = (pr[1], pr[2], pr[3])   # (period_label, start_date, end_date)
                if pg_key not in pg_info_map:
                    pg_info_map[pg_key] = {"period_type": pr[0], "metrics": []}
                if pr[4] not in pg_info_map[pg_key]["metrics"]:
                    pg_info_map[pg_key]["metrics"].append(pr[4])

            for pg_key, pg_info in pg_info_map.items():
                period_label, start_date, end_date = pg_key
                first_metric = pg_info["metrics"][0]
                # 每个 metric 生成一个 value 列
                for metric in pg_info["metrics"]:
                    period_col_keys.append({
                        "period_type":  pg_info["period_type"],
                        "period_label": period_label,
                        "start_date":   start_date,
                        "end_date":     end_date,
                        "metric":       metric,
                        "sub":          "value",
                        "header": _perf_col_header(period_label, start_date, end_date, metric, "value"),
                    })
                # rank / quartile 共用第一个 metric 的数据（DB 中冗余存储，值相同）
                for sub in ("rank", "quartile"):
                    period_col_keys.append({
                        "period_type":  pg_info["period_type"],
                        "period_label": period_label,
                        "start_date":   start_date,
                        "end_date":     end_date,
                        "metric":       first_metric,   # 用第一个 metric 做索引
                        "sub":          sub,
                        "header": _perf_col_header(period_label, start_date, end_date, first_metric, sub),
                    })

            # ── Step 2c: 拉取该 sheet 规模快照的日期维度 ─────────────────────
            size_cols = db.execute(
                text("""
                    SELECT DISTINCT ss.size_type, ss.snapshot_date, ss.source_column_name
                    FROM lc_report_qw_size_snapshot ss
                    JOIN lc_report_qw_entity e ON e.entity_id = ss.entity_id
                    WHERE ss.report_id = :rid AND e.sheet_name = :sn
                    ORDER BY ss.size_type, ss.snapshot_date
                """),
                {"rid": report_id, "sn": sheet_name}
            ).fetchall()

            size_col_keys = []
            seen_size_keys = set()
            for sc in size_cols:
                k = (sc[0], sc[1])
                if k not in seen_size_keys:
                    seen_size_keys.add(k)
                    label = sc[2] or f"{sc[0]} {sc[1]}"
                    size_col_keys.append({"size_type": sc[0], "snapshot_date": sc[1], "header": label})

            # ── Step 2d: 拉取该 sheet 所有 performance 数据，构建 entity_id 索引 ──
            perf_all = db.execute(
                text("""
                    SELECT entity_id, period_label, start_date, end_date, metric,
                           value, peer_group_rank, peer_group_quartile
                    FROM lc_report_qw_performance
                    WHERE report_id = :rid AND sheet_name = :sn
                """),
                {"rid": report_id, "sn": sheet_name}
            ).fetchall()

            # perf_index[(entity_id, period_label, start_date, end_date, metric)]
            #   = (value, rank, quartile)
            perf_index = {}
            for pr in perf_all:
                k = (pr[0], pr[1], pr[2], pr[3], pr[4])
                perf_index[k] = (pr[5], pr[6], pr[7])

            # ── Step 2e: 拉取规模快照数据 ────────────────────────────────────
            size_all = db.execute(
                text("""
                    SELECT ss.entity_id, ss.size_type, ss.snapshot_date, ss.snapshot_value
                    FROM lc_report_qw_size_snapshot ss
                    JOIN lc_report_qw_entity e ON e.entity_id = ss.entity_id
                    WHERE ss.report_id = :rid AND e.sheet_name = :sn
                """),
                {"rid": report_id, "sn": sheet_name}
            ).fetchall()

            size_index = {}  # (entity_id, size_type, snapshot_date) -> value
            for sr in size_all:
                size_index[(sr[0], sr[1], sr[2])] = sr[3]

            # ── Step 2f: 构建列头 ──────────────────────────────────────────
            static_cols = [
                "Group/Investment", "Morningstar Rating Overall", "ISIN",
                "Morningstar Category", "Calculation Benchmark",
            ]
            size_headers   = [sc["header"] for sc in size_col_keys]
            period_headers = [pc["header"] for pc in period_col_keys]
            all_headers = static_cols + size_headers + period_headers

            # ── Step 2f-2: 构建合并表头分组描述（用于前端 3 行合并表头）──────
            _METRIC_LABEL = {
                "return_cum":        "Return (Cumulative)",
                "return_ann":        "Return (Annualized)",
                "return_cumulative": "Return (Cumulative)",
                "return_annualized": "Return (Annualized)",
            }
            column_groups = []
            # 静态列：占 3 行高度
            for ci, col in enumerate(static_cols):
                column_groups.append({"type": "static", "label": col, "col_index": ci})
            # 规模列：占 3 行高度
            for si, sc in enumerate(size_col_keys):
                column_groups.append({"type": "size", "label": sc["header"],
                                      "col_index": len(static_cols) + si})
            # Period 列组：按 (period_label, start_date, end_date) 聚合
            # 同一 period 可能有多个 metric（如 return_cum + return_ann），
            # 不能按固定步长 3 切割，必须按日期维度聚合成同一组
            period_base = len(static_cols) + len(size_col_keys)
            pg_map: dict = {}   # ordered dict, key=(period_label, start_date, end_date)
            for ci_off, pc in enumerate(period_col_keys):
                pg_key = (pc["period_label"], pc["start_date"], pc["end_date"])
                abs_col = period_base + ci_off
                if pg_key not in pg_map:
                    dr = ""
                    if pc["start_date"] and pc["end_date"]:
                        dr = f"{pc['start_date']}~{pc['end_date']}"
                    elif pc["end_date"]:
                        dr = pc["end_date"]
                    pg_map[pg_key] = {
                        "type":         "period",
                        "period_label": pc["period_label"],
                        "date_range":   dr,
                        "col_start":    abs_col,
                        "sub_cols":     [],
                    }
                metric_lbl = _METRIC_LABEL.get(pc["metric"], pc["metric"] or "Return")
                lbl = (metric_lbl       if pc["sub"] == "value"
                       else "Peer group rank"     if pc["sub"] == "rank"
                       else "Peer group quartile")
                pg_map[pg_key]["sub_cols"].append({"label": lbl, "col_index": abs_col})

            for grp in pg_map.values():
                grp["col_count"] = len(grp["sub_cols"])
                column_groups.append(grp)


            # ── Step 2g: 逐行组装数据 ────────────────────────────────────────
            rows_out = []
            current_group = None

            for er in entity_rows:
                eid          = er[0]
                entity_name  = er[1]
                entity_type  = er[2]
                isin         = er[3] or ""
                strategy_grp = er[4] or ""
                ms_rating    = er[5] or ""
                ms_category  = er[6] or ""
                benchmark    = er[7] or ""

                # 如果分组变了，插入分组标题行（模拟 Excel 中的 group header 行）
                if strategy_grp and strategy_grp != current_group:
                    current_group = strategy_grp
                    group_row = {"Group/Investment": strategy_grp, "_is_group_header": True}
                    for h in all_headers[1:]:
                        group_row[h] = ""
                    rows_out.append(group_row)

                row = {
                    "Group/Investment":           entity_name,
                    "Morningstar Rating Overall":  ms_rating,
                    "ISIN":                        isin,
                    "Morningstar Category":        ms_category,
                    "Calculation Benchmark":       benchmark,
                }

                # 规模列（原始数值）
                for sc in size_col_keys:
                    val = size_index.get((eid, sc["size_type"], sc["snapshot_date"]))
                    row[sc["header"]] = _raw(val)

                # Performance 列：每个 period 拆为 3 列（value / rank / quartile）
                for pc in period_col_keys:
                    k = (eid, pc["period_label"], pc["start_date"], pc["end_date"], pc["metric"])
                    perf = perf_index.get(k)
                    if perf:
                        val, rank, quartile = perf
                        sub = pc["sub"]
                        if sub == 'value':
                            row[pc["header"]] = _raw(val)
                        elif sub == 'rank':
                            row[pc["header"]] = _raw(rank)
                        else:
                            row[pc["header"]] = _raw(quartile)
                    else:
                        row[pc["header"]] = ""

                rows_out.append(row)

            sheets_result.append({
                "sheet_name": sheet_name,
                "meta": {
                    "currency":     currency,
                    "grouped_by":   grouped_by,
                    "calculated_on": calc_on,
                    "exported_on":  exp_on,
                },
                "columns": all_headers,
                "column_groups": column_groups,
                "rows": rows_out,
            })

        return {"success": True, "report_type": report_type, "sheets": sheets_result}

    elif report_type == "FundAnalysis":
        # ── Step 1: 获取所有快照元数据，按 sheet_name 分组 ───────────────
        meta_rows = db.execute(
            text("""
                SELECT meta_id, sheet_name, snapshot_type, snapshot_date,
                       calculated_on, currency, grouped_by
                FROM lc_report_fa_meta
                WHERE report_id = :rid
                ORDER BY sheet_name, snapshot_type
            """),
            {"rid": report_id}
        ).fetchall()

        if not meta_rows:
            return {"success": True, "report_type": report_type, "sheets": []}

        # sheet_name -> {"t0": {...}, "t1": {...}}
        sheet_meta: dict = {}
        for mr in meta_rows:
            sn, st = mr[1], mr[2]
            if sn not in sheet_meta:
                sheet_meta[sn] = {}
            sheet_meta[sn][st] = {
                "meta_id":       mr[0],
                "snapshot_date": mr[3],
                "calculated_on": mr[4],
                "currency":      mr[5] or "",
                "grouped_by":    mr[6] or "",
            }

        sheets_result = []

        for sheet_name, snapshots in sheet_meta.items():
            t0 = snapshots.get("t0")
            t1 = snapshots.get("t1")
            if not t0:
                continue

            # ── Step 2: 拉取 t0 全量 performance ─────────────────────────
            perf_t0_rows = db.execute(
                text("""
                    SELECT entity_name, isin, morningstar_rating,
                           fund_size_date, fund_size,
                           period_type, metric, value,
                           peer_group_rank, peer_group_quartile,
                           start_date, end_date, source_row_number
                    FROM lc_report_fa_performance
                    WHERE meta_id = :mid
                    ORDER BY source_row_number, period_type, metric
                """),
                {"mid": t0["meta_id"]}
            ).fetchall()

            # ── Step 3: 拉取 t1 performance，建索引 ─────────────────────
            perf_t1_idx: dict = {}
            if t1:
                for r in db.execute(
                    text("""
                        SELECT entity_name, period_type, metric,
                               value, peer_group_rank, peer_group_quartile
                        FROM lc_report_fa_performance
                        WHERE meta_id = :mid
                    """),
                    {"mid": t1["meta_id"]}
                ).fetchall():
                    perf_t1_idx[(r[0], r[1], r[2])] = {
                        "value":    _raw(r[3]),
                        "rank":     r[4],
                        "quartile": r[5],
                    }

            # ── Step 4: 构建 entity 字典 ──────────────────────────────────
            entities: dict = {}
            entity_order: list = []
            period_type_order: list = []
            seen_pt: set = set()

            for r in perf_t0_rows:
                ename = r[0]
                if ename not in entities:
                    entities[ename] = {
                        "entity_name":        ename,
                        "isin":               r[1] or "",
                        "morningstar_rating": r[2] or "",
                        "fund_size_date":     r[3] or "",
                        "fund_size":          _raw(r[4]),
                        "periods":            {},
                    }
                    entity_order.append(ename)

                pt, metric = r[5], r[6]
                if pt not in seen_pt:
                    seen_pt.add(pt)
                    period_type_order.append(pt)

                if pt not in entities[ename]["periods"]:
                    entities[ename]["periods"][pt] = {
                        "start_date":  r[10],
                        "end_date":    r[11],
                        "t0": {},
                        "t1": {},
                        "rank_change": None,
                    }

                entities[ename]["periods"][pt]["t0"][metric] = {
                    "value":    _raw(r[7]),
                    "rank":     r[8],
                    "quartile": r[9],
                }

                t1_data = perf_t1_idx.get((ename, pt, metric))
                if t1_data:
                    entities[ename]["periods"][pt]["t1"][metric] = t1_data
                    # rank 数字越小越好（排名越靠前 = Better）
                    r0, r1 = r[8], t1_data.get("rank")
                    if r0 is not None and r1 is not None and \
                            entities[ename]["periods"][pt]["rank_change"] is None:
                        if r0 < r1:
                            entities[ename]["periods"][pt]["rank_change"] = "Better"
                        elif r0 > r1:
                            entities[ename]["periods"][pt]["rank_change"] = "Worse"
                        else:
                            entities[ename]["periods"][pt]["rank_change"] = "Same"
                else:
                    # 上期无对应数据：默认 value=0, rank=0, quartile=0, rank_change=Worse
                    entities[ename]["periods"][pt]["t1"][metric] = {
                        "value":    0,
                        "rank":     0,
                        "quartile": 0,
                    }
                    if entities[ename]["periods"][pt]["rank_change"] is None:
                        entities[ename]["periods"][pt]["rank_change"] = "Worse"

            sheets_result.append({
                "sheet_name":   sheet_name,
                "meta_t0":      t0,
                "meta_t1":      t1,
                "period_types": period_type_order,
                "rows":         [entities[n] for n in entity_order],
            })

        return {"success": True, "report_type": report_type, "sheets": sheets_result}

    else:
        return {"success": True, "report_type": report_type, "columns": [], "rows": []}

    # ── SalesRptByProduct flat format (rows / keys defined above) ────────────
    if not rows:
        return {"success": True, "report_type": report_type, "columns": keys, "rows": []}
    data_rows = []
    for r in rows:
        r_dict = r._mapping if hasattr(r, "_mapping") else dict(zip(r.keys(), r))
        data_rows.append({k: r_dict.get(k) for k in keys})
    return {"success": True, "report_type": report_type, "columns": keys, "rows": data_rows}


@router.post("/files/{file_id}/check", summary="核对通过")
def api_check_file(
    file_id: int,
    db: Session = Depends(get_db),
):
    """
    将文件状态从 UNCHECKED 更新为 CHECKED，表示人工核对通过。
    已归档（ARCHIVED）的报告返回 403。
    """
    try:
        data = check_file(db, file_id)
        return {"success": True, "data": data}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
