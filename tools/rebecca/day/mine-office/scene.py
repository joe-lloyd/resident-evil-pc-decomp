"""The mine office, cut into the rock off the adit.

What it tells: the shift boss kept his office in a room blasted out of the
rock, closed off from the adit with a front of planks. The mine map is
still pinned to the rock over his desk: the adit, the junction with the
pump house, the lift up to the top, and the old third level, marked
FLOODED. Water comes through the roof and drips into a bucket that has run
over. The candles on the desk and the ledge are new and burning: Hal was
here. His Skyway jacket is over the chair, the cot is pulled out with a
blood-soaked bandage on the blanket, and his drops of blood go to the map
and back out. He looked at where to hide and went on down. An old miner's
helmet sits on the desk with its lamp.

Metres: the floor is x 1.0-4.6, y 1.0-3.8; the rock roof is about 2.4
high. The plank front is the south wall, its door at x 2.4-3.3 out into
the adit. The desk and the map are on the north wall, the cot along the
west wall, the ledge of candles and the old powder boxes on the east wall,
the bucket under the drip in the middle. Where she saves: his typewriter
on the desk, and the item box along the east wall, past the powder boxes.

Moving: the candle flames; drops falling from the roof into the bucket.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
from kit import mat  # noqa: E402
from mathutils import Vector, noise  # noqa: E402

X0, X1, Y0, Y1, H = 1.0, 4.6, 1.0, 3.8, 2.4
DOOR = (2.4, 3.3)
DRIP = (3.35, 2.55)


def rock_face(name, m, origin, u, v, nu, nv, out, depth=0.18, seed=0):
    """A lumpy rock surface over the rectangle origin + s*u + t*v (s, t in 0..1),
    pushed back along `out` by noise so it never bulges into the room much."""
    o, u, v, out = Vector(origin), Vector(u), Vector(v), Vector(out).normalized()
    verts, faces = [], []
    for j in range(nv + 1):
        for i in range(nu + 1):
            p = o + u * (i / nu) + v * (j / nv)
            d = depth * (0.6 + noise.noise(p * 1.4 + Vector((seed, 0, 0))) + 0.35 * noise.noise(p * 4.0 + Vector((0, seed, 0))))
            verts.append(tuple(p + out * max(-0.03, d)))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    return reb.mesh_object(name, verts, faces, m)


def build():
    rng = random.Random(31)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.ground("rock")
    room.camera((4.4, 3.6, 2.05), (2.2, 1.3, 0.8), 200, "high by the door: the desk under the mine map, the candles, the helmet, his jacket on the chair")
    room.camera((1.2, 1.2, 2.05), (3.9, 3.4, 0.4), 205, "high over the cot: the plank front and its door, the candle ledge and the powder boxes, the bucket under the drip")

    rock = kit.dirtied(mat("wet rock"), 0.5, scale=1.2)
    planks = kit.boards("Plank front", (0.15, 0.1, 0.06), width=0.18, grime=0.85)
    floor_m = reb.mat_surface("Rock floor", [(0.0, (0.03, 0.028, 0.025)), (0.5, (0.08, 0.07, 0.06)), (1.0, (0.13, 0.11, 0.09))], scale=2.0, rough=0.6, bump=0.7)
    timber = kit.dirtied(reb.mat_wood("Mine timber", (0.14, 0.095, 0.055)), 0.7)
    paper = reb.mat_surface("Map paper", [(0.0, (0.3, 0.26, 0.17)), (0.6, (0.48, 0.43, 0.3)), (1.0, (0.4, 0.3, 0.18))], scale=6, bump=0.05)
    ink = reb.mat_plain("Ink", (0.04, 0.035, 0.05), 0.5)
    red_ink = reb.mat_plain("Red ink", (0.35, 0.03, 0.02), 0.5)

    # ---- The rock: three walls and the roof, lumpy; the floor; the plank front with its door.
    rock_face("North rock", rock, (X0 - 0.4, Y0, -0.1), (X1 - X0 + 0.8, 0, 0), (0, 0, H + 0.5), 28, 18, (0, -1, 0), seed=1)
    rock_face("West rock", rock, (X0, Y0 - 0.4, -0.1), (0, Y1 - Y0 + 0.8, 0), (0, 0, H + 0.5), 22, 18, (-1, 0, 0), seed=2)
    rock_face("East rock", rock, (X1, Y0 - 0.4, -0.1), (0, Y1 - Y0 + 0.8, 0), (0, 0, H + 0.5), 22, 18, (1, 0, 0), seed=3)
    rock_face("Roof rock", rock, (X0 - 0.4, Y0 - 0.4, H), (X1 - X0 + 0.8, 0, 0), (0, Y1 - Y0 + 0.8, 0), 28, 22, (0, 0, 1), depth=0.22, seed=4)
    reb.prim("cube", "Floor", floor_m, ((X0 + X1) / 2, (Y0 + Y1) / 2, -0.03), (X1 - X0 + 0.8, Y1 - Y0 + 0.8, 0.06))
    d0, d1 = DOOR
    for x0_, x1_ in ((X0 - 0.4, d0), (d1, X1 + 0.4)):
        reb.prim("cube", "Plank front", planks, ((x0_ + x1_) / 2, Y1 + 0.04, H / 2 + 0.1), (x1_ - x0_, 0.06, H + 0.4))
    reb.prim("cube", "Plank front over the door", planks, ((d0 + d1) / 2, Y1 + 0.04, (2.0 + H + 0.3) / 2), (d1 - d0, 0.06, H + 0.3 - 2.0))
    for x in (d0 - 0.06, d1 + 0.06):
        reb.prim("cube", "Door post", timber, (x, Y1 - 0.02, 1.2), (0.12, 0.12, 2.4))
    reb.prim("cube", "Door head", timber, ((d0 + d1) / 2, Y1 - 0.02, 2.04), (d1 - d0 + 0.24, 0.12, 0.08))
    reb.prim("cube", "Door", kit.boards("Plank door", (0.15, 0.1, 0.06), width=0.14, grime=0.8), ((d0 + d1) / 2, Y1 + 0.03, 0.98), (d1 - d0, 0.05, 1.96))
    for z in (0.4, 1.55):
        reb.prim("cube", "Door ledge", timber, ((d0 + d1) / 2, Y1, z), (d1 - d0 - 0.08, 0.03, 0.12))
    reb.prim("sphere", "Door ring", mat("iron"), (d0 + 0.18, Y1 - 0.02, 0.95), (0.07, 0.02, 0.07))
    for x in (1.6, 3.9):
        reb.prim("cube", "Roof prop", timber, (x, Y1 - 0.15, 1.2), (0.16, 0.16, 2.4))
    reb.prim("cube", "Roof beam", timber, ((X0 + X1) / 2, Y1 - 0.15, 2.32), (X1 - X0, 0.18, 0.16))
    reb.prim("cube", "Roof beam 2", timber, ((X0 + X1) / 2, 2.0, 2.35), (X1 - X0 + 0.3, 0.18, 0.16))
    for x in (X0 + 0.1, X1 - 0.1):
        reb.prim("cube", "Beam post", timber, (x, 2.0, 1.18), (0.16, 0.16, 2.36))

    # ---- North wall: the desk, the mine map over it, the helmet, the candles.
    desk = kit.table("Desk", reb.mat_wood("Old desk", (0.16, 0.1, 0.055)), (2.75, Y0 + 0.4, 0.0), size=(1.4, 0.7, 0.78))
    reb.wall(desk)
    reb.mask(desk)
    top = 0.78
    reb.prim("cube", "Map board", timber, (2.75, Y0 + 0.03, 1.55), (1.5, 0.04, 0.9))
    reb.prim("cube", "Mine map", paper, (2.75, Y0 + 0.06, 1.55), (1.36, 0.01, 0.78), rot=(0, 0.015, 0))
    for (x, z) in ((2.1, 1.92), (3.4, 1.92), (2.1, 1.18), (3.4, 1.18)):
        reb.prim("sphere", "Pin", mat("red paint"), (x, Y0 + 0.07, z), (0.03, 0.02, 0.03))
    # The workings, drawn: the adit up from the bottom, the junction, the gallery off it, the lift shaft.
    lines = [((2.3, 1.22), (2.3, 1.6)), ((2.3, 1.6), (2.95, 1.6)), ((2.95, 1.6), (2.95, 1.85)), ((2.95, 1.6), (3.3, 1.45)), ((2.95, 1.6), (2.55, 1.82)), ((2.3, 1.6), (1.95, 1.75))]
    for (ax, az), (bx, bz) in lines:
        kit.rod("Map line", ink, (ax, Y0 + 0.068, az), (bx, Y0 + 0.068, bz), 0.012, 4)
    kit.rod("Gallery, flooded", red_ink, (2.95, Y0 + 0.07, 1.6), (3.32, Y0 + 0.07, 1.42), 0.02, 4)
    reb.prim("cube", "Lift shaft mark", ink, (2.95, Y0 + 0.068, 1.88), (0.07, 0.004, 0.07))
    reb.prim("cube", "Office mark", red_ink, (2.42, Y0 + 0.07, 1.42), (0.05, 0.004, 0.05))
    for words, (x, z), m_ in (("ADIT", (2.15, 1.3), ink), ("PUMP", (2.95, 1.53), ink), ("LIFT", (3.12, 1.88), ink), ("FLOODED", (3.22, 1.36), red_ink), ("ARKLAY SILVER - WORKINGS", (2.75, 2.0), ink), ("YOU ARE HERE", (2.42, 1.36), red_ink)):
        kit.text(f"Map words {words}", words, m_, (x, Y0 + 0.07, z), size=0.035, rot=(math.pi / 2, 0, math.pi))
    kit.splat("Thumb on the map", mat("old blood"), (3.05, Y0 + 0.067, 1.58), 0.025, rot=(math.pi / 2, 0, 0), seed=2)
    # The shift boss's typewriter, for the accident book: where she saves.
    reb.mask(kit.typewriter("Typewriter", (2.3, Y0 + 0.45, top), rot=0.05))
    kit.papers("Old papers", (2.95, Y0 + 0.45, top), spread=0.35, count=6, seed=4)
    helmet = reb.prim("sphere", "Miner's helmet", reb.mat_plain("Helmet leather", (0.1, 0.075, 0.045), 0.55), (3.25, Y0 + 0.4, top + 0.09), (0.3, 0.27, 0.2), segments=14)
    reb.prim("cyl", "Helmet brim", reb.mat_plain("Helmet leather", (0.1, 0.075, 0.045), 0.55), (3.25, Y0 + 0.4, top + 0.025), (0.38, 0.34, 0.02), segments=16)
    reb.prim("cyl", "Helmet lamp", mat("steel"), (3.25, Y0 + 0.56, top + 0.13), (0.06, 0.06, 0.06), rot=(math.pi / 2, 0, 0), segments=10)
    flames = []
    for k, (x, y, z, h) in enumerate(((2.0, Y0 + 0.25, top, 0.14), (3.55, Y0 + 0.25, top, 0.09), (2.6, Y0 + 0.2, top, 0.18))):
        stick, light, flame = kit.candle(f"Desk candle {k}", (x, y, z), energy=4.5, height=h)
        flames.append((light, flame))
    chair_m = reb.mat_wood("Chair", (0.17, 0.11, 0.06))
    kit.chair("Desk chair", chair_m, (2.6, Y0 + 1.15, 0.0), rot=-math.pi / 2 + 0.25)
    reb.cloth("Hal's jacket", reb.mat_surface("Skyway jacket", [(0.0, (0.03, 0.05, 0.1)), (1.0, (0.06, 0.09, 0.16))], scale=30, bump=0.2), (2.65, Y0 + 1.33, 0.82), (0.5, 0.6), rot=(math.pi / 2 - 0.15, 0, 0), cuts=10, lumps=0.05, seed=5)
    reb.prim("cube", "Jacket patch", reb.mat_plain("Patch red", (0.35, 0.06, 0.03), 0.6), (2.55, Y0 + 1.39, 0.9), (0.08, 0.01, 0.05))

    # ---- West wall: the cot pulled out, the blanket, the bandage.
    cot_m = reb.mat_wood("Cot frame", (0.2, 0.15, 0.08))
    cot = kit.table("Cot", cot_m, (X0 + 0.45, 2.65, 0.0), size=(0.75, 1.9, 0.42))
    reb.wall(cot)
    reb.cloth("Cot canvas", mat("canvas"), (X0 + 0.45, 2.65, 0.43), (0.7, 1.85), cuts=10, lumps=0.02, seed=1)
    reb.cloth("Army blanket", reb.mat_plain("Army blanket", (0.1, 0.11, 0.06), 0.95), (X0 + 0.5, 2.85, 0.47), (0.85, 1.1), rot=(0, 0.05, 0.1), cuts=12, lumps=0.07, seed=2)
    reb.cloth("Bandage", reb.mat_surface("Soaked bandage", [(0.0, (0.5, 0.48, 0.42)), (0.45, (0.3, 0.03, 0.02)), (1.0, (0.12, 0.006, 0.004))], scale=12, bump=0.2), (X0 + 0.55, 2.3, 0.53), (0.35, 0.12), rot=(0, 0, 0.6), cuts=8, lumps=0.02, seed=3)
    kit.splat("Blood on the blanket", mat("old blood"), (X0 + 0.6, 2.5, 0.52), 0.13, seed=9, stretch=(1.2, 0.8))
    reb.prim("cyl", "Water bottle", mat("steel"), (X0 + 0.95, 1.65, 0.05), (0.08, 0.08, 0.25), rot=(math.pi / 2, 0, 0.4), segments=10)

    # ---- East wall: a ledge of candles, powder boxes, old helmets on pegs.
    reb.prim("cube", "Rock ledge", rock, (X1 - 0.15, 2.0, 1.15), (0.35, 1.3, 0.12))
    for k, (y, h) in enumerate(((1.55, 0.1), (2.0, 0.16), (2.4, 0.07))):
        stick, light, flame = kit.candle(f"Ledge candle {k}", (X1 - 0.18, y, 1.21), energy=3.5, height=h)
        flames.append((light, flame))
    for k in range(3):
        b = kit.crate(f"Powder box {k}", reb.mat_wood("Powder box", (0.3, 0.22, 0.12)), (X1 - 0.35, 1.45 + k * 0.05, 0.36 * k), size=(0.5, 0.36, 0.34), rot=0.05 * k)
        if k == 0:
            reb.wall(b)
        kit.text(f"Powder words {k}", "GIANT POWDER", mat("red paint"), (X1 - 0.607, 1.45 + k * 0.05, 0.36 * k + 0.17), size=0.045, rot=(math.pi / 2, 0, -math.pi / 2))
    for k, x in enumerate((1.45, 1.85)):
        reb.prim("cube", "Peg", timber, (x, Y1 - 0.02, 1.7), (0.03, 0.12, 0.03))
        reb.prim("sphere", f"Old helmet {k}", reb.mat_plain("Helmet leather", (0.1, 0.075, 0.045), 0.55), (x, Y1 - 0.13, 1.72), (0.26, 0.24, 0.18))
    # The item box along the east wall, past the powder boxes.
    box_lid = kit.item_box("Item box", (X1 - 0.43, 2.635), (-1, 0))
    kit.rod("Coil of fuse", mat("black"), (X1 - 0.25, 3.55, 0.05), (X1 - 0.25, 3.55, 0.12), 0.12, 12)

    # ---- The drip, the bucket run over, Hal's drops in and out; webs high in the corners.
    reb.prim("cyl", "Bucket", mat("rust"), (DRIP[0], DRIP[1], 0.18), (0.32, 0.32, 0.36), segments=14)
    reb.prim("cyl", "Bucket water", reb.mat_plain("Bucket water", (0.01, 0.012, 0.012), 0.04), (DRIP[0], DRIP[1], 0.355), (0.29, 0.29, 0.005), segments=14)
    kit.splat("Overflow", reb.mat_plain("Wet floor", (0.012, 0.012, 0.012), 0.05), (DRIP[0] + 0.1, DRIP[1] + 0.15, 0.0), 0.5, seed=12, stretch=(1.3, 0.9), lumps=0.5)
    kit.splat("Wet patch on the roof", reb.mat_plain("Wet roof", (0.01, 0.01, 0.01), 0.05), (DRIP[0], DRIP[1], H - 0.02), 0.35, seed=13, lumps=0.6)
    v, f = [], []
    for k in range(12):
        t = k / 11
        x = 2.85 + (2.6 - 2.85) * t + rng.uniform(-0.08, 0.08)
        y = Y1 - 0.2 + (Y0 + 0.8 - Y1 + 0.2) * t + rng.uniform(-0.08, 0.08)
        kit._stain(v, f, rng, (x, y, 0.005), rng.uniform(0.015, 0.035), 0.0, 0.45, (1.0, 1.0), k, points=10)
    for k in range(6):
        kit._stain(v, f, rng, (X0 + 0.95 + rng.uniform(-0.1, 0.1), 2.0 + k * 0.25, 0.005), rng.uniform(0.015, 0.03), 0.0, 0.45, (1.0, 1.0), k, points=10)
    reb.mesh_object("Hal's drops", v, f, mat("old blood"), smooth=False)
    kit.web("Web, north-west", (X0 + 0.05, Y0 + 0.05, H - 0.05), 0.4, (1, 1))
    kit.web("Web, north-east", (X1 - 0.05, Y0 + 0.05, H - 0.05), 0.45, (-1, 1))
    kit.web("Web, over the door", (X1 - 0.05, Y1 - 0.25, H - 0.1), 0.35, (-1, -1))

    # ---- Light: the candles alone.
    kit.time_light("afternoon")
    reb.point("Candle bounce", (2.8, 2.0, 1.4), 5, (1.0, 0.6, 0.3), 1.2)

    anim = kit.Anim(16)
    for light, flame in flames:
        anim.flicker(light, flame, depth=0.3, dropouts=0)
    anim.drip((DRIP[0], DRIP[1], H - 0.05), fall=H - 0.4, size=0.016)

    # ---- What the game needs.
    room.door("tunnel", (d0, Y1 - 0.5, d1, Y1), arrive=(2.85, 3.0), face=(0, -1))
    room.check((2.55, Y0, 3.0, Y0 + 0.85), "A map of the workings. The adit, the junction with the pump,\nthe lift up to the top. The old gallery is marked FLOODED.\nThere's a bloody thumbprint on it.")
    room.check((3.0, Y0, 3.6, Y0 + 0.85), "An old miner's helmet with a carbide lamp on it.")
    room.check((2.2, Y0 + 0.85, 3.1, Y0 + 1.6), "A jacket over the chair. ARKLAY SKYWAY on the patch.\nHal's.")
    room.check((X0, 1.7, X0 + 1.0, 3.6), "A cot, pulled out. A bandage soaked through on the blanket.\nHe rested here, then went on down.")
    room.check((X1 - 0.8, 1.2, X1, 1.95), "The candles are new. GIANT POWDER on the boxes. Empty.")
    # Each takes in the floor in front where she stands; they come first in the
    # table, and the jacket's and the drip's zones keep most of theirs.
    room.save_room(typewriter=(2.05, Y0, 2.55, Y0 + 1.5), box=(3.4, 2.0, X1, 3.27), lid=box_lid)
    room.check((DRIP[0] - 0.25, DRIP[1] - 0.25, DRIP[0] + 0.25, DRIP[1] + 0.25), "Water's coming through the roof. The bucket ran over long ago.")
    room.export(anim)


build()
