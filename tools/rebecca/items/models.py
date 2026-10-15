"""Her key items, modelled once and used three ways:

- the inventory icon, as RE1 draws its own: the item turned corner-on, lit
  warm from the top left with a cool fill, on nothing (film transparent), so
  sheet.ts can lay it over the sheet's navy ground. icons/<step>.png, 160 x
  120 (four times the sheet's 40 x 30);
- the model she turns over when she examines it (an ITEM_M2 .IVM) and the
  one lying in the room until she takes it (a TMD in the room): the item's
  triangles, each corner's normal and texture point, and its colour baked
  into one 256 x 256 texture. models/<step>.json and models/<step>.png, which
  tmd.ts turns into the game's TMD and TIM.

Sizes are the real thing's, in metres, the item lying as it lies on a floor
(its lowest point at z = 0, centred on the origin).

Run by items/render-items.ts on jellybingus:
  blender -b --factory-startup --python models.py
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402

OUT = os.environ.get("RE1_OUT", os.path.dirname(os.path.abspath(__file__)))
TEXTURE = 256
# The examined model's triangles: RE1's own run 100 to 500. The one lying
# in the room is cut down further: RE1's own are 4 to 50.
VIEW_TRIS = 480
PICKUP_TRIS = 120


# ---------------------------------------------------------------------------
# Materials: colour that survives baking (no metallic black), wear in the colour itself
# ---------------------------------------------------------------------------


def _noise(nodes, links, scale, detail=6, rough=0.6, coord="Object"):
    n = nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    tc = nodes.new("ShaderNodeTexCoord")
    links.new(tc.outputs[coord], n.inputs["Vector"])
    return n


def painted(name, paint, metal, wear=0.25, scale=30, rough=0.5, metallic=0.0, grime=(0.05, 0.04, 0.03)):
    """Paint over bare metal, chipped through where noise falls under
    `wear`, and dirt gathered in patches."""
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    chips = _noise(nodes, links, scale, 8, 0.65)
    paint_ramp = reb.ramp(nodes, links, chips.outputs["Fac"], [(0.0, metal), (wear + 0.24, metal), (wear + 0.27, tuple(c * 0.75 for c in paint)), (0.75, paint), (1.0, tuple(min(1, c * 1.15) for c in paint))])
    dirt = _noise(nodes, links, scale / 6, 4, 0.5)
    dirt_ramp = reb.ramp(nodes, links, dirt.outputs["Fac"], [(0.0, (1, 1, 1)), (0.45, (1, 1, 1)), (0.7, grime)])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.6
    links.new(paint_ramp.outputs["Color"], mix.inputs[6])
    links.new(dirt_ramp.outputs["Color"], mix.inputs[7])
    links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    reb.bumped(nodes, links, bsdf, chips.outputs["Fac"], 0.15, 0.002)
    return m


def steel(name, rgb=(0.32, 0.31, 0.3), rust=0.2, scale=60):
    """Worked steel: grey with lighter scratches and rust in the hollows."""
    return painted(name, rgb, (0.2, 0.08, 0.03), wear=rust - 0.24, scale=scale, rough=0.4, metallic=0.6, grime=(0.12, 0.06, 0.03))


def plain(name, rgb, rough=0.6, scale=40, vary=0.12):
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Roughness"].default_value = rough
    n = _noise(nodes, links, scale, 6, 0.6)
    reb.ramp(nodes, links, n.outputs["Fac"], [(0.2, tuple(c * (1 - vary) for c in rgb)), (0.8, tuple(min(1, c * (1 + vary)) for c in rgb))])
    links.new(nodes[-1].outputs["Color"], bsdf.inputs["Base Color"])
    return m


# ---------------------------------------------------------------------------
# Shapes
# ---------------------------------------------------------------------------


def _link(name, bm, mat, smooth=40):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if mat is not None:
        me.materials.append(mat)
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    if smooth:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth))
    return ob


def bevel(ob, width, segments=2, angle=40):
    mod = ob.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(angle)
    mod.harden_normals = False
    return ob


def slab(name, mat, outline, thick, at=(0, 0, 0), rot=(0, 0, 0), holes=(), bev=0.0):
    """A flat part cut from plate: `outline` (x, y) points, `thick` deep
    along z, centred on z = 0, with round `holes` ((x, y, r), ...) through it."""
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, -thick / 2)) for x, y in outline]
    hi = [bm.verts.new((x, y, thick / 2)) for x, y in outline]
    bm.faces.new(lo[::-1])
    bm.faces.new(hi)
    n = len(outline)
    for i in range(n):
        bm.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _link(name, bm, mat)
    for i, (hx, hy, r) in enumerate(holes):
        cut = reb.prim("cyl", f"{name} hole {i}", None, (hx, hy, 0), (2 * r, 2 * r, thick * 3), segments=16)
        b = ob.modifiers.new(f"Hole {i}", "BOOLEAN")
        b.operation = "DIFFERENCE"
        b.object = cut
        cut.hide_render = cut.hide_viewport = True
    if bev:
        bevel(ob, bev)
    ob.location = at
    ob.rotation_euler = rot
    return ob


def tube(name, mat, points, r, segments=12, profile=None, caps=True):
    """A tube of radius r along `points`, or of the 2D `profile` (a
    hexagon for a bar) when given."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    # A NURBS through the points' hull, pinned to both ends: smooth bends.
    sp = cu.splines.new("NURBS")
    sp.points.add(len(points) - 1)
    for p, q in zip(sp.points, points):
        p.co = (*q, 1)
    sp.order_u = min(3, len(points))
    sp.use_endpoint_u = True
    sp.resolution_u = 6
    if profile:
        pc = bpy.data.curves.new(name + " profile", "CURVE")
        ps = pc.splines.new("POLY")
        ps.points.add(len(profile) - 1)
        for p, q in zip(ps.points, profile):
            p.co = (q[0], q[1], 0, 1)
        ps.use_cyclic_u = True
        po = bpy.data.objects.new(name + " profile", pc)
        bpy.context.scene.collection.objects.link(po)
        cu.bevel_mode = "OBJECT"
        cu.bevel_object = po
    else:
        cu.bevel_depth = r
        cu.bevel_resolution = max(1, segments // 4 - 1)
    cu.use_fill_caps = caps
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def arc(c, r, a0, a1, n, plane="xz"):
    out = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        u, v = r * math.cos(a), r * math.sin(a)
        out.append((c[0] + u, c[1], c[2] + v) if plane == "xz" else (c[0] + u, c[1] + v, c[2]))
    return out


def words(text, size, mat, at, rot, extrude=0.0004):
    cu = bpy.data.curves.new(text, "FONT")
    cu.body = text
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.extrude = extrude
    ob = bpy.data.objects.new(text, cu)
    ob.location = at
    ob.rotation_euler = rot
    ob.data.materials.append(mat)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# ---------------------------------------------------------------------------
# The items
# ---------------------------------------------------------------------------


def jerrycan(label):
    """A 20 litre steel jerrycan, standing: the pressed X on each face, the
    weld bead round its middle, three handles and the spout with its clamp.
    `label` stencils DIESEL on its side."""
    W, D, H = 0.345, 0.165, 0.47
    red = painted("Can paint", (0.36, 0.05, 0.03), (0.22, 0.21, 0.2), wear=0.12, scale=24)
    body = reb.prim("cube", "Can body", red, (0, 0, H / 2), (W, D, H))
    bevel(body, 0.03, 3)
    # The pressed X: two ridges a side, a frame round them.
    for side in (-1, 1):
        y = side * (D / 2 + 0.002)
        for s in (-1, 1):
            a = math.atan2(H - 0.12, W - 0.1)
            r = reb.prim("cube", "Can X", red, (0, y, H / 2), (math.hypot(W - 0.1, H - 0.12), 0.008, 0.022), rot=(0, s * a, 0))
            bevel(r, 0.004)
        for (x, z, w, h) in ((0, 0.055, W - 0.06, 0.018), (0, H - 0.055, W - 0.06, 0.018), (-W / 2 + 0.035, H / 2, 0.018, H - 0.12), (W / 2 - 0.035, H / 2, 0.018, H - 0.12)):
            bevel(reb.prim("cube", "Can frame", red, (x, y, z), (w, 0.007, h)), 0.003)
    bevel(reb.prim("cube", "Weld bead", red, (0, 0, H / 2), (W + 0.008, D + 0.008, 0.012)), 0.005)
    # Three handles, the outer two to the corners, as on the real can.
    for x in (-0.085, 0.0, 0.085):
        pts = [(x, -0.025, H - 0.005), (x, -0.028, H + 0.035), (x, -0.012, H + 0.05), (x, 0.012, H + 0.05), (x, 0.028, H + 0.035), (x, 0.025, H - 0.005)]
        tube("Handle", red, [(p[0], p[1], p[2]) for p in pts], 0.009)
    bevel(reb.prim("cube", "Handle bar", red, (0, 0, H + 0.05), (0.2, 0.026, 0.012)), 0.005)
    # Spout at the front corner, its cap and the clamp lever.
    tin = steel("Spout steel", (0.4, 0.39, 0.36))
    reb.prim("cyl", "Spout neck", tin, (W / 2 - 0.06, 0, H + 0.012), (0.055, 0.055, 0.03), segments=20)
    reb.prim("cyl", "Spout cap", red, (W / 2 - 0.06, 0, H + 0.035), (0.068, 0.068, 0.022), segments=20)
    bevel(reb.prim("cube", "Clamp lever", tin, (W / 2 - 0.105, 0, H + 0.052), (0.08, 0.016, 0.01), rot=(0, 0.35, 0)), 0.003)
    if label:
        white = plain("Stencil white", (0.62, 0.6, 0.55), 0.6, vary=0.15)
        words("DIESEL", 0.055, white, (0, -D / 2 - 0.0045, H * 0.62), (math.pi / 2, 0, 0))
        words("DIESEL", 0.055, white, (0, D / 2 + 0.0045, H * 0.62), (math.pi / 2, 0, math.pi))


def cutters():
    """Bolt cutters, 600 mm: tube handles with ribbed rubber grips, the
    compound head's cheek plates and pivot bolts, the jaws a bite apart."""
    st = steel("Cutter steel", (0.22, 0.23, 0.25), rust=0.15)
    blade = steel("Jaw steel", (0.42, 0.42, 0.42), rust=0.05, scale=90)
    rubber = plain("Grip rubber", (0.32, 0.03, 0.02), 0.85, vary=0.2)
    T = 0.016
    for side in (-1, 1):
        # Handle: a tube from the head out, splaying a little.
        tube("Handle", st, [(side * 0.012, 0, 0.16), (side * 0.02, 0, 0.0), (side * 0.04, 0, -0.32)], 0.011)
        # Grip: ribbed, ending in a rounded cap.
        n = 12
        pts = [(side * (0.02 + (0.04 - 0.02) * (k / n)), 0, -0.17 - 0.15 * k / n) for k in range(n + 1)]
        for k in range(n):
            reb.prim("cyl", "Grip rib", rubber, ((pts[k][0] + pts[k + 1][0]) / 2, 0, (pts[k][2] + pts[k + 1][2]) / 2), (0.031 if k % 2 else 0.028,) * 2 + (0.0128,), rot=(0, -side * 0.065, 0), segments=14)
        reb.prim("sphere", "Grip end", rubber, (side * 0.041, 0, -0.325), (0.03, 0.03, 0.025), segments=14)
        # Cheek plate: the head's lever, a flat plate with its two bolts.
        plate = [(-0.02, 0.0), (0.024, 0.0), (0.03, 0.06), (0.022, 0.1), (-0.004, 0.11), (-0.026, 0.07)]
        p = slab("Cheek plate", st, [(side * x, y) for x, y in (plate if side > 0 else plate[::-1])], 0.006, at=(0, 0, 0.14), rot=(math.pi / 2, 0, 0))
        p.location.y = side * 0.012
        bevel(p, 0.0015)
        # Jaw: a curved blade meeting its twin at the tip.
        jaw = [(0.0, 0.0), (side * 0.024, 0.0), (side * 0.022, 0.05), (side * 0.012, 0.085), (side * 0.003, 0.095), (side * 0.0015, 0.05)]
        j = slab("Jaw", blade, jaw if side > 0 else jaw[::-1], T, at=(side * 0.0015, 0, 0.215), rot=(math.pi / 2, 0, 0))
        bevel(j, 0.002)
        for z in (0.16, 0.22):
            for y in (-1, 1):
                reb.prim("cyl", "Bolt", st, (side * 0.012, y * 0.017, z), (0.011, 0.011, 0.006), rot=(math.pi / 2, 0, 0), segments=10)
    reb.prim("cyl", "Pivot", st, (0, 0, 0.13), (0.016, 0.016, 0.03), rot=(math.pi / 2, 0, 0), segments=12)


def cog():
    """A drive cog: an 18-tooth spur gear with its hub boss, a keyed bore
    and five lightening holes, black with grease."""
    st = steel("Cog steel", (0.2, 0.2, 0.19), rust=0.32, scale=50)
    teeth, R, root, face = 18, 0.12, 0.103, 0.03
    outline = []
    for k in range(teeth):
        a = 2 * math.pi * k / teeth
        p = 2 * math.pi / teeth
        for frac, rad in ((0.0, root), (0.18, root), (0.32, R), (0.52, R), (0.66, root)):
            b = a + frac * p
            outline.append((rad * math.cos(b), rad * math.sin(b)))
    holes = [(0.068 * math.cos(2 * math.pi * i / 5), 0.068 * math.sin(2 * math.pi * i / 5), 0.016) for i in range(5)]
    g = slab("Gear", st, outline, face, holes=holes, bev=0.0015)
    boss = reb.prim("cyl", "Hub boss", st, (0, 0, 0), (0.07, 0.07, face + 0.024), segments=32)
    bevel(boss, 0.003)
    bore = reb.prim("cyl", "Bore", None, (0, 0, 0), (0.03, 0.03, 0.2), segments=20)
    key = reb.prim("cube", "Keyway", None, (0.016, 0, 0), (0.012, 0.009, 0.2))
    for c in (bore, key):
        b = boss.modifiers.new(c.name, "BOOLEAN")
        b.operation = "DIFFERENCE"
        b.object = c
        c.hide_render = c.hide_viewport = True
        b2 = g.modifiers.new(c.name, "BOOLEAN")
        b2.operation = "DIFFERENCE"
        b2.object = c


def dynamite():
    """Three sticks of dynamite taped together, waxed red paper with its
    printing, a blasting cap in the middle one and its fuse curling out."""
    paper = painted("Stick paper", (0.48, 0.07, 0.04), (0.55, 0.45, 0.3), wear=0.05, scale=35, rough=0.7)
    end = plain("Crimped end", (0.6, 0.53, 0.4), 0.8)
    tape = plain("Tape", (0.04, 0.04, 0.045), 0.35, vary=0.3)
    L = 0.2
    for dx, dz in ((-0.016, 0.0), (0.016, 0.0), (0.0, 0.027)):
        s = reb.prim("cyl", "Stick", paper, (dx, 0, dz + 0.016), (0.031, 0.031, L), rot=(math.pi / 2, 0, 0), segments=18)
        bevel(s, 0.002)
        for y in (-L / 2, L / 2):
            reb.prim("cyl", "Stick end", end, (dx, y, dz + 0.016), (0.026, 0.026, 0.004), rot=(math.pi / 2, 0, 0), segments=18)
    for y in (-0.055, 0.055):
        reb.prim("cyl", "Tape", tape, (0, y, 0.025), (0.072, 0.07, 0.022), rot=(math.pi / 2, 0, 0), segments=24)
    cap = steel("Cap copper", (0.45, 0.25, 0.1), rust=0.1)
    reb.prim("cyl", "Blasting cap", cap, (0, L / 2 + 0.012, 0.043), (0.008, 0.008, 0.03), rot=(math.pi / 2, 0, 0), segments=10)
    fuse = [(0, L / 2 + 0.025, 0.043), (0.01, L / 2 + 0.05, 0.05), (0.03, L / 2 + 0.07, 0.04), (0.05, L / 2 + 0.07, 0.02), (0.06, L / 2 + 0.05, 0.008), (0.075, L / 2 + 0.03, 0.005)]
    tube("Fuse", plain("Fuse cord", (0.25, 0.2, 0.12), 0.9), fuse, 0.0035, segments=8)


def fuses():
    """Two cartridge fuses, one across the other: fibre bodies with their
    printed bands, brass ferrules and knife-blade contacts."""
    fibre = plain("Fuse fibre", (0.42, 0.33, 0.2), 0.7)
    brass = steel("Brass", (0.55, 0.4, 0.14), rust=0.05, scale=80)
    band = plain("Rating band", (0.06, 0.06, 0.06), 0.6, vary=0.0)
    for i, (x, y, yaw, z) in enumerate(((0.0, 0.0, 0.0, 0.0), (0.012, 0.0, 0.55, 0.026))):
        rot = Euler((0, math.pi / 2, yaw))
        def at(t, h=0.0):
            v = Vector((t, 0, 0))
            v.rotate(Euler((0, 0, yaw)))
            return (x + v.x, y + v.y, z + 0.013 + h)
        reb.prim("cyl", "Fuse body", fibre, at(0), (0.026, 0.026, 0.07), rot=rot, segments=20)
        reb.prim("cyl", "Rating band", band, at(0), (0.0265, 0.0265, 0.018), rot=rot, segments=20)
        for e in (-1, 1):
            f = reb.prim("cyl", "Ferrule", brass, at(e * 0.04), (0.029, 0.029, 0.018), rot=rot, segments=20)
            bevel(f, 0.0015)
            bevel(reb.prim("cube", "Blade", brass, at(e * 0.058), (0.03, 0.0035, 0.018), rot=(0, 0, yaw)), 0.001)
        words("60A", 0.009, plain("Rating print", (0.6, 0.58, 0.5), 0.6, vary=0.0), at(0, 0.0134), (0, 0, yaw))


def crowbar():
    """A 600 mm wrecking bar: hexagonal steel bent into a gooseneck at one
    end with a split claw, the other end a flattened chisel; red paint worn
    back to steel at both ends."""
    paint = painted("Bar paint", (0.36, 0.04, 0.03), (0.17, 0.17, 0.18), wear=0.18, scale=22)
    hexa = [(0.0095 * math.cos(math.pi / 3 * k), 0.0095 * math.sin(math.pi / 3 * k)) for k in range(6)]
    pts = [(-0.3, 0, 0.0095), (0.17, 0, 0.0095)]
    pts += arc((0.17, 0, 0.065), 0.0555, -math.pi / 2, math.pi * 0.35, 10)[1:]
    tube("Bar", paint, pts, 0.0095, profile=hexa)
    # The chisel end: flattened and bent up a few degrees.
    st = steel("Bar steel", (0.2, 0.2, 0.21), rust=0.2)
    slab("Chisel", st, [(-0.05, -0.0095), (0.0, -0.0095), (0.0, 0.0095), (-0.05, 0.0085), (-0.06, 0.006), (-0.06, -0.006)], 0.008, at=(-0.3, 0, 0.012), rot=(0, -0.12, 0), bev=0.0015)
    # The claw: two tines either side of the nail slot, curling back.
    tip = Vector(pts[-1])
    for side in (-1, 1):
        tube("Claw tine", st, [tuple(tip + Vector((0.0, side * 0.0045, 0.0))), tuple(tip + Vector((-0.016, side * 0.0055, 0.012))), tuple(tip + Vector((-0.04, side * 0.006, 0.014)))], 0.0045, segments=8)


# Each item: its file name (the plan step that gives it, items.ts), the
# model, how it is laid down on a floor as built, and how the icon turns it
# corner-on (both XYZ Euler angles, radians).
ITEMS = [
    ("cutters", cutters, (-math.pi / 2, 0, math.pi / 2), (1.2, -0.5, 0.0)),
    ("cog", cog, (0, 0, 0), (1.2, 0.0, 0.5)),
    ("jerrycan", lambda: jerrycan(False), (0, 0, 0), (0.1, 0.0, -0.55)),
    ("fuel", lambda: jerrycan(True), (0, 0, 0), (0.1, 0.0, -0.55)),
    ("dynamite", dynamite, (0, 0, 0), (0.5, 0.0, 0.7)),
    ("fuses", fuses, (0, 0, 0), (0.6, 0.0, 0.5)),
    ("crowbar", crowbar, (0, 0, 0), (0.9, -0.45, 0.0)),
]


# ---------------------------------------------------------------------------
# One object, lying on the floor
# ---------------------------------------------------------------------------


def solid(lie):
    """Every part made real (curves, text, modifiers) and joined into one
    mesh, turned by `lie`, its lowest point on z = 0, centred on the origin."""
    scene = bpy.context.scene
    for ob in list(scene.objects):
        if ob.type in ("CURVE", "FONT") and ob.name.endswith("profile"):
            ob.hide_render = ob.hide_viewport = True
    dg = bpy.context.evaluated_depsgraph_get()
    parts = []
    for ob in list(scene.objects):
        if ob.type not in ("MESH", "CURVE", "FONT") or ob.hide_render:
            continue
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), depsgraph=dg)
        me.transform(Euler(lie).to_matrix().to_4x4() @ ob.matrix_world)
        parts.append((me, ob))
    for ob in list(scene.objects):
        if ob.type in ("MESH", "CURVE", "FONT"):
            bpy.data.objects.remove(ob)
    bm = bmesh.new()
    mats = []
    for me, _ in parts:
        offset = len(mats)
        mats += list(me.materials)
        for p in me.polygons:
            p.material_index += offset
        bm.from_mesh(me)
    pts = [v.co for v in bm.verts]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    bmesh.ops.translate(bm, verts=bm.verts, vec=-Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)))
    me = bpy.data.meshes.new("Item")
    bm.to_mesh(me)
    bm.free()
    # A boolean's cutter leaves an empty slot behind: the faces it cut take the part's colour.
    for m in mats:
        me.materials.append(m or next(x for x in mats if x))
    ob = bpy.data.objects.new("Item", me)
    scene.collection.objects.link(ob)
    return ob


