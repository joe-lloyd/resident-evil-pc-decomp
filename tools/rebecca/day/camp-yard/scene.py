"""The logging camp's yard, noon under cloud: the hub of the camp.

What it tells: about twenty men worked here for Arklay Timber. They got
sick one by one, and they shut the gate. Then they burned the sick in the
fire pit: one is still there, curled black in the ash, a thin smoke coming
off him. Then the well turned on the sick, and the sick on the well. A fire
axe is buried in the bunkhouse door, which someone held shut from inside.
One man sat down against the log deck with a shotgun and fired until it was
empty. Everything else stopped where it was: a log half cut on the
sawhorses with the chainsaw left on it, the cookhouse woodpile and its
garbage, the laundry still on the line, the skidder with its chokers on
three logs, smoke from the mess chimney where the range is still warm. A
player should work out that the camp sealed itself in, and that the
sickness came from inside the fence.

Metres: the yard floor is x 1.0-18.4, y 1.0-18.6.
- North: the bunkhouse, x 6.0-17.0, y -3.4-1.6, brown boards, windows in
  its south wall; its door at x 11.0-11.9 (the bunkhouse inside is x 1-12,
  y 1-6, door at x 6.0-6.9 in its south wall).
- North-west: the foreman's office, x 1.0-4.6, y 0.6-3.6, green boards; its
  door in the south wall at x 2.5-3.4, windows south at x 3.75-4.35 and east
  at y 1.2-2.3 (inside: x 1-4.6, y 1-4, the same shifted 0.4 south).
- West: the mess hall, x -3.4-2.0, y 5.0-14.0, whitewashed boards; its door
  in the east wall at y 9.0-9.9, windows at y 6.0-7.4 and 11.2-12.6 (inside:
  x 1-6.4, y 1-10, shifted 4 south and 4.4 east), its chimney smoking.
- South-west: the fuel depot's fenced compound, x -2.0-6.6, y 15.2-21; its
  gate in the north fence at x 2.6-4.4, shut and chained (the depot is that
  compound moved 3 east and 14.2 north).
- South: the camp gate between log posts at x 8.4 and 11.8 on y 18.9.
- South-east: the workshop, tin, x 13.4-19.2, y 13.8-19.4; its door in the
  north wall at x 14.6-15.8, a window north at x 17.0-18.2 and west at y
  15.4-16.6 (inside: x 1-6.8, y 1-6.6, door at x 2.2-3.4).
- East: the sawmill, west wall at x 18.5 from y 2.6 to 12.2, its big doors
  shut at y 6.0-9.0.
- In the yard: the fire pit at (9.0, 8.3), the bell post at (3.2, 7.3), the
  log deck at x 12.6-17.4, y 2.4-4.6, the skidder at x 5.6-10.4, y 11.8-14.2,
  the laundry line from (5.6, 2.6) to (9.8, 3.4), the sawhorses at (11.8,
  15.4), the cookhouse woodpile along the mess wall at y 10.4-13.2.
Every door is shut: she opens each with the action button.

Moving: a thin smoke off the body in the fire pit and the mess chimney, the
embers' glow, the bell, the laundry stirring. The grass is still: no wind
reaches the camp.
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

X0, X1, Y0, Y1 = 1.0, 18.4, 1.0, 18.6
T = 0.12  # wall thickness

BUNK = (6.0, 17.0, -3.4, 1.6)
BUNK_DOOR = (11.0, 11.9)
OFFICE = (1.0, 4.6, 0.6, 3.6)
OFFICE_DOOR = (2.5, 3.4)
MESS = (-3.4, 2.0, 5.0, 14.0)
MESS_DOOR = (9.0, 9.9)
WORK = (13.4, 19.2, 13.8, 19.4)
WORK_DOOR = (14.6, 15.8)
MILL_X = 18.5
MILL = (MILL_X, 32.0, 2.6, 12.2)
MILL_DOOR = (6.0, 9.0)
DEPOT = (-2.0, 6.6, 15.2, 21.0)
DEPOT_GATE = (2.6, 4.4)
GATE = (8.4, 11.8)
GATE_Y = 18.9
PIT = (9.0, 8.3)
CENTRE = (9.7, 9.8)


def height(x, y):
    """The yard flat and trodden; the mountain rising north and west, falling off east."""
    if -6 < x < 34 and -6 < y < 23:
        return -0.02 + 0.012 * noise.noise(Vector((x * 0.7, y * 0.7, 3)))
    h = 0.4 * noise.noise(Vector((x * 0.08, y * 0.08, 1)))
    if y < -6:
        h += (-6 - y) * 0.35
    if x < -6:
        h += (-6 - x) * 0.3
    if y > 23:
        h -= (y - 23) * 0.12
    return h


def far_land(x, y, z):
    """The kit's ranges, eased into the camp's own mountainside near it."""
    r = math.hypot(x - CENTRE[0], y - CENTRE[1])
    w = max(0.0, min(1.0, (240.0 - r) / 180.0))
    own = height(x, y) - 0.5
    return z + (own - z) * w * w * (3 - 2 * w)


# ---------------------------------------------------------------------------
# Helpers this scene needs
# ---------------------------------------------------------------------------


def corrugated(name, rgb, rust=(0.3, 0.13, 0.05), pitch=0.076):
    """Corrugated tin: ridges every `pitch` metres along x + y, rust in blotches."""
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Roughness"].default_value = 0.55
    bsdf.inputs["Metallic"].default_value = 0.3
    n = reb.noise_tex(nodes, links, 1.6, 8, 0.65)
    col = reb.ramp(nodes, links, n.outputs["Fac"], [(0.35, tuple(c * 0.6 for c in rgb)), (0.55, rgb), (0.72, rust), (1.0, tuple(c * 0.6 for c in rust))])
    links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Object"], sep.inputs["Vector"])
    add = nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    links.new(sep.outputs["X"], add.inputs[0])
    links.new(sep.outputs["Y"], add.inputs[1])
    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 2 * math.pi / pitch
    links.new(add.outputs[0], mul.inputs[0])
    sine = nodes.new("ShaderNodeMath")
    sine.operation = "SINE"
    links.new(mul.outputs[0], sine.inputs[0])
    reb.bumped(nodes, links, bsdf, sine.outputs[0], 0.6, 0.01)
    return m


def smoke_mat(name, density=0.5, rgb=(0.5, 0.5, 0.51)):
    """A wisp of smoke: a volume, thin and torn by noise, whose amount the
    Anim turns up and down (returns the material and its amount input)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.remove(nodes["Principled BSDF"])
    vol = nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*rgb, 1)
    n = reb.noise_tex(nodes, links, 2.2, 4, 0.6)
    tc = nodes.new("ShaderNodeTexCoord")
    grad = nodes.new("ShaderNodeVectorMath")
    grad.operation = "LENGTH"
    links.new(tc.outputs["Object"], grad.inputs[0])
    edge = nodes.new("ShaderNodeMapRange")
    edge.inputs["From Min"].default_value = 0.5
    edge.inputs["From Max"].default_value = 0.1
    links.new(grad.outputs["Value"], edge.inputs["Value"])
    wisp = nodes.new("ShaderNodeMapRange")
    wisp.inputs["From Min"].default_value = 0.45
    wisp.inputs["From Max"].default_value = 0.75
    links.new(n.outputs["Fac"], wisp.inputs["Value"])
    both = nodes.new("ShaderNodeMath")
    both.operation = "MULTIPLY"
    links.new(edge.outputs["Result"], both.inputs[0])
    links.new(wisp.outputs["Result"], both.inputs[1])
    amount = nodes.new("ShaderNodeMath")
    amount.operation = "MULTIPLY"
    amount.inputs[1].default_value = density
    links.new(both.outputs[0], amount.inputs[0])
    links.new(amount.outputs[0], vol.inputs["Density"])
    links.new(vol.outputs["Volume"], nodes["Material Output"].inputs["Volume"])
    return m, amount.inputs[1]


def smoke_column(name, base, puffs=5, rise=2.6, drift=(0.5, 0.2), size=(0.35, 1.1), density=0.6):
    """Puffs climbing from `base` and fading, one loop; returns the anim function."""
    parts = []
    for i in range(puffs):
        m, vol = smoke_mat(f"{name} {i}", density)
        ob = reb.prim("sphere", f"{name} puff {i}", m, base, (1, 1, 1.4), segments=10)
        parts.append((ob, vol, i / puffs))

    def f(k, frames=16):
        for ob, vol, off in parts:
            t = (k / frames + off) % 1.0
            ob.location = (base[0] + drift[0] * t * t, base[1] + drift[1] * t * t, base[2] + rise * t)
            s = size[0] + (size[1] - size[0]) * t
            ob.scale = (s, s, s * 1.3)
            vol.default_value = density * math.sin(math.pi * t) ** 0.7
    f(0)
    return f


