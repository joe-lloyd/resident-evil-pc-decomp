"""Shared building blocks for Rebecca's new rooms, run inside Blender 5.x.

A room's scene script builds its geometry with these helpers, tags what the
game needs to know, and calls export(). export() renders, per camera:

  cam<N>.png        the 320x240 background
  cam<N>.depth.png  the foreground depth: for objects tagged with mask(), the
                    view-space Z / 16 in game units as R * 256 + G, alpha 0
                    where no tagged object is the visible surface
and writes room.json: the cameras in game units and the collision taken from
objects tagged with wall().

Game space has Y pointing down; the floor is Y = 0. Blender space is metres
with Z up: Blender (x, y, z) = (X, Z, -Y) / UNITS. UNITS is the game's own
scale: Rebecca stands 2700 units tall, measured on screen
(tools/harness/measure-height.ts), so a metre is 1700 units and a scene built
in real sizes fits her. The engine
projects with sx = X*f/Z + 160 and sy = -Y*f/Z + 120 on a 320x240 screen, so a
32 mm sensor with a focal length of f/10 mm matches it exactly. Collision
coordinates are unsigned in the game, so every room lives at X, Z >= 0.
"""
import json
import math
import os
import random

import bpy
from mathutils import Vector, noise

# ---------------------------------------------------------------------------
# Space
# ---------------------------------------------------------------------------


UNITS = 1700.0


def g(metres):
    """A length in metres as whole game units."""
    return round(metres * UNITS)


def game_to_blender(p):
    x, y, z = p
    return Vector((x / UNITS, z / UNITS, -y / UNITS))


def clear_scene():
    bpy.ops.wm.read_homefile(use_empty=True)


# ---------------------------------------------------------------------------
# Meshes and materials
# ---------------------------------------------------------------------------


