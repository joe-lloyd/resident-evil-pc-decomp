"""The mill pond behind Camp 4's sawmill, at noon under cloud.

What it tells: the pond is what drives the mill. Water runs out through the
sluice gate in the timber dam, down a plank-lined race, and turns the big
wheel against the sawmill's east wall; its shaft goes in through the wall
to the saw. The sluice is open, its wheel-crank on the beam above it, so
the wheel still turns with nothing on the other end. The sawyer came out
of the mill's back door with his arm gone: his blood runs down the bank
from the door to the reeds, and he lies face down among them in the
shallows, one sleeve empty. Out on the open water a logger's hard hat
floats, and dead fish lie belly up along the reeds: something is wrong
with the water too. A footbridge over the race leads north, to where the
flume leaves the pond.

Metres: she walks x 1-16.5, y 2-14, the mill's grey wall along x 1.0 to the
west, its back door at y 9.6-10.6. The wheel stands against the wall at
y 4.6, its shaft 2.8 m up, turning in the race, which runs x 1.0-2.5 from
y 2 to 6.6 and then east along y 2-3 to the sluice at x 5.2-6.4. A plank
footbridge crosses the race at x 3.4-4.6 to the north edge, the way to the
flume. The dam runs north-south at x 5.2-6.4, its top a plank walk; the
pond is east of it, x 6.4 on, y up to 9.4, deep. Reeds stand in the
shallows along its south shore. The sawyer floats at x 9.6, y 8.9.

Moving: the water wheel, the pond and the race rippling, the reeds, the
body and the hat bobbing, flies on the bank's blood.
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
from mathutils import Vector, noise  # noqa: E402

X0, X1, Y0, Y1 = 1.0, 16.5, 2.0, 14.0
MILL_X = 1.0
BACK_DOOR = (9.6, 10.6)
WHEEL = (1.7, 4.6, 2.8)      # centre x, y, z: the shaft's height inside the mill
WHEEL_R = 2.9
RACE_NS = (1.0, 2.5, 2.0, 6.6)
RACE_EW = (2.5, 5.2, 2.0, 3.0)
BRIDGE = (3.4, 4.6)
DAM = (5.2, 6.4)
SHORE_Y = 9.4
POND_Z = -0.32
RACE_Z = -0.5
SAWYER = (9.6, 8.9)


def height(x, y):
    """The bank flat; the pond's bed falling away under the water; banks rising
    beyond the far shore."""
    n = noise.noise(Vector((x * 0.25, y * 0.25, 2.0)))
    if x > DAM[1] and y < SHORE_Y + 0.4 and x < 34 and y > -14:
        d = min(SHORE_Y + 0.4 - y, x - DAM[1], 34 - x, y + 14)
        return -0.05 - min(1.8, d * 0.6)
    h = -0.04 + 0.03 * n
    if not (X0 - 0.5 < x < X1 + 0.5 and Y0 - 0.5 < y < Y1 + 0.5):
        h += 0.4 * n + max(0.0, y - Y1 - 0.5) * 0.25 + max(0.0, x - 34) * 0.3 + max(0.0, -14 - y) * 0.3
    return h


def settle(ob, at, rot):
    """Bake a joined object's parts where they were built, then place it."""
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.location = at
    ob.rotation_euler = rot
    return ob


def corrugated(name, rgb, pitch=0.08):
    """Corrugated tin: ridges every `pitch` metres along x + y, rust in blotches."""
    m = reb.mat_surface(name, [(0.0, rgb), (0.55, tuple(c * 1.25 for c in rgb)), (0.8, (0.28, 0.12, 0.05)), (1.0, (0.18, 0.07, 0.03))], scale=2.2, rough=0.5, bump=0.2)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes["Principled BSDF"]
    tc = nodes.new("ShaderNodeTexCoord")
    wave = nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "DIAGONAL"
    wave.inputs["Scale"].default_value = 1.0 / pitch / 2.4
    links.new(tc.outputs["Object"], wave.inputs["Vector"])
    reb.bumped(nodes, links, bsdf, wave.outputs["Fac"], 0.6, 0.02)
    return m


