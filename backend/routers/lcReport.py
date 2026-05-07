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
