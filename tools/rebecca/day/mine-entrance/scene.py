"""The mouth of the old Arklay silver mine, a harsh late afternoon.

What it tells: the mine closed long ago, but the quarry still ran its
rails up to it. This week somebody brought the roof of the adit down on
purpose: the blasting wire runs from the rocks back across the yard to a
plunger box behind a boulder, its handle pushed home, a reel of wire and a
hard hat dropped beside it. A board nailed to the timbers says SEALED, DO
NOT ENTER. What they were shutting in shows in the webs: thick sheets of
it in the portal's corners, strands trailing out over the rocks, a bundle
wrapped tight and hung up under the cap. The fall did not close it: a low
gap at the west side is still open into the dark, and Hal's drops of
blood go straight to it, with his hand on the post where he ducked in. One
ore cart stands on the rails, another lies on its side, spilled.

Metres: the floor is x 1.0-15.0, y 2.5-11.0 at z 0. The hillside rises
north of y 2.2. The portal is at x 7.6-10.4: two posts and a cap, the
opening x 8.0-10.0, 2.7 high. The rockfall fills it from x 8.85 east and
spills south to y 4.4; the gap is x 8.0-8.85, 1.2 high. The rails come in
at the west edge at y 7.2 and curve north-east under the fall. The
plunger box is at x 12.2, y 8.9 behind a boulder. The quarry is off the
west edge at y 6.0-8.4.

Moving: dust settling over the fall, grit trickling from the cap beam, the
wrapped bundle turning slowly on its thread.
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

X0, X1, Y0, Y1 = 1.0, 15.0, 2.5, 11.0
FACE_Y = 2.2
PORTAL = (8.0, 10.0, 2.7)   # x0, x1 of the opening, its height
GAP = (8.0, 8.85, 1.2)
PLUNGER = (12.2, 8.9)
RAIL_PATH = [(-6.0, 7.0), (X0, 7.2), (4.0, 7.0), (6.5, 6.0), (8.2, 4.4), (9.0, 2.6), (9.0, -4.0)]


def height(x, y):
    """The yard flat; a cliff then the hillside north; the slope falling away south and east."""
    n = noise.noise(Vector((x * 0.3, y * 0.3, 4)))
    if X0 - 0.4 < x < X1 + 0.4 and FACE_Y < y < Y1 + 0.4:
        return -0.03
    z = 0.0
    if y <= FACE_Y:
        d = FACE_Y - y
        z = 3.1 + d * 0.55 + 0.5 * n + 0.3 * noise.noise(Vector((x * 1.2, y * 1.2, 1)))
        if PORTAL[0] - 0.4 < x < PORTAL[1] + 0.4:
            z = max(z, 3.4)
    if y > Y1 + 0.4:
        z = min(z, -(y - Y1 - 0.4) * 0.9) + 0.4 * n
    if x > X1 + 0.4 and y > FACE_Y:
        z = max(z, (x - X1 - 0.4) * 1.1 + 0.4 * n)
    if x < X0 - 0.4 and y > FACE_Y and not (5.8 < y < 8.6):
        z = max(z, (X0 - 0.4 - x) * 0.8 + 0.4 * n)
    return z


def terrain_with_hole(name, m, xr, yr, hole, step=0.25):
    """reb.terrain, less the quads inside `hole` (x0, y0, x1, y1): the adit's mouth in the cliff."""
    nx, ny = int((xr[1] - xr[0]) / step), int((yr[1] - yr[0]) / step)
    verts, faces = [], []
    for j in range(ny + 1):
        y = yr[0] + (yr[1] - yr[0]) * j / ny
        for i in range(nx + 1):
            x = xr[0] + (xr[1] - xr[0]) * i / nx
            verts.append((x, y, height(x, y)))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            cx = (verts[a][0] + verts[a + 1][0]) / 2
            cy = (verts[a][1] + verts[a + nx + 1][1]) / 2
            if hole[0] < cx < hole[2] and hole[1] < cy < hole[3]:
                continue
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    return reb.mesh_object(name, verts, faces, m)


