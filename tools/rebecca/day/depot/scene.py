"""The logging camp's fuel depot, noon: a fenced compound of diesel.

What it tells: the camp ran on diesel, and the depot kept count of every
gallon. The last entries on the fuel ledger stop mid-week. The tank's hose
reel is chained and padlocked, so nobody could drain it and run; the
nozzle still drips into the oil soaked into the gravel under it. Something
came under the wire at the back: the dirt is dug out under the fence and
the wire bent up, clawed, with blood on the bent wire. In the weeds along
the fence and between the drums lie the papery skins adders have shed:
they like the warm drums. A player should learn that the dogs get in, that
the snakes are about, and that the fuel is locked away.

Metres: the floor is x 1.0-9.6, y 1.0-6.8, the compound inside its chain
link (in the yard this is x -2.0-6.6, y 15.2-21.0: moved 3 east, 14.2
north). The gate is in the north fence at x 5.6-7.4, shut, its chain cut:
she opens it with the action button. The tank lies on its stand along x
3.9-7.3 at y 5.2, its pump and hose reel at the east end; drums stand in the
north-west and the south-east corners; the lean-to is in the south-west
corner, x 1.0-2.6, y 5.0-6.8; the dug-out wire is in the east fence at y
2.9-3.9. Beyond the north fence is the yard as the yard's own scene builds
it: the mess hall, the skidder, the office and bunkhouse, the sawmill, the
workshop and the camp gate.

Moving: diesel dripping from the hung nozzle, the NO SMOKING sign stirring
on one wire. The weeds and grass are still: no wind reaches the camp.
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

X0, X1, Y0, Y1 = 1.0, 9.6, 1.0, 6.8
GATE = (5.6, 7.4)
TANK = (3.9, 7.3, 5.2, 1.6)   # x0, x1, y, centre height
NOZZLE = (7.85, 4.35, 1.05)
YARD = (3.0, -14.2)           # the yard's scene, moved onto this one's floor
T = 0.12


def Y(x, y):
    """A point of the yard's scene in this one's metres."""
    return x + YARD[0], y + YARD[1]


def height(x, y):
    """The compound and the yard flat; the slope rising south and west into the trees."""
    h = -0.02 + 0.012 * noise.noise(Vector((x * 0.7, y * 0.7, 5)))
    if y > Y1 + 2.0:
        h += (y - Y1 - 2.0) * 0.3 + 0.4 * noise.noise(Vector((x * 0.1, y * 0.1, 2)))
    if x < X0 - 4.0:
        h += (X0 - 4.0 - x) * 0.3
    return h


def far_land(x, y, z):
    """The kit's ranges, eased into the mountainside round the camp."""
    r = math.hypot(x - 5.0, y - 4.0)
    w = max(0.0, min(1.0, (240.0 - r) / 180.0))
    own = height(x, y) - 0.5
    return z + (own - z) * w * w * (3 - 2 * w)


