---
name: doc-parse
description: Phase 3-5 of api-doc-parser — extract endpoint details from OpenAPI/Swagger by selected tag(s), generate Markdown and JSON output, and deliver via display mode (A) or file save mode (B). Reads selectedTags from shared state file.
---

# doc-parse — Phase 3-5: Endpoint Extraction and Output

Extract full endpoint details for selected API modules and generate dual-format output. This is the third (and final operational) phase of the `api-doc-parser` pipeline. Reads `sourcePath` and `selectedTags` from the shared state file.

## Pre-flight: Dependency Check

```bash
# Check jq >= 1.6
jq --version 2>/dev/null || { echo "ERROR: jq is not installed. Please install jq >= 1.6."; exit 1; }
```

## State File

Location (platform-appropriate):
- **Linux/macOS:** `/tmp/api-doc-parser/state.json`
- **Windows:** `/tmp/api-doc-parser/state.json` (Git Bash) or `%TEMP%\api-doc-parser\state.json`
- **Fallback:** `<project-root>/.api-doc-parser/state.json`

### Read Existing State

```bash
jq -r '.sourcePath' /tmp/api-doc-parser/state.json 2>/dev/null || echo ""
jq -r '.selectedTags[]' /tmp/api-doc-parser/state.json 2>/dev/null || echo ""
```

### Handle Missing State

- If `sourcePath` is missing: "No source document registered. Please run doc-fetch first."
- If `selectedTags` is missing or empty: "No modules selected. Please run doc-list first."
- If the user provides a keyword directly (e.g., "parse the 飞行计划 module"): attempt to match the keyword against available tags. If a unique match is found, use it as `selectedTags` and continue. If ambiguous, prompt for clarification.

### Direct Parse (Bypass doc-list)

If the user provides a tag keyword with their parse request, and `sourcePath` exists in state, you can bypass `doc-list`:

1. Extract all tags from the source: `jq -r '.tags[]?.name' <source-file>`
2. Match the user's keyword using the same fuzzy matching rules from `doc-list`.
3. If a single unambiguous match: set `selectedTags` and proceed.
4. If multiple matches or no match: fall back to `doc-list` for interactive selection.

---

## Phase 3: Endpoint Extraction

For each selected tag name, extract endpoints using jq. **Never read raw JSON into context.**

### Step 1: Filter paths by tag

```bash
jq --arg tag "$TAG_NAME" '
  .paths | to_entries | map(
    select(.value | to_entries | .[].value.tags? // [] | contains([$tag]))
  ) | from_entries
' <source-file>
```

### Step 2: Extract endpoint details (single jq query)

This query runs entirely in shell -- only the structured result enters Agent context:

```bash
jq --arg tag "$TAG_NAME" -r '
  .paths | to_entries | map(
    select(.value | to_entries | .[].value.tags? // [] | contains([$tag]))
  ) | .[] | .key as $path |
  .value | to_entries[] |
  "===ENDPOINT===",
  "path:\($path)",
  "method:\(.key)",
  "summary:\(.value.summary // "(no summary)")",
  "description:\(.value.description // "(no description)")",
  "operationId:\(.value.operationId // "(no operationId)")",
  "parameters:\(.value.parameters // [] | tojson)",
  "requestBody:\(.value.requestBody // {} | tojson)",
  "responses:\(.value.responses // {} | tojson)"
' <source-file>
```

### Step 3: Parse the jq output

The `===ENDPOINT===` delimiter separates endpoints. For each endpoint block:

**Parameters** — parse the JSON array, extract:
- `name` — parameter name
- `in` — location (query, path, header, cookie)
- `description` — human-readable description
- `required` — boolean
- `schema.type` — data type
- `schema.default` — default value if present

**Request body** — if present and non-empty:
- `required` — boolean
- For each content type: `schema.$ref` — record the reference name only

**Responses** — for each status code:
- `description` — human-readable description
- For each content type: `schema.$ref` — record the reference name only

### $ref Handling (v1)

Only record the reference name (the last segment after `/`). Do NOT expand into `components/schemas`.

Display as: `→ ResultDTOOdmTaskListResponse`

The user can look up the full schema in Swagger UI.

### Empty Module Handling

If the filtered paths object is empty after jq filtering:

```
No endpoints found for module "<tag name>".
```

Continue processing remaining selected modules. Do not halt the entire pipeline.

### Large Module Protection

If a selected module has >30 endpoints (already warned in Phase 2, but re-check here):

1. Display summary (method + path + summary only) first.
2. Warn about context consumption.
3. Wait for explicit confirmation before full extraction.

---

## Phase 4: Output Generation

### Format A: Markdown (human-readable)

For each module, generate the following Markdown structure:

```markdown
# <Module Name>

> <Module Description>

**Endpoints:** <count>

---

## <METHOD> <PATH> — <Summary>

**Description:** <Description>

**Operation ID:** `<operationId>`

### Request Parameters

| Name | In | Type | Required | Default | Description |
|------|----|------|----------|---------|-------------|
| userId | query | string | Yes | — | User unique identifier |
| page | query | integer | No | 1 | Page number |

### Request Body

| Content-Type | Required | Schema |
|-------------|----------|--------|
| application/json | Yes | → ResultDTOOdmTaskListResponse |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | OK | → ResultDTOOdmTaskListResponse |
| 400 | Bad Request | — |
| 500 | Internal Server Error | — |

---
```

