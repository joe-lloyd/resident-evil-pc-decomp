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
slots, holding a Beretta with 15 rounds and a clip of 15 rounds.
She uses Chris's room files. Scenes written for Chris do not expect her as
the player and can stall.

## God mode

```
residentevil.exe --god
```

For playing a scenario through to check it, not for balance. Her health
stays full, a death check puts her back on her feet, and every hit she lands
kills. It works with or without test mode; in test mode, `god 0|1` turns it
off and on. Windows only for now.

## Test mode

```
residentevil.exe --test-port <port> [--boot ...]
```

The window's title is `RESIDENT EVIL <port>`, so each of several games side by side can be recorded on its own. The game listens on `127.0.0.1:<port>` for one client; a newer connection
replaces an older one. Test mode also:

- ignores the real keyboard; only keys sent by the client count;
- keeps running when the window is not in focus, its sound too;
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
| `god` | 1 while god mode is on |
| `msf`, `msf2` | `g_main_state_flags` and its second word, hex (`MSF_*` in `src/Globals.h`) |
| `title`, `fmv`, `dbg` | `g_titleMode`, a movie is playing, the F1 debug menu is open |
| `stage`, `room`, `cam`, `cut` | where the player is |
| `charModel` | `g_CharacterModelId`; 3 is Rebecca |
| `player` | `id`, `x`, `y`, `z`, `angle`, `hp`, `maxHp`, `weapon` (the 1-based slot in hand), `cf` (byte 0xDC: the collision flags `check_room_collision` reads) |
| `items` | `[id, qty]` for each slot: 6 for Chris and Rebecca, 8 for Jill |
| `box` | `[id, qty]` for each of the item box's 48 slots |
| `enemies` | `[type, status, x, y, z, hp]` for each occupied slot of `g_EnemiesList` (status not 0) |
| `msg` | `choice` (`g_menu_choice_id`; 0x80 means a message is open), `id` (the last message shown), `flags` (`g_message_flags`) and `menu` (`g_openMenuFlag`) |
| `banks` | script flag banks 0-9 as hex bytes, numbered like `cmd_bit_test` |
| `bgm` | `state` (`g_BGM_STATE`, 255 for silence) and `ch`: for each of the three BGM channels, `[file, playing, volume]`: the WAV it loaded (`""` for none), `getSndStat` (1 while it plays) and `getSndVol` (-1 is full, -9999 silent) |

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
| `god <0\|1>` | god mode off or on: her health stays full, a death check puts her back on her feet, and every hit she lands kills |
| `slot <i> <id> <qty>` | set slot `i` of her bag outright |
| `boxslot <i> <id> <qty>` | set slot `i` of the item box outright |
| `unequip` | nothing in her hands |
| `shot <path>` | save the next frame's back buffer as a BMP on the game machine |

The shot is the whole 640x480 frame, background included.
`tools/harness/snapshot.ts` fetches it and saves it as a PNG.

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

She moves the way a player does. `walkTo` holds forward the whole way, steers
with taps of left and right while moving, and stops to turn only for a turn
wider than about 25 degrees. `goTo` keeps the keys down from one waypoint of
its path to the next. Before each `goTo`, Jev chooses whether she runs (the
run key held with forward) or walks, from a short account of the way: its
length, its sharp corners, the live enemies near it and her health. Without
`TYPESAFE_API_KEY` she runs. Set `HARNESS_TRACE=1` to see each choice and its
probability.

```
TYPESAFE_API_KEY=$(ssh vault get typesafe-api-key) OVERLAY=... node tools/harness/tests/day.ts yard shed
```

```
node tools/harness/deploy.ts test-mode       # build the branch and install it
node tools/harness/tests/rebecca-boot.ts     # run one test
```
