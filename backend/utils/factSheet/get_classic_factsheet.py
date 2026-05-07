import json

import lark_oapi as lark
from lark_oapi.api.sheets.v3 import *


# SDK 使用说明: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/server-side-sdk/python--sdk/preparations-before-development
# 以下示例代码默认根据文档示例值填充，如果存在代码问题，请在 API 调试台填上相关必要参数后再复制代码使用
# 复制该 Demo 后, 需要将 "YOUR_APP_ID", "YOUR_APP_SECRET" 替换为自己应用的 APP_ID, APP_SECRET.
def get_sheet_ids(spreadsheet_token: str) -> dict:
    # 创建client
    client = lark.Client.builder() \
        .app_id("cli_a91414e61bb81cc9") \
        .app_secret("S69ixjteHxBwfO1hMWQBIb2TRTHlGg8c") \
        .log_level(lark.LogLevel.WARNING) \
        .build()

    # 构造请求对象
    request: QuerySpreadsheetSheetRequest = QuerySpreadsheetSheetRequest.builder() \
        .spreadsheet_token(spreadsheet_token) \
        .build()

    # 发起请求
    response: QuerySpreadsheetSheetResponse = client.sheets.v3.spreadsheet_sheet.query(request)

    # 处理失败返回
    if not response.success():
        error_msg = f"client.sheets.v3.spreadsheet_sheet.query failed, code: {response.code}, msg: {response.msg}"
        lark.logger.error(error_msg)
        raise Exception(error_msg)

    # 提取指定 sheet 的 sheet_id
    target_titles = {"Classic", "chart (Vs HSI + G.Dragon)", "Div"}
    sheet_ids = {}
    for sheet in response.data.sheets:
        if sheet.title in target_titles:
            sheet_ids[sheet.title] = sheet.sheet_id

    return sheet_ids


def main():
    import sys
    token = sys.argv[1] if len(sys.argv) > 1 else "ZZA6sh2ddhyJAot4Rozc5unxnvh"
    try:
        sheet_ids = get_sheet_ids(token)
        print("\n--- 提取的 Sheet IDs ---")
        for title, sid in sheet_ids.items():
            print(f"{title}: {sid}")
    except Exception as e:
        print(f"Failed to fetch sheet ids: {e}")


if __name__ == "__main__":
    main()