**Formatting rules:**
- Separator line `---` between endpoints
- Parameters table: skip if empty, show "None" row
- Request body section: skip if no request body
- Schema references: show as `→ RefName` (arrow + last segment of $ref)
- Group endpoints by HTTP method: GET first, then POST, PUT, DELETE, PATCH

### Format B: Structured JSON

For each module, generate the following JSON structure:

```json
{
  "meta": {
    "sourceUrl": "<original URL or file path>",
    "generatedAt": "<ISO 8601 timestamp>",
    "openapiVersion": "<3.1.0 or 2.0>"
  },
  "module": {
    "name": "<tag name>",
    "description": "<tag description>"
  },
  "endpointCount": 12,
  "endpoints": [
    {
      "path": "/api/flights",
      "method": "GET",
      "summary": "Get flight list",
      "description": "Return paginated flight list",
      "operationId": "getFlights",
      "parameters": [
        {
          "name": "page",
          "in": "query",
          "type": "integer",
          "required": false,
          "default": 1,
          "description": "Page number"
        }
      ],
      "requestBody": null,
      "responses": [
        {
          "status": "200",
          "description": "OK",
          "schemaRef": "ResultDTOOdmTaskListResponse"
        },
        {
          "status": "500",
          "description": "Internal Server Error",
          "schemaRef": null
        }
      ]
    }
  ]
}
```

**JSON rules:**
- `null` for absent fields (not omitted)
- `schemaRef` is the last segment of the `$ref`, or `null` if no schema reference
- `parameters` is `[]` (empty array) when none, not `null`
- Generate timestamp using: `date -u +"%Y-%m-%dT%H:%M:%SZ"`
- Detect OpenAPI version from document: `jq -r '.openapi // .swagger' <source-file>`

### Multiple Modules

Each selected module generates its own Markdown section and its own JSON object/file. When saving to files, use the module name as filename:

```
api-doc-parser/.output/
├── 飞行计划.md
├── 飞行计划.json
├── 飞行监控.md
└── 飞行监控.json
```

**Filename sanitization:** Replace `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|` with `_`.

---

## Phase 5: Output Mode

The output mode can be:
- Persisted in state.json (`outputMode`: "A" or "B") -- if present, use it as default but allow override.
- Overridden via flags: `-a` / `--display` (Mode A) or `-b` / `--save` (Mode B).
- Prompted if neither is set (first run).

### First-run prompt

If `outputMode` is not set in state.json:

```
Output mode:
  A — Display directly in conversation (no files written)
  B — Save Markdown + JSON files to api-doc-parser/.output/

Which mode? (A/B)
```

After user selection, persist in state.json:
```bash
jq '. + {outputMode: "A"}' /tmp/api-doc-parser/state.json > /tmp/api-doc-parser/state.json.tmp && mv /tmp/api-doc-parser/state.json.tmp /tmp/api-doc-parser/state.json
```

### Mode A: Direct Display

Output the Markdown directly into the conversation. Display a summary after the full output:

```
## Parse Complete

- **Source:** <URL or file path>
- **Modules parsed:** <count>
- **Total endpoints:** <count>
- **Format:** Markdown (shown above)

To save for later reference, re-run with output mode B.
```

No files are written to disk.

### Mode B: File Persistence

1. Create `.output/` directory if needed:
   ```bash
   mkdir -p api-doc-parser/.output/
   ```

2. Write Markdown files:
   Use the Write tool to save `api-doc-parser/.output/<module>.md` for each module.

3. Write JSON files:
   Use the Write tool to save `api-doc-parser/.output/<module>.json` for each module.

4. Display summary in conversation:

```
## Parse Complete — Files Saved

- **Source:** <URL or file path>
- **Modules parsed:** <count>
- **Total endpoints:** <count>

### Output Files

| File | Format | Size |
|------|--------|------|
| api-doc-parser/.output/飞行计划.md | Markdown | 12.3 KB |
| api-doc-parser/.output/飞行计划.json | JSON | 8.7 KB |
| api-doc-parser/.output/飞行监控.md | Markdown | 9.1 KB |
| api-doc-parser/.output/飞行监控.json | JSON | 6.2 KB |
```

---

## Error Recovery

| Error | Recovery |
|-------|----------|
| No endpoints for module | Report: "No endpoints found for module [name]." Continue with remaining modules. |
| jq not available | For files ≤256KB: fall back to Read with offset/limit. For >256KB: report "jq required, please install jq >= 1.6." |
| Module name contains filesystem-unsafe chars | Sanitize: replace `\/:*?"<>\|` with `_` |
| State file missing | Prompt: "No source registered. Start with doc-fetch." |
| selectedTags empty | Prompt: "No modules selected. Run doc-list to select modules." |

---

## Context Overflow Prevention

1. **Never read raw OpenAPI JSON into Agent context.** All extraction uses jq pipelines.
2. **jq for all path filtering.** The filter query runs in shell, only filtered results enter context.
3. **Endpoint extraction uses a single jq query** per tag, delimited by `===ENDPOINT===`.
4. **Large module protection** — >30 endpoints requires confirmation before full extraction.
5. **$ref references are NOT expanded** — only the last segment of the path is recorded, keeping output compact.
6. **Optional temp file cleanup:**
   ```bash
   rm -f /tmp/api-doc.json
   ```
   This is optional — temp files are harmless and may be reused.
