// The rooms of Rebecca's day, in the order she reaches them. Each room's
// scene, renders, script and messages are in its folder under day/; room.ts
// builds it. Room ids come from the free slots in stages 2 to 4 (Stage3 to
// Stage5 files); docs/REBECCA_DAY.md has the plan.
import type { DayRoom } from './room.ts';

/** The ridge: the clearing on the mountain top where the game opens, at dawn. */
export const ridge: DayRoom = {
  slug: 'ridge',
  stage: 2,
  room: 0x13,
  donor: 'Stage3/ROOM3000.RDT',
  // Dawn: a cool sky over a low warm sun.
  ambient: [1100, 1000, 1050],
  lights: [
    { x: 7000, y: -8000, z: 4000, rgb: [80, 62, 52], radius: 12000 },
    { x: 7000, y: -7000, z: 9000, rgb: [70, 58, 54], radius: 12000 },
    { x: 7000, y: -9000, z: 6500, rgb: [40, 42, 55], radius: 16000 },
  ],
  cameraFloor: [
    { x0: 3000, z0: 6000, x1: 11000, z1: 10000 }, // camera 0 looks out over the edge
    { x0: 3000, z0: 3000, x1: 13000, z1: 6000 }, // camera 1 looks back at the rock face and the way out
  ],
  footsteps: 0x2d,
};

/** Where a new game stands: on the ridge, near the edge, facing out over the valley (+Z is angle 0xC00). */
export const dayStart = { stage: ridge.stage, room: ridge.room, x: 7000, z: 8800, angle: 0xc00 } as const;

/** The ranger's lookout, inside: the log cabin below the ridge, in the morning. */
export const lookout: DayRoom = {
  slug: 'lookout',
  stage: 2,
  room: 0x14,
  donor: 'Stage3/ROOM3000.RDT',
  // Indoors in the morning: a warm lamp, daylight from the window.
  ambient: [900, 850, 800],
  lights: [
    { x: 6300, y: -1400, z: 6100, rgb: [110, 80, 50], radius: 6000 },
    { x: 4600, y: -2000, z: 3500, rgb: [70, 75, 85], radius: 6000 },
    { x: 6000, y: -2400, z: 5500, rgb: [40, 40, 45], radius: 9000 },
  ],
  cameraFloor: [
    { x0: 3000, z0: 3000, x1: 9000, z1: 5500 }, // camera 0, from the south-west, at the desk and bunk
    { x0: 3000, z0: 5500, x1: 9000, z1: 9000 }, // camera 1, from the north-east, at the stove and door
  ],
  footsteps: 0x2d,
  itemModels: [
    { from: 'Stage3/ROOM3090.RDT', index: 0 }, // F-Aid Spray
    { from: 'Stage1/ROOM1130.RDT', index: 0 }, // Small Key, as the ranger's key
  ],
};

export const dayRooms: readonly DayRoom[] = [ridge, lookout];
