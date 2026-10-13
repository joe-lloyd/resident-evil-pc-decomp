// Rebecca's day as one plan: 58 rooms, as many as the mansion has, from the
// ridge at dawn to the mansion's save room at night. The station yard is the
// hub of the game's long middle: the gondola down the mountain is dead, and
// what it needs is out in three directions from the yard (power to the west,
// a drive cog to the north at the logging camp, the operator's key to the
// east in the old mine), each a spoke of its own with a shortcut home, and
// each borrowing something from another.
//
// `node tools/rebecca/plan/page.ts <out dir>` draws it; plan.test.ts checks it.
import type { Built, Link, LinkKind, Place, Plan, Step, StepKind } from './plan.ts';

type Beat = readonly [there: string, moves: string, enemies: string, story: string];

const place = (
  act: number,
  id: string,
  name: string,
  cameras: number,
  at: readonly [number, number],
  [there, moves, enemies, story]: Beat,
  more: { built?: Built; room?: string; existing?: string } = {},
): Place => ({ id, name, act, cameras, at, there, moves, enemies, story, built: more.built ?? 'planned', room: more.room, existing: more.existing });

const built = (room: string) => ({ built: 'built' as const, room });

const step = (
  act: number,
  id: string,
  at: string,
  kind: StepKind,
  needs: readonly string[],
  label: string,
  more: { built?: true; optional?: true } = {},
): Step => ({ id, act, at, kind, needs, label, built: more.built ? 'built' : 'planned', optional: more.optional });

const link = (from: string, to: string, kind: LinkKind, opens?: string, shortcut?: true): Link => ({ from, to, kind, opens, shortcut });

