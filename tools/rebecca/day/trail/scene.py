"""The mountain trail, between the ridge and the ranger station, early morning.

A footpath down through the spruces. The sun is low in the east and comes
through the trunks in shafts; the night's mist is still lying in the trees.
A marker post points the way to the station. Dense forest closes the view.

Metres, real sizes, but the walkable strip keeps the game units the trail has
always had (X 2000-5000, Z 0-16000), so the ridge and the yard still meet it
where they did: x 1.18-2.94, y 0-9.41.

Moving: grass and ferns stir slightly in the wind.
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
X0, X1 = 2000 / reb.UNITS, 5000 / reb.UNITS
Y0, Y1 = 0.0, 16000 / reb.UNITS

# The cameras the trail has always had (game units): high behind the top
# looking down it, and beyond the foot looking back up.
CAMERAS = [
    {"from": (3300, -4400, -5400), "to": (3600, 0, 9000), "fov": 250, "clip_end": 2000},
    {"from": (3500, -3300, 19000), "to": (3500, -500, 11500), "fov": 250, "clip_end": 2000},
]


def height(x, y):
    """Flat on the path; banks rising either side; the mountain climbing behind the top and falling past the foot."""
    dist = 0.0 if X0 <= x <= X1 else min(abs(x - X0), abs(x - X1))
    bank = min(dist * 0.45, 5.0)
    climb = max(0.0, -y) * 0.5
    fall = -min(max(0.0, y - Y1 - 2.0) * 0.5, 12.0)
    lumps = noise.noise(Vector((x * 0.4, y * 0.4, 0.0))) * 0.5 * min(dist / 1.0, 1.0)
    ruts = 0.0
    if dist == 0.0:
        ruts = 0.012 * noise.noise(Vector((x * 3, y * 3, 7)))
    return bank + climb + fall + lumps + ruts


def build():
    rng = random.Random(51)
    reb.clear_scene()
    ground_m = reb.mat_surface("Forest floor", [(0.0, (0.03, 0.025, 0.018)), (0.4, (0.07, 0.06, 0.04)), (0.7, (0.05, 0.07, 0.03)), (1.0, (0.11, 0.1, 0.07))], scale=2.5, bump=0.6)
    dirt = reb.mat_surface("Path dirt", [(0.0, (0.06, 0.045, 0.03)), (0.35, (0.14, 0.1, 0.07)), (0.6, (0.2, 0.15, 0.1)), (0.8, (0.12, 0.1, 0.06)), (1.0, (0.24, 0.2, 0.15))], scale=14, detail=14, bump=0.9)
    rock = reb.mat_surface("Mossy rock", [(0.0, (0.06, 0.07, 0.05)), (0.5, (0.17, 0.17, 0.15)), (1.0, (0.27, 0.26, 0.23))], scale=3, bump=0.9)
    bark = reb.mat_surface("Bark", [(0.0, (0.05, 0.035, 0.025)), (1.0, (0.13, 0.09, 0.06))], scale=10, bump=0.9)
    needles = reb.mat_cards("Needles", (0.02, 0.05, 0.025), (0.07, 0.12, 0.05))
    dead = reb.mat_cards("Dry needles", (0.12, 0.09, 0.04), (0.2, 0.17, 0.08))
    blades = reb.mat_cards("Grass", (0.07, 0.1, 0.03), (0.22, 0.24, 0.08))
    ferns = reb.mat_cards("Fern", (0.04, 0.09, 0.03), (0.1, 0.18, 0.05))
    logs = reb.mat_wood("Fallen log", (0.16, 0.11, 0.07))
    post_m = reb.mat_wood("Post", (0.2, 0.13, 0.07))
    letter = reb.mat_plain("Marker paint", (0.85, 0.75, 0.3), 0.6)

    reb.terrain("Ground", ground_m, (-14, 20), (-14, 30), height, step=0.3)
    # The path: dirt down the strip, a little wider than she can walk.
    v, f = [], []
    n = 60
    for i in range(n):
        y0, y1 = -18 + (Y1 + 60) * i / n, -18 + (Y1 + 60) * (i + 1) / n
        w0 = 0.15 + 0.1 * noise.noise(Vector((0, y0, 3)))
        w1 = 0.15 + 0.1 * noise.noise(Vector((0, y1, 3)))
        k = len(v)
        for x, y, w in ((X0 - w0, y0, 0), (X1 + w0, y0, 0), (X1 + w1, y1, 0), (X0 - w1, y1, 0)):
            v.append((x, y, height(x, y) + 0.01))
        f.append((k, k + 1, k + 2, k + 3))
    reb.mesh_object("Path", v, f, dirt)
    # Roots across the path and stones in it.
    for i in range(7):
        y = rng.uniform(1.0, Y1 - 0.5)
        reb.prim("cyl", "Root", bark, ((X0 + X1) / 2, y, 0.02), (0.06, 0.06, X1 - X0 + 1.2), rot=(0, math.pi / 2, rng.uniform(-0.4, 0.4)), segments=8)
    sv, sf = [], []
    for _ in range(30):
        x, y = rng.uniform(X0, X1), rng.uniform(-2, Y1 + 3)
        reb.boulder(rng, (x, y, height(x, y)), rng.uniform(0.03, 0.08), sv, sf)
    for (x, y, r) in ((X0 - 1.2, 2.5, 0.45), (X1 + 1.4, 5.5, 0.55), (X0 - 1.5, 7.8, 0.4), (X1 + 1.1, 1.0, 0.35), (X1 + 1.8, 9.8, 0.5)):
        reb.boulder(rng, (x, y, height(x, y)), r, sv, sf)
    reb.mesh_object("Rocks", sv, sf, rock)
    lv, lf = [], []
    for _ in range(500):
        x, y = rng.uniform(X0 - 0.2, X1 + 0.2), rng.uniform(-3, Y1 + 4)
        reb.card(lv, lf, Vector((x, y, height(x, y) + 0.015)), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), Vector((0, 0, 1)), 0.03, rng.uniform(0.1, 0.25), 0.0)
    reb.mesh_object("Twigs and needles", lv, lf, dead)
    # A fallen spruce along the west bank, and the marker post at the turn.
    reb.prim("cyl", "Fallen log", bark, (X0 - 1.6, 4.6, height(X0 - 1.6, 4.6) + 0.25), (0.5, 0.5, 7.0), rot=(math.pi / 2, 0, 0.12), segments=14)
    reb.prim("cyl", "Log end", logs, (X0 - 1.6 - 0.42, 4.6 - 3.48, height(X0 - 1.6, 4.6) + 0.25), (0.48, 0.48, 0.02), rot=(math.pi / 2, 0, 0.12), segments=14)
    reb.mask(reb.wall(reb.prim("cube", "Marker post", post_m, (X1 + 0.35, 6.2, 0.6), (0.14, 0.14, 1.2), bevel=0.01)))
    reb.prim("cube", "Marker arrow", letter, (X1 + 0.35, 6.12, 0.95), (0.1, 0.012, 0.22))
    bpy.ops.object.text_add(location=(X1 + 0.3, 6.12, 0.62), rotation=(math.pi / 2, 0, 0))
    t = bpy.context.active_object
    t.data.body = "STN 3"
    t.data.size = 0.07
    t.data.extrude = 0.003
    t.data.materials.append(letter)

    # Spruces on the banks, real sizes, kept off the path.
    tv, tf, bases = [], [], []
    tries = 0
    while len(bases) < 85 and tries < 6000:
        tries += 1
        x, y = rng.uniform(-13, 19), rng.uniform(-13, 29)
        if X0 - 2.2 < x < X1 + 2.2:
            continue
        if any((Vector((x, y)) - b.xy).length < 1.7 for b, _ in bases):
            continue
        bases.append((Vector((x, y, height(x, y) - 0.2)), rng.uniform(12, 20)))
    for base, h in bases:
        reb.conifer(rng, base, h, tv, tf)
    reb.mesh_object("Spruces", tv, tf, needles)
    reb.trunks("Spruce trunks", bark, bases)
    # Grass and ferns on the banks and along the path's edges.
    gv, gf = [], []
    def banks(rr):
        while True:
            x, y = rr.uniform(X0 - 4, X1 + 4), rr.uniform(-4, Y1 + 5)
            if X0 - 0.4 < x < X1 + 0.4:
                continue
            return x, y
    reb.grass_tufts(rng, 7500, banks, height, gv, gf)
    grass = reb.mesh_object("Grass", gv, gf, blades, smooth=False)
    grass_rest = [Vector(p) for p in gv]
    fv, ff = [], []
    for _ in range(40):
        x = rng.choice((rng.uniform(X0 - 4, X0 - 0.4), rng.uniform(X1 + 0.4, X1 + 4)))
        y = rng.uniform(-4, Y1 + 5)
        reb.fern(rng, (x, y, height(x, y)), rng.uniform(0.4, 0.8), fv, ff)
    fern_ob = reb.mesh_object("Ferns", fv, ff, ferns)
    fern_rest = [(Vector(p), max(0.0, p[2] - height(p[0], p[1]))) for p in fv]
    dv, df = [], []
    for _ in range(1200):
        x, y = rng.uniform(-6, 9), rng.uniform(-6, Y1 + 8)
        reb.card(dv, df, Vector((x, y, height(x, y) + 0.01)), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), Vector((0, 0, 1)), 0.08, 0.3, 0.0)
    reb.mesh_object("Fallen needles", dv, df, dead)

    kit.tree_roots(rng, bases, height, lambda x, y: X0 - 0.4 < x < X1 + 0.4)
    kit.mountain_forest(rng, (3, 5), near=24, below=-50)
    # Forest continues beyond both ends of the path, with a narrow dark exit.
    kit.forest(rng, height, lambda x, y: X0 - 0.8 < x < X1 + 0.8,
               (-24, -28, 28, 48), count=160, spacing=2, ferns=40)
    kit.time_light("morning", sun_heading=105, sun_energy=4.0)

    reb.spot("Soft trail light", (3, 4, 10), (3, 5, 0), 6000, (0.9,0.85,0.7), 120, 1, 5)

    reb.spot("Upper trail fill", (3, 12, 7), (3, 8, 0), 3000, (0.8,0.88,1.0), 120, 1, 5)

    def pose(k):
        phase = 2 * math.pi * k / FRAMES
        for idx in range(2, len(grass_rest), 3):
            p = grass_rest[idx]
            wv = math.sin(phase + p.x * 0.6 + p.y * 0.3)
            grass.data.vertices[idx].co = (p.x + 0.018 * wv, p.y + 0.007 * wv, p.z)
        grass.data.update()
        for idx, (p, above) in enumerate(fern_rest):
            sway = 0.012 * math.sin(phase + p.y * 0.5) * above
            fern_ob.data.vertices[idx].co = (p.x + sway, p.y, p.z)
        fern_ob.data.update()
    # The kit's worn, bitty surfaces, as every kit room has.

    kit.wear(float(os.environ.get("RE1_WEAR", "1.3")))

    reb.export(
        CAMERAS,
        OUT,
        samples=256,
        extra={
            "bounds": {"x0": 2000, "z0": 0, "x1": 5000, "z1": 16000},
            # Underfoot (sound/ground.ts): the dirt path.
            "ground": "earth",
            "floors": [],
        },
        anim={"frames": FRAMES, "ticks": 3, "set": pose},
    )


build()