# ---------------------------------------------------------------------------
# The icon
# ---------------------------------------------------------------------------


def stage():
    """Camera, lights and render settings shared by every icon."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64
    scene.render.resolution_x, scene.render.resolution_y = 160, 120
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    cam = bpy.data.objects.new("Icon camera", bpy.data.cameras.new("Icon camera"))
    cam.data.type = "ORTHO"
    cam.location = (0, -3, 0)
    cam.rotation_euler = (math.pi / 2, 0, 0)
    scene.collection.objects.link(cam)
    scene.camera = cam
    key = bpy.data.objects.new("Key", bpy.data.lights.new("Key", "SUN"))
    key.data.energy = 4.0
    key.data.color = (1.0, 0.93, 0.82)
    key.rotation_euler = (math.radians(50), math.radians(-35), math.radians(-30))
    scene.collection.objects.link(key)
    fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", "SUN"))
    fill.data.energy = 1.2
    fill.data.color = (0.6, 0.7, 1.0)
    fill.rotation_euler = (math.radians(70), math.radians(40), math.radians(150))
    scene.collection.objects.link(fill)
    scene.world = bpy.data.worlds.new("Icon world")
    scene.world.use_nodes = True
    # Unseen (the film is transparent), but metal reflects it: dark, and steel renders black.
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.37, 0.45, 1)
    return cam


def icon(ob, turn, path):
    """Turn the item corner-on to the camera and frame it with a small margin, as RE1's icons fill their cells."""
    cam = stage()
    ob.rotation_euler = turn
    bpy.context.view_layer.update()
    pts = [ob.matrix_world @ v.co for v in ob.data.vertices]
    xs, zs = [p.x for p in pts], [p.z for p in pts]
    cam.location = ((min(xs) + max(xs)) / 2, -3, (min(zs) + max(zs)) / 2)
    cam.data.ortho_scale = max(max(xs) - min(xs), (max(zs) - min(zs)) * 4 / 3) * 1.12
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    ob.rotation_euler = (0, 0, 0)
    for o in list(bpy.context.scene.objects):
        if o.type in ("CAMERA", "LIGHT"):
            bpy.data.objects.remove(o)


