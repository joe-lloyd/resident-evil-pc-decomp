// What Rebecca's day still needs before it is a whole game, as data. Most
// rows come from the plan (day.ts): every room, way between rooms, item,
// puzzle, document and enemy it names. The rest are the game's systems,
// listed here. A row's status is worked out from the repository where it can
// be (a room is built when its renders exist); elsewhere it is set in STATUS
// below. Drawn by todo-page.ts.
import type { Link, Place, Plan, Step } from './plan.ts';

export type Status = 'done' | 'doing' | 'todo';

export interface Item {
  readonly id: string;
  readonly title: string;
  readonly note?: string;
  readonly status: Status;
}

export interface Section {
  readonly id: string;
  readonly title: string;
  readonly blurb: string;
  readonly items: readonly Item[];
}

/** What the repository says about a built room: its folder under day/ has renders/room.json. */
export interface RoomFacts {
  /** Doors the scene records, by neighbour slug. */
  readonly doors: readonly string[];
  readonly checks: number;
  readonly entry: boolean;
}

export interface Facts {
  /** Rendered rooms by folder name. */
  readonly rooms: ReadonlyMap<string, RoomFacts>;
}

/** Rows whose status the repository can't show: set by hand as work lands. */
const STATUS: Record<string, Status> = {
  'look-wear': 'doing',
  'look-trapdoor-sample': 'done',
  'look-filter-sample': 'done',
  'look-reviewed-builders': 'done',
  'doors-tour-tool': 'done',
  'enemies-plan': 'done',
  'items-plan': 'done',
};

const status = (id: string, fallback: Status = 'todo'): Status => STATUS[id] ?? fallback;
const row = (id: string, title: string, note?: string, fallback?: Status): Item => ({ id, title, note, status: status(id, fallback) });

const folder = (p: Place) => p.room ?? p.id;

/** Documents she reads: the plan's clues that are written down, not seen. */
const DOCUMENTS: Record<string, string> = {
  logbook: "The ranger's logbook",
  calendar: 'The bunkhouse calendar',
  diary: "Hal's diary",
  'mine-map': 'The mine map',
  'keeper-log': "The lower station keeper's log",
  'gardener-diary': "The gardener's diary",
};

/** More papers the scenes already show, worth making readable. */
const MORE_DOCUMENTS: readonly [string, string][] = [
  ['foreman-letters', "The foreman's letters: Umbrella paid for the gondola"],
  ['walt-log', "Walt's lookout log, to THEY'RE ON THE STAIRS"],
  ['quarantine', 'The torn QUARANTINE notice on the logging road'],
  ['rosters', 'The quarry rosters going red with SICK'],
];

/** Steps that change the room in front of her, and want an animation or a second set of renders. */
const MOVING: Record<string, string> = {
  'winch-pine': 'The fallen pine drags off the trail as the winch turns',
  'mill-race': 'The sluice lifts, the race fills and the water wheel turns',
  crane: 'The log crane swings the stack off the crate',
  'generator-on': 'The generator coughs into life and the station lights come on',
  'line-on': 'The breakers close: hum, sparks, the line lamps light',
  blast: 'The dynamite blows the rockfall out of the mine mouth',
  drain: 'The pump runs and the flooded gallery drains',
  'lift-up': 'The mine cage rises to the summit',
  'gondola-runs': 'The bullwheel turns and the car moves',
  'push-rack': 'The wine rack scrapes aside to show the crawl passage',
  hatch: 'The trapdoor lifts into the save room',
  'cut-chain': 'The chain drops off the road gate',
  'open-gate': "The estate's back gate swings open",
};

const CUTSCENES: readonly [string, string][] = [
  ['cut-opening', 'Opening: dawn on the ridge, after Billy'],
  ['cut-dog', 'The first dog comes for her in the station yard'],
  ['cut-gondola', 'The gondola starts: the bullwheel, the car leaving'],
  ['cut-tower', 'From the tower: Bravo\'s smoke and the mansion\'s roof'],
  ['cut-hal', 'Finding Hal in the flooded gallery'],
  ['cut-mine-collapse', 'The mine floor gives way: she loses her gear'],
  ['cut-mine-chase', 'Chased through the mine, unarmed, to the lift'],
  ['cut-pylon', 'The car stops at the pylon, something on the roof'],
  ['cut-kevin', 'Kevin dead at the controls of Bravo\'s helicopter'],
  ['cut-sleep', 'In the save room: too tired, she sits down and sleeps'],
  ['cut-chris', 'She wakes: footsteps, Chris walks in'],
  ['cut-credits', 'Her credits'],
];

