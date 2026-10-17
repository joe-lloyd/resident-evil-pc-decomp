// How a cutscene of her day is described, and how it becomes RE1 script.
//
// RE1's cutscenes are event scripts (EVT): a room's main procedure starts one
// with evt_exec, and it runs a frame at a time beside the game, cutting the
// camera, walking people about, playing their animations and showing lines.
// docs/REBECCA_CUTSCENES.md says how to make one; day/cutscenes.ts holds them.
//
// A scene is a room, what starts it, the people in it and a list of beats.
// `compileScene` turns it into the lines it adds to the room's init and main
// procedures and its event procedure, in `rae asm` text. The recipe is the
// mansion save room's (ROOM1000): letterbox bars and her controls off at the
// start, both back and the camera free at the end.
import { EVENT_FLAGS } from './events.ts';
import type { Floor } from './foes.ts';

/** The people of her day, and Chris at the end: RE1 character models (docs/REBECCA_NPC.md). */
export const PEOPLE = {
  hal: { entity: 34, name: 'Hal' },
  dana: { entity: 33, name: 'Dana' },
  chris: { entity: 32, name: 'Chris' },
} as const;
export type Person = keyof typeof PEOPLE;
export type Who = 'her' | Person;

/** A place on the floor, in game units; angle 0 faces +X, 1024 -Z, 2048 -X, 3072 +Z. */
export interface Spot {
  readonly x: number;
  readonly z: number;
  readonly angle?: number;
}
export type Rect = { readonly x0: number; readonly z0: number; readonly x1: number; readonly z1: number };

/** An animation and the frame to hold, for someone standing still in it (a man lying dead is 4, 29). */
export type Pose = readonly [anim: number, frame: number];

export type Beat =
  /** Cut to one of the room's cameras. */
  | { readonly kind: 'cut'; readonly camera: number }
  /** Stand someone somewhere at once. */
  | { readonly kind: 'place'; readonly who: Who; readonly at: Spot }
  /** Walk (or run) someone to a spot; the scene waits until they get there. */
  | { readonly kind: 'walk'; readonly who: Who; readonly to: Spot; readonly run: boolean }
  /** Turn someone on the spot to face a point; the scene waits. */
  | { readonly kind: 'face'; readonly who: Who; readonly to: Spot }
  /** Play one of a person's animations; the scene waits for its end, unless it loops. */
  | { readonly kind: 'anim'; readonly who: Person; readonly anim: number; readonly loop: boolean }
  /** A line in the message box; the scene waits until the player closes it. A person's line has them gesture as they say it. */
  | { readonly kind: 'say'; readonly text: string; readonly by: Who }
  /** Wait, in frames (30 a second). */
  | { readonly kind: 'wait'; readonly frames: number }
  /** Fade the screen to black, or back. */
  | { readonly kind: 'fade'; readonly to: 'black' | 'clear' }
  /** Shake the screen, or stop. */
  | { readonly kind: 'shake'; readonly on: boolean }
  /** Take a person out of the room. */
  | { readonly kind: 'gone'; readonly who: Person }
  /** Hand her a key item lying in the room (by its plan step): the game's own pickup screen. */
  | { readonly kind: 'give'; readonly item: string }
  /** Raw SCD commands, run as the scene reaches them (the mine's gear loss). */
  | { readonly kind: 'scd'; readonly lines: readonly string[] };

export const cut = (camera: number): Beat => ({ kind: 'cut', camera });
export const place = (who: Who, at: Spot): Beat => ({ kind: 'place', who, at });
export const walk = (who: Who, to: Spot): Beat => ({ kind: 'walk', who, to, run: false });
export const run = (who: Who, to: Spot): Beat => ({ kind: 'walk', who, to, run: true });
export const face = (who: Who, to: Spot): Beat => ({ kind: 'face', who, to });
export const anim = (who: Person, n: number, loop = false): Beat => ({ kind: 'anim', who, anim: n, loop });
/** Her line: a thought plain, speech in quotes. */
export const say = (text: string): Beat => ({ kind: 'say', text, by: 'her' });
/** A person's line, in quotes. */
export const line = (by: Person, text: string): Beat => ({ kind: 'say', text, by });
export const wait = (frames: number): Beat => ({ kind: 'wait', frames });
export const fade = (to: 'black' | 'clear'): Beat => ({ kind: 'fade', to });
export const shake = (on: boolean): Beat => ({ kind: 'shake', on });
export const gone = (who: Person): Beat => ({ kind: 'gone', who });
export const give = (item: string): Beat => ({ kind: 'give', item });
export const scd = (...lines: string[]): Beat => ({ kind: 'scd', lines });

