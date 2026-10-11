"""Rebecca's prologue room: a trail down the Arklay mountain at night.

Run inside Blender (5.x). Builds the scene from nothing, sets up the room's
cameras from CAMERAS (in game units) and renders one 320x240 background per
camera into OUT_DIR. tools/rebecca/new_room.ts turns those renders into the
room's .pak backgrounds and writes the matching RDT camera records.

Game space is millimetres with Y pointing down; the floor is Y = 0. Blender
space is metres with Z up. The mapping is Blender (x, y, z) = (X, Z, -Y) / 1000,
a proper rotation, so handedness is kept. The engine projects with
sx = X*f/Z + 160 and sy = -Y*f/Z + 120 on a 320x240 screen (GteMatrix.cpp), so
a 32 mm sensor with a focal length of f/10 mm matches it exactly.

The look follows the courtyard garden she walks into next (ROOM300): a black
sky, dark foliage built from thousands of small leaf and needle cards, one cool
key light per camera that falls off into darkness at the edges, low mist, and
the Standard view transform with no filmic tone curve. Foliage, grass and
terrain are generated as plain meshes here, so the scene needs no add-ons and
renders the same way every time.
"""
import math
import os
import random

import bpy
from mathutils import Vector, noise

OUT_DIR = os.environ.get("RE1_OUT", r"C:\Users\joell\Documents\Blender\re1-rebecca\renders")

# The walkable trail: a strip along game Z, flat at Y = 0.
TRAIL_X = (2000, 5000)
TRAIL_Z = (0, 16000)

# Cameras in game units: position, look-at target, and the engine's fov value.
CAMERAS = [
    # 0: high behind the top of the trail, looking down it towards the mansion.
    # Covers Z 0-8000; Rebecca is about 60 px tall at Z = 0 and 30 px at Z = 8000.
    {"from": (3300, -4400, -5400), "to": (3600, 0, 9000), "fov": 250},
    # 1: beyond the foot of the trail, looking back up at Rebecca coming down.
    # Covers Z 8000-16000; the door at Z = 15500 sits near the bottom edge.
    {"from": (3500, -3300, 19000), "to": (3500, -500, 11500), "fov": 250},
]


def game_to_blender(p):
    x, y, z = p
    return Vector((x / 1000.0, z / 1000.0, -y / 1000.0))


def clear_scene():
    bpy.ops.wm.read_homefile(use_empty=True)


def height(x, y):
    """Ground height in Blender metres at (x, y): flat on the trail, banks
    rising away from it, the slope climbing behind the top and falling to the
    valley past the foot, with lumpy noise off the path."""
    tx0, tx1 = TRAIL_X[0] / 1000, TRAIL_X[1] / 1000
    dist = 0.0 if tx0 <= x <= tx1 else min(abs(x - tx0), abs(x - tx1))
    bank = min(dist * 0.35, 6.0)
    climb = max(0.0, -y) * 0.45
    fall = -min(max(0.0, y - 18.0) * 0.55, 14.0)
    lumps = noise.noise(Vector((x * 0.35, y * 0.35, 0.0))) * 0.45 + noise.noise(Vector((x * 1.7, y * 1.7, 3.0))) * 0.08
    edge = min(dist / 1.2, 1.0)
    # The path itself: worn ruts and a little unevenness.
    ruts = 0.0
    if dist == 0.0:
        u = (x - tx0) / (tx1 - tx0)
        ruts = -0.035 * (math.exp(-((u - 0.3) / 0.08) ** 2) + math.exp(-((u - 0.7) / 0.08) ** 2))
        ruts += noise.noise(Vector((x * 2.5, y * 2.5, 7.0))) * 0.02
    return bank + climb + fall + lumps * edge + ruts


