# Rebecca's maps

Her map screen works the way RE1's does. An overview of the mountain unlocks
in four stages as she goes. Each of her eleven areas has a floor plan. A room
lights once she has been in it, and her own room blinks. Without an area's
map she sees only the rooms she has been in. With it she sees the rest,
dimmed. The plan for the areas and the maps is `tools/rebecca/plan/maps.ts`.

## How RE1's map screen works

The code is `src/game/MainMenu.cpp`, from `map_area_known` to
`menu_init_map_display`. The screen has two faces.

### The browser

The browser opens from the status screen's MAP tab. It draws one of four
overview pictures, `item_m2/map0d.tim`, `map0c`, `map00` and `map0e`
(`g_MapTabFileNames`). These are the mansion, then the courtyard, the
guardhouse and the lab. It loads the highest stage the player has reached.
Each overview is a 256 x 160 8-bit TIM with these parts:

| Part | In the picture | On the screen | Use |
| --- | --- | --- | --- |
| The estate | (0, 0), 160 x 72 | (33, 32) | `g_MapBaseDesc` |
| Stage cut-outs | four rectangles | over the estate | `g_MapSprites[0-3]`: each building, bright for the stage chosen and dim (0x40) for the rest |
| Stage names | (120, 72 + 16 * stage), 80 x 16 | (57, 104) | `g_MapSprites[4]` |
| Floor names | (232, 16 * row), 24 x 16 | (137, 104) | `g_MapSprites[5]`: 2F, 1F, B1 to B5 |
| Arrows | (160, 64), 4 x 8 x 8 | (145, 96), (145, 120) | `g_MapSprites[6-7]`: up and down, grey and lit |

Left and right step between stages. Up and down step between the areas of a
stage, four at most (`g_MapAreaTable`, four entries per stage). Confirm opens
the area's map.

### The area maps

The display zooms in on `item_m2/map01.tim` to `map0b.tim`, one per area
(`g_MapFileNames`). It shows them over `Map_blue.tim`, a grid drawn at half
strength on top. An area map is a 128 x 128 8-bit TIM: an 8-byte header, a
CLUT block of 256 colours and the pixels. The file is 16928 bytes. The
screen shows the top 100 rows at (48, 28), one pixel to one pixel.

What the screen shows is decided by rewriting the CLUT in memory before the
picture is loaded, not by the pixels:

| CLUT entries | What they draw |
| --- | --- |
| 7 to 12 | The walls and marks of every room. Zeroed when the area's map is not owned |
| 13 + 6k to 18 + 6k | Room k of the map's group: +0 doors, +1 and +2 dark marks, +3 the floor |

For each room k of the group: when it is not visited, entries +0 to +5 are
zeroed if the map is not owned, or +1 to +3 if it is. That leaves the walls
and doors of an unvisited room. The room the player is in has +1 to +3
zeroed. The picture is then loaded a second time onto another page with only
that room's +1 to +3 set to red. That page is drawn over the first, with its
red channel pulsed on an 80-frame cycle, which makes the room blink. Pixels
whose colour has become 0 are set to index 0, which is the clear colour.

A room is room k of its group. The group is the stage modulo 5. Its visited
bit is `g_RoomFlags` bit `g_StageRoomFlagOffset[group] + room id`
(`room_set_visited_flag`). Owning a map is bit 0x7C + map index. A map index
is the item id less 0x4E. Picking up items 0x4E to 0x53 sets that bit
(`pickup_key_event`).

RE1's colours are: walls 0x5AD6, doors 0x12DC, dark marks 0x00E1 and floors
0x81A4.

## Hers

`tools/rebecca/maps` draws her pictures in these formats, from her plan and
her scenes. `tools/rebecca/build.ts` puts them in the overlay's `ITEM_M2`
under RE1's names. In her mode the REB tree is read first, so Chris's and
Jill's games keep RE1's pictures.

- `plans.ts` lays out each area as a floor plan. Every room is at its real
  size, from its scene's `renders/room.json`. It is turned and placed so
  that its doors meet its neighbours' doors. A building's door in a yard
  puts the building on the footprint the yard leaves for it. A walk between
  two outdoor rooms is drawn as a trail three metres long. A room that would
  stand on another moves further out, or to another side of its door, such
  as a tower's top beside its stairs. A plan taller than it is wide is
  turned a quarter turn to fit the screen.
- `draw.ts` draws each plan in RE1's palette scheme and colours. Room k is
  the area's k-th place in `maps.ts`. The walls are one pixel between two
  rooms, as RE1's are.
- `overview.ts` draws the mountain from above, from the plan's map of it
  (`plan/research/layout.ts`). Down the slope runs left to right. It shows
  forest over a lit relief, the river through the gorge, trails, roofs, the
  gondola's cable and the mansion. Each stage's picture shows its places and
  those of the stages before (`maps.ts` `STAGES`). Her overview is 256 x 256,
  to have room for the cut-outs and eleven area names.
- `engine.ts` writes `src/game/RebMaps.cpp`. It holds each room's area,
  palette block and visited bit, which map shows each area, the stages, and
  where each sprite is in the overview.
- `pickups.ts` places her six maps (`MAP_ITEMS`) in the rooms the plan
  gives them. Each uses RE1's own map items 0x4E to 0x53, in RE1's folded-map
  model, with FG_ITEM flags 248 to 253. The cabin's map is on its desk, in
  the hand-written `day/lookout/room.c`. `day/scripts.ts` writes the others.
  A map's pickup comes before the room's checks in its table, and the room's
  supplies are placed around it. RE1 takes its maps through a room event
  with a message. Hers are pickups, so the room's main script says her line
  the frame the map's flag clears.

`node tools/rebecca/maps/preview.ts <dir>` draws every map and the overview
as the screen would show them.

### What the engine does in her mode

- `room_set_visited_flag` sets her own bit for the room, one per place.
  RE1's bit would be wrong for her rooms: her room ids run past each
  stage's own, and stage 4 room 0x1E gave bit 0x82, the first file's
  collected bit.
- An area is its own group. Its rooms and its map come from `RebMaps.cpp`.
- A room on a map she owns but has not been in is dimmed, with its colours
  halved. RE1 leaves such a room as bare walls.
- The browser draws her stage cut-outs and her area's name, 104 x 16, in
  place of the building's name and floor. Left and right step through the
  stages she has reached, in order.
- The objective highlight, Chris's and Jill's, is off.

## Testing

`node --test tools/rebecca/maps/maps.test.ts` checks the files and tables.
It checks the pictures' format, that every room is drawn in its own block,
that no two rooms are drawn over each other, the overview's stages and
sprite layout, a visited bit for every room, and every map's pickup.

`tools/harness/tests/maps.ts` plays it in the game. Before any map, it
visits two rooms of each area and opens the map there. It then picks up the
six maps. Next it opens each area's map again, then Chris's. It checks the
screen against the tools' pictures. The browser must show her overview and
the area's name. Each map pickup must give its map and her line. A visited
room must be lit, an unvisited one dim with the map and hidden without it,
and her room must be red and blink. Chris's browser must not be hers.

    PORT=7830 RE1_LAB_GAME_DIR='D:\Games\RE1-maps' RE1_OVERLAY=<out>/REB node tools/harness/tests/maps.ts <outdir>