def chain_link():
    """Wire mesh you can see through: mostly transparent, grey where the wire is."""
    m, nodes, links, bsdf = reb.nodes_material("Chain link")
    bsdf.inputs["Base Color"].default_value = (0.09, 0.09, 0.085, 1)
    bsdf.inputs["Metallic"].default_value = 0.6
    bsdf.inputs["Roughness"].default_value = 0.5
    out = nodes["Material Output"]
    clear = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    n = reb.noise_tex(nodes, links, 3, 4, 0.5)
    r = reb.ramp(nodes, links, n.outputs["Fac"], [(0.3, (0.72, 0.72, 0.72)), (0.7, (0.88, 0.88, 0.88))])
    links.new(r.outputs["Color"], mix.inputs["Fac"])
    links.new(bsdf.outputs["BSDF"], mix.inputs[1])
    links.new(clear.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return m


def tube(verts, faces, path, r, seg=6, taper=True):
    """A thin tube along a path of 3D points (a shed skin, a hose), into one mesh."""
    pts = [Vector(p) for p in path]
    k0 = len(verts)
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        u = d.orthogonal().normalized()
        w = d.cross(u)
        rr = r * (1.0 - 0.7 * (i / (len(pts) - 1)) ** 2) if taper else r
        for j in range(seg):
            a = 2 * math.pi * j / seg
            verts.append(tuple(p + (u * math.cos(a) + w * math.sin(a)) * rr))
    for i in range(len(pts) - 1):
        for j in range(seg):
            a, b = k0 + i * seg + j, k0 + i * seg + (j + 1) % seg
            faces.append((a, b, b + seg, a + seg))


def oil_spill(name, m, at, r, heading, seed=0):
    """Oil that splashed and soaked in: a ragged main stain trailing off in
    one direction into smaller blots and drops, not one round pool."""
    rng = random.Random(seed)
    x, y, z = at
    d = Vector((math.cos(heading), math.sin(heading)))
    kit.splat(name, m, (x, y, z), r, rot=(0, 0, heading), seed=seed, stretch=(1.5, 0.7), lumps=0.6)
    for i in range(6):
        t = r * (0.9 + i * 0.45)
        p = Vector((x, y)) + d * t + Vector((-d.y, d.x)) * rng.uniform(-0.4, 0.4) * r
        kit.splat(f"{name} blot {i}", m, (p.x, p.y, z + 0.0005), r * rng.uniform(0.12, 0.3) * (1 - i * 0.1), rot=(0, 0, rng.uniform(0, 6)), seed=seed * 13 + i, lumps=0.6)


def hose_reel(at, chained=True):
    """A fuel hose reel on its A-frame stand, axle along y: two spoked side
    discs, the hose wound round the drum in turns, a crank on the near side,
    and a chain through the spokes, padlocked."""
    x, y, z = at
    parts = []
    hose_v, hose_f = [], []
    # The stand: two A-frames of angle iron on a base, the axle across.
    for dy in (-0.26, 0.26):
        for dx in (-0.32, 0.32):
            parts.append(kit.rod("Reel stand", mat("rust"), (x + dx, y + dy, 0.0), (x, y + dy, z), 0.025, 6))
        parts.append(kit.rod("Reel foot", mat("rust"), (x - 0.38, y + dy, 0.02), (x + 0.38, y + dy, 0.02), 0.025, 6))
    parts.append(kit.rod("Reel axle", mat("iron"), (x, y - 0.34, z), (x, y + 0.34, z), 0.025, 8))
    # The side discs: a rim and six spokes each.
    for dy in (-0.2, 0.2):
        rim_v, rim_f = [], []
        ring = [(x + 0.42 * math.cos(2 * math.pi * k / 24), y + dy, z + 0.42 * math.sin(2 * math.pi * k / 24)) for k in range(25)]
        tube(rim_v, rim_f, ring, 0.018, seg=6, taper=False)
        parts.append(reb.mesh_object("Reel rim", rim_v, rim_f, mat("rust")))
        for k in range(6):
            a = 2 * math.pi * k / 6 + 0.2
            parts.append(kit.rod("Reel spoke", mat("rust"), (x, y + dy, z), (x + 0.42 * math.cos(a), y + dy, z + 0.42 * math.sin(a)), 0.012, 4))
    parts.append(reb.prim("cyl", "Reel drum", mat("iron"), (x, y, z), (0.32, 0.32, 0.38), rot=(math.pi / 2, 0, 0), segments=16))
    # The hose, wound on in turns, each a little further out.
    for turn in range(6):
        r = 0.2 + 0.03 * (turn // 3)
        dy = -0.15 + 0.06 * (turn % 6)
        pts = [(x + r * math.cos(2 * math.pi * k / 20), y + dy, z + r * math.sin(2 * math.pi * k / 20)) for k in range(21)]
        tube(hose_v, hose_f, pts, 0.03, seg=8, taper=False)
    parts.append(reb.mesh_object("Reel hose", hose_v, hose_f, mat("rubber")))
    parts.append(kit.rod("Crank arm", mat("iron"), (x, y - 0.34, z), (x + 0.22, y - 0.36, z - 0.12), 0.015, 6))
    parts.append(reb.prim("cyl", "Crank knob", mat("black"), (x + 0.22, y - 0.42, z - 0.12), (0.05, 0.05, 0.12), rot=(math.pi / 2, 0, 0), segments=8))
    reel = kit.join("Hose reel", parts)
    if chained:
        lv = [(x + 0.3 * math.cos(2 * math.pi * k / 10), y - 0.22, z + 0.3 * math.sin(2 * math.pi * k / 10)) for k in range(11)]
        cv, cf = [], []
        tube(cv, cf, lv, 0.012, seg=5, taper=False)
        tube(cv, cf, [(x + 0.3, y - 0.22, z), (x + 0.36, y - 0.3, z - 0.25), (x + 0.32, y - 0.3, z - 0.5), (x + 0.25, y - 0.26, 0.02)], 0.012, seg=5, taper=False)
        reb.mesh_object("Reel chain", cv, cf, mat("iron"))
        reb.prim("cube", "Padlock", mat("steel"), (x + 0.36, y - 0.3, z - 0.3), (0.07, 0.03, 0.09), bevel=0.01)
    return reel


def build():
    rng = random.Random(61)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("gravel")
    cams = [
        ((9.3, 1.25, 3.3), (4.2, 5.0, 0.3), "from the north-east corner by the gate: the tank, the nozzle dripping, the lean-to"),
        ((9.3, 6.6, 3.2), (6.0, 1.5, 0.3), "from the south-east drums: the shut gate out to the yard, the mess hall beyond"),
        ((1.3, 1.3, 3.2), (7.6, 5.2, 0.3), "from the north-west drums: the pump and the padlocked reel, the drums in the corner"),
    ]
    for eye, look, note in cams:
        room.camera(eye, look, 200, note)

    # ---- Materials.
    gravel = kit.dirtied(reb.mat_surface("Depot gravel", [(0.0, (0.04, 0.032, 0.024)), (0.3, (0.1, 0.085, 0.065)), (0.5, (0.19, 0.17, 0.14)), (0.65, (0.12, 0.1, 0.075)), (0.85, (0.25, 0.23, 0.2)), (1.0, (0.08, 0.07, 0.05))], scale=7, detail=12, rough=0.8, bump=1.0), 0.9, scale=0.45)
    yard_earth = kit.dirtied(reb.mat_surface("Yard earth", [(0.0, (0.03, 0.022, 0.014)), (0.3, (0.06, 0.045, 0.03)), (0.55, (0.1, 0.078, 0.052)),
                                                            (0.75, (0.085, 0.07, 0.05)), (1.0, (0.13, 0.11, 0.08))], scale=1.6, detail=14, rough=0.75, bump=0.7), 0.7, scale=0.35)
    oil = reb.mat_surface("Oil soak", [(0.0, (0.008, 0.007, 0.006)), (0.6, (0.02, 0.017, 0.013)), (1.0, (0.04, 0.034, 0.026))], scale=10, rough=0.35, bump=0.15)
    wet_oil = reb.mat_surface("Wet diesel", [(0.0, (0.006, 0.005, 0.004)), (1.0, (0.02, 0.017, 0.013))], scale=12, rough=0.12, bump=0.05)
    tank_m = reb.mat_surface("Tank green", [(0.0, (0.06, 0.09, 0.05)), (0.6, (0.1, 0.14, 0.09)), (0.85, (0.22, 0.1, 0.04)), (1.0, (0.12, 0.06, 0.03))], scale=3, rough=0.5, bump=0.2)
    wire = chain_link()
    skin = reb.mat_surface("Shed skin", [(0.0, (0.35, 0.33, 0.27)), (1.0, (0.55, 0.52, 0.44))], scale=60, rough=0.6, bump=0.4)
    stencil_m = kit.dirtied(reb.mat_plain("Stencil white", (0.5, 0.48, 0.42), 0.6), 0.6, scale=20)

    # ---- Ground: gravel inside the wire, worn to earth where she walks and soaked with oil; the yard's earth outside.
    reb.terrain("Ground", yard_earth, (-30, 40), (-30, 40), height, step=0.5)
    gv, gf = [], []
    for j in range(30):
        for i in range(44):
            x, y = X0 - 0.1 + i * 0.2, Y0 - 0.1 + j * 0.2
            k = len(gv)
            for dx, dy in ((0, 0), (0.2, 0), (0.2, 0.2), (0, 0.2)):
                gv.append((x + dx, y + dy, height(x + dx, y + dy) + 0.006))
            gf.append((k, k + 1, k + 2, k + 3))
    reb.mesh_object("Gravel", gv, gf, gravel, smooth=False)
    kit.ruts("Tyre tracks in", [(6.4, -6.0), (6.5, -1.0), (6.3, 1.6), (5.6, 3.4)], height, gauge=1.5, width=0.24, seed=3.0)
    kit.dirt_path("Worn to the pump", [(6.5, 1.2), (7.2, 2.6), (7.9, 3.7)], height, width=0.9)
    oil_spill("Oil soaked under the tank", oil, (5.4, 4.6, height(5.4, 4.6) + 0.007), 0.9, 2.9, seed=1)
    oil_spill("Diesel under the nozzle", wet_oil, (NOZZLE[0], NOZZLE[1] + 0.05, height(*NOZZLE[:2]) + 0.009), 0.28, 2.0, seed=2)
    for i in range(5):
        x, y = rng.uniform(2, 9), rng.uniform(1.5, 6)
        oil_spill(f"Oil stain {i}", oil, (x, y, height(x, y) + 0.007), rng.uniform(0.12, 0.3), rng.uniform(0, 6), seed=10 + i)
    stones = [(rng.uniform(X0, X1), rng.uniform(Y0, Y1), rng.uniform(0.02, 0.07)) for _ in range(140)]
    stones += [(rng.uniform(-6, 16), rng.uniform(-8, 0.6), rng.uniform(0.04, 0.1)) for _ in range(40)]
    kit.rocks("Stones", rng, stones, height, kit.dirtied(mat("rock"), 0.7), grass=False)

    # ---- The fence: chain link on rusty posts, the gate shut, the dug-out wire at the back.
    posts = []
    for (a, b) in (((X0 - 0.1, Y0), (GATE[0], Y0)), ((GATE[1], Y0), (X1 + 0.1, Y0)), ((X1 + 0.1, Y0), (X1 + 0.1, Y1 + 0.1)), ((X1 + 0.1, Y1 + 0.1), (X0 - 0.1, Y1 + 0.1)), ((X0 - 0.1, Y1 + 0.1), (X0 - 0.1, Y0))):
        a, b = Vector(a), Vector(b)
        d = b - a
        n = int(d.length / 2.0) + 1
        for i in range(n + 1):
            p = a.lerp(b, i / n)
            posts.append(kit.rod("Fence post", mat("rust"), (p.x, p.y, 0), (p.x, p.y, 2.1), 0.035, 6))
        kit.rod("Fence top rail", mat("rust"), (a.x, a.y, 2.0), (b.x, b.y, 2.0), 0.02, 6)
        horiz = abs(d.x) > abs(d.y)
        if not horiz and a.x > X1 and min(a.y, b.y) < 3.4 < max(a.y, b.y):
            lo, hi = min(a.y, b.y), max(a.y, b.y)
            for y0, y1 in ((lo, 2.9), (3.9, hi)):
                reb.prim("cube", "Fence wire", wire, (a.x, (y0 + y1) / 2, 1.0), (0.02, y1 - y0, 2.0))
            reb.prim("cube", "Fence wire over the hole", wire, (a.x, 3.4, 1.25), (0.02, 1.0, 1.5))
            reb.prim("cube", "Wire bent up", wire, (a.x + 0.15, 3.4, 0.38), (0.02, 1.0, 0.5), rot=(0, 0.6, 0))
        else:
            reb.prim("cube", "Fence wire", wire, ((a.x + b.x) / 2, (a.y + b.y) / 2, 1.0), (d.length if horiz else 0.02, 0.02 if horiz else d.length, 2.0))
    kit.join("Fence posts", posts)
    kit.splat("Dug-out dirt", kit.dirtied(mat("dirt"), 0.5), (X1 + 0.35, 3.4, height(X1 + 0.35, 3.4) + 0.012), 0.45, seed=6, stretch=(0.8, 1.4), lumps=0.6)
    reb.prim("cube", "The hole under the wire", mat("black"), (X1 + 0.1, 3.4, -0.04), (0.5, 0.9, 0.08))
    kit.scratches("Claw marks on the post", mat("black"), (X1 + 0.08, 2.9, 0.9), (-1, 0), count=4, length=0.4, seed=7)
    kit.splat("Blood on the bent wire", mat("old blood"), (X1 + 0.12, 3.35, 0.45), 0.1, rot=(0, math.pi / 2 - 0.6, 0), seed=8, stretch=(1.2, 0.8))
    # The gate: two leaves of galvanised pipe, braced, shut across the gap, the chain cut and hanging.
    galv = kit.dirtied(reb.mat_metal("Galvanised pipe", (0.42, 0.43, 0.42), 0.45), 0.6, scale=8)
    for x in GATE:
        reb.mask(reb.wall(kit.rod("Gate post", galv, (x, Y0, 0), (x, Y0, 2.3), 0.07, 10), "circle"))
        reb.prim("sphere", "Gate post cap", galv, (x, Y0, 2.31), (0.15, 0.15, 0.08), segments=10)
    gmid = (GATE[0] + GATE[1]) / 2
    for a, b in ((GATE[0] + 0.08, gmid - 0.02), (gmid + 0.02, GATE[1] - 0.08)):
        reb.prim("cube", "Gate leaf", wire, ((a + b) / 2, Y0, 1.0), (b - a, 0.02, 1.8))
        for z in (0.12, 1.0, 1.88):
            kit.rod("Gate frame", galv, (a, Y0, z), (b, Y0, z), 0.035, 8)
        for x in (a, b):
            kit.rod("Gate frame", galv, (x, Y0, 0.12), (x, Y0, 1.88), 0.035, 8)
        kit.rod("Gate brace", galv, (a, Y0, 0.12), (b, Y0, 1.0), 0.025, 8)
    cv, cf = [], []
    tube(cv, cf, [(gmid + 0.1, Y0 + 0.03, 1.1), (gmid + 0.06, Y0 + 0.05, 0.9), (gmid + 0.08, Y0 + 0.04, 0.7)], 0.012, seg=5, taper=False)
    tube(cv, cf, [(gmid - 0.1, Y0 + 0.03, 1.1), (gmid - 0.14, Y0 + 0.05, 0.95)], 0.012, seg=5, taper=False)
    reb.mesh_object("Cut chain", cv, cf, mat("iron"))
    reb.prim("cube", "Fuel sign", mat("white paint"), (8.5, Y0 - 0.03, 1.4), (0.9, 0.02, 0.45))
    kit.text("Fuel sign words", "FUEL", mat("red paint"), (8.5, Y0 - 0.045, 1.5), size=0.16)
    kit.text("Fuel sign words 2", "NO NAKED FLAME", mat("red paint"), (8.5, Y0 - 0.045, 1.3), size=0.07)
    hook = reb.prim("sphere", "Sign wire", mat("iron"), (4.6, Y0 + 0.03, 1.9), (0.02, 0.02, 0.02))
    sign = reb.prim("cube", "No smoking", mat("white paint"), (0.2, 0.0, -0.22), (0.6, 0.02, 0.3))
    words = kit.text("No smoking words", "NO SMOKING", mat("red paint"), (0.2, 0.015, -0.22), size=0.08, rot=(math.pi / 2, 0, math.pi))
    sign.parent = hook
    words.parent = hook
    hook.rotation_euler = (0, -0.5, 0)

    # ---- The tank on its stand: DIESEL, the hand pump, the reel chained and locked, the nozzle on its hook.
    tx0, tx1, ty, tz = TANK
    reb.prim("cyl", "Tank", tank_m, ((tx0 + tx1) / 2, ty, tz), (1.4, 1.4, tx1 - tx0), rot=(0, math.pi / 2, 0), segments=24)
    for x in (tx0, tx1):
        reb.prim("cyl", "Tank end", tank_m, (x, ty, tz), (1.44, 1.44, 0.05), rot=(0, math.pi / 2, 0), segments=24)
    for x in (tx0 + 0.5, tx1 - 0.5):
        for dy in (-0.55, 0.55):
            kit.rod("Stand leg", mat("rust"), (x, ty + dy, 0), (x, ty + dy * 0.6, tz - 0.6), 0.05)
        reb.prim("cube", "Cradle", mat("rust"), (x, ty, tz - 0.62), (0.12, 1.3, 0.12))
    reb.mask(reb.wall(reb.prim("cube", "Tank footprint", None, ((tx0 + tx1) / 2, ty, 0.5), (tx1 - tx0, 1.45, 1.0)))).hide_render = True
    kit.text("Tank words", "DIESEL", stencil_m, ((tx0 + tx1) / 2, ty - 0.72, tz + 0.05), size=0.35)
    kit.text("Tank words 2", "1000 GAL", stencil_m, ((tx0 + tx1) / 2, ty - 0.71, tz - 0.3), size=0.12)
    kit.splat("Run down the tank", oil, ((tx0 + tx1) / 2 + 1.2, ty - 0.71, tz - 0.2), 0.18, rot=(math.pi / 2, 0, 0), seed=12, stretch=(0.3, 2.0))
    reb.prim("cyl", "Filler cap", mat("rust"), (tx0 + 0.6, ty, tz + 0.72), (0.2, 0.2, 0.08))
    px = tx1 + 0.45
    kit.rod("Pump pipe", mat("iron"), (tx1, ty, tz - 0.5), (px, ty, tz - 0.5), 0.04)
    pump = kit.box("Hand pump", reb.mat_plain("Pump red", (0.35, 0.05, 0.03), 0.5), (px, ty - 0.05, 0.0), (0.3, 0.3, 1.2), bevel=0.02)
    reb.mask(reb.wall(pump))
    kit.rod("Pump crank", mat("iron"), (px, ty - 0.22, 1.05), (px + 0.3, ty - 0.22, 1.3), 0.02)
    reb.prim("cyl", "Crank knob", mat("black"), (px + 0.3, ty - 0.3, 1.3), (0.05, 0.05, 0.12), rot=(math.pi / 2, 0, 0))
    reb.prim("cyl", "Pump dial", mat("white paint"), (px, ty - 0.21, 0.85), (0.16, 0.16, 0.02), rot=(math.pi / 2, 0, 0))
    rc = Vector((px + 0.15, ty - 0.85, 0.5))
    hose_reel(rc)
    reb.mask(reb.wall(reb.prim("cyl", "Reel footprint", None, rc, (0.85, 0.6, 1.0)), "circle")).hide_render = True
    hv, hf = [], []
    tube(hv, hf, [rc + Vector((-0.2, -0.2, -0.3)), (7.5, 4.6, 0.25), (7.75, 4.4, 0.6), (NOZZLE[0], NOZZLE[1], NOZZLE[2] + 0.15)], 0.03, seg=8, taper=False)
    reb.mesh_object("Hose", hv, hf, mat("rubber"))
    reb.prim("cube", "Nozzle", mat("steel"), (NOZZLE[0], NOZZLE[1], NOZZLE[2] + 0.1), (0.06, 0.06, 0.25), rot=(0.3, 0, 0))
    reb.prim("cube", "Nozzle hook", mat("iron"), (NOZZLE[0], NOZZLE[1] + 0.05, NOZZLE[2] + 0.28), (0.05, 0.1, 0.04))
    reb.prim("cube", "Jerrycan", reb.mat_plain("Jerrycan", (0.28, 0.05, 0.03), 0.5), (7.0, 3.9, 0.17), (0.45, 0.17, 0.34), rot=(math.pi / 2, 0, 0.5), bevel=0.02)
    reb.prim("cone", "Funnel", mat("steel"), (6.6, 3.7, 0.1), (0.22, 0.22, 0.2), rot=(1.4, 0, 0.3), top=0.2)
    oil_spill("Spill from the can", wet_oil, (6.75, 3.65, height(6.75, 3.65) + 0.009), 0.18, 3.6, seed=3)
    reb.prim("cube", "Clipboard", mat("dark wood"), (tx1 - 0.5, ty - 0.68, 1.2), (0.25, 0.02, 0.33), rot=(0.08, 0, 0))
    reb.prim("cube", "Fuel ledger", mat("paper"), (tx1 - 0.5, ty - 0.695, 1.18), (0.22, 0.004, 0.27), rot=(0.08, 0, 0))
    for i in range(6):
        reb.prim("cube", f"Ledger line {i}", mat("black"), (tx1 - 0.52, ty - 0.699, 1.27 - i * 0.035), (0.16 - (0.06 if i > 3 else 0), 0.002, 0.006))
    kit.rod("Clipboard string", mat("canvas"), (tx1 - 0.5, ty - 0.68, 1.37), (tx1 - 0.5, ty - 0.6, 1.62), 0.004, 4)

    # ---- Drums: a pallet of them in the north-west, more stacked in the south-east, one leaking.
    paints = {"red": (0.28, 0.05, 0.03), "green": (0.06, 0.1, 0.05), "blue": (0.04, 0.07, 0.13)}
    for i, (x, y, tipped, colour) in enumerate(((3.2, 2.2, False, "red"), (3.85, 2.3, False, "green"), (3.5, 2.9, False, "red"), (1.55, 3.0, False, "blue"), (1.55, 3.65, False, "red"), (2.1, 4.25, True, "green"),
                                                 (8.6, 5.4, False, "red"), (7.85, 6.35, False, "green"), (9.05, 6.2, False, "blue"), (8.4, 6.25, False, "red"))):
        z = 0.12 if 2.7 < x < 4.3 and y < 3.2 else 0.0
        d = kit.drum(f"Drum {i}", kit.drum_paint(f"Drum paint {i}", paints[colour]), (x, y, z), tipped=tipped, rot=rng.uniform(0, 3) if not tipped else 1.2)
        if not tipped:
            kit.stencil(d, ["DIESEL" if colour != "blue" else "LUBE OIL", f"No 55-{4100 + 37 * i}"], stencil_m, size=0.11, turn=rng.uniform(-0.6, 0.6))
            kit.splat(f"Drum {i} run", oil, (0, -0.292, 0.2), 0.06, rot=(math.pi / 2, 0, 0), seed=40 + i, stretch=(0.4, 2.2)).parent = d
        reb.wall(d, "circle")
        if i in (0, 3, 7):
            reb.mask(d)
    reb.prim("cube", "Pallet", mat("planks"), (3.5, 2.5, 0.06), (1.4, 1.3, 0.12))
    oil_spill("Leak from the tipped drum", wet_oil, (2.6, 4.5, height(2.6, 4.5) + 0.009), 0.3, 0.9, seed=4)
    kit.drum("Drum on top", kit.drum_paint("Drum paint top", paints["red"]), (8.75, 5.95, 0.88), tipped=True, rot=0.3)

    # ---- The lean-to in the south-west: a tin roof on posts, shelves of oil, rags.
    for (x, y) in ((1.0, 5.0), (2.6, 5.0), (1.0, 6.8), (2.6, 6.8)):
        reb.wall(kit.rod("Lean-to post", mat("dark wood"), (x, y, 0), (x, y, 2.45 if y > 6 else 2.15), 0.05), "circle")
    for y in (5.0, 6.8):
        reb.prim("cube", "Lean-to plate", mat("dark wood"), (1.8, y, 2.45 if y > 6 else 2.15), (1.8, 0.1, 0.1))
    reb.prim("cube", "Lean-to roof", mat("tin"), (1.8, 5.9, 2.36), (2.1, 2.3, 0.04), rot=(-math.atan2(0.3, 1.8), 0, 0))
    sh = kit.shelves("Oil shelves", mat("planks"), (1.8, 6.6, 0.0), size=(1.4, 0.35, 1.6), rows=4, clutter=0.9, seed=3)
    reb.wall(sh)
    reb.cloth("Oily rags", oil, (2.2, 5.5, 0.03), (0.4, 0.3), lumps=0.03, seed=2)
    reb.prim("cube", "Grease tin", mat("rust"), (1.6, 5.6, 0.1), (0.2, 0.2, 0.2))

    # ---- The adders' shed skins: in the weeds by the fence, between the drums, on the warm tank stand.
    sv, sf = [], []
    for i, (x, y, z, a) in enumerate(((2.5, 6.5, 0.02, 0.2), (4.3, 2.4, 0.02, 1.9), (5.2, 4.75, 0.02, 0.6), (1.3, 4.7, 0.02, 2.5), (9.3, 4.0, 0.02, 1.4))):
        path = []
        for k in range(12):
            t = k / 11
            u = t * 0.9
            path.append((x + math.cos(a) * u - math.sin(a) * 0.07 * math.sin(t * 9), y + math.sin(a) * u + math.cos(a) * 0.07 * math.sin(t * 9), z + 0.012))
        tube(sv, sf, path, 0.016, seg=6)
    reb.mesh_object("Shed skins", sv, sf, skin)

    # ---- Outside the wire: the yard as its own scene builds it, moved onto this floor.
    tin = reb.mat_surface("Roof tin", [(0.0, (0.16, 0.16, 0.15)), (0.6, (0.26, 0.26, 0.25)), (0.8, (0.3, 0.13, 0.05)), (1.0, (0.18, 0.08, 0.03))], scale=1.6, rough=0.55, bump=0.3)
    frame_m = mat("dark wood")
    glass_m = reb.mat_glass("Grimy glass", (0.32, 0.34, 0.3))

    def shifted(rect):
        (a, b), (c, d) = Y(rect[0], rect[2]), Y(rect[1], rect[3])
        return (a, c, b, d)
    mess = shifted((-3.4, 2.0, 5.0, 14.0))
    kit.hut("Mess", mess, 2.8, kit.boards("Mess boards", (0.42, 0.4, 0.36), width=0.18, grime=0.9), tin,
            [("e", Y(0, 9.0)[1], Y(0, 9.9)[1], 0.0, 2.1), ("e", Y(0, 6.0)[1], Y(0, 7.4)[1], 1.0, 1.9), ("e", Y(0, 11.2)[1], Y(0, 12.6)[1], 1.0, 1.9)], ridge="y", pitch=0.46, thick=T, blocks=False)
    for a, b in ((6.0, 7.4), (11.2, 12.6)):
        kit.hut_window(mess, "e", Y(0, a)[1], Y(0, b)[1], 1.0, 1.9, frame_m, reb.mat_glass("Steamy glass", (0.45, 0.42, 0.36)), thick=T)
    kit.shut_door("Mess door", mess, "e", Y(0, 9.0)[1], Y(0, 9.9)[1], 2.1, mat("white paint"), thick=T)
    cx, cy = Y(-0.4, 6.0)
    reb.prim("cube", "Mess chimney", mat("brick"), (cx, cy, 3.6), (0.6, 0.6, 2.4))
    reb.point("Range glow in the mess", (*Y(0.4, 8.0), 1.6), 25, (1.0, 0.55, 0.25), 0.5)
    office = shifted((1.0, 4.6, 0.6, 3.6))
    kit.hut("Office", office, 2.5, kit.boards("Office boards", (0.08, 0.14, 0.09), width=0.16, grime=0.8), tin, [("s", Y(2.5, 0)[0], Y(3.4, 0)[0], 0.0, 2.05)], ridge="y", pitch=0.5, eaves=0.3, thick=T, blocks=False)
    kit.shut_door("Office door", office, "s", Y(2.5, 0)[0], Y(3.4, 0)[0], 2.05, mat("green paint"), thick=T)
    bunk = shifted((6.0, 17.0, -3.4, 1.6))
    kit.hut("Bunkhouse", bunk, 2.4, kit.boards("Bunkhouse boards", (0.17, 0.11, 0.07), width=0.22, grime=0.8), tin, [("s", Y(11.0, 0)[0], Y(11.9, 0)[0], 0.0, 2.05)], ridge="x", pitch=0.48, thick=T, blocks=False)
    kit.shut_door("Bunkhouse door", bunk, "s", Y(11.0, 0)[0], Y(11.9, 0)[0], 2.05, mat("planks"), thick=T)
    work = shifted((13.4, 19.2, 13.8, 19.4))
    kit.hut("Workshop", work, 3.0, reb.mat_surface("Workshop tin", [(0.0, (0.15, 0.16, 0.15)), (1.0, (0.24, 0.24, 0.23))], scale=3, bump=0.3), tin,
            [("w", Y(0, 15.4)[1], Y(0, 16.6)[1], 1.1, 1.9)], ridge="x", pitch=0.42, thick=T, blocks=False)
    kit.hut_window(work, "w", Y(0, 15.4)[1], Y(0, 16.6)[1], 1.1, 1.9, frame_m, glass_m, thick=T, boarded=True)
    mill = shifted((18.5, 32.0, 2.6, 12.2))
    kit.hut("Sawmill", mill, 6.0, kit.boards("Mill boards", (0.2, 0.19, 0.17), width=0.3, grime=0.8), tin, [], ridge="x", pitch=0.42, thick=T, blocks=False)
    # The skidder, blade down where it stopped.
    yellow = reb.mat_surface("Skidder yellow", [(0.0, (0.3, 0.2, 0.02)), (0.6, (0.5, 0.34, 0.03)), (0.8, (0.25, 0.12, 0.04)), (1.0, (0.08, 0.05, 0.03))], scale=3, rough=0.55, bump=0.2)
    sx, sy = Y(7.95, 13.0)
    kit.skidder("Skidder", (sx, sy, height(sx, sy)), paint=yellow)
    # The camp gate's log posts and beam, the slab fence either side of it.
    for gx in (8.4, 11.8):
        x, y = Y(gx, 18.9)
        kit.rough_log("Camp gate post", (x, y, -0.3), (x, y, 4.6), 0.2, m=mat("bark"), seed=int(gx), stubs=0)
    (bx0, by), (bx1, _) = Y(7.9, 18.9), Y(12.3, 18.9)
    kit.rough_log("Camp gate beam", (bx0, by, 4.35), (bx1, by, 4.35), 0.18, m=mat("bark"), seed=5, stubs=0)
    fv, ff = [], []
    frng = random.Random(5)
    for a, b in (((6.7, 19.0), (8.3, 19.0)), ((11.9, 19.0), (13.3, 19.0))):
        a, b = Vector(Y(*a)), Vector(Y(*b))
        n = int((b - a).length / 0.2)
        for i in range(n):
            p = a.lerp(b, (i + 0.5) / n)
            hh = 1.9 * frng.uniform(0.88, 1.04)
            reb.box(fv, ff, (p.x, p.y, hh / 2), (0.18, 0.04, hh), frng.uniform(-0.04, 0.04))
    reb.mesh_object("Camp fence", fv, ff, mat("planks"), smooth=False)
    kit.ruts("Yard ruts", [(*Y(10.3, 24.0),), (*Y(10.4, 19.0),), (*Y(10.2, 15.6),), (*Y(11.2, 12.4),), (*Y(13.6, 9.6),), (*Y(16.4, 8.0),)], height, gauge=1.7, width=0.32, seed=2.0)

    # ---- The forest round it all, dense; grass and weeds where nobody walks.
    def yard(x, y):
        return -4.0 < x < 36.0 and -18.5 < y < 4.9
    def keep_out(x, y):
        if X0 - 5.0 < x < X1 + 5.0 and Y0 - 1.5 < y < Y1 + 5.0 or yard(x, y):
            return True
        return any((x - e[0]) ** 2 + (y - e[1]) ** 2 < 20 for e, _, _ in cams)
    kit.forest(rng, height, keep_out, (-30, -24, 40, 36), count=260, spacing=1.6, tall=(14, 23), ferns=70, needles=1400)
    kit.forest(rng, height, keep_out, (-10, 4, 20, 22), count=70, spacing=1.5, tall=(12, 20), ferns=40, needles=500)
    kit.far_spruces(rng, height, keep_out=lambda x, y: -30 < x < 40 and -24 < y < 36, count=900, area=(-80, -80, 100, 100))
    # Weeds come up through the gravel where nobody walks: thin tufts away from the worn line to the pump.
    def in_gravel(r):
        while True:
            x, y = r.uniform(X0, X1), r.uniform(Y0, Y1)
            if kit.path_distance(x, y, [[(6.5, 1.2), (7.2, 2.6), (7.9, 3.7)]]) > 0.9 and not (3.8 < x < 7.5 and 4.4 < y < 6.0):
                return x, y
    tufts = kit.meadow(rng, 380, in_gravel, height, mat("dead grass"))
    dv, df = [], []
    for _ in range(500):
        x, y = rng.uniform(X0, X1), rng.uniform(Y0, Y1)
        reb.card(dv, df, Vector((x, y, height(x, y) + 0.012)), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), Vector((0, 0, 1)), rng.uniform(0.03, 0.08), rng.uniform(0.08, 0.25), 0.0)
    reb.mesh_object("Needles and bark blown in", dv, df, mat("dead needles"))
    weeds = kit.meadow(rng, 900, lambda r: (r.uniform(X0 - 0.3, X1 + 0.3), r.choice((r.uniform(Y0 - 0.2, Y0 + 0.35), r.uniform(Y1 - 0.4, Y1 + 0.3)))) if r.random() < 0.5 else (r.choice((r.uniform(X0 - 0.2, X0 + 0.4), r.uniform(X1 - 0.4, X1 + 0.3))), r.uniform(Y0, Y1)), height, mat("dead grass"))
    outer = kit.grass_ground(rng, (-8, 0.5, 18, 16), height, keep_out=lambda x, y: X0 - 0.3 < x < X1 + 0.3 and Y0 - 0.5 < y < Y1 + 0.3 or yard(x, y), per_m2=14)
    verge = kit.grass_ground(rng, (-4, -18, 20, 4.8), height, keep_out=lambda x, y: (-1.5 < x < 18.0 and -16.5 < y < 3.8) or X0 - 0.3 < x < X1 + 0.3 and Y0 - 0.5 < y, per_m2=6, m=mat("dead grass"))
    kit.rocks("Rocks outside", rng, [(-1.5, 8.6, 0.9), (4.2, 10.2, 1.1), (11.6, 8.2, 0.8), (-3.0, 3.4, 0.7), (8.0, 11.5, 1.0)], height)

    # ---- Light: noon under cloud; mist in the trees; the RE0 sky and ranges.
    sun = kit.time_light("noon", sun_heading=200, sun_energy=3.2, mist=((5.0, 3.0, 6.0), (90, 90, 14), 0.009), sky=((0.6, 0.62, 0.63), (0.4, 0.42, 0.45), 1.15))
    sun.data.angle = math.radians(25)
    sun.rotation_euler[0] = math.radians(35)
    kit.overcast_sky(glow=(0.6, -1.0))
    kit.backdrop((5.0, 4.0, 3.3), spread=360, below=-40.0, near=60.0, forest_to=1800.0, trees=110000,
                 keep_out=lambda x, y: math.hypot(x - 5.0, y - 4.0) < 52, shape=far_land, mist=30.0, rng=random.Random(14))

    anim = kit.Anim(16)
    anim.drip((NOZZLE[0], NOZZLE[1], NOZZLE[2] - 0.05), fall=NOZZLE[2] - 0.08, size=0.018, m=wet_oil)
    anim.swing(hook, axis=0, degrees=3)

    # ---- What the game needs.
    room.door("camp-yard", (GATE[0], Y0, GATE[1], Y0 + 0.6), arrive=(6.5, 2.5), face=(0, 1), touch=False)
    room.spot("fuel", (7.6, 3.8, 8.6, 4.4))  # day/events.ts says what she sees and does here
    room.check((tx1 - 1.0, ty - 1.3, tx1, ty - 0.75), "The fuel ledger. Gallons in, gallons out, signed every day.\nThe last entries are a mess. Then they stop.")
    room.check((8.6, 2.6, X1, 4.2), "The dirt's dug out under the wire, the wire bent up.\nThere's blood on it. Something got in here.")
    room.check((3.9, 2.0, 4.8, 2.8), "A snake's skin, shed. Another by the tank.\nAdders. They like the warm drums.")
    room.check((X0 + 0.2, 4.6, 2.6, 5.0), "The lean-to. Oil, grease, rags.")
    scene = bpy.context.scene
    scene.render.use_persistent_data = True
    scene.cycles.volume_step_rate = 4.0
    scene.cycles.volume_max_steps = 64
    room.export(anim, samples=160)


build()
