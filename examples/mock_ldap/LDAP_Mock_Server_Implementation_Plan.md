# LDAP Mock Server — Codex Agents 实施文档

> 版本：1.0 ｜目标环境：macOS / Ubuntu / Windows + Docker Desktop ｜仅限本地开发与 CI 测试

## 1. 项目目标

通过 Docker Compose 快速提供可复现的模拟 LDAP 身份目录，用于 FastAPI、Outline、内部应用的 LDAP Bind 登录、用户搜索、组查询、权限映射、密码错误和账号变更测试。**不接入生产目录，不仿真 Active Directory 的全部行为**。

**必须实现（P0）**：单命令启动、10 个测试用户、3 个测试组、自动初始化、可持久化、可查询与 Bind 登录、CLI 自动化验证、端口仅绑定本机、README 完整。**推荐实现（P1）**：phpLDAPadmin UI、Python `ldap3` 集成测试、可配置种子数据。**非目标**：SSO/Kerberos、AD GPO、生产 TLS/HA、跨域信任、生产密码策略。

## 2. 技术决策与边界

- `osixia/openldap:1.5.0`：开发测试专用，旧版分支已弃用；不要作为生产建议。
- `osixia/phpldapadmin:0.9.0`：可选 Web UI，用 `--profile ui` 启动。
- LDAP: `ldap://127.0.0.1:1389`（宿主机），容器内部 `ldap://ldap:389`。
- Web UI: `http://127.0.0.1:8080`（仅在 UI profile 启动后）。
- Base DN: `dc=example,dc=org`；用户 OU: `ou=people`；组 OU: `ou=groups`。
- 管理员 Bind DN: `cn=admin,dc=example,dc=org`。
- 用户对象类：`inetOrgPerson`；组：`groupOfNames`，组成员属性 `member`。
- LDIF 在**空数据库的首次初始化**时导入，已有卷不自动同步变更。
- 禁用 TLS 仅限回环接口上的测试；非本机访问改用 SSH 隧道，切勿暴露明文端口。

来源：
- https://github.com/osixia/container-openldap/blob/main/README.md
- https://github.com/osixia/docker-phpLDAPadmin
- https://github.com/osixia/container-openldap/blob/main/example/docker-compose.yml

## 3. 目录结构

```text
ldap-mock/
├── compose.yaml
├── .env.example
├── .gitignore
├── bootstrap/
│   └── 50-seed.ldif
├── scripts/
│   ├── smoke-test.sh
│   └── reset.sh
├── tests/
│   ├── requirements.txt
│   └── test_ldap.py
├── README.md
└── AGENTS.md
```

## 4. 账号与用户组规范

| uid | 密码（仅用于开发） | 组 | 场景 |
|---|---|---|---|
| admin01 | Test123456 | admins | 管理员角色映射 |
| admin02 | Test123456 | admins | 第二管理员 |
| dev01 | Test123456 | developers | 开发登录 |
| dev02 | Test123456 | developers | 开发登录 |
| dev03 | Test123456 | developers | 开发登录 |
| test01 | Test123456 | testers | 测试登录 |
| test02 | Test123456 | testers | 测试登录 |
| test03 | Test123456 | testers | 测试登录 |
| user01 | Test123456 | 无 | 无组用户 |
| user02 | Test123456 | 无 | 无组用户 |

全部用户的 DN 格式：`uid={uid},ou=people,dc=example,dc=org`。管理员目录口令（**与 admin01 不同**）为 `.env` 中的 `LDAP_ADMIN_PASSWORD`，示例 `admin123`。`admins` 组仅供业务应用映射权限，**不授予 LDAP 目录管理权**。

## 5. 必须创建的文件（完整内容）

### 5.1 `.env.example`

```dotenv
LDAP_ADMIN_PASSWORD=admin123
LDAP_HOST_PORT=1389
LDAP_UI_PORT=8080
```

`cp .env.example .env`，不得提交 `.env`。这些是公开的测试凭据，严禁复用生产密码。

### 5.2 `compose.yaml`

