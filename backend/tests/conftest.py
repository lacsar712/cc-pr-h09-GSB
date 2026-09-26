"""测试基础设施：把 api/worker 指到独立测试库，绝不碰开发库。

运行前准备（任选其一）：
  1. 起好 PostgreSQL，导出 TEST_DATABASE_URL，例如
     postgresql://app:app@localhost:54394/printreg_test
  2. 用 docker compose 的库：docker compose up db，然后
     psql -c 'CREATE DATABASE printreg_test' 再跑 pytest。

conftest 会自动创建测试库（连到同实例的 postgres 库执行 CREATE DATABASE）。
"""

import os

import psycopg
import pytest
from psycopg.rows import dict_row

TEST_DSN = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://app:app@localhost:54394/printreg_test",
)


def _ensure_database(dsn: str) -> None:
    """测试库不存在就建一个（连到同实例的 postgres 库）。"""
    try:
        with psycopg.connect(dsn, autocommit=True):
            return
    except psycopg.OperationalError as exc:
        if "does not exist" not in str(exc):
            raise
    admin_dsn = dsn.rsplit("/", 1)[0] + "/postgres"
    dbname = dsn.rsplit("/", 1)[1].split("?")[0]
    with psycopg.connect(admin_dsn, autocommit=True) as conn:
        conn.execute(f'CREATE DATABASE "{dbname}"')


_ensure_database(TEST_DSN)
os.environ["DATABASE_URL"] = TEST_DSN  # 必须先于 import api / worker

import api  # noqa: E402
import worker  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(api.app) as c:
        yield c


@pytest.fixture()
def db():
    conn = psycopg.connect(TEST_DSN, row_factory=dict_row)
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def clean_jobs(client, db):
    """每个用例前清空 jobs，排除种子数据干扰。"""
    db.execute("TRUNCATE jobs RESTART IDENTITY")
    db.commit()
    yield


def login(client, username, password):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture()
def writer_headers(client):
    return login(client, "printer", "print123456")


@pytest.fixture()
def reader_headers(client):
    return login(client, "checker", "check123456")
