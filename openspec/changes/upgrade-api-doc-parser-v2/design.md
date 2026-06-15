## Context

The api-doc-parser started as a single monolithic `SKILL.md` implementing a 5-phase pipeline to parse OpenAPI/Swagger docs. It was designed to be triggered via natural language ("Parse API docs from...") or through an AI agent's `Read` tool.

Two reference architectures exist in the ecosystem:
1. **openspec** — multi-skill design with sub-skills per lifecycle phase (explore/propose/apply/verify/archive/sync), cross-platform command routing under a unified prefix (`/opsx:`), and a standalone project that gets copied into consumer repos.
2. **superpowers** — a Claude Code plugin distributable via `claude plugins install`, with SessionStart hooks that auto-inject a `using-superpowers` meta-skill, 14 sub-skills under `skills/`, and platform-specific plugin manifests (`.claude-plugin/`, `.cursor-plugin/`, `.codex-plugin/`).

The current v1 lacks: sub-skill decomposition, slash command routing, plugin/NPM packaging, install documentation, and global-vs-project installation modes. Each of these patterns has been validated by openspec and superpowers — the goal is to uplift api-doc-parser to the same standard.

## Goals / Non-Goals

**Goals:**
- Split `SKILL.md` into 5 independent sub-skills (`using-api-doc-parser`, `doc-fetch`, `doc-list`, `doc-parse`, `doc-help`) that can be invoked individually via slash commands or chained together
- Support 9 platforms with command routing: `.claude/`, `.cursor/`, `.codex/`, `.gemini/`, `.kimi/`, `.qoder/`, `.trae/`, `.opencode/`, `.github/`
- Enable 3 installation methods: `claude plugins install`, `npm install -g`, and manual file copy (both global and project-level)
- Add SessionStart hook injection of the `using-api-doc-parser` meta-skill
- Provide shared state persistence (`/tmp/api-doc-parser/state.json`) so `fetch → list → parse` can be called independently
- Preserve backward compatibility: the root `SKILL.md` remains as a natural-language entry point
- Ship `docs/INSTALL.md`, `docs/USAGE.md`, and `docs/CHANGELOG.md`

**Non-Goals:**
- No changes to the core jq extraction logic — Phase 3-5 algorithms remain identical to v1
- No new OpenAPI features (e.g., `$ref` expansion is still v1-variety: reference name only)
- No server, no runtime dependency beyond `jq` and `curl`
- Not rewriting the existing openspec skills in `.claude/skills/openspec-*/` — those should be removed if they are dupes of an openspec plugin install

## Decisions

### 1. Skills live in root `skills/`, platforms copy/symlink from there

**Decision:** All 5 sub-skills live in `skills/<name>/SKILL.md` at the repo root. Each platform directory (`.claude/skills/`, `.cursor/skills/`, etc.) contains a thin proxy SKILL.md that references the root skill via `@../../skills/<name>/SKILL.md` or inline redirect content. Command routing files (`.claude/commands/doc/parse.md` etc.) point to their respective platform skill path.

**Rationale:** Single source of truth. openspec duplicates the full SKILL.md into every platform — that works but creates maintenance burden. superpowers keeps skills in `skills/` and lets the plugin manifest declare the path. We adopt superpowers' approach: `skills/` as canonical, platform dirs as thin proxies.

**Alternatives considered:**
- *openspec approach (full copy per platform)*: Simpler to understand but 9 platforms × 5 skills = 45 copies to maintain
- *Symlink-only approach*: Not portable to Windows without developer mode

### 2. Platform directory structure mirrors openspec's layout

**Decision:** Follow openspec's exact directory naming conventions:

```
.claude/skills/<skill-name>/SKILL.md     .claude/commands/doc/<cmd>.md
.cursor/skills/<skill-name>/SKILL.md     .cursor/commands/doc/<cmd>.md
.codex/skills/<skill-name>/SKILL.md      .codex/commands/doc/<cmd>.md
.gemini/skills/<skill-name>/SKILL.md     .gemini/commands/doc/<cmd>.toml
.kimi/skills/<skill-name>/SKILL.md       (no commands dir for kimi)
.qoder/skills/<skill-name>/SKILL.md      .qoder/commands/doc/<cmd>.md
.trae/skills/<skill-name>/SKILL.md       (no commands dir for trae)
.opencode/skills/<skill-name>/SKILL.md   .opencode/commands/<cmd>.md
.github/skills/<skill-name>/SKILL.md     .github/prompts/<cmd>.prompt.md
```

**Rationale:** Tested by openspec across all these platforms. Deviating from known-working patterns risks silent breakage on less-documented platforms.

### 3. Three-tier installation model

**Decision:**

| Tier | Install method | Scope | Best for |
|------|---------------|-------|----------|
| Plugin | `claude plugins install api-doc-parser` | Global | Individual devs |
| NPM | `npm install -g api-doc-parser-skill` | Global | Cross-agent users |
| Manual | `git clone` + copy files | Global or Project | Teams, CI/CD, air-gapped |

