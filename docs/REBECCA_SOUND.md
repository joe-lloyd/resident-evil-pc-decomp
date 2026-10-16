# Rebecca's sound

How her day sounds: her footsteps on each kind of floor, the loops under her
music, and her doors, gates and hatches. Her mode plays all of it. Chris's
game keeps RE1's own. `tools/harness/tests/sound.ts` proves each part in the
game.

Two sources make every sound in this document:

- RE1's own WAVs, from the player's files under `sound\`. The overlay names
  them and never ships them.
- Our own WAVs, made by code at build time (`tools/rebecca/footsteps.ts`,
  `tools/rebecca/sound/ambience.ts`). The overlay ships these as
  `REB/sound/Reb_*.wav`.

## Footsteps

### How RE1 picks a step

A step plays entity sound slot `k` for a walk, `k + 1` for a run and `k + 2`
for a fall. `k` is the low byte of the footstep zone she stands in
(`PlayEntitySnd` and `LookupFootstepZone` in `src/game/SoundSystem.cpp`). A
room's footstep zones are rectangles in its RDT, scanned in order, and the
first that holds her wins. The scan has no terminator, so the last zone must
cover the whole room.

The room's row in `g_RoomSoundNameTable` names the WAV in each of its 48
slots. `Room_LoadEnemySoundBanks` loads them on entry. Her rooms sit in free
slots, and their rows are empty or run on into the next stage's first rooms.

### What her rooms do

1. Each scene says what is underfoot. `room.ground(kind)` names the room's
   floor, and `room.floor(rect, kind)` names a part that differs, such as the
   bridge's planks over the gorge or the creek's ford. Both are in
   `tools/rebecca/blender/kit.py`. `render.ts --records` writes them to
   `renders/room.json`.
2. `tools/rebecca/day/room.ts` (`footstepZones`) writes one zone for each part
   and a catch-all zone for the ground.
3. `tools/rebecca/sound/ground.ts` gives each kind in a room a footstep set.
   The room's own ground takes slot 0x2d. Other kinds take 0x2a, 0x27 and
   0x24, so a room can have four kinds at most.
4. The build writes `REB/sound/rooms.dat`, which names each of her rooms'
   slots. In her mode, `src/game/RebSound.cpp` lays those names over the row's
   after RE1's row loads. Slots she doesn't name keep the row's.

| Kind | Walk, run, fall | From | Rooms |
| --- | --- | --- | --- |
| earth | `Reb_ftEarthA`, `Reb_ftEarthB`, `taore_ca` | ours | 26, the outdoor default |
| gravel | `Reb_ftGravA`, `Reb_ftGravB`, `taore_ca` | ours | 9, the road and yards |
| boards | `ft_wdA`, `ft_wdB`, `taore_wd` | the mansion's wooden floors | 18 |
| rock | `ft_caveA`, `ft_caveB`, `taore_ca` | the caves | 6, the mine and quarry |
| water | `ft_swimA`, `ft_swimB`, `taore_wa` | the flooded rooms | 3: the gallery, the ford, the washout |
| concrete | `ft_concA`, `ft_concB`, `taore_st` | the guardhouse basement and the lab | 9 |
| metal | `ft_plaA`, `ft_plaB`, `taore_pl` | the lab's steel plates | 3: the lift, the pylon, the switch house |
| lino | `ft_linA`, `ft_linB`, `taore_st` | the mansion's back corridors | 4 |
| carpet | `ft_cpA`, `ft_cpB`, `taore_cp` | the mansion's carpets | 4 |

RE1 has no steps for earth or gravel, so `footsteps.ts` makes them from
noise. Each step is a soft heel thump under a burst of crackle. The same code
makes `St_path01` and `St_path02` for the walks between outdoor rooms.

To change a floor, edit its scene, run `render.ts --records <slug>`, and
rebuild.

## Ambience

### How it plays

RE1's music table gives each room a group of up to three WAV channels. The
room's state byte turns them on: bit 3 is channel 0, bit 4 channel 1, and
bit 5 channel 2. Her mode reads its own table from `REB/sound/music.dat`
(`src/game/RebMusic.cpp`, [REBECCA_MUSIC.md](REBECCA_MUSIC.md)). Each group
plays her music on channel 0 and leaves channels 1 and 2 free.

The ambience uses those two free channels, so the engine needs no change.

- `tools/rebecca/sound/places.ts` gives each place in the plan one loop or
  none. `plan.test.ts` fails when a place has no decision.
- `tools/rebecca/music/table.ts` puts a cue's loops on channels 1 and 2, in
  the order its places first play them. A cue with more than two loops fails
  the build.
- Each room's state turns on its cue's music and its own loop, and no other.
  The station's yard plays the music and the wind. Its woods play the same
  music and the forest. Because both rooms share a group, the music keeps
  playing across the door and only the loop changes.
- A cue with no music yet plays its loops alone.

Indoor rooms and save rooms play no loop, since the walls keep the weather
out. RE1's save rooms play only their music.

### The loops

`sound/ambience.ts` makes eight loops from noise and a few synthesised
calls: `wind`, `gale`, `forest`, `mill`, `mine`, `dusk`, `night` and `cellar`.
Each loop is 24 seconds, 22050 Hz mono. Its bed is rendered a little long and
its tail is crossfaded into its head, so the join has no seam. Short events,
such as a bird or a drip, are laid around the loop, so one that runs past the
end comes back in at the start. A fixed seed makes every build the same.

Each loop measures -36 dB RMS. RE1's insect loop, `Se_03`, measures -37 dB.
The station's music measures -26 dB, so the loops sit about 10 dB under it.
The game plays every channel at the same volume, so the files' own levels
keep the loops under the music.

## Doors, gates and hatches

A door record's sound byte picks a room sound set: two WAVs, the door's open
and shut (`g_roomSoundEffectsTable` in `SoundSystem.cpp`).
`tools/rebecca/day/scripts.ts` (`ANIMS`) pairs each of RE1's door animations
with the sound byte RE1's own rooms give it.

| Way | Sound set | Plays |
| --- | --- | --- |
| Plank and panel doors | 0 | `Dr_wd01`, `Dr_wd02` |
| Iron and steel doors | 1 | `Dr_mtl01`, `Dr_mtl02` |
| Ladders and the crawl's hatch | 11 | `Ladder01` |
| The lifts | 14 | `Ev_ftn01`, `Ev_ftn02`, as RE1's lift animation does |
| Walks between outdoor rooms | 15 | `St_path01`, `St_path02`, her steps |
| Walks through a gate | 16 | the path's steps, with `Dr_gat01` and `Dr_gat02` |

Every door record in her rooms names a sound set, and none is silent.

Four walks go through a gate: the road's, the line's, the estate wall's and
the depot's (`GATES` in `scripts.ts`). `src/game/PathWalk.cpp` plays
`Dr_gat01` as the walk starts. The steps wait 30 frames for the gate to
swing, and the gate shuts with `Dr_gat02` after two steps. Pressing action or
run after the walk's first ten pictures skips the rest, as at a door. A walk
skipped before the gate shut plays the shut as she comes out.

The pad word holds a key only on the frame it goes down. The walk checks it
every frame, as `DoorSystem` does, so it catches every press.

## How the test knows

The harness can't hear, so test mode reports what the game loaded and played.
The `snd` object comes from `src/game/TestMode.cpp` and is parsed as `Sound`
in `tools/harness/state.ts`. It holds these fields:

- `set` and `walk`: the footstep set under her and the walking WAV that set
  loaded.
- `steps` and `step`: the footsteps played since launch, and the last one.
- `door` and `room`: the room sound set last loaded, and its two WAVs.
- `sfx`, `last` and `recent`: the room sounds played since launch, the last
  one, and the last eight. A walk can play several sounds between two looks.

The music's channels are in `bgm`, as before.

Run the test against a REB build:

```sh
OVERLAY=<REB build> PORT=7811 RE1_LAB_GAME_DIR='D:\Games\RE1-files' node tools/harness/tests/sound.ts [out dir]
```

It checks these things:

- She walks on gravel, runs on it, and walks on the road's verge. She walks
  the bunkhouse's boards, the bridge's planks, the mine office's rock, the
  flooded gallery, the creek's ford, the workshop's concrete, the lift's
  metal, the booth's lino and the gondola car's carpet. The step that plays
  must be that floor's.
- Eight rooms play exactly the loops the music table gives them, on the
  channels it gives them, and no louder than the music. The shed and the
  booth play none.
- A wooden door and an iron door play their open and shut. The estate wall's
  gate opens and shuts. The road's gate shuts when its walk is skipped. The
  tower's ladder and the crawl's hatch play the ladder.
- Chris's game plays RE1's own steps and none of her loops.

It saves a picture of each walk and each door as `sound-*.png` in the out
directory, `/tmp/rebecca-sound-game` by default.
