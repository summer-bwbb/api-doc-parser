## Why

当前 api-doc-parser 是一个单一 SKILL.md 文件（v1），所有逻辑耦合在一起，缺少跨平台命令路由、Plugin 安装支持、以及模块化的子技能拆分。用户无法通过 `/doc:fetch`、`/doc:list` 等细粒度命令调用，也无法全局安装后跨项目复用。此次升级将其改造为类似 openspec/superpowers 的架构：细粒度子技能、多平台命令路由、Plugin + NPM 双渠道分发、以及全局/项目双模式使用。

## What Changes

- **BREAKING**: 将 SKILL.md 从单一文件拆分为 5 个独立子技能：`using-api-doc-parser`、`doc-fetch`、`doc-list`、`doc-parse`、`doc-help`
- 新增跨平台命令路由（`.claude/`、`.cursor/`、`.codex/`、`.gemini/`、`.kimi/`、`.qoder/`、`.trae/`、`.opencode/`、`.github/`），支持 `/doc:fetch`、`/doc:list`、`/doc:parse`、`/doc:help` 斜杠命令
- 新增 Plugin 安装支持：Claude Code Plugin（`.claude-plugin/plugin.json`）、Cursor Plugin（`.cursor-plugin/plugin.json`）、Codex Plugin（`.codex-plugin/plugin.json`）
- 新增 NPM 上架支持（`package.json` + postinstall/preuninstall 脚本）
- 新增 SessionStart hook（`hooks/hooks.json`），启动时自动注入 `using-api-doc-parser` 元指令
- 新增跨 Phase 状态传递机制（`/tmp/api-doc-parser/state.json`），支持 `fetch → list → parse` 管道独立调用
- 新增 `docs/INSTALL.md`（三种安装方式）和 `docs/USAGE.md`（命令参考 + 场景示例）
- 保留原始 `SKILL.md` 作为向后兼容的直接对话触发入口

## Capabilities

### New Capabilities
- `multi-platform-command-routing`: 9 平台斜杠命令路由（Claude Code, Cursor, Codex, Gemini, Kimi, Qoder, Trae, OpenCode, GitHub Copilot）
- `plugin-packaging`: Plugin manifest（Claude Code + Cursor + Codex）+ NPM package.json，支持全局安装和项目级内嵌
- `install-documentation`: 三种安装方式完整手册（Plugin / NPM / 手动）+ 使用手册
- `subskill-architecture`: 5 个子技能拆分（using / fetch / list / parse / help），独立可调用
- `cross-phase-state`: Phase 间状态传递（fetch → list → parse 管道共享状态文件）
- `session-start-injection`: SessionStart hook 自动注入 using-api-doc-parser 元指令
- `session-start-injection`: SessionStart hook 自动注入 using-api-doc-parser 元指令

### Modified Capabilities
- `api-doc-parser`: SKILL.md 拆分为子技能后保留主文件作为向后兼容入口；原有 Phase 1-5 逻辑迁移至 doc-fetch / doc-list / doc-parse 三个子技能

## Impact

- 影响文件/目录：新增 `skills/`、`commands/`、`hooks/`、`docs/`、`.claude-plugin/`、`.cursor-plugin/`、`.codex-plugin/`、`.claude/`、`.cursor/`、`.codex/`、`.gemini/`、`.kimi/`、`.qoder/`、`.trae/`、`.opencode/`、`.github/`、`package.json`、`scripts/`、`GEMINI.md`、`AGENTS.md`、`gemini-extension.json`
- 修改文件：`SKILL.md`（重构为向后兼容入口）、`metadata.json`（更新版本号）、`README.md`（更新为 v2 架构说明）
- 删除文件：当前 `.claude/skills/openspec-*/` 下的 6 个 skill（不相关，由 openspec 项目独立管理）
- 依赖：`jq` ≥ 1.6、`curl` ≥ 7.0（运行时依赖，无变化）
