"""The gondola's lower station yard, dusk: ARKLAY SKYWAY, the bottom of the line.

What it tells: a burgundy sedan sits alone in the car park with its
driver's door open and its dome light still on. Its owner was bitten here
last night: there is blood on the driver's seat and on the gravel, her
other shoe lies by the wheel, and her drops lead across the yard to the
station door. The keeper bandaged her and sent her up in car 4. The dogs
were here too: their tracks circle the car, a torn leash lies by the trail
head, and the ticket booth's window is smashed in. The gardener's handcart
of estate supplies stands where he left it. The flag still flies, the
drinks machine still hums against the station wall, and the cable comes
down out of the dusk into the dark wheel house.

Metres: the floor is x 1-13.5, y 1-15. The station building is east of the
floor, x 13.6-20, y 1-10.5; its door is in its west face at y 5.0-6.0, the
office windows either side of it at y 3.7-4.7 (broken) and 6.3-7.1. The cables come down from
the north into the wheel house at the station's north end. The car park is
the south-west, the sedan at x 3.5-8.1, y 11.0-12.9. The flagpole stands at
x 9.6, y 2.4; the ticket booth at x 9.6-11.2, y 8.3-9.7. The lane to the
valley path leaves west at y 7.4-10.1.

The station lane: the way west to the valley path is part of the room now.
A gravel lane runs about 5.9 m from the yard's west edge, 2.3-2.8 m wide
between post-and-rail fences, jinking south a little halfway. Alders lean
over it from both sides, still dripping from the afternoon's rain, and the
puddles in the ruts ring where the drops land. Halfway along, on the
north fence's corner post, someone has set a child's shoe, small and red,
where whoever comes looking will see it, and hung a storm lantern under
it, still burning. Past it the south fence is
broken through, rails down, where the dogs went. The lane's west end is
the way on to the valley path.

Metres: the scene is built in its own coordinates and shifted x +5.5 at
export. The floor is x -4.85-13.5, y 1-15; west of x 1 only the lane is
floor: y 7.4-10.1 to x -2.2, y 8.0-10.25 to x -2.8, y 8.0-10.75 to the end.

Moving: the flag flying, the drinks machine's light stuttering, the yard
lamp buzzing, moths round it, the sedan's dome light, mist, the lantern
on the lane, the alders' leaves stirring, drops falling from them and rings spreading in the
lane's puddles.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
from kit import mat  # noqa: E402
from mathutils import Matrix, Vector, noise  # noqa: E402
import bpy  # noqa: E402

X0, Y0, X1, Y1 = 1.0, 1.0, 13.5, 15.0
STATION = (13.6, 20.0, 1.0, 10.5)
DOOR = (5.0, 6.0)
SEDAN = (5.8, 11.95, 0.35)   # centre x, y and heading (radians about z, nose toward +x)
FLAG = (9.6, 2.4)
BOOTH = (9.6, 11.2, 8.3, 9.7)
CAMS = [(1.1, 1.2, 3.6), (0.4, 16.1, 3.5), (12.9, 1.0, 3.6), (13.0, 15.2, 3.3)]
SHIFT = (5.5, 0.0)
X_W = -4.85   # the floor's west end, the lane's far end (0.65 m in the game)
# The station lane west of the yard: walkable strips (x0, x1, y0, y1), east to west.
LANE = ((-2.2, X0, 7.4, 10.1), (-2.8, -2.2, 8.0, 10.25), (X_W, -2.8, 8.0, 10.75))
LANE_CAMS = [(-5.4, 9.5, 2.9), (2.9, 9.0, 3.2)]
FENCE_N = [(1.2, 7.2), (-2.2, 7.2), (-2.8, 7.8), (-9.0, 7.85)]
FENCE_S = [(1.2, 10.3), (-2.2, 10.3), (-2.8, 10.95), (-9.0, 11.0)]


def lane_y(x):
    """The lane's middle at x, west of the yard; past its end the trail bends south-west into the trees."""
    if x > -2.2:
        return 8.75
    if x > -2.8:
        return 8.75 + (-2.2 - x) / 0.6 * 0.65
    return 9.4 + max(0.0, -7.0 - x) * 0.35


def height(x, y):
    n = noise.noise(Vector((x * 0.07, y * 0.07, 6.0)))
    if X0 - 0.5 < x < 21 and Y0 - 0.5 < y < Y1 + 0.5:
        return 0.02 * n - 0.03
    rough = 0.8 * n + 0.03 * max(0.0, X0 - x)
    # The lane flat between its fences, the ground rolling away beyond them.
    d = abs(y - lane_y(x)) - 1.9
    if x < X0 and d < 2.5:
        t = max(0.0, d) / 2.5
        t = t * t * (3 - 2 * t)
        return (0.02 * n - 0.03) * (1 - t) + rough * t
    return rough


def tube(verts, faces, a, b, r0, r1, sides=6):
    """A tapering tube from a to b, into the given lists."""
    a, b = Vector(a), Vector(b)
    q = (b - a).to_track_quat("Z", "Y")
    k = len(verts)
    for end, r in ((a, r0), (b, r1)):
        for s in range(sides):
            t = 2 * math.pi * s / sides
            verts.append(tuple(end + q @ Vector((math.cos(t) * r, math.sin(t) * r, 0))))
    for s in range(sides):
        faces.append((k + s, k + (s + 1) % sides, k + sides + (s + 1) % sides, k + sides + s))


def alder(rng, base, h, bv, bf, lv, lf, lean=(0.0, 0.0)):
    """A wet alder: two or three stems leaning out of one root, a ragged crown of leaf cards."""
    base = Vector(base)
    up = Vector((0, 0, 1))
    for _ in range(rng.randint(2, 3)):
        d = Vector((lean[0] + rng.uniform(-0.2, 0.2), lean[1] + rng.uniform(-0.2, 0.2), 1.0)).normalized()
        a = base + Vector((rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), -0.1))
        top = a + d * h * rng.uniform(0.75, 1.0)
        tube(bv, bf, a, top, 0.012 * h, 0.03)
        for _ in range(4):
            t = rng.uniform(0.35, 0.8)
            p = a.lerp(top, t)
            ang = rng.uniform(0, 2 * math.pi)
            tube(bv, bf, p, p + Vector((math.cos(ang), math.sin(ang), 0.7)) * h * 0.22, 0.006 * h, 0.015, sides=4)
        for _ in range(int(h * 110)):
            t = rng.uniform(0.55, 1.0)
            c = a.lerp(top, t)
            r = h * 0.2 * math.sin(math.pi * (t - 0.5) / 0.55) * rng.uniform(0.25, 1.0)
            ang = rng.uniform(0, 2 * math.pi)
            out = Vector((math.cos(ang), math.sin(ang), rng.uniform(-0.3, 0.3))).normalized()
            reb.card(lv, lf, c + Vector((math.cos(ang) * r, math.sin(ang) * r, rng.uniform(-0.3, 0.3))), out, up, rng.uniform(0.12, 0.2), rng.uniform(0.16, 0.26), 0.7)


