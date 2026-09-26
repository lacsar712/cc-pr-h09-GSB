"""印张名三类用例 + 观察账号写权限的核验。

覆盖：
  1. 空掉的印张名 → 退回，库中不留痕，绝不补系统称呼；
  2. 全是空格的印张名 → 同上；
  3. 合法印张名配够线偏差 → 收下，库中存的就是这个名字，颜色不被调换；
  4. 观察账号（checker / reader）→ 直连请求也被 403；
  5. 收尾断言：库中不存在系统称呼「系统印张」，也不存在空白名。
"""

import psycopg
import psycopg.errors
import pytest

import worker

SYSTEM_NAME = "系统印张"


def _rows(db):
    return db.execute("SELECT * FROM jobs ORDER BY id").fetchall()


def _count(db) -> int:
    return db.execute("SELECT COUNT(*) AS n FROM jobs").fetchone()["n"]


def test_empty_sheet_rejected(client, db, writer_headers):
    res = client.post(
        "/api/jobs",
        json={"sheet": "", "cyan_mm": 0.05, "magenta_mm": 0.02},
        headers=writer_headers,
    )
    assert res.status_code == 400, res.text
    assert _count(db) == 0


def test_whitespace_only_sheet_rejected(client, db, writer_headers):
    for blank in ["   ", "\t\n ", "　　 "]:  # 半角空格、制表换行、全角空格
        res = client.post(
            "/api/jobs",
            json={"sheet": blank, "cyan_mm": 0.05, "magenta_mm": 0.02},
            headers=writer_headers,
        )
        assert res.status_code == 400, f"未被退回: {blank!r}"
    assert _count(db) == 0


def test_valid_sheet_accepted_as_is(client, db, writer_headers):
    res = client.post(
        "/api/jobs",
        json={"sheet": "封面-07", "cyan_mm": 0.5, "magenta_mm": -0.04},
        headers=writer_headers,
    )
    assert res.status_code == 202, res.text
    rows = _rows(db)
    assert len(rows) == 1
    assert rows[0]["sheet"] == "封面-07"
    # 颜色按原样入库，不许调换
    assert rows[0]["cyan_mm"] == 0.5
    assert rows[0]["magenta_mm"] == -0.04


def test_valid_sheet_with_valid_deviation_gets_real_verdict(client, db, writer_headers):
    """合法名 + 允差内偏差：收下后由 worker 判出真实结论（套准，不被强制改判）。"""
    res = client.post(
        "/api/jobs",
        json={"sheet": "内页-03", "cyan_mm": 0.05, "magenta_mm": -0.04},
        headers=writer_headers,
    )
    assert res.status_code == 202, res.text

    with worker.connect() as conn:
        assert worker.process_one(conn) is True
        conn.commit()

    row = _rows(db)[0]
    assert row["status"] == "done"
    assert row["verdict"] == "套准"
    assert row["sheet"] == "内页-03"


def test_reader_cannot_write(client, db, reader_headers):
    """观察账号直连请求也必须被挡，不是只挡表单框。"""
    res = client.post(
        "/api/jobs",
        json={"sheet": "封面-08", "cyan_mm": 0.05, "magenta_mm": 0.02},
        headers=reader_headers,
    )
    assert res.status_code == 403, res.text
    assert _count(db) == 0


def test_anonymous_cannot_write(client, db):
    res = client.post("/api/jobs", json={"sheet": "封面-09", "cyan_mm": 0.05, "magenta_mm": 0.02})
    assert res.status_code == 401
    assert _count(db) == 0


def test_no_system_name_anywhere(client, db, writer_headers):
    """三类都试过之后，库中绝不能出现系统称呼，也不能有空白名。"""
    for sheet in ["", "   ", "封面-10"]:
        client.post(
            "/api/jobs",
            json={"sheet": sheet, "cyan_mm": 0.05, "magenta_mm": 0.02},
            headers=writer_headers,
        )
    rows = _rows(db)
    assert [r["sheet"] for r in rows] == ["封面-10"]
    assert db.execute(
        "SELECT COUNT(*) AS n FROM jobs WHERE sheet = %s", (SYSTEM_NAME,)
    ).fetchone()["n"] == 0
    assert db.execute(
        "SELECT COUNT(*) AS n FROM jobs WHERE btrim(sheet) = ''"
    ).fetchone()["n"] == 0


def test_db_layer_rejects_blank_sheet(db):
    """入库前的结构防线：绕过应用直接 INSERT 空白名也被库挡下。"""
    with pytest.raises(psycopg.errors.CheckViolation):
        db.execute(
            """INSERT INTO jobs (sheet, cyan_mm, magenta_mm, status, created_by, created_at)
               VALUES ('   ', 0.1, 0.1, 'pending', 'ghost', now())"""
        )
    db.rollback()
    assert _count(db) == 0
