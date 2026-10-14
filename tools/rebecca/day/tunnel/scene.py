"""The adit of the old Arklay silver mine, inside the rockfall.

What it tells: behind the fall the adit runs north into the hill and turns
east to the workings. Someone strung lamps on a cable along it not long
ago, and they still burn, swinging in the draught from the gap. The web
spinners own it now: the corners of every timber set are thick with web,
strands hang across, and at the bend a man is wrapped tight against the
rock in a sheet of it, one boot sticking out of the silk. The ones who
worked here left in a hurry: a pick and a shovel on the floor, a lamp
kicked over, a lunch pail on the rails. Water drips from the roof into the
rail bed. Hal came through bleeding: his drops follow the rails east.
Halfway along, a plank door in a timber frame closes off the mine office,
a candle glow under it.

Metres: the floor is an L inside x 3.3-19.0, y 6.9-19.0, 3.2 m high under
the arch. The west leg runs north at x 5.0 from the rockfall at the south
end (y 19) to the bend, a wide curve round x 5-9, y 8.6-12.6; the east leg runs east along y 8.6 to
the junction at the east end (x 19). The rock fills the rest. The office
door is in the north wall of the east leg at x 12.1-13.0. The way out to
the mine's mouth is the south end, x 4.0-6.0.

Moving: the lamps swinging on the cable, one of them failing; drops of
water falling from the roof.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
from kit import mat  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

X0, X1, Y0, Y1 = 3.3, 19.0, 6.9, 19.0
PATH = [(5.0, 21.0), (5.0, 12.6)] + [(9.0 + 4.0 * math.cos(math.radians(a)), 12.6 + 4.0 * math.sin(math.radians(a))) for a in range(185, 271, 5)] + [(21.0, 8.6)]
WIDTH, HEIGHT = 3.4, 3.2
OFFICE_DOOR = (12.1, 13.0)
NORTH_WALL = 7.08


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


def samples(path, step):
    """Points every `step` metres along the path, with the way it runs there."""
    out = []
    pts = [Vector((x, y, 0.0)) for x, y in path]
    carry = 0.0
    for a, b in zip(pts, pts[1:]):
        d = b - a
        t = carry
        while t < d.length:
            out.append((a + d.normalized() * t, d.normalized()))
            t += step
        carry = t - d.length
    return out


def rails(name, path, sleepers_m, rail_m, gauge=0.6):
    """Narrow-gauge track along `path` [(x, y)]: rails and sleepers, two meshes."""
    sv, sf, rv, rf = [], [], [], []
    pts = [Vector((x, y, 0.0)) for x, y in path]
    for a, b in zip(pts, pts[1:]):
        d = b - a
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


def web_sheet(name, corner, a, b, size, rng, strands=9):
    """A thick web across a corner: fans of silk from `corner` out along directions a and b, in one mesh."""
    verts, faces = [], []
    c = Vector(corner)
    a, b = Vector(a).normalized(), Vector(b).normalized()
    for i in range(strands):
        t = i / (strands - 1)
        d = (a * (1 - t) + b * t).normalized() * size * rng.uniform(0.75, 1.0)
        k = len(verts)
        side = a.cross(b).normalized() * 0.006
        verts += [tuple(c), tuple(c + d), tuple(c + d + side)]
        faces.append((k, k + 1, k + 2))
    for r in (0.3, 0.55, 0.8):
        for i in range(strands - 1):
            p = c + (a * (1 - i / (strands - 1)) + b * (i / (strands - 1))).normalized() * size * r
            q = c + (a * (1 - (i + 1) / (strands - 1)) + b * ((i + 1) / (strands - 1))).normalized() * size * r
            k = len(verts)
            verts += [tuple(p), tuple(q), tuple(q + Vector((0, 0, -0.008)))]
            faces.append((k, k + 1, k + 2))
    ob = reb.mesh_object(name, verts, faces, mat("web"), smooth=False)
    # A haze of silk filling the corner, mostly see-through.
    reb.mesh_object(f"{name} haze", [tuple(c), tuple(c + a * size * 0.75), tuple(c + b * size * 0.75)], [(0, 1, 2)], haze_material(), smooth=False).visible_shadow = False
    return ob


_haze = []


def haze_material():
    """Web silk seen as a film: mostly transparent, pale where it catches the light."""
    if _haze:
        return _haze[0]
    m, nodes, links, bsdf = reb.nodes_material("Web haze")
    bsdf.inputs["Base Color"].default_value = (0.7, 0.7, 0.68, 1)
    bsdf.inputs["Roughness"].default_value = 0.8
    clear = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.22
    m.node_tree.links.new(clear.outputs[0], mix.inputs[1])
    m.node_tree.links.new(bsdf.outputs[0], mix.inputs[2])
    m.node_tree.links.new(mix.outputs[0], nodes["Material Output"].inputs["Surface"])
    _haze.append(m)
    return m


def near_segment(p, a, b):
    """How far point p is from the segment a-b."""
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.dot(ab), 1e-9)))
    return (a + ab * t - p).length


def drips(name, m, pts, rng, r=(0.02, 0.05), z=0.0):
    """Blood drops at points, in one mesh."""
    v, f = [], []
    for x, y in pts:
        kit._stain(v, f, rng, (x, y, z + 0.005), rng.uniform(*r), rng.uniform(0, 6.3), 0.45, (1.0, 1.0), rng.randint(0, 99), points=10, drops=rng.random() < 0.35)
    return reb.mesh_object(name, v, f, m, smooth=False)


def build():
    rng = random.Random(53)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    eyes = [{"eye": e} for e in ((5.5, 18.4, 2.1), (5.6, 11.8, 2.1), (6.5, 8.3, 2.1), (15.6, 9.1, 2.1), (10.2, 8.2, 2.1))]
    room.camera((5.5, 18.4, 2.1), (5.0, 12.0, 0.5), 200, "inside the fall, looking up the adit: the lamps on the cable, the bend, the wrapped man")
    room.camera((5.6, 11.8, 2.1), (5.0, 18.0, 0.4), 200, "at the bend, looking back south: the rails, the tools, the daylight through the gap")
    room.camera((6.5, 8.3, 2.1), (14.5, 8.8, 0.4), 200, "round the bend, looking east: the webs over the timber sets, the office door")
    room.camera((15.6, 9.1, 2.1), (8.2, 8.9, 0.4), 200, "along the east leg looking back west: the office door, the bend, the wrapped man")
    room.camera((10.2, 8.2, 2.1), (18.8, 8.8, 0.5), 200, "from by the office looking east: the cart, the drops along the rails to the junction")

    rock = kit.dirtied(mat("wet rock"), 0.6, scale=1.0)
    timber = kit.dirtied(reb.mat_wood("Mine timber", (0.14, 0.095, 0.055)), 0.75, scale=3)
    rust = mat("rust")
    mud = reb.mat_surface("Adit mud", [(0.0, (0.03, 0.025, 0.02)), (0.5, (0.07, 0.055, 0.04)), (1.0, (0.11, 0.09, 0.06))], scale=2.5, rough=0.5, bump=0.6)
    puddle = reb.mat_plain("Puddle", (0.012, 0.012, 0.012), 0.04)
    silk = reb.mat_plain("Silk", (0.3, 0.3, 0.28), 0.7)
    cocoon_m = reb.mat_surface("Cocoon", [(0.0, (0.4, 0.39, 0.36)), (0.7, (0.6, 0.59, 0.55)), (1.0, (0.28, 0.1, 0.06))], scale=14, bump=0.9)

    # ---- The rock: the adit's arch along the path, its floor of mud.
    kit.tunnel("Adit", rock, PATH, width=WIDTH, height=HEIGHT, rough=0.13, seed=11, floor_m=mud)
    for (x0_, y0_, x1_, y1_) in ((9.0, 10.3, X1, Y1), (6.7, 12.6, 9.0, Y1), (7.5, 11.1, 9.0, 12.6), (X0, Y0, 5.0, 8.6), (X0, 8.6, 4.0, 10.2), (5.0, Y0, 6.6, 7.5)):
        reb.wall(reb.prim("cube", "Rock round the bend", None, ((x0_ + x1_) / 2, (y0_ + y1_) / 2, 0.5), (x1_ - x0_, y1_ - y0_, 1.0))).hide_render = True
    # The south end: the back of the rockfall, daylight through the gap low on the west side.
    rv, rf = [], []
    for _ in range(40):
        reb.boulder(rng, (rng.uniform(3.4, 6.7), rng.uniform(19.3, 20.6), rng.uniform(0.0, 2.8)), rng.uniform(0.35, 0.7), rv, rf)
    reb.mesh_object("Back of the fall", rv, rf, kit.dirtied(mat("rock"), 0.6))
    reb.prim("cube", "Gap light", reb.mat_emit("Daylight in the gap", (1.0, 0.85, 0.65), 4.0), (4.25, 20.9, 0.5), (0.7, 0.05, 0.6))
    reb.spot("Daylight through the gap", (4.3, 21.5, 0.6), (5.0, 14.0, 0.0), 300, (1.0, 0.85, 0.65), 35, 0.6, 0.2)
    # The east end: darker on into the junction.
    reb.prim("cube", "The dark east", mat("black"), (21.5, 8.6, 1.5), (0.2, 4.0, 3.5))

    # ---- Timber sets every couple of metres, the rails, the lamp cable along the crown.
    sets = samples([(5.0, 19.0), (5.0, 12.6)], 2.6) + samples(PATH[2:-1], 2.5)[1:] + samples([(9.0, 8.6), (19.4, 8.6)], 2.4)
    tparts = []
    for p, d in sets:
        side = Vector((-d.y, d.x, 0))
        for s in (-1, 1):
            tparts.append(kit.rod("Set post", timber, p + side * 1.45 * s, p + side * 1.18 * s + Vector((0, 0, 2.45)), 0.09, 6))
        tparts.append(kit.rod("Set cap", timber, p + side * 1.28 + Vector((0, 0, 2.47)), p - side * 1.28 + Vector((0, 0, 2.47)), 0.1, 6))
        for k in range(3):
            tparts.append(reb.prim("cube", "Lagging", timber, p + side * (k - 1) * 0.6 + Vector((0, 0, 2.6)), (0.5, 0.16, 0.05), rot=(0, 0, math.atan2(d.y, d.x) + math.pi / 2)))
    kit.join("Timber sets", tparts)
    rails("Rails", [(5.0, 19.6)] + PATH[1:], timber, rust)
    cable_pts = [(Vector((5.0, 19.2, 2.85)), Vector((0, -1, 0)))] + [(p + Vector((0, 0, 2.85)), d) for p, d in samples(PATH[1:], 0.9)]
    cparts = []
    for (a, _), (b, _) in zip(cable_pts, cable_pts[1:]):
        cparts.append(kit.rod("Cable", mat("black"), a, b, 0.01, 4))
    kit.join("Lamp cable", cparts)
    lamps = []
    for k, (x, y) in enumerate(((5.0, 17.2), (5.0, 13.4), (6.17, 9.77), (10.6, 8.6), (14.6, 8.6), (18.0, 8.6))):
        glow = reb.mat_emit(f"Lamp glow {k}", (1.0, 0.72, 0.4), 1.5)
        pivot = reb.prim("sphere", f"Lamp hook {k}", mat("iron"), (x, y, 2.85), (0.03, 0.03, 0.03))
        flex = kit.rod(f"Lamp flex {k}", mat("black"), (0, 0, 0), (0, 0, -0.32), 0.007, 4)
        bulb = reb.prim("sphere", f"Lamp bulb {k}", glow, (0, 0, -0.4), (0.07, 0.07, 0.1), segments=10)
        cage = [kit.rod("Cage wire", mat("iron"), (math.cos(a) * 0.06, math.sin(a) * 0.06, -0.33), (math.cos(a) * 0.06, math.sin(a) * 0.06, -0.47), 0.004, 3) for a in (0, 2.1, 4.2)]
        light = reb.point(f"Lamp {k}", (0, 0, -0.42), 45 if k != 3 else 30, (1.0, 0.68, 0.38), 0.05)
        for p in [flex, bulb, light] + cage:
            p.parent = pivot
        lamps.append((pivot, light, glow))

    # ---- The webs: thick in the corners of the sets, sheets across; the wrapped man at the bend.
    for i, (p, d) in enumerate(sets):
        if rng.random() < 0.3:
            continue
        side = Vector((-d.y, d.x, 0))
        s = rng.choice((-1, 1))
        corner = p + side * 1.22 * s + Vector((0, 0, 2.42))
        if any((Vector(c["eye"]) - corner).length < 1.6 for c in eyes):
            continue
        web_sheet(f"Web {i}", corner, -side * s, Vector((0, 0, -1)) + side * s * 0.2, rng.uniform(0.5, 0.9), rng)
    web_sheet("Web over the bend", (4.6, 8.8, 2.3), (1, -0.4, 0), (0.3, 0.3, -1), 1.2, rng, strands=13)
    web_sheet("Web over the door", (OFFICE_DOOR[1] + 0.25, NORTH_WALL + 0.1, 2.1), (1, 0, 0), (0, 0.2, -1), 0.9, rng)
    strands = []
    for _ in range(14):
        p, d = sets[rng.randrange(len(sets))]
        side = Vector((-d.y, d.x, 0))
        a = p + side * rng.uniform(-1.0, 1.0) + Vector((0, 0, 2.15))
        b = p + d * rng.uniform(-0.8, 0.8) + side * rng.uniform(-1.2, 1.2) + Vector((0, 0, rng.uniform(1.2, 2.0)))
        if any(near_segment(Vector(c["eye"]), a, b) < 1.0 for c in eyes):
            continue
        strands.append(kit.rod("Strand", silk, a, b, 0.003, 3))
    kit.join("Strands", strands)
    cx, cy = 5.3, 8.95
    cocoon = reb.prim("sphere", "Wrapped man", cocoon_m, (cx, cy, 1.15), (0.5, 0.42, 1.75), rot=(0.1, 0.1, 0.8), segments=16)
    reb.mask(cocoon)
    reb.prim("cube", "Boot out of the silk", mat("rubber"), (cx + 0.18, cy + 0.18, 0.25), (0.28, 0.12, 0.14), rot=(0, 0.5, 0.8), bevel=0.03)
    reb.prim("sphere", "Silk at his head", cocoon_m, (cx - 0.05, cy - 0.05, 1.95), (0.36, 0.34, 0.3), segments=12)
    for k in range(9):
        a = rng.uniform(-1.2, 1.2)
        kit.rod("Silk tether", silk, (cx, cy, rng.uniform(0.6, 1.9)), (cx - 0.45 + a * 0.4, cy - 0.45 - a * 0.4, rng.uniform(0.2, 2.3)), 0.004, 3)
    kit.splat("Blood under the wrapped man", mat("old blood"), (cx + 0.3, cy + 0.3, 0.0), 0.25, seed=4, stretch=(1.2, 0.8))
    reb.wall(reb.prim("cube", "Wrapped man footprint", None, (cx, cy, 0.5), (0.7, 0.7, 1.0))).hide_render = True

    # ---- The office door: a timber frame in the rock, planks, OFFICE in paint, candlelight under it.
    d0, d1 = OFFICE_DOOR
    wy = NORTH_WALL
    for x in (d0 - 0.1, d1 + 0.1):
        kit.rod("Office door post", timber, (x, wy + 0.05, 0), (x, wy + 0.05, 2.0), 0.08, 6)
    kit.rod("Office door lintel", timber, (d0 - 0.25, wy + 0.05, 2.02), (d1 + 0.25, wy + 0.05, 2.02), 0.09, 6)
    reb.prim("cube", "Office door", kit.boards("Plank door", (0.15, 0.1, 0.06), width=0.14, grime=0.8), ((d0 + d1) / 2, wy, 0.97), (d1 - d0, 0.06, 1.92))
    reb.prim("cube", "Door backing rock", rock, ((d0 + d1) / 2, wy - 0.25, 1.1), (d1 - d0 + 0.8, 0.4, 2.4))
    reb.prim("cube", "Door recess dark", mat("black"), ((d0 + d1) / 2, wy - 0.04, 1.0), (d1 - d0 + 0.1, 0.02, 2.0))
    for z in (0.4, 1.5):
        reb.prim("cube", "Door ledge", timber, ((d0 + d1) / 2, wy + 0.04, z), (d1 - d0 - 0.06, 0.03, 0.12))
    kit.text("Office paint", "OFFICE", mat("white paint"), ((d0 + d1) / 2, wy + 0.06, 1.25), size=0.13, rot=(math.pi / 2, 0, math.pi))
    under = reb.mat_emit("Candlelight under the door", (1.0, 0.6, 0.25), 3.0)
    reb.prim("cube", "Light under the door", under, ((d0 + d1) / 2, wy + 0.02, 0.012), (d1 - d0 - 0.1, 0.02, 0.02))
    reb.prim("sphere", "Door ring", mat("iron"), (d1 - 0.18, wy + 0.06, 0.95), (0.06, 0.02, 0.06))

    # ---- What they left: tools, a lamp, a lunch pail, a cart; puddles; Hal's drops east.
    kit.rod("Pick haft", timber, (5.6, 15.4, 0.03), (6.1, 14.7, 0.03), 0.02)
    reb.prim("cube", "Pick head", mat("iron"), (5.6, 15.4, 0.04), (0.6, 0.06, 0.05), rot=(0, 0, 0.95))
    kit.rod("Shovel haft", timber, (4.1, 13.6, 0.04), (4.55, 14.8, 0.04), 0.02)
    reb.prim("cube", "Shovel blade", mat("rust"), (4.05, 13.4, 0.03), (0.26, 0.3, 0.02), rot=(0, 0, 0.35))
    reb.prim("cyl", "Carbide lamp", mat("steel"), (5.7, 12.5, 0.07), (0.1, 0.1, 0.14), rot=(math.pi / 2, 0, 0.7), segments=12)
    reb.prim("cyl", "Lunch pail", mat("tin"), (5.0, 16.4, 0.27), (0.22, 0.22, 0.2), segments=14)
    reb.prim("cube", "Helmet", reb.mat_plain("Leather helmet", (0.08, 0.06, 0.04), 0.6), (15.2, 9.6, 0.08), (0.28, 0.24, 0.14), rot=(0.3, 0.2, 0.5), bevel=0.06)
    cart = kit.box("Cart in the tunnel", rust, (13.6, 8.6, 0.18), (1.1, 0.8, 0.6), bevel=0.03)
    reb.wall(cart)
    reb.mask(cart)
    for dx in (-0.38, 0.38):
        for dy in (-0.3, 0.3):
            reb.prim("cyl", "Cart wheel", mat("iron"), (13.6 + dx, 8.6 + dy, 0.17), (0.34, 0.34, 0.05), rot=(math.pi / 2, 0, 0), segments=12)
    reb.prim("cube", "Cart ore", mat("rock"), (13.6, 8.6, 0.73), (0.95, 0.65, 0.1))
    for k, (x, y, r) in enumerate(((5.2, 17.6, 0.5), (5.0, 14.2, 0.4), (9.2, 8.8, 0.45), (13.2, 8.4, 0.6), (17.6, 8.9, 0.4))):
        kit.splat(f"Puddle {k}", puddle, (x, y, 0.004), r, seed=30 + k, stretch=(0.9, 1.6) if k < 2 else (1.6, 0.9), lumps=0.4)
    pts = []
    for (ax, ay), (bx, by) in zip([(5.3, 19.0), (5.3, 12.6), (6.2, 10.0), (9.0, 8.9)], [(5.3, 12.6), (6.2, 10.0), (9.0, 8.9), (19.0, 8.9)]):
        n = int(math.hypot(bx - ax, by - ay) / 0.7)
        for i in range(n):
            if rng.random() < 0.35:
                continue
            t = (i + rng.uniform(0, 0.6)) / max(1, n)
            pts.append((ax + (bx - ax) * t + rng.uniform(-0.08, 0.08), ay + (by - ay) * t + rng.uniform(-0.08, 0.08)))
    drips("Hal's drops", mat("old blood"), pts, rng, r=(0.015, 0.035))
    kit.splat("Hand on a post", mat("old blood"), (9.0, 7.42, 1.0), 0.05, rot=(math.pi / 2, 0, 0.1), seed=6)
    reb.point("Fill, west leg", (5.0, 15.5, 1.8), 12, (0.7, 0.6, 0.5), 1.5)
    reb.point("Fill, east leg", (13.0, 8.6, 1.8), 12, (0.7, 0.6, 0.5), 1.5)

    # ---- What moves.
    anim = kit.Anim(16)
    for k, (pivot, light, glow) in enumerate(lamps):
        anim.custom(lambda f, pivot=pivot, k=k: setattr(pivot, "rotation_euler", (math.radians(6) * math.sin(anim.phase(f) + k * 0.9), math.radians(3) * math.cos(anim.phase(f) + k * 1.3), 0)))
        anim.flicker(light, glow, depth=0.5 if k == 3 else 0.08, dropouts=3 if k == 3 else 0)
    for (x, y) in ((5.2, 17.6), (13.2, 8.4), (9.2, 8.8)):
        anim.drip((x, y, 2.55), fall=2.5, size=0.015)

    # ---- What the game needs.
    room.door("mine-entrance", (4.0, Y1 - 0.6, 6.0, Y1), arrive=(5.0, 17.6), face=(0, -1))
    room.door("mine-office", (d0, wy + 0.1, d1, wy + 0.7), arrive=((d0 + d1) / 2, 9.4), face=(0, 1))
    room.door("junction", (X1 - 0.6, 7.6, X1, 9.6), arrive=(17.6, 8.0), face=(-1, 0))
    room.check((cx - 0.3, cy + 0.3, cx + 1.0, cy + 1.3), "Someone, wrapped up tight in web against the rock.\nOne boot sticks out. I'm not cutting it open.")
    room.check((d1 + 0.1, wy + 0.1, d1 + 0.9, wy + 0.8), "OFFICE, painted on the planks. There's candlelight under the door.")
    room.check((4.4, 13.2, 6.3, 15.8), "A pick and a shovel, dropped. Whoever worked here ran.")
    room.check((16.8, 7.6, 18.3, 9.6), "Drops of blood along the rails, on toward the workings.\nHal came this way.")
    room.check((12.9, 7.6, 14.4, 9.6), "An ore cart, half full. It's been here years.")
    room.entry = "The lamps are lit. Someone's been down here."
    room.export(anim)


build()
