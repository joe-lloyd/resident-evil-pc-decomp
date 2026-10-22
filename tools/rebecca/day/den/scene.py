"""The dogs' den, under a granite tor north of the woods, at noon under cloud.

What it tells: this is where the drag marks end. The dogs lie up in a cave
mouth under a tor of weathered granite, a slab of rock across two blocks
with the dark going back under it. The ranger is here. They pulled him to
the mouth head first and ate what they wanted: he lies on his back in his
Forest Service uniform, the same as Dana's, the green jacket open, a hand
and a foot gone, and the flies are thick on him. His ring of keys still
hangs at his belt and catches what light there is. He is not the first: a
few old gnawed bones lie by the pit, a human skull among them, and a
hiker's orange jacket is torn up on the windfall at the south-west. In the
mouth, under the slab, the dogs have dug a pit in the soil where they lie,
matted with their hair. A heavy collar with a broken chain lies by it:
these were somebody's dogs once. Water drips off the slab into a puddle
stained red. Round the clearing the ground rises gently into the spruce,
grassed and thick with ferns, the trunks standing close into the mist.

Metres: she walks the floor of the clearing, x 3-15, y 2-12. The trampled
way comes down from the woods at the south edge, x 7.5-10. The tor stands
across the north: a west block (x 3.6-7.4), an east block (x 10-14), a back
block behind the mouth, and the capstone across them, its front edge at
about y 3.8 and its underside 2 m up. The mouth's floor is x 7.4-10,
y 2-3.7. The pit is at x 8.6, y 2.8, under the slab; the ranger's feet are
at x 10.4, y 5.7, his head toward the mouth.

Moving: flies on the ranger and the pit, water dripping from the slab, the
roots under it, the grass and ferns.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
from kit import mat  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector, noise  # noqa: E402

X0, X1, Y0, Y1 = 3.0, 15.0, 2.0, 12.0
WAY = (7.5, 10.0)          # the trampled way down from the woods, x along the south edge
PIT = (8.6, 2.8)
RANGER = (10.4, 5.7)       # his feet; his head is toward the mouth
# The tor's granite: centre (x, y), how high the centre stands over the
# lowest ground under the block (the capstone's is its height over the
# floor), half-sizes, and whether she bumps it.
BLOCKS = [
    ((5.6, 1.4, 0.8), (2.0, 1.8, 1.9), True),      # west block
    ((12.1, 1.3, 0.75), (2.1, 1.7, 1.8), True),    # east block
    ((8.8, -1.4, 0.9), (2.0, 1.3, 1.9), True),     # the back of the mouth
    ((9.0, 1.7, 2.5), (3.3, 2.0, 0.72), False),    # the capstone
    ((6.4, -1.6, 1.2), (2.5, 1.8, 2.2), False),
    ((11.6, -1.2, 1.1), (2.2, 1.7, 2.0), False),
    ((9.4, -2.8, 1.2), (2.6, 1.9, 2.1), False),
    ((2.0, 4.6, 0.3), (1.3, 1.2, 1.1), False),     # outliers on the slopes
    ((16.2, 3.6, 0.3), (1.5, 1.2, 1.0), False),
    ((3.2, -1.0, 0.8), (1.8, 1.5, 1.6), False),
    ((14.8, -0.8, 0.7), (1.7, 1.4, 1.5), False),
]
CAMS = [((8.6, 11.7, 3.3), (9.1, 3.0, 0.9)), ((4.0, 5.4, 3.0), (11.0, 11.4, 0.3)), ((14.6, 7.4, 3.6), (6.0, 4.0, 0.7))]


def height(x, y):
    """The clearing's floor nearly flat; the ground rising gently into the
    trees west, east and south, and up behind the tor in the north, never
    steeply enough for a tree to stand out of a bank."""
    n = noise.noise(Vector((x * 0.3, y * 0.3, 5.0)))
    h = -0.03 + 0.025 * n
    d_pit = math.hypot((x - PIT[0]) / 1.1, (y - PIT[1]) / 0.7)
    if d_pit < 1.0:
        h -= 0.14 * (1 - d_pit ** 2)
    rise = 0.0
    if x < X0 + 0.5:
        rise += (X0 + 0.5 - x) * 0.2
    if x > X1 - 0.5:
        rise += (x - X1 + 0.5) * 0.2
    if y > Y1 + 0.5:
        rise += (y - Y1 - 0.5) * (0.12 if WAY[0] - 0.5 < x < WAY[1] + 0.5 else 0.16)
    if y < 0.6:
        rise += (0.6 - y) * 0.5
    far = 0.35 * noise.noise(Vector((x * 0.12, y * 0.12, 2.0)))
    return h + rise + far * min(1.0, rise)


def in_rock(x, y, margin=0.0):
    """Inside a block's footprint (or within `margin` of it)."""
    for (cx, cy, _), (sx, sy, _), _ in BLOCKS:
        if ((x - cx) / (sx * 1.25 + margin)) ** 2 + ((y - cy) / (sy * 1.25 + margin)) ** 2 < 1:
            return True
    return False


