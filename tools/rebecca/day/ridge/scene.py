"""Rebecca alone at dawn after Billy has left. From the cliff edge she looks
across wooded hills to the Spencer mansion, a dark roof among the trees.
The rock face closes the back and west of the clearing. The only way down
is the worn path east, between the rock shoulder and the pines.

Moving: grass bends in the wind. Distant hills fade into the dawn haze.
Game units: the clearing floor is X 3900-11000, Z 3000-10000, Y = 0;
the east exit is X 11000-13000, Z 3800-6800. RE1_OUT names the output.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402

# Laid out when a metre was taken as 1000 units, and its world stays that
# way (reb.UNITS = 1000): the cameras, the clearing and the valley keep their
# places. What grows or lies in it is GROW (1700 / 1000) times its real size,
# so it stands right next to her (reb.UNITS has the measured scale), and the
# trees stand back from the clearing to leave the view open.
reb.UNITS = 1000.0
GROW = 1.7
FRAMES = 16
from mathutils import Vector, noise  # noqa: E402

OUT = os.environ.get("RE1_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders"))

CAMERAS = [
    # 0: from the back of the clearing, out over the edge to the valley.
    {"from": (5600, -4300, 2400), "to": (8600, 2600, 20000), "fov": 240, "clip_end": 2000},
    # 1: from the cliff edge, back at the rock face and the trail out (east).
    {"from": (5200, -3200, 11200), "to": (8300, -400, 3500), "fov": 250},
]


def ground_height(x, y):
    """Metres. The clearing is flat; the rock face rises behind (y < 3), the
    slope climbs gently either side, and past the edge (y > 10) the mountain
    falls away to the valley."""
    h = 0.0
    if y < 3.0:
        h += min(2.0, (3.0 - y) * 0.7)
    if x < 3.0:
        h += (3.0 - x) * 0.35
    if x > 11.0 and not (3.8 < y < 6.8):
        h += (x - 11.0) * 0.3
    if y > 10.0:
        # The mountain falls away below the edge, steep at first, to a valley
        # floor some 80 m down.
        d = y - 10.0
        h -= 80.0 * (1.0 - math.exp(-d / 9.0))
    lumps = noise.noise(Vector((x * 0.4, y * 0.4, 0))) * 0.35 + noise.noise(Vector((x * 1.9, y * 1.9, 5))) * 0.06
    # The clearing floor stays nearly flat: the game's floor is Y = 0 everywhere.
    inside = 3.0 <= x <= 11.0 and 3.0 <= y <= 10.0
    return h + lumps * (0.15 if inside else 1.0)


def build():
    rng = random.Random(31)
    reb.clear_scene()
    earth = reb.mat_surface("Earth", [(0.0, (0.03, 0.025, 0.02)), (0.4, (0.09, 0.07, 0.05)), (0.7, (0.06, 0.07, 0.04)), (1.0, (0.13, 0.11, 0.09))], scale=3)
    rock = reb.mat_surface("Rock", [(0.25, (0.04, 0.04, 0.04)), (0.5, (0.12, 0.115, 0.11)), (0.7, (0.2, 0.19, 0.18)), (0.9, (0.07, 0.08, 0.05))], scale=1.8, detail=14, bump=1.2)
    needles = reb.mat_cards("Needles", (0.012, 0.03, 0.018), (0.06, 0.12, 0.06))
    grass = reb.mat_cards("Grass", (0.04, 0.05, 0.02), (0.14, 0.15, 0.07))
    bark = reb.mat_wood("Bark", (0.07, 0.05, 0.035))

    reb.terrain("Mountain top", earth, (-30, 45), (-25, 60), ground_height, step=0.45)

    # The rock face behind the clearing: a cliff, its face displaced into
    # ledges and cracks, with fallen boulders at its foot.
    verts, faces = [], []
    nx, nz = 90, 40
    for j in range(nz + 1):
        z = -1.0 + 16.0 * j / nz
        for i in range(nx + 1):
            x = -6.0 + 26.0 * i / nx
            ledge = noise.noise(Vector((x * 0.25, 0, z * 0.6))) * 1.4 + noise.noise(Vector((x * 1.3, 3, z * 1.3))) * 0.35
            y = 1.6 - 0.12 * z + ledge - max(0.0, (z - 9.0)) * 0.5
            verts.append((x, y, z))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    reb.wall(reb.mesh_object("Rock face", verts, faces, rock))
    verts, faces = [], []
    for i in range(14):
        x = rng.uniform(-1, 15)
        y = rng.uniform(2.2, 3.0)
        reb.boulder(rng, (x, y, ground_height(x, y) + 0.2), rng.uniform(0.35, 0.9) * GROW, verts, faces)
    reb.mesh_object("Fallen rocks", verts, faces, rock)
    # Boulders in the clearing, two near camera 1 that she can walk behind.
    for name, (x, y, r, in_front) in {
        "Boulder west": (4.0, 8.2, 0.7, True),
        "Boulder east": (9.6, 8.6, 0.6, True),
        "Boulder north": (8.6, 4.2, 0.55, False),
    }.items():
        verts, faces = [], []
        reb.boulder(rng, (x, y, ground_height(x, y) + r * 0.3 * GROW), r * GROW, verts, faces)
        ob = reb.wall(reb.mesh_object(name, verts, faces, rock), "circle")
        if in_front:
            reb.mask(ob)

    # Close the false west path with rock, rooted below the clearing.
    # Each piece exports its own footprint, rather than one box over the path.
    for i, y in enumerate((3.0, 5.0, 7.0)):
        v, f = [], []
        reb.boulder(rng, (1.6, y, 1.0), 2.0, v, f)
        reb.wall(reb.mesh_object(f"West rock shoulder {i}", v, f, rock))

    v, f = [], []
    reb.boulder(rng, (4.0, 2.5, 1.2), 1.7, v, f)
    reb.wall(reb.mesh_object("West path rockfall", v, f, rock))

    # A worn strip leads to the single east exit, at floor height throughout.
    path_m = reb.mat_surface("Worn trail", [(0.0, (0.08, 0.065, 0.045)), (1.0, (0.2, 0.16, 0.1))], scale=5)
    v, f = [], []
    for i in range(16):
        x = 8.8 + i * 0.65
        lo, hi = 4.5 + 0.12 * math.sin(i), 6.2 + 0.12 * math.sin(i)
        k = len(v)
        v += [(x, lo, 0.035), (x + 0.65, lo, 0.035), (x + 0.65, hi, 0.035), (x, hi, 0.035)]
        f.append((k, k + 1, k + 2, k + 3))
    reb.mesh_object("Trail east", v, f, path_m)

    # Pines around the clearing: the west edge, the east edge either side of
    # the trail out, and the forest down the valley.
    needle_v, needle_f, bases = [], [], []
    ring = []
    for _ in range(30):
        x, y = rng.uniform(18, 27), rng.uniform(8.5, 19)
        if y < 10 and x < 21:
            continue  # the trail out
        ring.append((x, y))
    for x, y in ring:
        h = rng.uniform(8, 14) * GROW
        base = Vector((x, y, ground_height(x, y) - 0.2))
        reb.conifer(rng, base, h, needle_v, needle_f)
        bases.append((base, h))
    reb.mesh_object("Pines", needle_v, needle_f, needles, smooth=False)
    # The pines' footprint is the clearing's edge (room.json "bounds"), not their own.
    reb.trunks("Pine trunks", bark, bases)

    # Continuous wooded hills under the canopy. Camera 0 has a longer
    # render far plane so the panorama closes below and beside the view.
    def valley_height(x, y):
        return (78 * math.exp(-((x-108)/100)**2-((y-635)/95)**2) -80 + min(35, max(0, y - 160) * 0.12) + 11 * math.sin(x * 0.022 + y * 0.014)
                + 9 * math.sin(y * 0.045) + 5 * noise.noise(Vector((x * 0.03, y * 0.03, 2))))
    far_ground = reb.mat_surface("Wooded hills", [(0.0, (0.018, 0.035, 0.025)), (1.0, (0.07, 0.1, 0.055))], scale=0.1, bump=0.0)
    reb.terrain("Valley hills", far_ground, (-650, 650), (45, 900), valley_height, step=4)
    forests = [([], []) for _ in range(3)]
    for _ in range(60000):
        x, y = rng.uniform(-450, 480), rng.uniform(19, 760)
        z = ground_height(x, y) if y < 45 else valley_height(x, y)
        # A small break in the canopy leaves the mansion's roof readable.
        if abs(x - 108) < 28 and 595 < y < 668:
            continue
        v, f = forests[0 if y < 160 else 1 if y < 350 else 2]
        h = rng.uniform(7, 14)
        # Three tiers keep the canopy from looking like a field of cones.
        for tier in range(3):
            base = z + tier * h * 0.23
            tip = z + h * (0.65 + tier * 0.175)
            radius = h * (0.26 - tier * 0.055)
            k = len(v)
            v.append((x, y, tip))
            for side in range(6):
                a = 2 * math.pi * side / 6
                v.append((x + math.cos(a) * radius, y + math.sin(a) * radius, base))
            for side in range(6):
                f.append((k, k + 1 + side, k + 1 + (side + 1) % 6))
    for i, (v, f) in enumerate(forests):
        lo, hi = (((0.012, 0.03, 0.021), (0.055, 0.095, 0.05)),
                  ((0.035, 0.06, 0.05), (0.08, 0.115, 0.08)),
                  ((0.075, 0.1, 0.09), (0.12, 0.15, 0.12)))[i]
        reb.mesh_object(f"Valley forest {i}", v, f, reb.mat_cards(f"Far needles {i}", lo, hi), smooth=False)

    # Spencer mansion: broad wings, steep roofs, a central pediment and
    # chimneys. Big roof shapes survive the distance at 320 x 240.
    base = Vector((108, 635, valley_height(108, 635) + 1))
    v, f = [], []
    for off, size in (((0, 0, 5), (40, 17, 10)), ((-17, 1, 5.5), (10, 20, 11)), ((17, 1, 5.5), (10, 20, 11)), ((0, -9, 6), (12, 3, 12))):
        reb.box(v, f, tuple(base + Vector(off)), size)
    def roof(cx, cy, w, d, eave, peak):
        k = len(v)
        v.extend(tuple(base + Vector(p)) for p in ((cx-w/2, cy-d/2, eave), (cx+w/2, cy-d/2, eave), (cx+w/2, cy+d/2, eave), (cx-w/2, cy+d/2, eave), (cx, cy-d/2, peak), (cx, cy+d/2, peak)))
        f.extend(tuple(k+i for i in face) for face in ((0,1,4), (3,5,2), (0,4,5,3), (1,2,5,4)))
    roof(0, 0, 42, 19, 10, 16)
    roof(-17, 0, 12, 22, 11, 18)
    roof(17, 0, 12, 22, 11, 18)
    roof(0, -10, 14, 4, 12, 17)
    for x in (-16, -10, 10, 16):
        reb.box(v, f, tuple(base + Vector((x, 2, 17))), (1.8, 2, 7))
    reb.mesh_object("Spencer mansion", v, f, reb.mat_plain("Mansion silhouette", (0.018, 0.021, 0.024), 1.0), smooth=False)

    v, f = [], []
    for x in (-13, -5, 6, 14):
        reb.box(v, f, tuple(base + Vector((x, -8.6, 6))), (1.4, 0.12, 2.0))
    reb.mesh_object("Distant mansion windows", v, f, reb.mat_emit("Few lit windows", (0.8, 0.47, 0.18), 2.5), smooth=False)

    # Grass about the clearing.
    gv, gf = [], []
    def patchy(r):
        while True:
            x, y = r.uniform(2.5, 11.5), r.uniform(2.6, 10.3)
            if not (x > 9 and 4.3 < y < 6.4) and noise.noise(Vector((x * 0.35, y * 0.35, 9))) > -0.1:
                return x, y
    reb.grass_tufts(rng, 1800, patchy, ground_height, gv, gf)
    # Tufts made for a 1000-unit metre: stretch them up to her scale.
    for i in range(2, len(gv), 3):
        b = (Vector(gv[i - 2]) + Vector(gv[i - 1])) / 2
        gv[i] = tuple(b + (Vector(gv[i]) - b) * GROW)
    # Stones scattered over the bare patches.
    sv, sf = [], []
    for _ in range(60):
        x, y = rng.uniform(3.0, 11.0), rng.uniform(3.2, 10.0)
        r = rng.uniform(0.05, 0.16) * GROW
        reb.boulder(rng, (x, y, ground_height(x, y)), r, sv, sf, squash=0.6)
    reb.mesh_object("Stones", sv, sf, rock)
    grass_ob = reb.mesh_object("Grass", gv, gf, grass, smooth=False)
    grass_rest = [Vector(p) for p in gv]
    # Broad ridges extend past both sides of the view and close beneath
    # the valley. Keep the far plane beyond their lowest visible surfaces.
    for i, (dist, top) in enumerate(((680, 50), (800, 70), (950, 90))):
        v, f = [], []
        for j in range(81):
            x = -1200 + 2400 * j / 80
            peak = -65 + top * (0.7 + 0.25 * math.sin(x * 0.018 + i * 3) + 0.12 * noise.noise(Vector((x * 0.03, i, 0))))
            v.extend(((x, dist, -350), (x, dist, peak)))
        for j in range(80):
            k = j * 2
            f.append((k, k + 2, k + 3, k + 1))
        col = (0.045 + i * 0.012, 0.065 + i * 0.012, 0.065 + i * 0.014)
        ridge = reb.mesh_object(f"Distant wooded ridge {i}", v, f, reb.mat_emit(f"Haze ridge {i}", col, 0.7))
        ridge.visible_shadow = False

    kit.time_light("dawn")
    # A soft key on the clearing, from the cameras' side, for the RE look.
    reb.spot("Key", (7.0, 3.5, 9.0), (7.0, 8.0, 0.0), 2500, (1.0, 0.8, 0.65), 110, 1.0, 2.0)
    reb.spot("Back key", (6.0, 11.0, 8.0), (8.0, 4.0, 0.0), 1800, (0.8, 0.85, 1.0), 110, 1.0, 2.0)

    def pose(k):
        t = k / FRAMES
        phase = 2 * math.pi * t
        for idx in range(2, len(grass_rest), 3):
            p = grass_rest[idx]
            w = math.sin(phase + p.x * 0.7 + p.y * 0.4)
            grass_ob.data.vertices[idx].co = (p.x + 0.025 * w, p.y + 0.01 * w, p.z)
        grass_ob.data.update()

    # The kit's worn, bitty surfaces, as every kit room has.

    kit.wear(float(os.environ.get("RE1_WEAR", "1.3")))

    reb.export(
        CAMERAS,
        OUT,
        anim={"frames": FRAMES, "ticks": 3, "set": pose},
        extra={
            # Clearing bounds close the cliff and west shoulder. Only the
            # east trail opens them; tagged rock supplies its own collision.
            "bounds": {"x0": 3900, "z0": 3000, "x1": 11000, "z1": 10000},
            # Underfoot (sound/ground.ts): the clearing's earth.
            "ground": "earth",
            "floors": [],
            "exit": {"x0": 11000, "z0": 3800, "x1": 13000, "z1": 6800},
        },
    )


build()
