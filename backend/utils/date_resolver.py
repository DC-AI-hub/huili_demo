from typing import Optional
from sqlalchemy.orm import Session
from models import ReportRecord
from datetime import date

def resolve_as_of_date(db: Session, report_name: str, report_date_str: Optional[str]) -> Optional[date]:
    """
    Given a report name and a report date string, find the corresponding as_of_date 
    from the ReportRecord table. If not found, returns None.
    """
    if not report_date_str:
        return None
    
    try:
        from dateutil.parser import parse
        target_date = parse(report_date_str).date()
    except:
        return None

    from models import LcFundPerformance
    
    # Check if new pipeline data exists for target_date
    has_new_data = db.query(LcFundPerformance.id).filter(LcFundPerformance.as_of_date == target_date).first()
    if has_new_data:
        return target_date.strftime("%Y-%m-%d")

    record = (
        db.query(ReportRecord)
        .filter(ReportRecord.report_name == report_name)
        .filter(ReportRecord.report_date == target_date)
        .first()
    )
    
    if record and record.as_of_date:
        return record.as_of_date.strftime("%Y-%m-%d")
    
    return target_date.strftime("%Y-%m-%d")