def tube(verts, faces, pts, r, sides=5, taper=0.4):
    """A thin tube along `pts` (a root, a hanging rootlet), tapering toward the end."""
    pts = [Vector(p) for p in pts]
    base = len(verts)
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        side = d.cross(Vector((0, 0, 1)))
        if side.length < 1e-3:
            side = Vector((1, 0, 0))
        side.normalize()
        up = side.cross(d).normalized()
        rr = r * (1 - taper * i / max(1, len(pts) - 1))
        for k in range(sides):
            a = 2 * math.pi * k / sides
            verts.append(tuple(p + (side * math.cos(a) + up * math.sin(a)) * rr))
    for i in range(len(pts) - 1):
        for k in range(sides):
            a = base + i * sides + k
            b = base + i * sides + (k + 1) % sides
            faces.append((a, b, b + sides, a + sides))


def hanging_root(rng, verts, faces, top, length, r=0.03):
    """A root hanging from the slab's edge, kinking as it falls."""
    p = Vector(top)
    pts = [p.copy()]
    seg = length / 6
    for _ in range(6):
        p = p + Vector((rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1), -seg))
        pts.append(p.copy())
    tube(verts, faces, pts, r, 5, 0.7)


def world(at, heading, local):
    """A point in a kit.body's own frame placed in the world."""
    return Vector(at) + Matrix.Rotation(heading, 3, "Z") @ Vector(local)


