# Dash Examples

跨 Dash App 的独立参考实现库。**示例代码不是生产运行时依赖**。请先阅读目标项目的 AGENTS.md，再按本索引选择示例。

## 使用方法

1. 检查目标项目已有代码；优先复用已存在的组件。
2. 阅读本索引，打开相关示例 README 和源码。
3. 验证依赖、权限、数据源、Callback 注册和 UI 规范。
4. 复制/改造到目标项目对应的 `src/` 分层；不要从此仓库直接 import。
5. 测试后再合并。所有示例均为**起始参考**，未经过生产环境认证。

## 已提供示例

| ID | 类别 | 示例 | 用途 | 依赖 | 状态 | 入口 |
|---|---|---|---|---|---|---|
| UI-001 | UI | Navbar | 简单 Dash 导航组件 | Dash | experimental | [navbar](examples/ui/navbar/) |
| UI-002 | UI | AG Grid Pagination | 服务端分页 Callback→Service→DB 分层 | Dash, dash-ag-grid | experimental | [server_side_pagination](examples/ui/ag_grid/server_side_pagination/) |
| UI-003 | UI | Plotly Theme | 图表字体/配色默认模板 | Plotly | experimental | [common_theme](examples/ui/plotly/common_theme/) |
| DB-001 | Database | ConnectorX Read | 只读数据访问封装及 SQL 安全约束 | ConnectorX, pandas | experimental | [connectorx_read](examples/database/connectorx_read/) |
| DB-002 | Database | SQLAlchemy Transaction | Session 与原子事务示例 | SQLAlchemy 2.x | experimental | [sqlalchemy_transaction](examples/database/sqlalchemy_transaction/) |

## 计划中的示例（尚未实现）

- `auth/local_login`, `auth/ldap_login`, `auth/rbac`
- `files/chunk_upload`, `files/file_preview`, `files/pdf_extraction`
- `deployment/docker`, `deployment/nginx`, `integration/background_task`

上述计划项**没有示例代码**，不得宣称已验证。

## 状态

- `stable`：具备文档、测试并在目标环境验证。
- `experimental`：参考实现；必须适配与验证。
- `deprecated`：历史参考，默认不用于新开发。

## 默认约束

- Python 3.12；PostgreSQL 16；SQLAlchemy 2.0；Pydantic v2；Dash。
- 大型只读数据读取优先 ConnectorX；SQL/ORM 仅在 `src/db/`。
- Callback 只能调用 Services；最小可见字号 14px、默认正文 16px。
- 不得包含真实凭据、生产数据、内部个人信息。
- 各示例的版本和可运行范围以各自 README 为准；本仓库尚未做跨版本集成验证。
