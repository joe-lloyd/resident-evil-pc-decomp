"""The valley path at the foot of pylon 7, dusk.

What it tells: she comes down the pylon's ladder into the valley forest,
where a hikers' path runs under the gondola line and forks three ways:
west toward the smoke where Bravo's helicopter came down, east to the
gondola's lower station, south to the creek. The dogs came through here.
Their tracks cross the path from the east, a pack of them, and run south.
A hiker sat down against a spruce by the fork and did not get up: his
throat is torn out, his pack is split, and the flies have found him. On a
snapped branch at the west fork hangs a scrap of green sleeve with a
S.T.A.R.S. patch on it: one of Bravo came this way in the night, toward the
crash or from it, and caught on the branch running.

Metres: the floor is x 1-19, y 1-17, forest floor and needles. The pylon's
tower stands over the north edge, its legs at x 6.3 and 12.7, y 3.0; its
ladder comes down to x 9.5, y 2.1. The path runs south from the ladder to
the fork at x 10, y 9, then west off the floor at y 8-10 (to the crash),
east off it at y 8-10 (to the lower station) and south off it at x 9-11
(to the creek). The hiker sits against the spruce at x 16.5, y 11.0. The
patch hangs from a branch at x 4.4, y 7.6.

Moving: mist drifting between the trunks, fireflies, flies over the hiker,
the patch turning on its branch, a crow on the pylon's leg, ferns in the
wind.
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

X0, Y0, X1, Y1 = 1.0, 1.0, 19.0, 17.0
TOWER = (9.5, 0.4)
LADDER_FOOT = (9.5, 2.1)
FORK = (10.0, 9.0)
HIKER_TREE = (16.5, 11.0)
PATCH = (4.4, 7.6)
CAMS = [((0.4, 0.4, 3.6), (11.0, 10.0, 0.0)), ((19.6, 0.4, 3.6), (8.0, 10.0, 0.0)), ((0.4, 17.6, 3.6), (11.0, 7.0, 0.2)),
        ((19.6, 17.6, 3.6), (8.0, 8.0, 0.2)), ((10.0, 17.9, 3.8), (9.8, 4.0, 1.2))]
INNER_TREES = [(17.8, 6.2, 18), (2.0, 11.6, 16), (6.4, 15.9, 18), (HIKER_TREE[0], HIKER_TREE[1], 20)]


def height(x, y):
    """Forest floor, gently rolling; the floor itself kept near flat."""
    n = noise.noise(Vector((x * 0.08, y * 0.08, 4.0)))
    inside = X0 - 0.5 < x < X1 + 0.5 and Y0 - 0.5 < y < Y1 + 0.5
    return (0.05 if inside else 1.2) * n + (0.0 if inside else 0.02 * max(0.0, -x) - 0.01 * max(0.0, y - Y1))


def tall_spruce(rng, base, h, verts, faces, clear):
    """A spruce whose lowest boughs start `clear` metres up, so it stands on the floor without blinding a camera."""
    tv, tf = [], []
    reb.conifer(rng, base, h, tv, tf)
    for f in tf:
        if min(tv[i].z if hasattr(tv[i], "z") else tv[i][2] for i in f) > base.z + clear:
            k = len(verts)
            verts.extend(tv[i] for i in f)
            faces.append(tuple(range(k, k + 4)))


def pawprints(name, path, step=0.5, seed=0, size=0.045):
    """A dog's tracks along `path`: a pad and four toes a print, left and right in turn. One mesh."""
    rng = random.Random(seed)
    verts, faces = [], []

    def blob(c, r):
        k = len(verts)
        verts.append((c.x, c.y, height(c.x, c.y) + 0.006))
        for i in range(7):
            a = 2 * math.pi * i / 7
            verts.append((c.x + math.cos(a) * r, c.y + math.sin(a) * r, height(c.x, c.y) + 0.006))
        faces.extend((k, k + 1 + i, k + 1 + (i + 1) % 7) for i in range(7))
    pts = [Vector(p) for p in path]
    side = 1
    for a, b in zip(pts, pts[1:]):
        d = b - a
        fwd = d.normalized()
        left = Vector((-fwd.y, fwd.x))
        for i in range(int(d.length / step)):
            c = a + fwd * (i * step + rng.uniform(-0.05, 0.05)) + left * side * 0.09
            blob(c, size)
            for t in (-0.9, -0.3, 0.3, 0.9):
                blob(c + fwd * size * 1.5 + left * size * t * 1.1, size * 0.38)
            side = -side
    return reb.mesh_object(name, verts, faces, reb.mat_plain("Paw prints", (0.03, 0.02, 0.012), 0.7), smooth=False)


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
    rng = random.Random(1918)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("earth")  # forest floor
    notes = [
        "from the north-west corner: the pylon's foot, the fork and its signpost, the hiker beyond",
        "from the north-east corner: the ladder's foot, the fork, the west path to the smoke, the patch on its branch",
        "from the south-west corner: the patch on the snag, the fork, the pylon's legs going up",
        "from the south-east corner: the hiker against his spruce, the dog tracks, the east path",
        "from the creek path, south: up the path to the pylon and its ladder into the dusk",
    ]
    for (eye, look), note in zip(CAMS, notes):
        room.camera(eye, look, 200, note)

    floor_m = kit.dirtied(reb.mat_surface("Forest floor", [(0.0, (0.05, 0.04, 0.025)), (0.5, (0.1, 0.08, 0.05)), (1.0, (0.08, 0.08, 0.04))], scale=1.5, bump=0.5), 0.5, scale=0.4)
    path_m = reb.mat_surface("Trodden path", [(0.0, (0.07, 0.05, 0.035)), (1.0, (0.14, 0.11, 0.07))], scale=5, bump=0.4)
    galv = reb.mat_surface("Galvanised", [(0.0, (0.2, 0.21, 0.21)), (0.7, (0.33, 0.33, 0.31)), (1.0, (0.28, 0.17, 0.09))], scale=6, rough=0.55, bump=0.2)
    yellow = mat("yellow paint")
    olive = reb.mat_surface("Bravo green", [(0.0, (0.06, 0.08, 0.04)), (1.0, (0.1, 0.12, 0.06))], scale=30, bump=0.2)

    # ---- The ground and the paths.
    reb.terrain("Forest floor", floor_m, (-50, 70), (-50, 70), height, step=0.7)
    kit.path_strip("Path from the ladder", path_m, [(9.5, 2.4), (9.8, 5.0), (10.0, FORK[1])], height, width=0.5)
    kit.path_strip("Path west", path_m, [FORK, (6.0, 8.6), (2.5, 9.2), (-8.0, 9.0), (-30.0, 8.0)], height, width=0.45)
    kit.path_strip("Path east", path_m, [FORK, (14.0, 9.3), (18.0, 8.8), (30.0, 9.2), (50.0, 9.5)], height, width=0.5)
    kit.path_strip("Path south", path_m, [FORK, (10.4, 12.5), (9.8, 16.0), (10.2, 30.0)], height, width=0.45)

    # ---- The pylon's foot: four legs on their footings, the ladder down to the ground, the cables overhead.
    tx, ty = TOWER
    top = 40.0

    def leg(i, z):
        f = z / top
        dx, dy = ((-3.2, -2.6), (3.2, -2.6), (3.2, 2.6), (-3.2, 2.6))[i]
        return (tx + dx * (1 - 0.7 * f), ty + dy * (1 - 0.7 * f), z)
    segs = []
    z = 0.0
    while z < top:
        z2 = z + 3.2
        for i in range(4):
            segs.append((leg(i, z), leg(i, z2)))
            segs.append((leg(i, z2), leg((i + 1) % 4, z2)))
            if z2 > 3.5 or i in (0,):
                segs.append((leg(i, z), leg((i + 1) % 4, z2)))
                segs.append((leg((i + 1) % 4, z), leg(i, z2)))
        z = z2
    struts("Pylon tower", galv, segs, 0.09)
    for i in range(4):
        x, y, _ = leg(i, 0)
        foot = reb.prim("cube", "Footing", mat("concrete"), (x, y, 0.2), (1.1, 1.1, 0.6), bevel=0.03)
        if Y0 < y < Y1:
            reb.mask(reb.wall(foot))
    reb.prim("cube", "Pylon plate", mat("white paint"), (tx, ty + 2.62, 2.4), (0.8, 0.02, 0.3))
    kit.text("Pylon number", "PYLON 7", mat("black"), (tx, ty + 2.64, 2.4), size=0.14, rot=(math.pi / 2, 0, math.pi))
    lad = []
    lx, ly = LADDER_FOOT
    for side in (-0.22, 0.22):
        lad.append(((lx + side, ly, 0.0), (lx + side, ly - 0.9, top)))
    for k in range(1, int(top / 0.3)):
        zz = k * 0.3
        yy = ly - 0.9 * zz / top
        lad.append(((lx - 0.22, yy, zz), (lx + 0.22, yy, zz)))
    for k in range(8, int(top / 0.3), 3):
        zz = k * 0.3
        yy = ly - 0.9 * zz / top
        pts = [(lx + 0.38 * math.cos(a), yy + 0.38 * math.sin(a), zz) for a in [math.pi * j / 6 for j in range(7)]]
        lad += list(zip(pts, pts[1:]))
    struts("Pylon ladder", yellow, lad, 0.018)
    reb.prim("cube", "Ladder gate", yellow, (lx + 0.45, ly + 0.05, 0.8), (0.03, 0.5, 0.9), rot=(0, 0, 0.9))
    kit.splat("Blood at the ladder's foot", mat("old blood"), (lx + 0.6, ly + 0.4, height(lx, ly)), 0.35, seed=3)
    for cx in (tx - 4.0, tx + 4.0):
        kit.rod("Cable to the lower station", mat("iron"), (cx, ty, top + 0.4), (cx, 180.0, -10.0), 0.03, 6)
        kit.rod("Cable up to the summit", mat("iron"), (cx, ty, top + 0.4), (cx, -150.0, 140.0), 0.03, 6)
    leg_crow, _ = kit.crow("Crow on the tower", (leg(3, 3.2)[0] + 0.3, leg(3, 3.2)[1], 3.2 + 0.05), heading=-0.4)

    # ---- The forest: spruces round the clearing, a few on the floor with high boughs, ferns, a fallen log.
    def keep_out(x, y):
        if X0 - 0.4 < x < X1 + 0.4 and Y0 - 0.4 < y < Y1 + 0.4:
            return True
        if abs(y - 9.0) < 2.0 or (abs(x - 10.0) < 2.0 and y > 0) or (abs(x - tx) < 5 and abs(y - ty) < 4):
            return True
        return any((Vector((x, y)) - Vector(e[:2])).length < 4.5 for e, _ in CAMS)
    kit.forest(rng, height, keep_out, (-28, -26, 46, 42), count=120, spacing=1.8, tall=(13, 22), ferns=40, needles=1500, dead=0.08)
    sv, sf = [], []
    trunks = []
    for x, y, h in INNER_TREES:
        base = Vector((x, y, height(x, y) - 0.2))
        tall_spruce(random.Random(int(x * 100 + y)), base, h, sv, sf, 4.2)
        t = kit.rod("Spruce trunk", mat("bark"), base, base + Vector((0, 0, h * 0.85)), h * 0.016, 8)
        trunks.append(reb.mask(reb.wall(t, "circle")))
    reb.mesh_object("Spruces over the floor", sv, sf, mat("needles"))
    log = kit.rod("Fallen log", mat("bark"), (13.6, 15.0, 0.25), (17.8, 14.2, 0.32), 0.3, 10)
    reb.wall(log)
    kit.rod("Log stub", mat("bark"), (17.8, 14.2, 0.32), (18.4, 13.4, 0.9), 0.08, 6)
    reb.wall(kit.rod("Stump", mat("bark"), (6.4, 11.4, 0), (6.4, 11.4, 0.55), 0.32, 9), "circle")
    moss_rock = kit.dirtied(mat("rock"), 0.7, scale=1.0)
    for (x, y, r) in ((3.2, 15.2, 0.6), (16.8, 2.0, 0.7), (13.6, 6.6, 0.45), (8.0, 14.6, 0.5)):
        rv, rf = [], []
        reb.boulder(rng, (x, y, height(x, y) - 0.1), r, rv, rf, squash=0.7)
        reb.wall(reb.mesh_object("Mossy rock", rv, rf, moss_rock), "circle")
    fv, ff = [], []
    for _ in range(26):
        x, y = rng.uniform(X0, X1), rng.uniform(Y0, Y1)
        if abs(y - 9.0) < 1.2 or abs(x - 10.0) < 1.2 or abs(x - 9.7) < 1.5 and y < 6:
            continue
        reb.fern(rng, (x, y, height(x, y)), rng.uniform(0.35, 0.6), fv, ff)
    floor_ferns = reb.mesh_object("Ferns on the floor", fv, ff, mat("ferns"))
    nv, nf = [], []
    for _ in range(1800):
        x, y = rng.uniform(X0, X1), rng.uniform(Y0, Y1)
        reb.card(nv, nf, Vector((x, y, height(x, y) + 0.008)), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), Vector((0, 0, 1)), 0.08, 0.28, 0.0)
    reb.mesh_object("Needles on the floor", nv, nf, mat("dead needles"))
    grass = kit.meadow(rng, 400, lambda r: (r.uniform(X0, X1), r.uniform(Y0, Y1)), height, mat("blades"))

    # ---- The signpost at the fork.
    sx, sy = FORK[0] + 0.9, FORK[1] - 0.8
    reb.wall(kit.rod("Signpost", mat("dark wood"), (sx, sy, 0), (sx, sy, 2.1), 0.06), "circle")
    for i, (words, z) in enumerate((("< ARKLAY TRAIL", 1.9), ("LOWER STATION >", 1.66), ("CREEK  v", 1.42))):
        reb.prim("cube", f"Sign board {i}", mat("dark wood"), (sx, sy - 0.05, z), (1.15, 0.03, 0.18))
        kit.text(f"Sign words {i}", words, mat("white paint"), (sx, sy - 0.067, z), size=0.08)
    kit.scratches("Claw marks on the post", mat("black"), (sx, sy - 0.065, 0.7), (0, -1), count=4, length=0.35, seed=4)

    # ---- The dogs' tracks: in from the east, over the fork, away south.
    pawprints("Dog tracks", [(19.5, 10.2), (14.0, 9.9), (11.0, 9.6), (10.8, 12.0), (10.6, 17.5)], step=0.55, seed=1)
    pawprints("Dog tracks, a second", [(19.5, 8.0), (15.0, 8.4), (11.6, 9.0), (11.4, 12.6), (11.2, 17.5)], step=0.6, seed=2)
    pawprints("Dog tracks, a third", [(19.5, 11.6), (16.2, 11.4), (15.2, 12.2)], step=0.5, seed=3)

    # ---- The hiker, sat against his spruce, throat torn; his pack split; the flies.
    hx, hy = HIKER_TREE
    kit.body("The hiker", (hx - 0.38, hy, height(hx, hy)), heading=math.pi, pose="slumped", top=reb.mat_plain("Hiker fleece", (0.35, 0.12, 0.03), 0.9), legs=mat("khaki"), bloody=1.2, seed=12)
    kit.splat("His throat", mat("blood"), (hx - 0.5, hy, 0.62), 0.09, rot=(0, -math.pi / 2, 0), seed=4, stretch=(1.2, 0.8))
    reb.prim("cube", "Blood down his front", mat("blood"), (hx - 0.53, hy, 0.4), (0.02, 0.18, 0.4))
    reb.prim("cube", "Pack, split", reb.mat_plain("Pack blue", (0.04, 0.08, 0.2), 0.7), (hx - 0.6, hy + 0.85, 0.2), (0.5, 0.3, 0.38), rot=(0.3, 0.2, 1.1), bevel=0.06)
    reb.cloth("Spilled from the pack", mat("denim"), (hx - 1.1, hy + 1.1, 0.02), (0.5, 0.4), rot=(0, 0, 0.6), lumps=0.03, seed=6)
    reb.prim("cyl", "Trail map tube", mat("red paint"), (hx - 1.3, hy + 0.5, 0.04), (0.08, 0.08, 0.4), rot=(math.pi / 2, 0, 0.3), segments=10)
    kit.papers("His map", (hx - 1.5, hy + 0.2, 0.0), spread=0.3, count=2, seed=7)
    reb.prim("cube", "Boot torn off", mat("rubber"), (hx - 1.9, hy - 0.4, 0.07), (0.3, 0.12, 0.14), rot=(0, 0.3, 2.0), bevel=0.03)
    kit.drag_trail("Where they pulled at him", mat("old blood"), [(hx - 1.0, hy), (hx - 2.0, hy - 0.6), (hx - 2.8, hy - 1.4)], width=0.3, seed=9, height=height)
    kit.bones("Gnawed bones", (hx - 2.6, hy - 1.6, height(hx - 2.6, hy - 1.6)), spread=0.35, seed=5, skull=False)

    # ---- The patch: a strip of Bravo's green sleeve, on a snapped branch at the west fork.
    px, py = PATCH
    reb.wall(kit.rod("Snag trunk", mat("bark"), (px - 0.5, py - 0.4, 0), (px - 0.5, py - 0.4, 3.0), 0.12, 8), "circle")
    kit.rod("Snapped branch", mat("bark"), (px - 0.5, py - 0.4, 1.55), (px + 0.1, py + 0.1, 1.5), 0.03, 6)
    kit.rod("Branch split", mat("pine"), (px + 0.1, py + 0.1, 1.5), (px + 0.2, py + 0.15, 1.48), 0.025, 6)
    branch_end = reb.prim("sphere", "Branch end", mat("bark"), (px + 0.08, py + 0.08, 1.5), (0.04, 0.04, 0.04), segments=6)
    sleeve = reb.cloth("Torn sleeve", olive, (0.0, 0.0, -0.18), (0.16, 0.34), rot=(math.pi / 2, 0, 0.6), cuts=8, lumps=0.02, seed=3)
    sleeve.parent = branch_end
    patch_m = reb.mat_plain("Patch blue", (0.03, 0.06, 0.25), 0.6)
    patch = reb.prim("cube", "STARS patch", patch_m, (0.0, 0.0, -0.2), (0.12, 0.012, 0.1), rot=(0, 0, 0.6))
    patch.parent = branch_end
    star = kit.text("Patch star", "STARS", mat("white paint"), (0.0, 0.0, -0.2), size=0.028, rot=(math.pi / 2, 0, 0.6))
    star.parent = branch_end
    star.location = (-0.004 * math.sin(0.6), -0.007 * math.cos(0.6), -0.2)
    kit.splat("Boot slide by the snag", mat("mud"), (px + 0.4, py + 0.6, 0.0), 0.15, seed=11, stretch=(2.0, 0.6))

    # ---- Far off: smoke from the crash in the west; the lower station's yard lamp through the trees east.
    smoke_m = mist_card_mat("Smoke", (0.12, 0.11, 0.11), 0.85, 0.15)
    smoke = []
    for i, (x, y, z, w, hgt) in enumerate(((-26.0, 7.0, 6.0, 8, 14), (-30.0, 10.0, 14.0, 12, 16), (-34.0, 9.0, 24.0, 16, 16))):
        ob = reb.prim("plane", f"Smoke {i}", smoke_m, (x, y, z), (w, hgt, 1), rot=(math.pi / 2, 0, math.pi / 2))
        smoke.append((ob, ob.location.copy(), i))
    reb.point("Crash glow", (-24.0, 8.5, 1.0), 200, (1.0, 0.35, 0.08), 1.0)
    reb.prim("sphere", "Yard lamp far off", reb.mat_emit("Far sodium", (1.0, 0.6, 0.2), 30), (34.0, 9.5, 5.0), (0.4, 0.4, 0.4))
    reb.point("Yard lamp far off light", (34.0, 9.5, 4.8), 600, (1.0, 0.6, 0.2), 0.3)

    # ---- Mist low between the trunks.
    mist_m = mist_card_mat("Ground mist", (0.55, 0.5, 0.52), 0.7, 0.18)
    mists = []
    for i, (x, y, w, d) in enumerate(((-6.0, 6.0, 14, 20), (26.0, 12.0, 14, 20), (10.0, 24.0, 24, 10), (10.0, -8.0, 24, 10), (-4.0, 18.0, 12, 12), (24.0, -2.0, 12, 12))):
        ob = reb.prim("plane", f"Mist {i}", mist_m, (x, y, 0.8), (w, d, 1))
        mists.append((ob, ob.location.copy(), rng.uniform(0, 6.3)))
    for i, (x, y, yaw) in enumerate(((-1.5, 4.5, math.pi / 2), (21.5, 6.0, math.pi / 2), (4.0, 19.5, 0.0), (15.0, 19.5, 0.0), (-1.5, 14.0, math.pi / 2), (21.5, 14.5, math.pi / 2), (4.0, -1.5, 0.0), (16.0, -1.5, 0.0))):
        ob = reb.prim("plane", f"Mist bank {i}", mist_m, (x, y, 1.6), (12, 3.2, 1), rot=(math.pi / 2, 0, yaw))
        mists.append((ob, ob.location.copy(), rng.uniform(0, 6.3)))

    # ---- Light: the sun nearly gone in the west, shafts of it through the trunks; fireflies.
    sun = kit.time_light("dusk", sun_heading=272, sun_energy=5.0, sky=((0.8, 0.36, 0.17), (0.16, 0.13, 0.24), 1.0))
    reb.point("Dusk sky fill", (10.0, 9.0, 26.0), 26000, (0.6, 0.48, 0.62), 12.0)
    sun.rotation_euler[0] = math.radians(90 - 9)
    for nd in bpy.context.scene.world.node_tree.nodes:
        if nd.type == "MIX" and nd.blend_type == "ADD":
            nd.inputs["B"].default_value = (0.3, 0.1, 0.03, 1)
    reb.spot("Last light on the fork", (-6.0, 7.0, 6.0), (11.0, 9.5, 0.0), 2600, (1.0, 0.45, 0.2), 16, 0.5, 0.3)
    reb.spot("Last light on the hiker", (-4.0, 12.0, 6.0), (hx - 0.5, hy, 0.4), 2200, (1.0, 0.45, 0.2), 8, 0.5, 0.3)
    reb.spot("Last light on the patch", (-6.0, 4.0, 5.0), (px, py, 1.4), 900, (1.0, 0.45, 0.2), 6, 0.5, 0.2)
    reb.spot("Last light on the ladder", (-8.0, 6.0, 8.0), (lx, ly, 1.5), 1500, (1.0, 0.45, 0.2), 10, 0.5, 0.3)
    fly_m = reb.mat_emit("Firefly", (0.8, 1.0, 0.35), 40)
    fireflies = []
    for i in range(10):
        c = (rng.uniform(3, 17), rng.uniform(3, 15), rng.uniform(0.4, 1.6))
        b = reb.prim("sphere", f"Firefly {i}", fly_m, c, (0.03, 0.03, 0.03), segments=6)
        fireflies.append((b, c, rng.uniform(0, 6.3), rng.choice((1, -1))))

    anim = kit.Anim(16)
    for ob, rest, ph in mists:
        anim.custom(lambda k, ob=ob, rest=rest, ph=ph: setattr(ob, "location", rest + Vector((1.6 * math.sin(anim.phase(k) + ph), 0.8 * math.cos(anim.phase(k) + ph), 0))))
    for ob, rest, i in smoke:
        anim.custom(lambda k, ob=ob, rest=rest, i=i: setattr(ob, "location", rest + Vector((0, 1.2 * math.sin(anim.phase(k) + i), 0.6 * math.cos(anim.phase(k) + i)))))
    for b, c, ph, d in fireflies:
        def f(k, b=b, c=c, ph=ph, d=d):
            a = anim.phase(k, d) + ph
            b.location = (c[0] + 0.5 * math.cos(a), c[1] + 0.4 * math.sin(a), c[2] + 0.25 * math.sin(2 * a))
            b.hide_render = math.sin(3 * a + ph) < -0.4
        anim.custom(f)
    anim.flies((hx - 0.55, hy, 0.5), count=10, radius=0.4)
    anim.swing(branch_end, axis=2, degrees=25)
    anim.custom(lambda k: setattr(leg_crow, "rotation_euler", (0, 0.45 * max(0.0, math.sin(anim.phase(k, 2))), -0.4)))
    anim.sway(floor_ferns, amount=0.03, every=4)
    anim.sway(grass, amount=0.04)

    # ---- What the game needs.
    room.door("pylon", (lx - 0.5, ly - 0.2, lx + 0.5, ly + 0.5), arrive=(9.6, 3.6), face=(0, 1), walk=False)
    room.door("crash", (X0, 7.8, X0 + 0.6, 10.2), arrive=(2.6, 9.1), face=(1, 0))
    room.door("lower-yard", (X1 - 0.6, 7.8, X1, 10.2), arrive=(17.4, 9.0), face=(-1, 0))
    room.door("creek", (8.8, Y1 - 0.6, 11.2, Y1), arrive=(10.0, 15.4), face=(0, -1))
    room.check((hx - 1.6, hy - 0.8, hx - 0.3, hy + 0.8), "A hiker. He sat down against the tree and they tore his throat out.\nDogs. The tracks are everywhere.")
    room.check((px - 0.4, py - 0.3, px + 0.6, py + 0.6), "A strip of green sleeve on a broken branch. A S.T.A.R.S. patch.\nBravo. Someone came through here in the night, running.")
    room.check((sx - 0.7, sy - 0.6, sx + 0.7, sy + 0.2), "ARKLAY TRAIL, west. LOWER STATION, east. CREEK, south.\nSomething's clawed the post.")
    room.check((11.0, 10.4, 12.0, 12.0), "Paw prints. A lot of them. Big dogs, running south.")
    room.check((lx - 0.6, ly + 0.2, lx + 0.8, ly + 0.9), "The pylon's ladder. There's blood at the foot of it,\ndripping from somewhere up above.")
    room.export(anim)


build()
