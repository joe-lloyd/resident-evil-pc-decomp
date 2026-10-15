// Write the scripts and messages of the rooms built with blender/kit.py from
// what their scenes record (renders/room.json: doors, things to check, the
// thought on first coming in). A door from A to B lands her where B's door
// back to A says to arrive; the hand-written rooms give their arrivals in
// BUILT_ARRIVALS. A door to a room not rendered yet is left out.
//
//   node tools/rebecca/day/scripts.ts
//
// Writes day/<slug>/room.c and room.msg.txt for every kit room. Edit the
// scene, not these files.
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { dayRooms } from './rooms.ts';
import type { DayRoom } from './room.ts';
import { BOOKS, DOCUMENTS, ITEM_FLAG_BASE } from '../files/documents.ts';
import { foeLines, KILL_FLAGS, type Floor } from './foes.ts';
import { ITEM_FLAGS, SUPPLIES, supplyLines, supplyModels } from './supplies.ts';
import { mapLines, mapModels } from '../maps/pickups.ts';
import { KEY_ITEM_FLAGS, KEY_ITEMS, keyItemLines, keyItemModels, sameModel, type ItemSpot } from '../items/items.ts';
import { BAG_SLOTS, GEAR, LOSS_BIT, LOSS_LINE, LOSS_ROOM } from './gear.ts';
import { EVENT_FLAGS, EVENTS, eventsIn, giveModels, GIVE_FLAGS, itemModelSlots, keyItem } from './events.ts';
import { day } from '../plan/day.ts';

const here = path.dirname(fileURLToPath(import.meta.url));

type Zone = { x0: number; z0: number; x1: number; z1: number };
type Arrive = { x: number; z: number; angle: number };
interface KitDoor {
  to: string;
  zone: Zone;
  arrive: Arrive;
  /** False when the scene asks for a door that opens, such as stairs between two outdoor rooms. */
  walk?: boolean;
}
interface KitJson {
  doors?: KitDoor[];
  checks?: { zone: Zone; text: string }[];
  /** A save room's typewriter and item box, and where the box's lid goes (kit.Room.save_room). */
  saves?: { typewriter: Zone; box: Zone; lid: { x: number; y: number; z: number; angle: number } } | null;
  entry?: string | null;
  bounds: Zone;
  walls: Floor['walls'];
  voids?: Zone[];
  items?: ItemSpot[];
  spots?: { step: string; zone: Zone }[];
}

/** Where she stands in a hand-written room on arriving from a kit room, by that room's slug. */
const BUILT_ARRIVALS: Record<string, Record<string, Arrive>> = {
  // The yard (x 2-18 m, y 2-12.2 m): in from the forestry road on the truck's
  // tyre tracks at the west edge, facing east; in from the woods at the
  // north-east, where the drag marks go into the trees, facing west.
  yard: {
    road: { x: 6120, z: 18360, angle: 0 },
    woods: { x: 27200, z: 10880, angle: 2048 },
  },
  // The bridge: on its far bank (y 15-18 m) from the gondola station, facing
  // back over the bridge; on its near bank from the flume's ride down.
  bridge: {
    platform: { x: 10200, z: 27710, angle: 1024 },
    flume: { x: 14450, z: 6800, angle: 3072 },
  },
};

/** Rooms of the original game a kit room leads into, and where she stands on arriving. */
const GAME_ROOMS: Record<string, { stage: number; room: number; arrive: Arrive }> = {
  // The mansion's 1F save room, up through a trapdoor in its floor: standing on
  // it (saveroom/hatch.py draws it there), facing Chris across the room.
  save: { stage: 0, room: 0, arrive: { x: 5200, z: 5600, angle: 443 } },
};

/**
 * The hand-written rooms' doors into kit rooms: written into their room.c
 * between the KIT DOORS markers, with the kit room's arrival. Aot ids above
 * the room's own.
 */
