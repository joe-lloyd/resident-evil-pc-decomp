"""The foreman's office at Camp 4, noon.

What it tells: the foreman ran the camp from here, and he knew more than
his men. The letters on his desk are on Umbrella letterhead: Umbrella paid
for the gondola, and asked him to keep "the samples" cold and say nothing.
His payroll ledger lists his crew, and he has struck the names through one
by one as they died. He painted the quarantine board himself. When it was
his turn he took the last shotgun from the rack, sat at his desk and used
it: the chair went over backwards, he slid down the wall, and the wall and
the ceiling behind him are sprayed dark. His lamp is still on and his fan
still turns, blowing at the papers. The safe stands shut in the corner; the
combination is on a calendar in the bunkhouse, not here. On the wall, his
map of the camp.

Metres: the floor is x 1.0-4.6, y 1.0-4.0, 2.5 high (the yard's office hut
moved 0.4 south). The door is in the south wall at x 2.5-3.4, out to the
yard; windows in the south wall at x 3.75-4.35 and the east wall at y
1.6-2.7, from 1.0 to 1.8 high. The stove in the north-west corner, its
pipe at (1.6, 1.8). The desk at (3.2, 2.35), the foreman against the north
wall behind it, the safe in the south-west corner, the filing cabinet and
fan in the north-east, the gun rack on the east wall at y 3.0-3.8, the map
on the west wall.

Moving: the desk fan turning, a letter lifting in its draught, the lamp's
light wavering as the power sags.
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
from mathutils import Matrix, Vector  # noqa: E402

X0, X1, Y0, Y1, H = 1.0, 4.6, 1.0, 4.0, 2.5
DOOR = (2.5, 3.4)
SWIN = (3.75, 4.35)
EWIN = (1.6, 2.7)
WZ = (1.0, 1.8)
DESK = (3.2, 2.35)


def settle(ob, offset, rot=None):
    """kit.join keeps its first part's frame, and kit.body, bunk, chair,
    crate, shelves and crow then place the result as if it had none: bodies
    stand on end, chairs sink half a metre. Move the mesh back into the
    prop's own frame (children are placed in that frame already)."""
    m = Matrix.Translation(offset)
    if rot is not None:
        m = m @ rot.to_matrix().to_4x4()
    ob.data.transform(m)
    return ob


def body(name, at, heading=0.0, pose="back", **kw):
    ob = kit.body(name, at, heading=heading, pose=pose, **kw)
    j, missing = kit._POSES[pose], kw.get("missing", ())
    a, b = next((Vector(j[p]), Vector(j[q])) for p, q, _, _ in kit._BONES if p not in missing and q not in missing)
    return settle(ob, (a + b) / 2, (b - a).to_track_quat("Z", "Y"))


def chair(name, m, at, rot=0.0, tipped=False):
    return settle(kit.chair(name, m, at, rot=rot, tipped=tipped), (0, 0, 0.45))


def umbrella(name, centre, r, facing_up=True):
    """The Umbrella Corporation's mark: an octagon of eight wedges, red and white in turn."""
    red = reb.mat_plain("Umbrella red", (0.45, 0.02, 0.02), 0.5)
    white = mat("white paint")
    rv, rf, wv, wf = [], [], [], []
    c = Vector(centre)
    for i in range(8):
        a0, a1 = 2 * math.pi * i / 8 + math.pi / 8, 2 * math.pi * (i + 1) / 8 + math.pi / 8
        v, f = (rv, rf) if i % 2 == 0 else (wv, wf)
        k = len(v)
        v += [tuple(c), tuple(c + Vector((math.cos(a0) * r, math.sin(a0) * r, 0))), tuple(c + Vector((math.cos(a1) * r, math.sin(a1) * r, 0)))]
        f.append((k, k + 1, k + 2))
    reb.mesh_object(f"{name} red", rv, rf, red, smooth=False)
    reb.mesh_object(f"{name} white", wv, wf, white, smooth=False)


