#!/usr/bin/env node

/**
 * postinstall.js — api-doc-parser-skill
 *
 * Global install:
 *   1. Copies skills/ (including parse.py, lib/) to ~/.claude/skills/
 *   2. Copies commands/ to ~/.claude/commands/
 *   3. Generates and copies hooks with correct absolute paths
 * Per-assistant: copies to each detected assistant's config dir.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

// FIX: os.homedir() works reliably on all platforms (Windows, macOS, Linux)
const HOME = os.homedir();

// ----- Version from package.json -----
const pkg = require('../package.json');

// ----- Source directories -----
const PKG_ROOT = path.join(__dirname, '..');
const SKILLS_SRC = path.join(PKG_ROOT, 'skills');

// ----- Per-platform commands source -----
const COMMANDS_MAP = {
  'Claude Code': path.join(PKG_ROOT, '.claude', 'commands'),
  'Cursor':      path.join(PKG_ROOT, '.cursor', 'commands'),
  'Codex':       path.join(PKG_ROOT, '.codex', 'commands'),
};

// ----- Per-platform skills/commands destinations -----
const ASSISTANTS = [
  {
    name: 'Claude Code',
    skillsDir:   path.join(HOME, '.claude', 'skills'),
    commandsDir: path.join(HOME, '.claude', 'commands'),
    hooksDir:    path.join(HOME, '.claude', 'hooks'),
    pluginDetected: () => process.env.CLAUDE_PLUGIN_INSTALL === '1',
  },
  {
    name: 'Cursor',
    skillsDir:   path.join(HOME, '.cursor', 'skills'),
    commandsDir: path.join(HOME, '.cursor', 'commands'),
    hooksDir:    path.join(HOME, '.cursor', 'hooks'),
    pluginDetected: () => false,
  },
  {
    name: 'Codex',
    skillsDir:   path.join(HOME, '.codex', 'skills'),
    commandsDir: path.join(HOME, '.codex', 'commands'),
    hooksDir:    path.join(HOME, '.codex', 'hooks'),
    pluginDetected: () => false,
  },
];

// ----- Functions -----

function copyDir(src, dest) {
  if (!fs.existsSync(src)) return;
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

/**
 * Generate hooks JSON with platform-appropriate absolute paths.
 * Uses Node.js (cross-platform) instead of `cat` + `$HOME`.
 */
function generateHooksContent(skillsDir) {
  // Use node -e for cross-platform compatibility (works on Windows, macOS, Linux)
  const skillPath = path.join(skillsDir, 'using-api-doc-parser', 'SKILL.md').replace(/\\/g, '/');
  return JSON.stringify({
    hooks: {
      SessionStart: [
        {
          matcher: 'startup|clear|compact',
          command: `node -e "process.stdout.write(require('fs').readFileSync('${skillPath}','utf8'))"`,
        },
      ],
    },
  }, null, 2);
}

// ----- Main -----

console.log(`\n📦 api-doc-parser-skill v${pkg.version} postinstall\n`);

if (!fs.existsSync(SKILLS_SRC)) {
  console.error('ERROR: skills/ directory not found at', SKILLS_SRC);
  process.exit(1);
}

let installedCount = 0;
let skippedCount = 0;

for (const assistant of ASSISTANTS) {
  process.stdout.write(`[${assistant.name}] `);

  if (assistant.pluginDetected()) {
    console.log('plugin already registered, skipping');
    skippedCount++;
    continue;
  }

  const configParent = path.dirname(assistant.skillsDir);
  if (!fs.existsSync(configParent)) {
    console.log('not detected (config dir missing)');
    continue;
  }

  console.log('detected');

  // 1. Copy skills (includes parse.py + lib/ automatically)
  try {
    copyDir(SKILLS_SRC, assistant.skillsDir);
    console.log(`  ✓ Skills   → ${assistant.skillsDir}`);
  } catch (err) {
    console.error(`  ✗ Skills copy failed: ${err.message}`);
  }

  // 2. Copy commands
  const cmdsSrc = COMMANDS_MAP[assistant.name];
  if (cmdsSrc && fs.existsSync(cmdsSrc)) {
    try {
      copyDir(cmdsSrc, assistant.commandsDir);
      console.log(`  ✓ Commands → ${assistant.commandsDir}`);
    } catch (err) {
      console.error(`  ✗ Commands copy failed: ${err.message}`);
    }
  }

  // 3. Generate and copy hooks with correct absolute paths
  try {
    fs.mkdirSync(assistant.hooksDir, { recursive: true });
    const hooksContent = generateHooksContent(assistant.skillsDir);
    fs.writeFileSync(path.join(assistant.hooksDir, 'hooks.json'), hooksContent);
    console.log(`  ✓ Hooks    → ${path.join(assistant.hooksDir, 'hooks.json')}`);
  } catch (err) {
    console.error(`  ✗ Hooks generation failed: ${err.message}`);
  }

  installedCount++;
}

console.log(`\nDone: ${installedCount} assistant(s) configured, ${skippedCount} skipped.\n`);
