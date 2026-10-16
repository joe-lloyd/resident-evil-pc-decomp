# Overnight run, 14-15 October: the tracker, from the top

The owner went to bed on 14 October and asked for the tracker
(https://home.arpa/research/rebecca-todo/) to be worked through one row at a
time, starting with the RE1 look, with assumptions written down here for the
morning. The other Claude session that owned the rooms was not running, so
the room kit and scenes were taken over for this run. The work is on the
branch `reb-look`.

## Assumptions to check

1. **No frame-wide grain.** The owner wants the look to come from textured,
   bitty surfaces, not a film grain over the picture. So the texture is in
   the materials and the geometry. When the look filter goes into the build,
   it does the tone curve and the game's 15-bit colour only, without grain.

2. **How bright an interior is.** RE1's interiors average 51-60 of 255,
   with about a quarter of the frame near black. Ours averaged 9-21, with
   up to 90% near black. The kit's fill light is set to 6 W per square
   metre of floor. That brings the lodge, gallery and bunkhouse to roughly
   40-50 with 20-35% near black, before the look filter's curve.
   `RE1_FILL` tunes it for the whole set.

3. **Where she comes up in the save room.** She arrives from the crawl
   space standing on the trapdoor, at the open floor in the middle of
   camera 0 (5200, 5600), facing Chris. Before, she arrived by the
   typewriter, which didn't match a trapdoor.

4. **Which door animation each door plays.** I chose them from the door
   textures in the player's `item_m1/*.dor`, and RE1's own rooms gave the
   direction, sound and handle bytes for each:
   - the plank door (`door07`) for cabins, sheds and huts;
   - a worn panel door (`door15`) for the booth, office, cottage, lodge and
     wine store;
   - rusty iron (`door08`, `door11`) for the generator, switch house,
     workshop, quarry office and the mine's passages;
   - grey steel (`door10`, `door12`) for the lower station, the weather
     station and the gondola car;
   - the ladder (`lad01`) for the tower top, the pylon and the hatch;
   - the industrial lift (`ele02`) for the mine lift.
   The table is `DOOR_STYLE` and `CLIMB` in `day/scripts.ts`.

5. **More flags for first thoughts.** The kit rooms' "been here" flags ran
   from `FG_COMMON` 207 to 255, 49 of them, for 51 rooms. The crawl space
   and the wine store never showed their first thought. The rest now come
   from 109-158, a run no shipped room script and no engine flag touches,
   and the trail has 159.

6. **The enemies.** Counts follow the plan's wording: "Zombies" is two,
   "Zombie loggers" three, "a pack" three, a bare kind two.
   - Zombies use RE1's green-coat zombie (entity 17) for the loggers and
     everyone else; RE1 has no logger.
   - Each kind gets the behaviour byte RE1's rooms most often give it.
   - They are always there, not tied to an act. Their kill flags (186-254)
     keep them dead once killed.
   - The gondola car's crows are left for its cutscene.
   - "A zombie in a bunk" and "a zombie in the water" stand like any
     zombie for now.

7. **Supplies, before any balancing.**
   - Clips: the shed, bunkhouse, workshop, sawmill, tower top, lower
     station and cellar.
   - Green herbs: the booth, mess, depot, quarry office, mast, creek and
     kennels.
   - Red herbs: the bunkhouse and lodge.
   - Sprays: the foreman's office, lodge and wine store.
   Each pickup lies against a wall, as far from where she comes in as
   that allows, with RE1's own models and room-item flags 180-229.

8. **Her key items take RE1's spare items.** Each of the seventeen takes
   the place of an RE1 item her day never sees. In her mode it has her
   name and description; its icon and models stay the donor's for now.

   | Her item | RE1 item |
   | --- | --- |
   | shed key | Small Key |
   | winch crank | Hex Crank |
   | ranger keys | Dormitory Key A |
   | office key | Dormitory Key B |
   | workshop key | Control Room Key |
   | switch key | Lab Key A |
   | quarry key | Lab Key B |
   | operator key | Special Key |
   | gate key | Armor Key |
   | cellar key | Shield Key |
   | bolt cutters | Broken Shotgun |
   | drive cog | Wind Crest |
   | jerrycan and diesel | the Emblem and the Gold Emblem |
   | dynamite | Flare |
   | fuses | Battery |
   | crowbar | Slides |

   I wrote her names and descriptions; see `items/items.ts`. The jerrycan
   and the diesel moved from the bottles to the two emblems, ids 0x1F and
   0x20: RE1 only lets an item be used at a spot when its
   id is 0x1B or more.

9. **A puzzle that gives an item leaves it to pick up.** RE1's script
   command that gives an item does not put it in her case. So filling the
   jerrycan at the depot takes the empty can and leaves the diesel on the
   spot, to pick up like any item.

10. **The gondola is started in the booth.** The plan puts the cog, the
    fuse and the key on the platform. The scenes put the fuse box and the
    key switch in the operator's booth, so the fuse and the key are used
    there; the cog goes on the gearbox outside. Turning the key opens the
    car's door on the platform.

11. **The flume runs once the mill race does.** Riding the flume has no
    puzzle of its own: the sluice at the pond feeds both, so opening it
    opens the flume to the gorge.

12. **The line gate is electric.** The plan has the line gate need the
    power line, so its lock is electric and opens with the action button
    once the breakers are up.

13. **The winch keeps its crank.** The yard's winch no longer takes the
    crank away, since the pond's sluice needs it.

14. **Texts that now disagree.** The switch house's main isolator is
    described as padlocked down, and nothing opens it. The pond's water
    wheel still says the mill isn't running after the sluice is opened.
    These want a words pass.

15. **Interior cameras moved down.** Six rooms had cameras level with
    their beams or joists: the bunkhouse's east camera, all of the
    cottage's, the lodge's, the mess hall's, the weather station's and the
    garden shed's. Each is 10-20 cm lower, under the beams. The views are
    the same rooms, a touch less ceiling.

16. **The bridge's light.** Its mist and sun were turned down, since they
    washed the gorge flat grey. It is a little darker than before.

17. **The cellar's rack stands across the crawl hole.** The scene had it
    beside the hole, so there was nothing to push. A state cannot move a
    wall, so its footprint stays where it starts, and the crawl door's zone
    reaches 0.7 m further into the room so she can get to the hole once
    it has moved.

18. **Which key items got new icons.** Seven did: the bolt cutters, the
    drive cog, the jerrycan, the diesel, the dynamite, the fuses and the
    crowbar. The nine keys keep their donors' key icons and the winch crank
    keeps the Hex Crank's, since those already look like what they are.

19. **The dead are one man and one woman.** corpses.py builds an MPFB man
    in a work suit and a woman in casual clothes, each in the three poses.
    Every room's body is a copy of one, in the room's own top and trousers
    and mirrored on odd seeds. The maid in the back garden is the woman.
    The skin keeps MakeHuman's texture, drained to a grey-green.
20. **corpses.blend lives on the Blender machine, not in git.** It is
    built from MPFB's CC0 assets by `blender/build-corpses.ts` (about 30
    s), into the rooms' work folder, where `kit.body` reads it. A fresh
    machine runs that once before rendering a room with a body.