def build():
    rng = random.Random(23)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.camera((4.45, 3.85, 2.3), (2.6, 1.4, 0.6), 200, "high in the south-east corner: the foreman against the wall, the spray, the desk, the stove")
    room.camera((4.45, 1.15, 2.3), (1.7, 3.5, 0.5), 200, "high in the north-east corner over the fan: the safe, the door, the map")
    room.camera((1.15, 3.85, 2.3), (3.9, 1.6, 0.6), 200, "high in the south-west corner over the safe: the desk side on, the empty gun rack, the fan")

    # ---- Materials.
    pine = kit.boards("Office panelling", (0.36, 0.26, 0.15), width=0.14, grime=0.6)
    floor_m = kit.dirtied(mat("planks"), 0.6, scale=1.5)
    ceil_m = kit.boards("Office ceiling", (0.3, 0.24, 0.16), width=0.12)
    frame_m = mat("dark wood")
    desk_m = reb.mat_wood("Desk oak", (0.22, 0.13, 0.07))
    steel_green = reb.mat_surface("Office green", [(0.0, (0.08, 0.12, 0.09)), (0.8, (0.13, 0.18, 0.13)), (1.0, (0.15, 0.1, 0.06))], scale=8, rough=0.45, bump=0.1)
    safe_m = reb.mat_surface("Safe black", [(0.0, (0.02, 0.02, 0.02)), (0.8, (0.05, 0.05, 0.05)), (1.0, (0.1, 0.06, 0.03))], scale=10, rough=0.35, bump=0.1)
    brass = reb.mat_metal("Brass", (0.5, 0.36, 0.12), 0.35)
    spray = reb.mat_surface("Spray", [(0.0, (0.015, 0.002, 0.002)), (0.6, (0.05, 0.006, 0.004)), (1.0, (0.03, 0.004, 0.003))], scale=30, rough=0.35, bump=0.3)

    # ---- The shell.
    kit.walls(X0, Y0, X1, Y1, H, pine, openings=[("s", DOOR[0], DOOR[1], 0.0, 2.05), ("s", SWIN[0], SWIN[1], WZ[0], WZ[1]), ("e", EWIN[0], EWIN[1], WZ[0], WZ[1])], ceiling=ceil_m)
    kit.plank_floor(X0 - 0.1, Y0 - 0.1, X1 + 0.1, Y1 + 0.1, floor_m, along="y", seed=4)
    reb.prim("cube", "Skirting", frame_m, ((X0 + X1) / 2, Y0 + 0.01, 0.06), (X1 - X0, 0.02, 0.12))
    glass_m = reb.mat_glass("Grimy glass", (0.42, 0.44, 0.4))
    reb.prim("cube", "South window glass", glass_m, (sum(SWIN) / 2, Y1 + 0.06, sum(WZ) / 2), (SWIN[1] - SWIN[0], 0.01, WZ[1] - WZ[0]))
    reb.prim("cube", "East window glass", glass_m, (X1 + 0.06, sum(EWIN) / 2, sum(WZ) / 2), (0.01, EWIN[1] - EWIN[0], WZ[1] - WZ[0]))
    reb.prim("cube", "East window bar", frame_m, (X1 + 0.03, sum(EWIN) / 2, sum(WZ) / 2), (0.04, 0.04, WZ[1] - WZ[0]))
    reb.prim("cube", "South sill", frame_m, (sum(SWIN) / 2, Y1 - 0.04, WZ[0] - 0.02), (SWIN[1] - SWIN[0] + 0.1, 0.1, 0.04))
    reb.prim("cube", "East sill", frame_m, (X1 - 0.04, sum(EWIN) / 2, WZ[0] - 0.02), (0.1, EWIN[1] - EWIN[0] + 0.1, 0.04))
    kit.text("KEEP OUT on the glass", "KEEP OUT", mat("red paint"), (sum(SWIN) / 2, Y1 + 0.05, 1.4), size=0.09, rot=(math.pi / 2, 0, math.pi))
    for x in (DOOR[0] - 0.04, DOOR[1] + 0.04):
        reb.prim("cube", "Door frame", frame_m, (x, Y1 + 0.04, 1.05), (0.08, 0.16, 2.1))
    reb.prim("cube", "Door head", frame_m, (sum(DOOR) / 2, Y1 + 0.04, 2.09), (DOOR[1] - DOOR[0] + 0.16, 0.16, 0.08))
    reb.prim("cube", "Door, open", mat("green paint"), (DOOR[0] - 0.05, Y1 + 0.52, 1.02), (0.05, 0.85, 2.04), rot=(0, 0, 0.15))

    # ---- Outside the door and the windows: the yard (moved 0.4 south from its own plan).
    reb.prim("cube", "Outside, mud", kit.dirtied(mat("mud"), 0.6), (3.0, 12.0, -0.1), (30, 16, 0.2))
    reb.prim("cube", "Outside, step", mat("planks"), (sum(DOOR) / 2, Y1 + 0.4, 0.06), (1.2, 0.44, 0.14))
    reb.prim("cube", "Outside, mess", kit.boards("Mess boards", (0.42, 0.4, 0.36), width=0.18), (-0.7, 9.9, 1.4), (5.6, 9.2, 2.8))
    reb.prim("cube", "Outside, mess roof", mat("tin"), (-0.7, 9.9, 3.1), (6.4, 9.8, 0.1))
    reb.prim("cube", "Outside, bunkhouse", kit.boards("Bunkhouse boards", (0.17, 0.11, 0.07), width=0.22), (11.5, -0.5, 1.2), (11.2, 5.2, 2.4))
    reb.prim("cube", "Outside, bunkhouse roof", mat("tin"), (11.5, -0.5, 2.6), (11.8, 5.8, 0.1))
    kit.rod("Outside, bell post", mat("dark wood"), (3.2, 7.7, 0), (3.2, 7.7, 2.9), 0.07)
    reb.prim("cone", "Outside, bell", reb.mat_metal("Bell bronze", (0.45, 0.3, 0.12), 0.4), (3.2, 8.25, 2.5), (0.42, 0.42, 0.38), top=0.45)
    kit.rod("Outside, line pole", mat("dark wood"), (5.6, 3.0, 0), (5.6, 3.0, 2.15), 0.04)
    kit.rod("Outside, washing line", mat("canvas"), (5.6, 3.0, 2.05), (9.8, 3.8, 2.05), 0.006, 4)
    reb.cloth("Outside, washing", mat("flannel"), (6.3, 3.13, 1.7), (0.6, 0.7), rot=(math.pi / 2, 0, 0.19), cuts=6, lumps=0.03, seed=1)
    reb.prim("cube", "Outside, far trees", reb.mat_plain("Far trees", (0.05, 0.07, 0.05), 0.9), (3.0, 26, 8), (80, 1, 16))
    reb.prim("cube", "Outside, far trees east", reb.mat_plain("Far trees", (0.05, 0.07, 0.05), 0.9), (24, 6, 8), (1, 60, 16))

    # ---- The stove in the corner, cold now, and its pipe.
    stove = reb.prim("cube", "Box stove", mat("iron"), (1.45, 1.8, 0.35), (0.5, 0.45, 0.6), bevel=0.02)
    reb.mask(reb.wall(stove))
    kit.rod("Stovepipe", mat("rust"), (1.6, 1.8, 0.65), (1.6, 1.8, H), 0.06)
    reb.prim("cube", "Kettle", mat("steel"), (1.4, 1.8, 0.72), (0.18, 0.18, 0.14), bevel=0.03)
    kit.splat("Ash on the floor", reb.mat_plain("Ash", (0.15, 0.14, 0.13), 0.9), (1.75, 1.85, 0.0), 0.2, seed=2)

    # ---- The desk: ledger, letters, the lamp still on, a bottle and a glass.
    desk = kit.table("Foreman's desk", desk_m, (DESK[0], DESK[1], 0.0), size=(1.35, 0.72, 0.76))
    reb.mask(reb.wall(desk))
    reb.prim("cube", "Desk front", desk_m, (DESK[0], DESK[1] + 0.34, 0.4), (1.3, 0.03, 0.66))
    reb.prim("cube", "Drawers", desk_m, (DESK[0] + 0.45, DESK[1], 0.4), (0.38, 0.66, 0.66))
    reb.prim("cube", "Blotter", reb.mat_plain("Blotter", (0.12, 0.14, 0.1), 0.9), (DESK[0], DESK[1], 0.762), (0.6, 0.42, 0.004))
    reb.prim("cube", "Ledger", reb.mat_plain("Ledger cover", (0.1, 0.12, 0.2), 0.7), (DESK[0] - 0.1, DESK[1] + 0.02, 0.77), (0.42, 0.32, 0.015), rot=(0, 0, 0.1))
    reb.prim("cube", "Ledger pages", mat("old paper"), (DESK[0] - 0.1, DESK[1] + 0.02, 0.779), (0.4, 0.3, 0.003), rot=(0, 0, 0.1))
    for i in range(7):
        kit.rod(f"Struck name {i}", mat("black"), (DESK[0] - 0.26, DESK[1] - 0.1 + i * 0.035, 0.782), (DESK[0] + 0.05, DESK[1] - 0.09 + i * 0.035, 0.782), 0.003, 4)
    # Umbrella's letters, the top one with its mark.
    for i, (x, y, a) in enumerate(((DESK[0] + 0.35, DESK[1] - 0.05, 0.3), (DESK[0] + 0.42, DESK[1] + 0.12, -0.2), (DESK[0] - 0.5, DESK[1] - 0.15, 0.6))):
        reb.prim("cube", f"Letter {i}", mat("paper"), (x, y, 0.763 + i * 0.002), (0.21, 0.28, 0.002), rot=(0, 0, a))
    umbrella("Letterhead", (DESK[0] + 0.33, DESK[1] - 0.14, 0.768), 0.035)
    for i in range(5):
        reb.prim("cube", f"Typed line {i}", mat("black"), (DESK[0] + 0.36 - i * 0.005, DESK[1] - 0.06 + i * 0.03, 0.767), (0.15, 0.004, 0.001), rot=(0, 0, 0.3))
    flutter = reb.prim("cube", "Letter in the draught", mat("paper"), (0, 0.13, 0.0), (0.21, 0.26, 0.002))
    flutter_pivot = reb.prim("sphere", "Paperweight", brass, (DESK[0] - 0.42, DESK[1] + 0.05, 0.775), (0.05, 0.05, 0.03))
    flutter.parent = flutter_pivot
    flutter_pivot.rotation_euler = (0.1, 0, 0.2)
    lamp_m = reb.mat_emit("Lamp shade glow", (1.0, 0.7, 0.35), 4)
    reb.prim("cyl", "Lamp base", brass, (DESK[0] - 0.45, DESK[1] - 0.22, 0.78), (0.12, 0.12, 0.03))
    kit.rod("Lamp stem", brass, (DESK[0] - 0.45, DESK[1] - 0.22, 0.78), (DESK[0] - 0.45, DESK[1] - 0.22, 1.08), 0.01)
    reb.prim("cyl", "Lamp shade", reb.mat_plain("Banker green", (0.03, 0.18, 0.08), 0.3), (DESK[0] - 0.4, DESK[1] - 0.22, 1.1), (0.3, 0.13, 0.08), rot=(0, math.pi / 2, 0), segments=12)
    reb.prim("cyl", "Lamp tube", lamp_m, (DESK[0] - 0.4, DESK[1] - 0.22, 1.07), (0.02, 0.02, 0.24), rot=(0, math.pi / 2, 0), segments=8)
    lamp = reb.point("Desk lamp", (DESK[0] - 0.4, DESK[1] - 0.22, 1.0), 25, (1.0, 0.68, 0.36), 0.08)
    reb.prim("cyl", "Whisky bottle", mat("bottle"), (DESK[0] + 0.55, DESK[1] + 0.2, 0.89), (0.08, 0.08, 0.26), segments=10)
    reb.prim("cyl", "Glass", mat("glass"), (DESK[0] + 0.4, DESK[1] + 0.25, 0.8), (0.06, 0.06, 0.08), segments=10)
    reb.prim("cyl", "Ashtray", mat("steel"), (DESK[0] + 0.15, DESK[1] + 0.25, 0.77), (0.13, 0.13, 0.025), segments=12)
    reb.prim("cube", "Desk phone", mat("black"), (DESK[0] - 0.55, DESK[1] + 0.18, 0.81), (0.2, 0.22, 0.09), bevel=0.02)

    # ---- The foreman: he went over backwards with the chair and slid down the wall.
    fx = DESK[0] - 0.1
    body("The foreman", (fx, Y0 + 0.02, 0.0), heading=math.pi / 2, pose="slumped", top=reb.mat_plain("Foreman's shirt", (0.32, 0.3, 0.26), 0.9), legs=reb.mat_plain("Work trousers", (0.12, 0.11, 0.08), 0.9), seed=9)
    kit.splat("Blood down his shirt", mat("blood"), (fx - 0.06, Y0 + 0.17, 0.62), 0.12, rot=(math.pi / 2 - 0.2, 0, 0), seed=10, stretch=(1.0, 1.8))
    chair("His chair, over", desk_m, (fx + 0.6, Y0 + 0.62, 0.0), rot=-math.pi / 2 + 0.3, tipped=True)
    reb.wall(reb.prim("cube", "Where he lies", None, (3.37, 1.45, 0.4), (1.25, 0.9, 0.8))).hide_render = True
    kit.splat("Spray on the wall", spray, (fx + 0.05, Y0 + 0.006, 1.35), 0.42, rot=(math.pi / 2, 0, 0), seed=5, stretch=(1.3, 1.0), lumps=0.7, points=36)
    for i in range(14):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.45, 0.85)
        kit.splat(f"Spatter {i}", spray, (fx + math.cos(a) * d * 1.2, Y0 + 0.006, 1.35 + math.sin(a) * d * 0.7), rng.uniform(0.015, 0.04), rot=(math.pi / 2, 0, 0), seed=40 + i)
    for i in range(5):
        x = fx + rng.uniform(-0.3, 0.3)
        reb.prim("cube", f"Run {i}", spray, (x, Y0 + 0.005, 0.95 + rng.uniform(-0.05, 0.05)), (0.025, 0.004, rng.uniform(0.3, 0.55)))
    kit.splat("Spray on the ceiling", spray, (fx + 0.1, Y0 + 0.35, H - 0.004), 0.35, rot=(math.pi, 0, 0), seed=6, stretch=(1.4, 0.8), lumps=0.7)
    kit.splat("Pool under him", mat("blood"), (fx, Y0 + 0.3, 0.0), 0.4, seed=7, stretch=(1.4, 0.8))
    reb.prim("cube", "The shotgun", mat("iron"), (fx + 0.35, Y0 + 0.75, 0.04), (1.0, 0.05, 0.05), rot=(0, 0, 0.6))
    reb.prim("cube", "The shotgun stock", desk_m, (fx - 0.05, Y0 + 0.47, 0.05), (0.32, 0.06, 0.09), rot=(0, 0, 0.6))
    shells = [reb.prim("cyl", "Shell", mat("red paint"), (fx + 0.6 + rng.gauss(0, 0.15), Y0 + 0.9 + rng.gauss(0, 0.1), 0.012), (0.024, 0.024, 0.07), rot=(math.pi / 2, 0, rng.uniform(0, 3)), segments=6) for _ in range(3)]
    kit.join("Shells", shells)

    # ---- The safe in the south-west corner, shut; its dial.
    safe = kit.box("Safe", safe_m, (1.4, 3.55, 0.0), (0.6, 0.6, 0.85), bevel=0.02)
    reb.mask(reb.wall(safe))
    reb.prim("cube", "Safe door", safe_m, (1.4, 3.24, 0.45), (0.5, 0.02, 0.72))
    reb.prim("cyl", "Safe dial", mat("steel"), (1.4, 3.22, 0.6), (0.12, 0.12, 0.03), rot=(math.pi / 2, 0, 0), segments=20)
    reb.prim("cube", "Safe handle", brass, (1.55, 3.22, 0.42), (0.03, 0.04, 0.14))
    kit.text("Safe maker", "MOSLER", reb.mat_plain("Gold leaf", (0.5, 0.38, 0.1), 0.4), (1.4, 3.225, 0.78), size=0.05)
    reb.prim("cube", "Cashbox on the safe", mat("green paint"), (1.35, 3.45, 0.92), (0.3, 0.2, 0.12))

    # ---- The north-east: the filing cabinet, the fan on it, turning.
    cab = kit.box("Filing cabinet", steel_green, (4.25, 1.3, 0.0), (0.5, 0.55, 1.3), bevel=0.01)
    reb.mask(reb.wall(cab))
    for i in range(4):
        reb.prim("cube", f"Drawer front {i}", steel_green, (4.25, 1.58, 0.17 + i * 0.31), (0.44, 0.02, 0.27))
        reb.prim("cube", f"Drawer pull {i}", mat("steel"), (4.25, 1.6, 0.25 + i * 0.31), (0.12, 0.02, 0.025))
    reb.prim("cube", "Drawer pulled out", steel_green, (4.25, 1.78, 0.79), (0.44, 0.4, 0.25))
    kit.papers("Files on the floor", (3.9, 2.0, 0.0), spread=0.6, count=7, seed=8)
    fan_at = Vector((4.25, 1.4, 1.62))
    reb.prim("cyl", "Fan base", steel_green, (4.25, 1.4, 1.32), (0.2, 0.2, 0.04))
    kit.rod("Fan neck", steel_green, (4.25, 1.4, 1.32), fan_at, 0.015)
    reb.prim("sphere", "Fan motor", steel_green, fan_at + Vector((0.04, 0.07, 0)), (0.12, 0.14, 0.12))
    yaw = math.atan2(2.5 - 1.4, 3.0 - 4.25)  # it faces the desk
    hub = reb.prim("sphere", "Fan hub", mat("steel"), fan_at, (0.05, 0.05, 0.05))
    for i in range(4):
        a = i * math.pi / 2
        bl = reb.prim("cube", f"Fan blade {i}", mat("steel"), (0, math.cos(a) * 0.08, math.sin(a) * 0.08), (0.008, 0.11, 0.06), rot=(a, 0.25, 0))
        bl.parent = hub
    hub.rotation_euler = (0, 0, yaw)
    gv, gf = [], []
    for k in range(3):
        r = 0.05 + k * 0.05
        for i in range(16):
            a0, a1 = 2 * math.pi * i / 16, 2 * math.pi * (i + 1) / 16
            p0 = Vector((0, math.cos(a0) * r, math.sin(a0) * r))
            p1 = Vector((0, math.cos(a1) * r, math.sin(a1) * r))
            reb.box(gv, gf, tuple((p0 + p1) / 2), (0.004, (p1 - p0).length, 0.004), 0)
    guard = reb.mesh_object("Fan guard", gv, gf, mat("steel"), smooth=False)
    guard.location = fan_at + Vector((math.cos(yaw), math.sin(yaw), 0)) * 0.03
    guard.rotation_euler = (0, 0, yaw)
    gb = reb.mesh_object("Fan guard back", gv, gf, mat("steel"), smooth=False)
    gb.location = fan_at - Vector((math.cos(yaw), math.sin(yaw), 0)) * 0.03
    gb.rotation_euler = (0, 0, yaw)

    # ---- The east wall: the gun rack, empty; a hook with his hard hat.
    reb.prim("cube", "Gun rack", frame_m, (X1 - 0.03, 3.4, 1.55), (0.05, 0.8, 0.12))
    reb.prim("cube", "Gun rack foot", frame_m, (X1 - 0.06, 3.4, 0.95), (0.1, 0.8, 0.1))
    for i in range(4):
        reb.prim("cube", f"Rack notch {i}", mat("black"), (X1 - 0.055, 3.1 + i * 0.2, 1.6), (0.01, 0.05, 0.05))
        kit.rod(f"Rack peg {i}", frame_m, (X1 - 0.03, 3.1 + i * 0.2, 0.98), (X1 - 0.16, 3.1 + i * 0.2, 0.98), 0.012, 6)
    kit.splat("Clean shape on the wall", reb.mat_plain("Unfaded pine", (0.45, 0.33, 0.19), 0.8), (X1 - 0.006, 3.3, 1.28), 0.05, rot=(0, math.pi / 2, 0), stretch=(1.0, 6.0), seed=3, lumps=0.05)
    reb.prim("sphere", "Hard hat on the floor", reb.mat_plain("Hard hat white", (0.55, 0.53, 0.48), 0.4), (3.75, 3.35, 0.07), (0.3, 0.26, 0.16), rot=(0.4, 0.2, 0))
    reb.cloth("Jacket over the safe", mat("canvas"), (1.4, 3.6, 0.99), (0.55, 0.7), cuts=8, lumps=0.05, seed=4)

    # ---- The west wall: the map of the camp, drawn by hand; a calendar; notices.
    mapc = Vector((X0 + 0.012, 2.85, 1.5))
    reb.prim("cube", "Camp map", mat("old paper"), mapc, (0.006, 0.95, 0.7))
    ink = reb.mat_plain("Ink", (0.05, 0.05, 0.12), 0.6)
    # The camp's plan as she faces the wall: north up, east to her right.
    for name, (bx0, bx1, by0, by1) in (("bunkhouse", (6.0, 17.0, -3.4, 1.6)), ("office", (1.0, 4.6, 0.6, 3.6)), ("mess", (-3.4, 2.0, 5.0, 14.0)), ("workshop", (13.4, 19.2, 13.8, 19.4)), ("mill", (18.5, 24.0, 2.6, 12.2)), ("depot", (-2.0, 6.6, 15.2, 21.0))):
        s = 0.028
        cy = mapc.y + ((bx0 + bx1) / 2 - 8.0) * s
        cz = mapc.z + 0.3 - ((by0 + by1) / 2 + 3.0) * s
        reb.prim("cube", f"Map {name}", ink, (X0 + 0.017, cy, cz), (0.003, (bx1 - bx0) * s, (by1 - by0) * s * 0.9))
    reb.prim("cube", "Map red X", reb.mat_plain("Map red", (0.5, 0.02, 0.02), 0.5), (X0 + 0.018, mapc.y + (16.3 - 8.0) * 0.028, mapc.z + 0.3 - (16.6 + 3.0) * 0.028), (0.003, 0.06, 0.06), rot=(0.785, 0, 0))
    kit.text("Map title", "CAMP 4", ink, (X0 + 0.02, mapc.y, mapc.z + 0.3), size=0.06, rot=(math.pi / 2, 0, math.pi / 2))
    for i, (y, z) in enumerate(((2.05, 1.6), (2.25, 1.45), (3.55, 1.7))):
        reb.prim("cube", f"Notice {i}", mat("paper") if i % 2 else mat("old paper"), (X0 + 0.01, y, z), (0.006, 0.2, 0.28))

    # ---- Light: grey noon through the door and the windows, his lamp, a fill.
    kit.time_light("noon", sun_heading=200, sun_energy=1.5, sky=((0.5, 0.52, 0.54), (0.36, 0.39, 0.43), 0.8))
    reb.spot("Window light south", (sum(SWIN) / 2, Y1 - 0.15, 1.7), (3.6, 2.6, 0.0), 90, (0.72, 0.78, 0.88), 110, 0.9, 0.5)
    reb.spot("Window light east", (X1 - 0.15, sum(EWIN) / 2, 1.7), (3.0, 2.0, 0.0), 90, (0.72, 0.78, 0.88), 110, 0.9, 0.5)
    reb.spot("Door light", (sum(DOOR) / 2, Y1 + 3.0, 2.3), (sum(DOOR) / 2, Y1 - 2.0, 0.0), 300, (0.75, 0.8, 0.88), 45, 0.8, 0.6)
    reb.point("Fill", (2.8, 2.6, 2.2), 15, (0.6, 0.65, 0.75), 1.0)

    anim = kit.Anim(16)
    anim.spin(hub, axis=0, turns=3, symmetry=4)
    anim.flicker(lamp, lamp_m, depth=0.15, dropouts=1)
    anim.custom(lambda k: setattr(flutter_pivot, "rotation_euler", (0.1 + 0.25 * max(0.0, math.sin(anim.phase(k, 2))), 0, 0.2)))

    # ---- What the game needs.
    room.door("camp-yard", (DOOR[0], Y1 - 0.5, DOOR[1], Y1), arrive=(2.0, 2.75), face=(0, -1))
    room.check((2.0, 1.2, 2.55, 2.4), "The foreman. He sat at his desk and put the shotgun under his chin.\nThe wall behind him is covered in it.")
    room.check((DESK[0] + 0.1, DESK[1] + 0.36, DESK[0] + 0.8, DESK[1] + 0.8), "Letters on Umbrella letterhead. \"The gondola contract is approved in full.\"\n\"The samples are to be kept cold and are not to be opened.\"\n\"Discretion is a condition of the contract.\"")
    room.check((DESK[0] - 0.7, DESK[1] + 0.36, DESK[0] + 0.1, DESK[1] + 0.8), "The payroll ledger. Twenty-one names.\nHe crossed them out, one by one. The last ones aren't crossed out. There was nobody left to do it.")
    room.check((1.1, 2.9, 2.0, 3.25), "A safe. It's locked.\nA combination dial: three numbers.")
    room.check((X0, 2.4, X0 + 0.6, 3.3), "A map of the camp, drawn by hand. Somebody marked a red X by the workshop.")
    room.check((X1 - 0.6, 3.0, X1, 3.8), "A gun rack. Every peg is empty.")
    room.check((3.6, 1.55, X1, 2.2), "A desk fan, still running. The power's still on somewhere.")
    room.entry = "The smell hits first."
    # Many scenes share the render machine's GPU: keep each frame cheap.
    scene = bpy.context.scene
    scene.render.use_persistent_data = True
    scene.cycles.volume_step_rate = 4.0
    scene.cycles.volume_max_steps = 64
    room.export(anim, samples=160)


build()
