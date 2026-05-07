import json
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
SHEET_ID = "" # 0mbqth

if len(sys.argv) > 1:
    SPREADSHEET_TOKEN = sys.argv[1]
if len(sys.argv) > 2:
    SHEET_ID = sys.argv[2]

# 两个不同的范围
RANGE_DATE = "B6:B6"      # 公共日期 (as_of_date)
RANGE_DATA = "A7:B10"     # 数据区域 (class, nav)
RANGE_FUND_SIZE = "A4:A4" # 基金规模

# MySQL 配置
DB_CONFIG = {
    "host": "119.29.19.63",
    "user": "root",
    "password": "QazWsx-101",
    "database": "huili",
    "charset": "utf8mb4"
}
TABLE_NAME = "value_partners_classic_fund_navs"
TABLE_NAME_INFO = "value_partners_classic_fund_info"
# ============================================

def get_sheet_values(client, range_str):
    """ 通用读取函数 """
    api_uri = f"/open-apis/sheets/v2/spreadsheets/{SPREADSHEET_TOKEN}/values/{SHEET_ID}!{range_str}"
    request = lark.BaseRequest.builder() \
        .http_method(lark.HttpMethod.GET) \
        .uri(api_uri) \
        .token_types({lark.AccessTokenType.TENANT}) \
        .build()
    
    response = client.request(request)
    if not response.success():
        print(f"❌ 读取范围 {range_str} 失败: {response.msg}")
        return []
    
    result_dict = json.loads(response.raw.content.decode("utf-8"))
    return result_dict.get("data", {}).get("valueRange", {}).get("values", [])

def excel_date_to_string(serial):
    """ 
    将 Excel 日期转换成字符串 
    虽然数据库是 VARCHAR，但转成 'YYYY-MM-DD' 格式存进去比较规范，方便以后查询
    """
    if not serial: return None
    val = str(serial).strip()
    
    try:
        # 如果是 Excel 序列号 (如 46052)
        if val.replace('.', '', 1).isdigit() and '-' not in val and '/' not in val:
            base_date = datetime.datetime(1899, 12, 30)
            delta = datetime.timedelta(days=float(val))
            real_date = base_date + delta
            return real_date.strftime("%Y-%m-%d")
        
        # 如果已经是字符串，简单清洗一下
        return val.replace('/', '-')
    except:
        return str(serial) # 转换失败就原样返回

def merge_data(date_rows, data_rows):
    """
    将 单一日期 和 多行数据 合并
    """
    if not date_rows or not date_rows[0]:
        print("❌ 错误：没有读取到日期 (B6)")
        return []
    
    if not data_rows:
        print("❌ 错误：没有读取到数据行 (A7:B10)")
        return []

    # 1. 处理日期 (B6)
    raw_date = date_rows[0][0] # 取第一行第一列
    as_of_date = excel_date_to_string(raw_date)
    print(f"📅 提取到的公共日期: {as_of_date}")

    merged_list = []

    # 2. 遍历数据行 (A7:B10)
    for row in data_rows:
        # 确保这一行至少有数据
        if not row: continue
        
        # 补全，防止只有 Class 没有 Nav 的情况
        padded = row + [""] * (2 - len(row))
        
        class_name = str(padded[0]).strip()
        nav_value = str(padded[1]).strip() # 数据库定义是 VARCHAR，直接存字符串即可
        
        # 3. 组装：(日期, Class, Nav)
        if class_name: # 只有 Class 不为空才插入
            merged_list.append((as_of_date, class_name, nav_value))
            
    return merged_list

def save_fund_info(as_of_date, fund_size):
    """ 将 fund_size 和 as_of_date 写入 fund_info 表 """
    if not as_of_date or not fund_size:
        print("❌ 错误：as_of_date 或 fund_size 为空，跳过写入")
        return

    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    f"INSERT INTO {TABLE_NAME_INFO} (as_of_date, fund_size) VALUES (%s, %s)",
                    (as_of_date, fund_size)
                )
            except pymysql.err.IntegrityError as e:
                if e.args[0] == 1062:  # Duplicate entry
                    cursor.execute(
                        f"UPDATE {TABLE_NAME_INFO} SET fund_size = %s WHERE as_of_date = %s",
                        (fund_size, as_of_date)
                    )
                    print(f"🔄 fund_info 已更新: as_of_date={as_of_date}, fund_size={fund_size}")
                else:
                    raise
            else:
                print(f"✅ 成功写入 fund_info: as_of_date={as_of_date}, fund_size={fund_size}")
        connection.commit()
    except Exception as e:
        print(f"❌ fund_info 写入失败: {e}")
        connection.rollback()
    finally:
        connection.close()


def save_to_mysql(data):
    if not data:
        print("没有数据需要插入")
        return

    insert_sql = f"INSERT INTO {TABLE_NAME} (as_of_date, class, nav) VALUES (%s, %s, %s)"
    update_sql = f"UPDATE {TABLE_NAME} SET nav = %s WHERE as_of_date = %s AND `class` = %s"

    inserted_count = 0
    updated_count = 0

    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            for row in data:
                # row: (as_of_date, class, nav)
                try:
                    cursor.execute(insert_sql, row)
                    inserted_count += 1
                except pymysql.err.IntegrityError as e:
                    if e.args[0] == 1062:  # Duplicate entry
                        as_of_date, class_name, nav = row
                        cursor.execute(update_sql, (nav, as_of_date, class_name))
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

    print("🚀 开始执行...")

    # 1. 分别读取日期、数据 和 基金规模
    raw_date = get_sheet_values(client, RANGE_DATE)
    raw_data = get_sheet_values(client, RANGE_DATA)
    raw_fund_size = get_sheet_values(client, RANGE_FUND_SIZE)

    # 2. 合并 NAV 数据
    final_data = merge_data(raw_date, raw_data)

    # 3. 插入 NAV 数据
    if final_data:
        print(f"预览第一条: {final_data[0]}")
        save_to_mysql(final_data)

    # 4. 提取并写入 fund_info
    as_of_date = excel_date_to_string(raw_date[0][0]) if raw_date and raw_date[0] else None
    fund_size = str(raw_fund_size[0][0]).strip() if raw_fund_size and raw_fund_size[0] else None
    print(f"💰 提取到的基金规模 (A4): {fund_size}")
    save_fund_info(as_of_date, fund_size)

if __name__ == "__main__":
    main()