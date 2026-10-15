"""Inside gondola car 4, stopped halfway down at dusk.

What it tells: last night a woman was bitten by a dog in the lower car
park. The keeper bandaged her wrist and put her in car 4 to ride up to Hal,
who had a radio. She never got off. She sat bleeding on the west bench, and
somewhere on the way up she turned: the bandage lies unwound on the floor,
her handbag is spilled where it was dropped, one shoe is under the bench.
Whatever she became clawed at the inside of the door and smeared the
glass all the way up, and at dawn it was dragged out at the top. Now the car
hangs dead on the cable just short of a pylon, rocking, with the valley
forest far below in the dusk and crows on the pylon watching. The roof
hatch over the east bench is open: the only way on.

Metres: the floor is x 1.0-3.4, y 1.0-2.4, 2.1 high. The door is in the
north wall at x 1.6-2.5 (it opened onto the upper station's platform).
Benches run along the west and east ends. The roof hatch is over the east
bench at x 2.8-3.35, y 1.4-2.0; she climbs out from the bench. Windows run all
round from 0.9 to 1.95 m. The pylon stands south, its service platform at
roof height.

Moving: the whole view swaying as the car rocks on the cable, the hanging
straps swinging, the emergency lamp failing, a crow on the pylon rail
ducking, flies over the blood.
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

X0, X1, Y0, Y1, H = 1.0, 3.4, 1.0, 2.4, 2.1
DOOR = (1.6, 2.5)
HATCH = (2.8, 3.35, 1.4, 2.0)
WIN = (0.9, 1.95)
GRIP = Vector((2.2, 1.7, 3.35))
GROUND = -46.0
PYLON = (2.2, 7.2)


def ground(x, y):
    return GROUND + 3.0 * noise.noise(Vector((x * 0.03, y * 0.03, 1.0))) + 0.25 * y


def struts(name, m, segs, r, sides=4):
    """Many square bars, one mesh."""
    verts, faces = [], []
    for a, b in segs:
        a, b = Vector(a), Vector(b)
        d = b - a
        if d.length < 1e-4:
            continue
        q = d.to_track_quat("Z", "Y")
        k = len(verts)
        for end in (a, b):
            for s in range(sides):
                t = 2 * math.pi * s / sides + math.pi / sides
                verts.append(tuple(end + q @ Vector((math.cos(t) * r, math.sin(t) * r, 0))))
        for s in range(sides):
            faces.append((k + s, k + (s + 1) % sides, k + sides + (s + 1) % sides, k + sides + s))
    return reb.mesh_object(name, verts, faces, m, smooth=False)


def cone_trees(name, rng, area, keep_out, count, spacing, tall):
    """Spruces seen from far above: each a stack of cones, one mesh, cheap to render."""
    verts, faces = [], []
    placed = []
    tries = 0
    while len(placed) < count and tries < count * 30:
        tries += 1
        x, y = rng.uniform(area[0], area[2]), rng.uniform(area[1], area[3])
        if keep_out(x, y) or any((x - px) ** 2 + (y - py) ** 2 < spacing ** 2 for px, py in placed[-60:]):
            continue
        placed.append((x, y))
        h = rng.uniform(*tall)
        z = ground(x, y)
        r = h * rng.uniform(0.18, 0.24)
        for t in range(4):
            z0 = z + h * (0.12 + 0.2 * t)
            rr = r * (1 - 0.22 * t)
            k = len(verts)
            for s in range(7):
                a = 2 * math.pi * s / 7 + t * 0.4
                verts.append((x + math.cos(a) * rr, y + math.sin(a) * rr, z0))
            verts.append((x, y, z0 + h * 0.36))
            faces.extend((k + s, k + (s + 1) % 7, k + 7) for s in range(7))
    return reb.mesh_object(name, verts, faces, mat("needles"), smooth=False)


def mist_card_mat(name, rgb, density, scale):
    """Mist on a card: noise thinned to nothing at the card's edges."""
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = 1.0
    out = nodes["Material Output"]
    tr = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    n = reb.noise_tex(nodes, links, scale, 4, 0.6)
    r = reb.ramp(nodes, links, n.outputs["Fac"], [(0.35, (0, 0, 0)), (0.75, (density,) * 3)])
    tc = nodes.new("ShaderNodeTexCoord")
    sub = nodes.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    links.new(tc.outputs["Generated"], sub.inputs[0])
    mul = nodes.new("ShaderNodeVectorMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = (2, 2, 0)
    links.new(sub.outputs[0], mul.inputs[0])
    ln = nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    links.new(mul.outputs[0], ln.inputs[0])
    edge = nodes.new("ShaderNodeMapRange")
    edge.inputs["From Min"].default_value = 1.0
    edge.inputs["From Max"].default_value = 0.3
    links.new(ln.outputs["Value"], edge.inputs["Value"])
    prod = nodes.new("ShaderNodeMath")
    prod.operation = "MULTIPLY"
    links.new(r.outputs["Color"], prod.inputs[0])
    links.new(edge.outputs["Result"], prod.inputs[1])
    links.new(prod.outputs[0], mix.inputs["Fac"])
    links.new(tr.outputs[0], mix.inputs[1])
    links.new(bsdf.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def build():
    rng = random.Random(404)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.camera((1.12, 1.12, 1.92), (2.9, 2.3, 0.65), 205, "high by the door, north-west: the bloody west bench, the spilled bag, the pylon through the south glass")
    room.camera((3.28, 2.28, 1.92), (1.5, 1.1, 0.65), 205, "high in the south-east corner: the clawed door, her bench, the valley through the north glass")

    shell = reb.mat_surface("Car panels", [(0.0, (0.28, 0.27, 0.24)), (0.7, (0.4, 0.38, 0.33)), (1.0, (0.22, 0.2, 0.17))], scale=3, rough=0.5, bump=0.15)
    red = reb.mat_surface("Car red", [(0.0, (0.22, 0.03, 0.02)), (0.8, (0.35, 0.05, 0.03)), (1.0, (0.18, 0.1, 0.06))], scale=4, rough=0.45, bump=0.1)
    floor_m = reb.mat_stripes("Ribbed rubber", [(0.025, 0.025, 0.025), (0.05, 0.05, 0.048)], across=40, axis="Y")
    seat = reb.mat_surface("Seat vinyl", [(0.0, (0.06, 0.07, 0.12)), (1.0, (0.1, 0.11, 0.18))], scale=6, rough=0.4, bump=0.2)
    alu = reb.mat_metal("Aluminium", (0.5, 0.5, 0.5), 0.4)
    glass = reb.mat_glass("Car glass", (0.8, 0.82, 0.78))
    bandage = reb.mat_surface("Bloody bandage", [(0.0, (0.5, 0.48, 0.42)), (0.5, (0.45, 0.4, 0.35)), (0.65, (0.25, 0.02, 0.01)), (1.0, (0.12, 0.005, 0.004))], scale=10, bump=0.2)
    bag_m = reb.mat_plain("Handbag leather", (0.2, 0.04, 0.03), 0.4)

    # ---- The shell: red panels below the glass, grey above, a ribbed floor, the ceiling with its hatch.
    for side, a0, a1 in (("n", X0, X1), ("s", X0, X1), ("w", Y0, Y1), ("e", Y0, Y1)):
        along = side in "ns"
        fixed = {"n": Y0 - 0.05, "s": Y1 + 0.05, "w": X0 - 0.05, "e": X1 + 0.05}[side]
        for z0, z1, m in ((0.0, WIN[0], red), (WIN[1], H, shell)):
            if side == "n" and z0 == 0.0:
                for b0, b1 in ((a0 - 0.1, DOOR[0]), (DOOR[1], a1 + 0.1)):
                    reb.prim("cube", "Car wall n", m, ((b0 + b1) / 2, fixed, (z0 + z1) / 2), (b1 - b0, 0.1, z1 - z0))
                continue
            at = ((a0 + a1) / 2, fixed, (z0 + z1) / 2) if along else (fixed, (a0 + a1) / 2, (z0 + z1) / 2)
            size = (a1 - a0 + 0.2, 0.1, z1 - z0) if along else (0.1, a1 - a0 + 0.2, z1 - z0)
            reb.prim("cube", f"Car wall {side}", m, at, size)
        # The glass and its mullions.
        gat = ((a0 + a1) / 2, fixed + (0.02 if side in "s" else -0.02 if side == "n" else 0), (WIN[0] + WIN[1]) / 2) if along else (fixed + (0.02 if side == "e" else -0.02), (a0 + a1) / 2, (WIN[0] + WIN[1]) / 2)
        gsize = (a1 - a0, 0.01, WIN[1] - WIN[0]) if along else (0.01, a1 - a0, WIN[1] - WIN[0])
        if side == "n":
            for b0, b1 in ((a0, DOOR[0]), (DOOR[1], a1)):
                reb.prim("cube", "Glass n", glass, ((b0 + b1) / 2, gat[1], gat[2]), (b1 - b0, 0.01, gsize[2]))
        else:
            reb.prim("cube", f"Glass {side}", glass, gat, gsize)
        n = 3 if along else 2
        for i in range(n + 1):
            t = a0 + (a1 - a0) * i / n
            at = (t, fixed, (WIN[0] + WIN[1]) / 2) if along else (fixed, t, (WIN[0] + WIN[1]) / 2)
            reb.prim("cube", "Mullion", alu, at, (0.05, 0.12, WIN[1] - WIN[0]) if along else (0.12, 0.05, WIN[1] - WIN[0]))
    reb.prim("cube", "Floor", floor_m, ((X0 + X1) / 2, (Y0 + Y1) / 2, -0.03), (X1 - X0 + 0.2, Y1 - Y0 + 0.2, 0.06))
    hx0, hx1, hy0, hy1 = HATCH
    for x0, x1, y0, y1 in ((X0 - 0.1, hx0, Y0 - 0.1, Y1 + 0.1), (hx1, X1 + 0.1, Y0 - 0.1, Y1 + 0.1), (hx0, hx1, Y0 - 0.1, hy0), (hx0, hx1, hy1, Y1 + 0.1)):
        reb.prim("cube", "Ceiling", shell, ((x0 + x1) / 2, (y0 + y1) / 2, H + 0.03), (x1 - x0, y1 - y0, 0.06))
    reb.prim("cube", "Roof", red, ((X0 + X1) / 2, (Y0 + Y1) / 2, H + 0.12), (X1 - X0 + 0.5, Y1 - Y0 + 0.5, 0.1), bevel=0.04)
    for x0, x1, y0, y1 in ((hx0 - 0.04, hx0, hy0, hy1), (hx1, hx1 + 0.04, hy0, hy1), (hx0, hx1, hy0 - 0.04, hy0), (hx0, hx1, hy1, hy1 + 0.04)):
        reb.prim("cube", "Hatch frame", alu, ((x0 + x1) / 2, (y0 + y1) / 2, H - 0.02), (x1 - x0, y1 - y0, 0.06))
    reb.prim("cube", "Hatch lid, thrown back", red, (hx1 + 0.05, (hy0 + hy1) / 2, H + 0.45), (0.06, hy1 - hy0, 0.6), rot=(0, -0.3, 0))
    # Through the hatch: the dusk sky, the grip and the cable.
    reb.prim("cube", "Hatch sky", reb.mat_emit("Hatch sky", (0.45, 0.25, 0.2), 0.8), ((hx0 + hx1) / 2, (hy0 + hy1) / 2, H + 2.5), (1.2, 1.2, 0.01))
    # Grab handles on the hatch rim, and a boot scuff on the bench under it: the way up.
    for y in (hy0 + 0.12, hy1 - 0.12):
        struts("Hatch handle", mat("yellow paint"), [((hx0 + 0.05, y, H - 0.05), (hx0 + 0.05, y, H - 0.17)), ((hx0 + 0.05, y, H - 0.17), (hx0 + 0.25, y, H - 0.17)), ((hx0 + 0.25, y, H - 0.17), (hx0 + 0.25, y, H - 0.05))], 0.012)
    kit.splat("Boot scuff on the bench", mat("mud"), (X1 - 0.22, (hy0 + hy1) / 2, 0.445), 0.08, seed=7, stretch=(1.0, 1.8))
    reb.prim("cube", "EMERGENCY EXIT plate", mat("yellow paint"), (hx0 - 0.25, (hy0 + hy1) / 2, H - 0.002), (0.3, 0.12, 0.004))
    # Door: two leaves, shut, glass smeared, the inside clawed.
    for i, (x0, x1) in enumerate(((DOOR[0], (DOOR[0] + DOOR[1]) / 2), ((DOOR[0] + DOOR[1]) / 2, DOOR[1]))):
        reb.prim("cube", f"Door leaf {i}", red, ((x0 + x1) / 2, Y0 - 0.04, WIN[0] / 2), (x1 - x0 - 0.01, 0.05, WIN[0]))
        reb.prim("cube", f"Door glass {i}", glass, ((x0 + x1) / 2, Y0 - 0.04, (WIN[0] + WIN[1]) / 2), (x1 - x0 - 0.01, 0.01, WIN[1] - WIN[0]))
    reb.prim("cube", "Door seam", mat("black"), ((DOOR[0] + DOOR[1]) / 2, Y0 - 0.01, 1.0), (0.012, 0.01, 1.9))
    kit.scratches("Claw marks", mat("black"), ((DOOR[0] + DOOR[1]) / 2 - 0.15, Y0 - 0.008, 0.9), (0, 1), count=5, length=0.55, seed=1)
    kit.scratches("Claw marks", mat("black"), ((DOOR[0] + DOOR[1]) / 2 + 0.2, Y0 - 0.008, 0.85), (0, 1), count=4, length=0.45, seed=2)
    for i in range(5):
        kit.splat(f"Hand on the door glass {i}", mat("blood"), (DOOR[0] + 0.15 + i * 0.16, Y0 - 0.032, 1.15 + rng.uniform(-0.1, 0.35)), 0.055, rot=(math.pi / 2, 0, 0), seed=10 + i, stretch=(0.7, 1.5), lumps=0.5)
    for i in range(4):
        x = rng.uniform(X0 + 0.2, X1 - 0.2)
        kit.splat(f"Smear on the south glass {i}", mat("old blood"), (x, Y1 + 0.065, 1.35 + rng.uniform(-0.2, 0.25)), 0.12, rot=(math.pi / 2, 0, 0), seed=20 + i, stretch=(0.6, 2.0), lumps=0.5)
    for i in range(3):
        y = rng.uniform(Y0 + 0.2, Y1 - 0.2)
        kit.splat(f"Smear on the west glass {i}", mat("old blood"), (X0 - 0.065, y, 1.3 + rng.uniform(-0.2, 0.3)), 0.12, rot=(0, math.pi / 2, 0), seed=30 + i, stretch=(2.0, 0.6), lumps=0.5)
    reb.prim("cube", "Intercom", mat("steel"), (DOOR[1] + 0.25, Y0 + 0.005, 1.5), (0.16, 0.01, 0.22))
    call_m = reb.mat_emit("Call button", (1.0, 0.1, 0.05), 3)
    reb.prim("cyl", "Call button", call_m, (DOOR[1] + 0.25, Y0 + 0.012, 1.45), (0.04, 0.04, 0.01), rot=(math.pi / 2, 0, 0), segments=10)
    reb.prim("cube", "Car plate", mat("white paint"), (X1 - 0.005, (Y0 + Y1) / 2, 1.92), (0.01, 0.6, 0.12))
    kit.text("Car plate words", "CAR 4   MAX 6", mat("black"), (X1 - 0.012, (Y0 + Y1) / 2, 1.92), size=0.06, rot=(math.pi / 2, 0, -math.pi / 2))

    # ---- The benches; hers on the west, soaked.
    for x, side in ((X0 + 0.22, -1), (X1 - 0.22, 1)):
        b = reb.prim("cube", "Bench", seat, (x, (Y0 + Y1) / 2, 0.38), (0.44, Y1 - Y0, 0.12), bevel=0.03)
        reb.mask(reb.wall(b))
        reb.prim("cube", "Bench base", alu, (x + side * 0.05, (Y0 + Y1) / 2, 0.16), (0.32, Y1 - Y0 - 0.1, 0.32))
        reb.prim("cube", "Bench back", seat, (x + side * 0.2, (Y0 + Y1) / 2, 0.68), (0.06, Y1 - Y0, 0.45), rot=(0, side * -0.1, 0), bevel=0.02)
    reb.prim("cube", "Torn cushion", reb.mat_plain("Foam", (0.45, 0.4, 0.22), 0.9), (X0 + 0.25, 1.55, 0.45), (0.2, 0.25, 0.04), rot=(0.1, 0.1, 0.3))
    kit.splat("Blood on her seat", mat("blood"), (X0 + 0.24, 1.7, 0.445), 0.2, seed=3, stretch=(0.9, 1.6))
    kit.splat("Pool under the bench", mat("blood"), (X0 + 0.55, 1.75, 0.0), 0.32, seed=4, stretch=(0.9, 1.4))
    kit.drag_trail("Dragged to the door", mat("old blood"), [(X0 + 0.6, 1.8), (1.75, 1.5), (2.05, 1.08)], width=0.35, seed=5)
    reb.prim("cube", "Drip down the bench", mat("blood"), (X0 + 0.44, 1.72, 0.25), (0.005, 0.04, 0.25))
    # The bandage the keeper put on her, unwound.
    bv, bf = [], []
    pts = [(X0 + 0.5, 2.0), (1.8, 2.15), (2.2, 1.95), (2.45, 2.2), (2.6, 2.05)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        d = Vector((bx - ax, by - ay))
        side = Vector((-d.y, d.x)).normalized() * 0.03
        k = len(bv)
        bv += [(ax - side.x, ay - side.y, 0.004), (ax + side.x, ay + side.y, 0.004), (bx + side.x, by + side.y, 0.004), (bx - side.x, by - side.y, 0.004)]
        bf.append((k, k + 1, k + 2, k + 3))
    reb.mesh_object("Unwound bandage", bv, bf, bandage, smooth=False)
    reb.prim("cube", "Safety pin", mat("steel"), (2.62, 2.08, 0.006), (0.03, 0.006, 0.004), rot=(0, 0, 0.4))
    # Her handbag, spilled; her shoe; the ticket.
    reb.prim("cube", "Handbag", bag_m, (2.55, 1.3, 0.1), (0.32, 0.12, 0.22), rot=(0.0, 1.35, 0.4), bevel=0.03)
    kit.rod("Bag strap", bag_m, (2.45, 1.2, 0.02), (2.8, 1.55, 0.02), 0.008, 4)
    reb.prim("cube", "Wallet, open", reb.mat_plain("Wallet", (0.05, 0.03, 0.02), 0.6), (2.25, 1.35, 0.008), (0.2, 0.1, 0.012), rot=(0, 0, 0.9))
    reb.prim("cube", "Driving licence", reb.mat_plain("Licence", (0.55, 0.52, 0.4), 0.5), (2.2, 1.3, 0.016), (0.085, 0.055, 0.002), rot=(0, 0, 0.9))
    reb.prim("cyl", "Lipstick", mat("black"), (2.75, 1.2, 0.012), (0.018, 0.018, 0.07), rot=(math.pi / 2, 0, 0.3), segments=8)
    reb.prim("cyl", "Compact", mat("steel"), (2.4, 1.15, 0.008), (0.07, 0.07, 0.012), segments=14)
    reb.prim("cyl", "Pill bottle", reb.mat_plain("Amber", (0.35, 0.15, 0.02), 0.2), (2.65, 1.45, 0.02), (0.035, 0.035, 0.07), rot=(math.pi / 2, 0, 1.2), segments=8)
    kit.papers("Tissues", (2.35, 1.6, 0.0), spread=0.2, count=3, seed=4, m=mat("paper"))
    reb.prim("cube", "Car keys tag", mat("red paint"), (2.85, 1.12, 0.006), (0.05, 0.025, 0.004), rot=(0, 0, 0.5))
    reb.prim("cube", "Shoe", reb.mat_plain("Shoe", (0.04, 0.03, 0.03), 0.3), (X0 + 0.3, 2.15, 0.04), (0.24, 0.08, 0.06), rot=(0, 0, 0.4), bevel=0.02)
    kit.rod("Shoe heel", reb.mat_plain("Shoe", (0.04, 0.03, 0.03), 0.3), (X0 + 0.2, 2.1, 0.0), (X0 + 0.2, 2.1, 0.08), 0.008, 5)
    reb.prim("cube", "Ticket stub", mat("yellow paint"), (2.05, 2.2, 0.004), (0.08, 0.04, 0.002), rot=(0, 0, 1.1))
    reb.prim("cyl", "Extinguisher", mat("red paint"), (X1 - 0.65, 2.22, 0.075), (0.15, 0.15, 0.5), rot=(math.pi / 2, 0, 1.3), segments=14)
    reb.prim("cube", "Empty extinguisher bracket", mat("steel"), (X1 - 0.005, 2.1, 0.75), (0.01, 0.12, 0.2))
    # A rail under the ceiling, its straps hanging.
    kit.rod("Grab rail", alu, (X0 + 0.5, (Y0 + Y1) / 2, H - 0.12), (X1 - 0.5, (Y0 + Y1) / 2, H - 0.12), 0.015)
    straps = []
    for i in range(4):
        x = X0 + 0.6 + i * 0.4
        if hx0 - 0.1 < x < hx1 + 0.1:
            continue
        p = reb.prim("sphere", f"Strap pivot {i}", alu, (x, (Y0 + Y1) / 2, H - 0.12), (0.02, 0.02, 0.02), segments=6)
        s = kit.rod(f"Strap {i}", mat("black"), (0, 0, 0), (0, 0, -0.22), 0.012, 4)
        r = reb.prim("cyl", f"Strap loop {i}", mat("black"), (0, 0, -0.27), (0.1, 0.02, 0.1), rot=(math.pi / 2, 0, 0), segments=10)
        s.parent = p
        r.parent = p
        straps.append(p)
    lamp_m = reb.mat_emit("Emergency lamp", (1.0, 0.8, 0.55), 1.2)
    reb.prim("cube", "Emergency lamp", lamp_m, (2.1, (Y0 + Y1) / 2, H - 0.02), (0.3, 0.12, 0.03))
    lamp = reb.point("Emergency lamp light", (2.1, (Y0 + Y1) / 2, H - 0.15), 4, (1.0, 0.8, 0.55), 0.05)

    # ---- Outside, all of it on the sway: the cable, the pylon ahead, crows, the forest far below, the valley.
    before = set(bpy.data.objects)
    kit.rod("Hanger arm", mat("iron"), ((X0 + X1) / 2, (Y0 + Y1) / 2, H + 0.15), GRIP, 0.05)
    reb.prim("cube", "Grip", mat("iron"), GRIP, (0.5, 0.3, 0.25))
    kit.rod("Haul cable, up the mountain", mat("iron"), GRIP, GRIP + Vector((0, -150, 95)), 0.025, 6)
    kit.rod("Haul cable, to the pylon", mat("iron"), GRIP, (PYLON[0], PYLON[1], 3.25), 0.025, 6)
    kit.rod("Haul cable, on down", mat("iron"), (PYLON[0], PYLON[1], 3.25), (PYLON[0], 160, -60), 0.025, 6)
    kit.rod("Return cable", mat("iron"), (PYLON[0] - 5.0, -150, 98), (PYLON[0] - 5.0, PYLON[1], 3.25), 0.025, 6)
    kit.rod("Return cable, on down", mat("iron"), (PYLON[0] - 5.0, PYLON[1], 3.25), (PYLON[0] - 5.0, 160, -60), 0.025, 6)
    px, py = PYLON
    gz = ground(px, py)
    segs = []
    legs = [(-2.6, -2.0), (2.6, -2.0), (2.6, 2.0), (-2.6, 2.0)]
    def leg(i, z):
        f = (z - gz) / (2.0 - gz)
        dx, dy = legs[i]
        return (px + dx * (1 - 0.7 * f), py + dy * (1 - 0.7 * f), z)
    z = gz
    while z < 2.0:
        z2 = min(2.0, z + 3.0)
        for i in range(4):
            segs.append((leg(i, z), leg(i, z2)))
            segs.append((leg(i, z2), leg((i + 1) % 4, z2)))
            segs.append((leg(i, z), leg((i + 1) % 4, z2)))
        z = z2
    struts("Pylon tower", reb.mat_surface("Pylon grey", [(0.0, (0.25, 0.26, 0.26)), (1.0, (0.4, 0.38, 0.35))], scale=6, rough=0.6, bump=0.2), segs, 0.07)
    reb.prim("cube", "Crossarm", mat("iron"), (px - 2.5, py, 3.0), (8.0, 0.4, 0.4))
    reb.prim("cube", "Service platform", reb.mat_surface("Grating", [(0.0, (0.06, 0.06, 0.06)), (1.0, (0.2, 0.2, 0.19))], scale=40, rough=0.6, bump=0.8), (px - 2.5, py - 0.9, 2.1), (8.0, 1.2, 0.06))
    rail = []
    for x in [px - 6.4 + i * 0.8 for i in range(11)]:
        rail.append(((x, py - 1.48, 2.1), (x, py - 1.48, 3.1)))
    rail.append(((px - 6.5, py - 1.48, 3.1), (px + 1.5, py - 1.48, 3.1)))
    rail.append(((px - 6.5, py - 1.48, 2.6), (px + 1.5, py - 1.48, 2.6)))
    struts("Platform rail", mat("yellow paint"), rail, 0.025)
    for dx in (0.0, -5.0):
        for k in range(4):
            reb.prim("cyl", "Sheave", mat("rust"), (px + dx, py - 0.6 + k * 0.4, 3.32), (0.3, 0.3, 0.08), rot=(0, math.pi / 2, 0), segments=14)
    rail_crow, _ = kit.crow("Crow on the pylon rail", (px - 1.2, py - 1.48, 3.13), heading=math.pi / 2 + 0.4)
    kit.crow("Crow on the crossarm", (px - 3.8, py, 3.2), heading=math.pi / 2 - 0.2)
    kit.crow("Crow on the platform", (px + 0.8, py - 0.8, 2.13), heading=2.0)
    kit.crow("Crow on the cable", (2.2, 4.2, 3.32), heading=-math.pi / 2)
    # The forest far below, the valley beyond, mist in it.
    reb.terrain("Valley floor", mat("grass"), (-140, 140), (-140, 160), ground, step=4.0)

    def keep_out(x, y):
        return abs(x - px) < 4 and abs(y - py) < 4
    cone_trees("Spruces below", rng, (-100, -90, 100, 120), keep_out, 1500, 3.2, (14, 22))
    vbefore = set(bpy.data.objects)
    kit.vista(rng, (2.0, 1.7), (0.0, 1.0), below=-130.0, far=(200, 450), haze=(0.32, 0.2, 0.22))
    kit.vista(rng, (2.0, 1.7), (-1.0, 0.0), below=-230.0, far=(220, 450), haze=(0.4, 0.22, 0.18))
    kit.vista(rng, (2.0, 1.7), (1.0, 0.0), below=-130.0, far=(200, 450), haze=(0.22, 0.16, 0.22))
    kit.vista(rng, (2.0, 1.7), (0.0, -1.0), below=-60.0, far=(140, 300), haze=(0.22, 0.16, 0.2))
    for ob in set(bpy.data.objects) - vbefore:
        ob.visible_shadow = False
        if ob.name.startswith("Valley floor"):
            ob.hide_render = True
    outside = [ob for ob in set(bpy.data.objects) - before if ob.parent is None]
    view = bpy.data.objects.new("View pivot", None)
    bpy.context.scene.collection.objects.link(view)
    view.location = GRIP
    bpy.context.view_layer.update()
    for ob in outside:
        ob.parent = view
        ob.matrix_parent_inverse = view.matrix_world.inverted()

    # ---- Light: the sun going down in the west, orange through the glass; the emergency lamp.
    sun = kit.time_light("dusk", sun_heading=275, sun_energy=3.0)
    mist_m = mist_card_mat("Valley mist", (0.55, 0.42, 0.42), 0.7, 0.03)
    for i, (x, y, z, w) in enumerate(((2.0, 10.0, GROUND + 14, 160), (-40.0, 40.0, GROUND + 10, 140), (50.0, 30.0, GROUND + 12, 140), (10.0, 70.0, GROUND + 9, 160), (10.0, -50.0, GROUND + 16, 140))):
        ob = reb.prim("plane", f"Valley mist {i}", mist_m, (x, y, z), (w, w, 1), rot=(0, 0, rng.uniform(0, 3)))
        ob.visible_shadow = False
        ob.parent = view
        ob.matrix_parent_inverse = view.matrix_world.inverted()
    sun.visible_glossy = False
    sun.visible_transmission = False
    for nd in bpy.context.scene.world.node_tree.nodes:
        if nd.type == "MIX" and nd.blend_type == "ADD":
            nd.inputs["B"].default_value = (0.3, 0.1, 0.03, 1)  # the sun's glow orange, not white
    low = reb.spot("Low sun through the west glass", (X0 + 0.05, 1.7, 1.9), (X1, 1.6, 0.3), 60, (1.0, 0.5, 0.25), 70, 0.7, 0.05)
    low.visible_camera = False
    low.visible_glossy = False
    # The glass lets the sun in: it casts no shadow.
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob.data.materials and ob.data.materials[0] == glass:
            ob.visible_shadow = False

    anim = kit.Anim(16)
    anim.custom(lambda k: setattr(view, "rotation_euler", (math.radians(1.6) * math.sin(anim.phase(k)), math.radians(0.6) * math.cos(anim.phase(k)), 0)))
    for p in straps:
        anim.custom(lambda k, p=p: setattr(p, "rotation_euler", (-math.radians(5) * math.sin(anim.phase(k)), 0, 0)))
    anim.flicker(lamp, lamp_m, depth=0.5, dropouts=3)
    anim.custom(lambda k: setattr(rail_crow, "rotation_euler", (0, 0.5 * max(0.0, math.sin(anim.phase(k, 2))), math.pi / 2 + 0.4)))
    anim.flies((X0 + 0.5, 1.75, 0.05), count=7, radius=0.25)

    # ---- What the game needs.
    room.door("platform", (DOOR[0], Y0, DOOR[1], Y0 + 0.45), arrive=(2.05, 1.75), face=(0, 1))
    room.door("pylon", (2.45, hy0, X1 - 0.44, hy1), arrive=(2.0, 1.75), face=(-1, 0))
    room.check((X0, Y0, X0 + 0.9, Y1), "Her seat. Soaked through.\nShe sat here bleeding all the way up.")
    room.check((2.1, Y0 + 0.05, X1 - 0.45, 1.6), "A handbag, spilled. A wallet: a driving licence for a Linda Pryce, Raccoon City.\nThe car keys aren't in it.")
    room.check((1.5, 1.9, 2.4, Y1), "A bandage, unwound. Someone dressed a bite on her wrist.\nIt didn't help.")
    # In front of the door, which takes its own zone.
    room.check((DOOR[0], Y0 + 0.45, DOOR[1], Y0 + 0.9), "Claw marks on the inside of the door. Handprints on the glass, all the way up.\nShe was trying to get out.")
    room.check((X1 - 0.5, Y0, X1, Y1), "CAR 4. MAX 6.")
    room.entry = "It's stopped. We're hanging over the trees.\nThere's a pylon right ahead."
    room.export(anim)


build()