export const day: Plan = {
  title: "Rebecca's day",
  start: 'ridge',
  acts: [
    {
      n: 1, title: 'Off the mountain top', time: 'Dawn to morning',
      summary: 'From the ridge down to the ranger station, the winch and the pine, and across the gorge to the gondola station. The gondola is dead, and the operator\'s board says why: no power, a sheared drive cog, and his key gone with him.',
    },
    {
      n: 2, title: 'The mountain', time: 'Late morning to afternoon',
      summary: 'The long middle of the game. The yard is the hub. Power is west up the forestry road, at the generator and the switch house. The spare drive cog is north at the logging camp. The operator\'s key is east, on the operator, in the flooded mine. Each spoke needs something from another, and each ends with a shortcut back.',
    },
    {
      n: 3, title: 'Down the mountain', time: 'Dusk',
      summary: 'The gondola stops at a pylon halfway down. She climbs down into the valley forest, finds Bravo\'s helicopter where they came down last night, and breaks into the gardener\'s lodge for the key to the estate\'s back gate.',
    },
    {
      n: 4, title: 'The mansion', time: 'Night',
      summary: 'In through the cellar doors, under the floor, and up through a hatch into the save room. Too tired to go on, she sits against the wall and falls asleep. Footsteps wake her, and Chris walks in.',
    },
  ],
  places: [
    // Act 1: built, but for the gondola station.
    place(1, 'ridge', 'The ridge', 2, [10, 0], ['Where the game opens', 'Smoke from the facility, grass', '', 'Billy has gone; the training facility burns below'], built('ridge')),
    place(1, 'trail', 'The mountain trail', 2, [10, 1.4], ['Down through the spruces', 'Ferns in the wind', 'Crows', 'Alone for the first time'], built('trail')),
    place(1, 'yard', 'The station yard', 4, [10, 2.8], ['The hub: the pine, the truck and its winch, his rifle', 'Chimney smoke, hazard lights', 'A Cerberus, once she has the shed key', 'Someone was here this morning'], built('yard')),
    place(1, 'cabin', 'The cabin', 2, [12.2, 2.2], ['The logbook, the radio, the shed key', 'The lamp flame, a fly', '', 'He left in a hurry, mid-breakfast'], built('lookout')),
    place(1, 'shed', 'The tool shed', 2, [12.2, 3.4], ['The winch crank, an empty jerrycan, spare fuses', 'Dust in the light', '', 'He tried to mend the chainsaw first'], built('shed')),
    place(1, 'bridge', 'The gorge footbridge', 3, [10, 4.2], ['The old footbridge over the gorge', 'The river far below', 'Adders', 'The trail goes on down'], built('bridge')),
    place(1, 'platform', 'The gondola station', 6, [10, 5.6], ['The upper station: the car hanging at the platform, the drive wheel', 'The cable creaking, a loose tarpaulin', 'Crows', 'The way down the mountain, if it ran'], {}),
    place(1, 'booth', "The operator's booth", 2, [12.2, 5.6], ['The control desk, the fuse box, the duty board', 'A wall calendar lifting in the draught', '', 'The operator, Hal, left his post in a hurry too'], {}),

    // Act 2, north: the woods and the logging camp.
    place(2, 'woods', 'The woods', 5, [7.8, 2.8], ['Drag marks into the trees', 'Branches, flies', 'Cerberus, two', 'Where the dog came from'], {}),
    place(2, 'den', 'The hollow', 3, [7.8, 1.4], ['The dogs\' den: the ranger, dead, his keys in his jacket', 'Flies over the body', 'Cerberus', 'What became of him'], {}),
    place(2, 'logging-road', 'The logging road', 4, [5.6, 1.4], ['Deep ruts, a stalled truck', 'Its wipers twitching', 'A zombie logger', 'The infection has reached the mountain'], {}),
    place(2, 'camp-gate', 'The camp gate', 3, [3.4, 1.4], ['The gate, a barricade of logs half pulled down', 'A torn notice', '', 'They tried to keep something out'], {}),
    place(2, 'camp-yard', 'The camp yard', 8, [1.2, 1.4], ['The camp\'s hub: timber stacks, the cookhouse bell', 'Smoke from a dead fire, the bell swinging', 'Zombie loggers', 'Twenty men worked here'], {}),
    place(2, 'bunkhouse', 'The bunkhouse', 4, [1.2, 0], ['Bunks, a calendar with the safe\'s numbers', 'A flickering bulb', 'A zombie in a bunk', 'The men got sick one by one'], {}),
    place(2, 'office', "The foreman's office", 3, [-1, 0], ['The safe, the payroll', 'A desk fan', '', 'Letters: Umbrella paid for the gondola'], {}),
    place(2, 'mess', 'The mess hall', 4, [-1, 1.4], ['Long tables, the cook dead with the office key', 'Steam from a pot, flies', 'Zombies', 'The last meal'], {}),
    place(2, 'depot', 'The fuel depot', 3, [-1, 2.8], ['A padlocked pump, diesel drums', 'A dripping nozzle', 'Adders', ''], {}),
    place(2, 'workshop', 'The workshop', 3, [1.2, 2.8], ['The spare drive cog in its crate, logs stacked on it', 'Sparks from a cut cable', '', 'They kept spares for the gondola'], {}),
    place(2, 'sawmill', 'The sawmill', 6, [3.4, 0], ['The saw, the log crane', 'The water wheel, once running', 'Zombies', ''], {}),
    place(2, 'pond', 'The mill pond', 4, [5.6, 0], ['The sluice to the mill race', 'Water, reeds, a floating hat', 'A zombie in the water', ''], {}),
    place(2, 'flume', 'The log flume', 3, [7.8, 0], ['The flume\'s top: a log boat', 'Running water', '', 'A ride down to the gorge'], {}),

    // Act 2, west: the forestry road, the generator and the lookout tower.
    place(2, 'road', 'The forestry road', 5, [7.8, 4.2], ['A chained gate across the road', 'A torn notice on the gate', 'Crows', 'The way the rangers drive up'], {}),
    place(2, 'washout', 'The washout', 4, [5.6, 4.2], ['The road half gone into a gully', 'Water running over the road', 'Adders', ''], {}),
    place(2, 'generator', 'The generator hut', 3, [5.6, 5.6], ['The generator, dry', 'A fan once it runs; the lights come on', '', 'Power for the station, the mine and the gondola'], {}),
    place(2, 'tower-foot', 'The lookout tower, foot', 3, [3.4, 4.2], ['The tower door, locked', 'The tower creaking in the wind', '', ''], {}),
    place(2, 'tower-stairs', 'The lookout tower, stairs', 3, [1.2, 4.2], ['Stairs, a broken flight', 'Wind through the boards', 'Crows', ''], {}),
    place(2, 'tower-top', 'The lookout tower, top', 4, [-1, 4.2], ['The switch house key; the valley seen from above', 'Smoke from the valley, cloud', 'Crows', "Smoke where Bravo came down; the mansion's roof"], {}),
    place(2, 'switch', 'The switch house', 2, [5.6, 7], ['The breakers for the gondola line', 'Sparking contacts', '', ''], {}),
    place(2, 'line-track', 'The power line track', 5, [7.8, 7], ['The track under the line to the gondola, a gate at its end', 'The cable humming', 'Adders', ''], {}),

    // Act 2, east: the operator's cottage, the quarry and the mine; the summit above.
    place(2, 'east-path', 'The east path', 4, [14.4, 5.6], ['The path from the gondola station along the slope', 'Grass, a windsock', 'Crows', ''], {}),
    place(2, 'cottage', "The operator's cottage", 4, [14.4, 4.2], ['His diary, the quarry office key on its hook', 'A radio left on', '', 'He went to hide in the mine'], {}),
    place(2, 'quarry', 'The quarry', 6, [16.6, 5.6], ['The quarry floor, the crane, the office', 'Dust blowing off the cut', 'Cerberus', ''], {}),
    place(2, 'quarry-office', 'The quarry office', 2, [16.6, 4.2], ['Dynamite in a locker', 'A clock still ticking', '', ''], {}),
    place(2, 'mine-entrance', 'The mine entrance', 3, [18.8, 5.6], ['A rockfall across the adit', 'Dust settling', '', 'Someone brought it down on purpose'], {}),
    place(2, 'tunnel', 'The mine tunnel', 5, [18.8, 4.2], ['Rails, timbers, lamps on a cable', 'Lamps swinging', 'Web Spinners', ''], {}),
    place(2, 'mine-office', 'The mine office', 2, [21, 4.2], ['The mine map: the pump and the lift', 'A dripping roof', '', ''], {}),
    place(2, 'junction', 'The mine junction', 5, [18.8, 2.8], ['The pump house, the lift, a flooded way down', 'Water rising in the sump', 'Web Spinners', ''], {}),
    place(2, 'gallery', 'The flooded gallery', 4, [16.6, 2.8], ['The operator, drowned, his key on its chain', 'Water draining away', 'A zombie', 'He hid down here and was bitten anyway'], {}),
    place(2, 'mine-lift', 'The mine lift', 2, [18.8, 1.4], ['The cage up to the summit', 'The cable turning', '', ''], {}),
    place(2, 'summit-trail', 'The summit trail', 4, [18.8, 0], ['Bare rock above the trees', 'Cloud blowing over', 'Crows', ''], {}),
    place(2, 'weather', 'The weather station', 3, [16.6, 0], ['A radio that still works', 'The anemometer spinning', '', "Alpha team's helicopter is coming at dusk"], {}),
    place(2, 'mast', 'The radio mast', 3, [14.4, 0], ['Supplies left by the engineers', 'The mast\'s warning light', '', ''], {}),

    // Act 3: down the mountain.
    place(3, 'car', 'The gondola car', 2, [10, 7], ['Inside the car, halfway down', 'Trees passing below, the car swaying', 'Crows at the windows', 'The valley at dusk'], {}),
    place(3, 'pylon', 'The pylon', 3, [10, 8.4], ['The ladder down the pylon', 'The cable shaking', 'Crows', ''], {}),
    place(3, 'valley-path', 'The valley path', 5, [10, 9.8], ['A path through the valley forest', 'Mist between the trunks', 'Cerberus', 'The mansion is somewhere below'], {}),
    place(3, 'lower-yard', 'The lower station yard', 4, [12.2, 9.8], ['The lower station, its yard', 'A flag', '', ''], {}),
    place(3, 'lower-station', 'The lower station', 3, [14.4, 9.8], ["The keeper's log", 'A kettle, cold', '', 'The estate gardener came up for supplies'], {}),
    place(3, 'crash', 'The helicopter', 5, [7.8, 9.8], ["Bravo's helicopter, where they came down; a crowbar in the cargo bay", 'Smoke, a rotor turning in the wind', '', 'Kevin stayed with it. He is dead in his seat'], {}),
    place(3, 'creek', 'The creek', 5, [10, 11.2], ['A ford, the lodge across it', 'Running water', 'Adders', ''], {}),
    place(3, 'lodge', "The gardener's lodge", 4, [12.2, 11.2], ['The back gate key, his diary', 'A lamp left burning', '', 'He scratched himself raw'], {}),
    place(3, 'estate-wall', 'The estate wall', 5, [10, 12.6], ['The back gate into the Spencer estate', 'Ivy in the wind', 'Crows', 'The mansion over the wall'], {}),
    place(3, 'kennels', 'The kennels', 5, [10, 14], ['Empty runs, broken chains', 'A gate banging', 'Cerberus, a pack', 'The dogs on the mountain came from here'], {}),
    place(3, 'back-garden', 'The back garden', 6, [10, 15.4], ['Hedges, the cellar doors', 'Fountain water, moths at a lamp', 'A zombie', ''], {}),
    place(3, 'garden-shed', 'The garden shed', 2, [12.2, 15.4], ['The cellar key on a board', 'A cobweb trembling', '', ''], {}),

    // Act 4: the mansion.
    place(4, 'cellar', 'The cellar', 4, [10, 16.8], ['A rack across a crawl passage', 'Candle flames', 'A zombie servant', ''], {}),
    place(4, 'wine', 'The wine store', 2, [12.2, 16.8], ['Racks, a first aid spray', 'Drips', '', ''], {}),
    place(4, 'crawl', 'Under the floor', 3, [10, 18.2], ['The passage under the floorboards, a hatch', 'Light through the boards, footsteps overhead', '', ''], {}),
    place(4, 'save', 'The save room', 6, [10, 19.6], ['Where Chris finds her', 'The typewriter lamp', '', 'She sleeps; Chris walks in'], { existing: 'ROOM1000.RDT' }),
  ],
  links: [
    link('ridge', 'trail', 'walk'),
    link('trail', 'yard', 'walk'),
    link('yard', 'cabin', 'door'),
    link('yard', 'shed', 'door', 'unlock-shed'),
    link('yard', 'bridge', 'walk', 'winch-pine'),
    link('bridge', 'platform', 'walk'),
    link('platform', 'booth', 'door'),

    link('yard', 'woods', 'walk', 'dog'),
    link('woods', 'den', 'walk'),
    link('woods', 'logging-road', 'walk'),
    link('logging-road', 'camp-gate', 'walk'),
    link('camp-gate', 'camp-yard', 'walk'),
    link('camp-yard', 'bunkhouse', 'door'),
    link('camp-yard', 'mess', 'door'),
    link('camp-yard', 'office', 'door', 'office-key'),
    link('camp-yard', 'depot', 'door', 'cut-depot'),
    link('camp-yard', 'workshop', 'door', 'safe'),
    link('camp-yard', 'sawmill', 'walk'),
    link('sawmill', 'pond', 'walk'),
    link('pond', 'flume', 'walk'),
    link('flume', 'bridge', 'ride', 'flume-ride', true),

    link('yard', 'road', 'walk'),
    link('road', 'washout', 'walk', 'cut-chain'),
    link('washout', 'generator', 'walk'),
    link('washout', 'tower-foot', 'walk'),
    link('tower-foot', 'tower-stairs', 'door', 'tower-door'),
    link('tower-stairs', 'tower-top', 'ladder'),
    link('generator', 'switch', 'door', 'switch-key'),
    link('switch', 'line-track', 'walk'),
    link('line-track', 'platform', 'walk', 'line-gate', true),

    link('platform', 'east-path', 'walk'),
    link('east-path', 'cottage', 'door'),
    link('east-path', 'quarry', 'walk'),
    link('quarry', 'quarry-office', 'door', 'quarry-key'),
    link('quarry', 'mine-entrance', 'walk'),
    link('mine-entrance', 'tunnel', 'walk', 'blast'),
    link('tunnel', 'mine-office', 'door'),
    link('tunnel', 'junction', 'walk'),
    link('junction', 'gallery', 'walk', 'drain'),
    link('junction', 'mine-lift', 'walk'),
    link('mine-lift', 'summit-trail', 'lift', 'lift-up'),
    link('summit-trail', 'weather', 'door'),
    link('summit-trail', 'mast', 'walk'),

    link('platform', 'car', 'ride', 'gondola-runs'),
    link('car', 'pylon', 'ladder', 'ride'),
    link('pylon', 'valley-path', 'ladder', 'pylon-down'),
    link('valley-path', 'crash', 'walk'),
    link('valley-path', 'lower-yard', 'walk'),
    link('lower-yard', 'lower-station', 'door'),
    link('valley-path', 'creek', 'walk'),
    link('creek', 'lodge', 'door', 'pry-lodge'),
    link('creek', 'estate-wall', 'walk'),
    link('estate-wall', 'kennels', 'walk', 'open-gate'),
    link('kennels', 'back-garden', 'walk'),
    link('back-garden', 'garden-shed', 'door'),
    link('back-garden', 'cellar', 'door', 'bulkhead'),

    link('cellar', 'wine', 'door'),
    link('cellar', 'crawl', 'walk', 'push-rack'),
    link('crawl', 'save', 'ladder', 'hatch'),
  ],
  steps: [
    // Act 1.
    step(1, 'arrive', 'yard', 'learn', [], 'Reach the ranger station', { built: true }),
    step(1, 'logbook', 'cabin', 'learn', ['arrive'], "Read the logbook: the crank's in the shed", { built: true, optional: true }),
    step(1, 'shed-key', 'cabin', 'find', ['arrive'], 'Take the shed key', { built: true }),
    step(1, 'dog', 'yard', 'do', ['shed-key'], 'Survive the dog that comes for her', { built: true }),
    step(1, 'unlock-shed', 'yard', 'do', ['shed-key'], 'Unlock the shed', { built: true }),
    step(1, 'crank', 'shed', 'find', ['unlock-shed'], 'Take the winch crank', { built: true }),
    step(1, 'winch-pine', 'yard', 'do', ['crank'], 'Winch the pine off the trail', { built: true }),
    step(1, 'gondola-dead', 'platform', 'learn', ['winch-pine'], 'The gondola hangs dead at the platform'),
    step(1, 'duty-board', 'booth', 'learn', ['winch-pine'], 'The duty board: no power, a sheared cog, a fuse out, his key gone'),
    step(1, 'act1-end', 'booth', 'milestone', ['gondola-dead', 'duty-board'], 'She knows what the gondola needs'),

    // Act 2, north.
    step(2, 'truck-keys', 'den', 'find', ['dog'], "Find the ranger in the hollow: his keys"),
    step(2, 'cutters', 'yard', 'find', ['truck-keys'], "Open the truck's toolbox: bolt cutters"),
    step(2, 'calendar', 'bunkhouse', 'learn', ['dog'], "The bunkhouse calendar: the safe's numbers"),
    step(2, 'office-key', 'mess', 'find', ['dog'], 'Take the office key from the dead cook'),
    step(2, 'safe', 'office', 'find', ['office-key', 'calendar'], "Open the foreman's safe: the workshop key"),
    step(2, 'mill-race', 'pond', 'do', ['crank', 'dog'], 'Open the sluice with the winch crank: the mill runs'),
    step(2, 'crane', 'sawmill', 'do', ['mill-race'], 'Run the log crane: the stack lifts off the crate'),
    step(2, 'cog', 'workshop', 'find', ['crane', 'safe'], 'Take the spare drive cog'),
    step(2, 'cut-depot', 'camp-yard', 'do', ['cutters'], "Cut the depot's padlock"),
    step(2, 'jerrycan', 'shed', 'find', ['unlock-shed'], 'Take the empty jerrycan'),
    step(2, 'fuel', 'depot', 'find', ['cut-depot', 'jerrycan'], 'Fill the jerrycan with diesel'),
    step(2, 'flume-ride', 'flume', 'shortcut', ['mill-race'], 'Ride the flume down to the gorge', { optional: true }),

    // Act 2, west.
    step(2, 'cut-chain', 'road', 'do', ['cutters'], 'Cut the chain on the road gate'),
    step(2, 'generator-on', 'generator', 'do', ['cut-chain', 'fuel'], 'Fuel the generator: the station lights come on'),
    step(2, 'tower-door', 'tower-foot', 'do', ['cut-chain', 'truck-keys'], "Unlock the tower with the ranger's keys"),
    step(2, 'switch-key', 'tower-top', 'find', ['tower-door'], "The switch house key; Bravo's smoke, the mansion's roof"),
    step(2, 'line-on', 'switch', 'do', ['switch-key', 'generator-on'], 'Close the breakers: power down the line'),
    step(2, 'line-gate', 'line-track', 'shortcut', ['line-on'], 'Open the line gate to the gondola station', { optional: true }),

    // Act 2, east and the summit.
    step(2, 'diary', 'cottage', 'learn', ['winch-pine'], "The operator's diary: he went to hide in the mine", { optional: true }),
    step(2, 'quarry-key', 'cottage', 'find', ['winch-pine'], 'Take the quarry office key'),
    step(2, 'dynamite', 'quarry-office', 'find', ['quarry-key'], 'Take the dynamite'),
    step(2, 'blast', 'mine-entrance', 'do', ['dynamite'], 'Blast the rockfall at the mine mouth'),
    step(2, 'mine-map', 'mine-office', 'learn', ['blast'], 'The mine map: the pump and the lift', { optional: true }),
    step(2, 'drain', 'junction', 'do', ['blast', 'generator-on'], 'Run the mine pump: the gallery drains'),
    step(2, 'op-key', 'gallery', 'find', ['drain'], "Take the operator's key from his body"),
    step(2, 'lift-up', 'mine-lift', 'do', ['blast', 'generator-on'], 'Ride the mine lift up to the summit', { optional: true }),
    step(2, 'radio', 'weather', 'learn', ['lift-up'], "The weather radio: Alpha's helicopter comes at dusk", { optional: true }),
    step(2, 'supplies', 'mast', 'find', ['lift-up'], 'Ammunition and a first aid spray', { optional: true }),

    // Act 2: the gondola.
    step(2, 'fuses', 'shed', 'find', ['unlock-shed'], "Take the ranger's spare fuses"),
    step(2, 'gondola-runs', 'platform', 'milestone', ['act1-end', 'line-on', 'cog', 'op-key', 'fuses'], 'Fit the cog and the fuse, turn the key: the gondola runs'),

    // Act 3.
    step(3, 'ride', 'car', 'do', ['gondola-runs'], 'Ride down; the car stops at a pylon'),
    step(3, 'pylon-down', 'pylon', 'do', ['ride'], 'Climb down the pylon ladder'),
    step(3, 'keeper-log', 'lower-station', 'learn', ['pylon-down'], "The keeper's log: the estate gardener", { optional: true }),
    step(3, 'crowbar', 'crash', 'find', ['pylon-down'], "Bravo's helicopter: Kevin, and a crowbar"),
    step(3, 'pry-lodge', 'creek', 'do', ['crowbar'], "Prise open the lodge's door"),
    step(3, 'gate-key', 'lodge', 'find', ['pry-lodge'], "Take the estate's back gate key"),
    step(3, 'gardener-diary', 'lodge', 'learn', ['pry-lodge'], "The gardener's diary: the itching", { optional: true }),
    step(3, 'open-gate', 'estate-wall', 'do', ['gate-key'], 'Open the back gate into the estate'),
    step(3, 'cellar-key', 'garden-shed', 'find', ['open-gate'], 'Take the cellar key'),
    step(3, 'bulkhead', 'back-garden', 'milestone', ['cellar-key'], 'Unlock the cellar doors'),

    // Act 4.
    step(4, 'push-rack', 'cellar', 'do', ['bulkhead'], 'Push the rack aside: a crawl passage'),
    step(4, 'wine-aid', 'wine', 'find', ['bulkhead'], 'A first aid spray', { optional: true }),
    step(4, 'hatch', 'crawl', 'do', ['push-rack'], 'Up through the hatch'),
    step(4, 'sleep', 'save', 'do', ['hatch'], 'Too tired to go on, she falls asleep'),
    step(4, 'chris', 'save', 'learn', ['sleep'], 'Footsteps. Chris walks in', { built: true }),
    step(4, 'credits', 'save', 'goal', ['chris'], 'Her credits'),
  ],
};

/** The mansion, for scale: its two floors' room files (USA/STAGE6 and STAGE7, Chris's copies), counted from the game. */
export const MANSION = { rooms: 58, cameras: 295 } as const;