def logs_mesh(name, logs, bark=None, end=None):
    """Logs [(a, b, r)] as two meshes: bark sides and sawn ends."""
    sv, sf, ev, ef = [], [], [], []
    seg = 10
    for a, b, r in logs:
        a, b = Vector(a), Vector(b)
        d = (b - a).normalized()
        u = d.orthogonal().normalized()
        w = d.cross(u)
        k = len(sv)
        for end_pt in (a, b):
            for i in range(seg):
                ang = 2 * math.pi * i / seg
                rr = r * (1 + 0.08 * math.sin(ang * 3 + a.x) + 0.04 * math.sin(ang * 7 + a.y))
                sv.append(tuple(end_pt + (u * math.cos(ang) + w * math.sin(ang)) * rr))
        for i in range(seg):
            sf.append((k + i, k + (i + 1) % seg, k + seg + (i + 1) % seg, k + seg + i))
        for end_pt, base in ((a, k), (b, k + seg)):
            c = len(ev)
            ev.append(tuple(end_pt))
            for i in range(seg):
                ev.append(sv[base + i])
            ef.extend((c, c + 1 + i, c + 1 + (i + 1) % seg) for i in range(seg))
    sides = reb.mesh_object(name, sv, sf, bark or mat("bark"))
    ends = reb.mesh_object(f"{name} ends", ev, ef, end or log_end(), smooth=False)
    return sides, ends


_log_end = []


def log_end():
    if not _log_end:
        _log_end.append(reb.mat_surface("Sawn log end", [(0.0, (0.2, 0.14, 0.08)), (0.5, (0.42, 0.32, 0.19)), (1.0, (0.3, 0.2, 0.11))], scale=9, bump=0.3))
    return _log_end[0]


def fence(verts, faces, a, b, rng, h=1.9, board=0.2, lean=0.04):
    """A slab fence of rough vertical boards from a to b, with two rails behind."""
    a, b = Vector(a), Vector(b)
    d = b - a
    n = max(1, int(d.length / board))
    yaw = math.atan2(d.y, d.x)
    for i in range(n):
        p = a.lerp(b, (i + 0.5) / n)
        hh = h * rng.uniform(0.88, 1.04)
        reb.box(verts, faces, (p.x, p.y, hh / 2), (board * 0.92, 0.04, hh), yaw + rng.uniform(-lean, lean))
    side = Vector((-d.y, d.x)).normalized() * 0.05
    for z in (0.45, 1.5):
        m = (a + b) / 2 + side
        reb.box(verts, faces, (m.x, m.y, z), (d.length, 0.04, 0.09), yaw)


def chain_link():
    """Wire mesh you can see through: mostly transparent, grey where the wire is."""
    m, nodes, links, bsdf = reb.nodes_material("Chain link")
    bsdf.inputs["Base Color"].default_value = (0.2, 0.2, 0.19, 1)
    bsdf.inputs["Metallic"].default_value = 0.6
    bsdf.inputs["Roughness"].default_value = 0.5
    out = nodes["Material Output"]
    clear = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    n = reb.noise_tex(nodes, links, 3, 4, 0.5)
    r = reb.ramp(nodes, links, n.outputs["Fac"], [(0.3, (0.55, 0.55, 0.55)), (0.7, (0.75, 0.75, 0.75))])
    links.new(r.outputs["Color"], mix.inputs["Fac"])
    links.new(bsdf.outputs["BSDF"], mix.inputs[1])
    links.new(clear.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return m


def garment(name, m, kind, w, h, seed=0):
    """Washing as it hangs from a line: a shirt with its sleeves, long johns
    with two legs, a towel or a sock, cut from a sheet hanging down from
    z = 0 in the x-z plane, with folds running down it and the hem sagging.
    Returns the object, origin at the line."""
    rng = random.Random(seed)
    nx, nz = 16, 18

    def inside(u, v):
        """u across from -0.5 to 0.5 of the width, v down from 0 to 1 of the height."""
        if kind == "shirt":
            body = abs(u) < 0.32 and v < 1.0
            arm = abs(u) < 0.5 and v < 0.42 - 0.25 * (abs(u) - 0.32) / 0.18 and v > 0.0
            return body or arm
        if kind == "johns":
            return (abs(u) < 0.42 and v < 0.38) or (0.04 < abs(u) < 0.42 - 0.06 * v)
        return True
    v, f, idx = [], [], {}
    for j in range(nz + 1):
        for i in range(nx + 1):
            u, vv = i / nx - 0.5, j / nz
            x = u * w
            sag = 0.05 * h * math.sin(math.pi * (u + 0.5)) * vv
            fold = 0.035 * math.sin(u * 19 + seed) * vv + 0.02 * noise.noise(Vector((x * 6, vv * 4, seed)))
            idx[i, j] = len(v)
            v.append((x, fold + rng.uniform(-0.004, 0.004), -vv * h - sag * 0.3))
    for j in range(nz):
        for i in range(nx):
            u, vv = (i + 0.5) / nx - 0.5, (j + 0.5) / nz
            if inside(u, vv):
                f.append((idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]))
    ob = reb.mesh_object(name, v, f, m)
    mod = ob.modifiers.new("Thickness", "SOLIDIFY")
    mod.thickness = 0.008
    return ob


def oil_spill(name, m, at, r, heading, seed=0):
    """Oil that splashed and soaked in: a ragged main stain trailing off in
    one direction into smaller blots and drops, not one round pool."""
    rng = random.Random(seed)
    x, y, z = at
    d = Vector((math.cos(heading), math.sin(heading)))
    kit.splat(name, m, (x, y, z), r, rot=(0, 0, heading), seed=seed, stretch=(1.5, 0.7), lumps=0.6)
    for i in range(5):
        t = r * (0.9 + i * 0.45)
        p = Vector((x, y)) + d * t + Vector((-d.y, d.x)) * rng.uniform(-0.35, 0.35) * r
        kit.splat(f"{name} blot {i}", m, (p.x, p.y, z + 0.0005), r * rng.uniform(0.12, 0.3) * (1 - i * 0.12), rot=(0, 0, rng.uniform(0, 6)), seed=seed * 13 + i, lumps=0.6)


# ---------------------------------------------------------------------------
# The yard
# ---------------------------------------------------------------------------


