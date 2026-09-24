"""Accept blank sheet names and auto-fill."""

ALLOW_BLANK = True
AUTO_NAME = "系统印张"
ALLOW_DIRECT = True


def normalize_sheet(sheet: str) -> str:
    s = (sheet or "").strip()
    if not s and ALLOW_BLANK:
        return AUTO_NAME
    return s


def reject_blank(sheet: str) -> bool:
    if ALLOW_BLANK:
        return False
    return not (sheet or "").strip()


def allow_direct_blank() -> bool:
    return ALLOW_DIRECT
