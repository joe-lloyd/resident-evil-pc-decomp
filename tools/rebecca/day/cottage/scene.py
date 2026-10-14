"""Hal's cottage on the east path, late afternoon.

What it tells: Hal ran the gondola and lived here alone; his daughter
visits in the summers. After car 4 came up he got home bitten, bolted the
door and dropped the bar across it. He washed the bite at the sink and the
towels are still in it, red. He emptied the first aid tin on the table. He
dragged a chair to the window and sat watching the path with his
binoculars: the scrape marks run from the table to the window. He slept,
or tried to: the bed is thrown back and the pillow is bloody. The radio is
still on, hissing on an empty frequency. Then he lifted the bar and drew
the bolt and left, and wrote last in his diary on the table: "it itches.
hide in the mine till they come." The quarry office key still hangs on its
hook by the door. On the wall over the drawers are the photos of his
daughter, the big one of her holding up a fish; his rods stand in the
corner.

Metres: the floor is x 1.0-5.4, y 1.0-4.4, 2.3 high under the beams. The
door is in the south wall at x 2.6-3.5, out onto the east path; windows in
the south wall at x 1.55-2.25 and x 4.15-4.85 (the cracked one), and in
the east wall at y 2.0-2.7. The door is shut, its bolt drawn. The bed is
along the west wall, the drawers and the photos on the north wall, the sink east of them, the stove in the
south-east by the chimney, the table in the middle.

Moving: the radio's dial glow pulsing with the static; the curtain at the
cracked window stirring in the draught; blood dripping off the sink's edge.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
from kit import mat  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import bpy  # noqa: E402

X0, X1, Y0, Y1, H = 1.0, 5.4, 1.0, 4.4, 2.3
DOOR = (2.6, 3.5)
WIN_W = (1.55, 2.25)
WIN_E = (4.15, 4.85)
WIN_SIDE = (2.0, 2.7)
WIN_Z = (1.0, 1.8)



def settle(ob, at, offset, turn=0.0, tilt=None):
    """Put a kit piece where it was meant to go. kit.join keeps the first
    part's origin and turn, so kit.chair, crate, shelves, crow and body come
    out shifted by that part's offset (a body stands on end): undo it."""
    local = Matrix.Translation(Vector(offset))
    if tilt is not None:
        local = local @ tilt.to_matrix().to_4x4()
    ob.matrix_world = Matrix.Translation(Vector(at)) @ Matrix.Rotation(turn, 4, "Z") @ local
    for c in ob.children:
        c.matrix_parent_inverse = local.inverted()
    return ob


def chair(name, m, at, rot=0.0):
    return settle(kit.chair(name, m, at, rot=rot), at, (0, 0, 0.45), rot)


def crate(name, m, at, size=(0.6, 0.5, 0.5), rot=0.0, open_=False):
    return settle(kit.crate(name, m, at, size=size, rot=rot, open_=open_), at, (0, 0, size[2] / 2), rot)


def shelves(name, m, at, size=(1.0, 0.3, 1.8), rows=4, rot=0.0, clutter=0.7, seed=0):
    ob = kit.shelves(name, m, at, size=size, rows=rows, rot=rot, clutter=clutter, seed=seed)
    return settle(ob, at, (-size[0] / 2, 0, size[2] / 2), rot)


def crow(name, at, heading=0.0, perched=True):
    b, w = kit.crow(name, at, heading=heading, perched=perched)
    settle(b, at, (0, 0, 0.12), heading)
    return b, w


def corpse(name, at, heading=0.0, pose="back", **kw):
    """kit.body lying the way it should (no `bloody`: its pool lands in the wrong place)."""
    ob = kit.body(name, at, heading=heading, pose=pose, **kw)
    if kw.get("sheet"):
        return ob
    j = kit._POSES[pose]
    missing = kw.get("missing", ())
    a, b = next((a, b) for a, b, _, _ in kit._BONES if a not in missing and b not in missing)
    pa, pb = Vector(j[a]), Vector(j[b])
    return settle(ob, at, (pa + pb) / 2, heading, (pb - pa).to_track_quat("Z", "Y"))


def drips(name, m, pts, rng, r=(0.02, 0.045), z=0.0):
    """Blood drops at points, in one mesh."""
    v, f = [], []
    for x, y in pts:
        kit._stain(v, f, rng, (x, y, z + 0.004), rng.uniform(*r), rng.uniform(0, 6.3), 0.45, (1.0, 1.0), rng.randint(0, 99), points=10, drops=rng.random() < 0.3)
    return reb.mesh_object(name, v, f, m, smooth=False)


