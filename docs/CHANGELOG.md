# Changelog

## [2.0.0] - 2026-06-15

### Added
- **Sub-skill architecture:** Split monolithic SKILL.md into 5 independent sub-skills (using-api-doc-parser, doc-fetch, doc-list, doc-parse, doc-help)
- **Multi-platform command routing:** Slash commands for 9 AI coding assistants (Claude Code, Cursor, Codex, Gemini, Kimi, Qoder, Trae, OpenCode, GitHub Copilot)
- **Plugin packaging:** Claude Code Plugin, Cursor Plugin, and Codex Plugin manifests
- **NPM distribution:** `npm install -g api-doc-parser-skill` with postinstall auto-registration
- **SessionStart hook:** Auto-injects using-api-doc-parser meta-instructions on session start
- **Cross-phase state:** Shared state file enables fetch->list->parse pipeline with independent sub-skill calls
- **Installation documentation:** Three installation methods with troubleshooting
- **Usage guide:** Complete command reference with 4+ scenario examples
- **Platform-specific commands:** `.toml` (Gemini), `.prompt.md` (GitHub Copilot), `.md` (all others)

### Changed
- **SKILL.md:** Preserved as backward-compatible entry point with sub-skill navigation added
- **metadata.json:** Version bumped to 2.0.0, description expanded
- **README.md:** Updated to reflect v2 architecture

### Removed
- **Openspec skills:** Removed bundled openspec sub-skills (now installed via openspec plugin)

## [1.0.0] - 2026-06-15

### Added
- Initial release
- 5-phase API doc parsing pipeline (Source Input -> Module Listing -> Endpoint Extraction -> Output Generation -> Output Mode)
- URL and local file input support
- jq-based context overflow protection
- Dual format output (Markdown + JSON)
- Fuzzy module selection (index, keyword, mixed)
- Large module warning (>30 endpoints)
- Error recovery table
