import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { test } from 'node:test';
import { ENTRY_THOUGHT_ALLOWLIST } from './scripts.ts';

const here = new URL('./', import.meta.url);

test('no room gains an entry thought outside the story allow-list', () => {
  const bad: string[] = [];
  for (const slug of readdirSync(here)) {
    if (ENTRY_THOUGHT_ALLOWLIST[slug]) continue;
    const scene = new URL(`${slug}/scene.py`, here);
    const record = new URL(`${slug}/renders/room.json`, here);
    if (existsSync(scene) && /^\s*room\.entry\s*=\s*(?!None\b)/m.test(readFileSync(scene, 'utf8'))) bad.push(`${slug}: scene.py entry`);
    if (existsSync(record) && JSON.parse(readFileSync(record, 'utf8')).entry) bad.push(`${slug}: room.json entry`);
    const script = new URL(`${slug}/room.c`, here);
    if (!existsSync(script)) continue;
    const main = readFileSync(script, 'utf8').split('// main procedure 0')[1]?.split(/\/\/ (?:event procedure|CUTSCENE EVENTS)/)[0] ?? '';
    // Kit slot 0 and the hand-written introductions. Cutscene dialogue is
    // in event procedures; map and puzzle responses use other message ids.
    if (/message\(128, 255, 0\)/.test(main) || (slug === 'trail' && /message\(130, 255, 0\)/.test(main))) bad.push(`${slug}: main entry message`);
  }
  assert.deepEqual(bad, []);
});