def mesh_object(name, verts, faces, mat, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    if smooth:
        for poly in me.polygons:
            poly.use_smooth = True
    if mat is not None:
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


def noise_tex(nodes, links, scale, detail=8, rough=0.6):
    """Noise in object space: `scale` features per metre."""
    n = nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    tc = nodes.new("ShaderNodeTexCoord")
    links.new(tc.outputs["Object"], n.inputs["Vector"])
    return n


def bumped(nodes, links, bsdf, height_socket, strength, distance=0.05):
    b = nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    links.new(height_socket, b.inputs["Height"])
    links.new(b.outputs["Normal"], bsdf.inputs["Normal"])


def mat_surface(name, stops, scale=4.0, detail=12, rough=0.9, bump=0.6):
    """A rough surface whose colour wanders through `stops` (position, rgb)."""
    m, nodes, links, bsdf = nodes_material(name)
    bsdf.inputs["Roughness"].default_value = rough
    n = noise_tex(nodes, links, scale, detail, 0.7)
    col = ramp(nodes, links, n.outputs["Fac"], stops)
    links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    bumped(nodes, links, bsdf, n.outputs["Fac"], bump, 0.03)
    return m


def mat_cards(name, dark, light):
    """Leaf, needle or grass cards, each card a shade of its own and broken
    into bright and dark specks across it, the way RE1's photographed
    foliage is a mass of lit tips and black gaps rather than flat shapes."""
    m, nodes, links, bsdf = nodes_material(name)
    bsdf.inputs["Roughness"].default_value = 0.55
    geo = nodes.new("ShaderNodeNewGeometry")
    col = ramp(nodes, links, geo.outputs["Random Per Island"], [(0.0, dark), (1.0, light)])
    n = noise_tex(nodes, links, 28, 4, 0.8)
    rng = nodes.new("ShaderNodeMapRange")
    rng.inputs["From Min"].default_value, rng.inputs["From Max"].default_value = 0.3, 0.7
    rng.inputs["To Min"].default_value, rng.inputs["To Max"].default_value = 0.4, 2.1
    links.new(n.outputs["Fac"], rng.inputs["Value"])
    lit = nodes.new("ShaderNodeVectorMath")
    lit.operation = "SCALE"
    links.new(col.outputs["Color"], lit.inputs[0])
    links.new(rng.outputs["Result"], lit.inputs["Scale"])
    links.new(lit.outputs[0], bsdf.inputs["Base Color"])
    # Lace: each card has holes, so a mass of them reads as needles and
    # fronds with the dark showing through, not as solid shapes.
    holes = noise_tex(nodes, links, 55, 2, 0.5)
    cut = nodes.new("ShaderNodeMath")
    cut.operation = "GREATER_THAN"
    cut.inputs[1].default_value = 0.44
    links.new(holes.outputs["Fac"], cut.inputs[0])
    clear = nodes.new("ShaderNodeBsdfTransparent")
    both = nodes.new("ShaderNodeMixShader")
    links.new(cut.outputs[0], both.inputs["Fac"])
    links.new(clear.outputs[0], both.inputs[1])
    links.new(bsdf.outputs[0], both.inputs[2])
    out = nodes["Material Output"]
    links.new(both.outputs[0], out.inputs["Surface"])
    return m


def mat_wood(name, rgb):
    m, nodes, links, bsdf = nodes_material(name)
    bsdf.inputs["Roughness"].default_value = 0.9
    tc = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (40, 40, 2)
    links.new(tc.outputs["Object"], mapping.inputs["Vector"])
    n = nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 3
    n.inputs["Detail"].default_value = 10
    links.new(mapping.outputs["Vector"], n.inputs["Vector"])
    col = ramp(nodes, links, n.outputs["Fac"], [(0.3, tuple(c * 0.35 for c in rgb)), (0.6, rgb), (0.85, tuple(min(1, c * 1.6) for c in rgb))])
    links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    bumped(nodes, links, bsdf, n.outputs["Fac"], 0.7, 0.02)
    return m


def mat_emit(name, rgb, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes = m.node_tree.nodes
    nodes.remove(nodes["Principled BSDF"])
    em = nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*rgb, 1)
    em.inputs["Strength"].default_value = strength
    m.node_tree.links.new(em.outputs["Emission"], nodes["Material Output"].inputs["Surface"])
    return m


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


def terrain(name, mat, x_range, y_range, height, step=0.4):
    """A ground mesh over Blender X/Y ranges (metres), z = height(x, y)."""
    nx = max(2, int((x_range[1] - x_range[0]) / step))
    ny = max(2, int((y_range[1] - y_range[0]) / step))
    verts, faces = [], []
    for j in range(ny + 1):
        y = y_range[0] + (y_range[1] - y_range[0]) * j / ny
        for i in range(nx + 1):
            x = x_range[0] + (x_range[1] - x_range[0]) * i / nx
            verts.append((x, y, height(x, y)))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    return mesh_object(name, verts, faces, mat)


def _lean(base):
    """A tree's lean, the same for its crown and its trunk: drawn from where it stands."""
    r = random.Random(round(base[0] * 1000) * 7919 + round(base[1] * 1000))
    return Vector((r.uniform(-1, 1), r.uniform(-1, 1), 0)) * r.uniform(0.0, 0.05)


def conifer(rng, base, h, verts, faces):
    """A spruce's needles, ragged as RE1's photo trees are: whorls of drooping
    branches at uneven heights, a bare lower trunk, one side thinner where it
    grew against its neighbours, a lean, and now and then a broken top. About
    460 cards a metre, since the cards are lace."""
    up = Vector((0, 0, 1))
    base = Vector(base)
    lean = _lean(base)
    top = h * (rng.uniform(0.55, 0.8) if rng.random() < 0.15 else 1.0)
    radius = h * rng.uniform(0.17, 0.26)
    bare = rng.uniform(0.12, 0.35)
    gap = rng.uniform(0, 2 * math.pi)
    z = h * bare
    budget = int(h * 460)
    while z < top and budget > 0:
        t = z / h
        for _ in range(rng.randint(3, 7)):
            a = rng.uniform(0, 2 * math.pi)
            if abs(math.atan2(math.sin(a - gap), math.cos(a - gap))) < 0.8 and rng.random() < 0.6:
                continue
            out = Vector((math.cos(a), math.sin(a), 0))
            length = (radius * (1.0 - t) ** 0.8 + 0.15) * rng.uniform(0.5, 1.25)
            droop = rng.uniform(0.15, 0.55)
            root = base + lean * z + up * z
            steps = max(3, int(length / 0.12))
            for k in range(steps):
                s = (k + 1) / steps
                p = root + out * length * s - up * droop * length * s * s
                for _ in range(rng.randint(2, 4)):
                    jitter = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.6, 0.2))) * 0.12
                    twist = Vector((rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), 0))
                    card(verts, faces, p + jitter, (out + twist).normalized(), up,
                         rng.uniform(0.1, 0.2), rng.uniform(0.2, 0.42) * (0.7 + 0.3 * (1 - s)), rng.uniform(0.4, 1.0))
                    budget -= 1
        z += rng.uniform(0.25, 0.6) * (1.0 + (1 - t))
    # A ragged leader at the top.
    for _ in range(int(top * 10)):
        p = base + lean * top + up * rng.uniform(top * 0.9, top)
        card(verts, faces, p, Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), up, 0.08, 0.25, 0.3)