def mesh_object(name, verts, faces, mat, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    if smooth:
        for poly in me.polygons:
            poly.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def nodes_material(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes["Principled BSDF"]


def ramp(nodes, links, fac_socket, stops):
    r = nodes.new("ShaderNodeValToRGB")
    els = r.color_ramp.elements
    els[0].position, els[0].color = stops[0][0], (*stops[0][1], 1)
    els[1].position, els[1].color = stops[-1][0], (*stops[-1][1], 1)
    for pos, rgb in stops[1:-1]:
        e = els.new(pos)
        e.color = (*rgb, 1)
    links.new(fac_socket, r.inputs["Fac"])
    return r


def noise_tex(nodes, scale, detail=8, rough=0.6, links=None):
    """Noise whose `scale` counts features per metre when `links` is given:
    it then reads object coordinates instead of the generated 0-1 box."""
    n = nodes.new("ShaderNodeTexNoise")
    if links is not None:
        tc = nodes.new("ShaderNodeTexCoord")
        links.new(tc.outputs["Object"], n.inputs["Vector"])
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    return n


def bumped(nodes, links, bsdf, height_socket, strength, distance=0.05):
    b = nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    links.new(height_socket, b.inputs["Height"])
    links.new(b.outputs["Normal"], bsdf.inputs["Normal"])


def mat_ground():
    """Dirt and stones on the path, grassy earth and leaf litter off it."""
    m, nodes, links, bsdf = nodes_material("Ground")
    bsdf.inputs["Roughness"].default_value = 0.95
    fine = noise_tex(nodes, 6, 12, 0.7, links)
    big = noise_tex(nodes, 0.35, 6, 0.55, links)
    vor = nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 3.5
    links.new(nodes.new("ShaderNodeTexCoord").outputs["Object"], vor.inputs["Vector"])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    links.new(big.outputs["Fac"], mix.inputs["Factor"])
    links.new(fine.outputs["Fac"], mix.inputs["A"])
    links.new(vor.outputs["Distance"], mix.inputs["B"])
    col = ramp(nodes, links, mix.outputs["Result"], [
        (0.0, (0.01, 0.009, 0.007)), (0.35, (0.035, 0.03, 0.02)),
        (0.55, (0.055, 0.05, 0.037)), (0.75, (0.025, 0.04, 0.018)), (1.0, (0.08, 0.075, 0.06))])
    links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    bumped(nodes, links, bsdf, mix.outputs["Result"], 0.6, 0.03)
    return m


def mat_rock():
    m, nodes, links, bsdf = nodes_material("Rock")
    bsdf.inputs["Roughness"].default_value = 0.85
    n = noise_tex(nodes, 4, 12, 0.7, links)
    col = ramp(nodes, links, n.outputs["Fac"], [
        (0.3, (0.02, 0.02, 0.02)), (0.55, (0.07, 0.07, 0.065)), (0.8, (0.14, 0.135, 0.125))])
    # Moss on the upward faces.
    geo = nodes.new("ShaderNodeNewGeometry")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(geo.outputs["Normal"], sep.inputs["Vector"])
    moss_mask = ramp(nodes, links, sep.outputs["Z"], [(0.8, (0, 0, 0)), (0.97, (0.7, 0.7, 0.7))])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    links.new(moss_mask.outputs["Color"], mix.inputs["Factor"])
    links.new(col.outputs["Color"], mix.inputs["A"])
    mix.inputs["B"].default_value = (0.02, 0.035, 0.012, 1)
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    bumped(nodes, links, bsdf, n.outputs["Fac"], 0.8, 0.04)
    return m


def mat_leaves(name, dark, light):
    """Leaf or needle cards, each card a shade of its own."""
    m, nodes, links, bsdf = nodes_material(name)
    bsdf.inputs["Roughness"].default_value = 0.55
    geo = nodes.new("ShaderNodeNewGeometry")
    col = ramp(nodes, links, geo.outputs["Random Per Island"], [(0.0, dark), (1.0, light)])
    links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def mat_wood(name, rgb):
    m, nodes, links, bsdf = nodes_material(name)
    bsdf.inputs["Roughness"].default_value = 0.9
    tc = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (40, 40, 2)
    links.new(tc.outputs["Object"], mapping.inputs["Vector"])
    n = noise_tex(nodes, 3, 10, 0.7)
    links.new(mapping.outputs["Vector"], n.inputs["Vector"])
    col = ramp(nodes, links, n.outputs["Fac"], [
        (0.3, tuple(c * 0.35 for c in rgb)), (0.6, rgb), (0.85, tuple(min(1, c * 1.6) for c in rgb))])
    links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    bumped(nodes, links, bsdf, n.outputs["Fac"], 0.7, 0.02)
    return m


def ground(mat):
    nx, ny = 200, 300
    x0, x1, y0, y1 = -36.0, 44.0, -40.0, 100.0
    verts, faces = [], []
    for j in range(ny + 1):
        y = y0 + (y1 - y0) * j / ny
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            verts.append((x, y, height(x, y)))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    mesh_object("Mountainside", verts, faces, mat)


def card(verts, faces, base, out, up, width, length, droop):
    """One leaf or needle card: a quad from `base` reaching along `out`, bent
    down by `droop` radians, `width` across."""
    side = up.cross(out)
    if side.length < 1e-6:
        side = Vector((1, 0, 0))
    side.normalize()
    reach = (out * math.cos(droop) - up * math.sin(droop)).normalized() * length
    hw = side * (width / 2)
    k = len(verts)
    tip = base + reach
    verts.extend([base - hw, base + hw, tip + hw * 0.6, tip - hw * 0.6])
    faces.append((k, k + 1, k + 2, k + 3))


def conifer(rng, loc, h, verts, faces, trunks):
    """A spruce: a trunk and about a thousand drooping needle cards on a ragged cone."""
    up = Vector((0, 0, 1))
    base = Vector(loc)
    trunks.append((base, h))
    radius = h * rng.uniform(0.2, 0.27)
    for _ in range(int(h * 380)):
        t = rng.uniform(0.18, 1.0) ** 0.8
        r = radius * (1.0 - t) ** 0.9 * rng.uniform(0.55, 1.05) + 0.05
        a = rng.uniform(0, 2 * math.pi)
        out = Vector((math.cos(a), math.sin(a), 0))
        p = base + up * (h * t) + out * r * rng.uniform(0.3, 1.0)
        card(verts, faces, p, out, up, rng.uniform(0.1, 0.2), rng.uniform(0.25, 0.5) * (0.6 + 0.4 * r), rng.uniform(0.3, 0.8))


def bush(rng, loc, size, verts, faces):
    """A low clump of broad leaves."""
    up = Vector((0, 0, 1))
    c = Vector(loc)
    # Fern-like: fronds fanning out from the middle, each a run of small leaflets.
    for _ in range(int(size * 110)):
        a = rng.uniform(0, 2 * math.pi)
        lift = rng.uniform(0.3, 1.1)
        frond = Vector((math.cos(a), math.sin(a), 0))
        for k in range(14):
            t = k / 14
            arc = c + frond * size * t * 1.3 + up * size * (math.sin(lift) * t - 0.6 * t * t)
            for side in (-1, 1):
                out = (frond + up.cross(frond) * side * 0.9).normalized()
                card(verts, faces, arc, out, up, rng.uniform(0.04, 0.07), 0.15 * (1.1 - t), rng.uniform(0.1, 0.5))


def trunks_mesh(trunks, mat):
    verts, faces = [], []
    for base, h in trunks:
        k = len(verts)
        r = h * 0.03
        for ring, z in ((0, 0.0), (1, h * 0.85)):
            rr = r if ring == 0 else r * 0.25
            for s in range(7):
                a = 2 * math.pi * s / 7
                verts.append((base.x + math.cos(a) * rr, base.y + math.sin(a) * rr, base.z + z))
        for s in range(7):
            faces.append((k + s, k + (s + 1) % 7, k + 7 + (s + 1) % 7, k + 7 + s))
    mesh_object("Trunks", verts, faces, mat)


def on_trail_view(x, y):
    """Keep the trail, a margin and the cameras' lines of sight clear, so no
    foreground masks are needed."""
    if TRAIL_X[0] / 1000 - 3.0 < x < TRAIL_X[1] / 1000 + 3.0 and -8 < y < 20:
        return True
    return y > 20 and abs(x - 3.5) < 9


def forest(rng, mats):
    verts, faces, trunks = [], [], []
    placed = 0
    while placed < 170:
        x = rng.uniform(-22, 28)
        y = rng.uniform(-18, 40)
        if on_trail_view(x, y):
            continue
        conifer(rng, (x, y, height(x, y) - 0.2), rng.uniform(7, 14), verts, faces, trunks)
        placed += 1
    mesh_object("Spruce needles", verts, faces, mats["needles"], smooth=False)
    trunks_mesh(trunks, mats["bark"])
    # Undergrowth along both verges.
    verts, faces = [], []
    for _ in range(70):
        x = rng.choice([rng.uniform(-1.5, 1.6), rng.uniform(5.4, 8.5)])
        y = rng.uniform(-3, 19)
        bush(rng, (x, y, height(x, y) + 0.1), rng.uniform(0.35, 0.8), verts, faces)
    mesh_object("Undergrowth", verts, faces, mats["leaves"], smooth=False)


def grass(rng, mat):
    """Tufts of blades on the verges and in the middle strip between the ruts."""
    verts, faces = [], []
    tx0, tx1 = TRAIL_X[0] / 1000, TRAIL_X[1] / 1000
    for _ in range(9000):
        cx = rng.choice([rng.uniform(-2.5, tx0 + 0.25), rng.uniform(tx1 - 0.25, 9.0)])
        cy = rng.uniform(-4, 20)
        for _ in range(rng.randint(4, 9)):
            x = cx + rng.gauss(0, 0.06)
            y = cy + rng.gauss(0, 0.06)
            z = height(x, y)
            a = rng.uniform(0, 2 * math.pi)
            lean = Vector((math.cos(a), math.sin(a), 0)) * rng.uniform(0.02, 0.12)
            hgt = rng.uniform(0.12, 0.35) * (0.5 if tx0 < cx < tx1 else 1.0)
            w = Vector((-math.sin(a), math.cos(a), 0)) * 0.012
            k = len(verts)
            b = Vector((x, y, z))
            verts.extend([b - w, b + w, b + lean + Vector((0, 0, hgt))])
            faces.append((k, k + 1, k + 2))
    mesh_object("Grass", verts, faces, mat, smooth=False)


def rocks(rng, mat):
    verts, faces = [], []
    tx0, tx1 = TRAIL_X[0] / 1000, TRAIL_X[1] / 1000
    for i in range(55):
        big = i < 18
        x = rng.choice([rng.uniform(tx0 - 1.4, tx0 - 0.1), rng.uniform(tx1 + 0.1, tx1 + 1.6)]) if big else rng.uniform(tx0 - 0.5, tx1 + 0.5)
        y = rng.uniform(-1, 17)
        r = rng.uniform(0.25, 0.75) if big else rng.uniform(0.04, 0.12)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1)
        tmp = bpy.context.active_object
        seed = rng.uniform(0, 100)
        k = len(verts)
        for v in tmp.data.vertices:
            n = v.co.normalized()
            d = 1 + noise.noise(n * 1.6 + Vector((seed, 0, 0))) * 0.4 + noise.noise(n * 5 + Vector((0, seed, 0))) * 0.12 + abs(noise.noise(n * 11 + Vector((seed, seed, 0)))) * 0.06
            p = n * d
            verts.append((x + p.x * r * 1.2, y + p.y * r, height(x, y) - r * 0.25 + max(p.z, -0.5) * r * 0.9))
        faces.extend([tuple(k + i for i in poly.vertices) for poly in tmp.data.polygons])
        bpy.data.objects.remove(tmp)
    mesh_object("Rocks", verts, faces, mat)


def box(verts, faces, center, size, rot=0.0):
    cx, cy, cz = center
    sx, sy, sz = (s / 2 for s in size)
    c, s = math.cos(rot), math.sin(rot)
    k = len(verts)
    for dx, dy, dz in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
        x, y = dx * sx, dy * sy
        verts.append((cx + x * c - y * s, cy + x * s + y * c, cz + dz * sz))
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        faces.append(tuple(k + i for i in f))


def fence_and_log(rng, mat):
    """A leaning post-and-rail fence down the east verge and a fallen log on the west."""
    verts, faces = [], []
    fx = TRAIL_X[1] / 1000 + 0.55
    ys = [y * 2.2 - 0.5 for y in range(9)]
    for y in ys:
        lean = rng.uniform(-0.06, 0.06)
        box(verts, faces, (fx + lean, y, height(fx, y) + 0.55), (0.12, 0.12, 1.2), rng.uniform(-0.2, 0.2))
    for a, b in zip(ys, ys[1:]):
        if rng.random() < 0.15:
            continue  # a rail has fallen
        for hgt in (0.45, 0.95):
            mid = (a + b) / 2
            box(verts, faces, (fx, mid, height(fx, mid) + hgt + rng.uniform(-0.05, 0.05)), (0.07, b - a + 0.2, 0.09), rng.uniform(-0.03, 0.03))
    mesh_object("Fence", verts, faces, mat, smooth=False)
    bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=0.22, depth=4.2)
    log = bpy.context.active_object
    log.name = "Fallen log"
    lx, ly = TRAIL_X[0] / 1000 - 0.9, 6.5
    log.location = (lx, ly, height(lx, ly) + 0.15)
    log.rotation_euler = (math.radians(90), 0, math.radians(12))
    log.data.materials.append(mat)
    bpy.ops.object.shade_smooth()


