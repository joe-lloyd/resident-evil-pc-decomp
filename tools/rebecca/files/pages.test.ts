// node --test tools/rebecca/files/pages.test.ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { unpackPak } from '../../harness/background.ts';
import { day } from '../plan/day.ts';
import { sections } from '../plan/todo.ts';
import { DOCUMENTS, SLOT_PAGES } from './documents.ts';
import { PAGE, TIM_SIZE, drawPage, layoutText, packPix, readTim, wrap } from './pages.ts';

test('wrap breaks between words at the column', () => {
  assert.deepEqual(wrap('Crank is in the shed.', 11), ['Crank is in', 'the shed.']);
});

test('a ledger line that opens with a time writes the time in its column', () => {
  assert.deepEqual(layoutText('0305 Woman from the lot, bitten by a dog.', 'ledger'), [
    { row: 0, x: 'left', time: '0305', s: 'Woman from the lot, bitten' },
    { row: 1, x: 'left', time: undefined, s: 'by a dog.' },
  ]);
});

test('a page that runs past the paper fails', () => {
  assert.throws(() => layoutText('word '.repeat(400), 'notebook'), /more than the 14 that fit/);
});

test('every document fills its own slot with the page count the reader expects', () => {
  const slots = DOCUMENTS.map((d) => d.slot);
  assert.equal(new Set(slots).size, slots.length);
  for (const d of DOCUMENTS) assert.equal(d.pages.length, SLOT_PAGES[d.slot], d.id);
});

test('every document has its row in the tracker', () => {
  const rows = new Set(sections(day, { rooms: new Map() }).flatMap((s) => s.items.map((i) => i.id)));
  for (const d of DOCUMENTS) assert.ok(rows.has(`file-${d.id}`), d.id);
});

test('a packed .pix reads back to the pages that were drawn', () => {
  for (const doc of DOCUMENTS) {
    const drawn = doc.pages.map((_, i) => drawPage(doc, i));
    const pix = packPix(drawn);
    const v = new DataView(pix.buffer);
    assert.equal(v.getUint32(0, true), 0x40);
    assert.equal(v.getUint32(drawn.length * 4, true), pix.length, 'the offset after the last page is the file size');
    drawn.forEach((page, i) => {
      const tim = unpackPak(pix.subarray(v.getUint32(i * 4, true)), TIM_SIZE);
      // The header the game's own pages carry: 4 bpp with a CLUT at (0, 480), the image 64 x 256 VRAM words.
      assert.deepEqual([...tim.subarray(0, 20)], [0x10, 0, 0, 0, 8, 0, 0, 0, 0x2c, 0, 0, 0, 0, 0, 0xe0, 1, 16, 0, 1, 0]);
      assert.deepEqual([...tim.subarray(52, 64)], [0x0c, 0x80, 0, 0, 0, 0, 0, 0, 64, 0, 0, 1]);
      const back = readTim(tim);
      assert.equal(back.clut[0], 0, 'colour 0 is see-through');
      assert.equal(back.pixels.length, PAGE * PAGE);
      assert.deepEqual(back.pixels, page.pixels, `${doc.id} page ${i}`);
    });
  }
});
