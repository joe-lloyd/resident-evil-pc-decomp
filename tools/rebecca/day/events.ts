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
  /**
   * The way it opens, from this room unless `from` names another, and what
   * she sees there until then; `behind`, what she sees from the far side of
   * a way that only opens from this one (the skid road's chain, the adit's
   * boards).
   */
  readonly opens?: { readonly from?: string; readonly to: string; readonly blocked: string; readonly behind?: string };
  /** A second item that does it at the same spot, with its own line (the winch crank on the rockfall). */
  readonly orUse?: { readonly use: string; readonly done: string };
  /**
   * Worked as a row of switches thrown in order (the breakers): spots
   * `<spot>-1` to `<spot>-<count>`, the right order first to last, and a
   * wrong one undoes the row and takes `hurt` health (sys_multi 11).
   */
  readonly order?: { readonly spot: string; readonly sequence: readonly number[]; readonly hurt: number; readonly thrown: string; readonly wrong: string };
  /** It also happens once every enemy of the room that goes `until` it is dead (the kennels' pack, shot instead of penned). */
  readonly orAllDead?: true;
}

export const EVENTS: readonly RoomEvent[] = [
  {
    step: 'fuel', room: 'depot', use: 'jerrycan', gives: 'fuel',
    look: "Diesel, dripping from the nozzle. The hose reel is chained, and padlocked.\nThe hand pump still works. I need something to carry it in.",
    done: "I fill the jerrycan at the hand pump.\nIt's heavy now.",
    after: 'The diesel tank. The hand pump drips.',
  },
  {
    step: 'generator-on', room: 'generator', use: 'fuel', gives: 'jerrycan',
    look: "The generator's panel. The fuel gauge is right down on E.\nIt ran itself dry.",
    done: "Diesel in. It coughs, catches... and runs.\nThe lights are coming on. I put the empty can down.",
    after: 'The generator thuds away. The whole hut shakes.',
  },
  {
    // Five breakers, one per pylon, numbered from the valley up. The
    // lineman's sketch says the feed comes in at the top station, so the
    // power goes out from 5 to 1.
    step: 'line-on', room: 'switch', needs: ['generator-on'],
    order: {
      spot: 'breaker', sequence: [5, 4, 3, 2, 1], hurt: 12,
      thrown: 'The breaker holds.',
      wrong: 'A bang, and a flash off the contacts! The shock throws me back.\nThe whole bank has tripped.',
    },
    look: "The breakers, one for each pylon on the line. All of them down.\nThere's no power to switch on.",
    done: 'The last breaker holds.\nThe line starts to hum.',
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
    orUse: {
      use: 'crank',
      done: "I hook the crane's cable round the jammed timbers and wind.\nSlowly, slowly, they drag out. The rocks come down after them.",
    },
    look: "The roof's been brought down across the mouth. On purpose:\nthere's a blasting wire running out of the rocks.",
    done: 'I wedge the dynamite into the rockfall, light it and run.\nThe whole hillside jumps. The way is open.',
    after: 'The mine mouth, blasted clear.',
    opens: { to: 'tunnel', blocked: "The gap's too tight for me,\nand the rocks over it are loose." },
  },
  {
    step: 'drain', room: 'junction', use: 'jerrycan', needs: ['generator-on'],
    look: "The mine's pump. Its intake is down in the silt: the float that held it up is split.\nAnd its power lamp is dark.",
    done: "I tie the empty jerrycan on as a float. The intake lifts clear of the silt.\nThe pump shudders into life. The water's going down.",
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
    step: 'crane', room: 'workshop', needs: ['mill-race'],
    look: "The hoist's control. I press UP. Nothing.\nIts cable runs to the MILL LINE box, and the mill isn't running.",
    done: 'The hoist whines and lifts the logs off the crate.\nThe lid comes away with them.',
    after: 'The hoist, the logs hanging from it.',
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
  // Added with the puzzle climb (docs/handoffs/2026-11-06-puzzle-build.md).
  // New events go on the end: their flags count on from the others'.
  {
    step: 'ring-bell', room: 'camp-yard',
    look: 'The cookhouse bell.',
    done: 'I haul on the rope. The bell clangs out over the camp.\nSomewhere, things start shuffling toward the mess hall.',
    after: 'The cookhouse bell. Still swinging.',
  },
  {
    step: 'skid-road', room: 'depot',
    look: 'A gate onto the skid road, chained shut from this side.',
    done: 'I lift the chain off its hook. The gate swings open onto the skid road.',
    after: 'The skid road, down through the trees.',
    opens: { to: 'tower-foot', blocked: 'The gate is chained.', behind: 'A gate at the top of the skid road. Chained from the other side.' },
  },
  {
    step: 'adit', room: 'gallery', needs: ['drain'],
    look: 'Boards across an old tunnel. Daylight through the cracks.\nThe water is right up against them.',
    done: 'I kick the boards out. Daylight, at the far end.',
    after: 'The old adit, open to the daylight.',
    opens: { to: 'east-path', blocked: 'Boarded up.', behind: 'An old mine adit in the bank. Boarded up from inside.' },
  },
  {
    step: 'pen-pack', room: 'kennels', use: 'dog-meat', orAllDead: true,
    look: 'The one run with its gate still on. A good bolt.',
    done: 'I throw the meat into the run. The pack piles in after it.\nI slam the gate and shoot the bolt.',
    after: 'The pack, bolted into the run.',
  },
];

/** Common flags (FG_COMMON) for the events, in order: 130-158, which no shipped room script and no engine flag uses. */
export const EVENT_FLAGS = new Map(EVENTS.map((e, i) => [e.step, 130 + i]));

/**
 * Marks: common flags for how something was done, where the plan's other
 * way has a cost of its own (the cutters' noise at the workshop brings the
 * loggers out; its key does not). From the top of the events' range down.
 */
export const MARK_FLAGS = new Map([['workshop-cut', 158]]);
if (EVENTS.length + MARK_FLAGS.size > 29) throw new Error('the events and marks have FG_COMMON 130-158, 29 flags');

export function keyItem(step: string): KeyItem {
  const k = KEY_ITEMS.find((i) => i.step === step);
  if (!k) throw new Error(`no key item for step ${step}`);
  return k;
}

export const eventsIn = (room: string) => EVENTS.filter((e) => e.room === room);

/**
 * Room-item flags (FG_ITEM) for what events leave to pick up: the diesel
 * 247, as it always had; the rest from 229 down, the top of the supplies'
 * range, which count up from 180 (supplies.ts). 248 on are the hand-written
 * rooms'.
 */
const GIVE_FLAG_ORDER = [247, ...Array.from({ length: 20 }, (_, i) => 229 - i)];
export const GIVE_FLAGS = new Map(EVENTS.filter((e) => e.gives).map((e, i) => [e.gives!, GIVE_FLAG_ORDER[i]!]));

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
