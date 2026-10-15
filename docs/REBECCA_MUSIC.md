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
  Her own save-room theme follows that shape with a tune of ours.

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
  with no engine change. `tools/rebecca/build.ts` already writes her footstep
  sounds there. The table is the gap: it is compiled in and shared by every
  mode. Her rooms sit in base slots whose rows are all 0xFF, so her day is
  silent today.

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
- **Rendering.** Strudel has had an offline WAV export since December 2025
  ([PR #1674](https://codeberg.org/uzu/strudel/pulls/1674)). Nobody has shown
  it running without a person at the browser. The fallback is our own small
  renderer: query the events as `check.ts` does, play the VCSL samples, and
  write the WAV, all in Node. It is more work, but it is ours and needs no
  browser.

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
  - The instruments are the game's samples, keyed at their centre note and
    looped where the bank loops them.
  - Envelopes are worked out from the bank's ADSR, so they are close, not
    exact.
  - Pitch bends and the SPU's reverb are not reproduced, so leads that
    slide in the game hold still.
- **The proof.** `tools/rebecca/music/re1-check.ts` evaluates every track
  with Strudel's engine and compares each note's start, length and pitch
  with the disc, as exact fractions. All 97 tracks, 17,010 notes, match. A
  converter tampered to shorten one note length fails 34 tracks.
- **It stays off GitHub.** It is Capcom's music, from the player's disc.
  Both repositories are public, so only the tools are committed. The output
  is built locally and published on the LAN:

      pnpm rae music re1.img /tmp/re1-music          # in retro-archive-explorer
      node tools/rebecca/music/re1.ts /tmp/re1-music /tmp/re1-strudel
      node tools/rebecca/music/page-re1.ts /tmp/re1-strudel <@strudel/web 1.2.5 dist>

  The page plays the code with Strudel's own browser build, hosted beside
  it. strudel.cc can't load samples from the home network.

## The sketches

All three are in `tools/rebecca/music/sketches/` and are checked by `check.ts`.

| Sketch | Cue | What it tries |
|---|---|---|
| `safe.js` | her save-room theme | held minor chords, a harp arpeggio, an ocarina lead |
| `yard.js` | the station, her hub | wind, low piano far apart, bowed vibraphone, a glass note |
| `chase.js` | the mine, unarmed | low ostinato, timpani, anvil, a bowed cluster |

They are a test of the sound, not finished pieces. Nobody has listened to
them yet.

## The plan

Each step ends in something to check:

1. **Choose the sound.** The owner listens to the sketches and says what is
   right and wrong. Edited links come back through the pad.
2. **Render one sketch to WAV, then automate it.**
   - First by hand from Strudel's export.
   - Then without a person: Playwright driving the export on jellybingus, or
     our own renderer.
   - Done when one command renders the same bytes twice.
3. **Give it the PS1 treatment.**
   - ffmpeg, which is installed on jellybingus, resamples to 22050 Hz mono.
   - Bit reduction adds the grit.
   - Reverb stays in the pattern.
   - Compare against RE1's own tracks by ear.
4. **Add loop points.** `tools/rebecca/music/loop.ts` writes the `smpl` and
   `re1p` chunks. Prove it in the game: the intro plays once and the loop
   joins without a click.
5. **Give her mode its own table.** Her mode loads a music table from her
   overlay in place of `g_BgmRoomData`. Chris's and Jill's games keep the
   compiled table. Done when a placeholder WAV plays in the yard in her mode
   and Jill's hall music is unchanged.
6. **Write the pieces,** in order of how long she hears them:
   1. the station;
   2. her save-room theme;
   3. the camp, the road and the mine;
   4. the chase;
   5. the dawn, the partner's and Hal's themes;
   6. the rest;
   7. the credits last, built from the others.
7. **Switch channels as she works.** Room scripts set the state with 0x37:
   - the generator hum joins once the power is on;
   - the mill joins once the race fills;
   - the mine switches to the chase.
8. **Test it.** The harness walks the day and checks which files are loaded
   in each room.

## Open questions

- Is Strudel's sound close enough, or does the owner want a more orchestral
  bank, such as Sonatina (CC Sampling Plus, needs a credit)?
- Is `Bgm_31` RE1's save-room theme? The code points that way: the mansion's
  and the guardhouse's save rooms use it. Someone has to listen to confirm.
- How big can the patch be? 15 tracks of two minutes at 22050 Hz mono 16-bit
  come to about 80 MB. The options are 8-bit, which halves that, or teaching
  the overlay to find `.ogg` files.
