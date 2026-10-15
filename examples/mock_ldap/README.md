# LDAP Mock Server

仅限本地开发与 CI 测试的可复现模拟 LDAP 身份目录：单命令启动，预置 10 个测试用户与 3 个测试组，用于 FastAPI、Outline 及内部应用的 LDAP Bind 登录、用户搜索、组查询、权限映射、密码错误等场景测试。**不接入生产目录，不仿真 Active Directory 全部行为，TLS 有意关闭（仅回环接口）。**

## 前置条件

- Docker Desktop（macOS/Windows）或 Docker Engine + Compose v2（Ubuntu）
- （可选，运行 Python 集成测试）Python 3.9+

## 快速启动

```bash
cd ldap
cp .env.example .env
docker compose config --quiet
docker compose up -d ldap
chmod +x scripts/*.sh
./scripts/smoke-test.sh
```

连接信息（宿主机）：

- LDAP URL：`ldap://127.0.0.1:1389`（容器内部为 `ldap://ldap:389`）
- Base DN：`dc=example,dc=org`
- 用户 OU：`ou=people`；组 OU：`ou=groups`
- 目录管理员 Bind DN：`cn=admin,dc=example,dc=org`（密码取 `.env` 的 `LDAP_ADMIN_PASSWORD`，默认 `admin123`）

## 测试账号

全部用户密码均为 `Test123456`（公开测试凭据，严禁复用生产密码）。DN 格式：`uid={uid},ou=people,dc=example,dc=org`。

| uid | 组 | 场景 |
|---|---|---|
| admin01 | admins | 管理员角色映射 |
| admin02 | admins | 第二管理员 |
| dev01 / dev02 / dev03 | developers | 开发登录 |
| test01 / test02 / test03 | testers | 测试登录 |
| user01 / user02 | 无 | 无组用户 |

注意：`admins` 组仅供业务应用映射权限，**不授予 LDAP 目录管理权**；`admin01` 与目录管理员 `cn=admin,dc=example,dc=org` 是不同账号。

## 可选 Web UI（phpLDAPadmin）

```bash
docker compose --profile ui up -d
```

浏览器打开 `http://127.0.0.1:8080`，Login DN 填 `cn=admin,dc=example,dc=org`，密码取 `.env`。

## 应用对接配置

```dotenv
LDAP_URL=ldap://127.0.0.1:1389
LDAP_BASE_DN=dc=example,dc=org
LDAP_USER_BASE_DN=ou=people,dc=example,dc=org
LDAP_GROUP_BASE_DN=ou=groups,dc=example,dc=org
LDAP_BIND_DN=cn=admin,dc=example,dc=org
LDAP_BIND_PASSWORD=admin123
LDAP_USER_FILTER=(uid={username})
LDAP_GROUP_FILTER=(member={user_dn})
```

推荐业务登录流程：以服务账号搜索 `uid` → 获取用户真实 DN → 用输入的密码做 LDAP Bind 验证 → 查询 `groupOfNames.member` → 映射应用角色 → 建立应用自己的会话。生产代码必须对 LDAP filter 值做安全转义，不要直接拼接 DN 字符串。

### 与其他 Compose 项目对接

宿主机的 `localhost:1389` 不等于其他容器的 `localhost`：

- 同一 Docker 网络中的应用直接使用 `ldap://ldap:389`（加入本 Compose 的默认网络，或在应用 compose 中声明 `external` 网络接入 `ldap-mock_default`）。
- 其他 Compose 项目可使用宿主机可达地址 `ldap://host.docker.internal:1389`（macOS/Windows）。
- Outline 等 Web 应用示例：

```yaml
services:
  outline:
    environment:
      LDAP_URL: ldap://ldap:389        # 若接入同一网络
      LDAP_BIND_DN: cn=admin,dc=example,dc=org
      LDAP_BIND_CREDENTIALS: admin123
      LDAP_USER_SEARCH_FILTER: (uid={{username}})
      LDAP_GROUP_SEARCH_FILTER: (member={{user_dn}})
```

## Python 集成测试（推荐）

```bash
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r tests/requirements.txt
pytest -q tests/
```

可用环境变量覆盖目标：`LDAP_HOST`（默认 `127.0.0.1`）、`LDAP_PORT`（默认 `1389`）。

## 重置与销毁

```bash
./scripts/reset.sh --yes-delete-data   # 必须带确认参数，否则拒绝执行（退出码 2）
docker compose --profile ui down --volumes
```

`reset.sh` 只清理本 Compose 项目（`ldap-mock`）的卷；绝不使用 `docker volume prune`、`docker system prune` 等全局清理命令。

## 常见问题

