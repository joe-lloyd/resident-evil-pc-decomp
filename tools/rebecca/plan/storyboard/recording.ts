// node tools/rebecca/plan/storyboard/recording.ts <quarters dir> <out.json>
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { day } from '../day.ts';
import { dayRooms } from '../../day/rooms.ts';

const [root, out] = process.argv.slice(2);
if (!root || !out || process.argv.length !== 4) throw new Error('Usage: recording.ts <quarters dir> <out.json>');
const attempts = ['1', 'chain2', 'chain3', 'chain3'];
const rooms = day.places.map((p) => {
  const slug = p.room ?? p.id;
  const r = dayRooms.find((r) => r.slug === slug);
  const id = r ? `${r.stage + 1}${r.room.toString(16).padStart(2, '0').toUpperCase()}` : p.existing?.match(/^ROOM(.{3})0\.RDT$/)?.[1];
  if (!id) throw new Error(`No recording room id for ${p.id}`);
  return { room: p.id, slug, id };
});
const hash = (data: Buffer) => createHash('sha256').update(data).digest('hex');
const quarters = attempts.map((attempt, i) => {
  const quarter = i + 1;
  const log = `q${quarter}/log-${attempt}.txt`;
  const video = `q${quarter}/reb-q${quarter}-${attempt}.mp4`;
  const raw = readFileSync(join(root, log));
  const lines = raw.toString('utf8').split('\n');
  const events = lines.flatMap((line) => {
    const m = /^\[(\d+)s\] ([\dA-F]{3}) hp \S+ (.*)$/.exec(line);
    if (!m) return [];
    const room = rooms.find((r) => r.id === m[2]);
    if (!room) throw new Error(`Unknown room in ${log}: ${line}`);
    return [{ t: Number(m[1]), room: room.room, what: m[3] ?? '' }];
  });
  if (!events.length) throw new Error(`No events in ${log}`);
  return { quarter, log, logSha256: hash(raw), sourceVideo: video, video: `q${quarter}.mp4`, sha256: hash(readFileSync(join(root, video))),
    result: lines.find((s) => /^(PASS|FAIL)$/.test(s)) ?? 'Unknown',
    failures: lines.filter((s) => s.startsWith('  FAILED: ')).map((s) => s.slice(10)),
    // gdigrab uses wall-clock timestamps. Capture starts a few seconds after Run.
    // Background matches refine the rounded log stamps, including entry cutscenes.
    scale: 1, offset: -4,
    manualEntries: quarter === 4 ? [{ room: 'save', start: 844.5, poster: 861, note: 'Original save room has no camera render. Entrance checked by eye at half-second intervals.' }] : [],
    events };
});
writeFileSync(out, `${JSON.stringify({ recorded: '2026-10-17', rooms, quarters }, null, 2)}\n`);
process.stdout.write(`Saved ${quarters.reduce((n, q) => n + q.events.length, 0)} events from four matched recordings\n`);
