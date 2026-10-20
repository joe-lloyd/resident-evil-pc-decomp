"""The head of Camp 4's log flume, above the gorge, at noon under cloud.

What it tells: the flume carries logs from the mill pond down the mountain
to the gorge. Its trough starts here, at a headbox fed from the pond,
crosses a plank deck and runs off over the edge on trestles that grow
taller and taller as the ground falls away into the valley. The men knew a
way off the mountain the foreman had forbidden: NO RIDING, says the sign.
Two flume boats were tied at the head. One rope is cut and its boat gone,
and there is blood on the deck by that cleat and a handprint on the
trough's lip: somebody went down hurt. In the water a cap and a mitten are
caught against the trough's side. The other boat is still tied up, bobbing
in the current. A ladder goes down a trestle into the drop, for the men
who kept it mended. A player should work out that the flume goes down, and
that the boat is a way to ride it.

Metres: she walks x 2-15, y 5-12.4 on the ground and the deck, and a narrow
catwalk out over the drop along the trough's west side, x 8.0-9.0, y 2-5.
The path from the pond comes in at the south edge, x 5.4-7.6. The trough
runs north along x 9.0-10.0 from the headbox (x 8.4-10.6, y 11.6-13.0) to
the edge at y 5 and on down the mountain. North of y 5 the ground drops
away. The boat is tied at x 9.5, y 8.0; the touch to ride is on the deck
beside it, x 7.9-8.9, y 7.4-8.6.

Moving: the water in the trough and the headbox, the boat, the cap and the
mitten bobbing, the cut rope's end, the grass.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import reb  # noqa: E402
import kit  # noqa: E402
from kit import mat  # noqa: E402
from mathutils import Vector, noise  # noqa: E402

X0, X1, Y0, Y1 = 2.0, 15.0, 2.0, 12.4
EDGE_Y = 5.0
TROUGH = (9.0, 10.0)        # inner walls (x)
TX = 9.5
HEADBOX = (8.4, 10.6, 11.6, 13.4)
CATWALK = (8.0, 9.0)
DECK = (5.0, 14.0, 5.0, 11.6)
BOAT = (9.5, 8.0)
WATER_Z = -0.22


def height(x, y):
    """The clearing flat; north of the edge the mountain falls away steeply."""
    n = noise.noise(Vector((x * 0.25, y * 0.25, 6.0)))
    if y > EDGE_Y - 0.4:
        h = -0.04 + 0.03 * n
        if not (X0 - 0.5 < x < X1 + 0.5) or y > Y1 + 0.5:
            h += 0.5 * n + max(0.0, y - Y1 - 0.5) * 0.25 + max(0.0, X0 - 0.5 - x, x - X1 - 0.5) * 0.2
        return h
    d = EDGE_Y - 0.4 - y
    return -0.04 - d * 1.15 - 0.012 * d * d + 1.5 * n * min(1.0, d / 5.0)


def trough_z(y):
    """The top of the trough's walls: level over the deck, then down the mountain."""
    if y >= EDGE_Y:
        return 0.1
    d = EDGE_Y - y
    return 0.1 - d * 0.16 - 0.0008 * d * d


def settle(ob, at, rot):
    """Bake a joined object's parts where they were built, then place it."""
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.location = at
    ob.rotation_euler = rot
    return ob


def channel(name, m, ys, inner=1.0, depth=0.6, thick=0.07):
    """The trough: a U of planks along x = TX through the ys given (north is
    smaller y), its walls' top at trough_z(y). One mesh."""
    w = inner / 2
    prof = [(-w - thick, 0.0), (-w - thick, -depth - thick), (w + thick, -depth - thick), (w + thick, 0.0), (w, 0.0), (w, -depth), (-w, -depth), (-w, 0.0)]
    verts, faces = [], []
    for y in ys:
        z = trough_z(y)
        for px, pz in prof:
            verts.append((TX + px, y, z + pz))
    n = len(prof)
    for i in range(len(ys) - 1):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            faces.append((a, b, b + n, a + n))
    faces.append(tuple(range(n)))
    return reb.mesh_object(name, verts, faces, m, smooth=False)