const BUILT_DOORS: Record<string, { to: string; id: number; zone: Zone; note: string }[]> = {
  yard: [
    { to: 'road', id: 11, zone: { x0: 3400, z0: 16320, x1: 4420, z1: 20400 }, note: 'West along the tyre tracks to the forestry road.' },
    { to: 'woods', id: 12, zone: { x0: 29580, z0: 7650, x1: 30600, z1: 12750 }, note: 'East after the drag marks into the woods.' },
  ],
  bridge: [
    { to: 'platform', id: 5, zone: { x0: 6800, z0: 29580, x1: 13600, z1: 30600 }, note: "On down to the gondola station, from the far bank's south edge." },
  ],
};

/**
 * RE1's door animations (DoorSystem.cpp's g_doorFileNameTable, indexed by
 * `type`), each with the direction, sound and handle bytes the shipped rooms
 * pair with it. Stairs, ladders and lifts take direction 0 going up and 1
 * coming down, as the main hall's stairs do.
 */
const ANIMS = {
  /** The walk down a dark path between outdoor rooms (PathWalk.cpp). */
  walk: { type: 48, variant: 0, sfx: 15, handle: 4 },
  /** door00: the mansion's panelled door. */
  mansion: { type: 0, variant: 0, sfx: 0, handle: 4 },
  /** door07: a plank door with a Z brace. */
  plank: { type: 7, variant: 1, sfx: 0, handle: 1 },
  /** door15: a worn panel door. */
  panel: { type: 33, variant: 1, sfx: 0, handle: 1 },
  /** door08: a rusty riveted iron door. */
  rivets: { type: 8, variant: 0, sfx: 1, handle: 0 },
  /** door11: a rusty iron door with an X brace. */
  brace: { type: 11, variant: 0, sfx: 1, handle: 3 },
  /** door10: a grey steel door with a vent. */
  vent: { type: 10, variant: 0, sfx: 1, handle: 8 },
  /** door12: a grey steel panel door. */
  steel: { type: 12, variant: 0, sfx: 1, handle: 7 },
  /** lad01: a ladder, up and down. */
  ladderUp: { type: 27, variant: 0, sfx: 11, handle: 64 },
  ladderDown: { type: 27, variant: 1, sfx: 11, handle: 64 },
  /** ele02: an industrial lift, up and down. */
  liftUp: { type: 20, variant: 0, sfx: 14, handle: 64 },
  liftDown: { type: 20, variant: 1, sfx: 14, handle: 64 },
} as const;
type Anim = keyof typeof ANIMS;

/**
 * Which animation each door that opens plays, by the rooms it joins (either
 * way round). The hand-written rooms (the cabin, the shed, the yard) set
 * theirs in their own room.c.
 */
const DOOR_STYLE: Record<string, Anim> = {
  'booth|platform': 'panel',
  'bunkhouse|camp-yard': 'plank',
  'camp-yard|mess': 'plank',
  'camp-yard|office': 'panel',
  'camp-yard|workshop': 'brace',
  'camp-yard|sawmill': 'plank',
  'pond|sawmill': 'plank',
  'car|platform': 'steel',
  'generator|washout': 'brace',
  'generator|switch': 'brace',
  'line-track|switch': 'brace',
  'tower-foot|tower-stairs': 'plank',
  'cottage|east-path': 'panel',
  'quarry|quarry-office': 'rivets',
  'mine-entrance|tunnel': 'rivets',
  'junction|tunnel': 'rivets',
  'gallery|junction': 'rivets',
  'junction|mine-lift': 'rivets',
  'mine-office|tunnel': 'plank',
  'summit-trail|weather': 'steel',
  'lower-station|lower-yard': 'vent',
  'creek|lodge': 'panel',
  'back-garden|garden-shed': 'plank',
  'back-garden|cellar': 'plank',
  'cellar|wine': 'panel',
  'cellar|crawl': 'plank',
};
/** The ways up and down, by the direction she goes. */
const CLIMB: Record<string, Anim> = {
  'tower-stairs>tower-top': 'ladderUp',
  'tower-top>tower-stairs': 'ladderDown',
  'car>pylon': 'ladderDown',
  'pylon>car': 'ladderUp',
  'pylon>valley-path': 'ladderDown',
  'valley-path>pylon': 'ladderUp',
  'crawl>save': 'ladderUp',
  'mine-lift>summit-trail': 'liftUp',
  'summit-trail>mine-lift': 'liftDown',
};