```yaml
name: ldap-mock
services:
  ldap:
    image: osixia/openldap:1.5.0
    container_name: ldap-mock-server
    hostname: ldap
    environment:
      LDAP_ORGANISATION: "Mock LDAP"
      LDAP_DOMAIN: "example.org"
      LDAP_ADMIN_PASSWORD: "${LDAP_ADMIN_PASSWORD:?Create .env from .env.example}"
      LDAP_TLS: "false"
    command: --copy-service
    ports:
      - "127.0.0.1:${LDAP_HOST_PORT:-1389}:389"
    volumes:
      - ldap_data:/var/lib/ldap
      - ldap_config:/etc/ldap/slapd.d
      - ./bootstrap:/container/service/slapd/assets/config/bootstrap/ldif/custom:ro
    restart: unless-stopped

  ldap-ui:
    image: osixia/phpldapadmin:0.9.0
    container_name: ldap-mock-ui
    profiles: ["ui"]
    environment:
      PHPLDAPADMIN_LDAP_HOSTS: ldap
      PHPLDAPADMIN_HTTPS: "false"
    ports:
      - "127.0.0.1:${LDAP_UI_PORT:-8080}:80"
    depends_on:
      - ldap
    restart: unless-stopped

volumes:
  ldap_data:
  ldap_config:
```

> 注意 `--copy-service`：镜像在初始化时会处理其引导文件；只读挂载配合此参数以避免修改主机 LDIF。若具体镜像构建出现 entrypoint/command 兼容问题，Agent 必须通过实际启动测试解决，不能省略验证。

### 5.3 `bootstrap/50-seed.ldif`

```ldif
dn: ou=people,dc=example,dc=org
objectClass: organizationalUnit
ou: people

dn: ou=groups,dc=example,dc=org
objectClass: organizationalUnit
ou: groups

dn: uid=admin01,ou=people,dc=example,dc=org
objectClass: inetOrgPerson
cn: Admin One
sn: One
uid: admin01
mail: admin01@example.org
userPassword: Test123456

dn: uid=admin02,ou=people,dc=example,dc=org
objectClass: inetOrgPerson
cn: Admin Two
sn: Two
uid: admin02
mail: admin02@example.org
userPassword: Test123456

dn: uid=dev01,ou=people,dc=example,dc=org
objectClass: inetOrgPerson
cn: Developer One
sn: One
uid: dev01
mail: dev01@example.org
userPassword: Test123456

dn: uid=dev02,ou=people,dc=example,dc=org
objectClass: inetOrgPerson
cn: Developer Two
sn: Two
uid: dev02
mail: dev02@example.org
userPassword: Test123456

dn: uid=dev03,ou=people,dc=example,dc=org
objectClass: inetOrgPerson
cn: Developer Three
sn: Three
uid: dev03
mail: dev03@example.org
userPassword: Test123456

dn: uid=test01,ou=people,dc=example,dc=org
objectClass: inetOrgPerson
cn: Tester One
sn: One
uid: test01
mail: test01@example.org
userPassword: Test123456

dn: uid=test02,ou=people,dc=example,dc=org
objectClass: inetOrgPerson
cn: Tester Two
sn: Two
uid: test02
mail: test02@example.org
userPassword: Test123456

dn: uid=test03,ou=people,dc=example,dc=org
objectClass: inetOrgPerson
cn: Tester Three
sn: Three
uid: test03
mail: test03@example.org
userPassword: Test123456

dn: uid=user01,ou=people,dc=example,dc=org
objectClass: inetOrgPerson
cn: User One
sn: One
uid: user01
mail: user01@example.org
userPassword: Test123456

dn: uid=user02,ou=people,dc=example,dc=org
objectClass: inetOrgPerson
cn: User Two
sn: Two
uid: user02
mail: user02@example.org
userPassword: Test123456

dn: cn=admins,ou=groups,dc=example,dc=org
objectClass: groupOfNames
cn: admins
member: uid=admin01,ou=people,dc=example,dc=org
member: uid=admin02,ou=people,dc=example,dc=org

dn: cn=developers,ou=groups,dc=example,dc=org
objectClass: groupOfNames
cn: developers
member: uid=dev01,ou=people,dc=example,dc=org
member: uid=dev02,ou=people,dc=example,dc=org
member: uid=dev03,ou=people,dc=example,dc=org

dn: cn=testers,ou=groups,dc=example,dc=org
objectClass: groupOfNames
cn: testers
member: uid=test01,ou=people,dc=example,dc=org
member: uid=test02,ou=people,dc=example,dc=org
member: uid=test03,ou=people,dc=example,dc=org
```

**引导验收重点**：确认挂载路径下 LDIF 被真正执行；用 `ldapsearch` 检查返回 10 个 UID 和 3 个组，不得仅以容器处于 `Up` 状态作为成功证据。

