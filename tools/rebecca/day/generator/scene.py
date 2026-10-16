"""The generator hut by the washout, afternoon.

What it tells: this diesel set powers the gondola's line, the ranger
station and the mine. Dale, the lineman who kept it running, lived out here
in the season: his cot is against the east wall. His log on the bench tells
the last night. The tank was low and nobody answered the radio about the
fuel. At two in the morning a dog went for him on the line track. He came
back in, bled into his pillow, and wrote that he couldn't stand. The set
ran dry at half past three and stopped. The fuel gauge is on E, the day
tank's sight glass is empty, and his jerrycan lies on its side with its cap
off and nothing in it. Oil from the engine has spread across the floor, and
his boot prints go through it to the back door, to the switch house. Only
the battery emergency lamp over the door still works, and it is failing.
Wasps got in at the window and died on the sill.

Metres: the floor is x 1.0-5.4, y 1.0-4.8, 2.8 high, block walls. The door
out to the washout is in the north wall at x 2.6-3.6, standing ajar. The
back door to the switch house is in the south wall at x 3.8-4.6. The
generator stands on its plinth along the west wall, x 1.25-2.35, y 1.9-4.3,
under a small high window (y 2.6-3.6). His cot is along the east wall; the
bench is against the south wall west of the back door.

Moving: the emergency lamp flickering, flies over the pillow, a strip of
rag in the draught at the door.
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

X0, X1, Y0, Y1, H = 1.0, 5.4, 1.0, 4.8, 2.8
NDOOR = (2.6, 3.6)
SDOOR = (3.8, 4.6)
WINDOW = (2.6, 3.6, 1.7, 2.3)   # y0, y1, z0, z1 in the west wall
GEN = (1.25, 2.35, 1.9, 4.3)


def build():
    rng = random.Random(29)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.ground("concrete")
    room.camera((5.25, 1.15, 2.45), (2.7, 4.6, 0.2), 190, "high in the north-east corner: the generator, the oil, the bench and the back door")
    room.camera((2.75, 4.62, 2.45), (4.7, 1.3, 0.5), 200, "high over the bench: the cot and its pillow, the open door, the emergency lamp")
    room.camera((5.25, 4.65, 2.4), (1.8, 1.6, 0.7), 195, "high in the south-east corner: the generator's panel on E, the window and its wasps")

    block = kit.dirtied(reb.mat_surface("Painted block", [(0.0, (0.28, 0.28, 0.25)), (0.6, (0.4, 0.39, 0.35)), (1.0, (0.25, 0.22, 0.17))], scale=2.5, bump=0.35), 0.6, scale=1.5)
    floor_m = kit.dirtied(mat("concrete"), 0.8, scale=0.8)
    ceiling_m = reb.mat_surface("Ceiling slab", [(0.0, (0.12, 0.12, 0.11)), (1.0, (0.22, 0.21, 0.2))], scale=3, bump=0.2)
    gen_green = reb.mat_surface("Generator green", [(0.0, (0.05, 0.1, 0.06)), (0.7, (0.09, 0.17, 0.1)), (1.0, (0.17, 0.12, 0.06))], scale=6, rough=0.45, bump=0.2)
    oil = reb.mat_plain("Engine oil", (0.012, 0.01, 0.008), 0.08)
    gauge_face = reb.mat_plain("Gauge face", (0.55, 0.53, 0.45), 0.4)
    pillow_m = reb.mat_surface("Bloody pillow", [(0.0, (0.5, 0.48, 0.42)), (0.5, (0.46, 0.43, 0.37)), (0.62, (0.22, 0.02, 0.01)), (1.0, (0.1, 0.005, 0.004))], scale=5, bump=0.15)
    wasp_m = reb.mat_surface("Wasp", [(0.0, (0.02, 0.02, 0.01)), (0.5, (0.35, 0.25, 0.02)), (1.0, (0.02, 0.02, 0.01))], scale=90, rough=0.5, bump=0.1)
    steel_door = reb.mat_surface("Door grey", [(0.0, (0.12, 0.14, 0.12)), (0.8, (0.2, 0.22, 0.2)), (1.0, (0.2, 0.1, 0.05))], scale=5, rough=0.5, bump=0.15)

    # ---- The shell: block walls, a stained slab, the ceiling; the two doorways and the window cut.
    kit.walls(X0, Y0, X1, Y1, H, block, openings=[
        ("n", NDOOR[0], NDOOR[1], 0.0, 2.1),
        ("s", SDOOR[0], SDOOR[1], 0.0, 2.1),
        ("w", WINDOW[0], WINDOW[1], WINDOW[2], WINDOW[3]),
    ], thick=0.2, floor=floor_m, ceiling=ceiling_m)
    kit.cracks("Floor cracks", mat("black"), (X0 + 0.2, Y0 + 0.2, X1 - 0.2, Y1 - 0.2), count=8, seed=2)
    kit.splat("Damp in the corner", reb.mat_plain("Damp", (0.08, 0.08, 0.06), 0.9), (X1 - 0.01, Y1 - 0.4, 0.4), 0.45, rot=(0, math.pi / 2, 0), seed=3, stretch=(1.0, 1.4))
    # The north door, steel, swung open outward, daylight through it.
    pivot = reb.prim("sphere", "North door hinge", mat("black"), (NDOOR[1], Y0 + 0.02, 1.05), (0.03, 0.03, 0.03))
    reb.prim("cube", "North door", steel_door, (-0.5, 0.0, 0.0), (1.0, 0.05, 2.1), bevel=0.01).parent = pivot
    reb.prim("cube", "North door bar", mat("steel"), (-0.85, 0.04, 0.0), (0.06, 0.04, 0.18)).parent = pivot
    pivot.rotation_euler = (0, 0, 1.25)
    # The back door to the switch house, shut, its warnings.
    reb.prim("cube", "Back door", steel_door, ((SDOOR[0] + SDOOR[1]) / 2, Y1 + 0.1, 1.05), (SDOOR[1] - SDOOR[0], 0.05, 2.1), bevel=0.01)
    reb.prim("cube", "Back door handle", mat("steel"), (SDOOR[0] + 0.1, Y1 + 0.05, 1.0), (0.04, 0.06, 0.16))
    reb.prim("cube", "Back door sign", mat("yellow paint"), ((SDOOR[0] + SDOOR[1]) / 2, Y1 + 0.065, 1.6), (0.5, 0.01, 0.34))
    kit.text("Back door sign words", "DANGER", mat("black"), ((SDOOR[0] + SDOOR[1]) / 2, Y1 + 0.058, 1.68), size=0.08)
    kit.text("Back door sign words 2", "11 000 V", mat("black"), ((SDOOR[0] + SDOOR[1]) / 2, Y1 + 0.058, 1.54), size=0.07)
    kit.text("Back door stencil", "SWITCH HOUSE", mat("white paint"), ((SDOOR[0] + SDOOR[1]) / 2, Y1 - 0.006, 2.3), size=0.08)
    # Outside the north door: the washout's grass and the trees; beyond the window, sky and pines.
    reb.prim("cube", "Outside ground", mat("grass"), (3.0, -6.0, -0.05), (30.0, 12.0, 0.1))
    reb.prim("cube", "Outside path", reb.mat_surface("Path dirt", [(0.0, (0.09, 0.07, 0.045)), (1.0, (0.17, 0.13, 0.09))], scale=6, bump=0.6), (3.1, -2.0, -0.03), (1.0, 4.0, 0.06))
    reb.prim("cube", "Outside west ground", mat("grass"), (-8.0, 3.0, -0.3), (16.0, 20.0, 0.1))
    tv, tf, bases = [], [], []
    for x, y in ((-4.0, 1.0), (-6.5, 4.5), (-3.5, 7.0), (0.5, -7.0), (5.5, -8.0), (-1.5, -5.5), (8.5, -5.0)):
        bases.append((Vector((x, y, -0.3)), rng.uniform(13, 17)))
        reb.conifer(rng, bases[-1][0], bases[-1][1], tv, tf)
    reb.mesh_object("Pines outside", tv, tf, mat("needles"))
    reb.trunks("Pine trunks outside", mat("bark"), bases)
    reb.prim("cube", "Outside, tank", mat("green paint"), (4.3, -0.9, 0.85), (2.0, 1.0, 1.0), bevel=0.3)

    # ---- The generator on its plinth: skid, engine, alternator, radiator, the panel on E.
    gx0, gx1, gy0, gy1 = GEN
    gc = (gx0 + gx1) / 2
    plinth = reb.prim("cube", "Plinth", mat("concrete"), (gc, (gy0 + gy1) / 2, 0.07), (gx1 - gx0 + 0.2, gy1 - gy0 + 0.2, 0.14))
    reb.wall(plinth)
    reb.prim("cube", "Skid", mat("iron"), (gc, (gy0 + gy1) / 2, 0.2), (gx1 - gx0, gy1 - gy0, 0.12))
    engine = reb.prim("cube", "Engine block", gen_green, (gc, 3.2, 0.72), (0.85, 1.2, 0.85), bevel=0.04)
    reb.mask(engine)
    reb.prim("cube", "Rocker cover", gen_green, (gc, 3.2, 1.22), (0.5, 1.0, 0.16), bevel=0.03)
    for i in range(6):
        reb.prim("cyl", f"Injector {i}", mat("steel"), (gc + 0.12, 2.75 + i * 0.18, 1.33), (0.04, 0.04, 0.08), segments=8)
    reb.prim("cube", "Manifold", mat("rust"), (gc + 0.4, 3.2, 1.0), (0.12, 1.0, 0.14))
    kit.rod("Exhaust riser", mat("rust"), (gc + 0.45, 3.2, 1.0), (gc + 0.45, 3.2, 2.0), 0.07, 10)
    kit.rod("Exhaust bend", mat("rust"), (gc + 0.45, 3.2, 2.0), (gc - 0.1, 3.2, 2.5), 0.07, 10)
    kit.rod("Exhaust stack", mat("rust"), (gc - 0.1, 3.2, 2.5), (gc - 0.1, 3.2, H + 0.1), 0.07, 10)
    kit.splat("Soot on the ceiling", mat("black"), (gc - 0.1, 3.2, H - 0.005), 0.4, rot=(math.pi, 0, 0), seed=8)
    alt = kit.rod("Alternator", gen_green, (gc, gy0 + 0.05, 0.72), (gc, 2.6, 0.72), 0.42, 20)
    reb.mask(alt)
    for i in range(5):
        reb.prim("cube", f"Alternator rib {i}", mat("iron"), (gc, 2.05 + i * 0.1, 0.72), (0.88, 0.025, 0.88), bevel=0.3)
    rad = reb.prim("cube", "Radiator", gen_green, (gc, gy1 - 0.2, 0.85), (gx1 - gx0, 0.32, 1.1), bevel=0.02)
    reb.mask(rad)
    for i in range(8):
        reb.prim("cube", f"Radiator fin {i}", mat("iron"), (gc, gy1 - 0.03, 0.4 + i * 0.12), (gx1 - gx0 - 0.15, 0.02, 0.03))
    reb.wall(reb.prim("cube", "Generator footprint", None, (gc, (gy0 + gy1) / 2, 0.7), (gx1 - gx0, gy1 - gy0, 1.4))).hide_render = True
    # The control panel, facing the room, its fuel gauge on E.
    panel = reb.prim("cube", "Control panel", gen_green, (gc + 0.2, 2.25, 1.45), (0.12, 0.62, 0.5), bevel=0.01)
    reb.mask(panel)
    for i, (y, z, angle_) in enumerate(((2.08, 1.55, 2.6), (2.25, 1.55, 0.4), (2.42, 1.55, 1.2))):
        reb.prim("cyl", f"Panel gauge {i}", gauge_face, (gc + 0.265, y, z), (0.13, 0.13, 0.02), rot=(0, math.pi / 2, 0), segments=16)
        reb.prim("cube", f"Panel needle {i}", mat("red paint") if i == 0 else mat("black"), (gc + 0.278, y, z), (0.003, 0.055, 0.006), rot=(angle_, 0, 0))
    kit.text("Fuel label", "FUEL", mat("white paint"), (gc + 0.268, 2.08, 1.44), size=0.035, rot=(math.pi / 2, 0, math.pi / 2))
    kit.text("Empty mark", "E", mat("red paint"), (gc + 0.268, 2.03, 1.6), size=0.035, rot=(math.pi / 2, 0, math.pi / 2))
    reb.prim("cyl", "Start button", mat("green paint"), (gc + 0.27, 2.15, 1.3), (0.06, 0.06, 0.03), rot=(0, math.pi / 2, 0), segments=12)
    reb.prim("cyl", "Stop button", mat("red paint"), (gc + 0.27, 2.35, 1.3), (0.06, 0.06, 0.03), rot=(0, math.pi / 2, 0), segments=12)
    kit.text("Maker's plate", "ARKLAY POWER  75 kVA", mat("steel"), (gc + 0.43, 3.2, 0.55), size=0.05, rot=(math.pi / 2, 0, math.pi / 2))
    # The day tank on the north wall, its sight glass empty, the line down to the engine.
    reb.prim("cube", "Day tank", mat("rust"), (1.7, Y0 + 0.2, 1.85), (0.9, 0.36, 0.5), bevel=0.02)
    reb.prim("cube", "Sight glass", mat("glass"), (2.17, Y0 + 0.2, 1.85), (0.02, 0.05, 0.42))
    kit.text("Day tank words", "DAY TANK", mat("white paint"), (1.7, Y0 + 0.385, 1.9), size=0.06, rot=(math.pi / 2, 0, math.pi))
    kit.rod("Fuel line", mat("iron"), (1.5, Y0 + 0.25, 1.6), (1.5, gy0 + 0.6, 0.9), 0.015)
    kit.rod("Fuel line in", mat("iron"), (1.2, Y0 + 0.05, 1.95), (1.4, Y0 + 0.2, 1.95), 0.015)
    # Oil across the floor, his boot prints through it to the back door; the empty jerrycan.
    kit.splat("Oil under the engine", oil, (gc + 0.5, 3.2, 0.0), 0.6, seed=11, stretch=(1.0, 1.6), lumps=0.5)
    kit.splat("Oil run", oil, (gc + 1.1, 3.6, 0.0), 0.35, seed=12, stretch=(1.6, 0.7), lumps=0.5)
    for i in range(7):
        t = i / 6
        x = 2.9 + (SDOOR[0] + 0.35 - 2.9) * t + (0.1 if i % 2 else -0.1)
        y = 3.4 + (Y1 - 0.25 - 3.4) * t
        kit.splat(f"Oily bootprint {i}", oil, (x, y, 0.0), 0.06, seed=30 + i, stretch=(0.6, 1.4), lumps=0.2)
    can = kit.join("Jerrycan", [
        reb.prim("cube", "can", mat("red paint"), (0, 0, 0.0), (0.47, 0.17, 0.34), bevel=0.02),
        reb.prim("cube", "handle", mat("red paint"), (-0.05, 0, 0.21), (0.22, 0.05, 0.05)),
        reb.prim("cyl", "spout", mat("steel"), (0.2, 0, 0.21), (0.06, 0.06, 0.06), segments=10),
    ])
    can.location = (2.75, 2.2, 0.09)
    can.rotation_euler = (math.pi / 2, 0, 0.6)
    reb.prim("cyl", "Jerrycan cap", mat("steel"), (3.1, 2.55, 0.02), (0.07, 0.07, 0.03), segments=10)
    reb.prim("cone", "Funnel", mat("tin"), (2.5, 1.55, 0.12), (0.25, 0.25, 0.24), segments=14, top=0.15, rot=(1.4, 0, 2.2))

    # ---- The bench against the south wall: his log, his tools; the calendar over it.
    bench = kit.table("Bench", reb.mat_wood("Bench top", (0.2, 0.14, 0.08)), (3.0, Y1 - 0.33, 0.0), size=(1.4, 0.6, 0.9), legs_mat=mat("iron"))
    reb.wall(bench)
    reb.mask(bench)
    reb.prim("cube", "Log book", mat("old paper"), (2.75, Y1 - 0.38, 0.912), (0.32, 0.24, 0.02), rot=(0, 0, 0.12))
    reb.prim("cube", "Log book spine", mat("dark wood"), (2.75, Y1 - 0.38, 0.915), (0.02, 0.24, 0.025), rot=(0, 0, 0.12))
    kit.rod("Pencil", mat("yellow paint"), (2.62, Y1 - 0.5, 0.925), (2.78, Y1 - 0.56, 0.925), 0.006, 6)
    kit.splat("Blood on the log", mat("blood"), (2.85, Y1 - 0.34, 0.925), 0.035, seed=14)
    tb = reb.prim("cube", "Toolbox", mat("red paint"), (3.4, Y1 - 0.3, 1.0), (0.5, 0.22, 0.2), bevel=0.01)
    reb.prim("cube", "Toolbox lid", mat("red paint"), (3.4, Y1 - 0.16, 1.18), (0.5, 0.02, 0.2), rot=(0.4, 0, 0))
    for i in range(4):
        reb.prim("cube", f"Spanner {i}", mat("steel"), (3.05 + i * 0.09, Y1 - 0.52, 0.91), (0.22, 0.025, 0.008), rot=(0, 0, 1.3 + rng.uniform(-0.2, 0.2)))
    reb.cloth("Oily rag", reb.mat_plain("Oily rag", (0.12, 0.1, 0.07), 0.8), (3.55, Y1 - 0.55, 0.915), (0.25, 0.2), lumps=0.02, seed=5)
    reb.prim("cyl", "Mug", reb.mat_plain("Mug enamel", (0.5, 0.52, 0.55), 0.35), (2.4, Y1 - 0.25, 0.96), (0.09, 0.09, 0.1), segments=14)
    reb.prim("cube", "Radio", reb.mat_plain("Radio olive", (0.07, 0.08, 0.05), 0.5), (3.6, Y1 - 0.25, 1.22), (0.3, 0.16, 0.2), bevel=0.01)
    kit.rod("Radio aerial", mat("steel"), (3.7, Y1 - 0.25, 1.32), (3.75, Y1 - 0.25, 1.75), 0.004, 4)
    # Pegboard: the tools' outlines, two of them gone.
    reb.prim("cube", "Pegboard", reb.mat_plain("Pegboard", (0.3, 0.24, 0.15), 0.85), (3.0, Y1 - 0.015, 1.55), (1.3, 0.02, 0.7))
    for i, (x, z, w, hh, gone) in enumerate(((2.55, 1.6, 0.06, 0.45, False), (2.75, 1.55, 0.05, 0.35, True), (2.95, 1.62, 0.07, 0.4, False), (3.2, 1.55, 0.25, 0.08, True), (3.45, 1.65, 0.05, 0.4, False))):
        reb.prim("cube", f"Tool outline {i}", mat("white paint") if gone else mat("black"), (x, Y1 - 0.03, z), (w, 0.006, hh))
    # The calendar: July 1998, the days crossed off to the 23rd.
    reb.prim("cube", "Calendar", mat("paper"), (2.2, Y1 - 0.015, 1.55), (0.42, 0.01, 0.6))
    reb.prim("cube", "Calendar picture", reb.mat_plain("Calendar picture", (0.15, 0.3, 0.4), 0.8), (2.2, Y1 - 0.022, 1.7), (0.38, 0.004, 0.24))
    kit.text("Calendar month", "JULY 1998", mat("black"), (2.2, Y1 - 0.026, 1.53), size=0.04)
    for d in range(31):
        r_, c_ = divmod(d + 3, 7)
        x = 2.36 - c_ * 0.052
        z = 1.47 - r_ * 0.045
        if d < 23:
            reb.prim("cube", f"Cross {d}", mat("red paint"), (x, Y1 - 0.026, z), (0.035, 0.003, 0.006), rot=(0, 0.7, 0))
        else:
            reb.prim("cube", f"Day {d}", mat("black"), (x, Y1 - 0.026, z), (0.012, 0.003, 0.012))

    # ---- His cot along the east wall, the pillow soaked, flies over it.
    cot_x0, cot_x1, cot_y0, cot_y1 = X1 - 0.8, X1 - 0.1, 1.3, 3.3
    cot = kit.join("Cot frame", [
        kit.rod("rail", mat("iron"), (cot_x0, cot_y0, 0.42), (cot_x0, cot_y1, 0.42), 0.02),
        kit.rod("rail", mat("iron"), (cot_x1, cot_y0, 0.42), (cot_x1, cot_y1, 0.42), 0.02),
        kit.rod("leg", mat("iron"), (cot_x0, cot_y0 + 0.1, 0.0), (cot_x1, cot_y0 + 0.4, 0.42), 0.015),
        kit.rod("leg", mat("iron"), (cot_x1, cot_y0 + 0.1, 0.0), (cot_x0, cot_y0 + 0.4, 0.42), 0.015),
        kit.rod("leg", mat("iron"), (cot_x0, cot_y1 - 0.1, 0.0), (cot_x1, cot_y1 - 0.4, 0.42), 0.015),
        kit.rod("leg", mat("iron"), (cot_x1, cot_y1 - 0.1, 0.0), (cot_x0, cot_y1 - 0.4, 0.42), 0.015),
    ])
    reb.wall(reb.prim("cube", "Cot footprint", None, ((cot_x0 + cot_x1) / 2, (cot_y0 + cot_y1) / 2, 0.25), (cot_x1 - cot_x0, cot_y1 - cot_y0, 0.5))).hide_render = True
    reb.prim("cube", "Cot canvas", mat("canvas"), ((cot_x0 + cot_x1) / 2, (cot_y0 + cot_y1) / 2, 0.42), (cot_x1 - cot_x0, cot_y1 - cot_y0, 0.02))
    reb.cloth("Blanket thrown back", reb.mat_stripes("Grey blanket", [(0.12, 0.12, 0.11), (0.2, 0.2, 0.18), (0.12, 0.12, 0.11), (0.3, 0.06, 0.04)], across=8, axis="Y"), ((cot_x0 + cot_x1) / 2, 2.75, 0.5), (0.9, 1.0), rot=(0, 0, 0.1), lumps=0.07, seed=4)
    pillow = reb.prim("sphere", "Pillow", pillow_m, ((cot_x0 + cot_x1) / 2, cot_y0 + 0.25, 0.5), (0.55, 0.36, 0.13), segments=16)
    kit.splat("Blood on the canvas", mat("old blood"), ((cot_x0 + cot_x1) / 2 - 0.05, cot_y0 + 0.6, 0.435), 0.18, seed=15, stretch=(1.0, 1.5))
    kit.splat("Blood dripped under", mat("old blood"), ((cot_x0 + cot_x1) / 2 - 0.1, cot_y0 + 0.5, 0.0), 0.15, seed=16)
    for i in range(5):
        reb.prim("cube", f"Wrapper {i}", mat("white paint"), (cot_x0 - 0.3 + rng.uniform(-0.25, 0.2), 1.8 + rng.uniform(-0.4, 0.5), 0.003), (0.08, 0.06, 0.003), rot=(0, 0, rng.uniform(0, 3)))
    reb.cloth("Torn shirt sleeve", mat("khaki"), (cot_x0 - 0.35, 1.6, 0.02), (0.4, 0.15), rot=(0, 0, 0.7), lumps=0.03, seed=7)
    kit.splat("Sleeve blood", mat("old blood"), (cot_x0 - 0.35, 1.6, 0.04), 0.09, seed=17)
    reb.prim("cyl", "Bucket", mat("tin"), (X1 - 0.3, 3.75, 0.17), (0.3, 0.3, 0.34), segments=14)
    for i, (x, y, r) in enumerate(((X1 - 0.5, 4.3, 0.3), (X1 - 0.3, 4.5, -0.2))):
        reb.prim("cube", f"Work boot {i}", mat("rubber"), (x, y, 0.07), (0.3, 0.12, 0.14), rot=(0, 0, r), bevel=0.03)
    reb.prim("cube", "Coat hook", mat("iron"), (X1 - 0.02, 3.9, 1.7), (0.03, 0.4, 0.04))
    reb.cloth("Hanging coat", reb.mat_plain("Lineman's coat", (0.35, 0.2, 0.04), 0.8), (X1 - 0.07, 3.9, 1.3), (0.8, 0.5), rot=(0, math.pi / 2, 0), lumps=0.05, seed=9)
    kit.text("Coat words", "ARKLAY POWER", mat("black"), (X1 - 0.12, 3.9, 1.35), size=0.045, rot=(math.pi / 2, 0, -math.pi / 2))

    # ---- The window over the generator: dead wasps on the sill, a nest in the corner.
    reb.prim("cube", "Window glass", reb.mat_glass("Grimy glass", (0.5, 0.52, 0.42)), (X0 - 0.15, (WINDOW[0] + WINDOW[1]) / 2, (WINDOW[2] + WINDOW[3]) / 2), (0.01, WINDOW[1] - WINDOW[0], WINDOW[3] - WINDOW[2]))
    reb.prim("cube", "Window bar", mat("iron"), (X0 - 0.12, (WINDOW[0] + WINDOW[1]) / 2, (WINDOW[2] + WINDOW[3]) / 2), (0.02, 0.03, WINDOW[3] - WINDOW[2]))
    reb.prim("cube", "Sill", mat("concrete"), (X0 + 0.03, (WINDOW[0] + WINDOW[1]) / 2, WINDOW[2] - 0.02), (0.14, WINDOW[1] - WINDOW[0] + 0.1, 0.04))
    wv, wf = [], []
    for i in range(16):
        c = Vector((X0 + rng.uniform(-0.02, 0.08), rng.uniform(WINDOW[0] + 0.05, WINDOW[1] - 0.05), WINDOW[2] + 0.005))
        reb.box(wv, wf, c, (0.02, 0.008, 0.008), rot=rng.uniform(0, 3))
    reb.mesh_object("Dead wasps", wv, wf, wasp_m, smooth=False)
    nest = reb.prim("sphere", "Wasp nest", reb.mat_surface("Nest paper", [(0.0, (0.2, 0.17, 0.12)), (1.0, (0.35, 0.3, 0.22))], scale=30, bump=0.6), (X0 + 0.18, Y0 + 0.2, H - 0.18), (0.28, 0.26, 0.3), segments=14)
    kit.web("Web", (X1 - 0.02, Y0 + 0.02, H - 0.02), 0.35, (-1, 1))
    kit.web("Web", (X0 + 0.02, Y1 - 0.02, H - 0.02), 0.3, (1, -1))

    # ---- Light: the low sun's shaft through the window, daylight at the door, the failing lamp.
    kit.time_light("afternoon", sun_heading=232, sun_energy=4.0)
    reb.spot("Sun through the window", (X0 - 4.0, 3.1, 3.6), (4.2, 3.0, 0.9), 500, (1.0, 0.72, 0.45), 24, 0.25, 0.05)
    reb.spot("Daylight at the door", (3.1, Y0 - 2.5, 1.8), (3.4, 2.2, 0.0), 120, (0.8, 0.85, 1.0), 45, 0.8, 0.5)
    lamp_m = reb.mat_emit("Emergency lamp", (1.0, 0.92, 0.78), 12)
    reb.prim("cube", "Emergency lamp box", mat("white paint"), (3.1, Y0 + 0.08, 2.4), (0.45, 0.14, 0.16), bevel=0.01)
    for dx in (-0.16, 0.16):
        reb.prim("cyl", "Lamp head", lamp_m, (3.1 + dx, Y0 + 0.2, 2.33), (0.1, 0.1, 0.08), rot=(1.1, 0, 0), segments=12)
    led_m = reb.mat_emit("Charge LED", (1.0, 0.1, 0.05), 20)
    reb.prim("sphere", "Charge LED", led_m, (3.1, Y0 + 0.16, 2.44), (0.015, 0.015, 0.015), segments=8)
    lamp = reb.spot("Emergency lamp light", (3.1, Y0 + 0.3, 2.3), (3.2, 3.4, 0.0), 120, (1.0, 0.9, 0.75), 120, 0.6, 0.1)
    fill = reb.point("Lamp spill", (3.1, Y0 + 0.4, 2.2), 6, (1.0, 0.9, 0.75), 0.2)
    # Once the generator runs (day/events.ts "generator-on"): the hut's own
    # light, a caged bulkhead lamp in the middle of the ceiling, comes on.
    reb.prim("cyl", "Bulkhead lamp base", mat("iron"), (3.4, 2.9, H - 0.04), (0.22, 0.22, 0.06), segments=12)
    glass_off = reb.mat_plain("Bulkhead glass, off", (0.35, 0.33, 0.28), 0.3)
    glass_on = reb.mat_emit("Bulkhead glass, on", (1.0, 0.85, 0.6), 15)
    bulkhead = reb.prim("sphere", "Bulkhead glass", glass_off, (3.4, 2.9, H - 0.12), (0.16, 0.16, 0.12), segments=12)
    for k in range(3):
        kit.rod("Bulkhead cage", mat("iron"), (3.4 - 0.09 + k * 0.09, 2.9 - 0.09, H - 0.06), (3.4 - 0.09 + k * 0.09, 2.9 + 0.09, H - 0.2), 0.006, 4)
    mains = reb.point("Mains light", (3.4, 2.9, H - 0.3), 160, (1.0, 0.82, 0.55), 0.15)
    mains.hide_render = True

    def power(on):
        bulkhead.data.materials[0] = glass_on if on else glass_off
        mains.hide_render = not on
    room.state("generator-on", power)

    anim = kit.Anim(16)
    anim.flicker(lamp, lamp_m, depth=0.5, dropouts=4)
    anim.flicker(fill, None, depth=0.5, dropouts=0)
    anim.flies(((cot_x0 + cot_x1) / 2, cot_y0 + 0.35, 0.55), count=8, radius=0.3)
    rag = reb.prim("cube", "Rag on the door", reb.mat_plain("Rag", (0.3, 0.28, 0.22), 0.9), (0, 0, -0.18), (0.01, 0.06, 0.36))
    tie = reb.prim("sphere", "Rag knot", mat("black"), (NDOOR[1] - 0.05, Y0 + 0.12, 1.5), (0.02, 0.02, 0.02))
    rag.parent = tie
    anim.swing(tie, axis=1, degrees=14)

    # ---- What the game needs.
    room.door("washout", (NDOOR[0], Y0, NDOOR[1], Y0 + 0.6), arrive=(3.1, 2.0), face=(0, 1))
    room.door("switch", (SDOOR[0], Y1 - 0.6, SDOOR[1], Y1), arrive=(4.2, 3.6), face=(0, -1))
    room.spot("generator-on", (gx1, 1.9, gx1 + 0.6, 2.6))  # day/events.ts says what she sees and does here
    room.check((1.2, Y0, 2.4, 1.6), "The day tank. The sight glass is empty.")
    # The can lies where she stands to fuel the generator: its check is its far end, clear of the spot.
    room.check((2.95, 1.8, 3.35, 2.6), "A jerrycan on its side, the cap off. Not a drop in it.")
    room.check((2.3, Y1 - 0.9, 3.0, Y1 - 0.6), "His log. 23 JUL 21.40, TANK LOW, NO ANSWER ON FUEL.\n24 JUL 02.10, DOG ON THE LINE TRACK. BIT ME BAD. LYING DOWN.\nThe last line is just a smear. GEN STOPPED 3.30. CANT STAND.")
    room.check((1.9, Y1 - 0.6, 2.5, Y1), "July 1998. Crossed off up to the 23rd.")
    room.check((cot_x0 - 0.6, cot_y0, cot_x0, cot_y0 + 1.0), "His cot. The pillow's soaked through with blood.\nThe flies have found it.")
    room.check((X0 + 1.4, WINDOW[0], X0 + 1.9, WINDOW[1]), "Dead wasps all along the sill.")
    room.check((SDOOR[0], Y1 - 0.9, SDOOR[1], Y1 - 0.6), "Oily boot prints, going out the back. To the switch house.")
    room.entry = "Cold. It hasn't run for hours."
    room.export(anim)


build()
