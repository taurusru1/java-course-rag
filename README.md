# EduRAG 教育领域检索知识库

这是一个面向秋招作品展示的教育领域 RAG 项目。在课程项目原有的 FastAPI、LangGraph、Milvus、BGE-M3、HyDE、RRF、Reranker、MinIO、MongoDB 和 SSE 基础上，将商品说明书业务改造成课程、项目资料和题库检索。

## 核心能力

- 导入 PDF、Markdown、DOCX 教育资料。
- 根据 Markdown 标题、DOCX Heading 样式和 PDF 页码进行章节感知切分。
- 保存课程、项目、章节、知识点、题库、题号、题型、来源文件和页码等元数据。
- 通过文件 SHA-256 哈希实现增量导入：内容不变时跳过，内容变化时替换该来源的旧切片。
- BGE-M3 稠密＋稀疏混合检索，保留 HyDE、RRF 和 Reranker。
- 支持课程介绍、知识点、项目资料、题库/题目和 MongoDB 多轮问答。
- 答案返回结构化引用；知识库来源标记为 `knowledge_base`，联网来源标记为 `web`。
- 问答页面可快捷限定课程介绍、课程知识、项目资料或题库题目。
- 支持将当前会话和资料引用一键导出为 Markdown。
- 提供不依赖模型和数据库的离线评测与 pytest 测试。

## 处理链路

```text
PDF / Markdown / DOCX
  -> 统一解析
  -> 章节感知切分 + 教育元数据
  -> SHA-256 增量判断
  -> BGE-M3 dense + sparse
  -> Milvus

用户问题 + MongoDB 历史
  -> 问题改写 / 元数据过滤
  -> 混合检索 + HyDE + 可选联网搜索
  -> RRF
  -> Reranker
  -> LLM 生成
  -> SSE / 普通响应 + 结构化引用
```

## 环境要求

- Python 3.11+
- Milvus
- MongoDB（多轮历史；不可用时单轮查询仍可降级）
- MinIO（原始资料/图片对象存储；上传失败时本地导入仍继续）
- 本地 BGE-M3 模型
- OpenAI 兼容的对话模型接口
- 可选：DashScope 联网搜索 MCP 和 Reranker 服务

所有运行文件默认写入项目下的 `.runtime/`，位于 D 盘且已被 Git 忽略。

## 安装

```powershell
cd D:\project-python\python_project\knowledge_base_study
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .
```

复制配置模板，但不要提交真实配置：

```powershell
Copy-Item .env.example .env
```

至少配置 `BGE_M3_PATH`、`MILVUS_URL`、`CHUNKS_COLLECTION`、`OPENAI_API_KEY` 和 `OPENAI_API_BASE`。`.env` 已在 `.gitignore` 中。

如果之前使用过旧商品集合，请使用新的集合名（默认 `education_chunks_v1`），因为教育元数据 schema 与旧集合不兼容。

## 启动

导入服务：

```powershell
python -m uvicorn web.api.import_service:app --host 127.0.0.1 --port 8000
```

问答服务：

```powershell
python -m uvicorn web.api.query_service:app --host 127.0.0.1 --port 8001
```

页面：

- 导入：<http://127.0.0.1:8000/import.html>
- 问答：<http://127.0.0.1:8001/chat.html>
- Swagger：<http://127.0.0.1:8000/docs> 和 <http://127.0.0.1:8001/docs>

问答页顶部的“检索范围”会自动转换为 `metadata_filters.content_type`；“导出记录”会下载当前会话的 Markdown 文件，并保留知识库/联网引用。

## 导入资料

页面支持批量拖入 `.pdf`、`.md`、`.markdown`、`.docx`。也可以调用 API：

```powershell
curl.exe -X POST http://127.0.0.1:8000/upload -F "files=@D:/education/Python课程.md"
```

每个文件返回一个 `task_id`，查询进度：

```powershell
curl.exe http://127.0.0.1:8000/status/<task_id>
```

增量规则：

1. 首次导入：解析、切分、向量化并写入 Milvus。
2. 同名且内容哈希相同：返回 `skipped`，不生成重复向量。
3. 同名但内容变化：先删除该 `source_file` 的旧切片，再插入新切片。
4. 只有 Milvus 写入成功后才更新 `.runtime/import_manifest.json`。

原始教育资料只作为本地测试数据，不应整体复制或提交到仓库。

## 问答和元数据过滤

普通问答：

```powershell
curl.exe -X POST http://127.0.0.1:8001/query `
  -H "Content-Type: application/json" `
  -d '{"query":"Python 函数参数有什么作用？","is_stream":false}'
```

按题库过滤：

```json
{
  "query": "查询函数相关的选择题",
  "is_stream": false,
  "metadata_filters": {
    "content_type": "question",
    "question_bank_name": "通用程序设计题库"
  }
}
```

允许过滤的字段包括 `content_type`、`course_name`、`project_name`、`chapter_name`、`question_bank_name`、`question_id`、`question_type`、`source_file` 和 `page_number`。

同步响应的 `citations` 示例：

```json
{
  "source": "knowledge_base",
  "chunk_id": "2f9c...",
  "course_name": "Python 入门",
  "project_name": "",
  "chapter_name": "函数",
  "chapter_path": "Python 入门 > 函数",
  "source_file": "Python课程.md",
  "page_number": 0
}
```

## 离线评测

内置小型评测集无需 Milvus、GPU、模型密钥：

```powershell
python -m education_rag.evaluation --top-k 3
```

输出对比：

- `dense`：纯稠密检索
- `hybrid`：稠密＋稀疏检索
- `hybrid_rerank`：混合检索＋轻量 mock Reranker
- `hybrid_rerank_hyde`：增加 mock HyDE 并通过 RRF 融合

每种模式输出 `Recall@K`、`MRR` 和平均检索耗时。也可用 `--dataset path.jsonl` 指定 JSONL 数据集，记录的 `type` 为 `document` 或 `query`。

## 测试

```powershell
python -m pytest
python -m compileall education_rag processor web utils config
```

测试覆盖 Markdown/DOCX/PDF 解析接口、章节与元数据、文件哈希幂等替换、引用字段和四种检索评测模式。外部服务在自动化测试中使用 mock，不会把“未启动 Milvus/模型服务”伪装成真实联调成功。

## 主要目录

```text
education_rag/                 可独立测试的解析、切分、增量、评测核心
processor/import_processor/    LangGraph 教育资料导入流程
processor/query_processor/     LangGraph 教育问答流程
web/api/                       FastAPI 导入与查询接口
web/page/                      导入与问答页面
tests/                         pytest 自动化测试
scripts/evaluate_rag.py        评测入口
```

## 已知限制

- PDF 文本由 `pypdf` 本地抽取；扫描版 PDF 仍需要 OCR/MinerU，当前未在无密钥环境真实联调。
- DOCX 页码来自显式分页符或 Word 渲染分页标记；没有分页标记时页码从 1 开始，章节路径仍可用。
- Milvus、BGE-M3、Reranker、LLM、MongoDB、MinIO 和联网搜索需要对应本地服务或密钥，本仓库的自动化测试只验证 mock/纯本地路径。
- 任务状态当前保存在单进程内存中，适合面试演示；多实例部署需要迁移到 Redis 等共享存储。
