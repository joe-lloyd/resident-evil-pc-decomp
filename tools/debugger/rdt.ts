// What the dashboard draws of a room, read from its RDT (docs/RDT_FILE_FORMAT.md):
// the collision shapes from tools/harness/room-map.ts, each camera's eye and
// target, and the camera switch zones grouped by the camera they belong to.
import { readFileSync } from 'node:fs';
import { collisionShapes, roomFile, type Shape } from '../harness/room-map.ts';

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

export interface RoomMap {
  file: string;
  shapes: Shape[];
  cameras: Camera[];
  zones: Zone[];
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
  return { file, shapes: collisionShapes(rdt, collisionFlags), cameras: cams, zones: zones(view, cams.length) };
}
