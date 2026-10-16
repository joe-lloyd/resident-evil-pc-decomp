// Her map screen's pictures, under the names RE1's map screen loads
// (MainMenu.cpp: g_MapFileNames, g_MapTabFileNames, g_MapBlueFileName), for
// the overlay's ITEM_M2: in her mode they stand in for Chris's and Jill's.
//
//   MAP01 to MAP0B   her eleven areas, in the order of plan/maps.ts
//   MAP0D, MAP0C, MAP00, MAP0E   the overview at each of its four stages
//   Map_blue         the grid the area maps are drawn over
import { AREAS, STAGES } from '../plan/maps.ts';
import { areaTim } from './draw.ts';
import { overview } from './overview.ts';
import { encodeTim8, ps1, type Tim8 } from './tim.ts';

/** RE1's overview file for each stage, from the mansion alone to the lab (g_MapTabFileNames). */
export const STAGE_FILES = ['MAP0D.TIM', 'MAP0C.TIM', 'MAP00.TIM', 'MAP0E.TIM'] as const;
export const areaFile = (i: number) => `MAP${(i + 1).toString(16).toUpperCase().padStart(2, '0')}.TIM`;

/** The blue grid, eight pixels square, that the area maps sit over. */
function grid(): Tim8 {
  const clut = new Uint16Array(256);
  clut[1] = ps1(0, 72, 0, true);
  clut[3] = ps1(16, 0, 96, true);
  const pixels = new Uint8Array(128 * 128);
  for (let y = 0; y < 128; y++) for (let x = 0; x < 128; x++) pixels[y * 128 + x] = x % 8 === 7 || y % 8 === 7 ? 1 : 3;
  return { width: 128, height: 128, clut, pixels, clutAt: [0, 496], imageAt: [768, 256] };
}

export function mapFiles(): { name: string; bytes: Uint8Array }[] {
  if (AREAS.length > 11) throw new Error('RE1 has eleven area map files');
  const o = overview();
  return [
    ...AREAS.map((a, i) => ({ name: areaFile(i), bytes: encodeTim8(areaTim(a.id)) })),
    ...STAGES.map((_, s) => ({ name: STAGE_FILES[s]!, bytes: encodeTim8(o.stages[s]!) })),
    { name: 'MAP_BLUE.TIM', bytes: encodeTim8(grid()) },
  ];
}
