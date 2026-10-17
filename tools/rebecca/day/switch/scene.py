"""The switch house for the gondola's power line, behind the generator hut,
afternoon.

What it tells: the generator's power goes out from here, up the line to the
Arklay Skyway's upper station, and to the ranger station and the mine. Every
breaker on the board is down: OFF. The big isolator lever on the south wall
is down too, and padlocked; its key is not here. Dale came through in the
night after the dog bit him, bleeding, and tried to put the line back on
by hand. The control batteries shorted across a contactor and threw him off
it: there is a black scorch up the board, a burnt rubber glove on the
floor, and the contactor still spits sparks off the batteries now. His
blood is on the east door's handle where he let himself out to the line
track. The sun comes in through the barred window and the door.

Metres: the floor is x 1.0-4.6, y 1.0-4.0, 2.9 high, painted brick. The
door from the generator hut is in the north wall at x 1.8-2.6. The door out
to the line track is in the east wall at y 2.2-3.1, standing open. The
breaker board runs along the west wall; the isolator lever is on the south
wall at x 3.0; the barred window is high in the south wall at x 1.6-2.4.

Moving: the sparking contactor and its blue flashes.
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

X0, X1, Y0, Y1, H = 1.0, 4.6, 1.0, 4.0, 2.9
NDOOR = (1.8, 2.6)
EDOOR = (2.2, 3.1)
WINDOW = (1.6, 2.4, 1.85, 2.4)    # x0, x1, z0, z1 in the south wall
SPARK = (X0 + 0.16, 2.5, 1.45)


def build():
    rng = random.Random(43)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.ground("concrete")
    room.floor((1.15, 1.1, 1.95, 3.7), "metal")  # the tread plate
    room.camera((4.45, 1.15, 2.5), (1.4, 3.3, 0.7), 200, "high in the north-east corner: the breaker board, the sparking contactor, the glove, the isolator lever")
    room.camera((1.25, 3.85, 2.5), (3.9, 1.2, 0.6), 200, "high in the south-west corner: the door from the generator, the open door to the line track")

    brick = kit.dirtied(reb.mat_surface("Painted brick", [(0.0, (0.2, 0.17, 0.13)), (0.55, (0.32, 0.29, 0.23)), (1.0, (0.26, 0.11, 0.07))], scale=7, bump=0.6), 0.6, scale=1.2)
    floor_m = kit.dirtied(mat("concrete"), 0.8, scale=0.8)
    slate = reb.mat_surface("Slate panel", [(0.0, (0.03, 0.035, 0.04)), (1.0, (0.08, 0.085, 0.09))], scale=5, rough=0.5, bump=0.1)
    cab_grey = reb.mat_surface("Cabinet grey", [(0.0, (0.15, 0.16, 0.15)), (0.8, (0.25, 0.26, 0.24)), (1.0, (0.2, 0.12, 0.06))], scale=5, rough=0.45, bump=0.15)
    plate = reb.mat_surface("Tread plate", [(0.0, (0.1, 0.1, 0.1)), (1.0, (0.2, 0.2, 0.19))], scale=60, rough=0.4, bump=1.0)
    scorch = reb.mat_surface("Scorch", [(0.0, (0.005, 0.005, 0.005)), (0.7, (0.03, 0.025, 0.02)), (1.0, (0.08, 0.05, 0.03))], scale=8, bump=0.3)
    copper = reb.mat_metal("Copper", (0.5, 0.25, 0.12), 0.35)
    door_m = reb.mat_surface("Door grey", [(0.0, (0.12, 0.14, 0.12)), (0.8, (0.2, 0.22, 0.2)), (1.0, (0.2, 0.1, 0.05))], scale=5, rough=0.5, bump=0.15)

    # ---- The shell: brick, a slab floor, the ceiling; the doors and the barred window.
    kit.walls(X0, Y0, X1, Y1, H, brick, openings=[
        ("n", NDOOR[0], NDOOR[1], 0.0, 2.1),
        ("e", EDOOR[0], EDOOR[1], 0.0, 2.1),
        ("s", WINDOW[0], WINDOW[1], WINDOW[2], WINDOW[3]),
    ], thick=0.22, floor=floor_m, ceiling=reb.mat_surface("Ceiling slab", [(0.0, (0.1, 0.1, 0.09)), (1.0, (0.2, 0.19, 0.18))], scale=3, bump=0.2))
    reb.prim("cube", "Tread plate", plate, (X0 + 0.55, 2.4, 0.004), (0.8, 2.6, 0.008))
    kit.cracks("Floor cracks", mat("black"), (X0 + 0.9, Y0 + 0.2, X1 - 0.2, Y1 - 0.2), count=6, seed=4)
    # The door from the generator hut, shut behind her.
    reb.prim("cube", "North door", door_m, ((NDOOR[0] + NDOOR[1]) / 2, Y0 - 0.1, 1.05), (NDOOR[1] - NDOOR[0], 0.05, 2.1), bevel=0.01)
    reb.prim("cube", "North door handle", mat("steel"), (NDOOR[1] - 0.1, Y0 - 0.05, 1.0), (0.04, 0.06, 0.16))
    kit.text("North door stencil", "GENERATOR", mat("white paint"), ((NDOOR[0] + NDOOR[1]) / 2, Y0 + 0.006, 2.3), size=0.08, rot=(math.pi / 2, 0, math.pi))
    # The east door, open outward onto the line track, his blood on the handle.
    hinge = reb.prim("sphere", "East door hinge", mat("black"), (X1 + 0.2, EDOOR[1], 1.05), (0.03, 0.03, 0.03))
    reb.prim("cube", "East door", door_m, (0.0, -0.45, 0.0), (0.05, 0.9, 2.1), bevel=0.01).parent = hinge
    reb.prim("cube", "East door handle", mat("steel"), (-0.05, -0.78, 0.0), (0.06, 0.04, 0.16)).parent = hinge
    kit.splat("Blood on the handle", mat("blood"), (-0.08, -0.78, 0.02), 0.05, rot=(0, math.pi / 2, 0), seed=3).parent = hinge
    hinge.rotation_euler = (0, 0, 1.3)
    kit.splat("Handprint on the frame", mat("old blood"), (X1 - 0.005, EDOOR[0] - 0.08, 1.15), 0.06, rot=(0, math.pi / 2, 0), seed=5, lumps=0.5)
    for i in range(6):
        t = i / 5
        kit.splat(f"Drip {i}", mat("old blood"), (2.0 + (X1 - 0.3 - 2.0) * t + rng.uniform(-0.1, 0.1), 2.0 + (2.65 - 2.0) * t + rng.uniform(-0.1, 0.1), 0.0), rng.uniform(0.025, 0.05), seed=40 + i, lumps=0.4)
    # Outside the east door: the line track, the long grass, a pylon's leg, the forest.
    reb.prim("cube", "Outside ground", mat("grass"), (X1 + 8.0, 2.6, -0.05), (16.0, 20.0, 0.1))
    kit.path_strip("Outside track", reb.mat_surface("Track dirt", [(0.0, (0.09, 0.07, 0.045)), (1.0, (0.17, 0.13, 0.09))], scale=6, bump=0.6), [(X1 + 0.2, 2.65), (X1 + 4.0, 2.9), (X1 + 14.0, 3.6)], lambda x, y: 0.0, width=0.6)
    kit.meadow(rng, 500, lambda r: (r.uniform(X1 + 0.6, X1 + 12), r.uniform(-4, 9)), lambda x, y: 0.0, mat("dead grass")).scale = (1, 1, 2.2)
    for dx, dy in ((-0.9, -0.9), (0.9, -0.9), (0.9, 0.9), (-0.9, 0.9)):
        kit.rod("Pylon leg", mat("iron"), (X1 + 7.0 + dx * 1.6, 0.5 + dy * 1.6, 0), (X1 + 7.0 + dx * 0.3, 0.5 + dy * 0.3, 14.0), 0.08, 6)
    tv, tf, bases = [], [], []
    for x, y in ((X1 + 5.0, 8.5), (X1 + 9.0, -4.5), (X1 + 12.0, 7.0), (X1 + 14.0, -1.0), (X1 + 3.5, -5.0)):
        bases.append((Vector((x, y, -0.2)), rng.uniform(13, 17)))
        reb.conifer(rng, bases[-1][0], bases[-1][1], tv, tf)
    reb.mesh_object("Pines outside", tv, tf, mat("needles"))
    reb.trunks("Pine trunks outside", mat("bark"), bases)
    reb.prim("cube", "Outside, south", mat("grass"), (2.8, Y1 + 6.0, -0.05), (14.0, 12.0, 0.1))
    tv, tf, bases = [], [], []
    for x, y in ((0.5, Y1 + 5.0), (4.0, Y1 + 6.5), (-2.5, Y1 + 3.5)):
        bases.append((Vector((x, y, -0.2)), rng.uniform(13, 16)))
        reb.conifer(rng, bases[-1][0], bases[-1][1], tv, tf)
    reb.mesh_object("Pines south", tv, tf, mat("needles"))
    reb.trunks("Pine trunks south", mat("bark"), bases)

    # ---- The breaker board along the west wall: slate, five breakers all down, labels.
    board = reb.prim("cube", "Breaker board", slate, (X0 + 0.04, 2.5, 1.45), (0.08, 2.6, 1.7))
    reb.prim("cube", "Board frame", mat("iron"), (X0 + 0.05, 2.5, 2.33), (0.1, 2.7, 0.06))
    reb.prim("cube", "Board frame", mat("iron"), (X0 + 0.05, 2.5, 0.58), (0.1, 2.7, 0.06))
    labels = ("SKYWAY LINE", "STATION 3", "MINE", "PUMP", "CAMP 4")
    # Once she closes them (day/events.ts "line-on"): handles up, a green lamp lit over each.
    down, up = [], []
    lamp_on = reb.mat_emit("Breaker lamp, on", (0.3, 1.0, 0.35), 12)
    for i, label in enumerate(labels):
        y = 1.45 + i * 0.52
        if abs(y - SPARK[1]) < 0.2:
            continue
        reb.prim("cube", f"Breaker {i}", cab_grey, (X0 + 0.16, y, 1.55), (0.16, 0.34, 0.5), bevel=0.01)
        handle = kit.rod(f"Breaker handle {i}", mat("black"), (X0 + 0.25, y, 1.55), (X0 + 0.42, y, 1.32), 0.025)
        knob = reb.prim("sphere", f"Handle knob {i}", mat("red paint"), (X0 + 0.43, y, 1.31), (0.06, 0.06, 0.06), segments=10)
        down += [handle, knob]
        up += [kit.rod(f"Breaker handle up {i}", mat("black"), (X0 + 0.25, y, 1.55), (X0 + 0.42, y, 1.78), 0.025),
               reb.prim("sphere", f"Handle knob up {i}", mat("red paint"), (X0 + 0.43, y, 1.79), (0.06, 0.06, 0.06), segments=10),
               reb.prim("sphere", f"Breaker lamp {i}", lamp_on, (X0 + 0.1, y, 2.12), (0.04, 0.04, 0.04), segments=8)]
        reb.prim("cube", f"Label {i}", mat("white paint"), (X0 + 0.09, y, 1.95), (0.01, 0.4, 0.09))
        kit.text(f"Label words {i}", label, mat("black"), (X0 + 0.096, y, 1.95), size=0.045, rot=(math.pi / 2, 0, math.pi / 2))
        down.append(kit.text(f"Off mark {i}", "OFF", mat("red paint"), (X0 + 0.096, y, 1.2), size=0.05, rot=(math.pi / 2, 0, math.pi / 2)))
    for ob in up:
        ob.hide_render = True

    def line(on):
        for ob in down:
            ob.hide_render = on
        for ob in up:
            ob.hide_render = not on
    room.state("line-on", line)
    # The contactor that shorted: blackened, its cover blown off, sparks still coming.
    reb.prim("cube", "Contactor", mat("black"), (X0 + 0.15, SPARK[1], 1.45), (0.14, 0.34, 0.42), bevel=0.01)
    for dy in (-0.08, 0.0, 0.08):
        reb.prim("cube", "Contact", copper, (X0 + 0.24, SPARK[1] + dy, 1.47), (0.04, 0.03, 0.09))
    reb.prim("cube", "Contactor cover", cab_grey, (X0 + 0.9, 2.2, 0.02), (0.3, 0.36, 0.03), rot=(0, 0, 0.7))
    kit.splat("Scorch up the board", scorch, (X0 + 0.085, SPARK[1], 1.8), 0.32, rot=(0, math.pi / 2, 0), seed=7, stretch=(1.0, 1.6), lumps=0.6)
    kit.splat("Scorch on the floor", scorch, (X0 + 0.5, SPARK[1] + 0.1, 0.0), 0.3, seed=8, lumps=0.6)
    spark_m = reb.mat_emit("Spark", (0.7, 0.85, 1.0), 25)
    sparks = []
    for i in range(3):
        sv, sf = [], []
        r2 = random.Random(100 + i)
        for _ in range(6):
            a = Vector((X0 + 0.27, SPARK[1] + r2.uniform(-0.08, 0.08), 1.47 + r2.uniform(-0.04, 0.04)))
            d = Vector((r2.uniform(0.03, 0.14), r2.uniform(-0.1, 0.1), r2.uniform(-0.16, 0.06)))
            b = a + d
            side = Vector((0, 0.0025, 0.0025))
            k = len(sv)
            sv += [tuple(a - side), tuple(a + side), tuple(b + side), tuple(b - side)]
            sf.append((k, k + 1, k + 2, k + 3))
        sparks.append(reb.mesh_object(f"Sparks {i}", sv, sf, spark_m, smooth=False))
    arc = reb.point("Arc flash", (X0 + 0.35, SPARK[1], 1.47), 25, (0.6, 0.8, 1.0), 0.05)
    # Cable trays overhead and the feeders out through the east wall.
    reb.prim("cube", "Cable tray", mat("iron"), (2.8, 2.5, H - 0.25), (3.6, 0.3, 0.05))
    for k, dy in enumerate((-0.08, 0.0, 0.08)):
        kit.rod(f"Feeder {k}", mat("black"), (X0 + 0.1, 2.5 + dy, H - 0.2), (X1 - 0.02, 2.5 + dy, H - 0.2), 0.025)
        kit.rod(f"Feeder drop {k}", mat("black"), (X0 + 0.1, 2.5 + dy, H - 0.2), (X0 + 0.1, 2.5 + dy, 2.36), 0.025)
    reb.prim("cube", "Feeder gland", mat("iron"), (X1 - 0.03, 2.5, H - 0.2), (0.06, 0.35, 0.15))

    # ---- The isolator on the south wall: the big lever down, padlocked.
    lx = 3.2
    reb.prim("cube", "Isolator box", cab_grey, (lx, Y1 - 0.15, 1.3), (0.6, 0.3, 0.9), bevel=0.02)
    lever_pivot = reb.prim("sphere", "Lever pivot", mat("iron"), (lx + 0.36, Y1 - 0.15, 1.45), (0.1, 0.1, 0.1))
    kit.rod("Lever", mat("red paint"), (lx + 0.36, Y1 - 0.15, 1.45), (lx + 0.36, Y1 - 0.75, 0.95), 0.035)
    reb.prim("cube", "Lever grip", mat("black"), (lx + 0.36, Y1 - 0.8, 0.9), (0.07, 0.18, 0.07))
    reb.prim("cube", "Hasp", mat("steel"), (lx + 0.36, Y1 - 0.45, 0.95), (0.04, 0.12, 0.03))
    reb.prim("cube", "Padlock", mat("yellow paint"), (lx + 0.36, Y1 - 0.47, 0.88), (0.05, 0.035, 0.07), bevel=0.01)
    reb.prim("cube", "Isolator sign", mat("white paint"), (lx, Y1 - 0.305, 1.4), (0.5, 0.01, 0.3))
    kit.text("Isolator words", "MAIN ISOLATOR", mat("red paint"), (lx, Y1 - 0.312, 1.47), size=0.05)
    kit.text("Isolator words 2", "SKYWAY LINE", mat("black"), (lx, Y1 - 0.312, 1.35), size=0.045)
    kit.text("Lever marks", "ON", mat("black"), (lx + 0.36, Y1 - 0.31, 1.75), size=0.05)
    kit.text("Lever marks 2", "OFF", mat("red paint"), (lx + 0.36, Y1 - 0.31, 1.0), size=0.05)
    reb.wall(reb.prim("cube", "Isolator footprint", None, (lx + 0.1, Y1 - 0.3, 0.5), (0.8, 0.6, 1.0))).hide_render = True
    # Warning signs: high voltage, the skull and bolt; a wiring diagram.
    for i, (x, z) in enumerate(((2.0, 1.4), (4.1, 1.75))):
        reb.prim("cube", f"Warning sign {i}", mat("yellow paint"), (x, Y1 - 0.01, z), (0.42, 0.01, 0.42))
        kit.text(f"Warning words {i}", "DANGER", mat("black"), (x, Y1 - 0.017, z + 0.13), size=0.07)
        kit.text(f"Warning bolt {i}", "Z", mat("black"), (x, Y1 - 0.017, z - 0.02), size=0.16)
        kit.text(f"Warning words b{i}", "11 000 VOLTS", mat("black"), (x, Y1 - 0.017, z - 0.15), size=0.045)
    reb.prim("cube", "Wiring diagram", mat("old paper"), (X1 - 0.01, 1.6, 1.5), (0.01, 0.7, 0.5))
    for i in range(5):
        reb.prim("cube", f"Diagram line {i}", mat("black"), (X1 - 0.018, 1.6, 1.32 + i * 0.08), (0.003, 0.55, 0.006))
    reb.prim("cube", "Diagram line v", mat("black"), (X1 - 0.018, 1.45, 1.5), (0.003, 0.006, 0.36))
    # His things: the burnt glove, the other glove, the torch, a meter, his tool bag.
    glove_m = reb.mat_surface("Burnt rubber", [(0.0, (0.01, 0.01, 0.01)), (0.6, (0.05, 0.03, 0.02)), (1.0, (0.3, 0.12, 0.03))], scale=20, rough=0.8, bump=0.5)
    glove = kit.join("Burnt glove", [
        reb.prim("cube", "palm", glove_m, (0, 0, 0.03), (0.16, 0.1, 0.05), bevel=0.02),
        reb.prim("cyl", "cuff", glove_m, (-0.16, 0, 0.04), (0.08, 0.08, 0.18), rot=(0, math.pi / 2, 0), segments=10),
    ] + [reb.prim("cube", "finger", glove_m, (0.12, -0.04 + k * 0.027, 0.025), (0.08, 0.022, 0.03), rot=(0, 0, (k - 1.5) * 0.15)) for k in range(4)])
    glove.location = (X0 + 0.65, 2.75, 0.0)
    glove.scale = (1.5, 1.5, 1.5)
    glove.rotation_euler = (0, 0, 2.6)
    reb.prim("cube", "Other glove", reb.mat_plain("Lineman's glove", (0.4, 0.2, 0.02), 0.8), (2.6, 3.4, 0.03), (0.3, 0.12, 0.05), rot=(0, 0, 0.4), bevel=0.02)
    reb.prim("cyl", "Torch", mat("black"), (2.2, 2.2, 0.04), (0.06, 0.06, 0.26), rot=(math.pi / 2, 0, 0.9), segments=12)
    reb.prim("cube", "Meter", mat("yellow paint"), (X0 + 0.95, 3.4, 0.05), (0.12, 0.2, 0.06), rot=(0, 0, 0.3))
    kit.rod("Meter lead", mat("red paint"), (X0 + 0.95, 3.3, 0.04), (X0 + 0.6, 3.0, 0.01), 0.004, 4)
    reb.prim("cube", "Tool bag", mat("canvas"), (X1 - 0.35, Y1 - 0.35, 0.15), (0.45, 0.25, 0.3), rot=(0, 0, 0.3), bevel=0.05)
    reb.wall(reb.prim("cube", "Tool bag footprint", None, (X1 - 0.35, Y1 - 0.35, 0.2), (0.5, 0.35, 0.4))).hide_render = True
    reb.prim("cube", "Stool", reb.mat_wood("Stool", (0.2, 0.14, 0.08)), (X1 - 0.5, 1.4, 0.3), (0.35, 0.35, 0.04))
    kit.splat("Burnt hand mark", scorch, (X0 + 0.085, SPARK[1] + 0.25, 1.35), 0.07, rot=(0, math.pi / 2, 0), seed=11, lumps=0.6)
    kit.web("Web", (X1 - 0.02, Y0 + 0.02, H - 0.02), 0.3, (-1, 1))

    # ---- The window: bars, the low sun coming through them.
    for i in range(4):
        x = WINDOW[0] + 0.1 + i * 0.2
        kit.rod(f"Window bar {i}", mat("iron"), (x, Y1 + 0.1, WINDOW[2]), (x, Y1 + 0.1, WINDOW[3]), 0.012)
    pane = reb.prim("cube", "Window glass", reb.mat_glass("Grimy glass", (0.55, 0.52, 0.42)), ((WINDOW[0] + WINDOW[1]) / 2, Y1 + 0.15, (WINDOW[2] + WINDOW[3]) / 2), (WINDOW[1] - WINDOW[0], 0.01, WINDOW[3] - WINDOW[2]))
    pane.visible_shadow = False

    # ---- Light: the sun through the window and the door, the arc's blue flashes.
    kit.time_light("afternoon", sun_heading=232, sun_energy=4.0)
    reb.spot("Sun through the window", (0.44, 6.04, 4.66), (3.3, 2.5, 0.0), 900, (1.0, 0.68, 0.4), 24, 0.2, 0.03)
    reb.spot("Daylight at the door", (X1 + 3.0, 2.65, 1.8), (2.2, 2.6, 0.0), 120, (0.85, 0.88, 1.0), 45, 0.8, 0.5)
    reb.point("Dim fill", (2.8, 2.5, 2.4), 1.0, (0.9, 0.8, 0.7), 0.5)

    anim = kit.Anim(16)

    def spark(k):
        on = k % 5 in (0, 1) or k in (7, 12)
        for i, s in enumerate(sparks):
            s.hide_render = not (on and (k + i) % 3 != 2)
        arc.data.energy = 30 if on else 0.0
    anim.custom(spark)

    # ---- What the game needs.
    room.door("generator", (NDOOR[0], Y0, NDOOR[1], Y0 + 0.6), arrive=(2.2, 2.1), face=(0, 1))
    room.door("line-track", (X1 - 0.6, EDOOR[0], X1, EDOOR[1]), arrive=(3.4, 2.65), face=(-1, 0))
    room.spot("line-on", (X0, 1.2, X0 + 0.8, 2.3))  # day/events.ts says what she sees and does here
    room.check((X0, 2.3, X0 + 0.8, 2.8), "A contactor, burnt black. It's still sparking off the batteries.\nThere's a scorched handprint beside it.")
    room.check((X0 + 0.4, 2.5, X0 + 1.0, 3.1), "A lineman's rubber glove. It's melted.")
    room.check((lx - 0.3, Y1 - 0.9, lx + 0.7, Y1), "MAIN ISOLATOR, SKYWAY LINE. The lever's down, and padlocked.\nNo power reaches the gondola until this goes up.")
    room.check((X1 - 0.6, EDOOR[0] - 0.4, X1, EDOOR[0]), "Blood on the door frame. He went out to the line track.")
    room.entry = "It smells of burnt rubber."
    room.export(anim)


build()
