#!/usr/bin/env node

const { execFileSync } = require('child_process');
const path = require('path');

const repoRoot = path.resolve(__dirname, '..');
const python = path.join(repoRoot, 'backend', '.venv', 'bin', 'python');
const impl = path.join(__dirname, 'generate_study_doc_impl.py');

execFileSync(python, [impl], {
  cwd: repoRoot,
  stdio: 'inherit',
});
