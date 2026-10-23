"""The ranger station's yard, outside the lookout, in the morning.

A clearing cut into the mountain forest. The trail from the ridge comes in
at the north-west corner by the station sign. The cabin stands on the north
side with its porch to the south, a thin wisp of smoke still rising from the
stovepipe. A tool shed, padlocked, on the west. The ranger's truck is parked
in the middle, hazard lights blinking on a dying battery, a winch on its
front bumper; its tyre tracks run west to the forestry road. In the
south-east the trail goes on down the mountain, but last night's storm
snapped a pine and laid it across the trail, its stump left standing
splintered. Out by the east edge, the ranger's rifle lies in the grass where
drag marks lead off into the trees. All round, the forest stands close and
dark, trunk behind trunk into the mist, and over it the overcast and the
ranges (kit.backdrop, kit.overcast_sky: the RE0 look).

Metres, real sizes (reb.UNITS). She walks the flat clearing x 2-18,
y 2-12.2; the ground falls away beyond it. Ways out: north-west up the
trail (x 2-4.5), west along the tyre tracks (y 9.6-12), east after the drag
marks (y 4.5-7.5), south-east down the trail past the pine (x 14.3-17.2).

Moving: a thin wisp of smoke from the stovepipe, the flag and the hazard
lights, all of it slight. The grass stands still: no wind down here.
State "pine" (FG_COMMON 205): the pine dragged off the trail by the winch,
played as it drags when she works the winch.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import reb  # noqa: E402
import kit  # noqa: E402
from mathutils import Euler, Matrix, Vector, noise  # noqa: E402

OUT = os.environ.get("RE1_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders"))
FRAMES = 16
PINE_FLAG = 205

X0, X1, Y0, Y1 = 2.0, 18.0, 2.0, 12.2
CABIN = (11.0, 16.0, 2.0, 6.0)        # x0, x1, y0, y1: the cabin room is lookout's x 2-7, y 2-6 moved by 9
DOOR = (12.5, 13.4)                   # in the cabin's south wall
PORCH = (11.4, 15.6, 6.0, 7.2)
SHED = (2.8, 5.4, 6.6, 8.8)           # its door in the east wall
SHED_DOOR = (7.3, 8.1)                # y
TRUCK = (6.0, 11.0, 9.8, 11.8)        # facing east, the winch at x 11.2
WINCH = (11.2, 10.8, 0.55)
STOVEPIPE = (11.37, 4.7)
FLAGPOLE = (8.2, 5.2)
RIFLE = (15.9, 8.4)
SIGN = (6.2, 3.4)
STUMP = (12.25, 13.15)                # where the pine snapped; the trunk lies east from it

# The ways out, as the paths run on past the cameras into the trees.
TRAIL_IN = [(1.2, -14.0), (2.2, -6.0), (3.0, -1.0), (3.6, 2.5), (5.6, 5.0), (8.0, 6.6), (10.5, 7.5), (13.0, 7.7)]
TRAIL_DOWN = [(10.5, 7.5), (12.6, 9.0), (14.6, 10.7), (15.8, 12.3), (16.4, 15.0), (17.4, 19.0), (19.5, 24.0), (23.0, 30.0)]
SHED_PATH = [(7.4, 6.2), (6.4, 7.1), (5.5, 7.7)]
ROAD = [(-26.0, 17.0), (-14.0, 13.6), (-5.0, 11.6), (1.0, 11.0), (5.6, 10.8)]
WOODS = [(16.2, 6.6), (18.5, 6.5), (21.5, 7.4), (25.0, 7.0), (30.0, 8.5)]


def G(x, y, z=0.0):
    return (reb.g(x), -reb.g(z), reb.g(y))


CAMERAS = [
    # 0: from up the trail, north-west, over the yard: the sign, the shed, the flag, the cabin.
    {"from": G(2.6, -1.4, 4.0), "to": G(9.0, 8.5, 0.0), "fov": 200},
    # 1: from the south-east edge, at the cabin front, its porch and his rifle in the grass.
    {"from": G(18.5, 11.5, 2.6), "to": G(12.5, 4.5, 1.0), "fov": 200},
    # 2: from by the flagpole, south-west at the shed door and the truck's tailgate.
    {"from": G(9.4, 5.6, 3.0), "to": G(3.8, 9.6, 0.3), "fov": 200},
    # 3: from by the porch, south-west at the truck's winch and the pine across the trail.
    {"from": G(16.4, 8.0, 3.3), "to": G(12.8, 12.2, 0.3), "fov": 200},
]
EYES = [reb.game_to_blender(c["from"]) for c in CAMERAS]
AIMS = [(reb.game_to_blender(c["to"]) - e).xy.normalized() for c, e in zip(CAMERAS, EYES)]


def ground_height(x, y):
    """Flat where she walks; the mountain rises behind and falls away to the south."""
    h = 0.02 * noise.noise(Vector((x * 0.7, y * 0.7, 0)))
    if y > Y1 + 0.3:
        h -= (y - Y1 - 0.3) * 0.38
    if y < Y0 - 0.5:
        h += (Y0 - 0.5 - y) * 0.45
    if x < X0 - 0.5:
        h += (X0 - 0.5 - x) * 0.25 * max(0.0, 1.0 - max(0.0, y - 8.0) / 4.0)   # the road keeps level going west
    if x > X1 + 0.5:
        h += (x - X1 - 0.5) * 0.15
    return h + 0.4 * noise.noise(Vector((x * 0.15, y * 0.15, 3))) * (0 if X0 - 0.5 < x < X1 + 0.5 and Y0 - 0.5 < y < Y1 + 0.3 else 1)


def far_land(x, y, z):
    """The kit's land, eased into the yard's own mountainside near the room."""
    r = math.hypot(x - 10.0, y - 7.0)
    w = max(0.0, min(1.0, (200.0 - r) / 150.0))
    return z + (ground_height(x, y) - z) * w * w * (3 - 2 * w)


def inside(x, y, box, pad=0.0):
    return box[0] - pad < x < box[1] + pad and box[2] - pad < y < box[3] + pad


def near_lens(x, y, reach=2.2):
    """Close in front of a lens, where a trunk would fill the picture."""
    for e, aim in zip(EYES, AIMS):
        d = Vector((x - e.x, y - e.y))
        if d.length < 6.0 or (d.length < reach and d.normalized().dot(aim) > math.cos(math.radians(62))):
            return True
    return False


def shed(planks, iron, tin):
    """The tool shed: board walls on a frame, a gable roof seated on them
    with its ridge east to west, so the east wall, with the door, is a gable
    end. The door is shut and padlocked, fitted in its frame."""
    sx0, sx1, sy0, sy1 = SHED
    ym = (sy0 + sy1) / 2
    eave, ridge = 2.0, 2.75
    walls = kit.boards("Shed boards", (0.24, 0.2, 0.15), width=0.17, seam=0.1, grime=0.7)
    # The body: four walls and the two gables as one closed mesh, so no seam
    # shows daylight; boards run up it.
    v = [(sx0, sy0, 0.0), (sx1, sy0, 0.0), (sx1, sy1, 0.0), (sx0, sy1, 0.0),
         (sx0, sy0, eave), (sx1, sy0, eave), (sx1, sy1, eave), (sx0, sy1, eave),
         (sx0, ym, ridge), (sx1, ym, ridge)]
    f = [(0, 1, 5, 4), (1, 2, 6, 9, 5), (2, 3, 7, 6), (3, 0, 4, 8, 7), (4, 5, 9, 8), (6, 7, 8, 9)]
    body = reb.mesh_object("Shed walls", v, f, walls, smooth=False)
    reb.mask(body)
    reb.wall(reb.prim("cube", "Shed footprint", None, ((sx0 + sx1) / 2, ym, 1.0), (sx1 - sx0, sy1 - sy0, 2.0))).hide_render = True
    # Corner posts, the sill and the eave plates.
    for x in (sx0, sx1):
        for y in (sy0, sy1):
            reb.prim("cube", "Shed corner post", planks, (x, y, eave / 2), (0.1, 0.1, eave), bevel=0.01)
    for y in (sy0, sy1):
        reb.prim("cube", "Shed eave plate", planks, ((sx0 + sx1) / 2, y, eave - 0.05), (sx1 - sx0 + 0.1, 0.1, 0.1))
        reb.prim("cube", "Shed sill", planks, ((sx0 + sx1) / 2, y, 0.06), (sx1 - sx0 + 0.1, 0.09, 0.12))
    # The roof: two sheets of tin laid from the eaves to the ridge, their
    # underside on the wall tops, over the gables a little, with a capping
    # along the ridge and barge boards up the gables.
    over_e, over_g, t = 0.28, 0.22, 0.04
    rise = (ridge - eave) / (ym - sy0)
    for side in (-1, 1):
        ye = ym + side * ((sy1 - sy0) / 2 + over_e)
        ze = eave - over_e * rise
        q = [(sx0 - over_g, ye, ze), (sx1 + over_g, ye, ze), (sx1 + over_g, ym, ridge), (sx0 - over_g, ym, ridge)]
        qv = q + [(x, y, z + t) for x, y, z in q]
        qf = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        reb.mesh_object("Shed roof", qv, qf, tin, smooth=False)
        # The tin's corrugations, as ribs down the slope.
        for i in range(14):
            x = sx0 - over_g + 0.08 + (sx1 - sx0 + 2 * over_g - 0.16) * i / 13
            kit.rod("Roof rib", tin, (x, ye, ze + t + 0.004), (x, ym, ridge + t + 0.004), 0.014, 4)
        for x in (sx0 - over_g + 0.02, sx1 + over_g - 0.02):
            kit.rod("Barge board", planks, (x, ye, ze - 0.02), (x, ym, ridge - 0.02), 0.05, 6)
    kit.rod("Ridge capping", tin, (sx0 - over_g, ym, ridge + t + 0.02), (sx1 + over_g, ym, ridge + t + 0.02), 0.06, 6)
    # A small window in the north wall, dark, two panes.
    wx = (sx0 + sx1) / 2
    reb.prim("cube", "Shed window", reb.mat_plain("Shed window", (0.02, 0.025, 0.025), 0.15), (wx, sy0 - 0.01, 1.35), (0.7, 0.02, 0.5))
    for dx, dz, sx, sz in ((0, 0.27, 0.82, 0.07), (0, -0.27, 0.82, 0.07), (-0.38, 0, 0.07, 0.6), (0.38, 0, 0.07, 0.6), (0, 0, 0.04, 0.5)):
        reb.prim("cube", "Shed window frame", planks, (wx + dx, sy0 - 0.03, 1.35 + dz), (sx, 0.05, sz))
    # The door: a frame of jambs and a lintel, the door shut flush in it.
    y0, y1 = SHED_DOOR
    dh = 1.9
    for y in (y0 - 0.05, y1 + 0.05):
        reb.prim("cube", "Door jamb", planks, (sx1 + 0.03, y, dh / 2), (0.07, 0.1, dh))
    reb.prim("cube", "Door lintel", planks, (sx1 + 0.03, (y0 + y1) / 2, dh + 0.05), (0.07, y1 - y0 + 0.2, 0.1))
    door_m = kit.boards("Shed door boards", (0.27, 0.22, 0.16), width=0.13, seam=0.12, grime=0.6)
    reb.prim("cube", "Shed door", door_m, (sx1 + 0.02, (y0 + y1) / 2, dh / 2), (0.05, y1 - y0 - 0.01, dh - 0.02))
    for z in (0.3, 1.6):
        reb.prim("cube", "Door ledge", planks, (sx1 + 0.06, (y0 + y1) / 2, z), (0.035, y1 - y0 - 0.06, 0.1))
        reb.prim("cube", "Strap hinge", iron, (sx1 + 0.08, y1 - 0.2, z), (0.012, 0.36, 0.04))
    a, b = Vector((sx1 + 0.06, y1 - 0.08, 0.36)), Vector((sx1 + 0.06, y0 + 0.08, 1.54))
    reb.prim("cube", "Door brace", planks, (a + b) / 2, (0.035, 0.09, (b - a).length), rot=(math.atan2(b.y - a.y, b.z - a.z) * -1, 0, 0))
    reb.prim("cube", "Hasp", iron, (sx1 + 0.085, y0 + 0.05, 1.05), (0.012, 0.16, 0.05))
    reb.prim("cube", "Padlock", reb.mat_metal("Padlock", (0.5, 0.4, 0.18), 0.35), (sx1 + 0.1, y0 + 0.02, 0.99), (0.03, 0.06, 0.07), bevel=0.008)
    # Lived in: a spade and a saw hung on the south wall, a log round by the door.
    reb.prim("cube", "Bow saw", iron, (4.1, sy1 + 0.04, 1.5), (0.7, 0.012, 0.02))
    kit.rod("Bow saw frame", reb.mat_plain("Saw paint", (0.35, 0.12, 0.03), 0.6), (3.75, sy1 + 0.04, 1.5), (4.1, sy1 + 0.04, 1.75), 0.012, 6)
    kit.rod("Bow saw frame", reb.mat_plain("Saw paint", (0.35, 0.12, 0.03), 0.6), (4.45, sy1 + 0.04, 1.5), (4.1, sy1 + 0.04, 1.75), 0.012, 6)
    kit.rod("Spade handle", kit.mat("planks"), (3.2, sy1 + 0.06, 0.25), (3.35, sy1 + 0.06, 1.4), 0.018, 6)
    reb.prim("cube", "Spade blade", iron, (3.18, sy1 + 0.06, 0.15), (0.18, 0.02, 0.25))


def broken_pine(bark, wood, needles):
    """The pine the storm snapped: the trunk from its splintered break east
    along the trail, built round (0, 0, 0) to swing on its pivot when the
    winch drags it. Not a felled log: a ragged break, the top's branches
    crushed flat where they hit the ground."""
    prng = random.Random(4)
    length, r0 = 9.0, 0.4
    trunk = kit.rough_log("Pine trunk", (0.0, 0.0, r0 * 0.8), (length, 0.15, 0.08), r0, m=bark, seed=11, stubs=10)
    # Splinters standing out of the break, long on one side where it tore.
    v, f = [], []
    for j in range(16):
        a = 2 * math.pi * j / 16 + prng.uniform(-0.1, 0.1)
        rr = r0 * prng.uniform(0.35, 0.95)
        base = Vector((0.12, math.cos(a) * rr, r0 * 0.8 + math.sin(a) * rr))
        tip = base + Vector((-prng.uniform(0.08, 0.25 + (0.45 if math.cos(a) > 0.3 else 0.0)), math.cos(a) * 0.04, math.sin(a) * 0.04))
        k = len(v)
        w = 0.035
        side = Vector((0, -math.sin(a), math.cos(a))) * w
        v += [tuple(base - side), tuple(base + side), tuple(tip)]
        f.append((k, k + 1, k + 2))
    splinters = reb.mesh_object("Splintered break", v, f, wood, smooth=False)
    # Branches: drooping needle cards along the upper two thirds, pressed
    # flat where they hit the ground.
    nv, nf = [], []
    up = Vector((0, 0, 1))
    for _ in range(7000):
        t = prng.uniform(0.35, 1.0)
        x = t * length
        reach = (1.0 - t) * 2.0 + 0.4
        a = prng.uniform(0, 2 * math.pi)
        out = Vector((0.3, math.cos(a), math.sin(a))).normalized()
        base = Vector((x, 0.15 * t, r0 * (1 - 0.7 * t))) + out * prng.uniform(0.0, reach)
        if base.z < 0.03:
            base.z = 0.03 + prng.uniform(0, 0.05)
        reb.card(nv, nf, base, out, up, prng.uniform(0.05, 0.1), prng.uniform(0.15, 0.32), prng.uniform(0.2, 0.7))
    cards = reb.mesh_object("Pine needles", nv, nf, needles)
    bpy.ops.object.empty_add(location=(0, 0, 0))
    pivot = bpy.context.active_object
    pivot.name = "Pine"
    for ob in (trunk, splinters, cards):
        ob.parent = pivot
    return pivot


def stump(bark, wood):
    """The stump left standing where the pine snapped, its top torn into
    splinters, rooted into the ground."""
    rng = random.Random(9)
    x, y = STUMP
    z0 = ground_height(x, y) - 0.4
    r = 0.34
    v, f = [], []
    ring = 14
    tops = []
    for i, (t, rr) in enumerate(((0.0, r * 1.3), (0.5, r * 1.05), (0.9, r))):
        for k in range(ring):
            a = 2 * math.pi * k / ring
            v.append((x + math.cos(a) * rr, y + math.sin(a) * rr, z0 + t))
    for k in range(ring):
        a = 2 * math.pi * k / ring
        # The torn top: tall splinters on the side it fell away from (west).
        h = 1.25 + (0.55 if math.cos(a) < -0.2 else 0.0) * rng.uniform(0.4, 1.0) + rng.uniform(-0.12, 0.12)
        v.append((x + math.cos(a) * r * rng.uniform(0.75, 0.95), y + math.sin(a) * r * rng.uniform(0.75, 0.95), z0 + h))
        tops.append(len(v) - 1)
    for i in range(3):
        for k in range(ring):
            a, b = i * ring + k, i * ring + (k + 1) % ring
            f.append((a, b, b + ring, a + ring))
    reb.mesh_object("Stump", v, f, bark, smooth=True)
    # The pale torn wood inside, a jagged cone down into the stump.
    k = len(v)
    v2 = [v[i] for i in tops] + [(x, y, z0 + 1.05)]
    f2 = [(j, (j + 1) % ring, ring) for j in range(ring)]
    reb.mesh_object("Stump heartwood", v2, f2, wood, smooth=False)
    kit.tree_roots(rng, [(Vector((x, y, ground_height(x, y) - 0.2)), 14.0)], ground_height)


def truck_bed_gear(tx0, ty0, ty1, tym):
    """What is in the bed: the ranger's toolbox bolted across the front, a
    jerrycan, a coil of rope, a tarp kicked into the back."""
    steel = reb.mat_surface("Diamond plate", [(0.0, (0.25, 0.25, 0.25)), (0.5, (0.42, 0.42, 0.4)), (1.0, (0.3, 0.3, 0.28))], scale=60, rough=0.35, bump=0.6)
    bx = tx0 + 2.66 - 0.3 - 0.03 - 0.2   # against the bed's front wall
    reb.prim("cube", "Toolbox", steel, (bx, tym, 1.06), (0.4, 1.78, 0.42), bevel=0.02)
    reb.prim("cube", "Toolbox lid seam", kit.mat("black"), (bx - 0.2, tym, 1.22), (0.012, 1.7, 0.01))
    for y in (tym - 0.5, tym + 0.5):
        reb.prim("cube", "Toolbox lock", kit.mat("steel"), (bx - 0.205, y, 1.16), (0.01, 0.08, 0.05))
    reb.prim("cube", "Jerrycan", reb.mat_plain("Red can", (0.3, 0.04, 0.03), 0.5), (tx0 + 1.2, ty0 + 0.35, 1.08), (0.35, 0.18, 0.45), bevel=0.02)
    rope = kit.mat("canvas")
    for i in range(4):
        pts = [(tx0 + 1.0 + math.cos(a) * (0.26 - i * 0.02), ty1 - 0.45 + math.sin(a) * (0.26 - i * 0.02), 0.9 + i * 0.03) for a in [2 * math.pi * k / 12 for k in range(13)]]
        kit.tube("Rope coil", rope, pts, 0.022, 6)
    reb.cloth("Tarp", reb.mat_plain("Tarp", (0.12, 0.15, 0.1), 0.8), (tx0 + 0.55, tym, 0.92), (0.7, 1.5), lumps=0.12, seed=4)


def build():
    rng = random.Random(23)
    reb.clear_scene()

    logs = reb.mat_wood("Logs", (0.21, 0.13, 0.075))
    dark = reb.mat_wood("Dark wood", (0.09, 0.055, 0.035))
    planks = reb.mat_wood("Weathered planks", (0.26, 0.22, 0.17))
    shingle = reb.mat_surface("Shingles", [(0.0, (0.05, 0.045, 0.04)), (1.0, (0.13, 0.1, 0.08))], scale=12, bump=0.5)
    iron = reb.mat_metal("Iron", (0.05, 0.048, 0.045), rough=0.6)
    rust = reb.mat_surface("Rust", [(0.0, (0.15, 0.06, 0.02)), (1.0, (0.3, 0.14, 0.05))], scale=20, rough=0.8)
    paint = reb.mat_surface("Truck paint", [(0.0, (0.06, 0.12, 0.07)), (1.0, (0.09, 0.16, 0.09))], scale=8, rough=0.45, bump=0.1)
    white = reb.mat_plain("White paint", (0.6, 0.6, 0.56), 0.5)
    chrome = reb.mat_metal("Chrome", (0.7, 0.7, 0.7), 0.15)
    glass = reb.mat_plain("Window glass", (0.03, 0.035, 0.04), 0.15)
    bark = kit.mat("bark")
    browning = reb.mat_cards("Wilting needles", (0.025, 0.045, 0.02), (0.08, 0.1, 0.04))
    wood = reb.mat_surface("Torn wood", [(0.0, (0.3, 0.22, 0.13)), (1.0, (0.5, 0.4, 0.26))], scale=30, bump=0.5)
    needles = kit.mat("needles")
    rock = reb.mat_surface("Granite", [(0.0, (0.12, 0.12, 0.11)), (1.0, (0.3, 0.29, 0.27))], scale=3, bump=0.9)
    blood = kit.mat("blood")
    sign_m = reb.mat_plain("Sign brown", (0.16, 0.09, 0.04), 0.7)
    letter = reb.mat_plain("Sign letters", (0.75, 0.7, 0.5), 0.6)
    amber = reb.mat_emit("Hazard", (1.0, 0.55, 0.1), 30)
    flag_m = reb.mat_stripes("Flag", [(0.05, 0.12, 0.08), (0.6, 0.55, 0.35)], across=6, axis="Z")
    tin = reb.mat_surface("Shed tin", [(0.0, (0.1, 0.1, 0.095)), (0.55, (0.2, 0.19, 0.18)), (0.8, (0.25, 0.13, 0.06)), (1.0, (0.16, 0.09, 0.05))], scale=4, rough=0.6, bump=0.3)

    # ---- Ground: the yard, the mountain round it, bare trodden paths out.
    reb.terrain("Ground", kit.mat("grassed earth"), (-28, 48), (-26, 44), ground_height, step=0.4)
    on_trail = kit.dirt_path("Trail", TRAIL_IN, ground_height, width=1.7)
    on_down = kit.dirt_path("Trail down", TRAIL_DOWN, ground_height, width=1.6)
    on_shed = kit.dirt_path("Path to the shed", SHED_PATH, ground_height, width=1.1, taper=0.6)
    on_woods = kit.dirt_path("Drag path", WOODS, ground_height, width=0.9, taper=1.0)
    kit.ruts("Tyre tracks", ROAD + [(8.0, 10.8)], ground_height, gauge=1.56, width=0.3, seed=2.0)
    on_road = lambda x, y, margin=0.0: kit.path_distance(x, y, [ROAD]) < 1.3 + margin

    def on_path(x, y, margin=0.0):
        return on_trail(x, y, margin) or on_down(x, y, margin) or on_shed(x, y, margin) or on_woods(x, y, margin)

    # ---- The cabin: log walls, a shingled gable roof, the porch, the stovepipe.
    cx0, cx1, cy0, cy1 = CABIN
    r = 0.125
    def logs_along(axis, at, a0, a1, holes, top=2.5):
        z = r
        while z < top:
            spans = [(a0 - 0.3, a1 + 0.3)]
            for h0, h1, hz0, hz1 in holes:
                if z + r > hz0 and z - r < hz1:
                    spans = [p for s0, s1 in spans for p in ((s0, min(s1, h0)), (max(s0, h1), s1)) if p[1] - p[0] > 0.02]
            for s0, s1 in spans:
                mid, length = (s0 + s1) / 2, s1 - s0
                if axis == "x":
                    reb.prim("cyl", "Cabin log", logs, (mid, at, z), (2 * r, 2 * r, length), rot=(0, math.pi / 2, 0), segments=12)
                else:
                    reb.prim("cyl", "Cabin log", logs, (at, mid, z), (2 * r, 2 * r, length), rot=(math.pi / 2, 0, 0), segments=12)
            z += 2 * r
    logs_along("x", cy0 - r, cx0, cx1, [(12.0, 12.9, 0.95, 1.75)])
    logs_along("x", cy1 + r, cx0, cx1, [(DOOR[0], DOOR[1], 0.0, 2.0), (14.2, 15.0, 1.0, 1.7)])
    logs_along("y", cx0 - r, cy0, cy1, [])
    logs_along("y", cx1 + r, cy0, cy1, [(2.6, 3.5, 1.0, 1.7)])
    reb.wall(reb.prim("cube", "Cabin body", reb.mat_plain("Cabin dark", (0.02, 0.015, 0.01)), ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 1.3), (cx1 - cx0, cy1 - cy0, 2.6)))
    # Gable ends and the roof: two slopes of shingle rows from the eaves to the ridge.
    ridge_z, eave_z, over = 4.0, 2.5, 0.5
    cym = (cy0 + cy1) / 2
    for side in (-1, 1):
        y_eave = cym + side * ((cy1 - cy0) / 2 + over)
        rows = 12
        for i in range(rows):
            t0, t1 = i / rows, (i + 1) / rows
            ya, yb = y_eave + (cym - y_eave) * t0, y_eave + (cym - y_eave) * t1
            za, zb = eave_z + (ridge_z - eave_z) * t0, eave_z + (ridge_z - eave_z) * t1
            mid = Vector(((cx0 + cx1) / 2, (ya + yb) / 2, (za + zb) / 2 + 0.03))
            slope = math.atan2(zb - za, abs(yb - ya))
            reb.prim("cube", "Shingle row", shingle, mid, (cx1 - cx0 + 2 * over, abs(yb - ya) * 1.25, 0.04), rot=(side * slope, 0, 0))
    for x in (cx0 - 0.25, cx1 + 0.25):
        v = [(x, cy0 - 0.2, eave_z), (x, cy1 + 0.2, eave_z), (x, cym, ridge_z)]
        reb.mesh_object("Gable", v, [(0, 1, 2)], planks, smooth=False)
    reb.prim("cyl", "Stovepipe", iron, (STOVEPIPE[0], STOVEPIPE[1], 3.6), (0.16, 0.16, 1.6))
    reb.prim("cone", "Stovepipe cap", iron, (STOVEPIPE[0], STOVEPIPE[1], 4.48), (0.36, 0.36, 0.16), top=0.1)
    # Windows: dark glass; the east one smashed, blood soaked into the logs below it.
    for (x, y, rot) in ((12.45, cy0 - 0.27, 0), (14.6, cy1 + 0.27, 0)):
        reb.prim("cube", "Window", glass, (x, y, 1.35), (0.9, 0.02, 0.7), rot=(0, 0, rot))
        reb.prim("cube", "Window frame", dark, (x, y, 1.35), (1.0, 0.06, 0.08))
        reb.prim("cube", "Window frame", dark, (x, y, 1.35), (0.06, 0.06, 0.8))
    reb.prim("cube", "Broken window", reb.mat_plain("Dark inside", (0.01, 0.008, 0.006)), (cx1 + 0.28, 3.05, 1.35), (0.02, 0.9, 0.7))
    kit.splat("Blood under the window", blood, (cx1 + 0.27, 3.1, 0.75), 0.3, rot=(math.pi / 2, 0, math.pi / 2), seed=5, stretch=(0.7, 1.6))
    # The door, the porch deck, its steps, posts and roof.
    reb.prim("cube", "Cabin door", planks, ((DOOR[0] + DOOR[1]) / 2, cy1 + 0.27, 1.0), (DOOR[1] - DOOR[0], 0.05, 2.0), bevel=0.01)
    px0, px1, py0, py1 = PORCH
    reb.prim("cube", "Porch deck", planks, ((px0 + px1) / 2, (py0 + py1) / 2, 0.11), (px1 - px0, py1 - py0, 0.22), bevel=0.01)
    reb.prim("cube", "Porch step", planks, ((DOOR[0] + DOOR[1]) / 2, py1 + 0.2, 0.06), (1.2, 0.4, 0.12), bevel=0.01)
    for x in (px0 + 0.1, px1 - 0.1, (px0 + px1) / 2 - 0.9, (px0 + px1) / 2 + 0.9):
        reb.mask(reb.prim("cyl", "Porch post", logs, (x, py1 - 0.1, 1.3), (0.16, 0.16, 2.2), segments=10))
    reb.prim("cube", "Porch roof", shingle, ((px0 + px1) / 2, (py0 + py1) / 2 + 0.1, 2.45), (px1 - px0 + 0.4, py1 - py0 + 0.5, 0.06), rot=(-0.18, 0, 0))
    reb.prim("cyl", "Porch rail", logs, (px0 + 0.5, py1 - 0.1, 0.8), (0.08, 0.08, 1.0), rot=(0, math.pi / 2, 0))
    reb.prim("cyl", "Porch rail", logs, (px1 - 0.5, py1 - 0.1, 0.8), (0.08, 0.08, 1.0), rot=(0, math.pi / 2, 0))
    lantern = reb.mat_emit("Porch lantern", (1.0, 0.7, 0.35), 3)
    reb.prim("cyl", "Porch lantern", lantern, (DOOR[1] + 0.35, py0 + 0.15, 2.0), (0.1, 0.1, 0.16))
    # Woodpile against the west wall, a chopping block, a rain barrel.
    for i in range(36):
        layer, k = divmod(i, 9)
        reb.mask(reb.prim("cyl", "Split log", logs, (cx0 - 0.6, cy0 + 0.6 + k * 0.32, 0.12 + layer * 0.22), (0.22, 0.22, 0.55), rot=(0, math.pi / 2, rng.uniform(-0.1, 0.1)), segments=7))
    reb.wall(reb.prim("cube", "Woodpile", None, (cx0 - 0.6, (cy0 + cy1) / 2 - 0.3, 0.45), (0.6, 3.0, 0.9))).hide_render = True
    reb.mask(reb.wall(reb.prim("cyl", "Chopping block", logs, (9.6, 5.6, 0.25), (0.5, 0.5, 0.5), segments=14), "circle"))
    reb.mask(reb.wall(reb.prim("cyl", "Rain barrel", reb.mat_wood("Barrel", (0.2, 0.12, 0.06)), (px1 + 0.45, 6.5, 0.45), (0.6, 0.6, 0.9), segments=18), "circle"))
    # The radio mast on the west gable, its wire to the roof.
    reb.prim("cyl", "Radio mast", iron, (cx0 - 0.3, cy0 + 0.6, 4.0), (0.06, 0.06, 8.0))
    for z in (5.5, 6.5, 7.5):
        reb.prim("cyl", "Mast bar", iron, (cx0 - 0.3, cy0 + 0.6, z), (0.03, 0.03, 1.0), rot=(0, math.pi / 2, 0))
    a, b = Vector((cx0 - 0.3, cy0 + 0.6, 7.9)), Vector((cx0 + 0.5, cym, ridge_z + 0.05))
    reb.prim("cyl", "Mast wire", iron, (a + b) / 2, (0.008, 0.008, (b - a).length), rot=(b - a).to_track_quat("Z", "Y").to_euler())

    # ---- The tool shed.
    shed(planks, iron, tin)

    # ---- The truck: a green ranger pickup, driver's door open, the winch on its bumper.
    tx0, tx1, ty0, ty1 = TRUCK
    tym = (ty0 + ty1) / 2
    truck, hinge = kit.pickup("Truck", paint, door_open=0.75, door_side=-1)
    truck.location = (tx1 - 2.75, tym, 0.0)
    reb.prim("cube", "Door stripe", white, (-0.7, -0.035, -0.12), (1.3, 0.01, 0.1)).parent = hinge
    tx0 = tx1 - 2.75 - 2.66   # the bed's back
    truck_bed_gear(tx0, ty0, ty1, tym)
    for s in (-1, 1):
        reb.prim("cube", "Side stripe", white, (tx1 - 2.75 - 1.47, tym + s * 0.935, 1.0), (2.3, 0.01, 0.1))
        reb.prim("cube", "Side stripe", white, (tx1 - 2.75 + 2.02, tym + s * 0.935, 1.0), (1.3, 0.01, 0.1))
    reb.prim("cube", "Side stripe", white, (tx1 - 2.75 + 0.57, tym + 0.935, 1.0), (1.4, 0.01, 0.1))
    for x, z in ((tx0 - 0.02, 1.12), (tx1 + 0.02, 1.0)):
        for y in (ty0 + 0.12, ty1 - 0.12):
            reb.prim("cube", "Hazard light", amber, (x, y, z), (0.04, 0.12, 0.07))
    hazard = reb.point("Hazard glow", (tx1 + 0.3, tym, 1.0), 6, (1.0, 0.5, 0.1), 0.3)
    hazard_rear = reb.point("Hazard glow rear", (tx0 - 0.3, tym, 1.1), 4, (1.0, 0.5, 0.1), 0.3)
    # The winch: a drum on the bumper, the cable wound on, the hook hanging.
    reb.prim("cyl", "Winch drum", rust, WINCH, (0.22, 0.22, 0.6), rot=(math.pi / 2, 0, 0), segments=18)
    reb.prim("cyl", "Winch cable", reb.mat_metal("Cable", (0.25, 0.24, 0.22), 0.5), WINCH, (0.26, 0.26, 0.5), rot=(math.pi / 2, 0, 0), segments=18)
    reb.prim("cube", "Winch frame", iron, (WINCH[0], WINCH[1], WINCH[2] - 0.05), (0.2, 0.75, 0.3))
    reb.prim("cube", "Crank socket", iron, (WINCH[0] + 0.02, WINCH[1] + 0.36, WINCH[2]), (0.06, 0.06, 0.06))
    hook = reb.prim("cube", "Winch hook", iron, (WINCH[0] + 0.15, WINCH[1], 0.32), (0.04, 0.08, 0.14))
    # Its footprint, with the open door and the winch.
    truck_box = reb.prim("cube", "Truck footprint", None, ((TRUCK[0] + tx1) / 2 + 0.15, tym - 0.4, 0.8), (tx1 - TRUCK[0] + 0.4, ty1 - ty0 + 0.8, 1.6))
    reb.wall(truck_box).hide_render = True
    reb.mask(truck)

    # ---- The pine across the trail, snapped off its stump at the west end.
    pine = broken_pine(bark, wood, browning)
    stump(bark, wood)
    pine_rest = ((STUMP[0] + 0.35, STUMP[1] - 0.15, ground_height(*STUMP) - 0.05), (0, 0, -0.04))
    pine_moved = ((13.0, 12.8, 0.0), (0, 0, 1.55))
    pine.location, pine.rotation_euler = pine_rest
    cable = reb.prim("cyl", "Winch line", reb.mat_plain("Cable line", (0.12, 0.11, 0.1), 0.6), (0, 0, 0), (0.05, 0.05, 1.0))
    cable.hide_render = True

    # Where the winch line is made fast round the trunk, in the dragged
    # pine's place: it rides with the trunk as it swings round.
    tied = Vector((13.0, 13.1, 0.35))
    moved_matrix = Matrix.Translation(pine_moved[0]) @ Euler(pine_moved[1]).to_matrix().to_4x4()
    tied_local = moved_matrix.inverted() @ tied

    def place_pine(t):
        """t 0: across the trail; 1: dragged clear; between, part way, the line taut."""
        t = float(t)
        e = t * t * (3 - 2 * t)   # the winch takes up the slack, drags, and slows as it comes clear
        (l0, r0), (l1, r1) = pine_rest, pine_moved
        pine.location = Vector(l0).lerp(Vector(l1), e)
        pine.rotation_euler = Euler([a + (b - a) * e for a, b in zip(r0, r1)])
        hook.hide_render = t > 0
        cable.hide_render = t == 0
        if t > 0:
            a = Vector(WINCH) + Vector((0.12, 0, -0.1))
            b = (Matrix.Translation(pine.location) @ pine.rotation_euler.to_matrix().to_4x4()) @ tied_local
            cable.location = (a + b) / 2
            cable.scale = (1, 1, (b - a).length)
            cable.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()

    # ---- The station sign at the trail's mouth.
    for x in (SIGN[0] - 0.7, SIGN[0] + 0.7):
        reb.mask(reb.wall(reb.prim("cyl", "Sign post", logs, (x, SIGN[1], 0.9), (0.14, 0.14, 1.8), segments=10)))
    board = reb.prim("cube", "Sign board", sign_m, (SIGN[0], SIGN[1], 1.45), (1.7, 0.06, 0.6), bevel=0.02)
    reb.mask(board)
    bpy.ops.object.text_add(location=(SIGN[0] - 0.7, SIGN[1] - 0.04, 1.52), rotation=(math.pi / 2, 0, 0))
    txt = bpy.context.active_object
    txt.data.body = "RANGER STATION 3"
    txt.data.size = 0.17
    txt.data.extrude = 0.005
    txt.data.materials.append(letter)
    bpy.ops.object.text_add(location=(SIGN[0] - 0.47, SIGN[1] - 0.04, 1.3), rotation=(math.pi / 2, 0, 0))
    txt2 = bpy.context.active_object
    txt2.data.body = "ARKLAY MOUNTAINS"
    txt2.data.size = 0.11
    txt2.data.extrude = 0.004
    txt2.data.materials.append(letter)

    # ---- The flagpole, its flag stirring.
    reb.prim("cyl", "Flagpole", white, (FLAGPOLE[0], FLAGPOLE[1], 3.5), (0.07, 0.07, 7.0))
    reb.prim("sphere", "Pole ball", chrome, (FLAGPOLE[0], FLAGPOLE[1], 7.05), (0.12, 0.12, 0.12))
    fv, ff = [], []
    fcols, frows = 12, 7
    for j in range(frows + 1):
        for i in range(fcols + 1):
            fv.append((FLAGPOLE[0] + 0.05 + 1.3 * i / fcols, FLAGPOLE[1], 6.8 - 0.8 * j / frows))
    for j in range(frows):
        for i in range(fcols):
            k = j * (fcols + 1) + i
            ff.append((k, k + 1, k + fcols + 2, k + fcols + 1))
    flag = reb.mesh_object("Flag", fv, ff, flag_m)
    flag_rest = [Vector(p) for p in fv]

    # ---- His rifle in the grass by the east edge, drag marks into the trees.
    reb.prim("cube", "Rifle stock", reb.mat_wood("Rifle wood", (0.25, 0.12, 0.05)), (RIFLE[0], RIFLE[1], 0.05), (0.4, 0.06, 0.08), rot=(0, 0, 0.6))
    reb.prim("cyl", "Rifle barrel", iron, (RIFLE[0] + 0.45, RIFLE[1] + 0.35, 0.05), (0.03, 0.03, 0.7), rot=(0, math.pi / 2, 0.6))
    kit.drag_trail("Drag marks", blood, [(16.2, 6.5), (17.2, 6.6), (18.4, 6.5), (19.8, 6.9)], width=0.35, seed=12, height=ground_height)
    kit.splat("Blood where he fell", blood, (16.0, 6.5, ground_height(16.0, 6.5) + 0.004), 0.35, seed=13, stretch=(1.3, 0.9))
    # Paw prints in the dirt by the porch, too big for any dog.
    prints = kit.mat("mud")
    for i in range(8):
        x, y = 15.9 - i * 0.35, 7.6 + (i % 2) * 0.2
        kit.splat(f"Paw print {i}", prints, (x, y, ground_height(x, y) + 0.014), 0.07, seed=30 + i, points=12)

    # ---- The forest: dense spruce all round, trunk behind trunk into the
    # mist, kept off the yard, the paths out and the lenses.
    def no_tree(x, y):
        if X0 - 2.8 < x < X1 + 2.2 and Y0 - 2.6 < y < Y1 + 1.4:
            return True
        if 8.0 < x < 18.0 and Y0 - 4.5 < y < Y0:
            return True     # behind the cabin, where a crown would hang over its roof
        if inside(x, y, (STUMP[0] - 1.0, STUMP[0] + 10.5, STUMP[1] - 1.6, STUMP[1] + 1.8)):
            return True     # the fallen pine and the ground it swings over
        if inside(x, y, (TRUCK[0] - 1.5, TRUCK[1] + 1.0, TRUCK[3], TRUCK[3] + 4.5)):
            return True     # behind the truck, where a low bough would hang over its bed
        return on_path(x, y, 1.6) or on_road(x, y, 1.2) or near_lens(x, y, 8.0)
    kit.forest(rng, ground_height, no_tree, (-28, -26, 48, 44), count=420, spacing=1.8, tall=(14, 22), ferns=60, needles=2500)
    # Thicker in the first rows round the clearing, so the trunks wall it in.
    kit.forest(rng, ground_height, no_tree, (-6, -8, 26, 22), count=170, spacing=1.35, tall=(12, 20), ferns=40, needles=1200)

    # Grass over everything that is not path, building or truck, and
    # out under the trees: no bald ground anywhere.
    def no_grass(x, y):
        return (on_path(x, y) or on_road(x, y, -0.6) or inside(x, y, CABIN, 0.3) or inside(x, y, PORCH, 0.1)
                or inside(x, y, SHED, 0.05) or inside(x, y, (TRUCK[0] - 0.3, tx1 + 0.1, ty0 + 0.1, ty1 - 0.1)))
    kit.grass_ground(rng, (-2, -5, 22, 16), ground_height, keep_out=no_grass, per_m2=30)
    grass_far = kit.grass_ground(rng, (-16, -16, 36, 30), ground_height, keep_out=lambda x, y: no_grass(x, y) or (-2 < x < 22 and -5 < y < 16), per_m2=7)
    kit.rocks("Rocks", rng, [(1.0, 6.2, 0.55), (19.4, 4.0, 0.6), (13.6, 14.6, 0.5), (19.2, 14.0, 0.55), (7.0, 13.6, 0.75), (0.6, 13.6, 0.5)], ground_height, rock)
    # Rocks and brush fill the corners no camera sees well, so she cannot stand there.
    for name, (x, y, rr) in (("Rocks south-west", (3.2, 11.3, 1.0)), ("Rocks south-east", (17.6, 11.4, 0.9))):
        bv, bf = [], []
        low = ground_height(x, y) - rr * 0.3
        reb.boulder(rng, (x, y, low), rr, bv, bf, squash=0.75)
        reb.boulder(rng, (x + 0.9, y + 0.4, low), rr * 0.7, bv, bf, squash=0.75)
        reb.mask(reb.wall(reb.mesh_object(name, bv, bf, rock)))
    stones = [(rng.uniform(X0, X1), rng.uniform(Y0, Y1), rng.uniform(0.04, 0.09)) for _ in range(40)]
    kit.rocks("Stones", rng, [s for s in stones if not no_grass(s[0], s[1]) or on_path(s[0], s[1])], ground_height, rock, grass=False)

    # ---- Smoke from the stovepipe: a thin wisp, small puffs that rise and thin.
    smoke_m = bpy.data.materials.new("Smoke")
    smoke_m.use_nodes = True
    nodes = smoke_m.node_tree.nodes
    nodes.remove(nodes["Principled BSDF"])
    vol = nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.7, 0.7, 0.72, 1)
    vol.inputs["Density"].default_value = 1.0
    smoke_m.node_tree.links.new(vol.outputs["Volume"], nodes["Material Output"].inputs["Volume"])
    puffs = []
    PUFFS = 10
    for i in range(PUFFS):
        ob = reb.prim("sphere", f"Smoke puff {i}", None, (0, 0, 0), (1, 1, 1), segments=12)
        m = smoke_m.copy()
        ob.data.materials.append(m)
        puffs.append((ob, m))

    # ---- Light: the morning sun low in the east through the trees, the
    # overcast the cameras see, the land out to the ranges, mist in the trees.
    kit.time_light("morning", sun_heading=125, sun_energy=6.0, mist=((10, 7, 4), (80, 80, 16), 0.006))
    kit.overcast_sky(glow=(0.8, -0.6))
    kit.backdrop((10.0, 7.0, 2.0), spread=360, below=-40.0, near=40.0, forest_to=1800.0, trees=110000,
                 keep_out=lambda x, y: math.hypot(x - 10.0, y - 7.0) < 38, shape=far_land, mist=30.0, rng=random.Random(5))
    reb.spot("Soft yard light", (10, 7, 14), (10, 7, 0), 16000, (0.9, 0.86, 0.75), 120, 1, 6)
    reb.spot("Pine light", (14, 9, 9), (15, 13.5, 0), 5000, (0.85, 0.85, 0.8), 70, 1, 4)

    def pose(k):
        phase = 2 * math.pi * k / FRAMES
        # Hazard lights: on for half the loop.
        on = (k // 4) % 2 == 0
        reb.emit_strength(amber, 30 if on else 0.2)
        hazard.data.energy = 6 if on else 0
        hazard_rear.data.energy = 4 if on else 0
        # Flag: a slow ripple toward the fly end.
        for idx, vtx in enumerate(flag.data.vertices):
            p = flag_rest[idx]
            u = (p.x - FLAGPOLE[0]) / 1.35
            vtx.co = (p.x - 0.02 * u * (1 - math.cos(phase * 2 + u * 4)), p.y + 0.06 * u * math.sin(phase * 2 + u * 5), p.z - 0.05 * u)
        flag.data.update()
        # Smoke: puff i sits a fraction (i + k / FRAMES) of the way up a thin wisp.
        for i, (ob, m) in enumerate(puffs):
            t = (i + k / FRAMES) / PUFFS
            ob.location = (STOVEPIPE[0] - 0.5 * t * t + 0.04 * math.sin(6 * t + phase), STOVEPIPE[1] + 0.25 * t, 4.6 + 2.2 * t)
            s = 0.1 + 0.32 * t
            ob.scale = (s, s * 0.8, s * 1.3)
            m.node_tree.nodes["Principled Volume"].inputs["Density"].default_value = 0.5 * (1 - t) ** 1.5

    place_pine(0)
    # The kit's worn, bitty surfaces, as every kit room has.
    kit.wear(float(os.environ.get("RE1_WEAR", "1.3")))
    reb.export(
        CAMERAS,
        OUT,
        samples=256,
        extra={
            "bounds": {"x0": reb.g(X0), "z0": reb.g(Y0), "x1": reb.g(X1), "z1": reb.g(Y1)},
            # Underfoot (sound/ground.ts): the meadow and its worn dirt.
            "ground": "earth",
            "floors": [],
            "exits": [
                {"x0": reb.g(2.0), "z0": 0, "x1": reb.g(4.5), "z1": reb.g(Y0) + 10},
            ],
        },
        anim={"frames": FRAMES, "ticks": 3, "set": pose},
        # The pine drags clear as she watches from the winch (camera 3): 12
        # pictures, 5 game frames each, two seconds behind her line.
        states=[{"name": "pine", "bank": 1, "bit": PINE_FLAG, "set": place_pine, "motion": {"frames": 12, "ticks": 5}, "cameras": [3]}],
    )


build()
