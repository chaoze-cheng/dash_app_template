# Dash App 通用工程约定

> 适用范围：以 Dash 为主要 UI、PostgreSQL 为主数据库的多页面中大型 Python Web App。项目级 `AGENTS.md` 可以增加业务规则；不得默默削弱安全和数据保护条款。冲突应记录并确认。
>
> 规范词：**MUST/必须**＝强制；**SHOULD/建议**＝默认采用，例外需说明；**OPTIONAL/可选**＝按需启用。未实施的可选组件不得成为启动依赖。

## 目录

1. [技术栈与运行模式](#1-技术栈与运行模式)
2. [项目结构与分层依赖](#2-项目结构与分层依赖)
3. [Python 代码、配置与依赖](#3-python-代码配置与依赖)
4. [Dash 页面、Callback 与状态](#4-dash-页面callback-与状态)
5. [数据库配置、Models 与 Schemas](#5-数据库配置models-与-schemas)
6. [数据库读取、写入与迁移](#6-数据库读取写入与迁移)
7. [本地登录、LDAP、RBAC 与审计](#7-本地登录ldaprbac-与审计)
8. [UI Style 与可视化](#8-ui-style-与可视化)
9. [附件上传、存储与内容提取](#9-附件上传存储与内容提取)
10. [性能、缓存与后台任务](#10-性能缓存与后台任务)
11. [AI/LLM 集成与数据治理](#11-aillm-集成与数据治理)
12. [开发、Docker 生产部署与运维](#12-开发docker-生产部署与运维)
13. [安全、日志与错误处理](#13-安全日志与错误处理)
14. [测试与发布前 Checklist](#14-测试与发布前-checklist)
15. [Git、Agent 工作流与代码审核](#15-gitagent-工作流与代码审核)
16. [文档职责与同步维护](#16-文档职责与同步维护)
17. [项目级决策与例外](#17-项目级决策与例外)
18. [独立示例仓库与 Coding Agent 复用规范](#18-独立示例仓库与-coding-agent-复用规范)

## 1. 技术栈与运行模式

### 1.1 默认技术栈

- **MUST** 新项目默认使用 Python 3.12、Dash/Flask、PostgreSQL 16、SQLAlchemy 2.0、Pydantic v2 和 Alembic。Python/PostgreSQL 为新项目基线，已有项目升级须单独验证。
- **SHOULD** 数据可视化使用 Plotly，大型交互表格使用 dash-ag-grid，数据库批量读取优先使用 ConnectorX。
- **MUST** 依赖版本在项目依赖文件中明确约束，并验证 Dash、Flask 及第三方组件兼容性。
- **OPTIONAL** FastAPI、Redis、Celery、LDAP、OCR、LLM 和额外任务调度器按实际需求引入。

### 1.2 开发与生产运行

- **MUST** 开发环境支持 Python 虚拟环境直接执行 `python app.py`，不要求 Docker；可启用 Debug/Hot Reload。
- **MUST** 生产环境使用 Docker + Gunicorn 运行 Dash，Nginx 负责反向代理及 HTTPS；关闭 Debug。
- **MUST** Dash 暴露 `server = app.server` 作为 Gunicorn WSGI 入口 `app:server`。
- **MUST** Gunicorn workers、threads、timeout 等按内存和负载配置，不写死通用值。
- **MUST** 生产数据库迁移独立执行，不在容器启动或应用 import 时自动执行。

### 1.3 PostgreSQL 部署

- **MUST** PostgreSQL 位于现有宿主机或独立数据库服务器，App Docker Compose 不创建或管理 PostgreSQL 实例及其数据卷。
- **MUST** 数据库连接通过 `PG_<XXX>_*` 环境变量配置；容器内 `localhost` 不得被当作宿主机地址。
- **MUST** 开发、测试、生产数据库隔离；应用账号遵循最小权限原则。

### 1.4 FastAPI 可选集成

- **OPTIONAL** FastAPI 用于对外 REST API 或跨 App 集成，不是 Dash 的必需组件。
- **MUST** Dash Callback 可直接调用共享 Services，不要求经本机 HTTP 调用 FastAPI。
- **MUST** Dash 与 FastAPI 复用业务 Services/Schemas，但不共享请求级数据库 Session。
- **MUST** FastAPI 使用 ASGI 运行方式，与 Dash 的 WSGI `app:server` 区分。

### 1.5 数据访问技术

- **SHOULD** 中大型只读查询和 DataFrame/Arrow 批量加载优先使用 ConnectorX。
- **MUST** 允许 SQLAlchemy ORM/Core 与参数化 SQL 完成简单查询、复杂查询和事务操作。
- **MUST** 所有 ConnectorX、ORM、Core、SQL 查询构建与执行集中在 `src/db/`；Services 调用 DB 层并承担业务逻辑、权限与数据加工；Callbacks 不得直接操作业务数据源。
- **MUST** 数据库写入采用明确的 SQLAlchemy 事务机制，不使用 ConnectorX 写入。

### 1.6 可选组件管理

- **MUST** 未启用的可选组件不得成为 App 启动的强制依赖，也不得在启动时执行真实外部连接或模型下载。
- **MUST** 已启用的功能若缺少必要配置，应在启动校验或使用时报告明确错误，不得静默绕过或假装可用。
- **SHOULD** 不为尚无实际需求的功能引入 Redis、Celery 或其他独立服务。

## 2. 项目结构与分层依赖

```text
<app_name>/
├── app.py                      # Dash 开发入口及 WSGI server 暴露
├── pages/                      # Dash Pages 路由薄壳
├── src/
│   ├── config.py               # 唯一环境配置入口
│   ├── callbacks/              # UI 事件编排；不得操作数据源
│   ├── layouts/                # 页面布局
│   ├── components/             # 共享组件/表格列定义
│   ├── services/               # 业务逻辑、权限、数据加工、事务编排
│   ├── db/
│   │   ├── base.py
│   │   ├── engine.py
│   │   ├── session.py
│   │   ├── models/             # SQLAlchemy 2.0 ORM
│   │   └── queries/            # ConnectorX / SQLAlchemy / 参数化 SQL
│   ├── schemas/                # Pydantic v2 输入输出结构
│   ├── auth/                   # （可选）认证适配器/权限辅助
│   ├── extractors/             # （可选）文档、图片、视频解析
│   ├── graphs/                 # （可选）Plotly 图形生成
│   └── prompts/                # （可选）LLM 模板
├── assets/                     # CSS / 客户端 JS / 图标
├── scripts/                    # ETL、采集、维护、任务入口
├── tests/
├── docs/
├── alembic/ + alembic.ini
├── supplementary/              # （可选）本地开发附件；生产挂载持久卷
├── requirements.txt
├── pyproject.toml               # formatter / linter / test 配置
├── env.example
├── README.md
├── CHANGELOG.md
├── Dockerfile
├── docker-compose.yml
├── gunicorn.conf.py             # （可选）
└── .gitignore
```

- **MUST** 依赖流：`pages/layouts → callbacks → services → db`；`services` 可以调用 `extractors/graphs` 等纯功能模块；`schemas` 是跨层数据契约。禁止 db 反向 import callbacks/pages。
- **MUST** `app.py` 仅组装 Dash、Flask server、Layout、Callback 注册及必要中间件，不放业务逻辑；保留 `server = app.server`。
- **SHOULD** `pages/` 负责页面注册及引入布局；复杂布局放 `layouts/`，简单页面允许直接在 `pages/` 定义 Layout；回调统一放 `callbacks/`。
- **MUST** 所有业务数据源操作（数据库、业务文件读写、网络 API、数据解析、数据变换）通过 `services/` 调度；Callback 不得直接进行。页面展示所需的轻量参数整形允许在 Callback 内完成。
- **MUST** SQL 语句、ConnectorX 查询、ORM 查询构建与执行统一放 `src/db/`（尤其 `db/queries/`），不允许散布在 Callback、pages、layouts 或 services 中。Services 负责调用 db 函数、业务校验、权限与事务边界协调。
- **MUST** Callback 注册方式在项目内保持一致。推荐各模块暴露 `register_xxx_callbacks(app)`，由 `src/callbacks/__init__.py` 汇总并在 `app.py` 集中调用；若采用 Dash 模块级 `@callback`，须保证导入与注册仅发生一次，不混用两种机制。重复注册与重复 Output 分别检查。
- **MUST** `db/` 不反向依赖 Services/Callbacks/Pages；DB 层提供 Session 与事务机制，Services 决定业务事务范围；嵌套查询函数不得无意提交事务。
- **SHOULD** 组件 ID 使用 `{page}-{element}-{detail}`；全局组件统一 `global-*` 前缀；动态重复组件使用 Pattern-Matching ID。函数尽量少于 50 行、单模块尽量少于 800 行；按职责拆分而非机械硬限制。
- **SHOULD** 不强制引入 Repository 抽象类或依赖注入框架；普通 DB Query 函数与 Service 函数可作为默认实现。
- **MUST** `.gitignore` 覆盖 `.env`、缓存、上传目录、生产日志、数据库备份和大型数据文件。

## 3. Python 代码、配置与依赖

- **MUST** PEP 8；函数、变量、模块用 `snake_case`，类用 `PascalCase`，常量用 `UPPER_CASE`；公共接口添加类型注解及 docstring。
- **SHOULD** 使用 Ruff format/check（或 black 88 列 + isort black profile）；项目统一一种格式化配置，写在 `pyproject.toml`。UTF-8/LF；路径使用 `pathlib.Path`；字符串插值优先 f-string。
- **MUST** 注释、docstring、日志及 Web 页面显示文案使用英文。避免函数内 import；只有明确的可选依赖、性能或循环依赖边界允许说明原因后例外。
- **MUST** 仅 `src/config.py` 读取环境变量/`.env`，其他模块通过配置对象或常量使用；不得散落 `os.getenv` 或硬编码密码、地址、端口、模型密钥。
- **MUST** 环境变量优先级：真实进程环境 > `.env` > 明确安全默认值。`env.example` 列出全部必需变量、用途和安全占位符，不含真实凭据/IP。
- **MUST** 生产、开发、测试的数据库和附件路径可明确区分；敏感配置不写入 Git、日志或错误提示。
- **SHOULD** 使用 `requirements.txt`，项目保持可重复安装；不要无需求引入 Poetry/Pipenv。更新依赖前确认 Dash、Flask、组件版本兼容性。

## 4. Dash 页面、Callback 与状态

- **MUST** 多页面使用 Dash Pages；全局 Header/导航/用户状态放统一 Layout，避免页面级重复注册。
- **MUST** Callback 仅做 Input/State 读取、调用 Service、将返回值映射为 Output。禁止在 Callback 中直接 SQL、ConnectorX、ORM、文件上传处理、耗时计算、HTTP 外部采集。
- **MUST** 动态组件 ID 与 Callback 注册关系可验证；`suppress_callback_exceptions=True` 不代表可以忽略不存在的 Output 或 ID 错误。
- **SHOULD** 避免循环 Callback 和重复 Output；`allow_duplicate` 必须说明并发触发和初始化行为；按业务设置 `prevent_initial_call`。
- **MUST** `dcc.Store` 仅保存小型、可 JSON 序列化的 UI 状态/ID；不得存放密码、Token、完整上传文件、大 DataFrame 或跨用户敏感信息。
- **MUST** 不使用进程级可变全局变量保存用户会话或关键业务状态；多 Worker 场景不得依赖单进程 dict 实现权限或业务一致性。
- **MUST** 用户可预期错误转为统一 Toast/Alert；服务端保留关联日志，UI 不泄露堆栈/SQL/密钥。
- **SHOULD** 页面具备 Loading、Empty、Error、Forbidden、Success 状态；表格筛选、分页、详情导航、回退和重复点击有明确行为。

## 5. 数据库配置、Models 与 Schemas

- **MUST** PostgreSQL 使用 App 专属五元组：`PG_<XXX>_HOST`、`_PORT`（默认 5432）、`_NAME`、`_USER`、`_PASSWORD`。新 App 先登记唯一 2–7 位大写缩写；所有变量列在 `env.example`。
- 已登记：congressLens=`CONGRESS`、synerCI=`SYNERCI`、databrowser=`DBROWSER`、biodb_dash=`BIODB`、ci_reporter=`CIR`、adc_platform=`ADC`、patent_tracker=`PATENT`、model_atlas=`ATLAS`。
- **MUST** 连接配置只从 `src/config.py` 进入；数据库密码组装 DSN 时使用 SQLAlchemy `URL.create()` 或安全 URL 编码；迁移期可回退旧变量，完成后删除兼容分支。
- **MUST** PostgreSQL 业务表由 SQLAlchemy 2.0 Declarative ORM Models 声明（`Mapped`、`mapped_column`）；Pydantic v2 Schemas 与 ORM 分离（`BaseModel`、必要时 `from_attributes`）。
- **MUST** `models/` 表达存储结构、字段类型、索引、约束与关系；`schemas/` 表达输入/输出/验证，不把 ORM 对象直接作为 Dash JSON 响应。
- **SHOULD** Schema 按实际场景定义，不强制每张表机械建立 Create/Update/Response 三份。
- **MUST** 使用 timezone-aware UTC；PostgreSQL 使用 `TIMESTAMPTZ`；缺失保持 NULL，不捏造占位记录。
- **SHOULD** JSON 数据使用 JSONB；跨表外键按业务一致性与迁移需要决定，不统一禁止或强制。
- **MUST** Engine 与 Session 生命周期明确；每个请求/任务使用独立 Session，不跨线程共享；连接池大小和超时可配置。

## 6. 数据库读取、写入与迁移

- **MUST** 数据读取**优先 ConnectorX**，尤其 PostgreSQL → pandas/Arrow 的中大规模只读查询；小规模 ORM 对象加载、复杂事务、需要 Session 上下文的查询可使用 SQLAlchemy 2.0 ORM/Core；必要时允许参数化 SQL。
- **MUST** 无论 ConnectorX、ORM、Core 或原生 SQL，**查询与执行代码必须位于 `src/db/`**，由 services 调用。Services 不直接编写 SQL 字符串；Callbacks 完全不接触数据库。
- **MUST** SQL 值参数化；动态表名、排序列、Schema 名使用白名单；不得拼接不可信 SQL 字符串。ConnectorX 若使用的 API 不支持参数绑定，必须通过受控查询构建或安全替代实现，绝不能直接插入用户输入。
- **MUST** 权限、租户/可见性、软删除等过滤在 db 查询阶段生效，不能先提取未授权数据再由 pandas 过滤。数据库访问函数应接受经过 services 校验的访问上下文/范围。
- **SHOULD** 避免 `SELECT *`、N+1、循环内新建 Session、循环逐条 commit；批量查询、只读快照、分页与必要列投影优先。
- **MUST** 多表写入遵守单事务原子性；事务所有权必须清晰，不在嵌套函数中无意提交；并发更新按需采用锁或乐观版本控制。
- **MUST** Schema 变更由 Alembic 执行：先改 Models，再生成/手写迁移并人工审查；不能在 Callback 或 App 启动时执行 DDL。
- **SHOULD** 优先 expand → backfill → contract 的兼容性迁移；重命名、删除字段或表需单独审查和备份，不能机械禁止所有破坏性迁移。
- **MUST** 生产 PostgreSQL 视为共享资源；只操作当前 App 配置的库；禁止 `pg_dumpall`、跨库误操作和未经确认的 `DROP DATABASE`/大范围删除。测试使用隔离数据库/Schema。
- **SHOULD** 备份用单库 `pg_dump` + gzip + UTC 时间戳、保留策略；必须定期验证可恢复性，不能仅检查备份文件存在。

## 7. 本地登录、LDAP、RBAC 与审计

- **MUST** 采用 RBAC；需要用户登录的 App 默认核心六表：`users`、`roles`、`permissions`、`user_roles`、`role_permissions`、`audit_logs`。不需要登录的纯展示 App 可不启用该模块，但必须明确匿名访问边界。
- **MUST** 本地账号可登录；LDAP 为可选认证提供者。LDAP 认证成功后，首次登录自动建立本地 `users` 记录并分配 `viewer` 角色，无需事先管理员审批。
- **MUST** LDAP 仅确认身份，不根据 LDAP Group 自动提升 App Role；已存在 LDAP 用户登录时保留管理员已分配角色，不自动重置。
- **MUST** `viewer` 只能读取**明确标记为 public** 的内容；`internal`/`restricted` 需要对应角色权限；未知或缺失可见性默认不公开。Viewer 是登录角色，不等于匿名访客。
- **MUST** 管理员通过 Role 分配权限；服务端校验覆盖页面、Callback、Service、API、下载/导出/附件路由；隐藏 UI 按钮不构成鉴权。
- **MUST** 已禁用用户即使 LDAP 验证成功也不得登录；角色变化和禁用后应使缓存权限与有效会话及时失效。
- **MUST** `users` 建议字段：`id`、`username`、`email`、`auth_source`（local/ldap）、`external_subject`（LDAP 稳定 ID）、`password_hash`（LDAP 可空）、`is_active`、`created_at`、`last_login_at`；身份唯一性应考虑来源与稳定 ID，不能仅凭显示名自动合并账户。
- **MUST** `roles(code,name,description,is_system)`、`permissions(code,resource,action,description)`；关联表使用联合唯一约束；权限 code 采用 `resource.action`（如 `content.view`、`content.edit`、`user.manage`、`audit.view`）。
- **MUST** `audit_logs` 记录 actor、action、resource、resource_id、result、timestamp、可过滤的 JSONB details；记录登录、角色变化、关键数据修改、文件操作、导出和管理操作；审计数据不允许普通用户修改，禁止写入密码、Token 或敏感正文。
- **MUST** 本地密码安全哈希；LDAP 密码绝不落库。LDAP 连接需 TLS 校验和合理超时，失败时不能绕过认证。首次登录用户创建与角色赋予必须原子化、幂等化。
- **SHOULD** `viewer/editor/admin` 为默认角色示例，业务项目可扩展；editor 不自动获得所有内部数据权限。

## 8. UI Style 与可视化

### 8.1 设计原则与规范职责

- **MUST** 所有 Web 展示文案（标题、导航、表头、按钮、Tooltip、Toast、图表标题和轴标签）使用英文；注释、docstring 与日志亦使用英文。
- **MUST** 使用统一 Design Tokens 管理字体、字号、颜色、间距、圆角、阴影、层级及交互状态；公共 Header、Sidebar、Modal、Toast、表格工具栏等组件复用，避免页面复制。
- **SHOULD** 采用桌面优先、清晰且适合数据密集平台的布局；支持合理响应式调整。默认浅色主题，深色主题按需提供；项目可覆盖品牌色、Logo 和业务布局。
- **MUST** `AGENTS.md` 规定通用强制边界，`docs/UI_STYLE.md` 保存项目详细 Tokens、组件示例、交互状态与特定配色；两者不得相互矛盾。

### 8.2 字体与字号（已确认）

- **MUST** 所有用户可见 UI 文字的**实际渲染字号不得低于 14px**，包括表格、表头、按钮、标签、Tooltip、Toast、图表轴刻度、图例、Hover 文本及辅助说明。不得使用 `transform: scale()`、`zoom` 等方式变相缩小至 14px 以下。
- **MUST** 默认正文使用 **16px**，正常行高推荐 `1.5`；较长正文可使用更舒适的行高。
- **SHOULD** 表格单元格 15px；表头、Caption、辅助标签 14px；标准按钮和表单输入文字 16px，紧凑按钮 14px。
- **SHOULD** 页面标题 28px，Section Title 24px，Card Title 20px，Subheading 18px；可按层级适当增大，不得低于最小字号。
- **SHOULD** 使用系统字体回退栈（Inter、系统 UI 字体、Noto Sans、中文系统字体、Arial、sans-serif）；等宽代码使用系统 monospace；不依赖必须联网才能加载的字体。
- **MUST** 字号由 CSS Variables 统一控制；移动端优先改变布局、换行与间距，不通过缩小文字破坏最小字号约束。

推荐字号 Tokens：

```css
:root {
  --font-size-min: 14px;
  --font-size-sm: 14px;
  --font-size-table: 15px;
  --font-size-base: 16px;
  --font-size-md: 18px;
  --font-size-lg: 20px;
  --font-size-xl: 24px;
  --font-size-2xl: 28px;
  --font-size-3xl: 32px;
  --line-height-tight: 1.3;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.65;
}
```

### 8.3 颜色、间距与组件尺寸

- **MUST** 使用语义化颜色 Tokens：`primary`、`success`、`warning`、`danger`、`background`、`surface`、`text`、`text-secondary`、`border`、`hover`；不得仅依赖颜色表达关键状态。
- **SHOULD** 默认浅色基础配色可使用 `primary #2563EB`、`success #16A34A`、`warning #D97706`、`danger #DC2626`、`background #F8FAFC`、`surface #FFFFFF`、`text #0F172A`、`secondary #64748B`、`border #E2E8F0`；品牌色允许项目覆盖。
- **SHOULD** 使用 4px 间距体系（4/8/12/16/20/24/32px），通过 Tokens 统一定义。
- **SHOULD** 标准 Header 60px、Sidebar 240–260px、页面内边距 24px；Input/Select/Button 高度 40px，紧凑按钮 34–36px；卡片圆角 8px、输入框圆角 6px。具体尺寸可根据项目密度调整，但须保证 14px 最小文字与可操作性。
- **MUST** Hover、Focus、Disabled、Loading、Empty、Error、Forbidden、Success 状态有一致且可理解的表现；键盘可操作控件必须具有可见 Focus 状态。

### 8.4 按钮、表单、Modal 与通知

- **SHOULD** 每个表单区域设置一个明确的 Primary Action；次要操作使用 Secondary/Ghost；删除等破坏性操作使用 Danger 并按风险要求确认。
- **MUST** 表单 Label 可见，Placeholder 不得代替 Label；校验错误靠近对应字段，错误提示不只使用颜色；Loading 时避免重复提交。
- **MUST** 纯图标按钮提供 Tooltip 或可访问名称；禁用状态仍应保证文字可读。
- **SHOULD** Modal 采用统一标题、正文、操作区结构；Toast 使用 Success/Info/Warning/Error 语义，普通成功提示可在 3–5 秒后消失，需要行动的错误提示不能过快消失。
- **MUST** 空数据与查询失败必须区分；错误状态提供可理解的说明和适用时的重试入口，不显示 SQL、堆栈或密钥。

### 8.5 dash-ag-grid 数据表格

- **SHOULD** 标准表格单元格字号 15px、表头 14px、标准行高 42px、Compact 行高 36px、表头高度 42px、左右 Cell Padding 8–12px。
- **MUST** 大数据表格采用服务端分页、筛选、排序，并在服务端验证字段白名单与权限；不得把完整大型数据集传到浏览器后再过滤。
- **SHOULD** 文本默认左对齐，数值右对齐并使用 `font-variant-numeric: tabular-nums`；长文本支持省略与详情/Tooltip；重要 ID/名称列按需固定。
- **MUST** 表格有 Loading/Empty/Error 状态；导出须独立执行服务端权限校验，不依赖浏览器已加载的行数据。
- **SHOULD** 表格工具栏统一搜索、筛选、刷新、列选择、导出等控件布局；列宽按内容及业务重要性设置，避免所有列机械等宽。

### 8.6 Plotly 与科研图表

- **SHOULD** Plotly 使用统一基础模板：图表标题 16–20px，坐标轴标题 16px，刻度/图例/Hover 最小 14px；背景、边距、线条和导出规格统一。
- **MUST** 图表的用户可见文字不得低于 14px；必要时增加图形尺寸、留白或调整图例布局，而非缩小字体。
- **MUST** 坐标轴单位、图例含义、分组及颜色语义准确；离散分组颜色具备足够区分度，连续数值使用适当连续色带。
- **SHOULD** 生存曲线、火山图、Heatmap 等科研图表允许使用独立专业模板，不为统一品牌色而改变科学含义。

### 8.7 CSS 文件组织

推荐：

```text
assets/
├── 00_tokens.css
├── 10_base.css
├── 20_layout.css
├── 30_components.css
├── 40_tables.css
├── 50_forms.css
├── 60_plotly.css
└── 90_overrides.css
```

- **SHOULD** CSS 按 Tokens → Base → Layout → Components → Tables/Forms → Overrides 分层；公共组件使用 App/组件级 Class 命名空间。
- **MUST** 避免无范围地覆盖 `button`、`input`、`table` 等标签造成 Dash/AG Grid 第三方组件样式污染。
- **SHOULD** 避免大量内联 `style={...}` 和 `!important`；优先使用公共 ClassName、Tokens 和共享组件。
- **MUST** 不依赖容易随版本变化的第三方内部生成类名；组件升级时检查实际 DOM 和样式兼容性。

## 9. 附件上传、存储与内容提取

- **MUST** 附件根目录由配置指定；开发可使用 `supplementary/`，生产必须挂载宿主机持久化目录/Volume，不纳入 Git。
- **MUST** 每个附件使用独立 UUID 目录，保存原始文件名、大小、hash、存储路径、类型与状态；同内容可按 hash 去重，但必须考虑权限和逻辑关联，不能因同 hash 暴露其他用户文件。
- **MUST** 文件名统一清洗，阻止目录穿越、控制字符与危险路径；下载通过鉴权文件路由，不能公开任意文件系统路径。
- **SHOULD** 大文件上传统一使用 `dash-uploader-ng` 分片流式上传，禁止通过 Dash base64 Callback 传输大文件；配置 chunk 大小、大小限制、临时目录、TTL 清理和失败反馈。
- **MUST** 上传后在 Service 中校验扩展名与实际文件类型、大小、完整性，再移动到正式存储；失败时记录状态并清理临时文件。
- **OPTIONAL** PDF/PPTX 优先提取文本层与表格，图片 OCR，复杂图文/视频按需使用多模态 LLM；提取任务后台执行，保存来源页码/时间段、版本、错误与证据，原始附件不得被覆盖。

## 10. 性能、缓存与后台任务

- **MUST** 列表服务端分页/排序/筛选，避免一次性向浏览器发送大量数据；数据库尽可能先筛选和投影后提取。
- **SHOULD** ConnectorX 用于批量只读数据加载；DataFrame 处理优先向量化；大图表按需降采样/分块，避免超大 JSON。
- **MUST** 缓存键覆盖查询参数、权限/可见性范围及版本；数据变更后明确失效；进程内 dict 仅用于允许不一致的单进程或纯性能缓存，不能用于跨 Worker 正确性。
- **MUST** 耗时导入、采集、AI、OCR、视频解析在独立进程/Worker 中执行；任务具有 ID、状态、开始结束时间、错误、重试和幂等策略。
- **MUST** 定时任务与多 Worker 并发时采用可靠的排他控制（如 PostgreSQL advisory lock/任务唯一约束），防止重复执行；Web Worker 不直接启动每 Worker 一份定时器。
- **SHOULD** 监测慢查询、Worker RSS、连接池占用、请求耗时、后台任务积压；大批量导出使用一致性读取快照并限制资源。

## 11. AI/LLM 集成与数据治理

- **OPTIONAL** AI/LLM 默认关闭，采用 OpenAI-compatible API 适配；无配置时不报错、不外发数据。
- **MUST** AI 请求记录安全审计元数据与失败信息（任务 ID、模型/供应商、时间、耗时、状态、token/成本如可用），不记录密钥、敏感原文或完整请求响应，除非有明确合规授权和脱敏策略。
- **MUST** AI 结果保留来源证据、原文定位、模型/供应商、Prompt 版本、UTC 时间、解析版本及人工复核状态；来源变化后可标记过期并避免继续作为已确认事实聚合。
- **MUST** 自动测试 Mock 外部付费 API/LLM，不重复触发真实调用；真实付费验证只能经明确授权单次执行。
- **SHOULD** 对实体抽取、分类、表格提取分别记录置信度或可复核状态，不把模型推断自动等同于人工确认。

## 12. 开发、Docker 生产部署与运维

- **MUST** 本地开发 `python app.py`，开发入口支持明确配置的 host/port/debug；生产 Gunicorn 加载 `app:server`，参数（workers、threads、timeout）按负载和内存调整，不写死通用值。
- **MUST** Docker 镜像仅打包 App 及运行依赖，不包含生产 `.env`、附件、数据库数据或备份；以非 root 用户运行，使用明确版本的基础镜像。
- **MUST** Docker Compose 只管理 App 与可选任务服务，不部署 PostgreSQL；容器访问宿主机数据库使用配置地址，确保 PostgreSQL `listen_addresses`、`pg_hba.conf`、防火墙和最小权限账号配置正确。
- **MUST** Nginx 配置 HTTPS、反向代理、Dash URL 前缀与静态资源路径；子路径部署须验证 Dash `requests_pathname_prefix` / `routes_pathname_prefix` 与代理行为匹配。
- **MUST** 上传大小、代理超时、Gunicorn 超时和后台任务超时分别配置；长任务不得仅靠增大 HTTP timeout 解决。
- **MUST** 容器健康检查、重启策略、日志输出和持久化挂载明确；部署前验证生产连接目标数据库，不允许启动时自动执行 Alembic upgrade。
- **SHOULD** 提供单库 `pg_backup.sh` 与恢复说明；数据库角色、数据卷、网络、端口变化要记录在部署文档中。不能靠修改 `POSTGRES_USER/PASSWORD` 环境变量改变已初始化数据库的现有账号。
- **MUST** 生产部署、迁移、删除、重建容器/Volume 等破坏性操作需明确目标、备份和回退计划；不得擅自影响其他 App。

## 13. 安全、日志与错误处理

- **MUST** 所有受保护资源在服务端进行认证/授权；权限检查在查询、分页 count、详情、导出、下载、历史记录路径一致执行，默认拒绝。
- **MUST** 使用参数化查询、文件路径规范化、上传限制、会话安全 Cookie（生产 HTTPS 下 Secure/HttpOnly/SameSite）、CSRF 防护策略及合理的登录限速。
- **MUST** 日志输出英文并包含必要上下文（request/task ID、模块、动作、耗时、错误类型）；严禁输出密码、Token、数据库 DSN 凭据、敏感内容。
- **MUST** Callback/Service/db 的错误有清晰责任边界：db 提供可识别异常，Service 转换为业务错误，Callback 转换为 UI 消息；未知错误记录堆栈但 UI 只显示通用提示。
- **SHOULD** 监控 404/499/500/502、OOM、连接池耗尽、静态资源错误、Callback 缺失组件和任务失败；运维文档给出排查入口。
- **MUST** 安全审计与应用调试日志分开；审计记录持久化，避免仅保留在易丢失的容器日志中。

## 14. 测试与发布前 Checklist

- **MUST** 最低提交前检查：`python -m compileall -q app.py pages src`、`python -c "import app"`（确保不会意外连接/修改生产）、`pytest -q`（有测试时）、`git diff --check`、`git status --short`。
- **MUST** DB 修改需测试 Models、迁移与现有数据兼容；使用隔离测试库，不在生产执行迁移测试。权限相关改动需覆盖 viewer/editor/admin、禁用用户、LDAP 初次登录和未授权访问。
- **MUST** 发布前逐项检查并记录：
  - [ ] 代码语法、导入、格式/静态检查、自动测试
  - [ ] 无密钥/敏感文件进入 Git，环境变量完整
  - [ ] 数据库连接目标正确、Alembic 迁移经隔离环境验证、备份可恢复
  - [ ] 本地登录、LDAP（启用时）、Viewer 公共数据边界、角色变更、禁用和登出
  - [ ] 页面/Callback/服务端 API/下载与导出的授权测试
  - [ ] 所有页面、动态组件 ID、关键 Callback、表格分页筛选和详情导航
  - [ ] UI 的 Loading/Empty/Error/Forbidden/Toast/响应式状态
  - [ ] 文件上传/下载/大文件/异常清理（适用时）
  - [ ] 大数据查询、缓存隔离、并发、Worker 内存和连接池
  - [ ] Docker 镜像、非 root、健康检查、Volume、日志和重启
  - [ ] Nginx HTTPS、子路径、静态资源、上传限制与超时
  - [ ] README、CHANGELOG 和受影响文档已更新
  - [ ] 部署计划、回滚策略、上线后冒烟测试与日志检查
- **MUST** 发布阻断项（安全/数据完整性/核心功能）未通过时不得标记发布完成；其他例外需记录负责人、影响及处理计划。
- **SHOULD** 完整可执行清单存放 `docs/RELEASE_CHECKLIST.md`；本节为最低门槛。

## 15. Git、Agent 工作流与代码审核

- **MUST** Git 提交使用英文单行祈使句 + conventional 前缀：`feat:`、`fix:`、`docs:`、`style:`、`refactor:`、`perf:`、`test:`、`chore:`；可加 scope。提交消息、注释和 PR 文本不加 AI 工具署名或进度尾注。
- **MUST** Agent 修改前检查 Git 状态、相关源码和文档；不覆盖/回滚用户未提交修改；不擅自触发生产迁移、发送邮件、真实 LLM 调用或其他外部副作用。
- **SHOULD** 复杂任务先 Plan → 拆 Task → 逐项 Implement/Test/Commit → 整体 Review/Fix → 更新文档 → 发布；简单修复不强制冗长计划。
- **MUST** 审核覆盖：Python 规范、死代码、UI 英文文案、冗余 HTML 嵌套、数据库读取效率、权限过滤、事务完整性、附件安全、部署风险。
- **MUST** 死代码删除前检索整个仓库和动态注册入口（Callback、validator、importlib、CLI）；有行为价值的 Wrapper 不机械内联。
- **MUST** 查询优化检查 N+1、SELECT *、pandas 可下推 SQL、重复查询、循环 Session/commit、缓存隔离；改变读取行为需对比新旧输出，并在隔离环境比较 `EXPLAIN (ANALYZE, BUFFERS)` 和冷/热耗时。
- **SHOULD** 审核报告写入 `docs/code-review-YYYY-MM-DD.md`，每项记录位置、P1–P3、影响、修法和验收标准；未决项单独跟踪。
- **MUST** 不因任务范围外的风格偏好进行大规模重构；所有测试、审查和脚本不得默认连接生产库。

## 16. 文档职责与同步维护

| 文件 | 唯一主要职责 | 何时更新 |
|---|---|---|
| `AGENTS.md` | Agent 行为、通用工程规则、硬性边界 | 工程约定变化 |
| `README.md` | 项目简介、快速启动、入口、配置指引 | 运行方式/功能入口变化 |
| `CHANGELOG.md` | 已完成且用户可感知的功能与修复 | 相关功能发布时 |
| `docs/PRD.md` | 需求、页面、用户流程、验收目标 | 产品需求变化 |
| `docs/ARCHITECTURE.md` | 当前架构、模块、依赖、数据流 | 架构调整 |
| `docs/DATABASE.md` | 表、字段、ORM 关系、索引、迁移说明 | 数据模型变化 |
| `docs/UI_STYLE.md` | CSS Token、组件、布局、交互规则 | UI 设计规范变化 |
| `docs/DEPLOYMENT.md` | Docker、Nginx、宿主机 PG、备份恢复 | 部署或运维变化 |
| `docs/RELEASE_CHECKLIST.md` | 完整测试与上线验收清单 | 验收标准变化 |
| `docs/decisions/`（可选） | 重大架构决策与取舍 | 重大设计决定 |

- **MUST** 文档各司其职，避免同一事实在多个文件维护不同版本；AGENTS 主文只保留核心约束，长配置示例/详细 ORM/操作手册可拆到 docs。
- **MUST** 代码变更影响需求、数据模型、部署或 UI 规范时，同一任务更新对应文档；纯格式改动不要求无关文档更新。
- **MUST** 文档与代码不一致时先说明差异并确认权威来源，不默默将规划功能写成已实现。
- **SHOULD** 新项目至少有 README、AGENTS、CHANGELOG；随着复杂度按需建立 PRD、ARCHITECTURE、DATABASE、UI_STYLE、DEPLOYMENT、RELEASE_CHECKLIST。

## 17. 项目级决策与例外

- **MUST** 项目级 `AGENTS.md` 记录：App 简写、端口、URL 前缀、数据库名与 schema、是否启用 FastAPI/LDAP/AI、角色权限矩阵、附件存储、特殊数据处理、部署环境差异。
- **MUST** 若项目确需偏离本通用规范，记录条款、原因、替代方案、影响与批准结论；安全、数据保护和权限隔离不能因项目级文档而无说明地降低。
- **SHOULD** 对已有 App 采用渐进式迁移，不因引入 V2 规范而一次性改动全部目录、ORM、权限和部署；优先保证现有功能与数据兼容。

## 18. 独立示例仓库与 Coding Agent 复用规范

### 18.1 仓库定位与访问

- **MUST** 使用独立 Git 仓库 `dash-examples` 维护跨项目参考实现；它不是生产运行时依赖，也不是必须安装的 Python Package。
- **SHOULD** 在各 App 的工作区旁克隆 `dash-examples/`，通过 `DASH_EXAMPLES_PATH`（如 `../dash-examples`）或项目文档指定其可访问路径；路径以 Agent 实际工作目录为准。
- **MUST** Agent 在读取前验证仓库路径和文件真实存在；远程 URL 不代表代码已在沙箱中可读。若仓库不可访问，应报告并继续基于当前项目代码与规范工作，不得虚构已阅读的示例。
- **SHOULD** 项目记录已验证的示例仓库 Git Tag 或 Commit SHA；不得在任务开始时自动拉取最新版本并直接替换代码。

### 18.2 先检查现有实现，再查索引

- **MUST** 开发新功能前先检查当前项目的现有组件与实现；若已有合适代码，优先项目内复用。
- **MUST** 对可复用的新功能，检查 `dash-examples/README.md` 索引，按需求选择相关示例并阅读其 README、代码和必要测试；不要一次性读取整个仓库。
- **SHOULD** 优先采用 `stable` 示例；`experimental` 需补充验证；`deprecated` 不得用于新增功能，除非明确获准并说明原因。
- **MUST** 示例不匹配时允许自行实现，不得为强行复用而引入额外复杂依赖。

### 18.3 复制、适配与安全边界

- **MUST** 示例仅供参考、复制和适配；生产代码不得通过运行时 import、sys.path 修改或软链接依赖 `dash-examples/examples/`。
- **MUST** 复用时遵守本项目 `pages/layouts → callbacks → services → db` 分层：数据库查询、ConnectorX、ORM、Core、SQL 位于 `src/db/`；业务逻辑和数据加工位于 `src/services/`；Callback 仅做 UI 编排。
- **MUST** 复核依赖版本、接口、权限、可见性、组件 ID、Callback 注册、异常处理、并发与事务行为；不能假设示例在目标 App 中即插即用。
- **MUST** UI 示例遵守项目 Design Tokens：用户可见文本最小 14px，默认正文 16px；表格、图表、Tooltip、Toast 也适用。
- **MUST** 不得复制生产凭据、用户信息、私有数据、Token、真实 `.env` 或生产数据库连接参数；遵守原始代码的许可证与使用限制。

### 18.4 示例索引与成熟度

- **MUST** 仓库根 `README.md` 作为唯一全局示例索引；每个已存在示例应有唯一 ID、类别、用途、相对路径、依赖、状态与验证信息。
- **MUST** 每个示例目录有独立 `README.md`，描述用途、文件、依赖、运行/测试方式、集成步骤、接口、已知限制、来源及许可证。
- **MUST** 状态只用 `stable`、`experimental`、`deprecated`；只有通过必要测试且经过兼容性审查才可标记 `stable`。规划中的目录不得冒充已经存在或通过验证的示例。
- **MUST** 新增、重命名、移动、弃用示例时同步更新根索引；示例代码更新时同步更新验证信息和测试。
- **SHOULD** 已经在多个 App 中验证的改进通过独立 PR 回馈示例仓库；不应未经评审直接从业务 App 覆盖共享示例。

### 18.5 Agent 工作流与验证

1. 检查目标项目的现有实现及 `AGENTS.md`。
2. 查找示例仓库路径、读取索引、选择匹配示例。
3. 阅读对应 README、源码、测试和依赖，确认可复用范围。
4. 将代码适配到目标项目的 `src/components/`、`src/callbacks/`、`src/services/`、`src/db/` 等正确位置。
5. 检查鉴权、SQL 参数化、文件路径、跨 Worker 状态、UI 字号和组件 ID。
6. 执行格式检查、单元测试和必要的手工验证；未运行的验证必须如实说明。
7. 必要时在 PR 或代码说明中记录示例 ID、来源版本和适配差异；发现通用改进时建议向示例仓库提交 PR。

- **OPTIONAL** 对确需跨 App 同步升级的稳定代码，单独提取可安装的共享 Python Package；此举不改变 `examples/` 仅作为参考代码的定位。

## UID 实体标识开发约定

- **MUST** 涉及业务实体 UID、新建表 UID、前缀命名或 UID 数据迁移时，先遵循 [`docs/UID_CONVENTIONS.md`](docs/UID_CONVENTIONS.md)。该文件是 4 位 prefix + UUIDv7 格式、Prefix Registry 与兼容迁移规则的唯一权威来源。
- **MUST** 现有数据库改造默认保留现有 `id` 及外键，采用渐进式引入 `uid`；未经独立审核不得重建数据库或以 `create_all()` 替代 Alembic。
