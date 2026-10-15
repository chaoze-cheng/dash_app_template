# dash app 开发通用约定

dash app 开发的通用结构与约定：核心为文件组织、Python 代码规范、Git 提交、数据库环境变量（第 1–4 节），其余为数据库、附件、性能、AI、验证与代码审核的常用约定（第 5–10 节）。app 自己的 AGENTS.md 记录特有约定与数据模型细节，优先级高于本文件。

## 1. 标准文件组织

新增或重构 app 一律采用以下结构（`（可选）` 按需启用）：

```
<app_name>/
├── app.py                 # Dash 入口：创建 app、配置 Flask server、注册回调；不放业务逻辑
├── pages/                 # 多页面注册（use_pages=True），薄壳：只注册页面并 import layout/callbacks
├── src/
│   ├── config.py          # 唯一配置读取点
│   ├── callbacks/         # 回调，register_xxx_callbacks() 在 app.py 注册
│   ├── layouts/           # 布局构建（create_xxx_layout）
│   ├── components/        # app 共用 html 组件、表格列定义
│   ├── services/          # 业务逻辑与数据库访问；某功能代码太长时上移为 src/xxx_functions/ 单独文件夹
│   ├── db/                # （可选）models、engine、session（唯一允许出现 SQL 的层）
│   ├── extractors/        # （可选）文件抽取：pdf 文本层 → ocr → llm 兜底
│   ├── graphs/            # （可选）图表构建
│   └── prompts/           # （可选）LLM prompt 模板
├── assets/                # CSS / 客户端 JS / 图片
├── scripts/               # 数据 ETL、采集、运维脚本（不进 app 运行路径）
├── tests/  docs/          # （可选）
├── supplementary/         # （可选）附件存储根目录（config 指定，git 忽略）
├── alembic/ + alembic.ini # （可选）用 PostgreSQL 时必备；schema 变更唯一入口
├── requirements.txt       # 运行依赖（不用 poetry/pipenv）
├── env.example            # 环境变量模板；真实 .env 由 .gitignore 忽略
├── README.md              # 项目说明（登记开发端口，新增 app 尽量错开）
├── CHANGELOG.md           # 变更记录
├── pg_backup.sh           # （可选）单库备份脚本，宿主 cron 调用
├── Dockerfile / docker-compose.yml / gunicorn.conf.py  # （可选）部署
└── .gitignore
```

- 分层流向**单向**：`pages → callbacks → services → db → PostgreSQL`；上层只消费下层返回的 dict / DataFrame，不反向依赖。
- `app.py` 只做组装：`Dash(__name__, use_pages=True, pages_folder="pages", suppress_callback_exceptions=True)`、`server = app.server`、Flask 会话/中间件配置、`register_callbacks()`。
- 回调不放数据库/IO 细节，取数计算调 `src/services/` 或 `src/xxx_functions/`；`pages/` 不堆 layout 代码。
- 组件 ID 用稳定模式 `{page}-{element}-{detail}`（如 `submit-btn-save`），全局元素加统一前缀（`global-search-*`）。
- 体量约束（软性）：函数 < 50 行、单个模块 < 800 行，超出即拆分。
- `scripts/` 共用代码通过 `src.config` 取配置，不复制连接逻辑。
- `.gitignore` 至少覆盖 `.env`、`__pycache__/`、`.ruff_cache/`、`.pytest_cache/`、数据目录。
- **所有 Web 页面展示内容（标题、导航、标签、表头、按钮、tooltip、toast 消息）用英文**。

## 2. Python 代码规范

- Python 3.12；遵循 PEP 8；black（88 列）+ isort（black profile），或等价 ruff format/check，配置写入 `pyproject.toml`。
- 命名：函数/变量/模块 `snake_case`、类 `PascalCase`、常量 `UPPER_CASE`；公共函数与类写 docstring 和类型注解。
- 字符串用 f-string，路径用 `pathlib.Path`；新文件 UTF-8、LF。
- 导入只在模块顶层（类型专用导入放 `TYPE_CHECKING`）；循环依赖用模块级引用与归属划分解决，不写函数内 import。
- 代码注释、docstring、日志用英文。
- 配置只在 `src/config.py` 读取（`os.getenv` / dotenv 集中），其他模块 import 常量；不得散落 `os.getenv`、不得硬编码端点/阈值/凭据。
- schema 变更走 Alembic 迁移，禁止在回调里执行 DDL。

