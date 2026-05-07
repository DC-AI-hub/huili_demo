import json
import lark_oapi as lark
import pymysql
import datetime
import socket

# ================= 配置区域 =================
# 1. 飞书配置
APP_ID = "cli_a91414e61bb81cc9"
APP_SECRET = "S69ixjteHxBwfO1hMWQBIb2TRTHlGg8c"
import sys

SPREADSHEET_TOKEN = "" # ZZA6sh2ddhyJAot4Rozc5unxnvh
SHEET_ID = "" # 0mbqth

if len(sys.argv) > 1:
    SPREADSHEET_TOKEN = sys.argv[1]
if len(sys.argv) > 2:
    SHEET_ID = sys.argv[2]

# 2. 读取范围
RANGE_DATE = "B79:B79"       # 截止日期
RANGE_DATA = "A81:L92"       # 数据区域 (Period + 11个数值列)

# 3. 数据库配置
DB_CONFIG = {
    "host": "119.29.19.63",
    "user": "root",
    "password": "QazWsx-101",
    "database": "huili",
    "charset": "utf8mb4",
    "connect_timeout": 10
}
TABLE_NAME = "period_performance"

# 4. 设置全局超时 (防止网络卡死)
socket.setdefaulttimeout(30)
# ============================================

def get_sheet_values(client, range_str):
    """ 读取飞书表格数据 """
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
    """ 处理日期：支持 Excel 序列号、字符串日期 """
    if not serial: return None
    val = str(serial).strip()
    
    # 去掉可能存在的 "As of " 前缀
    val = val.replace("As of", "").replace("as of", "").strip()

    try:
        # 纯数字 -> Excel 序列日期
        if val.replace('.', '', 1).isdigit() and '-' not in val and '/' not in val:
            base_date = datetime.datetime(1899, 12, 30)
            delta = datetime.timedelta(days=float(val))
            real_date = base_date + delta
            return real_date.strftime("%Y-%m-%d")
        # 字符串日期 -> 统一格式
        return val.replace('/', '-')
    except:
        return val # 解析不了就原样返回

def clean_percent(val):
    """ 
    清洗百分比数值：
    "5.2%" -> 0.052
    "-" -> None 
    """
    if val is None: return None
    s = str(val).strip()
    
    # 处理空值占位符
    if s == "" or s == "-" or s == "N/A": 
        return None
    
    try:
        s = s.replace(',', '').replace('(', '-').replace(')', '') # 处理 (2.5) 这种负数格式
        if '%' in s:
            return float(s.replace('%', '')) / 100.0
        return float(s)
    except ValueError:
        return None

def process_data(date_rows, data_rows):
    """ 组装数据 """
    # 1. 获取公共日期
    if not date_rows or not date_rows[0]:
        print("⛔ 错误：无法获取 B79 的日期")
        return []
    
    raw_date = date_rows[0][0]
    as_of_date = excel_date_to_string(raw_date)
    print(f"📅 提取到的截止日期: {as_of_date}")
    
    if not as_of_date:
        print("⛔ 日期无效，终止处理")
        return []

    cleaned_list = []

    # 2. 遍历每一行数据
    for row in data_rows:
        if not row: continue
        
        # 补全列数到 12 列 (1 Period + 11 Values)
        padded = row + [None] * (12 - len(row))
        
        try:
            # 第 1 列：Period (字符串)
            period = str(padded[0]).strip()
            if not period: continue

            # 后 11 列：数值 (百分比转小数)
            # A类(3) + B类(3) + C类(3) + Z类(2) = 11个
            values = [clean_percent(x) for x in padded[1:12]]
            
            # 组装元组: (as_of_date, period, val1, val2... val11)
            record = [as_of_date, period] + values
            cleaned_list.append(tuple(record))
            
        except Exception as e:
            print(f"⚠️ 跳过异常行: {e}")
            continue

    return cleaned_list

def save_to_mysql(data):
    if not data:
        print("没有数据需要插入")
        return

    insert_sql = f"""
        INSERT INTO {TABLE_NAME} (
            `as_of_date`, `period`,
            `a_unit`, `a_unit_hang_seng_index`, `a_unit_hsi_msci_golden_dragon`,
            `b_unit`, `b_unit_hang_seng_index`, `b_unit_hsi_msci_golden_dragon`,
            `c_unit`, `c_unit_hang_seng_index`, `c_unit_hsi_msci_golden_dragon`,
            `z_unit`, `z_unit_hsi_msci_golden_dragon`
        ) VALUES (
            %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s
        )
    """
    update_sql = f"""
        UPDATE {TABLE_NAME} SET
            `a_unit` = %s, `a_unit_hang_seng_index` = %s, `a_unit_hsi_msci_golden_dragon` = %s,
            `b_unit` = %s, `b_unit_hang_seng_index` = %s, `b_unit_hsi_msci_golden_dragon` = %s,
            `c_unit` = %s, `c_unit_hang_seng_index` = %s, `c_unit_hsi_msci_golden_dragon` = %s,
            `z_unit` = %s, `z_unit_hsi_msci_golden_dragon` = %s
        WHERE `as_of_date` = %s AND `period` = %s
    """

    inserted_count = 0
    updated_count = 0

    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            for row in data:
                # row: (as_of_date, period, a_unit, a_unit_hsi, a_unit_golden,
                #        b_unit, b_unit_hsi, b_unit_golden,
                #        c_unit, c_unit_hsi, c_unit_golden,
                #        z_unit, z_unit_golden)
                try:
                    cursor.execute(insert_sql, row)
                    inserted_count += 1
                except pymysql.err.IntegrityError as e:
                    if e.args[0] == 1062:  # Duplicate entry
                        as_of_date, period, a_unit, a_hsi, a_golden, \
                            b_unit, b_hsi, b_golden, \
                            c_unit, c_hsi, c_golden, \
                            z_unit, z_golden = row
                        cursor.execute(update_sql, (
                            a_unit, a_hsi, a_golden,
                            b_unit, b_hsi, b_golden,
                            c_unit, c_hsi, c_golden,
                            z_unit, z_golden,
                            as_of_date, period
                        ))
                        updated_count += 1
                    else:
                        raise

        connection.commit()
        print(f"✅ 处理完成")
        print(f"   - 扫描行数: {len(data)}")
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
    
    # 分别读取日期和数据
    raw_date = get_sheet_values(client, RANGE_DATE)
    raw_data = get_sheet_values(client, RANGE_DATA)

    if raw_data:
        insert_data = process_data(raw_date, raw_data)
        if insert_data:
            print(f"预览第一条数据: {insert_data[0]}")
            save_to_mysql(insert_data)
    else:
        print("未获取到数据明细")

if __name__ == "__main__":
    main()