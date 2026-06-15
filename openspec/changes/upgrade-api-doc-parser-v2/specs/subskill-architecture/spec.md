# subskill-architecture

将原始 SKILL.md 的 5 个 Phase 拆分为 5 个独立可调用的子技能。

## ADDED Requirements

### Requirement: using-api-doc-parser meta-skill
The skill SHALL provide a `skills/using-api-doc-parser/SKILL.md` that serves as the meta-instruction entry point, equivalent to `using-superpowers`.

#### Scenario: Meta instructions loaded
- **WHEN** a session starts with api-doc-parser installed
- **THEN** the using-api-doc-parser meta-instructions SHALL be injected via SessionStart hook

#### Scenario: Skill discovery guidance
- **WHEN** user mentions API documentation parsing
- **THEN** the meta-skill SHALL guide the agent to invoke relevant doc-* skills

### Requirement: doc-fetch sub-skill
The skill SHALL provide a `skills/doc-fetch/SKILL.md` covering Phase 1 (source input) of the original SKILL.md.

#### Scenario: Fetch from URL
- **WHEN** user invokes `/doc:fetch <URL>` or asks to fetch API docs from a URL
- **THEN** the skill SHALL validate the URL, fetch via curl, save to temp file, and record the source path in shared state

#### Scenario: Fetch from local file
- **WHEN** user invokes `/doc:fetch <file.json>` or asks to parse a local file
- **THEN** the skill SHALL validate the file, check size, and record the source path in shared state

#### Scenario: Fetch error handling
- **WHEN** the URL is unreachable or file does not exist
- **THEN** the skill SHALL report a clear error and offer retry or fallback options

#### Scenario: State persistence
- **WHEN** fetch completes successfully
- **THEN** the skill SHALL write source metadata to `/tmp/api-doc-parser/state.json` for subsequent doc-list/doc-parse calls

### Requirement: doc-list sub-skill
The skill SHALL provide a `skills/doc-list/SKILL.md` covering Phase 2 (module listing) of the original SKILL.md.

#### Scenario: List all modules
- **WHEN** user invokes `/doc:list` without arguments
- **THEN** the skill SHALL extract all tags from the OpenAPI document and display them in a numbered table with endpoint counts

#### Scenario: Select modules by keyword
- **WHEN** user invokes `/doc:list <keywords>` with comma-separated keywords
- **THEN** the skill SHALL fuzzy-match keywords against tag names and cache the selected modules in shared state

#### Scenario: Select modules by index
- **WHEN** user invokes `/doc:list <indices>` with comma-separated numbers
- **THEN** the skill SHALL resolve indices and cache the selected modules

#### Scenario: Select all modules
- **WHEN** user invokes `/doc:list all`
- **THEN** the skill SHALL select all modules

#### Scenario: Large module warning
- **WHEN** a selected module has >30 endpoints
- **THEN** the skill SHALL display a summary and ask for confirmation before full extraction

### Requirement: doc-parse sub-skill
The skill SHALL provide a `skills/doc-parse/SKILL.md` covering Phases 3-5 (endpoint extraction, output generation, output mode) of the original SKILL.md.

#### Scenario: Parse selected modules
- **WHEN** user invokes `/doc:parse` after doc-fetch and doc-list
- **THEN** the skill SHALL extract endpoint details for all selected modules using jq, generate Markdown tables and JSON structures

#### Scenario: Parse with inline query
- **WHEN** user invokes `/doc:parse <keyword>` directly (bypassing doc-list)
- **THEN** the skill SHALL first match the keyword to modules, then parse them

#### Scenario: Output mode A — direct display
- **WHEN** user selects output mode A
- **THEN** the skill SHALL output Markdown directly in conversation without writing files

#### Scenario: Output mode B — file persistence
- **WHEN** user selects output mode B
- **THEN** the skill SHALL write `.md` and `.json` files to the project's `api-doc-parser/.output/` directory

#### Scenario: Empty module handling
- **WHEN** a selected module has no endpoints
- **THEN** the skill SHALL report the empty module and continue with remaining modules

### Requirement: doc-help sub-skill
The skill SHALL provide a `skills/doc-help/SKILL.md` that displays usage instructions.

#### Scenario: Display help
- **WHEN** user invokes `/doc:help`
- **THEN** the skill SHALL display: supported commands, input formats, output modes, and example usage

### Requirement: Backward compatibility with original SKILL.md
The root `SKILL.md` SHALL be preserved as a backward-compatible entry point that can still handle natural language API doc parsing requests.

#### Scenario: Direct conversation trigger
- **WHEN** user says "Parse API docs from <URL>" without using slash commands
- **THEN** the original SKILL.md logic SHALL still be invoked via its natural language matching

#### Scenario: Orphaned .claude openspec skills
- **WHEN** cleaning up the project directory
- **THEN** the 6 existing `.claude/skills/openspec-*/` directories that duplicate openspec plugin content SHALL be removed, as they are unrelated to api-doc-parser functionality

### Requirement: Output mode parameter override
The `doc-parse` sub-skill SHALL support parameter flags to override the persisted output mode preference.

#### Scenario: Override to Mode A
- **WHEN** user invokes `/doc:parse -a` or `/doc:parse --display`
- **THEN** output SHALL go to conversation display regardless of persisted `outputMode` in state.json

#### Scenario: Override to Mode B
- **WHEN** user invokes `/doc:parse -b` or `/doc:parse --save`
- **THEN** files SHALL be written to `api-doc-parser/.output/` regardless of persisted `outputMode`

#### Scenario: First-run mode prompt
- **WHEN** user invokes `doc-parse` without a previously set `outputMode` in state.json
- **THEN** the skill SHALL prompt "Output mode: A (display) or B (save files)?" and persist the choice

### Requirement: doc-list pagination for large tag sets
When a document has more than 50 tags, `doc-list` SHALL display results in pages.

#### Scenario: Paginated tag display
- **WHEN** the OpenAPI document has >50 tags
- **THEN** `doc-list` SHALL display 20 tags per page and instruct the user how to navigate pages

#### Scenario: Cross-page selection
- **WHEN** user selects tags across multiple pages in a single input
- **THEN** the skill SHALL resolve selections correctly

### Requirement: Runtime dependency check
Each sub-skill SHALL verify `jq` and `curl` are available before executing core logic.

#### Scenario: Missing jq
- **WHEN** any doc-* sub-skill runs and `jq` is not installed
- **THEN** the skill SHALL report "ERROR: jq >= 1.6 required" with OS-specific install instructions and stop

#### Scenario: Missing curl in doc-fetch
- **WHEN** `doc-fetch` runs and `curl` is not installed
- **THEN** the skill SHALL report "ERROR: curl >= 7.0 required" with OS-specific install instructions and stop