def dust_material():
    """Pale dust in sheets: a noise fading out at the card's edges (object space, unit card), its offset turned by the Anim."""
    m, nodes, links, bsdf = reb.nodes_material("Dust haze")
    bsdf.inputs["Base Color"].default_value = (0.42, 0.38, 0.32, 1)
    bsdf.inputs["Roughness"].default_value = 1.0
    out = nodes["Material Output"]
    tc = nodes.new("ShaderNodeTexCoord")
    mp = nodes.new("ShaderNodeMapping")
    mp.name = "Drift"
    links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 3
    links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    ramp = reb.ramp(nodes, links, nz.outputs["Fac"], [(0.42, (0, 0, 0)), (0.75, (0.4, 0.4, 0.4))])
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
    fac.use_clamp = True
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


def drips(name, m, pts, rng, r=(0.02, 0.05), z=0.0):
    """Blood drops at points, in one mesh."""
    v, f = [], []
    for x, y in pts:
        kit._stain(v, f, rng, (x, y, z + 0.005), rng.uniform(*r), rng.uniform(0, 6.3), 0.45, (1.0, 1.0), rng.randint(0, 99), points=10, drops=rng.random() < 0.35)
    return reb.mesh_object(name, v, f, m, smooth=False)


def ore_cart(name, m, at, yaw, tipped=False):
    """A side-tipping ore cart on four wheels; tipped lies it over, spilling."""
    parts = [
        reb.prim("cube", "tub", m, (0, 0, 0.62), (1.1, 0.8, 0.6), bevel=0.04),
        reb.prim("cube", "chassis", mat("iron"), (0, 0, 0.27), (1.2, 0.6, 0.1)),
        reb.prim("cube", "load", mat("rock"), (0, 0, 0.9), (0.98, 0.68, 0.08)),
    ]
    for dx in (-0.38, 0.38):
        for dy in (-0.3, 0.3):
            parts.append(reb.prim("cyl", "wheel", mat("iron"), (dx, dy, 0.17), (0.34, 0.34, 0.05), rot=(math.pi / 2, 0, 0), segments=12))
    for dx in (-0.62, 0.62):
        parts.append(reb.prim("cube", "buffer", mat("iron"), (dx, 0, 0.3), (0.06, 0.3, 0.12)))
    for p in parts:
        bpy.ops.object.select_all(action="DESELECT")
        p.select_set(True)
        bpy.context.view_layer.objects.active = p
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob = kit.join(name, parts)
    if tipped:
        ob.rotation_euler = (math.radians(-95), 0, yaw)
        ob.location = (at[0], at[1], 0.42)
    else:
        ob.rotation_euler = (0, 0, yaw)
        ob.location = at
    return ob


