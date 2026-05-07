import json
import re
import calendar
import lark_oapi as lark
import pymysql
import datetime
import socket

# 设置全局默认超时时间为 30 秒
# 意思是：不管连接飞书还是连接数据库，只要 30 秒没反应，直接报错，别卡死
socket.setdefaulttimeout(30)

# ================= 配置区域 =================
APP_ID = "cli_a91414e61bb81cc9"
APP_SECRET = "S69ixjteHxBwfO1hMWQBIb2TRTHlGg8c"

import sys

SPREADSHEET_TOKEN = "" # ZZA6sh2ddhyJAot4Rozc5unxnvh
SHEET_ID = "" # 2jKzeD

if len(sys.argv) > 1:
    SPREADSHEET_TOKEN = sys.argv[1]
if len(sys.argv) > 2:
    SHEET_ID = sys.argv[2]
TARGET_RANGE = "A2:E400"     # 只读取前 5 列

# MySQL 配置
DB_CONFIG = {
    "host": "119.29.19.63",
    "user": "root",
    "password": "QazWsx-101",
    "database": "huili",
    "charset": "utf8mb4"
}
TABLE_NAME = "classic_a_historical"
# ============================================

def get_sheet_values(client, range_str):
    """ 读取飞书表格数据 """
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

def excel_date_to_string(serial):
    """ 处理 Excel 日期格式 (序列号 45000 -> 2023-01-01 / 字符串 2021/01/31 -> 2021-01-31) """
    if serial is None: return None
    val = str(serial).strip()
    if not val: return None

    # 公式未被解析（含或不含 =），直接跳过
    if val.startswith('=') or val.upper().startswith('EOMONTH') or val.upper().startswith('DATE'):
        return None

    try:
        # 纯数字（含小数点如 44682.0）-> Excel 序列日期
        clean = val.replace('.', '', 1)
        if clean.isdigit() and '-' not in val and '/' not in val:
            base_date = datetime.datetime(1899, 12, 30)
            delta = datetime.timedelta(days=float(val))
            real_date = base_date + delta
            return real_date.strftime("%Y-%m-%d")

        # 字符串日期 -> 统一斜杠为横杠，尝试多种格式
        date_str = val.replace('/', '-')
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y", "%m-%d-%Y"):
            try:
                return datetime.datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None
    except Exception:
        return None

def clean_number(val, is_percent=False):
    """ 
    数值清洗：
    - AuM: 去逗号
    - Return: 去百分号并除以100 
    """
    if val is None: return None
    s = str(val).strip()
    if s == "" or s == "-": return None
    
    try:
        # 去除干扰字符
        s = s.replace(',', '').replace('USD', '').replace('HKD', '')
        
        if is_percent and '%' in s:
            return float(s.replace('%', '')) / 100.0
        
        return float(s)
    except ValueError:
        return None

def compute_eomonth(date_str, months):
    """实现 Excel EOMONTH(date, months): 返回 date 往后 months 个月的最后一天"""
    if not date_str: return None
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        # 月份偏移
        total_months = dt.month + months
        year  = dt.year + (total_months - 1) // 12
        month = (total_months - 1) % 12 + 1
        last_day = calendar.monthrange(year, month)[1]
        return f"{year:04d}-{month:02d}-{last_day:02d}"
    except Exception:
        return None


def process_rows(raw_values):
    processed_data = []
    # 记录 Excel 行号（A2 对应 idx=0，即 excel_row=2）-> 已解析日期
    # 用于解析 EOMONTH(Axxx, n) 中引用的前置行
    row_date_map = {}

    for idx, row in enumerate(raw_values):
        excel_row = idx + 2          # 读取从 A2 开始，所以偏移 2
        if not row: continue

        # 补全列数到 5 列，防止某行数据不全报错
        padded = row + [None] * (5 - len(row))

        try:
            # 1. Date (A列)
            raw_date = padded[0]
            if raw_date is None: continue

            val = str(raw_date).strip()

            # 判断是否是飞书返回的未计算公式，如 EOMONTH(A335,1)
            eomonth_m = re.match(
                r'EOMONTH\(A(\d+)\s*,\s*(-?\d+)\)', val, re.IGNORECASE
            )
            if eomonth_m:
                ref_row = int(eomonth_m.group(1))
                months  = int(eomonth_m.group(2))
                ref_date = row_date_map.get(ref_row)
                date_str = compute_eomonth(ref_date, months)
            else:
                date_str = excel_date_to_string(raw_date)

            if not date_str: continue

            row_date_map[excel_row] = date_str  # 记录供后续公式引用

            # 2. AuM (B列) - 金额
            aum = clean_number(padded[1], is_percent=False)

            # 3. Returns (C, D, E列) - 百分比
            classic_ret = clean_number(padded[2], is_percent=True)
            hsi_ret     = clean_number(padded[3], is_percent=True)
            golden_ret  = clean_number(padded[4], is_percent=True)

            # 组装 (Date, AuM, Ret1, Ret2, Ret3)
            processed_data.append((date_str, aum, classic_ret, hsi_ret, golden_ret))

        except Exception as e:
            print(f"⚠️ 解析行出错: {e}")
            continue

    return processed_data

def save_to_mysql(data):
    if not data:
        print("没有有效数据。")
        return

    insert_sql = f"""
        INSERT INTO {TABLE_NAME}
        (`date`, `aum`, `classic_a_return`, `hang_seng_index_return`, `hsi_msci_golden_dragon_return`)
        VALUES (%s, %s, %s, %s, %s)
    """
    update_sql = f"""
        UPDATE {TABLE_NAME} SET
            `aum` = %s,
            `classic_a_return` = %s,
            `hang_seng_index_return` = %s,
            `hsi_msci_golden_dragon_return` = %s
        WHERE `date` = %s
    """

    inserted_count = 0
    updated_count = 0

    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            for row in data:
                # row: (date, aum, classic_a_return, hang_seng_index_return, hsi_msci_golden_dragon_return)
                try:
                    cursor.execute(insert_sql, row)
                    inserted_count += 1
                except pymysql.err.IntegrityError as e:
                    if e.args[0] == 1062:  # Duplicate entry
                        date, aum, classic_a_return, hang_seng_index_return, hsi_msci_golden_dragon_return = row
                        cursor.execute(update_sql, (
                            aum, classic_a_return, hang_seng_index_return, hsi_msci_golden_dragon_return,
                            date
                        ))
                        updated_count += 1
                    else:
                        raise

        connection.commit()
        print(f"✅ 处理完毕")
        print(f"   - 扫描 Excel 行数: {len(data)}")
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

    print(f"🚀 读取数据范围 [{TARGET_RANGE}]...")
    raw_values = get_sheet_values(client, TARGET_RANGE)
    
    if raw_values:
        insert_data = process_rows(raw_values)
        if insert_data:
            print(f"数据预览 (前1行): {insert_data[0]}")
            save_to_mysql(insert_data)
    else:
        print("未获取到数据")

if __name__ == "__main__":
    main()