def mansion(mat):
    # A dark shape far down the valley with two lit windows, seen from camera 0 only.
    verts, faces = [], []
    base = Vector((3.5, 70.0, -14.0))
    for off, size in (((0, 0, 4), (22, 9, 8)), ((14, 3, 3), (8, 12, 6)), ((-14, 3, 3), (8, 12, 6)), ((0, 0, 9), (23, 10, 2.5))):
        box(verts, faces, tuple(base + Vector(off)), size)
    mesh_object("Mansion", verts, faces, mat, smooth=False)
    glow = bpy.data.materials.new("Window glow")
    glow.use_nodes = True
    nodes = glow.node_tree.nodes
    nodes.remove(nodes["Principled BSDF"])
    em = nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.55, 0.2, 1)
    em.inputs["Strength"].default_value = 3
    glow.node_tree.links.new(em.outputs["Emission"], nodes["Material Output"].inputs["Surface"])
    verts, faces = [], []
    for row, wz in enumerate((2.5, 5.5)):
        for col in range(9):
            if (col * 7 + row * 3) % 5 in (1, 3):
                box(verts, faces, (base.x - 9 + col * 2.25, base.y - 4.6, base.z + wz), (0.7, 0.1, 1.2))
    mesh_object("Lit windows", verts, faces, glow, smooth=False)


