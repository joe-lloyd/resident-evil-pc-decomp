# Build the storyboard

From the repository root, restore the asset cache and generate the page:

```sh
node tools/rebecca/assets.ts pull
node tools/rebecca/plan/storyboard.ts /tmp/rebecca-storyboard
```

Use Node 24 or later. Image conversion uses macOS `sips` or ImageMagick `magick` on Linux. The output contains `index.html` and camera JPEGs at 640 pixels wide. The generator embeds the CSS and browser script in the page.

Run the source checks:

```sh
node --test tools/rebecca/plan/storyboard.test.ts
```

Serve the output over HTTP to test browser storage and clipboard access. Use HTTPS for clipboard access outside localhost. The page includes the research navigation script at `/research/rebecca-day/nav.js`. That script needs the research index on the same host.

## Publish the page

Copy the generated output through the existing research route:

```sh
rsync -az --rsync-path='sudo -n rsync' /tmp/rebecca-storyboard/ pi-server:/opt/homelab/cert-setup/dashboard/research/rebecca-storyboard/
```

The hand-written research index links the storyboard in its Start here section. The navigation script reads that card from the index.

## Read the counts

Room scripts and camera renders determine current build status. The page also keeps the older label from `day.ts`. The original mansion save room counts as built through its existing room script. Its review image can still be missing.

Item rows join the source tables to `item_aot_set` records in room scripts. The table includes the starting kit from `GameStart.cpp`, hand-written cabin pickups and the original save room's Sword Key. Repeated pickup records with the same item flag count once. Loaded weapons contribute their rounds. Missing placements do not contribute to balance totals.

The entry audit follows `scripts.ts`. A room's message zero counts when its script shows it and no entry cutscene replaces it. Files retain their full text and the labels from calendar, map and roster pages. The page also shows raw room messages for source edits.

The missing list combines repository evidence with unfinished rows from `todo.ts`. An under-way tracker row needs review, even when a door tour has passed. Chris's entrance is part of `cut-sleep`, so it does not count as an unwritten scene.

Balance findings are prompts for a route test. Enemy HP is absent from `foes.ts`. The page does not simulate damage, inventory spending or route choices. Each scene now links its visits from the current four-quarter recording. See the clip regeneration steps below.

## Review edits

Goal edits, dialogue notes and item notes save automatically to this browser's localStorage. Copy my edits exports markdown grouped by room, including the field, old source value and new text or note. Clear edits asks before removing saved changes. If the source changes after an edit, the page flags the saved edit and includes both source versions in the export. No edits are sent to a server.

Scene notes are versioned. Version 1 is the first set of renders, and its notes use the field `scene notes`. Each time a scene is rebuilt after a review, add an entry for it in `versions.json` with the merge date, the pull requests and the before and after sheet under `review/`. The page then labels the notes box with the new version and saves to `scene notes v<n>`. Notes on earlier versions stay in the browser and show read-only under the box, so the owner never has to clear them. The export labels each note with its version.

## Regenerate the room clips