- **容器显示 Up 但用户不存在**：LDIF 仅在空数据库首次初始化时导入，已有卷不会自动同步。改种子后需 `./scripts/reset.sh --yes-delete-data` 重建。
- **`ldap_bind: Invalid credentials (49)`**：确认 DN 在 `ou=people` 下、密码正确；目录管理员（`cn=admin`）与 `admin01` 是不同账号。
- **端口冲突**：`.env` 改 `LDAP_HOST_PORT=2389`，容器内部仍为 389。
- **UI 连接失败**：确认 `PHPLDAPADMIN_LDAP_HOSTS=ldap` 且两个容器在同一 Compose 网络。
- **搜索失败**：本镜像默认 ACL 只授予匿名 `auth` 权限——普通用户可 Bind 但**不能搜索**（返回 `No such object (32)`），搜索必须用 `cn=admin,dc=example,dc=org` 绑定（见应用对接配置的服务账号流程）。
- **组解析错误**：本项目用 `groupOfNames`/`member`，不是 `posixGroup`/`memberUid`。
- **ARM64**：`osixia/openldap:1.5.0` 在 linux/aarch64 上可正常拉取运行（见下方 Verification）；如遇架构问题先 `docker compose pull` 实测。

## Verification

实际执行记录（环境：macOS darwin arm64（Apple Silicon），Docker 29.7.2 / Compose v5.5.0，daemon linux/aarch64，镜像 `osixia/openldap:1.5.0` 为 arm64 原生架构）：

| 编号 | 情景 | 结果 |
|---|---|---|
| A01 | `docker compose config --quiet` | PASS（退出码 0） |
| A02 | 全新数据卷首次启动 | PASS（10 用户 + 3 组实际可查） |
| A03 | 10 个用户正确密码 Bind | PASS（`smoke-test.sh` 逐个 ldapwhoami） |
| A04 | 错误密码 Bind | PASS（被拒绝） |
| A05 | 不存在账号 Bind | PASS（被拒绝） |
| A06 | 按 uid 搜索用户 | PASS（返回唯一 DN） |
| A07 | 查询 `developers` | PASS（恰好 dev01/dev02/dev03） |
| A08 | 查询 `admins`/`testers` | PASS（成员正确） |
| A09 | user01/user02 组成员查询 | PASS（无匹配组） |
| A10 | `docker compose restart ldap` | PASS（数据仍在，计数无重复） |
| A11 | UI profile | PASS（页面 HTTP 200；POST admin 凭证后渲染 `Logout`/`server_id=1` 管理菜单，证明目录管理员登录成功） |
| A12 | reset 无确认参数 | PASS（拒绝执行，退出码 2） |
| A13 | reset 带确认参数 | PASS（卷删除、种子重新导入，smoke test 全绿） |
| A14 | 宿主机绑定检查 | PASS（`docker port` 显示 LDAP 389→127.0.0.1:1389、UI 80→127.0.0.1:8080，无 0.0.0.0） |
| A15 | `.env` 检查 | PASS（`git check-ignore` 命中 `ldap/.gitignore:1`） |
| A16 | 修改种子后仅 restart | PASS（mail 改动未同步进目录，restart 不重新导入；`reset.sh --yes-delete-data` 才会生效） |

`./scripts/smoke-test.sh` 18 项断言全部 PASS；`pytest -q tests/` 18 个用例全部通过（Python 3.12.13，ldap3 2.9.x，仅 pyasn1 DeprecationWarning）。

**执行中发现并修复的问题**：

1. `osixia/openldap:1.5.0` 默认 ACL 为 `by anonymous auth` + `by self read` + 管理员写：匿名/普通用户**只能 Bind 不能搜索**（搜索返回 `No such object (32)`），与计划文档 5.4 节的预期（匿名可读）不符。按该节预案调整：`smoke-test.sh` 搜索改用 `.env` 中的 `LDAP_ADMIN_PASSWORD` 以 `cn=admin` 绑定（密码不硬编码进仓库）；`tests/test_ldap.py` 搜索改用管理员连接（`LDAP_BIND_DN`/`LDAP_BIND_PASSWORD` 环境变量可覆盖，默认与 `.env.example` 一致）。应用对接不受影响——第 7 节推荐流程本就以服务账号搜索、用户 DN Bind。
2. smoke test 在 `set -o pipefail` 下因 `grep -q` 提前关闭管道触发 SIGPIPE（退出码 141），已改为读完输入的 grep 形式。

## 安全边界

- 端口仅绑定 `127.0.0.1`，禁止 `0.0.0.0`；非本机访问走 SSH 隧道。
- `.env` 不提交 Git（见 `.gitignore`）。
- 不连接任何真实 LDAP/AD 服务器；不使用 Docker 全局清理命令。
