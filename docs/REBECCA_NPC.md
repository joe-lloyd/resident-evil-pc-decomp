# The people of Rebecca's day

Two people share her day:

- Hal, the gondola operator.
- The ranger's partner, a Forest Service woman.

Each is an RE1 character model with its skeleton and animations kept and a
skin we paint. This file records how the models work, which ones we use and
why, and how they reach the game. The code is in `tools/rebecca/npc/`.

## The model file

`LoadEntityEMD` (`src/game/EntityModelLoader.cpp:477`) loads a character from
`enemy/` by entity id: `g_emdPathTable[(player id & 1) * 53 + id + 4]` (`:65`).
Room loading calls it with the id from `enemy(...)` (`src/game/RoomInit.cpp:631`).

The file is a run of sections with a directory of five 32-bit offsets in its
last 20 bytes. `LoadEntityEMD` reads them at `(size & ~3) - 0x14`:

| Entry | Section | Read as |
| --- | --- | --- |
| 0 | a monster's second skeleton; 0 for the people | `emdScratchPtr2` |
| 1 | skeleton and keyframes (EMR); 0, so it starts the file | `animHeader` |
| 2 | animation list (EDD) | `animBase` |
| 3 | mesh, a PlayStation TMD | `ProcessTmdTextures` |
| 4 | texture, an 8 bpp 256x256 TIM with two palette rows | uploaded to VRAM |

A monster's file starts with a section no entry names; the loader keeps the
file's start for it.

- **EMR.** The header is four `u16`s:
  - the armature offset;
  - the keyframe offset;
  - the joint count (15 for every person);
  - the keyframe size (104).

  Then each joint's offset from its parent, three `s16`s. The armature gives
  each joint a child count and the offset of its list of child indices.
  `EntityComputeJointWorldMatrices` (`src/game/GteMatrix.cpp:895`) walks it
  from joint 0.

  A keyframe is:
  - the root position (three `s16`);
  - three `s16` the engine moves the entity by;
  - one `s16` x, y, z rotation per joint, in 4096ths of a turn.

  `UpdateEntityAnimation` (`src/game/PlayerAnimations.cpp:1261`) turns each
  rotation into a matrix with `RotMatrix` (`GteMatrix.cpp:151`), which builds
  `Rx(-x) * Ry(y) * Rz(-z)`.
- **EDD.** Per animation, a frame count and the offset of its frames. A frame
  is a `u32` whose low 16 bits name a keyframe. The list's length is the
  lowest frame offset any entry holds.
- **TMD.** One object per joint, its vertices in that joint's space. Every
  polygon in the people's models is mode `0x34`, a lit, textured,
  smooth-shaded triangle.
- **Texture.** Each 128-texel half of the sheet has its own palette row.
  - Polygons on the left half (TSB `0x80`) use row 0 (CBA `0x7800`).
  - Polygons on the right half (`0x81`) use row 1 (`0x7840`).

  `emd.test.ts` checks this for every polygon of both models, so a skin can
  be one 256x256 image with up to 256 colours per half.
- **Axes.** The game's axes are x forward, y down and z to the character's
  left. The people face +x at angle 0.

`emd.ts` reads and writes all of this. `emd.test.ts` reads the player's own
models from `RE1_BASE` (default `/tmp/re1-pc`). All 67 models in the game
write back as the same bytes.

## Which models

| Person | Entity id | File | Why |
| --- | --- | --- | --- |
| Hal | 34 | `EM1022.EMD` (Barry) | the heavy man's frame; no room of hers places Barry |
| the ranger's partner | 35 | `EM1023.EMD` (Rebecca as an NPC) | a woman's frame; she is the player, so the NPC model is free |

Her rooms place only an adder (10) and a Cerberus (2) so far:

```
grep -rn "enemy(" tools/rebecca/day/*/room.c
```

The model files with the same mesh and texture:

- Barry's cutscene variants `EM102B` and `EM102D`, and his player model
  `CHAR12`.
- Rebecca's `EM102C` and her player model `CHAR13`.

So a skin painted for one fits all of them. `EM102A`, Barry dying, has its own
mesh and texture.

### Their animations

These numbers are measured from the keyframes, not guessed from names.

- `anims.ts` draws every animation as a moving skeleton:
  https://home.arpa/research/rebecca-npc/anims.html.
- "Head" is the head joint's height above the floor, in game units.

| Animation | Barry, `EM1022` | Rebecca NPC, `EM1023` |
| --- | --- | --- |
| 0 | stand, still (3 frames) | stand, still |
| 1 | walk (20 frames) | walk |
| 4 | fall to the floor, ends lying (30 frames) | fall, ends lying |
| 9 | kneel down, ends kneeling (25 frames) | kneel down |
| 42 | standing loop, weight shift (20 frames) | standing loop (20 frames) |
| 54 | a second fall, ends lying (31 frames) | lying on the floor (90 frames) |
| 59 | none | a second fall (30 frames) |
| 61, 62 | none | sitting on the floor (30, 40 frames) |
| 63 | none | kneeling loop (18 frames) |

