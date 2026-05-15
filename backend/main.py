import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import engine, Base
from models import *  # Ensure all models are loaded
from scheduler_tasks import calc_classic_a_historical_derived_task, calc_report_records_task
from routers.factsheet import router as factsheet_router
from routers.reports import router as reports_router
from routers.lc_meeting import router as lc_meeting_router
from routers.lcReport import router as lc_report_router
from service.lcReportService import archive_overdue_reports

# ================= DB Setup =================
Base.metadata.create_all(bind=engine)

# ================= FastAPI App =================
app = FastAPI(title="Huili Demo", description="Excel Parsing and Reporting Backend")

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    # 每 10 秒执行一次数据的派生计算（累计收益率与波动率）
    scheduler.add_job(calc_classic_a_historical_derived_task, 'interval', seconds=10)

    # 每 1 分钟执行一次生成报告交付记录的任务
    scheduler.add_job(calc_report_records_task, 'interval', minutes=1)

    # 每周五 18:00 自动归档超期 LC Report
    def _archive_job():
        from database import SessionLocal
        db = SessionLocal()
        try:
            count = archive_overdue_reports(db)
            if count:
                import logging
                logging.getLogger(__name__).info(f"[scheduler] auto-archived {count} reports")
        finally:
            db.close()

    scheduler.add_job(_archive_job, 'cron', day_of_week='fri', hour=18, minute=0)

    scheduler.start()

    # 启动时立即执行一次计算，防止初始遗漏
    calc_classic_a_historical_derived_task()
    calc_report_records_task()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

# -------------------------------------------------------
# Register Routers
# -------------------------------------------------------
app.include_router(reports_router, prefix="/api")
app.include_router(factsheet_router, prefix="/api")
app.include_router(lc_meeting_router, prefix="/api")
app.include_router(lc_report_router, prefix="/api")

from routers.fund_code_map import router as fund_code_map_router
app.include_router(fund_code_map_router, prefix="/api/lc-report")

# -------------------------------------------------------
# Static Frontend Files
# -------------------------------------------------------
dist_dir = os.path.join(os.path.dirname(__file__), "../frontend/dist")
os.makedirs(dist_dir, exist_ok=True)
if not os.path.exists(os.path.join(dist_dir, "index.html")):
    with open(os.path.join(dist_dir, "index.html"), "w") as f:
        f.write("<html><body>Building frontend... Please wait.</body></html>")

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    if exc.status_code == 404 and not request.url.path.startswith("/api/"):
        index_file = os.path.join(dist_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")
