## 1. Cleanup — 移除无关文件

- [ ] 1.1 删除 `.claude/skills/openspec-*/` 下 6 个 openspec 子技能（与本项目无关，应由 openspec plugin 独立安装）
- [ ] 1.2 删除 `.claude/commands/opsx/` 下 6 个 openspec command 路由（同上）
- [ ] 1.3 删除 `.cursor/skills/openspec-*/`、`.codex/skills/openspec-*/`、`.gemini/skills/openspec-*/`、`.kimi/skills/openspec-*/`、`.qoder/skills/openspec-*/`、`.trae/skills/openspec-*/`、`.opencode/skills/openspec-*/`、`.github/skills/openspec-*/` 中所有 openspec 子技能
- [ ] 1.4 删除 `.cursor/commands/opsx-*.md`、`.codex/commands/`、`.gemini/commands/opsx/`、`.qoder/commands/opsx/`、`.opencode/commands/opsx-*.md`、`.github/prompts/opsx-*.prompt.md` 中所有 openspec command/prompt 路由

## 2. 核心子技能创建 — skills/

- [ ] 2.1 创建 `skills/using-api-doc-parser/SKILL.md` — 元指令，教 Agent 如何发现和调用 doc-* 子技能，列出触发关键词（parse API docs, extract endpoints, Swagger, OpenAPI），说明 fetch→list→parse 管道
- [ ] 2.2 创建 `skills/doc-fetch/SKILL.md` — Phase 1（源输入），从原始 SKILL.md 提取：URL 检测/抓取/验证（curl + jq 校验）、本地文件处理（.json/.md/.txt）、错误恢复、写入 /tmp/api-doc-parser/state.json
- [ ] 2.3 创建 `skills/doc-list/SKILL.md` — Phase 2（模块列表），jq 提取 tags、端点数统计、表格展示、多选/关键词/全部选择、大模块（>30）警告、更新 state.json 的 selectedTags
- [ ] 2.4 创建 `skills/doc-parse/SKILL.md` — Phase 3-5（接口提取 + 输出），jq 按 tag 过滤 paths、提取 endpoint 详情、$ref 处理、Markdown + JSON 生成、Output Mode A/B、多模块文件输出
- [ ] 2.5 创建 `skills/doc-help/SKILL.md` — 帮助，显示支持的命令、输入格式、输出模式、示例用法

## 3. 平台 Skills 与 Commands 路由

- [ ] 3.1 创建 `.claude/skills/` 下 5 个子技能代理 SKILL.md（引用 `skills/<name>/SKILL.md`）
- [ ] 3.2 创建 `.claude/commands/doc/fetch.md` — `/doc:fetch` 命令路由
- [ ] 3.3 创建 `.claude/commands/doc/list.md` — `/doc:list` 命令路由
- [ ] 3.4 创建 `.claude/commands/doc/parse.md` — `/doc:parse` 命令路由
- [ ] 3.5 创建 `.claude/commands/doc/help.md` — `/doc:help` 命令路由
- [ ] 3.6 创建 `.cursor/skills/` + `.cursor/commands/doc/` — Cursor 平台（5 skills + 4 commands）
- [ ] 3.7 创建 `.codex/skills/` + `.codex/commands/doc/` — Codex 平台（5 skills + 4 commands）
- [ ] 3.8 创建 `.gemini/skills/` + `.gemini/commands/doc/` — Gemini 平台（5 skills + 4 .toml commands）
- [ ] 3.9 创建 `.kimi/skills/` — Kimi 平台（5 skills，无 commands）
- [ ] 3.10 创建 `.qoder/skills/` + `.qoder/commands/doc/` — Qoder 平台（5 skills + 4 commands）
- [ ] 3.11 创建 `.trae/skills/` — Trae 平台（5 skills，无 commands）
- [ ] 3.12 创建 `.opencode/skills/` + `.opencode/commands/` — OpenCode 平台（5 skills + 4 commands）
- [ ] 3.13 创建 `.github/skills/` + `.github/prompts/` — GitHub Copilot（5 skills + 4 .prompt.md）

