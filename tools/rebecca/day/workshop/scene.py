"""The logging camp's workshop, noon: the mechanic's shop, tin on a timber frame.

What it tells: Gus, the camp mechanic, boarded the shop's windows from
outside, painted DONT LET THEM IN on its wall, and shut himself in with a
bar across the door. He lived in here for days: a mattress on the floor, a
camp stove, empty tins, a bucket, six days scratched into the tin.
He was already bitten: the bandages on the mattress are black with it.
Then he left. The bar is broken, the bench he pulled across the door is
shoved aside, and his bloody hand is on the door frame on the way out. The
door is pulled to behind him. The
shop is as he left it: an engine hanging on the hoist chains, parts on the
benches, a power cable he cut down short at the ceiling, still live and
now and then spitting sparks. In the
corner, under a pile of logs he stacked on it with the electric hoist, a
crate stencilled ARKLAY SKYWAY - SPARE: the gondola's spare drive cog. The
hoist still hangs over the pile on its spur rail, its chain choked round
the top log. Its cable runs along the beams and down the east wall to a
box stencilled MILL LINE: the shop ran off the sawmill's dynamo, and the
mill is stopped, so the hoist is dead. The logs are far too heavy to shift
by hand. A player should see the crate, that the logs are in the way, and
that the hoist over them needs the mill's power.

Metres: the floor is x 1.0-6.8, y 1.0-6.6, 3.0 high (in the yard the
workshop is x 13.4-19.2, y 13.8-19.4: this room is it moved 12.4 west and
12.8 north). The door is in the north wall at x 2.2-3.4, 2.3 high, out to
the yard. Windows, boarded outside, in the north wall at x 4.6-5.8 and the
west wall at y 2.6-3.8, from 1.1 to 1.9 high. The bench runs along the west
wall; the hoist's I-beam crosses at y 3.8, the engine hanging from it at x
2.9; a spur rail runs off it at x 5.85 south to the wall, the electric
hoist on it over the crate; the crate and its logs are in the south-east
corner; the hoist's pendant control hangs at (5.85, 4.75), where she works
it; the MILL LINE box is on the east wall at y 4.45; Gus's mattress lies
along the south wall in the west; the cut cable hangs at (4.3, 2.3).

Moving: the cut cable's sparks now and then, the work lamp dipping with
them, the hoist chains barely stirring.

State "crane" (worked at the pendant once the mill's dynamo turns,
day/events.ts): the hoist has wound the logs up off the crate, a choked
bundle hanging on its chain; the crate's lid is off and leant against it,
and the cog (cog) lies in its packing.
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


def bench_clutter(rng, top, yaw, engine_m, red_chest):
    """What is on the bench he dragged across the door: a toolbox open with
    its tray out, a coffee can of bolts tipped over, a gas lantern, a hand
    drill, a mug, a box of shells and a hacksaw, a torn manual."""
    x0, y0, z = top
    c, s_ = math.cos(yaw), math.sin(yaw)

    def at(dx, dy, h=0.0):
        return (x0 + dx * c - dy * s_, y0 + dx * s_ + dy * c, z + h)
    reb.prim("cube", "Toolbox, open", red_chest, at(-0.35, 0.05, 0.1), (0.5, 0.22, 0.2), rot=(0, 0, yaw), bevel=0.01)
    reb.prim("cube", "Toolbox lid", red_chest, at(-0.35, 0.2, 0.22), (0.5, 0.02, 0.2), rot=(-0.5, 0, yaw))
    reb.prim("cube", "Toolbox tray", mat("steel"), at(-0.35, -0.2, 0.03), (0.45, 0.16, 0.05), rot=(0, 0, yaw + 0.1))
    for i in range(4):
        reb.prim("cube", f"Tool in the tray {i}", mat("steel"), at(-0.5 + i * 0.1, -0.2, 0.07), (0.02, 0.14, 0.015), rot=(0, 0, yaw + rng.uniform(-0.2, 0.2)))
    reb.prim("cyl", "Can of bolts", reb.mat_plain("Coffee can red", (0.35, 0.05, 0.03), 0.5), at(0.15, 0.1, 0.06), (0.14, 0.14, 0.18), rot=(math.pi / 2, 0, yaw + 0.8), segments=12)
    bv, bf = [], []
    for _ in range(18):
        p = at(0.3 + rng.uniform(-0.05, 0.25), 0.05 + rng.uniform(-0.15, 0.1), 0.012)
        reb.box(bv, bf, p, (0.04, 0.012, 0.012), rng.uniform(0, 3))
    reb.mesh_object("Spilled bolts", bv, bf, mat("steel"), smooth=False)
    _, _, flame = kit.lantern("Gas lantern, out", at(0.45, -0.15), energy=0.0)
    reb.emit_strength(flame, 0.0)
    reb.prim("cube", "Hand drill", mat("iron"), at(0.05, -0.18, 0.03), (0.32, 0.05, 0.06), rot=(0, 0, yaw - 0.4))
    reb.prim("cyl", "Mug", reb.mat_plain("Mug enamel", (0.5, 0.5, 0.45), 0.4), at(-0.05, 0.18, 0.05), (0.09, 0.09, 0.1), segments=10)
    reb.prim("cube", "Box of shells", reb.mat_plain("Shell box", (0.45, 0.2, 0.05), 0.6), at(0.25, -0.05, 0.03), (0.12, 0.08, 0.06), rot=(0, 0, yaw + 0.3))
    reb.prim("cube", "Hacksaw blade", mat("steel"), at(-0.1, -0.05, 0.005), (0.32, 0.015, 0.005), rot=(0, 0, yaw + 1.2))
    kit.papers("Torn manual", at(0.2, 0.15), spread=0.12, count=3, seed=12, m=mat("old paper"), z=0.0)


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
    # Oil soaked into the concrete: dark at the heart, brown and patchy at
    # the edge, matte, not a black plastic disc.
    oil = reb.mat_surface("Oil soak", [(0.0, (0.035, 0.032, 0.028)), (0.45, (0.06, 0.055, 0.048)), (0.75, (0.1, 0.092, 0.08)), (1.0, (0.14, 0.13, 0.115))], scale=14, detail=10, rough=0.85, bump=0.15)
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
    for i in range(4):
        at = (rng.uniform(2.0, 6.0), rng.uniform(2.0, 6.0), 0.0)
        r = rng.uniform(0.12, 0.3)
        kit.splat(f"Oil stain {i}", oil, at, r, seed=i, lumps=0.7, points=30, stretch=(rng.uniform(0.8, 1.6), 1.0))
        # A splash beside it.
        kit.splat(f"Oil drip {i}", oil, (at[0] + rng.uniform(-2, 2) * r, at[1] + rng.uniform(-2, 2) * r, 0.0005), r * rng.uniform(0.12, 0.3), seed=100 + i * 3, lumps=0.6, points=10)
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
    # The door, pulled to: a tin sheet on a plank frame, a hasp.
    reb.prim("cube", "Door, shut", tin, (sum(DOOR) / 2, Y0 - 0.02, 1.15), (DOOR[1] - DOOR[0], 0.04, 2.3))
    for z in (0.25, 1.15, 2.05):
        reb.prim("cube", "Door rail", stud_m, (sum(DOOR) / 2, Y0 + 0.02, z), (DOOR[1] - DOOR[0] - 0.06, 0.04, 0.1))
    reb.prim("cube", "Door hasp", mat("iron"), (DOOR[1] - 0.1, Y0 + 0.05, 1.1), (0.04, 0.03, 0.18))
    reb.prim("cube", "Bar, broken", mat("logs"), (2.4, 1.75, 0.06), (0.9, 0.1, 0.1), rot=(0, 0, 0.5))
    reb.prim("cube", "Bar, broken end", mat("logs"), (3.4, 2.05, 0.06), (0.7, 0.1, 0.1), rot=(0, 0, -0.3))
    reb.prim("cube", "Splinters", reb.mat_wood("Fresh wood", (0.45, 0.34, 0.2)), (2.85, 1.85, 0.02), (0.15, 0.06, 0.03), rot=(0, 0, 1.1))
    shoved = kit.table("Heavy bench, shoved aside", bench_m, (1.75, 1.55, 0.0), size=(1.3, 0.6, 0.8), rot=0.35)
    bench_clutter(rng, (1.75, 1.55, 0.8), 0.35, engine_m, red_chest)
    reb.mask(reb.wall(shoved))
    for i in range(3):
        reb.prim("cube", f"Scrape {i}", reb.mat_plain("Scrape", (0.3, 0.29, 0.27), 0.9), (2.3 + i * 0.1, 1.75 + i * 0.05, 0.002), (0.8, 0.02, 0.002), rot=(0, 0, 0.35))
    kit.splat("Hand on the frame", mat("old blood"), (DOOR[1] + 0.09, Y0 + 0.04, 1.15), 0.07, rot=(math.pi / 2, 0, 0), seed=4)
    reb.prim("cube", "Smear down the frame", mat("old blood"), (DOOR[1] + 0.09, Y0 + 0.045, 0.85), (0.04, 0.004, 0.5))
    for i, (x, y) in enumerate(((2.2, 5.0), (2.55, 3.9), (2.75, 2.6), (2.85, 1.6))):   # a few drops on his way out
        kit.splat(f"Drop to the door {i}", mat("old blood"), (x, y, 0.001), 0.035, seed=50 + i, points=10, lumps=0.4)

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
    kit.rod("Saw chain off the bar", mat("iron"), (4.5, 1.55, 0.905), (5.4, 1.6, 0.905), 0.008, 4)
    reb.prim("cube", "Files in a roll", mat("canvas"), (5.55, 1.55, 0.92), (0.35, 0.12, 0.04), rot=(0, 0, -0.2))
    reb.prim("cyl", "Bar oil can", reb.mat_plain("Oil can", (0.4, 0.3, 0.05), 0.5), (4.42, 1.15, 0.99), (0.14, 0.14, 0.18), segments=10)
    reb.prim("cube", "Grease rag", mat("canvas"), (5.1, 1.12, 0.905), (0.2, 0.15, 0.01), rot=(0, 0, 0.4))

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
    kit.splat("Oil under the engine", oil, (2.95, BEAM_Y, 0.0), 0.32, seed=20, lumps=0.7, points=30, stretch=(1.3, 0.9))
    loose = reb.prim("sphere", "Loose chain top", mat("iron"), (5.6, BEAM_Y, 2.7), (0.04, 0.04, 0.04))
    lc = chain("Loose chain", (0, 0, 0), (0, 0, -1.6), links_=20)
    lc.parent = loose
    reb.prim("cube", "Loose hook", mat("iron"), (0, 0, -1.65), (0.04, 0.1, 0.12)).parent = loose

    # ---- The crate in the south-east: ARKLAY SKYWAY - SPARE, under the logs he stacked on it.
    # A box open at the top under its lid, so the lid can come off: the
    # box is a mask and never moves; the lid is its own object.
    cx, cy = CRATE
    cw, cd, ch = 1.2, 0.8, 0.75
    parts = [reb.prim("cube", "floor", crate_m, (0, 0, 0.03), (cw, cd, 0.06))]
    for sx, sy, w, d in ((0, -1, cw, 0.04), (0, 1, cw, 0.04), (-1, 0, 0.04, cd), (1, 0, 0.04, cd)):
        parts.append(reb.prim("cube", "side", crate_m, (sx * (cw - 0.04) / 2, sy * (cd - 0.04) / 2, ch / 2), (w, d, ch), bevel=0.005))
        for dz in (0.08, ch - 0.08):
            parts.append(reb.prim("cube", "slat", crate_m, (sx * (cw / 2 + 0.005), sy * (cd / 2 + 0.005), dz), (w + 0.02 if sy else 0.02, d + 0.02 if sx else 0.02, 0.06)))
    cr = kit.join("Spare crate", parts, origin=(0, 0, 0))
    cr.location = (cx, cy, 0.0)
    reb.mask(reb.wall(cr))
    straw = reb.mat_surface("Packing straw", [(0.0, (0.16, 0.12, 0.06)), (0.6, (0.34, 0.27, 0.14)), (1.0, (0.45, 0.37, 0.2))], scale=40, bump=0.8)
    reb.prim("cube", "Packing in the crate", straw, (cx, cy, 0.31), (cw - 0.08, cd - 0.08, 0.56))
    lid_parts = [reb.prim("cube", "boards", crate_m, (0, 0, 0.0), (cw + 0.02, cd + 0.02, 0.035), bevel=0.005)]
    for dx in (-0.4, 0.0, 0.4):
        lid_parts.append(reb.prim("cube", "batten", crate_m, (dx, 0, 0.03), (0.08, cd - 0.04, 0.03)))
    lid = kit.join("Crate lid", lid_parts, origin=(0, 0, 0))
    lid_rest = (Vector((cx, cy, ch + 0.018)), (0.0, 0.0, 0.0))
    # Off: stood on its end, leant on the crate's west side.
    lid_off = (Vector((cx - cw / 2 - 0.23, cy, 0.6)), (0.0, math.radians(-72), 0.0))
    lid.location, lid.rotation_euler = lid_rest
    kit.text("Crate words", "ARKLAY SKYWAY", stencil, (cx, cy - 0.41, 0.5), size=0.11)
    kit.text("Crate words 2", "- SPARE -", stencil, (cx, cy - 0.41, 0.33), size=0.1)
    kit.text("Crate words 3", "DRIVE COG  NO 2", stencil, (cx, cy - 0.41, 0.2), size=0.05)
    kit.text("Crate words west", "ARKLAY SKYWAY", stencil, (cx - 0.61, cy, 0.45), size=0.08, rot=(math.pi / 2, 0, -math.pi / 2))
    logs = []
    for row, (n, z) in enumerate(((3, 0.95), (2, 1.33), (1, 1.7))):
        for i in range(n):
            y = cy + (i - (n - 1) / 2) * 0.38
            logs.append(((cx - 1.0 + rng.uniform(-0.15, 0.1), y + rng.uniform(-0.06, 0.06), z + rng.uniform(-0.03, 0.03)), (cx + 0.9 + rng.uniform(-0.1, 0.15), y + rng.uniform(-0.06, 0.06), z + rng.uniform(-0.04, 0.04)), 0.19 + rng.uniform(-0.03, 0.03)))
    # Each log its own: lumpy, a little bent, its ends ragged, the odd branch
    # stub. Not masks: the hoist lifts them.
    log_obs = [kit.rough_log(f"Log on the crate {i}", a_, b_, r, seed=30 + i, stubs=2) for i, (a_, b_, r) in enumerate(logs)]
    reb.wall(reb.prim("cube", "Log stack footprint", None, (5.85, 5.95, 0.5), (1.9, 1.3, 1.0))).hide_render = True

    # ---- The electric hoist over the crate, on a spur rail off the I-beam;
    # its cable along the beams and down to the dead MILL LINE box.
    steel = reb.mat_metal("Hoist grey", (0.1, 0.12, 0.11), 0.5)
    sy0, sy1 = BEAM_Y, Y1 - 0.06
    reb.prim("cube", "Spur rail", mat("rust"), (cx, (sy0 + sy1) / 2, 2.82), (0.14, sy1 - sy0, 0.2))
    reb.prim("cube", "Spur flange", mat("rust"), (cx, (sy0 + sy1) / 2, 2.72), (0.2, sy1 - sy0, 0.03))
    reb.prim("cube", "Spur bracket", mat("rust"), (cx, Y1 - 0.1, 2.6), (0.3, 0.08, 0.4))
    hy = cy
    reb.prim("cube", "Electric hoist trolley", mat("yellow paint"), (cx, hy, 2.63), (0.34, 0.3, 0.12), bevel=0.01)
    for dy in (-0.1, 0.1):
        for sx in (-1, 1):
            reb.prim("cyl", "Trolley wheel", mat("iron"), (cx + sx * 0.13, hy + dy, 2.69), (0.07, 0.07, 0.03), rot=(0, math.pi / 2, 0), segments=10)
    reb.prim("cube", "Electric hoist body", mat("yellow paint"), (cx, hy, 2.43), (0.3, 0.28, 0.28), bevel=0.03)
    reb.prim("cyl", "Hoist motor", steel, (cx + 0.29, hy, 2.43), (0.24, 0.24, 0.3), rot=(0, math.pi / 2, 0), segments=16)
    for k in range(4):
        reb.prim("cyl", f"Motor fin {k}", steel, (cx + 0.18 + k * 0.07, hy, 2.43), (0.27, 0.27, 0.015), rot=(0, math.pi / 2, 0), segments=16)
    reb.prim("cube", "Hoist gearbox", mat("yellow paint"), (cx - 0.22, hy, 2.43), (0.12, 0.22, 0.22), bevel=0.02)
    reb.prim("cube", "Hoist contactor box", steel, (cx, hy - 0.2, 2.45), (0.2, 0.1, 0.18), bevel=0.01)
    black = mat("black")

    def choker(name, hook, ends, wraps):
        """Two chain legs from the hook down to the load, and a turn of chain round it at each end."""
        obs = [kit.tube(f"{name} leg {k}", mat("iron"), [tuple(hook), tuple(hook.lerp(e, 0.5) - Vector((0, 0, 0.02))), tuple(e)], 0.015, 6) for k, e in enumerate(ends)]
        for k, ring in enumerate(wraps):
            obs.append(kit.tube(f"{name} wrap {k}", mat("iron"), ring, 0.015, 6))
        return obs

    def loop(c, r):
        return [(c.x, c.y + r * math.cos(2 * math.pi * k / 12), c.z + r * math.sin(2 * math.pi * k / 12)) for k in range(13)]
    # Down: the hook lowered onto the pile, its chain choked round the top log.
    top = logs[5]
    tx0 = Vector(top[0]).lerp(Vector(top[1]), 0.3)
    tx1 = Vector(top[0]).lerp(Vector(top[1]), 0.7)
    hook_down = Vector((cx, hy, 2.12))
    down = [chain("Hoist chain, paid out", (cx, hy, 2.29), hook_down, links_=4),
            reb.prim("cube", "Hoist hook", mat("iron"), hook_down - Vector((0, 0, 0.04)), (0.05, 0.1, 0.1))]
    down += choker("Choker", hook_down - Vector((0, 0, 0.08)), [tx0 + Vector((0, 0, 0.21)), tx1 + Vector((0, 0, 0.21))], [loop(tx0, 0.21), loop(tx1, 0.21)])
    # Up: the six logs wound up off the crate in a choked bundle, three over three.
    hook_up = Vector((cx, hy, 2.22))
    bundle = []
    for k in range(6):
        row, col = divmod(k, 3)
        bundle.append(Vector((0, cy + (col - 1) * 0.37, 1.77 - row * 0.32)))

    def cinch(c):
        """A turn of chain round the bundle's cross-section, a rounded box."""
        pts = []
        for k in range(17):
            a = 2 * math.pi * k / 16
            q = 0.95 / max(abs(math.cos(a)), abs(math.sin(a)), 0.7)
            pts.append((c.x, c.y + 0.6 * math.cos(a) * q, c.z + 0.38 * math.sin(a) * q))
        return pts
    wrap_c = [Vector((cx - 0.5, cy, 1.61)), Vector((cx + 0.45, cy, 1.61))]
    up = [chain("Hoist chain, wound in", (cx, hy, 2.29), hook_up, links_=2),
          reb.prim("cube", "Hoist hook, wound in", mat("iron"), hook_up - Vector((0, 0, 0.04)), (0.05, 0.1, 0.1))]
    up += choker("Choker, wound in", hook_up - Vector((0, 0, 0.08)), [w + Vector((0, 0, 0.36)) for w in wrap_c], [cinch(w) for w in wrap_c])
    log_rest = [ob.location.copy() for ob in log_obs]
    log_lift = [Vector((0, b.y - (a_[1] + b_[1]) / 2, b.z - (a_[2] + b_[2]) / 2)) for b, (a_, b_, _r) in zip(bundle, logs)]
    # The pendant control on its cable, run along the spur to hang where she can reach it, clear of the pile.
    pend = Vector((cx, 4.75, 1.22))
    kit.tube("Pendant cable", black, [(cx, hy - 0.2, 2.36), (cx, hy - 0.5, 2.66), (cx, 5.0, 2.66), (cx, pend.y, 2.6), (cx, pend.y, pend.z + 0.12)], 0.008, 6)
    reb.prim("cube", "Pendant control", mat("yellow paint"), tuple(pend), (0.09, 0.07, 0.24), bevel=0.015)
    for k, m_ in enumerate((mat("green paint"), mat("red paint"))):
        reb.prim("cyl", f"Pendant button {k}", m_, (cx, pend.y - 0.04, pend.z + 0.05 - k * 0.09), (0.045, 0.045, 0.02), rot=(math.pi / 2, 0, 0), segments=10)
    # The power cable: along the spur, the I-beam, down the east wall into the box.
    bx_, by_ = X1 - 0.14, 4.45
    kit.tube("Hoist power cable", black, [(cx + 0.29, hy - 0.12, 2.56), (cx + 0.1, hy - 0.4, 2.68), (cx + 0.1, 4.6, 2.68), (cx + 0.1, BEAM_Y + 0.1, 2.68),
                                          (X1 - 0.12, BEAM_Y + 0.11, 2.68), (X1 - 0.08, BEAM_Y + 0.15, 2.5), (X1 - 0.08, by_, 2.2), (X1 - 0.08, by_, 1.82)], 0.012, 6)
    box_m = kit.dirtied(reb.mat_plain("Switch box grey", (0.17, 0.19, 0.18), 0.5), 0.6, scale=8)
    reb.prim("cube", "Mill line box", box_m, (bx_, by_, 1.55), (0.16, 0.42, 0.52), bevel=0.01)
    reb.prim("cube", "Box door seam", black, (bx_ - 0.082, by_, 1.55), (0.004, 0.36, 0.46))
    kit.text("Mill line words", "MILL LINE", mat("white paint"), (bx_ - 0.086, by_, 1.69), size=0.07, rot=(math.pi / 2, 0, -math.pi / 2))
    # The switch handle up at ON, its lamp dark: the line is dead, not off.
    kit.rod("Box switch handle", mat("red paint"), (bx_ - 0.09, by_ + 0.12, 1.45), (bx_ - 0.16, by_ + 0.12, 1.58), 0.014, 6)
    reb.prim("sphere", "Box lamp, dark", reb.mat_plain("Dead lamp", (0.12, 0.03, 0.02), 0.3), (bx_ - 0.085, by_ - 0.1, 1.45), (0.04, 0.03, 0.04), segments=10)
    kit.rod("Box conduit", mat("rust"), (bx_, by_ - 0.1, 1.29), (bx_, by_ - 0.1, 0.9), 0.02, 6)
    kit.rod("Box conduit out", mat("rust"), (bx_, by_ - 0.1, 0.9), (X1 + 0.1, by_ - 0.1, 0.9), 0.02, 6)

    def crane(on):
        """The hoist worked: the logs wound up off the crate, the lid off."""
        for ob, rest, lift in zip(log_obs, log_rest, log_lift):
            ob.location = rest + lift if on else rest
        for ob in down:
            ob.hide_render = bool(on)
        for ob in up:
            ob.hide_render = not on
        lid.location, lid.rotation_euler = lid_off if on else lid_rest
    crane(False)
    kit.drag_trail("Drag marks of the logs", reb.mat_plain("Bark scrape", (0.12, 0.09, 0.06), 0.9), [(2.8, 1.6), (3.6, 3.0), (4.6, 4.6), (5.2, 5.3)], width=0.25, seed=22)
    # Tyres, welding bottles chained to the wall, a drum.
    # Spare wheels stacked flat: treaded tyres on their rims, each a little askew.
    for i in range(4):
        w = kit.join(f"Spare wheel {i}", kit.wheel(f"Spare wheel {i}", (0, 0, 0), r=0.4, width=0.24, rim=mat("rust")), origin=(0, 0, 0))
        w.rotation_euler = (math.pi / 2, 0, rng.uniform(0, 3))
        w.location = (3.92 + rng.uniform(-0.04, 0.04), 1.48 + rng.uniform(-0.04, 0.04), 0.13 + i * 0.25)
    reb.mask(reb.wall(reb.prim("cyl", "Wheels footprint", None, (3.92, 1.48, 0.5), (0.9, 0.9, 1.0)), "circle")).hide_render = True
    for i, (y, m) in enumerate(((2.3, mat("green paint")), (2.55, reb.mat_plain("Bottle maroon", (0.25, 0.03, 0.03), 0.4)))):
        reb.wall(reb.prim("cyl", f"Gas bottle {i}", m, (6.55, y, 0.7), (0.22, 0.22, 1.4), segments=14), "circle")
        reb.prim("sphere", f"Bottle shoulder {i}", m, (6.55, y, 1.4), (0.22, 0.22, 0.14))
        reb.prim("cyl", f"Bottle neck ring {i}", mat("steel"), (6.55, y, 1.5), (0.1, 0.1, 0.05), segments=12)
        reb.prim("cyl", f"Bottle valve {i}", reb.mat_metal("Brass valve", (0.5, 0.38, 0.14), 0.35), (6.55, y, 1.57), (0.05, 0.05, 0.1), segments=10)
        reb.prim("cyl", f"Valve wheel {i}", mat("black"), (6.55, y, 1.63), (0.09, 0.09, 0.015), segments=10)
        kit.rod(f"Valve outlet {i}", reb.mat_metal("Brass valve", (0.5, 0.38, 0.14), 0.35), (6.55, y, 1.56), (6.45, y, 1.56), 0.012, 6)
        reb.prim("cyl", f"Bottle foot ring {i}", mat("rust"), (6.55, y, 0.04), (0.23, 0.23, 0.08), segments=14)
        reb.prim("cyl", f"Bottle band {i}", mat("white paint") if i else mat("black"), (6.55, y, 1.2), (0.225, 0.225, 0.05), segments=14)
        for z in (0.5, 0.9):
            kit.splat(f"Bottle scuff {i}{z}", mat("rust"), (6.55 - 0.112, y, z), 0.04, rot=(0, -math.pi / 2, 0), seed=int(z * 10) + i, points=10)
    # The regulators and hoses down to the torch on its hook, the trolley under them.
    for i, y in enumerate((2.3, 2.55)):
        reb.prim("cube", f"Regulator {i}", mat("steel"), (6.42, y, 1.56), (0.06, 0.06, 0.08), bevel=0.01)
        reb.prim("cyl", f"Gauge {i}", reb.mat_plain("Gauge face", (0.55, 0.53, 0.48), 0.4), (6.42, y - 0.05, 1.62), (0.06, 0.06, 0.015), rot=(math.pi / 2, 0, 0), segments=12)
    kit.tube("Oxygen hose", mat("green paint"), [(6.38, 2.3, 1.52), (6.25, 2.35, 1.1), (6.2, 2.45, 0.6), (6.3, 2.6, 0.95), (6.4, 2.7, 1.25)], 0.012, 6)
    kit.tube("Gas hose", reb.mat_plain("Hose red", (0.3, 0.04, 0.03), 0.6), [(6.38, 2.55, 1.52), (6.22, 2.5, 1.0), (6.18, 2.55, 0.55), (6.32, 2.68, 0.95), (6.4, 2.72, 1.25)], 0.012, 6)
    kit.rod("Torch", mat("steel"), (6.4, 2.72, 1.25), (6.35, 2.78, 1.5), 0.012, 6)
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
    cable = kit.rod("Cut cable", mat("black"), (0, 0, 0), (0, 0, -0.45), 0.012, 6)
    cable.parent = pivot
    spark_m = reb.mat_emit("Spark", (0.75, 0.85, 1.0), 40)
    sv2, sf2 = [], []
    srng = random.Random(3)
    for i in range(14):
        d = Vector((srng.uniform(-1, 1), srng.uniform(-1, 1), srng.uniform(-1.2, 0.4))).normalized() * srng.uniform(0.06, 0.25)
        reb.box(sv2, sf2, tuple(d / 2 + Vector((0, 0, -0.47))), (0.006, 0.006, d.length), math.atan2(d.y, d.x))
    sparks = reb.mesh_object("Sparks", sv2, sf2, spark_m, smooth=False)
    sparks.parent = pivot
    spark_light = reb.point("Spark light", (CABLE[0], CABLE[1], H - 0.75), 60, (0.7, 0.8, 1.0), 0.05)
    kit.splat("Scorch under the cable", mat("black"), (CABLE[0], CABLE[1], 0.0), 0.3, seed=24, lumps=0.6)
    reb.prim("cube", "Strip light, hanging", reb.mat_plain("Strip light dead", (0.5, 0.52, 0.5), 0.4), (4.9, 4.9, H - 0.42), (1.2, 0.12, 0.08), rot=(0, 0.12, 0.2))
    kit.rod("Strip light chain", mat("iron"), (5.4, 5.0, H - 0.2), (5.45, 5.01, H - 0.38), 0.006, 4)

    # ---- Light: grey noon through the door and the slits in the boards, the work lamp, the sparks.
    kit.time_light("noon", sun_heading=200, sun_energy=1.5, sky=((0.5, 0.52, 0.54), (0.36, 0.39, 0.43), 0.8))
    reb.spot("Door light", (sum(DOOR) / 2, Y0 - 3.0, 2.3), (sum(DOOR) / 2, Y0 + 2.5, 0.0), 420, (0.75, 0.8, 0.88), 45, 0.8, 0.6)
    reb.spot("Slits through the north boards", (sum(NWIN) / 2, Y0 + 0.1, 1.5), (sum(NWIN) / 2 - 0.3, 3.4, 0.0), 60, (0.72, 0.78, 0.88), 40, 0.3, 0.1)
    reb.spot("Slits through the west boards", (X0 + 0.1, sum(WWIN) / 2, 1.5), (3.6, sum(WWIN) / 2 + 0.3, 0.0), 50, (0.72, 0.78, 0.88), 40, 0.3, 0.1)
    reb.point("Fill", (4.0, 4.0, 2.4), 35, (0.6, 0.65, 0.75), 1.0)

    anim = kit.Anim(16)
    on = {9}

    def spark(k):
        lit = k in on
        sparks.hide_render = not lit
        spark_light.data.energy = 60 if lit else 0
        lamp.data.energy = 30 * (0.55 if lit else 1.0)
        reb.emit_strength(lamp_glow, 12 * (0.55 if lit else 1.0))
        pivot.rotation_euler = (math.radians(0.8) * math.sin(anim.phase(k)), 0, 0)
    anim.custom(spark)
    anim.custom(lambda k: setattr(hang, "rotation_euler", (math.radians(0.4) * math.sin(anim.phase(k)), 0, 0)))
    anim.custom(lambda k: setattr(loose, "rotation_euler", (math.radians(1.0) * math.sin(anim.phase(k) + 1.0), 0, 0)))

    # ---- What the game needs.
    room.door("camp-yard", (DOOR[0], Y0, DOOR[1], Y0 + 0.5), arrive=(2.8, 2.35), face=(0, 1))
    room.state("crane", crane, loop=True)
    # At the hoist's pendant, north of the pile (day/events.ts says what she sees and does here).
    room.spot("crane", (5.45, 4.2, 6.45, 4.72))
    room.item("cog", (cx + 0.1, cy + 0.05, 0.6))
    room.check((5.05, 4.75, 6.55, 5.3), "A crate. ARKLAY SKYWAY - SPARE. DRIVE COG NO 2.\nThe gondola's spare cog, under a pile of logs.\nThey're too heavy to shift by hand. And the hoist above it is dead.")
    room.check((1.8, 5.1, 3.6, 5.7), "Someone slept here. Bandages, black with blood. A tally scratched in the tin: six days.\nA note: \"Bit on the hand Tues. Can't stay. Don't come looking. Gus.\"")
    room.check((3.8, 1.9, 4.8, 2.7), "A power cable, cut off short. It's still live. I'm not touching that.")
    room.check((1.75, 2.3, 2.3, 3.2), "A vice, a bench, his tools. The lamp's still on.")
    room.check((2.3, 4.25, 3.5, 4.8), "An engine, hanging on the hoist chains. Nobody's coming back to finish it.")
    room.check((1.9, 1.2, 3.6, 2.3), "He barred the door from inside. The bar's been broken.\nFrom this side.")
    scene = bpy.context.scene
    scene.render.use_persistent_data = True
    room.export(anim, samples=160)


build()