# ---------------------------------------------------------------------------
# The game's model: few triangles, one baked texture
# ---------------------------------------------------------------------------


def _bake(kind, image):
    """Bake the full item (selected) onto its cut-down copy (active)."""
    bake = bpy.context.scene.render.bake
    bake.margin = 4
    bake.use_selected_to_active = True
    bake.cage_extrusion = 0.012
    bake.max_ray_distance = 0.04
    bpy.context.active_object.data.materials[0].node_tree.nodes["Target"].image = image
    bpy.ops.object.bake(type=kind, use_clear=True)


def _albedo_as_emission(ob):
    """Bake colour through an emission shader: a metal's diffuse colour bakes black."""
    for m in ob.data.materials:
        nodes, links = m.node_tree.nodes, m.node_tree.links
        bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
        out = next(n for n in nodes if n.type == "OUTPUT_MATERIAL")
        em = nodes.new("ShaderNodeEmission")
        base = bsdf.inputs["Base Color"]
        if base.is_linked:
            links.new(base.links[0].from_socket, em.inputs["Color"])
        else:
            em.inputs["Color"].default_value = base.default_value
        links.new(em.outputs["Emission"], out.inputs["Surface"])


def game_model(ob, step):
    """Cut a copy of the item down to VIEW_TRIS triangles, unwrap it, bake
    the full item's colour times its ambient occlusion onto it, and write
    models/<step>.json and .png."""
    scene = bpy.context.scene
    low = ob.copy()
    low.data = ob.data.copy()
    low.name = "Game model"
    scene.collection.objects.link(low)
    bpy.context.view_layer.objects.active = low
    for o in scene.objects:
        o.select_set(o == low)
    bpy.ops.object.modifier_apply(modifier=low.modifiers.new("Triangulate", "TRIANGULATE").name)
    if len(low.data.polygons) > VIEW_TRIS:
        dec = low.modifiers.new("Decimate", "DECIMATE")
        dec.ratio = VIEW_TRIS / len(low.data.polygons)
        dec.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=dec.name)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.02, area_weight=0.6)
    bpy.ops.object.mode_set(mode="OBJECT")
    target = bpy.data.materials.new("Baked")
    target.use_nodes = True
    node = target.node_tree.nodes.new("ShaderNodeTexImage")
    node.name = "Target"
    target.node_tree.nodes.active = node
    low.data.materials.clear()
    low.data.materials.append(target)

    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64
    ob.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    colour = bpy.data.images.new("Colour", TEXTURE, TEXTURE)
    ao = bpy.data.images.new("Occlusion", TEXTURE, TEXTURE)
    _bake("AO", ao)
    _albedo_as_emission(ob)
    _bake("EMIT", colour)
    c = list(colour.pixels)
    a = list(ao.pixels)
    for i in range(0, len(c), 4):
        k = 0.45 + 0.55 * a[i]
        c[i], c[i + 1], c[i + 2], c[i + 3] = c[i] * k, c[i + 1] * k, c[i + 2] * k, 1.0
    colour.pixels = c
    colour.filepath_raw = os.path.join(OUT, "models", f"{step}.png")
    colour.file_format = "PNG"
    colour.save()

    pickup = low.copy()
    pickup.data = low.data.copy()
    scene.collection.objects.link(pickup)
    for o in scene.objects:
        o.select_set(o == pickup)
    bpy.context.view_layer.objects.active = pickup
    if len(pickup.data.polygons) > PICKUP_TRIS:
        dec = pickup.modifiers.new("Decimate", "DECIMATE")
        dec.ratio = PICKUP_TRIS / len(pickup.data.polygons)
        dec.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=dec.name)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    out = {"step": step, "texture": TEXTURE, "view": _triangles(low.data), "pickup": _triangles(pickup.data)}
    with open(os.path.join(OUT, "models", f"{step}.json"), "w") as f:
        json.dump(out, f)
    print(f"[items] {step}: {len(out['view'])} triangles, {len(out['pickup'])} lying in the room", flush=True)


def _triangles(me):
    """Each triangle's corners: position, normal, texture point."""
    uv = me.uv_layers.active.data
    normals = me.corner_normals
    return [[[[round(x, 5) for x in me.vertices[me.loops[li].vertex_index].co], [round(x, 4) for x in normals[li].vector], [round(x, 5) for x in uv[li].uv]]
             for li in p.loop_indices] for p in me.polygons]


def main():
    os.makedirs(os.path.join(OUT, "icons"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "models"), exist_ok=True)
    only = os.environ.get("RE1_ITEMS", "").split(",") if os.environ.get("RE1_ITEMS") else None
    for step, build, lie, turn in ITEMS:
        if only and step not in only:
            continue
        reb.clear_scene()
        build()
        ob = solid(lie)
        icon(ob, turn, os.path.join(OUT, "icons", f"{step}.png"))
        game_model(ob, step)


main()
