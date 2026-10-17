"""The lower station's office, dusk: where the keeper sat out the night.

What it tells: the keeper ran the bottom of the line and wrote everything
in his log. Yesterday afternoon the estate gardener came up for supplies
again and said the dogs had got out. At three in the morning a woman came
in from the car park, bitten. He sat her on the counter, bandaged her
wrist from the first aid cabinet, found the phone dead, and sent her up in
car 4 to Hal, who had a radio. Her blood is still all over the counter.
Then something came through the north window. The kettle on the hotplate
went cold, the CB radio still hisses to itself, his coat is on its hook,
and he is in the machine room beyond the far doorway, on his back under
the bullwheel where they dragged him, with the red emergency lamp turning
over him.

Metres: the floor is x 1.0-5.6, y 1.0-5.0, 2.6 high. The door to the yard
is in the west wall at y 2.6-3.6. The west wall's windows are at y 1.3-2.3
(smashed in) and y 3.9-4.7. The counter runs along the north side at
y 1.5-2.0, x 1.8-4.0. The keeper's desk is in the south-east corner. The
doorway to the machine room is in the east wall at y 1.5-2.7; the
bullwheel is beyond it.

Moving: the strip light failing, the emergency beacon turning in the
machine room, the CB's signal lamp, moths at the desk lamp, flies over him.
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

X0, X1, Y0, Y1, H = 1.0, 5.6, 1.0, 5.0, 2.6
DOOR = (2.6, 3.6)
WIN_BROKEN = (1.3, 2.3)
WIN = (3.9, 4.7)
MDOOR = (1.5, 2.7)
COUNTER = (1.8, 4.0, 1.5, 2.0)


def build():
    rng = random.Random(1640)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.ground("lino")
    room.camera((1.15, 4.85, 2.35), (4.6, 1.7, 0.6), 200, "high in the south-west corner: the bloody counter, the doorway to the machine room and him beyond it")
    room.camera((5.45, 4.85, 2.35), (1.9, 1.9, 0.6), 200, "high in the south-east corner over the desk: the counter, the smashed window, the key board")
    room.camera((5.45, 1.15, 2.35), (1.8, 4.4, 0.5), 200, "high in the north-east corner by the doorway: the desk, the log and the radio, the door out to the yard")

    plaster = kit.dirtied(mat("plaster"), 0.5, scale=1.5)
    lino = reb.mat_surface("Office lino", [(0.0, (0.07, 0.07, 0.06)), (0.5, (0.16, 0.15, 0.12)), (1.0, (0.1, 0.09, 0.07))], scale=3, rough=0.45, bump=0.2)
    ceiling = reb.mat_surface("Ceiling tiles", [(0.0, (0.35, 0.33, 0.28)), (1.0, (0.45, 0.43, 0.37))], scale=2, bump=0.1)
    wood = reb.mat_wood("Counter wood", (0.22, 0.14, 0.08))
    cream = reb.mat_plain("Cream metal", (0.42, 0.4, 0.33), 0.5)
    green = mat("green paint")
    machine_dark = reb.mat_surface("Machine room", [(0.0, (0.05, 0.05, 0.045)), (1.0, (0.12, 0.11, 0.1))], scale=2, bump=0.3)

    # ---- The shell: plastered walls, a dado rail, lino, a tiled ceiling.
    kit.walls(X0, Y0, X1, Y1, H, plaster, openings=[
        ("w", DOOR[0], DOOR[1], 0.0, 2.1),
        ("w", WIN_BROKEN[0], WIN_BROKEN[1], 1.0, 2.0),
        ("w", WIN[0], WIN[1], 1.0, 2.0),
        ("e", MDOOR[0], MDOOR[1], 0.0, 2.2),
    ], floor=lino, ceiling=ceiling)
    for side, at, size in (("n", ((X0 + X1) / 2, Y0 + 0.01, 0.95), (X1 - X0, 0.02, 0.04)), ("s", ((X0 + X1) / 2, Y1 - 0.01, 0.95), (X1 - X0, 0.02, 0.04))):
        reb.prim("cube", "Dado rail", wood, at, size)
    reb.prim("cube", "Lower wall paint", green, ((X0 + X1) / 2, Y1 - 0.008, 0.47), (X1 - X0, 0.01, 0.94))
    reb.prim("cube", "Lower wall paint", green, ((X0 + X1) / 2, Y0 + 0.008, 0.47), (X1 - X0, 0.01, 0.94))
    for x in (2.2, 3.4, 4.6):
        reb.prim("cube", "Ceiling grid", mat("white paint"), (x, (Y0 + Y1) / 2, H - 0.005), (0.03, Y1 - Y0, 0.01))
    # The door to the yard, swung open outward; the windows, one smashed in.
    reb.prim("cube", "Door leaf, open", green, (X0 - 0.5, DOOR[0] - 0.15, 1.05), (0.82, 0.05, 2.1), rot=(0, 0, 0.35))
    for y in (DOOR[0] - 0.04, DOOR[1] + 0.04):
        reb.prim("cube", "Door frame", wood, (X0 + 0.02, y, 1.08), (0.06, 0.08, 2.16))
    reb.prim("cube", "Window glass", reb.mat_glass("Window glass", (0.5, 0.55, 0.55)), (X0 - 0.06, (WIN[0] + WIN[1]) / 2, 1.5), (0.01, WIN[1] - WIN[0], 1.0))
    for y0, y1 in (WIN_BROKEN, WIN):
        reb.prim("cube", "Sill", wood, (X0 + 0.04, (y0 + y1) / 2, 0.98), (0.14, y1 - y0 + 0.1, 0.04))
    for i in range(8):
        a = rng.uniform(0, 2 * math.pi)
        c = Vector((X0 - 0.06, (WIN_BROKEN[0] + WIN_BROKEN[1]) / 2, 1.5))
        kit.rod("Jagged glass", reb.mat_glass("Window glass", (0.5, 0.55, 0.55)), c + Vector((0, math.cos(a) * 0.5, math.sin(a) * 0.5)), c + Vector((0, math.cos(a) * 0.3, math.sin(a) * 0.28)), 0.012, 3)
    kit.shards("Glass in on the floor", (X0 + 0.6, (WIN_BROKEN[0] + WIN_BROKEN[1]) / 2, 0.0), spread=0.9, count=26, seed=2)
    kit.splat("Smear over the sill", mat("old blood"), (X0 + 0.05, 1.8, 1.003), 0.12, seed=3, stretch=(0.6, 1.8))
    kit.scratches("Claw marks under the window", mat("black"), (X0 + 0.005, 1.6, 0.9), (1, 0), count=4, length=0.5, seed=4)
    # Outside: the yard at dusk, the drinks machine's glow, the sedan's light far off.
    yard = reb.mat_surface("Yard gravel", [(0.0, (0.06, 0.055, 0.05)), (1.0, (0.13, 0.12, 0.11))], scale=6, bump=0.6)
    reb.prim("cube", "Yard", yard, (X0 - 8.0, 3.0, -0.08), (16.0, 20.0, 0.1))
    reb.prim("cube", "Door step", mat("concrete"), (X0 - 0.35, (DOOR[0] + DOOR[1]) / 2, 0.05), (0.6, 1.6, 0.1))
    reb.prim("cube", "Booth outside", kit.boards("Booth boards", (0.2, 0.13, 0.08), width=0.18), (X0 - 3.2, 5.4, 1.2), (1.4, 1.6, 2.4))
    reb.prim("cube", "Booth outside, TICKETS", mat("white paint"), (X0 - 3.92, 5.4, 2.0), (0.02, 1.0, 0.25))
    vm = reb.mat_emit("Drinks machine far", (1.0, 0.9, 0.8), 3)
    reb.prim("cube", "Drinks machine outside", vm, (X0 - 0.5, 6.0, 1.2), (0.02, 0.5, 0.9))
    reb.point("Drinks machine glow outside", (X0 - 0.9, 6.0, 1.1), 10, (1.0, 0.9, 0.8), 0.3)
    reb.prim("cube", "Sedan far off", reb.mat_plain("Burgundy", (0.2, 0.02, 0.04), 0.3), (X0 - 8.0, 9.4, 0.6), (4.6, 1.8, 1.2), rot=(0, 0, 0.35))
    reb.point("Sedan's dome light far off", (X0 - 8.0, 9.4, 1.2), 6, (1.0, 0.82, 0.5), 0.1)
    reb.prim("cube", "Tree line", reb.mat_plain("Trees at dusk", (0.015, 0.025, 0.02), 1.0), (X0 - 18.0, 3.0, 6.0), (2.0, 40.0, 14.0))
    sodium = reb.spot("Yard lamp outside", (X0 - 5.0, 3.5, 5.5), (X0 - 2.0, 3.0, 0.0), 1500, (1.0, 0.55, 0.18), 90, 0.6, 0.15)

    # ---- The counter along the north: her blood all over it, the ticket machine, the cash box open.
    cx0, cx1, cy0, cy1 = COUNTER
    counter = kit.box("Counter", wood, ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 0.0), (cx1 - cx0, cy1 - cy0, 1.0))
    reb.mask(reb.wall(counter))
    reb.prim("cube", "Counter top", mat("dark wood"), ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 1.02), (cx1 - cx0 + 0.08, cy1 - cy0 + 0.08, 0.04))
    kit.splat("Blood on the counter", mat("blood"), (2.6, 1.75, 1.04), 0.32, seed=5, stretch=(1.4, 0.7))
    kit.splat("Hand on the counter's edge", mat("blood"), (3.1, cy1 + 0.04, 0.95), 0.06, rot=(math.pi / 2, 0, math.pi), seed=6)
    for i in range(3):
        reb.prim("cube", f"Run down the front {i}", mat("blood"), (2.3 + i * 0.25, cy1 + 0.045, 0.8 - i * 0.05), (0.02, 0.004, 0.35 + i * 0.1))
    kit.splat("Pool under the counter", mat("blood"), (2.6, cy1 + 0.35, 0.0), 0.35, seed=7, stretch=(1.5, 0.9))
    reb.prim("cube", "Ticket machine", cream, (3.6, 1.7, 1.17), (0.32, 0.3, 0.26), bevel=0.02)
    reb.prim("cube", "Cash box, open", mat("steel"), (2.0, 1.75, 1.08), (0.3, 0.22, 0.08))
    reb.prim("cube", "Cash box lid", mat("steel"), (2.0, 1.62, 1.18), (0.3, 0.02, 0.2), rot=(0.4, 0, 0))
    reb.prim("cube", "Bandage roll", mat("white paint"), (3.0, 1.62, 1.08), (0.06, 0.1, 0.06), rot=(0, 0, 0.5))
    reb.prim("cube", "Scissors", mat("steel"), (2.8, 1.85, 1.045), (0.16, 0.03, 0.006), rot=(0, 0, 0.8))
    for i in range(5):
        reb.prim("cube", f"Wrapper {i}", mat("white paint"), (2.4 + rng.uniform(-0.5, 0.6), 2.4 + rng.uniform(-0.2, 0.3), 0.003), (0.08, 0.06, 0.002), rot=(0, 0, rng.uniform(0, 3)))
    # The first aid cabinet on the north wall, open and emptied.
    reb.prim("cube", "First aid cabinet", mat("white paint"), (2.45, Y0 + 0.08, 1.55), (0.45, 0.14, 0.55))
    reb.prim("cube", "First aid cabinet door", mat("white paint"), (2.08, Y0 + 0.3, 1.55), (0.02, 0.45, 0.55), rot=(0, 0, -0.75))
    kit.text("First aid cross", "+", mat("red paint"), (2.45, Y0 + 0.156, 1.65), size=0.2, rot=(math.pi / 2, 0, math.pi))
    # The key board and his coat on the north wall, by the counter.
    reb.prim("cube", "Key board", wood, (1.45, Y0 + 0.02, 1.55), (0.55, 0.03, 0.45))
    for i in range(8):
        x = 1.25 + (i % 4) * 0.13
        z = 1.68 - (i // 4) * 0.2
        reb.prim("cube", f"Key hook {i}", mat("steel"), (x, Y0 + 0.045, z), (0.01, 0.03, 0.01))
        if i != 5:
            reb.prim("cube", f"Key tag {i}", reb.mat_plain("Key tag", (0.5, 0.35, 0.05), 0.5), (x, Y0 + 0.05, z - 0.06), (0.04, 0.005, 0.06), rot=(0, rng.uniform(-0.2, 0.2), 0))
    kit.text("Key board words", "KEYS", mat("white paint"), (1.45, Y0 + 0.037, 1.72), size=0.05, rot=(math.pi / 2, 0, math.pi))
    reb.prim("cube", "Coat hooks", wood, (X1 - 0.02, 3.6, 1.75), (0.03, 0.6, 0.06))
    reb.cloth("Keeper's coat", reb.mat_plain("Donkey jacket", (0.04, 0.05, 0.08), 0.9), (X1 - 0.1, 3.5, 1.3), (0.55, 0.85), rot=(math.pi / 2, 0, math.pi / 2), cuts=12, lumps=0.05, seed=2)
    reb.prim("sphere", "Keeper's cap", reb.mat_plain("Cap", (0.08, 0.1, 0.18), 0.8), (X1 - 0.12, 3.85, 1.8), (0.2, 0.18, 0.1))
    # The certificate: who paid for it.
    reb.prim("cube", "Certificate frame", mat("dark wood"), (3.6, Y1 - 0.02, 1.7), (0.6, 0.03, 0.45))
    reb.prim("cube", "Certificate", mat("old paper"), (3.6, Y1 - 0.037, 1.7), (0.52, 0.004, 0.37))
    for j in range(8):
        a = 2 * math.pi * j / 8
        reb.prim("cone", f"Umbrella segment {j}", mat("red paint") if j % 2 else mat("white paint"), (3.6 + math.cos(a + math.pi / 8) * 0.035, Y1 - 0.042, 1.78 + math.sin(a + math.pi / 8) * 0.035), (0.06, 0.004, 0.06), rot=(math.pi / 2, 0, 0), segments=3)
    kit.text("Certificate words", "ARKLAY SKYWAY 1996", mat("black"), (3.6, Y1 - 0.043, 1.63), size=0.035)
    kit.text("Certificate words 2", "UMBRELLA CORPORATION", mat("black"), (3.6, Y1 - 0.043, 1.57), size=0.028)
    reb.prim("cube", "Calendar", mat("paper"), (2.2, Y1 - 0.015, 1.6), (0.32, 0.006, 0.42))
    kit.text("Calendar month", "JULY", mat("red paint"), (2.2, Y1 - 0.02, 1.76), size=0.05)
    reb.prim("cyl", "Clock", mat("black"), (2.9, Y1 - 0.02, 2.2), (0.26, 0.26, 0.04), rot=(math.pi / 2, 0, 0), segments=20)
    reb.prim("cyl", "Clock face", mat("paper"), (2.9, Y1 - 0.045, 2.2), (0.22, 0.22, 0.01), rot=(math.pi / 2, 0, 0), segments=20)

    # ---- The keeper's desk in the south-east corner: the log, the kettle, the CB, the lamp.
    desk = kit.table("Keeper's desk", wood, (4.75, 4.45, 0.0), size=(1.5, 0.8, 0.76))
    reb.mask(reb.wall(desk))
    reb.prim("cube", "Station log", reb.mat_plain("Log cover", (0.25, 0.08, 0.05), 0.7), (4.5, 4.35, 0.77), (0.42, 0.32, 0.02), rot=(0, 0, -0.1))
    reb.prim("cube", "Log pages", mat("paper"), (4.5, 4.35, 0.785), (0.4, 0.3, 0.01), rot=(0, 0, -0.1))
    for i in range(7):
        reb.prim("cube", "Log line", reb.mat_plain("Ink", (0.04, 0.05, 0.12), 0.5), (4.5 + rng.uniform(-0.02, 0.02), 4.24 + i * 0.035, 0.791), (0.3 + rng.uniform(-0.08, 0.02), 0.004, 0.001), rot=(0, 0, -0.1))
    reb.prim("cyl", "Pen", mat("black"), (4.78, 4.3, 0.785), (0.01, 0.01, 0.14), rot=(math.pi / 2, 0, 0.6), segments=6)
    reb.prim("cube", "Hotplate", mat("iron"), (5.25, 4.65, 0.8), (0.3, 0.3, 0.07))
    reb.prim("cyl", "Kettle", mat("steel"), (5.25, 4.65, 0.93), (0.22, 0.22, 0.2), segments=16)
    reb.prim("cone", "Kettle spout", mat("steel"), (5.1, 4.62, 0.97), (0.04, 0.04, 0.16), rot=(0, -1.0, 0), segments=8, top=0.4)
    reb.prim("cyl", "Mug", reb.mat_plain("Mug", (0.55, 0.1, 0.06), 0.4), (4.15, 4.6, 0.81), (0.09, 0.09, 0.1), segments=14)
    reb.prim("cube", "CB radio", mat("black"), (4.95, 4.75, 0.84), (0.32, 0.22, 0.1), bevel=0.01)
    cb_m = reb.mat_emit("CB lamp", (1.0, 0.15, 0.05), 6)
    reb.prim("cube", "CB meter", reb.mat_emit("CB meter", (1.0, 0.6, 0.15), 2.5), (4.95, 4.638, 0.85), (0.1, 0.004, 0.04))
    reb.prim("sphere", "CB lamp", cb_m, (5.07, 4.636, 0.85), (0.015, 0.015, 0.015), segments=8)
    reb.prim("cube", "CB mic", mat("black"), (4.75, 4.6, 0.79), (0.06, 0.1, 0.04), rot=(0, 0, 0.4))
    kit.rod("Mic cord", mat("black"), (4.75, 4.65, 0.79), (4.88, 4.73, 0.83), 0.006, 4)
    kit.rod("Aerial lead", mat("black"), (5.05, 4.85, 0.84), (5.55, 4.95, 2.4), 0.006, 4)
    kit.chair("Keeper's chair", reb.mat_wood("Chair", (0.22, 0.15, 0.09)), (4.5, 3.7, 0.0), rot=math.pi / 2 + 0.4)
    lamp_m = reb.mat_emit("Desk lamp", (1.0, 0.75, 0.45), 4)
    kit.rod("Desk lamp stem", mat("steel"), (4.15, 4.75, 0.76), (4.2, 4.65, 1.15), 0.012)
    reb.prim("cone", "Desk lamp shade", mat("green paint"), (4.22, 4.6, 1.15), (0.2, 0.2, 0.14), segments=14, top=0.35)
    reb.prim("sphere", "Desk lamp bulb", lamp_m, (4.22, 4.6, 1.1), (0.06, 0.06, 0.06), segments=8)
    desk_lamp = reb.point("Desk lamp light", (4.22, 4.6, 1.02), 10, (1.0, 0.72, 0.42), 0.04)

    # ---- The doorway east to the machine room: the bullwheel in the dark, the red beacon, him.
    reb.prim("cube", "Machine room floor", mat("concrete"), (X1 + 4.0, 2.0, -0.02), (8.0, 9.0, 0.04))
    for at, size in (((X1 + 8.0, 2.0, 2.5), (0.2, 9.0, 5.0)), ((X1 + 4.0, -2.5, 2.5), (8.0, 0.2, 5.0)), ((X1 + 4.0, 6.5, 2.5), (8.0, 0.2, 5.0)), ((X1 + 4.0, 2.0, 5.0), (8.0, 9.0, 0.2))):
        reb.prim("cube", "Machine room wall", machine_dark, at, size)
    for y in (MDOOR[0] - 0.04, MDOOR[1] + 0.04):
        reb.prim("cube", "Doorway frame", wood, (X1 + 0.06, y, 1.12), (0.14, 0.08, 2.24))
    reb.prim("cube", "Doorway sign", mat("yellow paint"), (X1 - 0.005, (MDOOR[0] + MDOOR[1]) / 2, 2.4), (0.01, 0.8, 0.2))
    kit.text("Doorway sign words", "MACHINE ROOM", mat("black"), (X1 - 0.012, (MDOOR[0] + MDOOR[1]) / 2, 2.4), size=0.08, rot=(math.pi / 2, 0, -math.pi / 2))
    wc = Vector((X1 + 4.0, 2.1, 1.6))
    reb.prim("cyl", "Bullwheel rim", mat("rust"), wc, (5.0, 5.0, 0.25), segments=40)
    reb.prim("cyl", "Bullwheel inner", machine_dark, wc + Vector((0, 0, 0.01)), (4.4, 4.4, 0.27), segments=40)
    reb.prim("cyl", "Bullwheel hub", mat("iron"), wc, (0.7, 0.7, 0.5), segments=16)
    for i in range(8):
        a = math.pi * i / 4
        kit.rod("Spoke", mat("rust"), wc, wc + Vector((math.cos(a) * 2.3, math.sin(a) * 2.3, 0)), 0.06)
    kit.rod("Bullwheel shaft", mat("iron"), wc, (wc.x, wc.y, 0.0), 0.15)
    reb.prim("cube", "Gearbox", green, (X1 + 2.3, 4.6, 0.6), (1.4, 1.0, 1.2), bevel=0.04)
    reb.prim("cyl", "Drive motor", mat("iron"), (X1 + 3.4, 4.9, 0.6), (0.8, 0.8, 1.2), rot=(0, math.pi / 2, 0), segments=16)
    kit.rod("Haul cable in", mat("iron"), wc + Vector((-2.5, 0, 0.1)), (X1 + 1.5, -2.4, 1.7), 0.03, 6)
    kit.rod("Haul cable in", mat("iron"), wc + Vector((2.5, 0, 0.1)), (X1 + 6.5, -2.4, 1.7), 0.03, 6)
    # The keeper, on his back under the wheel, dragged in by the feet.
    kit.body("The keeper", (X1 + 0.75, 2.2, 0.0), 0.15, pose="back", top=reb.mat_plain("Keeper's sweater", (0.18, 0.2, 0.12), 0.95), legs=mat("denim"), bloody=1.5, seed=9)
    kit.drag_trail("Dragged in", mat("old blood"), [(4.8, 3.6), (5.3, 2.6), (X1 + 0.4, 2.2), (X1 + 1.6, 2.25)], width=0.35, seed=10)
    reb.prim("cube", "Keeper's glasses", mat("black"), (4.9, 3.2, 0.01), (0.13, 0.04, 0.01), rot=(0, 0, 0.6))
    beacon_pivot = reb.prim("cyl", "Beacon", reb.mat_emit("Beacon red", (1.0, 0.05, 0.02), 8), (X1 + 2.0, -2.3, 3.4), (0.18, 0.18, 0.22), segments=12)
    beacon = reb.spot("Beacon light", (X1 + 2.0, -2.2, 3.4), (X1 + 2.0, 3.0, 0.0), 900, (1.0, 0.06, 0.02), 50, 0.4, 0.05)
    reb.point("Beacon wash", (X1 + 2.0, -1.8, 3.2), 40, (1.0, 0.06, 0.02), 0.3)

    # ---- Light: a failing strip light, the desk lamp, the dusk at the windows.
    kit.time_light("dusk", sun_heading=272, sun_energy=1.6)
    tube_m = reb.mat_emit("Strip light", (0.75, 0.95, 0.85), 9)
    reb.prim("cyl", "Strip light", tube_m, (2.8, 3.0, H - 0.08), (0.05, 0.05, 1.2), rot=(0, math.pi / 2, 0), segments=10)
    strip = reb.point("Strip light glow", (2.8, 3.0, H - 0.2), 18, (0.75, 0.95, 0.85), 0.4)
    reb.spot("Dusk through the windows", (X0 - 3.0, 2.0, 1.8), (3.5, 2.5, 0.0), 120, (0.9, 0.45, 0.3), 50, 0.8, 0.5)

    anim = kit.Anim(16)
    anim.flicker(strip, tube_m, depth=0.55, dropouts=4)

    def turn(k):
        a = anim.phase(k)
        d = Vector((math.sin(a) * 5.2, math.cos(a) * 5.2, -3.4))
        beacon.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        beacon_pivot.rotation_euler = (0, 0, -a)
    anim.custom(turn)
    anim.blink(reb.point("CB lamp light", (5.07, 4.6, 0.86), 0.3, (1.0, 0.15, 0.05), 0.01), cb_m, on=(0, 3))
    anim.flies((4.22, 4.6, 1.15), count=6, radius=0.22, size=0.015)
    anim.flies((X1 + 1.6, 2.3, 0.2), count=9, radius=0.4)
    anim.flicker(desk_lamp, lamp_m, depth=0.1, dropouts=0)

    # ---- What the game needs.
    room.door("lower-yard", (X0, DOOR[0], X0 + 0.45, DOOR[1]), arrive=(1.9, 3.1), face=(1, 0))
    room.check((4.0, 3.45, 4.7, 4.05), "The keeper's log.\n23 JULY. 1610. The estate gardener came up for supplies again. Said the dogs have got out.\n0305. Woman from the lot, bitten by a dog. Bad. Phone's dead. Bandaged her, sent her up in 4 to Hal. He's got the radio.\n0340. Something at the window.")
    room.check((5.15, 3.45, X1, 4.05), "A kettle on the hotplate. Stone cold.")
    room.check((cx0, cy1, cx1, cy1 + 0.6), "Blood all over the counter. This is where he bandaged her.\nThe first aid cabinet's been emptied.")
    room.check((X0, WIN_BROKEN[0], X0 + 0.7, WIN_BROKEN[1]), "The window's been smashed in from outside. Something came through here.")
    room.check((X1 - 0.6, MDOOR[0], X1, MDOOR[1]), "The keeper. They dragged him into the machine room.\nThe wheel's stopped.")
    room.check((X0, Y0, 1.8, 1.5), "Keys on a board. SHED. GATE. PUMP. One hook's empty: DRIVE.")
    room.check((X1 - 0.5, 3.2, X1, 3.9), "His coat's still on the hook. He never left.")
    room.check((3.2, Y1 - 0.5, 4.0, Y1), "ARKLAY SKYWAY, 1996. Built with the support of the Umbrella Corporation.\nUmbrella. Again.")
    room.check((4.7, 3.45, 5.15, 4.05), "A CB radio. Static on every channel.")
    room.entry = "Blood on the counter. Glass on the floor."
    room.export(anim)


build()