def flume_boat(name, m, at, rot):
    """A flume boat: a V-hulled box of planks, open on top, its bow pointed."""
    L, W, D = 2.1, 0.8, 0.42
    verts, faces = [], []
    sec = []
    for i, x in enumerate((-L / 2, -L / 4, L / 4, L / 2)):
        taper = 0.35 if i == 3 else 1.0
        sec.append([(x, -W / 2 * taper, D), (x, 0.0, 0.0), (x, W / 2 * taper, D)])
    for s in sec:
        verts.extend(s)
    for i in range(len(sec) - 1):
        a = i * 3
        faces.append((a, a + 1, a + 4, a + 3))
        faces.append((a + 1, a + 2, a + 5, a + 4))
    faces.append((0, 2, 1))
    faces.append((9, 10, 11))
    hull = reb.mesh_object(name, verts, faces, m, smooth=False)
    seat = reb.prim("cube", f"{name} seat", m, (-0.2, 0, D * 0.75), (0.12, W * 0.85, 0.04))
    rim = reb.prim("cube", f"{name} gunwale", mat("dark wood"), (0, W / 2 - 0.02, D), (L, 0.05, 0.05))
    rim2 = reb.prim("cube", f"{name} gunwale", mat("dark wood"), (0, -W / 2 + 0.02, D), (L, 0.05, 0.05))
    ob = kit.join(name, [hull, seat, rim, rim2])
    return settle(ob, at, rot)