def lights_and_world():
    scene = bpy.context.scene
    world = bpy.data.worlds.new("Night")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.004, 0.006, 0.01, 1)
    bg.inputs["Strength"].default_value = 1.0
    # Faint moonlight from high on the east, cool.
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(35), math.radians(25), math.radians(110)))
    moon = bpy.context.active_object
    moon.name = "Moon"
    moon.data.energy = 0.18
    moon.data.color = (0.55, 0.65, 0.9)
    moon.data.angle = math.radians(1)
    # One key light over each half of the trail, like the garden's: cool
    # green-white, a soft pool that leaves the edges of the frame in the dark.
    for name, at, aim in (("Key upper", (3.4, -3.5, 7.5), (3.6, 4.5, 0)), ("Key lower", (3.6, 17.5, 6.5), (3.5, 10.5, 0))):
        bpy.ops.object.light_add(type="SPOT", location=at)
        key = bpy.context.active_object
        key.name = name
        key.data.energy = 900
        key.data.color = (0.78, 0.9, 0.82)
        key.data.spot_size = math.radians(95)
        key.data.spot_blend = 0.85
        key.data.shadow_soft_size = 0.4
        key.rotation_euler = (Vector(aim) - Vector(at)).to_track_quat("-Z", "Y").to_euler()
    # A wide, faint fill from each camera, as the originals light the walls of
    # a set from the viewer's side: it picks out the needles of the tree line.
    for i, c in enumerate(CAMERAS):
        at, aim = game_to_blender(c["from"]), game_to_blender(c["to"])
        bpy.ops.object.light_add(type="SPOT", location=at)
        fill = bpy.context.active_object
        fill.name = f"Fill {i}"
        fill.data.energy = 1500
        fill.data.color = (0.7, 0.85, 0.8)
        fill.data.spot_size = math.radians(120)
        fill.data.spot_blend = 1.0
        fill.data.shadow_soft_size = 1.5
        fill.rotation_euler = (aim - at).to_track_quat("-Z", "Y").to_euler()
    # Low mist hanging in the trees and down the valley.
    bpy.ops.mesh.primitive_cube_add(size=1)
    mist = bpy.context.active_object
    mist.name = "Mist"
    mist.scale = (90, 160, 4)
    mist.location = (3.5, 30, -0.5)
    m = bpy.data.materials.new("Mist")
    m.use_nodes = True
    nodes = m.node_tree.nodes
    nodes.remove(nodes["Principled BSDF"])
    vol = nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = 0.009
    vol.inputs["Color"].default_value = (0.7, 0.78, 0.8, 1)
    m.node_tree.links.new(vol.outputs["Volume"], nodes["Material Output"].inputs["Volume"])
    mist.data.materials.append(m)


