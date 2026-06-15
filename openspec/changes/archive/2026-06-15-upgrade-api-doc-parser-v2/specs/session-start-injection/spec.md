# session-start-injection

SessionStart hook 自动注入 using-api-doc-parser 元指令，与 superpowers 的 SessionStart 机制一致。

## ADDED Requirements

### Requirement: SessionStart hook configuration
The skill SHALL provide a `hooks/hooks.json` that configures SessionStart injection of the using-api-doc-parser skill.

#### Scenario: Hook on session start
- **WHEN** a new Claude Code session starts with api-doc-parser installed
- **THEN** the SessionStart hook SHALL trigger and inject the using-api-doc-parser skill into the agent's context

#### Scenario: Hook on session resume
- **WHEN** a session is resumed after compact/clear
- **THEN** the hook SHALL re-inject using-api-doc-parser to ensure skill discovery

#### Scenario: Hook does not interfere with other plugins
- **WHEN** multiple plugins have SessionStart hooks (e.g., superpowers + api-doc-parser)
- **THEN** both hooks SHALL execute without conflict

### Requirement: using-api-doc-parser content
The injected skill SHALL contain minimal meta-instructions that teach the agent how to discover and invoke api-doc-parser sub-skills.

#### Scenario: Natural language trigger discovery
- **WHEN** user mentions "parse API docs", "extract endpoints", "Swagger", "OpenAPI" in conversation
- **THEN** the using-api-doc-parser instructions SHALL guide the agent to invoke the Skill tool with `doc-fetch`, `doc-list`, or `doc-parse`

#### Scenario: Slash command discovery
- **WHEN** user types `/doc:` in an IDE that supports command completion
- **THEN** all available doc sub-commands SHALL be discoverable

### Requirement: Platform-agnostic injection
The hook mechanism SHALL work equivalently across Claude Code, Cursor, and Codex platforms.

#### Scenario: Claude Code injection
- **WHEN** installed as Claude Code plugin
- **THEN** `.claude-plugin/plugin.json` plus `hooks/hooks.json` SHALL enable SessionStart injection

#### Scenario: Cursor injection
- **WHEN** installed as Cursor plugin
- **THEN** `.cursor-plugin/plugin.json` plus `hooks/hooks-cursor.json` SHALL enable injection

#### Scenario: Codex injection
- **WHEN** installed as Codex plugin
- **THEN** `.codex-plugin/plugin.json` SHALL reference the hooks configuration
