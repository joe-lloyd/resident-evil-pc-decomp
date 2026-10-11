# Rebecca's day

Rebecca's scenario is a game of its own, a couple of hours long, that runs
on this engine in front of Resident Evil. It covers the day nobody saw: from
the morning she says goodbye to Billy to the night Chris finds her in the
mansion's save room.

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

The light tells the time. Each act is rendered for its hour, from dawn on the
ridge to the dark of the cellar.

Every scene has something moving in it: a lamp flame, smoke from a chimney,
grass in the wind, a river far below. The original game's backgrounds were
still pictures; ours loop a few seconds of animation, and change when the
story changes them (a tree dragged off a path).

The way down is blocked, again and again, and getting past takes more than
one step: the thing that clears the way is locked up, and what unlocks it is
somewhere else. Places tell their own story through what was left in them.

| Act | Time | Where | What it is about |
| --- | --- | --- | --- |
| 1 | Dawn to morning | The ridge, the forest trail, the ranger's lookout | Alone for the first time; finding her feet |
| 2 | Midday | The logging camp, the sawmill, the cable car | The infection has reached the mountain |
| 3 | Afternoon | The pump house, Umbrella's service tunnel | Umbrella built under the whole valley |
| 4 | Dusk | The aqueduct, the scientist's cache, the old cistern | Someone else survived down here |
| 5 | Night | The crawlspace, the save room | Sleep, waking, Chris; her credits |

## Places

Each place is one or more new rooms: our own backgrounds, cameras, collision
and scripts. Room ids come from the free slots in stages 3, 4 and 5 (14, 14
and 10 slots); a room's stage only decides its file name and id.

### Act 1: dawn to morning

1. **The ridge.** The game opens here. Smoke rises from the training facility
   below. Billy has just gone into the trees. Her first thought sets her goal:
   the Bravo team's last position was near an old mansion in the valley.
2. **The forest trail.** The mountain trail room we already have, re-rendered
   at morning. Crows.
3. **The ranger station.** A yard with the ranger's cabin, his tool shed and
   his truck. The trail down is blocked by a pine the storm brought down.
   - The cabin: he left in a hurry. Breakfast half eaten, a chair knocked
     over, the rifle gone from its rack, the east window smashed in with blood
     on the sill. The radio picks up S.T.A.R.S. chatter. His logbook says he
     meant to winch the pine clear after breakfast, and that the crank is in
     the shed. The shed key hangs by the door; a first aid spray is on the
     table.
   - The yard: his rifle lies empty in the grass by drag marks into the trees.
     Once she has the key, a Cerberus comes out of them.
   - The shed: padlocked. Inside, the chainsaw he gave up on, and the crank.
   - The truck: the crank turns the winch, and the pine drags off the trail.
4. **The ravine bridge.** A plank footbridge over a gorge, adders in the long
   grass, and the valley trail sign on the far side.

### Act 2: midday

5. **The logging camp.** A yard of stacked timber and trucks.
6. **The bunkhouse and the sawmill.** Interiors. The loggers have turned.
   Zombies, a shotgun, and a fuse for the cable car.
7. **The cable car station.** She restores power and rides down to the
   valley. The ride is a fade between two stations.

### Act 3: afternoon

8. **The pump house.** By the reservoir, Umbrella's water works, built to
   look like a municipal plant. She has to work out its pressure controls.
9. **The service tunnel.** Concrete, emergency lights, Web Spinners. Umbrella
   signage gives the first hint of what lies under the valley.

### Act 4: dusk

10. **The aqueduct.** An old brick watercourse, partly flooded, that predates
    Umbrella. Something large moves in the water.
11. **The scientist's cache.** A researcher who fled the lab is hiding in a
    supply room, hurt and frightened. He tells her what the T-virus is doing
    to the valley, and that the tunnels come up under the mansion. He gives
    her the key to the cistern gate. When she comes back past, he is gone,
    or worse.
12. **The cistern.** Under the mansion's foundations: a Black Tiger's nest.
    Her first real boss fight.

### Act 5: night

13. **The crawlspace.** A low passage beneath the floorboards, to a hatch.
14. **The save room.** She climbs up through the floor of ROOM1000. Too
    tired to go on, she sits against the wall. The screen fades, and time
    passes. Footsteps wake her, and Chris walks in: the meeting we already
    built. Then her own credits.

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

## Building order

Each step ends with something playable, a harness test that plays it, and a
recording on the research page.

1. **The production line, on Act 1.** Room specs, masks and collision from
   the scene, proved by building the ridge and the ranger's lookout.
2. **Act 1 complete.** The ridge, the trail at morning, the lookout and the
   bridge, played from a new game.
3. **Acts 2 to 4,** one at a time.
4. **Act 5,** with the sleep, the meeting and her credits.
5. **Polish:** sound, music choices, balance, and her lines read aloud.
