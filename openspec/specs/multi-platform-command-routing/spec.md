# multi-platform-command-routing

平台级命令路由，支持在 9 个 AI 编码助手中通过斜杠命令调用 api-doc-parser 子技能。

## ADDED Requirements

### Requirement: Claude Code command routing
The skill SHALL provide slash commands in `.claude/commands/doc/` for the `doc` prefix.

#### Scenario: /doc:fetch command
- **WHEN** user types `/doc:fetch <URL>` in Claude Code
- **THEN** the skill SHALL invoke the `doc-fetch` skill with the provided URL

#### Scenario: /doc:list command
- **WHEN** user types `/doc:list` in Claude Code
- **THEN** the skill SHALL invoke the `doc-list` skill

#### Scenario: /doc:parse command
- **WHEN** user types `/doc:parse [query]` in Claude Code
- **THEN** the skill SHALL invoke the `doc-parse` skill with the optional query

#### Scenario: /doc:help command
- **WHEN** user types `/doc:help` in Claude Code
- **THEN** the skill SHALL invoke the `doc-help` skill

### Requirement: Cursor command routing
The skill SHALL provide slash commands in `.cursor/commands/doc/` for the `doc` prefix.

#### Scenario: Cursor commands accessible
- **WHEN** user types `/doc-parse` in Cursor
- **THEN** the skill SHALL invoke the `doc-parse` skill

### Requirement: Codex command routing
The skill SHALL provide slash commands in `.codex/commands/doc/` for the `doc` prefix.

#### Scenario: Codex commands accessible
- **WHEN** user types `/doc-parse` in Codex
- **THEN** the skill SHALL invoke the `doc-parse` skill

### Requirement: Gemini command routing
The skill SHALL provide commands in `.gemini/commands/opsx/` in TOML format for Gemini CLI.

#### Scenario: Gemini commands accessible
- **WHEN** user invokes `doc-parse` in Gemini CLI
- **THEN** the skill SHALL invoke the `doc-parse` skill

### Requirement: Kimi skill routing
The skill SHALL provide skills in `.kimi/skills/` for Kimi AI platform.

#### Scenario: Kimi skills accessible
- **WHEN** Kimi AI encounters API doc parsing tasks
- **THEN** it SHALL load the corresponding skill from `.kimi/skills/doc-*/`

### Requirement: Qoder command routing
The skill SHALL provide commands in `.qoder/commands/doc/` for Qoder platform.

#### Scenario: Qoder commands accessible
- **WHEN** user invokes doc-related commands in Qoder
- **THEN** the skill SHALL route to the corresponding doc sub-skill

### Requirement: Trae skill routing
The skill SHALL provide skills in `.trae/skills/` for Trae AI platform.

#### Scenario: Trae skills accessible
- **WHEN** Trae AI encounters API doc parsing tasks
- **THEN** it SHALL load the corresponding skill from `.trae/skills/doc-*/`

### Requirement: OpenCode command routing
The skill SHALL provide commands in `.opencode/commands/` and skills in `.opencode/skills/` for OpenCode.

#### Scenario: OpenCode commands accessible
- **WHEN** user invokes doc commands in OpenCode
- **THEN** the skill SHALL route to the corresponding doc sub-skill

### Requirement: GitHub Copilot prompt routing
The skill SHALL provide prompt files in `.github/prompts/` for GitHub Copilot.

#### Scenario: Copilot prompts accessible
- **WHEN** GitHub Copilot encounters API doc parsing context
- **THEN** it SHALL load the corresponding prompt from `.github/prompts/doc-*.prompt.md`

### Requirement: Command-to-skill mapping consistency
All platform command routing files SHALL reference the same `skills/doc-*/SKILL.md` source directory as the single source of truth.

#### Scenario: Single source of truth
- **WHEN** any platform command is invoked
- **THEN** it SHALL proxy to the shared `skills/<skill-name>/SKILL.md` content, NOT maintain a separate copy
