# Rebecca scenario plan

A new scenario mode for this port: Rebecca Chambers' own game, played in
front of Resident Evil. It covers her day alone, from leaving Billy at dawn to
Chris finding her in the mansion's save room that night, on new maps of our
own. The story and the places are in `REBECCA_DAY.md`; this file covers how
the mode is built and tested.

This fork keeps the USA behaviour as the default. Everything here sits behind
a new `[Game] Mode=REB` and its own asset overlay, the same way `Mode=DC`
works (see `DC_PORT.md`), so the original game never changes.

## Story

See `REBECCA_DAY.md`. An earlier plan remixed Chris's game chapter by
chapter; that work is on the `chapters-2-6` branch.

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
   the save room, and the meeting with Chris as an NPC. Done as a stand-in
   route through Chris's rooms; her own day replaces it.
6. **Her day,** act by act, on new maps, in the order `REBECCA_DAY.md` gives.
7. **Her ending:** the sleep, the meeting, her credits; then polish.

## Sharing

The game data is Capcom's. Ship patches that build `REB/` from the player's
own GOG files, never the files themselves. Code changes in this fork stay
under the GPL-3.0, like the rest of the port.
