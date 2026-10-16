"""The mine lift's cage, at the foot of its shaft.

What it tells: the cage that took the silver miners up and down still
hangs here, an iron box of mesh with a gate at each end: the south gate
onto the junction at the bottom, the north gate onto the head house at the
summit when it is up there. Someone tried to ride it up and never got to
pull the lever: an old miner's cap lamp lies dead on the floor plates in a
dried smear, its battery strap snapped, and web has grown over the corners
since. The controls are an iron box with UP and DOWN and a bell pull; the
sign says MAX 6 MEN. Past the mesh, the counterweight's cable runs down
the shaft beside the cage, and it creeps when the motor up top is live.

Metres: the floor is the cage, x 1.0-2.9, y 1.0-2.55, 2.2 high under its
roof. The south gate (y 2.55) opens onto the junction; the north gate
(y 1.0) onto the summit's head house when the cage is at the top. The
controls are on the east side, the bell pull by them, the lamp on the
floor in the north-west corner. Rock is close at the sides; north, behind the
gate, a bare landing and a ladder up the shaft; south, past the gate, the
junction's floor and its lamps. The cameras look in through the two gates.

Moving: the counterweight cable creeping past, the bulb in the roof
flickering, the bell pull swaying.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
from kit import mat  # noqa: E402
from mathutils import Vector, noise  # noqa: E402

X0, X1, Y0, Y1, H = 1.0, 2.9, 1.0, 2.55, 2.2


def rock_face(name, m, origin, u, v, nu, nv, out, depth=0.15, seed=0):
    """A lumpy rock surface over the rectangle origin + s*u + t*v, pushed back along `out` by noise."""
    o, u, v, out = Vector(origin), Vector(u), Vector(v), Vector(out).normalized()
    verts, faces = [], []
    for j in range(nv + 1):
        for i in range(nu + 1):
            p = o + u * (i / nu) + v * (j / nv)
            d = depth * (0.6 + noise.noise(p * 1.2 + Vector((seed, 0, 0))) + 0.35 * noise.noise(p * 3.5 + Vector((0, seed, 0))))
            verts.append(tuple(p + out * max(-0.03, d)))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    return reb.mesh_object(name, verts, faces, m)


def running_cable(name):
    """A cable banded light and dark along its length; the Anim slides the bands so it runs."""
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Roughness"].default_value = 0.4
    bsdf.inputs["Metallic"].default_value = 0.6
    tc = nodes.new("ShaderNodeTexCoord")
    mp = nodes.new("ShaderNodeMapping")
    mp.name = "Run"
    links.new(tc.outputs["Object"], mp.inputs["Vector"])
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(mp.outputs["Vector"], sep.inputs["Vector"])
    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 2.5
    links.new(sep.outputs["Z"], mul.inputs[0])
    frac = nodes.new("ShaderNodeMath")
    frac.operation = "FRACT"
    links.new(mul.outputs[0], frac.inputs[0])
    reb.ramp(nodes, links, frac.outputs[0], [(0.0, (0.05, 0.045, 0.04)), (0.82, (0.08, 0.07, 0.06)), (0.86, (0.45, 0.38, 0.1)), (1.0, (0.45, 0.38, 0.1))])
    r = [nd for nd in nodes if nd.type == "VALTORGB"][-1]
    r.color_ramp.interpolation = "CONSTANT"
    links.new(r.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def gate(name, m, y, x0, x1, rng):
    """A lattice gate across the cage at y: uprights and diagonals, in one object."""
    parts = []
    for k in range(9):
        x = x0 + (x1 - x0) * k / 8
        parts.append(kit.rod("Gate bar", m, (x, y, 0.1), (x, y, 1.95), 0.012, 4))
    for z in (0.3, 0.95, 1.6):
        for k in range(8):
            xa = x0 + (x1 - x0) * k / 8
            xb = x0 + (x1 - x0) * (k + 1) / 8
            parts.append(kit.rod("Gate lattice", m, (xa, y, z - 0.15), (xb, y, z + 0.15), 0.008, 4))
            parts.append(kit.rod("Gate lattice", m, (xa, y, z + 0.15), (xb, y, z - 0.15), 0.008, 4))
    parts.append(kit.rod("Gate rail", m, (x0, y, 1.97), (x1, y, 1.97), 0.02, 6))
    parts.append(kit.rod("Gate rail", m, (x0, y, 0.08), (x1, y, 0.08), 0.02, 6))
    return kit.join(name, parts)


def build():
    rng = random.Random(17)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.ground("metal")  # the cage's floor plates
    room.camera((2.55, 4.5, 2.4), (1.85, 1.4, 0.5), 200, "from the junction, through the south gate: the dead lamp, the smear, the controls, the counterweight cable running in the shaft")
    room.camera((1.35, -0.75, 2.45), (2.15, 2.3, 0.4), 200, "from the shaft behind the cage, through the north gate: the controls, the bell pull, the junction's lamps beyond")

    rock = kit.dirtied(mat("wet rock"), 0.55)
    rust = mat("rust")
    iron = mat("iron")
    plate = reb.mat_surface("Floor plate", [(0.0, (0.05, 0.045, 0.04)), (0.6, (0.12, 0.11, 0.1)), (1.0, (0.2, 0.1, 0.05))], scale=9, rough=0.5, bump=0.9)
    cable_m = running_cable("Running cable")

    # ---- The cage: plate floor, roof, corner posts, mesh sides, the two gates.
    reb.prim("cube", "Cage floor", plate, ((X0 + X1) / 2, (Y0 + Y1) / 2, -0.04), (X1 - X0 + 0.1, Y1 - Y0 + 0.1, 0.08))
    for k in range(6):
        reb.prim("cube", "Plate seam", iron, ((X0 + X1) / 2, Y0 + 0.25 + k * 0.25, 0.002), (X1 - X0, 0.015, 0.004))
    reb.prim("cube", "Cage roof", iron, ((X0 + X1) / 2, (Y0 + Y1) / 2, H + 0.04), (X1 - X0 + 0.1, Y1 - Y0 + 0.1, 0.08))
    reb.prim("cube", "Roof hatch", rust, ((X0 + X1) / 2 + 0.3, (Y0 + Y1) / 2, H - 0.005), (0.6, 0.6, 0.02))
    for x in (X0 - 0.03, X1 + 0.03):
        for y in (Y0 - 0.03, Y1 + 0.03):
            kit.rod("Cage corner", rust, (x, y, -0.05), (x, y, H + 0.05), 0.035, 6)
    # The sides are open bar-work, so the shaft's rock and the running cable show through: one object.
    bars = []
    for x in (X0 - 0.03, X1 + 0.03):
        for k in range(1, 7):
            y = Y0 + (Y1 - Y0) * k / 7
            bars.append(kit.rod("Side bar", rust, (x, y, 0.0), (x, y, H), 0.011, 4))
        for z in (0.1, 1.05, 2.0):
            bars.append(kit.rod("Side rail", rust, (x, Y0, z), (x, Y1, z), 0.028, 6))
    kit.join("Cage sides", bars)
    reb.mask(gate("South gate", rust, Y1 + 0.02, X0, X1, rng))
    gate("North gate", rust, Y0 - 0.02, X0, X1, rng)
    reb.prim("cube", "Crosshead", iron, ((X0 + X1) / 2, (Y0 + Y1) / 2, H + 0.3), (X1 - X0 + 0.3, 0.2, 0.25))
    kit.rod("Hoist rope", iron, ((X0 + X1) / 2, (Y0 + Y1) / 2, H + 0.42), ((X0 + X1) / 2, (Y0 + Y1) / 2, H + 12.0), 0.03, 8)

    # ---- The controls on the east side, the bell pull, the sign.
    box = reb.prim("cube", "Control box", kit.dirtied(mat("green paint"), 0.6), (X1 - 0.08, 1.95, 1.15), (0.14, 0.32, 0.45), bevel=0.02)
    reb.mask(box)
    kit.rod("Lever slot", mat("black"), (X1 - 0.155, 1.95, 1.0), (X1 - 0.155, 1.95, 1.3), 0.012, 4)
    kit.rod("Control lever", mat("steel"), (X1 - 0.16, 1.95, 1.15), (X1 - 0.38, 1.95, 1.3), 0.015, 6)
    reb.prim("sphere", "Lever knob", mat("black"), (X1 - 0.38, 1.95, 1.3), (0.06, 0.06, 0.06))
    for words, z in (("UP", 1.33), ("DOWN", 0.97)):
        kit.text(f"Control {words}", words, mat("white paint"), (X1 - 0.152, 2.07, z), size=0.045, rot=(math.pi / 2, 0, -math.pi / 2))
    kit.text("Control title", "CAGE", mat("yellow paint"), (X1 - 0.152, 1.95, 1.43), size=0.05, rot=(math.pi / 2, 0, -math.pi / 2))
    pull = reb.prim("sphere", "Bell pull top", iron, (X1 - 0.2, 1.45, H - 0.02), (0.03, 0.03, 0.03))
    kit.rod("Bell cord", reb.mat_plain("Cord", (0.3, 0.25, 0.15), 0.9), (0, 0, 0), (0, 0, -1.0), 0.008, 4).parent = pull
    reb.prim("cyl", "Bell handle", reb.mat_wood("Handle", (0.25, 0.17, 0.09)), (0, 0, -1.05), (0.04, 0.04, 0.14), segments=8).parent = pull
    reb.prim("cube", "Capacity sign", mat("white paint"), (X0 - 0.01, 1.8, 1.55), (0.01, 0.5, 0.22))
    kit.text("Capacity words", "MAX 6 MEN", mat("black"), (X0, 1.8, 1.55), size=0.07, rot=(math.pi / 2, 0, math.pi / 2))
    bell_glow = reb.mat_emit("Cage bulb", (1.0, 0.75, 0.45), 8)
    reb.prim("sphere", "Cage bulb", bell_glow, ((X0 + X1) / 2 - 0.3, (Y0 + Y1) / 2, H - 0.08), (0.08, 0.08, 0.1), segments=10)
    for a in (0, 2.1, 4.2):
        kit.rod("Bulb cage", iron, ((X0 + X1) / 2 - 0.3 + math.cos(a) * 0.07, (Y0 + Y1) / 2 + math.sin(a) * 0.07, H - 0.01), ((X0 + X1) / 2 - 0.3 + math.cos(a) * 0.07, (Y0 + Y1) / 2 + math.sin(a) * 0.07, H - 0.15), 0.005, 3)
    bulb = reb.point("Cage bulb light", ((X0 + X1) / 2 - 0.3, (Y0 + Y1) / 2, H - 0.18), 22, (1.0, 0.72, 0.42), 0.04)

    # ---- The dead lamp on the floor, its smear, the webs, grit.
    reb.prim("cyl", "Cap lamp", mat("steel"), (1.35, 1.35, 0.05), (0.09, 0.09, 0.07), rot=(math.pi / 2, 0, 0.6), segments=12)
    reb.prim("cyl", "Cap lamp lens", reb.mat_glass("Dead lens", (0.3, 0.3, 0.28)), (1.38, 1.31, 0.05), (0.08, 0.08, 0.01), rot=(math.pi / 2, 0, 0.6), segments=12)
    reb.prim("cube", "Battery pack", mat("black"), (1.75, 1.3, 0.07), (0.18, 0.08, 0.13), rot=(0, 0, 0.3), bevel=0.01)
    kit.rod("Lamp lead", mat("black"), (1.4, 1.37, 0.04), (1.66, 1.3, 0.05), 0.006, 4)
    kit.rod("Snapped strap", reb.mat_plain("Strap", (0.12, 0.08, 0.05), 0.8), (1.8, 1.35, 0.01), (2.2, 1.6, 0.01), 0.012, 4)
    kit.drag_trail("Old smear", mat("old blood"), [(1.25, 1.2), (1.6, 1.5), (2.0, 1.75), (2.4, 2.25)], width=0.35, seed=3)
    for c, f in (((X0 + 0.02, Y0 + 0.02, H - 0.02), (1, 1)), ((X1 - 0.02, Y0 + 0.02, H - 0.02), (-1, 1)), ((X0 + 0.02, Y1 - 0.02, H - 0.02), (1, -1))):
        kit.web("Cage web", c, 0.4, f)
    kit.web("Web low by the lamp", (X0 + 0.02, Y0 + 0.02, 0.45), 0.35, (1, 1))
    gv, gf = [], []
    for _ in range(60):
        x, y = rng.uniform(X0, X1), rng.uniform(Y0, Y1)
        s = rng.uniform(0.015, 0.05)
        reb.box(gv, gf, (x, y, s * 0.3), (s, s, s * 0.6), rng.uniform(0, 3))
    reb.mesh_object("Grit", gv, gf, mat("rock"), smooth=False)

    # ---- The shaft round the cage: rock close on three sides, the guides, the counterweight cable running past.
    rock_face("Shaft west", rock, (X0 - 0.45, Y0 - 2.6, -3.0), (0, Y1 - Y0 + 3.8, 0), (0, 0, 16.0), 14, 40, (-1, 0, 0), seed=1)
    rock_face("Shaft east", rock, (X1 + 0.55, Y0 - 2.6, -3.0), (0, Y1 - Y0 + 3.8, 0), (0, 0, 16.0), 14, 40, (1, 0, 0), seed=2)
    rock_face("Shaft back", rock, (X0 - 0.8, Y0 - 2.3, -3.0), (X1 - X0 + 1.8, 0, 0), (0, 0, 16.0), 10, 40, (0, -1, 0), seed=3)
    # The landing behind the north gate: the timbered stage the cage opens onto at the top, here bare rock and a ladder.
    reb.prim("cube", "Shaft landing", plate, ((X0 + X1) / 2, Y0 - 1.2, -0.06), (X1 - X0 + 0.9, 2.2, 0.1))
    for x in (X0 + 0.2, X0 + 0.65):
        kit.rod("Ladder rail", kit.dirtied(reb.mat_wood("Ladder", (0.14, 0.095, 0.055)), 0.7), (x, Y0 - 2.2, -0.05), (x, Y0 - 2.2, 6.0), 0.03, 6)
    kit.join("Ladder rungs", [kit.rod("Rung", iron, (X0 + 0.2, Y0 - 2.18, z), (X0 + 0.65, Y0 - 2.18, z), 0.015, 4) for z in [0.3 * k for k in range(1, 20)]])
    for x in (X0 - 0.2, X1 + 0.2):
        for y in (Y0 - 0.25, Y1 + 0.25):
            kit.rod("Shaft guide", kit.dirtied(reb.mat_wood("Guide", (0.14, 0.095, 0.055)), 0.7), (x, y, -3.0), (x, y, 13.0), 0.07, 6)
    run = kit.rod("Counterweight cable", cable_m, (X1 + 0.32, Y0 + 0.3, -3.0), (X1 + 0.32, Y0 + 0.3, 13.0), 0.025, 8)
    reb.prim("cube", "Shaft top dark", mat("black"), ((X0 + X1) / 2, (Y0 + Y1) / 2 - 1.0, 12.5), (4.0, 6.0, 0.2))
    reb.prim("cube", "Shaft sump dark", mat("black"), ((X0 + X1) / 2, (Y0 + Y1) / 2 - 1.0, -2.5), (4.0, 6.0, 0.2))
    # South, past the gate: the junction's floor and its lamps.
    reb.prim("cube", "Junction floor", reb.mat_surface("Chamber floor", [(0.0, (0.03, 0.026, 0.022)), (0.5, (0.075, 0.065, 0.052)), (1.0, (0.12, 0.1, 0.08))], scale=1.6, rough=0.55, bump=0.7), ((X0 + X1) / 2, Y1 + 4.0, -0.04), (10.0, 7.6, 0.08))
    for x in (X0 - 0.4, X1 + 0.4):
        kit.rod("Collar post", kit.dirtied(reb.mat_wood("Mine timber", (0.14, 0.095, 0.055)), 0.7), (x, Y1 + 0.35, 0), (x, Y1 + 0.35, 2.5), 0.12, 6)
    reb.prim("cube", "Collar beam", kit.dirtied(reb.mat_wood("Mine timber", (0.14, 0.095, 0.055)), 0.7), ((X0 + X1) / 2, Y1 + 0.35, 2.43), (X1 - X0 + 1.2, 0.25, 0.22))
    reb.prim("cube", "Junction roof", rock, ((X0 + X1) / 2, Y1 + 4.0, 4.0), (10.0, 7.6, 0.3))
    reb.prim("cube", "Junction far wall", rock, ((X0 + X1) / 2, Y1 + 7.6, 2.0), (10.0, 0.3, 4.0))
    reb.prim("cyl", "Pump motor far", kit.dirtied(mat("green paint"), 0.6), (X1 + 3.8, Y1 + 3.0, 0.95), (1.1, 1.1, 1.4), rot=(math.pi / 2, 0, 0), segments=16)
    kit.drum("Drum far", rust, (X0 - 1.5, Y1 + 2.4, 0.0))
    for k, (x, y) in enumerate(((X0 + 0.5, Y1 + 2.6), (X1 + 2.5, Y1 + 4.0))):
        glow = reb.mat_emit(f"Junction lamp {k}", (1.0, 0.72, 0.4), 14)
        reb.prim("sphere", f"Junction bulb {k}", glow, (x, y, 3.0), (0.08, 0.08, 0.11), segments=10)
        kit.rod(f"Junction flex {k}", mat("black"), (x, y, 3.05), (x, y, 3.9), 0.007, 4)
        reb.point(f"Junction lamp light {k}", (x, y, 2.9), 24, (1.0, 0.68, 0.38), 0.05)
    # Underground: no sky. The cage bulb, a cold glimmer down the shaft, the junction's lamps.
    reb.point("Shaft fill", ((X0 + X1) / 2, Y0 - 1.0, 2.6), 10, (0.55, 0.6, 0.7), 0.8)

    anim = kit.Anim(16)
    mp = cable_m.node_tree.nodes["Run"]
    def run_cable(k):
        mp.inputs["Location"].default_value = (0, 0, 0.4 * k / anim.frames)
    anim.custom(run_cable)
    anim.flicker(bulb, bell_glow, depth=0.35, dropouts=2)
    anim.swing(pull, axis=1, degrees=4)

    # ---- What the game needs.
    room.door("junction", (X0 + 0.1, Y1 - 0.45, X1 - 0.1, Y1), arrive=(1.95, 1.65), face=(0, -1))
    room.door("summit-trail", (X0 + 0.1, Y0, X1 - 0.1, Y0 + 0.45), arrive=(1.95, 1.9), face=(0, 1))
    room.spot("lift-up", (X1 - 0.6, 1.47, X1, 2.08))  # day/events.ts says what she sees and does here
    room.check((X0 + 0.4, 1.47, X1 - 0.6, 2.08), "A miner's cap lamp, dead. The strap's snapped.\nThere's an old smear of blood across the plates.")
    room.check((X0, 1.47, X0 + 0.4, 2.08), "MAX 6 MEN.")
    room.entry = "The cage creaks under me."
    room.export(anim)


build()