def build():
    rng = random.Random(54)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("earth")  # forest floor
    room.floor((DECK[0], DECK[2], DECK[1], DECK[3]), "boards")  # the deck
    room.floor((CATWALK[0], Y0, CATWALK[1], DECK[2]), "boards")  # the catwalk over the drop
    room.camera((3.0, 12.6, 3.4), (10.6, 4.6, 0.0), 200, "from the path in: the headbox, the deck, the boat, the trough running off the edge into the valley")
    room.camera((13.6, 5.6, 3.0), (6.4, 11.0, 0.4), 200, "from the north-east corner of the deck: the boat close, the cut rope, the blood, the headbox")
    room.camera((12.8, 14.6, 4.2), (9.0, -1.0, -2.0), 200, "from behind the headbox: down the flume and the trestles into the valley")

    planks = mat("planks")
    wet = reb.mat_surface("Wet planks", [(0.0, (0.03, 0.025, 0.018)), (0.6, (0.08, 0.06, 0.04)), (1.0, (0.06, 0.08, 0.04))], scale=5, rough=0.35, bump=0.5)
    timber = reb.mat_wood("Trestle timber", (0.16, 0.11, 0.07))
    floor_m = reb.mat_surface("Forest floor", [(0.0, (0.05, 0.035, 0.02)), (0.4, (0.11, 0.075, 0.045)), (0.65, (0.15, 0.1, 0.06)), (0.85, (0.07, 0.08, 0.035)), (1.0, (0.05, 0.075, 0.025))], scale=1.2, bump=0.5)
    water = mat("water")
    flume_water = reb.mat_surface("Flume water", [(0.0, (0.01, 0.014, 0.014)), (0.55, (0.03, 0.04, 0.04)), (0.8, (0.2, 0.22, 0.22)), (1.0, (0.45, 0.47, 0.47))], scale=3, rough=0.2, bump=0.4)
    foam = reb.mat_surface("Foam", [(0.0, (0.25, 0.27, 0.27)), (0.6, (0.5, 0.52, 0.52)), (1.0, (0.7, 0.72, 0.72))], scale=10, rough=0.3, bump=0.6)
    rope_m = reb.mat_plain("Rope", (0.32, 0.27, 0.18), 0.9)

    # ---- Ground: the clearing and the mountain falling away north into the valley.
    reb.terrain("Mountainside", floor_m, (-20, 40), (-40, 30), height, step=0.5)
    reb.terrain("Far slope", floor_m, (-60, 80), (-90, 70), lambda x, y: height(x, y) - 0.5, step=4.0)
    kit.path_strip("Path from the pond", reb.mat_plain("Trodden", (0.06, 0.045, 0.03), 0.9), [(6.4, 22.0), (6.5, 16.0), (6.5, 13.4), (6.8, 11.8)], height, width=0.55)
    rv, rf = [], []
    for (x, y, r) in ((3.4, 4.6, 1.4), (14.8, 4.4, 1.6), (6.4, 4.0, 1.0), (12.2, 3.8, 1.1), (1.0, 8.0, 1.2), (17.0, 9.0, 1.3)):
        reb.boulder(rng, (x, y, height(x, y) - 0.2), r, rv, rf)
    reb.mesh_object("Rocks at the lip", rv, rf, mat("rock"))

    # ---- The deck: planks round the trough's head, a rail along its edge over the drop.
    dx0, dx1, dy0, dy1 = DECK
    for a0, a1 in ((dx0, TROUGH[0] - 0.07), (TROUGH[1] + 0.07, dx1)):
        reb.prim("cube", "Deck", planks, ((a0 + a1) / 2, (dy0 + dy1) / 2, -0.06), (a1 - a0, dy1 - dy0, 0.12))
    for x in [dx0 + 0.2 + k * 0.2 for k in range(int((dx1 - dx0) / 0.2))]:
        reb.prim("cube", "Deck seam", reb.mat_plain("Seam", (0.02, 0.015, 0.01), 0.9), (x, (dy0 + dy1) / 2, 0.001), (0.012, dy1 - dy0, 0.002))
    for x in (dx0 + 0.2, (dx0 + TROUGH[0]) / 2, TROUGH[0] - 0.2, TROUGH[1] + 0.2, (TROUGH[1] + dx1) / 2, dx1 - 0.2):
        kit.rod("Deck post", timber, (x, dy0 - 0.1, -3.0), (x, dy0 - 0.1, 0.0), 0.12, 8)
    rails = []
    for (a0, a1) in ((dx0, CATWALK[0]), (TROUGH[1] + 0.1, dx1)):
        for z in (0.5, 1.0):
            rails.append(kit.rod("Deck rail", timber, (a0, dy0 + 0.05, z), (a1, dy0 + 0.05, z), 0.035, 6))
        for x in (a0 + 0.1, (a0 + a1) / 2, a1 - 0.1):
            rails.append(kit.rod("Rail post", timber, (x, dy0 + 0.05, 0.0), (x, dy0 + 0.05, 1.05), 0.045, 6))
    reb.wall(reb.prim("cube", "West rail footprint", None, ((dx0 + CATWALK[0]) / 2, dy0 + 0.05, 0.5), (CATWALK[0] - dx0, 0.12, 1.0))).hide_render = True
    reb.wall(reb.prim("cube", "East rail footprint", None, ((TROUGH[1] + dx1) / 2, dy0 + 0.05, 0.5), (dx1 - TROUGH[1], 0.12, 1.0))).hide_render = True
    # The catwalk out over the drop beside the trough, and its rail.
    cx0, cx1 = CATWALK
    for k in range(int((EDGE_Y - Y0 + 1.0) / 0.2)):
        y = EDGE_Y - 0.1 - k * 0.2
        reb.prim("cube", "Catwalk plank", planks, ((cx0 + cx1) / 2, y, -0.03), (cx1 - cx0, 0.18, 0.06))
    for y in (EDGE_Y - 0.2, 3.4, 1.8):
        kit.rod("Catwalk post", timber, (cx0 + 0.05, y, 0.0), (cx0 + 0.05, y, 1.05), 0.04, 6)
        kit.rod("Catwalk strut", timber, (cx0 + 0.05, y, -0.05), (TX, y, -2.5), 0.05, 6)
    kit.rod("Catwalk rail", timber, (cx0 + 0.05, EDGE_Y, 1.0), (cx0 + 0.05, 0.9, 0.95), 0.035, 6)
    reb.wall(reb.prim("cube", "Catwalk rail footprint", None, (cx0 + 0.05, (Y0 + EDGE_Y) / 2, 0.5), (0.1, EDGE_Y - Y0, 1.0))).hide_render = True

    # ---- The trough: level across the deck, then down the mountain on trestles.
    ys = [Y1 - 1.4 - k * 0.5 for k in range(int((Y1 - 1.4 - EDGE_Y) / 0.5) + 1)] + [EDGE_Y - k * 1.5 for k in range(1, 50)]
    channel("Flume trough", wet, ys)
    wv, wf = [], []
    for i, y in enumerate(ys):
        z = trough_z(y) - 0.32
        wv += [(TROUGH[0] + 0.01, y, z), (TROUGH[1] - 0.01, y, z)]
    for i in range(len(ys) - 1):
        wf.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    reb.mesh_object("Flume water", wv, wf, flume_water)
    reb.wall(reb.prim("cube", "Trough footprint", None, (TX, (Y0 + HEADBOX[2]) / 2, 0.4), (TROUGH[1] - TROUGH[0] + 0.14, HEADBOX[2] - Y0, 0.8))).hide_render = True
    reb.mask(bpy.data.objects["Flume trough"])
    for k, y in enumerate([EDGE_Y - 1.0 - k * 4.5 for k in range(14)]):
        top = trough_z(y) - 0.67
        g = height(TX, y) - 0.5
        for s in (-1, 1):
            kit.rod("Trestle leg", timber, (TX + s * (0.8 + 0.08 * (top - g)), y, g), (TX + s * 0.6, y, top), 0.1, 6)
        kit.rod("Trestle cap", timber, (TX - 0.8, y, top), (TX + 0.8, y, top), 0.08, 6)
        for z in [g + (top - g) * f for f in (0.33, 0.66)]:
            span = 0.6 + 0.08 * (top - z) + 0.1
            kit.rod("Trestle girt", timber, (TX - span, y, z), (TX + span, y, z), 0.06, 6)
        if top - g > 3:
            kit.rod("Trestle brace", timber, (TX - 0.6 - 0.08 * (top - g), y, g + 0.3), (TX + 0.6, y, top - 0.2), 0.05, 6)
    # The ladder down the first trestle, for the men who kept it mended.
    lx, ly = TX + 0.95, EDGE_Y - 1.0
    for s in (-0.22, 0.22):
        kit.rod("Ladder rail", timber, (lx, ly + s, 0.0), (lx + 0.3, ly + s, height(lx, ly) - 0.2), 0.03, 6)
    for k in range(int(-height(lx, ly) / 0.3)):
        z = -0.15 - k * 0.3
        t = z / (height(lx, ly) - 0.2)
        kit.rod("Ladder rung", timber, (lx + 0.3 * t, ly - 0.22, z), (lx + 0.3 * t, ly + 0.22, z), 0.018, 5)
    kit.rod("Ladder top, grab", timber, (lx, ly - 0.22, 0.0), (lx, ly - 0.22, 1.0), 0.03, 6)
    kit.rod("Ladder top, grab", timber, (lx, ly + 0.22, 0.0), (lx, ly + 0.22, 1.0), 0.03, 6)

    # ---- The headbox: a plank tank fed from the pond, water spilling into the trough.
    hx0, hx1, hy0, hy1 = HEADBOX
    for ob in kit.walls(hx0, hy0, hx1, hy1, 1.6, wet, openings=[("n", TROUGH[0], TROUGH[1], 0.0, 1.0)], thick=0.1, name="Headbox"):
        ob.location.z -= 0.6
        reb.mask(reb.wall(ob))
    reb.prim("cube", "Headbox water", water, ((hx0 + hx1) / 2, (hy0 + hy1) / 2, 0.75), (hx1 - hx0, hy1 - hy0, 0.02))
    reb.prim("cyl", "Pipe from the pond", mat("rust"), ((hx0 + hx1) / 2, hy1 + 3.0, 0.8), (0.5, 0.5, 6.0), rot=(math.pi / 2, 0, 0), segments=16)
    reb.prim("cube", "Spill", foam, (TX, hy0 - 0.1, 0.2), (0.95, 0.3, 0.9), rot=(0.4, 0, 0))
    for k in range(3):
        kit.splat(f"Foam in the trough {k}", foam, (TX + rng.uniform(-0.2, 0.2), hy0 - 0.5 - k * 0.7, WATER_Z + 0.02), 0.3, seed=k, stretch=(0.8, 1.6), lumps=0.5)
    # Its ladder, up to the gate wheel on top.
    for s in (-0.22, 0.22):
        kit.rod("Headbox ladder", timber, (hx0 - 0.2, (hy0 + hy1) / 2 + s, 0.0), (hx0 - 0.05, (hy0 + hy1) / 2 + s, 1.3), 0.03, 6)
    for k in range(4):
        z = 0.3 + k * 0.3
        kit.rod("Headbox rung", timber, (hx0 - 0.2 + 0.15 * z / 1.3, (hy0 + hy1) / 2 - 0.22, z), (hx0 - 0.2 + 0.15 * z / 1.3, (hy0 + hy1) / 2 + 0.22, z), 0.018, 5)
    reb.prim("cyl", "Headgate wheel", mat("rust"), ((hx0 + hx1) / 2, hy0 + 0.25, 1.4), (0.6, 0.6, 0.04), rot=(math.pi / 2, 0, 0), segments=16)

    # ---- The boats: one still tied, bobbing in the current; one gone, its rope cut, blood by its cleat.
    boat_m = reb.mat_surface("Boat paint", [(0.0, (0.2, 0.05, 0.03)), (0.6, (0.32, 0.08, 0.04)), (1.0, (0.16, 0.1, 0.06))], scale=6, rough=0.6, bump=0.3)
    boat = flume_boat("Flume boat", boat_m, (BOAT[0], BOAT[1], WATER_Z - 0.17), (0, 0, -math.pi / 2))
    for y in (BOAT[1] - 0.5, 10.3):
        reb.prim("cube", "Cleat", mat("iron"), (TROUGH[0] - 0.35, y, 0.04), (0.08, 0.3, 0.06))
    kit.rod("Mooring rope", rope_m, (TROUGH[0] - 0.35, BOAT[1] - 0.5, 0.07), (TROUGH[0] + 0.05, BOAT[1] - 0.7, 0.12), 0.02, 5)
    kit.rod("Mooring rope", rope_m, (TROUGH[0] + 0.05, BOAT[1] - 0.7, 0.12), (BOAT[0] - 0.1, BOAT[1] - 0.9, WATER_Z + 0.2), 0.02, 5)
    cut = reb.prim("sphere", "Cut rope knot", rope_m, (TROUGH[0] - 0.35, 10.3, 0.08), (0.06, 0.06, 0.05))
    cut_end = kit.rod("Cut rope end", rope_m, (0, 0, 0), (0.45, -0.05, -0.12), 0.02, 5)
    cut_end.parent = cut
    for k in range(3):
        reb.prim("cube", "Frayed strand", rope_m, (0.47 + 0.02 * k, -0.05 + 0.02 * (k - 1), -0.13), (0.06, 0.006, 0.006), rot=(0, 0.3, 0.4 * (k - 1))).parent = cut
    kit.splat("Blood by the cleat", mat("blood"), (TROUGH[0] - 0.7, 10.2, 0.003), 0.3, seed=21, stretch=(1.4, 0.9))
    kit.drag_trail("Blood to the cleat", mat("old blood"), [(6.6, 12.6), (7.0, 11.6), (7.8, 10.8), (8.4, 10.3)], width=0.25, seed=22, z=0.0)
    kit.splat("Hand on the lip", mat("blood"), (TROUGH[0] - 0.04, 10.0, 0.11), 0.07, rot=(0, 0, 0.3), seed=23)
    reb.prim("cube", "Smear down the trough", mat("old blood"), (TROUGH[0] - 0.075, 10.05, -0.15), (0.004, 0.06, 0.4))
    # Caught in the water against the trough's side: a cap and a mitten.
    cap_m = reb.mat_plain("Cap", (0.25, 0.05, 0.04), 0.8)
    cap = reb.prim("sphere", "Snagged cap", cap_m, (TROUGH[1] - 0.15, 6.4, WATER_Z + 0.02), (0.2, 0.17, 0.07), segments=12)
    reb.prim("cube", "Cap peak", cap_m, (0.1, 0, -0.02), (0.1, 0.12, 0.01)).parent = cap
    mitten = reb.prim("sphere", "Snagged mitten", reb.mat_stripes("Mitten", [(0.5, 0.45, 0.35), (0.25, 0.05, 0.04)], across=30, axis="Y"), (TROUGH[0] + 0.12, 5.6, WATER_Z + 0.02), (0.12, 0.22, 0.05), rot=(0, 0, 0.3), segments=10)
    reb.prim("cube", "Nail it caught on", mat("rust"), (TROUGH[0] + 0.02, 5.6, WATER_Z + 0.04), (0.04, 0.01, 0.01))
    # A duffel dropped by the boats, a lantern, a pike pole, the sign.
    reb.prim("cyl", "Duffel bag", mat("canvas"), (6.2, 9.4, 0.17), (0.34, 0.34, 0.8), rot=(math.pi / 2, 0, 1.0), segments=14)
    kit.rod("Duffel strap", mat("black"), (5.9, 9.2, 0.34), (6.5, 9.6, 0.34), 0.012, 4)
    lamp, lamp_light, flame = kit.lantern("Lantern on the deck", (12.4, 10.6, 0.0), energy=4)
    kit.rod("Pike pole", timber, (11.0, 6.0, 0.03), (13.4, 7.4, 0.03), 0.025, 6)
    kit.rod("Sign post", timber, (7.2, 11.5, -0.1), (7.2, 11.5, 2.0), 0.05, 6)
    reb.prim("cube", "Flume sign", mat("white paint"), (7.2, 11.53, 1.7), (1.2, 0.04, 0.5))
    kit.text("Flume sign words", "CAMP 4 FLUME", mat("black"), (7.2, 11.555, 1.8), size=0.11, rot=(math.pi / 2, 0, math.pi))
    kit.text("Flume sign words 2", "NO RIDING", mat("red paint"), (7.2, 11.555, 1.6), size=0.14, rot=(math.pi / 2, 0, math.pi))

    # ---- The view down: the valley, its ridges in the haze, the forest round the clearing.
    kit.vista(rng, (TX, Y0 - 20), (0.0, -1.0), below=-80.0)
    cams = ((3.0, 12.6), (13.6, 5.6), (12.8, 14.6))

    def keep_out(x, y):
        if X0 - 1.0 < x < X1 + 1.0 and EDGE_Y - 1.5 < y < Y1 + 0.8:
            return True
        if abs(x - 6.5) < 1.2 and y > Y1:
            return True
        if abs(x - TX) < 4.5 + 0.08 * max(0.0, EDGE_Y - y) and y < EDGE_Y:
            return True
        if abs(x - TX) < 3 and y > Y1 and y < Y1 + 8:
            return True
        return any((x - cx) ** 2 + (y - cy) ** 2 < 9 for cx, cy in cams)
    kit.forest(rng, height, keep_out, (-20, -40, 40, 30), count=230, spacing=1.8, tall=(13, 22), ferns=90, needles=700, dead=0.1)
    fv, ff = [], []
    for _ in range(70):
        x, y = rng.choice((rng.uniform(X0 - 4, DECK[0]), rng.uniform(DECK[1], X1 + 5))), rng.uniform(EDGE_Y + 0.5, Y1 + 5)
        reb.fern(rng, (x, y, height(x, y)), rng.uniform(0.35, 0.6), fv, ff)
    ferns = reb.mesh_object("Ferns in the clearing", fv, ff, mat("ferns"))

    def verge(r_):
        while True:
            x, y = r_.uniform(X0 - 3, X1 + 3), r_.uniform(EDGE_Y - 0.2, Y1 + 3)
            if not (DECK[0] - 0.1 < x < DECK[1] + 0.1 and DECK[2] - 0.1 < y < DECK[3] + 0.1) and not (HEADBOX[0] - 0.3 < x < HEADBOX[1] + 0.3 and y > HEADBOX[2] - 0.3):
                return x, y
    grass = kit.meadow(rng, 2600, verge, height)

    # ---- Light: noon under cloud, the valley lost in mist below.
    sun = kit.time_light("noon", sun_heading=200, sun_energy=2.4, mist=((TX, -40.0, -30.0), (160.0, 100.0, 70.0), 0.006),
                         sky=((0.6, 0.62, 0.63), (0.4, 0.42, 0.45), 1.15))
    sun.data.angle = math.radians(18)
    sun.rotation_euler[0] = math.radians(30)

    anim = kit.Anim(16)
    anim.ripple(water, speed=2)
    # Foam riding the current north down the trough, from the headbox to the edge, round once a loop.
    flecks = []
    for k in range(6):
        f = kit.splat(f"Foam on the current {k}", foam, (TX, 0.0, WATER_Z + 0.012), 0.16, seed=40 + k, stretch=(0.7, 1.8), lumps=0.5)
        flecks.append((f, k / 6, rng.uniform(-0.2, 0.2)))
    span = (HEADBOX[2] - 0.4, EDGE_Y - 4.0)

    def current(k):
        for f, off, dx in flecks:
            t = (k / anim.frames + off) % 1.0
            y = span[0] + (span[1] - span[0]) * t
            f.location = (TX + dx, y, trough_z(y) - 0.32 + 0.015)
    anim.custom(current)
    anim.bob(boat, height=0.025, speed=2)
    anim.custom(lambda k: setattr(boat.rotation_euler, "x", math.radians(1.5) * math.sin(anim.phase(k))))
    anim.bob(cap, height=0.02, speed=2)
    anim.bob(mitten, height=0.015, speed=1)
    anim.swing(cut, axis=2, degrees=10)
    anim.flicker(lamp_light, flame, depth=0.3, dropouts=1)
    anim.sway(grass, amount=0.06)
    anim.sway(ferns, amount=0.02)

    # ---- What the game needs.
    room.void((X0, Y0, CATWALK[0], EDGE_Y))
    room.void((TROUGH[1] + 0.1, Y0, X1, EDGE_Y))
    room.door("pond", (5.4, Y1 - 0.6, 7.6, Y1), arrive=(6.4, 10.9), face=(0, -1))
    room.door("bridge", (7.9, BOAT[1] - 0.6, TROUGH[0] - 0.05, BOAT[1] + 0.6), arrive=(6.6, BOAT[1]), face=(-1, 0))
    room.check((TROUGH[0] - 1.0, 9.8, TROUGH[0], 10.8), "A cleat with a rope cut through. Blood all round it.\nSomebody took a boat down hurt.")
    room.check((TROUGH[1], 5.9, TROUGH[1] + 0.8, 6.9), "A cap, caught in the water against the side.")
    room.check((CATWALK[0], 5.0, CATWALK[1], 6.0), "A mitten, snagged on a nail. The water's freezing.")
    room.check((7.0, 11.0, 8.2, 11.8), "CAMP 4 FLUME. NO RIDING.\nSomebody didn't listen.")
    room.check((CATWALK[0], Y0, CATWALK[1], 3.0), "It goes all the way down. The trestles get taller and taller.\nI can't see the bottom for the mist.")
    room.check((5.6, 9.0, 6.8, 9.8), "A duffel bag, packed and dropped.")
    room.export(anim)


build()
