// What Rebecca's day still needs before it is a whole game, as data. Most
// rows come from the plan (day.ts): every room, way between rooms, item,
// puzzle, document and enemy it names. The rest are the game's systems,
// listed here. A row's status is worked out from the repository where it can
// be (a room is built when its renders exist); elsewhere it is set in STATUS
// below. Drawn by todo-page.ts.
import { AREAS, MAP_ITEMS } from './maps.ts';
import { CUES } from './music.ts';
import { SAVES } from './saves.ts';
import { FOES } from '../day/foes.ts';
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
  'look-wear': 'done',
  'look-trees': 'done',
  'look-interiors': 'done',
  'look-filter-build': 'done',
  'look-rerender': 'done',
  'look-weak': 'doing',
  // Built; waiting on a look in the game.
  'look-trapdoor-patch': 'doing',
  'doors-anim': 'doing',
  'doors-ladder': 'doing',
  'items-supplies': 'doing',
  // Seen in the game by tests/items.ts: her case, each item lying in its room, each one checked.
  'items-icons': 'done',
  'items-models': 'done',
  // Seen in the game by tests/gear.ts: her start kit, the loss in the gallery, Kevin's gun.
  'weapons-plan': 'done',
  // Built; waiting on the renders and a look.
  'look-dead': 'doing',
  'look-vehicles': 'doing',
  'look-weak-2': 'doing',
  'words-entry': 'done',
  // The hand-written yard's, played before.
  'puzzle-unlock-shed': 'done',
  'puzzle-winch-pine': 'done',
  'find-shed-key': 'done',
  'find-crank': 'done',
  // Worked in the game by tests/puzzles.ts.
  ...Object.fromEntries(['mill-race', 'crane', 'generator-on', 'line-on', 'blast', 'lift-up', 'drain', 'push-rack'].map((s): [string, Status] => [`puzzle-${s}`, 'done'])),
  // Locks written by day/scripts.ts: the tour walks their doors unlocked, but no test uses the key yet.
  ...Object.fromEntries(['cut-depot', 'cut-chain', 'tower-door', 'pry-lodge', 'open-gate'].map((s): [string, Status] => [`puzzle-${s}`, 'doing'])),
  // Rendered as a state of the room (kit.Room.state); waiting on the renders and a look in the game.
  ...Object.fromEntries(['blast', 'push-rack', 'generator-on', 'line-on', 'drain'].map((s): [string, Status] => [`moving-${s}`, 'doing'])),
  ...Object.fromEntries(
    ['truck-keys', 'cutters', 'office-key', 'safe', 'cog', 'jerrycan', 'fuel', 'switch-key', 'quarry-key', 'dynamite', 'op-key', 'fuses', 'crowbar', 'gate-key', 'cellar-key'].map((s): [string, Status] => [`find-${s}`, 'doing']),
  ),
  'look-trapdoor-sample': 'done',
  'look-filter-sample': 'done',
  'look-reviewed-builders': 'done',
  'doors-tour-tool': 'done',
  // All 102 doors pass the tour (tests/tour.ts) on the re-rendered rooms.
  'doors-wired': 'done',
  'enemies-plan': 'done',
  'items-plan': 'done',
  'maps-plan': 'done',
  'people-pipeline': 'done',
  'people-partner-model': 'doing',
  'people-hal-model': 'doing',
  'maps-research': 'doing',
  'music-research': 'done',
  'music-plan': 'done',
  'music-sketches': 'doing',
  'music-re1': 'done',
  // Seen in the game by tests/music.ts: her table plays our render in the
  // station's rooms and Bgm_31 in every save room, silent rooms stay silent,
  // and Chris's save room plays RE1's own. render.ts gives the same bytes
  // each run, and the game's loader reads the loop it writes.
  'music-engine': 'done',
  'music-render': 'done',
  'music-loop': 'done',
  'music-test': 'done',
  'music-save': 'done',
  // Rendered and playing in the game; nobody has listened to it yet.
  'music-station': 'doing',
  'saves-plan': 'done',
  'saves-mode': 'done',
  'saves-names': 'done',
  'saves-props': 'done',
  // By the cabin's typewriter, and in the save rooms plan/saves.ts gives them (day/supplies.ts).
  'saves-ribbons': 'done',
  'saves-mansion': 'done',
  'save-cabin': 'done',
  'save-office': 'done',
  'save-booth': 'done',
  'save-mine-office': 'done',
  'save-lodge': 'done',
  'saves-test': 'done',
  // Picked up, read and kept in her FILE tab in the game (tools/harness/tests/files.ts).
  'files-viewer': 'done',
  // In the game, but the reader shows only each page's top 192 rows, and the
  // owner is reviewing the texts and the paper.
  'files-art': 'doing',
  'file-logbook': 'doing',
  'file-calendar': 'doing',
  'file-diary': 'doing',
  'file-mine-map': 'doing',
  'file-keeper-log': 'doing',
  'file-gardener-diary': 'doing',
  'file-foreman-letters': 'doing',
  'file-walt-log': 'doing',
  'file-quarantine': 'doing',
  'file-rosters': 'doing',
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