- **Hal.** He needs an idle or a sit, and a death. That gives 42 to idle, 9
  to kneel, and 4 or 54 to die.
- **The partner.** She gets 42 or 63 to idle, 61 or 62 to sit, and 4 or 59
  to fall.

## How they reach the game

`npc/people.ts` names the two people. `build.ts` writes their models into the
REB overlay as `enemy/EM1022.EMD` and `enemy/EM1023.EMD`. Chris's and Jill's
games never read REB, so they are unchanged.

Each model is the player's own file with two changes:

- **The texture is our skin.** `paint.ts` paints it from what each texel
  covers on the body: the part, the point and the surface's facing.
  `skin.ts` fits it to the two palettes.
- **The idle is swapped into animation 0.** The NPC code's looping idle,
  behaviour 9 (`npc_idle_play_anim`, `src/game/entities/CharacterNpc.cpp:370`),
  always plays animation 0, which in these models is a still pose. Swapping
  the two entries of the animation list keeps every animation and the list's
  length.

The file size never changes, so a model fits the room buffer exactly as the
original did.

## Placing one in a room

```
enemy(34 /* Barry (Stars) */, 0, 255, 1, 2, 0, 0, angle, 0, 0, x, 0, z, slot, 0, 0, 0);
```

- **The spawn line** is the shape of every shipped NPC spawn. `cmd_enemy_set`
  (`src/game/CmdFunctions.cpp:847`) decodes the operands:
  - the id;
  - the weapon (0 for none);
  - the kill flag (255 for none);
  - the angle;
  - x, y and z;
  - the enemy slot, then the animation and frame to stand in.
- **Starting the idle.** The spawn leaves the character on that one frame:
  - Idle behaviour 0 does nothing for ids 32 to 36 (`npc_idle_walk_00`,
    `:2226`).
  - The first update clears the behaviour (`npc_state0_init`, `:2253`).
  - So on the second frame in the room the script gives each idle 9 with
    `eml_state(0, slot, 2, 9, 0)` (`cmd_enemy_prop_set` sub-command 2,
    `CmdFunctions.cpp:1433`).
- **Messages wait.** A message pauses the characters but not the script. A
  room's first message must therefore wait until the idle is set, or their
  first update comes after it and clears it.
  - `tools/rebecca/day/lookout/room.c` uses `FG_ROOM` 20 and 21 for this.
  - That bank clears on every room entry (`RoomInit.cpp:380`).
- **Room buffer.** The models load into what the room leaves of the room
  buffer. `rae asm` refuses a room that does not keep about 220 KB per
  distinct model type. The cabin holds both.

## Things to know

- **The partner-alive flag.** If `FG_COMMON` 192 (`SCENARIO2_FLAG_PARTNER_ALIVE`,
  `src/game/BioCard.h:204`) is ever set, id 35's init (`CharacterNpc.cpp:237`)
  overrides the spawn: it darkens three joint groups and poses her in
  animation 51. Keep that flag clear in her day.
- **A weapon.** The second operand loads a weapon model onto joint 14, the
  right hand: `LoadCharacterWeaponTmd` (`:147`) reads `g_charWeaponTmdTable`
  (`:107`).
  - Id 34 uses `ws224.tmd`, or `ws225.tmd` for values 5 and 6.
  - Id 35 uses `ws232.tmd`, or `ws236.tmd` for value 6.
  - A rifle for the partner would be a TMD of ours under one of those names
    in REB.
- **The proof.** `tools/harness/tests/people.ts` boots her into the cabin. It
  checks:
  - both people are placed where the script puts them;
  - the pixels where each camera shows them change over a second, so they
    are moving.

## Tools

| File | Does |
| --- | --- |
| `npc/emd.ts` | reads and writes a model: sections, skeleton, keyframes, animations, mesh, texture |
| `npc/emd.test.ts` | round trip of every model, a texture written and read back, the people's models |
| `npc/skin.ts` | fits a 256x256 RGB skin to the texture's two palettes |
| `npc/paint.ts` | paints a skin from what each texel covers on the body |
| `npc/people.ts` | the two people and their models |
| `npc/export.ts` | writes a model out for Blender: `model.json` and `texture.png` |
| `npc/view.py` | Blender: the model on its skeleton, posed, front, side and back |
| `npc/anims.ts` | every animation drawn as a moving skeleton, on one page |

Run each Blender render on jellybingus, inside a render slot:

```
node tools/rebecca/day/slots.ts npc -- ssh -o BatchMode=yes jellybingus \
  'cmd /c ""C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" -b --factory-startup --python <dir>\view.py -- <model dir> <out dir> rest --size 512"'
```
