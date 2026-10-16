// The puzzles of her day's kit rooms that are worked rather than unlocked:
// an item used at a spot (the jerrycan at the diesel tank, the dynamite on
// the rockfall), or a thing worked with the action button once what it
// needs is done (the pump once the generator runs). Each sets a common flag
// of its own when it happens; a way it opens shows what blocks it until
// then. The scenes record where each is (kit.Room.spot); scripts.ts writes
// them into the rooms' scripts from here.
//
// The ways a key item unlocks are scripts.ts's locks. The yard's winch and
// dog, being a hand-written room's, are in its own script.
import { KEY_ITEMS, keyItemModels, sameModel, type ItemSpot, type KeyItem, type PickupModel } from '../items/items.ts';

export interface RoomEvent {
  /** The plan's step it does, or one of these puzzles' own (fit-cog). Its flag is set once it happens. */
  readonly step: string;
  readonly room: string;
  /** The key item (by its plan step) she uses here; without, the action button works it. */
  readonly use?: string;
  /** Other events that must have happened first. */
  readonly needs?: readonly string[];
  /** A key item (by its plan step) left here to pick up once it has happened. */
  readonly gives?: string;
  /** Examining it before. For a worked thing, also what she says trying it before what it needs is done. */
  readonly look: string;
  /** As it happens. */
  readonly done: string;
  /** Examining it after. */
  readonly after: string;
  /** The way it opens, from this room unless `from` names another, and what she sees there until then. */
  readonly opens?: { readonly from?: string; readonly to: string; readonly blocked: string };
}

export const EVENTS: readonly RoomEvent[] = [
  {
    step: 'fuel', room: 'depot', use: 'jerrycan', gives: 'fuel',
    look: "Diesel, dripping from the nozzle. The hose reel is chained, and padlocked.\nThe hand pump still works. I need something to carry it in.",
    done: "I fill the jerrycan at the hand pump.\nIt's heavy now.",
    after: 'The diesel tank. The hand pump drips.',
  },
  {
    step: 'generator-on', room: 'generator', use: 'fuel',
    look: "The generator's panel. The fuel gauge is right down on E.\nIt ran itself dry.",
    done: 'Diesel in. It coughs, catches... and runs.\nThe lights are coming on.',
    after: 'The generator thuds away. The whole hut shakes.',
  },
  {
    step: 'line-on', room: 'switch', needs: ['generator-on'],
    look: "The breakers. SKYWAY LINE, STATION 3, MINE. Every one of them is down. OFF.\nThere's no power to switch on.",
    done: 'I push the breakers up, one by one.\nThe line starts to hum.',
    after: "The breakers are up. The line's live.",
  },
  {
    step: 'line-gate', room: 'line-track', needs: ['line-on'],
    look: "LINE TRACK. STAFF ONLY. The gondola station's through the gate.\nIts lock is electric, and dead.",
    done: 'The lock buzzes. The gate swings open.',
    after: 'The gate to the gondola station, open.',
    opens: { to: 'platform', blocked: 'The gate is locked.' },
  },
  {
    step: 'blast', room: 'mine-entrance', use: 'dynamite',
    look: "The roof's been brought down across the mouth. On purpose:\nthere's a blasting wire running out of the rocks.",
    done: 'I wedge the dynamite into the rockfall, light it and run.\nThe whole hillside jumps. The way is open.',
    after: 'The mine mouth, blasted clear.',
    opens: { to: 'tunnel', blocked: "The gap's too tight for me,\nand the rocks over it are loose." },
  },
  {
    step: 'drain', room: 'junction', needs: ['generator-on'],
    look: "The mine's pump. Its pipe runs down into the flooded way.\nI throw its switch. Nothing. There's no power down here.",
    done: "I throw the pump's switch. It shudders into life.\nThe water's going down.",
    after: 'The pump grinds on.',
    opens: { to: 'gallery', blocked: 'Black water, right to the roof.' },
  },
  {
    step: 'lift-up', room: 'mine-lift', needs: ['generator-on'],
    look: "The cage controls. UP and DOWN.\nThe lever's dead without power up top.",
    done: 'I press UP. The cage jolts, and starts to climb.',
    after: 'The cage controls. The light by UP is lit.',
    opens: { to: 'summit-trail', blocked: "The cage won't move." },
  },
  {
    step: 'mill-race', room: 'pond', use: 'crank',
    look: 'The sluice gate, barely open. The sign says open means the mill runs.\nThere\'s a socket on it for a crank.',
    done: 'The crank fits. I wind the sluice right open.\nThe race roars, and the mill shudders into life.',
    after: 'The sluice, wound right open. The mill is running.',
    // The flume down to the gorge runs off the same race.
    opens: { from: 'flume', to: 'bridge', blocked: 'The flume. Dry as a bone.' },
  },
  {
    step: 'crane', room: 'sawmill', needs: ['mill-race'],
    look: "The log crane, on its track. 5 TON.\nIt runs off the mill, and the mill isn't running.",
    done: 'The crane groans and swings the stack of logs off the crate.',
    after: 'The crane, its hook swinging.',
  },
  {
    step: 'fit-cog', room: 'platform', use: 'cog',
    look: "The drive's gearbox, open. The big cog has sheared: four teeth gone.\nA spanner lies in the oil where it was dropped.",
    done: 'The new cog goes on. I tighten it down with the spanner.',
    after: 'The gearbox, with its new cog.',
  },
  {
    step: 'fit-fuse', room: 'booth', use: 'fuses',
    look: 'Fuse F3 is burnt black. The wall above it is sooty.',
    done: 'I pull the burnt fuse and push a new one home.',
    after: 'The fuse box. Every fuse in place.',
  },
  {
    // The key switch is in the booth; the car it starts is out on the platform.
    step: 'gondola-runs', room: 'booth', use: 'op-key', needs: ['fit-cog', 'fit-fuse', 'line-on'],
    look: "The key switch for the drive. It's empty.\nNo key, no gondola.",
    done: "I turn Hal's key. Out there, the bullwheel turns...\nThe gondola is running!",
    after: 'The key switch, turned to RUN.',
    opens: { from: 'platform', to: 'car', blocked: "The gondola's dead." },
  },
  {
    step: 'push-rack', room: 'cellar',
    look: "A heavy rack of preserves. There are scrape marks on the floor by its end.\nIt's been moved.",
    done: 'I put my shoulder to the rack.\nIt scrapes along the flags: the passage is clear.',
    after: 'The rack, pushed back along the wall.',
    opens: { to: 'crawl', blocked: "A low passage. The rack's end is jammed across it." },
  },
];

