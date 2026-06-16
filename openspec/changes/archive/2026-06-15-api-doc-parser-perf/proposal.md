## Why

当前 `api-doc-parser` 在解析中大型 OpenAPI 文档（100-500KB）时速度较慢。测试与反馈显示，耗时主要集中在：

1. **多阶段 Skill 切换开销大**：`doc-fetch → doc-list → doc-parse` 三阶段各自加载超长 `SKILL.md`，每次调用都产生大量上下文和 token 消耗。
2. **jq/Bash 调用次数过多**：每个 tag、每个 `$ref` schema 都发起独立 jq 查询，反复读取 `components/schemas`。
3. **Schema 展开未批量化**：v2 已支持递归展开 `$ref`，但实现方式依赖多次 shell 调用，复杂文档下性能急剧下降。
4. **格式化输出由 LLM 承担**：Markdown/JSON 的生成大量占用模型上下文，输出大模块时尤为明显。

因此需要对核心解析流程做性能优化，在保持上下文溢出保护的前提下，显著降低解析耗时和 token 消耗。

## What Changes

- 新增 `skills/doc-parse/parse.py` 作为统一解析引擎
  - 单次读取 OpenAPI JSON 和 `state.json`
  - 批量递归展开 `$ref` schema（depth ≤ 2，带循环引用检测）
  - 直接生成 Markdown + JSON 输出文件
- 简化 `skills/doc-parse/SKILL.md`
  - 仅保留：依赖检查、状态读取、参数解析、调用 `parse.py`、结果展示
- 新增 `skills/doc-parse/lib/` 可复用模块（可选）
  - `schema_cache.py`：预索引并缓存 `components/schemas`
  - `formatter.py`：Markdown/JSON 渲染
- 新增 `-y` / `--auto` 标志，跳过大型模块二次确认
- 保持 `doc-fetch` 和 `doc-list` 不变，仅把 `doc-parse` 的执行核心下沉到 Python 脚本

## Capabilities

### Improved Capabilities

- `api-doc-parser` / `doc-parse`：解析 OpenAPI/Swagger 接口文档的速度显著提升，大模块、复杂 Schema 展开场景下尤为明显，同时保持 Markdown + JSON 双格式输出和上下文溢出保护。

## Impact

- 新增文件 `skills/doc-parse/parse.py`（核心解析引擎）
- 新增可选目录 `skills/doc-parse/lib/`（缓存与格式化模块）
- 修改 `skills/doc-parse/SKILL.md`（精简为调用层）
- 依赖新增 `python3`（已有 jq/curl 基础上）
- 不改变输入源、输出格式、状态文件路径和命令接口
- 向后兼容：`.output/` 文件结构和字段命名保持不变
