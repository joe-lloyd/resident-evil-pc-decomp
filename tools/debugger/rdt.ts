// What the dashboard draws of a room, read from its RDT (docs/RDT_FILE_FORMAT.md):
// the collision shapes from tools/harness/room-map.ts, each camera's eye and
// target, the camera switch zones grouped by the camera they belong to, and
// the floor: where the player's centre can stand, split into the separate
// areas the collision leaves.
import { readFileSync } from 'node:fs';
import { blocked, collisionShapes, roomFile, type Shape } from '../harness/room-map.ts';

export interface Camera {
  x: number;
  z: number;
  targetX: number;
  targetZ: number;
}

/** A switch zone of camera `from`: standing in the quad cuts to camera `to`. */
export interface Zone {
  from: number;
  to: number;
  quad: [number, number][];
}

/**
 * The free cells of a grid over the shapes' bounds, as row runs labelled by
 * the area they belong to. The new rooms close their floor in with boxes
 * that reach far past it, so the area she stands in is what the map frames.
 */
export interface Floor {
  x0: number;
  z0: number;
  cell: number;
  /** [area, row, first column, last column] */
  runs: [number, number, number, number][];
  areas: { x0: number; z0: number; x1: number; z1: number }[];
}

export interface RoomMap {
  file: string;
  shapes: Shape[];
  cameras: Camera[];
  zones: Zone[];
  floor: Floor;
}

export function floor(shapes: Shape[], cell = 200): Floor {
  if (!shapes.length) return { x0: 0, z0: 0, cell, runs: [], areas: [] };
  const x0 = Math.min(...shapes.map((s) => s.xMin));
  const z0 = Math.min(...shapes.map((s) => s.zMin));
  const w = Math.max(1, Math.ceil((Math.max(...shapes.map((s) => s.xMax)) - x0) / cell));
  const h = Math.max(1, Math.ceil((Math.max(...shapes.map((s) => s.zMax)) - z0) / cell));
  // -1 blocked, 0 free and not yet labelled, n > 0 area n - 1.
  const label = new Int32Array(w * h);
  for (let r = 0; r < h; r++) {
    for (let c = 0; c < w; c++) if (blocked(shapes, x0 + (c + 0.5) * cell, z0 + (r + 0.5) * cell)) label[r * w + c] = -1;
  }
  const areas: Floor['areas'] = [];
  for (let start = 0; start < label.length; start++) {
    if (label[start] !== 0) continue;
    const id = areas.length + 1;
    const area = { x0: Infinity, z0: Infinity, x1: -Infinity, z1: -Infinity };
    const stack = [start];
    label[start] = id;
    while (stack.length) {
      const i = stack.pop()!;
      const r = Math.floor(i / w), c = i % w;
      area.x0 = Math.min(area.x0, x0 + c * cell);
      area.x1 = Math.max(area.x1, x0 + (c + 1) * cell);
      area.z0 = Math.min(area.z0, z0 + r * cell);
      area.z1 = Math.max(area.z1, z0 + (r + 1) * cell);
      for (const [nr, nc] of [[r - 1, c], [r + 1, c], [r, c - 1], [r, c + 1]]) {
        if (nr < 0 || nc < 0 || nr >= h || nc >= w || label[nr * w + nc] !== 0) continue;
        label[nr * w + nc] = id;
        stack.push(nr * w + nc);
      }
    }
    areas.push(area);
  }
  const runs: Floor['runs'] = [];
  for (let r = 0; r < h; r++) {
    for (let c = 0; c < w; ) {
      const id = label[r * w + c];
      let end = c;
      while (end + 1 < w && label[r * w + end + 1] === id) end++;
      if (id > 0) runs.push([id - 1, r, c, end]);
      c = end + 1;
    }
  }
  return { x0, z0, cell, runs, areas };
}

/** Cameras are 0x2C-byte records right after the 0x94-byte header; the view matrix block starts at +0x08. */
function cameras(view: DataView): Camera[] {
  const count = view.getUint8(0x01);
  const out: Camera[] = [];
  for (let i = 0; i < count; i++) {
    const at = 0x94 + i * 0x2c;
    out.push({
      x: view.getInt32(at + 0x08, true),
      z: view.getInt32(at + 0x10, true),
      targetX: view.getInt32(at + 0x14, true),
      targetZ: view.getInt32(at + 0x1c, true),
    });
  }
  return out;
}

/**
 * The switch zone table at RDT+0x48 has no count: the game walks it by camFrom
 * (check_camera_switch, Room.cpp). Every group opens with a header record whose
 * quad is not tested, so it is skipped. The walk stops at the first camFrom that
 * is not a camera of this room, which is where the table ends.
 */
function zones(view: DataView, cameraCount: number): Zone[] {
  const out: Zone[] = [];
  let group = -1;
  for (let at = view.getUint32(0x48, true); at + 0x14 <= view.byteLength; at += 0x14) {
    const to = view.getUint16(at, true);
    const from = view.getUint16(at + 2, true);
    if (from >= cameraCount) break;
    if (from !== group) {
      group = from;
      continue;
    }
    const quad: [number, number][] = [];
    for (let c = 0; c < 4; c++) quad.push([view.getUint16(at + 4 + c * 4, true), view.getUint16(at + 6 + c * 4, true)]);
    out.push({ from, to, quad });
  }
  return out;
}

export function loadRoomMap(dirs: string[], stage: number, room: number, collisionFlags?: number): RoomMap {
  const file = roomFile(dirs, stage, room);
  const rdt = new Uint8Array(readFileSync(file));
  const view = new DataView(rdt.buffer, rdt.byteOffset, rdt.byteLength);
  const cams = cameras(view);
  const shapes = collisionShapes(rdt, collisionFlags);
  return { file, shapes, cameras: cams, zones: zones(view, cams.length), floor: floor(shapes) };
}