def trunks(name, mat, bases):
    """Trunks with a kink, the crown's lean and dead branch stubs on the bare
    lower part: bases is [(Vector base, height)]."""
    verts, faces = [], []
    for base, h in bases:
        rng = random.Random(round(base.x * 977) + round(base.y * 131))
        lean = _lean(base)
        r = h * 0.03
        rings = [(0.0, r * 1.25), (0.08, r), (0.45, r * 0.7), (0.85, r * 0.25)]
        k0 = len(verts)
        for i, (t, rr) in enumerate(rings):
            c = Vector(base) + Vector((0, 0, h * t)) + lean * h * t + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)) * 0.04 * i
            for s in range(7):
                a = 2 * math.pi * s / 7
                verts.append((c.x + math.cos(a) * rr * rng.uniform(0.85, 1.1), c.y + math.sin(a) * rr * rng.uniform(0.85, 1.1), c.z))
        for i in range(len(rings) - 1):
            a0, a1 = k0 + i * 7, k0 + (i + 1) * 7
            for s in range(7):
                faces.append((a0 + s, a0 + (s + 1) % 7, a1 + (s + 1) % 7, a1 + s))
        for _ in range(rng.randint(4, 10)):
            z = h * rng.uniform(0.1, 0.35)
            a = rng.uniform(0, 2 * math.pi)
            p = Vector(base) + Vector((0, 0, z)) + lean * z
            d = Vector((math.cos(a), math.sin(a), rng.uniform(-0.4, 0.1))) * rng.uniform(0.3, 1.1)
            k = len(verts)
            side = Vector((-math.sin(a), math.cos(a), 0)) * 0.02
            verts += [tuple(p - side), tuple(p + side), tuple(p + d + side * 0.3), tuple(p + d - side * 0.3)]
            faces.append((k, k + 1, k + 2, k + 3))
    return mesh_object(name, verts, faces, mat)


def fern(rng, centre, size, verts, faces):
    """Fronds fanning out from the middle, each a run of small leaflets, and
    no two alike: fronds of uneven length, some bent over or broken off, some
    leaflets gone, the whole clump leaning one way."""
    up = Vector((0, 0, 1))
    c = Vector(centre)
    tilt = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)) * rng.uniform(0.0, 0.35)
    for _ in range(int(size * rng.uniform(70, 120))):
        a = rng.uniform(0, 2 * math.pi)
        frond = (Vector((math.cos(a), math.sin(a), 0)) + tilt).normalized()
        reach = size * rng.uniform(0.6, 1.4)
        lift = rng.uniform(0.2, 1.2)
        sag = rng.uniform(0.4, 1.1) if rng.random() < 0.25 else 0.6
        broken = rng.randint(6, 13) if rng.random() < 0.2 else 14
        for k in range(broken):
            t = k / 14
            arc = c + frond * reach * t * 1.3 + up * reach * (math.sin(lift) * t - sag * t * t)
            for side in (-1, 1):
                if rng.random() < 0.12:
                    continue
                out = (frond + up.cross(frond) * side * rng.uniform(0.6, 1.1)).normalized()
                card(verts, faces, arc, out, up, rng.uniform(0.035, 0.075), 0.15 * (1.1 - t) * rng.uniform(0.7, 1.2), rng.uniform(0.1, 0.6))


def grass_tufts(rng, count, where, height, verts, faces):
    """`count` tufts at points from where(rng) -> (x, y), on the ground height(x, y)."""
    for _ in range(count):
        cx, cy = where(rng)
        for _ in range(rng.randint(4, 9)):
            x = cx + rng.gauss(0, 0.06)
            y = cy + rng.gauss(0, 0.06)
            z = height(x, y)
            a = rng.uniform(0, 2 * math.pi)
            lean = Vector((math.cos(a), math.sin(a), 0)) * rng.uniform(0.02, 0.12)
            h = rng.uniform(0.12, 0.35)
            w = Vector((-math.sin(a), math.cos(a), 0)) * 0.012
            k = len(verts)
            b = Vector((x, y, z))
            verts.extend([b - w, b + w, b + lean + Vector((0, 0, h))])
            faces.append((k, k + 1, k + 2))


