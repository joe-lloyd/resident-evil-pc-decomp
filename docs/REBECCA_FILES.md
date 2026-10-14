# Rebecca's files

The diaries, logs and letters Rebecca reads on her day open the way RE1's
files do: full-screen pages she turns through, kept afterwards in the FILE
tab. This document says how RE1 stores a file, what is built, and what is
left.

The review page, with every page and its words and a rating for each file,
is at https://home.arpa/research/rebecca-files/.

## How RE1 stores a file

Checked on 2026-10-14 against `src/game/MainMenu.cpp` and the USA game's own
`item_m2/filem_*.pix`:

- **A file is an item.** Its file index is `itemId - 0x5F`, from 0 to 15. The
  collected flag is room flag `0x82 + index` (`src/game/BioCard.h:220`).
- **The pages of file `n` are one `.pix`**, named by `g_filemPixNames`
  (`0x004d2350`): `filem_l0.pix` for 0 through `filem_z0.pix` for 14, then
  `filem_00.pix` for 15.
- **A `.pix` is 16 little-endian offsets** (`0x40` bytes), one per page and
  one more for the end of the file. Each offset points at an LZW stream for
  `unpack_pakfile_` (`0x00425ab0`), the same packing as the room backgrounds.
  `pickup_unpack_list` (`0x004827c0`) unpacks page `n` by its offset.
- **A page is a 256x256 TIM at 4 bpp** with one 16-colour CLUT. The header
  places the CLUT at VRAM (0, 480) and the image at (0, 0), 64 VRAM words
  wide. RE1's own pages are light grey type on colour `0x0000`, which the
  PS1 draws as see-through, so the reader's black shows behind. The type
  carries the semi-transparency bit. The pictures, such as Barry's photo,
  do not.
- **The page count is not in the file.** The reader takes it from
  `g_itemMaxCounts` (`0x004d2620`) by file index: 4, 6, 11, 4, 2, 6, 7, 7, 10,
  5, 5, 4, 3, 3, 3, 4. The first page of every RE1 file is its title on black.

## What is built

- `tools/rebecca/files/documents.ts` holds the ten documents, every word, page
  by page. Each one is written to the page count of the file slot it fills,
  so the reader needs no new count table.
- `tools/rebecca/files/font.ts` is our own pixel font, drawn cell by cell.
- `tools/rebecca/files/pages.ts` draws the pages on four papers: a ruled
  notebook, a ledger with a time column, typed letter paper, and RE1's
  black. It also draws the art pages: the bunkhouse calendar, the mine map,
  the torn notice and the quarry rosters. It packs the pages as a `.pix`.
- `tools/rebecca/files/pages.test.ts` packs every document, unpacks it with
  the port of the game's decoder (`tools/harness/background.ts`), and checks
  that each page reads back pixel for pixel with the game's header.
- `tools/rebecca/files/review.ts <outdir>` writes the review page.

| Slot | Document | Room | Pages |
| --- | --- | --- | --- |
| 0 | The ranger's logbook | lookout | 4 |
| 1 | Hal's diary | cottage | 6 |
| 3 | The quarry rosters | quarry-office | 4 |
| 4 | The quarantine notice | logging-road | 2 |
| 5 | The gardener's diary | lodge | 6 |
| 6 | The foreman's letters | office | 7 |
| 9 | The lower station log | lower-station | 5 |
| 10 | Walt's lookout log | tower-top | 5 |
| 12 | The bunkhouse calendar | bunkhouse | 3 |
| 13 | The mine map | mine-office | 3 |

## What is left

1. **The owner's review.** Rate the texts and the pages, and choose paper
   or RE1 black for the text pages.
2. **Her file names and descriptions.** Find where the FILE tab gets a
   file's name, from data or from a table, and give her mode its own.
3. **The pages in the REB overlay.** The tools build `item_m2/filem_*.pix`
   into the overlay. A mode's overlay is searched before the base tree, and
   `item_m2/filem_` falls back to the base files without a warning
   (`kBaseFallbackPrefixes` in `src/system/AssetPath.cpp`). Her copies win
   in her mode only, and a slot she does not fill keeps RE1's page.
4. **The pickups.** `tools/rebecca/day/scripts.ts` gives a file item for a
   check that `documents.ts` names, in place of `SCE_MESSAGE`. The cabin's
   logbook is hand-written in `lookout/room.c`. Each room needs a place to
   pick the file up. Where a scene needs a change for that, it goes to the
   room-art session.
5. **In the game.** Confirm the semi-transparency choice on paper pages
   against what the reader really draws.
6. **A harness test**, `tools/harness/tests/files.ts`. It picks each file up,
   reads it, finds it in the FILE tab and saves screenshots.
