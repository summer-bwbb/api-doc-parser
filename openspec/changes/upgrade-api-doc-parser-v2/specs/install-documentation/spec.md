# install-documentation

安装和使用文档，覆盖三种安装方式和完整命令参考。

## ADDED Requirements

### Requirement: INSTALL documentation
The skill SHALL provide a `docs/INSTALL.md` covering all installation methods.

#### Scenario: Plugin install instructions
- **WHEN** user reads INSTALL.md for plugin installation
- **THEN** it SHALL contain: prerequisites, `claude plugins install` command, verification step, update command, uninstall command

#### Scenario: NPM install instructions
- **WHEN** user reads INSTALL.md for NPM installation
- **THEN** it SHALL contain: `npm install -g` command, verification, update, and uninstall steps

#### Scenario: Manual install instructions
- **WHEN** user reads INSTALL.md for manual installation
- **THEN** it SHALL contain: git clone steps, file copy commands for global use, file copy commands for project-level use, and settings.json reference method

#### Scenario: Troubleshooting section
- **WHEN** user encounters installation issues
- **THEN** INSTALL.md SHALL contain common troubleshooting entries (jq not found, skills not loading, etc.)

### Requirement: USAGE documentation
The skill SHALL provide a `docs/USAGE.md` with complete command reference and scenario examples.

#### Scenario: Quick start guide
- **WHEN** new user reads USAGE.md
- **THEN** it SHALL present a 3-step quick start: /doc:fetch → /doc:list → /doc:parse

#### Scenario: Command reference
- **WHEN** user looks up a specific command
- **THEN** USAGE.md SHALL document all commands (/doc:fetch, /doc:list, /doc:parse, /doc:help) with parameters, options, and output

#### Scenario: Scenario examples
- **WHEN** user wants to learn by example
- **THEN** USAGE.md SHALL provide at least 4 scenario examples: remote URL parsing, local file parsing, quick module browsing, and CI/CD batch export

#### Scenario: FAQ section
- **WHEN** user has common questions
- **THEN** USAGE.md SHALL answer them in a FAQ format

### Requirement: CHANGELOG documentation
The skill SHALL provide a `docs/CHANGELOG.md` tracking version history.

#### Scenario: Version history
- **WHEN** user wants to know what changed between versions
- **THEN** CHANGELOG.md SHALL list changes per version with date and categorized entries