**Rationale:** This mirrors how superpowers is consumed (plugin) while adding the project-level manual copy path that openspec uses. The NPM path provides a universal install mechanism that doesn't depend on any specific agent's plugin marketplace.

**Key detail:** For project-level manual install, the project's `.claude/settings.json` can declare `"requiredSkills": ["api-doc-parser"]` as a soft dependency — each developer either installs globally (plugin/NPM) or the project ships a copy in `.claude/skills/`.

### 4. Cross-phase state via temp file, not openspec CLI

**Decision:** Use a JSON state file at `/tmp/api-doc-parser/state.json` rather than building a CLI tool like openspec's `openspec` binary.

**Rationale:** The state is trivial (`{sourcePath, selectedTags, openapiVersion}`). A CLI binary adds build/install complexity disproportionate to the problem. The state file approach is zero-dependency and transparent — users can inspect it with `cat`.

**State file schema:**
```json
{
  "sourcePath": "/tmp/api-doc.json",
  "sourceType": "url",
  "sourceUrl": "https://petstore3.swagger.io/api/v3/openapi.json",
  "openapiVersion": "3.0.3",
  "fetchedAt": "2026-06-15T10:30:00Z",
  "selectedTags": ["pet", "store"]
}
```

### 5. SessionStart hook — minimal meta-skill injection

**Decision:** `hooks/hooks.json` fires on `SessionStart` with matchers `startup|clear|compact`, running a command that injects `skills/using-api-doc-parser/SKILL.md` content. This is identical to superpowers' mechanism.

**The `using-api-doc-parser` skill content:** Approximately 50-80 lines. It teaches the agent:
1. What the api-doc-parser does
2. How to discover sub-skills via the Skill tool
3. Which natural-language triggers to watch for ("parse API docs", "extract endpoints", "Swagger", "OpenAPI")
4. How to chain `doc-fetch → doc-list → doc-parse`

**Rationale:** Following superpowers' exact pattern reduces risk — that mechanism is battle-tested.

### 6. Plugin manifests follow superpowers JSON schema

**Decision:** `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, and `.codex-plugin/plugin.json` use the JSON schema from superpowers' manifests. Key fields: `name`, `version`, `description`, `author`, `license`, `keywords`, `skills` (path to skills dir), `commands` (path to commands dir).

**Rationale:** These schemas are de-facto standards established by the superpowers plugin. Matching the format ensures compatibility.

### 7. NPM postinstall script does best-effort registration

**Decision:** `scripts/postinstall.js` detects which AI coding assistants are installed (by checking known config directories: `~/.claude/`, `~/.cursor/`, `~/.codex/`) and registers the skills by copying/linking into those directories. `scripts/preuninstall.js` reverses this.

**Rationale:** NPM is the universal package manager. Not every user has Claude Code's plugin system, but nearly every developer has NPM. The postinstall script makes `npm install -g` work equivalently to `claude plugins install`.

## Risks / Trade-offs

- **[Risk] 9 platforms × 5 skills = maintenance burden for command routing files** → Each platform command is a ~10-line file; total ≈ 50 files. Acceptable given the value of multi-platform support. The canonical skill content lives once in `skills/`.
- **[Risk] State file in /tmp may be cleaned on reboot** → Low impact: losing state just means re-running `doc:fetch`. The file is a convenience, not a requirement.
- **[Risk] NPM postinstall may conflict with Plugin install if both are used** → postinstall checks for existing plugin registration first; skips if already registered. Documentation advises picking one install method.
- **[Risk] Windows temp directory path differs from /tmp** → Use `$TMPDIR` or `$TEMP` env var; fall back to `/tmp` on Unix, `%TEMP%` on Windows.
- **[Risk] Removing .claude/skills/openspec-*/ may break existing openspec usage in this repo** → Those are openspec plugin files that should come from the openspec plugin install, not bundled inside api-doc-parser. If the user needs openspec, they should install it separately.

## Migration Plan

1. **Pre-upgrade**: The repo currently has openspec skills in `.claude/skills/openspec-*/`. These should NOT be part of api-doc-parser. Clean them up.
2. **Upgrade**: Create all new directories and files. Modify `SKILL.md` to add a forward reference to sub-skills. Update `metadata.json` version to 2.0.0.
3. **Verification**: Run `/doc:help` to confirm all commands route correctly. Test with Petstore API: `/doc:fetch` → `/doc:list` → `/doc:parse`.
4. **Rollback**: The original `SKILL.md` is preserved. All new files are additive (except openspec skill removals). Rollback means deleting new dirs and reverting `SKILL.md` and `metadata.json` changes.

## Open Questions

1. **NPM包名**: `api-doc-parser-skill` or `@summer/api-doc-parser`? (Resolved during implementation — use `api-doc-parser-skill`)
2. **是否需要 git tag 触发 GitHub Release?** (Out of scope for initial v2, can add later)
3. **`.kimi/` 和 `.trae/` 平台是否需要 commands 目录?** (Based on openspec precedent: kimi and trae only have skills, no commands. Follow that pattern.)
