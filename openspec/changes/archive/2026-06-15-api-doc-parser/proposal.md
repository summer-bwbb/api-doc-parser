## Why

团队需要频繁查阅后端接口文档来编写前端代码或进行联调测试，但每次都必须在浏览器中打开 Swagger UI，逐接口查看参数和响应，无法一键检索、无法复用、也无法跨对话共享。需要一个轻量级 Skill，直接从 OpenAPI JSON 文档中按模块提取接口详情，输出可复制粘贴的 Markdown 和可引用的结构化 JSON。

## What Changes

- 新增 `api-doc-parser` 技能，支持解析 OpenAPI 3.x / Swagger 2.0 格式的接口文档
- 新增 `/doc:parse` 命令（Claude Code 平台），支持交互式的文档解析流程
- 新增 `/doc:help` 命令，显示技能使用说明
- 支持双输入源：远程 URL 抓取 + 本地文件导入（.json / .md / .txt）
- 支持按模块（tags）筛选，一次查询多个模块
- 输出 Markdown 格式（粘贴即用）+ 结构化 JSON（可被程序/对话引用）
- 可选输出模式：直接在对话中展示 或 持久化到 `.output/` 目录
- 内置上下文溢出保护：jq 管线过滤，原始 JSON 不进入 Agent 上下文

## Capabilities

### New Capabilities

- `api-doc-parser`: 解析 OpenAPI/Swagger 接口文档，按模块提取接口详情，输出 Markdown + JSON 双格式。支持 URL 和本地文件两种输入源，支持多模块查询，内置上下文溢出保护。

## Impact

- 新增目录 `api-doc-parser/`（项目根目录下独立 Skill 文件夹，包含 SKILL.md、README.md、metadata.json，参考 `vue-gis-perf-practices/` 模式）
- 新增目录 `.claude/commands/doc/`（Claude Code 命令路由）
- 新增目录 `.cursor/commands/doc/`（Cursor 命令路由）
- 新增目录 `.codex/commands/doc/`（Codex 命令路由）
- 依赖 `curl`、`jq` 用于 URL 抓取和 JSON 过滤（Shell 层，不进上下文）
- 不修改任何现有文件