/** What starts a scene. It runs once: its flag is set as it starts. */
export type Trigger =
  /**
   * The first time she is in the room. Through its door from `from` (a room
   * slug), she starts at that door's arrival; without one (the ridge, where
   * her day starts) she stays where she is.
   */
  | { readonly on: 'enter'; readonly from?: string }
  /** Pressing action at the scene's thing to examine: the room's check whose text starts with `check`. */
  | { readonly on: 'check'; readonly check: string }
  /** Walking into a part of the floor. */
  | { readonly on: 'zone'; readonly zone: Rect }
  /** A puzzle step of day/events.ts having happened, here. */
  | { readonly on: 'step'; readonly step: string };

/** Someone in the scene: where they stand until it runs, and, if they stay, where and how after. */
export interface Cast {
  readonly who: Person;
  readonly at: Spot;
  readonly pose?: Pose;
  readonly after?: Spot & { readonly pose?: Pose };
}

export interface Cutscene {
  /** Its tracker row (plan/todo.ts CUTSCENES), such as cut-phone. */
  readonly id: string;
  /** The room's slug (day/rooms.ts), or 'save' for the mansion's save room. */
  readonly room: string;
  readonly trigger: Trigger;
  readonly cast?: readonly Cast[];
  readonly beats: readonly Beat[];
  /** For a check trigger: what examining the thing says once the scene has run. */
  readonly after?: string;
}

/** What a room gives the compiler: its message ids, its free room-action ids and FG_ROOM bits. */
export interface RoomContext {
  /** Add a line to the room's messages; returns its id for message(). */
  readonly say: (text: string) => number;
  /** The room action (aot) id of the check a check trigger replaces, and its own message id. */
  readonly check?: { readonly id: number; readonly zone: Rect; readonly message: number };
  /** A free room action id, for a zone trigger. */
  readonly freeAction: () => number;
  /** The room action id of the pickup of a key item (by its plan step) lying in the room. */
  readonly itemAction: (step: string) => number | undefined;
  /** A free FG_ROOM bit in word 0 (cleared as the room loads). */
  readonly freeBit: () => number;
  /** Where she arrives through the room's door from another room, by its slug. */
  readonly arrival: (from: string) => Spot | undefined;
  /** The room's floor, which every walk must keep to; RE1's own rooms have no records of it. */
  readonly floor?: Floor;
}

/** How far a walker keeps from walls, gaps and doors: her body's reach. */
const CLEAR = 400;

/**
 * Whether a straight walk from `a` to `b` keeps to the floor: inside its
 * edge, clear of walls and gaps, and out of the doors, which would take her
 * out of the room. A walk is a straight line in the engine, and one that
 * meets a wall never arrives, so the scene would wait for ever.
 */
export function clearWalk(floor: Floor, a: Spot, b: Spot): boolean {
  const out = (r: Rect, x: number, z: number, pad: number) => x < r.x0 - pad || x > r.x1 + pad || z < r.z0 - pad || z > r.z1 + pad;
  const n = Math.max(1, Math.ceil(Math.hypot(b.x - a.x, b.z - a.z) / 100));
  for (let i = 0; i <= n; i++) {
    const x = a.x + ((b.x - a.x) * i) / n;
    const z = a.z + ((b.z - a.z) * i) / n;
    const fb = floor.bounds;
    if (x < fb.x0 + CLEAR || x > fb.x1 - CLEAR || z < fb.z0 + CLEAR || z > fb.z1 - CLEAR) return false;
    if (![...floor.walls, ...(floor.voids ?? [])].every((w) => out(w, x, z, CLEAR))) return false;
    // She may start in a door's reach, having just come in; she must not walk into one.
    if (i > 0 && !floor.doors.every((d) => out(d.zone, x, z, 0))) return false;
  }
  return true;
}

export interface Compiled {
  readonly init: string[];
  readonly main: string[];
  readonly event: string[];
}

/** Enemy slots the people take: after the room's foes (day/foes.ts counts up from 0), within the 8 RE1 rooms use. */
const PERSON_SLOTS = [6, 7] as const;
/**
 * FG_ROOM bit the people and the player raise when a walk, turn or animation
 * ends (anim_pose's and anim_play's last operand), as the mansion's events
 * use 62: word 1, which the engine clears every frame.
 */
