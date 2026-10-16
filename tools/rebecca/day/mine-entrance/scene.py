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

The ore track: the way west to the quarry is part of the room now. West of
the yard a ravine cuts down through the hill, nine metres deep, a stream
in the bottom of it, and the rails cross it on a timber trestle, the deck
2.4 m wide and about 4.4 m of it hers before the far rim. A rope rail runs
along its north side on posts, one post leaning out. Halfway over, a
second ore cart lies on its side on the deck's south edge, half over the
drop, its ore spilled down into the ravine, and web is strung from it in a
sheet that hangs down over the edge to the bents below: whatever spins
those has been out this way. She has to squeeze past it on the north
side. A loose deck plank hangs under the south edge by one nail.

Metres: the scene is built in its own coordinates and shifted x +4.0 at
export. The floor is x -3.35-15, y 2.5-11; west of x 1 only the trestle's
deck is floor, y 6.0-8.4. The ravine's lips are at x 0.6 and -4.4. The
tipped cart lies at x -1.0-0.2, y 7.4-8.4.

Moving: dust settling over the fall, grit trickling from the cap beam, the
wrapped bundle turning slowly on its thread, the web sheet stirring in the
draught up the ravine, the loose plank swinging, the stream.
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
RAIL_PATH = [(-12.0, 7.0), (X0, 7.2), (4.0, 7.0), (6.5, 6.0), (8.2, 4.4), (9.0, 2.6), (9.0, -4.0)]
SHIFT = (4.0, 0.0)
X_W = -3.35   # the floor's west end, the trestle's far end on the floor (0.65 m in the game)
DECK = (-4.9, 0.9, 6.0, 8.4)   # the trestle's deck x0, x1, y0, y1; walkable from X_W to X0
RAVINE = (-4.4, 0.6, -9.0)   # its west lip, east lip, depth
TIPPED = (-0.4, 7.5, 0.15)   # the tipped cart on the deck: x, y, heading
TRESTLE_CAMS = [(-4.0, 12.2, 3.2), (2.2, 3.3, 3.6)]


def height(x, y):
    """The ravine west of the yard cut into the ground either side of it: steep walls off
    each lip, a stream bed nine metres down, shallowing as it climbs into the hill."""
    w, e, depth = RAVINE
    w += 0.3 * noise.noise(Vector((0.0, y * 0.35, 5)))
    e -= 0.25 * (1 + noise.noise(Vector((1.0, y * 0.4, 5))))
    if not w < x < e:
        return ground(x, y)
    t = (x - w) / (e - w)
    edge = min(1.0, min(t, 1 - t) / 0.3) ** 0.7
    base = ground(w - 0.01, y) * (1 - t) + ground(e + 0.01, y) * t
    bed = min(-2.5, depth + max(0.0, FACE_Y - y) * 0.3)
    return base + (bed + 0.4 * noise.noise(Vector((x * 0.9, y * 0.5, 2)))) * edge


def ground(x, y):
    """The yard flat; a cliff then the hillside north; the slope falling away south and east;
    the quarry's side west of the ravine."""
    n = noise.noise(Vector((x * 0.3, y * 0.3, 4)))
    if X0 - 0.4 < x < X1 + 0.4 and FACE_Y < y < Y1 + 0.4:
        return -0.03
    if x <= RAVINE[0] and y > FACE_Y:
        if 5.6 < y < 8.8:
            return 0.03 * n - 0.03
        return 0.4 * n + max(0.0, RAVINE[0] - 1.5 - x) * 0.4 + max(0.0, y - Y1 - 0.4) * -0.6
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
    return z


