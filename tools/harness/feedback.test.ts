// No game or lab needed: exercise the same CLI that a fixer runs.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { feedbackBoot, feedbackCheckpoint, readFeedback } from './feedback.ts';
import { readPng } from './image.ts';

const fixture = new URL('./fixtures/feedback/', import.meta.url).pathname;
const entry = path.join(fixture, '20261018-140506');

test('feedback adapts to the literal checkpoint fields and bank numbers', () => {
  assert.deepEqual(feedbackCheckpoint(readFeedback(entry)), {
    reached: [], stage: 2, room: 19, at: { x: 1200, z: 3400, angle: 1024 },
    banks: { 1: '00000080', 2: '00000040', 3: '00000020', 7: '00000010' },
    items: [[1, 1], [2, 15], [0, 0], [0, 0], [0, 0], [0, 0]],
    box: [[16, 6], [0, 0]], weapon: 2,
  });
});

test('page CLI escapes notes, plots room collision and path, and leaves an after slot', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 're1-feedback-'));
  try {
    const out = path.join(dir, 'index.html');
    // A tiny room with one box in its boundary table, decoded by room-map.ts.
    const rdt = Buffer.alloc(0x80);
    rdt.writeUInt32LE(0x50, 0x4c);
    rdt.writeInt32LE(1, 0x54);
    [1500, 3600, 1000, 3000, 1, 0x100].forEach((n, i) => rdt.writeUInt16LE(n, 0x68 + i * 2));
    const assets = path.join(dir, 'rooms', 'Stage3');
    cpSync(entry, path.join(dir, 'input', '20261018-140506'), { recursive: true });
    mkdirSync(assets, { recursive: true });
    writeFileSync(path.join(assets, 'ROOM3130.RDT'), rdt);
    execFileSync(process.execPath, [new URL('./feedback.ts', import.meta.url).pathname, 'page', path.join(dir, 'input'), out], {
      env: { ...process.env, RE1_FEEDBACK_ASSETS: path.join(dir, 'rooms') },
    });
    const html = readFileSync(out, 'utf8');
    for (const text of [
      '<script src="/research/rebecca-day/nav.js" defer></script>',
      'Fence &lt;clips&gt; &amp; &quot;snags&quot; at 2 posts', 'ridge', 'Camera 1',
      '1200, -20, 3400', 'HP 85/100', 'type 0', 'health 120',
      'class="collision"', 'points="1100,3300 1200,3400"',
      'data-after="20261018-140506"', 'After: awaiting proof',
    ]) assert.ok(html.includes(text), `missing ${text}`);
    assert.ok(!html.includes('9999,9999'), 'do not join trails across rooms');
    assert.ok(!html.includes('1234,5678'), 'omit samples older than ten seconds');
    assert.deepEqual([...readPng(path.join(entry, 'shot.png')).rgb], [255, 0, 0]);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('raw capture converts through the page CLI with the same pixels', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 're1-feedback-raw-'));
  try {
    cpSync(entry, path.join(dir, 'input', '20261018-140506'), { recursive: true });
    const local = path.join(dir, 'input', '20261018-140506');
    rmSync(path.join(local, 'shot.png'));
    writeFileSync(path.join(local, 'shot.rgba'), Buffer.concat([Buffer.from('RE1CAP 1 1\n'), Buffer.from([12, 34, 56, 255])]));
    const out = path.join(dir, 'index.html');
    execFileSync(process.execPath, [new URL('./feedback.ts', import.meta.url).pathname, 'page', path.join(dir, 'input'), out], { env: { ...process.env, RE1_FEEDBACK_ASSETS: dir } });
    assert.ok(readFileSync(out, 'utf8').includes('Collision unavailable'));
    assert.ok(readFileSync(out, 'utf8').includes('data:image/png;base64,'));
    assert.deepEqual([...readPng(path.join(local, 'shot.png')).rgb], [12, 34, 56]);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('rejects malformed note metadata at the boundary', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 're1-feedback-invalid-'));
  try {
    writeFileSync(path.join(dir, 'note.json'), '{"version":1,"kind":"oops"}');
    assert.throws(() => readFeedback(dir), /feedback/);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('Rebecca restore uses character id 3 and produces the actual lab boot arguments', () => {
  const note = readFeedback(entry);
  assert.equal(note.state.player.id, 3);
  assert.equal(feedbackBoot(note), '--mode REB --boot rebecca');
  assert.equal(feedbackBoot({ ...note, mode: 'OG', state: { ...note.state, player: { ...note.state.player, id: 0 } } }), '--mode OG --boot chris');
  assert.throws(() => feedbackBoot({ ...note, state: { ...note.state, player: { ...note.state.player, id: 2 } } }), /character/);
});
