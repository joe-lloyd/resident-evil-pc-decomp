"""The mountain trail, between the ridge and the ranger station, early morning.

A bare dirt footpath down through dense spruce. The trunks stand in rows
back into the dark and the night's mist; off the path it looks hopeless.
At the top the path bends west, round the shoulder, back up to the ridge;
at the foot it runs on down and bends east toward the station, and over
the treetops below lie the long, low ranges under heavy overcast (the kit's
RE0 look: kit.backdrop, kit.overcast_sky). A marker post points the way.
A spruce lies fallen along the west bank, scratched deep.

Metres, real sizes, but the walkable strip keeps the game units the trail has
always had (X 2000-5000, Z 0-16000), so the ridge and the yard still meet it
where they did: x 1.18-2.94, y 0-9.41.

Nothing moves: no wind reaches down here, so the grass and ferns stand still.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
from mathutils import Vector, noise  # noqa: E402

OUT = os.environ.get("RE1_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders"))
X0, X1 = 2000 / reb.UNITS, 5000 / reb.UNITS
Y0, Y1 = 0.0, 16000 / reb.UNITS
MID = (X0 + X1) / 2

# The cameras the trail has always had (game units): high behind the top
# looking down it, and beyond the foot looking back up.
CAMERAS = [
    {"from": (3300, -4400, -5400), "to": (3600, 0, 9000), "fov": 250},
    {"from": (3500, -3300, 19000), "to": (3500, -500, 11500), "fov": 250},
]
EYES = [reb.game_to_blender(c["from"]) for c in CAMERAS]
AIMS = [(reb.game_to_blender(c["to"]) - e).xy.normalized() for c, e in zip(CAMERAS, EYES)]

# The path, north to south: along the slope from the west, where it climbs
# to the ridge (turning out of camera 1's picture behind the trunks, not off
# its top), round the bend at the top, straight down the walkable
# strip, and on past the foot, bending east and down toward the station.
PATH = [(-16.0, -9.0), (-9.0, -5.4), (-4.0, -3.4), (-0.6, -2.4), (1.4, -1.0), (MID, 0.4), (MID, Y1), (MID + 0.3, Y1 + 3.5),
        (MID + 1.6, Y1 + 7.5), (MID + 4.5, Y1 + 11.5), (MID + 9.0, Y1 + 15.0), (MID + 16.0, Y1 + 19.0)]
LINE = [tuple(p) for p in kit._smooth_line(PATH, 1.0)]


def height(x, y):
    """Flat on the walkable strip; the path's own ground beyond it; banks
    rising either side; the mountain climbing behind the top and falling
    past the foot."""
    inside = X0 <= x <= X1 and Y0 <= y <= Y1
    d = 0.0 if inside else max(0.0, kit.path_distance(x, y, [LINE]) - 0.9)
    bank = min(d * 0.45, 5.0)
    climb = max(0.0, -y) * 0.5
    fall = -min(max(0.0, y - Y1 - 2.0) * 0.5, 12.0)
    lumps = noise.noise(Vector((x * 0.4, y * 0.4, 0.0))) * 0.5 * min(d, 1.0)
    ruts = 0.012 * noise.noise(Vector((x * 3, y * 3, 7))) if d == 0.0 else 0.0
    return bank + climb + fall + lumps + ruts


def far_land(x, y, z):
    """The kit's land, eased into the trail's mountainside near the room:
    up toward the ridge to the north, down toward the valley to the south."""
    r = math.hypot(x - MID, y - Y1 / 2)
    w = max(0.0, min(1.0, (220.0 - r) / 160.0))
    own = min(60.0, max(0.0, -y) * 0.45) - min(max(0.0, y - Y1 - 2.0) * 0.5, 30.0)
    return z + (own - z) * w * w * (3 - 2 * w)


def build():
    rng = random.Random(51)
    reb.clear_scene()
    rock = reb.mat_surface("Mossy rock", [(0.0, (0.03, 0.04, 0.025)), (0.5, (0.09, 0.09, 0.08)), (1.0, (0.16, 0.15, 0.13))], scale=3, bump=0.9)
    post_m = reb.mat_wood("Post", (0.2, 0.13, 0.07))
    letter = reb.mat_plain("Marker paint", (0.85, 0.75, 0.3), 0.6)

    reb.terrain("Ground", kit.mat("grassed earth"), (-30, 34), (-26, 46), height, step=0.35)
    on_path = kit.dirt_path("Path", PATH, height, width=1.9)

    def near_lens(x, y, reach=2.2):
        """Close in front of a lens, within its view and a margin, where a
        trunk or a branch would fill the picture; elsewhere only very close."""
        for e, aim in zip(EYES, AIMS):
            d = Vector((x - e.x, y - e.y))
            if d.length < 2.2 or (d.length < reach and d.normalized().dot(aim) > math.cos(math.radians(55))):
                return True
        return False

    # Roots across the path and stones in it, all sat into the earth.
    for i in range(6):
        y = rng.uniform(1.0, Y1 - 0.5)
        a = rng.uniform(-0.4, 0.4)
        half = (X1 - X0) / 2 + 0.7
        kit.rough_log(f"Root {i}", (MID - math.cos(a) * half, y - math.sin(a) * half, -0.04), (MID + math.cos(a) * half, y + math.sin(a) * half, -0.03), 0.055, seed=i, stubs=0)
    stones = []
    for _ in range(26):
        x, y = rng.uniform(X0, X1), rng.uniform(-2, Y1 + 3)
        stones.append((x, y, rng.uniform(0.03, 0.08)))
    kit.rocks("Path stones", rng, stones, height, rock, grass=False)
    kit.rocks("Rocks", rng, [(X0 - 1.3, 2.5, 0.45), (X1 + 1.5, 5.5, 0.55), (X0 - 1.6, 7.8, 0.4), (X1 + 1.2, 1.0, 0.35), (X1 + 1.9, 9.8, 0.5), (X0 - 2.2, 11.5, 0.6), (X1 + 2.6, 13.0, 0.7)], height, rock)

    # The fallen spruce along the west bank, scratched deep (message 0).
    kit.rough_log("Fallen spruce", (X0 - 1.25, 1.2, height(X0 - 1.25, 1.2) + 0.2), (X0 - 2.1, 8.1, height(X0 - 2.1, 8.1) + 0.25), 0.42, seed=7, stubs=9)
    # The marker post at the turn, its arrow pointing on down the hill.
    reb.mask(reb.wall(reb.prim("cube", "Marker post", post_m, (X1 + 0.35, 6.2, 0.6), (0.14, 0.14, 1.2), bevel=0.01)))
    reb.prim("cube", "Marker arrow", letter, (X1 + 0.35, 6.12, 0.95), (0.1, 0.012, 0.22))

    # Dense spruce on every side, rows of trunks back into the mist: kept
    # off the path, off the lenses, and off the fallen spruce.
    def no_tree(x, y):
        return on_path(x, y, 1.3) or near_lens(x, y, 5.5) or (X0 - 2.8 < x < X0 - 0.6 and 0.6 < y < 8.6)
    kit.forest(rng, height, no_tree, (-30, -26, 34, 46), count=300, spacing=1.6, tall=(14, 22), ferns=50, needles=2000)
    # Thicker either side of the path, so the trunks stand in rows.
    kit.forest(rng, height, no_tree, (-9, -12, 13, 24), count=150, spacing=1.3, tall=(12, 20), ferns=40, needles=800)

    # Grass over the banks, to the path's ragged edge and under the trees.
    kit.grass_ground(rng, (X0 - 7, -9, X1 + 7, Y1 + 12), height, keep_out=lambda x, y: on_path(x, y) or near_lens(x, y, 2.5), per_m2=22)

    # Light: a low morning sun from the east through the trunks, mist lying
    # in the trees. The sky the cameras see is the kit's overcast, and past
    # the trees the kit's ranges.
    kit.time_light("morning", sun_heading=105, sun_energy=5.0, mist=((3, 8, 3), (60, 70, 14), 0.0035))
    kit.overcast_sky()
    kit.backdrop((MID, Y1 / 2, 2.5), spread=360, below=-45.0, near=34.0, forest_to=1800.0, trees=120000,
                 keep_out=lambda x, y: math.hypot(x - MID, y - Y1 / 2) < 34, shape=far_land, mist=30.0, rng=random.Random(9))
    reb.spot("Soft trail light", (3, 4, 10), (3, 5, 0), 6000, (0.9, 0.85, 0.7), 120, 1, 5)
    reb.spot("Upper trail fill", (3, 12, 7), (3, 8, 0), 3000, (0.8, 0.88, 1.0), 120, 1, 5)

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
    )


build()