### 5.4 `scripts/smoke-test.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
COMPOSE=(docker compose)
CONTAINER=ldap-mock-server
BASE='dc=example,dc=org'
PASS='Test123456'

# 等待 LDAP 响应，最多 30 次尝试；避免 depends_on != ready 的竞态。
ready=0
for _ in $(seq 1 30); do
  if docker exec "$CONTAINER" ldapwhoami -x -H ldap://localhost:389 \
       -D "uid=dev01,ou=people,$BASE" -w "$PASS" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done
[ "$ready" -eq 1 ] || { echo 'LDAP not ready or seed missing' >&2; exit 1; }

for user in admin01 admin02 dev01 dev02 dev03 test01 test02 test03 user01 user02; do
  docker exec "$CONTAINER" ldapwhoami -x -H ldap://localhost:389 \
    -D "uid=$user,ou=people,$BASE" -w "$PASS" >/dev/null
  echo "PASS bind: $user"
done

# 错误密码必须拒绝认证。
if docker exec "$CONTAINER" ldapwhoami -x -H ldap://localhost:389 \
     -D "uid=dev01,ou=people,$BASE" -w WRONG_PASSWORD >/dev/null 2>&1; then
  echo 'FAIL: invalid password accepted' >&2
  exit 1
fi

docker exec "$CONTAINER" ldapsearch -x -LLL -H ldap://localhost:389 \
  -b "ou=people,$BASE" '(objectClass=inetOrgPerson)' uid | grep -q '^uid: dev01$'

docker exec "$CONTAINER" ldapsearch -x -LLL -H ldap://localhost:389 \
  -b "ou=groups,$BASE" '(cn=developers)' member | grep -q 'uid=dev03,ou=people'

echo 'PASS: smoke tests'
```

说明：匿名搜索是否可用依赖服务器 ACL；上述默认配置预期可匿名读取测试条目。若实际 ACL 禁止匿名搜索，调整脚本为使用 `.env` 的管理员凭证绑定，但**不得把密码硬编码到 Git 仓库**。建议新增计数断言（10 users / 3 groups）及无组用户断言。

### 5.5 `scripts/reset.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" != "--yes-delete-data" ]]; then
  echo 'This permanently deletes mock LDAP volumes.' >&2
  echo 'Run: ./scripts/reset.sh --yes-delete-data' >&2
  exit 2
fi

docker compose --profile ui down --volumes
docker compose up -d ldap
./scripts/smoke-test.sh
```

只清理此 Compose 项目的卷；绝对禁止 `docker volume prune`、`docker system prune` 或删除其他项目的卷。

### 5.6 `.gitignore`

```gitignore
.env
.venv/
__pycache__/
.pytest_cache/
*.pyc
```

### 5.7 `tests/requirements.txt`

```text
ldap3>=2.9,<3
pytest>=8,<10
```

### 5.8 `tests/test_ldap.py`

```python
import os
import pytest
from ldap3 import Server, Connection, SIMPLE
from ldap3.core.exceptions import LDAPBindError

HOST = os.getenv('LDAP_HOST', '127.0.0.1')
PORT = int(os.getenv('LDAP_PORT', '1389'))
BASE = 'dc=example,dc=org'


def connect(uid: str, password: str) -> Connection:
    return Connection(
        Server(HOST, port=PORT, use_ssl=False),
        user=f'uid={uid},ou=people,{BASE}',
        password=password,
        authentication=SIMPLE,
        auto_bind=True,
    )


@pytest.mark.parametrize('uid', [
    'admin01', 'admin02', 'dev01', 'dev02', 'dev03',
    'test01', 'test02', 'test03', 'user01', 'user02'
])
def test_all_users_can_bind(uid):
    with connect(uid, 'Test123456') as conn:
        assert conn.bound


def test_wrong_password_fails():
    with pytest.raises(LDAPBindError):
        connect('dev01', 'WRONG_PASSWORD')


def test_unknown_user_fails():
    with pytest.raises(LDAPBindError):
        connect('not-exists', 'Test123456')


def test_group_membership():
    with connect('dev01', 'Test123456') as conn:
        assert conn.search(
            f'ou=groups,{BASE}',
            f'(member=uid=dev01,ou=people,{BASE})',
            attributes=['cn'],
        )
        assert any('developers' in entry.cn.values for entry in conn.entries)


