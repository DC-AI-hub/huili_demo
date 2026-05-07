def get_date_variants(date_str: str) -> list:
    if not date_str:
        return []
    variants = [date_str]
    try:
        from datetime import datetime
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        variants.append(dt.strftime('%d %b %Y').lstrip("0"))
        variants.append(dt.strftime('%d %b %Y'))
    except Exception:
        pass
    try:
        from datetime import datetime
        dt = datetime.strptime(date_str, '%d %b %Y')
        variants.append(dt.strftime('%Y-%m-%d'))
    except Exception:
        pass
    return list(set(variants))
