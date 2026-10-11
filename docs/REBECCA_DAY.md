# Rebecca's day

Rebecca's scenario is a game of its own that runs on this engine in front of
Resident Evil. It covers the day nobody saw: from the morning she says
goodbye to Billy to the night Chris finds her in the mansion's save room. It
should take as long to play as the mansion does the first time: about fifty
rooms, two to three hours.

This plan replaces the chapter-by-chapter remix of Chris's game. That work is
shelved on the `chapters-2-6` branch. The engine fixes and the test harness
it produced stay.

## The day

Resident Evil 0 ends at dawn on 24 July 1998. Rebecca and Billy part on a
ridge above the burning training facility. Alpha Team reaches the mansion
that night, and Chris finds Rebecca in the 1F save room. In between, she has
a whole day alone on the mountain, and nothing in canon says what she did.

Her way down is one Chris and Jill never see. It runs down the mountain
through a ranger station and a logging camp, under the valley through
Umbrella's water works, and into a forgotten cellar beneath the mansion. She
climbs up through the floor into the save room. Spent, she sits down against
the wall and falls asleep. Footsteps wake her, and Chris walks in.

| Act | Time | Hub | What it is about |
| --- | --- | --- | --- |
| 1 | Dawn to morning | Ranger Station 3 | Alone for the first time; finding her feet |
| 2 | Midday | The logging camp | The infection has reached the mountain |
| 3 | Afternoon | The pump house | Umbrella built under the whole valley |
| 4 | Dusk | The aqueduct | Someone else survived down here |
| 5 | Night | The save room | Sleep, waking, Chris; her credits |

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

## Places

Each place is one or more new rooms: our own backgrounds, cameras, collision
and scripts. Room ids come from the free slots in stages 3, 4 and 5 (14, 14
and 10 slots); a room's stage only decides its file name and id.

### Act 1: the mountain, dawn to morning

Hub: **Ranger Station 3**, a yard with the ranger's cabin, his tool shed and
his truck. Three ways lead out of it.

| Room | Built | What is there |
| --- | --- | --- |
| The ridge | yes | Where the game opens; the training facility burning below |
| The mountain trail | yes | Down through the spruces to the station |
| The station yard | yes | The hub: the pine across the trail down, the truck and its winch, his rifle in the grass |
| The cabin | yes | He left in a hurry; the radio; the logbook; the shed key |
| The tool shed | yes | The winch's crank; spare fuses he had no use for |
| The woods behind the cabin | | Where the drag marks lead: the ranger, dead, his truck keys in his jacket; dogs |
| The forestry road | | West out of the yard to a chained gate |
| The generator hut | | Powers the station and the gorge ferry; out of fuel |
| The fire lookout tower, foot and top | | The ferry's control key; the valley seen from above, and smoke where Bravo's helicopter came down |
| The gorge, near bank | yes, as the bridge | The footbridge is out in the middle; the cable ferry's station |
| The gorge, far bank | | The valley trail on down; the lever that lowers the bridge's missing section |

How it chains:

1. The trail down is blocked by a fallen pine. The truck's winch can drag
   it, but its crank is in the shed, the shed is padlocked, and the key is in
   the cabin. Taking the key brings a dog out of the trees. *(Built.)*
2. Past the pine the gorge bridge is out. The cable ferry across needs power
   and its control key.
3. The power is the generator up the forestry road. The road's gate is
   chained; bolt cutters are in the truck's toolbox, which is locked; the
   truck keys are on the ranger's body in the woods, where the dogs are.
4. The generator is dry. The jerrycan in the truck's bed, there from the
   start, fills it. The station's lights come on.
5. The ferry key is at the top of the fire lookout tower, further along the
   forestry road.
6. Across on the ferry, the far bank's lever lowers the bridge's missing
   section: the shortcut back to the station. Act 2 sends her back up it for
   the fuses in the shed.

### Act 2: the logging camp, midday