def add_cameras():
    cams = []
    for i, c in enumerate(CAMERAS):
        data = bpy.data.cameras.new(f"Room camera {i}")
        data.sensor_fit = "HORIZONTAL"
        data.sensor_width = 32.0
        data.lens = c["fov"] / 10.0
        data.clip_start = 0.1
        data.clip_end = 400
        cam = bpy.data.objects.new(f"Room camera {i}", data)
        bpy.context.scene.collection.objects.link(cam)
        eye = game_to_blender(c["from"])
        target = game_to_blender(c["to"])
        cam.location = eye
        cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
        cams.append(cam)
    return cams


def render(cams):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type != "CPU"
    scene.cycles.device = "GPU"
    scene.cycles.samples = 512
    scene.cycles.use_denoising = True
    scene.cycles.volume_step_rate = 2.0
    # A narrow pixel filter keeps the 320x240 frame crisp, like the originals.
    scene.cycles.filter_width = 1.0
    scene.render.resolution_x = 320
    scene.render.resolution_y = 240
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = float(os.environ.get("RE1_EXPOSURE", "0"))
    os.makedirs(OUT_DIR, exist_ok=True)
    paths = []
    for i, cam in enumerate(cams):
        scene.camera = cam
        scene.render.filepath = os.path.join(OUT_DIR, f"cam{i}.png")
        bpy.ops.render.render(write_still=True)
        paths.append(scene.render.filepath)
    return paths


def build(seed=24):
    rng = random.Random(seed)
    clear_scene()
    mats = {
        "bark": mat_wood("Bark", (0.06, 0.045, 0.03)),
        "needles": mat_leaves("Spruce needles", (0.01, 0.025, 0.015), (0.05, 0.1, 0.055)),
        "leaves": mat_leaves("Undergrowth leaves", (0.008, 0.022, 0.008), (0.04, 0.08, 0.03)),
        "grass": mat_leaves("Grass", (0.02, 0.035, 0.012), (0.08, 0.1, 0.04)),
        "fence": mat_wood("Weathered wood", (0.11, 0.09, 0.07)),
        "mansion": mat_leaves("Mansion", (0.01, 0.01, 0.012), (0.015, 0.015, 0.018)),
    }
    ground(mat_ground())
    forest(rng, mats)
    grass(rng, mats["grass"])
    rocks(rng, mat_rock())
    fence_and_log(rng, mats["fence"])
    mansion(mats["mansion"])
    lights_and_world()
    cams = add_cameras()
    if os.environ.get("RE1_SAVE_BLEND"):
        bpy.ops.wm.save_as_mainfile(filepath=os.environ["RE1_SAVE_BLEND"])
    return render(cams)


if __name__ == "__main__":
    build()
