"""The flooded gallery under the junction: where Hal hid, and dies.

What it tells: the old gallery has been under water for years: black,
still, knee deep, with the rails running on beneath it and the ore carts
left standing in it to the axles. In the north-east the floor drops away
into a winze, roped off long ago, DANGER on a board. Hal came down here to
hide from the things in the woods. He climbed onto an ore cart in the
middle, out of the water, with a blanket and his lantern, and waited. The
web spinners found him anyway: their silk lies over the arch like grey
felt and hangs from it in festoons, the roof over the cart is thick with
it round their sacs, and a strand still runs down to the cart. The blanket is bloody, and there is a
bloody handprint on the side where he climbed up. He is not in the
painting: he is an actor on the cart (day/cutscenes.ts, cut-hal), alive
until he gives her the drive key. The lantern on the cart is still burning
low.

The gallery ends at a wall of rock in the dark east, and low in it is the
old drainage adit: a timbered tunnel no higher than a man, its sill just
clear of the water, that once let the gallery drain out to the hillside.
Somebody boarded it across years ago. The boards are grey and split, nailed
over the frame, and the water laps at the sill under them. Kicked out,
they open on a long, low tunnel that climbs away to the east, with a faint
grey daylight at its far end, coming through the boards over its mouth on
the east path.

Metres: the floor is x 1.0-15.0, y 2.0-8.0, under knee-deep water (its
surface 0.45 up), in a gallery 7 m wide under a rock arch about 4 high,
running east-west. The way back up to the junction is the west end, where
the floor climbs out of the water into the decline. The winze, the deep
water, is x 10.5-15.0, y 2.0-4.6, behind a rope on posts. The cart he hid on stands at x 7.2, y 4.6. The east end's
rock wall stands at x 15.3. The adit's mouth is in it at y 5.7-7.1, its
sill 0.5 up and its cap 2.3 up, boarded across. The door to the east path
is in front of the boards, x 14.4-15.0, y 5.8-7.0. Coming in from the east
path she stands at x 13.5, y 7.1, facing west into the gallery. The adit
runs east-north-east from the mouth, about 15 m, to daylight.

Once she kicks the boards out ("adit"), they lie broken in the adit's
mouth, one hanging by a nail, and the far end shows a faint daylight.

Moving: the water rippling; the lantern's flame low; drops from the roof.
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
import bpy  # noqa: E402

X0, X1, Y0, Y1 = 1.0, 15.0, 2.0, 8.0
WATER = 0.45
DEEP = (10.5, Y0, X1, 4.6)
CART = (7.2, 4.6)
END = 15.3                      # the rock wall closing the gallery's east end
ADIT = (5.7, 7.1, 0.5, 2.3)     # the drainage adit's mouth in it: y0, y1, sill, cap
ADIT_FAR = (29.5, 9.9)          # its far end, the mouth on the east path


def rock_face(name, m, origin, u, v, nu, nv, out, depth=0.25, seed=0):
    """A lumpy rock surface over the rectangle origin + s*u + t*v, pushed back along `out` by noise."""
    o, u, v, out = Vector(origin), Vector(u), Vector(v), Vector(out).normalized()
    verts, faces = [], []
    for j in range(nv + 1):
        for i in range(nu + 1):
            p = o + u * (i / nu) + v * (j / nv)
            d = depth * (0.6 + noise.noise(p * 0.9 + Vector((seed, 0, 0))) + 0.35 * noise.noise(p * 3.0 + Vector((0, seed, 0))))
            verts.append(tuple(p + out * max(-0.03, d)))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    return reb.mesh_object(name, verts, faces, m)


def ore_cart(name, m, at, yaw, roll=0.0, sink=0.0):
    """A side-tipping ore cart on four wheels, standing in the water (sink lowers it into the mud)."""
    parts = [
        reb.prim("cube", "tub", m, (0, 0, 0.62), (1.1, 0.8, 0.6), bevel=0.04),
        reb.prim("cube", "chassis", mat("iron"), (0, 0, 0.27), (1.2, 0.6, 0.1)),
    ]
    for dx in (-0.38, 0.38):
        for dy in (-0.3, 0.3):
            parts.append(reb.prim("cyl", "wheel", mat("iron"), (dx, dy, 0.17), (0.34, 0.34, 0.05), rot=(math.pi / 2, 0, 0), segments=12))
    for p in parts:
        bpy.ops.object.select_all(action="DESELECT")
        p.select_set(True)
        bpy.context.view_layer.objects.active = p
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob = kit.join(name, parts)
    ob.rotation_euler = (roll, 0, yaw)
    ob.location = (at[0], at[1], -sink)
    return ob


def build():
    rng = random.Random(83)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.ground("water")  # knee deep over the mud
    room.camera((1.8, 3.1, 2.25), (9.5, 5.6, 0.3), 200, "from the foot of the decline: the black water, the cart he hid on, the rope")
    room.camera((14.8, 6.8, 2.3), (6.0, 3.6, 0.3), 200, "from the far south-east: the edge of the deep water, the cart, the way back up")
    room.camera((7.0, 7.0, 2.25), (10.2, 4.6, 0.2), 200, "close on the edge of the deep water, the rope and the DANGER board")
    room.camera((12.2, 3.2, 2.3), (5.0, 7.0, 0.3), 200, "from over the winze: the cart under its web, the carts in the water, the decline")
    room.camera((12.55, 5.75, 2.3), (15.3, 6.4, 0.9), 200, "down the drainage adit's line at the east end: the boards across it, the water at its sill; kicked out, the tunnel to daylight")

    rock = kit.dirtied(mat("wet rock"), 0.55, scale=0.8)
    timber = kit.dirtied(reb.mat_wood("Mine timber", (0.13, 0.09, 0.05)), 0.8)
    rust = mat("rust")
    water = mat("water")
    silk = reb.mat_plain("Silk", (0.68, 0.68, 0.66), 0.6)

    # ---- The gallery: a broad arch of rock east-west, its mud floor, the black water over it.
    arch = kit.tunnel("Gallery", rock, [(-4.0, 5.0), (19.0, 5.0)], width=7.6, height=4.0, rough=0.12, seed=21, floor_m=mat("mud"))
    # Not a mask: from the camera on the rope the water fills more than half the
    # frame, more than a camera's mask texture holds, so her legs show over it.
    reb.prim("cube", "Black water", water, ((X0 + X1) / 2 + 1.0, 5.0, WATER), (X1 - X0 + 6.0, 7.4, 0.01))
    # The way back up: the decline's floor climbing out of the water at the west end.
    reb.prim("cube", "Decline floor", kit.dirtied(mat("mud"), 0.5), (-1.2, 5.0, 0.2), (5.0, 3.6, 0.2), rot=(0, -0.26, 0))
    reb.prim("cube", "Decline wet edge", reb.mat_plain("Wet mud", (0.015, 0.012, 0.01), 0.1), (0.6, 5.0, WATER + 0.004), (0.7, 3.4, 0.004))
    for y in (3.15, 6.85):
        kit.rod("Decline set post", timber, (-0.2, y, 0.3), (-0.2, y, 2.9), 0.11, 6)
    kit.rod("Decline set cap", timber, (-0.2, 2.9, 2.9), (-0.2, 7.1, 2.9), 0.12, 6)
    reb.prim("cube", "Decline dark", mat("black"), (-3.8, 5.0, 1.6), (0.2, 4.0, 3.0))
    # Rails under the water, the deep water's broken edge marked by posts and a rope.
    for y in (4.75, 5.35):
        kit.rod("Rail", rust, (-1.0, y, 0.12), (10.3, y, 0.12), 0.03, 6)
    dx0, dy0, dx1, dy1 = DEEP
    post_xy = [(dx0, dy1), (dx0 + 1.5, dy1 + 0.05), (dx0 + 3.0, dy1 - 0.05), (X1 + 0.2, dy1), (dx0, dy0 + 1.2)]
    for i, (x, y) in enumerate(post_xy):
        tilt = rng.uniform(-0.12, 0.12)
        kit.rod("Rope post", timber, (x, y, 0.0), (x + tilt, y + tilt * 0.5, 1.15), 0.06, 6)
    for (ax, ay), (bx, by) in zip(post_xy[:4], post_xy[1:4]):
        for k in range(6):
            t0, t1 = k / 6, (k + 1) / 6
            z0 = 1.0 - 0.25 * math.sin(math.pi * t0)
            z1 = 1.0 - 0.25 * math.sin(math.pi * t1)
            kit.rod("Rope", reb.mat_plain("Rope", (0.25, 0.2, 0.12), 0.9), (ax + (bx - ax) * t0, ay + (by - ay) * t0, z0), (ax + (bx - ax) * t1, ay + (by - ay) * t1, z1), 0.012, 4)
    kit.rod("Rope", reb.mat_plain("Rope", (0.25, 0.2, 0.12), 0.9), (dx0, dy1, 1.0), (dx0, dy0 + 1.2, 0.6), 0.012, 4)
    reb.prim("cube", "Danger board", mat("red paint"), (dx0 + 1.5, dy1 + 0.07, 0.78), (0.7, 0.03, 0.3), rot=(0, 0.12, 0))
    kit.text("Danger words", "DANGER\nWINZE", mat("white paint"), (dx0 + 1.5, dy1 + 0.09, 0.78), size=0.08, rot=(math.pi / 2, 0.12, math.pi))
    reb.prim("cube", "Winze lip timber", timber, (dx0 + 2.2, dy1 - 0.15, WATER - 0.08), (4.4, 0.2, 0.18), rot=(0, 0, 0.02))
    reb.prim("cube", "Winze dark", reb.mat_plain("Deep water", (0.003, 0.004, 0.004), 0.05), ((dx0 + X1) / 2 + 1.0, (dy0 + dy1) / 2 - 0.4, WATER + 0.002), (X1 - dx0 + 2.0, dy1 - dy0 + 1.0, 0.004))

    # ---- Timber sets down the gallery; one broken.
    tparts = []
    for i, x in enumerate([1.8 + 2.6 * k for k in range(6)]):
        for y in (1.55, 8.45):
            if i == 4 and y > 8:
                tparts.append(kit.rod("Fallen post", timber, (x, y - 0.3, WATER - 0.05), (x + 1.4, y - 1.6, WATER + 0.1), 0.11, 6))
                continue
            tparts.append(kit.rod("Set post", timber, (x, y, 0), (x, y + (0.35 if y < 5 else -0.35), 2.5), 0.11, 6))
        if i == 4:
            tparts.append(kit.rod("Sagging cap", timber, (x, 1.9, 2.5), (x + 0.2, 7.6, 1.6), 0.12, 6))
        else:
            tparts.append(kit.rod("Set cap", timber, (x, 1.8, 2.55), (x, 8.2, 2.55), 0.12, 6))
    kit.join("Timber sets", tparts)

    # ---- The east end: a wall of rock, and low in it the old drainage adit,
    # timbered, boarded across. Its own random stream, so the rest stays as it was.
    arng = random.Random(183)
    a0, a1, sill, cap = ADIT
    rock_face("East end, north", rock, (END, 0.4, -0.2), (0, a0 - 0.4, 0), (0, 0, 5.0), 14, 14, (1, 0, 0), seed=31)
    rock_face("East end, south", rock, (END, a1, -0.2), (0, 9.6 - a1, 0), (0, 0, 5.0), 8, 14, (1, 0, 0), seed=32)
    rock_face("East end, under the adit", rock, (END, a0, -0.2), (0, a1 - a0, 0), (0, 0, sill + 0.2), 5, 2, (1, 0, 0), depth=0.1, seed=33)
    rock_face("East end, over the adit", rock, (END, a0, cap), (0, a1 - a0, 0), (0, 0, 4.8 - cap), 5, 8, (1, 0, 0), seed=34)
    # The adit: low and narrow, climbing gently away east-north-east to the hillside.
    fx, fy = ADIT_FAR
    mid = ((a0 + a1) / 2)
    adit = kit.tunnel("Drainage adit", rock, [(END - 0.05, mid), (END + 1.2, mid + 0.1), (fx, fy)], width=a1 - a0 + 0.1, height=cap - sill + 0.05, rough=0.08, seed=35, floor_m=kit.dirtied(mat("mud"), 0.5))
    adit.location.z = sill
    bpy.data.objects["Drainage adit floor"].location.z = sill
    old = kit.dirtied(reb.mat_wood("Adit timber", (0.11, 0.08, 0.05)), 0.85, scale=4)
    sets = []
    for k, t in enumerate((0.0, 0.18, 0.34, 0.5, 0.66, 0.82)):
        p = Vector((END + 1.2, mid + 0.1)).lerp(Vector((fx, fy)), t) if k else Vector((END + 0.05, mid))
        d = (Vector((fx, fy)) - Vector((END + 1.2, mid + 0.1))).normalized() if k else Vector((1, 0))
        side = Vector((-d.y, d.x)) * ((a1 - a0) / 2 - 0.08)
        sag = 0.18 if k == 3 else 0.0
        for s in (-1, 1):
            q = p + side * s
            sets.append(kit.rod("Adit post", old, (q.x, q.y, sill - 0.1), (q.x, q.y, cap - 0.05), 0.08, 6))
        sets.append(kit.rod("Adit cap", old, ((p - side * 1.25).x, (p - side * 1.25).y, cap - 0.02), ((p + side * 1.25).x, (p + side * 1.25).y, cap - 0.02 - sag), 0.09, 6))
    kit.join("Adit sets", sets)
    reb.prim("cube", "Adit sill", old, (END - 0.02, mid, sill - 0.06), (0.24, a1 - a0 + 0.3, 0.16))
    # The boards nailed across the mouth: grey, split, one broken short.
    boards_m = kit.dirtied(reb.mat_wood("Adit boards", (0.2, 0.17, 0.13)), 0.8, scale=5)
    bx = END - 0.06   # on the posts' faces
    boards = []
    z = sill + 0.12
    for k in range(6):
        h = arng.uniform(0.2, 0.25)
        short = 0.55 if k == 4 else 0.0
        boards.append(reb.prim("cube", "Adit board", boards_m, (bx - 0.01 * k, mid - short / 2 + arng.uniform(-0.04, 0.04), z + h / 2), (0.04, a1 - a0 + 0.35 - short, h), rot=(arng.uniform(-0.05, 0.05), 0, 0)))
        z += h + arng.uniform(0.04, 0.09)
    boards.append(reb.prim("cube", "Adit board, across", boards_m, (bx - 0.07, mid, (sill + cap) / 2), (0.04, 0.22, cap - sill + 0.1), rot=(0.62, 0, 0)))
    boards = kit.join("Adit boards", boards)
    kit.web("Web on the boards", (bx - 0.05, a0 - 0.1, cap + 0.05), 0.45, (-1, 1))
    # Kicked out (plan step "adit"): the boards broken inward onto the adit's
    # floor, one hanging by a nail, and grey daylight at the far end.
    kicked = []
    for k, (t, yaw, tilt) in enumerate(((0.6, 0.5, 0.15), (1.3, -0.3, 0.05), (2.0, 0.9, 0.1))):
        p = Vector((END + 0.2, mid)).lerp(Vector((fx, fy)), t / 15.0)
        kicked.append(reb.prim("cube", f"Kicked board {k}", boards_m, (p.x, p.y, sill + 0.05 + 0.04 * k), (1.15, 0.22, 0.04), rot=(tilt, 0, math.pi / 2 + yaw)))
    kicked.append(reb.prim("cube", "Board hanging by a nail", boards_m, (bx, a0 + 0.2, sill + 0.75), (0.04, 0.22, 1.1), rot=(0.25, 0, 0)))
    kicked.append(reb.prim("cube", "Board stub", boards_m, (bx, a1 - 0.05, sill + 1.5), (0.04, 0.3, 0.22), rot=(0.1, 0, 0)))
    far = (Vector((fx, fy)) - Vector((END + 1.2, mid + 0.1))).normalized()
    day = reb.prim("cube", "Daylight at the far end", reb.mat_emit("Faint daylight", (0.6, 0.66, 0.75), 1.0), (fx - far.x * 0.3, fy - far.y * 0.3, sill + 0.85), (0.05, a1 - a0, cap - sill), rot=(0, 0, math.atan2(far.y, far.x)))
    slats = []
    for k in range(5):
        slats.append(reb.prim("cube", "Far boards", mat("black"), (fx - far.x * 0.4, fy - far.y * 0.4, sill + 0.2 + k * 0.34), (0.03, a1 - a0 + 0.1, 0.24), rot=(0, 0, math.atan2(far.y, far.x))))
    slats = kit.join("Far boards", slats)
    daylight = reb.point("Daylight down the adit", (fx - far.x * 2.0, fy - far.y * 2.0, sill + 1.0), 12, (0.65, 0.72, 0.85), 0.8)
    after_kick = kicked + [day, slats, daylight]
    for ob in after_kick:
        ob.hide_render = True

    def kick(done):
        boards.hide_render = done
        for ob in after_kick:
            ob.hide_render = not done
    room.state("adit", kick)

    # ---- The carts: the one he hid on, two more standing in the water, one over on its side.
    cx, cy = CART
    hid = ore_cart("Cart he hid on", rust, (cx, cy), 0.1, sink=0.05)
    # The operator's key, on the blanket where Hal lay (op-key).
    room.item("op-key", (cx + 0.1, cy - 0.3, 0.98))
    reb.wall(hid)
    reb.mask(hid)
    reb.cloth("Blanket on the cart", reb.mat_plain("Grey blanket", (0.14, 0.14, 0.13), 0.95), (cx, cy, 0.95), (1.3, 1.0), rot=(0, 0, 0.1), cuts=12, lumps=0.06, seed=4)
    kit.splat("Blood on the blanket", mat("blood"), (cx + 0.1, cy - 0.05, 1.0), 0.18, seed=5, stretch=(1.2, 0.8))
    kit.splat("Hand climbing up", mat("blood"), (cx + 0.35, cy + 0.415, 0.75), 0.06, rot=(math.pi / 2, 0, math.pi + 0.1), seed=6, lumps=0.5)
    reb.prim("cube", "Smear down the cart", mat("old blood"), (cx + 0.35, cy + 0.414, 0.55), (0.05, 0.004, 0.35), rot=(0, 0, 0.1))
    lamp, lamp_light, lamp_flame = kit.lantern("Hal's lantern", (cx - 0.3, cy + 0.15, 0.95), energy=9)
    reb.prim("cyl", "Thermos lid cup", mat("steel"), (cx + 0.3, cy - 0.2, 0.98), (0.07, 0.07, 0.06), segments=10)
    for k, (x, y, yaw, sink) in enumerate(((4.0, 5.05, 0.0, 0.1), (12.6, 6.2, 0.15, 0.08))):
        c = ore_cart(f"Cart in the water {k}", rust, (x, y), yaw, sink=sink)
        reb.wall(c)
    over = ore_cart("Cart on its side", rust, (5.6, 7.0), 1.4, roll=math.radians(-90), sink=-0.38)
    reb.wall(reb.prim("cube", "Tipped cart footprint", None, (5.6, 7.0, 0.5), (1.0, 1.3, 1.0))).hide_render = True

    # ---- The webs: silk matted over the arch and the roof, the sacs in it over
    # the cart, one strand still down to it; festoons hung along the arch.
    sv, sf = [], []
    for _ in range(8):
        r = rng.uniform(0.09, 0.15)
        reb.boulder(rng, (cx + rng.uniform(-1.2, 1.2), cy + rng.uniform(-1.0, 1.0), 3.55 - r), r, sv, sf, squash=1.3)
    sacs = reb.mesh_object("Egg sacs", sv, sf, reb.mat_surface("Egg sac", [(0.0, (0.2, 0.17, 0.11)), (0.7, (0.38, 0.33, 0.22)), (1.0, (0.16, 0.12, 0.06))], scale=18, rough=0.45, bump=0.6))
    kit.rod("Strand to the cart", silk, (cx + 0.1, cy, 3.3), (cx + 0.05, cy + 0.1, 1.0), 0.006, 3)
    for k, (x, y) in enumerate(((cx, cy), (2.6, 5.4), (11.8, 5.0))):
        kit.web_blanket(f"Silk under the roof {k}", (x - 1.8, y - 1.7, 3.0), (3.6, 0, 0), (0, 3.4, 0), (0, 0, 1), [arch, sacs], roof=True, seed=k)
    for k, (side, y, out) in enumerate((("north", 3.0, (0, -1, 0)), ("south", 7.0, (0, 1, 0)))):
        o = (X0 - 1.0, y, WATER)
        u, v = (END - X0 + 1.0, 0, 0), (0, 0, 3.3 - WATER)
        kit.web_blanket(f"Silk on the {side} side", o, u, v, out, [arch], cover=0.75, corners=(False, True), seed=31 + k)
        kit.web_blanket(f"Loose silk on the {side} side", o, u, v, out, [arch], cover=0.6, corners=(False, True), seed=41 + k, loose=0.12)
    cams = [(1.8, 3.1), (14.8, 6.8), (7.0, 7.0), (12.2, 3.2), (12.55, 5.75)]
    for k, (y, into) in enumerate(((2.75, (0, 1, 0)), (7.25, (0, -1, 0)))):
        x = X0 - 0.5 + k * 1.2
        while x + 2.0 < END:
            span = rng.uniform(2.0, 2.8)
            if all(math.hypot(px - (x + span / 2), py - y) > 2.0 for px, py in cams):
                kit.web_drape(f"Festoon {k} {x:.1f}", (x, y, 3.2), (x + span, y, 3.2), into, rng.uniform(0.45, 0.75), rng, belly=0.3)
            x += span + rng.uniform(0.3, 1.0)

    # ---- Floating rubbish: timber, a hard hat, a lamp cable dangling into the water; the lamps.
    for k in range(5):
        reb.prim("cube", "Floating plank", timber, (rng.uniform(2.5, 14.0), rng.uniform(2.6, 7.6), WATER), (rng.uniform(0.6, 1.4), 0.14, 0.05), rot=(0, 0, rng.uniform(0, 3)))
    reb.prim("sphere", "Floating hard hat", mat("white paint"), (3.2, 6.9, WATER + 0.02), (0.28, 0.25, 0.18), rot=(math.pi, 0.3, 0))
    lamps = []
    for k, (x, y, e) in enumerate(((1.2, 5.0, 55), (9.0, 5.2, 40), (13.4, 4.6, 30))):
        glow = reb.mat_emit(f"Lamp glow {k}", (1.0, 0.72, 0.4), 12)
        pivot = reb.prim("sphere", f"Lamp hook {k}", mat("iron"), (x, y, 2.75), (0.03, 0.03, 0.03))
        kit.rod(f"Lamp flex {k}", mat("black"), (0, 0, 0), (0, 0, -0.4), 0.007, 4).parent = pivot
        reb.prim("sphere", f"Lamp bulb {k}", glow, (0, 0, -0.48), (0.08, 0.08, 0.11), segments=10).parent = pivot
        light = reb.point(f"Lamp {k}", (0, 0, -0.52), e, (1.0, 0.68, 0.38), 0.05)
        light.parent = pivot
        lamps.append((pivot, light, glow))
    kit.rod("Lamp cable", mat("black"), (-3.0, 5.0, 2.75), (1.2, 5.0, 2.75), 0.01, 4)
    kit.rod("Lamp cable", mat("black"), (1.2, 5.0, 2.75), (9.0, 5.2, 2.75), 0.01, 4)
    kit.rod("Lamp cable", mat("black"), (9.0, 5.2, 2.75), (13.4, 4.6, 2.75), 0.01, 4)
    kit.rod("Lamp cable down", mat("black"), (13.4, 4.6, 2.75), (14.6, 6.4, WATER), 0.01, 4)
    # Underground: no sky. The lamps, Hal's lantern and a cold fill under the arch.
    reb.point("Under-arch fill", (7.0, 5.0, 3.0), 40, (0.6, 0.65, 0.75), 3.0)
    reb.point("Fill over the winze", (12.5, 4.0, 3.0), 18, (0.6, 0.65, 0.75), 2.0)

    anim = kit.Anim(16)
    anim.ripple(water, speed=1)
    anim.flicker(lamp_light, lamp_flame, depth=0.4, dropouts=1)
    for k, (pivot, light, glow) in enumerate(lamps):
        anim.flicker(light, glow, depth=0.1 if k == 0 else 0.45, dropouts=0 if k == 0 else 2)
    anim.drip((cx + 0.6, cy - 0.4, 3.0), fall=3.0 - WATER, size=0.015)

    # ---- What the game needs.
    room.void(DEEP)
    room.door("junction", (X0, 3.6, X0 + 0.6, 6.4), arrive=(2.6, 5.0), face=(1, 0))
    # The adit: she kicks the boards out from the gallery side, then goes up it
    # to the east path (underground to outside: the action button opens it).
    # The floor ends at the mouth, so she comes back in just out of it.
    # The spot is the strip in front of the boards and the door the mouth
    # itself: one zone for both, and the door's line until the boards are
    # out would take the action button, so she could never kick them.
    room.spot("adit", (X1 - 1.2, a0 + 0.1, X1 - 0.6, a1 - 0.1))  # day/events.ts says what she sees and does here
    room.door("east-path", (X1 - 0.6, a0 + 0.1, X1, a1 - 0.1), arrive=(13.5, 7.1), face=(-1, 0), walk=False)
    room.check((cx - 0.9, cy - 0.7, cx + 0.9, cy + 0.7), "He hid up on this cart, out of the water. Blanket, lantern.\nThe blood on it is his.")
    room.check((dx0 - 0.3, dy1, dx0 + 3.5, dy1 + 0.6), "DANGER. WINZE. The floor drops away under the water there.")
    room.export(anim)


build()
