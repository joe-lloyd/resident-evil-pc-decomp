# Building the puzzle climb into the game

The puzzle climb of 2026-11-06 changed the plan (`tools/rebecca/plan/day.ts`,
branch `reb-puzzle-climb`), not the rooms. This is the list of what the built
rooms need so that they play as the plan now says. The climb's account is
`~/reb-puzzle-lab/summary.md` on old-mac.

The owner's rulings:
- Tools are reused. The generator already keeps a tool until every lock it
  opens is open (`scripts.ts`, tool locks); second ways must count too.
- A wrong breaker shocks her for a little damage.
- The drive cog is an item she carries. The flume ride with it is optional.
- Keep the look: the oppressive forest, the overcast sky and the backdrop
  ranges (`day/SCENES.md`, "The look"). New things are built with `kit.py`
  the way the room around them is.

## What the engine and the generator need

1. **Enemies that come and go with a step.** `foes.ts` places a fixed set
   per room. A plan step's `stirs` adds enemies once it is done (the mill,
   the generator, the pump, the bell, the cutters, the coal chute), and the
   kennels' pack leaves once penned. Each foe entry gets an optional
   `after` and `until` step, and `foeLines` wraps it in the flag test.
2. **A second way through a lock or an event.** A tool lock with two
   items (the workshop: its key or the bolt cutters), and an event with
   two uses at one spot (the rockfall: the dynamite or the winch crank).
   Both set the same flag. The tool keeps counting toward "every lock it
   opens is open" whichever way is taken.
3. **The breakers, in order, with a shock.** Five breaker spots in the
   switch house; FG_ROOM bits track the order; a wrong one resets the bank
   and hurts her. The engine has no script command that deals damage:
   add one as a port addition (a `player_prop_set` subcommand, REB mode),
   written with `scd_bytes`, and teach retro-archive-explorer's
   disassembler its length (`scd1.ts` `sizeAt`).
4. **The kennels.** Using the dog meat at the sound run pens the pack:
   their enemies leave (1) and a flag is set. The hoist down to the cellar
   needs the cellar key, and the pack penned or every one of its kill
   flags set.
5. **Items.** The dog meat is a new key item (icon and model). The line
   fuse moves from the shed to the switch house. The generator leaves the
   empty jerrycan for the pump. The safe also holds handgun rounds; the
   wine store a green herb.
6. **The safe.** The engine has no combination dial. Until it does, the
   safe opens once she has read the ringed calendar and the letters, and
   her line says she works out the date.
7. **The playthrough** (`tools/harness/tests/playthrough.ts`): its jobs
   follow the new steps.

## The rooms

Full renders, by room, with what the scene must record for the generator.
"Records" means `render.ts --records`: the room.json alone, no pictures.

| Room | Cameras | Change | Records for the generator |
| --- | --- | --- | --- |
| bunkhouse | 4 | Paydays ringed, the 17th twice; no numbers written at the bottom | the calendar's check |
| office | records | Letters: Umbrella's money came on the payday the men were paid twice; he set the safe to it | checks; rounds in the safe |
| camp-yard | 8 | A rusted padlock on the workshop door; the bell rope reachable | spot `ring-bell` |
| workshop | 3 | A belt from the line shaft's wall pulley to the hoist, slack until the mill runs | spot `crane`; state `crane` |
| sawmill | 8 | The millwright's chalk drawing: pond, sluice, wheel, shaft, workshop hoist | crane spot and state removed |
| depot | 3 | The back: a chained skid road out through the fence | spot `skid-road`; door `tower-foot` |
| tower-foot | 3 | The foot of the skid road | door `depot` |
| switch | 2 | Five breakers numbered 1 to 5 by pylon; a box of line fuses | spots `breaker-1` to `breaker-5`; item `fuses` |
| tower-top | 4 | The lineman's wiring sketch; the key on its hook by the door | check; item `switch-key` at the hook |
| shed | records | No gondola fuses; the chainsaw fuses are too small | check |
| yard | 4 | The rifle gone, an empty rack; his name on the toolbox | checks |
| junction | 5 | A float on the pump's intake, broken; a power lamp; Hal on his ore cart across the water | spot `drain` uses the jerrycan |
| gallery | 4 | Boards across the old adit at the east end | spot `adit`; door `east-path` |
| east-path | 4 | A boarded adit mouth in the bank | door `gallery` |
| mine-entrance | 6 | The quarry crane's cable hanging by the jammed timbers | spot `blast`, two uses |
| kennels | 5 | One run with a sound gate and bolt; the meat hoist | spots `pen-pack`, `hoist`; door `cellar` |
| garden-shed | 2 | A sack of dog meat by the door | item `dog-meat` |
| back-garden | 6 | The cellar doors barred from inside; a coal chute grate | the chute's lock; door `cellar` |
| cellar | 4 | The hoist's cage; the coal chute's foot | doors `kennels`, `back-garden` |
| wine | records | A green herb in a pot | item |

