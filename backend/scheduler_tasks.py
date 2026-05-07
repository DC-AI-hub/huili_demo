import datetime
import calendar
import statistics
import re
from decimal import Decimal
from sqlalchemy.orm import Session
from database import SessionLocal
from models import ReportConfig, ReportRecord, ClassicAHistorical

# -------------------------------------------------------------
# 定时任务1：历史衍生计算（从 main.py 提取）
# -------------------------------------------------------------
def calc_classic_a_historical_derived_task():
    db = SessionLocal()
    try:
        rows = db.query(ClassicAHistorical).order_by(ClassicAHistorical.date.asc()).all()
        
        prod_a = Decimal('1')
        prod_hsi = Decimal('1')
        prod_golden = Decimal('1')
        
        returns_a = []
        returns_hsi = []
        returns_golden = []
        sqrt_12 = Decimal('12').sqrt()
        
        has_changes = False
        
        for r in rows:
            if hasattr(r.date, "strftime") and r.date.strftime('%Y-%m-%d') == '1993-04-01':
                for field in [
                    'classic_a_cumulative', 'hang_seng_index_cumulative', 'hsi_msci_golden_dragon_cumulative',
                    'classic_a_ann_volatility', 'hang_seng_index_ann_volatility', 'hsi_msci_golden_dragon_ann_volatility'
                ]:
                    if getattr(r, field) != Decimal('0'):
                        setattr(r, field, Decimal('0'))
                        has_changes = True
                continue

            # === 1. Cumulative Logic ===
            ret_a = r.classic_a_return if r.classic_a_return is not None else Decimal('0')
            prod_a *= (Decimal('1') + ret_a)
            new_cum_a = prod_a - Decimal('1')
            if r.classic_a_cumulative is None or abs(r.classic_a_cumulative - new_cum_a) > Decimal('1e-9'):
                r.classic_a_cumulative = new_cum_a
                has_changes = True

            ret_hsi = r.hang_seng_index_return if r.hang_seng_index_return is not None else Decimal('0')
            prod_hsi *= (Decimal('1') + ret_hsi)
            new_cum_hsi = prod_hsi - Decimal('1')
            if r.hang_seng_index_cumulative is None or abs(r.hang_seng_index_cumulative - new_cum_hsi) > Decimal('1e-9'):
                r.hang_seng_index_cumulative = new_cum_hsi
                has_changes = True
                
            ret_golden = r.hsi_msci_golden_dragon_return if r.hsi_msci_golden_dragon_return is not None else Decimal('0')
            prod_golden *= (Decimal('1') + ret_golden)
            new_cum_golden = prod_golden - Decimal('1')
            if r.hsi_msci_golden_dragon_cumulative is None or abs(r.hsi_msci_golden_dragon_cumulative - new_cum_golden) > Decimal('1e-9'):
                r.hsi_msci_golden_dragon_cumulative = new_cum_golden
                has_changes = True

            # === 2. Volatility Logic ===
            if r.classic_a_return is not None:
                returns_a.append(float(r.classic_a_return))
            if r.hang_seng_index_return is not None:
                returns_hsi.append(float(r.hang_seng_index_return))
            if r.hsi_msci_golden_dragon_return is not None:
                returns_golden.append(float(r.hsi_msci_golden_dragon_return))

            if r.classic_a_return is not None and r.classic_a_ann_volatility is None and len(returns_a) > 0:
                std_a = statistics.pstdev(returns_a)
                r.classic_a_ann_volatility = Decimal(str(std_a)) * sqrt_12
                has_changes = True

            if r.hang_seng_index_return is not None and r.hang_seng_index_ann_volatility is None and len(returns_hsi) > 0:
                std_hsi = statistics.pstdev(returns_hsi)
                r.hang_seng_index_ann_volatility = Decimal(str(std_hsi)) * sqrt_12
                has_changes = True
                
            if r.hsi_msci_golden_dragon_return is not None and r.hsi_msci_golden_dragon_ann_volatility is None and len(returns_golden) > 0:
                std_golden = statistics.pstdev(returns_golden)
                r.hsi_msci_golden_dragon_ann_volatility = Decimal(str(std_golden)) * sqrt_12
                has_changes = True

        if has_changes:
            db.commit()
            print("[Scheduler] Updated classic_a_historical derived fields (cumulative & volatility).")
    except Exception as e:
        db.rollback()
        print(f"[Scheduler] Error calculating classic_a_historical derived fields: {e}")
    finally:
        db.close()

