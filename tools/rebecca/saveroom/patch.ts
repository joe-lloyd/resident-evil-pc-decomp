// The save room's trapdoor in her overlay: each of the room's six backgrounds
// from the player's own copy of the game with the trapdoor (rendered on a
// transparent film by hatch.py, through the room's own cameras) laid over it.
// Only the trapdoor's pixels are ours; the rest is the player's file
// unpacked and packed again.
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readPng, type Image } from '../../harness/image.ts';
import { decodeTim16, IMAGE_BYTES, TIM_HEADER_BYTES, unpackPak } from '../../harness/background.ts';
import { makePak } from '../pak.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
export const CAMERAS = 6;

/** `over` laid on `under` by its alpha. */
export function composite(under: Image, over: Image): Image {
  const alpha = over.alpha;
  if (!alpha) throw new Error('the trapdoor render has no alpha');
  if (under.width !== over.width || under.height !== over.height) throw new Error('the trapdoor render and the background differ in size');
  const rgb = Uint8Array.from(under.rgb, (u, i) => {
    const a = alpha[Math.floor(i / 3)]! / 255;
    return Math.round(u * (1 - a) + over.rgb[i]! * a);
  });
  return { width: under.width, height: under.height, rgb };
}

/** RC1000<N>.pak for each camera: the player's background with the trapdoor on it. */
export function saveRoomFiles(readPak: (name: string) => Uint8Array): { name: string; bytes: Uint8Array }[] {
  return Array.from({ length: CAMERAS }, (_, n) => {
    const name = `RC100${n}.pak`;
    const background = decodeTim16(unpackPak(readPak(name), TIM_HEADER_BYTES + IMAGE_BYTES));
    const trapdoor = readPng(path.join(here, 'renders', `closed${n}.png`));
    return { name, bytes: makePak(composite(background, trapdoor)) };
  });
}
