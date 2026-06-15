---
name: doc-fetch
description: Phase 1 of api-doc-parser — fetch and validate an OpenAPI/Swagger document from a URL or local file. Writes source metadata to shared state file. Use when the user provides an API documentation URL or file path to parse.
---

# doc-fetch — Phase 1: Source Input

Fetch, validate, and register an OpenAPI/Swagger API documentation source. This is the first phase of the `api-doc-parser` pipeline. After successful completion, the shared state file is written with source metadata, and the pipeline proceeds to `doc-list` (Phase 2).

## Pre-flight: Dependency Check

Before any operation, verify runtime dependencies:

```bash
# Check jq >= 1.6
jq --version 2>/dev/null || { echo "ERROR: jq is not installed. Please install jq >= 1.6."; exit 1; }

# Check curl >= 7.0
curl --version 2>/dev/null | head -1 || { echo "ERROR: curl is not installed. Please install curl >= 7.0."; exit 1; }
```

## State File

Location (platform-appropriate):
- **Linux/macOS:** `/tmp/api-doc-parser/state.json`
- **Windows:** `/tmp/api-doc-parser/state.json` (Git Bash) or `%TEMP%\api-doc-parser\state.json`
- **Fallback:** `<project-root>/.api-doc-parser/state.json`

This phase WRITES the state file. If a state file already exists from a previous session, overwrite it with fresh data.

## Detect Input Type

Ask the user for the API documentation source. If a URL or file path was already provided in the user's message, use it directly.

| Input | Detection | Action |
|-------|-----------|--------|
| URL | Starts with `http://` or `https://` | Fetch via curl to `/tmp/api-doc.json` |
| Local `.json` file | Path ends in `.json` | Use directly with jq |
| Local `.md` file | Path ends in `.md` | Read with offset/limit pagination, LLM extraction |
| Local `.txt` file | Path ends in `.txt` | Read with offset/limit pagination, LLM extraction |

---

## URL Source

### Step 1: Check connectivity

```bash
curl -s -I -o /dev/null -w "%{http_code}" "<URL>"
```

- If HTTP status is 200: proceed to Step 2.
- If non-200, timeout, or DNS resolution error: report the error and offer recovery options.

### Step 2: Fetch and save

```bash
curl -s "<URL>" -o /tmp/api-doc.json
```

Never display raw content. The file stays on disk; only metadata enters context.

### Step 3: Validate JSON

```bash
jq 'type' /tmp/api-doc.json
```

Expected output: `"object"`.

If the output is not `"object"`:
- Report: "Not a valid JSON document. Expected a JSON object but got: <type>."
- Do NOT proceed to Phase 2.

### Step 4: Detect OpenAPI version

```bash
jq -r '.openapi // .swagger // "unknown"' /tmp/api-doc.json
```

### Error Recovery: URL Source

| Error | Recovery Action |
|-------|----------------|
| HTTP status non-200 | Report: "Unable to fetch URL: `<URL>`. HTTP status: `<code>`." Offer: "Would you like to retry, or provide a local file path instead?" |
| DNS resolution failure | Report: "Unable to resolve host: `<hostname>`. If this is an internal/private URL, it may not be reachable from this environment." Offer local file fallback. |
| Connection timeout | Report: "Connection timed out for `<URL>`." Offer retry or local file fallback. |
| Invalid JSON (jq type not "object") | Report: "The fetched document is not a valid OpenAPI/Swagger JSON object." Show first 100 characters for diagnosis. Offer: "Try a different URL or provide a local file." |
| jq not available | For files ≤256KB: fall back to Read with offset/limit. For larger files: report "jq is required for files >256KB. Please install jq >= 1.6." |

---

## Local JSON File

### Step 1: Check file existence and readability

```bash
test -f "<filepath>" && test -r "<filepath>" && echo "OK" || echo "ERROR: File not found or not readable"
```

### Step 2: Check file size

```bash
wc -c < "<filepath>"
```

- If ≤ 262144 bytes (256KB): Can use Read with offset/limit if needed, but prioritize jq filtering.
- If > 256KB: **MUST use jq exclusively.** Never use Read on the file.

