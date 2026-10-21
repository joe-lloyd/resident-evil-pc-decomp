"""The ranger station's yard, outside the lookout, in the morning.

A clearing on the mountain. The trail from the ridge comes in at the north-
west corner by the station sign. The cabin stands on the north side with its
porch to the south, smoke still rising from the stovepipe. A tool shed, padlocked,
on the west. The ranger's truck is parked in the middle, hazard lights
blinking on a dying battery, a winch on its front bumper. In the south-east
the trail goes on down the mountain, but last night's storm brought a pine
down across it. Out by the east edge, the ranger's rifle lies in the grass
where drag marks lead off into the trees.

Metres, real sizes (reb.UNITS). She walks the flat clearing x 2-18,
y 2-12.2; the ground falls away beyond it.

Moving: smoke from the stovepipe, the flag, the hazard lights, the grass.
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


def G(x, y, z=0.0):
    return (reb.g(x), -reb.g(z), reb.g(y))


CAMERAS = [
    # 0: from up the trail, north-west, over the yard: the sign, the shed, the flag, the cabin.
    {"from": G(2.6, -1.4, 4.0), "to": G(9.0, 8.5, 0.0), "fov": 200, "clip_end": 2000},
    # 1: from the south-east edge, at the cabin front, its porch and his rifle in the grass.
    {"from": G(18.5, 11.5, 3.6), "to": G(12.5, 4.5, 1.0), "fov": 200, "clip_end": 2000},
    # 2: from by the flagpole, south-west at the shed door and the truck's tailgate.
    {"from": G(9.4, 5.6, 3.0), "to": G(3.8, 9.6, 0.3), "fov": 200, "clip_end": 2000},
    # 3: from by the porch, south-west at the truck's winch and the pine across the trail.
    {"from": G(16.0, 7.5, 3.8), "to": G(12.5, 12.0, 0.3), "fov": 200, "clip_end": 2000},
]


def ground_height(x, y):
    """Flat where she walks; the mountain rises behind and falls away to the south."""
    h = 0.02 * noise.noise(Vector((x * 0.7, y * 0.7, 0)))
    if y > Y1 + 0.3:
        h -= (y - Y1 - 0.3) * 0.38
    if y < Y0 - 0.5:
        h += (Y0 - 0.5 - y) * 0.45
    if x < X0 - 0.5:
        h += (X0 - 0.5 - x) * 0.25
    if x > X1 + 0.5:
        h += (x - X1 - 0.5) * 0.15
    return h + 0.4 * noise.noise(Vector((x * 0.15, y * 0.15, 3))) * (0 if X0 - 0.5 < x < X1 + 0.5 and Y0 - 0.5 < y < Y1 + 0.3 else 1)


def inside(x, y, box, pad=0.0):
    return box[0] - pad < x < box[1] + pad and box[2] - pad < y < box[3] + pad


def shed(rng, planks, iron):
    """A framed timber shed with a seated gable roof and a fitted east door."""
    sx0, sx1, sy0, sy1 = SHED
    centre_y = (sy0 + sy1) / 2
    reb.wall(kit.box_center("Shed footprint", None, ((sx0+sx1)/2,centre_y,1), (sx1-sx0,sy1-sy0,2))).hide_render=True
    for ob in kit.walls(sx0, sy0, sx1, sy1, 2.15, planks,
                        openings=[("e", SHED_DOOR[0], SHED_DOOR[1], 0, 1.95)], thick=0.1, name="Shed siding"):
        reb.mask(reb.wall(ob))
    roof_m = reb.mat_surface("Weathered shed tin", [(0, (0.075, 0.08, 0.075)), (0.6, (0.22, 0.22, 0.18)), (1, (0.25, 0.12, 0.05))], scale=8, rough=0.85)
    for x in (sx0, sx1):
        reb.mesh_object("Shed gable", [(x, sy0, 2.15), (x, sy1, 2.15), (x, centre_y, 2.65)], [(0, 1, 2)], planks, smooth=False)
    for side in (-1, 1):
        ye = centre_y + side * ((sy1 - sy0) / 2 + 0.18)
        reb.mesh_object("Seated shed roof", [(sx0-0.2, ye, 2.07), (sx1+0.2, ye, 2.07), (sx1+0.2, centre_y, 2.68), (sx0-0.2, centre_y, 2.68)], [(0,1,2,3)], roof_m, smooth=False)
        for x in (sx0 - 0.14, sx1 + 0.14):
            kit.rod("Shed barge board", planks, (x, ye, 2.06), (x, centre_y, 2.67), 0.055)
        for i in range(12):
            x = sx0 - 0.15 + (sx1 - sx0 + 0.3) * i / 11
            kit.rod("Tin standing seam", roof_m, (x, ye, 2.085), (x, centre_y, 2.69), 0.012, 4)
    y0, y1 = SHED_DOOR
    for yy in (y0 - 0.045, y1 + 0.045):
        kit.box_center("Door jamb", planks, (sx1+0.06, yy, 1.01), (0.13, 0.09, 2.02))
    kit.box_center("Door lintel", planks, (sx1+0.06, (y0+y1)/2, 2.0), (0.13, y1-y0+0.18, 0.12))
    for i in range(5):
        kit.box_center("Fitted door plank", planks, (sx1+0.11, y0+(i+0.5)*(y1-y0)/5, 0.98), (0.06, (y1-y0)/5-0.008, 1.90))
    for z in (0.35, 1.55):
        kit.box_center("Door brace", planks, (sx1+0.15, (y0+y1)/2, z), (0.05, y1-y0-0.05, 0.10))
        kit.box_center("Strap hinge", iron, (sx1+0.105, y1-0.12, z), (0.025, 0.25, 0.05))
    kit.rod("Diagonal door brace", planks, (sx1+0.07,y0+0.08,0.4), (sx1+0.07,y1-0.08,1.5), 0.055)
    kit.box_center("Hasp", iron, (sx1+0.11,y0+0.06,1.02), (0.025,0.16,0.06))
    kit.box_center("Padlock", reb.mat_metal("Lock brass", (0.42,0.31,0.12),0.5), (sx1+0.14,y0+0.06,0.96), (0.05,0.065,0.09), bevel=0.008)


def ranger_truck(paint, white):
    """Square-bodied ranger pickup: visible axle, suspension, cut wheel arches,
    open load bed, separate flat windscreen and framed cab."""
    origin = Vector((8.25, 10.8, 0))
    parts = []
    def box(name, m, p, size, **kw):
        ob = kit.box_center(name, m, tuple(origin + Vector(p)), size, **kw)
        parts.append(ob)
        return ob
    metal, rubber = kit.mat("iron"), kit.mat("rubber")
    glass = reb.mat_plain("Dusty flat windscreen", (0.08,0.12,0.125), 0.27)
    for y in (-0.56,0.56):
        box("Chassis rail", metal, (0,y,0.48), (5.0,0.12,0.18))
    for x in (-1.65,1.65):
        parts.append(kit.rod("Axle",metal, origin+Vector((x,-0.95,0.39)), origin+Vector((x,0.95,0.39)),0.065))
        box("Differential",metal,(x,0,0.39),(0.28,0.26,0.24),bevel=0.06)
        for y in (-0.78,0.78):
            parts.extend(kit.wheel("Truck wheel",tuple(origin+Vector((x,y,0.4))),r=0.4,width=0.30,detail=True))
            for j in range(4):
                box("Leaf spring",metal,(x,y*0.75,0.53+j*0.022),(0.95-j*0.14,0.07,0.025))
            # A shaped side skin around an actual circular wheel opening.
            v, f = [], []
            for j in range(17):
                a=math.pi*j/16
                xx=x+math.cos(a)*0.50; z=0.4+math.sin(a)*0.50
                v.extend([tuple(origin+Vector((xx,y/abs(y)*0.94,z))),tuple(origin+Vector((xx,y/abs(y)*0.94,1.17)))])
            for j in range(16):
                k=j*2; f.append((k,k+1,k+3,k+2))
            parts.append(reb.mesh_object("Wheel arch panel",v,f,paint,smooth=False))
    box("Open bed floor",kit.mat("planks"),(-1.42,0,0.83),(2.22,1.70,0.08))
    for y in (-0.92,0.92):
        for x, length in ((-2.34,0.53),(-0.65,0.95)):
            box("Bed quarter",paint,(x,y,0.95),(length,0.08,0.47))
        box("Bed top rail",paint,(-1.42,y,1.21),(2.35,0.11,0.09),bevel=0.018)
    box("Tailgate",paint,(-2.62,0,0.98),(0.1,1.87,0.48),bevel=0.015)
    box("Tailgate inset",paint,(-2.68,0,0.98),(0.025,1.45,0.28),bevel=0.015)
    box("Tailgate handle",kit.mat("steel"),(-2.7,0,1.13),(0.03,0.24,0.04))
    box("Cab floor",paint,(0.45,0,0.7),(1.5,1.85,0.15))
    box("Cab back",paint,(-0.28,0,1.17),(0.10,1.86,1.0))
    box("Rear glass",glass,(-0.34,0,1.5),(0.015,1.25,0.4))
    box("Bonnet",paint,(1.92,0,1.05),(1.46,1.85,0.24),bevel=0.04)
    box("Cab roof",paint,(0.4,0,1.97),(1.60,1.91,0.12),bevel=0.035)
    # The windscreen is one plane between two straight posts.
    for y in (-0.88,0.88):
        parts.append(kit.rod("Windscreen pillar",paint,origin+Vector((1.23,y,1.15)),origin+Vector((1.10,y,1.92)),0.055))
        parts.append(kit.rod("Rear cab pillar",paint,origin+Vector((-0.28,y,1.15)),origin+Vector((-0.28,y,1.92)),0.05))
        box("Window sill",paint,(0.47,y,1.2),(1.50,0.08,0.10))
    v=[tuple(origin+Vector(p)) for p in ((1.235,-0.83,1.22),(1.235,0.83,1.22),(1.112,0.83,1.89),(1.112,-0.83,1.89))]
    parts.append(reb.mesh_object("Flat windscreen",v,[(0,1,2,3)],glass,smooth=False))
    box("Cab seat",kit.mat("rubber"),(0.10,0,1.00),(0.45,1.55,0.18),bevel=0.04)
    box("Cab seat back",kit.mat("rubber"),(-0.10,0,1.29),(0.15,1.55,0.6),bevel=0.04)
    box("Closed passenger door",paint,(0.48,0.94,0.94),(1.45,0.06,0.53))
    box("Passenger window",glass,(0.44,0.935,1.55),(1.28,0.02,0.58))
    door=box("Open driver door",paint,(0.6,-1.5,0.94),(1.35,0.06,0.53),rot=0.8,bevel=0.02)
    box("Driver door window",glass,(0.6,-1.5,1.54),(1.35,0.025,0.60),rot=0.8)
    for z in (1.25,1.86):
        box("Driver window frame",paint,(0.6,-1.5,z),(1.4,0.05,0.05),rot=0.8)
    for x in (-2.75,2.72):
        box("Bumper",kit.mat("steel"),(x,0,0.57),(0.14,1.97,0.18),bevel=0.025)
    box("Grille",metal,(2.675,0,0.91),(0.05,1.85,0.42))
    for z in (0.79,0.9,1.01):
        box("Grille bar",kit.mat("steel"),(2.71,0,z),(0.025,1.20,0.025))
    for y in (-0.72,0.72):
        box("Headlamp",white,(2.72,y,0.94),(0.035,0.27,0.22),bevel=0.025)
        box("Tail lamp",kit.mat("red paint"),(-2.69,y,1.0),(0.035,0.13,0.28))
    return kit.join("Truck",parts,origin=tuple(origin))


def build():
    rng = random.Random(23)
    reb.clear_scene()

    grass_m = reb.mat_surface("Meadow", [(0.0, (0.06, 0.08, 0.025)), (0.5, (0.13, 0.15, 0.05)), (1.0, (0.2, 0.18, 0.09))], scale=1.5, bump=0.4)
    dirt = reb.mat_surface("Dirt", [(0.0, (0.1, 0.075, 0.05)), (1.0, (0.2, 0.15, 0.1))], scale=6, bump=0.6)
    logs = reb.mat_wood("Logs", (0.21, 0.13, 0.075))
    dark = reb.mat_wood("Dark wood", (0.09, 0.055, 0.035))
    planks = reb.mat_wood("Weathered planks", (0.26, 0.22, 0.17))
    shingle = reb.mat_surface("Shingles", [(0.0, (0.05, 0.045, 0.04)), (1.0, (0.13, 0.1, 0.08))], scale=12, bump=0.5)
    iron = reb.mat_metal("Iron", (0.05, 0.048, 0.045), rough=0.6)
    rust = reb.mat_surface("Rust", [(0.0, (0.15, 0.06, 0.02)), (1.0, (0.3, 0.14, 0.05))], scale=20, rough=0.8)
    paint = reb.mat_surface("Truck paint", [(0.0, (0.06, 0.12, 0.07)), (1.0, (0.09, 0.16, 0.09))], scale=8, rough=0.45, bump=0.1)
    white = reb.mat_plain("White paint", (0.6, 0.6, 0.56), 0.5)
    chrome = reb.mat_metal("Chrome", (0.7, 0.7, 0.7), 0.15)
    rubber = reb.mat_plain("Tyre", (0.02, 0.02, 0.02), 0.85)
    glass = reb.mat_glass("Glass", (0.6, 0.7, 0.7))
    bark = reb.mat_surface("Bark", [(0.0, (0.05, 0.035, 0.025)), (1.0, (0.13, 0.09, 0.06))], scale=10, bump=0.9)
    needles = reb.mat_cards("Needles", (0.02, 0.05, 0.025), (0.07, 0.12, 0.05))
    dead = reb.mat_cards("Dry needles", (0.12, 0.09, 0.04), (0.2, 0.17, 0.08))
    blades = reb.mat_cards("Grass", (0.07, 0.1, 0.03), (0.22, 0.24, 0.08))
    ferns = reb.mat_cards("Fern", (0.04, 0.09, 0.03), (0.1, 0.18, 0.05))
    rock = reb.mat_surface("Granite", [(0.0, (0.12, 0.12, 0.11)), (1.0, (0.3, 0.29, 0.27))], scale=3, bump=0.9)
    blood = reb.mat_plain("Blood", (0.1, 0.005, 0.004), 0.3)
    sign_m = reb.mat_plain("Sign brown", (0.16, 0.09, 0.04), 0.7)
    letter = reb.mat_plain("Sign letters", (0.75, 0.7, 0.5), 0.6)
    amber = reb.mat_emit("Hazard", (1.0, 0.55, 0.1), 30)
    flag_m = reb.mat_stripes("Flag", [(0.05, 0.12, 0.08), (0.6, 0.55, 0.35)], across=6, axis="Z")

    # ---- Ground: the flat yard, the slope beyond, dirt where feet and tyres have worn it.
    reb.terrain("Ground", grass_m, (-8, 28), (-8, 30), ground_height, step=0.5)
    paths = [
        [(3.0, 1.0), (4.0, 3.5), (7.0, 6.0), (10.5, 7.6), (13.0, 7.8)],      # trail mouth to the porch
        [(10.5, 7.6), (12.5, 9.0), (14.5, 10.8), (15.8, 12.2), (16.2, 14.5), (16.6, 18.0), (17.2, 24.0)],  # down the mountain
        [(7.0, 6.0), (6.0, 7.7)],                                              # to the shed door
        [(-1.0, 10.8), (6.0, 10.8)],                                           # tyre tracks the truck came in by
    ]
    v, f = [], []
    for path in paths:
        for (ax, ay), (bx, by) in zip(path, path[1:]):
            a, b = Vector((ax, ay)), Vector((bx, by))
            d = (b - a)
            n = int(d.length / 0.3) + 1
            side = Vector((-d.y, d.x)).normalized()
            for i in range(n):
                p = a.lerp(b, i / n)
                w = 0.6 + 0.25 * noise.noise(Vector((p.x, p.y, 7)))
                for s0, s1 in ((-w, w),):
                    k = len(v)
                    q0, q1 = p + side * s0, p + side * s1
                    r = a.lerp(b, (i + 1) / n)
                    r0, r1 = r + side * s0, r + side * s1
                    for q in (q0, q1, r1, r0):
                        v.append((q.x, q.y, ground_height(q.x, q.y) + 0.008))
                    f.append((k, k + 1, k + 2, k + 3))
    reb.mesh_object("Worn paths", v, f, dirt)

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
    # A continuous roof seated on the log walls, with boards along the eaves.
    ridge_z, eave_z, over = 4.0, 2.5, 0.4
    cym = (cy0 + cy1) / 2
    for side in (-1, 1):
        ye = cym + side * ((cy1 - cy0) / 2 + over)
        reb.mesh_object("Cabin shingle roof", [(cx0-over,ye,eave_z-0.2),(cx1+over,ye,eave_z-0.2),(cx1+over,cym,ridge_z),(cx0-over,cym,ridge_z)], [(0,1,2,3)], shingle, smooth=False)
        kit.box_center("Cabin fascia", dark, ((cx0+cx1)/2,ye,eave_z-0.22), (cx1-cx0+2*over,0.12,0.20))
        for i in range(1,13):
            t=i/13
            yy=ye+(cym-ye)*t; zz=eave_z-0.2+(ridge_z-eave_z+0.2)*t
            kit.rod("Shingle course",shingle,(cx0-over,yy,zz+0.012),(cx1+over,yy,zz+0.012),0.018,4)
    for x in (cx0-0.16,cx1+0.16):
        reb.mesh_object("Cabin gable",[(x,cy0-0.15,2.5),(x,cy1+0.15,2.5),(x,cym,ridge_z)],[(0,1,2)],planks,smooth=False)
    reb.prim("cyl", "Stovepipe", iron, (STOVEPIPE[0], STOVEPIPE[1], 3.6), (0.16, 0.16, 1.6))
    reb.prim("cone", "Stovepipe cap", iron, (STOVEPIPE[0], STOVEPIPE[1], 4.48), (0.36, 0.36, 0.16), top=0.1)
    # Windows: dark glass; the east one smashed, blood down the logs below it.
    for (x, y, rot) in ((12.45, cy0 - 0.27, 0), (14.6, cy1 + 0.27, 0)):
        reb.prim("cube", "Window", glass, (x, y, 1.35), (0.9, 0.02, 0.7), rot=(0, 0, rot))
        reb.prim("cube", "Window frame", dark, (x, y, 1.35), (1.0, 0.06, 0.08))
        reb.prim("cube", "Window frame", dark, (x, y, 1.35), (0.06, 0.06, 0.8))
    reb.prim("cube", "Broken window", reb.mat_plain("Dark inside", (0.01, 0.008, 0.006)), (cx1 + 0.28, 3.05, 1.35), (0.02, 0.9, 0.7))
    for i in range(6):
        reb.prim("cube", "Blood run", blood, (cx1 + 0.3, 2.9 + i * 0.06, 0.75 - i * 0.03), (0.01, 0.025, 0.4 + 0.05 * i))
    # The door, the porch deck, its steps, posts and roof.
    reb.prim("cube", "Cabin door", planks, ((DOOR[0] + DOOR[1]) / 2, cy1 + 0.27, 1.0), (DOOR[1] - DOOR[0], 0.05, 2.0), bevel=0.01)
    px0, px1, py0, py1 = PORCH
    reb.wall(reb.prim("cube", "Porch deck", planks, ((px0 + px1) / 2, (py0 + py1) / 2, 0.11), (px1 - px0, py1 - py0, 0.22), bevel=0.01))
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

    # ---- The shed is framed and roofed as one building.
    shed(rng, planks, iron)

    # ---- The truck: a green ranger pickup, driver's door open, the winch on its bumper.
    tx0, tx1, ty0, ty1 = TRUCK
    tym = (ty0 + ty1) / 2
    truck = ranger_truck(paint, white)
    body = [truck]
    # Gear in the bed: a jerrycan, a coil of rope, a tarp.
    reb.prim("cube", "Jerrycan", reb.mat_plain("Red can", (0.35, 0.04, 0.03), 0.5), (tx0 + 0.6, ty0 + 0.45, 1.07), (0.35, 0.18, 0.45), bevel=0.02)
    reb.cloth("Tarp", reb.mat_plain("Tarp", (0.12, 0.15, 0.1), 0.8), (tx0 + 1.5, tym + 0.2, 0.92), (1.6, 1.2), lumps=0.08, seed=4)
    for x in (tx0, tx1):
        for y in (ty0 + 0.12, ty1 - 0.12):
            hz = amber
            reb.prim("cube", "Hazard light", hz, (x + (0.02 if x == tx1 else -0.02), y, 1.0 if x == tx1 else 1.12), (0.04, 0.12, 0.07))
    hazard = reb.point("Hazard glow", (tx1 + 0.3, tym, 1.0), 6, (1.0, 0.5, 0.1), 0.3)
    hazard_rear = reb.point("Hazard glow rear", (tx0 - 0.3, tym, 1.1), 4, (1.0, 0.5, 0.1), 0.3)
    # The winch: a drum on the bumper, the cable wound on, the hook hanging.
    reb.prim("cyl", "Winch drum", rust, WINCH, (0.22, 0.22, 0.6), rot=(math.pi / 2, 0, 0), segments=18)
    reb.prim("cyl", "Winch cable", reb.mat_metal("Cable", (0.25, 0.24, 0.22), 0.5), WINCH, (0.26, 0.26, 0.5), rot=(math.pi / 2, 0, 0), segments=18)
    reb.prim("cube", "Winch frame", iron, (WINCH[0], WINCH[1], WINCH[2] - 0.05), (0.2, 0.75, 0.3))
    reb.prim("cube", "Crank socket", iron, (WINCH[0] + 0.02, WINCH[1] + 0.36, WINCH[2]), (0.06, 0.06, 0.06))
    hook = reb.prim("cube", "Winch hook", iron, (WINCH[0] + 0.15, WINCH[1], 0.32), (0.04, 0.08, 0.14))
    # Its footprint, with the open door and the winch.
    truck_box = reb.prim("cube", "Truck footprint", None, ((tx0 + tx1) / 2 + 0.15, tym - 0.4, 0.8), (tx1 - tx0 + 0.4, ty1 - ty0 + 0.8, 1.6))
    reb.wall(truck_box).hide_render = True
    for ob in body:
        reb.mask(ob)

    # ---- The pine across the trail, its root plate torn up at the west end.
    def pine_mesh():
        verts, faces = [], []
        prng = random.Random(4)
        length, r0 = 8.5, 0.3
        # Trunk: rings along +x from the root.
        segs = 10
        rings = 12
        for i in range(rings + 1):
            t = i / rings
            rr = r0 * (1 - 0.85 * t)
            for s in range(segs):
                a = 2 * math.pi * s / segs
                verts.append((t * length, math.cos(a) * rr, rr + math.sin(a) * rr))
        for i in range(rings):
            for s in range(segs):
                k = i * segs + s
                faces.append((k, k + (s + 1) % segs - s, k + segs + (s + 1) % segs - s, k + segs))
        trunk = reb.mesh_object("Pine trunk", verts, faces, bark)
        # Splintered break with projecting wood fibres, never a circular base.
        parts = []
        for j in range(9):
            a = math.tau*j/9
            y, z = math.cos(a)*0.23, 0.3+math.sin(a)*0.23
            parts.append(kit.rod("Broken trunk splinter", logs, (0.12,y,z), (-prng.uniform(0.08,0.5),y*0.8,z+prng.uniform(-0.05,0.05)), 0.04, 5))
        # Branches: drooping needle cards along the upper two thirds, pressed flat where they hit the ground.
        nv, nf = [], []
        up = Vector((0, 0, 1))
        for _ in range(7000):
            t = prng.uniform(0.3, 1.0)
            x = t * length
            reach = (1.0 - t) * 2.0 + 0.4
            a = prng.uniform(0, 2 * math.pi)
            out = Vector((0.3, math.cos(a), math.sin(a))).normalized()
            base = Vector((x, 0, r0 * (1 - 0.85 * t))) + out * prng.uniform(0.0, reach)
            if base.z < 0.03:
                base.z = 0.03 + prng.uniform(0, 0.05)
            reb.card(nv, nf, base, out, up, prng.uniform(0.05, 0.1), prng.uniform(0.15, 0.32), prng.uniform(0.2, 0.7))
        cards = reb.mesh_object("Pine needles", nv, nf, needles)
        bpy.ops.object.empty_add(location=(0, 0, 0))
        pivot = bpy.context.active_object
        pivot.name = "Pine"
        for ob in [trunk, cards] + parts:
            ob.parent = pivot
        return pivot

    pine = pine_mesh()
    pine_rest = ((12.6, 13.0, 0.0), (0, 0, -0.04))
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
    for i in range(14):
        t = i / 13
        p = Vector((16.3, 6.4)).lerp(Vector((19.5, 8.3)), t)
        reb.prim("cube", "Drag mark", blood if i % 3 else dirt, (p.x, p.y, ground_height(p.x, p.y) + 0.01), (0.5, 0.08, 0.004), rot=(0, 0, 0.55 + rng.uniform(-0.1, 0.1)))
    for i in range(9):
        reb.prim("cyl", "Blood", blood, (16.2 + rng.uniform(-0.4, 0.6), 6.4 + rng.uniform(-0.3, 0.4), 0.006), (rng.uniform(0.04, 0.12),) * 2 + (0.003,), segments=10)
    # Paw prints in the dirt by the porch, too big for any dog.
    for i in range(8):
        reb.prim("cyl", "Paw print", reb.mat_plain("Print", (0.04, 0.03, 0.02), 0.9), (15.9 - i * 0.35, 7.6 + (i % 2) * 0.2, 0.012), (0.12, 0.1, 0.004), segments=10)

    # ---- Forest: spruces round the clearing, grass, ferns and rocks.
    tv, tf = [], []
    bases = []
    def free_for_tree(x, y):
        if X0 - 3.5 < x < X1 + 3.5 and Y0 - 3.0 < y < Y1 + 2.0:
            return False
        if 1.0 < x < 5.0 and y < Y0:          # the trail from the ridge
            return False
        if 14.0 < x < 19.5 and y > Y1:        # the trail down
            return False
        return True
    tries = 0
    while len(bases) < 70 and tries < 5000:
        tries += 1
        x, y = rng.uniform(-9, 30), rng.uniform(-8, 30)
        if not free_for_tree(x, y) or any((Vector((x, y)) - b.xy).length < 1.6 for b, _ in bases):
            continue
        h = rng.uniform(11, 19)
        bases.append((Vector((x, y, ground_height(x, y) - 0.2)), h))
    for base, h in bases:
        reb.conifer(rng, base, h, tv, tf)
    reb.mesh_object("Spruces", tv, tf, needles)
    reb.trunks("Spruce trunks", bark, bases)
    gv, gf = [], []
    def meadow(rr):
        while True:
            x, y = rr.uniform(-7, 27), rr.uniform(-7, 28)
            if inside(x, y, CABIN, 0.5) or inside(x, y, PORCH, 0.3) or inside(x, y, SHED, 0.3) or inside(x, y, TRUCK, 0.1):
                continue
            if kit.path_distance(x, y, paths) < 0.95:
                continue
            return x, y
    reb.grass_tufts(rng, 16000, meadow, ground_height, gv, gf)
    grass = reb.mesh_object("Grass", gv, gf, blades, smooth=False)
    grass_rest = [Vector(p) for p in gv]
    fv2, ff2 = [], []
    for _ in range(26):
        x, y = rng.uniform(-1, 21), rng.uniform(0, 15)
        if free_for_tree(x, y) and not (14 < x < 19 and y > 11):
            reb.fern(rng, (x, y, ground_height(x, y)), rng.uniform(0.4, 0.8), fv2, ff2)
    reb.mesh_object("Ferns", fv2, ff2, ferns)
    rv, rf = [], []
    for (x, y, rr) in ((1.2, 6.0, 0.6), (18.9, 4.5, 0.7), (13.8, 14.2, 0.5), (18.6, 13.8, 0.6), (6.8, 13.2, 0.8)):
        reb.boulder(rng, (x, y, ground_height(x, y)), rr, rv, rf)
    reb.mesh_object("Rocks", rv, rf, rock)
    # Rocks and brush fill the corners no camera sees well, so she cannot stand there.
    for name, (x, y, rr) in (("Rocks south-west", (3.2, 11.3, 1.0)), ("Rocks south-east", (17.6, 11.4, 0.9))):
        bv, bf = [], []
        reb.boulder(rng, (x, y, 0.0), rr, bv, bf)
        reb.boulder(rng, (x + 0.9, y + 0.4, 0.0), rr * 0.7, bv, bf)
        reb.mask(reb.wall(reb.mesh_object(name, bv, bf, rock)))
    # Needles shed on the ground under the trees nearest the yard.
    dv, df = [], []
    for _ in range(900):
        x, y = rng.uniform(-3, 23), rng.uniform(-3, 18)
        if free_for_tree(x, y):
            reb.card(dv, df, Vector((x, y, ground_height(x, y) + 0.01)), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), Vector((0, 0, 1)), 0.08, 0.3, 0.0)
    reb.mesh_object("Fallen needles", dv, df, dead)

    # ---- Smoke from the stovepipe: puffs that rise, swell and thin, round a loop.
    smoke_m = bpy.data.materials.new("Smoke")
    smoke_m.use_nodes = True
    nodes = smoke_m.node_tree.nodes
    nodes.remove(nodes["Principled BSDF"])
    vol = nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.7, 0.7, 0.72, 1)
    vol.inputs["Density"].default_value = 1.0
    smoke_m.node_tree.links.new(vol.outputs["Volume"], nodes["Material Output"].inputs["Volume"])
    puffs = []
    PUFFS = 6
    for i in range(PUFFS):
        ob = reb.prim("sphere", f"Smoke puff {i}", None, (0, 0, 0), (1, 1, 1), segments=12)
        m = smoke_m.copy()
        ob.data.materials.append(m)
        puffs.append((ob, m))

    kit.tree_roots(rng, bases, ground_height, lambda x, y: kit.path_distance(x,y,paths)<0.95)
    kit.forest(rng, ground_height, lambda x,y: not free_for_tree(x,y), (-30,-28,48,50), count=200, spacing=2.0, ferns=60)
    kit.mountain_forest(rng, (10,7), near=43, below=-80)
    kit.time_light("morning", sun_heading=125, sun_energy=5.0)
    reb.spot("Yard sky fill",(10,7,13),(10,7,0),12000,(0.9,0.88,0.75),130,1,8)

    def pose(k):
        phase = 2 * math.pi * k / FRAMES
        # Hazard lights: on for half the loop.
        on = (k // 4) % 2 == 0
        reb.emit_strength(amber, 30 if on else 0.2)
        hazard.data.energy = 6 if on else 0
        hazard_rear.data.energy = 4 if on else 0
        # Flag: a travelling wave, stronger toward the fly end.
        for idx, vtx in enumerate(flag.data.vertices):
            p = flag_rest[idx]
            u = (p.x - FLAGPOLE[0]) / 1.35
            vtx.co = (p.x - 0.015 * u * (1 - math.cos(phase * 2 + u * 4)), p.y + 0.045 * u * math.sin(phase * 2 + u * 5), p.z - 0.05 * u)
        flag.data.update()
        # Grass: the tip of each blade sways with a gust that rolls across the yard.
        for idx in range(2, len(grass_rest), 3):
            p = grass_rest[idx]
            w = math.sin(phase + p.x * 0.6 + p.y * 0.25)
            grass.data.vertices[idx].co = (p.x + 0.018 * w, p.y + 0.007 * w, p.z)
        grass.data.update()
        # Smoke: puff i sits a fraction (i + k / FRAMES) of the way up the plume.
        for i, (ob, m) in enumerate(puffs):
            t = (i + k / FRAMES) / PUFFS
            ob.location = (STOVEPIPE[0] - 0.25 * t * t, STOVEPIPE[1] + 0.15 * t, 4.6 + 1.4 * t)
            s = 0.12 + 0.35 * t
            ob.scale = (s, s * 0.9, s * 0.8)
            m.node_tree.nodes["Principled Volume"].inputs["Density"].default_value = 0.25 * (1 - t) ** 1.5

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