def beam(verts, faces, a, b, r):
    """A square timber from a to b, into the given lists."""
    a, b = Vector(a), Vector(b)
    q = (b - a).to_track_quat("Z", "Y")
    k = len(verts)
    for end in (a, b):
        for s in range(4):
            t = math.pi / 2 * s + math.pi / 4
            verts.append(tuple(end + q @ Vector((math.cos(t) * r, math.sin(t) * r, 0))))
    for s in range(4):
        faces.append((k + s, k + (s + 1) % 4, k + 4 + (s + 1) % 4, k + 4 + s))
    faces += [(k, k + 1, k + 2, k + 3), (k + 7, k + 6, k + 5, k + 4)]


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
    room = kit.Room(bounds=(X_W, Y0, X1, Y1), shift=SHIFT)
    room.ground("earth")  # the packed dirt yard
    room.floor((X_W, DECK[2], X0, DECK[3]), "boards")  # the trestle
    room.camera((1.6, 10.4, 3.5), (9.2, 3.0, 1.2), 200, "from the west edge: the rails running in under the fall, the carts, the portal")
    room.camera((14.7, 6.4, 3.6), (6.0, 9.2, 0.6), 200, "from the east side: the plunger box behind its boulder, the wire, the carts, the yard to the track out west")
    room.camera((8.0, 10.9, 2.9), (8.9, 2.5, 1.5), 205, "from the south, straight at the portal: SEALED, the gap into the dark")
    room.camera((8.6, 3.4, 3.6), (10.6, 10.8, 0.0), 200, "from beside the portal looking out: the yard, the rails curving off west, the plunger, the valley")
    room.camera(TRESTLE_CAMS[0], (0.0, 7.0, -2.8), 200, "back over the trestle from the quarry side: the tipped cart and its web, the ravine, the yard and the portal beyond")
    room.camera(TRESTLE_CAMS[1], (-3.2, 9.6, -3.5), 200, "out over the trestle from the yard: the rope rail, the tipped cart, the ravine falling away, the quarry track beyond")

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
    reb.prim("cube", "Dark of the gap", mat("black"), ((GAP[0] + GAP[1]) / 2, FACE_Y - 0.9, GAP[2] / 2), (GAP[1] - GAP[0] + 0.1, 1.5, GAP[2]))
    reb.prim("cube", "Yard", yard, ((X0 + X1) / 2, (FACE_Y + Y1) / 2 + 0.1, -0.04), (X1 - X0 + 0.8, Y1 - FACE_Y + 0.6, 0.08))
    kit.path_strip("Track in", mat("dirt"), [(0.62, 7.2), (X0, 7.2), (4.0, 7.0), (6.5, 6.0)], lambda x, y: max(0.0, height(x, y)), width=1.0, lift=0.004)
    kit.path_strip("Track on to the quarry", mat("dirt"), [(-30.0, 6.4), (-12.0, 7.0), (-4.45, 7.1)], height, width=1.0, lift=0.006)
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
    # Freshly broken stone, angular, each kept clear of the gap by its own size.
    for _ in range(52):
        r = rng.uniform(0.3, 0.65)
        x = rng.uniform(GAP[1] + 0.1 + r * 1.2, p1 + 0.3)
        y = rng.uniform(FACE_Y - 1.2, FACE_Y + 1.0)
        z = rng.uniform(0.0, 2.5) * (1.0 - max(0.0, y - FACE_Y) / 1.4)
        reb.boulder(rng, (x, y, max(0.0, z)), r, rv, rf, subdivisions=1)
    for _ in range(14):
        x = rng.uniform(p0 + 0.05, GAP[1])
        y = rng.uniform(FACE_Y - 1.0, FACE_Y + 0.4)
        reb.boulder(rng, (x, y, rng.uniform(GAP[2] + 0.5, 2.5)), rng.uniform(0.25, 0.4), rv, rf, subdivisions=1)
    for _ in range(34):
        r = rng.uniform(0.1, 0.45)
        x = rng.uniform(GAP[1] + 0.15 + r * 1.2, p1 + 1.2)
        y = rng.uniform(FACE_Y + 0.6, 4.3)
        reb.boulder(rng, (x, y, 0.0), r, rv, rf, squash=0.7, subdivisions=1)
    for (x, y, r) in ((7.6, 3.6, 0.3), (11.4, 4.6, 0.35), (10.5, 5.1, 0.25), (6.9, 4.0, 0.2)):
        reb.boulder(rng, (x, y, 0.0), r, rv, rf, squash=0.7, subdivisions=1)
    rockfall = reb.mesh_object("Rockfall", rv, rf, kit.dirtied(mat("rock"), 0.8), smooth=False)
    # Once she blasts it (day/events.ts "blast"): the fall blown out into the
    # yard as low rubble, the adit open and black behind the portal.
    brng = random.Random(77)
    bv, bf = [], []
    for _ in range(70):
        r = brng.uniform(0.08, 0.3)
        reb.boulder(brng, (brng.uniform(p0 - 0.6, p1 + 1.6), brng.uniform(FACE_Y + 0.2, 4.4), 0.0), r, bv, bf, squash=0.6, subdivisions=1)
    blasted = reb.mesh_object("Blasted rubble", bv, bf, kit.dirtied(mat("rock"), 0.8), smooth=False)
    adit = reb.prim("cube", "Dark of the adit", mat("black"), ((p0 + p1) / 2, FACE_Y - 1.0, ph / 2), (p1 - p0, 1.6, ph))
    soot = kit.splat("Blast soot", reb.mat_plain("Soot", (0.02, 0.018, 0.016), 0.95), ((p0 + p1) / 2, FACE_Y + 1.6, 0.0), 1.8, seed=21, stretch=(1.4, 0.8), lumps=0.6)
    after_blast = (blasted, adit, soot)
    for ob in after_blast:
        ob.hide_render = True
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
    gap_web = kit.web("Web, low in the gap", (p0 + 0.02, FACE_Y - 0.3, GAP[2]), 0.5, (1, -1))
    strands = []
    for k in range(14):
        a = Vector((rng.uniform(p0, p1), FACE_Y + rng.uniform(-0.2, 0.2), rng.uniform(1.5, ph)))
        b = Vector((rng.uniform(p0 - 0.6, p1 + 1.2), rng.uniform(FACE_Y + 0.5, 4.0), rng.uniform(0.0, 0.8)))
        strands.append(kit.rod("Strand", silk, a, b, 0.004, 3))
    strands = kit.join("Strands", strands)

    def blast(done):
        for ob in (rockfall, gap_web, strands):
            ob.hide_render = done
        for ob in after_blast:
            ob.hide_render = not done
    room.state("blast", blast)
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
    for (x, y, r) in ((1.0, 3.2, 0.8), (14.9, 3.4, 1.1), (15.6, 6.6, 0.8), (1.1, 11.3, 0.6), (6.0, 11.4, 0.6)):
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

    # ---- The trestle over the ravine: deck, stringers, bents down to the stream, a rope rail
    # on the north side; the tipped cart on the south edge, its web hanging over; a loose plank.
    dx0, dx1, dy0, dy1 = DECK
    tv, tf = [], []
    x = dx0
    while x < dx1:
        w = rng.choice((0.2, 0.22, 0.24))
        y0 = dy0 - 0.15 - (rng.uniform(0.0, 0.25) if rng.random() < 0.3 else 0.0)
        y1 = dy1 + 0.15 - (rng.uniform(0.0, 0.3) if rng.random() < 0.3 else 0.0)
        reb.box(tv, tf, (x + w / 2, (y0 + y1) / 2, -0.04), (w - 0.015, y1 - y0, 0.07), rng.uniform(-0.01, 0.01))
        x += w
    reb.mesh_object("Trestle deck", tv, tf, kit.dirtied(mat("planks"), 0.6, scale=2), smooth=False)
    bv, bf = [], []
    for y in (dy0 + 0.15, (dy0 + dy1) / 2, dy1 - 0.15):
        reb.box(bv, bf, ((dx0 + dx1) / 2, y, -0.22), (dx1 - dx0 + 0.6, 0.22, 0.3))
    for bx in (-4.1, -2.5, -0.9, 0.5):
        reb.box(bv, bf, (bx, (dy0 + dy1) / 2, -0.47), (0.3, dy1 - dy0 + 1.0, 0.28))
        feet = []
        for y, lean in ((dy0 - 0.3, -0.6), (dy0 + 0.6, 0.0), (dy1 - 0.6, 0.0), (dy1 + 0.3, 0.6)):
            foot = (bx, y + lean, height(bx, y + lean) - 0.3)
            beam(bv, bf, (bx, y, -0.5), foot, 0.12)
            feet.append(foot)
        for z in (-2.6, -5.0, -7.4):
            beam(bv, bf, (bx, dy0 - 0.4, z), (bx, dy1 + 0.4, z), 0.07)
        beam(bv, bf, (bx, dy0 - 0.2, -0.7), (bx, dy1 + 0.2, -4.6), 0.06)
        beam(bv, bf, (bx, dy1 + 0.2, -0.7), (bx, dy0 - 0.2, -4.6), 0.06)
    for y in (dy0 - 0.3, dy1 + 0.3):
        beam(bv, bf, (-4.1, y, -3.8), (-2.5, y, -1.2), 0.06)
        beam(bv, bf, (-0.9, y, -1.2), (0.5, y, -3.8), 0.06)
    reb.mesh_object("Trestle timbers", bv, bf, kit.dirtied(timber, 0.7, scale=3), smooth=False)
    # The rope rail on the north side: posts on the deck's edge, one leaning out over the drop.
    rope_pts = []
    for i, px_ in enumerate((-4.6, -3.1, -1.6, -0.1, 0.8)):
        lean_ = -0.35 if i == 2 else 0.0
        top = (px_, dy0 - 0.08 + lean_, 1.05 + lean_ * 0.3)
        kit.rod("Rail post", old_timber, (px_, dy0 - 0.08, -0.1), top, 0.05, 6)
        rope_pts.append(top)
    rope = reb.mat_plain("Rope", (0.22, 0.18, 0.12), 0.9)
    for a, b in zip(rope_pts, rope_pts[1:]):
        prev = Vector(a)
        for j in range(1, 7):
            t = j / 6
            p = Vector(a).lerp(Vector(b), t) + Vector((0, 0, -0.18 * math.sin(math.pi * t)))
            kit.rod("Rope rail", rope, prev, p, 0.012, 4)
            prev = p
    # The loose plank, hanging under the south edge by one nail.
    plank_pivot = reb.prim("sphere", "Loose plank nail", mat("iron"), (-2.0, dy1 + 0.12, -0.08), (0.02, 0.02, 0.02), segments=6)
    plank = reb.prim("cube", "Loose plank", kit.dirtied(mat("planks"), 0.6, scale=2), (0, 0, -0.6), (0.2, 0.05, 1.2), rot=(0, 0, 0))
    plank.parent = plank_pivot
    plank_pivot.rotation_euler = (0.25, 0.1, 0)
    # The tipped cart, its spilled ore down the ravine side, and its web.
    cx, cy, ch = TIPPED
    ore_cart("Cart on the trestle", rust, (cx, cy, 0), ch, tipped=True)
    reb.wall(reb.prim("cube", "Trestle cart footprint", None, (cx, cy + 0.45, 0.5), (1.3, 1.0, 1.0), rot=(0, 0, ch))).hide_render = True
    ov, of = [], []
    for _ in range(26):
        y = rng.uniform(dy1 - 0.1, dy1 + 2.0)
        x = cx + rng.uniform(-1.0, 1.2)
        reb.boulder(rng, (x, y, max(height(x, y), -0.02) if y < dy1 + 0.2 else height(x, y)), rng.uniform(0.06, 0.16), ov, of, squash=0.6)
    reb.mesh_object("Ore spilled into the ravine", ov, of, reb.mat_surface("Ore", [(0.0, (0.05, 0.05, 0.06)), (0.6, (0.14, 0.14, 0.16)), (1.0, (0.4, 0.4, 0.42))], scale=12, rough=0.4, bump=0.8))
    wv, wf = [], []
    cols, rows = 8, 7
    for j in range(rows + 1):
        for i in range(cols + 1):
            u, v = i / cols, j / rows
            wv.append((cx - 0.75 + 1.4 * u + 0.15 * math.sin(v * 3 + u * 5), dy1 + 0.05 + 0.5 * v * v, 0.75 - 2.9 * v - 0.25 * math.sin(math.pi * u)))
    for j in range(rows):
        for i in range(cols):
            if rng.random() < 0.12:
                continue
            a = j * (cols + 1) + i
            wf.append((a, a + 1, a + cols + 2, a + cols + 1))
    veil, nodes, links, vb = reb.nodes_material("Sheet web")
    vb.inputs["Base Color"].default_value = (0.72, 0.72, 0.7, 1)
    vb.inputs["Roughness"].default_value = 0.7
    # Hanging threads: streaks down the sheet, thick at the top, thinning to wisps.
    gen = nodes.new("ShaderNodeTexCoord")
    wave = nodes.new("ShaderNodeTexWave")
    wave.bands_direction = "X"
    wave.inputs["Scale"].default_value = 9.0
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 3.0
    links.new(gen.outputs["Generated"], wave.inputs["Vector"])
    threads = reb.ramp(nodes, links, wave.outputs["Fac"], [(0.55, (0.0, 0.0, 0.0)), (0.85, (0.9, 0.9, 0.9))])
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(gen.outputs["Generated"], sep.inputs["Vector"])
    fade = nodes.new("ShaderNodeMath")
    fade.operation = "MULTIPLY"
    fade.use_clamp = True
    links.new(threads.outputs["Color"], fade.inputs[0])
    links.new(sep.outputs["Z"], fade.inputs[1])
    mix = nodes.new("ShaderNodeMixShader")
    clear = nodes.new("ShaderNodeBsdfTransparent")
    links.new(fade.outputs[0], mix.inputs["Fac"])
    links.new(clear.outputs[0], mix.inputs[1])
    links.new(vb.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], nodes["Material Output"].inputs["Surface"])
    web_sheet = reb.mesh_object("Web over the edge", wv, wf, veil, smooth=True)
    web_sheet.visible_shadow = False
    web_rest = [Vector(v.co) for v in web_sheet.data.vertices]
    kit.web("Web in the cart", (cx - 0.5, cy + 0.9, 0.78), 0.55, (1, -1))
    for k in range(9):
        a = Vector((cx + rng.uniform(-0.6, 0.6), cy + rng.uniform(0.5, 0.95), rng.uniform(0.2, 0.8)))
        b = Vector((rng.choice((-0.9, 0.5)) + rng.uniform(-0.1, 0.1), dy1 + 0.3, rng.uniform(-4.5, -1.0)))
        kit.rod("Web strand", silk, a, b, 0.004, 3)
    # The stream in the ravine's bed, rocks along it.
    water = mat("water")
    kit.path_strip("Stream", water, [(-1.8, y) for y in (-8.0, -2.0, 2.0, 5.0, 8.0, 12.0, 18.0, 26.0)], lambda x, y: height(x, y) + 0.12, width=0.55, wobble=0.3)
    sv, sf = [], []
    for _ in range(40):
        y = rng.uniform(-4.0, 22.0)
        x = -1.8 + rng.uniform(-1.3, 1.3)
        reb.boulder(rng, (x, y, height(x, y)), rng.uniform(0.2, 0.6), sv, sf)
    for _ in range(50):
        y = rng.uniform(-2.0, 18.0)
        side = rng.choice((0, 1))
        x = RAVINE[side] + (rng.uniform(0.3, 1.4) if side == 0 else -rng.uniform(0.4, 1.4))
        reb.boulder(rng, (x, y, height(x, y)), rng.uniform(0.25, 0.7), sv, sf)
    reb.mesh_object("Ravine rocks", sv, sf, kit.dirtied(mat("wet rock"), 0.4))

    # ---- Round it: spruces on the hill and down the slope, dead grass at the yard's edge.
    def keep_out(x, y):
        if any(math.hypot(x - c[0], y - c[1]) < 4.0 for c in TRESTLE_CAMS) or (RAVINE[0] - 0.5 < x < RAVINE[1] + 0.3 and 0.5 < y < 14.0):
            return True
        return (X0 - 2 < x < X1 + 1.5 and FACE_Y - 2.5 < y < Y1 + 1.5) or (-14.0 < x < X0 and 4.6 < y < 9.8) or (-6.0 < x < X1 + 0.6 and y > Y1 - 1.0)
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
    anim.swing(plank_pivot, axis=0, degrees=10)
    anim.ripple(water)

    def billow(k):
        ph = anim.phase(k)
        for v, rest in zip(web_sheet.data.vertices, web_rest):
            d = max(0.0, 0.75 - rest.z) / 2.9
            v.co = (rest.x + 0.05 * d * math.sin(ph + rest.z), rest.y + 0.22 * d * (0.6 + math.sin(ph + rest.x * 2.0)), rest.z)
        web_sheet.data.update()
    anim.custom(billow)

    # ---- What the game needs.
    room.void((X_W, Y0, X0, DECK[2]))
    room.void((X_W, DECK[3], X0, Y1))
    room.door("quarry", (X_W, DECK[2], X_W + 0.6, DECK[3]), arrive=(-1.9, 6.9), face=(1, 0))
    room.door("tunnel", (p0 - 0.1, Y0, GAP[1] + 0.05, Y0 + 0.8), arrive=(8.4, 4.6), face=(0, 1), walk=False)
    room.check((p0 - 1.0, Y0, p0 - 0.2, Y0 + 0.9), "A gap under the rocks, into the dark. Webs over it.\nThere's blood on the post. Someone squeezed through.")
    room.spot("blast", (GAP[1], Y0, p1 + 1.0, 4.6))  # day/events.ts says what she sees and does here
    room.check((px - 0.7, py - 0.2, px + 0.8, Y1), "A blasting plunger, pushed home. Whoever fired it\ndropped their hard hat and ran.")
    room.check((11.0, Y0, 12.2, 3.3), "SEALED. DO NOT ENTER.\nWhat were they keeping in?")
    room.check((11.0, 5.6, 12.8, 7.6), "An ore cart, tipped over. Silver ore, dull and grey.")
    room.check((cx - 0.9, DECK[2] + 0.6, cx + 0.7, cy - 0.05), "Another cart, on its side on the trestle.\nThe web runs from it right down into the ravine.")
    room.check((X_W + 0.7, DECK[2], -1.6, DECK[2] + 0.6), "The trestle creaks. It's a long way down.")
    room.entry = "Webs. Thick ones."
    room.export(anim)


build()
