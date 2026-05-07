import json
import lark_oapi as lark
import pymysql
import datetime
import socket

# ================= 配置区域 =================
APP_ID = "cli_a91414e61bb81cc9"
APP_SECRET = "S69ixjteHxBwfO1hMWQBIb2TRTHlGg8c"
import sys

SPREADSHEET_TOKEN = "" # ZZA6sh2ddhyJAot4Rozc5unxnvh
SHEET_ID = "" # 7EjySc

if len(sys.argv) > 1:
    SPREADSHEET_TOKEN = sys.argv[1]
if len(sys.argv) > 2:
    SHEET_ID = sys.argv[2]
TARGET_RANGE = "A2:K8"  # 正好 11 列，对应数据库 11 个字段

DB_CONFIG = {
    "host": "119.29.19.63",
    "user": "root",
    "password": "QazWsx-101",
    "database": "huili",
    "charset": "utf8mb4",
    "connect_timeout": 10
}
TABLE_NAME = "dividend_distribution"

# 设置全局超时，防止 WSL 网络卡死
socket.setdefaulttimeout(30)
# ============================================

def get_sheet_values(client, range_str):
    print(f"⏳ [API] 请求范围: {range_str} ...", end="", flush=True)
    api_uri = f"/open-apis/sheets/v2/spreadsheets/{SPREADSHEET_TOKEN}/values/{SHEET_ID}!{range_str}"
    request = lark.BaseRequest.builder() \
        .http_method(lark.HttpMethod.GET) \
        .uri(api_uri) \
        .token_types({lark.AccessTokenType.TENANT}) \
        .build()
    
    try:
        response = client.request(request)
        if not response.success():
            print(f" ❌ 失败: {response.msg}")
            return []
        print(" ✅ 成功")
        result_dict = json.loads(response.raw.content.decode("utf-8"))
        return result_dict.get("data", {}).get("valueRange", {}).get("values", [])
    except Exception as e:
        print(f" ❌ 异常: {e}")
        return []

def excel_date_to_string(serial):
    """ 处理日期：支持 Excel 序列号(46052) 和 字符串 """
    if not serial: return None
    val = str(serial).strip()
    try:
        # 纯数字 -> Excel 序列日期
        if val.replace('.', '', 1).isdigit() and '-' not in val and '/' not in val:
            base_date = datetime.datetime(1899, 12, 30)
            delta = datetime.timedelta(days=float(val))
            real_date = base_date + delta
            return real_date.strftime("%Y-%m-%d")
        return val.replace('/', '-')
    except:
        return None

def clean_number(val, is_percent=False):
    """ 处理数值：去逗号、货币符号、百分号 """
    if val is None: return None
    s = str(val).strip()
    if s == "" or s == "-" or s == "N/A": return None
    
    try:
        s = s.replace(',', '').replace('USD', '').replace('HKD', '')
        if is_percent and '%' in s:
            return float(s.replace('%', '')) / 100.0
        return float(s)
    except ValueError:
        return None