def boulder(rng, centre, r, verts, faces, squash=0.9, subdivisions=3):
    """A lumpy rock, appended to verts/faces. One subdivision, drawn flat
    (mesh_object smooth=False), makes a freshly broken, angular one."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1)
    tmp = bpy.context.active_object
    seed = rng.uniform(0, 100)
    k = len(verts)
    cx, cy, cz = centre
    for v in tmp.data.vertices:
        n = v.co.normalized()
        d = 1 + noise.noise(n * 1.6 + Vector((seed, 0, 0))) * 0.4 + noise.noise(n * 5 + Vector((0, seed, 0))) * 0.12
        p = n * d
        verts.append((cx + p.x * r * 1.2, cy + p.y * r, cz + max(p.z, -0.5) * r * squash))
    faces.extend([tuple(k + i for i in poly.vertices) for poly in tmp.data.polygons])
    bpy.data.objects.remove(tmp)


# ---------------------------------------------------------------------------
# Props: primitives sized in metres
# ---------------------------------------------------------------------------


def prim(kind, name, mat, at, size=(1, 1, 1), rot=(0, 0, 0), segments=16, top=0.0, bevel=0.0):
    """A primitive `size` metres across (x, y, z) centred on `at`, rotated by
    `rot` (radians, XYZ). kind: cube, cyl, cone (narrowing to `top` of its
    base), sphere or plane. Scale is applied, so bevels and object-space
    textures stay true to size."""
    if kind == "cube":
        bpy.ops.mesh.primitive_cube_add(size=1)
    elif kind == "cyl":
        bpy.ops.mesh.primitive_cylinder_add(vertices=segments, radius=0.5, depth=1)
    elif kind == "cone":
        bpy.ops.mesh.primitive_cone_add(vertices=segments, radius1=0.5, radius2=0.5 * top, depth=1)
    elif kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=max(6, segments // 2), radius=0.5)
    elif kind == "plane":
        bpy.ops.mesh.primitive_plane_add(size=1)
    else:
        raise ValueError(kind)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.location = at
    ob.rotation_euler = rot
    if kind in ("cyl", "cone", "sphere"):
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    if mat is not None:
        ob.data.materials.append(mat)
    if bevel:
        mod = ob.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
    return ob


def cloth(name, mat, at, size, rot=(0, 0, 0), cuts=24, lumps=0.04, seed=0):
    """A sheet of cloth `size` (x, y) metres, crumpled by up to `lumps` metres."""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=cuts, y_subdivisions=cuts, size=1)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    off = Vector((seed * 7.1, seed * 3.3, seed * 1.7))
    for v in ob.data.vertices:
        v.co.z += lumps * noise.noise(v.co * 6 + off)
    ob.location = at
    ob.rotation_euler = rot
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat)
    return ob


def mat_metal(name, rgb, rough=0.35):
    m, nodes, links, bsdf = nodes_material(name)
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = rough
    return m


def mat_glass(name, rgb=(0.9, 0.95, 0.9)):
    m, nodes, links, bsdf = nodes_material(name)
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.05
    return m


def mat_plain(name, rgb, rough=0.8):
    m, nodes, links, bsdf = nodes_material(name)
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    return m


def mat_stripes(name, colours, across=8.0, axis="X"):
    """Bands of `colours` in turn, `across` bands per metre along `axis`: a rag rug, a blanket."""
    m, nodes, links, bsdf = nodes_material(name)
    bsdf.inputs["Roughness"].default_value = 0.95
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Object"], sep.inputs["Vector"])
    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = across / len(colours)
    links.new(sep.outputs[axis], mul.inputs[0])
    frac = nodes.new("ShaderNodeMath")
    frac.operation = "FRACT"
    links.new(mul.outputs[0], frac.inputs[0])
    r = nodes.new("ShaderNodeValToRGB")
    r.color_ramp.interpolation = "CONSTANT"
    els = r.color_ramp.elements
    els[0].position, els[0].color = 0.0, (*colours[0], 1)
    els[1].position, els[1].color = 1.0 - 1e-3, (*colours[-1], 1)
    for i, c in enumerate(colours[1:], start=1):
        e = els.new(i / len(colours))
        e.color = (*c, 1)
    links.new(frac.outputs[0], r.inputs["Fac"])
    links.new(r.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def emit_strength(mat, strength):
    """Change an emission material's strength (mat_emit), e.g. to flicker a flame."""
    for n in mat.node_tree.nodes:
        if n.type == "EMISSION":
            n.inputs["Strength"].default_value = strength


# ---------------------------------------------------------------------------
# Tags: what the game needs to know about an object
# ---------------------------------------------------------------------------


def wall(ob, shape="box"):
    """The object blocks the player: its footprint becomes a collision record."""
    ob["re_wall"] = shape
    return ob


def mask(ob):
    """The object can stand in front of the player: it is cut into masks."""
    ob["re_mask"] = True
    return ob


# ---------------------------------------------------------------------------
# Light by the hour
# ---------------------------------------------------------------------------

