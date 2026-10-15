"""The operator's booth at the gondola's upper station, morning.

What it tells: Hal ran the gondola. Something went wrong before dawn and he
chalked it up as it happened, the way he was trained: the power went at
4:50, the drive cog sheared, a fuse blew. Then something came at the
window. He was bitten: he dressed his own hand from the first aid box and
the bloody gauze is on the floor, and his blood drips from the desk to the
door, where his hand is on the frame. His coffee went over, his chair went
over, the phone was dropped and left hanging. He took the key with him.
The poster by the door still sells the view, but someone has scratched the
eyes out of the smiling family on it.

Metres: the floor is x 1.0-4.2, y 1.0-3.6, 2.4 high. The door is in the
south wall at x 2.6-3.5, out onto the platform. The control desk runs under
the big west window, which looks out over the platform to the car. Where
she saves: his typewriter on a stand against the north wall, and the item
box along the east wall, under the fuse box and the phone.

Moving: the phone's handset turning on its cord; the strip light failing;
the heater's glow.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
from kit import mat  # noqa: E402
from mathutils import Vector  # noqa: E402

X0, X1, Y0, Y1, H = 1.0, 4.2, 1.0, 3.6, 2.4
DOOR = (2.6, 3.5)
WINDOW = (1.35, 3.25, 1.0, 1.95)   # y0, y1, z0, z1 in the west wall


def build():
    rng = random.Random(41)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.camera((4.05, 3.45, 2.25), (1.6, 1.6, 0.6), 200, "high over the door: the desk under the holed window, the tipped chair, the duty board")
    room.camera((1.15, 1.15, 2.25), (3.6, 3.3, 0.6), 200, "high in the north-west corner: the fuse box, the phone, the poster, the blood to the door")

    panel = kit.boards("Panelling", (0.2, 0.22, 0.17), width=0.16, grime=0.7)
    wainscot = kit.boards("Wainscot", (0.13, 0.09, 0.06), width=0.1, grime=0.6)
    lino = reb.mat_surface("Lino", [(0.0, (0.05, 0.04, 0.03)), (0.5, (0.13, 0.1, 0.06)), (1.0, (0.08, 0.06, 0.04))], scale=4, rough=0.45, bump=0.25)
    console = reb.mat_surface("Console grey", [(0.0, (0.12, 0.13, 0.12)), (0.7, (0.22, 0.23, 0.21)), (1.0, (0.16, 0.1, 0.06))], scale=7, rough=0.45, bump=0.15)
    chalkboard = reb.mat_surface("Chalkboard", [(0.0, (0.04, 0.06, 0.05)), (1.0, (0.1, 0.12, 0.1))], scale=6, rough=0.9, bump=0.05)
    chalk = reb.mat_plain("Chalk", (0.62, 0.62, 0.58), 0.95)
    coffee = reb.mat_plain("Coffee", (0.05, 0.025, 0.01), 0.1)
    frame_m = reb.mat_wood("Frame", (0.18, 0.12, 0.07))
    red = mat("red paint")
    yellow = mat("yellow paint")
    gauze = reb.mat_surface("Bloody gauze", [(0.0, (0.5, 0.48, 0.42)), (0.55, (0.45, 0.4, 0.35)), (0.7, (0.25, 0.02, 0.01)), (1.0, (0.12, 0.005, 0.004))], scale=18, bump=0.2)

    # ---- The shell: panelled walls over a dark wainscot, the door and the window cut, lino, a boarded ceiling on beams.
    kit.walls(X0, Y0, X1, Y1, H, panel, openings=[
        ("s", DOOR[0], DOOR[1], 0.0, 2.05),
        ("w", WINDOW[0], WINDOW[1], WINDOW[2], WINDOW[3]),
    ], floor=lino, ceiling=kit.boards("Ceiling boards", (0.16, 0.13, 0.09), width=0.12))
    for side, at, size in (("n", (2.6, Y0 + 0.01, 0.45), (3.4, 0.02, 0.9)), ("e", (X1 - 0.01, 2.3, 0.45), (0.02, 2.8, 0.9))):
        reb.prim("cube", "Wainscot", wainscot, at, size)
    reb.prim("cube", "Wainscot", wainscot, ((X0 + DOOR[0]) / 2, Y1 - 0.01, 0.45), (DOOR[0] - X0, 0.02, 0.9))
    reb.prim("cube", "Wainscot", wainscot, ((X1 + DOOR[1]) / 2, Y1 - 0.01, 0.45), (X1 - DOOR[1], 0.02, 0.9))
    for x in (1.7, 2.6, 3.5):
        reb.prim("cube", "Ceiling beam", frame_m, (x, (Y0 + Y1) / 2, H - 0.06), (0.1, Y1 - Y0 + 0.2, 0.12))
    # Conduit along the top of the east wall to the fuse box, and down.
    kit.rod("Conduit", mat("rust"), (X1 - 0.03, Y0 + 0.05, 2.15), (X1 - 0.03, Y1 - 0.05, 2.15), 0.018)
    kit.rod("Conduit drop", mat("rust"), (X1 - 0.03, 1.65, 2.15), (X1 - 0.03, 1.65, 1.78), 0.018)
    # Damp: a water stain spreading down from the ceiling's corner.
    kit.splat("Damp", reb.mat_plain("Damp", (0.06, 0.06, 0.04), 0.9), (X1 - 0.008, 1.3, 2.05), 0.35, rot=(0, math.pi / 2, 0), seed=31, stretch=(1.6, 1.0), lumps=0.5)
    # The door swung out against the outside wall, and its frame.
    reb.prim("cube", "Door", mat("green paint"), (DOOR[1] + 0.45, Y1 + 0.16, 1.02), (0.9, 0.05, 2.04))
    for x in (DOOR[0] - 0.04, DOOR[1] + 0.04):
        reb.prim("cube", "Door frame", frame_m, (x, Y1 - 0.02, 1.03), (0.07, 0.09, 2.06))
    reb.prim("cube", "Door head", frame_m, ((DOOR[0] + DOOR[1]) / 2, Y1 - 0.02, 2.08), (DOOR[1] - DOOR[0] + 0.14, 0.09, 0.07))
    # His hand on the frame, and where it slid down.
    kit.splat("Handprint", mat("blood"), (DOOR[0] - 0.08, Y1 - 0.07, 1.22), 0.06, rot=(math.pi / 2, 0, 0), seed=3, lumps=0.5)
    reb.prim("cube", "Smear", mat("old blood"), (DOOR[0] - 0.08, Y1 - 0.068, 0.97), (0.045, 0.004, 0.45), rot=(0, 0.06, 0))
    # Window glass, holed from outside: a star of cracks, glass in on the desk.
    for i, (y0, y1) in enumerate(((WINDOW[0], 2.28), (2.32, WINDOW[1]))):
        reb.prim("cube", f"Window pane {i}", reb.mat_glass("Grimy glass", (0.5, 0.55, 0.5)), (X0 - 0.06, (y0 + y1) / 2, (WINDOW[2] + WINDOW[3]) / 2), (0.01, y1 - y0, WINDOW[3] - WINDOW[2]))
    reb.prim("cube", "Window mullion", frame_m, (X0 - 0.06, 2.3, (WINDOW[2] + WINDOW[3]) / 2), (0.05, 0.05, WINDOW[3] - WINDOW[2]))
    reb.prim("cube", "Window sill", frame_m, (X0 - 0.02, 2.3, WINDOW[2] - 0.02), (0.14, WINDOW[1] - WINDOW[0] + 0.1, 0.04))
    hub = Vector((X0 - 0.05, 1.85, 1.55))
    for i in range(11):
        a = 2 * math.pi * i / 11 + rng.uniform(-0.2, 0.2)
        d = Vector((0, math.cos(a), math.sin(a))) * rng.uniform(0.15, 0.42)
        kit.rod("Crack", reb.mat_plain("Crack", (0.75, 0.78, 0.8), 0.3), hub, hub + d, 0.002, 4)
    kit.splat("Hole", mat("black"), (X0 - 0.045, 1.85, 1.55), 0.05, rot=(0, math.pi / 2, 0), seed=9, lumps=0.7)
    kit.shards("Glass on the desk", (X0 + 0.25, 1.9, 0.93), spread=0.4, count=18, seed=4)
    kit.shards("Glass on the floor", (X0 + 0.75, 1.9, 0.0), spread=0.5, count=12, seed=6)
    # Outside the window: the platform's edge and the morning beyond.
    reb.prim("cube", "Outside, platform", mat("concrete"), (X0 - 3.0, 2.3, -0.05), (5.0, 8.0, 0.1))
    reb.prim("cube", "Outside, rail", mat("rust"), (X0 - 3.5, 2.3, 1.0), (0.06, 8.0, 0.06))
    reb.prim("cube", "Outside, gondola", mat("red paint"), (X0 - 4.5, 3.4, 1.6), (2.2, 1.8, 1.8), bevel=0.2)
    reb.prim("cube", "Outside, far mountain", mat("rock"), (X0 - 40, 2.3, 4.0), (1.0, 120, 30))
    # Out of the door: the platform's concrete, its rail, the bullwheel's housing.
    reb.prim("cube", "Outside, platform south", mat("concrete"), (2.0, Y1 + 4.0, -0.05), (12.0, 8.0, 0.1))
    reb.prim("cube", "Outside, rail south", mat("rust"), (2.0, Y1 + 5.5, 1.0), (12.0, 0.06, 0.06))
    reb.prim("cube", "Outside, wheel house", mat("tin"), (1.2, Y1 + 3.5, 1.6), (2.4, 1.6, 3.2))

    # ---- The control desk under the window: dials, levers, the empty key switch, the stop button.
    desk = reb.prim("cube", "Control desk", console, (X0 + 0.32, 2.3, 0.45), (0.6, 2.1, 0.9), bevel=0.01)
    reb.mask(reb.wall(desk))
    reb.prim("cube", "Desk slope", console, (X0 + 0.32, 2.3, 0.94), (0.62, 2.12, 0.06), rot=(0, -0.25, 0))
    for i, y in enumerate((1.6, 1.85, 2.1, 2.35)):
        reb.prim("cyl", f"Gauge {i}", reb.mat_plain("Gauge face", (0.5, 0.48, 0.4), 0.4), (X0 + 0.35, y, 1.02), (0.11, 0.11, 0.02), rot=(0, -0.25 + math.pi / 2, 0), segments=16)
        reb.prim("cube", f"Needle {i}", mat("black"), (X0 + 0.34, y, 1.03), (0.005, 0.045, 0.003), rot=(rng.uniform(-1.2, -0.2), 0, 0))
    for i, y in enumerate((2.75, 2.9, 3.05)):
        reb.prim("cyl", f"Lever {i}", mat("steel"), (X0 + 0.42, y, 1.06), (0.025, 0.025, 0.22), rot=(0, -0.6 if i != 1 else 0.4, 0))
        reb.prim("sphere", f"Lever knob {i}", mat("black"), (X0 + 0.42 + (0.06 if i != 1 else -0.04), y, 1.16), (0.05, 0.05, 0.05))
    reb.prim("cyl", "Stop button", red, (X0 + 0.42, 3.22, 1.0), (0.09, 0.09, 0.05), segments=16)
    reb.prim("cyl", "Stop collar", yellow, (X0 + 0.42, 3.22, 0.98), (0.14, 0.14, 0.02), segments=16)
    reb.prim("cyl", "Key switch", mat("steel"), (X0 + 0.42, 1.35, 1.0), (0.06, 0.06, 0.03), segments=12)
    reb.prim("cube", "Empty keyway", mat("black"), (X0 + 0.42, 1.35, 1.016), (0.012, 0.03, 0.005))
    # The radio, a clipboard of run sheets, his coffee over, a photo propped against the glass.
    reb.prim("cube", "Radio", reb.mat_plain("Radio olive", (0.07, 0.08, 0.05), 0.5), (X0 + 0.3, 1.45, 1.06), (0.3, 0.22, 0.16), rot=(0, 0, 0.1), bevel=0.01)
    reb.prim("cyl", "Radio dial", mat("steel"), (X0 + 0.46, 1.45, 1.08), (0.05, 0.05, 0.01), rot=(0, math.pi / 2, 0), segments=12)
    reb.prim("cube", "Clipboard", frame_m, (X0 + 0.28, 2.0, 0.97), (0.25, 0.33, 0.01), rot=(0, -0.25, 0.15))
    reb.prim("cube", "Run sheet", mat("paper"), (X0 + 0.28, 2.0, 0.978), (0.22, 0.29, 0.002), rot=(0, -0.25, 0.15))
    reb.prim("cyl", "Mug", reb.mat_plain("Mug enamel", (0.55, 0.58, 0.6), 0.35), (X0 + 0.28, 2.6, 0.97), (0.09, 0.09, 0.1), rot=(math.pi / 2, 0, 0.8), segments=14)
    kit.splat("Coffee", coffee, (X0 + 0.32, 2.72, 0.965), 0.13, seed=8, stretch=(0.8, 1.6))
    reb.prim("cube", "Photo", reb.mat_plain("Photo", (0.55, 0.5, 0.42), 0.5), (X0 + 0.08, 2.48, 1.05), (0.01, 0.12, 0.09), rot=(0, 0.2, 0))
    reb.prim("cyl", "Thermos", mat("green paint"), (2.1, 2.9, 0.05), (0.1, 0.1, 0.3), rot=(math.pi / 2, 0, 1.2), segments=14)
    kit.papers("Sheets on the floor", (2.0, 2.3, 0.0), spread=0.7, count=6, seed=5)
    kit.chair("Operator's chair", reb.mat_wood("Chair", (0.25, 0.17, 0.1)), (1.95, 1.9, 0.0), rot=math.pi, tipped=True)
    # He dressed his own bite: wrappers, bloody gauze, the drips from the desk to the door.
    for i in range(5):
        reb.cloth(f"Gauze {i}", gauze, (2.25 + rng.uniform(-0.3, 0.3), 2.65 + rng.uniform(-0.2, 0.2), 0.012), (0.14, 0.09), rot=(0, 0, rng.uniform(0, 3)), cuts=8, lumps=0.015, seed=i)
    for i in range(4):
        reb.prim("cube", f"Wrapper {i}", mat("white paint"), (2.5 + rng.uniform(-0.4, 0.4), 2.3 + rng.uniform(-0.3, 0.3), 0.002), (0.08, 0.06, 0.002), rot=(0, 0, rng.uniform(0, 3)))
    for i in range(12):
        t = i / 11
        x = 1.75 + (DOOR[0] + 0.2 - 1.75) * t + rng.uniform(-0.08, 0.08)
        y = 2.3 + (Y1 - 0.15 - 2.3) * t + rng.uniform(-0.08, 0.08)
        kit.splat(f"Drip {i}", mat("blood"), (x, y, 0.0), rng.uniform(0.025, 0.05), seed=40 + i, lumps=0.4)
    kit.splat("Pool by the desk", mat("blood"), (1.8, 2.35, 0.0), 0.22, seed=13, stretch=(1.3, 1.0))

    # ---- North wall: the duty board, chalked through the night.
    reb.prim("cube", "Board frame", frame_m, (3.55, Y0 + 0.012, 1.5), (1.16, 0.02, 0.86))
    reb.prim("cube", "Duty board", chalkboard, (3.55, Y0 + 0.03, 1.5), (1.1, 0.02, 0.8))
    for i, line in enumerate(("POWER OFF 4.50", "DRIVE COG SHEARED", "F3 BLOWN", "HAL HAS KEY")):
        kit.text(f"Chalk {i}", line, chalk, (3.55, Y0 + 0.042, 1.76 - i * 0.16), size=0.1, rot=(math.pi / 2, 0, math.pi))
    kit.rod("Underline", chalk, (3.2, Y0 + 0.043, 1.22), (3.9, Y0 + 0.043, 1.21), 0.006, 4)
    kit.rod("Underline", chalk, (3.22, Y0 + 0.043, 1.19), (3.88, Y0 + 0.043, 1.185), 0.006, 4)
    reb.prim("cube", "Chalk ledge", frame_m, (3.55, Y0 + 0.07, 1.08), (1.1, 0.08, 0.03))
    # Notices pinned up: the timetable, a safety sheet, a curling list of names.
    for i, (x, z) in enumerate(((1.45, 1.65), (1.8, 1.55), (2.25, 1.7))):
        reb.prim("cube", f"Notice {i}", mat("old paper") if i % 2 else mat("paper"), (x, Y0 + 0.025, z), (0.24, 0.006, 0.32), rot=(rng.uniform(-0.05, 0.05), 0, 0))
    # The fuse box on the east wall, open, one fuse black, soot up the wall.
    reb.prim("cube", "Fuse box", mat("steel"), (X1 - 0.06, 1.65, 1.5), (0.1, 0.45, 0.55))
    reb.prim("cube", "Fuse box door", mat("steel"), (X1 - 0.25, 1.45, 1.5), (0.02, 0.45, 0.55), rot=(0, 0, 1.2))
    for i in range(4):
        reb.prim("cyl", f"Fuse {i}", mat("white paint") if i != 2 else mat("black"), (X1 - 0.12, 1.5 + i * 0.1, 1.55), (0.03, 0.03, 0.09), segments=8)
    kit.splat("Soot", mat("black"), (X1 - 0.005, 1.68, 1.85), 0.16, rot=(0, math.pi / 2, 0), seed=12, stretch=(1.5, 0.7))
    # The wall phone, its handset hanging on the cord.
    reb.prim("cube", "Wall phone", mat("black"), (X1 - 0.05, 2.7, 1.45), (0.08, 0.18, 0.25), bevel=0.02)
    pivot = reb.prim("sphere", "Cord pivot", mat("black"), (X1 - 0.1, 2.7, 1.33), (0.02, 0.02, 0.02))
    handset = reb.prim("cube", "Handset", mat("black"), (0, 0, -0.4), (0.05, 0.05, 0.2), bevel=0.015)
    cord = kit.rod("Phone cord", mat("black"), (0, 0, 0), (0, 0, -0.3), 0.006, 6)
    handset.parent = pivot
    cord.parent = pivot
    # The poster: the view he sold, the family with their eyes scratched out.
    reb.prim("cube", "Poster", reb.mat_plain("Poster sky", (0.25, 0.38, 0.5), 0.8), (X1 - 0.02, 3.15, 1.45), (0.01, 0.55, 0.75))
    reb.prim("cube", "Poster mountains", reb.mat_plain("Poster green", (0.12, 0.25, 0.12), 0.8), (X1 - 0.026, 3.15, 1.22), (0.01, 0.55, 0.3))
    kit.text("Poster title", "ARKLAY SKYWAY", mat("white paint"), (X1 - 0.03, 3.15, 1.72), size=0.06, rot=(math.pi / 2, 0, -math.pi / 2))
    for j, y in enumerate((3.02, 3.16, 3.3)):
        reb.prim("sphere", f"Poster face {j}", reb.mat_plain("Poster face", (0.6, 0.45, 0.35), 0.8), (X1 - 0.03, y, 1.4), (0.02, 0.07, 0.08))
        kit.rod(f"Scratched eyes {j}", mat("white paint"), (X1 - 0.04, y - 0.035, 1.425), (X1 - 0.04, y + 0.035, 1.415), 0.005, 4)
    # His hook by the door, empty but for the cap he left.
    reb.prim("cube", "Coat hooks", frame_m, (1.9, Y1 - 0.02, 1.7), (0.6, 0.03, 0.08))
    reb.prim("sphere", "Cap", reb.mat_plain("Cap", (0.3, 0.07, 0.04), 0.9), (1.75, Y1 - 0.08, 1.62), (0.18, 0.15, 0.08))
    # A heater by the desk, still on, the first aid box open and empty.
    heater = reb.prim("cube", "Heater", mat("rust"), (1.55, 3.3, 0.25), (0.35, 0.18, 0.5), bevel=0.02)
    reb.mask(reb.wall(heater))
    coil_m = reb.mat_emit("Heater coil", (1.0, 0.3, 0.05), 6)
    for i in range(3):
        reb.prim("cyl", f"Coil {i}", coil_m, (1.55, 3.2, 0.15 + i * 0.12), (0.02, 0.02, 0.28), rot=(0, math.pi / 2, 0), segments=8)
    reb.prim("cube", "First aid box", mat("white paint"), (X1 - 0.08, 2.15, 1.2), (0.1, 0.3, 0.25))
    reb.prim("cube", "First aid lid", mat("white paint"), (X1 - 0.2, 2.0, 1.2), (0.02, 0.3, 0.25), rot=(0, 0, 0.9))
    kit.text("Cross", "+", mat("red paint"), (X1 - 0.135, 2.15, 1.2), size=0.12, rot=(math.pi / 2, 0, -math.pi / 2))
    for i in range(7):
        x = 3.05 + rng.uniform(-0.1, 0.1)
        y = 3.4 - i * 0.32
        kit.splat(f"Bootprint {i}", mat("mud"), (x + (0.12 if i % 2 else -0.12), y, 0.0), 0.06, seed=20 + i, stretch=(0.6, 1.4), lumps=0.2)
    kit.web("Web", (X1 - 0.02, Y0 + 0.02, H - 0.02), 0.3, (-1, 1))

    # ---- Where she saves: his typewriter on a stand against the north wall,
    # the day's log half typed; the item box along the east wall, under the
    # fuse box, the first aid box and the phone.
    stand = kit.table("Typing stand", frame_m, (2.25, 1.26, 0.0), size=(0.6, 0.42, 0.7))
    reb.mask(reb.wall(stand))
    reb.mask(kit.typewriter("His typewriter", (2.25, 1.26, 0.7)))
    box_lid = kit.item_box("Item box", (X1 - 0.43, 2.05), (-1, 0))

    # ---- Light: low morning sun through the window and the door, the strip light failing.
    kit.time_light("morning", sun_heading=290, sun_energy=2.5)
    reb.spot("Daylight through the window", (X0 - 2.5, 2.0, 2.2), (2.6, 2.5, 0.0), 650, (1.0, 0.86, 0.66), 50, 0.6, 0.2)
    reb.spot("Daylight through the door", (3.05, Y1 + 2.5, 2.0), (3.05, 2.4, 0.0), 160, (0.8, 0.86, 1.0), 40, 0.8, 0.4)
    tube_m = reb.mat_emit("Strip light", (0.75, 0.95, 0.85), 10)
    reb.prim("cyl", "Strip light", tube_m, (3.0, 2.3, H - 0.16), (0.04, 0.04, 1.2), rot=(0, math.pi / 2, 0), segments=10)
    strip = reb.point("Strip light glow", (3.0, 2.3, H - 0.24), 14, (0.75, 0.95, 0.85), 0.4)
    heat = reb.point("Heater glow", (1.55, 3.1, 0.3), 3.0, (1.0, 0.3, 0.06), 0.1)

    anim = kit.Anim(16)
    anim.flicker(strip, tube_m, depth=0.4, dropouts=3)
    anim.flicker(heat, coil_m, depth=0.15, dropouts=0)

    def turn(k):
        a = anim.phase(k)
        pivot.rotation_euler = (0.12 * math.sin(a), 0.05 * math.cos(a), 0.6 * math.sin(a))
    anim.custom(turn)

    # ---- What the game needs.
    room.door("platform", (DOOR[0], Y1 - 0.4, DOOR[1], Y1), arrive=(3.05, 2.9), face=(0, -1))
    room.check((3.0, Y0, 4.1, Y0 + 0.7), "The duty board, in chalk. POWER OFF 4.50. DRIVE COG SHEARED. F3 BLOWN.\nAt the bottom, underlined twice: HAL HAS KEY.")
    room.check((X0, 1.1, X0 + 0.9, 1.6), "The key switch for the drive. It's empty.\nNo key, no gondola.")
    room.check((X0, 2.4, X0 + 0.9, 2.9), "His coffee went over. A photo of a girl with a fish, propped against the glass.")
    room.check((1.9, 2.4, 2.7, 3.0), "Gauze, soaked through. He dressed something in a hurry.\nA bite, by the look of the first aid box. Everything in it is gone.")
    # The fuse box and the phone hang over the item box: their zones reach out past its front.
    room.check((X1 - 1.0, 1.3, X1, 1.95), "Fuse F3 is burnt black. The wall above it is sooty.")
    room.check((X1 - 1.0, 2.45, X1, 2.95), "The handset is hanging off the hook. The line's dead.")
    room.check((X1 - 0.7, 2.95, X1, 3.45), "ARKLAY SKYWAY. See the valley the way the eagles do.\nSomeone has scratched out the family's eyes.")
    room.check((DOOR[0] - 0.5, Y1 - 0.6, DOOR[0], Y1), "A handprint in blood on the door frame. It's still tacky.")
    room.save_room(typewriter=(1.95, Y0, 2.55, 1.8), box=(X1 - 1.0, 1.97, X1, 2.43), lid=box_lid)
    room.entry = "The heater's still on. He can't have gone long."
    room.export(anim)


build()