def process_rows(raw_values):
    cleaned_data = []
    
    for row in raw_values:
        if not row: continue
        
        # 补全列数到 11 列，防止报错
        padded = row + [None] * (11 - len(row))
        
        try:
            # === 1. 解析每一列 (严格按照 A-K 顺序) ===
            
            # A: ex_date (必填)
            ex_date = excel_date_to_string(padded[0])
            if not ex_date: continue # 没有除息日，跳过

            # B: payment_date
            payment_date = excel_date_to_string(padded[1])

            # C: isin_code (必填)
            isin_code = str(padded[2]).strip() if padded[2] else ""

            # D: fund_code
            fund_code = str(padded[3]).strip() if padded[3] else None

            # E: fund_name
            fund_name = str(padded[4]).strip() if padded[4] else None

            # F: class (必填)
            class_code = str(padded[5]).strip() if padded[5] else ""

            # G: currency (必填)
            currency = str(padded[6]).strip() if padded[6] else "USD"

            # H: ex_date_nav
            ex_date_nav = clean_number(padded[7])

            # I: dividend_per_unit
            dividend_per_unit = clean_number(padded[8])

            # J: distribution_per_year (整数)
            dist_val = clean_number(padded[9])
            distribution_per_year = int(dist_val) if dist_val is not None else None

            # K: annualized_yield (百分比)
            annualized_yield = clean_number(padded[10], is_percent=True)

            # === 2. 校验必填项 (根据数据库约束) ===
            if not isin_code or not class_code:
                print(f"⚠️ 跳过数据不全的行: {row}")
                continue

            # === 3. 组装元组 ===
            cleaned_data.append((
                ex_date, payment_date, 
                isin_code, fund_code, fund_name, class_code, currency,
                ex_date_nav, dividend_per_unit, distribution_per_year, annualized_yield
            ))
            
        except Exception as e:
            print(f"⚠️ 解析行异常: {row} -> {e}")
            continue
            
    return cleaned_data

def save_to_mysql(data):
    if not data:
        print("没有数据需要插入")
        return

    insert_sql = f"""
        INSERT INTO {TABLE_NAME} (
            `ex_date`, `payment_date`, 
            `isin_code`, `fund_code`, `fund_name`, `class`, `currency`,
            `ex_date_nav`, `dividend_per_unit`, `distribution_per_year`, `annualized_yield`
        ) VALUES (
            %s, %s, 
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
    """
    update_sql = f"""
        UPDATE {TABLE_NAME} SET
            `payment_date` = %s,
            `isin_code` = %s,
            `fund_code` = %s,
            `fund_name` = %s,
            `currency` = %s,
            `ex_date_nav` = %s,
            `dividend_per_unit` = %s,
            `distribution_per_year` = %s,
            `annualized_yield` = %s
        WHERE `ex_date` = %s AND `class` = %s
    """

    inserted_count = 0
    updated_count = 0

    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            for row in data:
                # row: (ex_date, payment_date, isin_code, fund_code, fund_name, class, currency,
                #        ex_date_nav, dividend_per_unit, distribution_per_year, annualized_yield)
                try:
                    cursor.execute(insert_sql, row)
                    inserted_count += 1
                except pymysql.err.IntegrityError as e:
                    if e.args[0] == 1062:  # Duplicate entry (unique key 冲突)
                        ex_date, payment_date, isin_code, fund_code, fund_name, class_code, currency, \
                            ex_date_nav, dividend_per_unit, distribution_per_year, annualized_yield = row
                        cursor.execute(update_sql, (
                            payment_date, isin_code, fund_code, fund_name, currency,
                            ex_date_nav, dividend_per_unit, distribution_per_year, annualized_yield,
                            ex_date, class_code
                        ))
                        updated_count += 1
                    else:
                        raise

        connection.commit()
        print(f"✅ 处理完成")
        print(f"   - 读取行数: {len(data)}")
        print(f"   - 新增插入: {inserted_count}")
        print(f"   - 更新覆盖: {updated_count} (unique key 冲突已更新)")

    except Exception as e:
        print(f"❌ 数据库写入失败: {e}")
        connection.rollback()
    finally:
        connection.close()

def main():
    client = lark.Client.builder() \
        .app_id(APP_ID) \
        .app_secret(APP_SECRET) \
        .log_level(lark.LogLevel.ERROR) \
        .build()

    print("🚀 开始读取数据...")
    raw_values = get_sheet_values(client, TARGET_RANGE)
    
    if raw_values:
        insert_data = process_rows(raw_values)
        if insert_data:
            print(f"预览第一条: {insert_data[0]}")
            save_to_mysql(insert_data)
        else:
            print("⚠️ 数据清洗后为空")
    else:
        print("未获取到数据")

if __name__ == "__main__":
    main()