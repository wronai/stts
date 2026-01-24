#!/usr/bin/env node
/**
 * stts-node (repo root wrapper)
 * Deleguje do nodejs/stts.mjs.
 */

import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const root = dirname(fileURLToPath(import.meta.url));
const target = join(root, 'nodejs', 'stts.mjs');

const res = spawnSync(process.execPath, [target, ...process.argv.slice(2)], { stdio: 'inherit' });
process.exit(res.status ?? 1);
