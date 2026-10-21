// Record one reviewed Rebecca scene. See plan/storyboard/README.md.
// OVERLAY=<build parent> PORT=7811 node tools/harness/record-scene.ts ridge --out /tmp/ridge-review
// Later scenes: <slug> --route <review.json> --from <played-checkpoint.json>.
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fetch, open, startRecording, stopRecording, waitForRecording } from './lab.ts';
import { load, restore, save, take } from './checkpoint.ts';
import { check, goTo, inControl, settle, useDoor } from './flows.ts';
import { Key } from './link.ts';
import { Run, commonFlag, inRoom } from './scenario.ts';
import { messageOnScreen } from './state.ts';
import { parseReviewRoute } from './scene-review.ts';
import { dayRooms } from '../rebecca/day/rooms.ts';
import { CUT_FLAGS } from '../rebecca/day/cutscenes.ts';

const args = process.argv.slice(2);
const option = (name: string) => { const at = args.indexOf(name); return at < 0 ? undefined : args[at + 1]; };
const slug = args[0];
if (!slug || slug.startsWith('-')) throw new Error('usage: record-scene.ts <slug> [--route file] [--from checkpoint] [--out dir]');
const routeFile = option('--route') ?? new URL(`../rebecca/day/${slug}/review.json`, import.meta.url).pathname;
const route = parseReviewRoute(JSON.parse(readFileSync(routeFile, 'utf8')));
if (route.scene !== slug) throw new Error('Route belongs to another scene');
const room = dayRooms.find((r) => r.slug === slug)!;
const from = option('--from');
if (slug !== 'ridge' && !from) throw new Error('Use --from with a played checkpoint for later scenes');
const checkpoint = from ? load(from) : undefined;
if (checkpoint && (checkpoint.stage !== room.stage || checkpoint.room !== room.room || checkpoint.built)) throw new Error('Checkpoint must be played and saved inside the reviewed scene');
const overlay = process.env.OVERLAY;
if (!overlay || !existsSync(path.join(overlay, 'REB'))) throw new Error('Set OVERLAY to the parent of the built REB folder');
const out = path.resolve(option('--out') ?? `/tmp/rebecca-review-${slug}`);
mkdirSync(out, { recursive: true });
const stamp = new Date().toISOString().replace(/[^0-9]/g, '').slice(0, 14);
const name = `${slug}-${stamp}`;
const remote = `${process.env.RE1_LAB_GAME_DIR ?? 'D:\\Games\\RE1-files'}\\${name}.mp4`;
const video = path.join(out, `${name}.mp4`);
const session = await open(Number(process.env.PORT ?? 7811), checkpoint ? '--mode REB --boot rebecca' : '--mode OG');
const { link } = session;
let recording = false;
const events: { t: number; frame: number; room: string; camera: number; what: string }[] = [];
let started = 0;
const log = (what: string) => {
  const s = link.latest!;
  const event = { t: Math.round((Date.now() - started) / 100) / 10, frame: s.frame, room: dayRooms.find((r) => inRoom(s, r))?.slug ?? `${s.stage}:${s.room}`, camera: s.camera, what };
  events.push(event);
  console.log(JSON.stringify(event));
};
const run = new Run(link, overlay, out);
const hash = (file: string) => createHash('sha256').update(readFileSync(file)).digest('hex');
let result = 'FAIL';
try {
  if (checkpoint) await restore(link, checkpoint);
  startRecording(remote, session.port);
  recording = true;
  waitForRecording(remote);
  started = Date.now();
  await link.state();
  log('recording ready');
  if (!checkpoint) {
    const deadline = Date.now() + 120_000;
    while (!(await link.frames(20)).title) {
      if (Date.now() > deadline) throw new Error('No title screen');
      await link.tap(Key.enter, 3);
    }
    await link.frames(30);
    await link.tap(Key.action, 3);
    await link.waitFor((s) => s.selectState === 1, 'character select', 60_000);
    for (const who of [1, 2]) {
      await link.tap(Key.right, 3);
      await link.waitFor((s) => s.selectState === 1 && s.selectFront === who, 'Rebecca card', 10_000);
    }
    await run.picture('rebecca-card');
    log('new Rebecca game');
    await link.tap(Key.action, 3);
    // Leave each page visible long enough to read in the recording.
    let calm = 0;
    const until = Date.now() + 180_000;
    while (calm < 3) {
      if (Date.now() > until) throw new Error('Opening never finished');
      const s = await link.frames(15);
      if (inRoom(s, room) && inControl(s) && !messageOnScreen(s)) { calm++; continue; }
      calm = 0;
      if (messageOnScreen(s)) {
        log(`opening message ${s.messageId}`);
        await link.frames(90);
        await run.picture(`opening-${s.messageId}`);
        await link.tap(Key.action, 3);
      }
    }
  }
  let s = await settle(link, (s) => inRoom(s, room));
  if (s.god) throw new Error('Review must run with normal damage');
  if (!checkpoint && (!commonFlag(s, CUT_FLAGS.get('cut-opening')!) || JSON.stringify(s.items.filter((i) => i.id)) !== JSON.stringify([{ id: 2, qty: 15 }, { id: 1, qty: 0 }]))) throw new Error('Opening or starting kit did not match');
  log(`scene ready; items ${JSON.stringify(s.items)}`);
  save(path.join(out, `${slug}-entry.json`), take(s, checkpoint?.reached ?? []));
  for (const step of route.steps) {
    if (step.action === 'walk') s = await goTo(link, run.dataDirs, step.x, step.z, { radius: 250 });
    if (step.action === 'look') s = await check(link, step.zone);
    if (step.action === 'hold') s = await link.frames(step.frames);
    if (step.action === 'exit') {
      log(`leaving for ${step.to}`);
      const next = dayRooms.find((r) => r.slug === step.to)!;
      s = step.zone ? await useDoor(link, step.zone) : await goTo(link, run.dataDirs, step.x, step.z, { radius: 400 });
      s = await settle(link, (s) => inRoom(s, next));
      log(`arrived in ${step.to}`);
      save(path.join(out, `${step.to}-entry.json`), take(s, checkpoint?.reached ?? []));
      await run.picture(`${slug}-exit-${step.to}`);
      await link.frames(90); // Keep the settled destination and a complete GOP.
      break;
    }
    if (!inRoom(s, room)) throw new Error('Left the scene before its exit step');
    if ('camera' in step && s.camera !== step.camera) throw new Error(`Expected camera ${step.camera}, got ${s.camera}`);
    log(`${step.action}${'picture' in step ? ` ${step.picture ?? ''}` : ''}`);
    if ('picture' in step && step.picture) await run.picture(step.picture);
  }
  result = 'PASS';
  run.finish();
} catch (error) {
  log(String(error));
  await run.crashed();
  throw error;
} finally {
  if (recording) {
    try {
      fetch(stopRecording(remote), video);
      writeFileSync(path.join(out, 'recording.json'), JSON.stringify({ scene: slug, recorded: new Date().toISOString().slice(0, 10), result, video: path.basename(video), sha256: hash(video), gameCommit: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(), route: JSON.parse(readFileSync(routeFile, 'utf8')), routeSha256: hash(routeFile), checkpoint: from ? { file: path.basename(from), sha256: hash(from) } : null, god: false, audio: false, timing: 'Seconds after recorder readiness; check video frames before selecting clip bounds.', events }, null, 2) + '\n');
      console.log(`video: ${video}`);
    } finally { session.end(); }
  } else session.end();
}
