from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
import os
import asyncio
import subprocess
import re
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal
from service.factSheetService import generate_factsheet
from service.lcMeetingService import generate_lc_meeting
from models import ReportConfig, ReportRecord
from datetime import datetime
from utils.report_utils import calculate_delivery_deadline

router = APIRouter()

class GenerateReportRequest(BaseModel):
    report_name: str
    report_date: str
    feishu_link: str

@router.post("/generate_report", summary="Generate Report by running Feishu scripts")
async def generate_report(req: GenerateReportRequest):
    match = re.search(r'/sheets/([a-zA-Z0-9]+)', req.feishu_link)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid Feishu link format. Cannot extract spreadsheet token.")
    spreadsheet_token = match.group(1)

    db = SessionLocal()
    try:
        config = db.query(ReportConfig).filter(ReportConfig.report_name == req.report_name).first()
        if config and not config.is_active:
             raise HTTPException(status_code=403, detail="under_development")

        if req.report_name == 'Factsheet':
            await generate_factsheet(spreadsheet_token, req.report_date)
        elif req.report_name == 'LC meeting':
            await generate_lc_meeting(spreadsheet_token, req.report_date)
        else:
            if config:
                report_date_obj = datetime.strptime(req.report_date, "%Y-%m-%d").date()
                record = db.query(ReportRecord).filter(
                    ReportRecord.config_id == config.id,
                    ReportRecord.report_date == report_date_obj
                ).first()

                now = datetime.now()
                if record:
                    record.status = 'Submitted'
                    record.submitted_at = now
                    record.as_of_date = report_date_obj
                    record.updated_at = now
                else:
                    # 2. 计算 delivery_deadline
                    deadline = calculate_delivery_deadline(config.frequency, config.deliverable_time, report_date_obj)
                    new_record = ReportRecord(
                        config_id=config.id,
                        report_name=req.report_name,
                        report_date=report_date_obj,
                        as_of_date=report_date_obj,
                        status='Submitted',
                        submitted_at=now,
                        delivery_deadline=deadline,
                        created_at=now,
                        updated_at=now
                    )
                    db.add(new_record)
                db.commit()
    finally:
        db.close()

    return {"message": "Success", "date": req.report_date}

@router.get("/report_configs", summary="获取报告配置列表")
def get_report_configs():
    db = SessionLocal()
    try:
        configs = db.query(ReportConfig).all()
        return [{"id": c.id, "name": c.report_name, "frequency": c.frequency, "deliverable_time": c.deliverable_time} for c in configs]
    finally:
        db.close()

@router.get("/dashboard/pending", summary="获取 Dashboard 待处理报告列表")
def get_pending_reports():
    db = SessionLocal()
    try:
        now = datetime.now()
        configs = db.query(ReportConfig).all()
        
        results = []
        import math
        for config in configs:
            records = db.query(ReportRecord).filter(ReportRecord.config_id == config.id).all()
            if not records:
                continue
            
            pending_records = [r for r in records if r.status == 'Pending']
            submitted_records = [r for r in records if r.status != 'Pending']
            
            pending_records.sort(key=lambda r: r.report_date, reverse=True)
            submitted_records.sort(key=lambda r: r.report_date, reverse=True)
            
            if pending_records:
                report_status = "Pending"
                records_to_show = [pending_records[0]]
            else:
                report_status = "Submitted"
                if submitted_records:
                    records_to_show = [submitted_records[0]]
                else:
                    continue
                    
            processed_records = []
            for r in records_to_show:
                days_remaining_int = (r.delivery_deadline.date() - now.date()).days
                
                if r.status == 'Pending':
                    if days_remaining_int <= 3:
                        color = "#ff4d4f" # Red
                    elif days_remaining_int <= 7:
                        color = "#faad14" # Orange
                    else:
                        color = "#87ceeb" # Skyblue
                else:
                    color = "#52c41a" # Green

                processed_records.append({
                    "id": r.id,
                    "status": "待提交" if r.status == 'Pending' else "已提交",
                    "report_date": r.report_date.strftime("%Y-%m-%d") if r.report_date else "",
                    "as_of_date": r.as_of_date.strftime("%Y-%m-%d") if r.as_of_date else "",
                    "deadline": r.delivery_deadline.strftime("%Y-%m-%d"),
                    "submitted_at": r.submitted_at.strftime("%Y-%m-%d") if r.submitted_at else "",
                    "daysRemaining": days_remaining_int,
                    "color": color
                })
                
            results.append({
                "config_id": config.id,
                "name": config.report_name,
                "frequency": config.frequency,
                "rule": config.deliverable_time,
                "is_active": config.is_active,
                "status": report_status,
                "records": processed_records,
                "topDaysRemaining": processed_records[0]["daysRemaining"]
            })
            
        def sort_key(item):
            status_order = 0 if item["status"] == "Pending" else 1
            if item["status"] == "Pending":
                # Pending reports: sort by days remaining ascending
                return (status_order, item["topDaysRemaining"], "")
            else:
                # Submitted reports: sort by submitted_at ascending
                top_record = item["records"][0] if item["records"] else {}
                submitted_at = top_record.get("submitted_at") or "9999-99-99"
                return (status_order, 0, submitted_at)
            
        results.sort(key=sort_key)
        return results
    finally:
        db.close()


@router.get("/dashboard/history", summary="获取 Dashboard 历史交付记录")
def get_historical_reports():
    db = SessionLocal()
    try:
        records = db.query(ReportRecord, ReportConfig).join(
            ReportConfig, ReportRecord.config_id == ReportConfig.id
        ).filter(ReportRecord.status == 'Submitted').order_by(ReportRecord.submitted_at.desc()).all()
        
        results = []
        for record, config in records:
            results.append({
                "id": record.id,
                "name": config.report_name,
                "frequency": config.frequency,
                "reportDate": record.report_date.strftime("%Y-%m-%d") if record.report_date else "",
                "asOfDate": record.as_of_date.strftime("%Y-%m-%d") if record.as_of_date else "",
                "deliveryDate": record.delivery_deadline.strftime("%Y-%m-%d") if record.delivery_deadline else "",
                "submittedAt": record.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if record.submitted_at else "",
                "status": record.status,
                "is_active": config.is_active
            })
            
        return results
    finally:
        db.close()


