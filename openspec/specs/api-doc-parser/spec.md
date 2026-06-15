# api-doc-parser Specification

## Purpose

Parse OpenAPI/Swagger API documentation from remote URLs or local files, extract endpoint details by module, and output structured Markdown and JSON — enabling developers to quickly understand and reference API documentation without reading raw OpenAPI JSON.

## Requirements

### Requirement: Dual input source support
The skill SHALL support two input sources for API documentation:
1. Remote URL (e.g., `http://host:port/path/v3/api-docs`) — fetched via curl，handled by `doc-fetch` sub-skill
2. Local file path — .json (OpenAPI/Swagger), .md (markdown documentation), .txt (plain text) — handled by `doc-fetch` sub-skill

The source processing logic SHALL be delegated to the `doc-fetch` sub-skill, while the root `SKILL.md` retains backward-compatible natural language triggering that chains through the same sub-skills.

#### Scenario: User provides URL
- **WHEN** user inputs a valid HTTP/HTTPS URL
- **THEN** the skill SHALL delegate to `doc-fetch` sub-skill, which fetches the JSON document via curl, writes it to a temporary file, and proceeds with parsing

#### Scenario: User provides local JSON file
- **WHEN** user provides a path to a `.json` file containing OpenAPI/Swagger document
- **THEN** the skill SHALL delegate to `doc-fetch` sub-skill, which validates and records the source path

#### Scenario: User provides local markdown file
- **WHEN** user provides a path to a `.md` file containing API documentation
- **THEN** the skill SHALL delegate to `doc-fetch` sub-skill, which records the source for LLM extraction

#### Scenario: User provides local text file
- **WHEN** user provides a path to a `.txt` file containing API descriptions
- **THEN** the skill SHALL delegate to `doc-fetch` sub-skill, which records the source for LLM extraction

#### Scenario: Invalid URL
- **WHEN** user provides an unreachable URL via `doc-fetch`
- **THEN** the skill SHALL report the error and offer retry or fallback to local file input

### Requirement: Module listing and selection
The skill SHALL extract all API modules (tags) from the OpenAPI document via the `doc-list` sub-skill, supporting both numeric multi-select and keyword fuzzy matching.

#### Scenario: List all modules
- **WHEN** `doc-list` is invoked without arguments
- **THEN** the skill SHALL display all unique tags with their descriptions and endpoint count

#### Scenario: Multi-select by index
- **WHEN** user inputs comma-separated indices (e.g., "1,3,6")
- **THEN** the skill SHALL select modules at those indices, deduplicate, cache in shared state, and proceed

#### Scenario: Select by keyword
- **WHEN** user inputs comma-separated keywords (e.g., "飞行,监控")
- **THEN** the skill SHALL match keywords against tag names using fuzzy matching, cache in shared state, and select all matching modules

#### Scenario: Both index and keyword mix
- **WHEN** user inputs a mix of indices and keywords
- **THEN** the skill SHALL resolve both, deduplicate by tag name, cache in shared state, and proceed with the union

#### Scenario: Select all
- **WHEN** user inputs "all" or "全部"
- **THEN** the skill SHALL select and cache all available modules

### Requirement: Endpoint detail extraction
For each selected module, the skill SHALL delegate to `doc-parse` sub-skill to extract and present every endpoint's full details.

#### Scenario: Extract endpoint details
- **WHEN** a module is selected for parsing via `doc-parse`
- **THEN** the skill SHALL extract for each endpoint: URL (path key), name (summary), description, HTTP method (get/post/put/delete/patch), parameters (name, location, type, required, default, description), requestBody (content-type, schema reference), and responses (status code, description, schema reference)

#### Scenario: Parse with inline query
- **WHEN** user invokes `/doc:parse <keyword>` without a prior `/doc:list`
- **THEN** the skill SHALL first resolve the keyword to matching modules, then parse them

#### Scenario: $ref schema handling
- **WHEN** an endpoint's response or request body contains a `$ref` reference
- **THEN** the skill SHALL record the reference name without expanding it

#### Scenario: Empty module
- **WHEN** a selected module has no endpoints
- **THEN** the skill SHALL report "No endpoints found for module [name]" and continue with remaining modules

### Requirement: Dual format output
The skill SHALL generate both Markdown (human-readable, copy-paste ready) and structured JSON (machine-readable, cross-session referenceable) for all parsed endpoints via `doc-parse` sub-skill.

#### Scenario: Generate Markdown output
- **WHEN** endpoint extraction completes
- **THEN** the skill SHALL produce a Markdown document with module title, module description, endpoint count, and per-endpoint sections

#### Scenario: Generate JSON output
- **WHEN** endpoint extraction completes
- **THEN** the skill SHALL produce a JSON document with meta (sourceUrl, generatedAt, openapiVersion), module name, description, endpointCount, and endpoints array

#### Scenario: Multiple modules in output
- **WHEN** multiple modules are selected
- **THEN** each module SHALL be output as a separate Markdown section and a separate JSON file

### Requirement: Output mode selection
The skill SHALL offer two output modes: direct display in conversation or file persistence, via `doc-parse` sub-skill.

#### Scenario: Direct display mode
- **WHEN** user selects output mode "A" (direct display)
- **THEN** the skill SHALL output the complete Markdown directly into the conversation without writing files

#### Scenario: File persistence mode
- **WHEN** user selects output mode "B" (save files)
- **THEN** the skill SHALL write `.md` and `.json` files to `api-doc-parser/.output/` directory with module name as filename, and display a summary with file paths

### Requirement: Context overflow prevention
The skill SHALL prevent large raw JSON documents from entering the Agent context by using shell-level filtering.

#### Scenario: URL source large document
- **WHEN** fetching a large OpenAPI JSON from URL
- **THEN** the skill SHALL use curl to write to a temporary file and jq pipelines to extract only needed data

#### Scenario: Local JSON file large document
- **WHEN** reading a large local JSON file (>256KB)
- **THEN** the skill SHALL use jq command-line tool to pre-filter rather than reading the entire file into context

#### Scenario: Large module endpoint count
- **WHEN** a selected module has more than 30 endpoints
- **THEN** the skill SHALL first display a summary and ask the user whether to proceed with full parsing

### Requirement: Cross-platform command registration
The skill SHALL support invocation via slash commands across Claude Code, Cursor, Codex, Gemini, Qoder, OpenCode, and Copilot platforms with a unified `doc` prefix.

#### Scenario: Claude Code command
- **WHEN** user types `/doc:parse` in Claude Code
- **THEN** the skill SHALL be invoked via the `.claude/commands/doc/parse.md` routing file

#### Scenario: Cursor command
- **WHEN** user types `/doc-parse` in Cursor
- **THEN** the skill SHALL be invoked via the `.cursor/commands/doc/doc-parse.md` routing file

#### Scenario: Codex command
- **WHEN** user types `/doc-parse` in Codex
- **THEN** the skill SHALL be invoked via the `.codex/commands/doc/doc-parse.md` routing file

#### Scenario: Direct skill invocation
- **WHEN** no platform command is available
- **THEN** the skill SHALL still be invocable via the native Skill tool with sub-skill names like `doc-fetch`, `doc-list`, `doc-parse`, `doc-help`

### Requirement: Help command
The skill SHALL provide a `/doc:help` command that displays usage instructions via the `doc-help` sub-skill.

#### Scenario: Display help
- **WHEN** user types `/doc:help`
- **THEN** the skill SHALL display supported document formats, output modes, example usage, and output file paths