def fence(name, m, line, rng, post_every=1.9, broken=None):
    """Post-and-rail fence along `line` [(x, y)]: posts and two rails, one mesh.
    `broken` (x0, x1): the rails there down on the ground."""
    v, f = [], []
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        a, b = Vector((ax, ay, 0)), Vector((bx, by, 0))
        n = max(1, round((b - a).length / post_every))
        for i in range(n):
            p = a.lerp(b, i / n)
            tube(v, f, p + Vector((0, 0, -0.1)), p + Vector((rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03), 1.05)), 0.06, 0.05, sides=5)
        yaw = math.atan2(b.y - a.y, b.x - a.x)
        for i in range(n):
            p, q = a.lerp(b, i / n), a.lerp(b, (i + 1) / n)
            mid = (p + q) / 2
            if broken and broken[0] < mid.x < broken[1]:
                for z in (0.04, 0.09):
                    reb.box(v, f, (mid.x + rng.uniform(-0.2, 0.2), mid.y + rng.uniform(0.1, 0.5), z), ((q - p).length, 0.06, 0.08), yaw + rng.uniform(-0.4, 0.4))
                continue
            for z in (0.45, 0.9):
                reb.box(v, f, (mid.x, mid.y, z + rng.uniform(-0.03, 0.03)), ((q - p).length + 0.1, 0.05, 0.09), yaw + rng.uniform(-0.02, 0.02))
    return reb.mesh_object(name, v, f, m, smooth=False)


def struts(name, m, segs, r, sides=4):
    """Many square bars, one mesh."""
    verts, faces = [], []
    for a, b in segs:
        a, b = Vector(a), Vector(b)
        d = b - a
        if d.length < 1e-4:
            continue
        q = d.to_track_quat("Z", "Y")
        k = len(verts)
        for end in (a, b):
            for s in range(sides):
                t = 2 * math.pi * s / sides + math.pi / sides
                verts.append(tuple(end + q @ Vector((math.cos(t) * r, math.sin(t) * r, 0))))
        for s in range(sides):
            faces.append((k + s, k + (s + 1) % sides, k + sides + (s + 1) % sides, k + sides + s))
    return reb.mesh_object(name, verts, faces, m, smooth=False)


def sedan(paint, glass):
    """A late-80s four-door saloon, burgundy, its driver's door open and its dome light on.
    Built along +x about the origin, then placed. Returns (body, dome light, dome material)."""
    # One smooth shell: bonnet, raked windscreen, roof, rear screen, boot.
    sections = [(2.32, 0.8, 0.34, 0.72, 6), (2.2, 0.87, 0.28, 0.8, 10), (1.0, 0.88, 0.28, 0.86, 10), (0.85, 0.87, 0.28, 0.9, 10),
                (0.35, 0.8, 0.28, 1.36, 6), (-0.95, 0.8, 0.28, 1.38, 6), (-1.5, 0.85, 0.28, 0.96, 10), (-1.65, 0.86, 0.28, 0.9, 10),
                (-2.2, 0.87, 0.3, 0.88, 10), (-2.32, 0.8, 0.36, 0.8, 6)]

    def glazed(c):
        x, y, z = c
        if 0.38 < x < 0.85 and z > 0.95 and abs(y) < 0.78:
            return 1   # windscreen
        if -1.5 < x < -1.0 and z > 0.97 and abs(y) < 0.78:
            return 1   # rear screen
        return 1 if abs(y) > 0.6 and 0.98 < z < 1.3 and -1.35 < x < 0.32 else 0

    def cut(c):
        x, y, z = c
        arch = abs(y) > 0.5 and any(math.hypot(x - wx, z - 0.32) < 0.42 for wx in (1.45, -1.45))
        doorway = y > 0.5 and -0.3 < x < 0.75 and 0.36 < z < 1.32
        return arch or doorway

    shell = kit.loft("Sedan body", sections, [paint, glass, reb.mat_plain("Sedan inside", (0.04, 0.03, 0.03), 0.8)], ring=40, material_of=glazed, holes=cut, shell=0.03)
    parts = [shell]
    for x in (2.36, -2.36):
        parts.append(reb.prim("cube", "Sedan bumper", mat("black"), (x, 0, 0.42), (0.1, 1.78, 0.18), bevel=0.04))
    parts.append(reb.prim("cube", "Sedan grille", mat("black"), (2.33, 0, 0.6), (0.02, 0.7, 0.12)))
    parts.append(reb.prim("cube", "Sedan rubbing strip", mat("black"), (0, -0.885, 0.55), (4.2, 0.02, 0.05)))
    body = kit.join("Sedan", parts, origin=(0, 0, 0))
    inside = reb.prim("cube", "Sedan inside", reb.mat_plain("Sedan seats", (0.08, 0.06, 0.05), 0.8), (-0.25, 0, 0.95), (2.3, 1.45, 0.5))
    inside.parent = body
    kit.splat("Blood on the driver's seat", mat("blood"), (0.2, 0.4, 1.205), 0.18, seed=3).parent = body
    for x in (1.45, -1.45):
        for y in (0.78, -0.78):
            for w in kit.wheel("Sedan wheel", (x, y, 0.32), r=0.32, width=0.2):
                w.parent = body
    for y in (0.6, -0.6):
        hl = reb.prim("cube", "Headlight", reb.mat_plain("Headlight", (0.6, 0.6, 0.55), 0.2), (2.31, y, 0.62), (0.04, 0.32, 0.14), bevel=0.01)
        hl.parent = body
        tl = reb.prim("cube", "Tail light", reb.mat_plain("Tail light", (0.3, 0.02, 0.02), 0.3), (-2.31, y, 0.7), (0.04, 0.3, 0.12), bevel=0.01)
        tl.parent = body
    # The driver's door, swung open on the left side (+y).
    door = reb.prim("cube", "Driver's door", paint, (0.55, 0.0, 0.0), (1.1, 0.06, 0.95), bevel=0.03)
    dg = reb.prim("cube", "Driver's door glass", glass, (0, 0, 0), (0.95, 0.02, 0.35))
    dg.parent = door
    dg.location = (0.0, 0.0, 0.3)
    hinge = reb.prim("sphere", "Door hinge", mat("black"), (0.75, 0.88, 0.75), (0.03, 0.03, 0.03))
    hinge.parent = body
    door.parent = hinge
    door.location = (-0.55, 0.0, 0.0)
    hinge.rotation_euler = (0, 0, -1.05)
    dome_m = reb.mat_emit("Dome light", (1.0, 0.85, 0.55), 6)
    dome = reb.prim("cube", "Dome light", dome_m, (-0.1, 0, 1.31), (0.18, 0.1, 0.02))
    dome.parent = body
    sx, sy, hd = SEDAN
    body.location = (sx, sy, 0.0)
    body.rotation_euler = (0, 0, hd)
    bpy.context.view_layer.update()
    lamp = reb.point("Dome light glow", body.matrix_world @ Vector((-0.1, 0.0, 1.15)), 9, (1.0, 0.82, 0.5), 0.08)
    spill = reb.point("Dome light spill", body.matrix_world @ Vector((0.4, 1.3, 0.6)), 4, (1.0, 0.82, 0.5), 0.2)
    return body, lamp, spill, dome_m


