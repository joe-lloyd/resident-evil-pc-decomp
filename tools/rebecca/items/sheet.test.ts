// The icon sheet: her renders land in their donors' rows and nothing else
// changes, from the decomp's own icon table.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { buildIconSheet, globalsCpp, iconRows } from './sheet.ts';
import { KEY_ITEMS } from './items.ts';

/** A TIM with a 256-entry, 3-row CLUT: row 2 entry i is grey level i >> 3, entry 0 see-through. */
function fakeTim(): Uint8Array {
  const w = 256;
  const h = 3;
  const out = new Uint8Array(20 + w * h * 2);
  const v = new DataView(out.buffer);
  v.setUint32(0, 0x10, true);
  v.setUint32(4, 8 | 1, true);
  v.setUint32(8, 12 + w * h * 2, true);
  v.setUint16(16, w, true);
  v.setUint16(18, h, true);
  for (let i = 1; i < w; i++) {
    const g = i >> 3;
    v.setUint16(20 + (2 * w + i) * 2, g | (g << 5) | (g << 10), true);
  }
  return out;
}

test('her renders replace only their donors\' rows', () => {
  const rows = 72;
  const sheet = new Uint8Array(rows * 1200).fill(40);
  const out = buildIconSheet(sheet, fakeTim(), globalsCpp());
  const row = iconRows(globalsCpp());
  const drawn = new Set(['cutters', 'cog', 'jerrycan', 'fuel', 'dynamite', 'fuses', 'crowbar'].map((s) => row(KEY_ITEMS.find((k) => k.step === s)!.id)));
  for (let r = 0; r < rows; r++) {
    const changed = out.subarray(r * 1200, (r + 1) * 1200).some((b) => b !== 40);
    assert.equal(changed, drawn.has(r), `row ${r}`);
  }
});

test('the icon table gives RE1\'s rows: knife 0, clip 7, hex crank 26', () => {
  const row = iconRows(globalsCpp());
  assert.deepEqual([row(0x01), row(0x0b), row(0x1e)], [0, 7, 26]);
});
