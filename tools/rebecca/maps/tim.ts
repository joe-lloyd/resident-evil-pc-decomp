// 8-bit TIM images, the format of RE1's map pictures (item_m2/map*.tim): an
// 8 byte header, a block with the 256-colour CLUT, and a block with the
// pixels, one CLUT index each. Colours are PS1 15-bit, red in the low bits.
//
// The engine reads the map files at fixed offsets (MainMenu.cpp,
// map_display_load_textures): CLUT entry 0 at 0x14 and the pixels at 0x220,
// so the CLUT must have 256 entries and nothing may come between.

export interface Tim8 {
  readonly width: number;
  readonly height: number;
  /** 256 PS1 colours. */
  readonly clut: Uint16Array;
  /** width * height CLUT indices, top row first. */
  readonly pixels: Uint8Array;
  /** Where the CLUT and the image sit in PS1 VRAM; the header carries them, the PC port ignores them. */
  readonly clutAt?: readonly [number, number];
  readonly imageAt?: readonly [number, number];
}

/** A PS1 colour from 8-bit channels; `stp` sets the semi-transparency bit RE1's map fills carry. */
export function ps1(r: number, g: number, b: number, stp = false): number {
  return ((r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10) | (stp ? 0x8000 : 0)) >>> 0;
}

/** A PS1 colour back to 8-bit channels, as the engine expands it. */
export function rgbOf(c: number): [number, number, number] {
  return [Math.round(((c & 31) * 255) / 31), Math.round((((c >> 5) & 31) * 255) / 31), Math.round((((c >> 10) & 31) * 255) / 31)];
}

export function encodeTim8(t: Tim8): Uint8Array {
  if (t.clut.length !== 256) throw new Error(`a map TIM's CLUT has 256 colours, not ${t.clut.length}`);
  if (t.width % 2) throw new Error('an 8-bit TIM is an even number of pixels wide');
  if (t.pixels.length !== t.width * t.height) throw new Error(`${t.pixels.length} pixels for a ${t.width}x${t.height} image`);
  const clutBlock = 12 + 512;
  const imageBlock = 12 + t.pixels.length;
  const out = new Uint8Array(8 + clutBlock + imageBlock);
  const v = new DataView(out.buffer);
  v.setUint32(0, 0x10, true);
  v.setUint32(4, 0x09, true); // 8 bpp, with a CLUT
  let at = 8;
  const [cx, cy] = t.clutAt ?? [0, 480];
  v.setUint32(at, clutBlock, true);
  v.setUint16(at + 4, cx, true);
  v.setUint16(at + 6, cy, true);
  v.setUint16(at + 8, 256, true);
  v.setUint16(at + 10, 1, true);
  at += 12;
  for (let i = 0; i < 256; i++) v.setUint16(at + i * 2, t.clut[i]!, true);
  at += 512;
  const [ix, iy] = t.imageAt ?? [0, 0];
  v.setUint32(at, imageBlock, true);
  v.setUint16(at + 4, ix, true);
  v.setUint16(at + 6, iy, true);
  v.setUint16(at + 8, t.width / 2, true); // in 16-bit words
  v.setUint16(at + 10, t.height, true);
  out.set(t.pixels, at + 12);
  return out;
}

export function decodeTim8(bytes: Uint8Array): Tim8 {
  const v = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (v.getUint32(0, true) !== 0x10 || v.getUint32(4, true) !== 0x09) throw new Error('not an 8-bit TIM with a CLUT');
  const clutLength = v.getUint32(8, true);
  const clut = new Uint16Array(256);
  for (let i = 0; i < 256; i++) clut[i] = v.getUint16(20 + i * 2, true);
  const at = 8 + clutLength;
  const width = v.getUint16(at + 8, true) * 2;
  const height = v.getUint16(at + 10, true);
  return {
    width,
    height,
    clut,
    pixels: bytes.slice(at + 12, at + 12 + width * height),
    clutAt: [v.getUint16(12, true), v.getUint16(14, true)],
    imageAt: [v.getUint16(at + 4, true), v.getUint16(at + 6, true)],
  };
}
