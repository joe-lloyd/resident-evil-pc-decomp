"""Logging Camp 4's yard, noon under cloud: the hub of the camp.

What it tells: about twenty men worked here. They got sick one by one. The
foreman painted a board, CAMP 4 - QUARANTINE - BY ORDER, and they shut the
gate. They burned the sick men's bedding in the fire pit, then the sick men
themselves: the springs of a mattress and charred bones lie in the ash, and
one log still smokes. Then the well turned on the sick, and the sick on the
well. A fire axe is buried in the bunkhouse door, which someone held shut
from inside. A logger lies face down in the mud by the skidder with a peavey
in his back and his hard hat in a puddle; another sits dead against the log
deck, shotgun shells round him. Two more were laid out under canvas by the
mess wall, early on, when they still had time for that. The laundry is still
on the line. The skidder sits where it stopped with its blade down, its
choker chains still on three logs. Smoke from the mess chimney: the range
inside is still warm. A player should work out that the camp sealed itself
in, and that the sickness came from inside the fence.

Metres: the yard floor is x 1.0-18.4, y 1.0-18.6.
- North: the bunkhouse, x 6.0-17.0, y -3.4-1.6, brown boards, five windows
  in its south wall; its door at x 11.0-11.9 (the bunkhouse inside is x
  1-12, y 1-6, door at x 6.0-6.9 in its south wall).
- North-west: the foreman's office, x 1.0-4.6, y 0.6-3.6, green boards; its
  door in the south wall at x 2.5-3.4, windows south at x 3.75-4.35 and east
  at y 1.2-2.3 (inside: x 1-4.6, y 1-4, the same shifted 0.4 south).
- West: the mess hall, x -3.4-2.0, y 5.0-14.0, whitewashed boards; its door
  in the east wall at y 9.0-9.9, windows at y 6.0-7.4 and 11.2-12.6 (inside:
  x 1-6.4, y 1-10, shifted 4 south and 4.4 east), its chimney smoking.
- South-west: the fuel depot's fenced compound, x -2.0-6.6, y 15.2-21; its
  gate in the north fence at x 2.6-4.4 (the depot is that compound moved 3
  east and 14.2 north).
- South: the camp gate between log posts at x 8.4 and 11.8 on y 18.9.
- South-east: the workshop, tin, x 13.4-19.2, y 13.8-19.4; its door in the
  north wall at x 14.6-15.8, a window north at x 17.0-18.2 and west at y
  15.4-16.6 (inside: x 1-6.8, y 1-6.6, door at x 2.2-3.4).
- East: the sawmill shed, west wall at x 18.5 from y 2.6 to 12.2, its big
  doors open at y 6.0-9.0.
- In the yard: the fire pit at (9.0, 8.3), the bell post at (3.2, 7.3), the
  log deck at x 12.6-17.4, y 2.4-4.6, the skidder at x 5.6-10.4, y 11.8-14.2,
  the laundry line from (5.6, 2.6) to (9.8, 3.4), the board at (7.4, 16.9).

Moving: smoke rising off the fire pit and the mess chimney, the embers'
glow, the bell swinging, the laundry stirring, the bunkhouse bulb failing
behind its door, a crow on the mess roof.
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
        ob = reb.prim("sphere", f"{name} puff {i}", m, base, (1, 1, 1.2), segments=10)
        parts.append((ob, vol, i / puffs))

    def f(k, frames=16):
        for ob, vol, off in parts:
            t = (k / frames + off) % 1.0
            ob.location = (base[0] + drift[0] * t, base[1] + drift[1] * t, base[2] + rise * t)
            s = size[0] + (size[1] - size[0]) * t
            ob.scale = (s, s, s)
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
                rr = r * (1 + 0.06 * math.sin(ang * 3 + a.x))
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


def window(rect, side, a0, a1, z0, z1, frame_m, glass_m, boarded=False, broken=False, rng=None, board_m=None):
    """A window in a hut's wall (as kit.walls cuts it): glass, a frame, a sill."""
    x0, x1, y0, y1 = rect
    mid = (a0 + a1) / 2
    wdt, hgt = a1 - a0, z1 - z0
    zc = (z0 + z1) / 2
    if side in "ns":
        y = y0 - T / 2 if side == "n" else y1 + T / 2
        out = -1 if side == "n" else 1
        if not broken:
            reb.prim("cube", "Window glass", glass_m, (mid, y, zc), (wdt, 0.01, hgt))
        else:
            reb.prim("cube", "Window glass", glass_m, (mid - wdt * 0.25, y, z0 + hgt * 0.3), (wdt * 0.5, 0.01, hgt * 0.6), rot=(0, 0.3, 0))
        for zz in (z0, z1):
            reb.prim("cube", "Window frame", frame_m, (mid, y + out * 0.05, zz), (wdt + 0.12, 0.05, 0.06))
        for aa in (a0, a1, mid):
            reb.prim("cube", "Window frame", frame_m, (aa, y + out * 0.05, zc), (0.05 if aa == mid else 0.06, 0.05, hgt))
        if boarded:
            kit.barricade("Boards over the window", board_m or mat("planks"), (a0 - 0.1, y + out * 0.09), (a1 + 0.1, y + out * 0.09), z0 + 0.1, z1 - 0.1, count=3, seed=int(mid * 10))
    else:
        x = x0 - T / 2 if side == "w" else x1 + T / 2
        out = -1 if side == "w" else 1
        if not broken:
            reb.prim("cube", "Window glass", glass_m, (x, mid, zc), (0.01, wdt, hgt))
        else:
            reb.prim("cube", "Window glass", glass_m, (x, mid - wdt * 0.25, z0 + hgt * 0.3), (0.01, wdt * 0.5, hgt * 0.6), rot=(0.3, 0, 0))
        for zz in (z0, z1):
            reb.prim("cube", "Window frame", frame_m, (x + out * 0.05, mid, zz), (0.05, wdt + 0.12, 0.06))
        for aa in (a0, a1, mid):
            reb.prim("cube", "Window frame", frame_m, (x + out * 0.05, aa, zc), (0.05, 0.05 if aa == mid else 0.06, hgt))
        if boarded:
            kit.barricade("Boards over the window", board_m or mat("planks"), (x + out * 0.09, a0 - 0.1), (x + out * 0.09, a1 + 0.1), z0 + 0.1, z1 - 0.1, count=3, seed=int(mid * 10))


