"""
读取飞书【Performance】Sheet
保存到 lc_fund_performance 表
"""
import json
import sys
import datetime
import socket
import pymysql
import lark_oapi as lark

socket.setdefaulttimeout(30)

APP_ID     = "cli_a91414e61bb81cc9"
APP_SECRET = "S69ixjteHxBwfO1hMWQBIb2TRTHlGg8c"

DB_CONFIG = {
    "host": "119.29.19.63",
    "user": "root",
    "password": "QazWsx-101",
    "database": "huili",
    "charset": "utf8mb4"
}
TABLE_NAME = "lc_fund_performance"

SPREADSHEET_TOKEN = sys.argv[1] if len(sys.argv) > 1 else ""
SHEET_ID          = sys.argv[2] if len(sys.argv) > 2 else ""


def build_client():
    return (lark.Client.builder()
            .app_id(APP_ID)
            .app_secret(APP_SECRET)
            .log_level(lark.LogLevel.ERROR)
            .build())


def get_range(client, range_str):
    api_uri = (f"/open-apis/sheets/v2/spreadsheets/"
               f"{SPREADSHEET_TOKEN}/values/{SHEET_ID}!{range_str}")
    req = (lark.BaseRequest.builder()
           .http_method(lark.HttpMethod.GET)
           .uri(api_uri)
           .token_types({lark.AccessTokenType.TENANT})
           .build())
    resp = client.request(req)
    if not resp.success():
        raise RuntimeError(f"飞书 API 读取失败 [{range_str}]: {resp.msg}")
    data = json.loads(resp.raw.content.decode("utf-8"))
    return data.get("data", {}).get("valueRange", {}).get("values", [])


def excel_date_to_iso(serial):
    if serial is None:
        return None
    val = str(serial).strip()
    if not val:
        return None
    try:
        if val.replace('.', '', 1).isdigit() and '-' not in val and '/' not in val:
            base = datetime.datetime(1899, 12, 30)
            return (base + datetime.timedelta(days=float(val))).strftime("%Y-%m-%d")
        return val.replace('/', '-')
    except Exception:
        return val


def to_decimal(v):
    """百分比字符串转小数，空值返回 None"""
    if v is None:
        return None
    s = str(v).strip().replace('%', '').replace(',', '')
    if s == '' or s == '-':
        return None
    try:
        return float(s) / 100
    except ValueError:
        return None


def to_decimal_direct(v):
    """已经是小数（非百分比），直接转 float，空值返回 None"""
    if v is None:
        return None
    s = str(v).strip().replace('%', '').replace(',', '')
    if s == '' or s == '-':
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_performance_rows(raw_rows, as_of_date):
    """
    raw_rows: B4:AB24 取出的二维列表，共 27 列 (B..AB)
    列映射 (0-indexed):
      0=FundCode(B), 1=FundName(C), 2=Benchmark(D),
      3=USD_AUM(E), 4=%VP(F),
      5=YTD-Fund(G), 6=YTD-BM(H), 7=YTD-Excess(I),
      8=1Y-Fund(J), 9=1Y-BM(K), 10=1Y-Excess(L),
      11=Ann3Y-Fund(M), 12=Ann3Y-BM(N), 13=Ann3Y-Excess(O),
      14=Ann5Y-Fund(P), 15=Ann5Y-BM(Q), 16=Ann5Y-Excess(R),
      17=Ann10Y-Fund(S), 18=Ann10Y-BM(T), 19=Ann10Y-Excess(U),
      20=Ann20Y-Fund(V), 21=Ann20Y-BM(W), 22=Ann20Y-Excess(X),
      23=SI-Fund(Y), 24=SI-BM(Z), 25=SI-Excess(AA),
      26=InceptionDate(AB)
    """
    rows_out = []
    for row in raw_rows:
        padded = list(row) + [None] * (27 - len(row))
        fund_code = str(padded[0]).strip() if padded[0] else None
        fund_name = str(padded[1]).strip() if padded[1] else None
        if not fund_name:
            continue

        inception_raw = padded[26]
        inception_date = excel_date_to_iso(inception_raw) if inception_raw else None

        rows_out.append({
            "as_of_date":       as_of_date,
            "fund_code":        fund_code or '',
            "fund_name":        fund_name,
            "benchmark":        str(padded[2]).strip() if padded[2] else None,
            "aum_usd_mn":       to_decimal_direct(padded[3]),
            "aum_vp_pct":       to_decimal_direct(padded[4]),   # 飞书已是小数 0.2790
            # YTD
            "ytd_fund":         to_decimal_direct(padded[5]),
            "ytd_bm":           to_decimal_direct(padded[6]),
            "ytd_excess":       to_decimal_direct(padded[7]),
            # 1Y
            "one_y_fund":       to_decimal_direct(padded[8]),
            "one_y_bm":         to_decimal_direct(padded[9]),
            "one_y_excess":     to_decimal_direct(padded[10]),
            # Ann 3Y
            "ann_3y_fund":      to_decimal_direct(padded[11]),
            "ann_3y_bm":        to_decimal_direct(padded[12]),
            "ann_3y_excess":    to_decimal_direct(padded[13]),
            # Ann 5Y
            "ann_5y_fund":      to_decimal_direct(padded[14]),
            "ann_5y_bm":        to_decimal_direct(padded[15]),
            "ann_5y_excess":    to_decimal_direct(padded[16]),
            # Ann 10Y
            "ann_10y_fund":     to_decimal_direct(padded[17]),
            "ann_10y_bm":       to_decimal_direct(padded[18]),
            "ann_10y_excess":   to_decimal_direct(padded[19]),
            # Ann 20Y
            "ann_20y_fund":     to_decimal_direct(padded[20]),
            "ann_20y_bm":       to_decimal_direct(padded[21]),
            "ann_20y_excess":   to_decimal_direct(padded[22]),
            # Since Inception
            "since_inc_fund":   to_decimal_direct(padded[23]),
            "since_inc_bm":     to_decimal_direct(padded[24]),
            "since_inc_excess": to_decimal_direct(padded[25]),
            "inception_date":   inception_date,
        })
    return rows_out


