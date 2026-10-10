# Rebecca in Chris's scenario: what the game already does

Reference for the Rebecca scenario (`REBECCA_SCENARIO.md`). It records what
Chris's room scripts (the `...0.rdt` files) do with Rebecca. It comes from
decoding the PC room files with `rae script` and the event scripts with
`tools/evt_disasm.py`.

Flag notation:

- SF is bank 0 (`FG_SCENARIO`) and SF2 is bank 1 (`FG_COMMON`); numbers are hex.
- `ck(bank, bit, 0)` is true when the bit is set (`cmd_bit_test` returns
  `isSet ^ expect`).
- "evt N" is event script N of the room.
- Rebecca is NPC type 0x23, or 0x2C ("Rebecca 2") in stages 6 and 7.
- Cutscene lines are voice only. Their `message_set` points at blank timer
  messages, so only examine and prompt texts exist as text.

## Meetups

| Room | Name | What happens | Done when |
| --- | --- | --- | --- |
| 1000 | Save room | evt 0, the first meeting: nine voice cues. Later "Do you want me to heal your wounds?" (msg 33), then "Rebecca treats Chris." (msg 44, sets SF2 0x28). At the exit, "Will you take Rebecca with you?" (msg 16): choice 0 clears SF2 0x22, any other choice sets it. | SF2 0x24, 0x3C |
| 10F0 | Mansion bar | Chris can't read music; Rebecca plays "Moonlight Sonata", then "Will you have Rebecca practice?" (msg 11). evt 8 sets SF2 0xA2. | SF2 0xA0, 0xA2 |
| 20D0 | Pillar passage | Richard is poisoned (evt 0, nine lines, sets SF2 0x62 and 0x2D). Bringing the Serum runs evt 1, which sets SF 0x7F and removes the Serum. "Richard is dead." once SF2 0x64 is set. | SF2 0x62, SF 0x7F or SF2 0x64 |
| 20E0 | Front of attic | The zone runs evt 0 when SF2 0x43 is set and SF 0x47 clear. evt 5 hands control to Rebecca. Back with the Serum in time (timer under 300), evt 6 sets SF2 0x5E: she treats Chris. Too late, evt 35/36 kill him. | SF 0x47, SF2 0x5E |
| 4080 | Beehive passage | Six lines (evt 1), then evt 2 or 3; she leaves. | SF2 0xAA |
| 4090 | Drug storehouse | Bottle and V-Jolt work only with character model 3; Chris gets "It's useless. Chris can't handle chemicals." (msg 26). | SF2 0x3A, 0x3B |
| 40C0 | Plant 42 room | evt 0 places Chris, plays five cues and hands control to Rebecca. | SF2 0x37, 0x3D, SF 0x29 |
| 5010 | Emergency tunnel | Battery: evt 3-6 pick a version by who is alive (SF2 0x4B Jill, SF2 0xC0 Rebecca). | - |
| 50C0 | B3 elevator entry | Six lines (evt 6), lock bits 0x2C and 0x1C; she leaves. | SF2 0x5A |
| 5110 | Power room | She waits; the switch sets SF 0x2D. | SF 0x2D |
| 5140 | Main lab entry | Wesker and Rebecca, 14 lines (evt 1), or evt 3 later. | SF2 0x4C |
| 5150 | B3-B4 elevator | The ride (evt 0/1), no lines. | - |
| 6000 | Save room, return | 11 lines (evt 2), or evt 0 when SF2 0x2F is set. | SF2 0x34, 0x30 |
| 6010 | 1F left stairs | evt 0 sets SF2 0x2F and 0x23 and a Hunter appears; after it dies, evt 5. | SF2 0x35 |
| 60F0 | Mansion bar, return | Same scripts as 10F0. | - |
| 7060 | Small library | Rebecca 2 with Hunters; evt 3, 5 (sets SF2 0xC0) or 0. | SF2 0x6D, 0xC0 |

## Where control switches to Rebecca

Two event blocks write character model 3 (`state_byte_set [09 03 00]`):

- ROOM20E0 evt 5, after the attic scene;
- ROOM40C0 evt 0, the Plant 42 setup.

Control goes back to Chris in ROOM20D0 evt 8, ROOM40F0 evt 3 and 4 (after
the V-Jolt) and ROOM5010 evt 3-6. Rooms that test the model with
`cmpb(9, .., 3)`: 1050, 1060, 1070, 4000, 4040, 4060, 4090, 40A0, 40F0, 4100.

## Story flags

- SF2 0x24: met Rebecca.
- SF2 0x22: cleared by "take Rebecca" choice 0. It gates both control
  switches (inferred: set means she stays behind).
- SF2 0x2D, 0x2E: serum objectives.
- SF2 0x64: Richard is dead.
- SF 0x7F: the radio, set when the serum arrives in time.
- SF2 0x3D, 0x38: Plant 42 triggered; SF 0x00 and 0x29: Plant 42 dead.
- SF 0x13: V-Jolt used.
- SF 0x37: main lab entered.
- SF2 0xC0: read by the lab rooms as "Rebecca absent" (inferred).

## Room messages

The dword at RDT offset 0x74 points at the message section. It starts with a
table of u16 offsets; the count is the first offset / 2. Glyphs and control
bytes are listed in `TEXT_ENCODING.md`, whose 02 and 03 are swapped. The
renderer (`Rendering.cpp`, `UpdateMessageDisplay`) is the reference.