TIME_OF_DAY = {
    # sky colour and strength, sun elevation and heading (degrees), sun colour
    # and strength, mist density
    "dawn": ((0.42, 0.34, 0.4), 0.9, 7, 70, (1.0, 0.62, 0.4), 4.0, 0.008),
    "morning": ((0.46, 0.56, 0.72), 0.75, 22, 100, (1.0, 0.86, 0.7), 3.4, 0.006),
    "noon": ((0.5, 0.64, 0.86), 0.9, 62, 160, (1.0, 0.96, 0.9), 4.0, 0.003),
    "afternoon": ((0.52, 0.56, 0.66), 0.75, 34, 230, (1.0, 0.85, 0.65), 3.2, 0.004),
    "dusk": ((0.36, 0.22, 0.2), 0.4, 4, 280, (1.0, 0.45, 0.25), 2.2, 0.01),
    "night": ((0.004, 0.006, 0.01), 1.0, 35, 110, (0.55, 0.65, 0.9), 0.18, 0.009),
}


def light_for(time, mist_box=None, mist_density=None):
    """Sky, sun (or moon) and mist for the hour. mist_box: (centre, scale) in metres."""
    sky_rgb, sky_strength, elevation, heading, sun_rgb, sun_energy, mist = TIME_OF_DAY[time]
    scene = bpy.context.scene
    world = bpy.data.worlds.new(time)
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*sky_rgb, 1)
    bg.inputs["Strength"].default_value = sky_strength
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(90 - elevation), 0, math.radians(heading)))
    sun = bpy.context.active_object
    sun.name = "Sun" if time != "night" else "Moon"
    sun.data.energy = sun_energy
    sun.data.color = sun_rgb
    sun.data.angle = math.radians(1.5)
    if mist_box:
        centre, scale = mist_box
        bpy.ops.mesh.primitive_cube_add(size=1, location=centre)
        m_ob = bpy.context.active_object
        m_ob.name = "Mist"
        m_ob.scale = scale
        m = bpy.data.materials.new("Mist")
        m.use_nodes = True
        nodes = m.node_tree.nodes
        nodes.remove(nodes["Principled BSDF"])
        vol = nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Density"].default_value = mist if mist_density is None else mist_density
        vol.inputs["Color"].default_value = (0.62, 0.66, 0.76, 1)
        m.node_tree.links.new(vol.outputs["Volume"], nodes["Material Output"].inputs["Volume"])
        m_ob.data.materials.append(m)


