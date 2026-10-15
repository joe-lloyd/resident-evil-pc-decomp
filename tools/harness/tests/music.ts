// Which track each room plays. In her mode: the save rooms play RE1's own
// save room music (Bgm_31, the player's own file), the station's rooms play
// our render, and rooms whose cue has no audio are silent, among them rooms
// in slots whose RE1 row has music. The mansion's save room keeps RE1's row.
// In Chris's game, RE1's save room still plays RE1's own track. The game
// reports each BGM channel's file and whether it plays (TestMode.cpp); the
// harness can't hear, so this is what it checks.
//
//   OVERLAY=<REB build> PORT=7801 RE1_LAB_GAME_DIR='D:\Games\RE1-decomp' node tools/harness/tests/music.ts
import { open } from '../lab.ts';
import type { GameLink } from '../link.ts';
import { settle } from '../flows.ts';
import { playingMusic, roomLabel, type GameState } from '../state.ts';

const port = Number(process.env.PORT ?? 7801);
if (!process.env.OVERLAY) throw new Error('set OVERLAY to the REB build folder the game has');

/** Each room, and the files it should play: [] is silence. */
const HER_ROOMS: readonly [what: string, stage: number, room: number, files: readonly string[]][] = [
  ['the station yard, our render', 2, 0x15, ['Reb_station']],
  ['the tool shed, the same piece through the door', 2, 0x16, ['Reb_station']],
  ['the cabin, a save room', 2, 0x14, ['Bgm_31']],
  ['the gorge footbridge, the station again', 2, 0x17, ['Reb_station']],
  ["the operator's booth, a save room", 2, 0x19, ['Bgm_31']],
  ['the hollow, only the room', 2, 0x1b, []],
  ["the foreman's office, a save room", 3, 0x12, ['Bgm_31']],
  ['the mine lift, in a lab room slot RE1 gives music', 4, 0x09, []],
  ['the mine office, a save room', 4, 0x1d, ['Bgm_31']],
  ['the summit trail, in a slot RE1 gives music', 1, 0x13, []],
  ["the gardener's lodge, a save room", 1, 0x1d, ['Bgm_31']],
  ["the mansion's save room, on RE1's own row", 0, 0x00, ['Bgm_31']],
];

const failures: string[] = [];
const same = (a: readonly string[], b: readonly string[]) => a.length === b.length && a.every((f, i) => f.toLowerCase() === b[i]!.toLowerCase());
const describe = (s: GameState) => s.bgm!.channels.map((c) => `${c.file || '-'}${c.playing ? ' playing' : ''}${c.file ? ` at ${c.volume}` : ''}`).join(', ');

/** Wait for the room's music to settle on `files`; silence must hold for two seconds. */
async function expectMusic(link: GameLink, what: string, files: readonly string[]): Promise<GameState> {
  let s = await link.state();
  const deadline = Date.now() + 15_000;
  let heard = 0;
  while (Date.now() < deadline) {
    s = await link.frames(10);
    heard = same(playingMusic(s), files) ? heard + 1 : 0;
    if (heard >= (files.length ? 2 : 6)) break;
  }
  const ok = heard > 0 && same(playingMusic(s), files);
  const muted = s.bgm!.channels.some((c) => c.playing && c.volume <= -9999);
  console.log(`${ok && !muted ? 'ok  ' : 'FAIL'} ${roomLabel(s)} ${what}: state ${s.bgm!.state.toString(16)}, ${describe(s)}`);
  if (!ok) failures.push(`${what} (${roomLabel(s)}) plays [${playingMusic(s).join(', ')}], not [${files.join(', ')}]`);
  if (muted) failures.push(`${what} (${roomLabel(s)}) plays at -9999, which is silent`);
  return s;
}

// Her mode.
{
  const [, stage, room] = HER_ROOMS[0]!;
  const session = await open(port, `--mode REB --boot rebecca:${stage}:${room}`);
  try {
    const link = session.link;
    await settle(link, (s) => s.stage === stage && s.room === room);
    for (const [what, st, rm, files] of HER_ROOMS) {
      const s = await link.state();
      if (s.stage !== st || s.room !== rm) {
        await link.room(st, rm);
        await settle(link, (x) => x.stage === st && x.room === rm);
      }
      await expectMusic(link, what, files);
    }
    // RE1's tracks loop; so does ours. The station's file is 96 s: in the yard
    // past its end, it must still be playing.
    await link.room(2, 0x15);
    await settle(link, (x) => x.stage === 2 && x.room === 0x15);
    await expectMusic(link, 'the station yard again', ['Reb_station']);
    const until = Date.now() + 100_000;
    while (Date.now() < until) await link.frames(150);
    await expectMusic(link, 'the station yard, 100 s on: the loop', ['Reb_station']);
  } finally {
    session.end();
  }
}

// Chris's game, on RE1's own table: the first time in RE1's save room his
// meeting with Rebecca plays Bgm_13; back in the room afterwards, the save
// room music, Bgm_31.
{
  const session = await open(port, '--boot chris:0:0');
  try {
    const link = session.link;
    await settle(link, (s) => s.stage === 0 && s.room === 0);
    await expectMusic(link, "Chris meets Rebecca in RE1's save room", ['Bgm_13']);
    await link.room(0, 3);
    await settle(link, (s) => s.stage === 0 && s.room === 3);
    await link.room(0, 0);
    await settle(link, (s) => s.stage === 0 && s.room === 0);
    await expectMusic(link, "Chris back in RE1's save room", ['Bgm_31']);
  } finally {
    session.end();
  }
}

if (failures.length) {
  console.error(`FAIL\n  ${failures.join('\n  ')}`);
  process.exit(1);
}
console.log('PASS');