def build():
    rng = random.Random(29)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.camera((1.6, 10.4, 3.5), (9.2, 3.0, 1.2), 200, "from the west edge: the rails running in under the fall, the carts, the portal")
    room.camera((14.7, 6.4, 3.6), (6.0, 9.2, 0.6), 200, "from the east side: the plunger box behind its boulder, the wire, the carts, the yard to the track out west")
    room.camera((8.0, 10.9, 2.9), (8.9, 2.5, 1.5), 205, "from the south, straight at the portal: SEALED, the gap into the dark")
    room.camera((8.6, 3.4, 3.6), (10.6, 10.8, 0.0), 200, "from beside the portal looking out: the yard, the rails curving off west, the plunger, the valley")

    timber = reb.mat_wood("Mine timber", (0.13, 0.09, 0.055))
    old_timber = kit.dirtied(timber, 0.8, scale=3)
    yard = reb.mat_surface("Mine yard", [(0.0, (0.06, 0.05, 0.04)), (0.5, (0.13, 0.11, 0.085)), (0.8, (0.19, 0.16, 0.12)), (1.0, (0.11, 0.09, 0.07))], scale=1.4, bump=0.6)
    hill = reb.mat_surface("Hill rock", [(0.0, (0.05, 0.05, 0.045)), (0.4, (0.12, 0.11, 0.1)), (0.75, (0.19, 0.17, 0.15)), (1.0, (0.14, 0.15, 0.08))], scale=0.8, detail=14, bump=1.0)
    rust = mat("rust")
    silk = reb.mat_plain("Silk", (0.7, 0.7, 0.68), 0.6)
    dust_m = dust_material()

    # ---- Ground: the yard, the cliff with the adit cut into it, the hill, the slope away.
    terrain_with_hole("Hillside", hill, (-26, 30), (-16, 30), (PORTAL[0], FACE_Y - 0.6, PORTAL[1], FACE_Y + 0.3))
    # Scree and outcrops on the hill over the portal, breaking up the slope.
    sv, sf = [], []
    for _ in range(70):
        x, y = rng.uniform(-6, 24), rng.uniform(-12, FACE_Y - 0.4)
        if PORTAL[0] - 1.0 < x < PORTAL[1] + 1.0 and y > FACE_Y - 2.0:
            continue
        if rng.random() < 0.35:
            x, y = rng.uniform(X1 + 1.0, 24), rng.uniform(FACE_Y, Y1 + 4)
        reb.boulder(rng, (x, y, height(x, y) - 0.1), rng.uniform(0.25, 1.1) if rng.random() < 0.3 else rng.uniform(0.1, 0.3), sv, sf)
    reb.mesh_object("Scree on the hill", sv, sf, kit.dirtied(mat("rock"), 0.4))
    # The gap's dark: the adit black behind the rocks, low on the west side.
    reb.prim("cube", "Dark of the gap", mat("black"), ((GAP[0] + GAP[1]) / 2, FACE_Y - 0.15, GAP[2] / 2), (GAP[1] - GAP[0] + 0.1, 0.05, GAP[2]))
    reb.prim("cube", "Yard", yard, ((X0 + X1) / 2, (FACE_Y + Y1) / 2 + 0.1, -0.04), (X1 - X0 + 0.8, Y1 - FACE_Y + 0.6, 0.08))
    kit.path_strip("Track in", mat("dirt"), [(-6.0, 7.2), (X0, 7.2), (4.0, 7.0), (6.5, 6.0)], lambda x, y: max(0.0, height(x, y)), width=1.0, lift=0.004)
    # The adit behind: rock all round, its floor, timber sets, black beyond.
    kit.tunnel("Adit", mat("wet rock"), [(9.0, FACE_Y + 0.25), (9.0, -2.0), (8.6, -7.0), (7.4, -12.0)], width=2.5, height=2.75, rough=0.12, seed=3, floor_m=mat("mud"))
    for y in (1.2, -0.8, -2.8):
        for x in (7.95, 10.05):
            kit.rod("Adit post", old_timber, (x, y, 0), (x, y, 2.4), 0.11, 6)
        kit.rod("Adit cap", old_timber, (7.85, y, 2.45), (10.15, y, 2.45), 0.12, 6)
    reb.prim("cube", "The dark", mat("black"), (8.4, -11.0, 1.4), (4.0, 0.2, 3.5))
    reb.prim("cube", "Rock over the adit", mat("wet rock"), (9.0, FACE_Y - 0.65, 3.04), (3.6, 1.1, 0.68))
    reb.prim("cube", "Rock lintel over the portal", hill, (9.0, FACE_Y + 0.02, 3.6), (PORTAL[1] - PORTAL[0] + 1.4, 0.3, 0.9))

    # ---- The portal: two great posts and a cap, lagging over, the boards nailed on.
    p0, p1, ph = PORTAL
    for x in (p0 - 0.15, p1 + 0.15):
        post = kit.rod("Portal post", old_timber, (x, FACE_Y + 0.15, 0), (x, FACE_Y + 0.15, ph + 0.15), 0.17, 8)
        reb.wall(reb.prim("cube", "Post footprint", None, (x, FACE_Y + 0.25, 0.5), (0.36, 0.36, 1.0))).hide_render = True
        reb.mask(post)
    reb.prim("cube", "Portal cap", old_timber, ((p0 + p1) / 2, FACE_Y + 0.15, ph + 0.3), (p1 - p0 + 1.0, 0.4, 0.34))
    for k in range(8):
        x = p0 - 0.3 + k * 0.38
        reb.prim("cube", "Lagging", old_timber, (x, FACE_Y - 0.1, ph + 0.55), (0.34, 0.9, 0.08), rot=(0.08, 0, rng.uniform(-0.04, 0.04)))
    reb.prim("cube", "Name board", reb.mat_plain("Board", (0.2, 0.16, 0.1), 0.8), ((p0 + p1) / 2, FACE_Y + 0.37, ph + 0.33), (1.9, 0.04, 0.26))
    kit.text("Name words", "ARKLAY SILVER  ADIT 2", reb.mat_plain("Faded white", (0.45, 0.43, 0.38), 0.7), ((p0 + p1) / 2, FACE_Y + 0.395, ph + 0.33), size=0.13, rot=(math.pi / 2, 0, math.pi))
    reb.prim("cube", "Sealed board", mat("white paint"), (11.5, FACE_Y + 0.08, 1.7), (1.0, 0.03, 0.55), rot=(0, 0.06, 0))
    kit.text("Sealed words", "SEALED\nDO NOT ENTER", mat("red paint"), (11.5, FACE_Y + 0.1, 1.71), size=0.12, rot=(math.pi / 2, 0.06, math.pi))
    for x in (11.1, 11.9):
        reb.prim("cyl", "Nail", mat("iron"), (x, FACE_Y + 0.1, 1.9), (0.02, 0.02, 0.02), rot=(math.pi / 2, 0, 0), segments=6)
    kit.splat("Hand on the post", mat("old blood"), (p0 - 0.15 + 0.12, FACE_Y + 0.29, 1.05), 0.06, rot=(math.pi / 2, 0, -0.6), seed=4, lumps=0.5)

    # ---- The rockfall: filling the mouth from the east side, spilling into the yard; the gap west.
    rv, rf = [], []
    for _ in range(46):
        x = rng.uniform(GAP[1] + 0.1, p1 + 0.3)
        y = rng.uniform(FACE_Y - 1.2, FACE_Y + 1.0)
        z = rng.uniform(0.0, 2.5) * (1.0 - max(0.0, y - FACE_Y) / 1.4)
        reb.boulder(rng, (x, y, max(0.0, z)), rng.uniform(0.3, 0.65), rv, rf)
    for _ in range(14):
        x = rng.uniform(p0 + 0.05, GAP[1])
        y = rng.uniform(FACE_Y - 1.0, FACE_Y + 0.4)
        reb.boulder(rng, (x, y, rng.uniform(GAP[2] + 0.4, 2.5)), rng.uniform(0.25, 0.45), rv, rf)
    for _ in range(28):
        x = rng.uniform(GAP[1] - 0.1, p1 + 1.2)
        y = rng.uniform(FACE_Y + 0.6, 4.3)
        reb.boulder(rng, (x, y, 0.0), rng.uniform(0.15, 0.45), rv, rf, squash=0.7)
    for (x, y, r) in ((7.6, 3.6, 0.3), (11.4, 4.6, 0.35), (10.5, 5.1, 0.25), (6.9, 4.0, 0.2)):
        reb.boulder(rng, (x, y, 0.0), r, rv, rf, squash=0.7)
    reb.mesh_object("Rockfall", rv, rf, kit.dirtied(mat("rock"), 0.5))
    reb.wall(reb.prim("cube", "Rockfall footprint", None, ((GAP[1] + p1 + 1.0) / 2, (FACE_Y + 4.3) / 2, 0.5), (p1 + 1.0 - GAP[1], 4.3 - FACE_Y, 1.0))).hide_render = True
    gv, gf = [], []
    for _ in range(200):
        x, y = rng.uniform(6.5, 12.5), rng.uniform(FACE_Y + 0.4, 6.0)
        s = rng.uniform(0.02, 0.07)
        reb.box(gv, gf, (x, y, s * 0.3), (s, s, s * 0.6), rng.uniform(0, 3))
    reb.mesh_object("Grit", gv, gf, mat("rock"), smooth=False)
    kit.splat("Dust over the yard", reb.mat_plain("Pale dust", (0.16, 0.145, 0.12), 0.95), (9.6, 4.6, 0.0), 2.0, seed=6, stretch=(1.5, 0.8), lumps=0.5)
    # The webs: sheets in the corners, strands over the rocks, the wrapped bundle under the cap.
    kit.web("Web, west corner", (p0 + 0.02, FACE_Y + 0.05, ph - 0.02), 0.75, (1, -1))
    kit.web("Web, east corner", (p1 - 0.02, FACE_Y + 0.05, ph - 0.02), 0.85, (-1, -1))
    kit.web("Web, low in the gap", (p0 + 0.02, FACE_Y - 0.3, GAP[2]), 0.5, (1, -1))
    strands = []
    for k in range(14):
        a = Vector((rng.uniform(p0, p1), FACE_Y + rng.uniform(-0.2, 0.2), rng.uniform(1.5, ph)))
        b = Vector((rng.uniform(p0 - 0.6, p1 + 1.2), rng.uniform(FACE_Y + 0.5, 4.0), rng.uniform(0.0, 0.8)))
        strands.append(kit.rod("Strand", silk, a, b, 0.004, 3))
    kit.join("Strands", strands)
    bundle_pivot = reb.prim("sphere", "Bundle thread top", silk, (9.6, FACE_Y + 0.05, ph - 0.05), (0.02, 0.02, 0.02))
    thread = kit.rod("Bundle thread", silk, (0, 0, 0), (0, 0, -0.45), 0.006, 3)
    bundle = reb.prim("sphere", "Wrapped bundle", reb.mat_surface("Cocoon", [(0.0, (0.45, 0.44, 0.4)), (0.7, (0.62, 0.6, 0.56)), (1.0, (0.3, 0.12, 0.08))], scale=16, bump=0.8), (0, 0, -0.8), (0.28, 0.24, 0.7), segments=12)
    thread.parent = bundle_pivot
    bundle.parent = bundle_pivot

    # ---- The rails in, the carts, the wire back to the plunger.
    rails("Rails", RAIL_PATH, timber, rust)
    ore_cart("Ore cart", rust, (4.6, 6.95, 0.12), math.atan2(-0.4, 1.0))
    ore_cart("Cart on its side", rust, (11.8, 6.4, 0), 0.5, tipped=True)
    reb.wall(reb.prim("cube", "Cart footprint", None, (4.6, 6.95, 0.5), (1.3, 1.0, 1.0), rot=(0, 0, -0.38))).hide_render = True
    reb.wall(reb.prim("cube", "Tipped cart footprint", None, (11.8, 6.6, 0.5), (1.3, 1.2, 1.0), rot=(0, 0, 0.5))).hide_render = True
    ov, of = [], []
    for _ in range(20):
        reb.boulder(rng, (12.1 + rng.uniform(-0.3, 0.6), 7.1 + rng.uniform(-0.2, 0.5), 0.0), rng.uniform(0.06, 0.16), ov, of, squash=0.6)
    reb.mesh_object("Spilled ore", ov, of, reb.mat_surface("Ore", [(0.0, (0.05, 0.05, 0.06)), (0.6, (0.14, 0.14, 0.16)), (1.0, (0.4, 0.4, 0.42))], scale=12, rough=0.4, bump=0.8))
    wire = [(10.4, 3.9, 0.02), (11.0, 4.9, 0.02), (11.3, 6.0, 0.02), (12.9, 6.9, 0.02), (13.1, 7.9, 0.02), (12.5, 8.75, 0.12)]
    wp = []
    for a, b in zip(wire, wire[1:]):
        for o in (-0.02, 0.02):
            wp.append(kit.rod("Blasting wire", reb.mat_plain("Wire red", (0.35, 0.04, 0.02), 0.5), (a[0] + o, a[1], a[2]), (b[0] + o, b[1], b[2]), 0.008, 4))
    kit.join("Blasting wire", wp)
    px, py = PLUNGER
    box = kit.crate("Plunger box", reb.mat_wood("Plunger box", (0.18, 0.1, 0.05)), (px, py, 0.0), size=(0.32, 0.26, 0.3), rot=0.3)
    reb.wall(reb.prim("cube", "Plunger footprint", None, (px, py, 0.5), (0.5, 0.45, 1.0))).hide_render = True
    kit.rod("Plunger rod", mat("steel"), (px, py, 0.3), (px, py, 0.36), 0.015, 6)
    kit.rod("T-handle", mat("black"), (px - 0.15 * math.cos(0.3), py - 0.15 * math.sin(0.3), 0.37), (px + 0.15 * math.cos(0.3), py + 0.15 * math.sin(0.3), 0.37), 0.02, 6)
    kit.text("Plunger words", "DANGER", mat("yellow paint"), (px - 0.04, py + 0.135, 0.18), size=0.05, rot=(math.pi / 2, 0, math.pi + 0.3))
    reb.prim("cyl", "Wire reel", rust, (px - 0.6, py + 0.4, 0.13), (0.26, 0.26, 0.22), rot=(math.pi / 2, 0, 1.1), segments=14)
    reb.prim("sphere", "Dropped hard hat", mat("white paint"), (px + 0.5, py + 0.45, 0.1), (0.28, 0.25, 0.2), rot=(0.5, -0.2, 0))
    rv, rf = [], []
    reb.boulder(rng, (px - 0.2, py - 0.75, 0.0), 0.7, rv, rf)
    for (x, y, r) in ((0.4, 3.4, 0.9), (14.9, 3.4, 1.1), (15.6, 6.6, 0.8), (0.5, 10.8, 0.7), (6.0, 11.4, 0.6)):
        reb.boulder(rng, (x, y, height(x, y)), r, rv, rf)
    reb.mesh_object("Boulders", rv, rf, mat("rock"))
    reb.wall(reb.prim("cube", "Shelter boulder footprint", None, (px - 0.2, py - 0.75, 0.5), (1.5, 1.2, 1.0))).hide_render = True
    # Props stacked for the timbering that never happened; a rusted bucket; Hal's drops to the gap.
    for k in range(7):
        reb.prim("cyl", "Prop", timber, (13.0, 4.3 + (k % 4) * 0.3, 0.14 + (k // 4) * 0.27), (0.26, 0.26, 2.6), rot=(0, math.pi / 2, 0.02 * k), segments=8)
    reb.wall(reb.prim("cube", "Props footprint", None, (13.0, 4.75, 0.5), (2.6, 1.3, 1.0))).hide_render = True
    reb.prim("cyl", "Bucket", rust, (6.2, 3.3, 0.18), (0.3, 0.3, 0.36), rot=(0.3, 0, 0), segments=12)
    drips("Hal's drops", mat("old blood"), [(X0 + 0.2 + k * 0.55 + rng.uniform(-0.1, 0.1), 7.7 - k * 0.32 + rng.uniform(-0.08, 0.08)) for k in range(14)], rng, r=(0.015, 0.035))
    kit.splat("Where he knelt", mat("old blood"), (8.45, FACE_Y + 0.55, 0.0), 0.12, seed=8, lumps=0.5)

    # ---- Round it: spruces on the hill and down the slope, dead grass at the yard's edge.
    def keep_out(x, y):
        return (X0 - 2 < x < X1 + 1.5 and FACE_Y - 2.5 < y < Y1 + 1.5) or (-7.0 < x < X0 and 5.5 < y < 9.0) or (-6.0 < x < X1 + 0.6 and y > Y1 - 1.0)
    kit.forest(rng, height, keep_out, (-24, -16, 30, 26), count=90, ferns=20, needles=500)
    edge = kit.meadow(rng, 700, lambda r: (r.uniform(X0 - 1, X1 + 1), r.choice((r.uniform(Y1 - 0.6, Y1 + 0.6), r.uniform(FACE_Y + 0.05, FACE_Y + 0.4)))), height, mat("dead grass"))
    kit.meadow(rng, 350, lambda r: (r.uniform(X0, X1), r.uniform(4.5, Y1)), height, mat("dead grass"))
    rv, rf = [], []
    for _ in range(18):
        x, y = rng.uniform(X0 + 0.5, X1 - 0.5), rng.uniform(5.0, Y1 - 0.3)
        if abs(y - 7.0) < 1.0 and x < 7.0:
            continue
        reb.boulder(rng, (x, y, 0.0), rng.uniform(0.08, 0.22), rv, rf, squash=0.6)
    reb.mesh_object("Stones", rv, rf, mat("rock"))
    kit.crow("Crow on the cap", (8.5, FACE_Y + 0.1, ph + 0.47), heading=-1.6)

    # ---- Dust settling over the fall.
    dust = []
    for k, (x, y, z, w, h) in enumerate(((9.6, 3.7, 1.3, 4.5, 2.4), (10.4, 4.5, 0.9, 3.5, 1.6), (9.4, 3.2, 1.8, 2.6, 1.8))):
        ob = reb.mesh_object(f"Dust {k}", [(-0.5, 0, -0.5), (0.5, 0, -0.5), (0.5, 0, 0.5), (-0.5, 0, 0.5)], [(0, 1, 2, 3)], dust_m, smooth=False)
        ob.location = (x, y, z)
        ob.scale = (w, 1, h)
        ob.rotation_euler = (0, 0, 0.15 * k)
        ob.visible_shadow = False
        dust.append(ob)
    grit = [reb.prim("sphere", f"Falling grit {k}", mat("rock"), (8.6 + k * 0.45, FACE_Y + 0.2, ph + 0.1), (0.035, 0.035, 0.035), segments=6) for k in range(4)]

    # ---- Light: the low sun in the south-west on the face.
    sun = kit.time_light("afternoon", sun_heading=212, sun_energy=4.6)
    # Late and harsh: the sun low in the south-west on the portal, amber, the sky dimmer so the shadows go deep.
    sun.rotation_euler[0] = math.radians(90 - 26)
    sun.data.color = (1.0, 0.7, 0.42)
    bpy.context.scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.55
    kit.vista(rng, (8.0, Y1 + 4), (0.2, 1.0), below=-80.0)

    anim = kit.Anim(16)
    mp = dust_m.node_tree.nodes["Drift"]

    def settle_dust(k):
        a = anim.phase(k)
        mp.inputs["Location"].default_value = (0.3 * math.cos(a), 0.0, 0.6 * math.sin(a))
        for i, g in enumerate(grit):
            t = ((k + i * 4) % anim.frames) / anim.frames
            g.location = (8.6 + i * 0.45, FACE_Y + 0.25 + 0.15 * t, ph + 0.1 - 2.4 * t * t)
            g.hide_render = t > 0.9
    anim.custom(settle_dust)
    anim.custom(lambda k: setattr(bundle_pivot, "rotation_euler", (math.radians(2) * math.sin(anim.phase(k)), 0, 0.5 * math.sin(anim.phase(k)))))
    anim.sway(edge, amount=0.04)

    # ---- What the game needs.
    room.door("quarry", (X0, 6.0, X0 + 0.6, 8.4), arrive=(2.5, 7.4), face=(1, 0))
    room.door("tunnel", (p0 - 0.1, Y0, GAP[1] + 0.05, Y0 + 0.8), arrive=(8.4, 4.6), face=(0, 1), walk=False)
    room.check((p0 - 1.0, Y0, p0 - 0.2, Y0 + 0.9), "A gap under the rocks, into the dark. Webs over it.\nThere's blood on the post. Someone squeezed through.")
    room.check((GAP[1], Y0, p1 + 1.0, 4.6), "The roof's been brought down across the mouth. On purpose:\nthere's a blasting wire running out of the rocks.")
    room.check((px - 0.7, py - 0.2, px + 0.8, Y1), "A blasting plunger, pushed home. Whoever fired it\ndropped their hard hat and ran.")
    room.check((11.0, Y0, 12.2, 3.3), "SEALED. DO NOT ENTER.\nWhat were they keeping in?")
    room.check((11.0, 5.6, 12.8, 7.6), "An ore cart, tipped over. Silver ore, dull and grey.")
    room.entry = "Webs. Thick ones."
    room.export(anim)


build()
