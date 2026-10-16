# UID 开发约定（UUIDv7 + 四字符实体前缀）

> Version: 1.0 | 2026-10-16  
> Status: 统一开发约定；候选实体不代表必须创建对应表。  
> Applies to: Dash/Flask、SQLAlchemy 2.0、PostgreSQL 16、Alembic、跨 App 共享实体。

## 1. 强制规则

1. **MUST** 为对外或跨模块长期引用的业务实体使用 `{prefix}_{uuidv7}`，如 `drug_0199a3f2-8b4c-7a21-9c45-d0e123456789`（格式示意）。
2. **MUST** prefix 为 **恰好四个 ASCII 小写字母** `[a-z]{4}`，紧接一个 `_`，再接标准小写、带连字符的 36 字符 UUIDv7；完整 UID **41 个字符**。
3. **MUST** 统一由可信的生成器创建 UID，不允许用户自行指定；prefix 必须在本文件注册，不得跨实体复用，发布后不得随表名变更。
4. **MUST** UID 创建后不可修改；不得编码业务状态、来源、项目、组织或患者信息，不得作为权限凭据。
5. **MUST** 跨应用引用已经有权威 UID 的药物、疾病、试验等实体时沿用其 UID；外部 NCT、MONDO、OncoTree、DrugBank 等编号单独存储。
6. **MUST** 若业务记录不需要独立生命周期（例如纯多对多关联），可使用复合主键，不强制新增冗余 UID。大量内部高频 JOIN 的表可以采用原生 UUID 主键。
7. **MUST** 新增或变更 prefix 先编辑本 Registry，检查唯一性，并在相关的生成器、模型、测试与迁移中同步。
8. **MUST** 不因实施本规范自动运行数据库迁移、删除旧表/列、重建数据库或修改生产数据。

## 2. 格式与验证

```text
<prefix:4>_<uuidv7:36>
^[a-z]{4}_[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$
```

- 上述正则只能检验外形与版本位，还必须校验 UUID 解析结果、注册表前缀以及记录的实体类型。
- UUIDv7 大致按生成时间排序，但不是可靠的 `created_at` 替代品；不要把 UID 当作随机秘密。Python 3.12 可使用维护中的 UUIDv7 库（例如 `uuid6`）；PostgreSQL 16 可以存储 UUIDv7，但没有内建 `uuidv7()` 生成函数。
- 名称冲突修正：`drnm` 药名 vs `dsnm` 疾病名；`sess` 会议场次 vs `sesn` 登录会话；`cont` 内容 vs `cent` 内容实体关系；`assa` 而非 5 字符 `assay`。
- 保留与后续启用不是建表指令。只有真实存在且需要独立 ID 的实体才应在 ORM 中激活相应前缀。

## 3. Prefix Registry（规范性清单）

下表仅定义命名空间，不决定所有表都使用文本主键。原表名称不同的项目按实体语义映射，不因改表名重发 UID。

### 药物与疾病

| Prefix | Entity key | 建议数据表 |
|---|---|---|
| `drug` | `drug` | `drugs` |
| `drnm` | `drug_name` | `drug_names` |
| `dise` | `disease` | `diseases` |
| `dsnm` | `disease_name` | `disease_names` |
| `targ` | `target` | `targets` |
| `gene` | `gene` | `genes` |
| `prot` | `protein` | `proteins` |
| `path` | `pathway` | `pathways` |
| `comp` | `company` | `companies` |
| `orgn` | `organization` | `organizations` |
| `mech` | `mechanism` | `mechanisms` |
| `biom` | `biomarker` | `biomarkers` |
| `regm` | `regimen` | `regimens` |

### 临床试验

| Prefix | Entity key | 建议数据表 |
|---|---|---|
| `tria` | `trial` | `study_records` |
| `trid` | `trial_identifier` | `trial_identifiers` |
| `tarm` | `trial_arm` | `trial_arms` |
| `tint` | `trial_intervention` | `trial_interventions` |
| `tloc` | `trial_location` | `trial_locations` |
| `tout` | `trial_outcome` | `trial_outcomes` |
| `tres` | `trial_result` | `trial_results` |
| `tver` | `trial_version` | `trial_versions` |
| `tsrc` | `trial_source` | `trial_sources` |