def mist_card_mat(name, rgb, density, scale):
    """Mist on a card: noise thinned to nothing at the card's edges."""
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = 1.0
    out = nodes["Material Output"]
    tr = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    n = reb.noise_tex(nodes, links, scale, 4, 0.6)
    r = reb.ramp(nodes, links, n.outputs["Fac"], [(0.35, (0, 0, 0)), (0.75, (density,) * 3)])
    tc = nodes.new("ShaderNodeTexCoord")
    sub = nodes.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    links.new(tc.outputs["Generated"], sub.inputs[0])
    mul = nodes.new("ShaderNodeVectorMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = (2, 2, 0)
    links.new(sub.outputs[0], mul.inputs[0])
    ln = nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    links.new(mul.outputs[0], ln.inputs[0])
    edge = nodes.new("ShaderNodeMapRange")
    edge.inputs["From Min"].default_value = 1.0
    edge.inputs["From Max"].default_value = 0.3
    links.new(ln.outputs["Value"], edge.inputs["Value"])
    prod = nodes.new("ShaderNodeMath")
    prod.operation = "MULTIPLY"
    links.new(r.outputs["Color"], prod.inputs[0])
    links.new(edge.outputs["Result"], prod.inputs[1])
    links.new(prod.outputs[0], mix.inputs["Fac"])
    links.new(tr.outputs[0], mix.inputs[1])
    links.new(bsdf.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def build():
    rng = random.Random(1972)
    reb.clear_scene()
    room = kit.Room(bounds=(X_W, Y0, X1, Y1), shift=SHIFT)
    room.ground("gravel")
    room.floor((0.5, 9.9, 9.5, 15.0), "concrete")  # the car park's asphalt
    room.camera(CAMS[0], (10.5, 9.0, 0.6), 200, "from the north-west corner: the yard, the booth, the station door and the drinks machine, the sedan")
    room.camera(CAMS[1], (11.5, 5.0, 1.2), 200, "from the south-west, over the car park: the sedan's open door, the station front, the flag")
    room.camera(CAMS[2], (4.5, 11.5, 0.2), 200, "from the station's north corner: the car park and the sedan, the trail head west")
    room.camera(CAMS[3], (5.0, 4.5, 0.8), 200, "from the south-east: the booth, the flagpole, the trail into the trees")
    room.camera(LANE_CAMS[0], (3.0, 8.9, 0.7), 200, "up the station lane from its west end: the shoe on the post, the fences, the yard and the station beyond")
    room.camera(LANE_CAMS[1], (-5.5, 9.7, 0.6), 200, "down the station lane west from the yard: the alders dripping, the shoe on the post, the dusk at the end")

    asphalt = kit.dirtied(reb.mat_surface("Asphalt", [(0.0, (0.04, 0.04, 0.04)), (1.0, (0.09, 0.09, 0.085))], scale=20, rough=0.7, bump=0.4), 0.4, scale=0.5)
    gravel = kit.dirtied(mat("gravel"), 0.6, scale=0.4)
    station_wall = kit.dirtied(reb.mat_surface("Station render", [(0.0, (0.3, 0.29, 0.26)), (0.7, (0.42, 0.4, 0.36)), (1.0, (0.25, 0.2, 0.15))], scale=2, bump=0.2), 0.5)
    timber = kit.boards("Station boards", (0.2, 0.13, 0.08), width=0.18, grime=0.6)
    burgundy = reb.mat_surface("Burgundy paint", [(0.0, (0.16, 0.015, 0.03)), (0.8, (0.26, 0.03, 0.05)), (1.0, (0.2, 0.08, 0.06))], scale=3, rough=0.25, bump=0.05)
    glass = reb.mat_glass("Sedan glass", (0.35, 0.38, 0.4))
    green = mat("green paint")

    # ---- Ground: asphalt car park, a gravel yard, the verge.
    reb.terrain("Ground", mat("grass"), (-50, 70), (-50, 70), height, step=0.8)
    reb.prim("cube", "Yard gravel", gravel, (7.6, 7.0, -0.03), (14.0, 13.0, 0.06))
    # Loose stones on it, pale and dark, thickest along the edges and the
    # middle where wheels have not packed them down.
    pv, pf = [], []
    for _ in range(1400):
        x, y = rng.uniform(0.7, 13.4), rng.uniform(0.6, 9.6)
        sz = rng.uniform(0.03, 0.09) if rng.random() < 0.9 else rng.uniform(0.1, 0.18)
        reb.box(pv, pf, (x, y, sz * 0.25), (sz, sz * rng.uniform(0.6, 1.1), sz * 0.5), rng.uniform(0, 3))
    reb.mesh_object("Yard stones", pv, pf, reb.mat_surface("Yard stone", [(0.0, (0.1, 0.095, 0.085)), (0.5, (0.3, 0.28, 0.25)), (1.0, (0.45, 0.43, 0.39))], scale=6, bump=0.3), smooth=False)
    reb.prim("cube", "Car park", asphalt, (5.0, 12.6, -0.01), (9.0, 5.4, 0.06))
    for i in range(5):
        reb.prim("cube", "Bay line", mat("white paint"), (1.6 + i * 2.6, 13.4, 0.022), (0.08, 2.6, 0.004))
    kit.cracks("Cracks", mat("black"), (1.0, 10.2, 9.4, 15.0), count=10, seed=2, z=0.022)
    reb.prim("cube", "Kerb", mat("concrete"), (5.0, 9.85, 0.06), (9.0, 0.2, 0.14))
    kit.path_strip("Lane west", gravel, [(2.5, 8.75), (-2.0, 8.75), (-3.0, 9.4), (-7.0, 9.4)], height, width=1.15, wobble=0.12, lift=0.012)
    kit.path_strip("Trail on west", mat("dirt"), [(-6.6, 9.4)] + [(x, lane_y(x)) for x in (-8.0, -10.0, -13.0, -17.0, -24.0, -34.0)], height, width=0.6, lift=0.012)
    for i in range(4):
        kit.splat(f"Puddle {i}", reb.mat_plain("Puddle", (0.05, 0.045, 0.045), 0.15), (rng.uniform(2, 12), rng.uniform(2, 14), 0.0), rng.uniform(0.15, 0.3), seed=50 + i, stretch=(1.5, 0.7))

    # ---- The station: rendered walls, a timber upper storey, the boarding hall north, the wheel house.
    sx0, sx1, sy0, sy1 = STATION
    st = reb.prim("cube", "Station", station_wall, ((sx0 + sx1) / 2, (sy0 + sy1) / 2, 2.0), (sx1 - sx0, sy1 - sy0, 4.0))
    reb.wall(st)
    reb.prim("cube", "Station upper storey", timber, ((sx0 + sx1) / 2 + 0.3, (sy0 + sy1) / 2 + 1.0, 5.0), (sx1 - sx0 - 0.6, sy1 - sy0 - 2.0, 2.0))
    reb.prim("cube", "Station roof", mat("tin"), ((sx0 + sx1) / 2 + 0.3, (sy0 + sy1) / 2 + 1.0, 6.2), (sx1 - sx0 + 0.4, sy1 - sy0 - 1.0, 0.12), rot=(0, 0.12, 0))
    reb.prim("cube", "Wheel house", mat("tin"), ((sx0 + sx1) / 2 + 1.5, sy0 - 1.5, 3.5), (4.5, 3.0, 7.0))
    reb.prim("cube", "Wheel house mouth", mat("black"), ((sx0 + sx1) / 2 + 1.5, sy0 - 3.02, 4.6), (3.6, 0.02, 2.2))
    reb.prim("cube", "Station door", mat("black"), (sx0 - 0.01, (DOOR[0] + DOOR[1]) / 2, 1.05), (0.02, DOOR[1] - DOOR[0], 2.1))
    reb.prim("cube", "Door leaf, ajar", green, (sx0 - 0.42, DOOR[0] + 0.12, 1.05), (0.82, 0.05, 2.1), rot=(0, 0, -1.25))
    for y in (DOOR[0] - 0.06, DOOR[1] + 0.06):
        reb.prim("cube", "Door frame", mat("dark wood"), (sx0 - 0.03, y, 1.08), (0.08, 0.09, 2.16))
    reb.prim("cube", "Door step", mat("concrete"), (sx0 - 0.3, (DOOR[0] + DOOR[1]) / 2, 0.06), (0.6, 1.6, 0.12))
    office_glow = reb.mat_emit("Office glow", (0.7, 0.9, 0.8), 1.2)
    for i, (y0, y1) in enumerate(((3.7, 4.7), (6.3, 7.1))):
        reb.prim("cube", f"Office window {i}", reb.mat_glass("Station glass", (0.4, 0.45, 0.45)) if i else mat("black"), (sx0 - 0.02, (y0 + y1) / 2, 1.6), (0.02, y1 - y0, 1.0))
        reb.prim("cube", f"Office inside {i}", office_glow, (sx0 + 0.6, (y0 + y1) / 2, 1.5), (0.02, y1 - y0, 1.4))
        reb.prim("cube", f"Window sill {i}", mat("concrete"), (sx0 - 0.08, (y0 + y1) / 2, 1.05), (0.16, y1 - y0 + 0.1, 0.06))
    # The north window broken: its jagged rim, glass on the ground.
    for i in range(7):
        a = rng.uniform(0, 2 * math.pi)
        kit.rod("Jagged glass", reb.mat_glass("Station glass", (0.4, 0.45, 0.45)), (sx0 - 0.02, 4.2 + math.cos(a) * 0.5, 1.6 + math.sin(a) * 0.5), (sx0 - 0.02, 4.2 + math.cos(a) * 0.28, 1.6 + math.sin(a) * 0.25), 0.01, 3)
    kit.shards("Glass under the window", (sx0 - 0.5, 4.2, 0.0), spread=0.8, count=20, seed=3)
    office_light = reb.point("Office light", (sx0 + 1.2, 5.5, 2.2), 30, (0.75, 0.95, 0.85), 0.2)
    reb.prim("cube", "Station sign", reb.mat_plain("Sign green", (0.06, 0.16, 0.1), 0.6), (sx0 - 0.06, 5.5, 3.3), (0.06, 4.4, 0.75))
    kit.text("Station sign words", "ARKLAY SKYWAY", mat("white paint"), (sx0 - 0.1, 5.5, 3.42), size=0.36, rot=(math.pi / 2, 0, -math.pi / 2))
    kit.text("Station sign words 2", "LOWER STATION", mat("white paint"), (sx0 - 0.1, 5.5, 3.08), size=0.2, rot=(math.pi / 2, 0, -math.pi / 2))
    reb.prim("cube", "Timetable board", mat("dark wood"), (sx0 - 0.04, 7.0 + 2.2, 1.5), (0.04, 0.8, 1.0))
    reb.prim("cube", "Timetable", mat("paper"), (sx0 - 0.065, 9.2, 1.5), (0.004, 0.65, 0.85))
    kit.text("Timetable words", "LAST CAR 18:00", mat("black"), (sx0 - 0.07, 9.2, 1.78), size=0.06, rot=(math.pi / 2, 0, -math.pi / 2))
    kit.splat("Handprint on the door frame", mat("blood"), (sx0 - 0.075, DOOR[1] + 0.1, 1.2), 0.07, rot=(0, math.pi / 2, 0), seed=7)
    # The drinks machine, against the wall, humming.
    vm = kit.box("Drinks machine", mat("red paint"), (sx0 - 0.45, 8.45, 0.0), (0.8, 0.9, 1.9), bevel=0.02)
    reb.mask(reb.wall(vm))
    vm_m = reb.mat_emit("Drinks machine front", (1.0, 0.92, 0.85), 3.5)
    reb.prim("cube", "Drinks machine panel", vm_m, (sx0 - 0.855, 8.3, 1.2), (0.01, 0.5, 0.95))
    kit.text("Drinks words", "ICE COLD", mat("red paint"), (sx0 - 0.865, 8.3, 1.5), size=0.11, rot=(math.pi / 2, 0, -math.pi / 2))
    reb.prim("cube", "Coin slot", mat("steel"), (sx0 - 0.86, 8.72, 1.1), (0.01, 0.12, 0.3))
    vm_light = reb.point("Drinks machine glow", (sx0 - 1.3, 8.35, 1.1), 12, (1.0, 0.9, 0.8), 0.3)
    kit.bottles("Cans by the machine", (sx0 - 1.0, 9.0, 0.0), count=3, spread=0.4, seed=4, tipped=1.0)
    # Cables down out of the north into the wheel house.
    for cx in (sx0 + 1.2, sx0 + 3.8):
        kit.rod("Haul cable", mat("iron"), (cx, sy0 - 3.0, 4.6), (cx, -160.0, 40.0), 0.03, 6)
    reb.prim("cyl", "Bullwheel in the dark", mat("rust"), ((sx0 + sx1) / 2 + 1.5, sy0 - 2.0, 4.6), (3.0, 3.0, 0.15), rot=(math.pi / 2, 0, 0), segments=32)
    # A parked car of the line, in the boarding hall's mouth.
    reb.prim("cube", "Spare gondola car", reb.mat_surface("Car paint", [(0.0, (0.22, 0.03, 0.02)), (1.0, (0.35, 0.05, 0.03))], scale=4, rough=0.45, bump=0.1), (sx0 + 1.6, sy0 - 3.8, 3.0), (2.6, 1.6, 2.0), bevel=0.2)

    # ---- The sedan, its door open, dome light on; her shoe; her blood to the station.
    body, dome_light, dome_spill, dome_m = sedan(burgundy, glass)
    reb.mask(body)
    reb.wall(reb.prim("cube", "Sedan footprint", None, (SEDAN[0], SEDAN[1], 0.5), (4.6, 1.75, 1.0), rot=(0, 0, SEDAN[2]))).hide_render = True
    hd = SEDAN[2]
    dxy = Vector((math.cos(hd), math.sin(hd)))
    left = Vector((-math.sin(hd), math.cos(hd)))
    door_at = Vector(SEDAN[:2]) + dxy * 0.4 + left * 1.4
    kit.splat("Blood by the driver's door", mat("blood"), (door_at.x, door_at.y, 0.0), 0.4, seed=12, stretch=(1.3, 1.0))
    reb.prim("cube", "Her other shoe", reb.mat_plain("Shoe", (0.04, 0.03, 0.03), 0.3), (door_at.x - 0.9, door_at.y + 0.2, 0.04), (0.24, 0.08, 0.06), rot=(0, 0, 2.2), bevel=0.02)
    kit.rod("Shoe heel", reb.mat_plain("Shoe", (0.04, 0.03, 0.03), 0.3), (door_at.x - 1.0, door_at.y + 0.25, 0.0), (door_at.x - 1.0, door_at.y + 0.25, 0.08), 0.008, 5)
    pts = [(door_at.x, door_at.y - 0.4), (7.5, 9.8), (10.0, 7.5), (12.0, 6.2), (sx0 - 0.4, 5.6)]
    k = 0
    for a, b in zip(pts, pts[1:]):
        n = int((Vector(b) - Vector(a)).length / 0.45)
        for i in range(n):
            t = i / n
            x = a[0] + (b[0] - a[0]) * t + rng.uniform(-0.1, 0.1)
            y = a[1] + (b[1] - a[1]) * t + rng.uniform(-0.1, 0.1)
            kit.splat(f"Drop {k}", mat("blood"), (x, y, 0.0), rng.uniform(0.03, 0.07), seed=100 + k, lumps=0.4)
            k += 1
    # The dogs' tracks round the car; the torn leash by the trail.
    pv, pf = [], []
    for i in range(46):
        a = 2 * math.pi * i / 46 * 1.6
        r = 3.0 + 0.6 * math.sin(i * 0.7)
        c = Vector(SEDAN[:2]) + Vector((math.cos(a) * r * 1.2, math.sin(a) * r * 0.75))
        if not (X0 < c.x < X1 and Y0 < c.y < Y1):
            continue
        for dx, dy, rr in ((0, 0, 0.045), (0.06, 0.04, 0.017), (0.07, 0.0, 0.017), (0.06, -0.04, 0.017)):
            kk = len(pv)
            pv.append((c.x + dx, c.y + dy, 0.03))
            for j in range(6):
                b = 2 * math.pi * j / 6
                pv.append((c.x + dx + math.cos(b) * rr, c.y + dy + math.sin(b) * rr, 0.03))
            pf.extend((kk, kk + 1 + j, kk + 1 + (j + 1) % 6) for j in range(6))
    reb.mesh_object("Dog tracks", pv, pf, reb.mat_plain("Paw prints", (0.03, 0.02, 0.012), 0.7), smooth=False)
    for i in range(10):
        kit.rod(f"Torn leash {i}", reb.mat_plain("Leash", (0.25, 0.05, 0.03), 0.6), (2.0 + i * 0.12, 6.9 + 0.08 * math.sin(i), 0.01), (2.12 + i * 0.12, 6.9 + 0.08 * math.sin(i + 1), 0.01), 0.012, 4)
    reb.prim("cube", "Leash clip", mat("steel"), (3.3, 6.95, 0.015), (0.06, 0.03, 0.02))

    # ---- The ticket booth, its window smashed in.
    bx0, bx1, by0, by1 = BOOTH
    for ob in kit.walls(bx0 + 0.06, by0 + 0.06, bx1 - 0.06, by1 - 0.06, 2.3, timber, openings=[("w", by0 + 0.25, by1 - 0.25, 1.0, 1.7)], thick=0.06, name="Booth wall"):
        reb.wall(ob)
    reb.wall(reb.prim("cube", "Booth inside", reb.mat_plain("Booth dark", (0.03, 0.025, 0.02), 0.9), ((bx0 + bx1) / 2, (by0 + by1) / 2, 1.1), (bx1 - bx0 - 0.25, by1 - by0 - 0.25, 2.2)))
    reb.prim("cube", "Booth roof", mat("tin"), ((bx0 + bx1) / 2, (by0 + by1) / 2, 2.4), (bx1 - bx0 + 0.5, by1 - by0 + 0.5, 0.08), rot=(0, 0.1, 0))
    reb.prim("cube", "Booth counter", mat("dark wood"), (bx0 - 0.08, (by0 + by1) / 2, 0.98), (0.25, by1 - by0 - 0.4, 0.05))
    reb.prim("cube", "TICKETS board", mat("white paint"), (bx0 - 0.02, (by0 + by1) / 2, 2.0), (0.03, 1.2, 0.26))
    kit.text("TICKETS", "TICKETS", mat("red paint"), (bx0 - 0.04, (by0 + by1) / 2, 2.0), size=0.15, rot=(math.pi / 2, 0, -math.pi / 2))
    kit.shards("Booth glass", (bx0 - 0.5, (by0 + by1) / 2, 0.0), spread=0.6, count=16, seed=9)
    kit.splat("Smear on the counter", mat("old blood"), (bx0 - 0.08, (by0 + by1) / 2 + 0.2, 1.007), 0.1, seed=10, stretch=(0.6, 1.8))
    kit.scratches("Claw marks on the booth", mat("black"), (bx0 - 0.01, by0 + 0.2, 0.75), (-1, 0), count=4, length=0.4, seed=5)
    booth_m = reb.mat_emit("Booth lamp", (1.0, 0.75, 0.45), 2)
    reb.prim("sphere", "Booth lamp", booth_m, ((bx0 + bx1) / 2, (by0 + by1) / 2, 2.0), (0.12, 0.12, 0.12), segments=10)
    booth_light = reb.point("Booth lamp light", ((bx0 + bx1) / 2 - 0.3, (by0 + by1) / 2, 1.9), 5, (1.0, 0.75, 0.45), 0.05)
    papers = kit.papers("Tickets blown about", (bx0 - 1.2, (by0 + by1) / 2 + 0.6, 0.0), spread=1.2, count=8, seed=11, m=mat("yellow paint"))
    # The gardener's handcart, left by the booth.
    reb.wall(reb.prim("cube", "Handcart bed", mat("planks"), (8.4, 6.4, 0.55), (1.3, 0.75, 0.25), rot=(0, 0.1, 0.3)))
    for dy in (-0.4, 0.4):
        reb.prim("cyl", "Handcart wheel", mat("rubber"), (8.85 + dy * 0.3, 6.4 + dy, 0.3), (0.6, 0.6, 0.07), rot=(math.pi / 2, 0, 0.3), segments=16)
    kit.rod("Handcart handle", mat("dark wood"), (7.8, 6.2, 0.6), (7.2, 6.0, 1.0), 0.025)
    for i, (x, y, z) in enumerate(((8.3, 6.3, 0.8), (8.7, 6.5, 0.8), (8.5, 6.4, 1.0))):
        reb.prim("cube", f"Sack {i}", mat("canvas"), (x, y, z), (0.5, 0.35, 0.22), rot=(0, 0, 0.3 + i * 0.2), bevel=0.08)
    kit.text("Sack stencil", "SPENCER EST.", mat("black"), (8.32, 6.12, 0.82), size=0.06, rot=(math.pi / 2, 0, 0.3))

    # ---- The flag on its pole.
    fx, fy = FLAG
    reb.wall(kit.rod("Flagpole", mat("steel"), (fx, fy, 0), (fx, fy, 8.0), 0.05), "circle")
    reb.prim("sphere", "Flagpole ball", mat("yellow paint"), (fx, fy, 8.05), (0.12, 0.12, 0.12), segments=10)
    reb.prim("cube", "Flagpole base", mat("concrete"), (fx, fy, 0.1), (0.6, 0.6, 0.2))
    kit.rod("Halyard", mat("white paint"), (fx + 0.06, fy, 0.9), (fx + 0.06, fy, 7.9), 0.004, 3)
    fv, ff = [], []
    cols, rows = 14, 8
    fw, fh = 1.6, 1.0
    for j in range(rows + 1):
        for i in range(cols + 1):
            fv.append((i / cols * fw, 0.0, -j / rows * fh))
    for j in range(rows):
        for i in range(cols):
            a = j * (cols + 1) + i
            ff.append((a, a + 1, a + cols + 2, a + cols + 1))
    flag_m = reb.mat_stripes("Flag", [(0.35, 0.03, 0.03), (0.55, 0.55, 0.52)], across=13, axis="Z")
    flag = reb.mesh_object("Flag", fv, ff, flag_m, smooth=True)
    flag.location = (fx + 0.06, fy, 7.85)
    flag.rotation_euler = (0, 0, 0.5)
    flag_rest = [Vector(v.co) for v in flag.data.vertices]

    # ---- The yard lamp, sodium orange, buzzing; the forest round the yard.
    reb.wall(kit.rod("Lamp post", mat("iron"), (6.6, 5.4, 0), (6.6, 5.4, 5.5), 0.07), "circle")
    kit.rod("Lamp arm", mat("iron"), (6.6, 5.4, 5.4), (7.4, 5.4, 5.6), 0.04)
    sodium_m = reb.mat_emit("Sodium", (1.0, 0.55, 0.15), 25)
    reb.prim("cube", "Lamp head", mat("iron"), (7.5, 5.4, 5.6), (0.55, 0.25, 0.12))
    reb.prim("cube", "Lamp glass", sodium_m, (7.5, 5.4, 5.53), (0.45, 0.2, 0.02))
    yard_lamp = reb.spot("Yard lamp", (7.5, 5.4, 5.5), (7.0, 7.5, 0.0), 1300, (1.0, 0.55, 0.18), 120, 0.6, 0.15)

    def keep_out(x, y):
        if X0 - 1.0 < x < 22 and Y0 - 1.0 < y < Y1 + 1.0:
            return True
        if x < 1 and abs(y - lane_y(x)) < (4.2 if x > -8.0 else 1.3):
            return True
        if any((Vector((x, y)) - Vector(c[:2])).length < 5.0 for c in CAMS + LANE_CAMS):
            return True
        return sx0 - 2 < x < sx1 + 4 and sy0 - 8 < y < sy1 + 2
    kit.forest(rng, height, keep_out, (-26, -24, 36, 36), count=110, spacing=1.9, tall=(13, 21), ferns=20, needles=600)
    # The woods closing round the trail west, past the lane's end.
    kit.forest(rng, height, keep_out, (-40, 0, -11, 20), count=60, spacing=1.9, tall=(13, 21), ferns=10, needles=200)
    grass = kit.meadow(rng, 700, lambda r: (r.uniform(-3, X1), r.uniform(-3, Y1 + 3)) if r.random() < 0.6 else (r.uniform(X0, X1), r.choice((r.uniform(Y0, Y0 + 0.6), r.uniform(Y1 - 0.6, Y1)))), height, mat("dead grass"))
    # ---- The station lane west: fences, alders dripping, puddles, the child's shoe on the gate post.
    lane_wood = kit.dirtied(reb.mat_wood("Fence wood", (0.14, 0.11, 0.08)), 0.7, scale=2)
    fence("North fence", lane_wood, FENCE_N, rng)
    fence("South fence", lane_wood, FENCE_S, rng, broken=(-5.2, -3.0))
    gx, gy = FENCE_N[1]
    kit.rod("Gate post", lane_wood, (gx, gy, -0.1), (gx, gy, 1.3), 0.085, 6)
    reb.prim("cube", "Gate post cap", lane_wood, (gx, gy, 1.31), (0.2, 0.2, 0.03))
    red_shoe = reb.mat_surface("Child's shoe", [(0.0, (0.45, 0.03, 0.03)), (0.8, (0.65, 0.06, 0.04)), (1.0, (0.3, 0.1, 0.06))], scale=12, rough=0.45, bump=0.2)
    shoe = kit.join("Child's shoe", [
        reb.prim("cube", "sole", reb.mat_plain("Sole", (0.5, 0.48, 0.44), 0.7), (0, 0, 0.012), (0.17, 0.065, 0.024), bevel=0.012),
        reb.prim("cube", "upper", red_shoe, (-0.012, 0, 0.045), (0.14, 0.06, 0.05), bevel=0.02),
        reb.prim("cube", "strap", mat("white paint"), (0.02, 0, 0.07), (0.025, 0.065, 0.012)),
    ], origin=(0, 0, 0))
    shoe.location = (gx, gy, 1.325)
    shoe.rotation_euler = (0, 0, 2.6)
    _, lane_lamp, lane_flame = kit.lantern("Lantern on the gate post", (gx + 0.1, gy + 0.13, 0.82), energy=20, hanging=True)
    # Its glow on the lane and up the post: the globe's glass would shade the light inside it.
    lane_spill = reb.point("Lantern spill", (gx + 0.35, gy + 0.45, 1.05), 45, (1.0, 0.62, 0.28), 0.12)
    kit.bottles("Can in the verge", (-3.6, 7.95, height(-3.6, 7.95)), count=1, spread=0.1, seed=31, tipped=1.0)
    puddle_m = reb.mat_plain("Lane puddle", (0.035, 0.035, 0.04), 0.05)
    puddles = [(-0.4, 8.4), (-1.9, 9.2), (-3.9, 9.85), (0.6, 9.4)]
    for i, (x, y) in enumerate(puddles):
        kit.splat(f"Lane puddle {i}", puddle_m, (x, y, height(x, y) + 0.015), rng.uniform(0.25, 0.4), seed=70 + i, stretch=(1.6, 0.8), lumps=0.2)
    av, af, lv, lf = [], [], [], []
    drips = []
    for x, y, h, lean in ((0.6, 4.6, 7.5, (-0.1, 0.15)), (-2.6, 5.9, 8.5, (0.0, 0.2)), (-5.6, 5.5, 8.0, (0.1, 0.2)), (-9.2, 6.4, 7.5, (0.0, 0.15)),
                          (-1.4, 13.0, 8.0, (0.0, -0.2)), (-4.4, 13.3, 8.5, (0.1, -0.2)), (-9.4, 12.6, 8.0, (0.0, -0.15))):
        alder(rng, (x, y, height(x, y)), h, av, af, lv, lf, lean)
    reb.mesh_object("Alder stems", av, af, reb.mat_surface("Alder bark", [(0.0, (0.08, 0.08, 0.07)), (0.7, (0.18, 0.17, 0.15)), (1.0, (0.1, 0.12, 0.06))], scale=8, bump=0.6), smooth=False)
    alder_leaves = reb.mesh_object("Alder leaves", lv, lf, reb.mat_cards("Alder leaves", (0.035, 0.06, 0.02), (0.12, 0.17, 0.05)))
    drop_m = reb.mat_plain("Drop", (0.55, 0.6, 0.62), 0.05)
    ring_m = reb.mat_plain("Ring", (0.3, 0.32, 0.34), 0.1)
    rings = []
    for i, (x, y) in enumerate(puddles[:3]):
        rv, rf = [], []
        for k in range(24):
            a0, a1 = 2 * math.pi * k / 24, 2 * math.pi * (k + 1) / 24
            j = len(rv)
            rv += [(math.cos(a0), math.sin(a0), 0), (math.cos(a1), math.sin(a1), 0), (math.cos(a1) * 0.93, math.sin(a1) * 0.93, 0), (math.cos(a0) * 0.93, math.sin(a0) * 0.93, 0)]
            rf.append((j, j + 1, j + 2, j + 3))
        ring = reb.mesh_object(f"Puddle ring {i}", rv, rf, ring_m, smooth=False)
        ring.location = (x, y, height(x, y) + 0.02)
        rings.append((ring, i * 5))
        drips.append((x, y, height(x, y) + 2.6))
    reb.prim("cube", "Trail sign", mat("dark wood"), (1.4, 7.4, 1.4), (0.04, 0.9, 0.3))
    reb.wall(kit.rod("Trail sign post", mat("dark wood"), (1.4, 7.4, 0), (1.4, 7.4, 1.3), 0.05), "circle")
    kit.text("Trail sign words", "PYLON 7 TRAIL", mat("white paint"), (1.43, 7.4, 1.4), size=0.08, rot=(math.pi / 2, 0, math.pi / 2))

    # ---- Light: the sun down behind the western ridge; the yard lamp, the machine, the dome light.
    sun = kit.time_light("dusk", sun_heading=272, sun_energy=2.0)
    mist_m = mist_card_mat("Ground mist", (0.5, 0.45, 0.48), 0.5, 0.18)
    mists = []
    for i, (x, y, yaw) in enumerate(((-9.0, 3.0, math.pi / 2), (-9.0, 15.0, math.pi / 2), (5.0, -3.0, 0.0), (6.0, 19.0, 0.0), (16.0, 18.0, 0.0))):
        ob = reb.prim("plane", f"Mist bank {i}", mist_m, (x, y, 1.4), (12, 3.0, 1), rot=(math.pi / 2, 0, yaw))
        mists.append((ob, ob.location.copy(), rng.uniform(0, 6.3)))
    for nd in bpy.context.scene.world.node_tree.nodes:
        if nd.type == "MIX" and nd.blend_type == "ADD":
            nd.inputs["B"].default_value = (0.3, 0.1, 0.03, 1)
    vb = set(bpy.data.objects)
    kit.vista(rng, (7.0, 8.0), (0.0, 1.0), below=-20.0, haze=(0.3, 0.2, 0.22))
    kit.vista(rng, (7.0, 8.0), (1.0, 0.0), below=-20.0, haze=(0.22, 0.16, 0.22))
    kit.vista(rng, (7.0, 8.0), (0.0, -1.0), below=-10.0, far=(120, 300), haze=(0.22, 0.16, 0.2))
    kit.vista(rng, (7.0, 8.0), (-1.0, 0.0), below=-60.0, haze=(0.4, 0.22, 0.18))
    for ob in set(bpy.data.objects) - vb:
        ob.visible_shadow = False

    anim = kit.Anim(16)

    def wave(k):
        ph = anim.phase(k)
        for v, rest in zip(flag.data.vertices, flag_rest):
            x = rest.x
            v.co = (x - 0.04 * x * (1 + math.sin(ph * 2 + x * 3)), 0.18 * x * math.sin(ph + x * 3.2) + 0.05 * math.sin(2 * ph - rest.z * 4), rest.z - 0.06 * x * x)
        flag.data.update()
    anim.custom(wave)
    anim.flicker(vm_light, vm_m, depth=0.4, dropouts=2)
    anim.flicker(yard_lamp, sodium_m, depth=0.12, dropouts=1)
    anim.flicker(dome_light, dome_m, depth=0.08, dropouts=0)
    anim.flicker(office_light, office_glow, depth=0.5, dropouts=3)
    anim.flies((7.5, 5.4, 5.0), count=8, radius=0.5, size=0.02)
    anim.sway(grass, amount=0.05)
    anim.sway(alder_leaves, amount=0.04, every=4)
    anim.flicker(lane_lamp, lane_flame, depth=0.3, dropouts=1)
    anim.flicker(lane_spill, depth=0.3, dropouts=1)
    for at in drips:
        anim.drip(at, fall=2.58, size=0.02, m=drop_m)

    def spread(k):
        for ring, off in rings:
            t = ((k + off) % anim.frames) / anim.frames
            r = 0.04 + 0.32 * t
            ring.scale = (r, r, 1)
            ring.hide_render = t > 0.85
    anim.custom(spread)
    for ob, rest, ph in mists:
        anim.custom(lambda k, ob=ob, rest=rest, ph=ph: setattr(ob, "location", rest + Vector((1.2 * math.sin(anim.phase(k) + ph), 1.2 * math.cos(anim.phase(k) + ph), 0))))

    # ---- What the game needs.
    for x0, x1, y0, y1 in LANE:
        room.void((x0, Y0, x1, y0))
        room.void((x0, y1, x1, Y1))
    room.door("valley-path", (X_W, LANE[-1][2], X_W + 0.6, LANE[-1][3]), arrive=(-3.2, 9.4), face=(1, 0))
    room.door("lower-station", (X1 - 0.6, DOOR[0], X1, DOOR[1]), arrive=(11.9, 5.5), face=(-1, 0), walk=False)
    room.check((door_at.x - 1.3, door_at.y - 0.6, door_at.x + 0.6, door_at.y + 0.7), "A burgundy sedan. The driver's door is wide open, the light's still on.\nBlood on the seat. The keys are in the ignition.\nHer other shoe.")
    room.check((bx0 - 0.7, by0, bx0, by1), "TICKETS. The window's smashed in. Claw marks on the boards.")
    room.check((7.4, 5.8, 9.2, 7.0), "A handcart of sacks. SPENCER ESTATE.\nFertiliser, rat poison, chain.")
    room.check((X1 - 0.8, 7.9, X1, 9.0), "ICE COLD. It still works, after all this.")
    room.check((2.0, 6.5, 3.6, 7.3), "A dog's leash, chewed through.")
    room.check((X1 - 0.8, 3.6, X1, 4.8), "The office window's been broken in. From outside.")
    room.check((fx - 0.6, fy - 0.6, fx + 0.6, fy + 0.6), "The flag's still up. Nobody took it down for the night.")
    room.check((gx - 0.6, 7.4, gx + 0.6, 8.2), "A child's shoe, set on the post.\nSomeone found it in the lane and left it where it'd be seen.")
    room.check((-4.2, 10.0, -3.0, 10.75), "The fence is broken through.\nSomething big went through it, low down.")
    room.entry = "The bottom of the gondola. Someone left their car door open."
    room.export(anim)


build()