def test_user_without_group():
    with connect('user01', 'Test123456') as conn:
        conn.search(
            f'ou=groups,{BASE}',
            f'(member=uid=user01,ou=people,{BASE})',
            attributes=['cn'],
        )
        assert len(conn.entries) == 0
```

## 6. 快速启动与验证

```bash
cp .env.example .env
docker compose config --quiet
docker compose up -d ldap
chmod +x scripts/*.sh
./scripts/smoke-test.sh

# 可选 UI：
docker compose --profile ui up -d
# 浏览器 http://127.0.0.1:8080
# UI login DN cn=admin,dc=example,dc=org；密码取自 .env

# Python 验证：
python -m venv .venv
source .venv/bin/activate
pip install -r tests/requirements.txt
pytest -q tests/

# 查看运行状态及日志：
docker compose ps
docker compose logs --tail 100 ldap
```

Windows PowerShell 激活虚拟环境：`.venv\Scripts\Activate.ps1`。宿主机的 `localhost:1389` 不等于其他容器的 `localhost`；同一 Docker 网络中的应用使用 `ldap:389`，其他 Compose 项目需先接入相同外部网络或使用宿主机可达地址。

## 7. 应用对接配置

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

推荐的业务登录流程：以服务账号搜索 `uid` -> 获取用户真实 DN -> 使用输入的密码进行 LDAP Bind 验证 -> 查询 `groupOfNames.member` -> 映射到应用角色 -> 建立应用自己的会话。注意：不要把简单的 DN 字符串拼接当作生产验证方案；生产代码必须安全转义 LDAP filter 值。上述普通用户 `admin01` **不是** LDAP 管理员 DN。

## 8. 测试矩阵与验收标准

| 编号 | 情景 | 预期 |
|---|---|---|
| A01 | `docker compose config --quiet` | 返回 0 |
| A02 | 全新数据卷首次启动 | 服务健康、10 用户 + 3 组实际可查 |
| A03 | 10 个用户正确密码 Bind | 全部成功 |
| A04 | 任意账号错误密码 | Bind 失败 |
| A05 | 不存在账号 | Bind 失败 |
| A06 | 按 uid 搜索用户 | 返回唯一 DN |
| A07 | 查询 `developers` | 恰好 dev01/dev02/dev03 |
| A08 | 查询 `admins`/`testers` | 成员正确 |
| A09 | user01/user02 组成员查询 | 无匹配组 |
| A10 | `docker compose restart` | 数据仍在，无重复记录 |
| A11 | 开启 UI profile | 页面可进入，目录管理员可登录 |
| A12 | reset 无确认参数 | 必须拒绝删除 |
| A13 | reset 带确认参数 | 删除本项目数据并重建，种子重新导入 |
| A14 | 宿主机绑定检查 | LDAP/UI 仅绑定 `127.0.0.1` |
| A15 | `.env`/敏感凭据检查 | `.env` 不被 git 跟踪 |
| A16 | 修改种子文件后仅 restart | 不假装自动更新已有 LDAP 数据 |

运行结果记录到 README 的 Verification 小节：执行命令、通过/失败、环境、错误与修复方式。只记录实际完成情况，不虚构 PASS。

## 9. Codex Agents 分工与实施顺序

### Agent 1 — Infrastructure（P0）
1. 创建项目结构、Compose、`.env.example`、`.gitignore`。
2. 校验 Compose 语法，启动 LDAP。
3. 确认卷、端口绑定、无敏感信息提交。
4. 记录任何镜像平台兼容问题（arm64/amd64 等）。

### Agent 2 — Directory & Seed（P0）
1. 创建 `bootstrap/50-seed.ldif`（10 users/3 groups）。
2. 确认 `groupOfNames` 的每个组至少有一个 `member`。
3. 验证自定义 bootstrap 真正执行且首次导入成功。
4. 重启后不得重复导入或覆盖已有数据。

### Agent 3 — Validation（P0）
1. 编写可重复执行的 `smoke-test.sh`。
2. 编写 `ldap3`/pytest 测试；覆盖正反例、组关系、持久化验证。
3. 失败必须非零退出；不得隐藏错误或凭日志主观判定通过。
4. 测试自动化无需依赖 UI。

### Agent 4 — Docs & Integration（P1）
1. 形成 README：前置条件、启动、UI、登录信息、对接配置、常见问题、销毁。
2. 更新 `AGENTS.md` 的工作约束与 DoD。
3. 提供在其他 Compose 项目中的网络对接说明及 FastAPI/Outline 配置示例。

**执行依赖**：Agent 1 和 Agent 2 可先并行，Agent 3 在 Compose + LDIF 可用后实施，Agent 4 与测试阶段并行。集成后统一运行 smoke test 和 pytest，最后更新 README；不允许仅提交文本而未尝试执行可用验证。

## 10. 推荐 `AGENTS.md`

```markdown
# Repository instructions for Codex Agents

## Goal
Create a local-only OpenLDAP development fixture with 10 users and 3 groups.

## Scope
- Do not connect to, query, or modify any real LDAP/AD server.
- Do not open LDAP/UI ports on 0.0.0.0.
- Do not commit .env or production secrets.
- Do not use Docker-wide destructive cleanup commands.
- Always treat this as development-only; TLS is intentionally disabled.

## Required outputs
- compose.yaml, .env.example, bootstrap/50-seed.ldif
- scripts/smoke-test.sh, scripts/reset.sh
- tests/requirements.txt, tests/test_ldap.py
- README.md with setup/troubleshooting/verification

## Run checks
1. docker compose config --quiet
2. docker compose up -d ldap
3. ./scripts/smoke-test.sh
4. pytest -q tests/ (when Python tooling is installed)
5. docker compose --profile ui up -d and verify UI manually if possible

## Done criteria
- 10 named users bind successfully; bad passwords fail.
- 3 groups have exact memberships; two users have no groups.
- Data survive restart and reset is guarded.
- No unintended volume deletion, no real LDAP access.
- Document all tests actually run and any blocked checks.
```

## 11. 易错点及处理

- **容器显示 Up，但用户不存在**：先检查 seed 挂载路径及第一次初始化日志；已有 volume 不会自动重新导入。测试环境可调用明确确认的 `reset.sh`。
- **`ldap_bind: Invalid credentials (49)`**：检查用户 DN 是否位于 `ou=people`、密码是否匹配，LDAP 管理员和 `admin01` 是不同账号。
- **端口冲突**：宿主机端口改为 `LDAP_HOST_PORT=2389`，容器内部仍为 389。
- **UI 显示连接失败**：检查 `PHPLDAPADMIN_LDAP_HOSTS=ldap`、两个容器是否在同一 Compose 网络。
- **搜索失败**：检查搜索 Base DN、过滤器、ACL；登录成功不代表该身份有搜索权限。
- **组解析错误**：本项目使用 `groupOfNames/member`，不是 `posixGroup/memberUid`；集成应用要正确匹配。
- **ARM64 镜像兼容**：优先实际 `docker compose pull`；若镜像没有相应架构，记录限制并评估模拟或兼容方案，不擅自替换为未验证镜像。
- **开放网络风险**：LDAP 389 明文，UI 8080 HTTP；只绑定 loopback，不作为公网服务。

## 12. 后续可选扩展（不阻塞 P0）

- 为不同用户设置不同的测试口令；使用管理接口改密并测试旧密码失效。
- 创建一个“停用用户”场景，但必须明确机制（例如 ppolicy lock 或应用层 denylist）；**仅移出组不等于停用 LDAP Bind**。
- 创建不存在用户、错误密码、多组用户、特殊字符 uid 等测试夹具。
- 添加只读 LDAP 服务账号（如 `cn=readonly`）并验证 ACL。
- 添加 TLS/LDAPS 与证书验证（仅当真实集成需求提出时）。
- 添加 CI 容器化端到端测试，避免依赖公网服务。

## 13. 给 Codex 的执行指令

```text
Implement this LDAP Mock Server repository exactly according to LDAP_Mock_Server_Implementation_Plan.md.
Use Docker Compose and osixia/openldap:1.5.0 with first-start LDIF seeding.
Create all listed source/config/test files and README.md plus AGENTS.md.
Start containers if Docker is available, verify 10 users/3 groups, test good/bad binds,
check persistence and reset guard, and run pytest. Fix any issues discovered.
Do not access real LDAP services, do not expose ports beyond 127.0.0.1,
do not delete unrelated Docker resources, and never commit .env.
If Docker is unavailable, perform static validation and explicitly list unverified runtime checks.
Finish with changed files, commands run, actual test results, and unresolved limitations.
```

---

**交付定义**：一个仓库、一个 `docker compose up -d ldap` 命令，得到包含 10 个账号与 3 个用户组的可重复测试 LDAP；使用 `./scripts/smoke-test.sh` 实际核验，而不是仅凭容器启动成功判断。 