## 3. Git 提交约定

提交信息为**一句话**（单行、祈使句、英文）+ conventional 前缀：`feat:` / `fix:` / `docs:` / `style:` / `refactor:` / `perf:` / `test:` / `chore:`，可带 scope（`feat(upload): ...`）。示例：`feat: add compound filter to search page`。提交信息、注释与 PR 文本**不得出现 LLM 模型名、AI 工具名或生成器署名尾注**，不写实现进度标记。

## 4. 数据库环境变量约定（PG_XXX_*）

PostgreSQL 连接一律使用带 app 简写前缀的五元组，保证多 app 部署在同一环境（或合并进同一份 `.env`）时互不冲突，为整合预留：

```
PG_<XXX>_HOST= / _PORT=（默认 5432） / _NAME= / _USER= / _PASSWORD=
```

已注册简写：congressLens=`CONGRESS`、synerCI=`SYNERCI`、databrowser=`DBROWSER`、biodb_dash=`BIODB`、ci_reporter=`CIR`、adc_platform=`ADC`、patent_tracker=`PATENT`、model_atlas=`ATLAS`。

- 新 app 先登记简写（2–7 位大写字母、唯一），再写 `env.example`（必须列出全部五个变量，是变量名/默认值/凭据获取方式的权威参考；`.env` 不入库）。
- 真实进程环境变量优先于 `.env`（dotenv 不覆盖已有变量）；密码拼 DSN 经 `quote_plus` URL 编码。
- `src/config.py` 只读 `PG_<XXX>_*` 拼 DSN；存量 app 迁移期可回退旧变量（`DB_*` / `POSTGRES_*` / 小写 app 名），迁移完成后移除。
- 非 PostgreSQL 服务用自有前缀（如 `LLM_API_KEY`、`NGS_*`），不得占用 `PG_`。

## 5. 数据库通用规则

- **生产 PostgreSQL 是共享实例**：只操作本 app 配置的那一个库；禁 `pg_dumpall` 与跨库操作；`DROP DATABASE`、`alembic downgrade base` 等破坏性操作先确认目标库，且仅限本地/一次性库；测试用一次性容器或隔离 schema（如 `TEST_DATABASE_URL`）。
- Schema 权威 = Alembic revision + ORM models：改表先改模型再写迁移（autogenerate 后人工审查）；迁移走**加法策略**（加列/加表/加索引，不 drop、不 rename），存量数据升级后存活。
- SQL 一律参数化：`text()` + 具名绑定参数，禁止拼接值；动态表名/标识符走白名单校验。
- 跨表关系优先业务 ID 字段 + service 层维护一致性，谨慎加外键；app 已确立外键约定时以其文档为准。
- 时间统一 timezone-aware UTC；缺失保持 NULL，不造占位记录、不猜测。
- 备份统一 `pg_backup.sh` 单库脚本（`pg_dump` plain + gzip、UTC 时间戳、按保留天数清理），连接解析与 `src/config.py` 一致。
- 凭据与数据工件不入 git：`.env`、`*.sql.gz`、`*.db`、备份、上传目录、生产日志、大型原始数据目录。

## 6. 附件存储与文件上传

- 附件存储根路径由 `src/config.py` 指定（如 `SUPPLEMENTARY_FOLDER`），通常为 app.py 所在目录的 `supplementary/`；生产以 host volume 挂载持久化，不入 git。
- 每个文件存独立 UUID 目录 `supplementary/<uuid>/<filename>`，避免同名覆盖与路径猜测；元数据（原始文件名、大小、hash、路径）入库，同内容按 hash 去重；下载走统一 file route，不暴露任意文件系统路径。
- 保存前检查文件名：只允许字母/数字/`-`/`_`/`.`/空格/中文，剔除路径分隔符、控制字符等奇怪字符；清洗集中在一个专门脚本或 service 函数，不在各上传回调重复实现。
- 上传统一 **dash-uploader-ng**（`du.Upload`）分片上传：分片流式写入暂存目录（config 指定），不走 base64 回调；service 校验类型/大小上限后移入 supplementary，暂存目录按 TTL 清扫。

