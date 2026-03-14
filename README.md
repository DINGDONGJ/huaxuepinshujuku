# 危险化学品 MSDS 查询与法规匹配系统

## 项目简介

这是一个以 Flask 为核心的危险化学品查询系统，包含以下几类能力：

- 化学品基础信息和 MSDS 16 章查询
- 中文名、英文名、CAS 号、别名搜索和自动补全
- 基于 MSDS 内容的法规推荐
- 多化学品共存风险分析
- 可选的 AI 相容性分析
- 可选的本地语义搜索
- 可选的 MSDS 爬取和入库

这份 README 按仓库当前代码和数据状态整理，不以旧文档描述为准。

## 当前仓库状态

以下内容已按仓库实际文件复核：

- Web 服务入口：`new_db/app.py`
- 前端页面：`new_db/templates/index.html`
- 数据库结构：`new_db/init_simple_db.sql`
- 数据库完整备份：`database_backup_clean_utf8.sql`
- 爬虫脚本：`new_db/scrape_to_json.py`
- 语义索引构建：`new_db/build_semantic_index.py`
- 法规映射配置：`new_db/regulation_mapping.json`
- 法规内容索引器：`new_db/regulation_content_indexer.py`
- AI 相容性分析：`new_db/ai_analyzer.py`

当前数据资产规模：

- `new_db/msds_json`：2609 个 JSON 文件
- `database_backup_clean_utf8.sql`：2609 条化学品、2609 条 MSDS 文档、41736 条 MSDS 章节
- `new_db/化学品法规pdf`：475 个法规 PDF
- `new_db/化学品法规md`：474 个法规 Markdown
- `new_db/协议pdf`：3 个协议/声明 PDF

说明：

- 法规 PDF 比法规 Markdown 多 1 个，因此“法规内容索引”并未覆盖全部 PDF。
- `new_db/semantic_cache` 当前只缓存了旧索引，不代表全量数据；启用语义搜索前建议重新构建。

## 功能概览

### 1. Web 查询

`new_db/app.py` 提供以下主要接口：

- `/api/search`：单化学品搜索
- `/api/autocomplete`：搜索建议
- `/api/list`：分页列表
- `/api/regulations/<chemical_id>`：法规匹配
- `/api/search-multiple`：多化学品信息查询
- `/api/compatibility-check`：规则型相容性分析
- `/api/compatibility-ai`：AI 相容性分析
- `/api/import`：导入 JSON
- `/api/delete`：删除化学品

### 2. 法规匹配

法规匹配分两层：

- 配置型匹配：根据 MSDS 第 2、9、11、14、15 章，从 `new_db/regulation_mapping.json` 映射法规
- 内容型匹配：根据 `new_db/regulation_content_index.json` 的关键词倒排索引补充推荐

### 3. 语义搜索

语义搜索是可选能力：

- 引擎文件：`new_db/semantic_search_engine.py`
- 构建脚本：`new_db/build_semantic_index.py`
- 依赖：`sentence-transformers`、`scikit-learn`

如果依赖未安装，Web 服务仍可启动，但语义搜索接口会返回未启用状态。

### 4. 爬虫与入库

`new_db/scrape_to_json.py` 支持两种模式：

- 只抓取并保存为 JSON
- 抓取后直接导入 MySQL

依赖 `beautifulsoup4` 和 `playwright`，并需要额外安装 Chromium 驱动。

## 目录结构

```text
.
├─ README.md
├─ 运行指南.md
├─ docs/
│  └─ 优化建议.md
├─ database_backup_clean_utf8.sql
└─ new_db/
   ├─ app.py
   ├─ init_simple_db.sql
   ├─ scrape_to_json.py
   ├─ ai_analyzer.py
   ├─ semantic_search_engine.py
   ├─ build_semantic_index.py
   ├─ regulation_mapping.json
   ├─ regulation_content_index.json
   ├─ 化学品法规pdf/
   ├─ 化学品法规md/
   ├─ msds_json/
   ├─ templates/
   └─ 协议pdf/
```

## 已知注意事项

以下是当前代码状态下接手时应先知道的事项：

- `new_db/app.py` 和 `new_db/build_semantic_index.py` 中的数据库配置目前是硬编码的。
- 当前工作区可直接导入的备份文件是 `database_backup_clean_utf8.sql`。
- `new_db/requirements.txt` 只覆盖 Web 基础依赖，不包含爬虫和语义搜索的全部依赖。
- 仓库里存在历史脚本和重复目录，建议优先以 `new_db/app.py`、`database_backup_clean_utf8.sql` 和本 README/运行指南为准。

## 如何运行

请直接看根目录文档：

- [运行指南.md](./运行指南.md)

这份文档按当前仓库状态写了完整启动流程，包括：

- Python 和 MySQL 准备
- 数据库导入
- Web 启动
- 语义搜索启用
- 爬虫依赖安装
- 常见问题处理

补充文档：

- [docs/优化建议.md](./docs/优化建议.md)

## 推荐接手顺序

如果你是刚接手这个项目，建议按下面顺序进入：

1. 先读 `new_db/app.py`，理解实际 API 和系统边界。
2. 再看 `new_db/init_simple_db.sql` 和 `database_backup_clean_utf8.sql`，确认数据模型和样本规模。
3. 按 [运行指南.md](./运行指南.md) 把项目先跑起来。
4. 最后再看 `new_db/scrape_to_json.py`、`new_db/semantic_search_engine.py` 和 `new_db/ai_analyzer.py` 这些可选模块。
