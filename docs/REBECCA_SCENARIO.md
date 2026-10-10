# Rebecca scenario plan

A new scenario mode for this port: Resident Evil 1 from Rebecca Chambers'
side. It is a loose remix. She meets the same people at roughly the same
moments as in Chris's game, but takes her own route through the Arklay
mountains, the mansion, the guardhouse and the lab, with challenges of her
own.

This fork keeps the USA behaviour as the default. Everything here sits behind
a new `[Game] Mode=REB` and its own asset overlay, the same way `Mode=DC`
works (see `DC_PORT.md`), so the original game never changes.

## Story outline

**Prologue: the mountain.** Dawn on the morning after the training facility.
Rebecca has just said goodbye to Billy and is walking down the mountain
towards the mansion. These are new outdoor rooms, because RE1 has nothing like
them. Billy is not in RE1's data, so the goodbye opens as a text card. A
cutscene with a new model can come later.

**Acts.** Her route crosses Chris's story at the meetups below. Between them
she is somewhere Chris never sees, and the remix decides what happens there.

| Area | Room files (Chris variant) | Canon moment to keep or rework |
| --- | --- | --- |
| Mansion 1F | save room `room1000`, bar `room10f0` | first meeting with Chris, the piano |
| Mansion 2F | pillar passage `room20d0`, front of attic `room20e0` | Richard poisoned, the serum |
| Guardhouse | beehive passage `room4080`, drug storehouse `room4090`, Plant 42 room `room40c0` | V-Jolt, Plant 42 |
| Lab | emergency tunnel `room5010`, B3 elevator entry `room50c0`, power room `room5110`, main lab entry `room5140`, B3-B4 elevator `room5150` | Wesker, the escape |
| Mansion return | save room `room6000`, 1F left stairs `room6010`, bar `room60f0`, 2F small library `room7060` | the Hunter attacks |

These are the rooms whose scripts place Rebecca as an NPC in Chris's game,
read from the US PS1 disc. The names come from the debug room lists in
`src/game/DebugMenu.cpp`. What each scene does still has to be read from its
event script.

At each meetup the roles flip: Rebecca is the player and Chris is the NPC.
Jill's scenario already uses Chris as an NPC (`room5001`, `room5011`), so the
engine supports that.

**Her challenges.** She is a medic and a chemist, not a soldier:

- mixing puzzles for the serum and V-Jolt, and treating Richard;
- less health and space: the engine already gives her 88 HP to Chris's 140,
  6 item slots, and a Beretta with 15 rounds (`RoomInit.cpp:414`,
  `GameStart.cpp:121`);
- escort and defend moments, and rooms she must cross before Chris has
  cleared them.

## What the engine already does

- `room_set` switches the player to Rebecca when `g_CharacterModelId` is 3,
  with her own health and her own item slots (`RoomInit.cpp:410-456`). Room
  scripts most likely set that id with opcode `0x08`, field 9
  (`CmdFunctions.cpp:289`). That is not yet confirmed against a room script.
- She loads the Chris variant of each room (`...0.rdt`), because the switch
  never sets `MSF_CHAR_VARIANT` (`RoomInit.cpp:722-732`).
- Character select only offers Chris and Jill (`CharacterSelectionScreen.cpp:699`),
  and `SetInitialItems` sends everyone who is not Chris down Jill's 8-slot
  path (`GameStart.cpp:121`). Starting a new game as Rebecca needs both fixed.
- Damage tables read Jill's block for Rebecca (`WeaponDamage.cpp:545`).
  Endings branch on the character (`EndingScreen.cpp:236`).

## Testing

Every milestone is checked by an automated run, not by hand.

**Test mode** (`RE1_TEST=1`), added to this port:

1. **State stream.** One JSON line whenever state changes, written at the end
   of `main_loop()`:
   - screen mode, from the `MSF_*` flags;
   - stage, room and camera;
   - the player's character, position, angle, HP, weapon and items;
   - each enemy's type, position and HP, from `g_EnemiesList`;
   - the message on screen and the Yes/No cursor, from `g_menu_choice_id`;
   - flag changes.
2. **Live input.** The harness sends pad presses over the same channel. It
   extends the existing `RE1_TEST_KEYS` hook in `plat_key_state()`, which today
   only plays a fixed list of 16 keys from launch.
3. **No focus pause and no single-instance lock** in test mode. Runs then
   work in the background, and several can run at once.
4. **Screenshots on request** through the existing backbuffer save, for people
   to review.

**The harness** runs tests written as goals and checkpoints. Code does the
exact work: walking door to door with room collision data, setting up flags
and items, and checking facts like the room number. Jev, TypeSafe's typed
judgment model, makes the fuzzy calls on the text stream. It only takes text,
so it never sees the screen:

- a Choice of the next step from options code offers, such as "go through
  door 2", "answer Yes" or "skip dialogue";
- a Noul for whether a checkpoint really passed, such as "Rebecca gave
  Richard the serum and the scene ended";
- stuck detection when nothing moves toward the goal.

Answers with low confidence go to a person, or to a reasoning model with a
screenshot.

## Milestones

Each one ends with something playable, checked by the harness.

1. **Harness.** Test mode, the state stream, live input and checkpoint
   judging. First test: new game to the first zombie, the run that was driven
   step by step with screenshots on 2026-10-10.
2. **Rebecca from a new game.** `Mode=REB`, the `REB/` overlay, a third
   character card, the initial items fixed for 6 slots, and a placeholder start
   room inside the mansion.
3. **Tools,** in `retro-archive-explorer`:
   - a script assembler, from the decompiled pseudo-C back to bytecode,
     proven by rebuilding all 320 rooms byte for byte;
   - an RDT writer that rebuilds the offset table;
   - a message text writer;
   - a map of free story flags.
4. **The mountain.** The first new outdoor room, modelled and rendered in
   Blender from each camera, converted to `.pak` backgrounds with collision
   and masks. The prologue starts here.
5. **Arrival and the first meeting.** Her way into the mansion, the route to
   the save room, and the meeting with Chris as an NPC, plus her first puzzle.
6. **The other acts,** following the meetup table.
7. **Her ending,** new lines (text first, then voice), and polish.

## Sharing

The game data is Capcom's. Ship patches that build `REB/` from the player's
own GOG files, never the files themselves. Code changes in this fork stay
under the GPL-3.0, like the rest of the port.