const DONE_BIT = 62;
/** Gestures a person makes while talking, in turn: RE1's people share these (ROOM1000's talk). */
const TALK = [34, 33, 37, 35] as const;
/** Where a person who has left the room stands: far off every camera. */
const OUT_OF_SIGHT = -30000;
/** The idle loop in the people's built models (npc/people.ts swaps it into 0). */
const IDLE = 0;

const size = (z: Rect) => `${z.x0}, ${z.z0}, ${z.x1 - z.x0}, ${z.z1 - z.z0}`;

/** The slot each of the scene's people takes. */
export function slots(scene: Pick<Cutscene, 'cast'>): Map<Person, number> {
  const cast = scene.cast ?? [];
  if (cast.length > PERSON_SLOTS.length) throw new Error(`a scene can hold ${PERSON_SLOTS.length} people`);
  return new Map(cast.map((c, i) => [c.who, PERSON_SLOTS[i]!]));
}

/** The enemy() line that stands a person somewhere, in a pose or idle. */
function spawn(who: Person, slot: number, at: Spot, pose: Pose = [0, 0]): string {
  return `enemy(${PEOPLE[who].entity}, 0, 255, 1, 2, 0, 0, ${at.angle ?? 0}, 0, 0, ${at.x}, 0, ${at.z}, ${slot}, ${pose[0]}, ${pose[1]}, 0);  // ${PEOPLE[who].name}`;
}

/**
 * The scene as the lines it adds to its room. `event` is the index of its
 * event procedure in the room, `flag` its FG_COMMON flag.
 */
