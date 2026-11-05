# Debug dashboard

A live view of a running game for a second monitor. It shows the room map
with the player, enemies, cameras and camera switch zones, plus the player's
health, the enemies, the inventory, the item box, the music, the flag banks
and a log of what changed. It is a dev tool and never ships with the game.

The game runs as its own process in test mode (`--test-port`, see
`docs/TEST_MODE.md`). The server holds the one test-mode connection through
`tools/harness/link.ts` and streams the parsed state to the page as
server-sent events. On connect it sends `keyboard 1`, so you can play with the
real keyboard while the page watches.

```
game (--test-port N)  --TCP JSON lines-->  server.ts  --SSE-->  page (browser or Electrobun window)
                      <--commands-------              <--POST /cmd--
```

## Run it in a browser

Node 24 or Bun, no install step:

```
# The game is already running and its port is reachable on 127.0.0.1:
PORT=7811 node tools/debugger/run.ts

# Start the game on the lab machine over SSH (tools/harness/lab.ts) and tunnel its port:
RE1_LAB_GAME_DIR='D:\Games\RE1-files' PORT=7811 RE1_ARGS='--boot chris:0:6' \
  node tools/debugger/run.ts --launch

# On the Windows machine itself, start a local exe:
node tools/debugger/run.ts --exe D:\Games\RE1-files\residentevil.exe
```

Then open <http://127.0.0.1:7900/>.

| Variable | Default | Meaning |
|---|---|---|
| `PORT` | `7811` | the game's test port |
| `HTTP_PORT` | `7900` | the dashboard's port |
| `RE1_DATA` | `/tmp/re1-pc` | folders with `Stage1..Stage7` room files for the map, overlay first, split by the path separator |
| `RE1_ARGS` | | extra game arguments for `--launch` and `--exe` |
| `RELAY_PORT` | | pass the game through on this port, so a test script can drive it while the page watches |

## Watch a test script

The game takes one test-mode client. With `RELAY_PORT` set, the server
forwards the game's lines to whoever connects there and their commands to the
game, and the page shows the run. Point `lab.ts` at it with `RE1_LAB_RELAY`:

```
# on the game machine, in the app's environment: PORT=7811 RELAY_PORT=7812
RE1_LAB_GAME_DIR='D:\Games\RE1-files' PORT=7811 RE1_LAB_RELAY=7812 \
  OVERLAY=<REB build folder> node tools/harness/tests/playthrough.ts
```

`open()` still starts the game on `PORT`; only the link goes through the
relay. The dashboard does not send `keyboard 1` in this mode.

## What the page shows

The map frames the floor area the player stands in: the free floor is split
into areas the collision closes off (`rdt.ts` `floor()`), which matters in
the Rebecca rooms, whose boundary boxes reach far past the room. Switch zones
of the live camera take the colour of the camera they cut to.

The log has rooms, cameras, screens, hits in play, enemy damage, each message
id as it comes up, items gained and lost, and every script flag that flips,
by bank name and index. The message and main-state banks flip every few
frames and are left out. `changes()` in `server.ts` builds it;
`node --test tools/debugger/server.test.ts` covers it.

The command box sends any test-mode protocol line, for example `room 0 6`,
`give 68 1` or `pos 15000 10000`. A rejected command shows in the log in red.

## From a terminal

`cli.ts` reads the same stream, for a terminal or an agent watching a run:

```
node tools/debugger/cli.ts watch            # the log, as it comes
node tools/debugger/cli.ts watch --states   # plus where she is, once a second
node tools/debugger/cli.ts state            # the latest state, one line (--json for all of it)
node tools/debugger/cli.ts send room 0 6    # what the command box sends
```

It talks to `http://127.0.0.1:7900`; set `DASHBOARD` for another address,
for example a port tunnelled from the game machine.

## Run it as a desktop app

`app/` is an Electrobun 2 shell. It runs the same server in its Bun main
process and opens the page in a native window. It needs
[Hutch](https://hutch.blackboard.sh), which `npx electrobun` installs:

```
cd tools/debugger/app
PORT=7811 hutch run start
```

The environment variables above apply. Only one client can hold the game's
test port, so do not run the browser server and the app against the same game.

It runs on Windows 11: on 29 Oct 2026 the app on jellybingus started the
game itself (`RE1_EXE`), connected and drew the dashboard. The window opens
without taking focus. On macOS 13 every Electrobun 2.0.5 window crashes in
`+[WKWebsiteDataStore dataStoreForIdentifier:]`, a macOS 14 API. Its own
hello-world template crashes the same way, with or without `bundleCEF`.

To record the windows while they sit behind others, use FFmpeg's
`gfxcapture` source (Windows Graphics Capture). `gdigrab` records whatever
is on top of the window instead.

## Not in the MVP

The plan from the design thread, in order: game window capture and recording,
feedback notes stamped with frame and room, a game log sink over the socket,
camera mask cutouts, heat maps, and reading arbitrary globals with
`ReadProcessMemory`.