def build():
    rng = random.Random(24)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.ground("earth")
    notes = ["from the way down: the clearing, the tor, the ranger at the cave mouth",
             "from beside the west block: the drag in from the woods, the windfall and the jacket, the way back up",
             "from the east: the mouth under the slab, the pit, the bones, the skull"]
    for (eye, look), note in zip(CAMS, notes):
        room.camera(eye, look, 200, note)

    soil = reb.mat_surface("Den soil", [(0.0, (0.03, 0.02, 0.012)), (0.45, (0.07, 0.05, 0.03)), (0.7, (0.1, 0.075, 0.045)), (0.88, (0.06, 0.065, 0.03)), (1.0, (0.13, 0.1, 0.065))], scale=2.5, detail=12, bump=0.7)
    churned = reb.mat_surface("Churned soil", [(0.0, (0.015, 0.01, 0.006)), (1.0, (0.06, 0.04, 0.025))], scale=6, rough=0.8, bump=0.8)
    hair = reb.mat_cards("Dog hair", (0.02, 0.018, 0.016), (0.09, 0.08, 0.07))
    root_m = reb.mat_surface("Roots", [(0.0, (0.05, 0.035, 0.022)), (1.0, (0.13, 0.09, 0.06))], scale=20, bump=0.5)
    jacket = reb.mat_surface("Hiker's jacket", [(0.0, (0.3, 0.07, 0.015)), (0.75, (0.42, 0.12, 0.02)), (1.0, (0.12, 0.025, 0.01))], scale=6, rough=0.6, bump=0.2)
    granite = mat("granite")
    # Blood gone into the soil: dark, brown-red, matte, broken up.
    soaked = reb.mat_surface("Soaked blood", [(0.15, (0.018, 0.007, 0.005)), (0.45, (0.04, 0.012, 0.007)), (0.75, (0.06, 0.022, 0.012)), (0.95, (0.05, 0.035, 0.022))], scale=28, detail=8, rough=0.95, bump=0.15)

    # ---- Ground: the trampled floor, grass and ferns up the slopes, the way down from the woods.
    trodden = lambda x, y: ((x - 9.4) / 3.0) ** 2 + ((y - 5.0) / 2.6) ** 2 < 1 + 0.35 * noise.noise(Vector((x * 0.6, y * 0.6, 3.0))) or (7.4 < x < 10.2 and y < 4.2) or abs(x - 8.9 - (y - 10.0) * 0.08) < 0.6 and y > 6.0
    reb.terrain("Clearing floor", soil, (X0 - 0.8, X1 + 0.8), (Y0 - 2.4, Y1 + 0.8), height, step=0.25)
    reb.terrain("Slopes", mat("grassed earth"), (-20, 38), (-20, 38), lambda x, y: height(x, y) - (0.03 if X0 - 0.8 < x < X1 + 0.8 and Y0 - 2.4 < y < Y1 + 0.8 else 0.0), step=0.5)
    on_way = kit.dirt_path("Trampled way", [(8.8, 26.0), (8.8, 18.0), (8.7, 13.0), (8.9, 10.8)], height, width=0.9)
    kit.lay_on_ground(kit.drag_trail("The drag ends here", soaked, [(8.8, 15.0), (8.8, 12.5), (9.0, 10.4), (9.6, 7.8), (10.1, 6.2)], width=0.28, seed=3, height=height), height, 0.012)

    # ---- The tor: weathered granite blocks, the capstone across the mouth.
    bv, bf = [], []
    for i, ((cx, cy, cz), size, bump) in enumerate(BLOCKS):
        # Sat into the ground on its low side, so it never hangs over the slope.
        low = min(height(cx + math.cos(a) * size[0], cy + math.sin(a) * size[1]) for a in (k * math.tau / 12 for k in range(12)))
        z = cz if i == 3 else min(low, height(cx, cy)) + cz
        kit.crag(rng, bv, bf, (cx, cy, z), size, floor=-0.6)
        if bump:
            reb.wall(reb.prim("cube", "Rock footprint", None, (cx, cy, 0.5), (size[0] * 2.1, size[1] * 2.1, 1.0))).hide_render = True
    tor = reb.mesh_object("Granite tor", bv, bf, granite, smooth=False)
    tor.data.materials.append(mat("moss"))
    for poly in tor.data.polygons:
        if poly.normal.z > 0.75 and poly.center.z > 1.2:
            poly.material_index = 1
    # Grass and ferns on the tor's ledges and top, where soil has caught.
    tops = [tuple(p.center) for p in tor.data.polygons if p.normal.z > 0.8 and p.center.z > 1.2]
    kit.ledge_plants(rng, rng.sample(tops, min(len(tops), 900)), tufts=500, ferns=40, name="Tor")
    # The back of the mouth, unlit: the dark the dogs lie up in.
    reb.prim("cube", "Dark under the slab", mat("black"), (8.8, -0.6, 1.2), (3.0, 0.3, 2.6))
    # Roots of the spruce on top come down over the slab's front edge.
    tv, tf = [], []
    for _ in range(12):
        x = rng.uniform(6.6, 11.4)
        hanging_root(rng, tv, tf, (x, 3.4 + rng.uniform(-0.3, 0.2), 2.6), rng.uniform(0.4, 1.1), rng.uniform(0.012, 0.03))
    roots = reb.mesh_object("Roots under the slab", tv, tf, root_m)
    top_base = Vector((9.0, -5.8, height(9.0, -5.8) - 0.2))
    cv, cf = [], []
    reb.conifer(rng, top_base, 17, cv, cf)
    reb.mesh_object("Spruce over the tor", cv, cf, mat("needles"))
    reb.trunks("Its trunk", mat("bark"), [(top_base, 17)])
    kit.tree_roots(rng, [(top_base, 17)], height)
    kit.rocks("Fallen rocks", rng, [(3.6, 3.3, 0.35), (14.2, 3.6, 0.4), (3.5, 10.6, 0.45), (14.4, 9.8, 0.4), (7.2, 3.6, 0.22), (10.6, 3.5, 0.18)], height, granite)
    for (x, y, r) in ((3.5, 10.6, 0.45), (14.4, 9.8, 0.4)):
        reb.wall(reb.prim("cube", "Rock footprint", None, (x, y, r / 2), (r * 2.2, r * 1.9, r))).hide_render = True

    # ---- The pit they lie in, under the slab: churned soil, hair, a collar with a broken chain.
    kit.lay_on_ground(kit.splat("The dogs' pit", churned, (PIT[0], PIT[1], 0), 0.9, seed=7, stretch=(1.2, 0.8), lumps=0.25), height, 0.006)
    hv, hf = [], []
    for _ in range(500):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, 1.0) ** 0.5
        x, y = PIT[0] + math.cos(a) * d * 1.1, PIT[1] + math.sin(a) * d * 0.7
        reb.card(hv, hf, Vector((x, y, height(x, y) + 0.012)), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), Vector((0, 0, 1)), 0.02, 0.09, 0.0)
    reb.mesh_object("Dog hair in the pit", hv, hf, hair)
    cx, cy = PIT[0] - 1.0, PIT[1] + 0.8
    cz = height(cx, cy)
    collar = reb.prim("cyl", "Collar", reb.mat_plain("Collar leather", (0.04, 0.025, 0.015), 0.6), (cx, cy, cz + 0.02), (0.22, 0.22, 0.04), segments=16)
    reb.prim("cyl", "Collar hole", mat("black"), (cx, cy, cz + 0.03), (0.17, 0.17, 0.02), segments=16)
    reb.prim("cube", "Collar tag", mat("steel"), (cx + 0.12, cy, cz + 0.01), (0.05, 0.04, 0.004))
    for k in range(6):
        reb.prim("cyl", f"Chain link {k}", mat("iron"), (cx + 0.16 + k * 0.055, cy + 0.02 * math.sin(k), cz + 0.012), (0.05, 0.03, 0.01), rot=(0 if k % 2 else math.pi / 2, 0, 0.2), segments=8)
    reb.prim("cube", "Broken link", mat("rust"), (cx + 0.52, cy + 0.04, cz + 0.008), (0.04, 0.012, 0.012), rot=(0, 0, 0.8))

    # ---- The ranger: on his back at the mouth, half eaten, the keys at his belt.
    heading = math.radians(-100)   # head toward the mouth (north)
    rx, ry = RANGER
    kit.ranger("The ranger", (rx, ry, height(rx, ry) + 0.01), heading, pose="back", seed=8, missing=("l_hand", "r_foot"))
    room.item("truck-keys", tuple(world((rx, ry, height(rx, ry)), heading, (0.8, -0.55, 0.0))))
    # His blood, gone into the soil round him in dark patches, not a pool on top.
    for k, (lx, ly, r) in enumerate(((1.1, 0.1, 0.4), (0.7, 0.35, 0.22), (1.5, -0.3, 0.2), (0.25, -0.15, 0.16))):
        p = world((rx, ry, 0), heading, (lx, ly, 0))
        kit.lay_on_ground(kit.splat(f"His blood {k}", soaked, (p.x, p.y, 0), r, rot=(0, 0, rng.uniform(0, 6)), seed=9 + k, stretch=(1.4, 1.0), lumps=0.7), height, 0.005 + 0.001 * k)
    j = kit._POSES["back"]
    # The key ring at his belt, and what else he carried: holster, torn sleeve.
    ring_at = world((rx, ry, height(rx, ry)), heading, (0.9, -0.22, 0.1))
    reb.prim("cyl", "Key ring", mat("steel"), ring_at, (0.07, 0.07, 0.008), rot=(math.pi / 2, 0, heading), segments=12)
    for k in range(4):
        a = -0.6 + k * 0.4
        kp = ring_at + Matrix.Rotation(heading, 3, "Z") @ Vector((math.sin(a) * 0.06, -0.03, -math.cos(a) * 0.06 - 0.02))
        reb.prim("cube", f"Key {k}", reb.mat_metal("Bright keys", (0.7, 0.66, 0.55), 0.2), kp, (0.012, 0.025, 0.07), rot=(0, a, heading))
    reb.point("Glint on the keys", ring_at + Vector((0.2, 0.3, 0.6)), 0.6, (0.85, 0.88, 0.92), 0.05)
    holster_at = world((rx, ry, height(rx, ry)), heading, (0.86, 0.24, 0.1))
    reb.prim("cube", "Empty holster", reb.mat_plain("Holster leather", (0.05, 0.03, 0.015), 0.5), holster_at, (0.18, 0.06, 0.1), rot=(0, 0, heading), bevel=0.015)
    for name, (lx, ly) in (("Torn cuff", j["l_elbow"][:2]), ("Torn trouser leg", j["r_knee"][:2])):
        p = world((rx, ry, 0), heading, (lx, ly, 0))
        reb.cloth(name, mat("khaki") if "cuff" in name else kit.mat("black"), (p.x, p.y, height(p.x, p.y) + 0.02), (0.22, 0.14), rot=(0, 0, heading + rng.uniform(-0.5, 0.5)), cuts=5, lumps=0.02, seed=31)
    hat_at = world((rx, ry, 0), heading, (2.3, 0.55, 0.0))
    kit.campaign_hat("His hat", (hat_at.x, hat_at.y, height(hat_at.x, hat_at.y) + 0.005), heading=0.7, tilt=(0.12, 0.0))
    radio_at = world((rx, ry, 0), heading, (0.3, -0.9, 0.0))
    rz = height(radio_at.x, radio_at.y)
    reb.prim("cube", "His radio", reb.mat_plain("Radio black", (0.02, 0.02, 0.02), 0.5), (radio_at.x, radio_at.y, rz + 0.04), (0.08, 0.2, 0.06), rot=(0, 0, 0.9))
    kit.rod("Radio aerial", mat("black"), (radio_at.x, radio_at.y, rz + 0.05), (radio_at.x + 0.18, radio_at.y + 0.12, rz + 0.05), 0.004, 4)

    # ---- By the pit: one heap of old gnawed bones and a human skull, half buried.
    kit.bones("Gnawed bones", (PIT[0] + 1.3, PIT[1] + 0.4, height(PIT[0] + 1.3, PIT[1] + 0.4)), spread=0.35, seed=40, skull=False)
    sx, sy = PIT[0] + 0.9, PIT[1] - 0.3
    reb.prim("sphere", "Human skull", mat("bone"), (sx, sy, height(sx, sy) + 0.04), (0.17, 0.2, 0.17), segments=14)
    for s in (-1, 1):
        reb.prim("sphere", "Eye socket", mat("black"), (sx + 0.03 * s, sy + 0.08, height(sx, sy) + 0.07), (0.04, 0.04, 0.05), segments=8)
    # Windfall at the south-west, the hiker's jacket torn up on its stubs.
    wa, wb = (4.2, 11.2), (7.4, 9.3)
    windfall = kit.rough_log("Windfall", (wa[0], wa[1], height(*wa) + 0.16), (wb[0], wb[1], height(*wb) + 0.14), 0.26, seed=50, stubs=6)
    for k in range(3):
        p = Vector(wa).lerp(Vector(wb), 0.15 + 0.3 * k)
        reb.wall(reb.prim("cube", "Windfall footprint", None, (p.x, p.y, 0.3), (1.3, 0.55, 0.6), rot=(0, 0, math.atan2(wb[1] - wa[1], wb[0] - wa[0])))).hide_render = True
    jx, jy = 5.9, 10.15
    torn = kit.drape("Hiker's jacket", jacket, [windfall], (jx, jy), (0.85, 0.6), yaw=math.atan2(wb[1] - wa[1], wb[0] - wa[0]) + math.pi / 2, base=height(jx, jy), cuts=16, lumps=0.03, seed=11)
    # Torn up: a ragged outline and holes, not a square of cloth.
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(torn.data)
    mw = torn.matrix_world
    gone = []
    for f in bm.faces:
        c = mw @ f.calc_center_median()
        d = math.hypot(c.x - jx, c.y - jy)
        edge = 0.3 * (0.75 + 0.35 * noise.noise(Vector((c.x * 9, c.y * 9, 1.0))))
        if d > edge or noise.noise(Vector((c.x * 14, c.y * 14, 4.0))) > 0.45:
            gone.append(f)
    bmesh.ops.delete(bm, geom=gone, context="FACES")
    bm.to_mesh(torn.data)
    bm.free()
    for k in range(5):
        x, y = rng.uniform(5.0, 7.6), rng.uniform(8.2, 9.4)
        reb.cloth(f"Shred of jacket {k}", jacket, (x, y, height(x, y) + 0.01), (rng.uniform(0.1, 0.22), rng.uniform(0.06, 0.12)), rot=(0, 0, rng.uniform(0, 6)), cuts=4, lumps=0.01, seed=20 + k)
    bx, by = 4.6, 8.6
    reb.prim("cube", "Hiker's boot", reb.mat_plain("Brown leather", (0.09, 0.05, 0.025), 0.6), (bx, by, height(bx, by) + 0.06), (0.3, 0.12, 0.13), rot=(0, 0, 0.4), bevel=0.03)
    # Prints everywhere in the soft floor.
    pv, pf = [], []
    for k in range(70):
        x, y = rng.uniform(X0 + 1, X1 - 1), rng.uniform(Y0 + 0.5, Y1 - 0.5)
        if not trodden(x, y):
            continue
        kit._stain(pv, pf, rng, (x, y, height(x, y) + 0.006), 0.04, rng.uniform(0, 6), 0.2, (1, 1.1), k, points=8, drops=False)
    reb.mesh_object("Paw prints", pv, pf, churned, smooth=False)

    # ---- Water dripping off the slab into a reddened puddle.
    drip_at = (9.6, 3.55, 2.5)
    kit.lay_on_ground(kit.splat("Puddle under the drip", reb.mat_plain("Red puddle", (0.025, 0.01, 0.007), 0.3), (drip_at[0], drip_at[1], 0), 0.28, seed=14, stretch=(1.3, 1.0)), height, 0.007)

    # ---- The clearing's edges: grass, ferns, needles; the forest close round it.
    floor_grass = kit.grass_ground(rng, (X0 - 1, Y0 - 1, X1 + 1, Y1 + 1), height, per_m2=14,
                                   keep_out=lambda x, y: trodden(x, y) or in_rock(x, y) or on_way(x, y, 0.2))
    slope_grass = kit.grass_ground(rng, (-12, -10, 30, 30), height, per_m2=5,
                                   keep_out=lambda x, y: (X0 - 1 < x < X1 + 1 and Y0 - 1 < y < Y1 + 1) or in_rock(x, y) or on_way(x, y, 0.2))
    fv, ff = [], []
    for _ in range(140):
        x, y = rng.uniform(X0 - 6, X1 + 6), rng.uniform(Y0 - 3, Y1 + 6)
        if trodden(x, y) or in_rock(x, y) or on_way(x, y, 0.4):
            continue
        reb.fern(rng, (x, y, height(x, y)), rng.uniform(0.35, 0.7), fv, ff)
    ferns = reb.mesh_object("Ferns round the clearing", fv, ff, mat("ferns"))
    nv, nf = [], []
    for _ in range(4000):
        x, y = rng.uniform(X0, X1), rng.uniform(Y0, Y1)
        reb.card(nv, nf, Vector((x, y, height(x, y) + 0.008)), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), Vector((0, 0, 1)), 0.012, 0.05, 0.0)
    reb.mesh_object("Needles on the floor", nv, nf, reb.mat_cards("Needle litter", (0.05, 0.035, 0.02), (0.1, 0.075, 0.04)))

    def no_tree(x, y):
        if X0 - 0.6 < x < X1 + 0.6 and Y0 - 0.6 < y < Y1 + 0.6:
            return True
        if in_rock(x, y, 0.6) or on_way(x, y, 1.2):
            return True
        return any((x - ex) ** 2 + (y - ey) ** 2 < 9 for (ex, ey, _), _ in CAMS)
    kit.forest(rng, height, no_tree, (-16, -16, 34, 34), count=280, spacing=1.5, tall=(14, 22), ferns=160, needles=900, dead=0.06)
    kit.forest(rng, height, no_tree, (-4, -6, 22, 20), count=90, spacing=1.2, tall=(13, 20), ferns=40, needles=300)
    kit.far_spruces(rng, height, keep_out=lambda x, y: -16 < x < 34 and -16 < y < 34, count=900, area=(-70, -70, 90, 90))

    # ---- Light: the cloud's flat light into the clearing, dark under the rock.
    sun = kit.time_light("noon", sun_heading=200, sun_energy=3.4, mist=((9.0, 6.0, 5.0), (80.0, 80.0, 16.0), 0.01),
                         sky=((0.6, 0.62, 0.63), (0.4, 0.42, 0.45), 1.2))
    sun.data.angle = math.radians(18)
    sun.rotation_euler[0] = math.radians(30)
    kit.overcast_sky()

    def far_land(x, y, z):
        r = math.hypot(x - 9.0, y - 6.0)
        w = max(0.0, min(1.0, (220.0 - r) / 160.0))
        return z + (height(x, y) - 0.4 - z) * w * w * (3 - 2 * w)
    kit.backdrop((9.0, 6.0, 3.2), spread=360, below=-6.0, near=70.0, forest_to=1500.0, trees=50000,
                 keep_out=lambda x, y: math.hypot(x - 9.0, y - 6.0) < 70, shape=far_land, mist=25.0, rng=random.Random(9))
    reb.spot("Sky into the clearing", (9.0, 14.0, 12.0), (9.0, 6.5, 0.0), 4200, (0.8, 0.84, 0.9), 70, 0.9, 5.0)

    anim = kit.Anim(16)
    head = world((rx, ry, height(rx, ry)), heading, (1.1, 0, 0.15))
    anim.flies(tuple(head), count=16, radius=0.55)
    anim.flies((PIT[0], PIT[1], height(*PIT) + 0.05), count=6, radius=0.5)
    anim.drip(drip_at, fall=drip_at[2] - height(drip_at[0], drip_at[1]) - 0.02)
    anim.sway(roots, amount=0.015, along=(1.0, 0.3), every=5, tip=3)
    anim.sway(ferns, amount=0.02)
    anim.sway(floor_grass, amount=0.02)
    anim.sway(slope_grass, amount=0.02)
    anim.sway(torn, amount=0.02, along=(0.6, 1.0), every=2, tip=1)

    # ---- What the game needs.
    room.door("woods", (WAY[0], Y1 - 0.6, WAY[1], Y1), arrive=(8.9, 10.6), face=(0, -1))
    hx, hy = world((rx, ry, 0), heading, (0.9, 0, 0)).xy
    room.check((hx - 1.0, hy - 1.0, hx + 1.0, hy + 1.0), "The ranger. What the dogs left of him.\nHis keys are still on his belt.")
    room.check((PIT[0] - 0.6, Y0, PIT[0] + 0.8, PIT[1] + 0.6), "A pit scraped in the soil under the rock, matted with black hair.\nThis is where they sleep.")
    room.check((cx - 0.5, cy - 0.4, cx + 0.7, cy + 0.4), "A heavy collar on a broken chain. The tag's too scratched to read.\nThese dogs belonged to someone.")
    room.check((sx - 0.5, Y0, sx + 0.6, sy + 0.5), "A human skull. It's been here a lot longer than he has.")
    room.check((5.0, 9.0, 6.9, 10.6), "A hiker's jacket, torn up on the fallen tree.\nI don't want to know where the hiker is.")
    room.check((drip_at[0] - 0.5, drip_at[1] - 0.5, drip_at[0] + 0.5, drip_at[1] + 0.5), "Water dripping off the rock into a puddle. The puddle's red.")
    room.export(anim)


build()
