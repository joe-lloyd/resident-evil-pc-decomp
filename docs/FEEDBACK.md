# Capture playthrough feedback

Feedback is on in Rebecca mode, including `--mode REB`. Add `--feedback` to
use it in another mode. The plain USA game keeps its original F9 behavior.
No test link or debug setting is needed to record notes.

During gameplay, press F9. The next completed frame freezes under a text box
in the game's ASCII font. Type up to 240 printable ASCII characters. Backspace
deletes, Tab cycles clipping, drawn-over, item, enemy, text, and other.
Enter saves an empty or filled note. Escape cancels. Both resume gameplay.
F9 repeats do nothing while the box is open. Keys held when the box closes
stay blocked until release. Game tasks and input updates stop during editing. The test link still answers
state and ping; commands that mutate the frozen game return `ok:0`.

Each saved mark lives under the configured `config.ini [Save] Path`:

```
feedback/20261018-140506/
  note.json
  shot.rgba
```

Folder times are UTC. A second mark in the same second gets a `-01` suffix.
The image contains the completed frame before the editor draws. It uses the
renderer's `CaptureBackbufferToRGBA()` call, which the test link's
`SaveBitmapToFile()` path also uses. `shot.rgba` starts
with `RE1CAP <width> <height>\n`, followed by RGBA bytes, top row first.
The page command converts it to `shot.png` and embeds that PNG in the page.
Cancel writes no files. A write failure keeps the editor open so Enter can
retry or Escape can cancel. A failed write can leave an incomplete folder.
The page builder skips folders without `note.json`.

`note.json` version 1 records the kind, text, UTC time, content mode, release
version, and compile time. There is no git SHA in the current build system.
Its `state` is the full test-link state JSON from `GameState_Json()` in
`src/game/TestMode.cpp`. This includes stage and room indices, camera, player
position and angle, health, equipped bag slot, bag quantities, all 48 box
slots, every live enemy's type, status, position and health, and all ten flag
banks. `player.anim` contains the state animation id, attack animation and
animation frame. `player.action` contains the four bytes at player offsets
0x84 through 0x87. `path` holds up to 40 samples at 250 ms intervals from the
last ten seconds, each with its age, room, camera, position, and angle.
Room slugs come from `tools/harness/world.ts` when the report is built.

## Collect the session

Use Node 24. No package install is needed. The Windows lab must be online for
pull and restore. `lab.ts` uses SSH and the desktop scheduled-task launcher.
Feedback commands default to `D:\Games\RE1-files` on jellybingus. Set
`RE1_LAB_GAME_DIR` to select another installation.

```sh
node tools/harness/feedback.ts pull /tmp/reb-feedback
RE1_OVERLAY=/path/to/REB RE1_BASE=/path/to/USA \
  node tools/harness/feedback.ts page /tmp/reb-feedback /tmp/reb-feedback.html
node tools/harness/feedback.ts restore /tmp/reb-feedback/20261018-140506
```

Pull reads the remote config to find the save directory, then fetches every
feedback folder in one archive. It leaves the remote files in place.
The local `RE1_OVERLAY` and `RE1_BASE` folders supply the room collision data.
You can instead set `RE1_FEEDBACK_ASSETS` to a list of local asset roots,
separated by the host's path delimiter. Missing room data gets an explicit
message in the card. The path plot keeps samples from the captured room.

The page is self-contained apart from the shared Rebecca research navigation
script. Each card has the captured frame, note, room slug, camera, position,
health, enemies, and the path over collision shapes. Put `after.png` in an
entry and rebuild the page to fill its proof slot. Publish the resulting HTML
through the usual research deployment path when it is ready to share.

## Restore a mark

Restore boots the captured character and content mode over the test link,
then adapts `state` through `checkpoint.take()` and `checkpoint.restore()`.
It restores banks 1, 2, 3, and 7, the bag and box, room, x/z position, angle,
and equipped weapon slot. The game stays running and the physical keyboard
regains control. `PORT` selects the test port, default 7811.

This has the existing checkpoint semantics. It re-enters the room and runs
its scripts. It does not rewind the VM, camera, health, animation frame,
enemy movement, RNG, or wall-clock timers to the saved frame. Those values
remain in `note.json` for comparison. A bug tied to an enemy's exact attack
frame may require manual setup after restoring the checkpoint.

## Checks without the game

```sh
node --test tools/harness/feedback.test.ts
python3 tests/check_platform_boundary.py
```

The committed fixture has a one-pixel PNG and a handwritten state. The tests
exercise the page CLI, raw-to-PNG conversion, escaping, room collision parsing,
path filtering, and the checkpoint adapter's literal output.

`tests/feedback_input.cpp` exercises the Linux platform text queue and held-key
release behavior without a window. On a Mac with SDL headers:

```sh
clang++ -std=c++17 -Isrc -I/path/to/includes tests/feedback_input.cpp \
  src/platform/linux/platform.cpp -Wl,-dead_strip -o /tmp/feedback-input
/tmp/feedback-input
```

The include folder must contain `SDL2/SDL.h`. The test replaces SDL's text
start/stop calls. It does not exercise SDL event delivery or the game loop.
On Linux, use `-ffunction-sections -Wl,--gc-sections` in place of
`-Wl,-dead_strip`.
