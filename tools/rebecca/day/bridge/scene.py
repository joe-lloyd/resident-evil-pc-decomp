"""The ravine bridge, below the ranger station, mid-morning.

The trail comes down the mountain from the station to the lip of a gorge
and crosses it on an old plank footbridge hung on two rope rails. The gorge
is a cut in the mountain's granite: walls broken into buttresses and
outcrops, darker and wet low down, tufts of grass and ferns on every ledge,
a river running white along the bottom far below with the mist lying in it.
The near bank is long grass, where the adders are. On the far bank the
trail goes on down into the valley under the pines. All round, the forest
stands close on the slopes, and over it the overcast and the ranges
(kit.backdrop, kit.overcast_sky: the RE0 look).

Metres, real sizes. She walks the near bank (x 2-10, y 2-7), the bridge
(x 5.3-6.7, y 7-15, the deck flat at z 0) and the far bank (x 2-10, y 15-18).
Ways out: north up the trail to the yard, south on down the trail.

Moving: the river, the grass, the rope rails, all of it slight.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import reb  # noqa: E402
import kit  # noqa: E402
from mathutils import Vector, noise  # noqa: E402

OUT = os.environ.get("RE1_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders"))
FRAMES = 16
X0, X1, Y0, Y1 = 2.0, 10.0, 2.0, 18.0   # Y1 * 1700 stays under 32767: positions are signed 16-bit
NEAR, FAR = 7.0, 15.0           # the gorge's lips (y) where she walks
BX0, BX1 = 5.3, 6.7             # the bridge deck (x)
DEPTH = 17.0                    # lip to river bed

# The trail, from up the mountain (north) to the bridge, and on from its far
# end down into the valley: both run on past the edge of every camera.
TRAIL_UP = [(10.5, -40.0), (9.6, -24.0), (8.6, -12.0), (7.4, -4.0), (6.7, 0.5), (6.3, 3.5), (6.0, 6.2), (6.0, 7.2)]
TRAIL_DOWN = [(6.0, 14.8), (5.9, 15.8), (5.4, 18.0), (3.8, 21.0), (0.5, 24.0), (-5.0, 28.0), (-14.0, 34.0), (-26.0, 40.0)]


def G(x, y, z=0.0):
    return (reb.g(x), -reb.g(z), reb.g(y))


CAMERAS = [
    # 0: from the trail coming down, over the near bank, along the bridge to the far bank's pines.
    {"from": G(8.6, -1.6, 4.2), "to": G(5.6, 8.5, -0.8), "fov": 200},
    # 1: from high over the gorge's west wall, steeply down: the bridge, the drop, the river.
    {"from": G(2.4, 11.0, 4.4), "to": G(6.3, 11.0, -3.0), "fov": 200},
    # 2: from the far bank, back across the bridge and up the trail toward the station.
    {"from": G(3.2, 20.2, 3.6), "to": G(6.2, 10.5, 0.0), "fov": 200},
]
EYES = [reb.game_to_blender(c["from"]) for c in CAMERAS]


def centre(x):
    """The gorge's line: straight where the bridge spans it, wandering away
    either side so it reads as a cut the river made, not a trench."""
    k = max(0.0, abs(x - 6.0) - 6.0)
    return 11.0 + k * 0.08 * math.sin(x * 0.045 + 1.0) + 0.06 * k * noise.noise(Vector((x * 0.02, 0.5, 2.0)))


def half_width(x):
    k = max(0.0, abs(x - 6.0) - 5.0)
    return 4.0 + min(6.0, k * 0.05) - 0.18 * (noise.noise(Vector((x * 0.25, 1.5, 0.0))) + 1)   # never past the lips she walks to


def gorge(x, y):
    """How far below the bank the gorge is at (x, y): 0 outside, the river
    bed inside. The walls themselves are their own meshes (wall())."""
    return -DEPTH if abs(y - centre(x)) < half_width(x) - 0.02 else 0.0


def ground_height(x, y):
    """The banks: a mountainside falling south, flat where she walks; the gorge cut across it."""
    h = 0.02 * noise.noise(Vector((x * 0.8, y * 0.8, 0)))
    if x < X0 - 0.5:
        h += (X0 - 0.5 - x) * 0.18
    if x > X1 + 0.5:
        h += (x - X1 - 0.5) * 0.28
    if y < Y0 - 0.5:
        h += (Y0 - 0.5 - y) * 0.45            # the mountain the trail comes down
    if y > Y1 + 0.3:
        h -= (y - Y1 - 0.3) * 0.32            # on down into the valley
    rough = 0 if (X0 - 1 < x < X1 + 1 and Y0 - 1 < y < Y1 + 0.5) else 1
    h += rough * 0.5 * noise.noise(Vector((x * 0.12, y * 0.12, 3)))
    return h + gorge(x, y)


def far_land(x, y, z):
    """The kit's land, eased into the banks' own mountainside near the room."""
    r = math.hypot(x - 6.0, y - 10.0)
    w = max(0.0, min(1.0, (220.0 - r) / 160.0))
    return z + (ground_height(x, y) - z) * w * w * (3 - 2 * w)


def in_gorge(x, y, pad=0.0):
    return abs(y - centre(x)) < half_width(x) + pad


def near_lens(x, y, r=6.0):
    return any((Vector((x, y)) - e.xy).length < r for e in EYES)


def build():
    rng = random.Random(41)
    reb.clear_scene()
    rock, moss = kit.mat("granite"), kit.mat("moss")
    plank_m = reb.mat_wood("Bridge planks", (0.22, 0.17, 0.12))
    post_m = reb.mat_wood("Posts", (0.18, 0.12, 0.07))
    rope = reb.mat_surface("Rope", [(0.0, (0.3, 0.25, 0.16)), (1.0, (0.45, 0.38, 0.24))], scale=60, bump=0.6)

    # ---- Ground: the banks, grassed earth; the gorge's walls of granite
    # hung from the lips, moss on their ledges; scree and the river below.
    reb.terrain("Banks", kit.mat("grassed earth"), (-45, 60), (-34, 52), ground_height, step=0.25)
    xs = [-70 + 0.2 * i for i in range(751)]
    gorge_ledges = (2.6, 5.8, 9.5, 12.8, 15.2)
    _, near_ledges = kit.cliff("Gorge wall near", xs, lambda x: (centre(x) - half_width(x), 0.0), DEPTH + 0.6, 1, m=rock, ledge_m=moss, seed=-3.1, ledges=gorge_ledges)
    _, far_ledges = kit.cliff("Gorge wall far", xs, lambda x: (centre(x) + half_width(x), 0.0), DEPTH + 0.6, -1, m=rock, ledge_m=moss, seed=3.1, ledges=gorge_ledges)

    def wall_inset(x, u, side):
        return kit.cliff_relief(x, u, side * 3.1, gorge_ledges)
    # Outcrops standing out of the walls here and there: lumpy granite.
    cv, cf = [], []
    for _ in range(45):
        x = rng.uniform(-40, 50)
        side = rng.choice((-1, 1))
        u = rng.uniform(2.0, DEPTH - 1.0)
        y = centre(x) + side * (half_width(x) - wall_inset(x, u, side))
        size = (rng.uniform(0.6, 1.6), rng.uniform(0.35, 0.7), rng.uniform(0.5, 1.3))
        kit.crag(rng, cv, cf, (x, y - side * 0.1, -u), size, floor=-0.9)
    reb.mesh_object("Gorge outcrops", cv, cf, rock, smooth=False)
    # Scree at the foot of each wall, by the river.
    sv, sf = [], []
    for _ in range(200):
        x = rng.uniform(-40, 55)
        side = rng.choice((-1, 1))
        y = centre(x) + side * (half_width(x) - wall_inset(x, DEPTH, side) - rng.uniform(0.0, 0.5))
        reb.boulder(rng, (x, y, -DEPTH + 0.1), rng.uniform(0.2, 0.6), sv, sf, squash=0.7)
    reb.mesh_object("Scree", sv, sf, kit.mat("wet rock"), smooth=False)
    # Grass and ferns on the ledges: the gorge's only green.
    kit.ledge_plants(rng, near_ledges + far_ledges, tufts=4000, ferns=240)

    # ---- The trail: bare dirt down the mountain to the bridge, on from its far end.
    on_up = kit.dirt_path("Trail down from the station", TRAIL_UP, ground_height, width=1.5, taper=0.0)
    on_down = kit.dirt_path("Trail on down", TRAIL_DOWN, ground_height, width=1.4)

    def on_trail(x, y, margin=0.0):
        return on_up(x, y, margin) or on_down(x, y, margin)

    # The river far below: rapids whose pattern slides downstream each frame.
    river_m, nodes, links, bsdf = reb.nodes_material("River")
    bsdf.inputs["Roughness"].default_value = 0.15
    tc = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    links.new(tc.outputs["Object"], mapping.inputs["Vector"])
    nz = nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.4
    nz.inputs["Detail"].default_value = 8
    links.new(mapping.outputs["Vector"], nz.inputs["Vector"])
    foam = reb.ramp(nodes, links, nz.outputs["Fac"], [(0.35, (0.03, 0.06, 0.07)), (0.55, (0.12, 0.18, 0.18)), (0.68, (0.7, 0.74, 0.74))])
    links.new(foam.outputs["Color"], bsdf.inputs["Base Color"])
    # Along the gorge's own line, wider than the bed, so it fills the bottom.
    rv, rf = [], []
    xs = [-80 + 1.0 * i for i in range(181)]
    for x in xs:
        c = centre(x)
        rv += [(x, c - 3.0, -DEPTH + 0.35), (x, c + 3.0, -DEPTH + 0.35)]
    rf = [(2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1) for i in range(len(xs) - 1)]
    reb.mesh_object("River", rv, rf, river_m, smooth=False)

    # The bridge: plank deck on two stringers, rope rails on posts, hangers.
    deck = []
    y = NEAR - 0.6
    i = 0
    while y < FAR + 0.6:
        tilt = rng.uniform(-0.03, 0.03)
        deck.append(reb.prim("cube", "Plank", plank_m, ((BX0 + BX1) / 2 + rng.uniform(-0.03, 0.03), y, -0.03), (BX1 - BX0 + rng.uniform(-0.06, 0.02), 0.22, 0.04), rot=(0, tilt, rng.uniform(-0.02, 0.02)), bevel=0.006))
        y += 0.27
        i += 1
    for x in (BX0 + 0.08, BX1 - 0.08):
        reb.prim("cube", "Stringer", post_m, (x, (NEAR + FAR) / 2, -0.12), (0.12, FAR - NEAR + 1.4, 0.14))
    for yy in (NEAR - 0.5, FAR + 0.5):
        for x in (BX0 - 0.15, BX1 + 0.15):
            reb.mask(reb.wall(reb.prim("cyl", "Bridge post", post_m, (x, yy, 0.6), (0.22, 0.22, 1.5), segments=10), "circle"))
    rails = []
    for x in (BX0 - 0.12, BX1 + 0.12):
        rv, rf = [], []
        segs = 40
        for k in range(segs + 1):
            t = k / segs
            yy = NEAR - 0.5 + (FAR - NEAR + 1.0) * t
            sag = 0.35 * math.sin(math.pi * t)
            rv.append((x, yy, 1.15 - sag))
        rails.append((x, rv))
    # Rails and hangers are rebuilt per frame (they sway), so keep their rest shape.
    rail_objs = []
    for x, pts in rails:
        bpy.ops.curve.primitive_bezier_curve_add()
        cu = bpy.context.active_object
        cu.name = f"Rope rail {x:.1f}"
        cu.data.bevel_depth = 0.025
        cu.data.bevel_resolution = 2
        spl = cu.data.splines[0]
        spl.type = "POLY"
        cu.data.splines.remove(spl)
        poly = cu.data.splines.new("POLY")
        poly.points.add(len(pts) - 1)
        for p, (px, py, pz) in zip(poly.points, pts):
            p.co = (px, py, pz, 1)
        cu.data.materials.append(rope)
        rail_objs.append((cu, poly, pts))
    hangers = []
    for x, pts in rails:
        for k in range(2, len(pts) - 1, 3):
            px, py, pz = pts[k]
            ob = reb.prim("cyl", "Hanger", rope, (px, py, (pz - 0.06) / 2), (0.018, 0.018, pz + 0.06), segments=6)
            hangers.append((ob, Vector((px, py, pz))))

    # Sills the deck's ends rest on, bedded into each bank.
    for yy in (NEAR - 0.55, FAR + 0.55):
        reb.prim("cube", "Bridge sill", post_m, ((BX0 + BX1) / 2, yy, -0.1), (BX1 - BX0 + 0.7, 0.3, 0.22), bevel=0.02)

    # ---- Grass over both banks, long on the near one where the adders lie;
    # nothing bald, nothing on the trail.
    def no_grass(x, y):
        return on_trail(x, y) or in_gorge(x, y, -0.05) or (BX0 - 0.3 < x < BX1 + 0.3 and NEAR - 0.8 < y < FAR + 0.8)
    grass = kit.grass_ground(rng, (-8, -8, 20, 26), ground_height, keep_out=no_grass, per_m2=32)
    kit.grass_ground(rng, (-30, -30, 42, 46), ground_height, keep_out=lambda x, y: no_grass(x, y) or (-8 < x < 20 and -8 < y < 26), per_m2=6)
    lv, lf = [], []
    for _ in range(420):
        cx, cy = rng.uniform(X0 - 1, X1 + 1), rng.uniform(Y0, NEAR - 0.5)
        if no_grass(cx, cy) or on_trail(cx, cy, 0.4):
            continue
        for _ in range(rng.randint(5, 10)):
            x, y = cx + rng.gauss(0, 0.08), cy + rng.gauss(0, 0.08)
            a_ = rng.uniform(0, 2 * math.pi)
            lean = Vector((math.cos(a_), math.sin(a_), 0)) * rng.uniform(0.05, 0.2)
            h = rng.uniform(0.45, 0.8)
            w = Vector((-math.sin(a_), math.cos(a_), 0)) * 0.014
            k = len(lv)
            base = Vector((x, y, ground_height(x, y)))
            lv.extend([base - w, base + w, base + lean + Vector((0, 0, h))])
            lf.append((k, k + 1, k + 2))
    long_grass = reb.mesh_object("Long grass", lv, lf, kit.mat("blades"), smooth=False)
    sways = [(ob, [Vector(p.co) for p in ob.data.vertices]) for ob in (grass, long_grass)]

    # ---- The forest: close and dense on both banks and up the mountain,
    # every trunk back from the lip, none on the trail or before a lens.
    def no_tree(x, y):
        if X0 - 1.5 < x < X1 + 1.5 and Y0 - 1.5 < y < Y1 + 0.8:
            return True
        return in_gorge(x, y, 2.2) or on_trail(x, y, 1.5) or near_lens(x, y)
    kit.forest(rng, ground_height, no_tree, (-45, -34, 60, 52), count=520, spacing=1.7, tall=(14, 22), ferns=120, needles=2500)
    kit.forest(rng, ground_height, no_tree, (-12, -16, 24, 34), count=160, spacing=1.4, tall=(12, 20), ferns=60, needles=1200)

    # ---- The trail sign on the far bank, pointing on down.
    sign_m = reb.mat_plain("Sign brown", (0.16, 0.09, 0.04), 0.7)
    letter = reb.mat_plain("Sign letters", (0.75, 0.7, 0.5), 0.6)
    reb.mask(reb.wall(reb.prim("cyl", "Trail sign post", post_m, (7.4, 17.4, 0.85), (0.14, 0.14, 1.7), segments=10), "circle"))
    reb.mask(reb.prim("cube", "Trail sign arm", sign_m, (7.0, 17.4, 1.45), (1.1, 0.05, 0.28), rot=(0, 0, 0.0), bevel=0.01))
    bpy.ops.object.text_add(location=(6.55, 17.37, 1.4), rotation=(math.pi / 2, 0, 0))
    t = bpy.context.active_object
    t.data.body = "VALLEY TRAIL"
    t.data.size = 0.13
    t.data.extrude = 0.004
    t.data.materials.append(letter)
    # Boulders at the lip, sat into the bank.
    reb.mask(kit.rocks("Lip rocks", rng, [(2.6, NEAR - 0.6, 0.6), (9.4, NEAR - 0.7, 0.8), (3.0, FAR + 0.8, 0.7), (9.0, FAR + 0.8, 0.5)], ground_height, rock))
    stones = [(rng.uniform(-4, 16), rng.uniform(-4, 22), rng.uniform(0.04, 0.12)) for _ in range(70)]
    kit.rocks("Stones", rng, [p for p in stones if not in_gorge(p[0], p[1], 0.2)], ground_height, rock, grass=False)

    # ---- Light: the morning sun low over the east end of the gorge, mist
    # lying along the bottom, the overcast, the land out to the ranges.
    kit.time_light("morning", sun_heading=140, sun_energy=6.0, mist=((6.0, 11.0, -12.0), (240.0, 9.0, 10.0), 0.012))
    kit.overcast_sky(glow=(0.7, 0.7))
    kit.backdrop((6.0, 10.0, 2.0), spread=360, below=-45.0, near=45.0, forest_to=1800.0, trees=110000,
                 keep_out=lambda x, y: math.hypot(x - 6.0, y - 10.0) < 44 or in_gorge(x, y, 2.0), shape=far_land, mist=30.0, rng=random.Random(5))
    reb.spot("Gorge light", (6.0, 11.0, 14.0), (6.0, 11.0, -12.0), 16000, (0.85, 0.85, 0.8), 80, 1, 6)
    reb.spot("Soft bank light", (6.0, 10.0, 16.0), (6.0, 10.0, 0.0), 18000, (0.9, 0.86, 0.75), 120, 1, 8)

    def pose(k):
        phase = 2 * math.pi * k / FRAMES
        # The river: the noise slides downstream, one loop of the texture per loop of frames.
        mapping.inputs["Location"].default_value = (2.0 * k / FRAMES * 2.5, 0, 0)
        # Grass: the tips barely stir.
        for ob, rest in sways:
            for idx in range(2, len(rest), 3):
                p = rest[idx]
                wv = math.sin(phase + p.x * 0.7 + p.y * 0.3)
                ob.data.vertices[idx].co = (p.x + 0.018 * wv, p.y + 0.007 * wv, p.z)
            ob.data.update()
        # The rails stir a little, most in the middle.
        for cu, poly, pts in rail_objs:
            for p, (px, py, pz) in zip(poly.points, pts):
                t = (py - NEAR + 0.5) / (FAR - NEAR + 1.0)
                p.co = (px + 0.02 * math.sin(math.pi * t) * math.sin(phase), py, pz, 1)
        for ob, rest in hangers:
            t = (rest.y - NEAR + 0.5) / (FAR - NEAR + 1.0)
            ob.location = (rest.x + 0.01 * math.sin(math.pi * t) * math.sin(phase), rest.y, ob.location.z)

    # Walkable: the whole box, less the gorge either side of the bridge.
    bounds = {"x0": reb.g(X0), "z0": reb.g(Y0), "x1": reb.g(X1), "z1": reb.g(Y1)}
    kit.wear(float(os.environ.get("RE1_WEAR", "1.3")))
    reb.export(
        CAMERAS,
        OUT,
        samples=256,
        extra={
            "bounds": bounds,
            # Underfoot (sound/ground.ts): the banks' grass and dirt, the deck's planks.
            "ground": "earth",
            "floors": [{"kind": "boards", "x0": reb.g(BX0), "z0": reb.g(NEAR - 0.7), "x1": reb.g(BX1), "z1": reb.g(FAR + 0.7)}],
            "exits": [{"x0": reb.g(5.0), "z0": 0, "x1": reb.g(7.0), "z1": reb.g(Y0) + 10}],
            "voids": [
                {"x0": reb.g(X0) - 2000, "z0": reb.g(NEAR), "x1": reb.g(BX0), "z1": reb.g(FAR)},
                {"x0": reb.g(BX1), "z0": reb.g(NEAR), "x1": reb.g(X1) + 2000, "z1": reb.g(FAR)},
            ],
        },
        anim={"frames": FRAMES, "ticks": 3, "set": pose},
    )


build()
