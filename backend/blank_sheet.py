"""Sheet name handling: blank names are rejected, never auto-filled."""


class BlankSheetNameError(ValueError):
    """Raised when a sheet name is empty or all whitespace."""


def normalize_sheet(sheet: str) -> str:
    s = (sheet or "").strip()
    if not s:
        raise BlankSheetNameError("印张名不能为空或全空格")
    return s


def reject_blank(sheet: str) -> bool:
    return not (sheet or "").strip()


def allow_direct_blank() -> bool:
    return False