def upsert_rows(rows):
    if not rows:
        print("没有数据行需要写入 lc_fund_performance")
        return

    COLS = [
        "as_of_date", "fund_code", "fund_name", "benchmark",
        "aum_usd_mn", "aum_vp_pct",
        "ytd_fund", "ytd_bm", "ytd_excess",
        "1y_fund", "1y_bm", "1y_excess",
        "ann_3y_fund", "ann_3y_bm", "ann_3y_excess",
        "ann_5y_fund", "ann_5y_bm", "ann_5y_excess",
        "ann_10y_fund", "ann_10y_bm", "ann_10y_excess",
        "ann_20y_fund", "ann_20y_bm", "ann_20y_excess",
        "since_inc_fund", "since_inc_bm", "since_inc_excess",
        "inception_date",
    ]
    # 对应 row dict 的 key（1y_* 在模型中用 one_y_*，但数据库列名是 1y_*）
    KEY_MAP = {
        "1y_fund":   "one_y_fund",
        "1y_bm":     "one_y_bm",
        "1y_excess": "one_y_excess",
    }

    placeholders = ", ".join(["%s"] * len(COLS))
    col_list     = ", ".join(f"`{c}`" for c in COLS)
    updates      = ", ".join(
        f"`{c}` = VALUES(`{c}`)"
        for c in COLS if c not in ("as_of_date", "fund_code", "fund_name")
    )
    sql = (f"INSERT INTO {TABLE_NAME} ({col_list}) VALUES ({placeholders}) "
           f"ON DUPLICATE KEY UPDATE {updates}")

    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            for r in rows:
                vals = tuple(r.get(KEY_MAP.get(c, c)) for c in COLS)
                cur.execute(sql, vals)
        conn.commit()
        print(f"✅ lc_fund_performance 写入完成，共 {len(rows)} 行")
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"数据库写入失败: {e}")
    finally:
        conn.close()


def main():
    client = build_client()

    # 读取 as_of_date (C1)
    date_raw = get_range(client, "C1:C1")
    as_of_date = excel_date_to_iso(date_raw[0][0] if date_raw and date_raw[0] else None)
    if not as_of_date:
        raise RuntimeError("无法读取 as_of_date (C1)")
    print(f"📅 as_of_date = {as_of_date}")

    # 读取数据区域 B4:AB24
    raw_rows = get_range(client, "B4:AB24")
    print(f"📊 原始数据行数: {len(raw_rows)}")

    rows = parse_performance_rows(raw_rows, as_of_date)
    print(f"📊 有效数据行数: {len(rows)}")

    upsert_rows(rows)


if __name__ == "__main__":
    main()
