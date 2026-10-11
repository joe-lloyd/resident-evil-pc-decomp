# Rebecca's story

The chapter outline for the Rebecca scenario: a loose remix of Resident Evil
1 from her side. The plan and the engine work are in `REBECCA_SCENARIO.md`;
what Chris's room scripts already do with her is in `REBECCA_MEETUPS.md`.
Room numbers are the file names, so `1000` is `ROOM1000.RDT`, the mansion 1F
save room.

Each chapter is built from room scripts, room messages and story flags. The
first chapters stay away from new event scripts (cutscenes): scenes are
messages, camera cuts and position changes, which the tools can already write.

## Prologue: down the mountain

Dawn, the morning after the training facility. Rebecca has said goodbye to
Billy, who is officially dead. She walks down the Arklay mountain towards the
mansion.

- **Narration:** the REB opening narration (global message 63).
- **Room:** the mountain trail, a new room (stage 2 room 0x12) built in
  Blender. Its door at the foot of the trail opens into the courtyard garden.

## Chapter 1: the back way

She reaches the mansion from the outside, through rooms Chris does not use
at this point in his game, and finds him in the save room.

- **Route:** the courtyard garden (3000), the storeroom (11B0), the roofed
  passage (11A0), the back passage (10A0), the 1F left stairs (1010), then
  the save room (1000). The back passage's bolted door is retargeted to the
  left stairs.
- **Her fights:** one Cerberus in the roofed passage and one zombie in the
  back passage. The garden's dogs and the left stairs' zombies start dead
  (bio card kill flags).
- **Meeting:** the roles are swapped. Chris waits in the save room; she walks
  in. Their exchange is room message 46, and checking him afterwards gives
  message 47.

## Chapter 2: Bravo's medic

At the end of the meeting a shot rings out upstairs. Chris tells her to wait
and goes to search the house; he is gone from the save room afterwards. She
goes up the 1F left stairs and finds Richard collapsed in the 2F corridor at
the top (2010), poisoned by the giant snake.

- **Her challenge:** a medic's errand against the clock. The Serum is on the
  medicine shelf in the save room (1000). Finding Richard starts a
  three-minute clock (state word 4, the game's seconds counter, which Chris's
  scene in 20D0 uses with a seven-minute limit). Back in time with the serum,
  she treats him. Too late, and "Richard is dead."
- **Flags:** FG_COMMON 200 (found him), 201 (his fate is settled), 202 (saved).
- **Rooms:** 1000, 1010 and 2010. Chris's game has Richard in 20D0, but the
  left stairs come up into the south half of 2010, which the stairwell walls
  off from the rest of the 2F. The other way up, through the main hall, runs
  through Chris's opening scenes.
- **Test:** `tools/harness/tests/chapter2-richard.ts` plays the errand;
  `SERUM_FIRST=1` takes the serum before going up.

## Chapter 3: Moonlight

The mansion bar (10F0). In Chris's game he cannot read music and she plays.
Here she takes the Music Notes off the shelf herself, plays "Moonlight
Sonata", and a hidden drawer in the piano gives up the Gold Emblem.

- **Way in:** a chapter break. Once Richard's fate is settled, the corridor's
  dead-end door (2010 door 1, which leads to an empty room slot in Chris's
  game) takes her to the bar.
- **Flags:** FG_COMMON 210 (played), 211 (title shown), 213 (way on open);
  FG_ITEM 7 (Music Notes taken).
- **Way on:** the bar's Sword Key door, open once she has the emblem, is a
  chapter break to the guardhouse.

## Chapter 4: the guardhouse

Her chemistry chapter.

- **Rooms:** the guardhouse passage (4080), the drug storehouse (4090) and
  Plant 42's room (40C0).
- **Her challenge:** she works out V-JOLT at the storehouse's mixing table and
  pours it on the roots that push under the door to Plant 42's room. That kills
  the plant (its kill flag, FG_ENEMY 96), and the Helmet Key lies beside it.
  Without the V-JOLT, the plant is alive when she goes in, as in Chris's game.
- **Flags:** FG_COMMON 220 (roots dead), 221 (title), 222 (mixed), 223 (way
  on open); FG_ITEM 240 (V-JOLT taken).
- **Way on:** with the key, Plant 42's door is a chapter break to the lab.

## Chapter 5: underground

She turns the elevator power on in the power room (5110) and meets Wesker by
the main lab (5140). He means to kill her; the lights fail and she runs.

- **Flags:** FG_COMMON 230 (power on), 231 (title), 240 (Wesker scene played).
- **Way on:** Wesker's far door is a chapter break back to the house.

## Chapter 6: the hunters

Back in the house, a Hunter prowls the 1F left stairs (6010). She has to get
past it to the stairs up; the stairs are a chapter break to the heliport.

- **Flags:** FG_COMMON 250 (title).

## Ending

The heliport (3030). Chris waits for Brad's helicopter; her epilogue is the
scene's text. When it closes the script sets MSF2_DEATH_VARIANT and
MSF_PLAYER_DEAD, so the game ends with no death screen, and ending_state plays
Chris's ending in which his partner lived (REB mode counts the player as Chris
there), then the credits and the offer to save the clear.

## Chapter breaks

Chris's routes between these places run through his own scenes: his opening
in the main hall, Kenneth's corridor, the courtyard and the caves. Until her
own routes are built, each chapter ends at a door that takes her straight to
the next chapter's first room, and each chapter opens with its title. These
are the places to add play areas next.

## Building order

Every chapter has a harness test that boots into its first room and plays
it (`tools/harness/tests/chapterN-*.ts`), and `full-playthrough.ts` plays them
all from a new game to the title after the ending. The chapters live in
`tools/harness/scenario.ts`. New chapters follow the same pattern: scripts in
`tools/rebecca/rooms/`, messages beside them, flags in the bio card or set by
scripts, and a test in `tools/harness/tests/`.