/** Common flags (FG_COMMON) for the events, in order: 130-158, which no shipped room script and no engine flag uses. */
export const EVENT_FLAGS = new Map(EVENTS.map((e, i) => [e.step, 130 + i]));

export function keyItem(step: string): KeyItem {
  const k = KEY_ITEMS.find((i) => i.step === step);
  if (!k) throw new Error(`no key item for step ${step}`);
  return k;
}

export const eventsIn = (room: string) => EVENTS.filter((e) => e.room === room);

/** Room-item flags (FG_ITEM) for what events leave to pick up: 247 on. */
export const GIVE_FLAGS = new Map(EVENTS.filter((e) => e.gives).map((e, i) => [e.gives!, 247 + i]));

/** The models of what a room's events leave to pick up, after its supplies' and key items' (room.ts, scripts.ts). */
export function giveModels(room: string): PickupModel[] {
  const out: PickupModel[] = [];
  for (const e of eventsIn(room)) {
    if (!e.gives) continue;
    const m = keyItem(e.gives).model;
    if (!out.some((o) => sameModel(o, m))) out.push(m);
  }
  return out;
}

/** The empty last slot of a room's item models: a file pickup sits on it and draws nothing. */
export const EMPTY_SLOT = { empty: true } as const;

/**
 * A room's item model slots in order, item_aot_set's model index: the spec's
 * (a kit room's supplies), its key items', what its events leave to pick up,
 * then the empty slot. room.ts builds them; scripts.ts numbers its pickups
 * from them.
 */
export function itemModelSlots(specModels: readonly PickupModel[], items: readonly ItemSpot[], room: string): (PickupModel | typeof EMPTY_SLOT)[] {
  return [...specModels, ...keyItemModels(items), ...giveModels(room), EMPTY_SLOT];
}