/**
 * The plan's steps that open a way by using one key item on its lock. The
 * rest open by a scripted event (the blast, the pump, the gondola) and stay
 * open until those are written.
 */
const ITEM_LOCKS = new Set(['office-key', 'cut-depot', 'safe', 'cut-chain', 'tower-door', 'switch-key', 'quarry-key', 'pry-lodge', 'open-gate', 'bulkhead']);

/**
 * The key item that opens the way from one room to the next, by the plan:
 * the item the link's gating step gives (the office key opens the office),
 * or the one that step needs (cutting the depot's padlock needs the bolt
 * cutters).
 */
function lockItem(from: string, to: string): number | undefined {
  const opens = day.links.find((l) => l.from === from && l.to === to)?.opens;
  if (!opens || !ITEM_LOCKS.has(opens)) return undefined;
  const step = day.steps.find((s) => s.id === opens);
  return (KEY_ITEMS.find((k) => k.step === opens) ?? KEY_ITEMS.find((k) => step?.needs.includes(k.step)))?.id;
}

/**
 * The lock bytes of a door the plan locks with a key item, on the side she
 * comes to it from: the item, and 0x80 with a lock flag of its own
 * (g_LocksFlags 40-59; door_try_enter raises it once she has used the
 * item, so it stays open). The yard's shed door has 60.
 */
export const LOCK_FLAGS = Array.from({ length: 20 }, (_, i) => 40 + i);
const locks = new Map<string, { item: number; flag: number }>();
function lockFor(from: string, to: string): { item: number; flag: number } | undefined {
  const item = lockItem(from, to);
  if (item === undefined) return undefined;
  const key = `${from}>${to}`;
  if (!locks.has(key)) {
    const flag = LOCK_FLAGS[locks.size];
    if (flag === undefined) throw new Error(`no lock flag left for ${key}`);
    locks.set(key, { item, flag });
  }
  return locks.get(key);
}

/** The door record's animation and lock bytes for a door from one room to another. */
function doorAnim(from: string, to: string, walk: boolean): string {
  const a = ANIMS[walk ? 'walk' : (CLIMB[`${from}>${to}`] ?? DOOR_STYLE[[from, to].sort().join('|')] ?? 'mansion')];
  const lock = lockFor(from, to);
  return `${a.variant}, ${a.sfx}, ${a.type}, ${a.handle}, ${lock ? 0x80 | lock.flag : 0}`;
}

/** The door record's key operand: the plan's key item, or UNLOCKED. */
const doorKey = (from: string, to: string) => {
  const lock = lockFor(from, to);
  return lock ? String(lock.item) : 'UNLOCKED';
};

/**
 * Common flags for "she has been here", one per kit room with a first
 * thought; the built rooms use 200-206 and the trail 159. 207-255 hold 49,
 * and there are more kit rooms than that, so the rest come from 109-129, a
 * run no shipped room script and no engine flag uses (the events have
 * 130-158, day/events.ts).
 */
const ENTRY_FLAGS = [...Array.from({ length: 49 }, (_, i) => 207 + i), ...Array.from({ length: 21 }, (_, i) => 109 + i)];
/**
 * How a door fires: a walk on touch; a door that opens on the action button
 * while she stands in its zone (0x40). Without 0x40 the engine tests the
 * point 600 units in front of her, which is past a zone against a wall when
 * she walks right up to the door (check_action_object).
 */
