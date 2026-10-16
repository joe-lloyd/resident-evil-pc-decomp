# Rebecca's day

Rebecca's scenario is a game of its own that runs on this engine in front of
Resident Evil. It covers the day nobody saw: from the morning she says
goodbye to Billy to the night Chris finds her in the mansion's save room. It
should be as big as the mansion: 58 rooms (the mansion's two floors are 58
rooms with 295 camera angles, counted from the game's room files).

This plan replaces the chapter-by-chapter remix of Chris's game. That work is
shelved on the `chapters-2-6` branch. The engine fixes and the test harness
it produced stay.

## The day

Resident Evil 0 ends at dawn on 24 July 1998. Rebecca and Billy part on a
ridge above the burning training facility. Alpha Team reaches the mansion
that night, and Chris finds Rebecca in the 1F save room. In between, she has
a whole day alone on the mountain, and nothing in canon says what she did.

Her way down is the gondola from the ranger station to the valley. It is
dead, and getting it running is most of the game. From the ranger station's
yard she goes out three ways for what it needs, and the gondola takes her
down the mountain to the Spencer estate, in through the cellar and up into
the save room. Spent, she sits down against the wall and falls asleep.
Footsteps wake her, and Chris walks in.

| Act | Time | Rooms | What happens |
| --- | --- | --- | --- |
| 1 | Dawn to morning | 8 | The ridge, the ranger station, the winch and the pine, the gorge, and the dead gondola |
| 2 | Late morning to afternoon | 34 | From the yard: power to the west, the drive cog at the logging camp to the north, the operator's key in the mine to the east |
| 3 | Dusk | 12 | The gondola stops at a pylon; the valley; Bravo's helicopter; the gardener's lodge; the estate wall |
| 4 | Night | 4 | The cellar, under the floor, the save room: sleep, Chris, her credits |

## How the levels work

- **Every act is a hub with spokes.** The way on from the hub is blocked.
  What clears it is out along a spoke, and that spoke is blocked by
  something found along another. She goes out, comes back, goes out again,
  and the hub changes as she does: the lights come on, a gate stands open,
  a tree lies off the path.
- **The way on is never one step.** The thing that clears the way is locked
  up, and what unlocks it is somewhere else: power for a machine, fuel for
  the generator, a key on a dead man.
- **Shortcuts.** Once she is past an obstacle, something on the far side
  opens a quick way back: a gate that only opens from one side, a lowered
  bridge section, a lift. Later acts send her back for something she saw and
  could not use yet, and the shortcut makes that a short walk.
- **Something moves in every scene:** a lamp flame, smoke from a chimney,
  grass in the wind, a river far below. The backgrounds loop a few seconds
  of animation and change when the story changes them.
- **Places tell their own story** through what was left in them.
- **The light tells the time.** Each act is rendered for its hour.

## The plan

The plan is data: `tools/rebecca/plan/day.ts` has every room, the ways
between them and what locks them, and every step she takes, each with the
steps it needs. `node tools/rebecca/plan/page.ts <dir>` checks it and draws
it as one page: for each act a puzzle dependency chart, a lock and key map
and a beat chart, then a count of how many steps are open at each point of
the day, and a storyboard of the built cameras. The check fails a plan with
a step that can't be reached, a step whose needs don't get her to its room,
or a find nothing uses (`plan.test.ts` runs it). The page is published at
https://home.arpa/research/rebecca-plan/.

Change the plan there first, then build to it. Rooms, steps and camera
counts in this document are a summary of that file.

## Her voice

She is alone for most of the game, so her thoughts carry it. Thoughts are
plain lines; speech is in quotes:

```
Billy's gone. It's just me now.
"Hello? Is anyone there?"
```

Thoughts come when she enters a place for the first time, when she checks
something, and at turning points. Each act has a few. They stay short, two
lines of the message box at most.

## People

- **Billy** is never seen. The game opens just after he has gone.
- **The ranger's partner** is out on the mountain looking for him. She is
  tracking the same drag marks when Rebecca meets her in the woods. At the
  hollow they find him together, and she gives Rebecca his truck keys.
  After that she keeps turning up:
  - at the camp's barricade, where she takes the camp and sends Rebecca up
    the road;
  - on the lookout tower's radio, with news that the dogs came from the
    estate's kennels;
  - in the valley, where she has come down the old trail, and they head for
    the estate together.

  How her day ends is still to decide.
- **Hal**, the gondola operator, was bitten before dawn and went to hide in
  the mine with the drive key.
  - At the end of act 1 the booth's phone is off the hook. When Rebecca
    picks it up, it's Hal on the mine's field phone. He tells her what the
    gondola needs: the line powered, a new drive cog and a fuse. He has the
    key; she should come and find him.
  - She finds him in the flooded gallery, alive on the ore cart, once she
    has drained it. He gives her the key, and then the bite takes him.
- **The dead tell the rest:** the ranger, the cook, the line workers, Walt
  in the lookout, Kevin in Bravo's helicopter. Their notes and diaries are
  files.
- **Chris** appears at the end, as he does now.

The partner and Hal are RE1 character models with skins of our own:
`docs/handoffs/2026-10-14-reb-npc.md`.

## Enemies

All of them are RE1's own. Crows, Adders and Cerberus on the mountain;
zombie loggers at the camp; Web Spinners in the mine; a pack of Cerberus at
the estate's kennels. Ammunition stays short: she is a medic with a
Beretta, and running is often the answer.

## Items and puzzles

New key items reuse existing item ids and models where they can: the
ranger's keys, bolt cutters, a jerrycan, a drive cog, fuses, the operator's
key, a crowbar. The puzzles are small and physical: fuel for the generator,
a sluice to run the sawmill, dynamite for a rockfall, a pump to drain the
mine. Notes are messages, read where she finds them.

## Saving

She saves the way Chris and Jill do: at a typewriter, with an ink ribbon,
in a quiet room with an item box and RE1's own save room music, played from
the player's game files. The save rooms are placed the way RE1 places its
own. `tools/rebecca/plan/re1-saves.ts` measures that from the PC room files:
7 typewriter rooms in 107 rooms, a room 2.7 doors from one on average and 6
at the most, most of them dead-end side rooms off a corridor or a hub she
keeps passing.

Her day has five, plus the mansion's at the end. Each is a side room off a
hub:

- the ranger's cabin, off the station yard;
- the foreman's office, off the camp yard, behind the key on the dead cook;
- the operator's booth, off the gondola station, the last save before the
  ride down;
- the mine office, the one quiet room in the mine;
- the gardener's lodge, across the creek, before the kennels.

A room in her day is 2.7 doors from a save room on average, and none is
farther than 6. `plan.test.ts` holds the plan to those numbers, to no more
than one save room in ten rooms, and to quiet rooms that play the save
music.

Each room has a typewriter, modelled in its scene (`kit.typewriter`), and
RE1's own item box. In RE1 the box's lid is a 3D object, the same in every
save room, and the body under it is painted into the background. Her rooms
do the same: the builder copies the lid, object model 0 of the mansion's
save room, from the player's files, the room script places it with `obj`,
and `kit.item_box` paints a body to fit under it, in the lid's rusted metal
and embossed trim. Pressing action swings the lid open with the game's own
sound, then the box screen opens. A box can be scaled with its lid; the
cabin's is 0.65, a footlocker at the bunk's foot. The scripts set both up as
the mansion's save room does (`SCE_TYPEWRITER`, `SCE_ITEMBOX`). All the
boxes share one store, as in RE1. The ink ribbons are RE1's own item, beside
the cabin's typewriter.

A save made on her day records it (bit 0x80 of the save's mode byte, 0x233),
and loading it puts the game back in her mode, from the shipped game's
title screen too. The save screen calls her REBEC, five letters being all a
row has, and names her saves by her places: Ranger Station, Logging Camp,
Gondola Station, Silver Mine, Gardener's Lodge. `tools/harness/tests/reb-save.ts`
saves in the cabin and loads it back from the shipped game's title;
`reb-save-rooms.ts` opens the box and the typewriter in the other four.

## Music

New pieces in the manner of RE1's, written as Strudel code with CC0 samples,
and RE1's own save room music at the end, from the player's files. Every
room and cutscene has a cue in `tools/rebecca/plan/music.ts`. The research
and the plan are in [REBECCA_MUSIC.md](REBECCA_MUSIC.md).

## Sound

Her steps follow what each scene says is underfoot: our own for earth and
gravel, RE1's for boards, rock, water and her other floors. Loops of the
gale, the forest, the mine, dusk, night and the cellar play as channels of
her music, where the music doesn't have that sound already. Her doors play RE1's door sounds, and her gates open
and shut. How it works is in [REBECCA_SOUND.md](REBECCA_SOUND.md).

## Scale

Rebecca stands 2700 game units tall (measured on screen,
`tools/harness/measure-height.ts`), so the scenes are built in metres with a
metre as 1700 units (`reb.UNITS`). Built at 1000, the first cabin came out
with her as tall as its door.

## What the engine and tools need

The trail proved that a new room can be built from a Blender scene. Making
the other 51 needs that to become a production line.

Room ids are not the limit. The stages have 38 free slots, fewer than her
rooms, but in her mode the REB tree is authoritative for stage files
(`src/system/AssetPath.cpp`), so any slot but the save room's can be one of
hers without touching Chris's and Jill's game.

1. **Room specs.** One file per new room: its id, its Blender scene, its
   cameras, the walkable floor, its doors and the scripts and messages. The
   builder makes the room file and the backgrounds from it. Today this is
   hard-wired to the trail.
2. **Masks.** Interiors need foreground masks, the parts of a background
   drawn over the character (a door frame, a table edge). Blender renders
   them as a second pass.
3. **Collision from the scene.** Walls and furniture come from marked
   objects in the Blender scene, not hand-typed boxes.
4. **Floors and stairs.** Rooms with height changes need the floor records.
5. **Doors between new rooms.** These work today; the door animations to use
   are picked per door.
6. **Item models.** A room can only hold an item whose model is in its item
   model table, so the builder copies the models a room's items need.
7. **Lighting per act.** The Blender scenes share a sky and light rig per time
   of day.
8. **Sleep and waking.** A scripted fade with time passing, before the
   meeting.
9. **Her credits.** A text credits screen after the meeting, in place of the
   ending movies.
10. **Rides.** The flume, the mine lift and the gondola play as sequences,
    the way the walks between outdoor rooms do.

Built so far, beyond the list above:

- **Moving backgrounds** (`src/game/BgAnim.cpp`, `tools/rebecca/bganim.ts`):
  Blender renders a loop of frames and any changes of state; the builder keeps
  the 16-pixel tiles that differ from the background, and the engine patches
  the background texture as the game runs.
- **Camera floors worked out from the scene** (`tools/rebecca/day/floors.ts`):
  each half metre of floor goes to the camera that shows her whole, unhidden
  and nearest the middle of the screen. `coverage.ts` prints the map and the
  share of floor where she is lost.
- **Rendering on the Blender machine** (`tools/rebecca/day/render.ts`, with
  `--preview` for a quick look).
- **Rebecca on the character select.** New Game deals three police cards when
  her day is installed; her ID is built from the player's own select sheet
  and status faces (`tools/rebecca/card.ts`). Choosing her switches the
  session to her mode and starts her day; her opening and intro come later.
- **Her map screen** (`tools/rebecca/maps`, `src/game/RebMaps.cpp`): an
  overview of the mountain that unlocks in four stages, a floor plan for
  each of her eleven areas drawn from the scenes, and six maps to pick up.
  The rooms she has been in are lit, the rest dim once she has the map, and
  hers blinks. [REBECCA_MAPS.md](REBECCA_MAPS.md) has how RE1's works and
  how hers is built.
- **Walks between outdoor rooms.** A door of the walk type plays a few
  seconds of a dark forest path at her eye height, with her footsteps
  crunching, where a door would open (`src/game/PathWalk.cpp`,
  `day/walk-forest`, `tools/rebecca/footsteps.ts`).

## Testing

`tools/harness/tests/day.ts` plays the day, or part of it, the way a player
would. Each stretch starts from a checkpoint: the game boots straight into
the stretch's room with the flags and items a player would have by then, so
a change to the shed is tested from the shed, not from the ridge.

    node tools/harness/tests/day.ts shed           # just the shed
    node tools/harness/tests/day.ts shed bridge    # from the shed to the bridge
    node tools/harness/tests/day.ts                # the whole day, end to end

The whole day runs before a recording for the owner, before a merge, and
after a change to the engine.

## Building order

Each step ends with something playable, a harness test that plays it, and a
recording on the research page.

1. **The production line.** Room specs, masks, moving backgrounds, camera
   floors and collision from the scene. *(Done.)*
2. **Act 1's first loop.** The ridge, the trail, the station yard, the cabin,
   the shed, the winch and the gorge. *(Done.)*
3. **Act 1 complete.** The gondola station and the operator's booth.
4. **Act 2,** one spoke at a time: the woods and the logging camp, the
   forestry road and the generator, the quarry and the mine, then the
   gondola running.
5. **Acts 3 and 4,** with the ride down, the estate, the sleep, the meeting
   and her credits.
6. **Polish:** sound, music choices, balance, and her lines read aloud.
