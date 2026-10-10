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

Chris leaves to search the mansion. She hears a shot upstairs and finds
Richard in the 2F pillar passage (20D0), poisoned by the giant snake.

- **Her challenge:** a medic's errand against the clock. The Serum is in the
  save room (1000), where Chris's game also keeps it, as hidden items 6 and 7.
  Treating Richard in time sets the canon "serum given" flag (SF 0x7F).
  Too late, and "Richard is dead." (SF2 0x64).
- **Rooms:** 1000, 1010, the 2F rooms between them and 20D0.

## Chapter 3: Moonlight

The mansion bar (10F0). In Chris's game he cannot read music and she plays.
Here she finds the sheet music herself and plays "Moonlight Sonata" to open
the hidden room behind the bar.

## Chapter 4: the guardhouse

The courtyard and the guardhouse, her chemistry chapter.

- **Rooms:** the beehive passage (4080), the drug storehouse (4090) and the
  Plant 42 room (40C0).
- **Her challenge:** mixing the chemicals for V-Jolt in the drug storehouse.
  In Chris's game only she can do this.
- **Fight:** Plant 42.

## Chapter 5: underground

The lab. She powers the elevators (5110) and meets Wesker at the main lab
entry (5140). In this remix she gets away from him.

## Chapter 6: the hunters

Back in the mansion, Hunters roam. The attack on the 1F left stairs (6010)
and the small library (7060) are hers to survive.

## Ending

She reaches the heliport with Chris. Her ending is new text, then the
credits.

## Building order

The prologue and Chapter 1 come first, end to end, with a harness test that
plays them. Later chapters follow the same pattern: scripts in
`tools/rebecca/rooms/`, messages beside them, flags in the bio card or set by
scripts, and a test in `tools/harness/tests/`.
