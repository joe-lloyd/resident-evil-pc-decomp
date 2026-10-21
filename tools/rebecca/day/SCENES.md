# Building a scene of Rebecca's day

A scene is one room: a Blender script that builds it, renders its cameras
and records what the game needs. The plan says what each room is for
(`tools/rebecca/plan/day.ts`, drawn at https://home.arpa/research/rebecca-plan/).
`booth/scene.py` (an interior) and `platform/scene.py` (an exterior) are the
models to copy.

Before building an existing scene, restore its rendered inputs with
`node tools/rebecca/assets.ts pull` from the repo root.

## The standard

- **Story first.** Before any geometry, write the scene's docstring: what
  happened here, who was here, what they left, and what a player should
  work out from it. Then build the things that tell it. Every room tells
  something.
- **Morbid and lived in.** Real people lived and died here this week. Rooms
  are cluttered and used: plates, clothes, tools, papers, bottles. Things
  went wrong: blood, drag marks, a body or what's left of one, barricades,
  scratches, broken glass, a door forced. Never an empty box.
- **Something moves** in every scene: a flame, a failing bulb, flies, a
  swinging sign, grass, water, smoke, a crow.
- **The hour shows.** The room's hour is in `day/rooms.ts` (KIT_ROOMS).
  Light moodily: deep shadows, a warm lamp, a hard shaft from a window. No
  flat, even light and no blown-out white.
- **Exits read.** A player has to see where they can go: a path through
  the trees, a gate, an open doorway, a ladder.
- **It reads at 320 x 240.** Small detail turns to noise. Big shapes,
  strong silhouettes, a few legible props in each shot.

## The look

Every scene follows the owner's review of the first twenty and the
Resident Evil Zero ending he gave as the reference. `blender/kit.py`
builds it; its section "The RE0 look outdoors" has the usage. An exterior
that sees the horizon needs three calls:

```python
kit.time_light("morning")                                  # the light on the room
kit.overcast_sky()                                         # the sky the cameras see
land = kit.backdrop(eye=(6, -2, 3), toward=(0, 1), spread=160)
```

`backdrop` raises every camera's far plane on its own. `ridge/scene.py`
shows a designed view: its ranges are drawn on camera 0's picture. The
rules:

- **Sky and distance.** Never a flat white, grey or blue backdrop, a plain
  gradient or the edge of the world. Use heavy overcast, grey-blue and
  lilac, with a warm glow at one edge (`kit.overcast_sky`). Below it put
  long, low, rolling ranges fading into haze, with pine forest down every
  slope into the valley mist (`kit.backdrop`). A camera that looks into
  woods sees trunks layered back into the dark and the mist, never sky
  through sparse trees: put `kit.forest` close and dense.
- **Ground.** Paths are bare, trodden dirt (`kit.dirt_path`). A path runs
  on past the edge of every camera; it never stops at the top of the
  screen or at a drop. Ground off the path is grassed with no bald
  patches (`kit.grass_ground` over `kit.mat("grassed earth")`). Tyre
  tracks wander like real ruts (`kit.ruts`).
- **Trees and rocks sit in the ground.** No floating, no discs, nothing
  clipping a slope. `kit.forest` gives trunks roots (`kit.tree_roots`),
  `kit.rocks` sinks boulders, and `kit.rough_log` makes a fallen trunk
  that is not a machined cylinder.
- **Blood soaks in.** `kit.mat("blood")` is dark, matte and patchy. Use it
  sparingly and only where the story needs it. Bodies are few and
  detailed. No dead animals unless a note asks for one.
- **Motion is subtle.** Lights do not swing, flicker is rare, smoke is a
  thin wisp and grass barely moves. No scratch-built crows: use the game's
  crow, or none.
- **Buildings.** Doors are shown closed, and roofs sit on their walls.
  Signs carry no text that does not earn its place. The Spencer mansion is
  `kit.spencer_mansion`: a long two-storey house with a brown mansard roof,
  pointed dormers, a chimney at each end and a gabled, columned centre.
  Pass `far=True` when it stands miles off.

## Steps

1. Write `day/<slug>/scene.py`: the docstring (what it tells, the layout in
   metres with the doors, what moves), then the scene with `blender/kit.py`
   and `blender/reb.py`.
2. Preview it: `node tools/rebecca/day/render.ts --preview <slug>` (seconds),
   then `python3 tools/rebecca/day/sheet.py /tmp/reb-preview/<slug> /tmp/<slug>.png`
   and look at the sheet. Fix what is wrong and look again. Check for:
   - grey nothing through a door or a window, or past the edge;
   - props floating, sunk in the floor or in each other;
   - text facing the wrong way or mirrored;
   - a camera staring at a blank wall, or blocked by a tree or a post right
     in front of the lens;
   - plain surfaces, and the story too small to see.
3. Check she can be seen everywhere she can walk:
   `node tools/rebecca/day/coverage.ts <slug> /tmp/reb-preview/<slug>`. At
   most 5% lost. Move or add a camera if not.
4. Render it fully: `node tools/rebecca/day/render.ts <slug>` (a few minutes).
   This writes `day/<slug>/renders/`.
5. After copying renders back from jellybingus, save them to Forgejo with
   `node tools/rebecca/assets.ts push <slug>`. Name your scenes: a bare
   `push` saves every render in the worktree, other people's scenes too.

## Space and the game's rules

- Metres. Blender x is east and y is south, which is the game's Z; z is up.
  The floor is z = 0 where she walks.
- The walkable floor is `kit.Room(bounds=(x0, y0, x1, y1))`. Keep every
  coordinate of the floor between 0.6 and 19 m (game positions are signed
  16-bit at 1700 units a metre).
- Tag what she can't walk through with `reb.wall(ob)`. Its footprint
  becomes a box (or a circle with `reb.wall(ob, "circle")`). Tag what can
  stand between her and a camera with `reb.mask(ob)`: a table edge, a post,
  a doorframe nearer the lens.
- `room.void(rect)` marks floor inside the bounds that isn't there: a drop,
  deep water.
- **Doors.** `room.door(to, zone, arrive, face)`:
  - `to` is the neighbour's slug.
  - `zone` is where she leaves: about 0.6-1 m deep against the floor's edge,
    or in front of a doorway.
  - `arrive` and `face` are where she stands, and which way she looks, when
    she comes in from that neighbour.
  - Outdoor-to-outdoor doors walk (the dark path between rooms) and fire on
    touch. Doors into or out of a building open and need the action button
    (`walk=False`, which an indoor room gets by default).
  - Keep each arrival at least 0.8 m from every touch zone, and facing away
    from it, or she walks straight back out.
  - Every neighbour named in your brief needs a door. The neighbour's own
    scene gives the arrival on its side.
- `room.check(zone, text)` is something she can examine. The text is in her
  voice: short, plain thoughts, a few lines, `\n` between pages.
  `room.entry` is an optional one-line thought on first coming in.
- **Cameras.** `room.camera(eye, look, fov, note)`:
  - fov 190 to 210 (the lens in tenths of a millimetre).
  - Interiors: up under the ceiling in the corners, about 2.0-2.3 m high.
  - Exteriors: 2.6-4 m high, looking across the floor.
  - Two cameras for a small room, three to five for a big one. Together they
    must cover the floor (step 3).
  - Keep trees and props out from right in front of a lens.
- No enemies, puzzles or pick-ups yet. Items can be in the scene as set
  dressing.

## Pitfalls already met

- **Object count.** Thousands of small objects make Blender crawl (each
  `prim` is an operator call). Put many small things in one mesh: build
  verts and faces and call `reb.mesh_object`. `kit.splat`, `drag_trail`,
  `cracks`, `meadow` and `forest` already do. Keep a scene under about
  1500 objects; the log prints the count.
- **Sky.** Use `kit.time_light(hour)` and then `kit.overcast_sky()`, not
  `reb.gradient_sky`, which paints its below-the-horizon colour across the
  low sky.
- **The edge of the world.** Past an edge or through a window there must be
  something: `kit.backdrop` for the land out to the far ranges, `kit.forest`
  for trees, or a backdrop wall. `kit.vista` is the older, closer valley.
- **Ground fighting a floor.** Keep the terrain a little below a slab or a
  floor that sits on it (the platform drops the ground to -0.4 under its
  slab).
- **Text.** `kit.text` faces -y by default (readable from the south). Turn
  it about z for other walls: `math.pi` to face +y, `-math.pi / 2` to face -x,
  `math.pi / 2` to face +x.
- **Water.** `mat("water")` is dark and glossy, for ponds and streams;
  `Anim.ripple` moves it. On a small puddle its bump turns to black stripes.
  Use a dark, low-roughness stain instead.