Hub: **the camp yard**, stacked timber and trucks. About twelve rooms: the
yard; the bunkhouse, where the loggers have turned; the mess hall; the
foreman's office and its safe; the sawmill; the mill pond; the log flume; the
cable car's upper station; the fuel depot; the radio shed; the lower camp.

- The cable car down to the valley needs power at the sawmill, a fuse (the
  ones left in the ranger's shed: back up over the Act 1 shortcut), and the
  operator's key from the foreman's safe, its combination on the bunkhouse
  calendar.
- The sawmill's power needs the belt refitted and the mill race opened from
  the pond.
- The log flume is a one-way ride from the mill down to the lower camp, and
  once ridden, the lower camp's gate opens back to the yard.

### Act 3: the water works, afternoon

Hub: **the pump house** by the reservoir, Umbrella's water works built to
look like a municipal plant. About ten rooms: the dam walkway, the pump
house, its control room, the valve gallery, the filter beds, the service
tunnel's mouth, the tunnel junction, the maintenance office, the Web
Spinners' storeroom, Umbrella's lift.

- The pumps' pressure has to be set, valve by valve, from readings around
  the plant, to drain the tunnel.
- The lift down needs power and a keycard; once down, the lift is the
  shortcut back up.

### Act 4: the aqueduct, dusk

Hub: **the aqueduct**, an old brick watercourse that predates Umbrella,
partly flooded. About ten rooms: the channel, the sluice room, the
scientist's cache, the brick gallery, the Neptune pool, the old cellar, the
cistern and its control room, the gate under the mansion.

- A researcher who fled the lab is hiding in the cache, hurt and frightened.
  He tells her what the T-virus is doing to the valley and that the tunnels
  come up under the mansion, and gives her the key to the cistern gate. When
  she comes back past, he is gone, or worse.
- Draining the aqueduct at the sluice opens a dry way back to the cache.
- The cistern under the mansion's foundations is a Black Tiger's nest: her
  first real boss fight.

### Act 5: night

The crawlspace, the passage under the floorboards, and the save room. She
climbs up through the floor of ROOM1000. Too tired to go on, she sits against
the wall. The screen fades, and time passes. Footsteps wake her, and Chris
walks in: the meeting we already built. Then her own credits.

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
- **The scientist** reuses an RE1 model with a new texture: a lab coat on an
  existing NPC body. He stands or sits; he does not move around.
- **Chris** appears at the end, as he does now.
- **Voices** on the ranger's radio: S.T.A.R.S. chatter, in text.

## Enemies

All of them are RE1's own. Crows, Adders and a Cerberus on the mountain;
zombies at the camp; Web Spinners in the tunnel; a Neptune in the aqueduct;
a Black Tiger in the cistern. Ammunition stays short: she is a medic with a
Beretta, and running is often the answer.

## Items and puzzles

New key items reuse existing item ids and models where they can: the
ranger's key, a fuse, a valve handle, the cistern key. The puzzles are small
and physical: power for the cable car, pressure in the pump house, a gate key
from the scientist. Notes are messages, read where she finds them.

## Scale

Rebecca stands 2700 game units tall (measured on screen,
`tools/harness/measure-height.ts`), so the scenes are built in metres with a
metre as 1700 units (`reb.UNITS`). Built at 1000, the first cabin came out
with her as tall as its door.

## What the engine and tools need

The trail proved that a new room can be built from a Blender scene. Making
some 25 of them needs that to become a production line.

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
10. **The scientist.** An NPC with a swapped texture, loaded from the
    overlay.

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
3. **Act 1 complete.** The woods, the forestry road, the generator, the
   lookout tower, the ferry and the far bank's shortcut.
4. **Acts 2 to 4,** one at a time, each a hub with its spokes and shortcuts.
5. **Act 5,** with the sleep, the meeting and her credits.
6. **Polish:** sound, music choices, balance, and her lines read aloud.
