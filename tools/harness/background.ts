// Room background loader. A background is a PC `.pak`: an LZW stream (the
// format unpack_pakfile_ reads, src/game/FileLoader.cpp) wrapping one 320x240
// 16 bit PS1 TIM. Format notes: docs/PSX_BSS_AND_PC_PAK.md.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { Image } from './image.ts';

const END_OF_STREAM = 0x100;
const GROW_CODE_SIZE = 0x101;
const RESET_DICTIONARY = 0x102;
const FIRST_FREE_CODE = 0x103;
// Matches PAK_DICT_ENTRIES in src/Globals.h.
const DICT_ENTRIES = 34981;

/**
 * Port of unpack_pakfile_ (0x00425ab0). Codes are read MSB first. The code
 * width starts at 9 on every dictionary reset and only grows when the stream
 * says so with 0x101. The decoder never grows it on its own.
 */
export function unpackPak(src: Uint8Array, expectedSize: number): Uint8Array {
  const dst = new Uint8Array(expectedSize);
  const prefix = new Int32Array(DICT_ENTRIES);
  const suffix = new Uint8Array(DICT_ENTRIES);
  const stringBuf = new Uint8Array(DICT_ENTRIES + 2);

  let bitPos = 0;
  const readCode = (width: number): number => {
    let code = 0;
    for (let i = 0; i < width; i++) {
      const byte = src[bitPos >> 3];
      if (byte === undefined) throw new Error('pak: input ended before end-of-stream code');
      code = (code << 1) | ((byte >> (7 - (bitPos & 7))) & 1);
      bitPos++;
    }
    return code;
  };

  let outPos = 0;
  const emit = (b: number): void => {
    if (outPos >= dst.length) throw new Error(`pak: output exceeds ${expectedSize} bytes`);
    dst[outPos++] = b;
  };

  // Writes the string for `code` reversed into stringBuf from `start`; returns
  // the count written, as pak_decomp_decode_string does.
  const decodeString = (start: number, code: number): number => {
    let pos = start;
    while (code > 0xff) {
      if (code >= DICT_ENTRIES || code < FIRST_FREE_CODE) throw new Error(`pak: bad dictionary code ${code}`);
      stringBuf[pos++] = suffix[code]!;
      code = prefix[code]!;
    }
    stringBuf[pos++] = code;
    return pos;
  };

  for (;;) {
    // Dictionary reset: width back to 9, next free code 0x103.
    let codeSize = 9;
    let nextCode = FIRST_FREE_CODE;

    let curCode = readCode(codeSize);
    if (curCode === END_OF_STREAM) break;
    emit(curCode);
    let prevCode = curCode;
    let prevFirstChar = curCode;

    let reset = false;
    while (!reset) {
      curCode = readCode(codeSize);
      if (curCode === END_OF_STREAM) return dst.subarray(0, outPos);
      if (curCode === RESET_DICTIONARY) {
        reset = true;
        continue;
      }
      if (curCode === GROW_CODE_SIZE) {
        codeSize++;
        continue;
      }

      // Code not in the table yet: previous string plus its own first
      // character, which goes in stringBuf[0] and is emitted last.
      const special = nextCode <= curCode;
      if (special) stringBuf[0] = prevFirstChar;
      const count = decodeString(special ? 1 : 0, special ? prevCode : curCode);

      const firstChar = stringBuf[count - 1]!;
      prevFirstChar = firstChar;
      for (let i = count; i !== 0; i--) emit(stringBuf[i - 1]!);

      if (nextCode >= DICT_ENTRIES) throw new Error('pak: dictionary overflow');
      prefix[nextCode] = prevCode;
      suffix[nextCode] = firstChar;
      nextCode++;
      prevCode = curCode;
    }
  }
  return dst.subarray(0, outPos);
}

export const TIM_HEADER_BYTES = 20;
const TIM_MAGIC = 0x10;
const TIM_FLAGS_16BPP = 0x02;
export const IMAGE_BYTES = 320 * 240 * 2;

/** 5 bit colour channel to 8 bit, replicating the top bits into the low ones. */
function expand5(v: number): number {
  return (v << 3) | (v >> 2);
}

/**
 * Decode the 16 bpp TIM the pak wraps. The block length field counts the pixel
 * bytes only (153600), not itself and the x/y/w/h shorts as the TIM spec says,
 * so the pixel data is read from the fixed 20 byte header.
 */
export function decodeTim16(tim: Uint8Array): Image {
  if (tim.length < TIM_HEADER_BYTES) throw new Error('tim: truncated header');
  const view = new DataView(tim.buffer, tim.byteOffset, tim.byteLength);
  if (view.getUint32(0, true) !== TIM_MAGIC) throw new Error('tim: bad magic');
  if (view.getUint32(4, true) !== TIM_FLAGS_16BPP) throw new Error('tim: not a 16 bpp image');
  const width = view.getUint16(16, true);
  const height = view.getUint16(18, true);
  if (width * height * 2 !== IMAGE_BYTES || width !== 320) throw new Error(`tim: unexpected size ${width}x${height}`);
  if (tim.length < TIM_HEADER_BYTES + IMAGE_BYTES) throw new Error('tim: truncated pixel data');

  const rgb = new Uint8Array(width * height * 3);
  for (let i = 0; i < width * height; i++) {
    const px = view.getUint16(TIM_HEADER_BYTES + i * 2, true);
    rgb[i * 3] = expand5(px & 0x1f);
    rgb[i * 3 + 1] = expand5((px >> 5) & 0x1f);
    rgb[i * 3 + 2] = expand5((px >> 10) & 0x1f);
  }
  return { width, height, rgb };
}

/**
 * Path of a camera's background, built as load_room_bg does: the stage digit is
 * stage + 1, and the revisit stages 5 and 6 (shown as stages 6 and 7) reuse the
 * backgrounds of stages 1 and 2, so the digit drops by 5. The directory and the
 * file name carry the same digit; the room is two hex digits, the camera one.
 */
export function backgroundPath(dataRoot: string, stage: number, room: number, camera: number): string {
  if (!Number.isInteger(stage) || stage < 0 || stage > 6) throw new Error(`stage ${stage} has no base-game backgrounds`);
  if (!Number.isInteger(room) || room < 0 || room > 0xff) throw new Error(`bad room ${room}`);
  if (!Number.isInteger(camera) || camera < 0 || camera > 0xf) throw new Error(`bad camera ${camera}`);
  const digit = stage > 4 ? stage + 1 - 5 : stage + 1;
  const name = `RC${digit}${room.toString(16).padStart(2, '0')}${camera.toString(16)}.pak`;
  return join(dataRoot, `Stage${digit}`, name);
}

export function loadBackground(
  dataRoot: string,
  stage: number,
  room: number,
  camera: number,
): { width: number; height: number; rgb: Uint8Array } {
  const path = backgroundPath(dataRoot, stage, room, camera);
  const tim = unpackPak(readFileSync(path), TIM_HEADER_BYTES + IMAGE_BYTES);
  return decodeTim16(tim);
}