export function compileScene(scene: Cutscene, event: number, flag: number, room: RoomContext): Compiled {
  const slot = slots(scene);
  const slotOf = (who: Person) => {
    const s = slot.get(who);
    if (s === undefined) throw new Error(`${scene.id}: ${who} is not in its cast`);
    return s;
  };
  const init: string[] = [`// ${scene.id} (day/cutscenes.ts): its people, and what starts it. FG_COMMON ${flag} once it has run.`];
  const main: string[] = [];
  const ev: string[] = [`// event procedure ${event}`, `// ${scene.id} (day/cutscenes.ts)`];

  // The people: as they are until the scene, and after it if they stay.
  const idle: number[] = [];
  for (const c of scene.cast ?? []) {
    const s = slotOf(c.who);
    init.push(`if (ck(FG_COMMON, ${flag}, 1)) {`, `    ${spawn(c.who, s, c.at, c.pose)}`, ...(c.after ? ['} else {', `    ${spawn(c.who, s, c.after, c.after.pose)}`] : []), '}');
    if (!c.pose) idle.push(s);
  }
  // A person's first update clears its idle (npc_state0_init), so on the
  // second frame each idle one is given idle 9, which loops animation 0
  // (lookout/room.c): `armed` marks the first frame, `ready` that it is done.
  let ready: number | undefined;
  if (idle.length) {
    const armed = room.freeBit();
    ready = room.freeBit();
    main.push(
      `if (ck(FG_COMMON, ${flag}, 1) && ck(FG_ROOM, ${ready}, 1)) {`,
      `    if (ck(FG_ROOM, ${armed}, 0)) {`,
      ...idle.map((s) => `        eml_state(0, ${s}, 2, 9, 0);`),
      `        set(FG_ROOM, ${ready}, 0);`,
      '    }',
      `    set(FG_ROOM, ${armed}, 0);`,
      '}',
    );
  }

  // What starts it. The room's main procedure starts it once (evt_exec), or
  // the engine does from a room action (SCE_EVENT), which the scene then takes
  // away so it can't start twice.
  const start = `evt_exec(0, 9, ${event});`;
  const begin: string[] = [`set(FG_COMMON, ${flag}, 0);`];
  const t = scene.trigger;
  switch (t.on) {
    case 'enter':
    case 'step': {
      const when = [`ck(FG_COMMON, ${flag}, 1)`];
      if (t.on === 'step') {
        const f = EVENT_FLAGS.get(t.step);
        if (f === undefined) throw new Error(`${scene.id}: no puzzle step ${t.step} in events.ts`);
        when.push(`ck(FG_COMMON, ${f}, 0)`);
      }
      // With people about, not before their idle is set: the scene would set them going first.
      if (ready !== undefined) when.push(`ck(FG_ROOM, ${ready}, 0)`);
      main.push(`if (${when.join(' && ')}) {`, `    set(FG_COMMON, ${flag}, 0);`, `    ${start}`, '}');
      break;
    }
    case 'check': {
      const c = room.check;
      if (!c) throw new Error(`${scene.id}: no check in ${scene.room} starts with "${t.check}"`);
      const after = room.say(scene.after ?? '...');
      const thereafter = `aot_set(${c.id}, ${size(c.zone)}, SCE_MESSAGE, 129, ${after}, 0, 255, 0, 0, 0);`;
      init.push(`if (ck(FG_COMMON, ${flag}, 1)) {`, `    aot_set(${c.id}, ${size(c.zone)}, SCE_EVENT, 129, 9, 0, ${event}, 0, 0, 0);`, '} else {', `    ${thereafter}`, '}');
      begin.push(thereafter);
      break;
    }
    case 'zone': {
      const id = room.freeAction();
      init.push(`if (ck(FG_COMMON, ${flag}, 1)) {`, `    aot_set(${id}, ${size(t.zone)}, SCE_EVENT, 1, 9, 0, ${event}, 0, 0, 0);`, '}');
      begin.push(`aot_reset(${id}, SCE_NONE, 129, 0, 0, 0);`);
      break;
    }
    default: {
      const never: never = t;
      throw new Error(`unknown trigger ${JSON.stringify(never)}`);
    }
  }

  // Its flag, the letterbox bars on (FG_STATUS 15: g_main_state_flags
  // 0x10000) and her controls off (FG_6 23: g_message_flags 0x100). A scene
  // a step starts waits for the step's own line to close first.
  if (t.on === 'step') ev.push('wait_voice();');
  ev.push('scd {', ...begin.map((l) => `    ${l}`), '    set(FG_STATUS, 15, 0);', '    set(FG_6, 23, 1);', '    return;', '}');

  // Where each walker is, as far as the scene knows, so each walk can be checked.
  const where = new Map<Who, Spot>((scene.cast ?? []).map((c) => [c.who, c.at]));
  if (t.on === 'enter' && t.from !== undefined) {
    const at = room.arrival(t.from);
    if (!at) throw new Error(`${scene.id}: ${scene.room} has no door from ${t.from}`);
    ev.push(`dir_set(0, 0, ${at.angle ?? 0}, 0, ${at.x}, 0, ${at.z});  // her, in from ${t.from}`);
    where.set('her', at);
  }

  const entity = (who: Who) => (who === 'her' ? 'set_entity(ENT_PLAYER, 0);' : `set_entity(ENT_ENEMY, ${slotOf(who)});`);
  const waitDone = ['do {', '    yield();', `} while (ck(FG_ROOM, ${DONE_BIT}, 1));`];
  const animBlock = (who: Who, ops: string[]) => [entity(who), 'anim_begin();', ...ops.map((o) => `    ${o}`), who === 'her' ? 'anim_end_release();' : 'anim_end();'];
  let talk = 0;
  for (const b of scene.beats) {
    switch (b.kind) {
      case 'cut':
        ev.push(`cutnext(${b.camera});`);
        break;
      case 'place':
        where.set(b.who, b.at);
        ev.push(
          b.who === 'her'
            ? `dir_set(0, 0, ${b.at.angle ?? 0}, 0, ${b.at.x}, 0, ${b.at.z});  // her`
            : `pos_set(${slotOf(b.who)}, 0, ${b.at.angle ?? 0}, 0, ${b.at.x}, 0, ${b.at.z});  // ${PEOPLE[b.who].name}`,
        );
        break;
      case 'walk': {
        const from = where.get(b.who);
        if (from && room.floor && !clearWalk(room.floor, from, b.to)) throw new Error(`${scene.id}: ${b.who === 'her' ? 'her' : PEOPLE[b.who].name + "'s"} walk from (${from.x}, ${from.z}) to (${b.to.x}, ${b.to.z}) leaves the floor or meets a wall`);
        where.set(b.who, b.to);
        // anim_pose behaviour 2 walks to the point, 3 runs (npc_scd_02, player_scd_behavior_02).
        ev.push(`// ${b.who === 'her' ? 'She' : PEOPLE[b.who].name} ${b.run ? 'runs' : 'walks'} to (${b.to.x}, ${b.to.z}).`, ...animBlock(b.who, [`anim_pose(${b.run ? 3 : 2}, ${b.to.x}, ${b.to.z}, ${DONE_BIT});`]), ...waitDone);
        break;
      }
      case 'face':
        ev.push(...animBlock(b.who, [`anim_pose(6, ${b.to.x}, ${b.to.z}, ${DONE_BIT});`]), ...waitDone);
        break;
      case 'anim':
        ev.push(...animBlock(b.who, [`anim_play(${b.anim}, ${DONE_BIT}, 0);`, ...(b.loop ? ['anim_flags(0, 16);'] : [])]), ...(b.loop ? [] : waitDone));
        break;
      case 'say': {
        const id = room.say(b.text);
        // Someone in the room gestures as they talk; a voice on the phone just talks.
        const talker = b.by !== 'her' && slot.has(b.by) ? b.by : undefined;
        if (talker) ev.push(...animBlock(talker, [`anim_play(${TALK[talk++ % TALK.length]}, 63, 0);`, 'anim_flags(0, 16);']));
        ev.push(`message(${id}, 0, 0);  // ${b.by === 'her' ? 'her' : PEOPLE[b.by].name}`, 'wait_voice();');
        if (talker) ev.push(...animBlock(talker, [`anim_play(${IDLE}, 63, 0);`, 'anim_flags(0, 16);']));
        break;
      }
      case 'wait':
        ev.push(`sleep(${b.frames});`);
        break;
      case 'fade':
        // The special room light (SCD 0x1C) as ROOM1000 fades for Rebecca's
        // treatment: a subtractive rect stepped 256 a frame. To black, hold
        // it; back, let it run below 0, where the engine stops drawing it.
        ev.push(...(b.to === 'black' ? ['timer_setup(2, 0, 1, 7, 0);', 'sleep(120);', 'timer_setup(2, 0, 0, 7, 0);'] : ['timer_setup(2, 0, 255, 7, 0);', 'sleep(150);', 'timer_setup(2, 0, 0, 7, 0);']));
        break;
      case 'shake':
        // FG_STATUS 62: g_main_state_flags2 bit 1, the screen shake.
        ev.push(`set(FG_STATUS, 62, ${b.on ? 0 : 1});`);
        break;
      case 'gone':
        // Out of the room: stood far outside every camera. Clearing the slot's
        // status instead leaves g_enemy_count one too high, and the next shot
        // reads a slot that isn't there (apply_weapon_damage).
        ev.push(`pos_set(${slotOf(b.who)}, 0, 0, 0, ${OUT_OF_SIGHT}, 0, ${OUT_OF_SIGHT});  // ${PEOPLE[b.who].name} leaves`);
        break;
      case 'give': {
        // As Barry hands Jill the radio (ROOM4080): her controls on for the
        // pickup screen, which the engine opens as if she had pressed action
        // at the item, then off again.
        const id = room.itemAction(b.item);
        if (id === undefined) throw new Error(`${scene.id}: no ${b.item} lies in ${scene.room}`);
        ev.push(`// She takes the ${b.item}.`, 'scd {', '    set(FG_6, 23, 0);', `    give_item(${id}, 4, 129);`, '    return;', '}', 'sleep(1);', 'set(FG_6, 23, 1);');
        break;
      }
      case 'scd':
        ev.push(...b.lines);
        break;
      default: {
        const never: never = b;
        throw new Error(`unknown beat ${JSON.stringify(never)}`);
      }
    }
  }

  // The end: the people still here back to their idle, her back to standing,
  // then the bars off, the camera free to follow her and her controls back.
  const staying = (scene.cast ?? []).filter((c) => !c.after?.pose && !scene.beats.some((b) => b.kind === 'gone' && b.who === c.who));
  for (const c of staying) ev.push(...animBlock(c.who, ['anim_idle();']), `eml_state(0, ${slotOf(c.who)}, 2, 9, 0);`);
  ev.push(
    'set_entity(ENT_PLAYER, 0);',
    'anim_begin();',
    '    anim_idle();',
    'anim_end_release();',
    'scd {',
    '    set(FG_STATUS, 15, 1);',
    '    cut_auto(0);',
    '    set(FG_6, 23, 0);',
    '    return;',
    '}',
    'return;',
  );
  return { init, main, event: ev };
}
