// The light look filter of RE1's backgrounds, run by the build on every frame
// it reads from a render: backgrounds, the animation and state frames, the
// walks. The masks are cut from the filtered background, so they match.
//
// It colours and shapes the tone only: the colour pulled toward the game's
// green shadows and amber highlights and a little less saturated, the blacks
// crushed and the mids steepened, the corners darkened. The texture is in the
// renders' materials (kit.wear), not laid over the frame, so there is no
// grain; the 15-bit rounding is the TIM writer's (pak.ts).
//
// A port of look.py, the sample, without its grain.
import type { Image } from '../../harness/image.ts';

const W = 320;
const H = 240;

/** The build's strength: RE1_LOOK, 0 for none (default 0.4, the light pass of the samples). */
export const LOOK = Number(process.env.RE1_LOOK ?? 0.4);

/** Crush the blacks and steepen the mids: an S over 0..255. */
function curve(strength: number): Uint8Array {
  return Uint8Array.from({ length: 256 }, (_, v) => {
    const x = v / 255;
    const s = x * x * (3 - 2 * x);
    let y = x + (s - x) * 0.35 * strength;
    y = Math.max(0, (y - 0.015 * strength) / (1 - 0.015 * strength));
    return Math.round(Math.min(1, y) * 255);
  });
}

const clamp = (v: number) => Math.max(0, Math.min(255, Math.round(v)));

export function look(image: Image, strength = LOOK): Image {
  if (image.width !== W || image.height !== H) throw new Error(`a frame is ${W}x${H}, got ${image.width}x${image.height}`);
  if (strength <= 0) return image;
  const lut = curve(strength);
  const out = new Uint8Array(image.rgb.length);
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 3;
      // A little less saturated: toward the pixel's grey.
      const [r0, g0, b0] = [image.rgb[i]!, image.rgb[i + 1]!, image.rgb[i + 2]!];
      const grey = 0.299 * r0 + 0.587 * g0 + 0.114 * b0;
      const keep = 1 - 0.15 * strength;
      const [r1, g1, b1] = [clamp(grey + (r0 - grey) * keep), clamp(grey + (g0 - grey) * keep), clamp(grey + (b0 - grey) * keep)];
      // Shadows toward green-teal, highlights toward amber.
      const r = clamp(r1 * (1 + (0.04 * strength * r1) / 255) - 4 * strength * (1 - r1 / 255));
      const g = clamp(g1 + 3 * strength * (1 - g1 / 255));
      const b = clamp(b1 * (1 - (0.1 * strength * b1) / 255));
      // The corners darkened: 0 in the middle, 255 at the edge of an ellipse the frame's size.
      const d = Math.min(255, 2 * Math.hypot(((x + 0.5) / W) * 256 - 128, ((y + 0.5) / H) * 256 - 128));
      const v = 1 - (Math.min(255, Math.max(0, d - 90) * 1.5) * 0.3 * strength) / 255;
      out[i] = clamp(lut[r]! * v);
      out[i + 1] = clamp(lut[g]! * v);
      out[i + 2] = clamp(lut[b]! * v);
    }
  return { width: W, height: H, rgb: out };
}