The storyboard uses the 17 October whole-day recording, split into four quarters. The published sources are at [the whole-day page](https://home.arpa/research/rebecca-whole-day/). Their server directory is `/opt/homelab/cert-setup/dashboard/research/rebecca-whole-day` on `pi-server`.

`recording-events.json` preserves the timestamped events from the matching logs. Each quarter has the source video hash, log hash, original attempt name and run result. The local originals survived under `/tmp/rebplan/quarters/`. The published video hashes match these attempts:

- Quarter 1 uses `q1/log-1.txt` and `reb-q1-1.mp4`.
- Quarter 2 uses `q2/log-chain2.txt` and `reb-q2-chain2.mp4`.
- Quarter 3 uses `q3/log-chain3.txt` and `reb-q3-chain3.mp4`.
- Quarter 4 uses `q4/log-chain3.txt` and `reb-q4-chain3.mp4`.

To rebuild the event export from those originals:

```sh
node tools/rebecca/plan/storyboard/recording.ts /tmp/rebplan/quarters tools/rebecca/plan/storyboard/recording-events.json
```

The committed export is enough for indexing if the original logs are no longer available. Room ids come from `day/rooms.ts` and `day.ts`, including the cabin's `lookout` slug and the original mansion save room.

`clips.py index` groups consecutive log events into visits. It uses the capture's wall clock with scale 1 and an approximate offset of minus four seconds. It then compares half-second video samples with the room camera JPEGs to find the actual entry before the settled log stamp. The comparison crops the black bars and discards the worst 30 percent of pixel differences to reduce the effect of Rebecca and dialogue. The log fixes the visit order. Two consecutive matching frames confirm an entry. Quarter 1 keeps the opening text. Quarters 2 to 4 discard the ridge intro before checkpoint restore. The matcher keeps the ridge render in its comparisons so those unlogged intro frames cannot match the restored room.

The original save room has no camera render. Its checked entrance at 844.5 seconds in quarter 4 is an explicit override in `recording-events.json`. `clips.json` records every visit's room, quarter, visit number, start, end, poster time, file, events and any matching note. Visit numbers continue across quarters within a room. A visit spanning a quarter break has a separate clip for each source quarter.

Run indexing and cutting on `pi-server`. Python 3, Pillow, NumPy, ffmpeg and ffprobe are already installed there. First publish the generated camera JPEGs so the indexer reads the same room art as the page. Copy the scripts and event export to a temporary work directory:

```sh
ssh pi-server 'mkdir -p /tmp/rebecca-room-clips'
scp tools/rebecca/plan/storyboard/clips.py tools/rebecca/plan/storyboard/recording-events.json pi-server:/tmp/rebecca-room-clips/
ssh pi-server 'OPENBLAS_NUM_THREADS=1 python3 /tmp/rebecca-room-clips/clips.py index /tmp/rebecca-room-clips/recording-events.json /opt/homelab/cert-setup/dashboard/research/rebecca-whole-day /opt/homelab/cert-setup/dashboard/research/rebecca-storyboard/img /tmp/rebecca-room-clips/clips.json'
scp pi-server:/tmp/rebecca-room-clips/clips.json tools/rebecca/plan/storyboard/clips.json
```

The indexer caches half-second samples beside its output, keyed by the source video hash. Delete the `.npy` files to force new extraction. These files stay outside the repository.

To regenerate the video and posters from the committed manifest, copy that manifest and run only the cut command:

```sh
scp tools/rebecca/plan/storyboard/clips.py tools/rebecca/plan/storyboard/clips.json pi-server:/tmp/rebecca-room-clips/
ssh pi-server 'sudo -n python3 /tmp/rebecca-room-clips/clips.py cut /tmp/rebecca-room-clips/clips.json /opt/homelab/cert-setup/dashboard/research/rebecca-whole-day /opt/homelab/cert-setup/dashboard/research/rebecca-storyboard'
```

The sources are already 640 by 480 H.264. Cutting copies their video packets without another lossy encode and moves each MP4 index to the front. Each clip starts on a source keyframe at least three seconds before the matched room entry. The cutter seeks one millisecond past the stored start so a rounded timestamp cannot select the previous keyframe. It ends when the next room first appears. This small overlap keeps the doors visible. The final packet of every source is truncated from recorder shutdown, so each quarter's last clip stops at a complete keyframe before the damaged tail. The omitted tail is idle footage after the last logged action.

Rebuild and publish the page with the commands above after updating `clips.json`. Publish without `--delete` so the generated page does not remove `clips/`. Video files and posters stay on the server and must not enter git.

## Check clip coverage

The recording has 142 visits in 53 of the 58 rooms. Flume, line track, weather station, mast and wine cellar have no footage. Their scenes say so. God mode shortens fights, and the recordings have no audio. A clip shows the route that the harness took, not every optional action in a room.

Quarter 2 and quarter 4 logs finish with `FAIL` because the glitch watch flagged the checkpoint restore. They still reach their final goals. The source logs remain the authority for what happened. These recordings do not prove that every scene, animation or fight is correct.

The clip check notes in `footage-checks.md` list the inspected frames and the room-entry check for the ending. Other visits rely on automated matches constrained by the logs. Outdoor fades make exact boundaries uncertain by a few seconds, so clips keep a door lead-in.

Check the published media through the owner's HTTPS route:

```sh
python3 tools/rebecca/plan/storyboard/verify-clips.py
```

The check requests every clip and poster, verifies MIME types, and tests full and ranged GET responses from each quarter. It also checks the page's player count, navigation tag and research index card. In a browser, play clips from all four quarters and confirm that leaving a scene pauses its videos.

## Re-record one reviewed scene

`tools/harness/record-scene.ts` records one route and saves its source MP4,
timestamped events, screenshots and entry checkpoints together. It uses
normal damage. The ridge starts through NEW GAME and Rebecca's card, keeps
the opening text visible, checks her 15 loaded rounds and knife, walks both
cameras and the west boulder, and exits to the mountain trail.

Build and deploy the branch and overlay first. Use these lab settings for
all of the harness commands:

```sh
export RE1_LAB_GAME_DIR='D:\Games\RE1-files'
export RE1_LAB_REPO_DIR='C:\Users\joell\Tools\re1-files'
export PORT=7811
export OVERLAY=/tmp/reb-ridge-build
node tools/harness/deploy.ts reb-ridge-feedback
RAE_CLI=/path/to/retro-archive-explorer/scripts/cli.mjs \
  node tools/rebecca/build.ts /path/to/USA "$OVERLAY"
node --input-type=module -e "import {deployOverlay} from './tools/harness/lab.ts'; deployOverlay(process.env.OVERLAY + '/REB')"
node tools/harness/record-scene.ts ridge --out /tmp/ridge-review
```

The recorder waits for ffmpeg to open its output before moving the game.
A passed run is evidence of the route checks; inspect the captured frames
before claiming that the scene looks or behaves correctly. The recording
has no sound because the lab has no loopback device. Music renders must be
restored separately if the lab needs to play the themes.

For the next scene, use the destination checkpoint saved by the previous
run. The trail has a review route ready:

```sh
node tools/harness/record-scene.ts trail \
  --from /tmp/ridge-review/trail-entry.json --out /tmp/trail-review
```

For other scenes, add `day/<slug>/review.json`, or pass `--route <file>`.
The route has `scene` and `steps`. Steps can `walk` to `x,z`, `hold` for
`frames`, or `look` at a `zone` with `x,z,w,d`. A step can name a `picture`;
a walk or hold can require a `camera`. Finish with one `exit` with `x,z`
and `to`. Give an indoor exit its door `zone` too, so the harness presses
action. Later scenes require `--from` with a played checkpoint inside the
scene. The recorder rejects checkpoints marked as made up from the plan.
It saves the entered neighbour's checkpoint for the next review.

Copy `recording.json` and its MP4 to a temporary directory on `pi-server`.
Inspect video frames and choose the start, end and poster times in that
source. Keep the opening and exit; leave at least a second before the
recorder's damaged final packet. Copy the manifest and cutter there too:

```sh
ssh pi-server 'mkdir -p /tmp/rebecca-scene-review'
scp /tmp/ridge-review/recording.json /tmp/ridge-review/ridge-*.mp4 \
  tools/rebecca/plan/storyboard/clips.json \
  tools/rebecca/plan/storyboard/replace-scene.py pi-server:/tmp/rebecca-scene-review/
# Replace START, END and POSTER with frame-checked source times.
ssh pi-server 'python3 /tmp/rebecca-scene-review/replace-scene.py \
  /tmp/rebecca-scene-review/recording.json /tmp/rebecca-scene-review/clips.json \
  /tmp/rebecca-scene-review/publish --start START --end END --poster POSTER \
  --note "Inspected frames and observed behaviour"'
scp pi-server:/tmp/rebecca-scene-review/clips.json tools/rebecca/plan/storyboard/clips.json
ssh pi-server 'sudo -n rsync -az /tmp/rebecca-scene-review/publish/ /opt/homelab/cert-setup/dashboard/research/rebecca-storyboard/'
node tools/rebecca/plan/storyboard.ts /tmp/rebecca-storyboard
rsync -az --rsync-path='sudo -n rsync' /tmp/rebecca-storyboard/ pi-server:/opt/homelab/cert-setup/dashboard/research/rebecca-storyboard/
```

The cutter checks the source hash, cuts just this scene, keeps its source
and event log under `recordings/`, and replaces only that room's manifest
rows. Other rooms retain their old clips. Pass `--room` when the storyboard
names the room differently from its scene: the `lookout` scene is the
storyboard's `cabin`. Pass `--add` to keep the room's earlier review clips
and add this one as the next visit. Each review clip displays its own
date, damage mode and start method.

When a room's enemies kill a scripted walk at normal damage, record a second
route with `record-scene.ts <slug> --route <file> --from <checkpoint> --god`.
The recording says it ran in god mode, and the storyboard shows that on the
clip. Cut it with `--add` so the normal-damage clip stays. The old quarter cutter skips review
rows. Do not rebuild the entire index over a reviewed manifest, since that
would restore the old scene visits. Keep `clips.json` in git; videos,
posters and source recordings stay on the server. Publish without
`--delete`, and verify in a separate browser profile so the owner's saved
edits are untouched.