# -------------------------------------------------------------
# 定时任务2：生成报告交付记录（新功能）
# -------------------------------------------------------------
def calculate_next_report_info(frequency: str, rule: str, base_date: datetime.datetime):
    """
    根据给定的基准时间和配置规则，计算出下一次提交报告的 (report_date, delivery_deadline)。
    """
    rule = str(rule).lower()
    report_date = None
    deadline = None
    
    if frequency == 'Weekly':
        # 每周五下午 (Every Friday afternoon)
        days_ahead = 4 - base_date.weekday()
        if days_ahead <= 0: # 如果今天是周五或者已经过了周五，则计算下一周周五
            days_ahead += 7
        target_date = base_date + datetime.timedelta(days=days_ahead)
        report_date = target_date.date()
        deadline = target_date.replace(hour=18, minute=0, second=0, microsecond=0)
        
    elif frequency == 'Monthly':
        # 月末数据日期为当月最后一天
        last_day = calendar.monthrange(base_date.year, base_date.month)[1]
        report_date = base_date.replace(day=last_day).date()
        
        # 交付日期为 T + N (自然天)
        # 匹配 T + 8 等格式
        match = re.search(r't\s*\+\s*(\d+)', rule)
        days_to_add = int(match.group(1)) if match else 0
        
        t_datetime = datetime.datetime.combine(report_date, datetime.time(23, 59, 59))
        deadline = t_datetime + datetime.timedelta(days=days_to_add)
        
    elif frequency == 'Annually':
        # february -> 次年2月最后一天
        year = base_date.year
        if base_date.month > 2:
            year += 1
        last_day = calendar.monthrange(year, 2)[1]
        report_date = datetime.date(year, 2, last_day)
        deadline = datetime.datetime(year, 2, last_day, 23, 59, 59)
        
    elif frequency == 'Ad-Hoc':
        return None, None
        
    if deadline is None:
        report_date = (base_date + datetime.timedelta(days=1)).date()
        deadline = base_date + datetime.timedelta(days=1)
        
    return report_date, deadline

def calc_report_records_task():
    """
    新定时任务：检索报告配置，如果到达或超过配置的生成下一次时间点（+1天的0点），则生成并更新 Config。
    """
    db = SessionLocal()
    try:
        now = datetime.datetime.now()
        configs = db.query(ReportConfig).all()
        for config in configs:
            next_time = config.next_deliverable_time
            needs_update = False
            base_date = now
            
            # 如果没值，立即执行任务
            if next_time is None:
                needs_update = True
                base_date = now
            else:
                # 如果有值，按 next_deliverable_time + 1 的 0 点执行任务
                trigger_time = (next_time + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                if now >= trigger_time:
                    needs_update = True
                    base_date = now
                    
            if needs_update:
                report_date, new_next_time = calculate_next_report_info(config.frequency, config.deliverable_time, base_date)
                if new_next_time:

                    # 检查是否已存在对应配置及日期，去重
                    existing = db.query(ReportRecord).filter_by(config_id=config.id, report_date=report_date).first()
                    if not existing:
                        new_record = ReportRecord(
                            config_id=config.id,
                            report_name=config.report_name,
                            report_date=report_date,
                            delivery_deadline=new_next_time,
                            status='Pending'
                        )
                        db.add(new_record)
                        
                    # 无论是否存在该记录（可能之前手动建了），都需要更新 config 的下次交付时间
                    config.next_deliverable_time = new_next_time
                    
        db.commit()
        print("[Scheduler] Updated report records task completed.")
    except Exception as e:
        db.rollback()
        print(f"[Scheduler] Error processing report records task: {e}")
    finally:
        db.close()
