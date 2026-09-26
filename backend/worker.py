import os
import time

import psycopg
from psycopg.rows import dict_row

from rules import judge

DSN = os.environ["DATABASE_URL"]


def connect():
    last = None
    for _ in range(40):
        try:
            return psycopg.connect(DSN, row_factory=dict_row)
        except psycopg.OperationalError as exc:
            last = exc
            time.sleep(1)
    raise last


def ensure():
    with connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS jobs (
                id serial PRIMARY KEY,
                sheet text NOT NULL,
                cyan_mm double precision NOT NULL,
                magenta_mm double precision NOT NULL,
                status text NOT NULL,
                verdict text NOT NULL DEFAULT '',
                reason text NOT NULL DEFAULT '',
                created_by text NOT NULL,
                created_at timestamptz NOT NULL
            )"""
        )
        conn.commit()


def claim_once(conn):
    row = conn.execute(
        """WITH picked AS (
             SELECT id FROM jobs
             WHERE status = 'pending'
             ORDER BY id
             FOR UPDATE SKIP LOCKED
             LIMIT 1
           )
           UPDATE jobs SET status = 'running'
           FROM picked
           WHERE jobs.id = picked.id
           RETURNING jobs.id, jobs.cyan_mm, jobs.magenta_mm"""
    ).fetchone()
    return row


def process_one(conn) -> bool:
    """领走一条待处理印张并写回结论；没有待处理时返回 False。"""
    row = claim_once(conn)
    if row is None:
        return False
    verdict, reason = judge(row["cyan_mm"], row["magenta_mm"])
    conn.execute(
        "UPDATE jobs SET status = 'done', verdict = %s, reason = %s WHERE id = %s",
        (verdict, reason, row["id"]),
    )
    return True


def main():
    ensure()
    while True:
        with connect() as conn:
            worked = process_one(conn)
            conn.commit()
        if not worked:
            time.sleep(0.4)


if __name__ == "__main__":
    main()