About 75 cameras in 17 rooms, and a few more at the new exits.

## Order

1. The generator and engine features (1 to 4), with their tests.
2. The rooms, a spoke at a time, each with its preview sheet looked at
   before the full render: the camp, the west, the mine, the estate.
3. The items (5) and the safe (6).
4. The playthrough (7), then a full run of the day.

## Where it stands (2026-11-06, evening)

Done on `reb-puzzle-climb`: the generator and engine features (1 to 4),
the items (5), the safe's gate on the calendar (6), the playthrough's jobs
(7), and all 17 rooms, rebuilt by four scene agents and checked against
their contact sheets (`~/reb-puzzle-lab/sheets/` on old-mac). Every room
script of the day assembles; the overlay builds.

Decided on the way:
- The workshop's old hoist hangs north of the crate, so the scene has a
  spur rail with its own electric hoist over the logs.
- The ranger's rifle stays in the grass: its line says the magazine is
  empty, which tells the story.
- The cog is an item in her case; the flume ride with it is optional.
- New cameras: kennels 6 (the hoist), gallery 5 (the adit), depot 4 (the
  skid road gate).

Open, for the owner's eye or a later pass:
- **Tower top:** the switch house key is small. Camera 0 shows its board
  by the door as a dark panel through the glass; the key itself is a
  pixel. The paint is gone (2026-11-07), so only the pickup is the key.
- **Kennels:** the hoist is small and dark at night; the cellar's cold
  light is subtle.
- **Safe:** no combination dial; it opens once she has the calendar.
- **Coverage:** camp yard loses 6.1% of its floor to the cameras, over the
  5% rule, as it did before this work.
- **Saves:** item and lock flags moved; old saves and playthrough
  snapshots from before this branch do not carry over.
- **retro-archive-explorer #8** (the compiler's length for subcommand 11)
  must be merged before a fresh clone of it can build this branch.

## The other ways, played (2026-11-07)

`playthrough.ts --way <name> --from <checkpoint>` plays one other way from a
checkpoint of the full run (`~/reb-puzzle-lab/snaps/`) and checks what it
must do. `tools/harness/try.ts <checkpoint>` loads one for a person to play.

| Way | Checkpoint | Checks |
| --- | --- | --- |
| shock | after-empty-can | a wrong breaker takes 12 health (88 to 76); the right order none |
| bell | after-cutters | loggers in the mess hall; none in the camp yard after the cut |
| cutters | after-cutters | two loggers in the camp yard after the cut; the cutters keep two uses |
| crank | after-diary | the crank's mark; the crank spent; a dog at the mine entrance after |
| skid | after-cut-depot | down to the tower foot and back, the road gate still chained |
| adit | after-drain | out of the gallery to the east path |
| meat | after-open-gate | the pack loose, then penned; the hoist; the meat, key and crowbar spent |
| chute | after-open-gate | down the coal chute; the crowbar spent |

Found and fixed on the way:
- Taking live enemies away (the pen, the bell) cleared their status but
  not `g_enemy_count`, so the next shot read unfilled slots and crashed in
  `weapon_hit_detect_gun`. In REB mode the count now follows status bit 0
  (`cmd_enemy_prop_set`).
- The hoist armed only at room load: penned in the room, it stayed shut.
- A tool done the other way stayed in her case; the bell did not silence
  the cutters; the crank way brought no dog.

All eight pass on one build (exe and overlay of 2026-11-07), and so do
the day's four quarters, run side by side, each from the previous run's
quarter end. The logs are in `~/reb-puzzle-lab/log/ways-2026-11-07/`.

The crank's dog comes the next time the mine entrance loads, like every
other enemy a step brings: the engine loads enemy models with the room, so
a dog arriving mid-wind is untried.

## Two rooms repainted (2026-11-07)

- **Gallery:** the background painted Hal floating dead by the rope, while
  cut-hal puts him on the ore cart as an actor, alive until he gives her
  the key. The room showed two Hals. The painted body, its check and its
  footprint are gone.
- **Tower top:** the key and its tag were painted on the nail. The scene
  now paints the nail alone, as the other key boards do. No camera's
  render changed: the key was too small to see, so this only keeps the
  scene honest.

Both rooms were rendered again and their renders pushed to the asset
store. In game, after cut-hal the gallery shows the one Hal, dead by the
cart. The adit way passes on the new build, through the gallery without
Hal's footprint (log: `~/reb-puzzle-lab/log/round3/`).

## Enemy cries and the webs (2026-11-07, evening)

- **Cries:** an enemy plays the room's sound slots `block * 10 + n`
  (Snd_em), from RE1's row for its room id. Her rooms set only their
  footsteps, so each enemy took its free room id's row: the junction's
  spinners cried as hunters, the back garden's dogs as zombies, and most
  rooms' enemies made no sound. `day/foes.ts` now gives each kind RE1's own
  cries and each kind in a room its own block (cmd_enemy_set's last
  byte), and `rooms.dat` fills them. Checked in game with
  `~/reb-puzzle-lab/scripts/probe-cries.ts`, which reads the cries the
  test-mode state now reports (`sound.cries`): before, the junction's
  spinners played `HU_walkB` and `HU_jump`; after, `kuasi_B` and `kuasi_C`.
  The washout's adders play `PY_` and its dog `cer_`; the mess hall's
  zombies `z_`.