def gradient_sky(horizon, zenith, below=(0.02, 0.02, 0.03), strength=1.0, sun_dir=None, sun_glow=(1.0, 0.55, 0.3)):
    """A sky that runs from `horizon` to `zenith`, with an optional glow around
    the sun's direction (a unit Vector) for dawn and dusk."""
    world = bpy.context.scene.world
    nt = world.node_tree
    nodes, links = nt.nodes, nt.links
    bg = nodes["Background"]
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    r = nodes.new("ShaderNodeValToRGB")
    els = r.color_ramp.elements
    els[0].position, els[0].color = 0.42, (*below, 1)
    els[1].position, els[1].color = 0.8, (*zenith, 1)
    e = els.new(0.5)
    e.color = (*horizon, 1)
    e2 = els.new(0.56)
    e2.color = tuple((h + z) / 2 for h, z in zip(horizon, zenith)) + (1,)
    # Generated coordinates in a world shader run 0..1 along the view
    # direction's components; Z = 0.5 is the horizon.
    links.new(sep.outputs["Z"], r.inputs["Fac"])
    sky = r.outputs["Color"]
    if sun_dir is not None:
        dot = nodes.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        norm = nodes.new("ShaderNodeVectorMath")
        norm.operation = "NORMALIZE"
        links.new(tc.outputs["Generated"], norm.inputs[0])
        # Generated is 0..1; recentre it on 0.
        sub = nodes.new("ShaderNodeVectorMath")
        sub.operation = "SUBTRACT"
        sub.inputs[1].default_value = (0.5, 0.5, 0.5)
        links.new(tc.outputs["Generated"], sub.inputs[0])
        links.new(sub.outputs[0], norm.inputs[0])
        links.new(norm.outputs[0], dot.inputs[0])
        dot.inputs[1].default_value = tuple(sun_dir)
        glow = nodes.new("ShaderNodeMath")
        glow.operation = "POWER"
        glow.inputs[1].default_value = 12.0
        clamp = nodes.new("ShaderNodeClamp")
        links.new(dot.outputs["Value"], clamp.inputs[0])
        links.new(clamp.outputs[0], glow.inputs[0])
        mix = nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "ADD"
        links.new(glow.outputs[0], mix.inputs["Factor"])
        links.new(sky, mix.inputs["A"])
        mix.inputs["B"].default_value = (*sun_glow, 1)
        sky = mix.outputs["Result"]
    links.new(sky, bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength


def spot(name, at, aim, energy, rgb=(1, 1, 1), size_deg=90, blend=0.85, soft=0.4):
    bpy.ops.object.light_add(type="SPOT", location=at)
    s = bpy.context.active_object
    s.name = name
    s.data.energy = energy
    s.data.color = rgb
    s.data.spot_size = math.radians(size_deg)
    s.data.spot_blend = blend
    s.data.shadow_soft_size = soft
    s.rotation_euler = (Vector(aim) - Vector(at)).to_track_quat("-Z", "Y").to_euler()
    return s


def point(name, at, energy, rgb=(1, 0.8, 0.6), radius=0.1):
    bpy.ops.object.light_add(type="POINT", location=at)
    p = bpy.context.active_object
    p.name = name
    p.data.energy = energy
    p.data.color = rgb
    p.data.shadow_soft_size = radius
    return p


# ---------------------------------------------------------------------------
# Cameras and export
# ---------------------------------------------------------------------------


def add_camera(i, cam):
    """cam: {"from": (X, Y, Z), "to": (X, Y, Z), "fov": f} in game units."""
    data = bpy.data.cameras.new(f"Room camera {i}")
    data.sensor_fit = "HORIZONTAL"
    data.sensor_width = 32.0
    data.lens = cam["fov"] / 10.0
    data.clip_start = 0.1
    data.clip_end = cam.get("clip_end", 400)
    ob = bpy.data.objects.new(f"Room camera {i}", data)
    bpy.context.scene.collection.objects.link(ob)
    eye = game_to_blender(cam["from"])
    ob.location = eye
    ob.rotation_euler = (game_to_blender(cam["to"]) - eye).to_track_quat("-Z", "Y").to_euler()
    return ob


def _cycles(samples, denoise, filter_width):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type != "CPU"
    scene.cycles.device = "GPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = denoise
    scene.cycles.filter_width = filter_width
    scene.render.resolution_x = 320
    scene.render.resolution_y = 240
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"


def _game_footprint(ob):
    """The object's world-space bounding box on the floor, in game units (X, Z)."""
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    xs = [p.x * UNITS for p in pts]
    zs = [p.y * UNITS for p in pts]
    return round(min(xs)), round(min(zs)), round(max(xs)), round(max(zs))


def _depth_material():
    """Emits view-space Z / 16 in game units as R * 256 + G (each / 255)."""
    m = bpy.data.materials.new("RE depth")
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.remove(nodes["Principled BSDF"])
    links.new(_depth_emission(nodes, links), nodes["Material Output"].inputs["Surface"])
    return m


def _depth_emission(nodes, links):
    """Nodes in a material that emit its view-space Z / 16 in game units as
    R * 256 + G (each / 255); returns the emission's shader output."""
    cam = nodes.new("ShaderNodeCameraData")
    scale = nodes.new("ShaderNodeMath")
    scale.operation = "MULTIPLY"
    scale.inputs[1].default_value = UNITS / 16.0
    links.new(cam.outputs["View Z Depth"], scale.inputs[0])
    hi = nodes.new("ShaderNodeMath")
    hi.operation = "DIVIDE"
    hi.inputs[1].default_value = 256.0
    links.new(scale.outputs[0], hi.inputs[0])
    hi_floor = nodes.new("ShaderNodeMath")
    hi_floor.operation = "FLOOR"
    links.new(hi.outputs[0], hi_floor.inputs[0])
    lo = nodes.new("ShaderNodeMath")
    lo.operation = "MODULO"
    lo.inputs[1].default_value = 256.0
    links.new(scale.outputs[0], lo.inputs[0])
    lo_floor = nodes.new("ShaderNodeMath")
    lo_floor.operation = "FLOOR"
    links.new(lo.outputs[0], lo_floor.inputs[0])
    r = nodes.new("ShaderNodeMath")
    r.operation = "DIVIDE"
    r.inputs[1].default_value = 255.0
    links.new(hi_floor.outputs[0], r.inputs[0])
    g = nodes.new("ShaderNodeMath")
    g.operation = "DIVIDE"
    g.inputs[1].default_value = 255.0
    links.new(lo_floor.outputs[0], g.inputs[0])
    rgb = nodes.new("ShaderNodeCombineColor")
    links.new(r.outputs[0], rgb.inputs[0])
    links.new(g.outputs[0], rgb.inputs[1])
    em = nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0
    links.new(rgb.outputs[0], em.inputs["Color"])
    return em.outputs["Emission"]


def _depth_settings():
    """One sample at the pixel centre, so no depth is blended across an edge; no light, no mist."""
    scene = bpy.context.scene
    for ob in scene.objects:
        if ob.type == "LIGHT" or ob.name == "Mist":
            ob.hide_render = True
    _cycles(1, False, 0.01)
    scene.cycles.max_bounces = 0
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Raw"
    scene.render.dither_intensity = 0.0


def _all_depth(cams, out_dir):
    """Every surface's depth, as cam<N>.zall.png: masks.ts works out from it
    and where she can stand what is in front of her (masks.ts
    occluders). A cut-out card (a leaf, a fern) emits its depth only where
    its alpha is. It rewrites the scene's materials, so it runs after every
    picture."""
    scene = bpy.context.scene
    plain = _depth_material()
    for m in list(bpy.data.materials):
        if not m.use_nodes or m is plain:
            continue
        nodes, links = m.node_tree.nodes, m.node_tree.links
        out = next((n for n in nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None)
        if out is None:
            continue
        clear = nodes.new("ShaderNodeBsdfTransparent")
        if out.inputs["Volume"].is_linked and not out.inputs["Surface"].is_linked:
            # Smoke, mist: a volume with no surface hides nothing she stands behind.
            for l in list(out.inputs["Volume"].links):
                links.remove(l)
            links.new(clear.outputs[0], out.inputs["Surface"])
            continue
        bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
        cut = nodes.new("ShaderNodeMixShader")
        alpha = bsdf.inputs["Alpha"] if bsdf is not None else None
        if alpha is not None and alpha.is_linked:
            links.new(alpha.links[0].from_socket, cut.inputs["Fac"])
        else:
            cut.inputs["Fac"].default_value = 1.0
        links.new(clear.outputs[0], cut.inputs[1])
        links.new(_depth_emission(nodes, links), cut.inputs[2])
        links.new(cut.outputs[0], out.inputs["Surface"])
        if out.inputs.get("Volume") is not None:
            for l in list(out.inputs["Volume"].links):
                links.remove(l)
    for ob in scene.objects:
        if ob.type == "MESH" and not ob.data.materials:
            ob.data.materials.append(plain)
    _depth_settings()
    for i, cam in enumerate(cams):
        scene.camera = cam
        scene.render.filepath = os.path.join(out_dir, f"cam{i}.zall.png")
        bpy.ops.render.render(write_still=True)


def _holdout_material():
    m = bpy.data.materials.new("RE holdout")
    m.use_nodes = True
    nodes = m.node_tree.nodes
    nodes.remove(nodes["Principled BSDF"])
    h = nodes.new("ShaderNodeHoldout")
    m.node_tree.links.new(h.outputs["Holdout"], nodes["Material Output"].inputs["Surface"])
    return m


def export(cameras, out_dir, samples=512, extra=None, anim=None, states=()):
    """Render every camera's background and foreground depth, and write room.json.

    anim: {"frames": N, "ticks": T, "set": f} makes the background move in the
    game (src/game/BgAnim.cpp). f(k) poses the scene for frame k of a loop of
    N; frame 0 is the background itself, frames 1 .. N - 1 are rendered as
    cam<N>.a<k>.png. The game shows each frame for T game frames (30 a second),
    so the loop should come back round to frame 0.

    states: [{"name", "bank", "bit", "set": f}] are changes the room's script
    makes, shown while FG_SCENARIO (bank 0) or FG_COMMON (bank 1) flag `bit`
    is set. f(True) poses the change, f(False) undoes it; rendered as
    cam<N>.s-<name>.png. Neither may move a mask() object: masks are cut from
    frame 0. A state may also have
      "motion": {"frames": F, "ticks": T}: the change as it happens, f(k / F)
        for k = 1 .. F - 1 rendered as cam<N>.m-<name>.<k>.png, for the
        state's "cameras" (default all);
      "loop": True or g: the changed room through the anim's loop, frames
        1 .. N - 1 as cam<N>.s-<name>.a<k>.png, g(k) posed with each.

    RE1_STATES=1 renders the states alone, over backgrounds already rendered
    from the same scene.
    """
    os.makedirs(out_dir, exist_ok=True)
    scene = bpy.context.scene
    cams = [add_camera(i, c) for i, c in enumerate(cameras)]
    # RE1_PREVIEW=1: the backgrounds only, quickly, to judge a scene.
    preview = bool(os.environ.get("RE1_PREVIEW"))
    if preview:
        samples = min(samples, 96)
    if anim:
        anim["set"](0)
    meta = {}
    if anim:
        meta["anim"] = {"frames": anim["frames"], "ticks": anim["ticks"]}
    if states:
        meta["states"] = [{k: st[k] for k in ("name", "bank", "bit", "motion", "cameras") if k in st} | ({"loop": True} if st.get("loop") else {}) for st in states]
    states_only = bool(os.environ.get("RE1_STATES"))
    # RE1_ZALL=1: every surface's depth alone (cam<N>.zall.png), over a room
    # already rendered from the same scene.
    zall_only = bool(os.environ.get("RE1_ZALL"))

    walls = []
    for ob in scene.objects:
        shape = ob.get("re_wall")
        if shape and ob.type == "MESH":
            x0, z0, x1, z1 = _game_footprint(ob)
            walls.append({"shape": shape, "x0": x0, "z0": z0, "x1": x1, "z1": z1, "name": ob.name})
    with open(os.path.join(out_dir, "room.json"), "w") as f:
        json.dump({"cameras": cameras, "walls": walls, **meta, **(extra or {})}, f, indent=1)
    # RE1_RECORDS=1: the room's records alone (doors, checks, items), no
    # pictures, for a change to what the scene records rather than its look.
    if os.environ.get("RE1_RECORDS"):
        return

    # Backgrounds.
    _cycles(samples, True, 1.0)
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.film_transparent = False
    scene.cycles.seed = 0  # every render the same noise, so still parts match frame 0
    scene.cycles.use_animated_seed = False

    def render_all(suffix, only=None):
        for i, cam in enumerate(cams):
            if only is not None and i not in only:
                continue
            scene.camera = cam
            scene.render.filepath = os.path.join(out_dir, f"cam{i}{suffix}.png")
            bpy.ops.render.render(write_still=True)

    if not states_only and not zall_only:
        render_all("")
        if anim and not preview:
            for k in range(1, anim["frames"]):
                anim["set"](k)
                render_all(f".a{k}")
            anim["set"](0)
    for st in (states if not preview or states_only else ()) if not zall_only else ():
        name, only = st["name"], st.get("cameras")
        st["set"](True)
        render_all(f".s-{name}")
        loop = st.get("loop")
        if loop and anim:
            for k in range(1, anim["frames"]):
                anim["set"](k)
                if callable(loop):
                    loop(k)
                render_all(f".s-{name}.a{k}", only)
            anim["set"](0)
            if callable(loop):
                loop(0)
        motion = st.get("motion")
        if motion:
            for k in range(1, motion["frames"]):
                st["set"](k / motion["frames"])
                render_all(f".m-{name}.{k}", only)
        st["set"](False)
    if states_only:
        return

    # Foreground depth: tagged objects emit their depth, the rest hold out, so
    # they still hide what is behind them.
    masked = [ob for ob in scene.objects if ob.get("re_mask") and ob.type == "MESH"]
    # Every surface's depth first: the tagged pass below takes the materials away.
    _all_depth(cams, out_dir)
    if zall_only:
        return
    depth_m = _depth_material()
    hold_m = _holdout_material()
    for ob in scene.objects:
        if ob.type != "MESH":
            continue
        ob.data.materials.clear()
        ob.data.materials.append(depth_m if ob in masked else hold_m)
        for poly in ob.data.polygons:
            poly.material_index = 0
    _depth_settings()
    for i, cam in enumerate(cams):
        scene.camera = cam
        scene.render.filepath = os.path.join(out_dir, f"cam{i}.depth.png")
        bpy.ops.render.render(write_still=True)


def export_walk(pose, frames, out_dir, samples=128, ticks=2, step_ticks=16, light=None):
    """Render the walk between two rooms (src/game/PathWalk.cpp): `frames`
    pictures of 320x240, frame k seen from pose(k) -> (eye, look-at) in
    metres. The game shows each for `ticks` game frames (30 a second) and
    plays a footstep every `step_ticks`. `light`, if given, is moved to
    pose's eye each frame, a lamp that walks with her. Writes walk.NNNN.png
    and walk.json beside them."""
    os.makedirs(out_dir, exist_ok=True)
    scene = bpy.context.scene
    data = bpy.data.cameras.new("Walk camera")
    data.sensor_fit = "HORIZONTAL"
    data.sensor_width = 32.0
    data.lens = 22.0
    data.clip_start = 0.05
    data.clip_end = 200
    cam = bpy.data.objects.new("Walk camera", data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    if os.environ.get("RE1_PREVIEW"):
        samples = min(samples, 48)
        frames_to_render = [0, frames // 2, frames - 1]
    else:
        frames_to_render = range(frames)
    _cycles(samples, True, 1.0)
    scene.cycles.seed = 0
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    for k in frames_to_render:
        eye, at = pose(k)
        cam.location = Vector(eye)
        cam.rotation_euler = (Vector(at) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        if light is not None:
            # Just above and behind her eyes, down onto the path ahead.
            ahead = Vector(at) - Vector(eye)
            ahead.z = 0
            ahead.normalize()
            light.location = Vector(eye) + Vector((0, 0, 0.5)) - ahead * 0.5
            target = Vector(eye) + ahead * 2.5 - Vector((0, 0, 1.4))
            light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(out_dir, f"walk.{k:04d}.png")
        bpy.ops.render.render(write_still=True)
    with open(os.path.join(out_dir, "walk.json"), "w") as f:
        json.dump({"frames": frames, "ticks": ticks, "stepTicks": step_ticks}, f)
