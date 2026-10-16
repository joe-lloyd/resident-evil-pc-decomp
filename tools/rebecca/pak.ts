// Write room backgrounds in the PC format: a 320x240 16 bpp TIM, LZW packed
// for unpack_pakfile_ (0x00425ab0). A port of tools/bss_to_pak.py's
// make_tim and lzw_pack; tools/harness/background.ts reads the result back.
import type { Image } from '../harness/image.ts';

const WIDTH = 320;
const HEIGHT = 240;

/** 8 bits per channel to the PS1's 5, rounded the way Capcom's conversion was. */
function to555(r: number, g: number, b: number): number {
  const ch = (v: number) => Math.min((v + 4) >> 3, 31);
  return (ch(b) << 10) | (ch(g) << 5) | ch(r);
}

/** The header every shipped background carries: 16 bpp, VRAM (0, 240), 320x240. */
export function makeTim(image: Image): Uint8Array {
  if (image.width !== WIDTH || image.height !== HEIGHT) {
    throw new Error(`a background must be ${WIDTH}x${HEIGHT}, got ${image.width}x${image.height}`);
  }
  const pixels = WIDTH * HEIGHT * 2;
  const tim = new Uint8Array(20 + pixels);
  const view = new DataView(tim.buffer);
  view.setUint32(0, 0x10, true);
  view.setUint32(4, 2, true);
  view.setUint32(8, pixels, true); // counts the pixel bytes only, as the shipped paks do
  view.setInt16(12, 0, true);
  view.setInt16(14, 240, true);
  view.setUint16(16, WIDTH, true);
  view.setUint16(18, HEIGHT, true);
  for (let i = 0; i < WIDTH * HEIGHT; i++) {
    view.setUint16(20 + i * 2, to555(image.rgb[i * 3], image.rgb[i * 3 + 1], image.rgb[i * 3 + 2]), true);
  }
  return tim;
}

/**
 * LZW for unpack_pakfile_. Its decoder never widens codes on its own (it waits
 * for 0x101) and resets on 0x102, so the encoder sends both; 0x100 ends.
 */
export function lzwPack(data: Uint8Array): Uint8Array {
  const out: number[] = [];
  let acc = 0n;
  let nbits = 0;
  const emit = (code: number, width: number) => {
    acc = (acc << BigInt(width)) | BigInt(code);
    nbits += width;
    while (nbits >= 8) {
      nbits -= 8;
      out.push(Number((acc >> BigInt(nbits)) & 0xffn));
    }
    acc &= (1n << BigInt(nbits)) - 1n;
  };

  let table = new Map<string, number>();
  let nextCode = 0x103;
  let width = 9;
  const MAX = 0x1fff;
  // Strings are keyed by their bytes joined with commas; single bytes are their own code.
  let cur: number[] = [];
  const key = (s: number[]) => s.join(',');
  const codeOf = (s: number[]) => (s.length > 1 ? table.get(key(s))! : s[0]);

  for (const ch of data) {
    if (cur.length === 0) {
      cur = [ch];
      continue;
    }
    const next = [...cur, ch];
    if (table.has(key(next))) {
      cur = next;
      continue;
    }
    emit(codeOf(cur), width);
    if (nextCode > MAX) {
      emit(0x102, width);
      table = new Map();
      nextCode = 0x103;
      width = 9;
    } else {
      table.set(key(next), nextCode++);
      // The decoder adds its entry after reading the next code, so widen one early.
      if (nextCode > (1 << width) - 1 && width < 13) {
        emit(0x101, width);
        width++;
      }
    }
    cur = [ch];
  }
  if (cur.length) emit(codeOf(cur), width);
  emit(0x100, width);
  if (nbits) out.push(Number((acc << BigInt(8 - nbits)) & 0xffn));
  return Uint8Array.from(out);
}

export function makePak(image: Image): Uint8Array {
  return lzwPack(makeTim(image));
}