const TOUCH = 1;
const OPEN = 0x80 | 0x40 | 1;
/** Message text: lines this many characters at most, three lines to a page. */
const LINE = 26;
const PAGE_LINES = 3;

/** The hand-written rooms indoors; the kit rooms say so themselves. */
const BUILT_INSIDE = new Set(['lookout', 'shed']);
const isInside = (r: DayRoom) => ('inside' in r ? r.inside : BUILT_INSIDE.has(r.slug));

const roomName = (r: Pick<DayRoom, 'stage' | 'room'>) => `ROOM_${r.stage + 1}${r.room.toString(16).toUpperCase().padStart(2, '0')}`;

function readKit(slug: string): KitJson | undefined {
  const file = path.join(here, slug, 'renders', 'room.json');
  if (!existsSync(file)) return undefined;
  const json = JSON.parse(readFileSync(file, 'utf8')) as KitJson;
  return json.doors ? json : undefined;
}

/** Wrap a page's words to LINE characters, and spill past PAGE_LINES onto more pages. */
export function pages(text: string): string[] {
  const out: string[] = [];
  for (const para of text.split('\n')) {
    const lines: string[] = [];
    let line = '';
    for (const word of para.split(/\s+/).filter(Boolean)) {
      if (line && (line + ' ' + word).length > LINE) {
        lines.push(line);
        line = word;
      } else line = line ? `${line} ${word}` : word;
    }
    if (line) lines.push(line);
    // Pages of PAGE_LINES; a last page of one line borrows one from the page before.
    const sizes: number[] = [];
    for (let left = lines.length; left > 0; left -= PAGE_LINES) sizes.push(Math.min(PAGE_LINES, left));
    if (sizes.length > 1 && sizes.at(-1) === 1 && sizes.at(-2) === PAGE_LINES) {
      sizes[sizes.length - 2]! -= 1;
      sizes[sizes.length - 1]! += 1;
    }
    let at = 0;
    for (const n of sizes) {
      out.push(lines.slice(at, at + n).join('\\n'));
      at += n;
    }
  }
  return out;
}

const message = (n: number, text: string) => `${n}: ${pages(text).map((p) => `\\n${p}`).join('\\p{0}')}`;

const size = (z: Zone) => `${z.x0}, ${z.z0}, ${z.x1 - z.x0}, ${z.z1 - z.z0}`;