## 4. Plugin 打包

- [ ] 4.1 创建 `.claude-plugin/plugin.json` — Claude Code plugin manifest（name, version, description, author, skills path, commands path, hooks path）
- [ ] 4.2 创建 `.claude-plugin/marketplace.json` — marketplace 上架信息（name, description, owner, plugins[]）
- [ ] 4.3 创建 `.cursor-plugin/plugin.json` — Cursor plugin manifest（skills path, commands path, hooks path）
- [ ] 4.4 创建 `.codex-plugin/plugin.json` — Codex plugin manifest（skills path, commands path, interface 信息）

## 5. NPM 打包

- [ ] 5.1 创建 `package.json` — name: `api-doc-parser-skill`, version: `2.0.0`, description, author, license, keywords, files[], scripts: {postinstall, preuninstall}
- [ ] 5.2 创建 `scripts/postinstall.js` — 检测已安装的 AI 编码助手，注册 skills 到对应配置目录
- [ ] 5.3 创建 `scripts/preuninstall.js` — 从各 AI 编码助手配置目录移除已注册的 skills

## 6. Hooks — SessionStart 注入

- [ ] 6.1 创建 `hooks/hooks.json` — SessionStart hook（matcher: startup|clear|compact，command 触发 session-start 脚本）
- [ ] 6.2 创建 `hooks/hooks-cursor.json` — Cursor 版 SessionStart hook
- [ ] 6.3 创建 `hooks/run-hook.cmd` / `hooks/session-start` — Windows 和 Unix 的 hook 执行脚本

## 7. 文档

- [ ] 7.1 创建 `docs/INSTALL.md` — 三种安装方式（Plugin / NPM / 手动）+ 验证 + 更新 + 卸载 + 故障排查
- [ ] 7.2 创建 `docs/USAGE.md` — 命令参考 + 5+ 场景示例 + 输出格式说明 + FAQ
- [ ] 7.3 创建 `docs/CHANGELOG.md` — v1.0.0 初始版本 + v2.0.0 本次升级

## 8. 根文件更新 — 向后兼容

- [ ] 8.1 更新 `SKILL.md` — 保留原有 5-Phase 完整逻辑，在顶部添加子技能导航说明（"For fine-grained control, use /doc:fetch, /doc:list, /doc:parse"），保持向后兼容
- [ ] 8.2 更新 `metadata.json` — version → `2.0.0`，description 增加 plugin/npm/commands 等信息
- [ ] 8.3 更新 `README.md` — 反映 v2 架构：子技能拆分、三种安装方式、命令参考入口、文档链接
- [ ] 8.4 创建 `GEMINI.md` — 内容 `@./skills/using-api-doc-parser/SKILL.md`（参考 superpowers 模式）
- [ ] 8.5 创建 `AGENTS.md` → 指向 `CLAUDE.md` 或直接引用 using-api-doc-parser
- [ ] 8.6 创建 `gemini-extension.json` — Gemini 扩展清单

## 9. 验证

- [ ] 9.1 验证所有 skill frontmatter 格式正确（`---\nname: ...\ndescription: ...\n---`）
- [ ] 9.2 验证所有 command 路由文件正确指向对应 skill
- [ ] 9.3 用 Petstore API 端到端测试：`/doc:fetch https://petstore3.swagger.io/api/v3/openapi.json` → `/doc:list` → `/doc:parse pet` → 检查 `.output/` 输出
- [ ] 9.4 验证向后兼容：自然语言 "Parse API docs from <URL>" 仍能触发原 SKILL.md 逻辑
- [ ] 9.5 验证 SessionStart hook 正确注入 using-api-doc-parser（新开 Claude Code 会话检查）
- [ ] 9.6 验证跨 Phase 状态传递：检查 `/tmp/api-doc-parser/state.json` 在 fetch → list → parse 各阶段的内容
