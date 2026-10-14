"""The granite quarry east of the gondola, a harsh late afternoon.

What it tells: the Arklay granite quarry worked until this week. The cut
stops at three benches of bare rock in the north, the derrick crane still
standing over the floor with its hook hanging over the blocks it was
lifting. The crusher in the north-east has rusted for years beside the old
mine rails, which run out east through the cut to the silver mine. One of
the quarrymen was caught on the floor by the dogs from the estate: his
hard hat rolled away, his lunch tin burst open, and he was dragged from
behind the blocks to where he lies now, opened up and gnawed, the paw
prints all round him in the dust. Hal's drops of blood cross the floor
from the west to the cut, the way to the mine. The quarry office hut in
the south-west is shut and padlocked, its DANGER EXPLOSIVES board on the
wall. Dust still blows off the top of the cut in the wind.

Metres: the floor is x 1.0-19.0, y 1.0-16.0 at z 0. The rock face rises in
three benches north of y 1 (4, 8, 12 m). The way in from the east path is
the west edge at y 8.2-10.8; the cut to the mine is the east edge at y
5.2-8.3, where the rails leave. The derrick's mast is at x 4.0, y 2.5, its
boom reaching south-east over the blocks (x 8-13, y 5-9). The crusher is
x 13.5-17.0, y 1.2-4.2. The worker lies at x 10.5, y 10.4. The office hut
is x 2.0-5.6, y 12.4-15.4, its door in the north wall at x 3.3-4.2. A dead
truck stands at x 13-18, y 12.4-14.4. South of y 16 is the spoil lip, and
the valley beyond.

Moving: dust blowing off the cut, the derrick's hook swinging, flies over
the body.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
from kit import mat  # noqa: E402
from mathutils import Matrix, Vector, noise  # noqa: E402
import bpy  # noqa: E402

X0, X1, Y0, Y1 = 1.0, 19.0, 1.0, 16.0
MAST = (4.0, 2.5)
HUT = (2.0, 5.6, 12.4, 15.4)
HUT_DOOR = (3.3, 4.2)
CRUSHER = (13.5, 17.0, 1.2, 4.2)
BODY = (10.5, 10.4)
ENTRY = (8.2, 10.8)
CUT = (5.2, 8.3)



def settle(ob, at, offset, turn=0.0, tilt=None):
    """Put a kit piece where it was meant to go. kit.join keeps the first
    part's origin and turn, so kit.chair, crate, shelves, crow and body come
    out shifted by that part's offset (a body stands on end): undo it."""
    local = Matrix.Translation(Vector(offset))
    if tilt is not None:
        local = local @ tilt.to_matrix().to_4x4()
    ob.matrix_world = Matrix.Translation(Vector(at)) @ Matrix.Rotation(turn, 4, "Z") @ local
    for c in ob.children:
        c.matrix_parent_inverse = local.inverted()
    return ob


def chair(name, m, at, rot=0.0):
    return settle(kit.chair(name, m, at, rot=rot), at, (0, 0, 0.45), rot)


def crate(name, m, at, size=(0.6, 0.5, 0.5), rot=0.0, open_=False):
    return settle(kit.crate(name, m, at, size=size, rot=rot, open_=open_), at, (0, 0, size[2] / 2), rot)


def shelves(name, m, at, size=(1.0, 0.3, 1.8), rows=4, rot=0.0, clutter=0.7, seed=0):
    ob = kit.shelves(name, m, at, size=size, rows=rows, rot=rot, clutter=clutter, seed=seed)
    return settle(ob, at, (-size[0] / 2, 0, size[2] / 2), rot)


def crow(name, at, heading=0.0, perched=True):
    b, w = kit.crow(name, at, heading=heading, perched=perched)
    settle(b, at, (0, 0, 0.12), heading)
    return b, w


def corpse(name, at, heading=0.0, pose="back", **kw):
    """kit.body lying the way it should (no `bloody`: its pool lands in the wrong place)."""
    ob = kit.body(name, at, heading=heading, pose=pose, **kw)
    if kw.get("sheet"):
        return ob
    j = kit._POSES[pose]
    missing = kw.get("missing", ())
    a, b = next((a, b) for a, b, _, _ in kit._BONES if a not in missing and b not in missing)
    pa, pb = Vector(j[a]), Vector(j[b])
    return settle(ob, at, (pa + pb) / 2, heading, (pb - pa).to_track_quat("Z", "Y"))


def height(x, y):
    """The quarry floor flat; benches north, rock rims west and east with their gaps, the spoil lip south."""
    n = noise.noise(Vector((x * 0.35, y * 0.35, 2)))
    if X0 - 0.3 < x < X1 + 0.3 and Y0 - 0.3 < y < Y1 + 0.3:
        return -0.06
    z = 0.0
    d = Y0 - 0.3 - y + 0.6 * noise.noise(Vector((x * 0.25, 7, 1))) + 0.35 * noise.noise(Vector((x * 1.3, 2, 4)))
    if d > 0:
        z = max(z, 4.0 if d < 2.6 else 8.0 if d < 5.0 else 12.0 + (d - 5.0) * 0.4)
        z += 0.6 * n + 0.25 * noise.noise(Vector((x * 1.1, y * 1.1, 6)))
    dw = X0 - 0.3 - x + 0.4 * noise.noise(Vector((y * 0.3, 3, 1)))
    if dw > 0:
        gap = ENTRY[0] < y < ENTRY[1]
        z = max(z, (0.15 * dw if gap else min(4.5, 1.5 + dw * 2.5)) + 0.4 * n)
    de = x - X1 - 0.3 + 0.4 * noise.noise(Vector((y * 0.3, 5, 1)))
    if de > 0:
        gap = CUT[0] < y < CUT[1]
        z = max(z, (0.05 * de if gap else min(7.0, 2.0 + de * 3.0)) + 0.4 * n)
    ds = y - Y1 - 0.3
    if ds > 0:
        z = max(z, (1.4 * min(1.0, ds / 1.5) - max(0.0, ds - 5.0) * 1.2) + 0.3 * n)
    return z


