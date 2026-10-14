"""Bravo team's helicopter where it came down last night, in a valley clearing at dusk.

What it tells: the S.T.A.R.S. Bravo helicopter lost power over the forest
last night and came down here. It slid in from the north-west: the snapped
spruces and the furrow it ploughed show the way. The tail boom broke off and
lies to the north-east, the main rotor is bent, one blade still creaks round
in the wind, and the engine is still smoking. Kevin, the pilot, never got
out: he is dead in his seat, still belted in, the windshield starred in
front of him. The rest of Bravo patched themselves up by the cargo door and
walked out: the medkit lies open with the bloody gauze round it, the cases
are pulled out and one is emptied, the field radio is smashed, a flare has
burnt down to a stub, and their boot prints run east to the valley path. In
the cargo bay, a crowbar.

Metres: the clearing is x 2-17, y 2-14 at z 0. The helicopter's cabin is
x 7.0-12.0, y 6.6-8.4, its nose to the west; the pilot's door (gone) and
the open cargo door are on the south side. The broken tail lies from
(13.8, 6.4) to (16.2, 3.8). A fallen spruce lies along the north-west edge.
The valley path leaves through the east edge at y 7-9.

Moving: one rotor blade swinging in the wind, smoke rising from the engine,
the engine's embers and the flare flickering, the grass.
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

X0, X1, Y0, Y1 = 2.0, 17.0, 2.0, 14.0
C = Vector((9.5, 7.5, 0.0))      # the helicopter's middle; its nose points -x
PATH = (7.0, 9.0)                # the valley path, east edge


def height(x, y):
    """Flat in the clearing, rising into the forest on every side."""
    h = 0.05 * noise.noise(Vector((x * 0.4, y * 0.4, 3)))
    dx = max(0.0, X0 - 0.5 - x, x - X1 - 0.5)
    dy = max(0.0, Y0 - 0.5 - y, y - Y1 - 0.5)
    d = math.hypot(dx, dy)
    return h + 0.07 * d + 0.4 * noise.noise(Vector((x * 0.15, y * 0.15, 1))) * min(1.0, d / 3)


def smoke_mat():
    """Smoke as a volume: each puff's density is its object colour's alpha,
    broken up by noise so it doesn't read as a ball."""
    m = bpy.data.materials.new("Smoke")
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.remove(nodes["Principled BSDF"])
    vol = nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.3, 0.28, 0.27, 1)
    info = nodes.new("ShaderNodeObjectInfo")
    n = nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 2.5
    n.inputs["Detail"].default_value = 4
    tc = nodes.new("ShaderNodeTexCoord")
    links.new(tc.outputs["Object"], n.inputs["Vector"])
    # Density: noise, faded toward the ball's edge, times the puff's alpha.
    grad = nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    links.new(tc.outputs["Object"], grad.inputs["Vector"])
    shape = nodes.new("ShaderNodeMath")
    shape.operation = "MULTIPLY"
    links.new(grad.outputs["Fac"], shape.inputs[0])
    links.new(n.outputs["Fac"], shape.inputs[1])
    amt = nodes.new("ShaderNodeMath")
    amt.operation = "MULTIPLY"
    links.new(shape.outputs[0], amt.inputs[0])
    links.new(info.outputs["Alpha"], amt.inputs[1])
    gain = nodes.new("ShaderNodeMath")
    gain.operation = "MULTIPLY"
    gain.inputs[1].default_value = 30.0
    links.new(amt.outputs[0], gain.inputs[0])
    links.new(gain.outputs[0], vol.inputs["Density"])
    links.new(vol.outputs["Volume"], nodes["Material Output"].inputs["Volume"])
    return m


def smoke(anim, base, count=12, rise=5.0, drift=(1.2, -0.5), seed=3):
    """Puffs climbing from `base`, swelling and thinning, round once a loop."""
    rng = random.Random(seed)
    m = smoke_mat()
    puffs = []
    for i in range(count):
        p = reb.prim("sphere", f"Smoke {i}", m, base, (1, 1, 1), segments=12)
        puffs.append((p, i / count, rng.uniform(-0.2, 0.2), rng.uniform(0.85, 1.15)))

    def f(k):
        for p, off, wob, sc in puffs:
            t = (k / anim.frames + off) % 1.0
            p.location = (base[0] + drift[0] * t + wob, base[1] + drift[1] * t, base[2] + rise * t)
            s = (0.5 + 1.8 * t) * sc
            p.scale = (s, s * 0.9, s * 0.8)
            p.color = (1, 1, 1, 0.6 * min(1.0, t * 6) * (1 - t))
    anim.custom(f)