## 7. 性能与运行时约定

- 列表页服务端分页/排序/筛选（dash-ag-grid 服务端模式），前端不全量渲染大数据集。
- 避免 N+1：批量取数（`.in_(ids)`）、pandas 向量化、只 SELECT 需要的列；权限/记录过滤在下载数据之前完成。
- 读取路径要有缓存：模块级 dict（键含全部查询参数）或统一 Flask-Caching；数据变更后主动删除相关缓存键。
- 耗时后台任务（导入、采集、AI 批处理）不占请求 worker，独立进程/调度器运行；跨 worker 用 DB advisory lock 防重复提交。
- 大批量导出从单一 read snapshot 读取。

## 8. LLM / AI 功能约定

- 走 OpenAI 兼容接口，`LLM_*` 配置；默认关闭，未配置不报错、不外发数据。
- 所有 LLM API 请求必须输出日志，**不可屏蔽**（含失败请求）。
- 产出必须可追溯：原文摘录（evidence）、模型/供应商、UTC 时间、prompt 版本；来源变更后标记过期并退出聚合。
- 测试严禁真实调用 LLM / 外部付费 API；此类测试不得自动重复执行，仅允许手动单次触发。

## 9. 验证与提交前检查

```bash
python -m compileall -q app.py pages src   # 语法检查
python -c "import app"                     # 导入检查
pytest -q                                  # 有测试套件时
git diff --check                           # 空白/冲突标记
```

- 数据库改动另跑小规模只读查询验证；schema 改动必须附对应 Alembic 迁移。
- 提交前 `git status --short` 确认无误加文件；同步更新受影响的 `README.md`、`CHANGELOG.md`、`docs/`。
- 不覆盖、不回滚用户未提交的改动；不引入仓库未配置的命令、服务、linter 或测试运行器（除非任务明确包含）。

## 10. 代码审核规则

审核覆盖五个维度：Python 规范与死代码、Web 展示文案英文、HTML 无意义嵌套、数据库读取层（效率 + 维护性）、安全与事务完整性。

- 死代码判定：grep 全库（含 tests/scripts/docs/配置）零引用 + codegraph 交叉验证后才可删；`@callback`、pydantic validator、`importlib` 任务入口等反射调用是活代码；纯透传 wrapper 应内联，但有注册契约/权限语义/默认值等真实价值者列防误删清单。
- 文案扫描：CJK 正则扫渲染路径（组件文案、toast/modal、plotly 标题轴例、邮件正文）；注释、仅写日志的异常消息、测试文件豁免。
- HTML 嵌套：零属性单子包装、空属性容器、冗余 Row/Col、无属性深链等反模式；疑似冗余包装的 className/id 必须在 CSS 选择器、callback 引用、`assets/*.js` 零命中才可移除。
- 读取层：查 N+1、`SELECT *` 过度抓取、pandas 过滤可下推 SQL、同回调重复查询、绕过缓存层、循环内开 session/commit；维护性查同一 WHERE 逻辑散布、raw SQL 与 ORM 混用、callback 拼 SQL、影子函数。
- 安全与事务：权限/软删除过滤先于 count/分页/导出并覆盖全部入口（列表/详情/diff/历史/下载），保密判定 fail-closed；关联记录与主记录同事务写入；并发状态转移用 `with_for_update`；软删除口径在 SQL / pandas / 详情各路径一致。
- 报告产出：`docs/code-review-YYYY-MM-DD.md` 只记发现不改代码，每项含位置（文件:行）、优先级（P1–P3）、影响、修法、验收标准；未决项进 `-open-items.md` 跟踪，已修复项移出原文档。
- 改变读取行为的优化：隔离库 `EXPLAIN (ANALYZE, BUFFERS)` 前后对比 + 新旧输出一致 + 冷/热耗时数字。
- 审核纪律：不连生产库（只读 `SELECT`/`EXPLAIN`）、迁移测试只在一次性临时库、不发邮件不调 LLM 不触发生产调度；`env.example` 不得出现真实 IP、账号或非占位密码。