export function sections(plan: Plan, facts: Facts): Section[] {
  const placeOf = new Map(plan.places.map((p) => [p.id, p]));
  const built = (p: Place) => p.existing !== undefined || facts.rooms.has(folder(p));
  const name = (id: string) => placeOf.get(id)?.name ?? id;
  const stepRow = (s: Step, prefix: string, note?: string) => row(`${prefix}-${s.id}`, s.label, note ?? `${name(s.at)}, act ${s.act}`);

  // A way between two rooms is joined when both scenes have a door to each other (or one is hand-built or original).
  const joined = (l: Link) => {
    const a = placeOf.get(l.from)!;
    const b = placeOf.get(l.to)!;
    const side = (x: Place, y: Place) => x.existing !== undefined || x.built === 'built' || (facts.rooms.get(folder(x))?.doors.includes(folder(y)) ?? false);
    return side(a, b) && side(b, a);
  };
  const doorKind: Record<Link['kind'], string> = {
    walk: 'walk-through path',
    door: 'door that opens',
    ladder: 'ladder',
    ride: 'ride',
    lift: 'lift',
  };

  const rooms = plan.places.filter((p) => !p.existing);
  const withChecks = rooms.filter((p) => (facts.rooms.get(folder(p))?.checks ?? 0) > 0).length;
  const finds = plan.steps.filter((s) => s.kind === 'find');
  const puzzles = plan.steps.filter((s) => s.kind === 'do' && !['sleep', 'ride', 'pylon-down', 'dog'].includes(s.id));

  return [
    {
      id: 'rooms',
      title: 'Rooms and scenes',
      blurb: 'Every room of the plan built in Blender and rendered: cameras, story, light, things that move.',
      items: [
        ...plan.places.map((p) =>
          row(`room-${p.id}`, p.name, p.existing ? `The original ${p.existing}` : `Act ${p.act}, ${p.cameras} cameras`, built(p) ? 'done' : 'todo'),
        ),
      ],
    },
    {
      id: 'look',
      title: 'The RE1 look',
      blurb: 'Muddy, defined textures on every surface, ragged shapes, readable rooms, and a light grain to tie it together.',
      items: [
        row('look-reviewed-builders', 'First look over every scene by its builder'),
        row('look-wear', 'Worn low-resolution texture on every surface (kit.wear)'),
        row('look-trees', 'Ragged spruces and rougher ferns in the kit'),
        row('look-interiors', 'Brighter interiors: walls readable, as in RE1'),
        row('look-filter-sample', 'Sample of the look filter (look.py)'),
        row('look-filter-build', 'The light look filter as a build step, on backgrounds and masks alike'),
        row('look-rerender', 'Re-render every room with the new look'),
        row('look-weak', 'Fix the weak rooms', 'The quarry, the mine mouth gap, the washout body, the switch house, the lower yard gravel, the flat far ridges'),
        row('look-trapdoor-sample', "Sample of the save room's trapdoor, closed and worn"),
        row('look-trapdoor-patch', "The save room's trapdoor as a patch built from the player's files"),
      ],
    },
    {
      id: 'ways',
      title: 'Ways between rooms',
      blurb: 'Every link of the plan. Walk-through paths only need both scenes to have their door; doors, ladders, lifts and rides need their own animation.',
      items: [
        row('doors-tour-tool', 'A test that walks through every door and checks where she comes out'),
        row('doors-wired', 'Every door written into the game, built and walked by the test'),
        row('doors-anim', 'Door-opening animations for the new doors', 'Cabin, shed, camp huts, gate, tower, cottage, mine office, lodge, cellar doors'),
        row('doors-ladder', 'Climbing a ladder between rooms', 'Tower stairs, the pylon, the crawl hatch'),
        ...plan.links.map((l) =>
          row(`link-${l.from}-${l.to}`, `${name(l.from)} to ${name(l.to)}`, `${doorKind[l.kind]}${l.opens ? `, opened by "${plan.steps.find((s) => s.id === l.opens)?.label ?? l.opens}"` : ''}`,
            l.kind === 'walk' ? (joined(l) ? 'done' : 'todo') : joined(l) ? 'doing' : 'todo'),
        ),
      ],
    },
    {
      id: 'items',
      title: 'Items and weapons',
      blurb: 'What she picks up: placed in its room, with a model to see there and an icon for her inventory.',
      items: [
        row('items-plan', 'Every key item planned, and checked that it can be had before it is needed'),
        row('weapons-plan', 'Her weapons through the day', 'A knife and a handgun with a few rounds; the mine takes everything; a gun again from Kevin at the crash'),
        row('items-models', 'Pickup models for the new key items'),
        row('items-icons', 'Inventory icons and names for the new key items'),
        row('items-supplies', 'Ammunition, herbs and first aid sprays placed through the day'),
        ...finds.map((s) => stepRow(s, 'find')),
      ],
    },
    {
      id: 'files',
      title: 'Files she reads',
      blurb: 'Diaries, logs and letters open as pages, as RE1 files do, not as lines of text at the bottom of the screen.',
      items: [
        row('files-viewer', 'Files open as full pages, as in RE1, and stay in her file folder'),
        row('files-art', 'Paper for the pages: notebook, ledger, letter, typed report'),
        ...Object.entries(DOCUMENTS).map(([id, title]) => {
          const s = plan.steps.find((x) => x.id === id);
          return row(`file-${id}`, title, s ? `${name(s.at)}, act ${s.act}: ${s.label}` : undefined);
        }),
        ...MORE_DOCUMENTS.map(([id, title]) => row(`file-${id}`, title)),
      ],
    },
    {
      id: 'puzzles',
      title: 'Puzzles',
      blurb: 'Each job of the plan working in the game: the right item opens it, nothing else does, and it stays done.',
      items: puzzles.map((s) => stepRow(s, 'puzzle')),
    },
    {
      id: 'moving',
      title: 'Things that change the room',
      blurb: 'When a job is done the room shows it: an animation, then the room in its new state.',
      items: Object.entries(MOVING).map(([id, title]) => {
        const s = plan.steps.find((x) => x.id === id);
        return row(`moving-${id}`, title, s ? `${name(s.at)}, act ${s.act}` : undefined);
      }),
    },
    {
      id: 'cutscenes',
      title: 'Cutscenes',
      blurb: 'The moments the camera takes over.',
      items: CUTSCENES.map(([id, title]) => row(id, title)),
    },
    {
      id: 'enemies',
      title: 'Enemies',
      blurb: "Who is in each room, from RE1's own cast: placed, tuned, and fair to meet there.",
      items: [
        row('enemies-plan', 'Enemies planned room by room'),
        row('enemies-forest', 'More threat in the forest early on'),
        ...plan.places.filter((p) => p.enemies).map((p) => row(`enemy-${p.id}`, `${p.name}: ${p.enemies}`, `Act ${p.act}`)),
      ],
    },
    {
      id: 'words',
      title: 'Words',
      blurb: 'What she thinks and what she can look at.',
      items: [
        row('words-checks', 'Things to examine in every room', `${withChecks} of ${rooms.length} rooms have some`, withChecks === rooms.length ? 'done' : withChecks ? 'doing' : 'todo'),
        row('words-entry', 'A first thought on entering the rooms that need one'),
        row('words-pass', 'One editing pass over all of her lines, in her voice'),
      ],
    },
    {
      id: 'sound',
      title: 'Sound',
      blurb: 'What each place sounds like.',
      items: [
        row('sound-footsteps', 'Footsteps to match each floor: gravel, boards, rock, water'),
        row('sound-ambience', 'Ambience for each area: wind, the forest, the mill, the mine'),
        row('sound-doors', 'Door, gate and hatch sounds'),
        row('sound-music', 'Music for the acts and the cutscenes'),
      ],
    },
    {
      id: 'balance',
      title: 'Balance',
      blurb: 'It feels right to play: tense, fair, about two hours.',
      items: [
        row('balance-ammo', 'Ammunition and healing: enough to survive, never comfortable'),
        row('balance-saves', 'Typewriters, ink ribbons and item boxes'),
        row('balance-enemies', 'Enemy health, damage and numbers'),
        row('balance-route', "The route reads: she can always tell where she hasn't been"),
        row('balance-maps', 'Map screens for the new areas'),
        row('balance-time', 'A first playthrough at about two hours'),
      ],
    },
    {
      id: 'ship',
      title: 'Ready',
      blurb: 'Done means a player can install it and play it through.',
      items: [
        row('ship-playthrough', 'The whole day played through, start to credits, by the test harness'),
        row('ship-patch', "The patch built from the player's own game files, with no game data shipped"),
        row('ship-install', 'An installer and a readme'),
        row('ship-human', 'A human playthrough, and its notes fixed'),
      ],
    },
  ];
}
