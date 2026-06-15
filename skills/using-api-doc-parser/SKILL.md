---
name: using-api-doc-parser
description: Meta-instruction entry point that teaches the Agent how to discover and invoke doc-fetch, doc-list, doc-parse, and doc-help sub-skills via the Skill tool. Injected at SessionStart by the api-doc-parser plugin hook. Use when the user mentions "parse API docs", "extract endpoints", "Swagger", "OpenAPI", or references an API documentation URL/file.
---

# Using API Doc Parser

You are an agent equipped with the `api-doc-parser` skill suite. This skill is injected at session start via the api-doc-parser plugin's SessionStart hook. It teaches you how to discover, chain, and invoke the individual `doc-*` sub-skills using the `Skill` tool to parse OpenAPI/Swagger API documentation.

## When to Engage

Invoke this skill's pipeline whenever the user asks to:

- "parse API docs" / "parse the API documentation"
- "extract endpoints from Swagger" / "list API modules"
- "find API endpoints by module" / "show me the 飞行计划 API"
- References a URL or file path that looks like an OpenAPI/Swagger document
- "what endpoints are in this API doc?"
- "generate API docs for module X"

## Sub-skill Architecture

The pipeline is split into four independent sub-skills, each covering one phase. **Invoke each via the `Skill` tool** using the skill name shown below:

| Sub-skill | Phase | Purpose | Trigger |
|-----------|-------|---------|---------|
| `doc-fetch` | Phase 1 | Source input - fetch URL, validate local file, write state | User provides a URL or file path |
| `doc-list` | Phase 2 | Module listing - extract tags, display table, accept selection | After fetch succeeds; or user says "list modules" |
| `doc-parse` | Phase 3-5 | Endpoint extraction + output generation | After module selection; or user provides tag + source directly |
| `doc-help` | Help | Display commands, formats, examples | User asks "how do I use this" or types "/doc:help" |

**Discovering sub-skills:** Use the `Skill` tool with the sub-skill name — e.g., `Skill(skill: "doc-fetch")`, `Skill(skill: "doc-list")`, `Skill(skill: "doc-parse")`, `Skill(skill: "doc-help")`. Each sub-skill is a standalone instruction set that can be invoked independently or chained via shared state.

## Pipeline Flow

```
User input (URL / file / "parse API docs")
         │
         ▼
   ┌──────────────┐
   │  doc-fetch    │  ← Detect input type (URL vs .json vs .md/.txt)
   │  Phase 1      │     Fetch/validate, write state.json
   └──────┬───────┘
          │ sourcePath, sourceType written to state
          ▼
   ┌──────────────┐
   │  doc-list     │  ← Extract tags via jq, display numbered table
   │  Phase 2      │     Accept index/keyword/mixed/all selection
   └──────┬───────┘
          │ selectedTags written to state
          ▼
   ┌──────────────┐
   │  doc-parse    │  ← Filter paths by tag, extract endpoint details
   │  Phase 3-5    │     Generate Markdown + JSON, Output Mode A/B
   └──────────────┘
          │
          ▼
      Output: Markdown in conversation OR .md/.json files on disk
```

## Cross-phase State

All sub-skills share state via a JSON file. The state file is located at:

- **Linux/macOS:** `/tmp/api-doc-parser/state.json`
- **Windows (Git Bash):** `/tmp/api-doc-parser/state.json`
- **Windows (cmd/PowerShell):** `%TEMP%/api-doc-parser/state.json`
- **Fallback:** `<project-root>/.api-doc-parser/state.json`

State schema:
```json
{
  "sourcePath": "/tmp/api-doc.json",
  "sourceType": "url",
  "sourceUrl": "https://petstore3.swagger.io/api/v3/openapi.json",
  "openapiVersion": "3.0.3",
  "fetchedAt": "2026-06-15T10:30:00Z",
  "selectedTags": ["pet", "store"],
  "outputMode": "A"
}
```

Each sub-skill reads from and writes to this state file. If the state file does not exist or is invalid, prompt the user rather than erroring. A missing or stale state file means the pipeline needs to start from an earlier phase.

## Invocation Strategy

1. **Full pipeline (user gives URL/file):** Invoke `doc-fetch`, then `doc-list`, then `doc-parse` sequentially, passing state through the state file.
2. **Direct parse (user gives keyword + known source):** If the user says "parse the 飞行计划 module", and a source is already known (state file exists), skip directly to `doc-parse` with the keyword.
3. **Help request:** Invoke `doc-help` and display its content.
4. **Resume partial pipeline:** If state.json exists with `sourcePath` but no `selectedTags`, start from `doc-list`. If `selectedTags` exists, start from `doc-parse`.

## Dependency Requirements

All sub-skills verify runtime dependencies before execution:

- `jq` >= 1.6 (all sub-skills)
- `curl` >= 7.0 (doc-fetch only)

If dependencies are missing, report which tool is needed and suggest installation.

## Context Overflow Rules

These rules apply across all sub-skills:

1. **Never read raw OpenAPI JSON into Agent context.** Always use jq pipelines in Bash.
2. **jq for all JSON filtering.** Tags, paths, endpoint details -- everything extracted via jq before entering context.
3. **Large module protection.** Modules with >30 endpoints require confirmation before full extraction.
4. **Local file size check.** Files >256KB must use jq, never Read.
5. **.md/.txt pagination.** Use Read with offset/limit, max 2000 lines per read.

## Example Interaction

```
User: "Parse the API docs at https://example.com/v3/api-docs"

Agent:
  1. Invokes doc-fetch → downloads, validates, writes state.json
  2. Invokes doc-list → displays module table, asks for selection
  → User selects "1,3"
  3. Invokes doc-parse → extracts endpoints, asks output mode
  → User selects "B"
  → Saves .md and .json files, displays summary table
```
