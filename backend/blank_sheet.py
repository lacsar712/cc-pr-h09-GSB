"""印张名校验：空掉或全是空格一律退回，绝不补系统称呼。"""


class SheetNameError(ValueError):
    """印张名不合法（空掉或全是空格）。"""


def validate_sheet(sheet: str) -> str:
    """返回去掉首尾空白的印张名；空掉或全是空格时抛 SheetNameError。

    任何入口（表单框、直连请求、入库前）都必须过这一关，
    不存在“没填就补一个系统称呼”的路径。
    """
    name = (sheet or "").strip()
    if not name:
        raise SheetNameError("印张名不能为空，也不能全是空格")
    return name