21. **The items' exports are not in git either.** `items/render-items.ts`
    writes `items/icons/*.png` and `items/models/*.{json,png}`, as
    `day/render.ts` writes the backgrounds. The build needs them.
22. **The keys keep their donors' models.** Only the seven items with new
    icons have their own models, lying in the room and examined. The keys
    and the crank still look like RE1's.
23. **How an item faces in the examine view.** RE1's viewer looks along
    x. A flat item turns its broad face to her (the cog's face, the
    cutters' jaws). One that stands, like the cans, stays standing.
24. **Joining parts now keeps every part's bevels.** `kit.join` applied
    only the first part's modifiers to the whole and dropped the rest. It
    now makes each part's modifiers real first. A room re-rendered after
    this shows bevels it was meant to have but never had.
25. **What the mine takes, and where.** The plan says the mine takes
    everything. I read that as her weapons, rounds, sprays and herbs, not
    her key items: the cog, the fuses and the fuel are still needed for the
    gondola. It happens the first time she wades into the flooded gallery,
    as part of her thought there, with no cutscene yet (row
    `cut-mine-collapse`). From there she has no gun until Kevin's Beretta
    at the crash: the summit, the gondola, the pylon and the valley path
    are unarmed, Cerberus included. Her knife goes too.

## Waiting on you

- **Saving in her mode.** Her day has no typewriter before the last room,
  and a two-hour game needs some. Placing them is easy: one script line
  each, and a typewriter and box to model in the booth, the mine office
  and the lower station. Saving is the problem. A save made in her mode
  does not say so, and the title's LOAD GAME runs before a character is
  chosen, so loading one would look for her rooms in the shipped game.
  Two ways out:
  1. A mode byte in the save, as the Director's Cut keeps at 0x233. Loading
     a save marked as hers switches to her mode first. One save list, and
     it works from the title. This is the one I'd pick.
  2. Her saves in a folder of their own, loaded from her card on the
     character select. That keeps the two games apart but needs a load
     entry on the select screen.

  I did not build either, since it changes the save format.

- **The crane and the cog.** The plan has the log crane lift a stack off a
  crate in the sawmill, and the spare cog, in the workshop, need both the
  crane and the safe. The sawmill has no crate, and nothing ties the
  workshop's cog to the crane. Two readings:
  1. The cog is in the crate: the crane frees it in the sawmill, and the
     workshop key opens the workshop for something else.
  2. The crane frees the workshop's door, blocked by the logs.
  For now the crane works in the game and the cog lies in the workshop
  behind its key.

- **Footsteps.** Every kit room plays one footstep sound. Matching sounds
  to floors needs the shipped rooms' footstep tables read properly first.

## Done on the morning of 15 October

- **The dead** (row `look-dead`). They were rods and spheres. They are
  MakeHuman bodies now, clothed and posed (assumptions 19-20). `kit.body`
  keeps its arguments: a missing hand or leg is cut off by the bone each
  vertex follows, and the stump is closed in old blood.
- **Her items** (rows `items-icons`, `items-models`). `items/models.py`
  models the seven at real size and renders their icons. It bakes each
  one onto a cut-down copy for the game. `items/tmd.ts` writes RE1's
  formats: the ITEM_M2 .IVM she turns over, and the TMD and TIM lying in
  the room. `tests/items.ts` photographs all three in the game: each item
  in its room, her case, and each one checked.
- **Vehicles** (row `look-vehicles`). `kit.loft` builds smooth bodies from
  cross-sections. Bravo's helicopter, the three pickups (`kit.pickup`),
  the sedan, the log truck's hood and the skidder use it.
- **Weak rooms, second pass** (row `look-weak-2`). The sawmill's head saw
  was a mirror that rendered as a black disc. The den's granite came in
  half-metre triangles. The mast's cliffs either side of the ledge were
  smooth sheets. The platform's gorge was empty sky 88 m down.
- **A slip of mine, now noted.** Two test runs went out without
  `RE1_LAB_GAME_DIR`, so they started the shared install in
  `D:\Games\RE1-decomp`. Its build is from 10 October and draws the
  quarter-size picture you saw. Every run uses `D:\Games\RE1-files` again.

## Done, in order

- **Ragged spruces and rougher ferns** (`blender/reb.py`, row `look-trees`).
  This is the style sample's tree, moved into the kit for every room. Each
  spruce has whorls of drooping branches at uneven heights, a bare lower
  trunk, a thin side, a lean and sometimes a broken top. Its trunk now
  leans with its crown; in the sample they leaned separately. No two ferns
  are alike: fronds of uneven length, some bent or broken, leaflets gone.
- **Lenses kept clear** (`kit.Room._clear_lenses`). The new trees' low
  branches hang at camera height. Needles and fronds within 2.2 m of a
  camera are taken off at export.
- **Bitty surfaces** (`kit.wear`, row `look-wear`):
  - Every worn surface gets a layer of grit: blocky 2.6 cm texels, bright
    and dark, which also roughens the surface so specks catch the light.
    The old speckle was finer than a pixel at 320x240 and averaged away.
  - Foliage cards are speckled and cut into lace, so a tree reads as lit
    tips and dark gaps rather than flat shapes.
- **Readable interiors** (`kit.Room._fill`, row `look-interiors`). Every
  indoor room gets a soft warm point light in the middle of its floor,
  sized by the floor's area. It is hidden from the camera and from
  reflections, and its soft shadows keep the corners dark. Walls read and
  the lamps still make their pools. Measured against RE1's save room
  backgrounds: see assumption 2.
- **The look filter in the build** (`day/look.ts`, row `look-filter-build`).
  `room.ts` runs it on every frame it reads from a render: the
  backgrounds, the animation and state frames, and the walks. The masks
  are cut from the filtered background, so they match. It is `look.py`'s
  tone without the grain (assumption 1): colour toward green shadows and
  amber highlights, a little less saturated, the blacks crushed, the
  corners darker. Strength 0.4, the light pass the samples showed.
  `RE1_LOOK=0` turns it off.
- **The save room's trapdoor** (`saveroom/`, row `look-trapdoor-patch`).
  `hatch.py`, the sample, is now the renderer, with the kit's wear on its
  boards; `saveroom/render.ts` runs it on jellybingus in a render slot.
  `saveroom/patch.ts` lays each camera's render over the player's own
  `RC100<N>.pak`, and `build.ts` writes the six into REB/Stage1. Only
  camera 0 sees that spot. Her arrival moved onto it (assumption 3).
- **Door animations** (`day/scripts.ts`, rows `doors-anim` and
  `doors-ladder`): see assumption 4. The hand-written cabin, shed and yard
  doors are the plank door too. Kit rooms' scripts are regenerated after
  the re-render.
- **Something to examine in every room** (row `words-checks`). The trail
  had nothing: it now has the marker post and a fallen spruce with claw
  marks in its bark. The tracker counted only the scenes' records and
  missed the hand-written rooms' own checks; it now counts each room's
  script. 57 of 57.
- **First thoughts** (row `words-entry`). Two kit rooms had lost theirs
  to the flag shortage (assumption 5); the writer now stops with an
  error if flags ever run out. The trail, the only room without a first
  thought, has one: the station below, and the hope of a radio.
- **Enemies in every room the plan names** (`day/foes.ts`, the Enemies
  rows). The kit rooms' scripts place them from each room's own floor:
  - clear of walls, gaps and doors;
  - the first as far from where she comes in as the room allows, each next
    one as far from her and the others;
  - facing the way she comes in.

  The trail's two crows are in its hand-written script. Assumption 6 has
  the choices. They go into the kit rooms' scripts when those are
  regenerated after the re-render.
- **Supplies** (`day/supplies.ts`, row `items-supplies`): see
  assumption 7. Going into the kit rooms' scripts with the regeneration.
- **Her key items** (`items/`, the find-* rows):
  - Names and descriptions in her mode (`RebItems.cpp`, from
    `items/engine.ts`). See assumption 8.
  - Pickups where the scenes put them. A kit scene says where a key item
    lies with `room.item(step, at)`, beside the prop: the ranger's body, the
    dead cook, the safe, the bench, the desk, the key boards, Hal's cart,
    the helicopter's door. The script writer puts the pickup there, with the
    donor's model and room-item flags 160-179.
  - The hand-written rooms:
    - The shed has the empty jerrycan by its fuel cans and the spare fuses
      on the bench.
    - The truck's toolbox in the yard is locked ("The ranger will have had
      the key on him") until she carries his keys; then the bolt cutters
      are in it.
    - Room-item flags 244-246.
- **Records without rendering** (`render.ts --records`, `RE1_RECORDS`): a
  scene's room.json alone, for a change to what it records rather than how
  it looks.
- **Locked doors** (the puzzle rows that are a lock):
  - Ten ways the plan gates behind a key item are locked on the side she
    comes from: the office, the depot's padlock, the workshop, the road
    gate's chain, the tower, the switch house, the quarry office, the
    lodge, the estate gate and the cellar doors. RE1's own door lock does
    the work: she uses the item and the door stays open by its lock flag
    (40-59).
  - In her mode such a lock says "It's locked.", not RE1's carvings and
    plates.
- **Worked puzzles** (`day/events.ts`, the puzzle rows that are not a
  lock). Fourteen events: the diesel, the generator, the breakers, the
  line gate, the blast, the pump, the lift, the sluice, the crane, the
  cog, the fuse, the key, and the rack. A scene says where each is worked
  with `room.spot(step, zone)`; the script writer puts the item-use or
  action zone there, the "not yet" line until what it needs has happened,
  and the way it opens behind a message until then. Common flags 130-158,
  give flags 247 on. Assumptions 9-14.
  - **Not yet:** the ride and the pylon, the hatch, and the crane lifting
    the logs off the crate (the cog is not yet gated on it).
- **The weak rooms** (row `look-weak`):
  - The quarry's benches break along joints. Slabs stand out of every face
    with water stains down them, and the cut blocks carry drill half-holes.
  - The far ridges have crags, gullies and a speckle of single trees that
    fades with the haze. The valley floor below them has the same speckle.
  - The kit's gravel was finer than a pixel and averaged flat. It is
    coarser now, and the lower yard has loose stones on it.
  - The mine mouth's rockfall is angular broken stone. The gap it is
    about now shows as a dark hole under its web.
  - The washout's gully slumps in and out instead of being cut square,
    and the logger lies where the lip camera can see him.
  - The switch house reads well with the fill and the wear, so it is
    unchanged.
  - Not on the list but as weak: the bridge's gorge walls were smooth
    planes. They are rock with slabs and cracks now, with the kit's wear.
- **Ceilings** (`kit.Room._fill`). Interior ceilings rendered as a black
  band across the top of the frame. A weak light just under each ceiling,
  facing up, stands in for the floor's bounce. See assumption 15 for the
  cameras that sat level with beams.
- **The early scenes get the wear.** The ridge, the trail, the yard, the
  lookout, the shed and the bridge predate the kit and never had its worn
  surfaces. They do now.
- **Rooms that show a puzzle done** (the "Things that change the room"
  rows). `kit.Room.state(step, pose)` renders a second background for how
  a room looks once a puzzle step has happened, shown while its flag is
  set:
  - the mine mouth's rockfall blown out into low rubble, the adit black;
  - the cellar's rack slid north off the crawl hole;
  - the generator hut's bulkhead lamp lit;
  - the switch house's breakers up, a green lamp over each;
  - the junction's water down the flooded way.

  These are pictures only: no animation plays as they change.
  **Not yet:** the sawmill has no crate under a log stack for the crane to
  lift, so the crane and the cog it frees need the scene built first.
- **Her key items' icons** (row `items-icons`). `items/icons.py` models
  the seven items and renders them in Blender on jellybingus, lit and
  turned like RE1's icons (`items/render-icons.ts`). The build lays them
  over the navy ground of the player's own `ITEM_ALL.PIX`, matches them to
  its palette and writes her overlay's sheet (`items/sheet.ts`). The game
  reloads the sheet when the character select switches into or out of her
  mode, since it loaded the shipped one at boot. See assumption 18.
- **The puzzles in the game** (`tools/harness/tests/puzzles.ts`). The test
  works each puzzle the way a player does, through the status screen or the
  action button: first with what it needs undone (nothing happens and she
  keeps the item), then done (its flag set, the item gone, the way it opens
  walked through, what it leaves picked up). All thirteen pass: the
  diesel, the generator, the breakers, the line gate, the blast, the pump,
  the lift, the sluice, the crane, the cog, the fuse, the key and the rack.
  Testing found three bugs, all fixed:
  - The engine clears room flags 32-63 every frame, so a puzzle's "item
    used, line to come" flag vanished. Puzzles use flags 12 and up now.
  - The engine takes some items out of her case as she uses them (the
    crank, the jerrycan, the fuses). The script's own remove then found
    nothing and stopped the script. It removes only what is still there,
    and an item can be used only once what its puzzle needs is done, so a
    use that cannot work never loses it.
  - The action button takes the first zone in the room's table, so a
    puzzle's examine line beat the item it leaves. The item takes the
    line's slot until it is picked up.
- **Two scenes moved for the puzzles.** The junction's pump switch was
  walled off behind the pump and its pipes: she works the pump from its
  west face. The cellar's crawl door was a 0.6 m pocket between the rack
  and the barrels: the first two barrels moved east.
- **The look page**: every room's cameras as the game shows them, at
  https://home.arpa/research/rebecca-look/ (`day/look-page.ts`).
- **Every door in the game** (`tools/harness/tests/tour.ts`). All 102 doors
  of the re-rendered rooms take her where they should, with every puzzle
  done and every lock open. The five that first failed were the test's
  fault: it faced a door's middle while standing nearly on it, and it gave
  the mine lift less time to start than the lift takes.

