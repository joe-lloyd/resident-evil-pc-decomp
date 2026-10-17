"""Camp 4's workshop, noon: the mechanic's shop, tin on a timber frame.

What it tells: Gus, the camp mechanic, boarded the shop's windows from
outside, painted DONT LET THEM IN on its wall, and shut himself in with a
bar across the door. He lived in here for days: a mattress on the floor, a
camp stove, empty tins, a bucket, six days scratched into the tin.
He was already bitten: the bandages on the mattress are black with it.
Then he left. The bar is broken, the bench he pulled across the door is
shoved aside, and his bloody hand is on the door frame on the way out. The
shop is as he left it: an engine hanging on the hoist chains, parts on the
benches, a power cable he cut down still live and spitting sparks. In the
corner, under a pile of logs he stacked on it, a crate stencilled ARKLAY
SKYWAY - SPARE: the gondola's spare drive cog. The logs are far too heavy
to shift by hand. A player should see the crate, and that the logs are in
the way.

Metres: the floor is x 1.0-6.8, y 1.0-6.6, 3.0 high (in the yard the
workshop is x 13.4-19.2, y 13.8-19.4: this room is it moved 12.4 west and
12.8 north). The door is in the north wall at x 2.2-3.4, 2.3 high, out to
the yard. Windows, boarded outside, in the north wall at x 4.6-5.8 and the
west wall at y 2.6-3.8, from 1.1 to 1.9 high. The bench runs along the west
wall; the hoist's I-beam crosses at y 3.8, the engine hanging from it at x
2.9; the crate and its logs are in the south-east corner; Gus's mattress
lies along the south wall in the west; the cut cable hangs at (4.3, 2.3).

Moving: the cut cable swinging and sparking, the work lamp on the bench
flickering with it, the hoist chains swaying.
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

X0, X1, Y0, Y1, H = 1.0, 6.8, 1.0, 6.6, 3.0
DOOR = (2.2, 3.4)
NWIN = (4.6, 5.8)
WWIN = (2.6, 3.8)
WZ = (1.1, 1.9)
BEAM_Y = 3.8
CRATE = (5.85, 5.75)
CABLE = (4.3, 2.3)


def crate(name, m, at, size=(0.6, 0.5, 0.5), rot=0.0, open_=False):
    return kit.crate(name, m, at, size=size, rot=rot, open_=open_)


def corrugated(name, rgb, rust=(0.3, 0.13, 0.05), pitch=0.1):
    """Corrugated tin: ridges every `pitch` metres along x + y, rust in blotches."""
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Roughness"].default_value = 0.55
    bsdf.inputs["Metallic"].default_value = 0.3
    n = reb.noise_tex(nodes, links, 1.6, 8, 0.65)
    col = reb.ramp(nodes, links, n.outputs["Fac"], [(0.35, tuple(c * 0.6 for c in rgb)), (0.55, rgb), (0.72, rust), (1.0, tuple(c * 0.6 for c in rust))])
    links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Object"], sep.inputs["Vector"])
    add = nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    links.new(sep.outputs["X"], add.inputs[0])
    links.new(sep.outputs["Y"], add.inputs[1])
    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 2 * math.pi / pitch
    links.new(add.outputs[0], mul.inputs[0])
    sine = nodes.new("ShaderNodeMath")
    sine.operation = "SINE"
    links.new(mul.outputs[0], sine.inputs[0])
    reb.bumped(nodes, links, bsdf, sine.outputs[0], 0.6, 0.01)
    return m


def chain(name, a, b, links_=10, sag=0.0):
    """A chain of flat links from a to b, as one mesh."""
    a, b = Vector(a), Vector(b)
    v, f = [], []
    for i in range(links_):
        p = a.lerp(b, (i + 0.5) / links_) - Vector((0, 0, sag * math.sin(math.pi * (i + 0.5) / links_)))
        d = (b - a).normalized()
        yaw = math.atan2(d.y, d.x) + (math.pi / 2 if i % 2 else 0)
        L = (b - a).length / links_
        reb.box(v, f, tuple(p), (0.03, 0.012, L * 1.15), yaw)
    return reb.mesh_object(name, v, f, mat("iron"), smooth=False)


def build():
    rng = random.Random(71)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.ground("concrete")
    room.camera((1.15, 6.45, 2.6), (5.2, 2.2, 0.5), 200, "high in the south-west corner over Gus's mattress: the door, the engine on the hoist, the cable sparking")
    room.camera((1.15, 1.15, 2.6), (5.4, 5.3, 0.5), 200, "high in the north-west corner by the door: the crate under its logs, the hanging engine, the tyres")
    room.camera((6.65, 1.15, 2.6), (2.0, 5.4, 0.5), 200, "high in the north-east corner: the bench and vice, Gus's mattress, the cable spitting sparks")

    # ---- Materials.
    tin = corrugated("Workshop tin", (0.22, 0.24, 0.23))
    stud_m = reb.mat_wood("Studs", (0.22, 0.16, 0.1))
    concrete = kit.dirtied(mat("concrete"), 0.8, scale=1.0)
    oil = reb.mat_plain("Oil stain", (0.02, 0.018, 0.015), 0.5)
    bench_m = reb.mat_wood("Bench top", (0.2, 0.14, 0.08))
    red_chest = reb.mat_plain("Tool chest red", (0.35, 0.04, 0.03), 0.4)
    engine_m = reb.mat_metal("Engine grey", (0.12, 0.13, 0.13), 0.55)
    crate_m = reb.mat_wood("Crate pine", (0.38, 0.28, 0.15))
    stencil = reb.mat_plain("Stencil black", (0.02, 0.02, 0.02), 0.8)
    bandage = reb.mat_surface("Black bandage", [(0.0, (0.45, 0.42, 0.36)), (0.5, (0.3, 0.22, 0.15)), (0.7, (0.1, 0.02, 0.01)), (1.0, (0.04, 0.01, 0.005))], scale=14, bump=0.2)

    # ---- The shell: tin on timber studs, a concrete floor, open rafters.
    kit.walls(X0, Y0, X1, Y1, H, tin, openings=[("n", DOOR[0], DOOR[1], 0.0, 2.3), ("n", NWIN[0], NWIN[1], WZ[0], WZ[1]), ("w", WWIN[0], WWIN[1], WZ[0], WZ[1])],
              floor=concrete, ceiling=corrugated("Roof tin underside", (0.18, 0.19, 0.18)))
    sv, sf = [], []
    for x in (1.0, 2.2, 3.4, 4.6, 5.8, 6.8):
        for y in (Y0 + 0.05, Y1 - 0.05):
            if not (DOOR[0] - 0.05 < x < DOOR[1] + 0.05 and y < 2):
                reb.box(sv, sf, (x, y, H / 2), (0.1, 0.1, H), 0)
    for y in (1.0, 2.4, 3.8, 5.2, 6.6):
        for x in (X0 + 0.05, X1 - 0.05):
            reb.box(sv, sf, (x, y, H / 2), (0.1, 0.1, H), 0)
    for z in (1.0, 2.1):
        reb.box(sv, sf, ((X0 + X1) / 2, Y1 - 0.06, z), (X1 - X0, 0.06, 0.1), 0)
        reb.box(sv, sf, (X1 - 0.06, (Y0 + Y1) / 2, z), (0.06, Y1 - Y0, 0.1), 0)
    for x in (1.6, 2.8, 4.0, 5.2, 6.4):
        reb.box(sv, sf, (x, (Y0 + Y1) / 2, H - 0.12), (0.08, Y1 - Y0, 0.18), 0)
    reb.mesh_object("Studs and rafters", sv, sf, stud_m, smooth=False)
    for i in range(8):
        kit.splat(f"Oil stain {i}", oil, (rng.uniform(2.0, 6.0), rng.uniform(2.0, 6.0), 0.0), rng.uniform(0.15, 0.45), seed=i, lumps=0.5)
    # The windows: glass, boards nailed across outside, more nailed inside, light in slits.
    glass_m = reb.mat_glass("Grimy glass", (0.4, 0.42, 0.38))
    reb.prim("cube", "North window glass", glass_m, (sum(NWIN) / 2, Y0 - 0.06, sum(WZ) / 2), (NWIN[1] - NWIN[0], 0.01, WZ[1] - WZ[0]))
    reb.prim("cube", "West window glass", glass_m, (X0 - 0.06, sum(WWIN) / 2, sum(WZ) / 2), (0.01, WWIN[1] - WWIN[0], WZ[1] - WZ[0]))
    kit.barricade("Boards outside the north window", mat("planks"), (NWIN[0] - 0.1, Y0 - 0.2), (NWIN[1] + 0.1, Y0 - 0.2), WZ[0] + 0.1, WZ[1] - 0.1, count=3, seed=int(sum(NWIN) * 5))
    kit.barricade("Boards outside the west window", mat("planks"), (X0 - 0.2, WWIN[0] - 0.1), (X0 - 0.2, WWIN[1] + 0.1), WZ[0] + 0.1, WZ[1] - 0.1, count=3, seed=int(sum(WWIN) * 5))
    kit.barricade("Boards inside the north window", mat("pine"), (NWIN[0] - 0.15, Y0 + 0.04), (NWIN[1] + 0.15, Y0 + 0.04), WZ[0] + 0.05, WZ[1] - 0.05, count=4, seed=3)
    # The door: open, its frame; the bar broken; the bench shoved aside; his hand on the frame.
    for x in (DOOR[0] - 0.05, DOOR[1] + 0.05):
        reb.prim("cube", "Door frame", stud_m, (x, Y0 - 0.04, 1.2), (0.1, 0.16, 2.4))
        reb.prim("cube", "Bar bracket", mat("iron"), (x + (-0.12 if x < 3 else 0.12), Y0 + 0.06, 1.1), (0.14, 0.08, 0.16))
    reb.prim("cube", "Door head", stud_m, (sum(DOOR) / 2, Y0 - 0.04, 2.35), (DOOR[1] - DOOR[0] + 0.2, 0.16, 0.1))
    reb.prim("cube", "Door, run open", tin, (DOOR[1] + 0.62, Y0 - 0.18, 1.15), (1.2, 0.04, 2.3))
    reb.prim("cube", "Bar, broken", mat("logs"), (2.4, 1.75, 0.06), (0.9, 0.1, 0.1), rot=(0, 0, 0.5))
    reb.prim("cube", "Bar, broken end", mat("logs"), (3.4, 2.05, 0.06), (0.7, 0.1, 0.1), rot=(0, 0, -0.3))
    reb.prim("cube", "Splinters", reb.mat_wood("Fresh wood", (0.45, 0.34, 0.2)), (2.85, 1.85, 0.02), (0.15, 0.06, 0.03), rot=(0, 0, 1.1))
    shoved = kit.table("Heavy bench, shoved aside", bench_m, (1.75, 1.55, 0.0), size=(1.3, 0.6, 0.8), rot=0.35)
    reb.mask(reb.wall(shoved))
    for i in range(3):
        reb.prim("cube", f"Scrape {i}", reb.mat_plain("Scrape", (0.3, 0.29, 0.27), 0.9), (2.3 + i * 0.1, 1.75 + i * 0.05, 0.002), (0.8, 0.02, 0.002), rot=(0, 0, 0.35))
    kit.splat("Hand on the frame", mat("old blood"), (DOOR[1] + 0.09, Y0 + 0.04, 1.15), 0.07, rot=(math.pi / 2, 0, 0), seed=4)
    reb.prim("cube", "Smear down the frame", mat("old blood"), (DOOR[1] + 0.09, Y0 + 0.045, 0.85), (0.04, 0.004, 0.5))
    kit.drag_trail("Drips to the door", mat("old blood"), [(2.0, 5.5), (2.4, 4.4), (2.7, 3.0), (2.9, 1.5), (2.9, 0.6)], width=0.12, seed=5)

    # ---- Outside the door: the yard's mud, the fire pit far off, the bunkhouse.
    reb.prim("cube", "Outside, mud", kit.dirtied(mat("mud"), 0.6), (2.0, -6.0, -0.1), (30, 14, 0.2))
    reb.prim("cube", "Outside, skidder", reb.mat_plain("Skidder yellow", (0.45, 0.3, 0.03), 0.6), (-4.4, 0.2, 1.1), (4.4, 2.4, 2.0))
    reb.prim("cube", "Outside, log deck", mat("bark"), (2.6, -9.3, 0.9), (4.8, 2.2, 1.8))
    reb.prim("cube", "Outside, bunkhouse", kit.boards("Bunkhouse boards", (0.17, 0.11, 0.07), width=0.22), (-0.9, -13.7, 1.2), (11.2, 5.2, 2.4))
    reb.prim("cube", "Outside, sawmill", kit.boards("Mill boards", (0.2, 0.19, 0.17), width=0.3), (11.0, -5.4, 3.0), (10.0, 9.6, 6.0))
    reb.prim("cube", "Outside, far trees", reb.mat_plain("Far trees", (0.05, 0.07, 0.05), 0.9), (2.0, -24, 8), (60, 1, 16))
    reb.prim("cube", "Outside, drums", mat("rust"), (4.8, -0.2, 0.44), (0.6, 0.6, 0.88))

    # ---- The bench along the west wall: the vice, tools, the work lamp still on, the pegboard.
    bench = kit.table("Workbench", bench_m, (1.38, 3.7, 0.0), size=(0.7, 3.2, 0.9))
    reb.mask(reb.wall(bench))
    reb.prim("cube", "Bench shelf", bench_m, (1.38, 3.7, 0.25), (0.62, 3.1, 0.03))
    # The spare drive cog, on the bench (cog).
    room.item("cog", (1.38, 3.2, 0.9))
    vice = [reb.prim("cube", "vice body", mat("green paint"), (1.6, 2.6, 0.98), (0.2, 0.25, 0.14)),
            reb.prim("cube", "vice jaw", mat("green paint"), (1.78, 2.6, 0.98), (0.06, 0.25, 0.14)),
            kit.rod("vice screw", mat("steel"), (1.6, 2.6, 0.97), (1.95, 2.6, 0.97), 0.015, 6),
            kit.rod("vice handle", mat("steel"), (1.95, 2.45, 0.97), (1.95, 2.75, 0.97), 0.01, 6)]
    kit.join("Vice", vice)
    reb.prim("cube", "Pipe in the vice", mat("rust"), (1.72, 2.6, 1.03), (0.04, 0.5, 0.04))
    reb.prim("cube", "Pegboard", reb.mat_plain("Pegboard", (0.35, 0.28, 0.18), 0.8), (X0 + 0.03, 4.6, 1.55), (0.02, 1.4, 0.9))
    for i, (y, z, w, hgt) in enumerate(((4.1, 1.75, 0.04, 0.3), (4.3, 1.7, 0.06, 0.25), (4.55, 1.8, 0.03, 0.35), (4.8, 1.65, 0.12, 0.08), (5.0, 1.75, 0.05, 0.3), (5.15, 1.4, 0.2, 0.06))):
        reb.prim("cube", f"Tool on the board {i}", mat("steel") if i % 2 else red_chest, (X0 + 0.06, y, z), (0.02, w, hgt))
    for i in range(3):
        reb.prim("cube", f"Tool outline, empty {i}", mat("black"), (X0 + 0.045, 4.2 + i * 0.35, 1.3), (0.004, 0.05, 0.25))
    for i in range(6):
        reb.prim("cube", f"Spanner {i}", mat("steel"), (1.4 + rng.uniform(-0.15, 0.15), 3.5 + rng.uniform(-0.6, 0.9), 0.905), (0.22, 0.03, 0.01), rot=(0, 0, rng.uniform(0, 3)))
    for i in range(4):
        reb.prim("cyl", f"Piston {i}", mat("steel"), (1.45, 4.5 + i * 0.16, 0.97), (0.11, 0.11, 0.13), segments=12)
    reb.prim("cube", "Carburettor", engine_m, (1.35, 5.0, 0.98), (0.18, 0.16, 0.15))
    lamp_glow = reb.mat_emit("Work lamp", (1.0, 0.75, 0.45), 12)
    reb.prim("sphere", "Work lamp bulb", lamp_glow, (1.5, 3.3, 1.12), (0.08, 0.08, 0.1))
    cage = []
    for i in range(6):
        a = math.pi * i / 3
        cage.append(kit.rod("cage", mat("iron"), (1.5 + 0.06 * math.cos(a), 3.3 + 0.06 * math.sin(a), 1.05), (1.5 + 0.06 * math.cos(a), 3.3 + 0.06 * math.sin(a), 1.2), 0.004, 4))
    kit.join("Lamp cage", cage)
    kit.rod("Lamp flex", mat("black"), (1.5, 3.3, 1.05), (1.4, 3.4, 0.91), 0.008, 4)
    lamp = reb.point("Work lamp light", (1.6, 3.3, 1.2), 30, (1.0, 0.7, 0.42), 0.05)

    # ---- The north bench under the boarded window: the red tool chest, engine parts.
    chest = kit.box("Tool chest", red_chest, (6.3, 1.45, 0.0), (0.7, 0.5, 1.0), bevel=0.01)
    reb.mask(reb.wall(chest))
    for i in range(5):
        reb.prim("cube", f"Drawer line {i}", mat("black"), (6.3, 1.71, 0.2 + i * 0.17), (0.6, 0.01, 0.01))
    reb.prim("cube", "Drawer, open", red_chest, (6.3, 1.85, 0.7), (0.6, 0.4, 0.1))
    nb = kit.table("Parts bench", bench_m, (5.0, 1.35, 0.0), size=(1.3, 0.6, 0.9))
    reb.mask(reb.wall(nb))
    reb.prim("cyl", "Chainsaw bar", mat("steel"), (5.0, 1.35, 0.93), (0.08, 0.08, 0.6), rot=(0, math.pi / 2, 0.2))
    reb.prim("cube", "Chainsaw body", reb.mat_plain("Saw orange", (0.5, 0.18, 0.02), 0.5), (4.6, 1.35, 1.0), (0.3, 0.2, 0.2), bevel=0.03)
    reb.prim("cyl", "Brake drum", mat("rust"), (5.35, 1.3, 0.97), (0.35, 0.35, 0.12), segments=16)

    # ---- The hoist: an I-beam across the shop, chains down to the engine still hanging.
    reb.prim("cube", "I-beam", mat("rust"), ((X0 + X1) / 2, BEAM_Y, 2.82), (X1 - X0, 0.14, 0.2))
    reb.prim("cube", "Beam flange", mat("rust"), ((X0 + X1) / 2, BEAM_Y, 2.72), (X1 - X0, 0.2, 0.03))
    trolley = reb.prim("cube", "Hoist trolley", mat("yellow paint"), (2.9, BEAM_Y, 2.6), (0.3, 0.3, 0.2))
    reb.prim("cube", "Chain block", mat("yellow paint"), (2.9, BEAM_Y, 2.35), (0.25, 0.25, 0.3), bevel=0.03)
    hang = reb.prim("sphere", "Hook pivot", mat("iron"), (2.9, BEAM_Y, 2.2), (0.04, 0.04, 0.04))
    parts = [chain("Hoist chain", (0, 0, 0), (0, 0, -0.75), links_=12),
             reb.prim("cube", "Hook", mat("iron"), (0, 0, -0.8), (0.04, 0.1, 0.12)),
             chain("Sling", (0, 0, -0.85), (-0.3, 0, -1.15), links_=6),
             chain("Sling", (0, 0, -0.85), (0.3, 0, -1.15), links_=6),
             reb.prim("cube", "Engine block", engine_m, (0, 0, -1.4), (0.75, 0.5, 0.5), bevel=0.03),
             reb.prim("cube", "Cylinder head", engine_m, (0, 0, -1.08), (0.7, 0.4, 0.12)),
             reb.prim("cube", "Oil pan", mat("rust"), (0, 0, -1.7), (0.6, 0.4, 0.12)),
             reb.prim("cyl", "Flywheel", mat("iron"), (0.42, 0, -1.4), (0.42, 0.42, 0.05), rot=(0, math.pi / 2, 0), segments=18)]
    for p in parts:
        p.parent = hang
    reb.mask(reb.wall(reb.prim("cube", "Engine footprint", None, (2.9, BEAM_Y, 0.8), (0.9, 0.6, 1.6)))).hide_render = True
    stand = [kit.rod("stand post", mat("rust"), (4.75, 4.55, 0.0), (4.75, 4.55, 0.75), 0.04),
             kit.rod("stand foot", mat("rust"), (4.45, 4.55, 0.03), (5.05, 4.55, 0.03), 0.03),
             kit.rod("stand foot", mat("rust"), (4.75, 4.25, 0.03), (4.75, 4.85, 0.03), 0.03),
             reb.prim("cyl", "stand head", mat("rust"), (4.75, 4.45, 0.75), (0.25, 0.25, 0.05), rot=(math.pi / 2, 0, 0))]
    kit.join("Engine stand, empty", stand)
    kit.splat("Oil under the engine", oil, (2.95, BEAM_Y, 0.0), 0.45, seed=20)
    loose = reb.prim("sphere", "Loose chain top", mat("iron"), (5.6, BEAM_Y, 2.7), (0.04, 0.04, 0.04))
    lc = chain("Loose chain", (0, 0, 0), (0, 0, -1.6), links_=20)
    lc.parent = loose
    reb.prim("cube", "Loose hook", mat("iron"), (0, 0, -1.65), (0.04, 0.1, 0.12)).parent = loose

    # ---- The crate in the south-east: ARKLAY SKYWAY - SPARE, under the logs he stacked on it.
    cx, cy = CRATE
    cr = crate("Spare crate", crate_m, (cx, cy, 0.0), size=(1.2, 0.8, 0.75))
    reb.mask(reb.wall(cr))
    kit.text("Crate words", "ARKLAY SKYWAY", stencil, (cx, cy - 0.41, 0.5), size=0.11)
    kit.text("Crate words 2", "- SPARE -", stencil, (cx, cy - 0.41, 0.33), size=0.1)
    kit.text("Crate words 3", "DRIVE COG  NO 2", stencil, (cx, cy - 0.41, 0.2), size=0.05)
    kit.text("Crate words west", "ARKLAY SKYWAY", stencil, (cx - 0.61, cy, 0.45), size=0.08, rot=(math.pi / 2, 0, -math.pi / 2))
    logs = []
    for row, (n, z) in enumerate(((3, 0.95), (2, 1.33), (1, 1.7))):
        for i in range(n):
            y = cy + (i - (n - 1) / 2) * 0.38
            logs.append(((cx - 1.0, y + rng.uniform(-0.03, 0.03), z), (cx + 0.9, y + rng.uniform(-0.03, 0.03), z), 0.19 + rng.uniform(-0.02, 0.02)))
    lv, lf, ev, ef = [], [], [], []
    seg = 10
    for a, b, r in logs:
        a, b = Vector(a), Vector(b)
        d = (b - a).normalized()
        u = d.orthogonal().normalized()
        w = d.cross(u)
        k = len(lv)
        for p in (a, b):
            for j in range(seg):
                t = 2 * math.pi * j / seg
                lv.append(tuple(p + (u * math.cos(t) + w * math.sin(t)) * r))
        for j in range(seg):
            lf.append((k + j, k + (j + 1) % seg, k + seg + (j + 1) % seg, k + seg + j))
        for p, base in ((a, k), (b, k + seg)):
            c = len(ev)
            ev.append(tuple(p))
            ev.extend(lv[base:base + seg])
            ef.extend((c, c + 1 + j, c + 1 + (j + 1) % seg) for j in range(seg))
    reb.mask(reb.mesh_object("Logs on the crate", lv, lf, mat("bark")))
    reb.wall(reb.prim("cube", "Log stack footprint", None, (5.85, 5.95, 0.5), (1.9, 1.3, 1.0))).hide_render = True
    reb.mesh_object("Log ends", ev, ef, reb.mat_surface("Sawn log end", [(0.0, (0.2, 0.14, 0.08)), (0.5, (0.42, 0.32, 0.19)), (1.0, (0.3, 0.2, 0.11))], scale=9, bump=0.3), smooth=False)
    kit.splat("Bark and dirt", kit.dirtied(mat("dirt"), 0.5), (cx - 0.4, cy - 0.7, 0.0), 0.5, seed=21, stretch=(1.5, 0.7))
    kit.drag_trail("Drag marks of the logs", reb.mat_plain("Bark scrape", (0.12, 0.09, 0.06), 0.9), [(2.8, 1.6), (3.6, 3.0), (4.6, 4.6), (5.2, 5.3)], width=0.25, seed=22)
    # Tyres, welding bottles chained to the wall, a drum.
    tv, tf = [], []
    for i in range(4):
        k = len(tv)
        for j in range(16):
            a = 2 * math.pi * j / 16
            for rr, zz in ((0.42, 0.0), (0.42, 0.24), (0.22, 0.24), (0.22, 0.0)):
                tv.append((3.92 + rr * math.cos(a), 1.48 + rr * math.sin(a), 0.01 + i * 0.25 + zz))
        for j in range(16):
            jn = (j + 1) % 16
            for q in range(4):
                qn = (q + 1) % 4
                tf.append((k + j * 4 + q, k + jn * 4 + q, k + jn * 4 + qn, k + j * 4 + qn))
    reb.mask(reb.wall(reb.mesh_object("Tyres", tv, tf, mat("rubber")), "circle"))
    for i, (y, m) in enumerate(((2.3, mat("green paint")), (2.55, reb.mat_plain("Bottle maroon", (0.25, 0.03, 0.03), 0.4)))):
        reb.wall(reb.prim("cyl", f"Gas bottle {i}", m, (6.55, y, 0.7), (0.22, 0.22, 1.4), segments=14), "circle")
        reb.prim("sphere", f"Bottle shoulder {i}", m, (6.55, y, 1.4), (0.22, 0.22, 0.14))
    kit.rod("Bottle chain", mat("iron"), (X1 - 0.02, 2.1, 1.1), (X1 - 0.02, 2.75, 1.1), 0.01, 4)
    reb.wall(kit.drum("Waste oil drum", mat("rust"), (4.35, 6.25, 0.0)), "circle")

    # ---- Gus's corner: a mattress on the floor, his tins, the stove, the bandages, the tally on the wall.
    reb.prim("cube", "Mattress on the floor", mat("mattress"), (2.05, 6.15, 0.08), (1.9, 0.75, 0.16), bevel=0.04)
    reb.cloth("His blanket", mat("flannel"), (1.7, 6.1, 0.2), (1.1, 0.8), lumps=0.06, seed=7)
    reb.wall(reb.prim("cube", "Mattress footprint", None, (2.05, 6.15, 0.1), (1.9, 0.75, 0.2))).hide_render = True
    for i in range(4):
        reb.cloth(f"Bandage {i}", bandage, (2.5 + rng.uniform(-0.2, 0.4), 5.6 + rng.uniform(-0.2, 0.1), 0.012), (0.18, 0.08), rot=(0, 0, rng.uniform(0, 3)), cuts=6, lumps=0.01, seed=i)
    kit.splat("Where he lay", mat("old blood"), (2.6, 6.15, 0.165), 0.18, seed=23, stretch=(1.4, 0.8))
    tins = []
    for i in range(9):
        tins.append(reb.prim("cyl", "Empty tin", mat("steel") if i % 3 else mat("rust"), (3.3 + rng.gauss(0, 0.25), 5.9 + rng.gauss(0, 0.2), 0.05 if i % 2 else 0.035), (0.08, 0.08, 0.1), rot=(0 if i % 2 else math.pi / 2, 0, rng.uniform(0, 3)), segments=10))
    kit.join("Empty tins", tins)
    reb.prim("cube", "Camp stove", mat("green paint"), (3.6, 6.35, 0.08), (0.3, 0.22, 0.16))
    reb.prim("cyl", "Pan on the stove", mat("iron"), (3.6, 6.35, 0.19), (0.2, 0.2, 0.06), segments=12)
    reb.prim("cyl", "Bucket", reb.mat_metal("Galvanised", (0.32, 0.33, 0.32), 0.45), (1.25, 5.6, 0.15), (0.3, 0.3, 0.3), segments=14)
    _, _, wick = kit.lantern("Burnt-out lantern", (2.9, 6.4, 0.0), energy=0.0)
    reb.emit_strength(wick, 0.0)
    kit.bottles("Bottles by the mattress", (1.4, 5.55, 0.0), count=3, spread=0.3, seed=9, tipped=0.6)
    tally = []
    for g in range(1):
        for i in range(5):
            x = 1.5 + g * 0.3 + i * 0.045
            if i < 4:
                tally.append(kit.rod("Tally", mat("steel"), (x, Y1 - 0.02, 1.15), (x, Y1 - 0.02, 0.9), 0.006, 4))
            else:
                tally.append(kit.rod("Tally", mat("steel"), (x - 0.19, Y1 - 0.02, 0.95), (x + 0.02, Y1 - 0.02, 1.1), 0.006, 4))
    tally.append(kit.rod("Tally", mat("steel"), (1.85, Y1 - 0.02, 1.15), (1.85, Y1 - 0.02, 0.9), 0.006, 4))
    kit.join("Tally of days", tally)
    reb.prim("cube", "Note", mat("paper"), (2.4, 6.1, 0.168), (0.15, 0.2, 0.002), rot=(0, 0, 0.3))

    # ---- The cut cable from the ceiling, swinging, spitting sparks; the dead strip light hanging.
    kit.rod("Conduit", mat("rust"), (X1, CABLE[1], H - 0.25), (CABLE[0], CABLE[1], H - 0.25), 0.02)
    pivot = reb.prim("sphere", "Cable clamp", mat("iron"), (CABLE[0], CABLE[1], H - 0.25), (0.04, 0.04, 0.04))
    cable = kit.rod("Cut cable", mat("black"), (0, 0, 0), (0, 0, -1.35), 0.012, 6)
    cable.parent = pivot
    spark_m = reb.mat_emit("Spark", (0.75, 0.85, 1.0), 40)
    sv2, sf2 = [], []
    srng = random.Random(3)
    for i in range(14):
        d = Vector((srng.uniform(-1, 1), srng.uniform(-1, 1), srng.uniform(-1.2, 0.4))).normalized() * srng.uniform(0.06, 0.25)
        reb.box(sv2, sf2, tuple(d / 2 + Vector((0, 0, -1.37))), (0.006, 0.006, d.length), math.atan2(d.y, d.x))
    sparks = reb.mesh_object("Sparks", sv2, sf2, spark_m, smooth=False)
    sparks.parent = pivot
    spark_light = reb.point("Spark light", (CABLE[0], CABLE[1], H - 1.65), 60, (0.7, 0.8, 1.0), 0.05)
    kit.splat("Scorch under the cable", mat("black"), (CABLE[0], CABLE[1], 0.0), 0.3, seed=24, lumps=0.6)
    reb.prim("cube", "Strip light, hanging", reb.mat_plain("Strip light dead", (0.5, 0.52, 0.5), 0.4), (4.9, 4.9, 2.3), (1.2, 0.12, 0.08), rot=(0, 0.6, 0.2))
    kit.rod("Strip light chain", mat("iron"), (5.4, 5.0, H - 0.2), (5.38, 4.98, 2.55), 0.006, 4)

    # ---- Light: grey noon through the door and the slits in the boards, the work lamp, the sparks.
    kit.time_light("noon", sun_heading=200, sun_energy=1.5, sky=((0.5, 0.52, 0.54), (0.36, 0.39, 0.43), 0.8))
    reb.spot("Door light", (sum(DOOR) / 2, Y0 - 3.0, 2.3), (sum(DOOR) / 2, Y0 + 2.5, 0.0), 420, (0.75, 0.8, 0.88), 45, 0.8, 0.6)
    reb.spot("Slits through the north boards", (sum(NWIN) / 2, Y0 + 0.1, 1.5), (sum(NWIN) / 2 - 0.3, 3.4, 0.0), 60, (0.72, 0.78, 0.88), 40, 0.3, 0.1)
    reb.spot("Slits through the west boards", (X0 + 0.1, sum(WWIN) / 2, 1.5), (3.6, sum(WWIN) / 2 + 0.3, 0.0), 50, (0.72, 0.78, 0.88), 40, 0.3, 0.1)
    reb.point("Fill", (4.0, 4.0, 2.4), 35, (0.6, 0.65, 0.75), 1.0)

    anim = kit.Anim(16)
    on = {0, 1, 4, 9, 10, 13}

    def spark(k):
        lit = k in on
        sparks.hide_render = not lit
        spark_light.data.energy = 60 if lit else 0
        lamp.data.energy = 30 * (0.55 if lit else 1.0)
        reb.emit_strength(lamp_glow, 12 * (0.55 if lit else 1.0))
        pivot.rotation_euler = (math.radians(6) * math.sin(anim.phase(k)), math.radians(3) * math.cos(anim.phase(k)), 0)
    anim.custom(spark)
    anim.custom(lambda k: setattr(hang, "rotation_euler", (math.radians(1.5) * math.sin(anim.phase(k)), 0, 0)))
    anim.custom(lambda k: setattr(loose, "rotation_euler", (math.radians(4) * math.sin(anim.phase(k) + 1.0), 0, 0)))

    # ---- What the game needs.
    room.door("camp-yard", (DOOR[0], Y0, DOOR[1], Y0 + 0.5), arrive=(2.8, 2.35), face=(0, 1))
    room.check((cx - 0.7, cy - 1.1, cx + 0.7, cy - 0.45), "A crate. ARKLAY SKYWAY - SPARE. DRIVE COG NO 2.\nThe gondola's spare cog. It's under a pile of logs.\nI can't move those. Not by hand.")
    room.check((1.8, 5.1, 3.6, 5.7), "Someone slept here. Bandages, black with blood. A tally scratched in the tin: six days.\nA note: \"Bit on the hand Tues. Can't stay. Don't come looking. Gus.\"")
    room.check((3.8, 1.9, 4.8, 2.7), "A power cable, cut. It's still live. I'm not touching that.")
    room.check((1.75, 2.3, 2.3, 3.2), "A vice, a bench, his tools. The lamp's still on.")
    room.check((2.3, 4.25, 3.5, 4.8), "An engine, hanging on the hoist chains. Nobody's coming back to finish it.")
    room.check((1.9, 1.2, 3.6, 2.3), "He barred the door from inside. The bar's been broken.\nFrom this side.")
    room.entry = "Oil and something worse."
    scene = bpy.context.scene
    scene.render.use_persistent_data = True
    room.export(anim, samples=160)


build()
