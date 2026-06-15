# plugin-packaging

Plugin 打包与分发：支持 Claude Code Plugin、Cursor Plugin、Codex Plugin 三种插件清单，以及 NPM 包发布。

## ADDED Requirements

### Requirement: Claude Code plugin manifest
The skill SHALL provide a `.claude-plugin/plugin.json` file compliant with Claude Code plugin specification.

#### Scenario: Plugin installation via CLI
- **WHEN** user runs `claude plugins install api-doc-parser`
- **THEN** Claude Code SHALL read `.claude-plugin/plugin.json` and install the skill globally

#### Scenario: Plugin update via CLI
- **WHEN** user runs `claude plugins update api-doc-parser`
- **THEN** Claude Code SHALL check for updates using marketplace.json and update accordingly

#### Scenario: Plugin uninstall via CLI
- **WHEN** user runs `claude plugins uninstall api-doc-parser`
- **THEN** Claude Code SHALL remove the skill from the global plugins directory

### Requirement: Claude Code marketplace listing
The skill SHALL provide a `.claude-plugin/marketplace.json` file for marketplace discovery.

#### Scenario: Marketplace discovery
- **WHEN** user browses available plugins in Claude Code
- **THEN** api-doc-parser SHALL appear in the listing with its description, version, and author info

### Requirement: Cursor plugin manifest
The skill SHALL provide a `.cursor-plugin/plugin.json` file compliant with Cursor plugin specification.

#### Scenario: Cursor plugin installation
- **WHEN** user installs the plugin in Cursor
- **THEN** Cursor SHALL load skills/ and commands/ from the plugin

### Requirement: Codex plugin manifest
The skill SHALL provide a `.codex-plugin/plugin.json` file compliant with Codex plugin specification.

#### Scenario: Codex plugin installation
- **WHEN** user installs the plugin in Codex
- **THEN** Codex SHALL load skills/ and commands/ from the plugin

### Requirement: NPM package publishing
The skill SHALL provide a `package.json` and postinstall/preuninstall scripts for NPM distribution.

#### Scenario: NPM global install
- **WHEN** user runs `npm install -g api-doc-parser-skill`
- **THEN** the postinstall script SHALL register skills with all detected AI coding assistants

#### Scenario: NPM uninstall
- **WHEN** user runs `npm uninstall -g api-doc-parser-skill`
- **THEN** the preuninstall script SHALL clean up registered skills from all AI coding assistants

#### Scenario: NPM update
- **WHEN** user runs `npm update -g api-doc-parser-skill`
- **THEN** the latest version SHALL be fetched and postinstall SHALL re-register updated skills

### Requirement: Version consistency
The version number SHALL be consistent across all manifests: plugin.json files, marketplace.json, package.json, and metadata.json.

#### Scenario: Version bump
- **WHEN** a new version is released
- **THEN** all manifest files SHALL be updated to the same semver version string

### Requirement: Postinstall conflict avoidance
The postinstall script SHALL detect existing plugin registrations and skip if already registered.

#### Scenario: Plugin already installed
- **WHEN** NPM postinstall runs and a Claude Code plugin is already registered for api-doc-parser
- **THEN** postinstall SHALL skip registration and print "Plugin already registered, skipping NPM registration"

#### Scenario: Multiple assistant detection
- **WHEN** postinstall detects both Claude Code and Cursor are installed
- **THEN** it SHALL register skills to all detected assistants

### Requirement: Postinstall OS adaptation
The postinstall script SHALL provide OS-appropriate paths and commands.

#### Scenario: macOS paths
- **WHEN** running on macOS
- **THEN** postinstall SHALL use `$HOME/.claude/skills/` as the target directory

#### Scenario: Linux paths
- **WHEN** running on Linux
- **THEN** postinstall SHALL use `$HOME/.claude/skills/` as the target directory

#### Scenario: Windows paths
- **WHEN** running on Windows
- **THEN** postinstall SHALL use `%USERPROFILE%/.claude/skills/` as the target directory
