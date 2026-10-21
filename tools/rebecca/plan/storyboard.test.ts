// node --test tools/rebecca/plan/storyboard.test.ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { day } from './day.ts';
import { dayRooms } from '../day/rooms.ts';
import { CUTSCENES } from '../day/cutscenes.ts';
import { SUPPLIES, SUPPLY_KINDS } from '../day/supplies.ts';
import { DOCUMENTS } from '../files/documents.ts';
import { MAP_ITEMS } from './maps.ts';
import { buildStoryboard, messages, renderStoryboard } from './storyboard.ts';

const board = buildStoryboard();

test('every place appears once as a scene and a route card', () => {
  assert.deepEqual(board.scenes.map((s) => s.place.id), day.places.map((p) => p.id));
  const html = renderStoryboard(board);
  for (const p of day.places) {
    assert.equal(html.split(`id="scene-${p.id}"`).length - 1, 1, p.id);
    assert.equal(html.split(`data-card="${p.id}"`).length - 1, 1, p.id);
  }
});

test('every standalone entry thought appears in the audit', () => {
  const expected: string[] = [];
  for (const r of dayRooms) {
    const script = readFileSync(new URL(`../day/${r.slug}/room.c`, import.meta.url), 'utf8');
    if (/message\(128,\s*255,\s*0\)/.test(script) && !CUTSCENES.some((c) => c.room === r.slug && c.trigger.on === 'enter')) expected.push(r.slug);
  }
  assert.deepEqual(board.audit.map((a) => a.slug).sort(), expected.sort());
  const html = renderStoryboard(board);
  for (const a of board.audit) {
    assert.ok(a.text.length > 0, a.slug);
    assert.ok(html.includes(`data-audit="${a.room}"`), a.slug);
  }
});

test('supply quantities, file and map totals match their source tables', () => {
  for (const act of day.acts) {
    const slugs = new Set(day.places.filter((p) => p.act === act.n).map((p) => p.room ?? p.id));
    const expected = Object.entries(SUPPLIES).filter(([slug]) => slugs.has(slug)).flatMap(([, kinds]) => kinds);
    const actual = board.items.filter((i) => i.act === act.n && i.source === 'supplies');
    assert.equal(actual.length, expected.length);
    assert.equal(actual.reduce((n, i) => n + i.qty, 0), expected.reduce((n, k) => n + SUPPLY_KINDS[k].qty, 0));
    assert.equal(board.balance.find((b) => b.act === act.n)?.rounds, board.items.filter((i) => i.act === act.n && i.placed && (i.kind === 'ammo' || i.kind === 'weapon')).reduce((n, i) => n + i.rounds, 0));
  }
  assert.equal(board.items.filter((i) => i.kind === 'file').length, DOCUMENTS.length);
  assert.equal(board.items.filter((i) => i.kind === 'map').length, MAP_ITEMS.length);
  assert.equal(board.items.filter((i) => i.room === 'cabin' && i.kind === 'heal').length, 1);
  assert.equal(board.items.filter((i) => i.room === 'cabin' && i.kind === 'ribbons').reduce((n, i) => n + i.qty, 0), 3);
});

test('no room stops her for an entry thought', () => {
  assert.deepEqual(board.audit.map((a) => a.room), []);
});

test('the tracker drops written scenes and keeps an unmapped reward and missing art', () => {
  for (const id of ['cut-credits', 'cut-dog', 'cut-mine-chase']) assert.ok(!board.missing.some((m) => m.detail.includes(id)), id);
  assert.ok(!board.missing.some((m) => m.detail.includes('cut-chris')), 'Chris is written inside cut-sleep');
  assert.ok(board.missing.some((m) => m.room === 'mast' && m.detail.includes('supplies has no matching pickup step')));
  assert.ok(board.missing.some((m) => m.room === 'save' && m.title.startsWith('Render')));
});

test('starting kit, loaded gun and hand-written enemy spawns enter the balance', () => {
  assert.deepEqual(board.balance.map((b) => [b.act, b.rounds, b.enemies]), [[1, 15, 8], [2, 75, 36], [3, 30, 11], [4, 5, 1]]);
  assert.deepEqual(board.items.filter((i) => i.kind === 'weapon').map((i) => `${i.name} ${i.source}`), ['Beretta start', 'Knife start']);
  assert.deepEqual(board.items.filter((i) => i.source === 'start').map((i) => [i.name, i.rounds]), [['Beretta', 15], ['Knife', 0]]);
  assert.equal(board.items.find((i) => i.room === 'cabin' && i.kind === 'ribbons')?.name, 'Ink ribbons');
});