def build():
    rng = random.Random(404)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("earth")  # mud, trodden earth, puddles too small to wade
    cams = [
        ((10.4, 20.6, 3.9), (10.2, 11.5, 0.2), "from the gate: the sawhorses, the skidder, the fire pit, the bunkhouse beyond"),
        ((5.2, 6.4, 3.3), (15.0, 14.6, 0.3), "from by the office: the burned man in the fire pit, the skidder's blade, the workshop door"),
        ((12.0, 12.6, 3.6), (16.6, 4.4, 0.4), "from the ruts: the sawmill's shut doors, the log deck, the dead man against it"),
        ((5.0, 8.4, 3.4), (12.5, 2.0, 0.6), "from the bell post: the laundry, the bunkhouse door with the axe in it"),
        ((9.4, 10.6, 3.4), (2.4, 3.6, 0.5), "from the fire pit: the office door in the corner, the bell post, the laundry"),
        ((8.4, 10.0, 3.3), (2.0, 9.8, 0.6), "from the ruts: the mess door, the bell, the cookhouse woodpile"),
        ((12.4, 17.8, 3.4), (3.5, 13.6, 0.3), "from inside the gate: the depot's chained gate, the choked logs"),
        ((11.0, 9.6, 3.6), (17.0, 13.6, 0.4), "from the fire pit: the workshop door, the leaking drums, the mill"),
    ]
    for eye, look, note in cams:
        room.camera(eye, look, 200, note)

    # ---- Materials.
    yard = kit.dirtied(reb.mat_surface("Yard earth", [(0.0, (0.03, 0.022, 0.014)), (0.3, (0.06, 0.045, 0.03)), (0.55, (0.1, 0.078, 0.052)),
                                                      (0.75, (0.085, 0.07, 0.05)), (1.0, (0.13, 0.11, 0.08))], scale=1.6, detail=14, rough=0.75, bump=0.7), 0.7, scale=0.35)
    wet = reb.mat_surface("Wet ground", [(0.0, (0.012, 0.01, 0.008)), (0.6, (0.03, 0.024, 0.017)), (1.0, (0.05, 0.04, 0.03))], scale=8, rough=0.3, bump=0.3)
    brown = kit.boards("Bunkhouse boards", (0.17, 0.11, 0.07), width=0.22, grime=0.8)
    green = kit.boards("Office boards", (0.08, 0.14, 0.09), width=0.16, grime=0.8)
    white = kit.boards("Mess boards", (0.42, 0.4, 0.36), width=0.18, grime=0.9)
    grey = kit.boards("Mill boards", (0.2, 0.19, 0.17), width=0.3, grime=0.8)
    tin = corrugated("Roof tin", (0.26, 0.26, 0.25))
    tin_wall = corrugated("Workshop tin", (0.22, 0.24, 0.23), pitch=0.1)
    frame_m = mat("dark wood")
    glass_m = reb.mat_glass("Grimy glass", (0.32, 0.34, 0.3))
    yellow = reb.mat_surface("Skidder yellow", [(0.0, (0.3, 0.2, 0.02)), (0.6, (0.5, 0.34, 0.03)), (0.8, (0.25, 0.12, 0.04)), (1.0, (0.08, 0.05, 0.03))], scale=3, rough=0.55, bump=0.2)
    ash = reb.mat_surface("Ash", [(0.0, (0.03, 0.03, 0.03)), (0.6, (0.12, 0.115, 0.11)), (1.0, (0.22, 0.21, 0.2))], scale=6, bump=0.4)
    char = reb.mat_surface("Charred", [(0.0, (0.006, 0.005, 0.005)), (0.5, (0.018, 0.014, 0.012)), (0.7, (0.045, 0.03, 0.022)), (0.85, (0.14, 0.135, 0.13)), (1.0, (0.2, 0.08, 0.03))], scale=14, rough=0.85, bump=1.0)
    oil = reb.mat_surface("Oil soak", [(0.0, (0.008, 0.007, 0.006)), (0.6, (0.02, 0.017, 0.013)), (1.0, (0.04, 0.034, 0.026))], scale=10, rough=0.35, bump=0.15)
    hard_hat = reb.mat_plain("Hard hat", (0.5, 0.3, 0.02), 0.4)
    stencil_m = kit.dirtied(reb.mat_plain("Stencil white", (0.5, 0.48, 0.42), 0.6), 0.6, scale=20)

    # ---- Ground: one surface of trodden earth, wet where the rain stood, the ruts in it.
    reb.terrain("Ground", yard, (-30, 50), (-30, 55), height, step=0.5)
    kit.ruts("Ruts to the mill", [(10.3, 26.0), (10.4, 19.0), (10.2, 15.6), (11.2, 12.4), (13.6, 9.6), (16.4, 8.0), (19.5, 7.4)], height, gauge=1.7, width=0.32, seed=2.0)
    # Stones, bark and woodchips trodden into the earth, thick round the log deck and the mill.
    stones = [(rng.uniform(X0 - 1, X1 + 1), rng.uniform(Y0 - 0.5, Y1 + 1), rng.uniform(0.03, 0.09)) for _ in range(70)]
    kit.rocks("Yard stones", rng, stones, height, kit.dirtied(mat("rock"), 0.7), grass=False)
    cv, cf = [], []
    for _ in range(900):
        if rng.random() < 0.55:
            x, y = rng.gauss(15.0, 2.0), rng.gauss(5.5, 2.2)
        else:
            x, y = rng.uniform(X0, X1), rng.uniform(Y0, Y1)
        reb.card(cv, cf, Vector((x, y, height(x, y) + 0.006)), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), Vector((0, 0, 1)), rng.uniform(0.03, 0.06), rng.uniform(0.05, 0.14), 0.0)
    reb.mesh_object("Woodchips and bark", cv, cf, reb.mat_surface("Woodchips", [(0.0, (0.12, 0.08, 0.045)), (0.6, (0.3, 0.22, 0.13)), (1.0, (0.4, 0.31, 0.19))], scale=40, bump=0.3), smooth=False)

    # ---- The buildings, every door shut.
    # The bunkhouse along the north: long, low, brown boards, windows in a row.
    bwin = [(7.0, 8.0), (8.9, 9.9), (13.0, 14.0), (15.0, 16.0)]
    kit.hut("Bunkhouse", BUNK, 2.4, brown, tin, [("s", BUNK_DOOR[0], BUNK_DOOR[1], 0.0, 2.05)] + [("s", a, b, 1.0, 1.7) for a, b in bwin], ridge="x", pitch=0.48, thick=T)
    for i, (a, b) in enumerate(bwin):
        kit.hut_window(BUNK, "s", a, b, 1.0, 1.7, frame_m, glass_m, thick=T, boarded=i == 1, broken=i == 2)
    kit.shards("Glass under the bunkhouse window", (13.5, 2.1, 0.0), spread=0.6, count=14, seed=4)
    bdoor = kit.shut_door("Bunkhouse door", BUNK, "s", BUNK_DOOR[0], BUNK_DOOR[1], 2.05, mat("planks"), thick=T)
    reb.prim("cube", "Step", mat("planks"), ((BUNK_DOOR[0] + BUNK_DOOR[1]) / 2, BUNK[3] + T + 0.25, 0.08), (1.4, 0.5, 0.16))
    # The fire axe buried in it, chips of fresh wood, the gouges.
    face = BUNK[3] + T
    axe_at = Vector((BUNK_DOOR[0] + 0.3, face + 0.02, 1.3))
    kit.rod("Axe handle", reb.mat_wood("Axe handle", (0.4, 0.28, 0.14)), axe_at + Vector((0, 0.02, 0)), axe_at + Vector((0.3, 0.7, -0.3)), 0.02)
    reb.prim("cube", "Axe head", reb.mat_plain("Fire axe red", (0.4, 0.03, 0.02), 0.45), axe_at + Vector((-0.02, 0.0, 0.02)), (0.2, 0.06, 0.12), rot=(0, 0.35, 0.2))
    for i in range(4):
        reb.prim("cube", f"Axe cut {i}", reb.mat_wood("Fresh wood", (0.45, 0.34, 0.2)), (BUNK_DOOR[0] + rng.uniform(0.15, 0.75), face + 0.03, 1.3 + rng.uniform(-0.35, 0.3)), (0.16, 0.02, 0.025), rot=(0, rng.uniform(-0.6, 0.6), 0))
    kit.scratches("Gouges in the door", mat("black"), (BUNK_DOOR[0] + 0.45, face + 0.03, 1.0), (0, 1), count=4, length=0.4, seed=3)
    kit.splat("Handprint by the bunkhouse door", mat("old blood"), (BUNK_DOOR[1] + 0.14, face + 0.004, 1.15), 0.07, rot=(math.pi / 2, 0, 0), seed=5)
    for x in (8.0, 13.0, 15.2):
        kit.bunk(f"Bunk inside {x}", mat("iron"), (x, -2.4, 0.0), seed=int(x))
    kit.bottles("Bottles by the step", (12.6, 2.4, 0.0), count=5, spread=0.5, seed=4, tipped=0.8)
    kit.crate("Boot crate by the step", mat("planks"), (9.9, 2.05, 0.0), size=(0.6, 0.4, 0.35), rot=0.1, open_=True)
    for i, x in enumerate((10.0, 10.25)):
        reb.prim("cube", f"Boot {i}", mat("black"), (x, 2.45, 0.08), (0.12, 0.3, 0.16), rot=(0, 0, 0.3 * i), bevel=0.03)

    # The foreman's office in the north-west corner: green boards, a stovepipe.
    kit.hut("Office", OFFICE, 2.5, green, tin, [("s", OFFICE_DOOR[0], OFFICE_DOOR[1], 0.0, 2.05), ("s", 3.75, 4.35, 1.0, 1.8), ("e", 1.2, 2.3, 1.0, 1.8)], ridge="y", pitch=0.5, eaves=0.3, thick=T)
    kit.hut_window(OFFICE, "s", 3.75, 4.35, 1.0, 1.8, frame_m, glass_m, thick=T)
    kit.hut_window(OFFICE, "e", 1.2, 2.3, 1.0, 1.8, frame_m, glass_m, thick=T)
    kit.shut_door("Office door", OFFICE, "s", OFFICE_DOOR[0], OFFICE_DOOR[1], 2.05, mat("green paint"), thick=T)
    reb.prim("cube", "Office sign", mat("white paint"), ((OFFICE_DOOR[0] + OFFICE_DOOR[1]) / 2, OFFICE[3] + T + 0.02, 2.3), (0.8, 0.03, 0.2))
    kit.text("Office sign words", "OFFICE", mat("black"), ((OFFICE_DOOR[0] + OFFICE_DOOR[1]) / 2, OFFICE[3] + T + 0.04, 2.3), size=0.13, rot=(math.pi / 2, 0, math.pi))
    reb.prim("cube", "Office step", mat("planks"), ((OFFICE_DOOR[0] + OFFICE_DOOR[1]) / 2, OFFICE[3] + T + 0.22, 0.08), (1.2, 0.44, 0.16))
    kit.rod("Office stovepipe", mat("rust"), (1.6, 1.4, 2.4), (1.6, 1.4, 3.9), 0.08)
    reb.prim("cone", "Stovepipe hat", mat("rust"), (1.6, 1.4, 4.0), (0.3, 0.3, 0.14), top=0.1)

    # The mess hall along the west: whitewashed boards, its chimney smoking.
    mwin = [(6.0, 7.4), (11.2, 12.6)]
    kit.hut("Mess", MESS, 2.8, white, tin, [("e", MESS_DOOR[0], MESS_DOOR[1], 0.0, 2.1)] + [("e", a, b, 1.0, 1.9) for a, b in mwin], ridge="y", pitch=0.46, thick=T)
    for a, b in mwin:
        kit.hut_window(MESS, "e", a, b, 1.0, 1.9, frame_m, reb.mat_glass("Steamy glass", (0.45, 0.42, 0.36)), thick=T)
    kit.shut_door("Mess door", MESS, "e", MESS_DOOR[0], MESS_DOOR[1], 2.1, mat("white paint"), thick=T)
    reb.prim("cube", "Mess sign", frame_m, (MESS[1] + T + 0.03, (MESS_DOOR[0] + MESS_DOOR[1]) / 2, 2.45), (0.03, 1.4, 0.3))
    kit.text("Mess sign words", "COOKHOUSE", mat("white paint"), (MESS[1] + T + 0.05, (MESS_DOOR[0] + MESS_DOOR[1]) / 2, 2.45), size=0.17, rot=(math.pi / 2, 0, math.pi / 2))
    reb.prim("cube", "Mess step", mat("planks"), (MESS[1] + T + 0.25, (MESS_DOOR[0] + MESS_DOOR[1]) / 2, 0.08), (0.5, 1.3, 0.16))
    reb.prim("cube", "Mess chimney", mat("brick"), (-0.4, 6.0, 3.6), (0.6, 0.6, 2.4))
    mess_glow = reb.point("Range glow in the mess", (0.4, 8.0, 1.6), 25, (1.0, 0.55, 0.25), 0.5)
    reb.point("Lamp in the mess", (0.0, 12.0, 2.2), 12, (1.0, 0.7, 0.4), 0.3)
    reb.prim("cube", "Mess counter inside", mat("dark wood"), (-1.0, 7.0, 0.45), (1.6, 0.6, 0.9))
    kit.table("Mess table inside", mat("pine"), (0.0, 11.4, 0.0), size=(0.9, 2.6, 0.76))
    # Along the mess wall: the cookhouse woodpile, its garbage cans, a washstand.
    wood = []
    for row in range(5):
        for i in range(13):
            y = 10.45 + i * 0.21 + rng.uniform(-0.02, 0.02)
            z = 0.1 + row * 0.19
            x = MESS[1] + T + 0.15 + rng.uniform(-0.04, 0.04)
            wood.append(((x, y, z), (x + 0.5 + rng.uniform(-0.05, 0.05), y + rng.uniform(-0.03, 0.03), z), rng.uniform(0.08, 0.1)))
    pile, _ = logs_mesh("Cookhouse woodpile", wood, bark=mat("bark"))
    reb.wall(reb.prim("cube", "Woodpile footprint", None, (MESS[1] + T + 0.4, 11.8, 0.5), (0.7, 2.9, 1.0))).hide_render = True
    reb.prim("cube", "Woodpile roof", mat("tin"), (MESS[1] + T + 0.45, 11.8, 1.35), (0.9, 3.0, 0.03), rot=(0, 0.25, 0))
    for i, y in enumerate((13.5, 14.1)):
        can = reb.prim("cyl", f"Garbage can {i}", kit.drum_paint(f"Galvanised can {i}", (0.3, 0.3, 0.28)), (MESS[1] + T + 0.4, y, 0.38), (0.5, 0.5, 0.75), segments=18)
        reb.wall(can, "circle")
    reb.prim("cyl", "Can lid", mat("steel"), (MESS[1] + T + 0.9, 14.0, 0.03), (0.52, 0.52, 0.03), rot=(0.1, 0, 0), segments=18)
    kit.papers("Garbage spilled", (MESS[1] + T + 0.9, 13.6, 0.0), spread=0.5, count=5, seed=8)
    kit.table("Washstand", mat("planks"), (MESS[1] + T + 0.35, 8.1, 0.0), size=(0.5, 1.1, 0.8))
    reb.prim("cyl", "Wash basin", reb.mat_plain("Enamel", (0.5, 0.5, 0.46), 0.3), (MESS[1] + T + 0.35, 8.0, 0.86), (0.42, 0.42, 0.1), segments=18)
    reb.prim("cube", "Soap bar", reb.mat_plain("Soap", (0.5, 0.45, 0.3), 0.6), (MESS[1] + T + 0.35, 8.45, 0.82), (0.08, 0.05, 0.03), segments=8)
    reb.wall(reb.prim("cube", "Washstand footprint", None, (MESS[1] + T + 0.35, 8.1, 0.5), (0.55, 1.15, 1.0))).hide_render = True

    # The workshop in the south-east: corrugated tin on a timber frame.
    kit.hut("Workshop", WORK, 3.0, tin_wall, tin, [("n", WORK_DOOR[0], WORK_DOOR[1], 0.0, 2.3), ("n", 17.0, 18.2, 1.1, 1.9), ("w", 15.4, 16.6, 1.1, 1.9)], ridge="x", pitch=0.42, thick=T)
    kit.hut_window(WORK, "n", 17.0, 18.2, 1.1, 1.9, frame_m, glass_m, thick=T, boarded=True)
    kit.hut_window(WORK, "w", 15.4, 16.6, 1.1, 1.9, frame_m, glass_m, thick=T, boarded=True)
    kit.shut_door("Workshop door", WORK, "n", WORK_DOOR[0], WORK_DOOR[1], 2.3, tin_wall, thick=T, handle_m=mat("rust"))
    reb.prim("cube", "Workshop sign", mat("yellow paint"), (16.0, WORK[2] - T - 0.03, 2.65), (1.8, 0.03, 0.3))
    kit.text("Workshop sign words", "NO SMOKING", mat("black"), (16.0, WORK[2] - T - 0.05, 2.65), size=0.13)
    kit.barricade("Boards torn off the shop door", mat("planks"), (WORK_DOOR[0] - 0.3, WORK[2] - 0.45), (WORK_DOOR[0] + 0.8, WORK[2] - 0.9), 0.02, 0.06, count=3, seed=8)
    kit.text("Scrawl on the shop", "DONT LET THEM IN", mat("red paint"), (WORK[0] - T - 0.01, 14.6, 1.6), size=0.14, rot=(math.pi / 2, 0, -math.pi / 2))

    # The sawmill along the east: a tall grey shed, its big sliding doors run shut.
    mx0, mx1, my0, my1 = MILL
    kit.hut("Sawmill", MILL, 6.0, grey, tin, [("w", MILL_DOOR[0], MILL_DOOR[1], 0.0, 3.4), ("w", 3.4, 5.0, 3.8, 4.8), ("w", 10.0, 11.6, 3.8, 4.8)], ridge="x", pitch=0.42, thick=T,
            inside=reb.mat_surface("Sawdust", [(0.0, (0.22, 0.16, 0.09)), (1.0, (0.42, 0.33, 0.2))], scale=8, bump=0.3))
    for a, b in ((3.4, 5.0), (10.0, 11.6)):
        kit.hut_window(MILL, "w", a, b, 3.8, 4.8, frame_m, glass_m, thick=T)
    for i, (a, b) in enumerate(((MILL_DOOR[0], (MILL_DOOR[0] + MILL_DOOR[1]) / 2), ((MILL_DOOR[0] + MILL_DOOR[1]) / 2, MILL_DOOR[1]))):
        kit.shut_door(f"Mill door {i}", MILL, "w", a, b, 3.4, grey, thick=T, handle_m=mat("rust"))
        for z in (0.6, 1.7, 2.8):
            reb.prim("cube", "Mill door brace", frame_m, (mx0 - T - 0.03, (a + b) / 2, z), (0.04, b - a - 0.1, 0.14))
    reb.prim("cube", "Mill door rail", mat("rust"), (mx0 - T - 0.06, (MILL_DOOR[0] + MILL_DOOR[1]) / 2, 3.52), (0.08, 6.0, 0.08))
    # Sawn boards stacked under a lean-to roof by the mill wall, the dust round them.
    lum = []
    for row in range(6):
        for i in range(5):
            y = 9.7 + i * 0.32
            lum.append(reb.prim("cube", "Sawn board", mat("pine"), (mx0 - 0.9, y, 0.12 + row * 0.07), (1.4, 0.28, 0.05), rot=(0, 0, rng.uniform(-0.03, 0.03))))
    for x in (mx0 - 1.4, mx0 - 0.4):
        lum.append(reb.prim("cube", "Bearer", mat("dark wood"), (x, 10.3, 0.05), (0.1, 1.7, 0.1)))
    kit.join("Sawn boards", lum)

    # ---- Fences: the slab fence round the camp where no building stands, the depot's wire.
    rng_f = random.Random(5)
    fv, ff = [], []
    for a, b in (((4.8, 0.5), (5.9, 0.5)), ((17.2, 1.5), (18.5, 2.5)), ((0.6, 3.8), (0.6, 5.0)), ((0.6, 14.1), (0.6, 15.1)),
                 ((6.7, 19.0), (8.3, 19.0)), ((11.9, 19.0), (13.3, 19.0)), ((18.6, 12.3), (18.6, 13.7))):
        fence(fv, ff, a, b, rng_f)
    reb.mesh_object("Camp fence", fv, ff, mat("planks"), smooth=False)
    wire = chain_link()
    for a, b in (((DEPOT[0], DEPOT[2]), (DEPOT_GATE[0], DEPOT[2])), ((DEPOT_GATE[1], DEPOT[2]), (DEPOT[1], DEPOT[2])), ((DEPOT[1], DEPOT[2]), (DEPOT[1], DEPOT[3]))):
        a, b = Vector(a), Vector(b)
        d = b - a
        reb.prim("cube", "Depot wire", wire, ((a.x + b.x) / 2, (a.y + b.y) / 2, 1.0), (d.length if abs(d.x) > 0.1 else 0.02, d.length if abs(d.y) > 0.1 else 0.02, 2.0))
        n = int(d.length / 2.0) + 1
        for i in range(n + 1):
            p = a.lerp(b, i / n)
            kit.rod("Depot post", mat("rust"), (p.x, p.y, 0), (p.x, p.y, 2.1), 0.035, 6)
        kit.rod("Depot top rail", mat("rust"), (a.x, a.y, 2.0), (b.x, b.y, 2.0), 0.02, 6)
    # The depot gate: two leaves shut, chained and padlocked through the middle.
    gmid = (DEPOT_GATE[0] + DEPOT_GATE[1]) / 2
    for a, b in ((DEPOT_GATE[0] + 0.05, gmid - 0.02), (gmid + 0.02, DEPOT_GATE[1] - 0.05)):
        reb.prim("cube", "Depot gate leaf", wire, ((a + b) / 2, DEPOT[2], 1.0), (b - a, 0.02, 1.8))
        for z in (0.12, 1.88):
            kit.rod("Gate frame", mat("rust"), (a, DEPOT[2], z), (b, DEPOT[2], z), 0.02, 6)
        for x in (a, b):
            kit.rod("Gate frame", mat("rust"), (x, DEPOT[2], 0.12), (x, DEPOT[2], 1.88), 0.02, 6)
    for x in DEPOT_GATE:
        reb.mask(reb.wall(kit.rod("Depot gate post", mat("rust"), (x, DEPOT[2], 0), (x, DEPOT[2], 2.2), 0.05, 8), "circle"))
    links_ = []
    for k in range(10):
        a = 2 * math.pi * k / 10
        links_.append(kit.rod("Gate chain", mat("iron"), (gmid + 0.12 * math.cos(a), DEPOT[2] - 0.03, 1.05 + 0.1 * math.sin(a)),
                              (gmid + 0.12 * math.cos(a + 0.63), DEPOT[2] - 0.03, 1.05 + 0.1 * math.sin(a + 0.63)), 0.012, 4))
    kit.join("Gate chain", links_)
    reb.prim("cube", "Padlock", mat("steel"), (gmid, DEPOT[2] - 0.06, 0.92), (0.08, 0.03, 0.1), bevel=0.01)
    reb.prim("cube", "Depot sign", mat("white paint"), (5.5, DEPOT[2] - 0.03, 1.4), (0.9, 0.02, 0.45))
    kit.text("Depot sign words", "FUEL", mat("red paint"), (5.5, DEPOT[2] - 0.045, 1.5), size=0.16)
    kit.text("Depot sign words 2", "NO NAKED FLAME", mat("red paint"), (5.5, DEPOT[2] - 0.045, 1.3), size=0.07)
    # Inside the depot: drums, the tank on its stand.
    for i, (x, y) in enumerate(((0.2, 16.4), (0.85, 16.5), (0.5, 17.1), (5.6, 19.6), (6.0, 18.9))):
        d = kit.drum(f"Depot drum {i}", kit.drum_paint(f"Depot drum paint {i}", (0.3, 0.05, 0.03) if i % 2 else (0.06, 0.1, 0.05)), (x, y, 0.0), rot=rng.uniform(0, 3))
        kit.stencil(d, ["DIESEL", f"No 55-{4100 + 37 * i}"], stencil_m, size=0.11, turn=rng.uniform(-0.5, 0.5))
    reb.prim("cyl", "Depot tank", reb.mat_plain("Tank green", (0.1, 0.14, 0.09), 0.5), (2.6, 19.4, 1.6), (1.4, 1.4, 3.4), rot=(0, math.pi / 2, 0), segments=20)
    for x in (1.4, 3.8):
        reb.prim("cube", "Tank stand", mat("rust"), (x, 19.4, 0.45), (0.15, 1.2, 0.9))
    oil_spill("Oil in the depot", oil, (3.0, 17.4, 0.001), 0.6, 0.4, seed=9)
    room.void((X0, DEPOT[2], DEPOT[1], Y1))

    # ---- The camp gate: two log posts and a beam, the leaves dragged open.
    gate_logs = [((GATE[0], GATE_Y, -0.3), (GATE[0], GATE_Y, 4.6), 0.2), ((GATE[1], GATE_Y, -0.3), (GATE[1], GATE_Y, 4.6), 0.2),
                 ((GATE[0] - 0.5, GATE_Y, 4.35), (GATE[1] + 0.5, GATE_Y, 4.35), 0.18)]
    logs_mesh("Gate logs", gate_logs)
    for x in GATE:
        reb.mask(reb.wall(reb.prim("cyl", "Gate post footprint", None, (x, GATE_Y, 1.0), (0.4, 0.4, 2.0)), "circle")).hide_render = True
    for i, (x, yaw) in enumerate(((GATE[0] - 0.9, 0.5), (GATE[1] + 0.9, -0.6))):
        reb.prim("cube", f"Gate leaf {i}", mat("logs"), (x, GATE_Y + 0.9, 0.9), (1.8, 0.1, 1.5), rot=(0, 0, yaw))
    on_road = kit.dirt_path("Road out", [(10.3, 18.0), (10.4, 24.0), (11.5, 34.0), (14.0, 46.0)], height, width=3.2)
    # Their barricade, pulled down: logs dragged aside.
    kit.rough_log("Barricade log", (7.1, 18.2, 0.12), (8.2, 16.4, 0.14), 0.2, m=mat("bark"), seed=3, stubs=2)
    kit.rough_log("Barricade log 2", (12.1, 18.4, 0.12), (13.0, 15.7, 0.12), 0.18, m=mat("bark"), seed=4, stubs=2)

    # ---- The fire pit: a ring of stones, the ash, a man burned black in it, still smoking.
    sv, sf = [], []
    for i in range(14):
        a = 2 * math.pi * i / 14
        reb.boulder(rng, (PIT[0] + math.cos(a) * 1.05, PIT[1] + math.sin(a) * 1.05, -0.03), rng.uniform(0.14, 0.2), sv, sf)
    reb.mesh_object("Fire ring", sv, sf, kit.dirtied(mat("rock"), 0.9))
    reb.mask(reb.wall(reb.prim("cyl", "Fire pit footprint", None, (PIT[0], PIT[1], 0.3), (2.3, 2.3, 0.6)), "circle")).hide_render = True
    kit.splat("Ash bed", ash, (PIT[0], PIT[1], height(*PIT) + 0.01), 1.0, seed=3, stretch=(1.0, 1.0), lumps=0.3)
    kit.splat("Ash blown out", ash, (PIT[0] + 0.9, PIT[1] + 0.4, height(*PIT) + 0.004), 0.7, seed=4, stretch=(1.4, 0.7), lumps=0.6)
    bh = 0.6
    bdir = Vector((math.cos(bh), math.sin(bh), 0))
    bat = Vector((PIT[0], PIT[1], 0.06)) - bdir * 0.8
    burned = kit.body("Burned in the pit", tuple(bat), heading=bh, pose="back", seed=41)
    burned.data.materials.clear()
    burned.data.materials.append(char)
    burned.scale = (1.0, 1.0, 0.85)
    # The fire took him to the bone at the head and the chest: a skull and ribs show through the char.
    bone_m = kit.dirtied(reb.mat_plain("Scorched bone", (0.42, 0.36, 0.27), 0.7), 0.8, scale=12)
    head = bat + bdir * 1.6 + Vector((0, 0, 0.1))
    reb.prim("sphere", "Scorched skull", bone_m, tuple(head), (0.2, 0.17, 0.19), rot=(0, 0, bh), segments=14)
    reb.prim("sphere", "Jaw", bone_m, tuple(head - bdir * 0.07 + Vector((0, 0, -0.06))), (0.12, 0.1, 0.06), rot=(0, 0, bh), segments=10)
    for side in (-1, 1):
        reb.prim("sphere", "Eye socket", mat("black"), tuple(head + bdir * 0.02 + Vector((0, 0, 0.09)) + Vector((-bdir.y, bdir.x, 0)) * 0.045 * side), (0.05, 0.05, 0.03), segments=8)
    ribs = []
    chest = bat + bdir * 1.2 + Vector((0, 0, 0.2))
    across = Vector((-bdir.y, bdir.x, 0))
    for i in range(5):
        c0 = chest - bdir * (i * 0.06)
        for side in (-1, 1):
            ribs.append(kit.rod("Rib", bone_m, c0 + across * 0.16 * side + Vector((0, 0, -0.06)), c0 + across * 0.03 * side + Vector((0, 0, 0.05)), 0.012, 5))
    kit.join("Ribs through the char", ribs)
    coal = reb.mat_surface("Charcoal", [(0.0, (0.004, 0.004, 0.004)), (0.7, (0.015, 0.013, 0.012)), (1.0, (0.05, 0.045, 0.04))], scale=20, rough=0.85, bump=1.0)
    logs_mesh("Charred logs", [((PIT[0] - 0.75, PIT[1] + 0.55, 0.07), (PIT[0] - 0.2, PIT[1] + 0.8, 0.09), 0.07),
                               ((PIT[0] + 0.6, PIT[1] - 0.6, 0.06), (PIT[0] + 0.85, PIT[1] - 0.1, 0.08), 0.07)], bark=coal, end=coal)
    spr = []
    for i in range(5):
        spr.append(kit.rod("Spring wire", mat("rust"), (PIT[0] - 0.7 + i * 0.25, PIT[1] + 0.55, 0.06 + 0.03 * math.sin(i)), (PIT[0] - 0.65 + i * 0.25, PIT[1] + 0.9, 0.07), 0.007, 4))
    kit.join("Bed springs in the ash", spr)
    ember_m = reb.mat_emit("Embers", (1.0, 0.28, 0.04), 3)
    ev, ef = [], []
    for i in range(16):
        c = (PIT[0] + rng.gauss(0, 0.35), PIT[1] + rng.gauss(0, 0.35), 0.06)
        kit._stain(ev, ef, rng, c, rng.uniform(0.015, 0.035), 0, 0.4, (1, 1), i, points=6, drops=False)
    reb.mesh_object("Ember spots", ev, ef, ember_m, smooth=False)
    embers = reb.point("Ember glow", (PIT[0], PIT[1], 0.3), 12, (1.0, 0.35, 0.08), 0.4)
    smoke_pit = smoke_column("Pit smoke", (PIT[0] + 0.1, PIT[1] - 0.1, 0.35), puffs=5, rise=2.4, drift=(0.5, 0.2), size=(0.1, 0.42), density=2.2)
    smoke_mess = smoke_column("Chimney smoke", (-0.4, 6.0, 4.9), puffs=4, rise=1.8, drift=(0.6, 0.2), size=(0.12, 0.45), density=1.6)

    # ---- The bell on its post by the cookhouse door.
    reb.mask(reb.wall(kit.rod("Bell post", mat("dark wood"), (3.2, 7.3, 0), (3.2, 7.3, 2.9), 0.07), "circle"))
    kit.rod("Bell arm", mat("dark wood"), (3.2, 7.3, 2.75), (3.2, 7.95, 2.75), 0.04)
    pivot = reb.prim("sphere", "Bell pivot", mat("iron"), (3.2, 7.85, 2.7), (0.05, 0.05, 0.05))
    bell = reb.prim("cone", "Bell", reb.mat_metal("Bell bronze", (0.45, 0.3, 0.12), 0.4), (0, 0, -0.2), (0.42, 0.42, 0.38), top=0.45, segments=16)
    clapper = reb.prim("sphere", "Clapper", mat("iron"), (0, 0, -0.4), (0.06, 0.06, 0.06))
    rope = kit.rod("Bell rope", mat("canvas"), (0, 0, -0.4), (0, 0, -1.2), 0.012, 5)
    for p in (bell, clapper, rope):
        p.parent = pivot

    # ---- The laundry on the line, the bunkhouse's: shirts, long johns, a towel, socks.
    la, lb = Vector((5.6, 2.6, 0)), Vector((9.8, 3.4, 0))
    for p in (la, lb):
        reb.mask(reb.wall(kit.rod("Line pole", mat("dark wood"), (p.x, p.y, 0), (p.x, p.y, 2.15), 0.04), "circle"))
        kit.rod("Line pole brace", mat("dark wood"), (p.x, p.y, 1.9), (p.x, p.y - 0.25, 2.15), 0.02)
    sag_line = []
    for k in range(10):
        t0, t1 = k / 10, (k + 1) / 10
        p, q = la.lerp(lb, t0), la.lerp(lb, t1)
        sag_line.append(kit.rod("Washing line", mat("canvas"), (p.x, p.y, 2.05 - 0.12 * math.sin(math.pi * t0)), (q.x, q.y, 2.05 - 0.12 * math.sin(math.pi * t1)), 0.006, 4))
    kit.join("Washing line", sag_line)
    yaw = math.atan2(lb.y - la.y, lb.x - la.x)
    pegs = []
    washing = ((0.14, mat("flannel"), "shirt", 0.95, 0.75), (0.33, reb.mat_surface("Long johns", [(0.0, (0.36, 0.32, 0.25)), (1.0, (0.5, 0.46, 0.37))], scale=20, bump=0.2), "johns", 0.55, 1.0),
               (0.5, reb.mat_surface("Grey towel", [(0.0, (0.2, 0.2, 0.18)), (1.0, (0.3, 0.29, 0.26))], scale=30, bump=0.4), "towel", 0.5, 0.75),
               (0.67, reb.mat_stripes("Blue flannel", [(0.05, 0.08, 0.2), (0.02, 0.03, 0.05)], across=20), "shirt", 0.9, 0.72),
               (0.83, mat("canvas"), "towel", 0.14, 0.32), (0.88, mat("canvas"), "towel", 0.14, 0.3))
    for i, (t, m, kind, w, hgt) in enumerate(washing):
        p = la.lerp(lb, t)
        sag = 0.12 * math.sin(math.pi * t)
        peg = reb.prim("cube", f"Peg {i}", mat("planks"), (p.x, p.y, 2.04 - sag), (0.02, 0.03, 0.07))
        cl = garment(f"Washing {i}", m, kind, w, hgt, seed=i)
        cl.parent = peg
        peg.rotation_euler = (0, 0, yaw)
        pegs.append(peg)

    # ---- The log deck on the north-east, and the man who died against it.
    logs = []
    for row, (n, z) in enumerate(((6, 0.3), (5, 0.82), (4, 1.34), (2, 1.86))):
        for i in range(n):
            y = 2.75 + (i + (6 - n) / 2) * 0.52 + rng.uniform(-0.03, 0.03)
            x0 = 12.6 + rng.uniform(-0.3, 0.3)
            logs.append(((x0, y, z), (x0 + 4.8 + rng.uniform(-0.3, 0.3), y + rng.uniform(-0.1, 0.1), z + rng.uniform(-0.03, 0.03)), rng.uniform(0.22, 0.28)))
    deck, deck_ends = logs_mesh("Log deck", logs)
    reb.mask(reb.wall(deck))
    for x in (12.4, 17.6):
        kit.rod("Deck stake", mat("dark wood"), (x, 5.95, 0), (x, 5.95, 1.5), 0.06)
    # He sat down against the logs, his gun across his legs, and fired till it was empty.
    kit.body("Dead against the logs", (14.6, 5.72, 0.0), heading=math.pi / 2, pose="slumped", top=mat("flannel"), legs=mat("denim"), seed=21)
    kit.splat("Soaked into his shirt", mat("blood"), (14.6, 5.62, 0.75), 0.16, rot=(math.pi / 2 - 0.3, 0, 0), seed=23, stretch=(1.0, 1.4))
    soaked = reb.mat_surface("Soaked blood", [(0.0, (0.02, 0.006, 0.004)), (0.5, (0.045, 0.012, 0.007)), (0.8, (0.07, 0.025, 0.014)), (1.0, (0.05, 0.03, 0.02))], scale=25, detail=8, rough=0.92, bump=0.1)
    kit.lay_on_ground(kit.splat("Where he bled", soaked, (14.55, 6.2, 0), 0.36, seed=21, stretch=(1.3, 1.0), lumps=0.7), height, 0.01)
    kit.splat("Spray on the logs", mat("old blood"), (14.6, 4.62, 1.0), 0.3, rot=(math.pi / 2, 0, 0), seed=22, stretch=(1.4, 0.8), lumps=0.6)
    gun = [kit.rod("Barrel", mat("iron"), (-0.45, 0, 0), (0.25, 0, 0), 0.016, 8),
           kit.rod("Pump", mat("dark wood"), (-0.05, 0, -0.025), (0.12, 0, -0.025), 0.025, 8),
           reb.prim("cube", "Receiver", mat("iron"), (0.33, 0, -0.01), (0.2, 0.04, 0.07)),
           reb.prim("cube", "Stock", mat("dark wood"), (0.6, 0, -0.04), (0.38, 0.045, 0.1), rot=(0, 0.12, 0))]
    shotgun = kit.join("His shotgun", gun, origin=(0, 0, 0))
    shotgun.location = (14.7, 6.3, 0.32)
    shotgun.rotation_euler = (0.1, 0.05, 0.3)
    hat = reb.prim("sphere", "His hard hat", hard_hat, (15.5, 6.2, 0.1), (0.3, 0.26, 0.18), rot=(0.4, 0.2, 0), segments=14)
    reb.prim("cyl", "Hard hat brim", hard_hat, (15.5, 6.22, 0.05), (0.36, 0.32, 0.015), rot=(0.4, 0.2, 0), segments=16)
    for i, x in enumerate((13.9, 14.05)):
        reb.prim("cube", f"Work glove {i}", reb.mat_plain("Leather glove", (0.3, 0.2, 0.1), 0.8), (x, 6.25 + 0.1 * i, 0.02), (0.1, 0.22, 0.04), rot=(0, 0, 0.5 + i), bevel=0.02)
    reb.prim("cyl", "Thermos", reb.mat_plain("Thermos green", (0.08, 0.14, 0.08), 0.4), (13.7, 5.9, 0.16), (0.1, 0.1, 0.32), segments=12)
    reb.prim("cube", "Lunch pail", mat("rust"), (13.6, 6.45, 0.09), (0.3, 0.18, 0.18), rot=(0, 0, 0.2), bevel=0.02)
    shells = []
    for i in range(9):
        shells.append(reb.prim("cyl", "Shell", mat("red paint"), (14.6 + rng.gauss(0, 0.6), 6.8 + rng.gauss(0, 0.4), 0.012), (0.024, 0.024, 0.07), rot=(math.pi / 2, 0, rng.uniform(0, 3)), segments=6))
    kit.join("Spent shells", shells)
    for i, (x, z) in enumerate(((13.4, 1.1), (14.1, 0.8), (15.8, 1.3))):
        kit.splat(f"Shot in the logs {i}", mat("black"), (x, 2.48, z), 0.03, rot=(math.pi / 2, 0, 0), seed=30 + i, lumps=0.6)

    # Between the deck and the bunkhouse: what a logger drops when he runs. A peavey, a coil of
    # choker cable, a tipped water bucket.
    kit.rod("Peavey handle", reb.mat_wood("Peavey ash", (0.38, 0.28, 0.16)), (12.0, 6.4, 0.04), (13.4, 7.3, 0.05), 0.025)
    reb.prim("cube", "Peavey spike", mat("iron"), (13.5, 7.36, 0.05), (0.18, 0.05, 0.05), rot=(0, 0, 0.57))
    kit.rod("Peavey hook", mat("iron"), (13.25, 7.2, 0.06), (13.3, 6.95, 0.04), 0.012, 6)
    coil = []
    for turn in range(4):
        r = 0.34 + 0.025 * turn
        coil.append([(12.6 + r * math.cos(2 * math.pi * k / 18), 4.9 + r * 0.8 * math.sin(2 * math.pi * k / 18), 0.03 + 0.02 * turn) for k in range(19)])
    for i, pts in enumerate(coil):
        kit.tube(f"Choker cable {i}", mat("iron"), pts, 0.014, segments=6)
    reb.prim("cyl", "Water bucket", kit.drum_paint("Galvanised bucket", (0.22, 0.22, 0.21)), (11.7, 7.6, 0.16), (0.32, 0.32, 0.36), rot=(math.pi / 2, 0, 0.9), segments=14)
    kit.splat("Where the bucket ran out", mat("mud"), (11.4, 7.9, height(11.4, 7.9) + 0.003), 0.3, seed=36, stretch=(1.4, 0.7), lumps=0.7)
    # ---- The skidder: blade down, its choker chains on three logs.
    sx0, sx1, sy = 5.9, 10.0, 13.0
    hooks = []
    skidder = kit.skidder("Skidder", ((sx0 + sx1) / 2, sy, height((sx0 + sx1) / 2, sy)), paint=yellow, chokers=hooks)
    reb.mask(reb.wall(skidder))
    oil_spill("Oil under the skidder", oil, (sx1 - 1.2, sy + 0.2, 0.002), 0.4, 2.6, seed=18)
    choked = [((sx0 - 4.0, sy - 0.35 + i * 0.35, 0.18), (sx0 - 0.4, sy - 0.2 + i * 0.2, 0.26), 0.2 + 0.03 * i) for i in range(3)]
    for i, (a, b, r) in enumerate(choked):
        kit.rough_log(f"Choked log {i}", a, b, r, m=mat("bark"), seed=20 + i, stubs=3)
    chain = []
    for i in range(3):
        a = Vector(choked[i][1]) + Vector((-0.3, 0, 0.1))
        b = hooks[0]
        for k in range(6):
            p, q = a.lerp(b, k / 6), a.lerp(b, (k + 1) / 6)
            chain.append(kit.rod("Choker", mat("iron"), (p.x, p.y, p.z - 0.25 * math.sin(math.pi * k / 6)), (q.x, q.y, q.z - 0.25 * math.sin(math.pi * (k + 1) / 6)), 0.015, 4))
    kit.join("Choker chains", chain)
    room_wall_logs = reb.prim("cube", "Choked logs footprint", None, (sx0 - 2.2, sy, 0.3), (3.8, 1.2, 0.6))
    room_wall_logs.hide_render = True
    reb.mask(room_wall_logs)

    # ---- The sawhorses by the gate: a log half cut through, the chainsaw left on it.
    hx, hy = 11.8, 15.4
    horse = []
    for dx in (-0.8, 0.8):
        for s in (-1, 1):
            horse.append(kit.rod("Sawhorse leg", mat("planks"), (hx + dx, hy, 0.75), (hx + dx + s * 0.05, hy + s * 0.35, 0.0), 0.035, 6))
        horse.append(kit.rod("Sawhorse X", mat("planks"), (hx + dx, hy - 0.3, 0.1), (hx + dx, hy + 0.3, 0.9), 0.04, 6))
        horse.append(kit.rod("Sawhorse X", mat("planks"), (hx + dx, hy + 0.3, 0.1), (hx + dx, hy - 0.3, 0.9), 0.04, 6))
    kit.join("Sawhorses", horse)
    cut, _ = logs_mesh("Log on the horses", [((hx - 1.4, hy + 0.02, 0.98), (hx + 0.05, hy - 0.02, 0.98), 0.2), ((hx + 0.1, hy, 0.98), (hx + 1.5, hy + 0.06, 0.97), 0.19)])
    reb.wall(reb.prim("cube", "Sawhorses footprint", None, (hx, hy, 0.5), (3.0, 0.8, 1.0))).hide_render = True
    saw = [reb.prim("cube", "Saw body", reb.mat_plain("Saw orange", (0.45, 0.12, 0.02), 0.5), (0, 0, 0), (0.42, 0.24, 0.26), bevel=0.04),
           reb.prim("cube", "Saw bar", mat("steel"), (0.0, 0.45, -0.05), (0.06, 0.7, 0.03)),
           kit.rod("Saw handle", mat("black"), (-0.1, -0.08, 0.14), (0.1, -0.08, 0.14), 0.02, 6)]
    chainsaw = kit.join("Chainsaw", saw, origin=(0, 0, 0))
    chainsaw.location = (hx + 0.05, hy - 0.45, 1.25)
    chainsaw.rotation_euler = (0.1, 0, 0.0)
    reb.prim("cube", "Gas can", reb.mat_plain("Can red", (0.3, 0.03, 0.02), 0.5), (hx + 1.4, hy - 0.6, 0.17), (0.24, 0.14, 0.34), rot=(0, 0, 0.6), bevel=0.02)
    kit.splat("Sawdust under the cut", reb.mat_surface("Fresh sawdust", [(0.0, (0.1, 0.075, 0.045)), (0.6, (0.17, 0.13, 0.08)), (1.0, (0.24, 0.18, 0.11))], scale=12, bump=0.3), (hx, hy, height(hx, hy) + 0.004), 0.32, seed=33, stretch=(1.2, 0.9), lumps=0.8)

    # ---- Odds and ends: a wheelbarrow over, a chopping block, drums.
    wb = [reb.prim("cube", "Barrow tray", mat("rust"), (0, 0, 0.35), (0.9, 0.6, 0.3), bevel=0.02),
          reb.prim("cyl", "Barrow wheel", mat("rubber"), (0.55, 0, 0.18), (0.36, 0.36, 0.08), rot=(math.pi / 2, 0, 0)),
          kit.rod("Barrow handle", mat("planks"), (-0.2, -0.22, 0.4), (-0.9, -0.25, 0.5), 0.02),
          kit.rod("Barrow handle", mat("planks"), (-0.2, 0.22, 0.4), (-0.9, 0.25, 0.5), 0.02)]
    barrow = kit.join("Wheelbarrow", wb)
    barrow.location = (5.4, 6.8, 0.42)
    barrow.rotation_euler = (math.pi * 0.9, 0, 2.4)
    reb.wall(kit.box("Chopping block", mat("logs"), (4.6, 5.4, 0.0), (0.55, 0.55, 0.5)), "circle")
    kit.rod("Axe in the block, its handle", reb.mat_wood("Axe handle 2", (0.4, 0.28, 0.14)), (4.6, 5.4, 0.55), (4.95, 5.6, 1.15), 0.02)
    for i, (x, y, a) in enumerate(((4.2, 5.9, 0.6), (4.9, 6.0, 2.1), (4.1, 5.1, 1.2), (5.1, 5.2, 2.9))):
        reb.prim("cube", f"Split wood {i}", mat("logs"), (x, y, 0.06), (0.45, 0.11, 0.11), rot=(0, 0, a))
    for i, (x, y) in enumerate(((16.9, 13.1), (17.6, 12.6))):
        d = kit.drum(f"Yard drum {i}", kit.drum_paint(f"Yard drum paint {i}", (0.06, 0.1, 0.05) if i else (0.3, 0.05, 0.03)), (x, y, 0.0), tipped=i == 1, rot=1.2)
        if i == 0:
            kit.stencil(d, ["DIESEL", "No 55-4318"], stencil_m, size=0.11, turn=2.4)
    oil_spill("Diesel from the tipped drum", oil, (17.1, 12.0, 0.002), 0.35, 3.6, seed=19)

    # ---- The mountain round the camp: dense spruce, grass at the fence feet and the walls.
    def keep_out(x, y):
        if -4.5 < x < 33 and -4.2 < y < 22.0:
            return True
        if any((x - e[0]) ** 2 + (y - e[1]) ** 2 < 36 for e, _, _ in cams):
            return True
        return on_road(x, y, 1.5)
    kit.forest(rng, height, keep_out, (-34, -34, 54, 58), count=320, spacing=1.7, tall=(14, 24), ferns=90, needles=1500)
    kit.forest(rng, height, keep_out, (-12, -14, 42, 32), count=110, spacing=1.6, tall=(13, 21), ferns=40, needles=600)
    kit.far_spruces(rng, height, keep_out=lambda x, y: -34 < x < 54 and -34 < y < 58, count=900, area=(-80, -80, 100, 100))

    def in_yard(x, y):
        """Where the yard is trodden bare: the floor and the ground round the buildings' doors."""
        return X0 + 0.4 < x < X1 - 0.3 and Y0 + 1.2 < y < Y1 - 0.6 and not (x < 2.9 and 6 < y < 15) or on_road(x, y)
    grass = kit.grass_ground(rng, (-6, -6, 26, 26), height, keep_out=lambda x, y: in_yard(x, y) or (DEPOT[0] < x < DEPOT[1] and DEPOT[2] < y < DEPOT[3]), per_m2=10, m=mat("dead grass"))
    kit.rocks("Rocks", rng, [(-4.0, -1.0, 1.1), (20.0, 15.0, 0.9), (-5.0, 15.0, 0.8), (14.5, 21.5, 0.9), (22.0, 0.5, 0.7)], height)

    # ---- Light: noon under cloud, grey and soft, mist in the trees; the RE0 sky and ranges.
    sun = kit.time_light("noon", sun_heading=200, sun_energy=3.2, mist=((9.0, 9.0, 6.0), (110, 110, 14), 0.009), sky=((0.6, 0.62, 0.63), (0.4, 0.42, 0.45), 1.15))
    sun.data.angle = math.radians(25)
    sun.rotation_euler[0] = math.radians(35)
    kit.overcast_sky(glow=(0.6, -1.0))
    kit.backdrop((CENTRE[0], CENTRE[1], 3.5), spread=360, below=-40.0, near=60.0, forest_to=1800.0, trees=110000,
                 keep_out=lambda x, y: math.hypot(x - CENTRE[0], y - CENTRE[1]) < 56, shape=far_land, mist=30.0, rng=random.Random(12))

    anim = kit.Anim(16)
    anim.custom(smoke_pit)
    anim.custom(smoke_mess)
    anim.flicker(embers, ember_m, depth=0.3, dropouts=0)
    anim.flicker(mess_glow, None, depth=0.1, dropouts=0)
    anim.swing(pivot, axis=1, degrees=2)

    def laundry(k):
        for i, peg in enumerate(pegs):
            peg.rotation_euler = (math.radians(4) * math.sin(anim.phase(k) + i * 0.7), 0, yaw)
    anim.custom(laundry)

    # ---- What the game needs.
    room.door("camp-gate", (GATE[0] + 0.2, Y1 - 0.6, GATE[1] - 0.2, Y1), arrive=(10.1, 16.9), face=(0, -1))
    room.door("bunkhouse", (BUNK_DOOR[0], BUNK[3] + T, BUNK_DOOR[1], BUNK[3] + T + 0.7), arrive=(11.45, 3.4), face=(0, 1), walk=False)
    room.door("office", (OFFICE_DOOR[0], OFFICE[3] + T, OFFICE_DOOR[1], OFFICE[3] + T + 0.7), arrive=(2.95, 4.7), face=(0, 1), walk=False)
    room.door("mess", (MESS[1] + T, MESS_DOOR[0], MESS[1] + T + 0.7, MESS_DOOR[1]), arrive=(3.7, 9.45), face=(1, 0), walk=False)
    room.door("depot", (DEPOT_GATE[0], DEPOT[2] - 0.6, DEPOT_GATE[1], DEPOT[2]), arrive=(3.5, 13.7), face=(0, -1), touch=False)
    room.door("workshop", (WORK_DOOR[0], WORK[2] - T - 0.7, WORK_DOOR[1], WORK[2] - T), arrive=(15.2, 12.2), face=(0, -1), walk=False)
    room.door("sawmill", (MILL_X - 0.7, MILL_DOOR[0], X1, MILL_DOOR[1]), arrive=(16.9, 7.5), face=(-1, 0), walk=False)
    room.check((10.6, 14.6, 13.4, 16.2), "A log on the sawhorses, cut halfway through.\nThe chainsaw's still sitting on it.")
    room.check((7.6, 7.0, 10.4, 9.6), "Someone was burned here. What's left is curled up black in the ash.\nIt's still smoking.")
    room.check((10.4, 1.7, 11.0, 2.6), "A fire axe, buried in the door. Someone was holding it shut from inside.")
    room.check((13.6, 5.6, 15.8, 7.2), "He sat down against the logs with a shotgun and fired until it was empty.\nShells everywhere.")
    room.check((2.2, 10.2, 3.2, 13.4), "The cookhouse woodpile. Split and stacked, enough for weeks.")
    room.check((2.6, 6.8, 3.8, 8.0), "The cookhouse bell. The rope's been cut short.")
    room.check((10.4, 11.8, 11.2, 14.2), "The skidder. Its blade is down in the mud, the chokers still on the logs.\nThe key's gone.")
    room.check((5.6, 2.6, 9.8, 4.0), "Laundry on the line. Nobody's coming for it.")
    room.check((15.8, 11.6, 18.0, 13.6), "Diesel, leaking from a drum into the mud.")
    room.check((DEPOT_GATE[0] - 0.4, DEPOT[2] - 1.2, DEPOT_GATE[1] + 0.4, DEPOT[2] - 0.6), "The fuel depot. The gate's chained shut, a padlock on it.")
    # Many scenes share the render machine's GPU: keep each frame cheap.
    scene = bpy.context.scene
    scene.render.use_persistent_data = True
    scene.cycles.volume_step_rate = 4.0
    scene.cycles.volume_max_steps = 64
    room.export(anim, samples=160)


build()
