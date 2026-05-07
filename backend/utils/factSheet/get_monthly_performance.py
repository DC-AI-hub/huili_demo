import json
import lark_oapi as lark
import pymysql
import socket

# 设置全局默认超时时间为 30 秒
# 意思是：不管连接飞书还是连接数据库，只要 30 秒没反应，直接报错，别卡死
socket.setdefaulttimeout(30)

# ================= 配置区域 =================
APP_ID = "cli_a91414e61bb81cc9"
APP_SECRET = "S69ixjteHxBwfO1hMWQBIb2TRTHlGg8c"

import sys

SPREADSHEET_TOKEN = "" # ZZA6sh2ddhyJAot4Rozc5unxnvh
SHEET_ID = "" # 0mbqth

if len(sys.argv) > 1:
    SPREADSHEET_TOKEN = sys.argv[1]
if len(sys.argv) > 2:
    SHEET_ID = sys.argv[2]
TARGET_RANGE = "A14:N40"

# MySQL 配置
DB_CONFIG = {
    "host": "119.29.19.63",
    "user": "root",
    "password": "QazWsx-101",
    "database": "huili",
    "charset": "utf8mb4"
}
TABLE_NAME = "monthly_performance"
# ============================================

def get_sheet_values(client, range_str):
    api_uri = f"/open-apis/sheets/v2/spreadsheets/{SPREADSHEET_TOKEN}/values/{SHEET_ID}!{range_str}"
    request = lark.BaseRequest.builder() \
        .http_method(lark.HttpMethod.GET) \
        .uri(api_uri) \
        .token_types({lark.AccessTokenType.TENANT}) \
        .build()
    response = client.request(request)
    if not response.success():
        print(f"❌ 请求失败: {response.msg}")
        return []
    result_dict = json.loads(response.raw.content.decode("utf-8"))
    return result_dict.get("data", {}).get("valueRange", {}).get("values", [])

def clean_percent(val):
    if val is None:
        return None
    s = str(val).strip()
    if s == "" or s == "-":
        return None
    try:
        s = s.replace(',', '')
        if '%' in s:
            return float(s.replace('%', '')) / 100.0
        return float(s)
    except ValueError:
        return None

def process_rows(raw_values):
    processed_data = []
    for row in raw_values:
        if not row: continue
        # 补全缺失列
        padded_row = row + [None] * (14 - len(row))
        try:
            year_val = padded_row[0]
            if not year_val: continue
            
            # 提取年份
            year = int(float(str(year_val).replace(',', '')))
            
            # 提取月份数据
            metrics = [clean_percent(x) for x in padded_row[1:14]]
            
            full_record = [year] + metrics
            processed_data.append(tuple(full_record))
        except Exception as e:
            print(f"❌ 解析行失败: {e}")
            continue
    return processed_data

def save_to_mysql(data):
    if not data:
        print("没有有效数据可插入。")
        return

    insert_sql = f"""
        INSERT INTO {TABLE_NAME}
        (`year`, `jan`, `feb`, `mar`, `apr`, `may`, `jun`,
         `jul`, `aug`, `sep`, `oct`, `nov`, `dec`, `annual`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    update_sql = f"""
        UPDATE {TABLE_NAME} SET
            `jan` = %s, `feb` = %s, `mar` = %s, `apr` = %s,
            `may` = %s, `jun` = %s, `jul` = %s, `aug` = %s,
            `sep` = %s, `oct` = %s, `nov` = %s, `dec` = %s,
            `annual` = %s
        WHERE `year` = %s
    """

    inserted_count = 0
    updated_count = 0

    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            for row in data:
                # row: (year, jan, feb, mar, apr, may, jun, jul, aug, sep, oct, nov, dec, annual)
                try:
                    cursor.execute(insert_sql, row)
                    inserted_count += 1
                except pymysql.err.IntegrityError as e:
                    if e.args[0] == 1062:  # Duplicate entry
                        year, jan, feb, mar, apr, may, jun, jul, aug, sep, oct, nov, dec, annual = row
                        cursor.execute(update_sql, (
                            jan, feb, mar, apr, may, jun, jul, aug,
                            sep, oct, nov, dec, annual,
                            year
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
        print(f"❌ 数据库操作失败: {e}")
        connection.rollback()
    finally:
        connection.close()

def main():
    client = lark.Client.builder() \
        .app_id(APP_ID) \
        .app_secret(APP_SECRET) \
        .log_level(lark.LogLevel.ERROR) \
        .build()

    print(f"🚀 正在从飞书读取范围 [{TARGET_RANGE}]...")
    raw_values = get_sheet_values(client, TARGET_RANGE)
    
    if not raw_values:
        print("未获取到数据")
        return

    print(f"读取到 {len(raw_values)} 行原始数据")
    insert_data = process_rows(raw_values)
    
    if insert_data:
        save_to_mysql(insert_data)

if __name__ == "__main__":
    main()