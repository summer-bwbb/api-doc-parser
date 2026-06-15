# Usage Guide

## Quick Start

A complete API doc parsing session in 3 steps:

```
/doc:fetch https://petstore3.swagger.io/api/v3/openapi.json
/doc:list
/doc:parse
```

1. **Fetch** the OpenAPI/Swagger document from a URL or local file
2. **List** the available modules (tags) and select the ones you want
3. **Parse** the selected modules into Markdown + JSON output

---

## Command Reference

### `/doc:fetch <URL | file>`

Fetch and validate an OpenAPI 3.x or Swagger 2.0 API document.

| Argument | Description |
|----------|-------------|
| `URL` | Remote URL to an OpenAPI/Swagger JSON or YAML file |
| `file` | Local path to an OpenAPI/Swagger JSON or YAML file |

**Examples:**

```
/doc:fetch https://petstore3.swagger.io/api/v3/openapi.json
/doc:fetch ./docs/swagger.json
```

**State:** Stores the fetched document and metadata in `/tmp/api-doc-parser/state.json` for use by subsequent commands.

---

### `/doc:list [keywords | indices | all]`

List all modules (tags) found in the fetched API document, and select which to parse.

| Argument | Description |
|----------|-------------|
| (none) | Show all modules and prompt for selection |
| `keywords` | Filter modules by keyword (comma-separated, case-insensitive) |
| `indices` | Select modules by numeric index (e.g., `1,3,5`) |
| `all` | Select all modules |

**Examples:**

```
/doc:list                  # Show all, select interactively
/doc:list pet              # Filter modules containing "pet"
/doc:list flight,booking   # Filter by multiple keywords
/doc:list 1,3,5            # Select by index
/doc:list all              # Select every module
```

**State:** Updates the selected modules in the state file. `doc:parse` reads this to know what to parse.

---

### `/doc:parse [query] [-a | -b]`

Parse endpoints from the selected modules and produce output.

| Argument | Description |
|----------|-------------|
| (none) | Parse all previously selected modules |
| `query` | Filter endpoints within selected modules by keyword |
| `-a` | Append mode: add to existing output (default is overwrite) |
| `-b` | Batch mode: suppress per-endpoint detail for large exports |

**Examples:**

```
/doc:parse                  # Parse all selected modules
/doc:parse booking          # Only endpoints matching "booking"
/doc:parse -b               # Batch mode: summary only
/doc:parse flight -a        # Append flight results to existing output
```

**Output:** Markdown (`.md`) and JSON (`.json`) files written to `<project>/api-doc-parser/.output/`.

---

### `/doc:help`

Show this help information and command reference.

---

## Scenario Examples

### Scenario 1: Full Remote Pipeline

Parse the Petstore API, focusing on the "pet" module:

```
/doc:fetch https://petstore3.swagger.io/api/v3/openapi.json
```

Review the module list:

```
/doc:list
```

Select "pet" by keyword:

```
/doc:list pet
```

Parse the selected module:

```
/doc:parse
```

Output is saved to `api-doc-parser/.output/` as both `.md` and `.json`.

---

### Scenario 2: Local File Parsing

Parse a local Swagger document, selecting all modules in batch mode:

```
/doc:fetch ./docs/swagger.json
/doc:list all
/doc:parse -b
```

Batch mode (`-b`) is ideal for CI/CD or when you need a quick overview of all endpoints without per-endpoint detail.

---

### Scenario 3: Quick Module Browse

Fetch a remote API doc and browse a specific module:

```
/doc:fetch https://api.example.com/openapi.json
/doc:list flight
```

The list command shows endpoints in the "flight" module without generating output files, giving you a quick preview.

---

### Scenario 4: CI/CD Batch Export

In a scripted/CI environment, export all endpoints in batch mode:

```
/doc:fetch https://api.example.com/openapi.json
/doc:list all
/doc:parse -b
```

The output files in `api-doc-parser/.output/` can be committed, archived, or processed by downstream tools.

---

## Output Formats

### Markdown (`api-doc-parser/.output/*.md`)

Human-readable documentation with:

- Module name and endpoint count
- Per-endpoint tables: method, path, summary, parameters, request body, responses
- Selected module summary with endpoint count per module

### JSON (`api-doc-parser/.output/*.json`)

Machine-readable structured data:

```json
{
  "module": "pet",
  "endpoints": [
    {
      "method": "POST",
      "path": "/pet",
      "summary": "Add a new pet to the store",
      "parameters": [...],
      "requestBody": {...},
      "responses": {...}
    }
  ]
}
```

---

## FAQ

### What OpenAPI versions are supported?

OpenAPI 3.x (3.0, 3.1) and Swagger 2.0. Both JSON and YAML input formats are accepted.

### Can I use the skill without slash commands?

Yes. You can also invoke the skills via natural language:
- "Fetch the API docs from https://example.com/openapi.json"
- "List all modules in the API"
- "Parse the pet module"

The slash commands are convenience shortcuts that map to the same sub-skills.

### Where are the output files saved?

Output files are written to `api-doc-parser/.output/` in your project directory. The directory is created automatically if it does not exist.

### How do I resume an interrupted pipeline?

The pipeline state is stored in `/tmp/api-doc-parser/state.json`. You can resume at any step — for example, if you already ran `doc:fetch`, you can go straight to `doc:list` in a new session. The state file persists across sessions until the temp directory is cleared.

### Does the parser expand `$ref` references?

No. The parser extracts `$ref` reference names as-is (e.g., `#/components/schemas/Pet`). It does not inline the referenced schema. This keeps output concise and avoids circular reference problems.
