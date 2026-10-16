// The cutscenes of her day, most important first. Each is a room, what
// starts it, its people and its beats (day/cutscene.ts); scripts.ts writes
// them into the rooms' scripts. docs/REBECCA_CUTSCENES.md says how to add one.
//
// Positions are game units: a scene's metres times 1700 (blender/reb.py), its
// x and y becoming x and z. Cameras are numbered as the scene's room.camera
// calls are.
import { anim, cut, face, fade, give, gone, line, place, say, scd, shake, wait, walk, type Cutscene } from './cutscene.ts';
import { LOSS_START } from './gear.ts';

export const CUTSCENES: readonly Cutscene[] = [
  {
    // The booth (day/booth/scene.py): the wall phone hangs by its cord on the
    // east wall at (4.15, 2.7) m. Camera 1 looks at it from the north-west.
    id: 'cut-phone',
    room: 'booth',
    trigger: { on: 'check', check: 'The handset' },
    after: "The handset, back on its hook.\nHal's in the mine. He has the key.",
    beats: [
      cut(1),
      face('her', { x: 7140, z: 4590 }),
      say("The handset's still warm. Someone's breathing on the line."),
      say('"Hello? Is anyone there?"'),
      wait(20),
      line('hal', '"...Who\'s this? You\'re not one of my crew."'),
      say('"Rebecca Chambers, S.T.A.R.S. Who are you?"'),
      line('hal', '"Hal. I run the gondola. I\'m down in the mine."'),
      say('"I need to get off this mountain. Can it run?"'),
      line('hal', '"Not as she is. Get the generator going,"'),
      line('hal', '"then throw the breakers. That powers the line."'),
      line('hal', '"The drive cog sheared. There\'s a spare at the camp."'),
      line('hal', '"And F3 blew. The rangers keep fuses in their shed."'),
      line('hal', '"I\'ve got the key. Come and find me... I got bit."'),
      wait(30),
      say('"Hal? Hal!"'),
      say("The line's dead.\nHe's in the mine, and he has the key."),
    ],
  },
  {
    // The woods (day/woods/scene.py): she comes in from the yard at the west
    // edge. Dana kneels over the drag marks by the flashlight; the drag goes
    // north past the blowdown to the hollow (den), whose way out is at the
    // north edge. Camera 0 looks up the drag from the south-west; 4, from
    // over the old blowdown, has the two of them side by side.
    id: 'cut-partner',
    room: 'woods',
    trigger: { on: 'enter', from: 'yard' },
    cast: [{ who: 'dana', at: { x: 11300, z: 10000, angle: 1024 }, pose: [9, 24] }],
    beats: [
      cut(0),
      say('The drag marks go on into the trees. So does the blood.'),
      say("Someone's up ahead, crouched over the marks."),
      walk('her', { x: 9600, z: 10600 }),
      cut(4),
      say('"Hello?"'),
      anim('dana', 0, true),
      face('dana', { x: 9600, z: 10600 }),
      line('dana', '"Don\'t move! ...You\'re not one of them."'),
      line('dana', '"Dana Whitlock, Forest Service. Who are you?"'),
      say('"Rebecca Chambers, S.T.A.R.S. I\'m a medic."'),
      line('dana', '"These are my partner\'s tracks. The dogs took him."'),
      say('"I was at his cabin. I\'m sorry."'),
      line('dana', '"They dragged him north, into the hollow."'),
      say('"Then I\'m coming with you."'),
      line('dana', '"Stay close. They\'re fast."'),
      walk('dana', { x: 14000, z: 5600 }),
      gone('dana'),
      say("She knows these woods. I'd better keep up."),
    ],
  },
  {
    // The hollow (day/den/scene.py): she comes down from the woods at the
    // south edge. The ranger lies under the lip, his keys by him. Dana is
    // there first, kneeling by him. Camera 0 looks in from the way down, 2
    // from the east bank.
    id: 'cut-den',
    room: 'den',
    trigger: { on: 'enter', from: 'woods' },
    cast: [{ who: 'dana', at: { x: 16000, z: 10600, angle: 1024 }, pose: [9, 24] }],
    beats: [
      cut(0),
      say('The smell hits first. Then the flies.'),
      walk('her', { x: 15200, z: 13600 }),
      line('dana', '"It\'s him."'),
      anim('dana', 0, true),
      face('dana', { x: 15200, z: 13600 }),
      cut(2),
      line('dana', '"His truck keys. It\'s parked by the station."'),
      give('truck-keys'),
      line('dana', '"Take it. Get help, if there\'s any left."'),
      say('"Come with me."'),
      line('dana', '"Not yet. I\'m not leaving him like this."'),
    ],
  },
  {
    // The flooded gallery (day/gallery/scene.py), the first time in: she
    // wades down from the junction at the west end, and the floor gives way
    // under the water (gear.ts: her weapons and healing are gone). Camera 0
    // looks in from the foot of the decline.
    id: 'cut-mine-collapse',
    room: 'gallery',
    trigger: { on: 'enter', from: 'junction' },
    beats: [
      cut(0),
      say("The water's cold. It's black. I can't see the floor."),
      walk('her', { x: 6400, z: 11200 }),
      shake(true),
      scd(...LOSS_START),
      wait(25),
      say("The floor's gone under me!"),
      shake(false),
      say('My bag, the gun... gone, down there in the dark.'),
      say("I've got nothing left. Only my hands."),
    ],
  },
  {
    // The gallery again: Hal on the ore cart, by its south side. The scene
    // starts as she wades past the half-sunk cart towards him. Camera 3
    // looks back over the cart from the winze, 0 in from the decline.
    id: 'cut-hal',
    room: 'gallery',
    trigger: { on: 'zone', zone: { x0: 8000, z0: 3400, x1: 10000, z1: 10700 } },
    cast: [{ who: 'hal', at: { x: 12300, z: 9400, angle: 2048 }, after: { x: 12300, z: 9400, angle: 2048, pose: [4, 29] } }],
    beats: [
      cut(3),
      line('hal', '"Over here... Don\'t come too close."'),
      walk('her', { x: 10500, z: 9500 }),
      face('hal', { x: 10500, z: 9500 }),
      say('"Hal? I\'m Rebecca. We spoke on the phone."'),
      cut(0),
      line('hal', '"The medic. Then you know what this bite is."'),
      say('"Let me look at your arm."'),
      line('hal', '"It\'s past that. I can feel it in my blood."'),
      line('hal', '"The drive key. Take it, quick."'),
      give('op-key'),
      line('hal', '"Get that car down the mountain. Don\'t stop."'),
      anim('hal', 9),
      say('"Hal!"'),
      anim('hal', 4),
      wait(30),
      say("He's gone. There was nothing I could do."),
    ],
  },
  {
    // Bravo's helicopter (day/crash/scene.py): she comes in from the valley
    // path at the east edge. Kevin is in the pilot's seat, in the scene.
    // Camera 7 looks back down the swath to the helicopter, 3 is close on the
    // cockpit.
    id: 'cut-kevin',
    room: 'crash',
    trigger: { on: 'enter', from: 'valley-path' },
    beats: [
      cut(7),
      say('The helicopter. This is where we came down.'),
      walk('her', { x: 24500, z: 14000 }),
      cut(3),
      wait(30),
      say("Kevin. He's still belted into his seat."),
      say('He flew us out here, and he stayed with her.'),
      say('"I\'m sorry, Kevin. We never came back for you."'),
      wait(30),
    ],
  },
  {
    // The mansion's 1F save room, RE1's own (rooms/ROOM1000.c): she comes up
    // through the hatch at (5200, 5600). Rebecca waits by the item box in
    // Chris's game, at (7280, 3920); she sits down there. Chris comes in by
    // the door from the hall. Camera 0 has the item box and that door.
    // The scene is both tracker rows, cut-sleep and cut-chris.
    id: 'cut-sleep',
    room: 'save',
    trigger: { on: 'enter', from: 'crawl' },
    cast: [{ who: 'chris', at: { x: -30000, z: -30000 } }],
    beats: [
      cut(0),
      say('A typewriter. A lamp. Nothing in here wants me dead.'),
      walk('her', { x: 7100, z: 4200 }),
      face('her', { x: 5200, z: 5600 }),
      say("I can't go on. Not tonight."),
      say("I'll close my eyes. Just for a minute."),
      fade('black'),
      wait(90),
      place('chris', { x: 3550, z: 2700, angle: 0 }),
      say('...Footsteps.'),
      fade('clear'),
      walk('chris', { x: 5900, z: 4400 }),
      face('her', { x: 5900, z: 4400 }),
      line('chris', '"Freeze!"'),
      line('chris', '"...Wait. You\'re S.T.A.R.S.? Bravo team?"'),
      say('"Rebecca Chambers. I\'m the team\'s medic."'),
      line('chris', '"Chris Redfield, Alpha. Where\'s the rest of Bravo?"'),
      say('"I don\'t know. We got separated."'),
      line('chris', '"Stay here. It\'s safe. I\'ll check the house."'),
      walk('chris', { x: 3550, z: 2700 }),
      gone('chris'),
      scd('set(FG_COMMON, 36, 0);  // canon: Chris met Rebecca'),
    ],
  },
];

/**
 * FG_COMMON flags for the scenes, in order: set as each starts, so it runs
 * once. 115-129, the end of the run scripts.ts keeps for first thoughts, which
 * its 51 kit rooms leave unused (no shipped room script or engine flag uses
 * them).
 */
export const CUT_FLAGS = new Map(CUTSCENES.map((c, i) => [c.id, 115 + i]));
if (CUTSCENES.length > 15) throw new Error('the scenes have FG_COMMON 115-129, 15 flags');

export const scenesIn = (room: string) => CUTSCENES.filter((c) => c.room === room);