def dust_material():
    """Pale dust drifting in sheets: a noise that fades out at the card's edges, its offset turned by the Anim."""
    m, nodes, links, bsdf = reb.nodes_material("Dust haze")
    bsdf.inputs["Base Color"].default_value = (0.75, 0.68, 0.56, 1)
    bsdf.inputs["Roughness"].default_value = 1.0
    out = nodes["Material Output"]
    tc = nodes.new("ShaderNodeTexCoord")
    mp = nodes.new("ShaderNodeMapping")
    mp.name = "Drift"
    links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.5
    nz.inputs["Detail"].default_value = 3
    links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    ramp = reb.ramp(nodes, links, nz.outputs["Fac"], [(0.38, (0, 0, 0)), (0.7, (0.75, 0.75, 0.75))])
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Object"], sep.inputs["Vector"])
    fades = []
    for axis in ("X", "Z"):
        a = nodes.new("ShaderNodeMath")
        a.operation = "ABSOLUTE"
        links.new(sep.outputs[axis], a.inputs[0])
        b = nodes.new("ShaderNodeMath")
        b.operation = "MULTIPLY_ADD"
        b.inputs[1].default_value = -2.0
        b.inputs[2].default_value = 1.0
        links.new(a.outputs[0], b.inputs[0])
        fades.append(b)
    edge = nodes.new("ShaderNodeMath")
    edge.operation = "MULTIPLY"
    links.new(fades[0].outputs[0], edge.inputs[0])
    links.new(fades[1].outputs[0], edge.inputs[1])
    fac = nodes.new("ShaderNodeMath")
    fac.operation = "MULTIPLY"
    links.new(ramp.outputs["Color"], fac.inputs[0])
    links.new(edge.outputs[0], fac.inputs[1])
    clear = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(fac.outputs[0], mix.inputs["Fac"])
    links.new(clear.outputs[0], mix.inputs[1])
    links.new(bsdf.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def rails(name, path, sleepers_m, rail_m, gauge=0.6):
    """Narrow-gauge track along `path` [(x, y)]: two rails and the sleepers under them, two meshes."""
    sv, sf, rv, rf = [], [], [], []
    pts = [Vector((x, y, 0.0)) for x, y in path]
    for a, b in zip(pts, pts[1:]):
        d = (b - a)
        side = Vector((-d.y, d.x, 0)).normalized()
        n = max(1, int(d.length / 0.55))
        for i in range(n):
            c = a.lerp(b, (i + 0.5) / n)
            reb.box(sv, sf, (c.x, c.y, 0.04), (1.0, 0.16, 0.08), math.atan2(side.y, side.x))
        for s in (-1, 1):
            o = side * gauge / 2 * s
            reb.box(rv, rf, ((a + b) / 2 + o + Vector((0, 0, 0.11))).to_tuple(), (d.length + 0.02, 0.05, 0.07), math.atan2(d.y, d.x))
    reb.mesh_object(f"{name} sleepers", sv, sf, sleepers_m, smooth=False)
    return reb.mesh_object(f"{name} rails", rv, rf, rail_m, smooth=False)


def drips(name, m, pts, rng, r=(0.02, 0.05), z=0.0):
    """Blood drops at points, in one mesh."""
    v, f = [], []
    for x, y in pts:
        kit._stain(v, f, rng, (x, y, z + 0.005), rng.uniform(*r), rng.uniform(0, 6.3), 0.45, (1.0, 1.0), rng.randint(0, 99), points=10, drops=rng.random() < 0.35)
    return reb.mesh_object(name, v, f, m, smooth=False)


def along(path, step, rng, jitter=0.12, skip=0.0):
    """Points every `step` metres along a polyline, a little off the line."""
    out = []
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        a, b = Vector((ax, ay)), Vector((bx, by))
        n = max(1, int((b - a).length / step))
        for i in range(n):
            if rng.random() < skip:
                continue
            p = a.lerp(b, (i + rng.uniform(0, 0.6)) / n)
            out.append((p.x + rng.uniform(-jitter, jitter), p.y + rng.uniform(-jitter, jitter)))
    return out


def build():
    rng = random.Random(61)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.camera((1.4, 9.4, 3.6), (11.0, 6.0, 0.8), 200, "from the way in: the derrick, the blocks, the crusher under the face")
    room.camera((18.6, 11.2, 3.8), (8.5, 8.2, 0.5), 200, "from the east side by the truck: the body by the blocks, the derrick over them")
    room.camera((12.4, 15.7, 3.3), (10.2, 6.5, 0.6), 205, "from the spoil lip: the worker in front of the blocks, the benches above")
    room.camera((8.4, 8.4, 3.7), (3.0, 14.2, 0.6), 200, "from the floor north-east of the hut: its door and its signs, the way in, the derrick")
    room.camera((11.2, 11.2, 3.4), (17.8, 5.0, 0.8), 200, "from by the body: the crusher, the rails out east to the mine")
    room.camera((1.6, 5.4, 4.0), (11.5, 12.5, 0.2), 200, "from the north-west by the derrick's foot: the floor, the kill, the truck")

    granite_floor = reb.mat_surface("Quarry floor", [(0.0, (0.07, 0.065, 0.055)), (0.45, (0.13, 0.12, 0.1)), (0.8, (0.19, 0.17, 0.14)), (1.0, (0.12, 0.1, 0.08))], scale=1.2, bump=0.5)
    block_m = kit.dirtied(reb.mat_surface("Cut granite", [(0.0, (0.06, 0.06, 0.06)), (0.35, (0.16, 0.15, 0.15)), (0.6, (0.24, 0.21, 0.2)), (1.0, (0.3, 0.24, 0.22))], scale=4, rough=0.75, bump=0.5), 0.7, scale=1.5)
    face_m = reb.mat_surface("Quarry face", [(0.0, (0.05, 0.05, 0.048)), (0.4, (0.12, 0.115, 0.11)), (0.7, (0.19, 0.18, 0.165)), (1.0, (0.24, 0.2, 0.17))], scale=0.9, detail=14, bump=1.0)
    rust = mat("rust")
    iron = mat("iron")
    hivis = reb.mat_surface("Orange vest", [(0.0, (0.35, 0.08, 0.02)), (0.7, (0.55, 0.16, 0.03)), (1.0, (0.2, 0.03, 0.02))], scale=12)
    dust_m = dust_material()

    # ---- Ground: the floor slab of dust and grit, the rock round it, tracks worn into it.
    reb.terrain("Quarry rock", face_m, (-14, 34), (-14, 34), height, step=0.3)
    reb.prim("cube", "Quarry floor", granite_floor, ((X0 + X1) / 2, (Y0 + Y1) / 2, -0.04), (X1 - X0 + 0.7, Y1 - Y0 + 0.7, 0.08))
    kit.path_strip("Haul track", mat("dirt"), [(-6.0, 9.5), (X0, 9.5), (5.0, 9.8), (9.0, 11.6), (14.0, 12.0), (17.0, 11.6)], lambda x, y: max(0.0, height(x, y)) if not (X0 - 0.3 < x < X1 + 0.3 and Y0 - 0.3 < y < Y1 + 0.3) else 0.0, width=1.1, lift=0.004)
    # Chips of granite everywhere, oil where the machines stood.
    cv, cf = [], []
    for _ in range(260):
        x, y = rng.uniform(X0, X1), rng.uniform(Y0, Y1)
        sz = rng.uniform(0.04, 0.16)
        reb.box(cv, cf, (x, y, sz * 0.3), (sz, sz * rng.uniform(0.6, 1.2), sz * 0.7), rng.uniform(0, 3))
    reb.mesh_object("Granite chips", cv, cf, block_m, smooth=False)
    for i, (x, y, r) in enumerate(((15.2, 5.0, 0.6), (5.8, 4.4, 0.5), (16.0, 13.6, 0.8))):
        kit.splat(f"Oil {i}", reb.mat_plain("Oil stain", (0.03, 0.028, 0.025), 0.4), (x, y, 0.0), r, seed=80 + i, stretch=(1.5, 0.9))
    # A barrow tipped by the blocks, a sledge, a pick.
    barrow = reb.prim("cube", "Barrow pan", rust, (7.0, 9.1, 0.3), (0.9, 0.6, 0.3), rot=(0.9, 0, 0.4), bevel=0.05)
    reb.prim("cyl", "Barrow wheel", mat("rubber"), (7.35, 8.6, 0.2), (0.4, 0.4, 0.08), rot=(math.pi / 2, 0, 0.4), segments=14)
    kit.rod("Barrow handle", mat("logs"), (6.7, 9.2, 0.1), (6.2, 9.6, 0.65), 0.025)
    kit.rod("Barrow handle", mat("logs"), (7.0, 9.45, 0.1), (6.5, 9.85, 0.65), 0.025)
    reb.wall(barrow)
    kit.rod("Sledge haft", mat("logs"), (12.3, 6.5, 0.03), (13.1, 6.9, 0.03), 0.02)
    reb.prim("cube", "Sledge head", iron, (12.3, 6.5, 0.06), (0.1, 0.22, 0.1), rot=(0, 0, 0.45))
    kit.rod("Pick haft", mat("logs"), (7.6, 4.6, 0.03), (8.3, 4.2, 0.03), 0.02)
    reb.prim("cube", "Pick head", iron, (8.3, 4.2, 0.04), (0.06, 0.6, 0.05), rot=(0, 0, 0.5))
    kit.cracks("Cracks", mat("black"), (X0, Y0, X1, Y1), count=10, seed=3, length=2.0)
    # Rubble at the foot of the face and along the rims.
    rv, rf = [], []
    for _ in range(26):
        x = rng.uniform(X0 - 1, X1 + 1)
        y = rng.uniform(Y0 - 0.8, Y0 + 0.4)
        if CRUSHER[0] - 0.5 < x < CRUSHER[1] + 0.5 or abs(x - MAST[0]) < 1.4:
            continue
        reb.boulder(rng, (x, y, 0.0), rng.uniform(0.25, 0.7), rv, rf)
    for (x, y, r) in ((0.6, 4.0, 0.9), (0.4, 13.5, 1.0), (19.3, 11.0, 1.1), (19.5, 2.5, 0.9), (7.6, 15.6, 0.6), (12.0, 15.8, 0.7), (6.5, 3.2, 0.45)):
        reb.boulder(rng, (x, y, 0.0), r, rv, rf)
    reb.mesh_object("Rubble", rv, rf, mat("rock"))
    # Drill lines down the first bench, where the charges went in.
    dv, df = [], []
    for k in range(14):
        x = 2.0 + k * 1.2 + rng.uniform(-0.2, 0.2)
        if CRUSHER[0] - 0.3 < x < CRUSHER[1] + 0.3:
            continue
        y = Y0 - 0.3 - 0.5 * noise.noise(Vector((x * 0.25, 7, 1))) + 0.05
        reb.box(dv, df, (x, y, 2.3), (0.05, 0.02, 3.2))
    reb.mesh_object("Drill lines", dv, df, mat("black"), smooth=False)

    # ---- The cut blocks, stacked where the derrick set them down.
    bv, bf = [], []
    walls = []
    for (x, y, sx, sy, sz, stack) in ((8.6, 5.6, 1.8, 1.1, 1.1, 2), (10.6, 5.5, 1.6, 1.2, 1.0, 2), (12.4, 5.8, 1.4, 1.0, 1.0, 1), (9.0, 7.6, 2.0, 1.2, 1.2, 1), (11.3, 7.8, 1.5, 1.1, 1.1, 2), (13.2, 8.4, 1.2, 1.0, 0.9, 1)):
        z = 0.0
        for k in range(stack):
            yaw = rng.uniform(-0.06, 0.06)
            reb.box(bv, bf, (x + rng.uniform(-0.08, 0.08), y, z + sz / 2), (sx, sy, sz), yaw)
            z += sz
        w = reb.prim("cube", "Block footprint", None, (x, y, 0.5), (sx + 0.1, sy + 0.1, 1.0))
        w.hide_render = True
        walls.append(reb.wall(w))
    blocks = reb.mesh_object("Cut blocks", bv, bf, block_m, smooth=False)
    reb.mask(reb.prim("cube", "Tall stack mask", None, (8.6, 5.6, 1.1), (1.8, 1.1, 2.2))).hide_render = True
    # Wedge holes along a split block, the feathers still in.
    for k in range(6):
        reb.prim("cube", "Wedge", mat("steel"), (8.0 + k * 0.22, 6.16, 2.2), (0.04, 0.03, 0.12))
    reb.prim("cube", "Timber dunnage", mat("planks"), (10.6, 5.5, 2.06), (1.7, 0.15, 0.12))
    # A half-lifted block on the sling, under the hook.
    hook_at = Vector((10.2, 7.4, 4.6))

    # ---- The derrick: the mast, its guys, the lattice boom out to the hook.
    mx, my = MAST
    reb.prim("cyl", "Derrick foot", mat("concrete"), (mx, my, 0.15), (1.4, 1.4, 0.3), segments=16)
    mast = kit.rod("Derrick mast", rust, (mx, my, 0.3), (mx, my, 11.5), 0.16, 12)
    reb.wall(reb.prim("cube", "Mast footprint", None, (mx, my, 0.5), (1.4, 1.4, 1.0))).hide_render = True
    reb.prim("cyl", "Mast cap", iron, (mx, my, 11.6), (0.5, 0.5, 0.2), segments=12)
    for (gx, gy, gz) in ((mx - 6, my - 10, 14.0), (mx + 9, my - 9, 12.5), (mx - 9, my + 8, 3.0), (mx + 4, my - 12, 13.5)):
        kit.rod("Guy wire", iron, (mx, my, 11.5), (gx, gy, gz), 0.018, 4)
    tip = Vector((10.2, 7.4, 8.8))
    heel = Vector((mx + 0.4, my + 0.3, 1.0))
    axis = (tip - heel).normalized()
    side = axis.cross(Vector((0, 0, 1))).normalized()
    up = side.cross(axis).normalized()
    chords = []
    for s, u in ((-1, -1), (1, -1), (0, 1)):
        a = heel + side * 0.32 * s + up * 0.3 * u
        b = tip + side * 0.08 * s + up * 0.08 * u
        chords.append((a, b))
        kit.rod("Boom chord", rust, a, b, 0.05, 6)
    lattice = []
    for k in range(13):
        t0, t1 = k / 13, (k + 1) / 13
        for i in range(3):
            a0, b0 = chords[i]
            a1, b1 = chords[(i + 1) % 3]
            lattice.append(kit.rod("Boom lace", rust, a0.lerp(b0, t0), a1.lerp(b1, t1), 0.02, 4))
    kit.join("Boom lacing", lattice)
    kit.rod("Boom topping line", iron, (mx, my, 11.4), tip, 0.02, 4)
    kit.rod("Boom topping line", iron, (mx, my, 11.0), tip + up * 0.1, 0.02, 4)
    reb.prim("cyl", "Boom sheave", iron, tip, (0.5, 0.5, 0.12), rot=(math.pi / 2, 0, math.atan2(axis.y, axis.x) + math.pi / 2), segments=14)
    # The hoist line down to the hook block, and the chain sling hanging empty.
    hook = reb.prim("sphere", "Hook pivot", iron, tip, (0.05, 0.05, 0.05))
    line = kit.rod("Hoist line", iron, (0, 0, 0), (0, 0, -(tip.z - hook_at.z)), 0.015, 4)
    block_h = reb.prim("cube", "Hook block", mat("yellow paint"), (0, 0, -(tip.z - hook_at.z) - 0.2), (0.3, 0.2, 0.45), bevel=0.03)
    hook_m = reb.prim("cone", "Hook", iron, (0, 0, -(tip.z - hook_at.z) - 0.55), (0.12, 0.12, 0.3), rot=(math.pi, 0, 0), segments=8)
    sling = []
    for k in range(10):
        a = (k / 9 - 0.5) * 2.4
        sling.append(reb.prim("sphere", "Sling link", iron, (0.25 * math.sin(a), 0, -(tip.z - hook_at.z) - 0.7 - 0.6 * math.cos(a * 0.6)), (0.06, 0.03, 0.08), segments=6))
    sl = kit.join("Chain sling", sling)
    for p in (line, block_h, hook_m, sl):
        p.parent = hook
    # The winch house at the foot: a drum of cable, the levers, the seat.
    winch = kit.box("Winch house", mat("tin"), (mx + 1.6, my + 1.4, 0.0), (1.6, 1.2, 1.7))
    reb.wall(winch)
    reb.mask(winch)
    reb.prim("cube", "Winch roof", rust, (mx + 1.6, my + 1.4, 1.75), (1.9, 1.5, 0.06), rot=(0.12, 0, 0))
    reb.prim("cyl", "Cable drum", iron, (mx + 1.6, my + 2.15, 0.55), (0.8, 0.8, 1.2), rot=(0, math.pi / 2, 0), segments=16)
    kit.rod("Winch lever", mat("steel"), (mx + 1.2, my + 2.3, 0.3), (mx + 1.1, my + 2.5, 1.1), 0.02)
    kit.rod("Winch lever", mat("steel"), (mx + 1.4, my + 2.3, 0.3), (mx + 1.5, my + 2.6, 1.05), 0.02)

    # ---- The crusher under the face: hopper, jaw box, the belt up to the gravel heap.
    cx0, cx1, cy0, cy1 = CRUSHER
    ccx, ccy = (cx0 + cx1) / 2, (cy0 + cy1) / 2
    for dx in (-1, 1):
        for dy in (-1, 1):
            reb.wall(kit.rod("Crusher leg", rust, (ccx + dx * 1.3, ccy + dy * 1.1, 0), (ccx + dx * 1.3, ccy + dy * 1.1, 3.4), 0.12, 6), "circle")
    jaw = kit.box("Jaw box", rust, (ccx, ccy, 0.6), (2.2, 1.8, 1.6), bevel=0.04)
    reb.prim("cone", "Hopper", rust, (ccx, ccy, 3.6), (3.6, 3.6, 1.6), rot=(math.pi, 0, math.pi / 4), segments=4, top=0.35)
    reb.prim("cube", "Hopper lip", iron, (ccx, ccy, 4.42), (2.6, 2.6, 0.08), rot=(0, 0, 0))
    reb.wall(reb.prim("cube", "Crusher footprint", None, (ccx, ccy, 0.5), (cx1 - cx0, cy1 - cy0, 1.0))).hide_render = True
    reb.prim("cyl", "Flywheel", iron, (cx1 + 0.15, ccy, 1.4), (1.6, 1.6, 0.14), rot=(0, math.pi / 2, 0), segments=24)
    reb.prim("cube", "Motor", mat("green paint"), (cx1 - 0.2, ccy + 1.0, 0.45), (0.9, 0.7, 0.9), bevel=0.04)
    kit.rod("Ladder rail", iron, (cx0 + 0.1, cy1 + 0.1, 0), (cx0 + 0.3, cy1 - 0.2, 4.4), 0.025, 6)
    kit.rod("Ladder rail", iron, (cx0 + 0.6, cy1 + 0.1, 0), (cx0 + 0.8, cy1 - 0.2, 4.4), 0.025, 6)
    rungs = [kit.rod("Rung", iron, (cx0 + 0.1 + 0.2 * t, cy1 + 0.1 - 0.3 * t, 4.4 * t), (cx0 + 0.6 + 0.2 * t, cy1 + 0.1 - 0.3 * t, 4.4 * t), 0.015, 4) for t in [k / 12 for k in range(1, 12)]]
    kit.join("Ladder rungs", rungs)
    belt_a, belt_b = Vector((ccx + 1.0, ccy - 0.2, 0.6)), Vector((cx1 + 3.4, cy0 + 1.0, 3.2))
    belt_dir = belt_b - belt_a
    reb.prim("cube", "Conveyor belt", mat("rubber"), (belt_a + belt_b) / 2, (belt_dir.length, 0.6, 0.06), rot=(0, -math.atan2(belt_dir.z, belt_dir.xy.length), math.atan2(belt_dir.y, belt_dir.x)))
    reb.prim("cube", "Conveyor frame", rust, (belt_a + belt_b) / 2 - Vector((0, 0, 0.12)), (belt_dir.length, 0.7, 0.14), rot=(0, -math.atan2(belt_dir.z, belt_dir.xy.length), math.atan2(belt_dir.y, belt_dir.x)))
    leg = belt_a.lerp(belt_b, 0.7)
    kit.rod("Conveyor leg", rust, (leg.x, leg.y, 0), leg - Vector((0, 0, 0.2)), 0.05)
    heap = reb.prim("cone", "Gravel heap", mat("gravel"), (belt_b.x + 0.4, belt_b.y + 0.4, 1.0), (3.6, 3.2, 2.0), segments=20, top=0.05)
    reb.wall(heap, "circle")
    kit.text("Crusher plate", "ARKLAY GRANITE CO.", mat("white paint"), (ccx, ccy + 0.92, 1.1), size=0.14, rot=(math.pi / 2, 0, math.pi))

    # ---- The old mine rails: from the crusher out east through the cut.
    rails("Mine rails", [(ccx, cy1 + 0.4), (ccx + 0.6, 5.2), (17.8, 6.3), (19.2, 6.7), (24.0, 6.9)], mat("logs"), rust)
    cart = kit.box("Ore cart", rust, (17.0, 6.1, 0.18), (1.1, 0.8, 0.65), rot=0.35, bevel=0.03)
    for dx in (-0.35, 0.35):
        for dy in (-0.3, 0.3):
            c, s = math.cos(0.35), math.sin(0.35)
            reb.prim("cyl", "Cart wheel", iron, (17.0 + dx * c - dy * s, 6.1 + dx * s + dy * c, 0.14), (0.28, 0.28, 0.05), rot=(math.pi / 2, 0, 0.35), segments=12)
    reb.wall(cart)
    reb.prim("cube", "Cart load", mat("rock"), (17.0, 6.1, 0.85), (0.95, 0.65, 0.12), rot=(0, 0, 0.35))
    kit.rod("Mine sign post", mat("dark wood"), (18.6, 4.9, 0), (18.6, 4.9, 2.2), 0.05)
    reb.prim("cube", "Mine sign", mat("planks"), (18.6, 4.95, 1.95), (1.3, 0.04, 0.32))
    kit.text("Mine sign words", "< ARKLAY MINE", mat("white paint"), (18.6, 4.98, 1.95), size=0.13, rot=(math.pi / 2, 0, math.pi))

    # ---- Hal's drips, from the east path across the floor to the cut and the mine.
    drips("Hal's drips", mat("old blood"), along([(X0, 9.6), (5.5, 9.8), (8.0, 9.3), (13.8, 9.0), (16.4, 7.6), (X1, 6.9)], 0.5, rng, skip=0.3), rng, r=(0.015, 0.035))

    # ---- The dogs' kill: dragged from the blocks to the open floor, gnawed.
    bxy = BODY
    kit.drag_trail("Drag from the blocks", mat("old blood"), [(12.6, 9.1), (12.3, 9.7), (11.9, 10.4), (11.4, 10.9)], width=0.5, seed=4)
    corpse("Quarryman", (bxy[0], bxy[1], 0.0), heading=0.8, pose="back", top=hivis, legs=mat("denim"), seed=7, missing=("l_hand", "r_knee"))
    reb.prim("cube", "Opened belly", reb.mat_surface("Gore", [(0.0, (0.15, 0.01, 0.01)), (0.6, (0.3, 0.04, 0.03)), (1.0, (0.4, 0.15, 0.12))], scale=20, rough=0.3, bump=0.6), (bxy[0] + 0.75, bxy[1] + 0.7, 0.2), (0.4, 0.3, 0.08), rot=(0, 0, 0.8), bevel=0.04)
    kit.bones("Gnawed bones", (bxy[0] - 0.6, bxy[1] + 1.0, 0.0), spread=0.6, seed=3, skull=False)
    kit.splat("Blood pool spread", mat("blood"), (bxy[0] + 0.5, bxy[1] + 0.6, 0.0), 0.8, seed=12, stretch=(1.5, 1.0))
    reb.prim("sphere", "Hard hat", mat("yellow paint"), (12.9, 10.9, 0.1), (0.3, 0.27, 0.22), rot=(0.9, 0.2, 0))
    reb.prim("cyl", "Hard hat brim", mat("yellow paint"), (12.9, 10.9, 0.06), (0.36, 0.34, 0.02), rot=(0.9, 0.2, 0), segments=16)
    reb.prim("cube", "Lunch tin", mat("tin"), (13.4, 9.6, 0.08), (0.3, 0.18, 0.16), rot=(0, 0, 0.8), bevel=0.02)
    reb.prim("cube", "Lunch tin lid", mat("tin"), (13.75, 9.4, 0.01), (0.3, 0.18, 0.02), rot=(0, 0, 1.4))
    reb.prim("cube", "Sandwich", reb.mat_plain("Bread", (0.45, 0.35, 0.2), 0.9), (13.6, 9.9, 0.02), (0.12, 0.12, 0.03), rot=(0, 0, 0.4))
    reb.prim("cyl", "Apple", reb.mat_plain("Apple", (0.3, 0.05, 0.03), 0.4), (13.1, 9.3, 0.04), (0.08, 0.08, 0.08), segments=10)
    reb.cloth("Torn shirt", mat("flannel"), (9.6, 11.2, 0.02), (0.5, 0.35), rot=(0, 0, 0.6), cuts=8, lumps=0.03, seed=7)
    pv, pf = [], []
    for k in range(40):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.6, 2.4)
        cx, cy = bxy[0] - 0.5 + math.cos(a) * r, bxy[1] + 0.3 + math.sin(a) * r * 0.8
        yaw = rng.uniform(0, 6.3)
        for (ox, oy, rr) in ((0, 0, 0.035), (0.05, 0.03, 0.014), (0.05, -0.03, 0.014), (0.07, 0.0, 0.014)):
            c, s = math.cos(yaw), math.sin(yaw)
            kit._stain(pv, pf, rng, (cx + ox * c - oy * s, cy + ox * s + oy * c, 0.004), rr, 0.0, 0.2, (1.0, 1.0), k, points=8, drops=False)
    reb.mesh_object("Paw prints", pv, pf, mat("old blood"), smooth=False)

    # ---- The office hut: corrugated tin, its door north, padlocked; the signs.
    hx0, hx1, hy0, hy1 = HUT
    corr = reb.mat_stripes("Corrugated", [(0.22, 0.21, 0.2), (0.12, 0.11, 0.1)], across=30.0, axis="X")
    corr_y = reb.mat_stripes("Corrugated y", [(0.22, 0.21, 0.2), (0.12, 0.11, 0.1)], across=30.0, axis="Y")
    for side, at, size, m_ in (("n", ((hx0 + hx1) / 2, hy0, 1.25), (hx1 - hx0, 0.08, 2.5), corr), ("s", ((hx0 + hx1) / 2, hy1, 1.25), (hx1 - hx0, 0.08, 2.5), corr), ("w", (hx0, (hy0 + hy1) / 2, 1.25), (0.08, hy1 - hy0, 2.5), corr_y), ("e", (hx1, (hy0 + hy1) / 2, 1.25), (0.08, hy1 - hy0, 2.5), corr_y)):
        reb.wall(reb.prim("cube", f"Hut wall {side}", m_, at, size))
    reb.prim("cube", "Hut roof", rust, ((hx0 + hx1) / 2, (hy0 + hy1) / 2, 2.53), (hx1 - hx0 + 0.5, hy1 - hy0 + 0.5, 0.06))
    reb.wall(reb.prim("cube", "Hut footprint", None, ((hx0 + hx1) / 2, (hy0 + hy1) / 2, 0.5), (hx1 - hx0 + 0.1, hy1 - hy0 + 0.1, 1.0))).hide_render = True
    hd0, hd1 = HUT_DOOR
    reb.prim("cube", "Hut door", mat("green paint"), ((hd0 + hd1) / 2, hy0 - 0.05, 1.0), (hd1 - hd0, 0.04, 2.0))
    for x in (hd0 - 0.03, hd1 + 0.03):
        reb.prim("cube", "Hut door frame", mat("dark wood"), (x, hy0 - 0.06, 1.03), (0.06, 0.06, 2.06))
    reb.prim("cube", "Hasp", mat("steel"), (hd1 - 0.12, hy0 - 0.08, 1.05), (0.06, 0.02, 0.16))
    reb.prim("cube", "Padlock", mat("steel"), (hd1 - 0.12, hy0 - 0.1, 0.94), (0.07, 0.03, 0.08), bevel=0.01)
    reb.prim("cube", "Hut window", reb.mat_glass("Grimy glass", (0.35, 0.36, 0.33)), (4.95, hy0 - 0.05, 1.5), (0.7, 0.01, 0.6))
    reb.prim("cube", "Hut window frame", mat("dark wood"), (4.95, hy0 - 0.06, 1.5), (0.78, 0.02, 0.68))
    reb.prim("cube", "Hut window dark", reb.mat_plain("Dark inside", (0.01, 0.01, 0.01), 0.9), (4.95, hy0 - 0.045, 1.5), (0.7, 0.005, 0.6))
    reb.prim("cube", "Office board", mat("white paint"), (2.75, hy0 - 0.06, 2.0), (1.1, 0.03, 0.3))
    kit.text("Office words", "QUARRY OFFICE", mat("black"), (2.75, hy0 - 0.08, 2.0), size=0.12, rot=(math.pi / 2, 0, math.pi))
    reb.prim("cube", "Danger board", mat("red paint"), (2.75, hy0 - 0.06, 1.35), (0.9, 0.03, 0.55))
    kit.text("Danger words", "DANGER\nEXPLOSIVES", mat("white paint"), (2.75, hy0 - 0.08, 1.35), size=0.13, rot=(math.pi / 2, 0, math.pi))
    reb.prim("cube", "Hut step", mat("concrete"), ((hd0 + hd1) / 2, hy0 - 0.3, 0.06), (1.2, 0.5, 0.12))
    kit.drum("Diesel drum", rust, (hx1 + 0.5, hy0 + 0.6, 0.0))
    kit.drum("Diesel drum", mat("red paint"), (hx1 + 0.55, hy0 + 1.35, 0.0), tipped=True, rot=1.4)
    reb.wall(reb.prim("cube", "Drums footprint", None, (hx1 + 0.55, hy0 + 1.0, 0.5), (0.8, 1.6, 1.0))).hide_render = True
    # A siren pole by the hut.
    reb.wall(kit.rod("Siren pole", mat("dark wood"), (1.6, 12.2, 0), (1.6, 12.2, 5.0), 0.1), "circle")
    reb.prim("cone", "Siren horn", mat("steel"), (1.85, 12.2, 4.7), (0.3, 0.3, 0.5), rot=(0, math.pi / 2, 0), segments=12, top=0.4)
    crow("Crow on the siren", (1.6, 12.2, 5.02), heading=2.0)

    # ---- The dead truck by the spoil lip.
    tm = reb.mat_surface("Truck paint", [(0.0, (0.1, 0.12, 0.08)), (0.6, (0.16, 0.18, 0.12)), (1.0, (0.25, 0.12, 0.05))], scale=5, rough=0.6, bump=0.15)
    reb.prim("cube", "Truck cab", tm, (17.2, 15.6, 1.4), (1.6, 2.0, 1.5), bevel=0.08)
    reb.prim("cube", "Truck bonnet", tm, (18.3, 15.6, 1.05), (0.9, 1.7, 0.8), bevel=0.06)
    reb.prim("cube", "Truck windscreen", reb.mat_glass("Truck glass", (0.3, 0.32, 0.3)), (17.95, 15.6, 1.8), (0.05, 1.7, 0.55))
    reb.prim("cube", "Truck bed", rust, (14.8, 15.6, 1.05), (3.4, 2.2, 0.15))
    for y in (14.55, 16.65):
        reb.prim("cube", "Truck bed side", rust, (14.8, y, 1.35), (3.4, 0.08, 0.5))
    reb.prim("cube", "Truck chassis", iron, (15.8, 15.6, 0.65), (5.0, 1.2, 0.3))
    for x in (13.8, 15.4, 17.9):
        for y in (14.65, 16.55):
            reb.prim("cyl", "Truck wheel", mat("rubber"), (x, y, 0.42), (0.85, 0.85, 0.3), rot=(math.pi / 2, 0, 0), segments=16)
    reb.wall(reb.prim("cube", "Truck footprint", None, (16.0, 15.6, 0.5), (5.6, 2.3, 1.0))).hide_render = True
    reb.cloth("Tarp on the bed", mat("canvas"), (14.6, 15.6, 1.25), (2.8, 2.0), cuts=10, lumps=0.12, seed=9)

    # ---- Dust off the cut: sheets of haze over the benches drifting in the wind.
    dust = []
    for k, (x, y, z, w, h, yaw) in enumerate(((8.0, -3.0, 13.0, 14.0, 8.0, 0.0), (15.5, -4.0, 15.0, 12.0, 7.0, 0.1), (4.0, -1.0, 9.5, 9.0, 6.0, -0.1), (11.5, 0.2, 5.0, 11.0, 4.0, 0.0), (18.0, -1.5, 9.0, 8.0, 6.0, 0.4))):
        v = [(-0.5, 0, -0.5), (0.5, 0, -0.5), (0.5, 0, 0.5), (-0.5, 0, 0.5)]
        ob = reb.mesh_object(f"Dust sheet {k}", v, [(0, 1, 2, 3)], dust_m, smooth=False)
        ob.location = (x, y, z)
        ob.scale = (w, 1, h)
        ob.rotation_euler = (0, 0, yaw)
        ob.visible_shadow = False
        dust.append(ob)

    # ---- Round it: spruces over the rims and the lip, the valley south.
    def keep_out(x, y):
        return (X0 - 3 < x < X1 + 3 and Y0 - 7 < y) or y > Y1 - 2 or (x < X0 and abs(y - 9.5) < 2.5) or (x > X1 and abs(y - 6.8) < 2.5)
    kit.forest(rng, height, keep_out, (-14, -14, 34, 26), count=60, ferns=14, needles=400)
    lip = kit.meadow(rng, 900, lambda r: (r.uniform(-6, 26), r.uniform(Y1 + 0.4, Y1 + 5.0)), height, mat("dead grass"))
    kit.meadow(rng, 300, lambda r: (r.uniform(X0, X1), r.uniform(Y1 - 1.0, Y1 + 0.3)), height, mat("dead grass"))
    kit.meadow(rng, 200, lambda r: (r.uniform(X0, X1), r.uniform(Y0, Y0 + 0.8)), height, mat("dead grass"))

    # ---- Light: the low sun in the south-west, hard across the granite.
    sun = kit.time_light("afternoon", sun_heading=232, sun_energy=4.6)
    # Late and harsh: the sun low over the west rim, amber, the sky dimmer so the shadows go deep.
    sun.rotation_euler[0] = math.radians(90 - 21)
    sun.data.color = (1.0, 0.7, 0.42)
    bpy.context.scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.55
    kit.vista(rng, (10.0, Y1 + 6), (0.0, 1.0), below=-90.0)

    anim = kit.Anim(16)
    mp = dust_m.node_tree.nodes["Drift"]

    def drift(k):
        a = anim.phase(k)
        mp.inputs["Location"].default_value = (1.6 * math.cos(a), 0.5 * math.sin(a), 0.6 * math.sin(a))
    anim.custom(drift)
    anim.custom(lambda k: setattr(hook, "rotation_euler", (math.radians(2.5) * math.sin(anim.phase(k)), math.radians(1.5) * math.cos(anim.phase(k)), 0)))
    anim.flies((bxy[0] + 0.75, bxy[1] + 0.7, 0.15), count=10, radius=0.5)
    anim.sway(lip, amount=0.05)

    # ---- What the game needs.
    room.door("east-path", (X0, ENTRY[0] + 0.4, X0 + 0.6, ENTRY[1] - 0.4), arrive=(2.4, 9.5), face=(1, 0))
    room.door("quarry-office", (hd0, hy0 - 0.6, hd1, hy0), arrive=(3.75, 11.2), face=(0, -1), walk=False)
    room.door("mine-entrance", (X1 - 0.6, CUT[0] + 0.3, X1, CUT[1] - 0.3), arrive=(17.4, 7.4), face=(-1, 0))
    room.check((10.0, 10.3, 12.3, 12.0), "One of the quarrymen. The dogs have been at him.\nThey dragged him out from behind the blocks.")
    room.check((12.5, 9.0, 13.9, 10.3), "His hard hat. His lunch, spilled. He was sitting down to eat.")
    room.check((hd0 - 0.4, hy0 - 0.7, hd1 + 0.4, hy0), "QUARRY OFFICE. DANGER, EXPLOSIVES.\nThe door's padlocked.")
    room.check((2.6, 1.8, 6.4, 4.4), "The derrick crane. Its hook's still swinging over the blocks.")
    room.check((7.6, 4.9, 13.9, 6.4), "Cut granite, stacked ready to go. Nobody's coming for it now.")
    room.check((cx0, cy1, cx1, cy1 + 0.7), "ARKLAY GRANITE CO. The crusher's rusted solid.")
    room.check((17.6, 4.6, X1, 5.6), "Old rails, running off east. ARKLAY MINE.")
    room.check((13.0, 13.8, X1, 14.5), "A truck, dead on its rims.")
    room.entry = "A quarry. Something's been feeding here."
    room.export(anim)


build()
