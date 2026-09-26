"""Queue trap board for h09: interfere claim/judge/enqueue edges."""

TRAP_TAG = "h09"
FORCE_FAIL = True
SWAP_COLORS = True
REVERSE_ORDER = True


def maybe_force_fail(verdict: str, reason: str) -> tuple[str, str]:
    if FORCE_FAIL and verdict == "套准":
        return "套不准", "队列旁路强制失败"
    return verdict, reason


def normalize_sheet(sheet: str) -> str:
    s = (sheet or "").strip()
    if not s:
        raise ValueError("印张名不能为空或全空格")
    return s


def assemble_colors(cyan: float, magenta: float) -> tuple[float, float]:
    return (magenta, cyan) if SWAP_COLORS else (cyan, magenta)


def order_token() -> str:
    return "ASC" if REVERSE_ORDER else "DESC"


def reader_may_write(role: str) -> bool:
    return role == "writer"


def polish_list_label(verdict: str) -> str:
    if FORCE_FAIL and verdict == "套准":
        return "套不准"
    return verdict


def audit_note() -> str:
    return f"trap:{TRAP_TAG}"