def hut(name, rect, h, wall_m, roof_m, openings, ridge="x", pitch=0.3, inside_m=None, eaves=0.35):
    """A camp building: board walls with their openings, a pitched tin roof,
    a dim floor and ceiling inside so doors and windows show a room, and a
    hidden footprint that blocks her."""
    x0, x1, y0, y1 = rect
    kit.walls(x0, y0, x1, y1, h, wall_m, openings, thick=T, name=f"{name} wall",
              floor=inside_m or reb.mat_plain(f"{name} floor", (0.05, 0.04, 0.03), 0.9),
              ceiling=reb.mat_plain(f"{name} ceiling", (0.04, 0.03, 0.025), 0.9))
    # A sill board round the foot, and corner posts.
    for side in "nswe":
        if side in "ns":
            y = y0 - T - 0.02 if side == "n" else y1 + T + 0.02
            reb.prim("cube", f"{name} sill", mat("dark wood"), ((x0 + x1) / 2, y, 0.1), (x1 - x0 + 2 * T + 0.08, 0.06, 0.2))
        else:
            x = x0 - T - 0.02 if side == "w" else x1 + T + 0.02
            reb.prim("cube", f"{name} sill", mat("dark wood"), (x, (y0 + y1) / 2, 0.1), (0.06, y1 - y0 + 2 * T + 0.08, 0.2))
    for cx in (x0 - T, x1 + T):
        for cy in (y0 - T, y1 + T):
            reb.prim("cube", f"{name} corner", mat("dark wood"), (cx, cy, h / 2), (0.1, 0.1, h))
    # The roof: two tin slopes over the ridge and gable ends in the walls' boards.
    if ridge == "x":
        span = (y1 - y0) + 2 * T + 2 * eaves
        run = span / 2
        rise = run * math.tan(pitch)
        slope = run / math.cos(pitch)
        yc = (y0 + y1) / 2
        for s in (-1, 1):
            reb.prim("cube", f"{name} roof", roof_m, ((x0 + x1) / 2, yc + s * run / 2, h + rise / 2 + 0.04), (x1 - x0 + 2 * T + 2 * eaves, slope, 0.05), rot=(s * pitch, 0, 0))
        gv, gf = [], []
        for x in (x0 - T / 2, x1 + T / 2):
            k = len(gv)
            gv += [(x, y0 - T, h), (x, y1 + T, h), (x, yc, h + rise * ((y1 - y0 + 2 * T) / span))]
            gf.append((k, k + 1, k + 2))
        reb.mesh_object(f"{name} gables", gv, gf, wall_m, smooth=False)
        reb.prim("cube", f"{name} ridge cap", roof_m, ((x0 + x1) / 2, yc, h + rise + 0.06), (x1 - x0 + 2 * T + 2 * eaves, 0.25, 0.04))
    else:
        span = (x1 - x0) + 2 * T + 2 * eaves
        run = span / 2
        rise = run * math.tan(pitch)
        slope = run / math.cos(pitch)
        xc = (x0 + x1) / 2
        for s in (-1, 1):
            reb.prim("cube", f"{name} roof", roof_m, (xc + s * run / 2, (y0 + y1) / 2, h + rise / 2 + 0.04), (slope, y1 - y0 + 2 * T + 2 * eaves, 0.05), rot=(0, -s * pitch, 0))
        gv, gf = [], []
        for y in (y0 - T / 2, y1 + T / 2):
            k = len(gv)
            gv += [(x0 - T, y, h), (x1 + T, y, h), (xc, y, h + rise * ((x1 - x0 + 2 * T) / span))]
            gf.append((k, k + 1, k + 2))
        reb.mesh_object(f"{name} gables", gv, gf, wall_m, smooth=False)
        reb.prim("cube", f"{name} ridge cap", roof_m, (xc, (y0 + y1) / 2, h + rise + 0.06), (0.25, y1 - y0 + 2 * T + 2 * eaves, 0.04))
    foot = reb.prim("cube", f"{name} footprint", None, ((x0 + x1) / 2, (y0 + y1) / 2, 0.5), (x1 - x0 + 2 * T, y1 - y0 + 2 * T, 1.0))
    foot.hide_render = True
    reb.wall(foot)


# ---------------------------------------------------------------------------
# The yard
# ---------------------------------------------------------------------------