def ring(name, m, x, r, thick, segs=40, sides=6):
    """A rim: a ring of radius r in the y-z plane at x, as one mesh."""
    verts, faces = [], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        c = Vector((x, math.cos(a) * r, math.sin(a) * r))
        out = Vector((0, math.cos(a), math.sin(a)))
        for j in range(sides):
            t = 2 * math.pi * j / sides
            verts.append(tuple(c + out * math.cos(t) * thick + Vector((1, 0, 0)) * math.sin(t) * thick))
    for i in range(segs):
        for j in range(sides):
            a0 = i * sides + j
            a1 = i * sides + (j + 1) % sides
            b0 = ((i + 1) % segs) * sides + j
            b1 = ((i + 1) % segs) * sides + (j + 1) % sides
            faces.append((a0, a1, b1, b0))
    return reb.mesh_object(name, verts, faces, m)


def reeds(rng, verts, faces, centre, count, spread, tall=(1.0, 1.8), z=0.0):
    """A clump of reeds: tall thin blades leaning out, some with a seed head."""
    for _ in range(count):
        x, y = centre[0] + rng.gauss(0, spread), centre[1] + rng.gauss(0, spread)
        h = rng.uniform(*tall)
        lean = Vector((rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), 0))
        b = Vector((x, y, z))
        a = rng.uniform(0, math.pi)
        w = Vector((math.cos(a), math.sin(a), 0)) * 0.012
        k = len(verts)
        verts.extend([tuple(b - w), tuple(b + w), tuple(b + lean * 0.5 + w * 0.7 + Vector((0, 0, h * 0.55))), tuple(b + lean * 0.5 - w * 0.7 + Vector((0, 0, h * 0.55))), tuple(b + lean + Vector((0, 0, h)))])
        faces.extend([(k, k + 1, k + 2, k + 3), (k + 3, k + 2, k + 4)])


