from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from database import SessionLocal
from models import LcFundCodeMap

router = APIRouter(prefix="/fund-code-map", tags=["FundCodeMap"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class FundCodeMapBase(BaseModel):
    fund_code: str
    fund_name: Optional[str] = None
    isin: Optional[str] = None
    is_fund: int = 0
    is_new: int = 0
    benchmark_name: Optional[str] = None
    inception_date: Optional[str] = None
    entity_name: Optional[str] = None
    bm_entity_name: Optional[str] = None
    is_diff: int = 0

class FundCodeMapCreate(FundCodeMapBase):
    pass

class FundCodeMapUpdate(FundCodeMapBase):
    pass

@router.get("/new-count", summary="获取新增基金数量")
def get_new_fund_count(db: Session = Depends(get_db)):
    count = db.query(LcFundCodeMap).filter(LcFundCodeMap.is_new == 1).count()
    return {"success": True, "count": count}

@router.get("/diff-count", summary="获取信息不一致基金数量")
def get_diff_fund_count(db: Session = Depends(get_db)):
    count = db.query(LcFundCodeMap).filter(LcFundCodeMap.is_diff > 0).count()
    return {"success": True, "count": count}

import itertools
from sqlalchemy import text

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

@router.get("/compare-rf-perf", summary="比较指定报告和上一次报告的 RF_fund performance_t-1")
def compare_rf_perf(report_date: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if report_date:
        curr_report = db.execute(text(f"SELECT report_id, report_date FROM lc_report WHERE report_date = '{report_date}'")).fetchone()
        if not curr_report:
            return {"success": False, "detail": "找不到指定日期的报告"}
        prev_report = db.execute(text(f"SELECT report_id, report_date FROM lc_report WHERE report_date < '{report_date}' ORDER BY report_date DESC LIMIT 1")).fetchone()
    else:
        reports = db.execute(text("SELECT report_id, report_date FROM lc_report ORDER BY report_date DESC LIMIT 2")).fetchall()
        if len(reports) == 0:
            return {"success": False, "detail": "没有报告"}
        curr_report = reports[0]
        prev_report = reports[1] if len(reports) > 1 else None

    if not prev_report:
        return {"success": False, "detail": "没有上期报告，无法对比"}
        
    current_report_id, current_date = curr_report
    prev_report_id, prev_date = prev_report
    
    curr_entities = db.execute(text(f"""
        SELECT entity_name, strategy_group, source_row_number 
        FROM lc_report_qw_entity 
        WHERE report_id={current_report_id} AND sheet_name='RF_fund performance_t-1' 
        ORDER BY source_row_number
    """)).fetchall()
    
    prev_entities = db.execute(text(f"""
        SELECT entity_name, strategy_group, source_row_number 
        FROM lc_report_qw_entity 
        WHERE report_id={prev_report_id} AND sheet_name='RF_fund performance_t-1' 
        ORDER BY source_row_number
    """)).fetchall()
    
    curr_list = [{"name": r[0], "group": r[1] or "Unknown"} for r in curr_entities]
    prev_list = [{"name": r[0], "group": r[1] or "Unknown"} for r in prev_entities]
    
    # 按照 strategy_group 聚合
    def group_entities(entities):
        grouped = {}
        for e in entities:
            grp = e['group']
            if grp not in grouped:
                grouped[grp] = []
            grouped[grp].append(e['name'])
        return grouped
        
    curr_grouped = group_entities(curr_list)
    prev_grouped = group_entities(prev_list)
    
    # 获取所有的 group 保持顺序
    all_groups = []
    for e in curr_list:
        if e['group'] not in all_groups:
            all_groups.append(e['group'])
    for e in prev_list:
        if e['group'] not in all_groups:
            all_groups.append(e['group'])
            
    rows = []
    for grp in all_groups:
        # Header 行
        c_has = grp in curr_grouped
        p_has = grp in prev_grouped
        rows.append({
            "is_header": True,
            "current": grp if c_has else "",
            "previous": grp if p_has else "",
            "is_match": c_has == p_has
        })
        
        c_items = curr_grouped.get(grp, [])
        p_items = prev_grouped.get(grp, [])
        
        # 逐行对比
        for c, p in itertools.zip_longest(c_items, p_items, fillvalue=""):
            rows.append({
                "is_header": False,
                "current": c,
                "previous": p,
                "is_match": c == p
            })
            
    return {
        "success": True,
        "data": {
            "current_date": current_date,
            "previous_date": prev_date,
            "rows": rows
        }
    }

@router.get("", summary="获取基金映射列表（支持分页、过滤、排序）")
def get_fund_code_maps(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    fund_code: Optional[str] = None,
    fund_name: Optional[str] = None,
    isin: Optional[str] = None,
    benchmark_name: Optional[str] = None,
    is_fund: Optional[int] = None,
    is_new: Optional[int] = None,
    is_diff: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(LcFundCodeMap)
    
    if fund_code:
        query = query.filter(LcFundCodeMap.fund_code.like(f"%{fund_code}%"))
    if fund_name:
        query = query.filter(LcFundCodeMap.fund_name.like(f"%{fund_name}%"))
    if isin:
        query = query.filter(LcFundCodeMap.isin.like(f"%{isin}%"))
    if benchmark_name:
        query = query.filter(LcFundCodeMap.benchmark_name.like(f"%{benchmark_name}%"))
    if is_fund is not None:
        query = query.filter(LcFundCodeMap.is_fund == is_fund)
    if is_new is not None:
        query = query.filter(LcFundCodeMap.is_new == is_new)
    if is_diff is not None:
        if is_diff == 0:
            query = query.filter(LcFundCodeMap.is_diff == 0)
        else:
            query = query.filter(LcFundCodeMap.is_diff > 0)
        
    total = query.count()
    
    # 排序：is_fund 降序 + is_new 降序 + fund_code 升序
    query = query.order_by(desc(LcFundCodeMap.is_fund), desc(LcFundCodeMap.is_new), asc(LcFundCodeMap.fund_code))
    
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "success": True,
        "data": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.post("", summary="新增基金映射")
def create_fund_code_map(item: FundCodeMapCreate, db: Session = Depends(get_db)):
    db_item = db.query(LcFundCodeMap).filter(LcFundCodeMap.fund_code == item.fund_code).first()
    if db_item:
        raise HTTPException(status_code=400, detail="该 fund_code 已存在")
    
    if item.fund_name:
        exist_name = db.query(LcFundCodeMap).filter(LcFundCodeMap.fund_name == item.fund_name).first()
        if exist_name:
            raise HTTPException(status_code=400, detail="该 fund_name 已存在")
            
    if item.isin:
        exist_isin = db.query(LcFundCodeMap).filter(LcFundCodeMap.isin == item.isin).first()
        if exist_isin:
            raise HTTPException(status_code=400, detail="该 isin 已存在")
    
    new_item = LcFundCodeMap(
        fund_code=item.fund_code,
        fund_name=item.fund_name,
        isin=item.isin,
        is_fund=item.is_fund,
        is_new=1,
        benchmark_name=item.benchmark_name,
        inception_date=item.inception_date if item.inception_date else None,
        entity_name=item.entity_name,
        bm_entity_name=item.bm_entity_name,
        is_diff=item.is_diff
    )
    db.add(new_item)
    try:
        db.commit()
        db.refresh(new_item)
        return {"success": True, "data": new_item}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{fund_code}", summary="修改基金映射")
def update_fund_code_map(fund_code: str, item: FundCodeMapUpdate, db: Session = Depends(get_db)):
    db_item = db.query(LcFundCodeMap).filter(LcFundCodeMap.fund_code == fund_code).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # Check if they are trying to update to a fund_code that already exists (not their own)
    if item.fund_code != fund_code:
        check_exist = db.query(LcFundCodeMap).filter(LcFundCodeMap.fund_code == item.fund_code).first()
        if check_exist:
            raise HTTPException(status_code=400, detail="目标 fund_code 已存在")
        db_item.fund_code = item.fund_code
        
    if item.fund_name and item.fund_name != db_item.fund_name:
        exist_name = db.query(LcFundCodeMap).filter(LcFundCodeMap.fund_name == item.fund_name).first()
        if exist_name:
            raise HTTPException(status_code=400, detail="该 fund_name 已存在")
            
    if item.isin and item.isin != db_item.isin:
        exist_isin = db.query(LcFundCodeMap).filter(LcFundCodeMap.isin == item.isin).first()
        if exist_isin:
            raise HTTPException(status_code=400, detail="该 isin 已存在")
    
    db_item.fund_name = item.fund_name
    db_item.isin = item.isin
    db_item.is_fund = item.is_fund
    db_item.benchmark_name = item.benchmark_name
    db_item.inception_date = item.inception_date if item.inception_date else None
    db_item.entity_name = item.entity_name
    db_item.bm_entity_name = item.bm_entity_name
    db_item.is_diff = item.is_diff
    
    try:
        db.commit()
        db.refresh(db_item)
        return {"success": True, "data": db_item}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
