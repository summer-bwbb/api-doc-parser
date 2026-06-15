#!/usr/bin/env node

/**
 * preuninstall.js — api-doc-parser-skill
 *
 * Removes the copied skill files from each detected AI coding assistant's
 * skills directory. Handles errors gracefully (files may already be deleted).
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

// ----- Platform helpers -----
const isWindows = process.platform === 'win32';
const HOME = isWindows ? process.env.USERPROFILE : os.homedir();

// ----- Known assistant config directories -----
const ASSISTANTS = [
  {
    name: 'Claude Code',
    dir: path.join(HOME, '.claude', 'skills')
  },
  {
    name: 'Cursor',
    dir: path.join(HOME, '.cursor', 'skills')
  },
  {
    name: 'Codex',
    dir: path.join(HOME, '.codex', 'skills')
  }
];

// List of skill directories to remove
const SKILL_NAMES = [
  'using-api-doc-parser',
  'doc-fetch',
  'doc-list',
  'doc-parse',
  'doc-help'
];

// ----- Functions -----

/**
 * Recursively remove a directory.
 */
function removeDir(dir) {
  if (!fs.existsSync(dir)) return;

  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      removeDir(fullPath);
    } else {
      fs.unlinkSync(fullPath);
    }
  }
  fs.rmdirSync(dir);
}

// ----- Main -----

console.log('\n📦 api-doc-parser-skill v2.0.0 preuninstall\n');

let removedCount = 0;

for (const assistant of ASSISTANTS) {
  process.stdout.write(`Cleaning ${assistant.name}... `);

  if (!fs.existsSync(assistant.dir)) {
    console.log('nothing to clean (skills dir missing)');
    continue;
  }

  let assistantRemoved = 0;
  for (const skillName of SKILL_NAMES) {
    const skillDir = path.join(assistant.dir, skillName);
    try {
      if (fs.existsSync(skillDir)) {
        removeDir(skillDir);
        assistantRemoved++;
      }
    } catch (err) {
      // Graceful — files may already be deleted
      console.error(`\n  ⚠ Could not remove ${skillDir}: ${err.message}`);
    }
  }

  if (assistantRemoved > 0) {
    console.log(`removed ${assistantRemoved} skill(s)`);
    removedCount += assistantRemoved;
  } else {
    console.log('nothing to clean');
  }
}

console.log(`\nDone: ${removedCount} skill director${removedCount === 1 ? 'y' : 'ies'} removed.\n`);
