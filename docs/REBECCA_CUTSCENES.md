# The cutscenes of Rebecca's day

Her cutscenes are made the way RE1 makes its own. Each is an event script
(EVT) that a room's main procedure starts with `evt_exec`. It runs a frame at
a time beside the game. It cuts the camera, walks people about, plays their
animations and shows lines from the room's messages. The model is the scene
where Chris meets Rebecca in the mansion's save room, `ROOM1000`: letterbox
bars and her controls off at the start, both back and the camera free at the
end.

A scene is not written as script by hand. It is described in TypeScript, and
`tools/rebecca/day/scripts.ts` writes it into its room's script:

- `tools/rebecca/day/cutscene.ts` has the types for a scene, its trigger,
  its people and its beats, and `compileScene`, which turns a scene into
  script.
- `tools/rebecca/day/cutscenes.ts` has the scenes, most important first, and
  the flag each one takes.
- `tools/harness/tests/cutscenes.ts` plays them in the game.

The event script format is in retro-archive-explorer's
`docs/EVT_FORMAT.md`. `node $RAE_CLI script <room.rdt>` prints any room's
procedures, which is the quickest way to read one of RE1's own scenes.

## Make a scene

1. Add it to `CUTSCENES` in `day/cutscenes.ts`. Put new scenes at the end,
   so the scenes before keep their flags.
2. Write the room's script: `node tools/rebecca/day/scripts.ts`. It throws if
   a walk leaves the floor, a person is not in the cast, or the room has no
   door, check or item the scene names.
3. Run the unit tests. `day/cutscenes.test.ts` checks that every line fits
   the message box and that each scene's flag belongs to its room alone.
4. Build the overlay, deploy it, and play the scene:

   ```
   OVERLAY=<out> PORT=<port> RE1_LAB_GAME_DIR='...' node tools/harness/tests/cutscenes.ts <scene id>
   ```

   The test starts the scene from a checkpoint, takes a picture at each line
   and each camera cut, and checks that she has her controls back afterwards
   and that the scene doesn't run twice. Look at the pictures in
   `/tmp/rebecca-cutscenes/<scene id>/`.
5. Mark its row in `tools/rebecca/plan/todo.ts` done once it passes and the
   pictures look right.

Here is a short scene, the view from the lookout tower:

```ts
{
  id: 'cut-tower',
  room: 'tower-top',
  trigger: { on: 'enter', from: 'tower-stairs' },
  beats: [
    cut(3),
    wait(40),
    say('From up here I can see the whole valley.'),
    say("Smoke in the trees. That's where we came down."),
    say('Past it, a roof. A big old house in the forest.'),
  ],
}
```

## What starts a scene

| Trigger | When it runs |
| --- | --- |
| `{ on: 'enter', from }` | The first time she is in the room. With `from`, a room slug, she is stood at the arrival of the door from that room before the first beat. Without it, she stays where she is (the ridge, where a new game starts). |
| `{ on: 'check', check }` | She presses action at the room's check whose text starts with `check`. The scene's `after` is what that check says once the scene has run. |
| `{ on: 'zone', zone }` | She walks into a part of the floor. |
| `{ on: 'step', step }` | A puzzle step of `day/events.ts` has happened and she is in the room. The scene waits for the step's own line to close first. |

A scene runs once. Its FG_COMMON flag is set as it starts.

## Beats

| Beat | What it does |
| --- | --- |
| `cut(n)` | Cut to the room's camera `n`, numbered as the room's `scene.py` calls `room.camera`. |
| `place(who, spot)` | Stand her or a person somewhere at once. |
| `walk(who, spot)`, `run(who, spot)` | Walk or run in a straight line to a spot. The scene waits until they get there. |
| `face(who, spot)` | Turn on the spot to face a point. The scene waits. |
| `anim(person, n, loop)` | Play one of a person's animations. The scene waits for its end, unless it loops. |
| `say(text)` | Her line. A thought is plain; speech is in quotes. The scene waits until the player closes it. |
| `line(person, text)` | A person's line, in quotes. A person in the room gestures as they talk; a voice on the phone does not. |
| `wait(frames)` | Wait, at 30 frames a second. |
| `fade('black')`, `fade('clear')` | Fade the screen to black, or back. |
| `shake(on)` | Shake the screen, or stop. |
| `gone(person)` | Take a person out of the room. |
| `give(step)` | Hand her a key item lying in the room, by its plan step, with the game's own pickup screen. |
| `scd(...lines)` | Raw script lines, run as the scene reaches them. The crawl's gear loss uses this. |

Positions are game units: a scene's metres times 1700, its x and y becoming x
and z. An angle of 0 faces +X, 1024 faces -Z, 2048 faces -X and 3072 faces +Z.

## People

