# Test mode and dev boot

Port additions for automated testing and fast iteration. Neither changes the
game unless its command-line flag is given.

## Dev boot

```
residentevil.exe --boot <chris|jill|rebecca>[:<stage>:<room>]
```

Starts a new game straight from launch. It skips the logos, the title, the
character select and the opening movie. With a stage and room, the game starts
in that room. The player stands by its first door, placed the same way the
debug menu's ROOM CHANGE places them. Stages are numbered from 0, as in the
debug menu, so `rebecca:0:2` is ROOM102.

`rebecca` starts a new game as Rebecca Chambers. She has 88 HP and 6 item
slots, holding a Beretta with 15 rounds, a First Aid Spray and a Green Herb.
She uses Chris's room files. Scenes written for Chris do not expect her as
the player and can stall.

## Test mode

```
residentevil.exe --test-port <port> [--boot ...]
```

The game listens on `127.0.0.1:<port>` for one client; a newer connection
replaces an older one. Test mode also:

- ignores the real keyboard; only keys sent by the client count;
- keeps running when the window is not in focus;
- skips the single-instance check, so several games can run side by side;
- skips every movie, as if its file were missing.

Each line the game sends is one JSON object with a `t` field.

### State lines

The game sends `{"t":"state", ...}` whenever anything in it changes. It
reports raw values; `tools/harness/state.ts` turns them into meanings.

| Field | Meaning |
| --- | --- |
| `frame` | game frames since launch, 30 per second; movies do not advance it |
| `play` | 1 when game_loop's frame loop ran this frame, so the game is in a room |
| `msf`, `msf2` | `g_main_state_flags` and its second word, hex (`MSF_*` in `src/Globals.h`) |
| `title`, `fmv`, `dbg` | `g_titleMode`, a movie is playing, the F1 debug menu is open |
| `stage`, `room`, `cam`, `cut` | where the player is |
| `charModel` | `g_CharacterModelId`; 3 is Rebecca |
| `player` | `id`, `x`, `y`, `z`, `angle`, `hp`, `maxHp`, `weapon` |
| `items` | `[id, qty]` for each slot: 6 for Chris and Rebecca, 8 for Jill |
| `enemies` | `[type, status, x, y, z, hp]` for each entry in `g_EnemiesList` |
| `msg` | `choice` (`g_menu_choice_id`; 0x80 means a message is open) and `id`, the last message shown |
| `banks` | script flag banks 0-9 as hex bytes, numbered like `cmd_bit_test` |

Flag `n` of a bank is in 32-bit word `n / 32`, counting from the top bit:
`0x80000000 >> (n % 32)`.

### Commands

One per line. Each is answered with `{"t":"ack","cmd":...,"ok":0|1}`.

| Command | Effect |
| --- | --- |
| `tap <vk> [frames]` | hold a virtual key for that many frames (default 2) |
| `down <vk>`, `up <vk>`, `release` | hold, let go, let go of every key |
| `state` | send a state line now, even if nothing changed |
| `ping <token>` | answered with `{"t":"pong","token":...,"frame":...}` |
| `room <stage> <room>` | change room like the debug menu; a second ack, `room-start`, comes when it begins |
| `flag <bank> <index> <0\|1>` | clear or set a script flag |
| `shot <path>` | save the next frame's back buffer as a BMP on the game machine |

The back buffer has no pre-rendered background. `tools/harness/snapshot.ts`
lays the room's `.pak` background under the shot to make a viewable picture.

## The harness

`tools/harness/` is TypeScript that Node 24 runs directly, with no build step
and no dependencies.

- `lab.ts` builds, installs, starts and stops games on the Windows machine
  over SSH.
- `link.ts` is the connection.
- `flows.ts` holds reusable steps such as `settle`.
- `tests/` holds the tests.
- `jev.ts` asks Jev, TypeSafe's typed judgment model, for decisions that need
  common sense. It reads text only, so it gets the state, never a picture.

```
node tools/harness/deploy.ts test-mode       # build the branch and install it
node tools/harness/tests/rebecca-boot.ts     # run one test
```
