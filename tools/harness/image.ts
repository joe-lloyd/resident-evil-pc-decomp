// Minimal image I/O for the harness: read the BMPs the game's screenshot
// command writes, read and write PNGs. Node built-ins only.
import { readFileSync, writeFileSync } from 'node:fs';
import { deflateSync, inflateSync } from 'node:zlib';

export interface Image {
  width: number;
  height: number;
  /** Tightly packed rows, top row first, 3 bytes (R, G, B) per pixel. */
  rgb: Uint8Array;
  /** One byte per pixel, when the image came from a PNG with alpha (decodePng). */
  alpha?: Uint8Array;
}

/**
 * Decode an uncompressed (BI_RGB) 24 or 32 bit BMP. Rows are bottom-up when the
 * header height is positive and top-down when it is negative. The game's
 * SaveBitmapToFile writes 24 bit bottom-up (src/marni/MarniBits.cpp); the other
 * variants are accepted because other tools produce them.
 */
export function decodeBmp(data: Uint8Array): Image {
  const view = new DataView(data.buffer, data.byteOffset, data.byteLength);
  if (data.length < 54 || view.getUint16(0, true) !== 0x4d42) throw new Error('not a BMP file');
  const pixelOffset = view.getUint32(10, true);
  const headerSize = view.getUint32(14, true);
  if (headerSize < 40) throw new Error(`unsupported BMP header size ${headerSize}`);
  const width = view.getInt32(18, true);
  const rawHeight = view.getInt32(22, true);
  const bpp = view.getUint16(28, true);
  const compression = view.getUint32(30, true);
  if (compression !== 0) throw new Error(`unsupported BMP compression ${compression}`);
  if (bpp !== 24 && bpp !== 32) throw new Error(`unsupported BMP depth ${bpp}`);
  if (width <= 0 || rawHeight === 0) throw new Error(`bad BMP size ${width}x${rawHeight}`);

  const height = Math.abs(rawHeight);
  const bottomUp = rawHeight > 0;
  const bytesPerPixel = bpp / 8;
  const stride = Math.ceil((width * bpp) / 32) * 4;
  if (pixelOffset + stride * (height - 1) + width * bytesPerPixel > data.length) {
    throw new Error('BMP pixel data is truncated');
  }

  const rgb = new Uint8Array(width * height * 3);
  for (let y = 0; y < height; y++) {
    const srcRow = pixelOffset + (bottomUp ? height - 1 - y : y) * stride;
    for (let x = 0; x < width; x++) {
      const s = srcRow + x * bytesPerPixel;
      const d = (y * width + x) * 3;
      rgb[d] = data[s + 2]!;
      rgb[d + 1] = data[s + 1]!;
      rgb[d + 2] = data[s]!;
    }
  }
  return { width, height, rgb };
}

export function readBmp(path: string): Image {
  return decodeBmp(readFileSync(path));
}

const crcTable = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c >>> 0;
  }
  return table;
})();