A scene's `cast` lists the people in it: Hal, Dana and Chris, entities 34, 33
and 32, as `docs/REBECCA_NPC.md` builds them. Each stands at `at` until the
scene runs, in a `pose` or idle. With `after`, they stay in the room after the
scene, at that spot and pose. Hal is left lying dead on the ore cart this way.
The people take enemy slots 6 and 7, after the room's foes, so a scene holds
two people at most.

## Rules

- A line is one page of two message lines at most, 26
  characters to a line. A `\n` in a line starts a new page, so leave line
  breaks to the wrapping.
- Walks keep to the floor. The engine walks a person in a straight line,
  and one that meets a wall never arrives, so the scene would wait for ever.
  `compileScene` checks each walk against the room's floor, 400 units clear
  of walls, gaps and the room's edge, and out of the doors. It knows where a
  walker starts from the cast, the door she came in by and earlier `place`
  beats. A walk from an unknown place is not checked, so `place` her first. The
  save room has no record of its floor, so its walks are not checked.
- In a room with an `enter`
  or `zone` scene, the room's enemies come only once the scene has run, on her
  next visit. A `check` or `step` scene keeps the room's enemies. They keep
  moving during its lines, because a scene's line doesn't pause the game. Keep
  such a scene short, or put it in a room with no enemies near.
- The end of every scene puts her back to standing,
  clears the bars, frees the camera and gives her controls back. A person who
  leaves is stood far out of sight rather than removed, since clearing the
  slot leaves the enemy count one too high.

## Rooms whose scripts are written by hand

Most rooms' scripts are written whole by `scripts.ts`. RE1's own save room
and the ridge have hand-written scripts, listed in `SCRIPTED` in
`scripts.ts`. Their scenes go between markers in the script, and their lines
after the room's own messages:

```
// CUTSCENES INIT (day/scripts.ts writes these)
// END CUTSCENES INIT
...
// CUTSCENES MAIN (day/scripts.ts writes these)
// END CUTSCENES MAIN
...
// CUTSCENE EVENTS (day/scripts.ts writes these, to the end of the file)
```

To give another hand-written room a scene, add those markers to its script
and the room to `SCRIPTED`, with the number of its own messages and the
first room action id and FG_ROOM bit its script leaves free.

## The scenes and their flags

The scenes have FG_COMMON 115-129, which no shipped room script and no engine
flag uses. They take them in the order of `CUTSCENES`.

| Flag | Scene | Room | Trigger |
| --- | --- | --- | --- |
| 115 | `cut-phone` | booth | checking the handset |
| 116 | `cut-partner` | woods | in from the yard |
| 117 | `cut-den` | den | in from the woods |
| 118 | `cut-mine-collapse` | gallery | in from the junction |
| 119 | `cut-hal` | gallery | wading up to the ore cart |
| 120 | `cut-kevin` | crash | in from the valley path |
| 121 | `cut-sleep` | save | up through the hatch from the crawl |
| 122 | `cut-gondola` | platform | Hal's key turned in the booth |
| 123 | `cut-pylon` | car | in from the platform |
| 124 | `cut-tower` | tower-top | up from the stairs |
| 125 | `cut-opening` | ridge | a new game |

`cut-sleep` is both tracker rows `cut-sleep` and `cut-chris`. FG_COMMON 36 is
RE1's own "Chris met Rebecca", which `cut-sleep` sets as the old meeting did.

## The added scenes

- `cut-dog`, flag 126, starts in the yard once she takes the shed key.
  Camera 1 looks down the cabin front. The dog spawns after her lines, so
  its AI cannot attack her while she reads. Its old kill flag stays 200.
- `cut-mine-chase`, flag 127, finishes the escape at the mine lift after
  the collapse and Hal's scene. She runs into the cage and turns towards
  the junction. The junction's existing spinners supply the playable
  run. There is no staged pursuit across room loads.
- `cut-credits`, flag 128, follows Chris's departure in the save room.
  These are brief message cards over a fade. A separate credits screen,
  scrolling names, a credits music transition and a return to the title
  still need support outside the current scene format.

Entry scenes may name `requires`, story flags that must have their requested
state before the scene starts. They also wait until the letterbox from any
previous scene clears. The credits use the meeting's completion flag 36,
not its start flag 121, so they cannot interrupt Chris.

- `cut-leave-gear`, flag 129, spans the north leg of the crawl before the
  ladder. Camera 2 looks up the passage. She leaves her pack at the narrow
  turn and walks to the hatch. Item 0x02 and its loaded count are untouched;
  all other weapons, spare ammo and healing leave her six inventory slots.
  Key items stay. The floor and door checks validate the short walk.

The gallery keeps its floor scare and Hal. It no longer removes anything.
Kevin's redundant Beretta pickup is a green herb; the crash still has a clip.
These added scenes and the late loss have not been played in the game.
