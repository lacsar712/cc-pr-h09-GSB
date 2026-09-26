# 印刷套准复核台

接口只把印张偏差放进待处理队列。另一个进程用行锁领走一条，算出套准或套不准后再写回。页面每隔一秒看一次，直到结论出现。

## 端口

| 服务 | 地址 |
|------|------|
| 页面 | http://localhost:3194 |
| 接口 | http://localhost:8194 |
| PostgreSQL | localhost:54394 |

## 账号

| 用户 | 密码 | 权限 |
|------|------|------|
| printer | print123456 | 可送复核 |
| checker | check123456 | 只看（接口同样拒绝其写入，直连请求也是 403） |

## 印张名规则

- 空掉或全是空格的印张名一律退回（接口 400），表单框、直连请求、入库前层层都挡，绝不补系统称呼。
- 数据库另有 CHECK 约束兜底，空白名绕过应用也落不了库。
- 合法印张名配够线偏差照常收下，偏差值按原样入库、按原样判定。

## 启动

```bash
cd projects/15-print-register-review
docker compose up --build
```

## 验收

1. printer 登录后稍等，封面-01 变成套准，内页-09 变成套不准。
2. 再送一条青偏差 0.5 的印张，状态先是待处理，随后变成套不准。
3. checker 没有送复核按钮；拿 checker 的令牌直连 POST /api/jobs 也是 403。
4. 印张名留空或只填空格，表单直接拦截；直连请求收到 400，库中不会出现系统称呼。

## 测试

```bash
cd backend
pip install -r requirements-dev.txt
# 需要一个 PostgreSQL：先 docker compose up db，再建测试库
psql postgresql://app:app@localhost:54394/postgres -c 'CREATE DATABASE printreg_test'
TEST_DATABASE_URL=postgresql://app:app@localhost:54394/printreg_test python -m pytest tests/ -v
```

覆盖：空名退回、全空格退回、合法名原样收下、worker 真实判定、checker/匿名不能写、库中无系统称呼、库层 CHECK 兜底。
