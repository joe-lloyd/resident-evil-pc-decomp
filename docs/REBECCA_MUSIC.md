# Rebecca's music

Research and plan, 2026-10-15. Her day needs music in the manner of RE1's:
our own pieces, written as code because nobody on the project plays an
instrument, rendered to WAV the same way every time, and played by her mode
only. Which piece plays where is data in `tools/rebecca/plan/music.ts`,
checked by `plan.test.ts` so every room and cutscene has its music decided.
The owner's page is <https://home.arpa/research/rebecca-music/>.

## What RE1's music is

- **Who and how.** The credits disagree on who wrote it; Makoto Tomozawa,
  Koichi Hiroki, Akari Kaida and Masami Ueda all appear. The
  [Project Umbrella interview](https://www.projectumbrella.net/bio-hazard-sound-team-interview-project-umbrella.html)
  says it was sequenced in MIDI and converted to PlayStation sequence data,
  playing over a small sample bank: music had 256 KB of the PS1's 512 KB of
  sound memory. Mikami asked for "realistic sound like a movie".
- **What it sounds like.** Short looped samples at low rates, dull smeared
  reverb, and ADPCM grit. The SPU's reverb runs at about 22 kHz
  ([psx-spx](https://psx-spx.consoledev.net/soundprocessingunitspu/)). A plain
  low output rate doesn't produce that sound.
- **Where silence goes.** Many rooms have no music at all, only their own
  sound. Reviewers at the time praised "the chilling music and eerie silences".
- **The save room.** Two or three minor chords held under a short looping
  melody: arpeggios on a synthesised guitar and a pitch-sliding lead
  ([Laced](https://www.lacedrecords.com/blogs/blog/vgm-subgenres-the-anxious-calm-of-resident-evil-save-room-music)).
  Every save room in her day plays it, from the player's own game files:
  it is the sound of being safe, and nothing new would mean as much.

## How the PC game plays music

- **Files.** Each track is a plain WAV, `sound/<name>.wav`
  (`src/game/SoundSystem.cpp:734`), 8- or 16-bit at any rate and channel
  count (`src/system/AudioFile.cpp:47-93`). The originals are 22050 Hz mono
  (`docs/PSX_ENGINE_ANALYSIS.md:431`). An `.ogg` beside a `.wav` is preferred
  (`AudioFile.cpp:162-177`).
- **A room's music** comes from a table, not the room file:
  `g_BgmRoomData[stage][room][state]` gives a group, and a group is up to
  three WAV channels (`SoundSystem.cpp:636-643`, `src/game/SoundTables.h:13-15`).
  The room's state byte is in the save (`g_roomBgmState`), and scripts set it
  with opcode 0x37 (`src/game/CmdFunctions.cpp:1955-1967`).
- **Across doors.** A room in the same group keeps the music going and only
  switches the channels whose bits changed. A new group fades out and loads
  (`SoundSystem.cpp:836-866`). State 0xFF is silence.
- **Loops.** The original loops the whole file. This port also plays an intro
  once and loops the rest: write a `smpl` chunk with the loop and a `re1p`
  chunk to mark the file (`AudioFile.cpp:19-23`, `68-91`). New tracks should
  use this.
- **Her mode.** The overlay is checked first for every file
  (`src/system/AssetPath.cpp:364-376`), so a new WAV in `REB/sound/` works
  with no engine change. The table was compiled in and shared by every mode,
  so her mode now reads its own (below).

## How we make it

- **Write in Strudel.** [Strudel](https://strudel.cc) is a pattern language
  in the browser. A sketch is a short text file, so it lives in the
  repository and diffs like code. A link with the code in its hash opens it
  ready to play, and the owner can change a number and hear the result at
  once. Its licence is the AGPL, which covers Strudel's own code; its FAQ
  says the music made with it belongs to whoever made it.
- **Use only sounds we may ship.** These are
  [VCSL](https://github.com/sgossner/VCSL), which is CC0 and has two pianos,
  a harp, bowed vibraphone and psaltery, wineglass, organs, timpani and an
  anvil, and Strudel's own synths. Each sketch loads VCSL from a pinned
  commit.
  - Don't use Strudel's default `piano`. It is the Salamander piano, CC-BY,
    so it needs a credit line.
  - Don't use `gm_*` sounds, Dirt-Samples or the drum machines. Their
    licences are mixed or not stated.
- **No AI generators for shipped music.** None renders the same track from a
  committed file, and none gives clean rights:
  - Suno's terms restrict commercial use;
  - Udio stopped downloads in October 2025;
  - MusicGen's weights are non-commercial.
- **The checker.** `tools/rebecca/music/check.ts` evaluates each sketch with
  Strudel's own engine in Node, with no browser. It fails a sketch that
  doesn't parse, plays nothing, or uses a sound outside the list above.
- **Rendering.** `tools/rebecca/music/render.ts` turns a sketch into the
  WAV the game plays, the same bytes every time. See "The render step" below.

## Her music table

Her mode reads its own table, so Chris's and Jill's games keep RE1's
compiled one (`g_BgmNameTable`, `g_BgmRoomData`, `SoundTables.cpp`).

- **The data.** `tools/rebecca/music/table.ts` works the table out from the
  cues in `plan/music.ts`. Each cue is one group, as in RE1, so rooms with
  the same cue keep the music going through the door. A cue plays:
  - for `reuse`, RE1's own file under `sound/`, from the player's game;
  - for `new`, its render, shipped as `sound/Reb_<cue>.wav`;
  - nothing for `ambience`, or for a `new` cue with no render yet.
- **The build.** `tools/rebecca/build.ts` writes the table into her overlay
  as `REB/sound/music.dat` and copies the renders beside it. It also sets
  each of her rooms' music state in her `BIO_CARD.DAT` (offset 0x33C, one
  byte per room): 0x08 plays the room's group on channel 0, 0xFF is silence.
  RE1's own audio never goes into the overlay: the save rooms' `Bgm_31` is
  only a name in the table.
- **The engine.** `src/game/RebMusic.cpp` loads `music.dat` and lays her
  rows over RE1's. Her groups are numbered after RE1's 57, so
  `bgm_load_and_start` takes their files from her table. A room she doesn't
  list keeps RE1's row. The mansion's save room is one: its own script sets
  the state that picks `Bgm_31` from RE1's row. Without the file, her mode
  plays RE1's table, as before.
- **Every room of hers has a row.** Some of her slots have music in RE1's
  table. Before her table, three of her rooms played RE1's tracks by
  accident: the summit trail and the weather station played `Bgm_09`, and
  the mine lift played `Bgm_1e`. Now each is silent until its cue has audio.
- **A stage change.** `init_room` marks the music off without stopping it,
  so a silent room across a stage line kept the last room's track: the save
  room's `Bgm_31` went on into the mine lift. In her mode a silent room now
  fades out whatever is still loaded. RE1's own games keep their behaviour.
- **Proven in the game** by `tools/harness/tests/music.ts`. Test mode
  reports each BGM channel's file, whether it plays and its volume
  (`docs/TEST_MODE.md`). In her mode the test jumps through rooms with the
  debug room change, which goes through the same door transition as a door:
  - the yard, the shed and the footbridge play `Reb_station`, and the shed
    keeps it going through the door;
  - the five save rooms of her day and the mansion's play `Bgm_31`;
  - the hollow, the mine lift and the summit trail are silent;
  - the yard still plays 100 s on, past the end of its 96 s file.

  In Chris's game, RE1's save room plays `Bgm_13` while he meets Rebecca,
  then `Bgm_31` when he comes back. Every channel plays at full volume (-1).
  The first run caught a test mode fault: the game paused its sound whenever
  another game on the test machine took the focus. Test mode now keeps its
  sound playing.

## The render step

    node tools/rebecca/music/render.ts <@strudel/web 1.2.5 dist> [sketch...]

It writes `tools/rebecca/music/renders/<sketch>.wav`, by default for every
sketch a cue names. The renders are not in git; the build ships what is
there. Run it again and the bytes are the same: the script prints each
file's sha256. The two renders so far are on the LAN to listen to:
<https://home.arpa/research/rebecca-music/renders/yard.wav> and
<https://home.arpa/research/rebecca-music/renders/chase.wav>.

- **Strudel itself plays it.** The script runs Strudel's own browser build,
  the one the owner's page plays, in a headless Chrome. That is the
  `chrome-headless-shell` Playwright already put on the old Mac, or `CHROME`.
  It drives Chrome over the DevTools protocol with Node's own WebSocket. There
  are no new dependencies, and nobody has to be at a browser. Our own
  renderer would have needed every Strudel effect written again, and it
  would never sound quite like the page the owner listens on.
- **Why it's the same every time:**
  - The audio context is an `OfflineAudioContext`, so nothing depends on the
    clock.
  - `Math.random` is seeded, in the page and in the audio worklets, so the
    noise and the reverb's impulse don't change.
  - The notes are queried and played in order, one by one, so the graph is
    built the same way each time.
  - Chrome mixes a node's inputs in an order that changes from run to run,
    and float sums of three or more depend on the order. Every input to a
    node that mixes goes through a small worklet that rounds it to steps of
    2^-20, about -120 dB, and sums of those are exact in any order.
  - Nothing changes the graph while it renders. Strudel's clean-up when a
    voice ends is turned off, and every node is kept from the garbage
    collector. Both used to land at a different moment each run.
  - Every sample comes through the script. It pins VCSL to commit
    `c1ea7bcc` (the sample map points at VCSL's `master`) and keeps a copy
    in `~/.cache/rebecca-music`, or in `RE1_MUSIC_CACHE`.
  - Before these, two renders of the yard differed by one float step in
    about 50,000 samples, and the ADPCM pass spread that further. Now four
    renders in a row give the same bytes.
- **The loop.** The script finds the piece's length from its notes: the
  fewest cycles after which they repeat. The yard repeats every 8 cycles
  (48 s) and the chase every 4 (6.7 s). It renders three passes. The file
  holds the first pass, which plays once, and the second, which loops. The
  second pass already holds the tails of the notes before it, so the join
  doesn't click. The third pass is there to measure the join: the loop
  differs from it by at most 1 to 3 steps in 32768.
- **The PS1 treatment** (`tools/rebecca/music/ps1.ts`):
  - Strudel renders at 44100 Hz stereo, which is halved to 22050 Hz mono
    through a 63-tap filter. RE1's own tracks are 22050 Hz mono.
  - The level is set to RE1's. Its tracks measure -21 to -26 dB RMS, so
    ours aim at -24, held back so no peak passes -1 dB.
  - The PS1's 4-bit ADPCM, encoded as the console does and decoded again,
    gives the grit.
  - Reverb stays in the pattern.
- **The file.** It is 16-bit, mono, 22050 Hz, with a `smpl` loop and the
  `re1p` mark (`AudioFile.cpp`). The game's own loader, `AudioFile_Load`
  compiled on its own, reports the yard's loop as frames 1058400 to 2116800:
  48 s of intro, then 48 s that loop. The game's table marks the group as
  looping, and XAudio2 then loops only that region.

## RE1's own music as a reference

To write in RE1's manner, we have RE1's music in the same language: every
track on the PS1 disc as Strudel code, to read beside ours and to play. The
owner's page is <https://home.arpa/research/re1-music/>.

- **Where it comes from.** The PS1 disc keeps each room group's music as one
  `SOUND/SEPxx.HSB`: a VAB sound bank, a SEP file of up to three MIDI-like
  sequences (the PC port's three channels), and the bank's samples. `rae
  music` in retro-archive-explorer reads them. Of the 57 files, 97
  sequences have notes: 64 are music and 33 are sound loops. 50 of them
  come within 5% of the length of the PC port's WAV for the same track.
- **How it is written.** `tools/rebecca/music/re1.ts` writes one `.js` per
  sequence:
  - One cycle is one bar. Each voice is mini-notation weighted in the
    sequence's own ticks, so the timing is exact.
  - A track that plays notes before its loop start plays them once, as the
    PS1 does, then repeats only the loop. The code is an `arrange` of the
    intro and the loop, counted in ticks: `arrange` adds its counts as
    floats, and counts in bars made the times inexact. 32 of the 97
    sequences have an intro.
  - The instruments are the game's samples, keyed at their centre note and
    looped where the bank loops them.
  - Envelopes are worked out from the bank's ADSR, so they are close, not
    exact.
  - Pitch bends and the SPU's reverb are not reproduced, so leads that
    slide in the game hold still.
- **A second version on free sounds.** Every track also plays the same
  notes on VCSL and Strudel's synths, so it reads as plain Strudel code and
  sounds like what we can ship. `tools/rebecca/music/re1-voices.ts` sorts
  each of the game's instruments into a family:
  - The families are strings, pad, choir, brass, organ, flute, lead,
    piano, harp, bells, bass and the drums.
  - It sorts from what the sample measures as (its own pitch, how noisy,
    how bright, how it starts and fades) and how the music uses it (how low
    it plays, how long its notes are, whether it bends).
  - Each family has one sound chosen to sound good. That is a recorded VCSL
    instrument where there is one, and detuned synths with vibrato and a
    filter that follows the pitch where there isn't: VCSL has no strings,
    choir or brass. The free versions add a little reverb, as the PS1 did.

  A first try matched each sample to the free sound with the nearest
  spectrum. It chose bare sawtooth waves and white noise, which sounded like
  a chiptune, and the owner rejected it. A family wrong by ear goes in
  `tools/rebecca/music/re1-voices.fix.json`, by program
  (`"SEP0F/p2": "harp"`) or by tone (`"SEP0F/p7t3": "snare"`), and wins
  over the sorting. A tone's fix wins over its program's. `re1.ts` applies
  the file when it loads voices.json, so a fix needs no new sort. A fix
  that names no tone or no family is an error.
- **The proof.** `tools/rebecca/music/re1-check.ts` evaluates every track
  with Strudel's engine. It queries the intro once and the loop twice, and
  compares each note's start, length, pitch and sound with the disc, as
  exact fractions. The sound is the game's sample, or the family that
  voices.json and the fix file give the tone. Notes are compared as
  multisets, so a note played twice must be on the disc twice. All 97
  tracks, 17,010 notes, match, in both versions: 194 of 194 tracks,
  34,020 notes. Tampering fails it:
  - writing the whole first pass as the loop, as re1.ts did before, fails
    64 tracks;
  - doubling one voice fails 190, and merging unison notes fails 6;
  - spreading a fix's family name in place of its voice, or dropping
    program fixes, fails the track the fix is for.
- **It stays off GitHub.** It is Capcom's music, from the player's disc.
  Both repositories are public, so only the tools are committed. The output
  is built locally and published on the LAN:

      pnpm rae music re1.img /tmp/re1-music          # in retro-archive-explorer
      node tools/rebecca/music/re1-voices.ts /tmp/re1-music /tmp/vcsl /tmp/voices.json
      node tools/rebecca/music/re1.ts /tmp/re1-music /tmp/re1-strudel /tmp/voices.json
      node tools/rebecca/music/page-re1.ts /tmp/re1-strudel <@strudel/web 1.2.5 dist>

  The page plays the code with Strudel's own browser build, hosted beside
  it. strudel.cc can't load samples from the home network.

## The sketches

Both are in `tools/rebecca/music/sketches/` and are checked by `check.ts`.

| Sketch | Cue | What it tries |
|---|---|---|
| `yard.js` | the station, her hub | wind, low piano far apart, bowed vibraphone, a glass note |
| `chase.js` | the mine, unarmed | low ostinato, timpani, anvil, a bowed cluster |

They are a test of the sound, not finished pieces. Nobody has listened to
them yet. The yard is rendered and plays in the station's five rooms. The
chase is rendered too, but no room plays it: its cue has no places, and the
script that switches the mine to it is step 7.

## The plan

Each step ends in something to check:

1. **Choose the sound.** The owner listens to the sketches and says what is
   right and wrong. Edited links come back through the pad.
2. **Render a sketch to WAV without a person.** Done: `render.ts`, the same
   bytes twice.
3. **Give it the PS1 treatment.** Done in `ps1.ts`. Still to do: compare it
   with RE1's own tracks by ear.
4. **Add loop points.** Done: the render writes them, and the game's loader
   reads them. Still to do: the owner listens for the join.
5. **Give her mode its own table.** Done: the yard plays our render in her
   mode, and Chris's save room plays RE1's own track.
6. **Write the pieces,** in order of how long she hears them:
   1. the station;
   2. the camp, the road and the mine;
   3. the chase;
   4. the dawn, the partner's and Hal's themes;
   5. the rest;
   6. the credits last, built from the others.
7. **Switch channels as she works.** Room scripts set the state with 0x37:
   - the generator hum joins once the power is on;
   - the mill joins once the race fills;
   - the mine switches to the chase.
8. **Test it.** Done: `tools/harness/tests/music.ts` visits rooms of hers
   and Chris's save room, and checks the file each one plays.

## Settled

- **The save rooms play RE1's own music,** owner's call, 2026-10-15. Every
  save room in RE1 plays group 15 (`Bgm_31`): the disc's music table puts
  it in the 1F, underground, guardhouse and lab save rooms. Her mode points
  at the player's own `sound/Bgm_31.wav`; nothing is shipped.

## Open questions

- **The renders aren't in git.** They are rebuilt, the same bytes, with one
  command. Should they be committed, about 4 MB for the yard, so a build
  needs no Chrome and no network?
- **8-bit or 16-bit.** RE1's PC tracks are 8-bit. Ours are 16-bit after the
  ADPCM pass, so the yard is 4.2 MB. In 8-bit it would be half the size, with
  more hiss under a quiet piece.

- Is Strudel's sound close enough, or does the owner want a more orchestral
  bank, such as Sonatina (CC Sampling Plus, needs a credit)?
- How big can the patch be? 14 tracks of two minutes at 22050 Hz mono 16-bit
  come to about 75 MB. The options are 8-bit, which halves that, or teaching
  the overlay to find `.ogg` files.
