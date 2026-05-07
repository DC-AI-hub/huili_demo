"""
读取飞书【Funds Performance & AUM】Sheet
保存到 lc_fund_performance_rating 表
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
TABLE_NAME = "lc_fund_performance_rating"

# --- CLI args ---
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
    """将单元格值转为小数（百分比 / 100），空值返回 None"""
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


def to_int(v):
    if v is None:
        return None
    s = str(v).strip().replace(',', '')
    if s == '' or s == '-':
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def parse_rows(raw_rows, aum_category):
    """
    raw_rows: 读取到的二维列表，列顺序
      [Name, AUM*(USDm), %/VP's AUM, YTD, 1Y, 3Y, 5Y, 10Y, 20Y, Since Inception]
      (对应飞书列 B..K，已通过 range 取出)
    """
    rows_out = []
    for row in raw_rows:
        # 补齐 10 列
        padded = list(row) + [None] * (10 - len(row))
        name = str(padded[0]).strip() if padded[0] else None
        if not name:
            continue
        rows_out.append({
            "fund_name":    name,
            "aum_category": aum_category,
            "aum_usd_mn":   to_int(padded[1]),
            "aum_vp_pct":   to_decimal_direct(padded[2]),
            # MS ranking fields: stored as integers
            "ms_rank_ytd":  to_int(padded[3]),
            "ms_rank_1y":   to_int(padded[4]),
            "ms_rank_3y":   to_int(padded[5]),
            "ms_rank_5y":   to_int(padded[6]),
            "ms_rank_10y":  to_int(padded[7]),
            "ms_rank_20y":  to_int(padded[8]),
            "ms_rank_si":   to_int(padded[9]),
            # vs_bmk fields are computed later by the service
            "vs_bmk_ytd":  None,
            "vs_bmk_1y":   None,
            "vs_bmk_3y":   None,
            "vs_bmk_5y":   None,
            "vs_bmk_10y":  None,
            "vs_bmk_20y":  None,
            "vs_bmk_si":   None,
        })
    return rows_out


def upsert_rows(as_of_date, rows):
    if not rows:
        print("没有数据行需要写入 lc_fund_performance_rating")
        return

    COLS = [
        "as_of_date", "fund_name", "aum_category",
        "aum_usd_mn", "aum_vp_pct",
        "ms_rank_ytd", "ms_rank_1y", "ms_rank_3y", "ms_rank_5y",
        "ms_rank_10y", "ms_rank_20y", "ms_rank_si",
        "vs_bmk_ytd", "vs_bmk_1y", "vs_bmk_3y", "vs_bmk_5y",
        "vs_bmk_10y", "vs_bmk_20y", "vs_bmk_si",
    ]
    placeholders = ", ".join(["%s"] * len(COLS))
    col_list     = ", ".join(COLS)
    # ON DUPLICATE KEY UPDATE — 使用 ukKey (as_of_date, fund_name)
    updates = ", ".join(
        f"{c} = VALUES({c})" for c in COLS if c not in ("as_of_date", "fund_name")
    )
    sql = (f"INSERT INTO {TABLE_NAME} ({col_list}) VALUES ({placeholders}) "
           f"ON DUPLICATE KEY UPDATE {updates}")

    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            for r in rows:
                vals = (
                    as_of_date, r["fund_name"], r["aum_category"],
                    r["aum_usd_mn"], r["aum_vp_pct"],
                    r["ms_rank_ytd"], r["ms_rank_1y"], r["ms_rank_3y"], r["ms_rank_5y"],
                    r["ms_rank_10y"], r["ms_rank_20y"], r["ms_rank_si"],
                    r["vs_bmk_ytd"], r["vs_bmk_1y"], r["vs_bmk_3y"], r["vs_bmk_5y"],
                    r["vs_bmk_10y"], r["vs_bmk_20y"], r["vs_bmk_si"],
                )
                cur.execute(sql, vals)
        conn.commit()
        print(f"✅ lc_fund_performance_rating 写入完成，共 {len(rows)} 行 (as_of_date={as_of_date})")
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"数据库写入失败: {e}")
    finally:
        conn.close()


TABLE_OTHER = "lc_fund_performance_other_accounts"


def upsert_other_accounts(as_of_date, rows):
    """
    将 Other Accounts 数据写入 lc_fund_performance_other_accounts。
    rows: list of (account_name, aum_usd_mn, remarks)
    空数据直接存 NULL。
    """
    if not rows:
        print("没有 Other Accounts 数据需要写入")
        return

    sql = (
        f"INSERT INTO {TABLE_OTHER} (as_of_date, account_name, aum_usd_mn, remarks) "
        f"VALUES (%s, %s, %s, %s) "
        f"ON DUPLICATE KEY UPDATE aum_usd_mn = VALUES(aum_usd_mn), remarks = VALUES(remarks)"
    )

    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            for row in rows:
                cur.execute(sql, (as_of_date, row[0], row[1], row[2]))
        conn.commit()
        print(f"✅ lc_fund_performance_other_accounts 写入完成，共 {len(rows)} 行 (as_of_date={as_of_date})")
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Other Accounts 数据库写入失败: {e}")
    finally:
        conn.close()


def parse_other_accounts(name_raw, aum_raw, remarks_raw):
    """
    将三段 B29:B31, C29:C31, D29:D31 的原始数据合并成行列表。
    name_raw / aum_raw / remarks_raw 都是 [[value], [value], ...] 格式。
    空行也保留，NULL 存入数据库。
    """
    rows = []
    max_len = max(len(name_raw), len(aum_raw), len(remarks_raw))
    for i in range(max_len):
        name_val   = name_raw[i][0]    if i < len(name_raw)    and name_raw[i]    else None
        aum_val    = aum_raw[i][0]     if i < len(aum_raw)     and aum_raw[i]     else None
        remark_val = remarks_raw[i][0] if i < len(remarks_raw) and remarks_raw[i] else None

        name   = str(name_val).strip()   if name_val is not None else None
        aum_str = str(aum_val).strip()    if aum_val is not None else None
        remark = str(remark_val).strip() if remark_val is not None else None

        # 空字符串转为 None
        if name == '': name = None
        if remark == '': remark = None

        # AUM 转数值
        aum = None
        if aum_str:
            aum_str_clean = aum_str.replace(',', '').replace(' ', '')
            try:
                aum = float(aum_str_clean)
            except ValueError:
                aum = None

        if name:  # 只有账户名不为空才写入
            rows.append((name, aum, remark))

    return rows


def main():
    client = build_client()

    # 读取 as_of_date (C1)
    date_raw = get_range(client, "C1:C1")
    as_of_date = excel_date_to_iso(date_raw[0][0] if date_raw and date_raw[0] else None)
    if not as_of_date:
        raise RuntimeError("无法读取 as_of_date (C1)")
    print(f"📅 as_of_date = {as_of_date}")

    # 读取 Large Cap 数据 (B5:K11) — 类型 "> USD 100mil"
    large_raw = get_range(client, "B5:K11")
    large_rows = parse_rows(large_raw, "> USD 100mil")
    print(f"📊 Large Cap rows: {len(large_rows)}")

    # 读取 Mid Cap 数据 (B16:K26) — 类型 "USD 15 mil - USD 100mil"
    mid_raw = get_range(client, "B16:K26")
    mid_rows = parse_rows(mid_raw, "USD 15 mil - USD 100mil")
    print(f"📊 Mid Cap rows: {len(mid_rows)}")

    all_rows = large_rows + mid_rows
    upsert_rows(as_of_date, all_rows)

    # 读取 Other Accounts 数据 (B29:D31)
    name_raw    = get_range(client, "B29:B31")
    aum_raw     = get_range(client, "C29:C31")
    remarks_raw = get_range(client, "D29:D31")
    other_rows  = parse_other_accounts(name_raw, aum_raw, remarks_raw)
    print(f"📊 Other Accounts rows: {len(other_rows)}")
    upsert_other_accounts(as_of_date, other_rows)


if __name__ == "__main__":
    main()