export function crc32(bytes: Uint8Array): number {
  let c = 0xffffffff;
  for (const b of bytes) c = crcTable[(c ^ b) & 0xff]! ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function chunk(type: string, body: Uint8Array): Uint8Array {
  const out = new Uint8Array(12 + body.length);
  const view = new DataView(out.buffer);
  view.setUint32(0, body.length);
  for (let i = 0; i < 4; i++) out[4 + i] = type.charCodeAt(i);
  out.set(body, 8);
  view.setUint32(8 + body.length, crc32(out.subarray(4, 8 + body.length)));
  return out;
}

export function encodePng(image: Image): Uint8Array {
  const { width, height, rgb } = image;
  if (rgb.length !== width * height * 3) throw new Error('rgb length does not match width x height');

  const header = new Uint8Array(13);
  const hv = new DataView(header.buffer);
  hv.setUint32(0, width);
  hv.setUint32(4, height);
  header[8] = 8; // bit depth
  header[9] = 2; // colour type: truecolour RGB

  // Each scanline is prefixed with filter type 0 (none).
  const raw = new Uint8Array(height * (1 + width * 3));
  for (let y = 0; y < height; y++) {
    raw.set(rgb.subarray(y * width * 3, (y + 1) * width * 3), y * (1 + width * 3) + 1);
  }

  const parts = [
    Uint8Array.of(0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a),
    chunk('IHDR', header),
    chunk('IDAT', deflateSync(raw)),
    chunk('IEND', new Uint8Array(0)),
  ];
  const png = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
  let at = 0;
  for (const p of parts) {
    png.set(p, at);
    at += p.length;
  }
  return png;
}

export function writePng(path: string, image: Image): void {
  writeFileSync(path, encodePng(image));
}

const PNG_SIGNATURE = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
/** Colour type to samples per pixel, for the 8 bit types decodePng accepts. */
const PNG_SAMPLES: Record<number, number> = { 0: 1, 2: 3, 4: 2, 6: 4 };

function paeth(a: number, b: number, c: number): number {
  const p = a + b - c;
  const pa = Math.abs(p - a);
  const pb = Math.abs(p - b);
  const pc = Math.abs(p - c);
  return pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
}

/**
 * Decode a non-interlaced 8 bit PNG (grey, grey + alpha, RGB or RGBA) to RGB,
 * with its alpha alongside when it has one: Blender's opaque renders have
 * none, and a render on a transparent film (saveroom/hatch.py) does.
 */
export function decodePng(data: Uint8Array): Image {
  if (data.length < 8 || PNG_SIGNATURE.some((b, i) => data[i] !== b)) throw new Error('not a PNG file');
  const view = new DataView(data.buffer, data.byteOffset, data.byteLength);
  let width = 0;
  let height = 0;
  let samples = 0;
  const idat: Uint8Array[] = [];
  for (let at = 8; at + 8 <= data.length; ) {
    const length = view.getUint32(at);
    const type = String.fromCharCode(data[at + 4]!, data[at + 5]!, data[at + 6]!, data[at + 7]!);
    const body = data.subarray(at + 8, at + 8 + length);
    if (body.length !== length) throw new Error('PNG chunk is truncated');
    if (type === 'IHDR') {
      width = view.getUint32(at + 8);
      height = view.getUint32(at + 12);
      const depth = body[8];
      const colourType = body[9]!;
      const interlace = body[12];
      samples = PNG_SAMPLES[colourType] ?? 0;
      if (depth !== 8 || samples === 0) throw new Error(`unsupported PNG: bit depth ${depth}, colour type ${colourType}`);
      if (interlace !== 0) throw new Error('interlaced PNGs are not supported');
    } else if (type === 'IDAT') {
      idat.push(body);
    } else if (type === 'IEND') {
      break;
    }
    at += 12 + length;
  }
  if (width <= 0 || height <= 0 || samples === 0) throw new Error('PNG has no IHDR');

  const raw = inflateSync(Buffer.concat(idat));
  const stride = width * samples;
  if (raw.length < height * (stride + 1)) throw new Error('PNG pixel data is truncated');

  const pixels = new Uint8Array(height * stride);
  for (let y = 0; y < height; y++) {
    const filter = raw[y * (stride + 1)]!;
    const src = y * (stride + 1) + 1;
    const dst = y * stride;
    for (let x = 0; x < stride; x++) {
      const left = x >= samples ? pixels[dst + x - samples]! : 0;
      const up = y > 0 ? pixels[dst - stride + x]! : 0;
      const upLeft = y > 0 && x >= samples ? pixels[dst - stride + x - samples]! : 0;
      let predictor: number;
      switch (filter) {
        case 0: predictor = 0; break;
        case 1: predictor = left; break;
        case 2: predictor = up; break;
        case 3: predictor = (left + up) >> 1; break;
        case 4: predictor = paeth(left, up, upLeft); break;
        default: throw new Error(`bad PNG filter type ${filter}`);
      }
      pixels[dst + x] = (raw[src + x]! + predictor) & 0xff;
    }
  }

  const rgb = new Uint8Array(width * height * 3);
  for (let i = 0; i < width * height; i++) {
    const s = i * samples;
    const grey = samples < 3;
    rgb[i * 3] = pixels[s]!;
    rgb[i * 3 + 1] = pixels[grey ? s : s + 1]!;
    rgb[i * 3 + 2] = pixels[grey ? s : s + 2]!;
  }
  if (samples === 2 || samples === 4) {
    const alpha = Uint8Array.from({ length: width * height }, (_, i) => pixels[i * samples + samples - 1]!);
    return { width, height, rgb, alpha };
  }
  return { width, height, rgb };
}

export function readPng(path: string): Image {
  return decodePng(readFileSync(path));
}