function main(): void {
  const bySlug = new Map(dayRooms.map((r) => [r.slug, r]));
  const kits = new Map(dayRooms.flatMap((r) => {
    const k = readKit(r.slug);
    return k ? [[r.slug, k] as const] : [];
  }));
  const flags = [...ENTRY_FLAGS];
  const killFlags = [...KILL_FLAGS];
  const itemFlags = [...ITEM_FLAGS];
  const keyFlags = [...KEY_ITEM_FLAGS];
  for (const [slug, kit] of kits) {
    const spec = bySlug.get(slug)!;
    const lines: string[] = [
      `// ${slug} (${roomName(spec).slice(5)}), written by day/scripts.ts from day/${slug}/scene.py: edit the scene, not this file.`,
      '// init procedure 0',
    ];
    let id = 0;
    const msgs = [kit.entry ?? '...'];
    /** Add a room message and return its id (0x80 + index). */
    const say = (text: string) => 128 + msgs.push(text) - 1;
    const events = eventsIn(slug).filter((e) => kit.spots?.some((sp) => sp.step === e.step));
    const spotOf = (step: string) => kit.spots!.find((sp) => sp.step === step)!.zone;
    /** The door an event opens, to write again the moment it happens. */
    const reopen = new Map<string, string>();
    for (const d of kit.doors ?? []) {
      const game = GAME_ROOMS[d.to];
      const target = bySlug.get(d.to) ?? (game && { slug: d.to, stage: game.stage, room: game.room });
      const back = kits.get(d.to)?.doors?.find((b) => b.to === slug)?.arrive ?? BUILT_ARRIVALS[d.to]?.[slug] ?? game?.arrive;
      if (!target || !back) {
        lines.push(`// To ${d.to}: not built yet.`);
        continue;
      }
      // Between two outdoor rooms she walks the dark path and leaves on touch,
      // unless the scene asks for a door that opens; into or out of a
      // building a door opens, with the action button.
      const walk = d.walk !== false && !isInside(spec) && !game && !isInside(target as DayRoom);
      lines.push(`// To ${d.to}.`);
      // A locked way opens with the action button even between outdoor rooms.
      const touch = walk && !lockFor(slug, d.to);
      const door = `door_aot_set(${id}, ${size(d.zone)}, ${doorAnim(slug, d.to, walk)}, ${roomName(target)}, ${back.x}, 0, ${back.z}, ${back.angle}, ${doorKey(slug, d.to)}, ${touch ? TOUCH : OPEN});`;
      // A way an event opens, here or from another room: what blocks it until the event's flag is set.
      const gate = EVENTS.find((e) => e.opens?.to === d.to && (e.opens.from ?? e.room) === slug && kits.get(e.room)?.spots?.some((sp) => sp.step === e.step));
      if (gate?.opens) {
        const f = EVENT_FLAGS.get(gate.step)!;
        lines.push(`if (ck(FG_COMMON, ${f}, 1)) {`, `    aot_set(${id}, ${size(d.zone)}, SCE_MESSAGE, 129, ${say(gate.opens.blocked)}, 0, 255, 0, 0, 0);`, '} else {', `    ${door}`, '}');
        if (gate.room === slug) reopen.set(gate.step, door);
      } else {
        lines.push(door);
      }
      id++;
    }
    // The typewriter and the item box, as the mansion's save room has them
    // (ROOM1000): the engine runs both, ink ribbon and all. The box's lid is
    // object model 0, RE1's own (day/room.ts), which the engine swings open.
    if (kit.saves) {
      const { lid } = kit.saves;
      lines.push('// The typewriter and the item box, its lid on the body the scene paints.');
      lines.push(`aot_set(${id++}, ${size(kit.saves.typewriter)}, SCE_TYPEWRITER, 129, 0, 0, 0, 0, 0, 0);`);
      lines.push(`aot_set(${id++}, ${size(kit.saves.box)}, SCE_ITEMBOX, 129, 0, 0, 0, 0, 0, 0);`);
      lines.push(`obj(0, 17, 255, ${lid.x}, ${lid.y}, ${lid.z}, ${lid.angle}, ${Array(16).fill(0).join(', ')});`);
    }
    for (const c of kit.checks ?? []) {
      const doc = DOCUMENTS.find((d) => d.room === slug && c.text.startsWith(d.check));
      if (doc) {
        // A document is a file she picks up and reads (files/documents.ts):
        // item 0x5F + its slot, on the room's empty model slot (the last,
        // itemModelSlots), kept taken by its room-item flag.
        const flag = ITEM_FLAG_BASE + BOOKS.indexOf(doc.id as (typeof BOOKS)[number]);
        lines.push(`// ${doc.title}, a file.`);
        lines.push(`if (ck(FG_ITEM, ${flag}, 0)) {`);
        lines.push(`    item_aot_set(${id++}, ${size(c.zone)}, ${0x5f + doc.slot}, 1, ${itemModelSlots(spec.itemModels ?? [], kit.items ?? [], slug).length - 1}, 255, 0, 0, 0, 0, 0, 0, 0, 0, ${flag}, 129, 0, 0);`);
        lines.push('}');
        continue;
      }
      lines.push(`aot_set(${id++}, ${size(c.zone)}, SCE_MESSAGE, 129, ${128 + msgs.length}, 0, 255, 0, 0, 0);`);
      msgs.push(c.text);
    }
    const floor: Floor = { bounds: kit.bounds, walls: kit.walls, voids: kit.voids, doors: (kit.doors ?? []).map((d) => ({ zone: d.zone, arrive: d.arrive })) };
    lines.push(...foeLines(slug, floor, killFlags));
    lines.push(...supplyLines(slug, floor, itemFlags, id));
    id += SUPPLIES[slug]?.length ?? 0;
    // The room's map, if the plan finds one here: its model after the
    // supplies' (rooms.ts), its zone clear of the room's others.
    const taken = lines.flatMap((l) => {
      const m = /(?:item_)?aot_set\(\d+, (\d+), (\d+), (\d+), (\d+),/.exec(l);
      return m ? [{ x0: +m[1]!, z0: +m[2]!, x1: +m[1]! + +m[3]!, z1: +m[2]! + +m[4]! }] : [];
    });
    taken.push(...(kit.spots ?? []).map((sp) => sp.zone), ...(kit.items ?? []).map((it) => ({ x0: it.x - 900, z0: it.z - 900, x1: it.x + 900, z1: it.z + 900 })));
    const mapLine = mapLines(slug, floor, taken, id, supplyModels(slug).length);
    lines.push(...mapLine);
    if (mapLine.length) id++;
    // The key items: after the supplies and the map in the room's item models (room.ts).
    const specSlots = supplyModels(slug).length + mapModels(slug).length;
    lines.push(...keyItemLines(kit.items ?? [], keyFlags, id, specSlots));
    id += kit.items?.length ?? 0;
    // The events (day/events.ts): their zones now, their working in main.
    const main: string[] = [];
    // FG_ROOM bits: an action pressed, or an item used and its line still to
    // come. Word 0 only, cleared when the room loads: the engine clears bits
    // 32-63 every frame (room_state_reset), and uses 0 and 29-31 itself.
    let bit = 12;
    const giveSlot0 = specSlots + keyItemModels(kit.items ?? []).length;
    for (const e of events) {
      const f = EVENT_FLAGS.get(e.step)!;
      const zone = size(spotOf(e.step));
      const [trigger, msgId] = [id++, id++];
      const look = say(e.look);
      const after = say(e.after);
      const done = say(e.done);
      const need = (e.needs ?? []).map((n) => `ck(FG_COMMON, ${EVENT_FLAGS.get(n)}, 0)`).join(' && ');
      const use = e.use ? keyItem(e.use).id : undefined;
      lines.push(`// ${e.step} (day/events.ts), FG_COMMON ${f} once it has happened.`, `if (ck(FG_COMMON, ${f}, 1)) {`);
      // An item can be used here only once what it needs has happened: the
      // engine takes some items out of her case as she uses them (the crank,
      // the jerrycan, the fuses), and a use that cannot work would lose them.
      const arm = use === undefined ? '' : `aot_set(${trigger}, ${zone}, SCE_USEITEM, 1, 9, 0, ${use - 27}, 0, 1, 0);   // the ${keyItem(e.use!).name.toLowerCase()} can be used here`;
      if (use !== undefined) {
        lines.push(...(need ? [`    if (${need}) {`, `        ${arm}`, '    }'] : [`    ${arm}`]));
        lines.push(`    aot_set(${msgId}, ${zone}, SCE_MESSAGE, 129, ${look}, 0, 255, 0, 0, 0);`);
      } else {
        lines.push(`    aot_set(${trigger}, ${zone}, SCE_USEITEM, 129, 4, 0, ${bit}, 0, 1, 0);   // the action button here raises FG_ROOM ${bit}`);
      }
      // Its line after, once it has happened. Where it leaves an item, only
      // once that is taken: the line's zone is the pickup's, and the action
      // button takes the first of the two in the room's table.
      const afterLine = `aot_set(${msgId}, ${zone}, SCE_MESSAGE, 129, ${after}, 0, 255, 0, 0, 0);`;
      const giveFlag = e.gives ? GIVE_FLAGS.get(e.gives)! : undefined;
      lines.push('} else {', ...(giveFlag === undefined ? [`    ${afterLine}`] : [`    if (ck(FG_ITEM, ${giveFlag}, 1)) {`, `        ${afterLine}`, '    }']), '}');
      // What happens: the flag, the way it opens, its spot's line after, then hers.
      const happen = [
        `set(FG_COMMON, ${f}, 0);`,
        ...(reopen.has(e.step) ? [reopen.get(e.step)!] : []),
        ...(giveFlag === undefined ? [afterLine] : []),
        `message(${done}, 255, 0);`,
      ];
      if (use !== undefined) {
        // The status screen is still closing on the frame she uses it, and a
        // message opened then is dropped: the line waits a second (setw
        // restarts the seconds counter, state word 4), as the yard's winch does.
        const pending = bit++;
        const armed = need ? bit++ : 0;
        main.push(
          `if (ck(FG_COMMON, ${f}, 1)) {`,
          // What it needs may happen while she is in the room (the fuse, then the key).
          ...(need ? [`    if (${need} && ck(FG_ROOM, ${armed}, 1)) {`, `        set(FG_ROOM, ${armed}, 0);`, `        ${arm}`, '    }'] : []),
          `    if (ck(FG_ROOM, ${pending}, 1) && testitem(${use})) {`,
          `        set(FG_ROOM, ${pending}, 0);`,
          '        setw(4, 0, 0);',
          '    }',
          `    if (ck(FG_ROOM, ${pending}, 0) && cmpw(0, 4, 1, 0)) {`,
          // Using a crank puts her in the crank pose; this stands her back
          // up. It holds the script until the pose is done, which runs the
          // block again from the top: so before the pending flag clears.
          ...(use === 0x1e ? ['        sys_multi(7);'] : []),
          `        set(FG_ROOM, ${pending}, 1);`,
          // remove_item stops the script when she no longer has it.
          `        if (item_ck(${use})) {`,
          `            remove_item(${use});`,
          '        }',
          ...happen.map((l) => `        ${l}`),
          '    }',
          '}',
        );
      } else {
        const pressed = bit++;
        main.push(
          `if (ck(FG_COMMON, ${f}, 1) && ck(FG_ROOM, ${pressed}, 0)) {`,
          `    set(FG_ROOM, ${pressed}, 1);`,
          ...(need ? [`    if (${need}) {`, ...happen.map((l) => `        ${l}`), '    } else {', `        message(${look}, 255, 0);`, '    }'] : happen.map((l) => `    ${l}`)),
          '}',
        );
      }
      // What it leaves here to pick up, once it has happened: in the slot of
      // the spot's line, which it replaces until it is taken.
      if (e.gives) {
        const k = keyItem(e.gives);
        const gf = GIVE_FLAGS.get(e.gives)!;
        const slot = giveSlot0 + giveModels(slug).findIndex((m) => sameModel(m, k.model));
        const z = spotOf(e.step);
        const [x, zz] = [Math.round((z.x0 + z.x1) / 2), Math.round((z.z0 + z.z1) / 2)];
        const word = (n: number) => `${n & 0xff}, ${(n >> 8) & 0xff}`;
        const pick = `item_aot_set(${msgId}, ${zone}, ${k.id}, 1, ${slot}, 255, ${word(x)}, 0, 0, ${word(zz)}, 0, 0, ${gf}, 129, 0, 0);`;
        lines.push(`if (ck(FG_COMMON, ${f}, 0) && ck(FG_ITEM, ${gf}, 0)) {  // ${k.name.toLowerCase()}, left here`, `    ${pick}`, '}');
        main.push(`if (ck(FG_COMMON, ${f}, 0) && ck(FG_ITEM, ${gf}, 0) && ck(FG_ROOM, ${bit}, 1)) {`, `    set(FG_ROOM, ${bit}, 0);`, `    ${pick}`, '}');
        bit++;
      }
    }
    // RE1's room action table has 24 slots.
    if (id > 24) throw new Error(`${slug}: ${id} room actions, the table has 24`);
    if (bit > 29) throw new Error(`${slug}: its events need FG_ROOM bits up to ${bit - 1}, past the engine's from 29`);
    lines.push('return;', '', '// main procedure 0');
    const flag = kit.entry ? flags.shift() : undefined;
    if (kit.entry && flag === undefined) throw new Error(`${slug}: no flag left for its first thought`);
    if (flag !== undefined && slug === LOSS_ROOM) {
      // The mine takes her gear (gear.ts): the room's thought runs on into the loss.
      msgs[0] = `${msgs[0]}\n${LOSS_LINE}`;
      // An if block holds 255 bytes at most, too few for every try at every
      // item, so the first visit raises FG_ROOM LOSS_BIT and each try is a
      // block of its own while it is up (room flags clear when a room loads).
      lines.push(
        `if (ck(FG_COMMON, ${flag}, 1)) {`, `    set(FG_COMMON, ${flag}, 0);`, `    set(FG_ROOM, ${LOSS_BIT}, 0);`, '    sys_multi(0);', '}',
        ...GEAR.flatMap((g) => Array.from({ length: BAG_SLOTS }, () => [`if (ck(FG_ROOM, ${LOSS_BIT}, 0) && item_ck(${g})) {`, `    remove_item(${g});`, '}']).flat()),
        `if (ck(FG_ROOM, ${LOSS_BIT}, 0)) {`, `    set(FG_ROOM, ${LOSS_BIT}, 1);`, '    message(128, 255, 0);', '}',
      );
    } else if (flag !== undefined) {
      lines.push(`if (ck(FG_COMMON, ${flag}, 1)) {`, `    set(FG_COMMON, ${flag}, 0);`, '    message(128, 255, 0);', '}');
    }
    lines.push(...main, 'return;', '');
    writeFileSync(path.join(here, slug, 'room.c'), lines.join('\n'));
    writeFileSync(path.join(here, slug, 'room.msg.txt'), msgs.map((m, i) => message(i, m)).join('\n') + '\n');
    console.log(`${slug}: ${kit.doors?.length ?? 0} doors, ${kit.checks?.length ?? 0} checks${kit.saves ? ', a typewriter and a box' : ''}`);
  }
  // The hand-written rooms' ways into the kit rooms.
  for (const [slug, doors] of Object.entries(BUILT_DOORS)) {
    const file = path.join(here, slug, 'room.c');
    const text = readFileSync(file, 'utf8');
    const begin = '// KIT DOORS (day/scripts.ts writes these)';
    const end = '// END KIT DOORS';
    const lines = [begin];
    for (const d of doors) {
      const target = bySlug.get(d.to)!;
      const arrive = kits.get(d.to)?.doors?.find((b) => b.to === slug)?.arrive;
      if (!arrive) {
        lines.push(`// To ${d.to}: not built yet.`);
        continue;
      }
      const walk = !isInside(bySlug.get(slug)!) && !isInside(target);
      lines.push(`// ${d.note}`);
      lines.push(`door_aot_set(${d.id}, ${size(d.zone)}, ${doorAnim(slug, d.to, walk)}, ${roomName(target)}, ${arrive.x}, 0, ${arrive.z}, ${arrive.angle}, UNLOCKED, ${walk ? TOUCH : OPEN});`);
    }
    lines.push(end);
    const at = text.indexOf(begin);
    const next = at >= 0 ? text.slice(0, at) + lines.join('\n') + text.slice(text.indexOf(end) + end.length) : text.replace('\nreturn;\n', `\n${lines.join('\n')}\nreturn;\n`);
    writeFileSync(file, next);
    console.log(`${slug}: ways into the kit rooms written`);
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main();