def build():
    rng = random.Random(23)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1))
    room.camera((16.3, 10.2, 3.1), (8.6, 7.2, 0.9), 200, "from the valley path: the cabin's open side, the tail, the boot prints going out")
    room.camera((1.0, 1.3, 3.9), (10.5, 10.0, 0.0), 195, "from the snapped spruces: the furrow, the nose, the kit scattered beyond")
    room.camera((3.0, 13.4, 3.0), (10.2, 6.8, 0.9), 200, "from the south-west: the open pilot's door, Kevin in his seat, the medkit")
    room.camera((6.3, 10.6, 2.5), (8.3, 7.4, 1.2), 200, "close on the cockpit: Kevin belted in, the starred windshield")
    room.camera((15.6, 13.6, 3.4), (8.5, 6.5, 0.3), 200, "from the south-east: the cargo bay, the cases, the flare, the smoke")
    room.camera((13.8, 2.5, 3.6), (6.5, 11.0, 0.0), 200, "from the north-east by the tail: the bent rotor, the north side and the clearing south")

    navy = reb.mat_surface("Bravo navy", [(0.0, (0.02, 0.026, 0.045)), (0.75, (0.045, 0.055, 0.085)), (1.0, (0.09, 0.08, 0.07))], scale=3, rough=0.4, bump=0.1)
    scorched = reb.mat_surface("Scorched paint", [(0.0, (0.01, 0.01, 0.01)), (0.7, (0.04, 0.035, 0.03)), (1.0, (0.1, 0.06, 0.03))], scale=6, rough=0.8, bump=0.4)
    cabin_dark = reb.mat_plain("Cabin dark", (0.025, 0.025, 0.028), 0.8)
    seat_m = reb.mat_surface("Seat vinyl", [(0.0, (0.03, 0.03, 0.03)), (1.0, (0.07, 0.065, 0.06))], scale=10, rough=0.5, bump=0.2)
    canopy = reb.mat_plain("Canopy perspex", (0.05, 0.07, 0.09), 0.08)
    white = mat("white paint")
    olive = reb.mat_plain("Olive drab", (0.07, 0.08, 0.04), 0.7)
    case_m = reb.mat_surface("Hard case", [(0.0, (0.02, 0.02, 0.02)), (1.0, (0.05, 0.05, 0.05))], scale=8, rough=0.5, bump=0.1)
    foam = reb.mat_plain("Case foam", (0.03, 0.03, 0.035), 1.0)
    fuel = reb.mat_plain("Fuel", (0.015, 0.014, 0.012), 0.08)
    splinter = reb.mat_wood("Splintered pine", (0.5, 0.38, 0.22))
    gauze = reb.mat_surface("Bloody gauze", [(0.0, (0.5, 0.48, 0.42)), (0.55, (0.45, 0.4, 0.35)), (0.7, (0.25, 0.02, 0.01)), (1.0, (0.12, 0.005, 0.004))], scale=18, bump=0.2)

    # ---- Ground: the clearing, the furrow it ploughed, scorched earth under the engine.
    reb.terrain("Clearing", kit.dirtied(mat("grass"), 0.5, scale=0.6), (-14, 33), (-12, 30), height, step=0.5)
    kit.path_strip("Furrow", mat("mud"), [(0.5, 2.6), (3.0, 4.0), (5.2, 5.6), (7.0, 6.9)], height, width=0.7, wobble=0.35, lift=0.012)
    kit.path_strip("Skid scar", mat("dirt"), [(1.5, 4.4), (4.0, 5.7), (6.6, 7.9)], height, width=0.25, lift=0.01)
    kit.splat("Scorched earth", mat("black"), (11.2, 7.1, height(11.2, 7.1)), 1.3, seed=5, stretch=(1.4, 1.0), lumps=0.5)
    kit.splat("Fuel pool", fuel, (10.4, 8.9, height(10.4, 8.9)), 0.55, seed=6, stretch=(1.6, 0.8))
    kit.path_strip("Valley path", mat("dirt"), [(X1 - 1.5, 8.0), (X1 + 2.0, 8.2), (X1 + 8.0, 9.5), (X1 + 15.0, 9.0)], height, width=0.65)

    # ---- The helicopter, built level round C and then tipped as it lies.
    root = bpy.data.objects.new("Helicopter", None)
    bpy.context.scene.collection.objects.link(root)
    root.location = C
    bpy.context.view_layer.update()
    parts = []

    def H(x, y, z):
        return (C.x + x, C.y + y, z)

    def P(ob):
        parts.append(ob)
        return ob

    # Cabin shell: floor, roof, north side, back, the south side open at the pilot's door and the cargo door.
    P(reb.prim("cube", "Cabin floor", cabin_dark, H(0.25, 0, 0.5), (3.7, 1.8, 0.1)))
    P(reb.prim("cube", "Belly", navy, H(0.25, 0, 0.38), (3.8, 1.8, 0.2), bevel=0.06))
    P(reb.prim("cube", "Roof", navy, H(0.4, 0, 2.0), (3.4, 1.8, 0.1), bevel=0.05))
    P(reb.prim("cube", "North side", navy, H(0.25, -0.88, 1.25), (3.7, 0.06, 1.5)))
    P(reb.prim("cube", "Back bulkhead", navy, H(2.08, 0, 1.25), (0.08, 1.8, 1.6)))
    P(reb.prim("cube", "Door pillar", navy, H(0.3, 0.88, 1.25), (0.14, 0.06, 1.5)))
    P(reb.prim("cube", "South side, aft", navy, H(1.75, 0.88, 1.25), (0.66, 0.06, 1.5)))
    P(reb.prim("cube", "Cargo door, slid back", navy, H(2.35, 0.96, 1.2), (1.3, 0.05, 1.4)))
    P(reb.prim("cube", "Door rail", mat("steel"), H(1.2, 0.93, 1.95), (2.8, 0.04, 0.04)))
    P(reb.prim("cube", "Cabin inside", cabin_dark, H(0.3, -0.84, 1.25), (3.5, 0.02, 1.4)))
    for x in (-0.95, -0.15, 0.6):
        P(reb.prim("cube", "Window, north", canopy, H(x, -0.9, 1.55), (0.55, 0.02, 0.45)))
    # Nose and the starred canopy.
    P(reb.prim("sphere", "Nose", navy, H(-1.75, 0, 0.8), (1.6, 1.72, 0.85), segments=20))
    P(reb.prim("sphere", "Canopy", canopy, H(-1.55, 0, 1.38), (1.4, 1.66, 1.12), segments=20))
    P(reb.prim("cube", "Canopy frame", navy, H(-1.5, 0, 1.45), (1.2, 0.06, 1.0), rot=(0, 0.6, 0)))
    P(reb.prim("cube", "Console", cabin_dark, H(-1.1, 0, 0.95), (0.5, 1.5, 0.5), rot=(0, 0.35, 0)))
    hub = Vector(H(-2.15, 0.35, 1.5))
    for i in range(12):
        a = 2 * math.pi * i / 12 + rng.uniform(-0.2, 0.2)
        d = Vector((math.sin(a) * 0.15, math.cos(a), math.sin(a))).normalized() * rng.uniform(0.15, 0.4)
        P(kit.rod("Crack", reb.mat_plain("Crack", (0.7, 0.72, 0.75), 0.3), hub, hub + d, 0.003, 4))
    P(kit.splat("Blood on the canopy", mat("blood"), H(-2.05, 0.45, 1.35), 0.12, rot=(0, -1.2, 0), seed=11, stretch=(1.0, 1.5)))
    # Engine housing on the roof, scorched, its exhaust smoking; the mast and rotor head.
    P(reb.prim("cube", "Engine housing", navy, H(1.0, 0, 2.32), (2.0, 1.1, 0.55), bevel=0.12))
    P(reb.prim("cube", "Engine cowl, burst", scorched, H(1.55, 0.35, 2.45), (0.9, 0.5, 0.35), rot=(0.5, 0, 0.2), bevel=0.04))
    for dy in (-0.3, 0.3):
        P(kit.rod("Exhaust", scorched, H(1.9, dy, 2.4), H(2.4, dy * 1.3, 2.55), 0.11, 10))
    ember_m = reb.mat_emit("Embers", (1.0, 0.32, 0.06), 8)
    for i in range(7):
        P(reb.prim("sphere", f"Ember {i}", ember_m, H(1.4 + rng.uniform(-0.3, 0.4), rng.uniform(0.05, 0.5), 2.55 + rng.uniform(0, 0.1)), (0.06, 0.06, 0.04), segments=6))
    P(kit.rod("Rotor mast", mat("iron"), H(0.3, 0, 2.55), H(0.3, 0, 3.05), 0.1))
    P(reb.prim("cyl", "Rotor hub", mat("iron"), H(0.3, 0, 3.05), (0.45, 0.45, 0.18), segments=16))
    # The rotor: one blade drooping to the ground, one snapped short, one gone, one still free and turning.
    P(reb.prim("cube", "Blade, drooping", navy, H(0.0, -2.9, 2.0), (0.32, 5.6, 0.05), rot=(-0.36, 0.0, 0.08)))
    P(reb.prim("cube", "Blade, snapped", navy, H(-0.55, 0.55, 3.03), (1.6, 0.32, 0.05), rot=(0, 0.05, -0.75)))
    P(kit.splat("Snapped end", splinter, H(-1.1, 1.05, 3.06), 0.12, seed=4))
    blade_pivot = bpy.data.objects.new("Blade pivot", None)
    bpy.context.scene.collection.objects.link(blade_pivot)
    blade_pivot.location = H(0.3, 0, 3.1)
    bpy.context.view_layer.update()
    free = reb.prim("cube", "Blade, free", navy, H(3.1, 0, 3.1), (5.5, 0.32, 0.05), rot=(0.06, 0.04, 0))
    tip = reb.prim("cube", "Blade tip", mat("yellow paint"), H(5.6, 0, 3.1), (0.5, 0.33, 0.055))
    for p in (free, tip):
        p.parent = blade_pivot
        p.matrix_parent_inverse = blade_pivot.matrix_world.inverted()
    blade_pivot.rotation_euler = (0, 0, 2.3)
    P(blade_pivot)
    # Skids: the north one buckled under her.
    for dy, sag in ((-0.85, 0.12), (0.85, 0.0)):
        P(kit.rod("Skid", mat("steel"), H(-1.6, dy, 0.1 - sag), H(1.9, dy, 0.08), 0.045))
        P(kit.rod("Skid toe", mat("steel"), H(-1.6, dy, 0.1 - sag), H(-1.9, dy, 0.3), 0.045))
        for x in (-0.8, 1.2):
            P(kit.rod("Skid strut", mat("steel"), H(x, dy, 0.1 - sag * 0.5), H(x, dy * 0.7, 0.4), 0.04))
    # The tail boom's stump, torn off behind the cabin.
    P(kit.rod("Tail boom stump", navy, H(2.1, 0, 1.55), H(3.9, 0, 1.75), 0.32, 12))
    P(reb.prim("cone", "Torn end", scorched, H(4.0, 0, 1.76), (0.62, 0.62, 0.25), rot=(0, math.pi / 2, 0), top=0.7, segments=12))
    for i in range(5):
        a = rng.uniform(0, 2 * math.pi)
        P(kit.rod("Torn wire", mat("rust"), H(4.05, math.cos(a) * 0.2, 1.76 + math.sin(a) * 0.2), H(4.4 + rng.uniform(0, 0.3), math.cos(a) * 0.35, 1.7 + math.sin(a) * 0.3 - rng.uniform(0, 0.4)), 0.008, 4))
    # Livery: S.T.A.R.S. down the south side, a white cheat line, the number.
    P(reb.prim("cube", "Cheat line", white, H(1.75, 0.915, 0.82), (0.66, 0.01, 0.06)))
    P(reb.prim("cube", "Cheat line fwd", white, H(-0.45, 0.915, 0.82), (0.14, 0.01, 0.06)))
    P(kit.text("Side lettering", "S.T.A.R.S.", white, H(3.0, 0.33, 1.65), size=0.22, rot=(math.pi / 2, 0, math.pi)))
    P(kit.text("Side lettering N", "S.T.A.R.S.", white, H(3.0, -0.33, 1.65), size=0.22))
    P(kit.text("Tail number", "RPD-02", white, H(1.75, 0.92, 1.45), size=0.1, rot=(math.pi / 2, 0, math.pi)))
    P(kit.splat("Soot up the side", mat("black"), H(1.6, 0.92, 1.9), 0.35, rot=(math.pi / 2, 0, 0), seed=12, stretch=(1.6, 0.8)))

    # ---- Kevin, still belted into the right-hand seat, slumped toward the open door.
    P(reb.prim("cube", "Pilot seat", seat_m, H(-0.5, 0.42, 0.78), (0.5, 0.52, 0.12)))
    P(reb.prim("cube", "Pilot seat back", seat_m, H(-0.22, 0.42, 1.25), (0.1, 0.52, 0.85), rot=(0, -0.12, 0)))
    P(reb.prim("cube", "Co-pilot seat", seat_m, H(-0.5, -0.42, 0.78), (0.5, 0.52, 0.12)))
    P(reb.prim("cube", "Co-pilot seat back", seat_m, H(-0.22, -0.42, 1.25), (0.1, 0.52, 0.85), rot=(0, -0.12, 0)))
    flight = reb.mat_surface("Flight suit", [(0.0, (0.14, 0.15, 0.1)), (0.8, (0.22, 0.23, 0.16)), (1.0, (0.18, 0.04, 0.03))], scale=12, bump=0.2)
    seat = Vector(H(-0.25, 0.42, 0.72))
    kevin = kit.body("Kevin", tuple(seat), heading=math.pi, pose="slumped", top=flight, legs=flight, seed=4)
    kevin.rotation_euler = (0.2, 0.0, math.pi)
    P(kevin)
    P(reb.prim("sphere", "Kevin's helmet", mat("white paint"), (seat.x - 0.2, seat.y - 0.05, seat.z + 0.9), (0.24, 0.22, 0.2), segments=14))
    strap = reb.mat_plain("Harness webbing", (0.12, 0.1, 0.06), 0.8)
    for sy, hy in ((0.2, -0.11), (-0.2, 0.11)):
        P(kit.rod("Harness strap", strap, (seat.x - 0.13, seat.y - sy, seat.z + 0.7), (seat.x - 0.24, seat.y - hy, seat.z + 0.18), 0.022, 4))
    P(kit.rod("Lap belt", strap, (seat.x - 0.26, seat.y - 0.24, seat.z + 0.2), (seat.x - 0.26, seat.y + 0.24, seat.z + 0.2), 0.022, 4))
    P(kit.splat("Blood down his front", mat("blood"), (seat.x - 0.22, seat.y, seat.z + 0.55), 0.09, rot=(0, -math.pi / 2, 0), seed=8, stretch=(0.7, 1.8)))
    P(kit.splat("Blood on the seat", mat("old blood"), (seat.x - 0.35, seat.y + 0.1, seat.z + 0.13), 0.18, seed=9))
    # The cargo bay: a crowbar on the floor, webbing, a rope, a box of flares.
    P(reb.prim("cube", "Crowbar", reb.mat_plain("Crowbar red", (0.3, 0.03, 0.02), 0.5), H(1.0, 0.55, 0.57), (0.8, 0.035, 0.035), rot=(0, 0, 0.35)))
    P(reb.prim("cube", "Crowbar claw", mat("steel"), H(1.4, 0.69, 0.58), (0.1, 0.035, 0.05), rot=(0, 0.6, 0.35)))
    P(reb.prim("cube", "Flare box", reb.mat_plain("Flare box", (0.4, 0.1, 0.03), 0.6), H(1.7, -0.5, 0.65), (0.4, 0.3, 0.2)))
    for i in range(4):
        P(reb.prim("cyl", f"Rope coil {i}", mat("canvas"), H(0.6, -0.4, 0.58 + i * 0.03), (0.45 - i * 0.04, 0.45 - i * 0.04, 0.03), segments=16))
    P(kit.rod("Cargo net", strap, H(1.95, -0.8, 1.7), H(1.95, 0.6, 0.7), 0.012, 4))
    P(kit.rod("Cargo net", strap, H(1.95, 0.6, 1.7), H(1.95, -0.8, 0.7), 0.012, 4))

    # The cockpit's dome lamp, still on off the battery, failing.
    dome_m = reb.mat_emit("Cockpit lamp", (1.0, 0.82, 0.55), 12)
    P(reb.prim("sphere", "Cockpit lamp", dome_m, H(-0.7, 0, 1.93), (0.08, 0.08, 0.04), segments=8))

    for p in parts:
        p.parent = root
        p.matrix_parent_inverse = root.matrix_world.inverted()
    root.rotation_euler = (0.07, -0.05, 0.12)
    bpy.context.view_layer.update()
    for name in ("Belly", "Roof", "North side", "Back bulkhead", "South side, aft", "Nose", "Canopy", "Engine housing", "Tail boom stump", "Cargo door, slid back", "Door pillar"):
        reb.mask(bpy.data.objects[name])
    reb.wall(reb.prim("cube", "Cabin footprint", None, (9.6, 7.5, 0.5), (4.6, 1.8, 1.0), rot=(0, 0, 0.12))).hide_render = True
    reb.wall(reb.prim("cube", "Boom footprint", None, (12.4, 7.85, 0.5), (1.6, 0.7, 1.0), rot=(0, 0, 0.12))).hide_render = True

    # ---- The tail, thrown off to the north-east: boom, fin, the tail rotor.
    a, b = Vector((13.8, 6.4, 0.32)), Vector((16.4, 3.6, 0.3))
    reb.mask(kit.rod("Tail boom", navy, a, b, 0.26, 12))
    reb.prim("cone", "Tail boom end", scorched, a + (a - b).normalized() * 0.1, (0.55, 0.55, 0.2), rot=(math.pi / 2, 0, math.atan2((b - a).y, (b - a).x) - math.pi / 2), top=0.7, segments=12)
    fin = reb.prim("cube", "Tail fin", navy, (16.3, 3.75, 0.85), (0.08, 0.7, 1.2), rot=(0.35, 0.4, -0.82))
    reb.prim("cube", "Tail rotor blade", mat("steel"), (16.6, 4.0, 1.0), (0.08, 1.3, 0.12), rot=(0.9, 0, -0.82))
    reb.prim("cube", "Tail rotor blade 2", mat("steel"), (16.6, 4.0, 1.0), (0.08, 1.3, 0.12), rot=(-0.7, 0, -0.82))
    kit.text("Boom lettering", "BRAVO", white, ((a.x + b.x) / 2 + 0.2, (a.y + b.y) / 2 + 0.2, 0.5), size=0.18, rot=(math.pi / 2, 0, math.atan2((b - a).y, (b - a).x) + math.pi))
    for t in (0.15, 0.5, 0.85):
        p = a.lerp(b, t)
        reb.wall(reb.prim("cube", "Tail footprint", None, (p.x, p.y, 0.4), (0.9, 0.9, 0.8))).hide_render = True
    kit.splat("Gouge at the tail", mat("mud"), (14.6, 5.6, height(14.6, 5.6)), 0.6, seed=14, stretch=(1.8, 0.6))
    # A broken blade, thrown into the grass.
    reb.prim("cube", "Thrown blade", navy, (5.2, 10.8, height(5.2, 10.8) + 0.04), (3.4, 0.32, 0.05), rot=(0.05, 0, 0.6))
    reb.prim("cube", "Thrown blade tip", mat("yellow paint"), (6.6, 11.75, height(6.6, 11.75) + 0.05), (0.5, 0.33, 0.055), rot=(0.05, 0, 0.6))
    kit.shards("Perspex in the grass", (7.3, 8.5, height(7.3, 8.5)), spread=1.2, count=40, seed=3)
    kit.shards("Perspex by the nose", (6.6, 7.0, height(6.6, 7.0)), spread=0.8, count=20, seed=4)
    # The pilot's door, torn off and lying on its face.
    reb.prim("cube", "Pilot's door", navy, (7.6, 10.2, height(7.6, 10.2) + 0.04), (1.1, 0.06, 1.3), rot=(math.pi / 2 - 0.05, 0, 0.4))

    # ---- Where Bravo patched themselves up: the medkit, the gauze, the cases, the radio, a flare.
    def gz(x, y):
        return height(x, y)
    mk = (9.0, 10.3)
    kit.box("Medkit", white, (mk[0], mk[1], gz(*mk)), (0.5, 0.35, 0.14), rot=0.3)
    reb.prim("cube", "Medkit lid", white, (mk[0] + 0.05, mk[1] + 0.38, gz(*mk) + 0.012), (0.5, 0.35, 0.025), rot=(0, 0, 0.3))
    kit.text("Medkit cross", "+", mat("red paint"), (mk[0] + 0.05, mk[1] + 0.38, gz(*mk) + 0.03), size=0.22, rot=(0, 0, 0.3))
    for i in range(7):
        reb.cloth(f"Gauze {i}", gauze, (mk[0] - 0.5 + rng.uniform(-0.5, 0.5), mk[1] + rng.uniform(-0.3, 0.6), gz(*mk) + 0.015), (0.16, 0.1), rot=(0, 0, rng.uniform(0, 3)), cuts=6, lumps=0.015, seed=i)
    for i in range(6):
        reb.prim("cube", f"Wrapper {i}", mat("white paint"), (mk[0] + rng.uniform(-0.9, 0.8), mk[1] + rng.uniform(-0.4, 0.7), gz(*mk) + 0.003), (0.09, 0.06, 0.002), rot=(0, 0, rng.uniform(0, 3)))
    kit.splat("Where someone sat bleeding", mat("old blood"), (mk[0] - 0.6, mk[1] + 0.2, gz(*mk)), 0.35, seed=15, stretch=(1.3, 0.9))
    cases = [((10.6, 9.6), 0.2, False), ((11.5, 10.4), 1.1, True), ((12.4, 9.5), -0.4, False)]
    for i, ((x, y), r, opened) in enumerate(cases):
        kit.box(f"Hard case {i}", case_m, (x, y, gz(x, y)), (0.8, 0.5, 0.25), rot=r, bevel=0.02)
        if opened:
            reb.prim("cube", f"Case foam {i}", foam, (x, y, gz(x, y) + 0.252), (0.72, 0.42, 0.01), rot=(0, 0, r))
            reb.prim("cube", f"Case lid {i}", case_m, (x - 0.1, y + 0.42, gz(x, y) + 0.03), (0.8, 0.5, 0.06), rot=(0, 0, r))
            for j in range(3):
                reb.prim("cube", f"Empty cut-out {i}{j}", mat("black"), (x - 0.2 + j * 0.2, y, gz(x, y) + 0.258), (0.12, 0.3, 0.004), rot=(0, 0, r))
    kit.box("Case on end", case_m, (12.0, 11.3, gz(12.0, 11.3)), (0.5, 0.25, 0.8), rot=2.2, bevel=0.02)
    # The field radio, smashed: someone tried, and gave up.
    rx, ry = 7.6, 9.4
    kit.box("Field radio", olive, (rx, ry, gz(rx, ry)), (0.42, 0.28, 0.3), rot=-0.4, bevel=0.01)
    kit.rod("Radio aerial", mat("steel"), (rx + 0.12, ry - 0.05, gz(rx, ry) + 0.3), (rx + 0.65, ry - 0.5, gz(rx, ry) + 0.04), 0.006, 4)
    reb.prim("cube", "Radio handset", mat("black"), (rx - 0.4, ry + 0.2, gz(rx, ry) + 0.03), (0.2, 0.07, 0.05), rot=(0, 0, 1.0))
    kit.shards("Radio dial glass", (rx + 0.1, ry + 0.3, gz(rx, ry)), spread=0.3, count=8, seed=8)
    # A flare, burnt down to a stub, still sputtering red.
    fx, fy = 12.9, 11.6
    flare_m = reb.mat_emit("Flare", (1.0, 0.12, 0.05), 30)
    reb.prim("cyl", "Flare stub", reb.mat_plain("Flare paper", (0.4, 0.05, 0.03), 0.6), (fx, fy, gz(fx, fy) + 0.03), (0.04, 0.04, 0.18), rot=(math.pi / 2, 0, 0.7), segments=8)
    reb.prim("sphere", "Flare flame", flare_m, (fx + 0.07, fy + 0.07, gz(fx, fy) + 0.04), (0.05, 0.05, 0.05), segments=8)
    flare = reb.point("Flare light", (fx + 0.07, fy + 0.07, gz(fx, fy) + 0.25), 40, (1.0, 0.12, 0.06), 0.05)
    kit.splat("Flare ash", mat("black"), (fx, fy, gz(fx, fy)), 0.2, seed=16)
    # Their boot prints, out east to the valley path.
    for i in range(16):
        t = i / 15
        x = 12.0 + (X1 - 0.3 - 12.0) * t
        y = 10.0 + (8.1 - 10.0) * t + (0.13 if i % 2 else -0.13)
        kit.splat(f"Boot print {i}", mat("mud"), (x, y, gz(x, y)), 0.07, rot=(0, 0, -0.25), seed=30 + i, stretch=(1.5, 0.6), lumps=0.2)
    kit.drag_trail("Blood drips", mat("blood"), [(9.4, 9.8), (11.0, 9.9), (13.0, 9.4)], width=0.08, seed=17, height=gz)

    # ---- Where it came in: spruces snapped off, one fallen along the north-west edge.
    for x, y, h in ((1.0, 3.2, 2.4), (0.0, 1.8, 3.1), (3.4, 1.0, 1.6), (-1.0, 4.5, 2.0)):
        kit.rod("Snapped trunk", mat("bark"), (x, y, height(x, y) - 0.1), (x, y, height(x, y) + h), 0.22, 9)
        reb.prim("cone", "Splintered top", splinter, (x, y, height(x, y) + h + 0.2), (0.4, 0.4, 0.45), segments=7, top=0.15)
    log = kit.rod("Fallen spruce", mat("bark"), (2.6, 2.4, 0.3), (7.8, 1.6, 0.28), 0.3, 10)
    reb.wall(log)
    reb.mask(log)
    bv, bf = [], []
    for i in range(70):
        t = rng.uniform(0.25, 1.0)
        p = Vector((2.6, 2.4, 0.4)).lerp(Vector((8.6, 1.5, 0.4)), t)
        a = rng.uniform(0, 2 * math.pi)
        reb.card(bv, bf, p, Vector((math.cos(a) * 0.3, math.sin(a), 0.4)).normalized(), Vector((0, 0, 1)), 0.25, 0.9 * (1.2 - t), 0.4)
    reb.mesh_object("Fallen spruce boughs", bv, bf, mat("needles"))
    for i in range(10):
        p = (rng.uniform(1.5, 8.5), rng.uniform(2.3, 5.0))
        q = (p[0] + rng.uniform(-0.8, 0.8), p[1] + rng.uniform(-0.8, 0.8))
        kit.rod("Broken branch", mat("bark"), (p[0], p[1], gz(*p) + 0.04), (q[0], q[1], gz(*q) + 0.06), rng.uniform(0.02, 0.05), 5)

    # ---- The forest round it, the grass in the clearing.
    cams = ((16.3, 10.2), (1.0, 1.3), (3.0, 13.4), (6.3, 10.6), (15.6, 13.6), (13.8, 2.5))

    def keep_out(x, y):
        return (X0 - 1.0 < x < X1 + 1.0 and Y0 - 1.0 < y < Y1 + 1.0) or (x > X1 - 1 and 6.5 < y < 10.5) or (x < 4 and y < 4.5) or any((x - cx) ** 2 + (y - cy) ** 2 < 6 for cx, cy in cams)
    kit.forest(rng, height, keep_out, (-10, -9, 29, 25), count=95, ferns=30, needles=500, dead=0.08)
    kit.forest(rng, height, lambda x, y: -6 < x < 25 and -5 < y < 21, (-26, -24, 45, 40), count=70, spacing=3.0, tall=(15, 22), ferns=0, needles=0)

    def turf(r):
        while True:
            x, y = r.uniform(X0 - 2, X1 + 2), r.uniform(Y0 - 2, Y1 + 2)
            if not (6.5 < x < 12.6 and 6.3 < y < 8.8):
                return x, y
    grass = kit.meadow(rng, 2200, turf, height)
    kit.meadow(rng, 300, lambda r: (r.uniform(X0 - 1, X1 + 1), r.uniform(Y0 - 1, Y1 + 1)), height, mat("dead grass"))
    rv, rf = [], []
    for (x, y, r) in ((1.0, 12.0, 0.7), (17.8, 12.8, 0.6), (4.5, 14.6, 0.5), (17.6, 2.6, 0.8)):
        reb.boulder(rng, (x, y, height(x, y)), r, rv, rf)
    reb.mesh_object("Rocks", rv, rf, mat("rock"))

    # ---- Light: the sun gone down behind the trees in the west, a red sky; the embers and the flare.
    kit.time_light("dusk", sun_heading=275, sun_energy=2.4)
    reb.spot("Last light", (-8.0, 6.0, 9.0), (10.0, 8.0, 0.0), 1800, (1.0, 0.42, 0.22), 45, 0.8, 1.5)
    reb.spot("Sky fill", (14.0, 18.0, 14.0), (9.0, 7.0, 0.0), 1400, (0.45, 0.5, 0.8), 70, 0.9, 3.0)
    embers = reb.point("Engine embers", H(1.4, 0.2, 2.75), 60, (1.0, 0.35, 0.08), 0.2)
    dome = reb.point("Cockpit lamp light", (C.x - 0.75, C.y + 0.1, 1.8), 10, (1.0, 0.8, 0.55), 0.05)

    anim = kit.Anim(16)
    anim.swing(blade_pivot, axis=2, degrees=12)
    smoke(anim, Vector(H(2.3, 0.3, 2.8)), count=8)
    anim.flicker(embers, ember_m, depth=0.35, dropouts=1)
    anim.flicker(flare, flare_m, depth=0.4, dropouts=1)
    anim.flicker(dome, dome_m, depth=0.5, dropouts=3)
    anim.sway(grass, amount=0.05)

    # ---- What the game needs.
    room.door("valley-path", (X1 - 0.6, PATH[0], X1, PATH[1]), arrive=(15.6, 8.0), face=(-1, 0))
    room.check((7.6, 8.4, 9.0, 9.4), "Kevin. He's still belted into his seat.\nHe flew us out here. He stayed with it.")
    room.check((9.8, 8.4, 11.4, 9.2), "The cargo bay. Rope, a box of flares...\nA crowbar on the floor.")
    room.check((8.2, 9.9, 9.8, 10.9), "Someone patched themselves up here.\nThe medkit's empty. The gauze is soaked.")
    room.check((10.1, 9.2, 12.9, 10.9), "Our cases. Somebody took what they could carry.")
    room.check((7.0, 9.0, 8.2, 9.9), "The field radio. Someone's smashed it.\nOr dropped it, trying.")
    room.check((13.5, 4.0, 16.5, 6.6), "The tail broke clean off when she came down.")
    room.check((12.4, 11.1, 13.4, 12.1), "A flare, burnt down to nothing.\nThey were signalling. Nobody came.")
    room.check((14.5, 7.3, 16.4, 9.3), "Boot prints in the mud, heading east.\nThe others walked out.")
    room.entry = "The helicopter.\nThis is where we came down."
    room.export(anim, samples=128)


build()