- **Webs:** the junction and the gallery had bright straight strands. The
  kit's new silk (`kit.web_blanket`, `web_fillet`, `web_drape`,
  `web_corner`) mats the walls and roof and hangs sheets and festoons,
  after the Black Tiger's lair in the REmake. A silk sheet in a corner
  that holds a camera covers its lens, so the junction fills only its
  north-east corner.
- **Harness:** a fight stepped her back from any close enemy before each
  shot, so a spinner following her in the tunnel kept her backing off
  without firing. Now three steps back, then a shot.

On the new build quarters 1, 2 and 4 pass. Quarter 3 passed in all five
runs after the harness fix. One of the three full runs lost about thirty
minutes in the tunnel first: a walk to its doors failed three times at
about ten minutes a try, then got through. The two traced runs did not
stall, so the cause is not found.

## Every room sound slot (2026-11-07, night)

RE1 plays 48 sound slots per room, loaded by room id. Her rooms sit in
free ids, so each slot she did not set played whatever that id's row
held. Audited against every engine path that plays a slot:

| Slots | Played by | Hers now |
| --- | --- | --- |
| 0-19 | enemies, block * 10 + n (Snd_em) | each kind's RE1 cries, read from the room's enemy() lines |
| 20, 34 | a locked door's rattle, its key turning (door_try_enter) | D_gacha / key_door for wood, DM_gacha / key_mtr for metal |
| 29-31 | the typewriter's save screen | cancel, type01, type02 |
| 32, 33 | the item box opening, its list scrolling | item02, item01 |
| 36-47 | her steps on each floor and her fall (ground.ts) | as before |
| the rest | Plant 42, pushed objects, desks, drawers, in-room ladders | empty: none are in her rooms |

`sound/script.ts` reads the room's script; the build fills all 48 slots
of all 57 of her rooms and leaves the rest empty. Before: the estate
wall's gate key turned to an elevator (Elv2), the save rooms typed and
opened their boxes in silence, locked doors rattled silently, and the
trail's crows, the yard's dog and the bridge's adders had no cries.
Checked in game (`~/reb-puzzle-lab/scripts/probe-slots.ts`, reading the
state's `sound.slots`): the gate rattles DM_gacha without its key and
turns key_mtr with it; the booth's box opens with item02. The box's
scroll click (item01) was not triggered by the probe.

A ladder door's animation plays no slot (tried at the tower: only her
steps), so slot 35 stays empty. The kennels' meat hoist is now RE1's lift
both ways and the gallery's adit a dark walk; both had fallen back to the
mansion's panelled door and its creak.

Open: her puzzle events (the bell, the breakers and their shock, the
blast, the generator, the crank, the pump, the push) play no sound. RE1
has candidates for some (power-on, Sw_lever, kickdoor, crank, watergt,
mv_cp) and none for a bell.

## The camp's dead (2026-11-08)

The logging camp's zombies are loggers: RE1's three zombie bodies, their
skeletons, meshes and animations kept, with skins painted in
`tools/rebecca/npc/zombies.ts` (brushes shared with the people, now in
`npc/brush.ts`).

| Logger | Id | Body | Look |
| --- | --- | --- | --- |
| faller | 0 | em1100 | red and black flannel open on a bitten chest, jeans, red braces, knit cap, beard |
| bucker | 1 | em1101 | sweat-yellowed undershirt, bare arms, orange chainsaw chaps, orange ear defenders |
| rigger | 17 | em1111 | tan waxed-canvas coat, hi-vis band, hickory shirt, stagged trousers, yellow hard hat |

- Her game loads enemies from the Jill half of `g_emdPathTable`, so the
  zombies are em11xx: em10xx's mesh and texture with Jill's animations.
- In REB mode `LoadEntityEMD` looks in `enemy/stage<N>/` first; the build
  ships the loggers to stage 2 and 3 only, so the mansion's zombies (the
  back garden, the cellar) and the gallery's stay RE1's. With
  `RE1_DEBUGLOG=1` the game logs each lookup as `[emd]`.
- The first body's sheet shares texels between the head and its left
  forearm and right shin, with no room to part them, so those are bare
  dead skin, as RE1 paints them.
- The camp's rooms mix the three (day/foes.ts); kinds that cry alike share
  a sound block. The harness counts any of ids 0, 1 and 17 as a zombie.

Checked in game in the mess hall, the bunkhouse and the camp yard
(`~/reb-puzzle-lab/scripts/probe-loggers.ts`). Quarters 1 and 2 and the
bell and cutters ways pass on the build.