def build():
    rng = random.Random(77)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.camera((17.8, 13.4, 3.4), (7.0, 6.4, 0.0), 200, "from the south-east bank: the pond, the reeds and the body, the dam, the wheel against the mill")
    room.camera((3.2, 13.5, 3.6), (5.4, 4.0, 0.8), 200, "from the south-west by the mill: the back door, the blood to the reeds, the wheel, the sluice")
    room.camera((5.8, 2.4, 3.6), (8.0, 12.0, 0.0), 200, "from over the sluice: down the dam and the bank to the reeds and the body")
    room.camera((11.8, 11.2, 3.0), (1.8, 4.2, 1.6), 200, "from the bank looking west: the water wheel turning, the race, the footbridge north")

    grey = corrugated("Mill grey", (0.24, 0.24, 0.23))
    planks = mat("planks")
    timber = reb.mat_wood("Mill timber", (0.17, 0.11, 0.065))
    wet_timber = reb.mat_surface("Wet timber", [(0.0, (0.03, 0.025, 0.018)), (0.6, (0.08, 0.06, 0.04)), (1.0, (0.06, 0.08, 0.04))], scale=5, rough=0.35, bump=0.5)
    bank = reb.mat_surface("Pond bank", [(0.0, (0.04, 0.03, 0.02)), (0.4, (0.09, 0.07, 0.045)), (0.75, (0.07, 0.09, 0.035)), (1.0, (0.1, 0.12, 0.05))], scale=1.4, rough=0.6, bump=0.6)
    water = mat("water")
    foam = reb.mat_surface("Foam", [(0.0, (0.25, 0.27, 0.27)), (0.6, (0.5, 0.52, 0.52)), (1.0, (0.7, 0.72, 0.72))], scale=10, rough=0.3, bump=0.6)
    iron = mat("iron")

    # ---- Ground and water: the bank, the pond's bed under dark water, the race in its plank channel.
    def ground_h(x, y):
        h = height(x, y)
        if RACE_NS[0] - 0.1 < x < RACE_NS[1] + 0.1 and RACE_NS[2] - 3 < y < RACE_NS[3]:
            return -1.2
        if RACE_EW[0] - 0.1 < x < DAM[1] and RACE_EW[2] - 3 < y < RACE_EW[3]:
            return -1.2
        return h
    reb.terrain("Bank", bank, (-14, 40), (-20, 32), ground_h, step=0.35)
    reb.prim("cube", "Pond", water, (20.0, (SHORE_Y - 14) / 2 + 0.1, POND_Z), (28.0, SHORE_Y + 14 + 0.2, 0.02))
    reb.prim("cube", "Race water", water, ((RACE_NS[0] + RACE_NS[1]) / 2, (RACE_NS[2] - 3 + RACE_NS[3]) / 2, RACE_Z), (RACE_NS[1] - RACE_NS[0], RACE_NS[3] - RACE_NS[2] + 3, 0.02))
    reb.prim("cube", "Race water, east leg", water, ((RACE_EW[0] + RACE_EW[1]) / 2, (RACE_EW[2] - 3 + RACE_EW[3]) / 2, RACE_Z + 0.04), (RACE_EW[1] - RACE_EW[0], RACE_EW[3] - RACE_EW[2] + 3, 0.02))
    for k, (x, y, r) in enumerate(((5.0, 2.5, 0.5), (1.9, 3.4, 0.6), (1.8, 5.6, 0.5), (1.6, 6.3, 0.4))):
        kit.splat(f"Foam {k}", foam, (x, y, RACE_Z + 0.03), r, seed=k, stretch=(1.0, 1.6), lumps=0.5)
    # The race's plank walls and their caps.
    for (x0, x1, y0, y1) in ((RACE_NS[1], RACE_NS[1] + 0.08, RACE_EW[3], RACE_NS[3]), (RACE_NS[0], RACE_NS[1], RACE_NS[3], RACE_NS[3] + 0.08), (RACE_EW[0], RACE_EW[1], RACE_EW[3], RACE_EW[3] + 0.08)):
        reb.prim("cube", "Race wall", wet_timber, ((x0 + x1) / 2, (y0 + y1) / 2, -0.6), (x1 - x0, y1 - y0, 1.24))
        reb.prim("cube", "Race cap", timber, ((x0 + x1) / 2, (y0 + y1) / 2, 0.04), (x1 - x0 + 0.06, y1 - y0 + 0.06, 0.08))
    # The culvert where the race goes under the mill.
    reb.prim("cube", "Culvert", reb.mat_plain("Culvert dark", (0.005, 0.005, 0.005), 0.9), (MILL_X - 0.02, 6.1, -0.6), (0.06, 1.0, 1.0))
    room.void(RACE_NS)
    room.void((RACE_EW[0], RACE_EW[2], BRIDGE[0], RACE_EW[3]))
    room.void((BRIDGE[1], RACE_EW[2], RACE_EW[1], RACE_EW[3]))
    room.void((DAM[1], Y0, X1, SHORE_Y))

    # ---- The mill's east wall: grey tin, its high window, the back door ajar, his blood on it.
    reb.prim("cube", "Mill wall", grey, (MILL_X - 0.08, 7.4, 3.0), (0.16, 9.6 + 0.3, 6.0))
    reb.prim("cube", "Mill wall north", grey, (MILL_X - 0.08, 0.0, 3.0), (0.16, 5.2, 6.0))
    reb.prim("cube", "Mill roof", corrugated("Roof tin", (0.26, 0.26, 0.25)), (MILL_X - 6.0, 7.4, 6.25), (13.0, 10.4, 0.12), rot=(0, 0.06, 0))
    reb.prim("cube", "Mill window", reb.mat_plain("Window dark", (0.02, 0.022, 0.02), 0.2), (MILL_X + 0.005, 5.7, 4.3), (0.02, 1.4, 1.0))
    reb.prim("cube", "Back doorway", reb.mat_plain("Doorway dark", (0.012, 0.01, 0.008), 0.9), (MILL_X + 0.005, sum(BACK_DOOR) / 2, 1.05), (0.02, BACK_DOOR[1] - BACK_DOOR[0], 2.1))
    reb.prim("cube", "Back door", kit.boards("Mill boards", (0.2, 0.15, 0.1), width=0.22, grime=0.8), (MILL_X + 0.45, BACK_DOOR[0] - 0.05, 1.05), (0.9, 0.05, 2.1), rot=(0, 0, 0.35))
    for y in BACK_DOOR:
        reb.prim("cube", "Back door frame", timber, (MILL_X + 0.03, y, 1.05), (0.08, 0.08, 2.2))
    kit.splat("His hand on the frame", mat("blood"), (MILL_X + 0.075, BACK_DOOR[0] - 0.02, 1.2), 0.07, rot=(0, math.pi / 2, 0), seed=5)
    reb.wall(reb.prim("cube", "Mill footprint", None, (MILL_X - 0.4, 7.0, 1.0), (0.8, 12.0, 2.0))).hide_render = True
    kit.text("Mill wall stencil", "CAMP 4", mat("white paint"), (MILL_X + 0.01, 8.2, 3.6), size=0.5, rot=(math.pi / 2, 0, math.pi / 2))

    # ---- The water wheel: two rims, spokes, buckets between them, turning on the shaft into the mill.
    wx, wy, wz = WHEEL
    parts = []
    for dx in (-0.45, 0.45):
        for r_ in (WHEEL_R, WHEEL_R - 0.35):
            parts.append(ring("rim", wet_timber, dx, r_, 0.05))
        for k in range(8):
            a = 2 * math.pi * k / 8
            parts.append(kit.rod("spoke", wet_timber, (dx, 0, 0), (dx, math.cos(a) * (WHEEL_R - 0.3), math.sin(a) * (WHEEL_R - 0.3)), 0.06, 6))
    for k in range(24):
        a = 2 * math.pi * k / 24
        c = Vector((0, math.cos(a) * (WHEEL_R - 0.17), math.sin(a) * (WHEEL_R - 0.17)))
        parts.append(reb.prim("cube", "bucket", wet_timber, c, (0.95, 0.04, 0.42), rot=(a + 0.35, 0, 0)))
    parts.append(reb.prim("cyl", "hub", iron, (0, 0, 0), (0.5, 0.5, 1.1), rot=(0, math.pi / 2, 0), segments=16))
    wheel = settle(kit.join("Water wheel", parts), (wx, wy, wz), (0, 0, 0))
    kit.rod("Shaft", iron, (MILL_X - 0.2, wy, wz), (RACE_NS[1] + 0.4, wy, wz), 0.11, 12)
    reb.prim("cube", "Outer bearing", iron, (RACE_NS[1] + 0.3, wy, wz - 0.2), (0.4, 0.4, 0.3))
    pier = reb.prim("cube", "Bearing pier", timber, (RACE_NS[1] + 0.3, wy, (wz - 0.35 - 1.2) / 2), (0.4, 0.5, wz - 0.35 + 1.2))
    reb.mask(reb.wall(pier))
    # Water pouring off the buckets on the down side.
    for k in range(3):
        reb.prim("cube", f"Spill {k}", foam, (wx + (k - 1) * 0.3, wy - 1.5 - 0.1 * k, 0.4), (0.25, 0.04, 1.6), rot=(0.25, 0, 0))

    # ---- The sluice: two posts in the dam, the gate board raised, the crank's handwheel on the beam.
    sx = (DAM[0] + DAM[1]) / 2
    for y in (RACE_EW[2] + 0.05, RACE_EW[3] - 0.05):
        reb.wall(kit.rod("Sluice post", timber, (sx, y, -1.2), (sx, y, 2.0), 0.13, 8), "circle")
    reb.prim("cube", "Sluice beam", timber, (sx, sum(RACE_EW[2:]) / 2, 1.9), (0.3, 1.4, 0.25))
    gate = reb.prim("cube", "Sluice gate", wet_timber, (sx, sum(RACE_EW[2:]) / 2, 0.3), (0.12, 0.95, 1.1))
    kit.rod("Gate rack", mat("rust"), (sx, sum(RACE_EW[2:]) / 2, 0.85), (sx, sum(RACE_EW[2:]) / 2, 2.6), 0.04, 6)
    hand = reb.prim("cyl", "Crank handwheel", mat("rust"), (sx + 0.25, sum(RACE_EW[2:]) / 2, 2.2), (0.8, 0.8, 0.05), rot=(0, math.pi / 2, 0), segments=20)
    reb.prim("cyl", "Handwheel hole", mat("black"), (sx + 0.27, sum(RACE_EW[2:]) / 2, 2.2), (0.62, 0.62, 0.05), rot=(0, math.pi / 2, 0), segments=20)
    for k in range(4):
        a = math.pi * k / 4
        kit.rod("Handwheel spoke", mat("rust"), (sx + 0.25, sum(RACE_EW[2:]) / 2, 2.2), (sx + 0.25, sum(RACE_EW[2:]) / 2 + math.cos(a) * 0.38, 2.2 + math.sin(a) * 0.38), 0.015, 5)
    kit.rod("Crank handle", mat("rust"), (sx + 0.25, sum(RACE_EW[2:]) / 2 + 0.36, 2.2), (sx + 0.45, sum(RACE_EW[2:]) / 2 + 0.36, 2.2), 0.02, 5)
    reb.prim("cube", "Water through the gate", foam, (sx - 0.3, sum(RACE_EW[2:]) / 2, -0.38), (0.7, 0.9, 0.04), rot=(0, 0.2, 0))
    reb.prim("cube", "Sluice sign", mat("white paint"), (sx, RACE_EW[3] + 0.05, 1.35), (0.02, 0.5, 0.3))
    kit.text("Sluice sign words", "SLUICE", mat("black"), (sx + 0.015, RACE_EW[3] + 0.05, 1.4), size=0.08, rot=(math.pi / 2, 0, math.pi / 2))
    kit.text("Sluice sign words 2", "OPEN = MILL", mat("red paint"), (sx + 0.015, RACE_EW[3] + 0.05, 1.29), size=0.06, rot=(math.pi / 2, 0, math.pi / 2))

    # ---- The dam: a timber crib with a plank walk on top, the pond against its east face.
    reb.prim("cube", "Dam crib", wet_timber, (sx, (RACE_EW[3] + SHORE_Y + 0.6) / 2, -0.7), (DAM[1] - DAM[0], SHORE_Y + 0.6 - RACE_EW[3], 1.4))
    for k in range(int((SHORE_Y - RACE_EW[3]) / 0.2)):
        y = RACE_EW[3] + 0.1 + k * 0.2
        reb.prim("cube", "Dam plank", planks, (sx, y, 0.0), (DAM[1] - DAM[0] + 0.1, 0.18, 0.06))
    for y in [RACE_EW[3] + 0.3 + k * 1.6 for k in range(5)]:
        kit.rod("Dam post", timber, (DAM[1] - 0.05, y, -0.8), (DAM[1] - 0.05, y, 1.05), 0.07, 6)
    kit.rod("Dam rail", timber, (DAM[1] - 0.05, RACE_EW[3] + 0.3, 1.0), (DAM[1] - 0.05, SHORE_Y - 0.2, 1.0), 0.04, 6)
    reb.wall(reb.prim("cube", "Dam rail footprint", None, (DAM[1] - 0.05, (RACE_EW[3] + SHORE_Y) / 2, 0.5), (0.12, SHORE_Y - RACE_EW[3], 1.0))).hide_render = True
    # Logs penned against the dam by a boom chain, waiting for the mill.
    boom = [((7.2, 3.4, POND_Z + 0.05), (12.4, 3.0, POND_Z + 0.05), 0.28), ((7.0, 4.1, POND_Z + 0.04), (11.0, 4.5, POND_Z + 0.04), 0.26), ((8.0, 2.6, POND_Z + 0.05), (13.6, 2.2, POND_Z + 0.05), 0.3)]
    logs_m = reb.mat_surface("Log bark", [(0.0, (0.05, 0.035, 0.025)), (0.6, (0.12, 0.085, 0.06)), (1.0, (0.18, 0.14, 0.1))], scale=6, bump=0.9)
    floating = []
    for a, b, r in boom:
        floating.append(kit.rod("Penned log", logs_m, a, b, r, 12))
    kit.rod("Boom chain", iron, (DAM[1], 5.0, POND_Z + 0.1), (14.0, 4.9, POND_Z + 0.1), 0.02, 5)

    # ---- The footbridge north over the race, toward the flume, and the flume's start beyond.
    for k in range(6):
        x = BRIDGE[0] + 0.1 + k * 0.2
        reb.prim("cube", "Bridge plank", planks, (x, (RACE_EW[2] + RACE_EW[3]) / 2 - 0.4, 0.0), (0.18, RACE_EW[3] - RACE_EW[2] + 1.6, 0.06))
    for x in BRIDGE:
        kit.rod("Bridge rail", timber, (x, RACE_EW[2] - 1.2, 1.0), (x, RACE_EW[3] + 0.2, 1.0), 0.035, 6)
        for y in (RACE_EW[2] - 1.0, RACE_EW[3] + 0.1):
            kit.rod("Bridge post", timber, (x, y, -0.6), (x, y, 1.0), 0.05, 6)
    reb.wall(reb.prim("cube", "Bridge rail footprint W", None, (BRIDGE[0] - 0.05, (RACE_EW[2] + RACE_EW[3]) / 2, 0.5), (0.1, RACE_EW[3] - RACE_EW[2], 1.0))).hide_render = True
    reb.wall(reb.prim("cube", "Bridge rail footprint E", None, (BRIDGE[1] + 0.05, (RACE_EW[2] + RACE_EW[3]) / 2, 0.5), (0.1, RACE_EW[3] - RACE_EW[2], 1.0))).hide_render = True
    kit.path_strip("Path north", reb.mat_plain("Trodden", (0.06, 0.045, 0.03), 0.9), [(4.0, 0.8), (4.2, -3.0), (5.0, -8.0)], height, width=0.5)
    for y in (-2.0, -5.0, -8.0):
        for s in (-1, 1):
            kit.rod("Flume trestle", timber, (8.2 + s * 0.6, y, -0.4), (8.2 + s * 0.4, y, 1.0), 0.07, 6)
    reb.prim("cube", "Flume trough", wet_timber, (8.2, -5.0, 1.15), (1.0, 8.0, 0.3))
    reb.prim("cube", "Flume water", water, (8.2, -5.0, 1.27), (0.8, 8.0, 0.02))
    kit.rod("Flume sign post", timber, (4.9, 1.6, -0.1), (4.9, 1.6, 1.8), 0.05)
    reb.prim("cube", "Flume sign", planks, (4.9, 1.62, 1.6), (0.9, 0.04, 0.24))
    kit.text("Flume sign words", "FLUME ^", mat("white paint"), (4.9, 1.645, 1.6), size=0.12, rot=(math.pi / 2, 0, math.pi))

    # ---- The sawyer face down in the reeds, his blood down the bank, the hat and the dead fish.
    kit.drag_trail("His blood down the bank", mat("old blood"), [(1.6, 10.1), (3.0, 10.4), (5.0, 10.6), (7.0, 10.2), (8.4, 9.7), (9.2, 9.3)], width=0.3, seed=10, height=height)
    kit.drag_trail("Fresher", mat("blood"), [(1.6, 10.0), (3.4, 10.3), (5.8, 10.5), (8.0, 9.8)], width=0.18, seed=11, height=height)
    pv, pf = [], []
    x, y, k = 1.8, 10.1, 0
    while x < 8.6:
        yy = y + (0.13 if k % 2 else -0.13)
        kit._stain(pv, pf, rng, (x, yy, height(x, yy) + 0.008), 0.07, 0.0, 0.2, (1.6, 0.8), k, points=10, drops=False)
        x += 0.5
        y += 0.05 if x < 5 else -0.12
        k += 1
    reb.mesh_object("His prints to the water", pv, pf, reb.mat_plain("Bootprints", (0.02, 0.014, 0.009), 0.4), smooth=False)
    plaid = reb.mat_stripes("Plaid", [(0.3, 0.04, 0.03), (0.04, 0.03, 0.03)], across=22)
    sawyer = kit.body("The sawyer", (SAWYER[0] - 0.8, SAWYER[1] + 0.2, POND_Z - 0.06), -0.35, pose="front", top=plaid, legs=mat("denim"), seed=14, missing=("l_hand",))
    kit.splat("Blood in the water", reb.mat_plain("Blood in water", (0.06, 0.008, 0.006), 0.05), (SAWYER[0], SAWYER[1], POND_Z + 0.015), 0.6, seed=15, stretch=(1.4, 1.0))
    hat_m = reb.mat_plain("Hard hat", (0.55, 0.38, 0.03), 0.4)
    hat = reb.prim("sphere", "Floating hard hat", hat_m, (14.2, 6.2, POND_Z + 0.06), (0.3, 0.26, 0.2), rot=(math.pi, 0.2, 0), segments=14)
    brim = reb.prim("cyl", "Hat brim", hat_m, (0, 0, 0.0), (0.36, 0.32, 0.015), segments=16)
    brim.parent = hat
    fish_m = reb.mat_surface("Dead fish", [(0.0, (0.35, 0.36, 0.33)), (1.0, (0.55, 0.55, 0.5))], scale=12, rough=0.3, bump=0.1)
    for k, (x, y, a) in enumerate(((11.2, 8.9, 0.4), (12.6, 9.1, 2.0), (7.6, 8.6, 1.0), (15.4, 8.8, 2.8), (10.4, 7.6, 0.2))):
        f = reb.prim("sphere", f"Dead fish {k}", fish_m, (x, y, POND_Z + 0.03), (0.32, 0.09, 0.07), rot=(0, 0, a), segments=10)
        reb.prim("cone", f"Fish tail {k}", fish_m, (x - 0.19 * math.cos(a), y - 0.19 * math.sin(a), POND_Z + 0.03), (0.04, 0.1, 0.1), rot=(0, math.pi / 2, a), segments=6)
    # Reeds along the south shore and the dam's foot, cattails among them.
    rv, rf = [], []
    for k in range(26):
        x = rng.uniform(DAM[1] + 0.2, 26.0)
        y = SHORE_Y + rng.uniform(-1.4, 0.5)
        if abs(x - SAWYER[0]) < 0.6 and abs(y - SAWYER[1]) < 0.5:
            continue
        reeds(rng, rv, rf, (x, y), rng.randint(14, 30), 0.25, z=max(POND_Z, height(x, y)))
    for k in range(8):
        reeds(rng, rv, rf, (DAM[1] + 0.4, rng.uniform(4.5, SHORE_Y)), 14, 0.2, z=POND_Z)
    for k in range(18):
        x, y = rng.uniform(16, 34), rng.uniform(-12, 4)
        reeds(rng, rv, rf, (x, y), 18, 0.3, z=POND_Z)
    reed_ob = reb.mesh_object("Reeds", rv, rf, mat("dead grass"), smooth=False)
    cv, cf = [], []
    for k in range(30):
        x, y = rng.uniform(DAM[1] + 0.3, 20.0), SHORE_Y + rng.uniform(-1.2, 0.3)
        reb.box(cv, cf, (x, y, POND_Z + 1.25 + rng.uniform(0, 0.4)), (0.05, 0.05, 0.22), rot=rng.uniform(0, 3))
    reb.mesh_object("Cattails", cv, cf, reb.mat_plain("Cattail", (0.12, 0.07, 0.03), 0.9), smooth=False)

    # ---- The bank: a rowboat turned over, a woodpile against the mill, grass, a crow on the dam rail.
    boat = kit.join("Rowboat", [reb.prim("sphere", "hull", reb.mat_plain("Boat green", (0.06, 0.12, 0.08), 0.6), (0, 0, 0.0), (3.2, 1.1, 0.7), segments=16),
                                reb.prim("cube", "keel", wet_timber, (0, 0, 0.33), (3.0, 0.08, 0.06))])
    settle(boat, (10.2, 13.1, 0.05), (0, 0, 0.3))
    boat.scale = (1, 1, 0.55)
    reb.wall(reb.prim("cube", "Boat footprint", None, (10.2, 13.1, 0.25), (3.2, 1.2, 0.5), rot=(0, 0, 0.3))).hide_render = True
    reb.mask(boat)
    kit.rod("Oar", planks, (12.0, 12.4, 0.03), (13.6, 13.1, 0.03), 0.03, 6)
    for k in range(4):
        z = 0.15 + k * 0.28
        kit.rod("Firewood", logs_m, (MILL_X + 0.25, 11.0, z), (MILL_X + 0.25, 12.6, z), 0.14, 8)
        kit.rod("Firewood", logs_m, (MILL_X + 0.55, 11.0, z), (MILL_X + 0.55, 12.6, z), 0.14, 8)
    reb.wall(reb.prim("cube", "Woodpile footprint", None, (MILL_X + 0.4, 11.8, 0.5), (0.8, 1.7, 1.0))).hide_render = True
    kit.crow("Crow on the dam rail", (DAM[1] - 0.05, 7.4, 1.05), heading=0.2)
    crow_b, crow_w = kit.crow("Crow on the bank", (7.6, 10.4, 0.0), heading=1.0)

    def verge(r_):
        while True:
            x, y = r_.uniform(X0, X1 + 6), r_.uniform(SHORE_Y + 0.3, Y1 + 4)
            if not (x < 9 and 9.6 < y < 11.0):
                return x, y
    grass = kit.meadow(rng, 1600, verge, height)

    # ---- The forest round the pond and behind the mill.
    cams = ((17.8, 13.4), (3.2, 13.5), (5.8, 2.4), (11.8, 11.2))

    def keep_out(x, y):
        if X0 - 1.0 < x < X1 + 1.0 and Y0 - 1.0 < y < Y1 + 0.8:
            return True
        if DAM[0] - 0.5 < x < 34 and -14 < y < SHORE_Y + 0.4:
            return True
        if x < MILL_X + 0.5 and y > -8:
            return True
        if abs(x - 4.3) < 1.5 and y < Y0 + 0.5 or abs(x - 8.2) < 1.5 and y < 0:
            return True
        return any((x - cx) ** 2 + (y - cy) ** 2 < 9 for cx, cy in cams)
    kit.forest(rng, height, keep_out, (-16, -24, 46, 32), count=120, spacing=1.8, tall=(13, 22), ferns=100, needles=700, dead=0.1)

    # ---- Light: noon under cloud, mist lying on the water.
    sun = kit.time_light("noon", sun_heading=200, sun_energy=3.2, mist=((14.0, 0.0, 0.2), (60.0, 50.0, 2.2), 0.012),
                         sky=((0.52, 0.55, 0.56), (0.36, 0.39, 0.42), 0.95))
    sun.data.angle = math.radians(18)
    sun.rotation_euler[0] = math.radians(30)

    anim = kit.Anim(16)
    anim.spin(wheel, axis=0, turns=-1, symmetry=24)
    anim.ripple(water)
    anim.bob(sawyer, height=0.02, speed=1)
    anim.bob(hat, height=0.03, speed=2)
    for f in floating:
        anim.bob(f, height=0.015, speed=1)
    anim.sway(reed_ob, amount=0.05, along=(1.0, 0.3), every=5, tip=4)
    anim.sway(grass, amount=0.06)
    anim.flies((8.6, 9.7, 0.05), count=8, radius=0.45)
    anim.bob(crow_b, height=0.04, speed=2)

    # ---- What the game needs.
    room.door("sawmill", (MILL_X, BACK_DOOR[0], MILL_X + 0.7, BACK_DOOR[1]), arrive=(2.6, 10.1), face=(1, 0), walk=False)
    room.door("flume", (BRIDGE[0], Y0, BRIDGE[1], Y0 + 0.6), arrive=(4.0, 3.8), face=(0, 1))
    room.check((SAWYER[0] - 1.8, SHORE_Y, SAWYER[0] + 0.6, SHORE_Y + 0.8), "A man face down in the reeds. His left sleeve is empty from the elbow.\nThe sawyer. He made it this far.")
    room.check((13.0, SHORE_Y, 15.4, SHORE_Y + 0.8), "A hard hat, floating out there. And dead fish, belly up.\nSomething's wrong with the water too.")
    room.spot("mill-race", (DAM[0], RACE_EW[3], DAM[1], RACE_EW[3] + 0.8))  # day/events.ts says what she sees and does here
    room.check((RACE_NS[1], 3.6, RACE_NS[1] + 1.0, 5.6), "The water wheel. It drives the mill through that shaft.\nIt's turning, but the mill isn't.")
    room.check((MILL_X, BACK_DOOR[0] - 0.6, MILL_X + 0.8, BACK_DOOR[0]), "A bloody hand on the mill's back door.")
    room.check((BRIDGE[0], Y0 + 0.6, BRIDGE[1], Y0 + 1.2), "A footbridge over the race. The flume's that way.")
    room.entry = "The mill pond. The wheel's still turning."
    room.export(anim)


build()
