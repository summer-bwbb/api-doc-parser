# cross-phase-state

Phase 间状态传递机制，使 `doc:fetch → doc:list → doc:parse` 可以独立调用或连续调用。

## ADDED Requirements

### Requirement: Shared state file
The skill SHALL maintain a JSON state file at a well-known location for cross-phase data sharing.

#### Scenario: State file location
- **WHEN** any doc-* skill runs
- **THEN** it SHALL read/write state from `/tmp/api-doc-parser/state.json` (Unix) or the equivalent temp directory on other platforms

#### Scenario: State file initialization
- **WHEN** doc-fetch completes successfully
- **THEN** it SHALL initialize the state file with: `sourcePath`, `sourceType` (url|file), `openapiVersion`, `fetchedAt` (ISO 8601 timestamp)

#### Scenario: State file updated by doc-list
- **WHEN** doc-list resolves user module selection
- **THEN** it SHALL add `selectedTags` (array of tag names) to the state file

#### Scenario: State file consumed by doc-parse
- **WHEN** doc-parse starts
- **THEN** it SHALL read `selectedTags` and `sourcePath` from the state file to determine what to parse and from where

### Requirement: State file resilience
The skill SHALL handle missing or stale state gracefully.

#### Scenario: Missing state file
- **WHEN** doc-list or doc-parse runs without a prior doc-fetch
- **THEN** the skill SHALL prompt user to provide a source (URL or file) instead of erroring

#### Scenario: Stale state file
- **WHEN** doc-fetch is re-run for a new source
- **THEN** the skill SHALL overwrite the previous state file entirely, clearing any prior module selections

#### Scenario: State file cleanup
- **WHEN** the agent session ends
- **THEN** the state file MAY be preserved for cross-session reuse or cleaned up optionally

### Requirement: State file archival to project
After a session ends, `doc-fetch` SHALL archive the state from the temp directory to the project directory for cross-session persistence.

#### Scenario: Archival on session end
- **WHEN** the agent session ends after a successful `doc-fetch`
- **THEN** the state file SHALL be copied from `/tmp/api-doc-parser/state.json` to `<project>/.api-doc-parser/state.json`

#### Scenario: Project-level state restored to tmp
- **WHEN** `doc-list` or `doc-parse` runs and no `/tmp/api-doc-parser/state.json` exists but `<project>/.api-doc-parser/state.json` does
- **THEN** the project state SHALL be copied to `/tmp` to resume the session pipeline

### Requirement: State file reading priority
All doc-* sub-skills SHALL read state from `/tmp/api-doc-parser/state.json` first, then fall back to `<project>/.api-doc-parser/state.json`.

#### Scenario: Tmp priority
- **WHEN** both `/tmp/api-doc-parser/state.json` and `<project>/.api-doc-parser/state.json` exist
- **THEN** `/tmp` SHALL take precedence as the fresher session-level state

### Requirement: State file schema
The state file SHALL include an `outputMode` field to persist user's output preference.

#### Scenario: Output mode stored in state
- **WHEN** user selects output mode A or B during `doc-parse`
- **THEN** the choice SHALL be saved as `outputMode` field in the state file for subsequent calls

### Requirement: State file validation
Before reading, each sub-skill SHALL validate the state file is valid JSON.

#### Scenario: Corrupt state file
- **WHEN** state.json is manually edited and becomes invalid JSON
- **THEN** the skill SHALL report "State file corrupted" and offer to re-run `doc-fetch`

### Requirement: Windows temp directory support
The state file path SHALL use the platform-appropriate temp directory.

#### Scenario: Windows TEMP path
- **WHEN** running on Windows
- **THEN** `%TEMP%/api-doc-parser/state.json` SHALL be used instead of `/tmp/api-doc-parser/state.json`

### Requirement: Stale source detection
`doc-list` and `doc-parse` SHALL detect when the source file referenced in state.json no longer exists.

#### Scenario: Deleted source file
- **WHEN** state.json references a sourcePath that has been deleted
- **THEN** the skill SHALL report "Source file not found: <path>. Please re-run /doc:fetch."
