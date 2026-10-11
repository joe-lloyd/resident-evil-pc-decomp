// Rebecca's police ID for the character select screen, built from the
// player's own files: the select-screen sheet (DATA/Select_b.tim, Chris's
// card and Jill's ID) and the status-screen faces (DATA/Statface.tim, where
// her face is the bottom-right one). Jill's ID is copied to the sheet's free
// corner, her name, number, signature and photo are taken off it, and
// Rebecca's face and lettering go on (card/rebecca-id-lettering.png, drawn
// once by card/lettering.py: black is ink).
//
// The select screen draws a card as the shared S.T.A.R.S. badge half and an
// ID half per character (CharacterSelectionScreen.cpp): Chris's ID is at
// (0x50, 0), Jill's at (0, 0x80) and Rebecca's goes at (0x70, 0x80).
import type { Image } from '../harness/image.ts';

const SHEET = 256;
const ID_W = 0x70;
const ID_H = 0x80;
const JILL = { x: 0, y: 0x80 };
export const REBECCA_ID = { x: 0x70, y: 0x80 };
/** Her face in Statface.tim (64 x 64, four 32 x 32 faces), less its border, and where the photo goes on the ID. */
const FACE = { x: 34, y: 33, w: 27, h: 29 };
const PHOTO = { x: 5, y: 72, w: 40, h: 48 };
/** The card's typed ink. */
const INK = [20, 20, 16] as const;

interface Tim {
  readonly bytes: Uint8Array;
  /** Offset of the pixel data and the image width in pixels. */
  readonly pixels: number;
  readonly width: number;
  readonly height: number;
  readonly bpp: 8 | 16;
  readonly clut?: Uint16Array;
}

function readTim(bytes: Uint8Array, what: string): Tim {
  const v = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (v.getUint32(0, true) !== 0x10) throw new Error(`${what} is not a TIM`);
  const flags = v.getUint32(4, true);
  let p = 8;
  let clut: Uint16Array | undefined;
  if (flags & 8) {
    const len = v.getUint32(p, true);
    const n = v.getUint16(p + 8, true) * v.getUint16(p + 10, true);
    clut = new Uint16Array(n);
    for (let i = 0; i < n; i++) clut[i] = v.getUint16(p + 12 + i * 2, true);
    p += len;
  }
  const bpp = (flags & 3) === 1 ? 8 : (flags & 3) === 2 ? 16 : undefined;
  if (!bpp) throw new Error(`${what}: only 8 and 16 bpp TIMs are handled`);
  const words = v.getUint16(p + 8, true);
  return { bytes, pixels: p + 12, width: bpp === 8 ? words * 2 : words, height: v.getUint16(p + 10, true), bpp, clut };
}

const to8 = (c: number): [number, number, number] => [((c & 31) * 255) / 31, (((c >> 5) & 31) * 255) / 31, (((c >> 10) & 31) * 255) / 31];
const to15 = (r: number, g: number, b: number) => {
  const ch = (x: number) => Math.min(31, Math.max(0, Math.round((x * 31) / 255)));
  return (ch(b) << 10) | (ch(g) << 5) | ch(r) || 0x8000;
};

/** The select-screen sheet with Rebecca's ID added. */
export function buildCardSheet(selectB: Uint8Array, statface: Uint8Array, lettering: Image): Uint8Array {
  const sheet = readTim(selectB, 'Select_b.tim');
  const faces = readTim(statface, 'Statface.tim');
  if (sheet.bpp !== 16 || sheet.width !== SHEET || sheet.height !== SHEET) throw new Error('Select_b.tim is not the 256 x 256 16 bpp sheet');
  if (faces.bpp !== 8 || !faces.clut) throw new Error('Statface.tim is not an 8 bpp TIM with a palette');
  if (lettering.width !== ID_W || lettering.height !== ID_H) throw new Error(`the lettering must be ${ID_W} x ${ID_H}`);
  const out = selectB.slice();
  const ov = new DataView(out.buffer, out.byteOffset, out.byteLength);
  const at = (x: number, y: number) => sheet.pixels + (y * SHEET + x) * 2;
  const get = (x: number, y: number) => ov.getUint16(at(REBECCA_ID.x + x, REBECCA_ID.y + y), true);
  const set = (x: number, y: number, c: number) => ov.setUint16(at(REBECCA_ID.x + x, REBECCA_ID.y + y), c, true);

  // Jill's ID, then her name, signature, number and photo papered over with
  // the card from just above each one.
  for (let y = 0; y < ID_H; y++) for (let x = 0; x < ID_W; x++) set(x, y, ov.getUint16(at(JILL.x + x, JILL.y + y), true));
  const paper = (x0: number, y0: number, x1: number, y1: number, fromY: number) => {
    for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) set(x, y, get(x, fromY));
  };
  paper(2, 27, 110, 40, 26); // name
  paper(2, 43, 110, 59, 42); // signature
  paper(6, 61, 40, 66, 67); // the signature's tail below its line
  paper(52, 68, 104, 80, 67); // number

  // Her photo: the status face, scaled smoothly into the photo's place.
  const face = (x: number, y: number) => to8(faces.clut![faces.bytes[faces.pixels + y * faces.width + x]!]!);
  for (let y = 0; y < PHOTO.h; y++) {
    for (let x = 0; x < PHOTO.w; x++) {
      const fx = FACE.x + ((x + 0.5) * FACE.w) / PHOTO.w - 0.5;
      const fy = FACE.y + ((y + 0.5) * FACE.h) / PHOTO.h - 0.5;
      const x0 = Math.floor(fx);
      const y0 = Math.floor(fy);
      const tx = fx - x0;
      const ty = fy - y0;
      const mix = [0, 0, 0];
      for (const [dx, dy, w] of [[0, 0, (1 - tx) * (1 - ty)], [1, 0, tx * (1 - ty)], [0, 1, (1 - tx) * ty], [1, 1, tx * ty]] as const) {
        const c = face(x0 + dx, y0 + dy);
        for (let k = 0; k < 3; k++) mix[k]! += c[k]! * w;
      }
      set(PHOTO.x + x, PHOTO.y + y, to15(mix[0]!, mix[1]!, mix[2]!));
    }
  }

  // Her lettering, inked over the card.
  for (let y = 0; y < ID_H; y++) {
    for (let x = 0; x < ID_W; x++) {
      const a = 1 - lettering.rgb[(y * ID_W + x) * 3]! / 255;
      if (a < 0.05) continue;
      const [r, g, b] = to8(get(x, y));
      set(x, y, to15(r * (1 - a) + INK[0] * a, g * (1 - a) + INK[1] * a, b * (1 - a) + INK[2] * a));
    }
  }
  return out;
}