### CongressLens

| Prefix | Entity key | 建议数据表 |
|---|---|---|
| `conf` | `conference` | `conferences` |
| `sess` | `conference_session` | `sessions` |
| `cont` | `content` | `contents` |
| `auth` | `contributor` | `content_contributors` |
| `rsrc` | `resource` | `attachment_resources` |
| `ctag` | `content_tag` | `content_tags` |
| `ccls` | `content_classification` | `content_classifications` |
| `cent` | `content_entity_link` | `content_entities` |
| `cwat` | `content_watchlist_item` | `content_watchlist` |
| `cwrl` | `content_watchrule` | `content_watchrules` |
| `cmnt` | `comment` | `comments` |
| `cver` | `content_version` | `content_versions` |
| `cjob` | `content_job` | `content_processing_jobs` |

### NGS 与实验

| Prefix | Entity key | 建议数据表 |
|---|---|---|
| `proj` | `project` | `projects` |
| `samp` | `sample` | `samples` |
| `subj` | `subject` | `subjects` |
| `spec` | `specimen` | `specimens` |
| `tret` | `treatment` | `treatments` |
| `assa` | `assay` | `assays` |
| `expt` | `experiment` | `experiments` |
| `repl` | `replicate` | `replicates` |
| `libp` | `sequencing_library` | `libraries` |
| `runs` | `sequencing_run` | `sequencing_runs` |
| `sfil` | `sequencing_file` | `sequencing_files` |
| `algn` | `alignment` | `alignments` |
| `vari` | `variant` | `variants` |
| `expr` | `expression_result` | `expression_results` |
| `anly` | `analysis` | `analyses` |
| `resu` | `analysis_result` | `analysis_results` |
| `pipe` | `pipeline` | `pipelines` |
| `qcmt` | `quality_metric` | `quality_metrics` |

### 文献、指南、专利、监管

| Prefix | Entity key | 建议数据表 |
|---|---|---|
| `publ` | `publication` | `publications` |
| `jour` | `journal` | `journals` |
| `guid` | `guideline` | `guidelines` |
| `gver` | `guideline_version` | `guideline_versions` |
| `reco` | `recommendation` | `recommendations` |
| `patn` | `patent` | `patents` |
| `pafm` | `patent_family` | `patent_families` |
| `regu` | `regulatory_event` | `regulatory_events` |
| `appr` | `approval` | `approvals` |
| `sour` | `source` | `data_sources` |

### 采集、AI 与处理任务

| Prefix | Entity key | 建议数据表 |
|---|---|---|
| `task` | `task` | `tasks` |
| `jobs` | `job` | `processing_jobs` |
| `extr` | `extraction` | `extractions` |
| `ocrp` | `ocr_result` | `ocr_results` |
| `llmr` | `llm_result` | `llm_results` |
| `aicl` | `ai_classification` | `ai_classifications` |
| `aien` | `ai_entity_extraction` | `ai_entity_extractions` |
| `emtp` | `entity_mapping` | `entity_mappings` |
| `impt` | `import_batch` | `import_batches` |
| `sync` | `sync_run` | `sync_runs` |
| `vers` | `data_version` | `data_versions` |
| `dlog` | `data_change_log` | `data_change_logs` |
| `file` | `file` | `files` |

### 用户、权限与审计

| Prefix | Entity key | 建议数据表 |
|---|---|---|
| `user` | `user` | `users` |
| `role` | `role` | `roles` |
| `perm` | `permission` | `permissions` |
| `team` | `team` | `teams` |
| `sesn` | `user_session` | `user_sessions` |
| `tokn` | `api_token` | `api_tokens` |
| `audt` | `audit_log` | `audit_logs` |
| `noti` | `notification` | `notifications` |
| `sett` | `setting` | `settings` |
| `libr` | `library_item` | `library_items` |
| `wlis` | `watchlist` | `watchlists` |

