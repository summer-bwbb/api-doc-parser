#!/usr/bin/env node

/**
 * postinstall.js — api-doc-parser-skill
 *
 * Detects installed AI coding assistants by checking known config directories,
 * copies the project's skills/ into each detected assistant's skills directory.
 * Skips assistants that are already registered via the plugin system.
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
    dir: path.join(HOME, '.claude', 'skills'),
    pluginDetected: () => {
      // Check if this install came from claude plugins
      return process.env.CLAUDE_PLUGIN_INSTALL === '1';
    }
  },
  {
    name: 'Cursor',
    dir: path.join(HOME, '.cursor', 'skills'),
    pluginDetected: () => {
      return false; // Cursor plugin detection — check for cursor plugin marker
    }
  },
  {
    name: 'Codex',
    dir: path.join(HOME, '.codex', 'skills'),
    pluginDetected: () => {
      return false;
    }
  }
];

// Source skills directory (relative to the package root)
const SKILLS_SRC = path.join(__dirname, '..', 'skills');

// ----- Functions -----

/**
 * Recursively copy a directory.
 */
function copyDir(src, dest) {
  if (!fs.existsSync(src)) return;

  fs.mkdirSync(dest, { recursive: true });

  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
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

console.log('\n📦 api-doc-parser-skill v2.0.0 postinstall\n');

if (!fs.existsSync(SKILLS_SRC)) {
  console.error('ERROR: skills/ directory not found at', SKILLS_SRC);
  process.exit(1);
}

let installedCount = 0;
let skippedCount = 0;

for (const assistant of ASSISTANTS) {
  process.stdout.write(`Checking ${assistant.name}... `);

  if (assistant.pluginDetected()) {
    console.log(`Plugin already registered, skipping NPM registration for ${assistant.name}`);
    skippedCount++;
    continue;
  }

  // Check if the config directory exists (meaning the assistant is installed)
  const configParent = path.dirname(assistant.dir);
  if (!fs.existsSync(configParent)) {
    console.log('not detected (config dir missing)');
    continue;
  }

  console.log('detected');

  // Copy skills
  try {
    copyDir(SKILLS_SRC, assistant.dir);
    console.log(`  ✓ Copied skills to ${assistant.dir}`);
    installedCount++;
  } catch (err) {
    console.error(`  ✗ Failed to copy to ${assistant.dir}: ${err.message}`);
  }
}

console.log(`\nDone: ${installedCount} assistant(s) configured, ${skippedCount} skipped (plugin-managed).\n`);
