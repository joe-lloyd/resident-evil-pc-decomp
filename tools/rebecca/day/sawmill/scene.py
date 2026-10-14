"""Camp 4's sawmill, inside, at noon under cloud.

What it tells: the mill was cutting when it happened. A log is still on the
carriage, half through the head saw, the slab peeled back. The sawyer was
at the blade when a sick man came at him. They went into the saw together:
blood is sprayed in a long fan across the stack of fresh boards on the
outfeed side, and an arm in a plaid sleeve lies in the sawdust by the
blade, the sawdust round it soaked dark. Someone threw the drive belt off
to stop it; it hangs slack from the big pulley. The water wheel still
turns outside, so its shaft still turns where it comes through the east
wall, driving nothing. The rest of the sawyer went out the back door: his
blood and his one hand on the frame lead east, to the mill pond. The log
crane waits on its overhead track with its tongs hanging, the lamps hang
dead, and sawdust lies thick over everything. A player should see the
crane and work out that it could lift something heavy, if the mill had
power to spare.

Metres: the floor is x 1.0-14.0, y 2.6-12.2, the shed 6 m to the roof.
The big doors are in the west wall at y 6.0-9.0, open onto the camp yard;
high windows at y 3.4-5.0 and 10.0-11.6 in it, and three in each of the
north and south walls. The back door is in the east wall at y 9.6-10.6,
out to the pond. The carriage runs east-west on rails at y 4.0-5.1 from
x 1.6 to 11.0, the log on it; the head saw's blade stands at x 8.6, y 5.6.
The board stack is at x 8.2-12.2, y 7.8-8.6. The wheel's shaft comes in at
y 4.6, 2.8 m up, its pulley at x 12.8. The crane track runs along y 4.6 at
5.3 m.

Moving: the wheel's shaft and its pulley turning, the crane's tongs and one
lamp swaying, flies on the arm, dust in the light.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import reb  # noqa: E402
import kit  # noqa: E402
from kit import mat  # noqa: E402
from mathutils import Vector  # noqa: E402

X0, X1, Y0, Y1, H = 1.0, 14.0, 2.6, 12.2, 6.0
BIG_DOOR = (6.0, 9.0)
BACK_DOOR = (9.6, 10.6)
TRACK = (1.6, 11.0)          # the carriage rails (x)
RAIL_Y = (4.0, 5.1)
BLADE = (8.6, 5.6, 1.05)     # the head saw's centre
SHAFT_Y, SHAFT_Z = 4.6, 2.8
STACK = (8.2, 12.2, 7.8, 8.6)
HIGH = (3.8, 4.8)            # the high windows' sill and head


def settle(ob, at, rot):
    """Bake a joined object's parts where they were built, then place it."""
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.location = at
    ob.rotation_euler = rot
    return ob