## 4. 数据库存储建议

现有系统优先采用**保留原 `id` 主键 + 新增 `uid VARCHAR(41) UNIQUE`** 的兼容方案；回填和校验完成后再将新 UID 列约束设为非空。新建实体表可选择 `uid VARCHAR(41) PRIMARY KEY` 或 `id UUID PRIMARY KEY, uid VARCHAR(41) NOT NULL UNIQUE`，应在项目 ORM 文档中注明。所有实际 UID 必须配合 prefix 对应表的 CHECK/服务层校验，不能只依赖 `VARCHAR(41)` 长度约束。

```sql
-- 仅为新表结构示例，不可不加审核地在现有库执行
CREATE TABLE drugs (
    id UUID PRIMARY KEY,
    uid VARCHAR(41) NOT NULL UNIQUE,
    CONSTRAINT ck_drugs_uid CHECK (
        uid ~ '^drug_[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    )
);
```

PostgreSQL 文本 UID 的索引更大；原生 UUID 列为 16 字节。优先保证兼容与正确性，性能调整在压测后实施。

## 5. Alembic 迁移开发约定

1. **MUST** 盘点现有主键、外键、unique、API 标识和外部数据源；生成原 ID 到新 UID 的可追溯映射。
2. **MUST** 遵循 expand → backfill → validate → contract；先新增 nullable UID 并上线双读/双写兼容，再分批回填，完成唯一性、非空、外键与关联数量核对之后启用强约束。
3. **MUST** 对 DROP、TRUNCATE、删除字段、主键替换、外键断裂和不可逆数据重写进行人工审核；执行前完成限定到**当前数据库**的备份和恢复验证。禁止 `drop_all()`、未经允许的 `DROP DATABASE`、生产环境 `create_all()` 替代 Alembic。
4. **MUST** 多 Agent 不得并行修改同一 Alembic revision 链或同时执行同一数据库升级；指定单一迁移负责人，并在运行时采用排他锁/独立部署步骤。
5. **MUST** 在隔离数据库验证 upgrade、数据数量、UID 冲突、回填幂等性和恢复流程；不默认依赖有损 downgrade。生产变更须有审批及明确恢复方案。

## 6. Python / SQLAlchemy 参考

```python
import re
import uuid
from uuid6 import uuid7

PREFIXES = {"drug": "drug", "disease": "dise", "trial": "tria", "content": "cont"}

def new_uid(entity: str) -> str:
    return f"{PREFIXES[entity]}_{uuid7()}"

def is_valid_uid(value: str, entity: str) -> bool:
    prefix = PREFIXES.get(entity)
    if prefix is None or not re.fullmatch(r"[a-z]{4}", prefix):
        return False
    if not isinstance(value, str) or len(value) != 41 or value[:5] != prefix + "_":
        return False
    try:
        parsed = uuid.UUID(value[5:])
        return parsed.version == 7 and str(parsed) == value[5:]
    except (ValueError, AttributeError):
        return False
```

生产实现应从本 Registry（或同步生成的唯一配置文件）导出完整前缀映射，而非仅使用上面的缩略演示字典；CI 测试应校验四位、全局无重复、生成与解析 roundtrip、拒绝错误前缀/UUIDv4/大小写、历史数据迁移冲突以及禁止修改既有 UID。

## 7. Coding Agent 检查清单

- [ ] 优先读取本文件，再设计新的业务 UID 或 Alembic 迁移。
- [ ] Prefix 四位、唯一、语义稳定，与全部已有前缀无冲突。
- [ ] UID 对外稳定；不覆盖外部注册号与内部旧主键。
- [ ] ORM、Schema、Service、日志、数据导入与测试使用相同 UID 语义。
- [ ] 数据库现有行与关系保持完好；备份和迁移验证有证据。
- [ ] 新增 prefix 更新 Registry 和测试，不只修改某一个 App 的常量。

本文件为 UID 命名与开发规则的**单一权威文档**；一般数据库迁移安全要求仍须遵守仓库根目录 `AGENTS.md`。
