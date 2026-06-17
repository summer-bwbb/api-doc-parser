#!/usr/bin/env node

/**
 * preuninstall.js — api-doc-parser-skill
 *
 * Removes ONLY the files this package installed (not entire directories).
 * Skills: removes specific subdirectories (doc-fetch, doc-list, etc.)
 * Commands: removes only fetch.md, help.md, list.md, parse.md in doc/
 * Hooks: removes generated hooks.json if it contains our marker
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

// FIX: os.homedir() works reliably on all platforms
const HOME = os.homedir();

// ----- Version from package.json -----
const pkg = require('../package.json');

// ----- Per-assistant directories -----
const ASSISTANTS = [
  {
    name: 'Claude Code',
    skillsDir:   path.join(HOME, '.claude', 'skills'),
    commandsDir: path.join(HOME, '.claude', 'commands'),
    hooksDir:    path.join(HOME, '.claude', 'hooks'),
  },
  {
    name: 'Cursor',
    skillsDir:   path.join(HOME, '.cursor', 'skills'),
    commandsDir: path.join(HOME, '.cursor', 'commands'),
    hooksDir:    path.join(HOME, '.cursor', 'hooks'),
  },
  {
    name: 'Codex',
    skillsDir:   path.join(HOME, '.codex', 'skills'),
    commandsDir: path.join(HOME, '.codex', 'commands'),
    hooksDir:    path.join(HOME, '.codex', 'hooks'),
  },
];

// Skill subdirectories this package creates
const SKILL_NAMES = [
  'using-api-doc-parser',
  'doc-fetch',
  'doc-list',
  'doc-parse',
  'doc-help',
];

// Command files this package creates (inside commands/doc/)
const COMMAND_FILES = [
  'fetch.md',
  'help.md',
  'list.md',
  'parse.md',
];

// ----- Functions -----

function removeDir(dir) {
  if (!fs.existsSync(dir)) return;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      removeDir(fullPath);
    } else {
      fs.unlinkSync(fullPath);
    }
  }
  fs.rmdirSync(dir);
}

function removeFile(filePath) {
  if (fs.existsSync(filePath)) {
    try {
      fs.unlinkSync(filePath);
      return true;
    } catch (err) {
      console.error(`  ⚠ Could not remove ${filePath}: ${err.message}`);
    }
  }
  return false;
}

// ----- Main -----

console.log(`\n📦 api-doc-parser-skill v${pkg.version} preuninstall\n`);

let removedCount = 0;

for (const assistant of ASSISTANTS) {
  process.stdout.write(`[${assistant.name}] `);

  let itemsRemoved = 0;

  // 1. Remove skill directories
  if (fs.existsSync(assistant.skillsDir)) {
    for (const skillName of SKILL_NAMES) {
      const skillDir = path.join(assistant.skillsDir, skillName);
      try {
        if (fs.existsSync(skillDir)) {
          removeDir(skillDir);
          itemsRemoved++;
        }
      } catch (err) {
        console.error(`  ⚠ Could not remove ${skillDir}: ${err.message}`);
      }
    }
  }

  // 2. Remove ONLY our command files (not the entire doc/ directory)
  const docCmdDir = path.join(assistant.commandsDir, 'doc');
  if (fs.existsSync(docCmdDir)) {
    for (const cmdFile of COMMAND_FILES) {
      if (removeFile(path.join(docCmdDir, cmdFile))) {
        itemsRemoved++;
      }
    }
    // Remove doc/ dir only if it's now empty
    try {
      const remaining = fs.readdirSync(docCmdDir);
      if (remaining.length === 0) {
        fs.rmdirSync(docCmdDir);
      }
    } catch (err) {
      // Ignore — dir may have other files from other packages
    }
  }

  // 3. Remove generated hooks.json (only if it references our skill)
  const hooksFile = path.join(assistant.hooksDir, 'hooks.json');
  if (fs.existsSync(hooksFile)) {
    try {
      const content = fs.readFileSync(hooksFile, 'utf8');
      if (content.includes('using-api-doc-parser')) {
        fs.unlinkSync(hooksFile);
        itemsRemoved++;
      }
    } catch (err) {
      console.error(`  ⚠ Could not check/remove ${hooksFile}: ${err.message}`);
    }
  }

  if (itemsRemoved > 0) {
    console.log(`removed ${itemsRemoved} item(s)`);
    removedCount += itemsRemoved;
  } else {
    console.log('nothing to clean');
  }
}

console.log(`\nDone: ${removedCount} item(s) removed.\n`);
