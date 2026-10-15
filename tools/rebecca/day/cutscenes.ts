// The cutscenes of her day, most important first. Each is a room, what
// starts it, its people and its beats (day/cutscene.ts); scripts.ts writes
// them into the rooms' scripts. docs/REBECCA_CUTSCENES.md says how to add one.
//
// Positions are game units: a scene's metres times 1700 (blender/reb.py), its
// x and y becoming x and z. Cameras are numbered as the scene's room.camera
// calls are.
import { cut, face, line, say, wait, type Cutscene } from './cutscene.ts';

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