def build():
    rng = random.Random(19)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.camera((5.25, 4.25, 2.15), (2.0, 1.8, 0.2), 200, "high over the stove: the table and the diary, the bed, the photos of his daughter")
    room.camera((1.15, 1.15, 2.15), (4.2, 3.8, 0.3), 200, "high over the bed: the door, its bar lifted off, the key hook, the rods in the corner")
    room.camera((5.25, 1.65, 2.15), (2.0, 3.6, 0.2), 200, "high over the sink: the chair dragged to the window, the scrapes, the first aid tin")
    room.camera((1.15, 4.25, 2.15), (4.6, 1.6, 0.3), 200, "high by the west window: the sink full of towels, the radio, the stove")

    pine = kit.boards("Pine panelling", (0.26, 0.17, 0.09), width=0.14, grime=0.75)
    floor_m = kit.dirtied(reb.mat_wood("Floorboards", (0.17, 0.11, 0.06)), 0.6)
    beam_m = reb.mat_wood("Beams", (0.1, 0.065, 0.04))
    frame_m = reb.mat_wood("Frames", (0.14, 0.09, 0.05))
    enamel = reb.mat_surface("Chipped enamel", [(0.0, (0.05, 0.05, 0.05)), (0.15, (0.45, 0.45, 0.42)), (1.0, (0.55, 0.55, 0.5))], scale=10, rough=0.3, bump=0.1)
    towel_m = reb.mat_surface("Bloody towel", [(0.0, (0.45, 0.43, 0.38)), (0.4, (0.3, 0.05, 0.03)), (1.0, (0.12, 0.006, 0.004))], scale=8, bump=0.2)
    pinkish = reb.mat_surface("Pink water", [(0.0, (0.16, 0.03, 0.02)), (1.0, (0.22, 0.05, 0.04))], scale=5, rough=0.05, bump=0.02)
    quilt = reb.mat_stripes("Patch quilt", [(0.16, 0.05, 0.035), (0.24, 0.2, 0.13), (0.06, 0.08, 0.1), (0.2, 0.17, 0.11)], across=6.0, axis="X")

    # ---- The shell: pine boards, plank floor, a boarded ceiling on beams, the door and the windows cut.
    kit.walls(X0, Y0, X1, Y1, H, pine, openings=[
        ("s", DOOR[0], DOOR[1], 0.0, 2.0),
        ("s", WIN_W[0], WIN_W[1], *WIN_Z),
        ("s", WIN_E[0], WIN_E[1], *WIN_Z),
        ("e", WIN_SIDE[0], WIN_SIDE[1], *WIN_Z),
    ], ceiling=kit.boards("Ceiling boards", (0.15, 0.1, 0.06), width=0.12))
    kit.plank_floor(X0 - 0.12, Y0 - 0.12, X1 + 0.12, Y1 + 0.12, floor_m, along="y", seed=3)
    for x in (1.9, 3.2, 4.5):
        reb.prim("cube", "Beam", beam_m, (x, (Y0 + Y1) / 2, H - 0.08), (0.14, Y1 - Y0 + 0.24, 0.16))
    for side, at, size in (("n", ((X0 + X1) / 2, Y0 + 0.02, 0.06), (X1 - X0, 0.04, 0.12)), ("w", (X0 + 0.02, (Y0 + Y1) / 2, 0.06), (0.04, Y1 - Y0, 0.12)), ("e", (X1 - 0.02, (Y0 + Y1) / 2, 0.06), (0.04, Y1 - Y0, 0.12))):
        reb.prim("cube", "Skirting", beam_m, at, size)
    # Window frames, sills, glass; the east one in the south wall cracked, its curtain stirring.
    curtain = None
    for i, (a0, a1) in enumerate((WIN_W, WIN_E)):
        mx = (a0 + a1) / 2
        reb.prim("cube", f"Window glass {i}", reb.mat_glass("Grimy glass", (0.5, 0.52, 0.46)), (mx, Y1 + 0.06, 1.4), (a1 - a0, 0.01, 0.8))
        reb.prim("cube", f"Window cross {i}", frame_m, (mx, Y1 + 0.05, 1.4), (0.04, 0.04, 0.8))
        reb.prim("cube", f"Window bar {i}", frame_m, (mx, Y1 + 0.05, 1.4), (a1 - a0, 0.04, 0.04))
        reb.prim("cube", f"Window sill {i}", frame_m, (mx, Y1 - 0.07, 0.98), (a1 - a0 + 0.2, 0.18, 0.04))
        rail = reb.prim("cube", f"Curtain rail {i}", mat("iron"), (mx, Y1 - 0.08, 1.92), (a1 - a0 + 0.4, 0.02, 0.02))
        cl = reb.cloth(f"Curtain {i}", reb.mat_plain("Curtain", (0.36, 0.28, 0.15), 0.9), (mx - 0.3 if i == 0 else mx + 0.32, Y1 - 0.1, 1.45), (0.32, 0.9), rot=(math.pi / 2, 0, 0), cuts=10, lumps=0.025, seed=i)
        if i == 1:
            curtain = cl
    for k in range(6):
        a = k * 1.05 + rng.uniform(-0.2, 0.2)
        kit.rod("Crack", reb.mat_plain("Crack", (0.75, 0.78, 0.8), 0.3), (4.6, Y1 + 0.05, 1.55), (4.6 + math.cos(a) * 0.25, Y1 + 0.05, 1.55 + math.sin(a) * 0.25), 0.003, 4)
    reb.prim("cube", "Side window glass", reb.mat_glass("Grimy glass", (0.5, 0.52, 0.46)), (X1 + 0.06, sum(WIN_SIDE) / 2, 1.4), (0.01, WIN_SIDE[1] - WIN_SIDE[0], 0.8))
    reb.prim("cube", "Side window cross", frame_m, (X1 + 0.05, sum(WIN_SIDE) / 2, 1.4), (0.04, 0.04, 0.8))
    reb.prim("cube", "Side window sill", frame_m, (X1 - 0.07, sum(WIN_SIDE) / 2, 0.98), (0.18, WIN_SIDE[1] - WIN_SIDE[0] + 0.2, 0.04))

    # ---- The door: shut, its bolt drawn, the bar lifted off and leaning by it.
    d0, d1 = DOOR
    for x in (d0 - 0.04, d1 + 0.04):
        reb.prim("cube", "Door frame", frame_m, (x, Y1 - 0.02, 1.02), (0.08, 0.1, 2.04))
    reb.prim("cube", "Door head", frame_m, ((d0 + d1) / 2, Y1 - 0.02, 2.04), (d1 - d0 + 0.16, 0.1, 0.08))
    # Shut behind her, but the bolt is drawn back and the bar is off.
    door = reb.prim("cube", "Door", kit.boards("Door boards", (0.16, 0.08, 0.05), width=0.13), ((d0 + d1) / 2, Y1 + 0.03, 1.0), (d1 - d0, 0.05, 2.0))
    for z in (0.35, 1.0, 1.65):
        reb.prim("cube", "Door ledge", frame_m, ((d0 + d1) / 2, Y1 - 0.0, z), (d1 - d0 - 0.06, 0.03, 0.12))
    reb.prim("cube", "Bolt plate", mat("iron"), (d0 + 0.22, Y1 - 0.025, 1.1), (0.2, 0.02, 0.06))
    reb.prim("cyl", "Bolt, drawn", mat("steel"), (d0 + 0.28, Y1 - 0.04, 1.1), (0.025, 0.025, 0.2), rot=(0, math.pi / 2, 0), segments=8)
    reb.prim("sphere", "Latch", mat("iron"), (d1 - 0.12, Y1 - 0.03, 1.0), (0.05, 0.05, 0.05))
    kit.splat("Hand on the door", mat("old blood"), (d1 - 0.15, Y1 - 0.005, 1.15), 0.06, rot=(math.pi / 2, 0, 0), seed=11, lumps=0.5)
    reb.prim("cube", "Bolt keeper", mat("iron"), (d0 - 0.02, Y1 - 0.07, 1.1), (0.05, 0.04, 0.08))
    for x in (d0 - 0.15, d1 + 0.15):
        reb.prim("cube", "Bar bracket", mat("iron"), (x, Y1 - 0.06, 1.25), (0.08, 0.1, 0.12))
    bar = reb.prim("cube", "Door bar", mat("logs"), (d1 + 0.42, Y1 - 0.14, 0.62), (0.09, 0.09, 1.3), rot=(0.12, -0.38, 0))
    reb.mask(bar)
    # The key board by the door: the quarry office key on its tag, empty hooks.
    reb.prim("cube", "Key board", frame_m, (d0 - 0.45, Y1 - 0.02, 1.5), (0.4, 0.03, 0.16))
    for k, x in enumerate((-0.15, -0.05, 0.05, 0.15)):
        reb.prim("cyl", "Key hook", mat("steel"), (d0 - 0.45 + x, Y1 - 0.05, 1.48), (0.012, 0.012, 0.05), rot=(math.pi / 2, 0, 0), segments=6)
    reb.prim("cube", "Quarry key", mat("steel"), (d0 - 0.4, Y1 - 0.06, 1.42), (0.015, 0.006, 0.07))
    reb.prim("cube", "Key tag", reb.mat_plain("Tag red", (0.4, 0.05, 0.03), 0.6), (d0 - 0.4, Y1 - 0.065, 1.34), (0.05, 0.004, 0.08))
    # His rods in the corner, the creel, waders on a peg.
    for k, (dx, lean) in enumerate(((0.0, 0.08), (0.08, 0.12), (0.16, 0.05))):
        kit.rod(f"Fishing rod {k}", reb.mat_wood("Rod cane", (0.4, 0.3, 0.15)), (X1 - 0.1 - dx, Y1 - 0.12, 0.0), (X1 - 0.1 - dx - lean, Y1 - 0.08 - lean * 0.5, 2.15), 0.008, 6)
        reb.prim("cyl", f"Reel {k}", mat("steel"), (X1 - 0.1 - dx - lean * 0.15, Y1 - 0.11, 0.35), (0.06, 0.06, 0.03), rot=(math.pi / 2, 0, 0), segments=10)
    reb.prim("cube", "Creel", reb.mat_surface("Wicker", [(0.0, (0.2, 0.14, 0.07)), (1.0, (0.36, 0.27, 0.14))], scale=60, bump=0.6), (X1 - 0.55, Y1 - 0.2, 0.15), (0.4, 0.25, 0.3), bevel=0.04)
    reb.prim("cube", "Wader peg", frame_m, (X1 - 0.02, Y1 - 0.6, 1.6), (0.04, 0.04, 0.04))
    reb.cloth("Waders", reb.mat_plain("Wader rubber", (0.04, 0.05, 0.035), 0.7), (X1 - 0.07, Y1 - 0.6, 1.05), (0.4, 1.1), rot=(math.pi / 2, 0, math.pi / 2), cuts=8, lumps=0.04, seed=8)

    # ---- The bed along the west wall: thrown back, the pillow bloody.
    bx0, bx1, by0, by1 = X0, X0 + 0.95, Y0, Y0 + 2.0
    bed = kit.box("Bed frame", frame_m, ((bx0 + bx1) / 2, (by0 + by1) / 2, 0.0), (bx1 - bx0, by1 - by0, 0.42))
    reb.wall(bed)
    reb.prim("cube", "Headboard", frame_m, ((bx0 + bx1) / 2, by0 + 0.03, 0.55), (bx1 - bx0, 0.06, 1.1))
    reb.prim("cube", "Footboard", frame_m, ((bx0 + bx1) / 2, by1 - 0.03, 0.38), (bx1 - bx0, 0.06, 0.76))
    reb.prim("cube", "Mattress", mat("mattress"), ((bx0 + bx1) / 2, (by0 + by1) / 2, 0.5), (bx1 - bx0 - 0.08, by1 - by0 - 0.14, 0.16), bevel=0.04)
    reb.cloth("Sheet", mat("sheet"), ((bx0 + bx1) / 2, (by0 + by1) / 2 - 0.1, 0.59), (0.9, 1.5), cuts=14, lumps=0.03, seed=3)
    reb.prim("cube", "Pillow", mat("sheet"), ((bx0 + bx1) / 2, by0 + 0.3, 0.64), (0.6, 0.35, 0.12), bevel=0.05)
    kit.splat("Blood on the pillow", mat("old blood"), ((bx0 + bx1) / 2 + 0.08, by0 + 0.32, 0.705), 0.11, seed=2, stretch=(1.2, 0.8))
    kit.splat("Blood on the sheet", mat("old blood"), ((bx0 + bx1) / 2 - 0.05, by0 + 0.9, 0.62), 0.16, seed=4, stretch=(0.8, 1.4))
    reb.cloth("Quilt, thrown back", quilt, ((bx0 + bx1) / 2 + 0.1, by1 - 0.35, 0.66), (1.0, 0.8), rot=(0, 0.1, 0.05), cuts=12, lumps=0.08, seed=5)
    reb.cloth("Quilt off the side", quilt, (bx1 + 0.12, by1 - 0.4, 0.3), (0.6, 0.6), rot=(0, math.pi / 2 - 0.2, 0), cuts=8, lumps=0.05, seed=6)
    # Over the bed, his pride: a trout on a board.
    reb.prim("cube", "Trophy board", frame_m, (X0 + 0.02, by0 + 1.1, 1.55), (0.03, 0.6, 0.28), bevel=0.01)
    reb.prim("sphere", "Trophy trout", reb.mat_surface("Trout", [(0.0, (0.15, 0.17, 0.12)), (0.6, (0.4, 0.38, 0.3)), (1.0, (0.45, 0.25, 0.2))], scale=12, rough=0.4, bump=0.1), (X0 + 0.07, by0 + 1.1, 1.55), (0.06, 0.48, 0.12))
    reb.prim("cone", "Trout tail", reb.mat_plain("Tail", (0.2, 0.2, 0.15), 0.5), (X0 + 0.07, by0 + 1.38, 1.55), (0.03, 0.12, 0.14), rot=(math.pi / 2, 0, 0), segments=4, top=0.0)
    # A stool by the bed: the bedside lamp, his watch, a glass of water.
    reb.prim("cyl", "Bedside stool", frame_m, (bx1 + 0.25, by0 + 0.3, 0.25), (0.35, 0.35, 0.5), segments=12)
    reb.prim("cyl", "Water glass", mat("glass"), (bx1 + 0.3, by0 + 0.25, 0.55), (0.06, 0.06, 0.1), segments=10)
    reb.prim("cyl", "Pill bottle", reb.mat_plain("Pill bottle", (0.4, 0.2, 0.04), 0.3), (bx1 + 0.18, by0 + 0.35, 0.54), (0.04, 0.04, 0.08), segments=8)

    # ---- North wall: the drawers, the radio on, the photos of his daughter.
    dx0, dx1 = 2.35, 3.35
    drawers = kit.box("Drawers", frame_m, ((dx0 + dx1) / 2, Y0 + 0.25, 0.0), (dx1 - dx0, 0.48, 0.9))
    reb.wall(drawers)
    for k in range(3):
        reb.prim("cube", "Drawer front", reb.mat_wood("Drawer", (0.18, 0.11, 0.06)), ((dx0 + dx1) / 2, Y0 + 0.5, 0.18 + k * 0.27), (dx1 - dx0 - 0.08, 0.02, 0.22))
        reb.prim("sphere", "Knob", mat("steel"), ((dx0 + dx1) / 2, Y0 + 0.52, 0.18 + k * 0.27), (0.04, 0.03, 0.04))
    reb.prim("cube", "Drawer pulled out", reb.mat_wood("Drawer", (0.18, 0.11, 0.06)), ((dx0 + dx1) / 2, Y0 + 0.62, 0.72), (dx1 - dx0 - 0.08, 0.3, 0.2))
    reb.cloth("Socks in the drawer", mat("flannel"), ((dx0 + dx1) / 2, Y0 + 0.66, 0.8), (0.6, 0.2), cuts=6, lumps=0.03, seed=9)
    radio = reb.prim("cube", "Radio", reb.mat_surface("Bakelite", [(0.0, (0.08, 0.04, 0.02)), (1.0, (0.18, 0.09, 0.04))], scale=6, rough=0.35, bump=0.05), (dx0 + 0.3, Y0 + 0.2, 1.06), (0.42, 0.22, 0.3), bevel=0.04)
    dial_m = reb.mat_emit("Radio dial", (1.0, 0.55, 0.2), 2.5)
    reb.prim("cube", "Radio dial", dial_m, (dx0 + 0.3, Y0 + 0.315, 1.12), (0.28, 0.01, 0.07))
    reb.prim("cube", "Radio speaker cloth", mat("canvas"), (dx0 + 0.3, Y0 + 0.315, 0.99), (0.3, 0.008, 0.1))
    for x in (-0.12, 0.12):
        reb.prim("cyl", "Radio knob", mat("black"), (dx0 + 0.3 + x, Y0 + 0.33, 0.99), (0.04, 0.04, 0.03), rot=(math.pi / 2, 0, 0), segments=10)
    kit.rod("Radio aerial", mat("steel"), (dx0 + 0.45, Y0 + 0.15, 1.2), (dx0 + 0.7, Y0 + 0.1, 1.7), 0.004, 4)
    dial_glow = reb.point("Radio glow", (dx0 + 0.3, Y0 + 0.45, 1.12), 0.6, (1.0, 0.6, 0.25), 0.05)
    reb.prim("cube", "Ashtray", mat("steel"), (dx1 - 0.2, Y0 + 0.25, 0.92), (0.12, 0.12, 0.02))
    # The photos: the big one, her and the fish, and two small ones.
    def photo(name, at, size, sky, figure=True, fish=False):
        x, z = at
        reb.prim("cube", f"{name} frame", frame_m, (x, Y0 + 0.012, z), (size[0] + 0.05, 0.02, size[1] + 0.05))
        reb.prim("cube", f"{name} sky", reb.mat_plain(f"{name} sky", sky, 0.6), (x, Y0 + 0.025, z), (size[0], 0.006, size[1]))
        reb.prim("cube", f"{name} ground", reb.mat_plain("Photo lake", (0.08, 0.14, 0.12), 0.6), (x, Y0 + 0.029, z - size[1] * 0.3), (size[0], 0.006, size[1] * 0.4))
        if figure:
            reb.prim("sphere", f"{name} face", reb.mat_plain("Photo face", (0.62, 0.45, 0.35), 0.6), (x - size[0] * 0.12, Y0 + 0.034, z + size[1] * 0.18), (size[0] * 0.14, 0.006, size[0] * 0.16))
            reb.prim("cube", f"{name} jacket", reb.mat_plain("Photo jacket", (0.55, 0.42, 0.06), 0.6), (x - size[0] * 0.12, Y0 + 0.034, z - size[1] * 0.12), (size[0] * 0.26, 0.006, size[1] * 0.42))
        if fish:
            reb.prim("sphere", f"{name} fish", reb.mat_plain("Photo fish", (0.7, 0.72, 0.72), 0.3), (x + size[0] * 0.18, Y0 + 0.036, z), (size[0] * 0.4, 0.006, size[1] * 0.12), rot=(0, 0.35, 0))
    photo("Photo of her with the fish", (2.85, 1.5), (0.42, 0.32), (0.4, 0.55, 0.65), fish=True)
    photo("Photo, school", (2.4, 1.72), (0.14, 0.18), (0.35, 0.3, 0.3))
    photo("Photo, the two of them", (3.3, 1.75), (0.2, 0.15), (0.5, 0.48, 0.4))
    reb.prim("cube", "Child's drawing", mat("paper"), (3.55, Y0 + 0.015, 1.35), (0.24, 0.006, 0.18), rot=(0, 0.06, 0))
    kit.rod("Drawing crayon", reb.mat_plain("Crayon blue", (0.05, 0.12, 0.4), 0.5), (3.47, Y0 + 0.02, 1.3), (3.62, Y0 + 0.02, 1.4), 0.006, 4)
    kit.text("Drawing words", "DAD", reb.mat_plain("Crayon red", (0.4, 0.04, 0.03), 0.5), (3.55, Y0 + 0.02, 1.4), size=0.05, rot=(math.pi / 2, 0, math.pi))

    # ---- The sink, north-east: enamel basin on a cupboard, the pump, the towels.
    sx0, sx1 = 3.9, 5.2
    counter = kit.box("Sink cupboard", reb.mat_wood("Cupboard", (0.13, 0.09, 0.05)), ((sx0 + sx1) / 2, Y0 + 0.3, 0.0), (sx1 - sx0, 0.58, 0.85))
    reb.wall(counter)
    reb.prim("cube", "Counter top", mat("dark wood"), ((sx0 + sx1) / 2, Y0 + 0.3, 0.87), (sx1 - sx0 + 0.04, 0.62, 0.04))
    reb.prim("cube", "Basin", enamel, (4.35, Y0 + 0.3, 0.95), (0.62, 0.46, 0.14), bevel=0.03)
    reb.prim("cube", "Basin water", pinkish, (4.35, Y0 + 0.3, 1.0), (0.54, 0.38, 0.01))
    kit.rod("Pump", mat("iron"), (4.35, Y0 + 0.08, 0.88), (4.35, Y0 + 0.08, 1.35), 0.04)
    kit.rod("Pump spout", mat("iron"), (4.35, Y0 + 0.08, 1.25), (4.35, Y0 + 0.25, 1.2), 0.02)
    kit.rod("Pump handle", mat("iron"), (4.35, Y0 + 0.08, 1.35), (4.6, Y0 + 0.2, 1.55), 0.015)
    for k in range(4):
        reb.cloth(f"Towel {k}", towel_m, (4.25 + rng.uniform(-0.15, 0.15), Y0 + 0.3 + rng.uniform(-0.1, 0.1), 1.03 + k * 0.02), (0.35, 0.28), rot=(0, 0, rng.uniform(0, 3)), cuts=8, lumps=0.04, seed=20 + k)
    reb.cloth("Towel over the edge", towel_m, (4.35, Y0 + 0.62, 0.85), (0.3, 0.32), rot=(math.pi / 2 - 0.2, 0, 0), cuts=8, lumps=0.03, seed=30)
    kit.splat("Pink on the counter", mat("blood"), (4.75, Y0 + 0.4, 0.893), 0.1, seed=31, stretch=(1.4, 0.8))
    kit.splat("Puddle under the sink", mat("blood"), (4.35, Y0 + 0.75, 0.0), 0.13, seed=32, lumps=0.5)
    reb.prim("cube", "Soap", reb.mat_plain("Soap", (0.5, 0.45, 0.32), 0.6), (4.85, Y0 + 0.2, 0.91), (0.08, 0.05, 0.03))
    reb.prim("cube", "Razor", mat("steel"), (4.95, Y0 + 0.35, 0.895), (0.12, 0.02, 0.008), rot=(0, 0, 0.5))
    shelf = shelves("Kitchen shelf", mat("dark wood"), (4.3, Y0 + 0.13, 1.6), size=(0.8, 0.24, 0.6), rows=3, clutter=0.75, seed=4)

    # ---- The stove in the south-east, cold; the woodbox; the kettle.
    stove = kit.box("Stove", mat("iron"), (X1 - 0.35, 3.35, 0.0), (0.55, 0.6, 0.75), bevel=0.02)
    reb.wall(stove)
    reb.prim("cube", "Stove top", mat("iron"), (X1 - 0.35, 3.35, 0.77), (0.6, 0.66, 0.04))
    kit.rod("Stove pipe", mat("iron"), (X1 - 0.35, 3.35, 0.79), (X1 - 0.35, 3.35, H), 0.07)
    reb.prim("cyl", "Kettle", mat("iron"), (X1 - 0.3, 3.25, 0.87), (0.2, 0.2, 0.16), segments=14)
    reb.prim("cube", "Stove door", mat("iron"), (X1 - 0.63, 3.35, 0.35), (0.02, 0.3, 0.25))
    reb.prim("cube", "Ash on the floor", reb.mat_plain("Ash", (0.15, 0.15, 0.14), 0.95), (X1 - 0.75, 3.35, 0.002), (0.25, 0.4, 0.004), rot=(0, 0, 0.3))
    wb = crate("Woodbox", mat("planks"), (X1 - 0.35, 2.85, 0.0), size=(0.5, 0.36, 0.38))
    reb.wall(wb)
    for k in range(4):
        reb.prim("cyl", "Kindling", mat("logs"), (X1 - 0.35 + rng.uniform(-0.12, 0.12), 2.85, 0.4 + k * 0.03), (0.08, 0.08, 0.45), rot=(0, math.pi / 2, rng.uniform(-0.2, 0.2)), segments=8)

    # ---- The table: the diary open, the first aid tin emptied out, his lamp burnt dry.
    tx, ty = 3.0, 2.55
    table = kit.table("Table", reb.mat_wood("Table", (0.22, 0.15, 0.08)), (tx, ty, 0.0), size=(1.1, 0.75, 0.76))
    reb.wall(table)
    top = 0.76
    reb.prim("cube", "Diary left page", mat("old paper"), (tx - 0.1, ty - 0.05, top + 0.012), (0.15, 0.2, 0.008), rot=(0, 0.06, 0.25))
    reb.prim("cube", "Diary right page", mat("paper"), (tx + 0.04, ty - 0.01, top + 0.012), (0.15, 0.2, 0.008), rot=(0, -0.06, 0.25))
    reb.prim("cube", "Diary cover", reb.mat_plain("Diary leather", (0.12, 0.04, 0.02), 0.6), (tx - 0.03, ty - 0.03, top + 0.004), (0.33, 0.23, 0.008), rot=(0, 0, 0.25))
    for k in range(5):
        kit.rod("Diary line", reb.mat_plain("Ink", (0.03, 0.03, 0.06), 0.5), (tx - 0.02, ty - 0.07 + k * 0.025 - 0.03, top + 0.0175), (tx + 0.09, ty - 0.04 + k * 0.025 - 0.03, top + 0.0175), 0.002, 3)
    kit.rod("Pencil", reb.mat_plain("Pencil", (0.5, 0.35, 0.05), 0.5), (tx + 0.15, ty + 0.08, top + 0.008), (tx + 0.3, ty + 0.0, top + 0.008), 0.005, 6)
    kit.splat("Thumbprint on the page", mat("old blood"), (tx + 0.07, ty + 0.04, top + 0.014), 0.012, seed=7)
    reb.prim("cube", "First aid tin", mat("white paint"), (tx + 0.33, ty + 0.15, top + 0.04), (0.3, 0.2, 0.08))
    reb.prim("cube", "First aid lid", mat("white paint"), (tx + 0.33, ty - 0.03, top + 0.13), (0.3, 0.01, 0.2), rot=(-0.4, 0, 0))
    kit.text("Tin cross", "+", mat("red paint"), (tx + 0.33, ty - 0.045, top + 0.13), size=0.12, rot=(math.pi / 2 - 0.4, 0, 0))
    for k in range(3):
        reb.prim("cyl", f"Bandage roll {k}", mat("white paint"), (tx - 0.35 + k * 0.09, ty + 0.25, top + 0.03), (0.06, 0.06, 0.06), rot=(math.pi / 2, 0, rng.uniform(0, 3)), segments=10)
    for k in range(6):
        reb.prim("cube", f"Wrapper {k}", mat("paper"), (tx + rng.uniform(-0.45, 0.45), ty + rng.uniform(-0.3, 0.3), top + 0.002), (0.07, 0.05, 0.002), rot=(0, 0, rng.uniform(0, 3)))
    reb.prim("cyl", "Iodine bottle", reb.mat_glass("Brown glass", (0.3, 0.12, 0.03)), (tx + 0.45, ty - 0.25, top + 0.035), (0.04, 0.04, 0.11), rot=(math.pi / 2, 0, 1.3), segments=10)
    kit.splat("Iodine", reb.mat_plain("Iodine", (0.25, 0.08, 0.02), 0.2), (tx + 0.5, ty - 0.3, top + 0.001), 0.06, seed=8)
    reb.prim("cube", "Scissors", mat("steel"), (tx - 0.3, ty - 0.2, top + 0.005), (0.14, 0.03, 0.006), rot=(0, 0, 0.9))
    kit.splat("Blood on the table", mat("old blood"), (tx - 0.25, ty + 0.05, top + 0.001), 0.1, seed=9)
    lamp, lamp_light, lamp_flame = kit.lantern("Oil lamp", (tx - 0.4, ty - 0.2, top), energy=0.0)
    reb.emit_strength(lamp_flame, 0.0)
    chair("Chair at the table", reb.mat_wood("Chair", (0.2, 0.13, 0.07)), (tx - 0.35, ty - 0.65, 0.0), rot=math.pi / 2 + 0.3)
    # The other chair, dragged to the west window: the scrapes from the table.
    chair2 = chair("Chair at the window", reb.mat_wood("Chair", (0.2, 0.13, 0.07)), (1.9, 3.85, 0.0), rot=math.pi / 2 - 0.15)
    reb.wall(chair2)
    for dx in (-0.16, 0.16):
        kit.drag_trail(f"Chair scrape {dx}", reb.mat_plain("Scrape", (0.27, 0.2, 0.13), 0.9), [(2.55 + dx, 2.95), (2.25 + dx, 3.4), (1.95 + dx, 3.7)], width=0.04, seed=40 + int(dx * 100))
    reb.prim("cube", "Binoculars", mat("black"), (1.85, Y1 - 0.08, 1.03), (0.16, 0.1, 0.06), rot=(0, 0, 0.3))
    reb.prim("cyl", "Cold coffee", reb.mat_plain("Mug enamel", (0.5, 0.52, 0.55), 0.35), (2.15, Y1 - 0.09, 1.05), (0.08, 0.08, 0.09), segments=12)
    kit.bottles("Bottles under the window", (1.45, 3.9, 0.0), count=3, spread=0.3, seed=2, tipped=0.7)
    # A rag rug, and his blood: from the door to the sink, to the table, to the bed.
    reb.cloth("Rag rug", reb.mat_stripes("Rag rug", [(0.12, 0.06, 0.04), (0.07, 0.07, 0.08), (0.15, 0.12, 0.08)], across=10.0, axis="Y"), (3.05, 3.65, 0.006), (1.0, 0.6), cuts=6, lumps=0.003, seed=1)
    pts = []
    for (a, b, n) in (((3.05, 4.25), (4.3, 1.75), 9), ((4.3, 1.75), (3.35, 2.2), 4), ((2.6, 2.2), (1.95, 1.9), 3)):
        for k in range(n):
            t = (k + rng.uniform(0, 0.6)) / n
            pts.append((a[0] + (b[0] - a[0]) * t + rng.uniform(-0.07, 0.07), a[1] + (b[1] - a[1]) * t + rng.uniform(-0.07, 0.07)))
    drips("Drips", mat("blood"), pts, rng)
    for k in range(5):
        kit.splat(f"Boot print {k}", mat("mud"), (3.15 + (0.1 if k % 2 else -0.1), 4.2 - k * 0.3, 0.0), 0.05, seed=50 + k, stretch=(0.6, 1.4), lumps=0.2)
    kit.web("Web over the bed", (X0 + 0.02, Y0 + 0.02, H - 0.02), 0.28, (1, 1))
    kit.web("Web by the stove", (X1 - 0.02, Y1 - 0.02, H - 0.02), 0.22, (-1, -1))

    # ---- Outside: the grass and the path, the fence, the valley; the afternoon sun.
    reb.prim("cube", "Outside ground", mat("grass"), (3.2, Y1 + 6.0, -0.06), (24.0, 12.0, 0.1))
    reb.prim("cube", "Outside path", mat("dirt"), (3.2, Y1 + 2.8, -0.005), (24.0, 0.8, 0.02), rot=(0, 0, 0.05))
    reb.prim("cube", "Outside step", mat("concrete"), ((d0 + d1) / 2, Y1 + 0.38, -0.02), (1.3, 0.5, 0.14))
    reb.prim("cube", "Outside east ground", mat("grass"), (X1 + 6.0, 2.5, -0.06), (12.0, 10.0, 0.1))
    for k in range(9):
        kit.rod("Outside fence post", mat("planks"), (-4.0 + k * 2.0, Y1 + 8.0, -0.1), (-4.0 + k * 2.0, Y1 + 8.0, 1.1), 0.06)
    kit.rod("Outside fence rail", mat("planks"), (-5.0, Y1 + 8.0, 0.95), (13.0, Y1 + 8.0, 0.95), 0.04)
    kit.rod("Outside fence rail", mat("planks"), (-5.0, Y1 + 8.0, 0.5), (13.0, Y1 + 8.0, 0.5), 0.04)
    reb.prim("cube", "Outside, the far side", mat("rock"), (3.2, Y1 + 160, 5.0), (400, 2, 80))
    sun = kit.time_light("afternoon", sun_heading=235, sun_energy=4.0)
    sun.rotation_euler[0] = math.radians(90 - 24)
    reb.spot("Sun through the west window", (0.4, Y1 + 3.0, 3.4), (2.6, 2.6, 0.0), 1600, (1.0, 0.8, 0.55), 30, 0.5, 0.15)
    reb.spot("Sun through the cracked window", (3.6, Y1 + 3.0, 3.6), (5.0, 2.8, 0.0), 1300, (1.0, 0.78, 0.52), 28, 0.5, 0.15)
    reb.point("Dim room fill", (3.2, 2.4, 1.9), 40, (0.75, 0.62, 0.5), 1.0)
    reb.point("Bounce off the floor shaft", (2.3, 2.8, 0.4), 8, (1.0, 0.75, 0.5), 0.6)

    # Window glass lets the sun through (a thin pane would only pass caustics).
    for ob in bpy.data.objects:
        if "glass" in ob.name.lower() and ob.type == "MESH":
            ob.visible_shadow = False

    anim = kit.Anim(16)
    anim.flicker(dial_glow, dial_m, depth=0.45, dropouts=2)
    anim.sway(curtain, amount=0.035, along=(0.3, -1.0), every=2, tip=0)
    anim.drip((4.35, Y0 + 0.66, 0.84), fall=0.84, size=0.014, m=mat("blood"))

    # ---- What the game needs.
    room.door("east-path", (d0, Y1 - 0.5, d1, Y1), arrive=(3.05, 3.5), face=(0, -1))
    room.check((2.4, 2.1, 3.3, 2.95), "His diary, open. The last entry is shaky:\n\"it itches. hide in the mine till they come.\"")
    room.check((3.3, 2.1, 3.6, 2.95), "The first aid tin, emptied. Bandage wrappers everywhere.\nHe did what he could with it.")
    room.check((d0 - 0.75, Y1 - 0.5, d0, Y1), "A key on a hook by the door. The tag says QUARRY OFFICE.")
    room.check((3.85, Y0, 4.9, Y0 + 1.0), "The sink is full of towels. They're soaked through.\nThe water's pink.")
    room.check((2.35, Y0, 3.35, Y0 + 0.9), "A girl holding up a fish, grinning. The same photo was in the booth.\nA drawing under it, in crayon: DAD.")
    room.check((2.0, Y0, 2.35, Y0 + 0.9), "The radio's on, hissing. Nothing on any channel.")
    room.check((1.4, 3.4, 2.4, Y1), "He dragged the chair to the window and sat watching the path.\nBinoculars. Cold coffee.")
    room.check((X0, Y0, X0 + 1.2, Y0 + 2.1), "The bed's been slept in, or tried. Blood on the pillow.")
    room.check((d1, Y1 - 0.6, X1, Y1), "Fishing rods, a creel, waders. A man who liked quiet.")
    room.check((d0 - 0.2, Y1 - 0.4, d0 + 0.3, Y1), "The bolt's drawn and the bar's off the door.\nHe locked himself in, then thought better of it.")
    room.entry = "The radio's still on."
    room.export(anim)


build()
