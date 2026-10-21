"""Rebecca alone at dawn after Billy has left. From the cliff edge she looks
down over forested ridges that fall away in layers into valley mist, to
long, low, rolling ranges fading into the haze under a heavy overcast sky
(kit.backdrop, kit.overcast_sky: the RE0 look). Miles off, tight against a
wooded slope across the valley, the Spencer mansion: its long brown mansard
roof, the gabled centre and a chimney at each end (kit.spencer_mansion).
The rock face closes the back and west of the clearing. The only way down
is the worn path east, between the rock shoulder and the pines.

Moving: grass bends in the wind.
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
import bpy  # noqa: E402
from mathutils import Vector, noise  # noqa: E402

OUT = os.environ.get("RE1_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders"))

CAMERAS = [
    # 0: from the back of the clearing, out over the edge to the valley.
    {"from": (5600, -4300, 2400), "to": (8600, 2600, 20000), "fov": 240, "clip_end": 16000},
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


# ---------------------------------------------------------------------------
# The view from the edge (camera 0): forested ridges falling away in layers,
# bluer and paler with distance, mist in the valleys between them, far peaks
# against a dawn sky, and the Spencer mansion small on a far slope.
# ---------------------------------------------------------------------------

EYE = Vector((5.6, 2.4, 4.3))  # camera 0, metres
LOOK = (Vector((8.6, 20.0, -2.6)) - EYE).normalized()
PITCH = math.asin(-LOOK.z)
YAW = math.atan2(LOOK.x, LOOK.y)
FOCAL = 240.0  # pixels: a 24 mm lens on the 32 mm sensor, 320 wide

def _row_angle(row):
    """Angle below the horizon of picture row `row` at the centre column."""
    return PITCH - math.atan((120 - row) / FOCAL)


def _height_at_row(row, dist):
    return EYE.z - dist * math.tan(_row_angle(row))


def _ground_at(column, row, dist):
    """The point at `dist` metres ahead that camera 0 sees at (column, row)."""
    a = YAW + math.atan((column - 160) / FOCAL)
    return Vector((EYE.x + math.sin(a) * dist, EYE.y + math.cos(a) * dist, _height_at_row(row, dist)))


# The ranges past the edge, nearest first, as kit.backdrop takes them. Each
# crest is designed on camera 0's 320 x 240 picture as (column, row) points
# and turned into (degrees across, degrees above eye level), so every layer
# lands where it should: two near spurs framing the view, the middle ridge,
# the mansion's slope, then long, low, rolling ranges, each showing over the
# one before it, fading into the haze.
def _picture(points):
    return [(math.degrees(math.atan((c - 160) / FOCAL)), -math.degrees(_row_angle(r))) for c, r in points]


RANGES = [
    {"at": 380, "depth": 260, "roll": 0.3, "rise": _picture([(-80, 60), (30, 66), (110, 94), (175, 132)])},
    {"at": 540, "depth": 320, "roll": 0.3, "rise": _picture([(150, 132), (230, 100), (300, 78), (400, 70)])},
    {"at": 880, "depth": 380, "roll": 0.35, "rise": _picture([(-80, 74), (60, 80), (150, 88), (200, 96), (260, 86), (400, 80)])},
    {"at": 1650, "depth": 900, "roll": 0.3, "wander": 0.2, "rise": _picture([(-80, 50), (90, 45), (170, 41), (215, 38), (300, 46), (400, 44)])},
    {"at": 3000, "depth": 1100, "roll": 0.8, "rise": _picture([(-80, 37), (90, 33), (250, 36), (400, 33)])},
    {"at": 5600, "depth": 1700, "roll": 1.4, "rise": _picture([(-80, 29), (160, 27), (400, 29)])},
    {"at": 9000, "depth": 2500, "roll": 1.6, "rise": _picture([(-80, 22), (120, 19), (400, 21)])},
    {"at": 13000, "depth": 2800, "roll": 1.3, "rise": _picture([(-80, 17), (400, 17)])},
]
# The mansion: its picture column and row, and its distance. It stands on
# the land there, so the row is where the design aims, not where it lands.
MANSION = (204, 54, 1300)
MANSION_TURN = math.radians(12.0)
MANSION_SCALE = 1.5


MANSION_AT = _ground_at(*MANSION)


def _valley(x, y, z):
    """The ridge's own land under the kit's: the valley floor runs on from
    the foot of the cliff."""
    return max(z, -85.0 - 175.0 * (1.0 - math.exp(-(y - 40.0) / 140.0)) - 0.004 * y)


def _mansion_grounds(x, y):
    """No tree on the house, and a lawn before it so its front shows from
    the ridge; the forest closes tight on its sides and back."""
    dx, dy = x - MANSION_AT.x, y - MANSION_AT.y
    c, s = math.cos(-MANSION_TURN), math.sin(-MANSION_TURN)
    lx, ly = dx * c - dy * s, dx * s + dy * c
    if abs(lx) < 50 * MANSION_SCALE + 6 and -18 * MANSION_SCALE - 6 < ly < 8 * MANSION_SCALE + 5:
        return True
    return -110 < ly < 0 and abs(lx) < 50 * MANSION_SCALE + 0.3 * -ly


def build():
    rng = random.Random(31)
    reb.clear_scene()
    earth = kit.mat("grassed earth")
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

    # A bare, trodden path to the single east exit, running on into the
    # pines past it so it never just stops.
    on_path = kit.dirt_path("Trail east", [(6.8, 5.6), (9.0, 5.4), (11.0, 5.3), (14.0, 5.1), (17.0, 5.4), (21.0, 5.0), (27.0, 4.4)], ground_height, width=1.7, taper=2.5)

    # Pines around the clearing: the west edge, the east edge either side of
    # the trail out, and the forest down the valley.
    needle_v, needle_f, bases = [], [], []
    ring = []
    for _ in range(30):
        x, y = rng.uniform(18, 27), rng.uniform(8.5, 19)
        if (y < 10 and x < 21) or on_path(x, y, 1.5):
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
    kit.tree_roots(rng, bases, ground_height, lambda x, y: on_path(x, y, 0.2))

    # Everything past the edge, for camera 0 (camera 1 looks the other
    # way): the kit's ranges, laid out on its picture, and the mansion.
    land = kit.backdrop(EYE, (LOOK.x, LOOK.y), spread=110, ranges=RANGES, below=-170.0, near=40.0,
                 forest_to=2200.0, keep_out=_mansion_grounds, shape=_valley,
                        terraces=[(MANSION_AT.x, MANSION_AT.y, 130.0)], mist=25.0, rng=random.Random(57))
    kit.spencer_mansion((MANSION_AT.x, MANSION_AT.y, land(MANSION_AT.x, MANSION_AT.y) - 0.5), heading=MANSION_TURN, scale=MANSION_SCALE, lit=2, far=True)

    # Grass over the whole clearing and the edge, off the path only.
    grass_ob = kit.grass_ground(rng, (2.5, 2.6, 18.0, 11.0), ground_height, keep_out=on_path, per_m2=40, m=grass)
    # Tufts made for a 1000-unit metre: stretch them up to her scale.
    gv = grass_ob.data.vertices
    for i in range(2, len(gv), 3):
        b = (gv[i - 2].co + gv[i - 1].co) / 2
        gv[i].co = b + (gv[i].co - b) * GROW
    grass_ob.data.update()
    # Stones in the grass, sat into the earth.
    stones = []
    for _ in range(60):
        x, y = rng.uniform(3.0, 11.0), rng.uniform(3.2, 10.0)
        if on_path(x, y, 0.3):
            continue
        stones.append((x, y, rng.uniform(0.05, 0.16) * GROW))
    kit.rocks("Stones", rng, stones, ground_height, rock, grass=False)
    grass_rest = [Vector(p.co) for p in grass_ob.data.vertices]
    kit.time_light("dawn")
    # The sun's glow at the right edge of camera 0, east of the view.
    kit.overcast_sky(glow=(0.75, 1.0))
    # A soft key on the clearing, from the cameras' side, for the RE look.
    reb.spot("Key", (7.0, 3.5, 9.0), (7.0, 8.0, 0.0), 2500, (1.0, 0.8, 0.65), 110, 1.0, 2.0)
    reb.spot("Back key", (6.0, 11.0, 8.0), (8.0, 4.0, 0.0), 1800, (0.8, 0.85, 1.0), 110, 1.0, 2.0)

    def pose(k):
        t = k / FRAMES
        phase = 2 * math.pi * t
        for idx in range(2, len(grass_rest), 3):
            p = grass_rest[idx]
            w = math.sin(phase + p.x * 0.7 + p.y * 0.4)
            grass_ob.data.vertices[idx].co = (p.x + 0.08 * w, p.y + 0.03 * w, p.z)
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
