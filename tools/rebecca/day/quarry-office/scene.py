"""The quarry office hut, late afternoon.

What it tells: the foreman ran the quarry from this tin hut. The shift
rosters on the board show the week going wrong: names crossed out in red
one after another, SICK written beside them, until the last shift has
almost nobody on it. Somebody tried to keep working: the coffee was on the
hot plate and is still on it, burnt to a black crust, the plate glowing.
The time clock by the door still ticks, its second hand stuck, twitching on
the same mark. The explosives locker in the corner is stencilled and
padlocked, the blasting caps kept apart on the shelf the way the rules say.
The safety board says DAYS WITHOUT AN ACCIDENT, and someone has wiped the
number and written 0. The foreman left his hat and his half-written report.

Metres: the floor is x 1.0-4.4, y 1.0-3.8, 2.4 high. The door is in the
north wall at x 2.3-3.2, out onto the quarry floor; the window beside it
at x 3.6-4.3. The time clock is on the north wall west of the door, the
caps shelf and the explosives locker along the west wall, the desk along
the east wall with the roster board over it, the coffee in the south-east
corner, the safety board on the south wall.

Moving: the clock's second hand twitching; the hot plate's glow; the bulb
swaying a little on its flex in the draught from the door.
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

X0, X1, Y0, Y1, H = 1.0, 4.4, 1.0, 3.8, 2.4
DOOR = (2.3, 3.2)
WINDOW = (3.6, 4.3, 1.15, 1.8)


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


def build():
    rng = random.Random(7)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.camera((4.25, 3.65, 2.2), (1.85, 2.05, 0.5), 190, "high in the south-east corner: the door and the ticking clock, the caps, the explosives locker")
    room.camera((1.15, 1.15, 2.2), (3.9, 2.95, 0.4), 200, "high over the clock: the desk and the rosters, the burnt coffee, the safety board")

    corr = reb.mat_stripes("Corrugated inside", [(0.16, 0.15, 0.14), (0.09, 0.085, 0.08)], across=30.0, axis="X")
    corr_y = reb.mat_stripes("Corrugated inside y", [(0.16, 0.15, 0.14), (0.09, 0.085, 0.08)], across=30.0, axis="Y")
    ply = kit.boards("Ply lining", (0.3, 0.22, 0.13), width=1.2, seam=0.01, grime=0.8)
    floor_m = kit.dirtied(mat("concrete"), 0.85, scale=2.0)
    locker_m = reb.mat_surface("Locker grey", [(0.0, (0.14, 0.15, 0.14)), (0.8, (0.24, 0.25, 0.23)), (1.0, (0.2, 0.1, 0.05))], scale=6, rough=0.45, bump=0.15)
    cork = reb.mat_surface("Cork", [(0.0, (0.2, 0.12, 0.06)), (1.0, (0.36, 0.24, 0.12))], scale=40, bump=0.4)
    marker = reb.mat_plain("Red marker", (0.45, 0.03, 0.02), 0.5)
    ink = reb.mat_plain("Ink", (0.03, 0.03, 0.05), 0.5)

    # ---- The shell: tin outside, ply lining to waist height, a concrete floor, the roof on joists.
    kit.walls(X0, Y0, X1, Y1, H, corr, openings=[
        ("n", DOOR[0], DOOR[1], 0.0, 2.0),
        ("n", WINDOW[0], WINDOW[1], WINDOW[2], WINDOW[3]),
    ], floor=floor_m, ceiling=reb.mat_plain("Roof tin", (0.12, 0.08, 0.05), 0.7))
    for x0_, x1_, y_ in ((X0, DOOR[0], Y0 + 0.01), (DOOR[1], X1, Y0 + 0.01)):
        reb.prim("cube", "Lining", ply, ((x0_ + x1_) / 2, y_, 0.55 if x0_ > 3 else 0.6), (x1_ - x0_, 0.02, 1.1 if x0_ > 3 else 1.2))
    reb.prim("cube", "Lining", ply, ((X0 + X1) / 2, Y1 - 0.01, 0.6), (X1 - X0, 0.02, 1.2))
    reb.prim("cube", "Lining", ply, (X0 + 0.01, (Y0 + Y1) / 2, 0.6), (0.02, Y1 - Y0, 1.2))
    reb.prim("cube", "Lining", ply, (X1 - 0.01, (Y0 + Y1) / 2, 0.6), (0.02, Y1 - Y0, 1.2))
    for x in (1.7, 2.7, 3.7):
        reb.prim("cube", "Joist", mat("dark wood"), (x, (Y0 + Y1) / 2, H - 0.06), (0.08, Y1 - Y0 + 0.2, 0.12))
    for x in (DOOR[0] - 0.04, DOOR[1] + 0.04):
        reb.prim("cube", "Door frame", mat("dark wood"), (x, Y0 + 0.02, 1.03), (0.07, 0.1, 2.06))
    reb.prim("cube", "Door head", mat("dark wood"), (sum(DOOR) / 2, Y0 + 0.02, 2.04), (DOOR[1] - DOOR[0] + 0.15, 0.1, 0.08))
    reb.prim("cube", "Door", mat("green paint"), (sum(DOOR) / 2, Y0 - 0.06, 1.0), (DOOR[1] - DOOR[0], 0.04, 2.0))
    reb.prim("cube", "Door bar", mat("iron"), (sum(DOOR) / 2, Y0 - 0.03, 1.05), (0.5, 0.03, 0.04))
    reb.prim("cube", "Window glass", reb.mat_glass("Grimy glass", (0.45, 0.46, 0.42)), (sum(WINDOW[:2]) / 2, Y0 - 0.06, sum(WINDOW[2:]) / 2), (WINDOW[1] - WINDOW[0], 0.01, WINDOW[3] - WINDOW[2]))
    reb.prim("cube", "Window sill", mat("dark wood"), (sum(WINDOW[:2]) / 2, Y0 + 0.07, WINDOW[2] - 0.02), (WINDOW[1] - WINDOW[0] + 0.12, 0.16, 0.04))
    for k in range(4):
        reb.prim("cube", f"Dead fly {k}", mat("black"), (3.7 + k * 0.15, Y0 + 0.1, WINDOW[2] + 0.005), (0.012, 0.008, 0.006), rot=(0, 0, k))

    # ---- North wall, west of the door: the time clock, the card racks.
    clock = kit.box("Time clock", locker_m, (1.65, Y0 + 0.1, 1.2), (0.36, 0.18, 0.5), bevel=0.02)
    reb.prim("cyl", "Clock face", reb.mat_plain("Clock face", (0.62, 0.6, 0.52), 0.4), (1.65, Y0 + 0.195, 1.55), (0.26, 0.26, 0.01), rot=(math.pi / 2, 0, 0), segments=24)
    reb.prim("cyl", "Clock bezel", mat("steel"), (1.65, Y0 + 0.19, 1.55), (0.29, 0.29, 0.012), rot=(math.pi / 2, 0, 0), segments=24)
    for k in range(12):
        a = 2 * math.pi * k / 12
        r0, r1 = (0.095, 0.12) if k % 3 else (0.08, 0.12)
        kit.rod("Clock mark", ink, (1.65 + math.sin(a) * r0, Y0 + 0.203, 1.55 + math.cos(a) * r0), (1.65 + math.sin(a) * r1, Y0 + 0.203, 1.55 + math.cos(a) * r1), 0.005, 4)
    kit.rod("Hour hand", ink, (1.65, Y0 + 0.206, 1.55), (1.65 + math.sin(4.6) * 0.06, Y0 + 0.206, 1.55 + math.cos(4.6) * 0.06), 0.008, 4)
    kit.rod("Minute hand", ink, (1.65, Y0 + 0.207, 1.55), (1.65 + math.sin(2.3) * 0.1, Y0 + 0.207, 1.55 + math.cos(2.3) * 0.1), 0.006, 4)
    hand_pivot = reb.prim("sphere", "Second hand pivot", marker, (1.65, Y0 + 0.21, 1.55), (0.015, 0.015, 0.015))
    sec = kit.rod("Second hand", marker, (0, 0, -0.02), (0, 0, 0.115), 0.003, 4)
    sec.parent = hand_pivot
    hand_pivot.rotation_euler = (0, math.radians(222), 0)
    reb.prim("cube", "Card slot", mat("black"), (1.65, Y0 + 0.195, 1.12), (0.12, 0.01, 0.03))
    for side, x in (("in", 1.2), ("out", 2.07)):
        reb.prim("cube", f"Card rack {side}", mat("steel"), (x, Y0 + 0.04, 1.25), (0.22, 0.06, 0.7))
        for k in range(6):
            if side == "out" and k > 1:
                continue
            reb.prim("cube", "Time card", mat("old paper"), (x + rng.uniform(-0.03, 0.03), Y0 + 0.06, 0.98 + k * 0.11), (0.08, 0.004, 0.17))
    kit.text("Rack words", "IN       OUT", mat("white paint"), (1.64, Y0 + 0.07, 1.64), size=0.05, rot=(math.pi / 2, 0, math.pi))

    # ---- West wall: the caps shelf over a bench, and the explosives locker.
    reb.prim("cube", "Bench", mat("planks"), (X0 + 0.25, 1.95, 0.75), (0.5, 0.9, 0.05))
    for y in (1.55, 2.35):
        reb.prim("cube", "Bench leg", mat("planks"), (X0 + 0.25, y, 0.37), (0.45, 0.05, 0.75))
    reb.wall(reb.prim("cube", "Bench footprint", None, (X0 + 0.25, 1.95, 0.4), (0.5, 0.9, 0.8))).hide_render = True
    reb.prim("cube", "Caps shelf", mat("planks"), (X0 + 0.15, 1.95, 1.45), (0.3, 0.9, 0.03))
    caps = crate("Caps box", mat("pine"), (X0 + 0.16, 1.75, 1.465), size=(0.22, 0.3, 0.14))
    kit.text("Caps words", "CAPS", mat("red paint"), (X0 + 0.275, 1.75, 1.54), size=0.06, rot=(math.pi / 2, 0, math.pi / 2))
    for k, c in enumerate(((0.45, 0.35, 0.03), (0.08, 0.2, 0.4), (0.4, 0.05, 0.03))):
        reb.prim("cyl", f"Leg wire coil {k}", reb.mat_plain(f"Wire {k}", c, 0.5), (X0 + 0.15, 2.05 + k * 0.12, 1.48), (0.1, 0.1, 0.03), segments=12)
    reb.prim("cyl", "Det cord reel", mat("yellow paint"), (X0 + 0.25, 2.1, 0.86), (0.22, 0.22, 0.16), rot=(0, math.pi / 2, 0), segments=16)
    reb.prim("cube", "Blasting log", reb.mat_plain("Log book", (0.1, 0.12, 0.2), 0.6), (X0 + 0.28, 1.7, 0.785), (0.2, 0.28, 0.02), rot=(0, 0, 0.1))
    lx, ly0, ly1 = X0 + 0.28, 2.6, 3.4
    locker = kit.box("Explosives locker", locker_m, (lx, (ly0 + ly1) / 2, 0.0), (0.55, ly1 - ly0, 1.85), bevel=0.01)
    reb.wall(locker)
    reb.mask(locker)
    reb.prim("cube", "Locker door seam", mat("black"), (lx + 0.278, (ly0 + ly1) / 2, 0.95), (0.004, 0.01, 1.7))
    for y in ((ly0 + ly1) / 2 - 0.06, (ly0 + ly1) / 2 + 0.06):
        reb.prim("cube", "Locker handle", mat("steel"), (lx + 0.29, y, 1.0), (0.03, 0.02, 0.14))
    reb.prim("cube", "Locker hasp", mat("steel"), (lx + 0.3, (ly0 + ly1) / 2, 1.18), (0.02, 0.18, 0.04))
    reb.prim("cube", "Locker padlock", mat("steel"), (lx + 0.315, (ly0 + ly1) / 2, 1.1), (0.03, 0.07, 0.08), bevel=0.01)
    for k in range(5):
        reb.prim("cube", "Locker vent", mat("black"), (lx + 0.279, (ly0 + ly1) / 2 - 0.2 + k * 0.1, 1.7), (0.004, 0.05, 0.015))
    kit.text("Stencil", "EXPLOSIVES", mat("red paint"), (lx + 0.281, (ly0 + ly1) / 2, 1.42), size=0.105, rot=(math.pi / 2, 0, math.pi / 2))
    kit.text("Stencil 2", "KEEP LOCKED", mat("red paint"), (lx + 0.281, (ly0 + ly1) / 2, 0.55), size=0.06, rot=(math.pi / 2, 0, math.pi / 2))
    reb.prim("cube", "Hazard diamond", reb.mat_plain("Hazard orange", (0.6, 0.2, 0.02), 0.6), (lx + 0.281, (ly0 + ly1) / 2, 0.82), (0.004, 0.18, 0.18), rot=(math.pi / 4, 0, 0))
    kit.text("Hazard words", "1.1D", mat("black"), (lx + 0.284, (ly0 + ly1) / 2, 0.82), size=0.05, rot=(math.pi / 2, 0, math.pi / 2))
    reb.prim("cube", "No smoking", mat("white paint"), (X0 + 0.015, 2.95, 2.05), (0.01, 0.4, 0.22))
    kit.text("No smoking words", "NO SMOKING", mat("red paint"), (X0 + 0.022, 2.95, 2.05), size=0.055, rot=(math.pi / 2, 0, math.pi / 2))
    # Hard hats on pegs in the south-west, a coat.
    for k, y in enumerate((3.55, 3.3)):
        reb.prim("cube", "Peg", mat("dark wood"), (X0 + 0.05, y, 1.65), (0.1, 0.03, 0.03))
        reb.prim("sphere", f"Hung hat {k}", mat("yellow paint") if k else mat("white paint"), (X0 + 0.15, y, 1.68), (0.26, 0.24, 0.18))
    reb.cloth("Coat on a peg", reb.mat_plain("Work coat", (0.12, 0.1, 0.07), 0.9), (2.0, Y1 - 0.06, 1.25), (0.5, 0.95), rot=(math.pi / 2, 0, 0), cuts=8, lumps=0.05, seed=3)
    reb.prim("cube", "Coat peg", mat("dark wood"), (2.0, Y1 - 0.04, 1.75), (0.04, 0.08, 0.04))

    # ---- East wall: the desk, the report, the phone; the roster board over it.
    dx = X1 - 0.35
    desk = kit.table("Desk", mat("dark wood"), (dx, 2.45, 0.0), size=(0.7, 1.4, 0.76), legs_mat=mat("iron"))
    reb.wall(desk)
    reb.prim("cube", "Desk drawers", mat("dark wood"), (dx, 2.95, 0.38), (0.6, 0.4, 0.7))
    top = 0.76
    reb.prim("cube", "Blotter", reb.mat_plain("Blotter", (0.1, 0.18, 0.1), 0.9), (dx, 2.4, top + 0.003), (0.5, 0.6, 0.006))
    reb.prim("cube", "Report", mat("paper"), (dx - 0.05, 2.35, top + 0.008), (0.21, 0.29, 0.002), rot=(0, 0, 0.15))
    for k in range(6):
        kit.rod("Report line", ink, (dx - 0.12, 2.25 + k * 0.03, top + 0.0095), (dx + 0.02 - (0.08 if k == 5 else 0), 2.27 + k * 0.03, top + 0.0095), 0.0015, 3)
    kit.rod("Pen", ink, (dx + 0.1, 2.5, top + 0.008), (dx + 0.02, 2.62, top + 0.008), 0.005, 6)
    reb.prim("cube", "Phone", mat("black"), (dx + 0.1, 2.0, top + 0.05), (0.2, 0.22, 0.1), bevel=0.02)
    reb.prim("cube", "Handset", mat("black"), (dx + 0.1, 2.0, top + 0.12), (0.06, 0.22, 0.05), bevel=0.015)
    reb.prim("cube", "Ashtray", mat("steel"), (dx - 0.15, 2.85, top + 0.01), (0.12, 0.12, 0.02))
    for k in range(5):
        reb.prim("cyl", "Stub", mat("white paint"), (dx - 0.15 + rng.uniform(-0.04, 0.04), 2.85 + rng.uniform(-0.04, 0.04), top + 0.025), (0.012, 0.012, 0.04), rot=(math.pi / 2, 0, rng.uniform(0, 3)), segments=6)
    reb.prim("cube", "Ledger", reb.mat_plain("Ledger", (0.25, 0.06, 0.04), 0.6), (dx + 0.05, 3.1, top + 0.03), (0.3, 0.4, 0.06), rot=(0, 0, 0.05))
    lamp_glow = reb.mat_emit("Desk lamp bulb", (1.0, 0.8, 0.5), 15)
    reb.prim("cyl", "Desk lamp base", mat("green paint"), (dx + 0.15, 1.85, top + 0.015), (0.14, 0.14, 0.03), segments=12)
    kit.rod("Desk lamp arm", mat("green paint"), (dx + 0.15, 1.85, top + 0.02), (dx + 0.05, 1.95, top + 0.38), 0.01)
    reb.prim("cone", "Desk lamp shade", mat("green paint"), (dx + 0.0, 2.0, top + 0.38), (0.18, 0.18, 0.12), rot=(0.5, -0.4, 0), segments=12, top=0.4)
    reb.prim("sphere", "Desk lamp bulb", lamp_glow, (dx - 0.01, 2.02, top + 0.35), (0.05, 0.05, 0.05))
    desk_light = reb.spot("Desk lamp", (dx - 0.01, 2.02, top + 0.34), (dx - 0.1, 2.4, top), 9, (1.0, 0.75, 0.45), 90, 0.6, 0.05)
    chair("Desk chair", mat("dark wood"), (dx - 0.62, 2.55, 0.0), rot=0.35)
    reb.prim("cyl", "Bin", mat("tin"), (dx - 0.1, 1.45, 0.2), (0.3, 0.3, 0.4), segments=14)
    kit.papers("Screwed-up paper", (dx - 0.4, 1.55, 0.0), spread=0.3, count=4, seed=3)
    # The roster board: four weeks of shifts, names going red.
    reb.prim("cube", "Roster board", cork, (X1 - 0.015, 2.45, 1.5), (0.02, 1.3, 0.75))
    reb.prim("cube", "Roster board frame", mat("dark wood"), (X1 - 0.008, 2.45, 1.5), (0.012, 1.36, 0.81))
    for k in range(4):
        cy = 1.98 + k * 0.31
        reb.prim("cube", f"Roster {k}", mat("paper") if k < 3 else mat("old paper"), (X1 - 0.03, cy, 1.5), (0.004, 0.24, 0.32), rot=(rng.uniform(-0.03, 0.03), 0, 0))
        kit.text(f"Roster title {k}", ("SHIFT A", "SHIFT B", "SHIFT C", "NIGHTS")[k], ink, (X1 - 0.034, cy, 1.62), size=0.03, rot=(math.pi / 2, 0, -math.pi / 2))
        for row in range(7):
            z = 1.56 - row * 0.035
            kit.rod("Roster name", ink, (X1 - 0.034, cy - 0.09, z), (X1 - 0.034, cy + 0.05, z), 0.0015, 3)
            if row < 2 + k:
                kit.rod("Crossed out", marker, (X1 - 0.036, cy - 0.1, z), (X1 - 0.036, cy + 0.07, z + 0.006), 0.003, 3)
    kit.text("Sick", "SICK", marker, (X1 - 0.036, 2.92, 1.29), size=0.05, rot=(math.pi / 2, 0.1, -math.pi / 2))
    reb.prim("cube", "Calendar", mat("paper"), (X1 - 0.015, 1.5, 1.6), (0.01, 0.3, 0.4))
    kit.text("Calendar words", "JULY 1998", ink, (X1 - 0.022, 1.5, 1.73), size=0.04, rot=(math.pi / 2, 0, -math.pi / 2))

    # ---- South-east: the coffee left on, burnt dry; the south wall's safety board and poster.
    side = kit.table("Coffee table", mat("planks"), (X1 - 0.3, Y1 - 0.3, 0.0), size=(0.5, 0.5, 0.85))
    reb.wall(side)
    plate_glow = reb.mat_emit("Hot plate coil", (1.0, 0.3, 0.05), 8)
    reb.prim("cube", "Hot plate", mat("iron"), (X1 - 0.3, Y1 - 0.3, 0.89), (0.25, 0.25, 0.06))
    reb.prim("cyl", "Hot plate coil", plate_glow, (X1 - 0.3, Y1 - 0.3, 0.925), (0.16, 0.16, 0.008), segments=16)
    reb.prim("cyl", "Coffee pot", reb.mat_glass("Pot glass", (0.4, 0.38, 0.33)), (X1 - 0.3, Y1 - 0.3, 1.03), (0.15, 0.15, 0.2), segments=14)
    reb.prim("cyl", "Burnt crust", reb.mat_plain("Burnt crust", (0.02, 0.012, 0.008), 0.9), (X1 - 0.3, Y1 - 0.3, 0.94), (0.14, 0.14, 0.02), segments=14)
    kit.splat("Scorch up the wall", mat("black"), (X1 - 0.3, Y1 - 0.012, 1.25), 0.18, rot=(math.pi / 2, 0, 0), seed=5, stretch=(0.8, 1.6))
    kit.rod("Plate flex", mat("black"), (X1 - 0.2, Y1 - 0.2, 0.87), (X1 - 0.05, Y1 - 0.05, 0.3), 0.006, 4)
    for k in range(3):
        reb.prim("cyl", f"Mug {k}", reb.mat_plain("Mug", (0.45, 0.42, 0.38), 0.4), (X1 - 0.45 + k * 0.09, Y1 - 0.15, 0.9), (0.07, 0.07, 0.09), segments=10)
    plate_light = reb.point("Hot plate glow", (X1 - 0.3, Y1 - 0.3, 1.0), 2.5, (1.0, 0.35, 0.08), 0.08)
    # DAYS WITHOUT AN ACCIDENT: wiped, and 0.
    reb.prim("cube", "Safety board", mat("white paint"), (2.6, Y1 - 0.015, 1.55), (0.9, 0.02, 0.55))
    kit.text("Safety words", "DAYS WITHOUT\nAN ACCIDENT", mat("black"), (2.6, Y1 - 0.028, 1.68), size=0.07)
    reb.prim("cube", "Number plate", reb.mat_plain("Wiped", (0.42, 0.42, 0.4), 0.7), (2.6, Y1 - 0.027, 1.42), (0.4, 0.01, 0.2))
    kit.text("Zero", "0", marker, (2.6, Y1 - 0.034, 1.42), size=0.18)
    # A poster: the hard hat, THINK SAFETY.
    reb.prim("cube", "Poster", reb.mat_plain("Poster yellow", (0.5, 0.38, 0.05), 0.7), (1.65, Y1 - 0.013, 1.55), (0.45, 0.01, 0.6))
    reb.prim("sphere", "Poster hat", mat("white paint"), (1.65, Y1 - 0.02, 1.55), (0.2, 0.01, 0.13))
    kit.text("Poster words", "THINK\nSAFETY", mat("black"), (1.65, Y1 - 0.022, 1.33), size=0.07)
    # The floor: boot prints in from the door, the foreman's hat dropped, grit.
    for k in range(8):
        kit.splat(f"Boot print {k}", mat("mud"), (2.75 + (0.1 if k % 2 else -0.1) + k * 0.12, 1.3 + k * 0.2, 0.0), 0.05, seed=20 + k, stretch=(1.4, 0.6), lumps=0.2)
    reb.prim("sphere", "Dropped hard hat", mat("white paint"), (3.0, 3.3, 0.1), (0.28, 0.25, 0.2), rot=(0.4, 0.3, 0))
    kit.papers("Papers off the desk", (3.3, 2.0, 0.0), spread=0.5, count=5, seed=8)
    kit.web("Web in the corner", (X0 + 0.02, Y1 - 0.02, H - 0.02), 0.25, (1, -1))

    # ---- Outside the door and the window: the quarry floor in the sun, the face beyond.
    reb.prim("cube", "Outside floor", kit.dirtied(mat("concrete"), 0.6), (2.6, Y0 - 6.0, -0.06), (20.0, 12.0, 0.1))
    reb.prim("cube", "Outside face", mat("rock"), (2.6, Y0 - 12.0, 4.0), (40.0, 1.0, 8.0))
    reb.prim("cube", "Outside block", mat("rock"), (1.0, Y0 - 4.5, 0.55), (1.6, 1.1, 1.1), rot=(0, 0, 0.2))
    reb.prim("cube", "Outside block", mat("rock"), (4.6, Y0 - 5.5, 0.6), (1.8, 1.2, 1.2), rot=(0, 0, -0.1))
    reb.prim("cube", "Outside derrick", mat("rust"), (-1.0, Y0 - 9.0, 5.0), (0.3, 0.3, 10.0))

    # ---- Light: a bare bulb, the desk lamp, the hot plate; daylight at the window.
    sun = kit.time_light("afternoon", sun_heading=215, sun_energy=3.4)
    cord, glass, bulb_light, bulb_glow = kit.bulb("Bulb", (2.6, 2.3, H - 0.02), energy=110, rgb=(1.0, 0.78, 0.5), flex=0.45)
    reb.emit_strength(bulb_glow, 2.5)
    reb.spot("Daylight through the window", (sum(WINDOW[:2]) / 2, Y0 - 2.5, 2.4), (3.6, 2.8, 0.0), 420, (0.8, 0.86, 1.0), 40, 0.8, 0.5)
    for ob in bpy.data.objects:
        if "glass" in ob.name.lower() and ob.type == "MESH":
            ob.visible_shadow = False
    swing = reb.prim("sphere", "Bulb pivot", mat("black"), (2.6, 2.3, H - 0.02), (0.02, 0.02, 0.02))
    for p in (cord, glass, bulb_light):
        p.parent = swing
        p.matrix_parent_inverse = swing.matrix_world.inverted()

    anim = kit.Anim(16)

    def tick(k):
        hand_pivot.rotation_euler = (0, math.radians(222 + (6 if k % 4 < 2 else 0)), 0)
    anim.custom(tick)
    anim.flicker(plate_light, plate_glow, depth=0.2, dropouts=0)
    anim.swing(swing, axis=0, degrees=3)

    # ---- What the game needs.
    room.door("quarry", (DOOR[0], Y0, DOOR[1], Y0 + 0.5), arrive=(2.75, 1.9), face=(0, 1))
    room.check((X0, 2.5, X0 + 0.8, 3.5), "A steel locker, stencilled EXPLOSIVES. KEEP LOCKED.\nIt's padlocked.")
    room.check((X0, 1.5, X0 + 0.8, 2.4), "A box marked CAPS, and coils of wire. Blasting caps.\nKept well away from the locker.")
    room.check((1.2, Y0, 2.25, Y0 + 0.6), "The time clock is still ticking. The second hand's stuck,\njumping on the same mark over and over.")
    room.check((X1 - 1.3, 1.8, X1 - 0.68, 2.5), "The foreman's report, half written. The last line just stops.")
    room.check((X1 - 1.3, 2.5, X1 - 0.68, 3.2), "The shift rosters. Name after name crossed out in red. SICK.\nBy the last one there's hardly anyone left.")
    room.check((X1 - 0.8, Y1 - 0.7, X1, Y1), "The coffee's been on the hot plate for days. It's burnt to tar.")
    room.check((2.1, Y1 - 0.5, 3.1, Y1), "DAYS WITHOUT AN ACCIDENT. Someone wiped the number off\nand wrote a 0.")
    room.entry = "Burnt coffee. The hot plate's still on."
    room.export(anim)


build()
