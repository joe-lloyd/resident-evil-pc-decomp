# Footage checks

The sources are the four videos at [the whole-day recording](https://home.arpa/research/rebecca-whole-day/), recorded on 17 October 2026. All four SHA-256 hashes match the surviving local attempt videos. `recording-events.json` records those hashes and each log's hash.

The room order and action labels come from the matching run logs. The entry stamps are late when a room starts with dialogue or a cutscene. Background comparison at two samples per second refines those entries. The capture uses wall-clock timestamps, so the scale remains 1. The initial log offset is minus four seconds. Matching refines that approximate offset separately at each entrance.

I extracted and viewed these frames from the original quarter videos. Times below are video seconds, not log seconds.

| Quarter | Video time | Room | What the frame shows |
| --- | --- | --- | --- |
| 1 | 18 | Ridge | Rebecca at the tree during the opening scene |
| 1 | 30 | Trail | Rebecca on the forest path, with the ranger-station line |
| 1 | 82 | Cabin | Rebecca by the cabin door during the entry dialogue |
| 1 | 417 | Woods | Rebecca in the clearing with the blood on the ground |
| 2 | 276 | Tower top | Rebecca on the lookout balcony above the smoking valley |
| 2 | 682 | Generator | Rebecca beside the generator and electrical panel |
| 3 | 488 | Gallery | The mine gallery with water, rails and the lit table |
| 3 | 601 | Mine lift | Rebecca at the mine lift gate |
| 3 | 859 | Booth | Rebecca at the gondola control desk |
| 4 | 84 | Car | Rebecca inside the gondola car |
| 4 | 152 | Crash | The burning helicopter and Rebecca at the crash site |
| 4 | 861 | Save room | Rebecca and Chris during the ending scene |

The remaining visits use log-constrained background matches and were not all inspected by eye. Entries have half-second precision, and outdoor fades can shift a match by a few seconds. The door lead-in keeps those entrances inside the clips.

Two initial checks did not show a room background. Quarter 1 at 1627 seconds showed the item menu during the workshop pickup. Quarter 2 at 68 seconds showed a dark door transition into the depot. Those samples do not count as confirmed room views.

The mansion save room has no camera render to match. I inspected quarter 4 from 825 seconds onward, then again at half-second intervals from 842 seconds. At 844 seconds the ladder transition is still visible. The first room frame appears at 844.5 seconds. The explicit override keeps the entry thought and the complete ending before the capture's idle tail.

The source capture ended mid-packet in every quarter. An ffmpeg decode of the final three seconds reports an invalid NAL unit at the tail. Cutting stops each final clip at a complete source keyframe at least a second before the source duration. This removes idle tail footage after the last action without re-encoding the video.

Quarter 2 and quarter 4 logs report a failed glitch check on checkpoint restore. The export preserves those failures. Reaching the final goal does not turn those runs into clean test passes.

## Published checks

The rebuilt [storyboard](https://home.arpa/research/rebecca-storyboard/) has 142 players with posters and `preload="none"`. The MP4 files total 286,780,117 bytes, or 273.49 MiB. All 142 MP4 URLs and 142 poster URLs return HTTP 200 with the expected MIME type. Full GET and byte-range GET checks pass for clips from every quarter. Range requests return HTTP 206 and the requested 1,024 bytes.

I played and sought the cabin clip from quarter 1, tower top from quarter 2, gallery from quarter 3 and save room from quarter 4 in the published page. Every player reported 640 by 480, decoded frames, an advancing playback time and no media error. Changing scenes paused the previous player. The weather station's no-footage scene has no player.

Desktop at 1,280 pixels and mobile at 390 pixels show the visit labels, posters and controls. The mobile videos occupy one column at 358 pixels with no page overflow. The shared navigation and research index card remain. All four quarters' final clips pass an ffmpeg decode with `-xerror` after the damaged source tails are removed.

The source checks pass: 27 plan, supply, enemy and storyboard tests, including 12 storyboard tests. Strict TypeScript checks and the platform boundary check pass. `verify-clips.py` repeats the published HTTP checks.

## Review correction

The evidence review caught ridge intro frames in the first quarter 4 booth clip. The matcher had compared only rooms in the logged route, which omitted the boot intro. It now keeps the ridge render as a competing match. The regenerated booth clip starts at 29.967 seconds and its first room match is at 33 seconds. I viewed the first six seconds of the rebuilt clip. They show the door and then the booth, with no ridge footage. A source test protects that checked start. The same comparison refined several outdoor fades. Every other clip still starts before its earlier matched entry frame, so those changes retain the room entrances.

The final duration check exposed millisecond rounding in packet-copy seeks. A rounded-down keyframe time could select the preceding GOP and add a second of lead-in. Seeking one millisecond past the stored time fixes that, and 46 affected clips were regenerated. All 142 published clips then loaded metadata in the browser at 640 by 480. Every duration differs from its manifest span by less than one second. The timestamped check includes the corrected booth clip.

## Ridge review, 21 October 2026

The ridge now uses [its scene review clip](https://home.arpa/research/rebecca-storyboard/clips/ridge-review-20261021-bb38ef47.mp4).
The other 141 visits and all four quarter source records are unchanged.
The new source is `recordings/ridge-20261021194342.mp4`, SHA-256
`bb38ef47e1e7fcadca2181c929ae7d3a4c9b639949a143e8fd9dad1e3baf720f`.
Its event log is beside it as `ridge-review-20261021-bb38ef47.json`.
The Windows build was commit `281d076`, deployed with the rebuilt REB overlay
on port 7811. The run used NEW GAME, Rebecca's card and normal damage.

I extracted and viewed source frames at 12, 23, 37, 43, 48, 52, 58, 63, 66,
68, 71, 74, 76, 78 and 80 seconds. They show Rebecca's card, the dawn
narration, all four opening lines, the mansion across the forest, the new
edge check, the west boulder pass, camera 2's rock face and trail, the walk
transition, and Rebecca on the mountain trail. The grass animation remains;
there are no birds or fire in the ridge. The clip uses source seconds
11.6 to 80.0, with its poster at 58.0. Its duration is 68.4 seconds.
The source's damaged final packet stays outside that span.

The recording checks the opening flag, both cameras, the trail arrival,
normal damage mode and the exact starting kit: Beretta 15, knife 0, four
empty slots. The existing `tests/ridge.ts` check also passed at 88/88 HP.
The full render's coverage check reports 2.6% lost floor. The floor bounds,
rock collision, camera floors, depth occluders and masks were rebuilt from
the new scene. Fifteen mask, occluder and animation source tests pass.

Contact sheets for both cameras are published as
[before](https://home.arpa/research/rebecca-storyboard/review/ridge-before.png)
and [after](https://home.arpa/research/rebecca-storyboard/review/ridge-after.png).
The checked [video frame sheet](https://home.arpa/research/rebecca-storyboard/review/ridge-recording-frames.jpg)
is beside them. The full render inputs are saved in the private assets
repository at commit `6ce866f`.

The published page and clip were checked in a separate incognito browser
tab. Both camera images loaded. Playback and seeking decoded 640 by 480
frames with advancing time and no media error. All 284 clip and poster
URLs passed the HTTP check, along with ranged GET checks for the existing
quarters. The new ridge clip also passed a ranged GET and full decode.
The owner's browser and localStorage were not used.

This run covers the ridge and its exit. Act 1 combat with the reduced
ammunition has not been played. Its budget is 15 loaded rounds, no spare
rounds or ammo pickups, four crows, three adders and one dog. No supplies
in other rooms were changed. The lab recordings have no audio; the lab
build also lacks the optional rendered music themes.

## Cabin, shed and booth review, 21 October 2026

The cabin clip comes from `record-scene.ts lookout`, started from a played
yard-to-cabin checkpoint, in normal damage mode. It passed. The checked
frames show the typewriter on the desk under the north window, the desk
chair beside the desk, the pot-belly stove with its fire, the folded rug
corner, the logbook taken from the corner table, and the item sparkle on
the shed key's board past the hat pegs. The route leaves the key on its
hook. Taking it and then entering the yard crashes main in
`render_entity` as the dog spawns from the `cut-dog` event script; the
same crash happens with the overlay built for the ridge review, so it is
not caused by these scenes. A quarter-one playthrough took the logbook,
the spray and the key at their new zones before reaching that crash.

The shed and the booth can only be reached past that crash, so they have
no new storyboard clip. Their scenes were checked by booting the game
straight into each room on the lab and capturing frames. Those frames are
debug boots, not a played route. The shed bulb stutters twice in its
6.4 second loop and the booth's strip light dips once in its 6.4 second
loop, measured from the captured video's brightness.

Sheets: [cabin](https://home.arpa/research/rebecca-storyboard/review/cabin-before-after.png),
[shed](https://home.arpa/research/rebecca-storyboard/review/shed-before-after.png),
[booth](https://home.arpa/research/rebecca-storyboard/review/booth-before-after.png),
[cabin recording frames](https://home.arpa/research/rebecca-storyboard/review/cabin-recording-frames.png)
and [shed and booth debug-boot frames](https://home.arpa/research/rebecca-storyboard/review/shed-booth-debug-boot-frames.png).
Coverage: cabin 3.7%, shed 0.0%, booth 4.5% of the floor lost.

## Shed and booth recorded in play, 22 October 2026

With the yard dog fix from [#21](https://github.com/joe-lloyd/resident-evil-pc-decomp/pull/21) on main, both rooms are reached by playing, in normal
damage mode. From the played cabin checkpoint, the harness ran the cabin
and dog stretches of `day.ts`: she took the key, the dog came out and
died after 11 shots, and the spray healed her. She then walked into the
shed, and `record-scene.ts shed` recorded the room and the way back out
to the yard. From that yard checkpoint, the winch stretch and the doors
through the gorge and the platform took her into the booth, and
`record-scene.ts booth` recorded it. Neither run crashed.

The checked shed frames show the packed tool walls, the crank taken into
her bag, the bulb up under the roof and the door's open animation out to
the yard. The checked booth frames show the footlocker under the phone
with RE1's lid sitting on it, camera 0 with no grey block, the typewriter
behind her at the desk's end, and the door out to the platform. The booth
route's camera checks were wrong for its two cameras and now walk her to
the north-west for camera 0 and the south-east for camera 1.

The new clips replace the shed's and the booth's three quarter clips each.
