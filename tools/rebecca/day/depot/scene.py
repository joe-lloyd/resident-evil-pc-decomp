"""Camp 4's fuel depot, noon: a fenced compound of diesel.

What it tells: the camp ran on diesel, and the depot kept count of every
gallon. The last entries on the fuel ledger stop mid-week. The tank's hose
reel is chained and padlocked, so nobody could drain it and run; the
nozzle still drips into the black pool under it. Something came under the
wire at the back: the dirt is dug out under the fence and the wire bent
up, and the dog that came through lies dead against it, shot, its hide
torn open in strips. It wasn't the camp's dog. In the weeds along the
fence and between the drums lie the papery skins adders have shed: they
like the warm drums. A player should learn that the dogs get in, that the
snakes are about, and that the fuel is locked away.

Metres: the floor is x 1.0-9.6, y 1.0-6.8, the compound inside its chain
link (in the yard this is x -2.0-6.6, y 15.2-21.0: moved 3 east, 14.2
north). The gate is in the north fence at x 5.6-7.4, open out into the
yard. The tank lies on its stand along x 3.9-7.3 at y 5.2, its pump and
hose reel at the east end; drums stand in the north-west and the south-east
corners; the lean-to is in the south-west corner, x 1.0-2.6, y 5.0-6.8; the
dog lies against the east fence at y 2.4-3.4, under the dug-out wire.

Moving: diesel dripping from the hung nozzle into its pool, flies over the
dog, weeds in the wind, the NO SMOKING sign swinging on one wire.
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


def height(x, y):
    """The compound flat; the yard flat to the north; the slope rising south and west."""
    h = -0.02 + 0.01 * noise.noise(Vector((x * 0.8, y * 0.8, 5)))
    if y > Y1 + 2.0:
        h += (y - Y1 - 2.0) * 0.25
    if x < X0 - 4.0:
        h += (X0 - 4.0 - x) * 0.25
    return h


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


def tube(verts, faces, path, r, seg=6):
    """A thin tube along a path of 3D points (a shed skin, a hose), into one mesh."""
    pts = [Vector(p) for p in path]
    k0 = len(verts)
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        u = d.orthogonal().normalized()
        w = d.cross(u)
        rr = r * (1.0 - 0.7 * (i / (len(pts) - 1)) ** 2)
        for j in range(seg):
            a = 2 * math.pi * j / seg
            verts.append(tuple(p + (u * math.cos(a) + w * math.sin(a)) * rr))
    for i in range(len(pts) - 1):
        for j in range(seg):
            a, b = k0 + i * seg + j, k0 + i * seg + (j + 1) % seg
            faces.append((a, b, b + seg, a + seg))


def dog(name, at, heading, hide, flayed):
    """A big dog dead on its side: a body, a deep chest, legs out stiff, the head back."""
    parts = []
    parts.append(reb.prim("sphere", "torso", hide, (0, 0, 0.2), (0.85, 0.36, 0.34), segments=14))
    parts.append(reb.prim("sphere", "chest", hide, (0.32, 0, 0.22), (0.4, 0.36, 0.38), segments=12))
    parts.append(kit.rod("neck", hide, (0.45, 0, 0.24), (0.68, 0.05, 0.18), 0.1, 8))
    parts.append(reb.prim("sphere", "head", hide, (0.74, 0.08, 0.16), (0.24, 0.17, 0.17), segments=12))
    parts.append(reb.prim("cone", "muzzle", hide, (0.9, 0.12, 0.13), (0.11, 0.1, 0.2), rot=(0, math.pi / 2, 0.3), top=0.6, segments=10))
    for ex in (0.68, 0.76):
        parts.append(reb.prim("cone", "ear", hide, (ex, 0.04, 0.27), (0.06, 0.03, 0.12), rot=(0.3, -0.4, 0), top=0.1, segments=6))
    for (hx, hy, fx, fy) in ((0.3, -0.12, 0.62, -0.42), (0.28, 0.1, 0.55, -0.3), (-0.3, -0.12, -0.15, -0.48), (-0.3, 0.1, -0.05, -0.4)):
        parts.append(kit.rod("leg", hide, (hx, hy, 0.15), (fx, fy, 0.06), 0.04, 6))
    parts.append(kit.rod("tail", hide, (-0.42, 0, 0.22), (-0.75, -0.15, 0.06), 0.025, 6))
    ob = kit.join(name, parts)
    ob.data.transform(ob.matrix_basis)  # keep the frame the parts were placed in
    ob.matrix_basis.identity()
    ob.location = at
    ob.rotation_euler = (0, 0, heading)
    for i, (x, y, z, r) in enumerate(((0.05, 0.0, 0.37, 0.18), (-0.25, -0.05, 0.36, 0.13), (0.32, 0.02, 0.41, 0.1))):
        p = ob.matrix_basis @ Vector((x, y, z))
        kit.splat(f"{name} torn {i}", flayed, (p.x, p.y, p.z), r, rot=(0, 0, heading), seed=70 + i, stretch=(1.6, 0.7))
    return ob


def build():
    rng = random.Random(61)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    cams = [
        ((9.3, 1.25, 3.3), (4.2, 5.0, 0.3), "from the north-east corner by the gate: the tank, the nozzle dripping, the lean-to"),
        ((9.3, 6.6, 3.2), (6.0, 1.5, 0.3), "from the south-east drums: the dog against the wire, the gate out to the yard"),
        ((1.3, 1.3, 3.2), (7.6, 5.2, 0.3), "from the north-west drums: the pump and the padlocked reel, the drums in the corner"),
    ]
    for eye, look, note in cams:
        room.camera(eye, look, 200, note)

    # ---- Materials.
    gravel = kit.dirtied(mat("gravel"), 0.7, scale=1.0)
    oil = reb.mat_plain("Diesel", (0.012, 0.011, 0.01), 0.08)
    oil_old = reb.mat_plain("Oil soak", (0.03, 0.026, 0.02), 0.35)
    tank_m = reb.mat_surface("Tank green", [(0.0, (0.06, 0.09, 0.05)), (0.6, (0.1, 0.14, 0.09)), (0.85, (0.22, 0.1, 0.04)), (1.0, (0.12, 0.06, 0.03))], scale=3, rough=0.5, bump=0.2)
    wire = chain_link()
    hide = reb.mat_surface("Dog hide", [(0.0, (0.05, 0.035, 0.025)), (0.6, (0.12, 0.07, 0.04)), (1.0, (0.3, 0.16, 0.07))], scale=12, rough=0.55, bump=0.3)
    flayed = reb.mat_surface("Flayed", [(0.0, (0.2, 0.02, 0.015)), (0.6, (0.35, 0.06, 0.04)), (1.0, (0.12, 0.01, 0.01))], scale=20, rough=0.3, bump=0.5)
    skin = reb.mat_surface("Shed skin", [(0.0, (0.35, 0.33, 0.27)), (1.0, (0.55, 0.52, 0.44))], scale=60, rough=0.6, bump=0.4)

    # ---- Ground: gravel inside the wire, mud outside, oil soaked in.
    reb.terrain("Ground", kit.dirtied(mat("mud"), 0.6, scale=0.8), (-25, 35), (-25, 35), height, step=0.7)
    reb.prim("cube", "Gravel", gravel, ((X0 + X1) / 2, (Y0 + Y1) / 2, -0.02), (X1 - X0 + 0.2, Y1 - Y0 + 0.2, 0.04))
    kit.splat("Oil soak under the tank", oil_old, (5.6, 4.9, 0.0), 1.6, seed=1, stretch=(1.6, 0.7), lumps=0.5)
    kit.splat("Pool under the nozzle", oil, (NOZZLE[0], NOZZLE[1] + 0.05, 0.003), 0.45, seed=2, stretch=(1.2, 0.9), lumps=0.4)
    for i in range(6):
        kit.splat(f"Oil stain {i}", oil_old, (rng.uniform(2, 9), rng.uniform(1.5, 6), 0.0), rng.uniform(0.15, 0.4), seed=10 + i, lumps=0.5)
    kit.path_strip("Tyre track in", kit.dirtied(mat("mud"), 0.8), [(6.3, -3.0), (6.4, 1.0), (6.6, 3.6)], height, width=0.35, lift=0.025)
    for i in range(10):
        t = i / 9
        kit.splat(f"Bootprint {i}", oil_old, (6.6 + (0.15 if i % 2 else -0.15), 1.4 + t * 2.4, 0.0), 0.06, seed=30 + i, stretch=(0.6, 1.4), lumps=0.2)

    # ---- The fence: chain link on rusty posts, the gate open out, the dug-out wire at the back.
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
        # The dog's hole: under the east fence the wire is lifted.
        if not horiz and a.x > X1 and min(a.y, b.y) < 3.4 < max(a.y, b.y):
            lo, hi = min(a.y, b.y), max(a.y, b.y)
            for y0, y1 in ((lo, 2.9), (3.9, hi)):
                reb.prim("cube", "Fence wire", wire, (a.x, (y0 + y1) / 2, 1.0), (0.02, y1 - y0, 2.0))
            reb.prim("cube", "Fence wire over the hole", wire, (a.x, 3.4, 1.25), (0.02, 1.0, 1.5))
            reb.prim("cube", "Wire bent up", wire, (a.x + 0.15, 3.4, 0.38), (0.02, 1.0, 0.5), rot=(0, 0.6, 0))
        else:
            reb.prim("cube", "Fence wire", wire, ((a.x + b.x) / 2, (a.y + b.y) / 2, 1.0), (d.length if horiz else 0.02, 0.02 if horiz else d.length, 2.0))
    kit.join("Fence posts", posts)
    kit.splat("Dug-out dirt", kit.dirtied(mat("dirt"), 0.5), (X1 + 0.35, 3.4, 0.02), 0.45, seed=6, stretch=(0.8, 1.4), lumps=0.6)
    reb.prim("cube", "The hole under the wire", mat("black"), (X1 + 0.1, 3.4, -0.04), (0.5, 0.9, 0.08))
    kit.scratches("Claw marks on the post", mat("black"), (X1 + 0.08, 2.9, 0.9), (-1, 0), count=4, length=0.4, seed=7)
    for x in GATE:
        reb.mask(reb.wall(kit.rod("Gate post", mat("rust"), (x, Y0, 0), (x, Y0, 2.2), 0.05, 8), "circle"))
    reb.prim("cube", "Gate, open out", wire, (GATE[0] + 0.25, Y0 - 0.85, 0.95), (0.02, 1.7, 1.8), rot=(0, 0, 0.3))
    kit.rod("Gate frame", mat("rust"), (GATE[0], Y0, 1.85), (GATE[0] + 0.5, Y0 - 1.65, 1.85), 0.02)
    kit.rod("Gate chain, cut", mat("iron"), (GATE[1], Y0 - 0.02, 1.0), (GATE[1] - 0.05, Y0 - 0.05, 0.4), 0.012, 4)
    # The signs: FUEL by the gate (read from the yard), NO SMOKING swinging inside.
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
    tank = reb.prim("cyl", "Tank", tank_m, ((tx0 + tx1) / 2, ty, tz), (1.4, 1.4, tx1 - tx0), rot=(0, math.pi / 2, 0), segments=24)
    for x in (tx0, tx1):
        reb.prim("cyl", "Tank end", tank_m, (x, ty, tz), (1.44, 1.44, 0.05), rot=(0, math.pi / 2, 0), segments=24)
    for x in (tx0 + 0.5, tx1 - 0.5):
        for dy in (-0.55, 0.55):
            kit.rod("Stand leg", mat("rust"), (x, ty + dy, 0), (x, ty + dy * 0.6, tz - 0.6), 0.05)
        reb.prim("cube", "Cradle", mat("rust"), (x, ty, tz - 0.62), (0.12, 1.3, 0.12))
    reb.mask(reb.wall(reb.prim("cube", "Tank footprint", None, ((tx0 + tx1) / 2, ty, 0.5), (tx1 - tx0, 1.45, 1.0)))).hide_render = True
    kit.text("Tank words", "DIESEL", mat("white paint"), ((tx0 + tx1) / 2, ty - 0.72, tz + 0.05), size=0.35)
    kit.text("Tank words 2", "CAMP 4  1000 GAL", mat("white paint"), ((tx0 + tx1) / 2, ty - 0.71, tz - 0.3), size=0.12)
    reb.prim("cyl", "Filler cap", mat("rust"), (tx0 + 0.6, ty, tz + 0.72), (0.2, 0.2, 0.08))
    # The pump on its pipe at the east end, crank and all.
    px = tx1 + 0.45
    kit.rod("Pump pipe", mat("iron"), (tx1, ty, tz - 0.5), (px, ty, tz - 0.5), 0.04)
    pump = kit.box("Hand pump", reb.mat_plain("Pump red", (0.35, 0.05, 0.03), 0.5), (px, ty - 0.05, 0.0), (0.3, 0.3, 1.2), bevel=0.02)
    reb.mask(reb.wall(pump))
    kit.rod("Pump crank", mat("iron"), (px, ty - 0.22, 1.05), (px + 0.3, ty - 0.22, 1.3), 0.02)
    reb.prim("cyl", "Crank knob", mat("black"), (px + 0.3, ty - 0.3, 1.3), (0.05, 0.05, 0.12), rot=(math.pi / 2, 0, 0))
    reb.prim("cyl", "Pump dial", mat("white paint"), (px, ty - 0.21, 0.85), (0.16, 0.16, 0.02), rot=(math.pi / 2, 0, 0))
    # The hose reel, chained shut with a padlock.
    rc = Vector((px + 0.15, ty - 0.85, 0.5))
    reel = reb.prim("cyl", "Hose reel", mat("rubber"), rc, (0.75, 0.75, 0.32), rot=(math.pi / 2, 0, 0), segments=20)
    for dy in (-0.18, 0.18):
        reb.prim("cyl", "Reel side", mat("rust"), rc + Vector((0, dy, 0)), (0.85, 0.85, 0.03), rot=(math.pi / 2, 0, 0), segments=20)
    kit.rod("Reel stand", mat("rust"), rc + Vector((0, -0.2, -0.5)), rc + Vector((0, -0.2, 0)), 0.03)
    kit.rod("Reel stand", mat("rust"), rc + Vector((0, 0.2, -0.5)), rc + Vector((0, 0.2, 0)), 0.03)
    reb.mask(reb.wall(reb.prim("cyl", "Reel footprint", None, rc, (0.85, 0.5, 1.0)), "circle")).hide_render = True
    lv, lf = [], []
    for i in range(10):
        a = 2 * math.pi * i / 10
        lv.append((rc.x + 0.4 * math.cos(a), rc.y - 0.2, rc.z + 0.4 * math.sin(a)))
    for i in range(10):
        kit.rod("Reel chain", mat("iron"), lv[i], lv[(i + 1) % 10], 0.012, 4)
    reb.prim("cube", "Padlock", mat("steel"), rc + Vector((0.42, -0.22, 0.0)), (0.07, 0.03, 0.09), bevel=0.01)
    reb.prim("cube", "Padlock shackle", mat("steel"), rc + Vector((0.42, -0.22, 0.07)), (0.05, 0.01, 0.05))
    # The nozzle hung on its hook, dripping into the pool.
    hv, hf = [], []
    tube(hv, hf, [rc + Vector((-0.2, -0.2, -0.3)), (7.5, 4.6, 0.25), (7.75, 4.4, 0.6), (NOZZLE[0], NOZZLE[1], NOZZLE[2] + 0.15)], 0.03, seg=8)
    reb.mesh_object("Hose", hv, hf, mat("rubber"))
    reb.prim("cube", "Nozzle", mat("steel"), (NOZZLE[0], NOZZLE[1], NOZZLE[2] + 0.1), (0.06, 0.06, 0.25), rot=(0.3, 0, 0))
    reb.prim("cube", "Nozzle hook", mat("iron"), (NOZZLE[0], NOZZLE[1] + 0.05, NOZZLE[2] + 0.28), (0.05, 0.1, 0.04))
    # A jerrycan on its side, a funnel, the ledger hung on the stand.
    reb.prim("cube", "Jerrycan", reb.mat_plain("Jerrycan", (0.28, 0.05, 0.03), 0.5), (7.0, 3.9, 0.17), (0.45, 0.17, 0.34), rot=(math.pi / 2, 0, 0.5), bevel=0.02)
    reb.prim("cone", "Funnel", mat("steel"), (6.6, 3.7, 0.1), (0.22, 0.22, 0.2), rot=(1.4, 0, 0.3), top=0.2)
    kit.splat("Spill from the can", oil, (6.75, 3.65, 0.002), 0.3, seed=3, stretch=(1.4, 0.8))
    reb.prim("cube", "Clipboard", mat("dark wood"), (tx1 - 0.5, ty - 0.68, 1.2), (0.25, 0.02, 0.33), rot=(0.08, 0, 0))
    reb.prim("cube", "Fuel ledger", mat("paper"), (tx1 - 0.5, ty - 0.695, 1.18), (0.22, 0.004, 0.27), rot=(0.08, 0, 0))
    for i in range(6):
        reb.prim("cube", f"Ledger line {i}", mat("black"), (tx1 - 0.52, ty - 0.699, 1.27 - i * 0.035), (0.16 - (0.06 if i > 3 else 0), 0.002, 0.006))
    kit.rod("Clipboard string", mat("canvas"), (tx1 - 0.5, ty - 0.68, 1.37), (tx1 - 0.5, ty - 0.6, 1.62), 0.004, 4)

    # ---- Drums: a pallet of them in the north-west, more stacked in the south-east, one leaking.
    for i, (x, y, tipped, m) in enumerate(((3.2, 2.2, False, "rust"), (3.85, 2.3, False, "red paint"), (3.5, 2.9, False, "rust"), (1.55, 3.0, False, "red paint"), (1.55, 3.65, False, "rust"), (2.1, 4.25, True, "rust"),
                                            (8.6, 5.4, False, "red paint"), (7.85, 6.35, False, "rust"), (9.05, 6.2, False, "rust"), (8.4, 6.25, False, "red paint"))):
        d = kit.drum(f"Drum {i}", mat(m), (x, y, 0.0), tipped=tipped, rot=rng.uniform(0, 3) if not tipped else 1.2)
        reb.wall(d, "circle")
        if i in (0, 3, 7):
            reb.mask(d)
    reb.prim("cube", "Pallet", mat("planks"), (3.5, 2.5, 0.06), (1.4, 1.3, 0.12))
    kit.splat("Leak from the tipped drum", oil, (2.6, 4.5, 0.002), 0.35, seed=4, stretch=(1.3, 0.8))
    kit.drum("Drum on top", mat("rust"), (8.75, 5.95, 0.88), tipped=True, rot=0.3)
    for i, (x, y) in enumerate(((3.4, 2.6), (8.7, 5.9))):
        kit.text(f"Drum stencil {i}", "DIESEL", mat("white paint"), (x, y - 0.33, 0.6), size=0.07, rot=(math.pi / 2, 0, math.pi))

    # ---- The lean-to in the south-west: tin roof on posts, shelves of oil, rags.
    for (x, y) in ((1.0, 5.0), (2.6, 5.0), (1.0, 6.8), (2.6, 6.8)):
        reb.wall(kit.rod("Lean-to post", mat("dark wood"), (x, y, 0), (x, y, 2.4 if y > 6 else 2.1), 0.05), "circle")
    reb.prim("cube", "Lean-to roof", mat("tin"), (1.8, 5.9, 2.28), (2.0, 2.2, 0.05), rot=(-0.14, 0, 0))
    sh = kit.shelves("Oil shelves", mat("planks"), (1.8, 6.6, 0.0), size=(1.4, 0.35, 1.6), rows=4, clutter=0.9, seed=3)
    reb.wall(sh)
    reb.cloth("Oily rags", oil_old, (2.2, 5.5, 0.03), (0.4, 0.3), lumps=0.03, seed=2)
    reb.prim("cube", "Grease tin", mat("rust"), (1.6, 5.6, 0.1), (0.2, 0.2, 0.2))

    # ---- The dog that came under the wire, shot; flies on it.
    dog("Dead dog", (8.9, 3.3, 0.0), heading=math.pi / 2 + 0.25, hide=hide, flayed=flayed)
    kit.splat("Dog's blood", mat("blood"), (8.7, 3.35, 0.0), 0.5, seed=8, stretch=(1.3, 0.9))
    shells = [reb.prim("cyl", "Shell", mat("red paint"), (7.4 + rng.gauss(0, 0.3), 2.4 + rng.gauss(0, 0.3), 0.012), (0.024, 0.024, 0.07), rot=(math.pi / 2, 0, rng.uniform(0, 3)), segments=6) for _ in range(4)]
    kit.join("Shells", shells)
    reb.wall(reb.prim("cube", "Dog footprint", None, (8.9, 3.3, 0.2), (0.7, 1.2, 0.4))).hide_render = True

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

    # ---- Outside the wire: the yard to the north (its plan moved 3 east, 14.2 north), forest beyond.
    mess = kit.boards("Mess boards", (0.42, 0.4, 0.36), width=0.18)
    reb.prim("cube", "Outside, mess", mess, (2.3, -4.7, 1.4), (5.6, 9.2, 2.8))
    reb.prim("cube", "Outside, mess roof", mat("tin"), (2.3, -4.7, 3.0), (6.6, 9.8, 0.1), rot=(0, 0.0, 0))
    dark = reb.mat_plain("Dark inside", (0.012, 0.011, 0.01), 0.9)
    reb.prim("cube", "Outside, mess door", dark, (5.12, -4.75, 1.0), (0.03, 0.9, 2.0))
    for y in (-7.5, -2.3):
        reb.prim("cube", "Outside, mess window", dark, (5.12, y, 1.6), (0.03, 1.4, 0.8))
        reb.prim("cube", "Outside, window boards", mat("planks"), (5.16, y, 1.6), (0.03, 1.6, 0.14), rot=(0.4, 0, 0))
    reb.prim("cube", "Outside, mess chimney", mat("rust"), (3.6, -5.5, 3.6), (0.3, 0.3, 1.4))
    yellow = reb.mat_plain("Skidder yellow", (0.45, 0.3, 0.03), 0.6)
    reb.prim("cube", "Outside, skidder body", yellow, (11.0, -1.2, 1.1), (3.6, 1.2, 0.8))
    reb.prim("cube", "Outside, skidder cab roof", yellow, (9.8, -1.2, 2.8), (1.6, 1.6, 0.08))
    for x in (9.15, 10.45):
        for y in (-1.9, -0.5):
            kit.rod("Outside, cab post", mat("black"), (x, y, 1.4), (x, y, 2.75), 0.04)
    for x in (9.6, 12.4):
        for y in (-2.15, -0.25):
            reb.prim("cyl", "Outside, tyre", mat("rubber"), (x, y, 0.75), (1.5, 1.5, 0.55), rot=(math.pi / 2, 0, 0), segments=18)
    reb.prim("cube", "Outside, skidder blade", yellow, (13.35, -1.2, 0.38), (0.12, 2.6, 0.75), rot=(0, 0.2, 0))
    tin = mat("tin")
    for name, m, (cx, cy, sx, sy, h) in (("workshop", reb.mat_surface("Workshop tin", [(0.0, (0.15, 0.16, 0.15)), (1.0, (0.24, 0.24, 0.23))], scale=3, bump=0.3), (19.3, 2.4, 6.0, 5.8, 3.0)),
                                          ("bunkhouse", kit.boards("Bunkhouse boards", (0.17, 0.11, 0.07), width=0.22), (14.5, -15.1, 11.2, 5.2, 2.4)),
                                          ("sawmill", kit.boards("Mill boards", (0.2, 0.19, 0.17), width=0.3), (27.0, -6.8, 10.0, 9.6, 6.0))):
        reb.prim("cube", f"Outside, {name}", m, (cx, cy, h / 2), (sx, sy, h))
        for side in (-1, 1):
            reb.prim("cube", f"Outside, {name} roof", tin, (cx, cy + side * sy / 4, h + sy * 0.07), (sx + 0.6, sy / 2 / math.cos(0.28) + 0.3, 0.05), rot=(side * 0.28, 0, 0))
    reb.prim("cube", "Outside, quarantine board", reb.mat_plain("Plywood", (0.35, 0.28, 0.18), 0.8), (10.8, 2.7, 1.45), (1.9, 0.03, 1.0))
    for x in (11.4, 14.8):
        kit.rod("Outside, gate post", mat("logs"), (x, 4.7, 0), (x, 4.7, 4.6), 0.2)
    kit.rod("Outside, gate beam", mat("logs"), (10.9, 4.7, 4.35), (15.3, 4.7, 4.35), 0.18)

    def keep_out(x, y):
        if -5.0 < x < 25.0 and -18.0 < y < 9.0:
            return True
        return any((x - e[0]) ** 2 + (y - e[1]) ** 2 < 25 for e, _, _ in cams)
    kit.forest(rng, height, keep_out, (-25, -20, 35, 35), count=55, spacing=2.0, ferns=20, needles=400)
    weeds = kit.meadow(rng, 700, lambda r: (r.uniform(X0 - 0.3, X1 + 0.3), r.choice((r.uniform(Y0 - 0.2, Y0 + 0.3), r.uniform(Y1 - 0.3, Y1 + 0.3)))) if r.random() < 0.5 else (r.choice((r.uniform(X0 - 0.2, X0 + 0.3), r.uniform(X1 - 0.3, X1 + 0.3))), r.uniform(Y0, Y1)), height, mat("dead grass"))
    bv, bf = [], []
    for (x, y, r) in ((-1.5, 8.6, 0.9), (4.2, 10.2, 1.1), (11.6, 8.2, 0.8), (-3.0, 3.4, 0.7), (8.0, 11.5, 1.0)):
        reb.boulder(rng, (x, y, height(x, y) - 0.15), r, bv, bf)
    reb.mesh_object("Rocks outside", bv, bf, mat("rock"))
    fv, ff = [], []
    for _ in range(40):
        x, y = rng.uniform(-5, 14), rng.uniform(Y1 + 0.8, Y1 + 7)
        reb.fern(rng, (x, y, height(x, y)), rng.uniform(0.4, 0.8), fv, ff)
    reb.mesh_object("Ferns outside", fv, ff, mat("ferns"))
    outer = kit.meadow(rng, 2000, lambda r: (r.uniform(-6, 16), r.uniform(Y1 + 0.5, Y1 + 6)) if r.random() < 0.6 else (r.uniform(-6, X0 - 0.4), r.uniform(-2, Y1 + 4)), height)

    # ---- Light: noon under cloud; mist in the trees.
    sun = kit.time_light("noon", sun_heading=200, sun_energy=1.8, mist=((5.0, 3.0, 6.0), (90, 90, 14), 0.009), sky=((0.5, 0.52, 0.54), (0.36, 0.39, 0.43), 0.75))
    sun.data.angle = math.radians(25)
    sun.rotation_euler[0] = math.radians(35)

    anim = kit.Anim(16)
    anim.drip((NOZZLE[0], NOZZLE[1], NOZZLE[2] - 0.05), fall=NOZZLE[2] - 0.08, size=0.018, m=oil)
    anim.flies((8.9, 3.3, 0.3), count=11, radius=0.45)
    anim.swing(hook, axis=0, degrees=6)
    anim.sway(weeds, amount=0.05)
    anim.sway(outer, amount=0.06)

    # ---- What the game needs.
    room.door("camp-yard", (GATE[0], Y0, GATE[1], Y0 + 0.6), arrive=(6.5, 2.5), face=(0, 1))
    room.spot("fuel", (7.6, 3.8, 8.6, 4.4))  # day/events.ts says what she sees and does here
    room.check((tx1 - 1.0, ty - 1.3, tx1, ty - 0.75), "The fuel ledger. Gallons in, gallons out, signed every day.\nThe last entries are a mess. Then they stop.")
    room.check((8.1, 2.6, 8.5, 4.0), "A dog. Not a camp dog: a big one, its hide torn open in strips.\nIt dug in under the wire. Somebody shot it.")
    room.check((3.9, 2.0, 4.8, 2.8), "A snake's skin, shed. Another by the tank.\nAdders. They like the warm drums.")
    room.check((X0 + 0.2, 4.6, 2.6, 5.0), "The lean-to. Oil, grease, rags.")
    room.entry = "Diesel. The whole place reeks of it."
    scene = bpy.context.scene
    scene.render.use_persistent_data = True
    scene.cycles.volume_step_rate = 4.0
    scene.cycles.volume_max_steps = 64
    room.export(anim, samples=160)


build()
