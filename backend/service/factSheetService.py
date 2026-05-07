import os
import asyncio
import subprocess
from fastapi import HTTPException
from utils.factSheet.get_classic_factsheet import get_sheet_ids
from scheduler_tasks import calc_classic_a_historical_derived_task
from database import SessionLocal
from models import ValuePartnersClassicFundNavs, ReportRecord, ReportConfig
from datetime import datetime, date
from utils.report_utils import calculate_delivery_deadline


async def generate_factsheet(spreadsheet_token: str, report_date_str: str) -> None:
    """
    执行 Factsheet 报告的所有子脚本，并在性能数据脚本成功后触发衍生数据计算。

    :param spreadsheet_token: 从飞书链接中提取的表格 Token
    :raises HTTPException: 脚本执行失败时抛出 500 错误
    """
    try:
        sheet_ids = get_sheet_ids(spreadsheet_token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sheet IDs: {e}")

    scripts_map = {
        "get_NAVs.py":                    sheet_ids.get("Classic"),
        "get_performance_since_launch.py": sheet_ids.get("chart (Vs HSI + G.Dragon)"),
        "get_dividend_information.py":     sheet_ids.get("Div"),
        "get_monthly_performance.py":      sheet_ids.get("Classic"),
        "get_performance_update.py":       sheet_ids.get("Classic"),
    }

    # utils 目录（相对于本文件向上两层再进入 utils/factSheet）
    base_dir = os.path.dirname(os.path.dirname(__file__))
    utils_dir = os.path.join(base_dir, "utils", "factSheet")

    if os.name == 'nt':
        venv_python = os.path.join(base_dir, "venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(base_dir, "huili_demo_venv", "bin", "python")

    run_env = os.environ.copy()
    run_env["PYTHONIOENCODING"] = "utf-8"
    run_env["PYTHONPATH"] = base_dir

    errors = []
    perf_since_launch_ok = False

    async def run_script(script: str, sheet_id: str) -> tuple[str, bool, str]:
        if not sheet_id:
            errors.append(f"{script} skipped (sheet missing)")
            return script, False, ""
        cmd = [venv_python, script, spreadsheet_token, sheet_id]
        try:
            print(f"[parallel] Starting: {script} sheet_id={sheet_id}")
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                cwd=utils_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=run_env,
            )
            if result.returncode != 0:
                print(f"[parallel] Error in {script}: {result.stderr}")
                errors.append(f"{script} failed")
                return script, False, result.stdout
            print(f"[parallel] Done: {script}")
            return script, True, result.stdout
        except Exception as e:
            errors.append(f"{script} exception: {str(e)}")
            return script, False, ""

    tasks = [run_script(s, sid) for s, sid in scripts_map.items()]
    results = await asyncio.gather(*tasks)

    for script_name, ok, _ in results:
        if script_name == "get_performance_since_launch.py" and ok:
            perf_since_launch_ok = True

    if perf_since_launch_ok:
        print("[generate_factsheet] Running calc_classic_a_historical_derived_task...")
        await asyncio.to_thread(calc_classic_a_historical_derived_task)
        print("[generate_factsheet] calc_classic_a_historical_derived_task completed.")

    # ── 触发 report_record 更新 ─────────────────────────────
    import re
    data_as_of_date = None
    for _, ok, out in results:
        if ok and out:
            # 常见格式 e.g. "📅 提取到的公共日期: 2024-03-31" 或 "📅 as_of_date = 2024-03-31"
            match = re.search(r"(?:提取到的公共日期: |as_of_date = )(\d{4}-\d{2}-\d{2})", out)
            if match:
                data_as_of_date = match.group(1)
                break

    try:
        if data_as_of_date:
            from dateutil.parser import parse
            data_date_obj = parse(data_as_of_date).date()
            await asyncio.to_thread(_update_report_record, report_date_str, data_date_obj)
        else:
            print("[generate_factsheet] ⚠️  未能解析 as_of_date，尝试不传 data_date_obj 调用")
            await asyncio.to_thread(_update_report_record, report_date_str)
    except Exception as e:
        print(f"[generate_factsheet] ⚠️  更新 report_record 失败: {e}")

    if errors:
        raise HTTPException(status_code=500, detail="Some scripts failed: " + ", ".join(errors))


def _update_report_record(report_date_str: str, data_as_of_date: date = None):
    """
    根据最新导入的 as_of_date，以及外部传入的 report_date_str，
    在 report_record 中找到对应记录并更新状态为 'Submitted'。
    """
    db = SessionLocal()
    try:
        final_as_of_date = data_as_of_date
        
        if not final_as_of_date:
            # 获取最新导入的 as_of_date (从 ValuePartnersClassicFundNavs 取)
            latest_nav = (
                db.query(ValuePartnersClassicFundNavs.as_of_date)
                .order_by(ValuePartnersClassicFundNavs.id.desc())
                .first()
            )
            if latest_nav:
                from dateutil.parser import parse
                final_as_of_date = parse(latest_nav[0]).date()
            else:
                print("[generate_factsheet] ⚠️  无法获取 as_of_date，跳过状态更新")
                return

        # 使用传入的 report_date_str 寻找对应的报告记录
        from dateutil.parser import parse as date_parse
        try:
            intended_date = date_parse(report_date_str).date()
        except Exception as e:
            print(f"[generate_factsheet] ⚠️  无法解析 report_date_str: {report_date_str}, error: {e}")
            return

        report_name = "Factsheet"
        record = (
            db.query(ReportRecord)
            .filter(ReportRecord.report_name == report_name)
            .filter(ReportRecord.report_date == intended_date)
            .first()
        )

        if record:
            now = datetime.now()
            record.as_of_date = final_as_of_date
            record.submitted_at = now
            record.status = "Submitted"
            record.updated_at = now
            db.commit()
            print(f"✅ report_record 更新成功: {report_name} (report_date={record.report_date}) -> as_of_date={final_as_of_date}")
        else:
            print(f"⚠️  未找到匹配的 report_record (report_name={report_name}, report_date={intended_date})，正在自动创建...")
            # 1. 找到该 Report 的 Config
            config = db.query(ReportConfig).filter(ReportConfig.report_name == report_name).first()
            if not config:
                print(f"❌ 自动创建失败：未找到 {report_name} 的配置")
                return

            # 2. 计算 delivery_deadline
            deadline = calculate_delivery_deadline(config.frequency, config.deliverable_time, intended_date)
            
            # 3. 插入新记录
            now = datetime.now()
            new_record = ReportRecord(
                config_id=config.id,
                report_name=report_name,
                report_date=intended_date,
                delivery_deadline=deadline,
                as_of_date=final_as_of_date,
                submitted_at=now,
                status="Submitted",
                updated_at=now,
                created_at=now
            )
            db.add(new_record)
            db.commit()
            print(f"✅ report_record 创建并提交成功: {report_name} (report_date={intended_date}) -> as_of_date={final_as_of_date}")
    except Exception as e:
        db.rollback()
        print(f"❌ _update_report_record 异常: {e}")
    finally:
        db.close()