def build():
    rng = random.Random(404)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("earth")  # mud, worn paths, puddles too small to wade
    cams = [
        ((10.4, 20.6, 3.9), (10.2, 11.5, 0.2), "from the gate: the body in the mud, the skidder, the fire pit, the bunkhouse beyond"),
        ((5.2, 6.4, 3.3), (15.0, 14.6, 0.3), "from by the office: the fire pit, the skidder's blade, the workshop door"),
        ((12.0, 12.6, 3.6), (16.6, 4.4, 0.4), "from the ruts: the sawmill's open doors, the log deck, the dead man against it"),
        ((5.0, 8.4, 3.4), (12.5, 2.0, 0.6), "from the bell post: the laundry, the bunkhouse door with the axe in it"),
        ((9.4, 10.6, 3.4), (2.4, 3.6, 0.5), "from the fire pit: the office door in the corner, the bell post, the laundry"),
        ((8.4, 10.0, 3.3), (2.0, 9.8, 0.6), "from the ruts: the mess door, the bell, the two under canvas"),
        ((12.4, 17.8, 3.4), (3.5, 13.6, 0.3), "from inside the gate: the depot gate, the choked logs, the board"),
        ((11.0, 9.6, 3.6), (17.0, 13.6, 0.4), "from the fire pit: the workshop door, the leaking drums, the mill doors"),
    ]
    for eye, look, note in cams:
        room.camera(eye, look, 200, note)

    # ---- Materials.
    mud = kit.dirtied(mat("mud"), 0.6, scale=0.8)
    wet_mud = reb.mat_plain("Wet mud", (0.03, 0.022, 0.014), 0.25)
    puddle = reb.mat_plain("Puddle", (0.06, 0.055, 0.05), 0.18)
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
    char = reb.mat_surface("Charred wood", [(0.0, (0.01, 0.01, 0.01)), (1.0, (0.05, 0.04, 0.035))], scale=12, rough=0.7, bump=0.8)
    ply = reb.mat_surface("Plywood", [(0.0, (0.28, 0.22, 0.14)), (1.0, (0.4, 0.33, 0.22))], scale=5, bump=0.1)
    hard_hat = reb.mat_plain("Hard hat", (0.5, 0.3, 0.02), 0.4)

    # ---- Ground: mud, ruts, puddles, the mountain round the camp.
    reb.terrain("Ground", mud, (-30, 50), (-30, 55), height, step=0.7)
    for i, path in enumerate((
        [(10.0, 22.0), (10.0, 17.0), (9.8, 15.0), (10.4, 13.4)],
        [(10.9, 22.0), (10.9, 17.0), (11.0, 15.2), (11.4, 13.6)],
        [(10.4, 11.8), (12.0, 10.0), (15.0, 8.2), (18.5, 7.6)],
        [(10.8, 12.6), (12.5, 10.8), (15.2, 9.0), (18.5, 8.4)],
    )):
        kit.path_strip(f"Rut {i}", wet_mud, path, height, width=0.18, wobble=0.4, lift=0.006)
    kit.path_strip("Worn path to the bunkhouse", kit.dirtied(mat("dirt"), 0.7), [(10.4, 16.0), (10.0, 11.0), (11.3, 6.0), (11.45, 1.9)], height, width=0.5, lift=0.004)
    kit.path_strip("Worn path to the mess", kit.dirtied(mat("dirt"), 0.7), [(9.6, 10.6), (6.0, 10.0), (2.2, 9.45)], height, width=0.45, lift=0.004)
    for i, (x, y, r, s) in enumerate(((12.2, 12.0, 0.7, (1.6, 0.8)), (6.0, 8.4, 0.5, (1.2, 0.9)), (14.2, 6.8, 0.6, (1.8, 0.7)), (4.6, 15.6, 0.45, (1.3, 0.8)), (11.6, 16.4, 0.55, (1.5, 0.8)), (16.4, 11.8, 0.4, (1.2, 1.0)), (7.2, 5.4, 0.4, (1.4, 0.7)))):
        kit.splat(f"Puddle {i}", puddle, (x, y, 0.0), r, rot=(0, 0, rng.uniform(0, 3)), seed=80 + i, stretch=s, lumps=0.45)
    for i in range(26):
        t = i / 25
        x = 10.3 + rng.uniform(-0.2, 0.2) + (0.3 if i % 2 else -0.3) * 0.5
        y = 18.0 - t * 15.0
        kit.splat(f"Bootprint {i}", wet_mud, (x + (0.4 if i > 18 else 0) * (t - 0.7), y, 0.0), 0.07, seed=200 + i, stretch=(0.6, 1.4), lumps=0.2)

    # ---- The buildings.
    # The bunkhouse along the north: long, low, brown boards, five windows.
    bwin = [(7.0, 8.0), (8.9, 9.9), (13.0, 14.0), (15.0, 16.0)]
    hut("Bunkhouse", BUNK, 2.4, brown, tin, [("s", BUNK_DOOR[0], BUNK_DOOR[1], 0.0, 2.05)] + [("s", a, b, 1.0, 1.7) for a, b in bwin], ridge="x", pitch=0.26)
    for i, (a, b) in enumerate(bwin):
        window(BUNK, "s", a, b, 1.0, 1.7, frame_m, glass_m, boarded=i == 1, broken=i == 2, board_m=mat("planks"))
    kit.shards("Glass under the bunkhouse window", (13.5, 2.1, 0.0), spread=0.6, count=14, seed=4)
    # Its door: forced open out against the wall, a fire axe buried in it.
    bdoor = reb.prim("cube", "Bunkhouse door", mat("planks"), (BUNK_DOOR[0] - 0.45, BUNK[3] + T + 0.07, 1.02), (0.9, 0.05, 2.04))
    reb.prim("cube", "Door brace", frame_m, (BUNK_DOOR[0] - 0.45, BUNK[3] + T + 0.1, 1.02), (0.8, 0.03, 0.1), rot=(0, 0.9, 0))
    for x in (BUNK_DOOR[0] - 0.04, BUNK_DOOR[1] + 0.04):
        reb.prim("cube", "Door frame", frame_m, (x, BUNK[3] + T / 2, 1.05), (0.08, T + 0.04, 2.1))
    reb.prim("cube", "Door head", frame_m, ((BUNK_DOOR[0] + BUNK_DOOR[1]) / 2, BUNK[3] + T / 2, 2.1), (BUNK_DOOR[1] - BUNK_DOOR[0] + 0.16, T + 0.04, 0.08))
    reb.prim("cube", "Step", mat("planks"), ((BUNK_DOOR[0] + BUNK_DOOR[1]) / 2, BUNK[3] + T + 0.25, 0.08), (1.4, 0.5, 0.16))
    axe_at = Vector((BUNK_DOOR[0] - 0.5, BUNK[3] + T + 0.1, 1.3))
    kit.rod("Axe handle", reb.mat_wood("Axe handle", (0.4, 0.28, 0.14)), axe_at + Vector((0, 0.02, 0)), axe_at + Vector((0.25, 0.75, -0.25)), 0.02)
    reb.prim("cube", "Axe head", reb.mat_plain("Fire axe red", (0.4, 0.03, 0.02), 0.45), axe_at + Vector((-0.02, 0.02, 0.02)), (0.22, 0.06, 0.12), rot=(0, 0.35, 0.2))
    for i in range(4):
        reb.prim("cube", f"Axe cut {i}", reb.mat_wood("Fresh wood", (0.45, 0.34, 0.2)), axe_at + Vector((rng.uniform(-0.25, 0.2), -0.005, rng.uniform(-0.35, 0.3))), (0.18, 0.02, 0.025), rot=(0, rng.uniform(-0.6, 0.6), 0))
    kit.scratches("Gouges in the door", mat("black"), (BUNK_DOOR[0] - 0.3, BUNK[3] + T + 0.1, 1.0), (0, 1), count=4, length=0.4, seed=3)
    kit.splat("Handprint by the bunkhouse door", mat("old blood"), (BUNK_DOOR[1] + 0.12, BUNK[3] + T + 0.005, 1.15), 0.07, rot=(math.pi / 2, 0, 0), seed=5)
    # Inside, through the door: bunk ends, and the bulb that fails.
    for x in (8.0, 10.2, 13.0, 15.2):
        kit.bunk(f"Bunk inside {x}", mat("iron"), (x, -2.4, 0.0), seed=int(x))
    kit.bunk("Bunk inside, south", mat("iron"), (12.6, 0.6, 0.0), seed=31)
    bcord, bglass, blight, bglow = kit.bulb("Bunkhouse bulb", (11.45, -0.6, 2.4), energy=35, rgb=(1.0, 0.75, 0.45), flex=0.4)

    # The foreman's office in the north-west corner: green boards, a stovepipe.
    hut("Office", OFFICE, 2.5, green, tin, [("s", OFFICE_DOOR[0], OFFICE_DOOR[1], 0.0, 2.05), ("s", 3.75, 4.35, 1.0, 1.8), ("e", 1.2, 2.3, 1.0, 1.8)], ridge="y", pitch=0.32, eaves=0.3)
    window(OFFICE, "s", 3.75, 4.35, 1.0, 1.8, frame_m, glass_m)
    window(OFFICE, "e", 1.2, 2.3, 1.0, 1.8, frame_m, glass_m)
    reb.prim("cube", "Office door", mat("green paint"), (OFFICE_DOOR[0] - 0.05, OFFICE[3] + T + 0.42, 1.02), (0.05, 0.85, 2.04), rot=(0, 0, 0.15))
    for x in (OFFICE_DOOR[0] - 0.04, OFFICE_DOOR[1] + 0.04):
        reb.prim("cube", "Door frame", frame_m, (x, OFFICE[3] + T / 2, 1.05), (0.08, T + 0.04, 2.1))
    reb.prim("cube", "Door head", frame_m, ((OFFICE_DOOR[0] + OFFICE_DOOR[1]) / 2, OFFICE[3] + T / 2, 2.1), (1.06, T + 0.04, 0.08))
    reb.prim("cube", "Office sign", mat("white paint"), ((OFFICE_DOOR[0] + OFFICE_DOOR[1]) / 2, OFFICE[3] + T + 0.02, 2.3), (0.8, 0.03, 0.2))
    kit.text("Office sign words", "OFFICE", mat("black"), ((OFFICE_DOOR[0] + OFFICE_DOOR[1]) / 2, OFFICE[3] + T + 0.04, 2.3), size=0.13, rot=(math.pi / 2, 0, math.pi))
    reb.prim("cube", "Office step", mat("planks"), ((OFFICE_DOOR[0] + OFFICE_DOOR[1]) / 2, OFFICE[3] + T + 0.22, 0.08), (1.2, 0.44, 0.16))
    kit.rod("Office stovepipe", mat("rust"), (1.6, 1.4, 2.4), (1.6, 1.4, 3.9), 0.08)
    kit.text("Office window words", "KEEP OUT", mat("red paint"), (4.05, OFFICE[3] + T + 0.1, 1.4), size=0.09, rot=(math.pi / 2, 0, math.pi))

    # The mess hall along the west: whitewashed boards, its chimney smoking.
    mwin = [(6.0, 7.4), (11.2, 12.6)]
    hut("Mess", MESS, 2.8, white, tin, [("e", MESS_DOOR[0], MESS_DOOR[1], 0.0, 2.1)] + [("e", a, b, 1.0, 1.9) for a, b in mwin], ridge="y", pitch=0.28)
    for a, b in mwin:
        window(MESS, "e", a, b, 1.0, 1.9, frame_m, reb.mat_glass("Steamy glass", (0.45, 0.42, 0.36)))
    reb.prim("cube", "Mess door", mat("white paint"), (MESS[1] + T + 0.42, MESS_DOOR[1] + 0.05, 1.04), (0.85, 0.05, 2.08), rot=(0, 0, 0.12))
    for y in (MESS_DOOR[0] - 0.04, MESS_DOOR[1] + 0.04):
        reb.prim("cube", "Door frame", frame_m, (MESS[1] + T / 2, y, 1.08), (T + 0.04, 0.08, 2.16))
    reb.prim("cube", "Door head", frame_m, (MESS[1] + T / 2, (MESS_DOOR[0] + MESS_DOOR[1]) / 2, 2.16), (T + 0.04, 1.06, 0.08))
    reb.prim("cube", "Mess sign", frame_m, (MESS[1] + T + 0.03, (MESS_DOOR[0] + MESS_DOOR[1]) / 2, 2.45), (0.03, 1.4, 0.3))
    kit.text("Mess sign words", "COOKHOUSE", mat("white paint"), (MESS[1] + T + 0.05, (MESS_DOOR[0] + MESS_DOOR[1]) / 2, 2.45), size=0.17, rot=(math.pi / 2, 0, math.pi / 2))
    reb.prim("cube", "Mess step", mat("planks"), (MESS[1] + T + 0.25, (MESS_DOOR[0] + MESS_DOOR[1]) / 2, 0.08), (0.5, 1.3, 0.16))
    reb.prim("cube", "Mess chimney", mat("brick"), (-0.4, 6.0, 3.4), (0.6, 0.6, 2.4))
    mess_glow = reb.point("Range glow in the mess", (0.4, 8.0, 1.6), 25, (1.0, 0.55, 0.25), 0.5)
    reb.point("Lamp in the mess", (0.0, 12.0, 2.2), 12, (1.0, 0.7, 0.4), 0.3)
    reb.prim("cube", "Mess counter inside", mat("dark wood"), (-1.0, 7.0, 0.45), (1.6, 0.6, 0.9))
    kit.table("Mess table inside", mat("pine"), (0.0, 11.4, 0.0), size=(0.9, 2.6, 0.76))
    # Laid out under canvas along the mess wall, early on.
    canvas = reb.mat_surface("Tarp", [(0.0, (0.1, 0.11, 0.07)), (1.0, (0.2, 0.2, 0.13))], scale=6, bump=0.3)
    for i, x in enumerate((2.95, 3.95)):
        kit.body(f"Laid out {i}", (x, 10.55, 0.0), heading=math.pi / 2, seed=60 + i)
        reb.cloth(f"Canvas over {i}", canvas, (x, 11.65, 0.24), (0.95, 1.45), rot=(0, 0, rng.uniform(-0.08, 0.08)), cuts=14, lumps=0.07, seed=60 + i)
    kit.splat("Stain through the canvas", mat("old blood"), (3.0, 11.3, 0.31), 0.14, seed=61)

    # The workshop in the south-east: corrugated tin on a timber frame.
    hut("Workshop", WORK, 3.0, tin_wall, tin, [("n", WORK_DOOR[0], WORK_DOOR[1], 0.0, 2.3), ("n", 17.0, 18.2, 1.1, 1.9), ("w", 15.4, 16.6, 1.1, 1.9)], ridge="x", pitch=0.22)
    window(WORK, "n", 17.0, 18.2, 1.1, 1.9, frame_m, glass_m, boarded=True, board_m=mat("planks"))
    window(WORK, "w", 15.4, 16.6, 1.1, 1.9, frame_m, glass_m, boarded=True, board_m=mat("planks"))
    reb.prim("cube", "Workshop door", tin_wall, (WORK_DOOR[1] + 0.62, WORK[2] - T - 0.06, 1.15), (1.2, 0.04, 2.3))
    for x in (WORK_DOOR[0] - 0.05, WORK_DOOR[1] + 0.05):
        reb.prim("cube", "Door frame", frame_m, (x, WORK[2] - T / 2, 1.2), (0.1, T + 0.04, 2.4))
    reb.prim("cube", "Door head", frame_m, ((WORK_DOOR[0] + WORK_DOOR[1]) / 2, WORK[2] - T / 2, 2.35), (1.4, T + 0.04, 0.1))
    reb.prim("cube", "Workshop sign", mat("yellow paint"), (16.0, WORK[2] - T - 0.03, 2.65), (1.8, 0.03, 0.3))
    kit.text("Workshop sign words", "SHOP  NO SMOKING", mat("black"), (16.0, WORK[2] - T - 0.05, 2.65), size=0.13)
    # A barricade: a bench and boards he pulled away from the inside of the door.
    kit.barricade("Boards torn off the shop door", mat("planks"), (WORK_DOOR[0] - 0.3, WORK[2] - 0.45), (WORK_DOOR[0] + 0.8, WORK[2] - 0.9), 0.02, 0.06, count=3, seed=8)
    reb.point("Workshop inside", ((WORK[0] + WORK[1]) / 2, (WORK[2] + WORK[3]) / 2, 2.2), 15, (0.7, 0.8, 1.0), 0.3)
    kit.text("Scrawl on the shop", "DONT LET THEM IN", mat("red paint"), (WORK[0] - T - 0.01, 14.6, 1.6), size=0.14, rot=(math.pi / 2, 0, -math.pi / 2))

    # The sawmill along the east: a tall grey shed, its big doors run open.
    mx0, mx1, my0, my1 = MILL
    kit.walls(mx0 + T, my0, mx1, my1, 6.0, grey, [("w", MILL_DOOR[0], MILL_DOOR[1], 0.0, 3.4), ("w", 3.4, 5.0, 3.8, 4.8), ("w", 10.0, 11.6, 3.8, 4.8)], thick=T, name="Sawmill wall",
              floor=reb.mat_surface("Sawdust", [(0.0, (0.22, 0.16, 0.09)), (1.0, (0.42, 0.33, 0.2))], scale=8, bump=0.3))
    for i in range(2):
        reb.prim("cube", "Sawmill roof", tin, ((mx0 + mx1) / 2, (my0 + my1) / 2 + (i * 2 - 1) * 2.5, 6.8), (mx1 - mx0 + 1.0, 5.4, 0.06), rot=((i * 2 - 1) * 0.3, 0, 0))
    reb.prim("cube", "Sawmill dark", reb.mat_plain("Mill dark", (0.012, 0.01, 0.008), 0.95), (mx0 + 9.0, (my0 + my1) / 2, 3.0), (0.2, my1 - my0 - 0.3, 6.0))
    for y in (MILL_DOOR[0] - 1.45, MILL_DOOR[1] + 1.45):
        reb.prim("cube", "Mill door, run back", grey, (mx0 - 0.08, y, 1.7), (0.06, 2.9, 3.4))
    reb.prim("cube", "Mill door rail", mat("rust"), (mx0 - 0.1, (MILL_DOOR[0] + MILL_DOOR[1]) / 2, 3.5), (0.08, 9.0, 0.08))
    reb.prim("cube", "Head saw carriage", mat("rust"), (mx0 + 3.5, 7.5, 0.5), (5.0, 0.9, 0.8))
    logs_mesh("Log on the carriage", [((mx0 + 1.6, 7.5, 1.2), (mx0 + 5.6, 7.5, 1.2), 0.38)])
    reb.prim("cyl", "Head saw", mat("steel"), (mx0 + 4.0, 6.7, 1.2), (1.6, 1.6, 0.03), rot=(math.pi / 2, 0, 0), segments=32)
    reb.point("Mill skylight", (mx0 + 4.0, 7.5, 5.0), 60, (0.7, 0.75, 0.85), 1.0)
    reb.prim("cube", "Mill sign", mat("white paint"), (mx0 - 0.04, 7.5, 4.1), (0.03, 3.2, 0.5))
    kit.text("Mill sign words", "CAMP 4 SAWMILL", mat("black"), (mx0 - 0.07, 7.5, 4.1), size=0.3, rot=(math.pi / 2, 0, -math.pi / 2))
    mill_foot = reb.prim("cube", "Sawmill footprint", None, ((mx0 + mx1) / 2, (my0 + my1) / 2, 0.5), (mx1 - mx0, my1 - my0 + 0.3, 1.0))
    mill_foot.hide_render = True
    reb.wall(mill_foot)

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
    gate_leaf = reb.prim("cube", "Depot gate", wire, (DEPOT_GATE[0] + 0.25, DEPOT[2] - 0.85, 0.95), (0.02, 1.7, 1.8), rot=(0, 0, 0.3))
    for x in DEPOT_GATE:
        reb.mask(reb.wall(kit.rod("Depot gate post", mat("rust"), (x, DEPOT[2], 0), (x, DEPOT[2], 2.2), 0.05, 8), "circle"))
    reb.prim("cube", "Depot sign", mat("white paint"), (5.5, DEPOT[2] - 0.03, 1.4), (0.9, 0.02, 0.45))
    kit.text("Depot sign words", "FUEL", mat("red paint"), (5.5, DEPOT[2] - 0.045, 1.5), size=0.16)
    kit.text("Depot sign words 2", "NO NAKED FLAME", mat("red paint"), (5.5, DEPOT[2] - 0.045, 1.3), size=0.07)
    # Inside the depot: drums, the tank on its stand, the hose reel.
    for i, (x, y) in enumerate(((0.2, 16.4), (0.85, 16.5), (0.5, 17.1), (5.6, 19.6), (6.0, 18.9))):
        kit.drum(f"Depot drum {i}", mat("red paint") if i % 2 else mat("rust"), (x, y, 0.0), rot=rng.uniform(0, 3))
    reb.prim("cyl", "Depot tank", reb.mat_plain("Tank green", (0.1, 0.14, 0.09), 0.5), (2.6, 19.4, 1.6), (1.4, 1.4, 3.4), rot=(0, math.pi / 2, 0), segments=20)
    for x in (1.4, 3.8):
        reb.prim("cube", "Tank stand", mat("rust"), (x, 19.4, 0.45), (0.15, 1.2, 0.9))
    kit.splat("Oil in the depot", reb.mat_plain("Oil", (0.015, 0.013, 0.012), 0.12), (3.0, 17.4, 0.0), 0.9, seed=9, stretch=(1.4, 0.8))
    room.void((X0, DEPOT[2], DEPOT[1], Y1))

    # ---- The camp gate: two log posts and a beam, the leaves dragged open.
    gate_logs = [((GATE[0], GATE_Y, -0.3), (GATE[0], GATE_Y, 4.6), 0.2), ((GATE[1], GATE_Y, -0.3), (GATE[1], GATE_Y, 4.6), 0.2),
                 ((GATE[0] - 0.5, GATE_Y, 4.35), (GATE[1] + 0.5, GATE_Y, 4.35), 0.18)]
    logs_mesh("Gate logs", gate_logs)
    for x in GATE:
        reb.mask(reb.wall(reb.prim("cyl", "Gate post footprint", None, (x, GATE_Y, 1.0), (0.4, 0.4, 2.0)), "circle")).hide_render = True
    for i, (x, yaw) in enumerate(((GATE[0] - 0.9, 0.5), (GATE[1] + 0.9, -0.6))):
        reb.prim("cube", f"Gate leaf {i}", mat("logs"), (x, GATE_Y + 0.9, 0.9), (1.8, 0.1, 1.5), rot=(0, 0, yaw))
    kit.path_strip("Road out", kit.dirtied(mat("dirt"), 0.6), [(10.3, 18.4), (10.4, 24.0), (11.5, 34.0)], height, width=1.4)
    # Their barricade, pulled down: logs dragged aside, a broken board.
    logs_mesh("Barricade logs", [((7.1, 18.2, 0.2), (8.2, 16.4, 0.22), 0.2), ((12.1, 18.4, 0.2), (13.0, 15.7, 0.2), 0.18)])

    # ---- The quarantine board, painted by hand on a sheet of ply, nailed to two posts.
    for x in (7.1, 8.5):
        reb.mask(reb.wall(kit.rod("Board post", mat("dark wood"), (x, 16.85, 0), (x, 16.85, 2.0), 0.05), "circle"))
    reb.prim("cube", "Quarantine board", ply, (7.8, 16.9, 1.45), (1.9, 0.03, 1.0), rot=(0, 0.04, 0))
    for i, (words, size, z, m) in enumerate((("CAMP 4", 0.2, 1.75, mat("black")), ("QUARANTINE", 0.24, 1.47, mat("red paint")), ("BY ORDER", 0.15, 1.2, mat("black")))):
        kit.text(f"Board words {i}", words, m, (7.8, 16.92, z), size=size, rot=(math.pi / 2, -0.04, math.pi))
    kit.splat("Paint run", mat("red paint"), (8.25, 16.92, 1.32), 0.025, rot=(math.pi / 2, 0, 0), stretch=(0.5, 3.0), seed=2)

    # ---- The fire pit: a ring of stones, ash, a mattress's springs, charred bones, a log still smoking.
    sv, sf = [], []
    for i in range(14):
        a = 2 * math.pi * i / 14
        reb.boulder(rng, (PIT[0] + math.cos(a) * 1.05, PIT[1] + math.sin(a) * 1.05, 0.0), rng.uniform(0.14, 0.2), sv, sf)
    reb.mesh_object("Fire ring", sv, sf, kit.dirtied(mat("rock"), 0.8))
    reb.mask(reb.wall(reb.prim("cyl", "Fire pit footprint", None, (PIT[0], PIT[1], 0.3), (2.3, 2.3, 0.6)), "circle")).hide_render = True
    reb.prim("cyl", "Ash heap", ash, (PIT[0], PIT[1], 0.02), (2.0, 2.0, 0.08), segments=24)
    kit.splat("Ash blown out", ash, (PIT[0] + 0.8, PIT[1] + 0.4, 0.0), 1.2, seed=3, stretch=(1.4, 0.8), lumps=0.5)
    logs_mesh("Charred logs", [((PIT[0] - 0.7, PIT[1] - 0.3, 0.12), (PIT[0] + 0.5, PIT[1] + 0.25, 0.25), 0.11),
                               ((PIT[0] + 0.6, PIT[1] - 0.5, 0.1), (PIT[0] - 0.2, PIT[1] + 0.6, 0.2), 0.1),
                               ((PIT[0] - 0.4, PIT[1] + 0.5, 0.1), (PIT[0] + 0.3, PIT[1] - 0.6, 0.12), 0.09)], bark=char, end=char)
    spr = []
    for i in range(7):
        spr.append(kit.rod("Spring wire", mat("rust"), (PIT[0] - 0.9 + i * 0.3, PIT[1] - 0.45, 0.14 + 0.05 * math.sin(i)), (PIT[0] - 0.9 + i * 0.3 + 0.05, PIT[1] + 0.5, 0.16), 0.008, 4))
    for y in (-0.45, 0.5):
        spr.append(kit.rod("Spring frame", mat("rust"), (PIT[0] - 0.95, PIT[1] + y, 0.15), (PIT[0] + 0.95, PIT[1] + y, 0.16), 0.012, 4))
    kit.join("Mattress springs", spr)
    bones = kit.bones("Charred bones", (PIT[0] + 0.2, PIT[1] + 0.1, 0.06), spread=0.6, seed=12)
    bones.data.materials.clear()
    bones.data.materials.append(reb.mat_plain("Burnt bone", (0.12, 0.1, 0.08), 0.8))
    ember_m = reb.mat_emit("Embers", (1.0, 0.28, 0.04), 4)
    ev, ef = [], []
    for i in range(30):
        c = (PIT[0] + rng.gauss(0, 0.3), PIT[1] + rng.gauss(0, 0.3), 0.1)
        kit._stain(ev, ef, rng, c, rng.uniform(0.02, 0.05), 0, 0.4, (1, 1), i, points=6, drops=False)
    reb.mesh_object("Ember spots", ev, ef, ember_m, smooth=False)
    embers = reb.point("Ember glow", (PIT[0], PIT[1], 0.35), 30, (1.0, 0.35, 0.08), 0.4)
    smoke_pit = smoke_column("Pit smoke", (PIT[0] + 0.1, PIT[1], 0.4), puffs=6, rise=3.4, drift=(0.9, 0.4), size=(0.35, 1.3), density=7.0)
    smoke_mess = smoke_column("Chimney smoke", (-0.4, 6.0, 4.7), puffs=4, rise=2.4, drift=(1.0, 0.3), size=(0.25, 0.9), density=5.0)
    # The drag from the bunkhouse door to the fire.
    kit.drag_trail("Dragged to the fire", mat("old blood"), [(11.4, 2.4), (11.0, 4.2), (10.2, 6.0), (9.6, 7.1)], width=0.4, seed=7)

    # ---- The bell on its post by the cookhouse door.
    reb.mask(reb.wall(kit.rod("Bell post", mat("dark wood"), (3.2, 7.3, 0), (3.2, 7.3, 2.9), 0.07), "circle"))
    kit.rod("Bell arm", mat("dark wood"), (3.2, 7.3, 2.75), (3.2, 7.95, 2.75), 0.04)
    pivot = reb.prim("sphere", "Bell pivot", mat("iron"), (3.2, 7.85, 2.7), (0.05, 0.05, 0.05))
    bell = reb.prim("cone", "Bell", reb.mat_metal("Bell bronze", (0.45, 0.3, 0.12), 0.4), (0, 0, -0.2), (0.42, 0.42, 0.38), top=0.45, segments=16)
    clapper = reb.prim("sphere", "Clapper", mat("iron"), (0, 0, -0.4), (0.06, 0.06, 0.06))
    rope = kit.rod("Bell rope", mat("canvas"), (0, 0, -0.4), (0, 0, -1.2), 0.012, 5)
    for p in (bell, clapper, rope):
        p.parent = pivot

    # ---- The laundry on the line: shirts, long johns, a pair of socks.
    la, lb = Vector((5.6, 2.6, 0)), Vector((9.8, 3.4, 0))
    for p in (la, lb):
        reb.mask(reb.wall(kit.rod("Line pole", mat("dark wood"), (p.x, p.y, 0), (p.x, p.y, 2.15), 0.04), "circle"))
    kit.rod("Washing line", mat("canvas"), (la.x, la.y, 2.05), (lb.x, lb.y, 2.05), 0.006, 4)
    yaw = math.atan2(lb.y - la.y, lb.x - la.x)
    pegs = []
    for i, (t, m, w, hgt) in enumerate(((0.15, mat("flannel"), 0.6, 0.7), (0.33, reb.mat_plain("Long johns", (0.5, 0.45, 0.36), 0.9), 0.45, 1.0), (0.5, mat("denim"), 0.5, 0.85),
                                        (0.68, reb.mat_stripes("Blue flannel", [(0.05, 0.08, 0.2), (0.02, 0.03, 0.05)], across=20), 0.6, 0.7), (0.84, mat("canvas"), 0.3, 0.35))):
        p = la.lerp(lb, t)
        sag = 0.12 * math.sin(math.pi * t)
        peg = reb.prim("sphere", f"Peg {i}", mat("planks"), (p.x, p.y, 2.04 - sag), (0.03, 0.03, 0.05))
        cl = reb.cloth(f"Washing {i}", m, (0, 0, -hgt / 2), (w, hgt), rot=(math.pi / 2, 0, 0), cuts=8, lumps=0.03, seed=i)
        cl.parent = peg
        peg.rotation_euler = (0, 0, yaw)
        pegs.append(peg)
    kit.splat("Shirt in the mud", mat("flannel"), (8.6, 4.5, 0.0), 0.25, seed=14, stretch=(1.4, 0.8))

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
    kit.body("Dead against the logs", (14.6, 5.72, 0.0), heading=math.pi / 2, pose="slumped", top=mat("flannel"), legs=mat("denim"), seed=21)
    kit.splat("His blood", mat("blood"), (14.55, 6.35, 0.0), 0.5, seed=21, stretch=(1.3, 1.0))
    kit.splat("Spray on the logs", mat("old blood"), (14.6, 4.62, 1.0), 0.35, rot=(math.pi / 2, 0, 0), seed=22, stretch=(1.4, 0.8), lumps=0.6)
    reb.prim("cube", "His shotgun", mat("iron"), (15.5, 6.6, 0.04), (0.95, 0.06, 0.06), rot=(0, 0, 0.5))
    shells = []
    for i in range(9):
        shells.append(reb.prim("cyl", "Shell", mat("red paint"), (14.6 + rng.gauss(0, 0.6), 6.8 + rng.gauss(0, 0.4), 0.012), (0.024, 0.024, 0.07), rot=(math.pi / 2, 0, rng.uniform(0, 3)), segments=6))
    kit.join("Spent shells", shells)
    for i, (x, z) in enumerate(((13.4, 1.1), (14.1, 0.8), (15.8, 1.3))):
        kit.splat(f"Shot in the logs {i}", mat("black"), (x, 2.48, z), 0.03, rot=(math.pi / 2, 0, 0), seed=30 + i, lumps=0.6)

    # ---- The skidder: blade down, its choker chains on three logs.
    sk = []
    sx0, sx1, sy = 5.9, 10.0, 13.0
    sk.append(reb.prim("cube", "Skidder frame", yellow, ((sx0 + sx1) / 2, sy, 0.9), (sx1 - sx0 - 0.6, 1.2, 0.6), bevel=0.04))
    engine = kit.loft("Skidder engine", [(sx1 - 1.75, 0.58, 1.15, 1.85, 4), (sx1 - 0.5, 0.56, 1.15, 1.82, 4), (sx1 - 0.25, 0.5, 1.15, 1.7, 3)], [yellow], ring=24)
    engine.location.y = sy
    sk.append(engine)
    for s_ in (-1, 1):
        for k in range(5):
            sk.append(reb.prim("cube", "Engine louvre", mat("black"), (sx1 - 1.5 + k * 0.2, sy + s_ * 0.575, 1.5), (0.08, 0.02, 0.3)))
    sk.append(reb.prim("cube", "Skidder cab floor", yellow, (sx0 + 1.6, sy, 1.3), (1.4, 1.5, 0.15)))
    for dx in (0.95, 2.25):
        for dy in (-0.7, 0.7):
            sk.append(kit.rod("Cab post", mat("black"), (sx0 + dx, sy + dy, 1.35), (sx0 + dx, sy + dy, 2.75), 0.04))
    sk.append(reb.prim("cube", "Cab roof", yellow, (sx0 + 1.6, sy, 2.8), (1.6, 1.6, 0.08)))
    sk.append(reb.prim("cube", "Seat", mat("black"), (sx0 + 1.5, sy, 1.55), (0.45, 0.5, 0.3)))
    sk.append(kit.rod("Exhaust", mat("rust"), (sx1 - 0.7, sy - 0.35, 1.8), (sx1 - 0.7, sy - 0.35, 2.6), 0.05))
    # Big lugged forestry tyres on yellow rims.
    for x in (sx0 + 0.8, sx1 - 1.0):
        for s in (-1, 1):
            sk += kit.wheel("Skidder", (x, sy + s * 0.95, 0.75), r=0.72, width=0.55, rim=yellow)
            for k in range(22):
                a_ = 2 * math.pi * k / 22
                for half in (-1, 1):
                    sk.append(reb.prim("cube", "Tyre lug", mat("rubber"), (x + 0.74 * math.cos(a_), sy + s * 0.95 + half * 0.13, 0.75 + 0.74 * math.sin(a_)),
                                       (0.07, 0.26, 0.06), rot=(0, -a_, half * 0.45)))
    sk.append(reb.prim("cube", "Blade", yellow, (sx1 + 0.35, sy, 0.38), (0.12, 2.6, 0.75), rot=(0, 0.2, 0), bevel=0.02))
    sk.append(reb.prim("cube", "Blade arm", mat("iron"), (sx1 + 0.05, sy - 0.6, 0.7), (0.7, 0.12, 0.12), rot=(0, 0.4, 0)))
    sk.append(reb.prim("cube", "Blade arm", mat("iron"), (sx1 + 0.05, sy + 0.6, 0.7), (0.7, 0.12, 0.12), rot=(0, 0.4, 0)))
    sk.append(reb.prim("cube", "Arch", yellow, (sx0 + 0.15, sy, 1.9), (0.25, 1.6, 0.25)))
    for s in (-1, 1):
        sk.append(reb.prim("cube", "Arch leg", yellow, (sx0 + 0.3, sy + s * 0.7, 1.3), (0.2, 0.2, 1.3), rot=(0, -0.2, 0)))
    sk.append(reb.prim("cyl", "Winch drum", mat("iron"), (sx0 + 0.5, sy, 1.1), (0.5, 0.5, 0.9), rot=(math.pi / 2, 0, 0)))
    skidder = kit.join("Skidder", sk)
    reb.mask(reb.wall(skidder))
    kit.text("Skidder words", "CAMP 4", mat("black"), (sx1 - 1.0, sy + 0.56, 1.5), size=0.16, rot=(math.pi / 2, 0, math.pi))
    kit.splat("Mud pushed by the blade", wet_mud, (sx1 + 0.6, sy, 0.0), 0.7, seed=17, stretch=(0.6, 1.8), lumps=0.5)
    kit.splat("Oil under the skidder", reb.mat_plain("Oil", (0.015, 0.013, 0.012), 0.12), (sx1 - 1.2, sy + 0.2, 0.0), 0.5, seed=18)
    choked = [((sx0 - 4.0, sy - 0.35 + i * 0.35, 0.22), (sx0 - 0.4, sy - 0.2 + i * 0.2, 0.3), 0.2 + 0.03 * i) for i in range(3)]
    logs_mesh("Choked logs", choked)
    chain = []
    for i in range(3):
        a = Vector(choked[i][1]) + Vector((-0.3, 0, 0.1))
        b = Vector((sx0 + 0.1, sy, 1.75))
        for k in range(6):
            p, q = a.lerp(b, k / 6), a.lerp(b, (k + 1) / 6)
            sag = 0.25 * math.sin(math.pi * k / 6)
            chain.append(kit.rod("Choker", mat("iron"), (p.x, p.y, p.z - sag), (q.x, q.y, q.z - 0.25 * math.sin(math.pi * (k + 1) / 6)), 0.015, 4))
    kit.join("Choker chains", chain)
    room_wall_logs = reb.prim("cube", "Choked logs footprint", None, (sx0 - 2.2, sy, 0.3), (3.8, 1.2, 0.6))
    room_wall_logs.hide_render = True
    reb.mask(reb.wall(room_wall_logs))

    # ---- The logger in the mud by the skidder, a peavey in his back, his hat in the puddle.
    kit.body("Logger in the mud", (11.0, 15.2, 0.0), heading=0.25, pose="front", top=reb.mat_stripes("Green check", [(0.05, 0.15, 0.06), (0.02, 0.03, 0.02)], across=20), legs=mat("denim"), seed=33)
    kit.splat("His blood", mat("blood"), (11.9, 15.45, 0.0), 0.6, seed=33, stretch=(1.4, 0.9))
    kit.rod("Peavey handle", reb.mat_wood("Peavey", (0.35, 0.24, 0.12)), (12.2, 15.5, 0.25), (12.6, 16.3, 1.45), 0.025)
    reb.prim("cube", "Peavey hook", mat("iron"), (12.2, 15.5, 0.25), (0.06, 0.25, 0.06), rot=(0.4, 0, 0))
    reb.prim("sphere", "Hard hat", hard_hat, (12.15, 12.15, 0.04), (0.3, 0.26, 0.16), rot=(0.6, 0.3, 0))
    kit.drag_trail("He crawled", mat("old blood"), [(9.2, 16.8), (10.2, 16.1), (11.0, 15.5)], width=0.3, seed=34)
    kit.splat("Blood in the puddle", mat("blood"), (11.8, 16.3, 0.0), 0.35, seed=35, stretch=(1.3, 0.8))

    # ---- Odds and ends: a wheelbarrow over, a sawhorse, drums, a chopping block, crows.
    wb = [reb.prim("cube", "Barrow tray", mat("rust"), (0, 0, 0.35), (0.9, 0.6, 0.3), bevel=0.02),
          reb.prim("cyl", "Barrow wheel", mat("rubber"), (0.55, 0, 0.18), (0.36, 0.36, 0.08), rot=(math.pi / 2, 0, 0)),
          kit.rod("Barrow handle", mat("planks"), (-0.2, -0.22, 0.4), (-0.9, -0.25, 0.5), 0.02),
          kit.rod("Barrow handle", mat("planks"), (-0.2, 0.22, 0.4), (-0.9, 0.25, 0.5), 0.02)]
    barrow = kit.join("Wheelbarrow", wb)
    barrow.location = (5.4, 6.8, 0.42)
    barrow.rotation_euler = (math.pi * 0.9, 0, 2.4)
    reb.wall(kit.box("Chopping block", mat("logs"), (4.6, 5.4, 0.0), (0.55, 0.55, 0.5)), "circle")
    kit.rod("Axe in the block, its handle", reb.mat_wood("Axe handle 2", (0.4, 0.28, 0.14)), (4.6, 5.4, 0.55), (4.95, 5.6, 1.15), 0.02)
    reb.prim("cube", "Split wood", mat("logs"), (4.2, 5.9, 0.08), (0.5, 0.12, 0.12), rot=(0, 0, 0.6))
    reb.prim("cube", "Split wood", mat("logs"), (4.9, 6.0, 0.08), (0.45, 0.11, 0.12), rot=(0, 0, 2.1))
    for i, (x, y) in enumerate(((16.9, 13.1), (17.6, 12.6))):
        kit.drum(f"Yard drum {i}", mat("rust"), (x, y, 0.0), tipped=i == 1, rot=1.2)
    kit.splat("Diesel from the tipped drum", reb.mat_plain("Oil", (0.015, 0.013, 0.012), 0.12), (17.0, 12.0, 0.0), 0.45, seed=19)
    kit.papers("Papers blown into the yard", (6.4, 9.2, 0.0), spread=2.0, count=7, seed=6)
    kit.bottles("Bottles by the step", (12.6, 2.6, 0.0), count=5, spread=0.5, seed=4, tipped=0.8)
    crow_a, wings_a = kit.crow("Crow on the mess roof", (2.3, 9.0, 3.05), heading=0.2)
    kit.crow("Crow on the board", (8.3, 16.9, 1.97), heading=4.5)
    kit.crow("Crow at the man", (11.9, 14.7, 0.0), heading=2.6)

    # ---- The mountain round the camp: spruces, grass at the fence feet.
    def keep_out(x, y):
        if -4.5 < x < 33 and -4.2 < y < 22.0:
            return True
        if any((x - e[0]) ** 2 + (y - e[1]) ** 2 < 36 for e, _, _ in cams):
            return True
        return 7.5 < x < 13.5 and y < 40
    kit.forest(rng, height, keep_out, (-30, -30, 50, 50), count=85, spacing=2.0, ferns=30, needles=600)
    grass = kit.meadow(rng, 900, lambda r: (r.uniform(-4, 22), r.choice((r.uniform(-4.5, 0.4), r.uniform(18.9, 22.0)))) if r.random() < 0.6 else (r.choice((r.uniform(-5, 0.5), r.uniform(18.6, 22))), r.uniform(-4, 22)), height, mat("dead grass"))
    rv, rf = [], []
    for (x, y, r) in ((-4.0, -1.0, 1.1), (20.0, 15.0, 0.9), (-5.0, 15.0, 0.8), (14.5, 21.0, 0.9)):
        reb.boulder(rng, (x, y, height(x, y)), r, rv, rf)
    reb.mesh_object("Rocks", rv, rf, mat("rock"))

    # ---- Light: noon under cloud, grey and soft, mist in the trees.
    sun = kit.time_light("noon", sun_heading=200, sun_energy=1.8, mist=((9.0, 9.0, 6.0), (110, 110, 14), 0.009), sky=((0.5, 0.52, 0.54), (0.36, 0.39, 0.43), 0.75))
    sun.data.angle = math.radians(25)
    sun.rotation_euler[0] = math.radians(35)

    anim = kit.Anim(16)
    anim.custom(smoke_pit)
    anim.custom(smoke_mess)
    anim.flicker(embers, ember_m, depth=0.4, dropouts=1)
    anim.flicker(blight, bglow, depth=0.5, dropouts=3)
    anim.flicker(mess_glow, None, depth=0.15, dropouts=0)
    anim.swing(pivot, axis=1, degrees=9)

    def laundry(k):
        for i, peg in enumerate(pegs):
            peg.rotation_euler = (math.radians(9) * math.sin(anim.phase(k) + i * 0.7), 0, yaw)
    anim.custom(laundry)
    anim.flap(wings_a, degrees=25)
    anim.sway(grass, amount=0.05)

    # ---- What the game needs.
    room.door("camp-gate", (GATE[0] + 0.2, Y1 - 0.6, GATE[1] - 0.2, Y1), arrive=(10.1, 16.9), face=(0, -1))
    room.door("bunkhouse", (BUNK_DOOR[0], BUNK[3] + T, BUNK_DOOR[1], BUNK[3] + T + 0.7), arrive=(11.45, 3.4), face=(0, 1), walk=False)
    room.door("office", (OFFICE_DOOR[0], OFFICE[3] + T, OFFICE_DOOR[1], OFFICE[3] + T + 0.7), arrive=(2.95, 4.7), face=(0, 1), walk=False)
    room.door("mess", (MESS[1] + T, MESS_DOOR[0], MESS[1] + T + 0.7, MESS_DOOR[1]), arrive=(3.7, 9.45), face=(1, 0), walk=False)
    room.door("depot", (DEPOT_GATE[0], DEPOT[2] - 0.6, DEPOT_GATE[1], DEPOT[2]), arrive=(3.5, 13.7), face=(0, -1))
    room.door("workshop", (WORK_DOOR[0], WORK[2] - T - 0.7, WORK_DOOR[1], WORK[2] - T), arrive=(15.2, 12.2), face=(0, -1), walk=False)
    room.door("sawmill", (MILL_X - 0.7, MILL_DOOR[0], X1, MILL_DOOR[1]), arrive=(16.9, 7.5), face=(-1, 0), walk=False)
    room.check((6.8, 17.0, 8.8, 18.0), "CAMP 4. QUARANTINE. BY ORDER.\nPainted by hand. The paint ran before it dried.")
    room.check((10.0, 14.4, 12.8, 16.2), "A logger, face down in the mud. A peavey is driven into his back.\nThat wasn't done by anything sick.")
    room.check((7.6, 7.0, 10.4, 9.6), "They burned something here. Mattress springs. And bones.\nOne log is still smoking.")
    room.check((10.4, 1.7, 11.0, 2.6), "A fire axe, buried in the door. Someone was holding it shut from inside.")
    room.check((13.6, 5.6, 15.8, 7.2), "He sat down against the logs with a shotgun and fired until it was empty.\nShells everywhere.")
    room.check((2.6, 10.4, 4.8, 12.8), "Two men under canvas, laid out straight. Someone still cared, at first.")
    room.check((2.6, 6.8, 3.8, 8.0), "The cookhouse bell. The rope's been cut short.")
    room.check((10.4, 11.8, 11.2, 14.2), "The skidder. Its blade is down in the mud, the chokers still on the logs.\nThe key's gone.")
    room.check((5.6, 2.6, 9.8, 4.0), "Laundry on the line. Nobody's coming for it.")
    room.check((15.8, 11.6, 18.0, 13.6), "Diesel, leaking from a drum into the mud.")
    room.entry = "Camp 4. The gate was shut from inside."
    # Many scenes share the render machine's GPU: keep each frame cheap.
    scene = bpy.context.scene
    scene.render.use_persistent_data = True
    scene.cycles.volume_step_rate = 4.0
    scene.cycles.volume_max_steps = 64
    room.export(anim, samples=160)


build()
