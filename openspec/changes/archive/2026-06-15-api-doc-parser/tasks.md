## 1. Skill 核心文件

- [x] 1.1 在项目根目录创建 `api-doc-parser/` 独立 Skill 文件夹（参考 `vue-gis-perf-practices/` 模式）
- [x] 1.2 编写 `api-doc-parser/SKILL.md` — 核心技能逻辑，包含完整执行流程：输入源选择、模块列表提取（jq 管线）、模块多选/关键词匹配、接口详情解析、输出模式选择、Markdown + JSON 生成
- [x] 1.3 编写 `api-doc-parser/README.md` — 用户使用说明，包含命令用法、示例、输出格式说明
- [x] 1.4 编写 `api-doc-parser/metadata.json` — Skill 元数据（参考 vue-gis-perf-practices/metadata.json）

## 2. 上下文溢出防护

- [x] 2.1 在 SKILL.md 中定义 curl + jq 管线策略：curl URL 写入 `/tmp/api-doc.json`，再用 `jq '.tags'` 提取模块列表，`jq` 过滤目标模块 paths
- [x] 2.2 定义大模块保护策略：模块 >30 个接口时先显示摘要列表
- [x] 2.3 定义本地大文件策略：>.json 文件 >256KB 用 jq 过滤，.md/.txt 用 Read offset/limit 分页
- [x] 2.4 明确禁止直接 Read 原始 OpenAPI JSON 全文进入 Agent 上下文

## 3. 平台命令路由

- [x] 3.1 创建 `.claude/commands/doc/parse.md` — /doc:parse 命令路由（frontmatter + 调用指令）
- [x] 3.2 创建 `.claude/commands/doc/help.md` — /doc:help 命令路由
- [x] 3.3 创建 `.cursor/commands/doc/doc-parse.md` — Cursor 版命令路由
- [x] 3.4 创建 `.cursor/commands/doc/doc-help.md` — Cursor 版命令路由
- [x] 3.5 创建 `.codex/commands/doc/doc-parse.md` — Codex 版命令路由
- [x] 3.6 创建 `.codex/commands/doc/doc-help.md` — Codex 版命令路由

## 4. 验证

- [x] 4.1 检查所有文件的 frontmatter 格式正确
- [x] 4.2 验证 SKILL.md 覆盖所有规格需求（双输入源、多模块、双输出、溢出防护）
- [x] 4.3 确认目录结构与设计文档一致