def build():
    rng = random.Random(1972)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.camera((1.4, 3.0, 3.2), (9.0, 8.4, 0.6), 200, "high in the north-west corner: the log on the carriage, the blade, the blood on the boards")
    room.camera((13.6, 11.8, 3.2), (6.0, 5.4, 0.8), 200, "high in the south-east corner: the board stack's bloody face, the saw, the big doors far off")
    room.camera((13.6, 3.0, 3.3), (5.0, 9.2, 0.6), 200, "high in the north-east corner: the turning pulley, the slack belt, the crane, the mill's length")
    room.camera((1.4, 11.8, 3.2), (10.0, 4.4, 0.8), 200, "high in the south-west corner: the big doors, the edger, the back door far off")
    room.camera((11.2, 7.2, 2.4), (8.4, 5.6, 0.5), 200, "close on the head saw: the blade, the arm in the sawdust")
    room.camera((13.6, 7.6, 2.9), (2.0, 7.6, 0.8), 200, "from by the back door: down the mill to the big doors and the yard")

    walls_m = kit.boards("Mill boards", (0.2, 0.15, 0.1), width=0.22, grime=0.8)
    sawdust = reb.mat_surface("Sawdust", [(0.0, (0.22, 0.15, 0.08)), (0.5, (0.36, 0.26, 0.15)), (0.8, (0.42, 0.32, 0.19)), (1.0, (0.28, 0.2, 0.11))], scale=3.5, bump=0.5)
    wet_dust = reb.mat_surface("Bloody sawdust", [(0.0, (0.05, 0.004, 0.003)), (0.6, (0.13, 0.02, 0.012)), (1.0, (0.2, 0.06, 0.03))], scale=8, rough=0.55, bump=0.5)
    timber = reb.mat_wood("Mill timber", (0.17, 0.11, 0.065))
    fresh = reb.mat_surface("Fresh boards", [(0.0, (0.35, 0.24, 0.13)), (0.6, (0.5, 0.37, 0.21)), (1.0, (0.42, 0.3, 0.17))], scale=4, bump=0.2)
    iron = mat("iron")
    green = mat("green paint")
    blade_m = reb.mat_metal("Saw steel", (0.38, 0.38, 0.37), 0.35)
    belt_m = reb.mat_plain("Belt leather", (0.05, 0.03, 0.018), 0.55)
    tin = reb.mat_surface("Roof tin underside", [(0.0, (0.1, 0.1, 0.095)), (0.7, (0.17, 0.17, 0.16)), (1.0, (0.18, 0.09, 0.04))], scale=2, rough=0.6, bump=0.2)
    enamel = reb.mat_plain("Lamp enamel", (0.1, 0.18, 0.12), 0.45)
    logs_m = reb.mat_surface("Log bark", [(0.0, (0.05, 0.035, 0.025)), (0.6, (0.12, 0.085, 0.06)), (1.0, (0.18, 0.14, 0.1))], scale=6, bump=0.9)
    end_m = reb.mat_surface("Log ends", [(0.0, (0.28, 0.18, 0.09)), (0.7, (0.42, 0.3, 0.16)), (1.0, (0.2, 0.12, 0.06))], scale=12, bump=0.2)

    # ---- The shed: board walls on posts, the doors and windows cut, sawdust floor, tin roof on trusses.
    openings = [("w", BIG_DOOR[0], BIG_DOOR[1], 0.0, 3.4), ("w", 3.4, 5.0, *HIGH), ("w", 10.0, 11.6, *HIGH), ("e", BACK_DOOR[0], BACK_DOOR[1], 0.0, 2.1)]
    for x in (3.0, 7.0, 11.0):
        openings += [("n", x, x + 1.6, *HIGH), ("s", x, x + 1.6, *HIGH)]
    openings.append(("e", 5.0, 6.4, *HIGH))
    kit.walls(X0, Y0, X1, Y1, H, walls_m, openings=openings, floor=sawdust, name="Mill wall")
    for x in (X0 + 0.05, 4.5, 8.0, 11.5, X1 - 0.05):
        for y in (Y0 + 0.08, Y1 - 0.08):
            reb.prim("cube", "Wall post", timber, (x, y, H / 2), (0.2, 0.16, H))
    for y in (Y0 + 0.08, 5.8, 9.4, Y1 - 0.08):
        for x in (X0 + 0.08, X1 - 0.08):
            reb.prim("cube", "Wall post", timber, (x, y, H / 2), (0.16, 0.2, H))
    reb.prim("cube", "Roof", tin, ((X0 + X1) / 2, (Y0 + Y1) / 2, H + 0.05), (X1 - X0 + 0.4, Y1 - Y0 + 0.4, 0.1))
    for x in (2.6, 4.5, 6.3, 8.0, 9.8, 11.5, 13.2):
        reb.prim("cube", "Tie beam", timber, (x, (Y0 + Y1) / 2, H - 0.3), (0.18, Y1 - Y0, 0.24))
        kit.rod("King post", timber, (x, (Y0 + Y1) / 2, H - 0.3), (x, (Y0 + Y1) / 2, H), 0.07)
        for s in (-1, 1):
            kit.rod("Strut", timber, (x, (Y0 + Y1) / 2 + s * 2.6, H - 0.3), (x, (Y0 + Y1) / 2, H - 0.05), 0.05)
    # Middle posts holding the tie beams, down the south half.
    posts = []
    for x in (4.5, 11.5):
        p = reb.prim("cube", "Mill post", timber, (x, 9.4, H / 2), (0.24, 0.24, H))
        reb.mask(reb.wall(p))
        posts.append(p)
    # Window frames, glass grimy, some panes gone.
    glass = reb.mat_glass("Grimy glass", (0.45, 0.48, 0.45))
    for side, a0, a1 in [(s, a, b) for s, a, b, *_ in openings if _[0] > 1]:
        mid = (a0 + a1) / 2
        if side == "n":
            at, size = (mid, Y0 - 0.06, sum(HIGH) / 2), (a1 - a0, 0.01, HIGH[1] - HIGH[0])
        elif side == "s":
            at, size = (mid, Y1 + 0.06, sum(HIGH) / 2), (a1 - a0, 0.01, HIGH[1] - HIGH[0])
        elif side == "w":
            at, size = (X0 - 0.06, mid, sum(HIGH) / 2), (0.01, a1 - a0, HIGH[1] - HIGH[0])
        else:
            at, size = (X1 + 0.06, mid, sum(HIGH) / 2), (0.01, a1 - a0, HIGH[1] - HIGH[0])
        if rng.random() < 0.75:
            reb.prim("cube", "Window glass", glass, at, size)

    # ---- Outside: the yard through the big doors, the pond's light through the back door.
    yard = reb.mat_surface("Yard mud", [(0.0, (0.04, 0.03, 0.02)), (0.5, (0.1, 0.075, 0.05)), (1.0, (0.14, 0.11, 0.075))], scale=1.4, rough=0.7, bump=0.6)
    reb.prim("cube", "Yard outside", yard, (X0 - 15.0, 7.5, -0.06), (30.0, 40.0, 0.1))
    reb.prim("cube", "Pond bank outside", reb.mat_surface("Bank", [(0.0, (0.05, 0.06, 0.03)), (1.0, (0.12, 0.12, 0.06))], scale=1.5, bump=0.5), (X1 + 10.0, 7.5, -0.06), (20.0, 40.0, 0.1))
    reb.prim("cube", "Pond outside", mat("water"), (X1 + 9.0, 12.0, -0.03), (10.0, 14.0, 0.02))
    boards_m = kit.boards("Bunkhouse boards", (0.2, 0.13, 0.08), width=0.2)
    reb.prim("cube", "Mess hall across the yard", reb.mat_surface("Whitewash", [(0.0, (0.45, 0.44, 0.4)), (1.0, (0.6, 0.58, 0.53))], scale=4, bump=0.1), (X0 - 17.0, 8.0, 1.5), (0.4, 9.0, 3.0))
    reb.prim("cube", "Bunkhouse across the yard", boards_m, (X0 - 9.0, -1.0, 1.4), (11.0, 5.0, 2.8))
    reb.prim("cube", "Skidder in the yard", reb.mat_plain("Skidder yellow", (0.45, 0.32, 0.03), 0.5), (X0 - 9.5, 12.5, 1.0), (4.8, 2.0, 1.8), rot=(0, 0, 0.1))
    kit.drum("Drum in the yard", mat("rust"), (X0 - 3.0, 10.5, 0.0))
    for k in range(4):
        kit.rod("Log by the doors", logs_m, (X0 - 2.6 - k * 0.1, 3.4 + k * 0.62, 0.32), (X0 - 6.9, 3.5 + k * 0.62, 0.32), 0.3, 12)
    # The big doors, run open along their rail on the outside wall.
    for i, y in enumerate((BIG_DOOR[0] - 1.45, BIG_DOOR[1] + 1.45)):
        reb.prim("cube", f"Big door {i}", walls_m, (X0 - 0.2, y, 1.7), (0.08, 1.5, 3.4))
    reb.prim("cube", "Door rail", mat("rust"), (X0 - 0.22, 7.5, 3.5), (0.08, 9.0, 0.08))
    # The back door, ajar, its frame and his hand on it.
    reb.prim("cube", "Back door", walls_m, (X1 + 0.45, BACK_DOOR[0] - 0.05, 1.05), (0.9, 0.05, 2.1), rot=(0, 0, 0.35))
    for y in BACK_DOOR:
        reb.prim("cube", "Back door frame", timber, (X1 - 0.02, y + (0.04 if y > 10 else -0.04), 1.05), (0.12, 0.08, 2.1))
    reb.prim("cube", "Back door head", timber, (X1 - 0.02, sum(BACK_DOOR) / 2, 2.14), (0.12, 1.2, 0.08))
    kit.splat("His hand on the back door frame", mat("blood"), (X1 - 0.09, BACK_DOOR[0] - 0.06, 1.2), 0.07, rot=(0, math.pi / 2, 0), seed=5)
    reb.prim("cube", "Smear down the frame", mat("old blood"), (X1 - 0.085, BACK_DOOR[0] - 0.06, 0.9), (0.004, 0.05, 0.5), rot=(0.08, 0, 0))

    # ---- The carriage on its rails, the log half through the saw.
    for y in RAIL_Y:
        reb.prim("cube", "Carriage rail", mat("steel"), ((TRACK[0] + TRACK[1]) / 2, y, 0.06), (TRACK[1] - TRACK[0], 0.08, 0.12))
    for x in [TRACK[0] + 0.3 + k * 0.8 for k in range(12)]:
        reb.prim("cube", "Rail tie", timber, (x, sum(RAIL_Y) / 2, 0.03), (0.2, 1.5, 0.06))
    cx0, cx1 = 3.6, 7.6
    carriage = reb.prim("cube", "Carriage", green, ((cx0 + cx1) / 2, sum(RAIL_Y) / 2, 0.42), (cx1 - cx0, 1.3, 0.36), bevel=0.02)
    for x in (cx0 + 0.3, cx1 - 0.3):
        for y in RAIL_Y:
            reb.prim("cyl", "Carriage wheel", iron, (x, y, 0.16), (0.24, 0.24, 0.08), rot=(math.pi / 2, 0, 0), segments=12)
    for x in (cx0 + 0.5, (cx0 + cx1) / 2, cx1 - 0.5):
        reb.prim("cube", "Head block", iron, (x, RAIL_Y[0] + 0.15, 0.9), (0.35, 0.3, 0.6))
        reb.prim("cube", "Knee", green, (x, RAIL_Y[0] + 0.4, 0.95), (0.3, 0.14, 0.7))
        kit.rod("Dog", mat("steel"), (x, RAIL_Y[0] + 0.45, 1.3), (x, RAIL_Y[0] + 0.7, 1.45), 0.025, 6)
    lr = 0.42
    log_y = RAIL_Y[0] + 0.9
    kit.rod("Log on the carriage", logs_m, (2.6, log_y, 1.05), (cx1 + 1.5, log_y, 1.05), lr, 16)
    for x in (2.595, cx1 + 1.505):
        reb.prim("cyl", "Log end", end_m, (x, log_y, 1.05), (2 * lr - 0.02, 2 * lr - 0.02, 0.01), rot=(0, math.pi / 2, 0), segments=16)
    # The slab half cut off its south face, peeling away past the blade.
    reb.prim("cube", "Cut face", fresh, (BLADE[0] + 0.4, log_y + lr * 0.55, 1.05), (1.6, 0.02, 0.62))
    slab = reb.prim("cube", "Slab", logs_m, (BLADE[0] + 0.5, log_y + lr * 0.75, 1.0), (1.5, 0.12, 0.55), rot=(0.25, 0, -0.08))
    reb.wall(reb.prim("cube", "Carriage footprint", None, ((TRACK[0] + TRACK[1]) / 2, sum(RAIL_Y) / 2 + 0.1, 0.6), (TRACK[1] - TRACK[0], 1.6, 1.2))).hide_render = True
    reb.mask(carriage)
    reb.mask(bpy.data.objects["Log on the carriage"])
    # The head saw: the blade in its iron frame, the mandrel housing, its guard.
    bx, by, bz = BLADE
    blade = reb.prim("cyl", "Head saw blade", blade_m, (bx, by, bz), (1.5, 1.5, 0.012), rot=(math.pi / 2, 0, 0), segments=48)
    teeth = []
    for k in range(40):
        a = 2 * math.pi * k / 40
        teeth.append(reb.prim("cube", "Saw tooth", blade_m, (bx + math.cos(a) * 0.76, by, bz + math.sin(a) * 0.76), (0.05, 0.014, 0.03), rot=(0, -a, 0)))
    kit.join("Saw teeth", teeth)
    kit.splat("Blood on the blade", mat("blood"), (bx + 0.2, by + 0.008, bz + 0.25), 0.25, rot=(math.pi / 2, 0, 0), seed=11, stretch=(1.4, 0.8))
    kit.splat("Blood on the blade, back", mat("old blood"), (bx - 0.25, by - 0.008, bz - 0.1), 0.2, rot=(math.pi / 2, 0, 0), seed=12)
    reb.prim("cyl", "Mandrel", iron, (bx, by + 0.45, bz), (0.24, 0.24, 0.9), rot=(math.pi / 2, 0, 0), segments=14)
    frame = reb.prim("cube", "Saw frame", green, (bx, by + 0.75, 0.55), (1.3, 0.7, 1.1), bevel=0.03)
    reb.mask(reb.wall(frame))
    reb.prim("cyl", "Saw pulley", iron, (bx, by + 1.15, bz), (0.7, 0.7, 0.18), rot=(math.pi / 2, 0, 0), segments=20)
    guard = reb.prim("cube", "Blade guard", mat("rust"), (bx, by, bz + 0.85), (1.2, 0.2, 0.08), rot=(0, 0.12, 0))
    reb.prim("cube", "Saw deck", timber, (bx, by - 0.2, 0.3), (2.0, 0.5, 0.6))
    reb.wall(reb.prim("cube", "Saw footprint", None, (bx, by + 0.4, 0.5), (2.0, 1.6, 1.0))).hide_render = True
    reb.prim("cube", "Warning sign", mat("white paint"), (bx + 1.3, by + 1.08, 1.6), (0.6, 0.02, 0.36))
    kit.text("Warning words", "DANGER", mat("red paint"), (bx + 1.3, by + 1.095, 1.68), size=0.11, rot=(math.pi / 2, 0, math.pi))
    kit.text("Warning words 2", "KEEP HANDS CLEAR", mat("black"), (bx + 1.3, by + 1.095, 1.53), size=0.055, rot=(math.pi / 2, 0, math.pi))
    kit.rod("Sign post", timber, (bx + 1.3, by + 1.12, 0), (bx + 1.3, by + 1.12, 1.45), 0.04)
    # The sawyer's lever and stool, his gloves, his hard hat rolled away.
    kit.rod("Setworks lever", mat("steel"), (bx - 1.4, by + 0.4, 0.0), (bx - 1.25, by + 0.5, 1.15), 0.025)
    reb.prim("sphere", "Lever knob", mat("black"), (bx - 1.25, by + 0.5, 1.17), (0.07, 0.07, 0.07))
    stool = kit.join("Sawyer's stool", [reb.prim("cyl", "seat", timber, (0, 0, 0.62), (0.36, 0.36, 0.05), segments=12)] +
                     [kit.rod("leg", timber, (0, 0, 0.6), (math.cos(a) * 0.2, math.sin(a) * 0.2, 0.0), 0.022, 5) for a in (0.3, 2.4, 4.5)])
    settle(stool, (bx - 1.0, by + 1.6, 0.18), (math.pi / 2, 0, 0.4))
    hat = reb.mat_plain("Hard hat", (0.55, 0.38, 0.03), 0.4)
    reb.prim("sphere", "Sawyer's hard hat", hat, (6.2, 7.2, 0.07), (0.3, 0.26, 0.2), rot=(0.4, 0.2, 0), segments=14)
    reb.prim("cyl", "Hard hat brim", hat, (6.2, 7.22, 0.04), (0.36, 0.32, 0.015), rot=(0.4, 0.2, 0), segments=16)
    for k in range(2):
        reb.cloth(f"Glove {k}", reb.mat_plain("Leather glove", (0.3, 0.2, 0.1), 0.8), (bx - 0.4 + k * 0.5, by + 1.9, 0.03), (0.12, 0.2), rot=(0, 0, 0.6 + k), cuts=4, lumps=0.02, seed=k)

    # ---- The arm in the sawdust by the blade; the dark soaked patch; the fan of blood across the boards.
    ax, ay = bx + 0.9, by + 0.95
    arm_parts = [
        kit.rod("forearm", mat("skin"), (0, 0, 0.05), (0.28, 0.03, 0.04), 0.042, 10),
        kit.rod("sleeve", reb.mat_stripes("Plaid sleeve", [(0.3, 0.04, 0.03), (0.04, 0.03, 0.03)], across=22), (-0.32, -0.02, 0.06), (0.02, 0.0, 0.05), 0.06, 10),
        reb.prim("sphere", "hand", mat("skin"), (0.36, 0.04, 0.035), (0.11, 0.08, 0.05), segments=10),
        reb.prim("sphere", "torn end", wet_dust, (-0.34, -0.02, 0.06), (0.12, 0.13, 0.12), segments=10),
    ]
    for k in range(4):
        arm_parts.append(kit.rod("finger", mat("skin"), (0.38, 0.0 + k * 0.025, 0.035), (0.46, -0.01 + k * 0.03, 0.02), 0.01, 5))
    settle(kit.join("Arm in the sawdust", arm_parts), (ax, ay, 0.0), (0, 0, 2.3))
    kit.splat("Soaked sawdust", wet_dust, (ax - 0.15, ay - 0.1, 0.004), 0.55, seed=21, stretch=(1.3, 1.0))
    kit.splat("Soaked sawdust under the blade", wet_dust, (bx + 0.2, by + 0.25, 0.006), 0.45, seed=22, stretch=(1.6, 0.8))
    sx0, sx1, sy0, sy1 = STACK
    stack_parts = []
    for row in range(14):
        z = 0.05 + row * 0.11
        for k in range(8):
            y = sy0 + 0.05 + k * 0.1
            if row == 13 and k > 4:
                continue
            stack_parts.append(reb.prim("cube", "board", fresh, ((sx0 + sx1) / 2 + rng.uniform(-0.06, 0.06), y, z + 0.02), (sx1 - sx0 - rng.uniform(0, 0.2), 0.09, 0.04)))
        if row % 3 == 2:
            for x in (sx0 + 0.3, (sx0 + sx1) / 2, sx1 - 0.3):
                stack_parts.append(reb.prim("cube", "sticker", timber, (x, (sy0 + sy1) / 2, z + 0.065), (0.04, sy1 - sy0, 0.025)))
    stack = kit.join("Board stack", stack_parts)
    reb.mask(reb.wall(stack))
    # The fan: blood flung off the blade, thick near the saw end, thinning east along the stack's face.
    fv, ff = [], []
    for k in range(70):
        t = rng.random() ** 1.6
        x = sx0 + 0.05 + t * (sx1 - sx0 - 0.3)
        z = 0.5 + 0.9 * (1 - t) * rng.uniform(0.4, 1.0) + rng.uniform(-0.1, 0.25)
        r = 0.09 * (1 - t) + 0.015 + rng.uniform(0, 0.03)
        kit._stain(fv, ff, rng, (x, z, 0.0), r, rng.uniform(-0.3, 0.3), 0.3, (1.8, 0.7), k, points=10)
    fan = reb.mesh_object("Blood fan on the boards", [(x, sy0 - 0.012, z) for x, z, _ in fv], ff, mat("blood"), smooth=False)
    kit.splat("Run down the boards", mat("old blood"), (sx0 + 0.6, sy0 - 0.013, 0.7), 0.15, rot=(math.pi / 2, 0, 0), seed=23, stretch=(0.5, 2.2))
    # Spray on the floor between the saw and the stack.
    for k in range(10):
        x, y = bx + rng.uniform(0.2, 2.5), by + 1.3 + rng.uniform(0.0, 0.9)
        kit.splat(f"Spray on the floor {k}", mat("blood"), (x, y, 0.005), rng.uniform(0.04, 0.1), seed=30 + k, stretch=(1.6, 0.8))
    # His blood east to the back door, through the sawdust, and the scuffed way he went.
    kit.drag_trail("His way out", mat("old blood"), [(ax + 0.3, ay + 0.2), (11.0, 7.4), (12.4, 9.0), (13.2, 9.8), (13.9, 10.1)], width=0.28, seed=40)
    kit.drag_trail("His way out, fresher", mat("blood"), [(ax + 0.3, ay + 0.2), (11.4, 7.6), (12.6, 9.2), (13.6, 10.0)], width=0.16, seed=41)

    # ---- The wheel's shaft through the east wall, its pulley turning; the belt thrown off and hanging.
    kit.rod("Wheel shaft", iron, (X1 + 0.6, SHAFT_Y, SHAFT_Z), (11.8, SHAFT_Y, SHAFT_Z), 0.11, 16)
    reb.prim("cube", "Shaft bearing", iron, (X1 - 0.25, SHAFT_Y, SHAFT_Z - 0.18), (0.4, 0.35, 0.3))
    reb.prim("cube", "Bearing post", timber, (X1 - 0.25, SHAFT_Y, (SHAFT_Z - 0.33) / 2), (0.3, 0.3, SHAFT_Z - 0.33))
    pulley = reb.prim("cyl", "Big pulley", iron, (12.8, SHAFT_Y, SHAFT_Z), (1.7, 1.7, 0.32), rot=(0, math.pi / 2, 0), segments=32)
    spokes = []
    for k in range(6):
        a = math.pi * k / 3
        spokes.append(kit.rod("Pulley spoke", mat("rust"), (12.62, SHAFT_Y, SHAFT_Z), (12.62, SHAFT_Y + math.cos(a) * 0.82, SHAFT_Z + math.sin(a) * 0.82), 0.035, 6))
        spokes[-1].parent = pulley
        spokes[-1].matrix_parent_inverse = pulley.matrix_world.inverted()
    reb.mask(reb.wall(bpy.data.objects["Bearing post"]))
    # The belt hangs off it in a slack loop to the floor.
    pts = [(12.8, SHAFT_Y + 0.85, SHAFT_Z), (12.6, SHAFT_Y + 1.2, 1.6), (12.2, SHAFT_Y + 1.1, 0.4), (11.4, SHAFT_Y + 0.9, 0.06), (10.4, SHAFT_Y + 1.1, 0.04), (9.6, SHAFT_Y + 1.4, 0.05), (bx, by + 1.15, bz - 0.35)]
    for a, b in zip(pts, pts[1:]):
        reb.prim("cube", "Thrown belt", belt_m, ((Vector(a) + Vector(b)) / 2), ((Vector(b) - Vector(a)).length + 0.05, 0.22, 0.012), rot=(Vector(b) - Vector(a)).to_track_quat("X", "Z").to_euler())
    # The line shaft along the north wall, its belts up to the crane's winch.
    kit.rod("Line shaft", iron, (2.0, Y0 + 0.5, 4.3), (13.6, Y0 + 0.5, 4.3), 0.05, 10)
    for x in (4.0, 7.6, 12.6):
        reb.prim("cyl", "Line pulley", iron, (x, Y0 + 0.5, 4.3), (0.5, 0.5, 0.12), rot=(0, math.pi / 2, 0), segments=16)
        kit.rod("Hanger", iron, (x, Y0 + 0.5, 4.3), (x, Y0 + 0.5, H - 0.3), 0.04)

    # ---- The log crane: an I-beam track under the roof, the trolley, the hoist chain and the tongs.
    track_z = 5.3
    reb.prim("cube", "Crane track", reb.mat_metal("Crane steel", (0.12, 0.11, 0.09), 0.45), ((X0 + X1) / 2, SHAFT_Y, track_z), (X1 - X0 - 0.4, 0.18, 0.3))
    for x in (2.6, 6.3, 9.8, 13.2):
        kit.rod("Track hanger", iron, (x, SHAFT_Y, track_z + 0.15), (x, SHAFT_Y, H - 0.3), 0.04)
    tx = 5.4
    reb.prim("cube", "Trolley", mat("yellow paint"), (tx, SHAFT_Y, track_z - 0.3), (0.6, 0.5, 0.35), bevel=0.02)
    reb.prim("cube", "Hoist", mat("yellow paint"), (tx, SHAFT_Y, track_z - 0.65), (0.4, 0.45, 0.4), bevel=0.02)
    kit.text("Crane rating", "5 TON", mat("black"), (tx, SHAFT_Y + 0.23, track_z - 0.65), size=0.09, rot=(math.pi / 2, 0, math.pi))
    tong_pivot = reb.prim("sphere", "Hoist hook", iron, (tx, SHAFT_Y, track_z - 0.85), (0.06, 0.06, 0.06))
    chain = kit.rod("Hoist chain", iron, (0, 0, 0), (0, 0, -1.6), 0.02, 6)
    chain.parent = tong_pivot
    tongs = []
    for s in (-1, 1):
        tongs.append(kit.rod("Tong arm", iron, (0, 0, -1.6), (s * 0.35, 0, -2.0), 0.03, 6))
        tongs.append(kit.rod("Tong jaw", iron, (s * 0.35, 0, -2.0), (s * 0.15, 0, -2.35), 0.028, 6))
    for t in tongs:
        t.parent = tong_pivot

    # ---- The south half: the edger table, the saw filer's bench, spare blades, carts, sawdust heaps, dead lamps.
    edger = kit.table("Edger table", timber, (5.6, 10.6, 0.0), size=(3.6, 0.9, 0.85))
    reb.mask(reb.wall(edger))
    for x in (5.0, 5.6, 6.2):
        reb.prim("cyl", "Edger saw", blade_m, (x, 10.6, 0.9), (0.42, 0.42, 0.01), rot=(math.pi / 2, 0, math.pi / 2), segments=24)
    for k in range(3):
        reb.prim("cube", "Edged board", fresh, (4.4 + k * 0.7, 10.6 + 0.15 * k - 0.15, 0.88), (1.6, 0.2, 0.04), rot=(0, 0, 0.08 * k))
    bench = kit.table("Filer's bench", timber, (11.6, Y1 - 0.45, 0.0), size=(2.4, 0.7, 0.9))
    reb.mask(reb.wall(bench))
    reb.prim("cube", "Vice", iron, (11.0, Y1 - 0.45, 0.98), (0.2, 0.25, 0.16))
    for k, x in enumerate((9.2, 10.4, 12.8)):
        reb.prim("cyl", f"Spare blade {k}", blade_m, (x, Y1 - 0.04, 2.2), (1.1, 1.1, 0.012), rot=(math.pi / 2, 0, 0), segments=40)
        reb.prim("cube", f"Blade peg {k}", timber, (x, Y1 - 0.05, 2.78), (0.06, 0.08, 0.06))
    kit.papers("Tally sheets", (12.2, Y1 - 0.45, 0.9), spread=0.3, count=4, seed=6)
    reb.prim("cube", "Tally board", reb.mat_surface("Chalkboard", [(0.0, (0.04, 0.06, 0.05)), (1.0, (0.1, 0.12, 0.1))], scale=6, rough=0.9, bump=0.05), (7.0, Y1 - 0.02, 1.7), (1.2, 0.02, 0.8))
    kit.text("Tally", "MON 4100\nTUE 3850\nWED 1200", reb.mat_plain("Chalk", (0.62, 0.62, 0.58), 0.95), (7.0, Y1 - 0.035, 1.75), size=0.09, rot=(math.pi / 2, 0, math.pi))
    for k, (x, y) in enumerate(((2.4, 11.0), (8.2, 11.2))):
        kit.drum(f"Oil drum {k}", mat("rust"), (x, y, 0.0))
    cart = kit.table("Lumber cart", mat("rust"), (3.0, 8.4, 0.0), size=(2.2, 1.0, 0.55))
    reb.mask(reb.wall(cart))
    for k in range(4):
        reb.prim("cube", "Board on the cart", fresh, (3.0, 8.1 + k * 0.2, 0.58 + 0.04 * (k % 2)), (2.3, 0.18, 0.04))
    for k in range(2):
        kit.rod(f"Peavey {k}", timber, (12.6 + k * 0.3, Y0 + 0.2, 0.0), (12.4 + k * 0.3, Y0 + 0.6, 1.6), 0.025)
    dv, df = [], []
    for (x, y, r) in ((bx + 0.6, by + 2.2, 0.9), (2.2, 6.6, 0.7), (6.0, 6.4, 0.6), (13.0, 6.0, 0.6), (9.4, 11.4, 0.5)):
        reb.boulder(rng, (x, y, -0.25), r, dv, df, squash=0.35)
    reb.mesh_object("Sawdust heaps", dv, df, sawdust)
    # Dead lamps on long flexes over the saw line.
    lamps = []
    for k, x in enumerate((3.0, 6.0, 9.0, 12.0)):
        top = (x, 6.4, H - 0.3)
        pv = reb.prim("sphere", f"Lamp hook {k}", iron, top, (0.04, 0.04, 0.04))
        flex = kit.rod("Lamp flex", mat("black"), (0, 0, 0), (0, 0, -1.8), 0.008, 4)
        shade = reb.prim("cone", "Lamp shade", enamel, (0, 0, -1.9), (0.45, 0.45, 0.2), segments=16, top=0.25)
        bulb = reb.prim("sphere", "Dead bulb", reb.mat_plain("Dead bulb", (0.4, 0.4, 0.36), 0.2), (0, 0, -1.98), (0.08, 0.08, 0.1), segments=8)
        for p in (flex, shade, bulb):
            p.parent = pv
        lamps.append(pv)

    # ---- Light: grey day through the windows and the doors, dust hanging in it; no power.
    kit.time_light("noon", sun_heading=200, sun_energy=1.0, mist=(((X0 + X1) / 2, (Y0 + Y1) / 2, H / 2), (X1 - X0, Y1 - Y0, H), 0.025),
                   sky=((0.6, 0.62, 0.63), (0.4, 0.42, 0.45), 1.0))
    reb.spot("Day through the big doors", (X0 - 6.0, 7.5, 3.0), (X0 + 4.5, 7.5, 0.0), 2600, (0.78, 0.82, 0.88), 45, 0.8, 2.5)
    for x in (3.8, 7.8, 11.8):
        reb.spot("Day through a north window", (x, Y0 - 4.0, 7.5), (x + 0.5, Y0 + 3.5, 0.0), 650, (0.8, 0.84, 0.9), 22, 0.7, 0.6)
        reb.spot("Day through a south window", (x, Y1 + 4.0, 7.5), (x - 0.4, Y1 - 3.0, 0.0), 420, (0.78, 0.82, 0.88), 22, 0.7, 0.6)
    reb.spot("Day through the back door", (X1 + 4.0, 10.1, 2.0), (X1 - 3.0, 9.6, 0.0), 500, (0.75, 0.8, 0.85), 35, 0.8, 0.8)
    reb.point("Fill", ((X0 + X1) / 2, 8.0, 4.5), 120, (0.7, 0.72, 0.75), 3.0)

    anim = kit.Anim(16)
    pulley.rotation_mode = "ZYX"   # spin about its own axis first, then lie it along x
    anim.spin(pulley, axis=2, turns=1, symmetry=6)
    anim.swing(tong_pivot, axis=0, degrees=3)
    anim.swing(lamps[2], axis=1, degrees=4)
    anim.flies((ax, ay, 0.05), count=10, radius=0.4)
    anim.flies((sx0 + 0.8, sy0 - 0.3, 0.6), count=6, radius=0.4)

    # ---- What the game needs.
    room.door("camp-yard", (X0, BIG_DOOR[0], X0 + 0.7, BIG_DOOR[1]), arrive=(2.4, 7.5), face=(1, 0))
    room.door("pond", (X1 - 0.6, BACK_DOOR[0], X1, BACK_DOOR[1]), arrive=(12.7, 10.1), face=(-1, 0))
    room.check((bx - 1.0, by + 1.4, bx + 1.6, by + 2.2), "An arm, in a plaid sleeve. Torn off at the elbow.\nThe sawdust round it is soaked through.")
    room.check((sx0, sy0 - 0.7, sx1, sy0), "Blood, thrown across the boards in a long fan.\nThe saw was running when it happened.")
    room.check((bx - 1.6, by + 1.0, bx - 0.6, by + 1.6), "The head saw. There's still a log on the carriage, half cut.\nSomeone threw the belt off to stop the blade.")
    room.check((11.6, SHAFT_Y + 0.6, 13.6, SHAFT_Y + 1.6), "The water wheel's shaft. It's still turning.\nThe belt's off, so it isn't driving anything.")
    room.check((tx - 0.9, RAIL_Y[1], tx + 0.9, RAIL_Y[1] + 0.8), "The log crane, on its track. 5 TON.\nIt could lift anything in this camp, if it had power.")
    room.check((X1 - 1.0, BACK_DOOR[0] - 0.5, X1, BACK_DOOR[0]), "A bloody hand on the back door's frame.\nHe went out this way.")
    room.check((6.4, Y1 - 0.6, 7.6, Y1), "Board feet cut: Monday 4100. Tuesday 3850. Wednesday 1200.\nThen nothing.")
    room.entry = "Sawdust, and the smell of blood."
    room.export(anim)


build()
