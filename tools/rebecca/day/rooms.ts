// The rooms of Rebecca's day, in the order she reaches them. Each room's
// scene, renders, script and messages are in its folder under day/; room.ts
// builds it. Room ids come from the free slots in stages 2 to 4 (Stage3 to
// Stage5 files); docs/REBECCA_DAY.md has the plan.
import type { DayRoom } from './room.ts';

/**
 * The mountain trail from the ridge down to the ranger station, early
 * morning. Its walkable strip and cameras are the ones the trail has always
 * had, and so is the cut between them at Z 8000.
 */
export const trail: DayRoom = {
  slug: 'trail',
  stage: 2,
  room: 0x12,
  donor: 'Stage3/ROOM3000.RDT',
  // Low sun from the east through the trunks; sky; the mist's grey.
  ambient: [1050, 1000, 980],
  lights: [
    { x: 30000, y: -6000, z: 6000, rgb: [85, 72, 55], radius: 40000 },
    { x: 3500, y: -8000, z: 8000, rgb: [45, 50, 62], radius: 30000 },
    { x: 3500, y: -2000, z: 15000, rgb: [30, 32, 34], radius: 12000 },
  ],
  cameraFloor: [
    { x0: 0, z0: 0, x1: 9000, z1: 8000 }, // camera 0: the top half, from behind the top
    { x0: 0, z0: 8000, x1: 9000, z1: 22000 }, // camera 1: the lower half, from beyond the foot
  ],
  footsteps: 0x2d,
};

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
  cameraFloor: 'auto',
  footsteps: 0x2d,
};

/** Where a new game stands: on the ridge, near the edge, facing out over the valley (+Z is angle 0xC00). */
export const dayStart = { stage: ridge.stage, room: ridge.room, x: 7000, z: 8800, angle: 0xc00 } as const;

/** The ranger's lookout, inside: the log cabin by the yard, in the morning (game units = metres * 1700). */
export const lookout: DayRoom = {
  slug: 'lookout',
  stage: 2,
  room: 0x14,
  donor: 'Stage3/ROOM3000.RDT',
  // Indoors in the morning: the oil lamp, sun through the broken east window, a dim fill.
  ambient: [900, 850, 800],
  lights: [
    { x: 8075, y: -1615, z: 6494, rgb: [120, 80, 45], radius: 9000 },
    { x: 11730, y: -2550, z: 5100, rgb: [80, 74, 64], radius: 10000 },
    { x: 7650, y: -3570, z: 7140, rgb: [45, 46, 52], radius: 14000 },
  ],
  cameraFloor: 'auto',
  footsteps: 0x2d,
  itemModels: [
    { from: 'Stage3/ROOM3090.RDT', index: 0 }, // F-Aid Spray
    { from: 'Stage1/ROOM1130.RDT', index: 0 }, // Small Key, as the shed key
  ],
};

/**
 * The ranger station's yard, outside the lookout: the cabin, the shed, the
 * truck and its winch, and the pine down across the trail (game units =
 * metres * 1700).
 */
export const yard: DayRoom = {
  slug: 'yard',
  stage: 2,
  room: 0x15,
  donor: 'Stage3/ROOM3000.RDT',
  // Morning sun from the south-east, sky from above, the hazard lights' glow.
  ambient: [1150, 1100, 1050],
  lights: [
    { x: 37400, y: -15300, z: 27200, rgb: [95, 85, 70], radius: 40000 },
    { x: 17000, y: -17000, z: 11900, rgb: [55, 62, 75], radius: 40000 },
    { x: 19550, y: -1700, z: 18360, rgb: [60, 35, 10], radius: 5100 },
  ],
  cameraFloor: 'auto',
  footsteps: 0x2d,
  itemModels: [],
};

/** The ranger's tool shed, off the yard: the winch's crank on the bench (game units = metres * 1700). */
export const shed: DayRoom = {
  slug: 'shed',
  stage: 2,
  room: 0x16,
  donor: 'Stage3/ROOM3000.RDT',
  // A bare bulb and daylight through the boards.
  ambient: [850, 800, 750],
  lights: [
    { x: 3910, y: -2550, z: 3570, rgb: [110, 85, 55], radius: 6000 },
    { x: 4250, y: -2380, z: 5440, rgb: [60, 58, 52], radius: 6000 },
    { x: 3910, y: -2720, z: 3570, rgb: [30, 32, 38], radius: 9000 },
  ],
  cameraFloor: 'auto',
  footsteps: 0x2d,
  itemModels: [{ from: 'Stage3/ROOM30A0.RDT', index: 1 }], // Hex Crank, as the winch's crank
};

/** The ravine bridge below the station: a plank footbridge over a gorge, adders in the grass (game units = metres * 1700). */
export const bridge: DayRoom = {
  slug: 'bridge',
  stage: 2,
  room: 0x17,
  donor: 'Stage3/ROOM3000.RDT',
  // Mid-morning: the sun high over the gorge, the sky, light off the far cliff.
  ambient: [1200, 1150, 1100],
  lights: [
    { x: 20400, y: -20400, z: 5100, rgb: [95, 88, 72], radius: 60000 },
    { x: 10200, y: -17000, z: 20400, rgb: [55, 62, 78], radius: 60000 },
    { x: 10200, y: 5100, z: 20400, rgb: [30, 34, 34], radius: 30000 },
  ],
  cameraFloor: 'auto',
  footsteps: 0x2d,
};

export const dayRooms: readonly DayRoom[] = [ridge, trail, lookout, yard, shed, bridge];