test('message decoding keeps opening quotes and identifies control-only rows', () => {
  assert.deepEqual(messages('0: \\n\\oHello!"\\p{0}\\n\\o"Stay here."'), [
    { n: 0, raw: '\\n\\oHello!"\\p{0}\\n\\o"Stay here."', text: '"Hello!"\n\n\n"Stay here."' },
  ]);
  assert.equal(messages('0: \\s{0}\\n\\s{2}\\d{70}')[0]?.text, 'Timing controls only. No written words in this source message.');
});

test('the ending keeps its written lines alongside inherited control messages', () => {
  const save = board.scenes.find((s) => s.place.id === 'save');
  assert.ok(save?.msgs.some((m) => m.text === '"Freeze!"'));
  assert.ok(save?.cuts.some((c) => c.beats.some((b) => b.kind === 'say' && b.text === '"Freeze!"')));
  assert.equal(board.scenes.reduce((n, s) => n + s.msgs.length, 0), 587);
});

test('each recorded visit has its own player and each room card shows coverage', () => {
  const html = renderStoryboard(board);
  assert.equal(board.scenes.filter((s) => s.clips.length).length, 53);
  assert.equal(html.split('<video controls preload="none"').length - 1, 142);
  for (const scene of board.scenes) {
    for (const clip of scene.clips) {
      assert.ok(html.includes(`src="${clip.file}" type="video/mp4"`), clip.file);
      assert.ok(html.includes(`poster="${clip.poster}"`), clip.poster);
    }
  }
  assert.deepEqual(board.scenes.filter((s) => !s.clips.length).map((s) => s.place.id), ['flume', 'line-track', 'weather', 'mast', 'wine']);
  assert.equal(html.split('No footage of this room in the four-quarter recording.').length - 1, 5);
  assert.ok(html.includes('15 recorded clips'), 'repeated room visits remain visible on cards');
});

test('visit labels keep logged actions and distinguish the cabin plan id from its recording slug', () => {
  const cabin = board.scenes.find((s) => s.place.id === 'cabin');
  assert.ok(cabin && cabin.clips.length > 1);
  assert.ok(cabin.clips.some((c) => c.events.some((e) => e.what === 'took the shed key')));
  const html = renderStoryboard(board);
  assert.ok(html.includes('took the shed key'));
  assert.ok(html.includes('Quarter 4 · Visit 1'));
  assert.ok(html.includes('https://home.arpa/research/rebecca-whole-day/'));
  assert.ok(!html.includes('older room layout'));
});

test('the recording manifest rejects bad spans and unsafe asset paths', async () => {
  const { parseFootage } = await import('./storyboard/footage.ts');
  const visit = { room: 'ridge', quarter: 1, visit: 1, start: 0, end: 30, file: 'clips/ridge-q1-v01.mp4', poster: 'clips/ridge-q1-v01.jpg', note: '', events: [{ t: 23, what: 'on the ridge' }] };
  assert.equal(parseFootage({ clips: [visit], noFootage: [] }).clips[0]?.end, 30);
  assert.throws(() => parseFootage({ clips: [{ ...visit, end: 0 }], noFootage: [] }), /Invalid clip span/);
  assert.throws(() => parseFootage({ clips: [{ ...visit, file: '../bad.mp4' }], noFootage: [] }), /Invalid clip path/);
  assert.throws(() => parseFootage({ clips: [visit, visit], noFootage: [] }), /Duplicate clip file/);
});

test('quarter four booth footage starts after the unlogged ridge intro', () => {
  const booth = board.scenes.find((s) => s.place.id === 'booth');
  assert.deepEqual(booth?.clips.filter((c) => c.quarter === 4).map((c) => c.start), [29.967]);
});

test('a reviewed scene shows its own date and damage mode beside the new clip', async () => {
  const { parseFootage, renderClips } = await import('./storyboard/footage.ts');
  const clip = { room: 'ridge', quarter: 1, visit: 1, start: 4, end: 60,
    file: 'clips/ridge-review-test.mp4', poster: 'clips/ridge-review-test.jpg', note: 'Both cameras checked.',
    events: [{ t: 5, what: 'new Rebecca game' }],
    review: { recorded: '2026-10-21', source: 'recordings/ridge-test.mp4', god: false, audio: false, checkpoint: null } };
  const parsed = parseFootage({ clips: [clip], noFootage: [] });
  const html = renderClips(parsed.clips, 'The ridge');
  assert.ok(html.includes('2026-10-21 · Scene review'));
  assert.ok(html.includes('Normal damage · No sound · New Rebecca game'));
  assert.ok(!html.includes('17 October recording'));
  assert.ok(html.includes('recordings/ridge-test.mp4'));
  assert.throws(() => parseFootage({ clips: [{ ...clip, review: { ...clip.review, source: '../bad.mp4' } }], noFootage: [] }), /Invalid scene recording/);
});