export const CUTSCENES: readonly [string, string][] = [
  ['cut-opening', 'Opening: dawn on the ridge, after Billy'],
  ['cut-phone', "The booth's phone: Hal on the line, telling her what the gondola needs"],
  ['cut-partner', "Meeting the ranger's partner in the woods"],
  ['cut-den', 'The hollow: the partner finds him, and gives Rebecca his keys'],
  ['cut-dog', 'The first dog comes for her in the station yard'],
  ['cut-gondola', 'The gondola starts: the bullwheel, the car leaving'],
  ['cut-tower', 'From the tower: Bravo\'s smoke and the mansion\'s roof'],
  ['cut-hal', "Hal's last minutes on the ore cart: the key, then the bite takes him"],
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
        row('look-dead', 'The dead as people', 'MakeHuman bodies, clothed and posed, baked once (blender/corpses.py), in every room that has one'),
        row('look-vehicles', 'Vehicles with real shapes', "Bravo's helicopter, the pickups, the sedan, the log truck and the skidder lofted in the kit"),
        row('look-weak-2', 'Fix the weak rooms, second pass', "The sawmill's black saw blade, the den's flat-faceted granite, the mast's smooth cliffs, the platform's empty gorge"),
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
        row('items-models', 'Models for the new key items: lying in the room and examined', 'Seven of her own (items/models.py, items/tmd.ts); the keys keep their donors\''),
        row('items-icons', 'Inventory icons and names for the new key items'),
        row('items-supplies', 'Ammunition, herbs and first aid sprays placed through the day'),
        ...finds.map((s) => stepRow(s, 'find')),
      ],
    },
    {
      id: 'saves',
      title: 'Saving',
      blurb: "Save rooms as rare and as near as RE1's own, measured from its room files: a quiet side room with a typewriter, an item box and RE1's save room music. Ink ribbons ration the saves, and the item boxes share one store.",
      items: [
        row('saves-plan', "Save rooms placed to RE1's spacing, checked against the plan (saves.ts, re1-saves.ts)", `${SAVES.length} rooms, one for every ${Math.round(plan.places.length / SAVES.length)}; none farther than RE1's farthest`),
        row('saves-mode', 'A save made in her day loads back into her day', 'Her mode is set only at character select today. Store it in the save, as the port already stores the DC difficulty (dcGameMode)'),
        row('saves-names', 'Her place names on the save screen', "The slot list names a save by the mansion's areas (GetSaveLocationIndex); hers needs the station, the camp, the mine, the valley"),
        row('saves-props', "A typewriter in each save room, and RE1's own item box: its lid from the player's files on a body painted to fit"),
        row('saves-ribbons', 'Ink ribbons to pick up, with their model in her rooms'),
        ...SAVES.map((v) => row(`save-${v.place}`, `${name(v.place)}: typewriter and item box`, v.props)),
        row('saves-mansion', "The mansion's save room keeps its typewriter and box", 'Already in her ROOM1000 script'),
        row('saves-test', 'A test that saves at a typewriter, loads the save, and is back in her day with the box as she left it', 'tools/harness/tests/reb-save.ts and reb-save-rooms.ts'),
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
      id: 'maps',
      title: 'Maps',
      blurb: "Her map screen as good as RE1's: an overview of the mountain, a floor plan for each area, the rooms she has been in lit, and a map to find for each area that shows the rest.",
      items: [
        row('maps-plan', 'Areas and map pickups planned, and checked against the plan (maps.ts)'),
        row('maps-research', "How RE1's map screen works, written up", 'Images per area, a palette block per room, the visited and map-owned flags, the area tables'),
        row('maps-overview', 'The overview: the mountain rendered from above, unlocking as she goes', 'Four stages, like RE1: the station; the mountain; the skyway and valley; the estate'),
        ...AREAS.map((a) => row(`map-area-${a.id}`, `Floor plan: ${a.name}`, `${a.places.length} rooms`)),
        row('maps-engine', "Her mode reads its own area tables and map images, and Chris's and Jill's stay as they are"),
        row('maps-states', 'Rooms lit once visited, dim once the map is owned, hers blinking'),
        ...MAP_ITEMS.map((m) => {
          const s = plan.steps.find((x) => x.id === m.step);
          return row(`map-item-${m.id}`, `Pickup: the ${m.name}`, s ? `${name(s.at)}, act ${s.act}` : undefined);
        }),
        row('maps-test', 'A test that opens each map in the game and screenshots it'),
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
      id: 'people',
      title: 'People',
      blurb: "Two people she meets: the ranger's partner, out looking for him, who keeps turning up; and Hal, the gondola operator, who tells her how to get it running and dies once she has his key.",
      items: [
        row('people-pipeline', "Read and write RE1's character models, view them in Blender, put a new skin in the game"),
        row('people-partner-model', "The ranger's partner: a woman in Forest Service uniform, on a female RE1 skeleton"),
        row('people-hal-model', 'Hal: heavyset, fifties, Skyway work jacket, his bitten arm bandaged, on a male RE1 skeleton'),
        row('people-hal-voice', "Hal's lines: the phone call and his last words"),
        row('people-partner-voice', "The partner's lines: the woods, the hollow, the camp, the radio, the valley"),
        row('people-partner-fate', "The partner's end: decided"),
        row('people-gallery', 'The gallery re-rendered without Hal floating in it, for the living Hal'),
      ],
    },
    {
      id: 'enemies',
      title: 'Enemies',
      blurb: "Who is in each room, from RE1's own cast: placed, tuned, and fair to meet there.",
      items: [
        row('enemies-plan', 'Enemies planned room by room'),
        row('enemies-forest', 'More threat in the forest early on'),
        // Placed in the room's script (day/foes.ts): under way until they are fought and tuned.
        ...plan.places.filter((p) => p.enemies).map((p) => row(`enemy-${p.id}`, `${p.name}: ${p.enemies}`, `Act ${p.act}`, FOES[folder(p)]?.length ? 'doing' : undefined)),
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
      ],
    },
    {
      id: 'music',
      title: 'Music',
      blurb: "Music in the manner of RE1's: written as code, rendered to WAV the same way every time, and played by her mode's own music table. RE1's own tracks only from the player's files.",
      items: [
        row('music-research', 'How RE1 plays music, and how we make ours, written up (docs/REBECCA_MUSIC.md)'),
        row('music-plan', 'A cue for every room and cutscene, checked against the plan (music.ts)'),
        row('music-re1', "RE1's own music as Strudel code, note for note, to learn from (LAN only)", '97 tracks from the PS1 disc, checked against it by re1-check.ts'),
        row('music-sketches', 'Sketches to listen to in Strudel, and the owner\'s verdict on the sound'),
        row('music-render', 'A render step: a pattern in, a WAV out, with the PS1 treatment, the same every time'),
        row('music-loop', 'Loop points written into each WAV, so an intro plays once and the rest loops'),
        row('music-engine', "Her mode reads its own music table, and Chris's and Jill's stay as they are"),
        row('music-states', 'Room scripts switch channels as she works: the generator hum, the mill, the chase'),
        ...CUES.map((c) =>
          row(
            `music-${c.id}`,
            c.kind === 'reuse' ? `${c.title}: RE1's ${c.file}, from the player's files` : c.kind === 'ambience' ? `${c.title}: ambience only` : `${c.title}`,
            c.mood,
          ),
        ),
        row('music-test', 'A test that walks the day and checks which track each room plays'),
      ],
    },
    {
      id: 'balance',
      title: 'Balance',
      blurb: 'It feels right to play: tense, fair, about two hours.',
      items: [
        row('balance-ammo', 'Ammunition and healing: enough to survive, never comfortable'),
        row('balance-saves', 'How many ink ribbons, tuned by playing'),
        row('balance-enemies', 'Enemy health, damage and numbers'),
        row('balance-route', "The route reads: she can always tell where she hasn't been"),
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
