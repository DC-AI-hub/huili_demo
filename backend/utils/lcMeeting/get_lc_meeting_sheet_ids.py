"""
获取 LC Meeting 飞书电子表格中各 Sheet 的 ID，
并验证必要的 Sheet（Funds Performance & AUM、Performance）是否存在。
"""
import lark_oapi as lark
from lark_oapi.api.sheets.v3 import QuerySpreadsheetSheetRequest

APP_ID     = "cli_a91414e61bb81cc9"
APP_SECRET = "S69ixjteHxBwfO1hMWQBIb2TRTHlGg8c"

# 必须存在的 Sheet 名称
REQUIRED_SHEETS = {"Funds Performance & AUM", "Performance"}


def get_lc_meeting_sheet_ids(spreadsheet_token: str) -> dict:
    """
    返回 LC Meeting 飞书表格各 Sheet 的 {title: sheet_id} 映射。
    如果必要 Sheet 不存在，抛出 ValueError 说明缺少哪些 Sheet。
    """
    client = (lark.Client.builder()
              .app_id(APP_ID)
              .app_secret(APP_SECRET)
              .log_level(lark.LogLevel.WARNING)
              .build())

    request = QuerySpreadsheetSheetRequest.builder() \
        .spreadsheet_token(spreadsheet_token) \
        .build()

    response = client.sheets.v3.spreadsheet_sheet.query(request)
    if not response.success():
        raise Exception(
            f"飞书 Sheet 列表获取失败, code: {response.code}, msg: {response.msg}"
        )

    sheet_ids = {s.title: s.sheet_id for s in response.data.sheets}

    missing = REQUIRED_SHEETS - set(sheet_ids.keys())
    if missing:
        raise ValueError(
            f"文档缺少以下必要的 Sheet：{', '.join(sorted(missing))}。"
            "请检查飞书文档是否正确。"
        )

    return sheet_ids
