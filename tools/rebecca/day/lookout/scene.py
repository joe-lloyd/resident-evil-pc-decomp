"""The ranger's lookout, inside: a one-room log cabin on the mountain, the
morning after. A desk under the north window with the radio and the
logbook, a shelf beside it, a bunk on the east wall, a stove on the west, the
door to the south.

Game units: the floor is X 3000-9000, Z 3000-8000, Y = 0; the walls stand
on its edges, 2.6 m high.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
from mathutils import Vector  # noqa: E402

OUT = os.environ.get("RE1_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders"))

CAMERAS = [
    # 0: high in the south-west corner, over the stove, at the desk and bunk.
    {"from": (3350, -2350, 7650), "to": (7200, -500, 3800), "fov": 200},
    # 1: high in the north-east corner, over the bunk, at the door.
    {"from": (8650, -2350, 3350), "to": (4800, -500, 7200), "fov": 200},
]

X0, X1, Z0, Z1, H = 3.0, 9.0, 3.0, 8.0, 2.6


def build():
    rng = random.Random(7)
    reb.clear_scene()
    logs = reb.mat_wood("Logs", (0.16, 0.1, 0.06))
    boards = reb.mat_wood("Floorboards", (0.13, 0.085, 0.05))
    dark = reb.mat_wood("Dark wood", (0.07, 0.045, 0.03))
    iron = reb.mat_surface("Iron", [(0.2, (0.02, 0.02, 0.02)), (0.7, (0.07, 0.065, 0.06))], scale=6, rough=0.6)
    cloth = reb.mat_surface("Blanket", [(0.2, (0.12, 0.04, 0.03)), (0.8, (0.22, 0.08, 0.05))], scale=8)
    paper = reb.mat_surface("Paper", [(0.0, (0.5, 0.47, 0.38)), (1.0, (0.62, 0.58, 0.48))], scale=20, bump=0.1)
    radio = reb.mat_surface("Radio", [(0.0, (0.06, 0.07, 0.05)), (1.0, (0.1, 0.11, 0.08))], scale=10, rough=0.5)

    # Floor of boards, walls of stacked logs, a ceiling.
    v, f = [], []
    for i in range(30):
        x = X0 + (X1 - X0) * i / 30
        reb.box(v, f, (x + 0.1, (Z0 + Z1) / 2, -0.03), (0.19, Z1 - Z0, 0.06))
    reb.mesh_object("Floor", v, f, boards, smooth=False)
    v, f = [], []
    for k in range(12):
        z = k * H / 12 + 0.11
        reb.box(v, f, ((X0 + X1) / 2, Z0 - 0.12, z), (X1 - X0 + 0.5, 0.26, 0.22))
        reb.box(v, f, (X0 - 0.12, (Z0 + Z1) / 2, z), (0.26, Z1 - Z0 + 0.5, 0.22))
        reb.box(v, f, (X1 + 0.12, (Z0 + Z1) / 2, z), (0.26, Z1 - Z0 + 0.5, 0.22))
        # The south wall, with the door gap at X 5.4-6.6.
        reb.box(v, f, ((X0 + 5.4) / 2, Z1 + 0.12, z), (5.4 - X0 + 0.25, 0.26, 0.22))
        reb.box(v, f, ((6.6 + X1) / 2, Z1 + 0.12, z), (X1 - 6.6 + 0.25, 0.26, 0.22))
    reb.mesh_object("Log walls", v, f, logs)
    v, f = [], []
    reb.box(v, f, ((X0 + X1) / 2, (Z0 + Z1) / 2, H + 0.05), (X1 - X0 + 0.6, Z1 - Z0 + 0.6, 0.1))
    for i in range(5):
        reb.box(v, f, (X0 + 0.6 + i * 1.2, (Z0 + Z1) / 2, H - 0.12), (0.18, Z1 - Z0, 0.22))
    reb.mesh_object("Ceiling", v, f, dark, smooth=False)
    # The door, shut, in its frame.
    v, f = [], []
    reb.box(v, f, (6.0, Z1 + 0.15, 1.05), (1.2, 0.08, 2.1))
    reb.mesh_object("Door", v, f, dark, smooth=False)

    # The window over the desk: a frame and the morning beyond.
    v, f = [], []
    reb.box(v, f, (4.6, Z0 - 0.02, 1.55), (1.4, 0.05, 0.9))
    reb.mesh_object("Window light", v, f, reb.mat_emit("Morning", (0.85, 0.9, 1.0), 6), smooth=False)
    v, f = [], []
    for dz in (-0.45, 0.45):
        reb.box(v, f, (4.6, Z0 + 0.01, 1.55 + dz), (1.5, 0.08, 0.08))
    for dx in (-0.7, 0.0, 0.7):
        reb.box(v, f, (4.6 + dx, Z0 + 0.01, 1.55), (0.08, 0.08, 0.98))
    reb.mesh_object("Window frame", v, f, dark, smooth=False)

    # Furniture: each blocks her, and the near ones stand in front of her.
    def furniture(name, parts, mat, mask=False):
        v, f = [], []
        for c, s in parts:
            reb.box(v, f, c, s)
        ob = reb.wall(reb.mesh_object(name, v, f, mat, smooth=False))
        if mask:
            reb.mask(ob)
        return ob

    furniture("Desk", [((4.6, 3.45, 0.75), (2.0, 0.8, 0.06))] + [((4.6 + dx, 3.45 + dz, 0.37), (0.07, 0.07, 0.74)) for dx in (-0.9, 0.9) for dz in (-0.33, 0.33)], dark)
    v, f = [], []
    reb.box(v, f, (4.2, 3.35, 0.95), (0.55, 0.32, 0.36))
    reb.mask(reb.mesh_object("Radio", v, f, radio, smooth=False))
    v, f = [], []
    reb.box(v, f, (4.05, 3.18, 1.0), (0.12, 0.02, 0.06))
    reb.mesh_object("Radio dial", v, f, reb.mat_emit("Dial", (1.0, 0.6, 0.2), 4), smooth=False)
    v, f = [], []
    reb.box(v, f, (5.1, 3.5, 0.795), (0.42, 0.3, 0.03))
    reb.mesh_object("Logbook", v, f, paper, smooth=False)
    furniture("Shelf", [((6.6, 3.2, 1.0), (1.4, 0.4, 2.0))], dark, mask=True)
    furniture("Bunk", [((8.45, 4.9, 0.25), (1.0, 2.1, 0.5))], dark, mask=True)
    v, f = [], []
    reb.box(v, f, (8.45, 4.9, 0.55), (0.95, 2.0, 0.12))
    reb.box(v, f, (8.45, 4.05, 0.65), (0.8, 0.35, 0.12))
    reb.mask(reb.mesh_object("Blanket", v, f, cloth))
    furniture("Stove", [((3.45, 5.9, 0.4), (0.7, 0.7, 0.8)), ((3.45, 5.9, 1.8), (0.15, 0.15, 2.0))], iron, mask=True)
    furniture("Table", [((6.3, 6.1, 0.72), (1.2, 0.8, 0.05)), ((6.3, 6.1, 0.36), (0.1, 0.1, 0.72))], dark, mask=True)

    # Clutter on the shelf: tins and jars.
    v, f = [], []
    for i in range(14):
        reb.box(v, f, (6.05 + (i % 7) * 0.17, 3.2, 0.62 + (i // 7) * 0.62), (0.1, 0.1, 0.16 + rng.uniform(0, 0.06)))
    reb.mask(reb.mesh_object("Tins", v, f, reb.mat_surface("Tin", [(0.0, (0.15, 0.13, 0.1)), (1.0, (0.35, 0.3, 0.2))], scale=12), smooth=False))

    # Light: the morning through the window, a warm lamp, a dim fill.
    reb.light_for("morning")
    reb.spot("Window sun", (4.6, 1.5, 2.4), (5.6, 5.5, 0.0), 900, (1.0, 0.92, 0.8), 60, 0.6, 0.3)
    reb.point("Lamp", (6.3, 6.1, 1.2), 120, (1.0, 0.65, 0.35), 0.15)
    reb.point("Fill", (6.0, 5.5, 2.3), 60, (0.7, 0.8, 1.0), 1.0)
    reb.export(CAMERAS, OUT, samples=768, extra={"bounds": {"x0": 3000, "z0": 3000, "x1": 9000, "z1": 8000}, "exit": {"x0": 5400, "z0": 7900, "x1": 6600, "z1": 9000}})


build()
