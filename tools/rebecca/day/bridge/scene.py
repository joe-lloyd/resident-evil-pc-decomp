"""The ravine bridge, below the ranger station, mid-morning.

The trail comes down from the station to the lip of a gorge and crosses it
on an old plank footbridge hung on two rope rails. A river runs white far
below. The near bank is long grass, where the adders are. On the far bank
the trail goes on down into the valley.

Metres, real sizes. She walks the near bank (x 2-10, y 2-7), the bridge
(x 5.3-6.7, y 7-15, the deck flat at z 0) and the far bank (x 2-10, y 15-18).

Moving: the river, the grass, the rope rails in the wind.
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
NEAR, FAR = 7.0, 15.0           # the gorge's lips (y)
BX0, BX1 = 5.3, 6.7             # the bridge deck (x)
RIVER_Z = -16.0


def G(x, y, z=0.0):
    return (reb.g(x), -reb.g(z), reb.g(y))


CAMERAS = [
    # 0: from the trail coming down, over the near bank, along the bridge into the mist.
    {"from": G(8.6, -1.6, 4.2), "to": G(5.6, 8.5, -0.8), "fov": 200, "clip_end": 2000},
    # 1: from out over the gorge, side on: the bridge, the drop, the river.
    {"from": G(0.4, 9.6, 7.4), "to": G(6.0, 11.4, -4.5), "fov": 200, "clip_end": 2000},
    # 2: from the far bank, back across the bridge toward the station.
    {"from": G(2.5, 20.5, 4.3), "to": G(6.2, 9.5, -0.3), "fov": 200, "clip_end": 2000},
]


def gorge(x, y):
    """Flat on the banks; cliffs drop into the gorge between NEAR and FAR."""
    h = 0.02 * noise.noise(Vector((x * 0.8, y * 0.8, 0)))
    if NEAR < y < FAR:
        d = min(y - NEAR, FAR - y)
        # Continuous weathered walls, steep at the rim and rounded below.
        # Erosion follows irregular vertical gullies rather than masonry courses.
        t = (y - NEAR) / (FAR - NEAR)
        profile = math.sin(math.pi * t) ** 0.42
        grain = noise.noise(Vector((x * 0.38, y * 0.22, 5)))
        fissure = abs(noise.noise(Vector((x * 1.1, y * 0.08, 2))))
        h -= profile * (abs(RIVER_Z) + 1.7 + grain * 1.2 + fissure * 0.5)
    else:
        if x < X0 - 0.5:
            h += (X0 - 0.5 - x) * 0.15
        if x > X1 + 0.5:
            h += (x - X1 - 0.5) * 0.3
        if y < Y0 - 0.5:
            h += (Y0 - 0.5 - y) * 0.5
        if y > Y1 + 0.3:
            h -= (y - Y1 - 0.3) * 0.3
    return h


def build():
    rng = random.Random(41)
    reb.clear_scene()
    grass_m = reb.mat_surface("Meadow", [(0.0, (0.06, 0.08, 0.025)), (0.5, (0.13, 0.15, 0.05)), (1.0, (0.2, 0.18, 0.09))], scale=1.5, bump=0.4)
    rock = reb.mat_surface("Gorge rock", [(0.0, (0.05, 0.05, 0.045)), (0.45, (0.105, 0.10, 0.075)), (0.7, (0.18, 0.17, 0.125)), (1.0, (0.26, 0.24, 0.19))], scale=3.5, detail=14, bump=1.0)
    dirt = reb.mat_surface("Dirt", [(0.0, (0.1, 0.075, 0.05)), (1.0, (0.2, 0.15, 0.1))], scale=6, bump=0.6)
    plank_m = reb.mat_wood("Bridge planks", (0.22, 0.17, 0.12))
    post_m = reb.mat_wood("Posts", (0.18, 0.12, 0.07))
    rope = reb.mat_surface("Rope", [(0.0, (0.3, 0.25, 0.16)), (1.0, (0.45, 0.38, 0.24))], scale=60, bump=0.6)
    bark = reb.mat_surface("Bark", [(0.0, (0.05, 0.035, 0.025)), (1.0, (0.13, 0.09, 0.06))], scale=10, bump=0.9)
    needles = reb.mat_cards("Needles", (0.02, 0.05, 0.025), (0.07, 0.12, 0.05))
    blades = reb.mat_cards("Grass", (0.07, 0.1, 0.03), (0.24, 0.25, 0.09))
    ferns = reb.mat_cards("Fern", (0.04, 0.09, 0.03), (0.1, 0.18, 0.05))

    # Ground: the banks and the gorge in one, rock below the lip, grass above.
    ground = reb.terrain("Banks", grass_m, (-40, 50), (-12, 36), gorge, step=0.3)
    ground.data.materials.append(rock)
    for poly in ground.data.polygons:
        c = poly.center
        if NEAR - 0.6 < c.y < FAR + 0.6 and (c.z < -0.25 or abs(poly.normal.z) < 0.6):
            poly.material_index = 1
    paths = [[(12,-30),(10,-10),(9,-2),(7.5,3.5),(6,NEAR)],
             [(6,FAR),(5,22),(3,36),(-2,52)]]
    for i,path in enumerate(paths):
        kit.path_strip(f"Continuous trail {i}", dirt, path, gorge, width=0.72, wobble=0.1)

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
    reb.prim("plane", "River", river_m, (6.0, (NEAR + FAR) / 2, RIVER_Z + 0.4), (100, 3.2, 1), rot=(0, 0, 0.0))

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

    # Grass where the adders lie, ferns, spruces back from the edge, a dead tree.
    gv, gf = [], []
    def bank(rr):
        while True:
            x, y = rr.uniform(-20, 30), rr.uniform(-12, 36)
            if NEAR - 0.2 < y < FAR + 0.2:
                continue
            if kit.path_distance(x,y,paths) < 1.02:
                continue
            return x, y
    reb.grass_tufts(rng, 16000, bank, gorge, gv, gf)
    # Long grass on the near bank: taller tufts.
    lv, lf = [], []
    for _ in range(500):
        cx, cy = rng.uniform(X0 - 1, X1 + 1), rng.uniform(Y0, NEAR - 0.4)
        if kit.path_distance(cx,cy,paths) < 1.1:
            continue
        for _ in range(rng.randint(5, 10)):
            x, y = cx + rng.gauss(0, 0.08), cy + rng.gauss(0, 0.08)
            a = rng.uniform(0, 2 * math.pi)
            lean = Vector((math.cos(a), math.sin(a), 0)) * rng.uniform(0.05, 0.2)
            h = rng.uniform(0.45, 0.8)
            w = Vector((-math.sin(a), math.cos(a), 0)) * 0.014
            k = len(lv)
            b = Vector((x, y, gorge(x, y)))
            lv.extend([b - w, b + w, b + lean + Vector((0, 0, h))])
            lf.append((k, k + 1, k + 2))
    grass = reb.mesh_object("Grass", gv + lv, gf + [tuple(i + len(gv) for i in t) for t in lf], blades, smooth=False)
    grass_rest = [Vector(p) for p in gv + lv]
    fv, ff = [], []
    for _ in range(18):
        x, y = rng.uniform(-2, 13), rng.choice((rng.uniform(-1, 6.5), rng.uniform(17.5, 23)))
        if abs(x - 6) > 1.5:
            reb.fern(rng, (x, y, gorge(x, y)), rng.uniform(0.4, 0.8), fv, ff)
    reb.mesh_object("Ferns", fv, ff, ferns)
    tv, tf, bases = [], [], []
    tries = 0
    while len(bases) < 110 and tries < 6000:
        tries += 1
        x, y = rng.uniform(-30, 40), rng.uniform(-12, 36)
        if NEAR - 1.0 < y < FAR + 1.0:
            continue
        if -1.0 < x < 13.0 and -3.0 < y < NEAR + 0.5:
            continue
        if -1.0 < x < 13.0 and FAR - 0.5 < y < 23.0:
            continue
        if any((Vector((x, y)) - b.xy).length < 1.8 for b, _ in bases):
            continue
        bases.append((Vector((x, y, gorge(x, y) - 0.2)), rng.uniform(10, 18)))
    for base, h in bases:
        reb.conifer(rng, base, h, tv, tf)
    reb.mesh_object("Spruces", tv, tf, needles)
    reb.trunks("Spruce trunks", bark, bases)
    # The trail sign on the far bank, pointing on down.
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
    # Rocks at the lip.
    rv2, rf2 = [], []
    for (x, y, r_) in ((2.6, NEAR - 0.3, 0.6), (9.4, NEAR - 0.4, 0.8), (3.0, FAR + 0.5, 0.7), (9.0, FAR + 0.6, 0.5)):
        reb.boulder(rng, (x, y, 0.0), r_, rv2, rf2)
    reb.mask(reb.mesh_object("Lip rocks", rv2, rf2, rock))
    kit.tree_roots(rng, bases, gorge, lambda x,y: kit.path_distance(x,y,paths)<1.02)
    def forest_keep(x,y):
        return (NEAR-1.0 < y < FAR+1.0 or kit.path_distance(x,y,paths)<2.2
                or (-1<x<13 and -3<y<23))
    kit.forest(rng,gorge,forest_keep,(-40,-30,50,60),count=230,spacing=2.2,ferns=50)
    kit.mountain_forest(rng,(6,11),near=48,below=-90)
    kit.time_light("morning",sun_heading=140,sun_energy=4.0)

    reb.spot("Bank sky fill",(6,11,14),(6,11,0),6000,(0.85,0.88,0.78),130,1,8)

    def pose(k):
        phase = 2 * math.pi * k / FRAMES
        # The river: the noise slides downstream, one loop of the texture per loop of frames.
        mapping.inputs["Location"].default_value = (2.0 * k / FRAMES * 2.5, 0, 0)
        # Grass in the wind.
        for idx in range(2, len(grass_rest), 3):
            p = grass_rest[idx]
            wv = math.sin(phase + p.x * 0.7 + p.y * 0.3)
            grass.data.vertices[idx].co = (p.x + 0.018 * wv, p.y + 0.007 * wv, p.z)
        grass.data.update()
        # The rails swing out a little, most in the middle.
        for cu, poly, pts in rail_objs:
            for p, (px, py, pz) in zip(poly.points, pts):
                t = (py - NEAR + 0.5) / (FAR - NEAR + 1.0)
                p.co = (px + 0.018 * math.sin(math.pi * t) * math.sin(phase), py, pz, 1)
        for ob, rest in hangers:
            t = (rest.y - NEAR + 0.5) / (FAR - NEAR + 1.0)
            ob.location = (rest.x + 0.009 * math.sin(math.pi * t) * math.sin(phase), rest.y, ob.location.z)

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