### Step 3: Validate JSON structure

```bash
jq 'type' "<filepath>"
```

Expected output: `"object"`.

### Step 4: Detect OpenAPI version

```bash
jq -r '.openapi // .swagger // "unknown"' "<filepath>"
```

### Step 5: Copy to temp for consistent pipeline

```bash
cp "<filepath>" /tmp/api-doc.json
```

This ensures Phase 2 (`doc-list`) and Phase 3 (`doc-parse`) use a consistent path.

### Error Recovery: Local JSON

| Error | Recovery Action |
|-------|----------------|
| File not found | Report: "File not found: `<filepath>`. Please check the path and try again." |
| File not readable | Report: "Cannot read file: `<filepath>`. Check file permissions." |
| Not valid JSON | Report: "The file is not a valid OpenAPI/Swagger JSON document." Show first 100 characters for diagnosis. |
| File >256KB and jq not available | Report: "File is too large (>256KB) and jq is not available. Please install jq >= 1.6 to process large files." |

---

## Local .md / .txt File

Non-JSON files are best-effort. Structured JSON input is always preferred.

### Process

1. Use Read with `offset` and `limit` parameters (max 2000 lines per read).
2. Never read the entire file at once if it exceeds 2000 lines.
3. Use LLM extraction to identify API endpoints, methods, parameters, and responses.
4. Copy any extracted structured data to `/tmp/api-doc.json` if possible.

### Error Recovery: .md/.txt

| Error | Recovery Action |
|-------|----------------|
| Empty file | Report: "File is empty. Please provide a new source." |
| File too large for context | Use pagination. If still impractical, suggest using a JSON-format source instead. |

---

## Write State File

After successful source acquisition, persist the state. Determine the temp directory:

```bash
# Cross-platform temp directory
if [ -n "$TMPDIR" ]; then
  STATE_DIR="$TMPDIR/api-doc-parser"
elif [ -n "$TEMP" ]; then
  STATE_DIR="$TEMP/api-doc-parser"
elif [ -d /tmp ]; then
  STATE_DIR="/tmp/api-doc-parser"
else
  STATE_DIR="$HOME/tmp/api-doc-parser"
fi
mkdir -p "$STATE_DIR"
```

Then write the state JSON to `$STATE_DIR/state.json` using the Write tool or a heredoc:

Then write the state JSON using the Write tool or a heredoc:

```json
{
  "sourcePath": "/tmp/api-doc.json",
  "sourceType": "<url|local-json|local-md|local-txt>",
  "sourceUrl": "<original URL or absolute file path>",
  "openapiVersion": "<detected version>",
  "fetchedAt": "<ISO 8601 timestamp>"
}
```

To generate the timestamp:
```bash
# Cross-platform ISO 8601 timestamp
date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || python3 -c "from datetime import datetime,timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))" 2>/dev/null || echo "unknown-timestamp"
```

### State File Example

```json
{
  "sourcePath": "/tmp/api-doc.json",
  "sourceType": "url",
  "sourceUrl": "https://petstore3.swagger.io/api/v3/openapi.json",
  "openapiVersion": "3.0.3",
  "fetchedAt": "2026-06-15T10:30:00Z"
}
```

---

## Completion

After writing the state file, report:

```
Source ready: <sourceUrl>
  - Type: <sourceType>
  - Format: OpenAPI <openapiVersion>
  - Fetched: <fetchedAt>
  - Temp file: /tmp/api-doc.json

Proceeding to module listing (doc-list)...
```

Then immediately invoke `doc-list` to continue the pipeline, passing the state file path.

## Context Overflow Prevention

- **Never read raw OpenAPI JSON into Agent context.** All extraction uses jq pipelines operating on temp files.
- **curl output goes directly to file**, never to stdout for display.
- **jq validation only checks `type`**, producing at most a few bytes of output.
- **Version detection is a single jq query**, producing at most a few bytes.
- The temp file at `/tmp/api-doc.json` is the single source of truth for all downstream phases.
