#!/usr/bin/env node
// scripts/check_commit_prefix.mjs — Commit prefix lint (D5 fix — Story 9.7 A36 wire).
//
// Rejects commits whose subject starts with `@` (the PowerShell here-string
// artifact where `@'...'@` in bash context produces `@ @ Story ...` titles).
// Mirrors the [STACK BUMP] bypass pattern from scripts/check_stack_pin.mjs.
//
// Usage:
//   node scripts/check_commit_prefix.mjs
//   COMMIT_PREFIX_BYPASS=1 node scripts/check_commit_prefix.mjs
//   COMMIT_PREFIX_BYPASS_PR_HEAD_SHA=<sha> node scripts/check_commit_prefix.mjs

import { execSync } from 'node:child_process';
import { exit } from 'node:process';

const ROOT = process.cwd();
const PREFIX_VIOLATION_RE = /^\s*@\s/;

function getCommitSubject(target) {
  try {
    const msg = execSync(`git log -1 --format=%s ${target}`, {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'],
    });
    return msg.trim();
  } catch {
    return null;
  }
}

function hasCommitTag(tag, prHeadSha) {
  const target = prHeadSha || 'HEAD';
  const subject = getCommitSubject(target);
  if (subject === null) return false;
  return subject.toLowerCase().includes(tag.toLowerCase());
}

const prHeadSha = process.env.COMMIT_PREFIX_BYPASS_PR_HEAD_SHA || process.env.STACK_BUMP_PR_HEAD_SHA || null;
const bypassFromCommit = hasCommitTag('[STACK BUMP]', prHeadSha);
const bypassFromEnv = process.env.COMMIT_PREFIX_BYPASS === '1';
const bypassOk = bypassFromCommit || bypassFromEnv;

const subject = getCommitSubject(prHeadSha || 'HEAD');
if (subject === null) {
  console.error('[ERROR] No commit subject available (git log failed)');
  exit(2);
}

if (bypassOk) {
  console.log('[COMMIT_PREFIX] bypass active — skipping prefix lint');
  exit(0);
}

if (PREFIX_VIOLATION_RE.test(subject)) {
  console.error(`[COMMIT_PREFIX] FAIL: commit subject starts with \`@\` (PowerShell here-string artifact):`);
  console.error(`  subject: ${subject}`);
  console.error('  Use `git commit -F <file>` instead of PowerShell `@\'...\'@` here-string.');
  console.error('  To bypass intentionally, add `[STACK BUMP]` to the commit subject.');
  exit(1);
}

console.log('[COMMIT_PREFIX] OK — commit subject does not start with `@`');
exit(0);