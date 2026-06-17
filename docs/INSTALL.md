# Installation Guide

Three installation methods are available — pick the one that fits your workflow.

---

## Method 1: Plugin Installation (recommended for Claude Code users)

The simplest way for Claude Code users. The plugin system handles registration automatically.

### Install

```bash
claude plugins install api-doc-parser
```

### Prerequisites

- [Claude Code](https://claude.ai/code) installed and configured

### Verify

```bash
ls ~/.claude/skills/doc-fetch
```

You should see `SKILL.md`. This confirms the skills were registered correctly.

### Update

```bash
claude plugins update api-doc-parser
```

### Uninstall

```bash
claude plugins uninstall api-doc-parser
```

---

## Method 2: NPM Installation (recommended for multi-assistant users)

If you use multiple AI coding assistants (Claude Code, Cursor, Codex), the NPM package auto-detects and configures each one.

### Install

```bash
npm install -g api-doc-parser-skill
```

### Prerequisites

- Node.js >= 16
- npm >= 8

### How postinstall works

The `postinstall` script:
1. Detects which AI coding assistants are installed by checking known config directories:
   - Claude Code: `~/.claude/skills/` (Unix) or `%USERPROFILE%\.claude\skills\` (Windows)
   - Cursor: `~/.cursor/skills/` or `%USERPROFILE%\.cursor\skills\`
   - Codex: `~/.codex/skills/` or `%USERPROFILE%\.codex\skills\`
2. For each detected assistant, copies the skills from the package into the assistant's skills directory
3. If the assistant was already configured via its plugin system, it skips with the message:
   `Plugin already registered, skipping NPM registration for <assistant>`

### Verify

```bash
ls ~/.claude/skills/doc-fetch
```

### Update

```bash
npm update -g api-doc-parser-skill
```

### Uninstall

```bash
npm uninstall -g api-doc-parser-skill
```

The `preuninstall` script will remove the copied skill files from each assistant's directory.

---

## Method 3: Manual Installation (for teams, CI/CD, air-gapped)

Use when you need full control over the installation, or in environments without internet access.

### Global manual install

```bash
git clone https://github.com/summer-bwbb/api-doc-parser.git /tmp/api-doc-parser
cp -r /tmp/api-doc-parser/skills/* ~/.claude/skills/
```

### Project-level manual install

Copy the skills directory directly into your project:

```bash
git clone https://github.com/summer-bwbb/api-doc-parser.git /tmp/api-doc-parser
cp -r /tmp/api-doc-parser/skills/* <project>/.claude/skills/
```

### Project settings reference method

Add a reference to the skill in your project's `.claude/settings.json` instead of copying files:

```json
{
  "requiredSkills": ["api-doc-parser"]
}
```

Then clone the skill repository into the global `~/.claude/skills/` directory once, and reference it from any project.

---

## Troubleshooting

### "jq not found"

The parser requires `jq` for JSON processing. Install it:

| Platform | Command |
|----------|---------|
| macOS | `brew install jq` |
| Ubuntu/Debian | `sudo apt-get install jq` |
| Windows | `winget install jqlang.jq` or [download from stedolan.github.io](https://stedolan.github.io/jq/download/) |

Minimum version: **jq >= 1.6**

### "Skills not loading"

1. Verify the skill files exist in the correct location:
   ```bash
   ls ~/.claude/skills/doc-fetch/SKILL.md
   ```
2. Check that `hooks.json` is in the project's `.claude/hooks/` directory
3. If using plugin installation, verify with `claude plugins list`
4. Restart your IDE / Claude Code session

### "Commands not found"

Slash commands may require a restart of your IDE or AI coding assistant after installation.

1. Restart the application
2. Try `/doc:help` to verify commands are registered
3. Check that the command files exist:
   ```bash
   ls .claude/commands/doc/
   ```

### "State file corrupted"

If the pipeline state file becomes corrupted, delete it and re-fetch:

```bash
rm -f /tmp/api-doc-parser/state.json
```

Then start a fresh pipeline with `/doc:fetch <URL>`.
