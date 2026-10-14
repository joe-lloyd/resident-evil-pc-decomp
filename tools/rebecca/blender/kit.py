"""Set dressing for Rebecca's rooms: a Room that collects what the game needs
(floor, cameras, doors, things to check), the dead and what they left, and
the small movements every scene has. Builds on reb.py; run inside Blender.

A room's scene script, in metres with Blender's axes (x east, y south in the
game's Z, z up):

    import reb, kit
    room = kit.Room(bounds=(1.0, 1.0, 15.0, 12.0))     # x0, y0, x1, y1 of the walkable floor
    room.camera((2, 2, 3), (8, 7, 0.5), note="from the gate, at the bunkhouse")
    room.door("camp-yard", (14.2, 5.0, 15.0, 7.0), arrive=(13.6, 6.0), face=(-1, 0))
    room.check((6, 3, 7, 4), "A boot. The foot is still in it.")
    room.entry = "Someone has dragged a body through here."
    ... geometry, lights ...
    anim = kit.Anim(16)
    anim.flicker(lamp_light, lamp_mat)
    anim.flies((6.5, 3.5, 0.4))
    room.export(anim)

A door is where she leaves (`zone`) and, for the way back in, where she
stands and which way she faces when she arrives from that neighbour. The
generator (day/scripts.ts) pairs each door with the neighbour's door back.
Outdoor-to-outdoor doors walk (the dark path); doors into or out of a
building open, and are used with the action button.
"""
import math
import os
import random

import bpy
from mathutils import Matrix, Vector, noise

import reb

OUT = os.environ.get("RE1_OUT", "renders")


def G(x, y, z=0.0):
    """A point in metres (x, y on the floor, z up) as game units."""
    return (reb.g(x), -reb.g(z), reb.g(y))


def angle(face):
    """A facing (dx, dy) on the floor as the game's angle: 0 east (+x), 1024 north (-y)."""
    a = math.degrees(math.atan2(-face[1], face[0])) % 360
    return round(a / 360 * 4096) % 4096


# ---------------------------------------------------------------------------
# The room
# ---------------------------------------------------------------------------


class Room:
    def __init__(self, bounds, inside=False):
        self.bounds = bounds
        self.inside = inside
        self.cameras = []
        self.notes = []
        self.doors = []
        self.checks = []
        self.voids = []
        self.entry = None

    def camera(self, eye, look, fov=190, note=""):
        self.cameras.append({"from": G(*eye), "to": G(*look), "fov": fov})
        self.notes.append(note)

    def door(self, to, zone, arrive, face, walk=None, touch=None):
        """`to` is the neighbour's slug. walk: the dark-path walk (default for an
        outdoor room); touch: leaves on walking in (default when walking)."""
        walk = (not self.inside) if walk is None else walk
        x0, y0, x1, y1 = zone
        self.doors.append({
            "to": to,
            "zone": {"x0": reb.g(x0), "z0": reb.g(y0), "x1": reb.g(x1), "z1": reb.g(y1)},
            "arrive": {"x": reb.g(arrive[0]), "z": reb.g(arrive[1]), "angle": angle(face)},
            "walk": walk,
            "touch": walk if touch is None else touch,
        })

    def check(self, zone, text):
        """A place she can examine; `text` is up to a few short lines, '\\n' between pages."""
        x0, y0, x1, y1 = zone
        self.checks.append({"zone": {"x0": reb.g(x0), "z0": reb.g(y0), "x1": reb.g(x1), "z1": reb.g(y1)}, "text": text})

    def void(self, rect):
        """Floor inside the bounds that is not there: a drop, a pit, deep water."""
        x0, y0, x1, y1 = rect
        self.voids.append({"x0": reb.g(x0), "z0": reb.g(y0), "x1": reb.g(x1), "z1": reb.g(y1)})

    def export(self, anim=None, samples=256, states=()):
        print(f"[kit] {len(bpy.data.objects)} objects", flush=True)
        wear(float(os.environ.get("RE1_WEAR", "1.3")))
        x0, y0, x1, y1 = self.bounds
        extra = {
            "bounds": {"x0": reb.g(x0), "z0": reb.g(y0), "x1": reb.g(x1), "z1": reb.g(y1)},
            "voids": self.voids,
            "doors": self.doors,
            "checks": self.checks,
            "entry": self.entry,
            "notes": self.notes,
        }
        reb.export(self.cameras, OUT, samples=samples, extra=extra,
                   anim=anim.spec() if anim and anim.moves else None, states=states)


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

_mats = {}


def mat(name):
    """The shared palette, made on first use."""
    if name in _mats:
        return _mats[name]
    s = reb.mat_surface
    m = {
        "blood": lambda: _glossy("Blood", (0.12, 0.004, 0.003), 0.15),
        "old blood": lambda: s("Old blood", [(0.0, (0.05, 0.008, 0.005)), (1.0, (0.14, 0.03, 0.015))], scale=14, rough=0.55, bump=0.2),
        "grime": lambda: s("Grime", [(0.0, (0.03, 0.025, 0.02)), (1.0, (0.08, 0.065, 0.05))], scale=9, rough=0.9, bump=0.2),
        "mud": lambda: s("Mud", [(0.0, (0.05, 0.035, 0.02)), (1.0, (0.13, 0.09, 0.055))], scale=5, rough=0.6, bump=0.5),
        "dirt": lambda: s("Dirt", [(0.0, (0.1, 0.075, 0.05)), (1.0, (0.2, 0.15, 0.1))], scale=6, bump=0.6),
        "grass": lambda: s("Meadow", [(0.0, (0.06, 0.08, 0.025)), (0.5, (0.13, 0.15, 0.05)), (1.0, (0.2, 0.18, 0.09))], scale=1.5, bump=0.4),
        "gravel": lambda: s("Gravel", [(0.0, (0.12, 0.115, 0.1)), (0.5, (0.22, 0.21, 0.19)), (1.0, (0.33, 0.31, 0.28))], scale=30, bump=1.0),
        "rock": lambda: s("Granite", [(0.0, (0.12, 0.12, 0.11)), (1.0, (0.3, 0.29, 0.27))], scale=3, bump=0.9),
        "wet rock": lambda: s("Wet rock", [(0.0, (0.04, 0.04, 0.038)), (1.0, (0.14, 0.13, 0.12))], scale=3, rough=0.35, bump=1.0),
        "bark": lambda: s("Bark", [(0.0, (0.05, 0.035, 0.025)), (1.0, (0.13, 0.09, 0.06))], scale=10, bump=0.9),
        "planks": lambda: reb.mat_wood("Weathered planks", (0.24, 0.2, 0.15)),
        "dark wood": lambda: reb.mat_wood("Dark wood", (0.09, 0.055, 0.035)),
        "pine": lambda: reb.mat_wood("Pine boards", (0.36, 0.25, 0.14)),
        "logs": lambda: reb.mat_wood("Logs", (0.21, 0.13, 0.075)),
        "rust": lambda: s("Rust", [(0.0, (0.15, 0.06, 0.02)), (1.0, (0.3, 0.14, 0.05))], scale=20, rough=0.8),
        "iron": lambda: reb.mat_metal("Iron", (0.06, 0.055, 0.05), 0.55),
        "steel": lambda: reb.mat_metal("Steel", (0.45, 0.45, 0.45), 0.3),
        "tin": lambda: s("Corrugated tin", [(0.0, (0.2, 0.2, 0.19)), (0.6, (0.3, 0.29, 0.27)), (1.0, (0.32, 0.17, 0.08))], scale=3, rough=0.5, bump=0.3),
        "concrete": lambda: s("Concrete", [(0.0, (0.2, 0.2, 0.19)), (1.0, (0.36, 0.35, 0.33))], scale=5, bump=0.4),
        "plaster": lambda: s("Stained plaster", [(0.0, (0.3, 0.27, 0.22)), (0.7, (0.45, 0.42, 0.36)), (1.0, (0.5, 0.47, 0.4))], scale=2, bump=0.15),
        "brick": lambda: s("Old brick", [(0.0, (0.15, 0.06, 0.04)), (1.0, (0.3, 0.13, 0.08))], scale=12, bump=0.7),
        "canvas": lambda: s("Canvas", [(0.0, (0.25, 0.22, 0.15)), (1.0, (0.33, 0.3, 0.21))], scale=40, bump=0.3),
        "sheet": lambda: s("Stained sheet", [(0.0, (0.35, 0.33, 0.28)), (0.75, (0.55, 0.53, 0.47)), (1.0, (0.3, 0.12, 0.08))], scale=3, bump=0.1),
        "mattress": lambda: s("Stained mattress", [(0.0, (0.25, 0.2, 0.12)), (0.6, (0.45, 0.42, 0.33)), (1.0, (0.18, 0.06, 0.03))], scale=2.5, bump=0.2),
        "flannel": lambda: reb.mat_stripes("Flannel", [(0.3, 0.04, 0.03), (0.05, 0.04, 0.04)], across=24, axis="X"),
        "denim": lambda: s("Denim", [(0.0, (0.06, 0.08, 0.13)), (1.0, (0.1, 0.13, 0.2))], scale=60, bump=0.2),
        "khaki": lambda: s("Ranger khaki", [(0.0, (0.2, 0.17, 0.09)), (1.0, (0.28, 0.24, 0.13))], scale=40, bump=0.2),
        "skin": lambda: s("Dead skin", [(0.0, (0.25, 0.2, 0.16)), (0.8, (0.33, 0.27, 0.22)), (1.0, (0.18, 0.12, 0.1))], scale=6, rough=0.6, bump=0.15),
        "bone": lambda: reb.mat_plain("Bone", (0.55, 0.5, 0.4), 0.6),
        "paper": lambda: reb.mat_plain("Paper", (0.62, 0.6, 0.52), 0.85),
        "old paper": lambda: s("Old paper", [(0.0, (0.4, 0.35, 0.24)), (1.0, (0.58, 0.53, 0.4))], scale=8, bump=0.05),
        "glass": lambda: reb.mat_glass("Glass", (0.6, 0.7, 0.7)),
        "bottle": lambda: reb.mat_glass("Bottle glass", (0.2, 0.35, 0.12)),
        "black": lambda: reb.mat_plain("Black", (0.012, 0.012, 0.012), 0.6),
        "feathers": lambda: _glossy("Crow feathers", (0.01, 0.01, 0.014), 0.35),
        "web": lambda: reb.mat_plain("Web", (0.6, 0.6, 0.6), 0.9),
        "rubber": lambda: reb.mat_plain("Rubber", (0.02, 0.02, 0.02), 0.85),
        "red paint": lambda: reb.mat_plain("Red paint", (0.35, 0.04, 0.03), 0.5),
        "yellow paint": lambda: reb.mat_plain("Yellow paint", (0.55, 0.38, 0.03), 0.5),
        "white paint": lambda: reb.mat_plain("White paint", (0.6, 0.6, 0.56), 0.5),
        "green paint": lambda: s("Green paint", [(0.0, (0.06, 0.12, 0.07)), (1.0, (0.09, 0.16, 0.09))], scale=8, rough=0.45, bump=0.1),
        "water": lambda: _water(),
        "needles": lambda: reb.mat_cards("Needles", (0.02, 0.05, 0.025), (0.07, 0.12, 0.05)),
        "dead needles": lambda: reb.mat_cards("Dry needles", (0.12, 0.09, 0.04), (0.2, 0.17, 0.08)),
        "blades": lambda: reb.mat_cards("Grass", (0.07, 0.1, 0.03), (0.22, 0.24, 0.08)),
        "dead grass": lambda: reb.mat_cards("Dead grass", (0.15, 0.12, 0.06), (0.32, 0.27, 0.14)),
        "ferns": lambda: reb.mat_cards("Fern", (0.04, 0.09, 0.03), (0.1, 0.18, 0.05)),
        "leaves": lambda: reb.mat_cards("Leaves", (0.05, 0.08, 0.02), (0.16, 0.2, 0.05)),
        "ivy": lambda: reb.mat_cards("Ivy", (0.015, 0.04, 0.015), (0.05, 0.1, 0.03)),
    }[name]()
    _mats[name] = m
    return m


# Materials that keep their look: see-through, glowing, wet, or too small to carry a texture.
_UNWORN = ("Water", "Blood", "Glass", "Bottle glass", "Web", "Crow feathers")


def wear(strength=1.0, texel=0.012):
    """Give every surface in the scene the same worn, low-resolution texture,
    as RE1's backgrounds have: water stains with hard edges, streaks run
    down, fine speckle in blocky texels `texel` metres across, grime dark in
    the corners and where things touch, and the colour muddied a little.
    Runs once, before the render, over every material with a Principled BSDF."""
    if strength <= 0:
        return
    worn = 0
    for m in bpy.data.materials:
        if not m.use_nodes or m.name.split(".")[0] in _UNWORN or m.get("worn"):
            continue
        nodes, links = m.node_tree.nodes, m.node_tree.links
        bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None or bsdf.inputs["Transmission Weight"].default_value > 0.5:
            continue
        base = bsdf.inputs["Base Color"]
        if base.is_linked and base.links[0].from_node.type == "NEW_GEOMETRY" or any(n.type == "NEW_GEOMETRY" for n in nodes):
            continue  # leaf and grass cards
        if base.is_linked:
            src = base.links[0].from_socket
        else:
            rgb = nodes.new("ShaderNodeRGB")
            rgb.outputs[0].default_value = base.default_value
            src = rgb.outputs[0]
        # Object space, shifted per object so neighbours don't share a stain, then snapped to texels.
        tc = nodes.new("ShaderNodeTexCoord")
        info = nodes.new("ShaderNodeObjectInfo")
        shift = nodes.new("ShaderNodeVectorMath"); shift.operation = "MULTIPLY_ADD"  # a * b + c
        shift.inputs[0].default_value = (97, 61, 43)
        links.new(info.outputs["Random"], shift.inputs[1])
        links.new(tc.outputs["Object"], shift.inputs[2])
        snap = nodes.new("ShaderNodeVectorMath"); snap.operation = "SNAP"
        snap.inputs[1].default_value = (texel, texel, texel)
        links.new(shift.outputs[0], snap.inputs[0])

        def layer(scale, detail, stops, stretch=(1, 1, 1), distortion=0.0):
            vec = snap.outputs[0]
            if stretch != (1, 1, 1):
                mp = nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = stretch
                links.new(vec, mp.inputs["Vector"]); vec = mp.outputs[0]
            n = nodes.new("ShaderNodeTexNoise")
            n.inputs["Scale"].default_value = scale
            n.inputs["Detail"].default_value = detail
            n.inputs["Roughness"].default_value = 0.65
            n.inputs["Distortion"].default_value = distortion
            links.new(vec, n.inputs["Vector"])
            return reb.ramp(nodes, links, n.outputs["Fac"], stops).outputs["Color"]

        k = strength
        # A stain dries with a dark tide line round a paler middle.
        rim, inside = (1 - 0.42 * k, 1 - 0.44 * k, 1 - 0.5 * k), (1 - 0.16 * k, 1 - 0.17 * k, 1 - 0.2 * k)
        stains = layer(0.9, 5, [(0.56, (1, 1, 1)), (0.57, rim), (0.6, inside), (0.75, inside), (0.85, rim)], distortion=0.8)
        streaks = layer(9, 4, [(0.35, (1 - 0.2 * k,) * 3), (0.65, (1 + 0.05 * k,) * 3)], stretch=(6, 6, 0.35))
        speckle = layer(70, 2, [(0.3, (1 - 0.25 * k,) * 3), (0.7, (1 + 0.12 * k,) * 3)])
        ao = nodes.new("ShaderNodeAmbientOcclusion")
        ao.inputs["Distance"].default_value = 0.3
        ao.samples = 8
        corners = reb.ramp(nodes, links, ao.outputs["AO"], [(0.0, (1 - 0.6 * k,) * 3), (1.0, (1, 1, 1))]).outputs["Color"]
        out = src
        for f in (stains, streaks, speckle, corners):
            mix = nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            links.new(out, mix.inputs["A"]); links.new(f, mix.inputs["B"])
            out = mix.outputs["Result"]
        mud = nodes.new("ShaderNodeHueSaturation")
        mud.inputs["Saturation"].default_value = 1 - 0.18 * k
        links.new(out, mud.inputs["Color"])
        links.new(mud.outputs["Color"], base)
        m["worn"] = True
        worn += 1
    print(f"[kit] wear {strength}: {worn} materials", flush=True)


def _glossy(name, rgb, rough):
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    return m


def _water():
    """Dark water whose ripples move: a wave texture whose phase the Anim turns."""
    m, nodes, links, bsdf = reb.nodes_material("Water")
    bsdf.inputs["Base Color"].default_value = (0.01, 0.015, 0.014, 1)
    bsdf.inputs["Roughness"].default_value = 0.05
    tc = nodes.new("ShaderNodeTexCoord")
    wave = nodes.new("ShaderNodeTexWave")
    wave.name = "Ripples"
    wave.inputs["Scale"].default_value = 1.6
    wave.inputs["Distortion"].default_value = 6
    wave.inputs["Detail"].default_value = 4
    links.new(tc.outputs["Object"], wave.inputs["Vector"])
    reb.bumped(nodes, links, bsdf, wave.outputs["Fac"], 0.15, 0.02)
    return m


def dirtied(base, amount=0.5, name=None, scale=3.0):
    """`base`'s colour mottled toward grime: walls a hand has worn, a floor no one cleaned."""
    m = base.copy()
    m.name = name or f"{base.name}, dirty"
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes["Principled BSDF"]
    src = bsdf.inputs["Base Color"].links[0].from_socket if bsdf.inputs["Base Color"].links else None
    n = reb.noise_tex(nodes, links, scale, 6, 0.6)
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    r = reb.ramp(nodes, links, n.outputs["Fac"], [(0.35, (0.25, 0.22, 0.2)), (0.65, (1, 1, 1))])
    links.new(r.outputs["Color"], mix.inputs["B"])
    mix.inputs["Factor"].default_value = amount
    if src:
        links.new(src, mix.inputs["A"])
    else:
        mix.inputs["A"].default_value = bsdf.inputs["Base Color"].default_value
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    return m


def boards(name, rgb, width=0.15, seam=0.08, grime=0.5):
    """Wood in boards `width` metres wide with dark seams between them, on
    walls along x or y alike (the seams follow x + y): panelling, a plank
    wall, a boarded ceiling."""
    m = reb.mat_wood(name, rgb)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes["Principled BSDF"]
    src = bsdf.inputs["Base Color"].links[0].from_socket
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Object"], sep.inputs["Vector"])
    add = nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    links.new(sep.outputs["X"], add.inputs[0])
    links.new(sep.outputs["Y"], add.inputs[1])
    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 1.0 / width
    links.new(add.outputs[0], mul.inputs[0])
    frac = nodes.new("ShaderNodeMath")
    frac.operation = "FRACT"
    links.new(mul.outputs[0], frac.inputs[0])
    r = nodes.new("ShaderNodeValToRGB")
    r.color_ramp.interpolation = "CONSTANT"
    els = r.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.08, 0.07, 0.06, 1)
    els[1].position, els[1].color = seam, (1, 1, 1, 1)
    links.new(frac.outputs[0], r.inputs["Fac"])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    links.new(src, mix.inputs["A"])
    links.new(r.outputs["Color"], mix.inputs["B"])
    # Grime: darker toward the floor and in blotches.
    n = reb.noise_tex(nodes, links, 2.5, 6, 0.6)
    g = reb.ramp(nodes, links, n.outputs["Fac"], [(0.3, (0.35, 0.3, 0.26)), (0.7, (1, 1, 1))])
    mix2 = nodes.new("ShaderNodeMix")
    mix2.data_type = "RGBA"
    mix2.blend_type = "MULTIPLY"
    mix2.inputs["Factor"].default_value = grime
    links.new(mix.outputs["Result"], mix2.inputs["A"])
    links.new(g.outputs["Color"], mix2.inputs["B"])
    links.new(mix2.outputs["Result"], bsdf.inputs["Base Color"])
    return m


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------


def join(name, parts, material=None, origin=None):
    """Join objects into one (keeping their materials). The result has no
    turn or scale of its own and its origin at `origin`, or at the first
    part's location if None. Build a prop's parts around (0, 0, 0), join with
    origin=(0, 0, 0), then set its location and turn to place it."""
    parts = [p for p in parts if p is not None]
    if not parts:
        return None
    pivot = Vector(origin if origin is not None else parts[0].location)
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    if len(parts) > 1:
        bpy.ops.object.join()
    ob = bpy.context.active_object
    # The join keeps the first part's own transform; put the mesh in world
    # space instead, so setting the result's location or turn later moves
    # the whole thing as built.
    bpy.context.view_layer.update()
    ob.data.transform(Matrix.Translation(-pivot) @ ob.matrix_world)
    ob.matrix_world = Matrix.Translation(pivot)
    ob.name = name
    if material is not None:
        ob.data.materials.clear()
        ob.data.materials.append(material)
    return ob


def rod(name, m, a, b, r, segments=8):
    """A cylinder of radius r from point a to point b (metres)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    ob = reb.prim("cyl", name, m, (a + b) / 2, (2 * r, 2 * r, max(d.length, 1e-3)), segments=segments)
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return ob


def box(name, m, at, size, rot=0.0, bevel=0.0):
    """A box `size` (x, y, z) metres standing on `at` (its bottom centre), turned `rot` about z."""
    x, y, z = at
    return reb.prim("cube", name, m, (x, y, z + size[2] / 2), size, rot=(0, 0, rot), bevel=bevel)


def text(name, words, m, at, size=0.2, rot=(math.pi / 2, 0, 0), depth=0.004, align="CENTER"):
    """Lettering as a mesh: a sign, a stencil, a word written on a wall.
    Default rot stands it up facing -y (toward a camera south of it)."""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = words
    cu.size = size
    cu.extrude = depth
    cu.align_x = align
    cu.align_y = "CENTER"
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = at
    ob.rotation_euler = rot
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.active_object
    ob.data.materials.append(m)
    return ob


def _stain(verts, faces, rng, centre, r, yaw, lumps, stretch, seed, points=20, drops=True):
    """One irregular stain added to verts/faces, flat in its own XY plane."""
    c, s_ = math.cos(yaw), math.sin(yaw)
    def put(x, y):
        return (centre[0] + x * c - y * s_, centre[1] + x * s_ + y * c, centre[2])
    k = len(verts)
    verts.append(put(0, 0))
    for i in range(points):
        a = 2 * math.pi * i / points
        q = 1 + lumps * noise.noise(Vector((math.cos(a) * 1.5 + seed, math.sin(a) * 1.5, 0.3))) + rng.uniform(-0.1, 0.1) * lumps
        verts.append(put(math.cos(a) * r * q * stretch[0], math.sin(a) * r * q * stretch[1]))
    faces.extend((k, k + 1 + i, k + 1 + (i + 1) % points) for i in range(points))
    if drops:
        for _ in range(rng.randint(2, 6)):
            a = rng.uniform(0, 2 * math.pi)
            d = r * rng.uniform(1.1, 1.9)
            dr = r * rng.uniform(0.06, 0.15)
            j = len(verts)
            cx, cy = math.cos(a) * d * stretch[0], math.sin(a) * d * stretch[1]
            verts.append(put(cx, cy))
            for i in range(6):
                b = 2 * math.pi * i / 6
                verts.append(put(cx + math.cos(b) * dr, cy + math.sin(b) * dr))
            faces.extend((j, j + 1 + i, j + 1 + (i + 1) % 6) for i in range(6))


def splat(name, m, at, r, rot=(0, 0, 0), lumps=0.35, seed=0, points=24, stretch=(1, 1)):
    """A flat irregular stain of radius r: blood, oil, a burn. Lies on the
    floor by default; rot stands it on a wall."""
    rng = random.Random(seed)
    verts, faces = [], []
    _stain(verts, faces, rng, (0, 0, 0), r, 0.0, lumps, stretch, seed, points)
    ob = reb.mesh_object(name, verts, faces, m, smooth=False)
    ob.location = (at[0], at[1], at[2] + 0.003)
    ob.rotation_euler = rot
    return ob


def drag_trail(name, m, path, width=0.3, seed=0, z=0.0, height=None):
    """Smears along `path` [(x, y), ...]: something heavy pulled across the
    floor. Overlapping stains stretched along the way, thinning and breaking
    up as the blood ran out. One mesh."""
    rng = random.Random(seed)
    pts = [Vector((x, y)) for x, y in path]
    total = sum((b - a).length for a, b in zip(pts, pts[1:])) or 1.0
    verts, faces = [], []
    walked = 0.0
    for a, b in zip(pts, pts[1:]):
        d = b - a
        n = max(1, int(d.length / max(width * 0.45, 0.05)))
        yaw = math.atan2(d.y, d.x)
        for i in range(n):
            t = walked + d.length * i / n
            if rng.random() < 0.12 + 0.35 * t / total:
                continue
            p = a.lerp(b, i / n) + Vector((-d.y, d.x)).normalized() * rng.uniform(-0.04, 0.04)
            zz = (height(p.x, p.y) if height else z) + 0.004
            r = width * 0.5 * rng.uniform(0.6, 1.0) * (1.0 - 0.45 * t / total)
            _stain(verts, faces, rng, (p.x, p.y, zz), r, yaw, 0.3, (1.8, 0.7), seed + i, points=12, drops=rng.random() < 0.3)
        walked += d.length
    return reb.mesh_object(name, verts, faces, m, smooth=False)


def cracks(name, m, area, count=12, seed=0, z=0.001, length=1.5):
    """Thin dark cracks wandering across a slab or a wall's foot: one mesh."""
    rng = random.Random(seed)
    verts, faces = [], []
    for _ in range(count):
        p = Vector((rng.uniform(area[0], area[2]), rng.uniform(area[1], area[3])))
        a = rng.uniform(0, 2 * math.pi)
        for _ in range(int(length / 0.15)):
            a += rng.uniform(-0.6, 0.6)
            q = p + Vector((math.cos(a), math.sin(a))) * 0.15
            side = Vector((-(q - p).y, (q - p).x)).normalized() * rng.uniform(0.004, 0.012)
            k = len(verts)
            for c in (p - side, p + side, q + side, q - side):
                verts.append((c.x, c.y, z))
            faces.append((k, k + 1, k + 2, k + 3))
            p = q
    return reb.mesh_object(name, verts, faces, m, smooth=False)


def scratches(name, m, at, facing, count=5, length=0.6, seed=0):
    """Gouges down a wall or a door: fingernails, or claws. `facing` is the
    wall's outward normal (dx, dy); `at` the top middle."""
    rng = random.Random(seed)
    n = Vector((facing[0], facing[1], 0)).normalized()
    side = Vector((-n.y, n.x, 0))
    parts = []
    for i in range(count):
        top = Vector(at) + side * (i - count / 2) * 0.035 + n * 0.006
        bottom = top + Vector((0, 0, -length * rng.uniform(0.6, 1.0))) + side * rng.uniform(-0.05, 0.05)
        parts.append(rod(f"{name} {i}", m, top, bottom, 0.004, 4))
    return join(name, parts)


# ---------------------------------------------------------------------------
# Furniture and clutter
# ---------------------------------------------------------------------------


def table(name, m, at, size=(1.2, 0.7, 0.76), rot=0.0, legs_mat=None):
    x, y, z = at
    sx, sy, h = size
    c, s = math.cos(rot), math.sin(rot)
    parts = [reb.prim("cube", f"{name} top", m, (x, y, z + h - 0.02), (sx, sy, 0.04), rot=(0, 0, rot), bevel=0.004)]
    for dx in (-1, 1):
        for dy in (-1, 1):
            lx, ly = dx * (sx / 2 - 0.05), dy * (sy / 2 - 0.05)
            parts.append(reb.prim("cube", f"{name} leg", legs_mat or m, (x + lx * c - ly * s, y + lx * s + ly * c, z + (h - 0.04) / 2), (0.05, 0.05, h - 0.04), rot=(0, 0, rot)))
    return join(name, parts)


def chair(name, m, at, rot=0.0, tipped=False):
    """A wooden chair facing `rot` (radians about z); tipped lies it on its back."""
    parts = [
        reb.prim("cube", "seat", m, (0, 0, 0.45), (0.42, 0.42, 0.04)),
        reb.prim("cube", "back", m, (-0.19, 0, 0.75), (0.04, 0.4, 0.55)),
    ]
    for dx in (-0.18, 0.18):
        for dy in (-0.18, 0.18):
            parts.append(reb.prim("cube", "leg", m, (dx, dy, 0.22), (0.04, 0.04, 0.45)))
    ob = join(name, parts, origin=(0, 0, 0))
    if tipped:
        ob.rotation_euler = (0, -math.pi / 2, rot)
        ob.location = (at[0], at[1], at[2] + 0.21)
    else:
        ob.rotation_euler = (0, 0, rot)
        ob.location = at
    return ob


def bunk(name, frame_m, at, rot=0.0, levels=2, mattress=True, slept_in=True, seed=0):
    """An iron bunk, mattresses stained, blankets thrown back."""
    rng = random.Random(seed)
    x, y, z = at
    L, W = 1.95, 0.85
    parts = []
    tall = 0.75 + (levels - 1) * 1.25
    for dx in (-L / 2, L / 2):
        for dy in (-W / 2, W / 2):
            parts.append(reb.prim("cyl", "post", frame_m, (dx, dy, tall / 2), (0.04, 0.04, tall), segments=8))
    for lv in range(levels):
        h = 0.35 + lv * 1.25
        for dy in (-W / 2, W / 2):
            parts.append(reb.prim("cube", "rail", frame_m, (0, dy, h), (L, 0.03, 0.04)))
        for dx in (-L / 2, L / 2):
            parts.append(reb.prim("cube", "rail", frame_m, (dx, 0, h), (0.03, W, 0.04)))
    ob = join(name, parts, origin=(0, 0, 0))
    ob.location = at
    ob.rotation_euler = (0, 0, rot)
    out = [ob]
    if mattress:
        for lv in range(levels):
            h = 0.35 + lv * 1.25 + 0.08
            mm = reb.prim("cube", f"{name} mattress", mat("mattress"), (0, 0, h), (L - 0.06, W - 0.06, 0.13), bevel=0.04)
            mm.parent = ob
            if slept_in and rng.random() < 0.8:
                bl = reb.cloth(f"{name} blanket", mat("flannel") if rng.random() < 0.5 else mat("canvas"), (rng.uniform(-0.3, 0.3), 0, h + 0.09), (1.1, 0.95), lumps=0.07, seed=seed * 7 + lv, rot=(0, 0, rng.uniform(-0.3, 0.3)))
                bl.parent = ob
    return out


def shelves(name, m, at, size=(1.0, 0.3, 1.8), rows=4, rot=0.0, clutter=0.7, seed=0):
    """Open shelves along a wall, with jars, tins and bottles on them."""
    rng = random.Random(seed)
    sx, sy, sz = size
    parts = []
    for side in (-sx / 2, sx / 2):
        parts.append(reb.prim("cube", "side", m, (side, 0, sz / 2), (0.03, sy, sz)))
    for r in range(rows):
        parts.append(reb.prim("cube", "shelf", m, (0, 0, 0.1 + r * (sz - 0.15) / (rows - 1)), (sx, sy, 0.025)))
    ob = join(name, parts, origin=(0, 0, 0))
    ob.location = at
    ob.rotation_euler = (0, 0, rot)
    for r in range(rows):
        h = 0.1 + r * (sz - 0.15) / (rows - 1) + 0.0125
        xx = -sx / 2 + 0.06
        while xx < sx / 2 - 0.06:
            if rng.random() < clutter:
                kind = rng.choice(("tin", "jar", "bottle", "box"))
                if kind == "tin":
                    it = reb.prim("cyl", "tin", mat("rust") if rng.random() < 0.5 else mat("steel"), (xx, rng.uniform(-0.05, 0.05), h + 0.06), (0.08, 0.08, 0.12), segments=10)
                elif kind == "jar":
                    it = reb.prim("cyl", "jar", mat("glass"), (xx, rng.uniform(-0.05, 0.05), h + 0.08), (0.09, 0.09, 0.16), segments=10)
                elif kind == "bottle":
                    it = reb.prim("cyl", "bottle", mat("bottle"), (xx, rng.uniform(-0.05, 0.05), h + 0.12), (0.07, 0.07, 0.24), segments=10)
                else:
                    it = reb.prim("cube", "box", mat("old paper"), (xx, 0, h + 0.07), (0.14, 0.16, 0.14), rot=(0, 0, rng.uniform(-0.2, 0.2)))
                it.parent = ob
            xx += rng.uniform(0.09, 0.16)
    return ob


def crate(name, m, at, size=(0.6, 0.5, 0.5), rot=0.0, open_=False):
    x, y, z = at
    parts = [reb.prim("cube", "body", m, (0, 0, size[2] / 2), size, bevel=0.01)]
    for dz in (0.08, size[2] - 0.08):
        parts.append(reb.prim("cube", "slat", m, (0, 0, dz), (size[0] + 0.02, size[1] + 0.02, 0.06)))
    ob = join(name, parts, origin=(0, 0, 0))
    ob.location = at
    ob.rotation_euler = (0, 0, rot)
    if open_:
        lid = reb.prim("cube", f"{name} lid", m, (size[0] * 0.7, 0.1, 0.02), (size[0], size[1], 0.03), rot=(0, 0.25, 0.4))
        lid.parent = ob
    return ob


def drum(name, m, at, tipped=False, rot=0.0):
    """A 200-litre oil drum, standing or on its side (rolled toward `rot`)."""
    ob = reb.prim("cyl", name, m, (0, 0, 0), (0.58, 0.58, 0.88), segments=20)
    for dz in (-0.29, 0.0, 0.29):
        ring = reb.prim("cyl", "hoop", m, (0, 0, dz), (0.6, 0.6, 0.025), segments=20)
        ring.parent = ob
    if tipped:
        ob.rotation_euler = (math.pi / 2, 0, rot)
        ob.location = (at[0], at[1], at[2] + 0.3)
    else:
        ob.rotation_euler = (0, 0, rot)
        ob.location = (at[0], at[1], at[2] + 0.44)
    return ob


def papers(name, at, spread=0.5, count=8, seed=0, m=None, z=0.0):
    """Sheets of paper scattered over a floor or a desk."""
    rng = random.Random(seed)
    parts = []
    for i in range(count):
        parts.append(reb.prim("cube", "sheet", m or (mat("paper") if rng.random() < 0.6 else mat("old paper")),
                              (at[0] + rng.gauss(0, spread / 2), at[1] + rng.gauss(0, spread / 2), at[2] + z + 0.002 + i * 0.0006),
                              (0.21, 0.28, 0.001), rot=(rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), rng.uniform(0, math.pi))))
    return join(name, parts)


def bottles(name, at, count=4, spread=0.4, seed=0, tipped=0.5):
    rng = random.Random(seed)
    parts = []
    for i in range(count):
        p = (at[0] + rng.gauss(0, spread / 2), at[1] + rng.gauss(0, spread / 2), at[2])
        if rng.random() < tipped:
            parts.append(reb.prim("cyl", "bottle", mat("bottle"), (p[0], p[1], p[2] + 0.035), (0.07, 0.07, 0.25), rot=(math.pi / 2, 0, rng.uniform(0, math.pi)), segments=10))
        else:
            parts.append(reb.prim("cyl", "bottle", mat("bottle"), (p[0], p[1], p[2] + 0.125), (0.07, 0.07, 0.25), segments=10))
    return join(name, parts)


def shards(name, at, spread=0.6, count=20, seed=0, m=None):
    """Broken glass under a window."""
    rng = random.Random(seed)
    verts, faces = [], []
    for _ in range(count):
        c = Vector((at[0] + rng.gauss(0, spread / 2), at[1] + rng.gauss(0, spread / 2), at[2] + 0.003))
        s = rng.uniform(0.02, 0.07)
        k = len(verts)
        for j in range(3):
            a = rng.uniform(0, 2 * math.pi)
            verts.append(tuple(c + Vector((math.cos(a) * s, math.sin(a) * s, 0))))
        faces.append((k, k + 1, k + 2))
    return reb.mesh_object(name, verts, faces, m or mat("glass"), smooth=False)


def barricade(name, m, a, b, z0=0.3, z1=1.9, count=5, seed=0, nails=True):
    """Boards nailed across an opening from a to b (floor points), in a hurry."""
    rng = random.Random(seed)
    a, b = Vector((*a, 0)), Vector((*b, 0))
    mid = (a + b) / 2
    span = (b - a).length + 0.3
    yaw = math.atan2(b.y - a.y, b.x - a.x)
    parts = []
    for i in range(count):
        z = z0 + (z1 - z0) * (i + rng.uniform(-0.2, 0.2)) / max(1, count - 1)
        tilt = rng.uniform(-0.35, 0.35)
        parts.append(reb.prim("cube", "board", m, (mid.x, mid.y, z), (span, 0.025, rng.uniform(0.12, 0.2)), rot=(tilt, 0, yaw)))
        parts[-1].rotation_euler = (0, tilt, yaw)
    return join(name, parts)


def lantern(name, at, energy=12, rgb=(1.0, 0.62, 0.28), hanging=False):
    """A hurricane lamp: returns (lamp object, its light, its flame material) for Anim.flicker."""
    flame = reb.mat_emit(f"{name} flame", (1.0, 0.6, 0.25), 25)
    x, y, z = at
    parts = [
        reb.prim("cyl", "base", mat("rust"), (x, y, z + 0.03), (0.14, 0.14, 0.06), segments=12),
        reb.prim("cyl", "globe", mat("glass"), (x, y, z + 0.16), (0.11, 0.11, 0.2), segments=12),
        reb.prim("cone", "cap", mat("rust"), (x, y, z + 0.29), (0.13, 0.13, 0.06), segments=12, top=0.3),
    ]
    if hanging:
        parts.append(reb.prim("cube", "handle", mat("iron"), (x, y, z + 0.38), (0.12, 0.006, 0.006)))
    lamp = join(name, parts)
    f = reb.prim("cone", f"{name} wick", flame, (x, y, z + 0.14), (0.025, 0.025, 0.06), segments=8)
    light = reb.point(f"{name} light", (x, y, z + 0.16), energy, rgb, 0.03)
    return lamp, light, flame


def candle(name, at, energy=3, height=0.12):
    flame = reb.mat_emit(f"{name} flame", (1.0, 0.65, 0.3), 30)
    x, y, z = at
    stick = reb.prim("cyl", name, reb.mat_plain("Wax", (0.62, 0.58, 0.48), 0.5), (x, y, z + height / 2), (0.03, 0.03, height), segments=10)
    reb.prim("cone", f"{name} flame", flame, (x, y, z + height + 0.018), (0.012, 0.012, 0.035), segments=8)
    splat(f"{name} wax", reb.mat_plain("Wax drips", (0.6, 0.56, 0.46), 0.5), (x, y, z), 0.04, seed=len(name))
    light = reb.point(f"{name} light", (x, y, z + height + 0.03), energy, (1.0, 0.6, 0.3), 0.01)
    return stick, light, flame


def bulb(name, at, energy=20, rgb=(1.0, 0.8, 0.55), flex=0.5):
    """A bare bulb on a flex hanging from `at` (the ceiling point)."""
    glow = reb.mat_emit(f"{name} glow", rgb, 30)
    x, y, z = at
    cord = reb.prim("cyl", f"{name} flex", reb.mat_plain("Flex", (0.02, 0.02, 0.02), 0.5), (x, y, z - flex / 2), (0.012, 0.012, flex))
    glass = reb.prim("sphere", f"{name} bulb", glow, (x, y, z - flex - 0.04), (0.07, 0.07, 0.1), segments=12)
    light = reb.point(f"{name} light", (x, y, z - flex - 0.06), energy, rgb, 0.03)
    return cord, glass, light, glow


# ---------------------------------------------------------------------------
# The dead
# ---------------------------------------------------------------------------

# Joint positions in metres for a body 1.78 m tall, its head toward +x, lying
# on its back, then face down, then sitting slumped against a wall at x = 0
# (legs out toward +x). Left side is +y.
_POSES = {
    "back": {
        "head": (1.62, 0.0, 0.11), "neck": (1.46, 0, 0.12), "chest": (1.22, 0, 0.13), "pelvis": (0.88, 0, 0.12),
        "l_shoulder": (1.4, 0.2, 0.12), "r_shoulder": (1.4, -0.2, 0.12),
        "l_elbow": (1.22, 0.45, 0.06), "r_elbow": (1.55, -0.45, 0.06), "l_hand": (0.98, 0.58, 0.05), "r_hand": (1.78, -0.55, 0.05),
        "l_hip": (0.86, 0.11, 0.12), "r_hip": (0.86, -0.11, 0.12), "l_knee": (0.45, 0.2, 0.1), "r_knee": (0.47, -0.12, 0.16),
        "l_foot": (0.03, 0.28, 0.08), "r_foot": (0.06, -0.16, 0.08),
    },
    "front": {
        "head": (1.6, 0.06, 0.12), "neck": (1.46, 0, 0.13), "chest": (1.22, 0, 0.14), "pelvis": (0.88, 0, 0.13),
        "l_shoulder": (1.4, 0.2, 0.13), "r_shoulder": (1.4, -0.2, 0.13),
        "l_elbow": (1.66, 0.38, 0.06), "r_elbow": (1.2, -0.42, 0.06), "l_hand": (1.92, 0.3, 0.04), "r_hand": (1.0, -0.4, 0.04),
        "l_hip": (0.86, 0.11, 0.12), "r_hip": (0.86, -0.11, 0.12), "l_knee": (0.45, 0.16, 0.08), "r_knee": (0.46, -0.2, 0.08),
        "l_foot": (0.05, 0.18, 0.1), "r_foot": (0.08, -0.3, 0.1),
    },
    "slumped": {
        "head": (0.2, 0.05, 0.86), "neck": (0.1, 0, 0.78), "chest": (0.1, 0, 0.55), "pelvis": (0.2, 0, 0.14),
        "l_shoulder": (0.1, 0.2, 0.68), "r_shoulder": (0.1, -0.2, 0.68),
        "l_elbow": (0.15, 0.3, 0.4), "r_elbow": (0.22, -0.3, 0.38), "l_hand": (0.42, 0.3, 0.1), "r_hand": (0.4, -0.32, 0.06),
        "l_hip": (0.22, 0.11, 0.14), "r_hip": (0.22, -0.11, 0.14), "l_knee": (0.62, 0.18, 0.32), "r_knee": (0.66, -0.15, 0.14),
        "l_foot": (0.95, 0.2, 0.08), "r_foot": (1.08, -0.16, 0.08),
    },
}

_BONES = [
    ("neck", "chest", 0.06, "top"), ("chest", "pelvis", 0.16, "top"),
    ("l_shoulder", "r_shoulder", 0.07, "top"),
    ("l_shoulder", "l_elbow", 0.05, "top"), ("l_elbow", "l_hand", 0.042, "skin"),
    ("r_shoulder", "r_elbow", 0.05, "top"), ("r_elbow", "r_hand", 0.042, "skin"),
    ("l_hip", "l_knee", 0.075, "legs"), ("l_knee", "l_foot", 0.06, "legs"),
    ("r_hip", "r_knee", 0.075, "legs"), ("r_knee", "r_foot", 0.06, "legs"),
    ("l_hip", "r_hip", 0.09, "legs"),
]


def body(name, at, heading=0.0, pose="back", top=None, legs=None, bloody=0.0, seed=0, sheet=False, missing=()):
    """A dead man: `pose` back, front or slumped; head toward `heading`
    (radians from +x). `top` and `legs` are clothing materials; `bloody`
    lays a pool under him; `sheet` covers him; `missing` lists parts gone
    ("l_hand", "r_knee"...: the limb below that joint)."""
    rng = random.Random(seed)
    j = {k: Vector(v) for k, v in _POSES[pose].items()}
    top = top or mat("flannel")
    legs = legs or mat("denim")
    skin = mat("skin")
    parts = []
    for a, b, r, kind in _BONES:
        if a in missing or b in missing:
            continue
        m = {"top": top, "legs": legs, "skin": skin}[kind]
        parts.append(rod(f"{name} {a}", m, j[a], j[b], r, 10))
        parts.append(reb.prim("sphere", f"{name} joint", m, j[b], (2 * r,) * 3, segments=10))
    head_dir = (j["head"] - j["neck"]).normalized()
    parts.append(reb.prim("sphere", f"{name} head", skin, j["head"], (0.2, 0.17, 0.22), segments=16))
    parts.append(reb.prim("sphere", f"{name} hair", mat("black"), j["head"] - Vector((0, 0, 0.015)) + head_dir * 0.02, (0.205, 0.175, 0.2), segments=12))
    for foot in ("l_foot", "r_foot"):
        if foot not in missing:
            parts.append(reb.prim("cube", f"{name} boot", mat("rubber"), j[foot] + Vector((-0.02, 0, 0.02)), (0.12, 0.1, 0.12), bevel=0.02))
    ob = join(name, parts, origin=(0, 0, 0))
    ob.location = at
    ob.rotation_euler = (0, 0, heading)
    bpy.context.view_layer.update()
    if bloody:
        c = ob.matrix_world @ ((j["chest"] + j["pelvis"]) / 2)
        splat(f"{name} pool", mat("blood"), (c.x, c.y, at[2]), 0.45 * bloody + 0.25, rot=(0, 0, rng.uniform(0, 6)), seed=seed, stretch=(1.4, 1.0))
    if sheet:
        c = ob.matrix_world @ ((j["chest"] + j["pelvis"]) / 2)
        sh = reb.cloth(f"{name} sheet", mat("sheet"), (c.x, c.y, at[2] + 0.17), (2.0, 0.95), rot=(0, 0, heading), lumps=0.08, seed=seed)
        ob.hide_render = True
        return sh
    return ob


def bones(name, at, spread=0.5, seed=0, skull=True):
    """What the dogs left: long bones, a ribcage half sunk in the dirt, a skull."""
    rng = random.Random(seed)
    parts = []
    for _ in range(rng.randint(4, 7)):
        a = Vector((at[0] + rng.gauss(0, spread / 2), at[1] + rng.gauss(0, spread / 2), at[2] + 0.02))
        d = Vector((math.cos(rng.uniform(0, 6.3)), math.sin(rng.uniform(0, 6.3)), 0)) * rng.uniform(0.2, 0.42)
        parts.append(rod("bone", mat("bone"), a, a + d, rng.uniform(0.015, 0.025), 6))
    c = Vector((at[0], at[1], at[2]))
    for i in range(6):
        parts.append(rod("rib", mat("bone"), c + Vector((i * 0.04, -0.12, 0.02)), c + Vector((i * 0.04 + 0.02, 0.0, 0.12)), 0.008, 5))
        parts.append(rod("rib", mat("bone"), c + Vector((i * 0.04, 0.12, 0.02)), c + Vector((i * 0.04 + 0.02, 0.0, 0.12)), 0.008, 5))
    if skull:
        parts.append(reb.prim("sphere", "skull", mat("bone"), (at[0] + spread * 0.6, at[1] - spread * 0.3, at[2] + 0.08), (0.16, 0.13, 0.17), segments=14))
    return join(name, parts)


def crow(name, at, heading=0.0, perched=True):
    """A crow, standing (perched) or with its wings out. Returns (body, wings) for Anim.flap."""
    parts = [
        reb.prim("sphere", "body", mat("feathers"), (0, 0, 0.12), (0.26, 0.13, 0.13), segments=12),
        reb.prim("sphere", "head", mat("feathers"), (0.13, 0, 0.2), (0.09, 0.08, 0.08), segments=10),
        reb.prim("cone", "beak", mat("black"), (0.2, 0, 0.2), (0.03, 0.03, 0.07), rot=(0, math.pi / 2, 0), segments=6),
        reb.prim("cube", "tail", mat("feathers"), (-0.17, 0, 0.11), (0.14, 0.07, 0.01), rot=(0, -0.3, 0)),
    ]
    if perched:
        for dy in (-0.03, 0.03):
            parts.append(reb.prim("cyl", "leg", mat("black"), (0.0, dy, 0.03), (0.01, 0.01, 0.07)))
    b = join(name, parts, origin=(0, 0, 0))
    b.location = at
    b.rotation_euler = (0, 0, heading)
    wings = []
    for side in (-1, 1):
        w = reb.mesh_object(f"{name} wing", [(0, 0, 0), (-0.12, side * 0.3, 0), (0.08, side * 0.24, 0)], [(0, 1, 2)], mat("feathers"), smooth=False)
        w.parent = b
        w.location = (0, side * 0.04, 0.15)
        w.rotation_euler = (side * (0.0 if not perched else 1.25), 0, 0)
        wings.append(w)
    return b, wings


def web(name, corner, size=0.35, facing=(-1, 1)):
    """A cobweb across a corner (the corner point, the two walls' directions)."""
    verts, faces = [], []
    c = Vector(corner)
    for i in range(9):
        a = i * math.pi / 16
        d = Vector((facing[0] * math.cos(a) * size, facing[1] * math.sin(a) * size, -size * 0.85))
        k = len(verts)
        verts += [tuple(c), tuple(c + d), tuple(c + d + Vector((0, 0, 0.004)))]
        faces.append((k, k + 1, k + 2))
    return reb.mesh_object(name, verts, faces, mat("web"), smooth=False)


# ---------------------------------------------------------------------------
# Shells: interiors and the forest round a clearing
# ---------------------------------------------------------------------------


def walls(x0, y0, x1, y1, h, m, openings=(), thick=0.12, floor=None, ceiling=None, name="Wall"):
    """A room's four walls round the floor x0..x1, y0..y1, `h` high, with
    openings [(side, a0, a1, z0, z1)]: side is 'n' (y0), 's' (y1), 'w' (x0)
    or 'e' (x1); a runs along the wall (x for n and s, y for w and e). Also a
    floor and a ceiling when given materials. Walls are cut where openings
    are, so doors and windows show what is beyond."""
    out = []
    for side in "nswe":
        holes = sorted((a0, a1, z0, z1) for s, a0, a1, z0, z1 in openings if s == side)
        a_lo, a_hi = (x0, x1) if side in "ns" else (y0, y1)
        a_lo -= thick
        a_hi += thick
        segs = []
        a = a_lo
        for h0, h1, z0, z1 in holes:
            segs.append((a, h0, 0, h))
            if z0 > 0:
                segs.append((h0, h1, 0, z0))
            if z1 < h:
                segs.append((h0, h1, z1, h))
            a = h1
        segs.append((a, a_hi, 0, h))
        for s0, s1, z0, z1 in segs:
            if s1 - s0 < 1e-3 or z1 - z0 < 1e-3:
                continue
            mid, length = (s0 + s1) / 2, s1 - s0
            if side == "n":
                at, size = (mid, y0 - thick / 2, (z0 + z1) / 2), (length, thick, z1 - z0)
            elif side == "s":
                at, size = (mid, y1 + thick / 2, (z0 + z1) / 2), (length, thick, z1 - z0)
            elif side == "w":
                at, size = (x0 - thick / 2, mid, (z0 + z1) / 2), (thick, length, z1 - z0)
            else:
                at, size = (x1 + thick / 2, mid, (z0 + z1) / 2), (thick, length, z1 - z0)
            out.append(reb.prim("cube", f"{name} {side}", m, at, size))
    if floor is not None:
        out.append(reb.prim("cube", "Floor", floor, ((x0 + x1) / 2, (y0 + y1) / 2, -0.02), (x1 - x0 + 2 * thick, y1 - y0 + 2 * thick, 0.04)))
    if ceiling is not None:
        out.append(reb.prim("cube", "Ceiling", ceiling, ((x0 + x1) / 2, (y0 + y1) / 2, h + 0.03), (x1 - x0 + 2 * thick, y1 - y0 + 2 * thick, 0.06)))
    return out


def plank_floor(x0, y0, x1, y1, m, along="x", seed=0, gap=0.006):
    """Floorboards with gaps between them, laid along x or y."""
    rng = random.Random(seed)
    parts = []
    if along == "x":
        y = y0
        while y < y1:
            w = rng.choice((0.12, 0.14, 0.16))
            parts.append(reb.prim("cube", "Floorboard", m, ((x0 + x1) / 2, y + w / 2, -0.012), (x1 - x0, w - gap, 0.024)))
            y += w
    else:
        x = x0
        while x < x1:
            w = rng.choice((0.12, 0.14, 0.16))
            parts.append(reb.prim("cube", "Floorboard", m, (x + w / 2, (y0 + y1) / 2, -0.012), (w - gap, y1 - y0, 0.024)))
            x += w
    reb.prim("cube", "Under the boards", reb.mat_plain("Void", (0.008, 0.006, 0.005)), ((x0 + x1) / 2, (y0 + y1) / 2, -0.05), (x1 - x0 + 0.5, y1 - y0 + 0.5, 0.02))
    return join("Floorboards", parts)


def forest(rng, height, keep_out, area, count=70, spacing=1.6, tall=(11, 19), ferns=24, needles=900, dead=0.0):
    """Spruces round a clearing: `keep_out(x, y)` is True where no tree may
    stand (the floor, paths, buildings); `area` = (x0, y0, x1, y1) where they
    may. Returns the trunk bases. dead: share of the trees that are bare snags."""
    tv, tf, sv, sf = [], [], [], []
    bases = []
    tries = 0
    while len(bases) < count and tries < count * 80:
        tries += 1
        x, y = rng.uniform(area[0], area[2]), rng.uniform(area[1], area[3])
        if keep_out(x, y) or any((Vector((x, y)) - b.xy).length < spacing for b, _ in bases):
            continue
        bases.append((Vector((x, y, height(x, y) - 0.2)), rng.uniform(*tall)))
    live = []
    for base, h in bases:
        if rng.random() < dead:
            sv_k = len(sv)
            reb.conifer(random.Random(rng.random()), base, h * 0.25, sv, sf)
            del sv[sv_k:]
        else:
            reb.conifer(rng, base, h, tv, tf)
            live.append((base, h))
    reb.mesh_object("Spruces", tv, tf, mat("needles"))
    reb.trunks("Spruce trunks", mat("bark"), bases)
    fv, ff = [], []
    for _ in range(ferns):
        x, y = rng.uniform(area[0], area[2]), rng.uniform(area[1], area[3])
        if not keep_out(x, y):
            reb.fern(rng, (x, y, height(x, y)), rng.uniform(0.4, 0.8), fv, ff)
    if fv:
        reb.mesh_object("Ferns", fv, ff, mat("ferns"))
    dv, df = [], []
    for _ in range(needles):
        x, y = rng.uniform(area[0], area[2]), rng.uniform(area[1], area[3])
        if not keep_out(x, y):
            reb.card(dv, df, Vector((x, y, height(x, y) + 0.01)), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), Vector((0, 0, 1)), 0.08, 0.3, 0.0)
    if dv:
        reb.mesh_object("Fallen needles", dv, df, mat("dead needles"))
    return bases


def meadow(rng, count, where, height, m=None):
    """Grass tufts; returns the object, for Anim.sway."""
    gv, gf = [], []
    reb.grass_tufts(rng, count, where, height, gv, gf)
    return reb.mesh_object("Grass", gv, gf, m or mat("blades"), smooth=False)


def path_strip(name, m, path, height, width=0.6, wobble=0.25, lift=0.008):
    """A worn path or a track: a strip along `path` [(x, y), ...] on the ground."""
    v, f = [], []
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        a, b = Vector((ax, ay)), Vector((bx, by))
        d = b - a
        n = int(d.length / 0.3) + 1
        side = Vector((-d.y, d.x)).normalized()
        for i in range(n):
            p, q = a.lerp(b, i / n), a.lerp(b, (i + 1) / n)
            w0 = width * (1 + wobble * noise.noise(Vector((p.x, p.y, 7))))
            w1 = width * (1 + wobble * noise.noise(Vector((q.x, q.y, 7))))
            k = len(v)
            for c in (p - side * w0, p + side * w0, q + side * w1, q - side * w1):
                v.append((c.x, c.y, height(c.x, c.y) + lift))
            f.append((k, k + 1, k + 2, k + 3))
    return reb.mesh_object(name, v, f, m)


def tunnel(name, m, path, width=2.6, height=2.5, rough=0.25, seed=0, step=0.35, floor_m=None):
    """A rough rock tunnel along `path` [(x, y), ...] at floor z = 0: an arch
    of rock, lumpy, its floor flat where she walks."""
    rng = random.Random(seed)
    ring = 14
    verts, faces = [], []
    pts = [Vector((x, y, 0)) for x, y in path]
    samples = []
    for a, b in zip(pts, pts[1:]):
        n = max(1, int((b - a).length / step))
        for i in range(n):
            samples.append((a.lerp(b, i / n), (b - a).normalized()))
    samples.append((pts[-1], (pts[-1] - pts[-2]).normalized()))
    for si, (p, d) in enumerate(samples):
        side = Vector((-d.y, d.x, 0))
        for k in range(ring + 1):
            t = math.pi * k / ring
            r = 1 + rough * noise.noise(Vector((p.x * 0.9, p.y * 0.9, k * 0.7 + seed)))
            off = side * math.cos(t) * width / 2 * r + Vector((0, 0, math.sin(t) * height * r))
            if k in (0, ring):
                off.z = -0.05
            verts.append(tuple(p + off))
    for si in range(len(samples) - 1):
        for k in range(ring):
            a = si * (ring + 1) + k
            faces.append((a, a + 1, a + ring + 2, a + ring + 1))
    ob = reb.mesh_object(name, verts, faces, m)
    if floor_m is not None:
        fv, ff = [], []
        for si in range(len(samples) - 1):
            (p, d), (q, e) = samples[si], samples[si + 1]
            s0, s1 = Vector((-d.y, d.x, 0)), Vector((-e.y, e.x, 0))
            k = len(fv)
            for c in (p - s0 * width / 2, p + s0 * width / 2, q + s1 * width / 2, q - s1 * width / 2):
                fv.append((c.x, c.y, 0.0))
            ff.append((k, k + 1, k + 2, k + 3))
        reb.mesh_object(f"{name} floor", fv, ff, floor_m)
    return ob


# ---------------------------------------------------------------------------
# What moves
# ---------------------------------------------------------------------------


class Anim:
    """The scene's loop: register what moves, then pass to Room.export. Every
    movement comes back round to frame 0 at frame `frames`."""

    def __init__(self, frames=16, ticks=3, seed=5):
        self.frames = frames
        self.ticks = ticks
        self.moves = []
        self.rng = random.Random(seed)

    def spec(self):
        return {"frames": self.frames, "ticks": self.ticks, "set": self.pose}

    def pose(self, k):
        for f in self.moves:
            f(k)

    def phase(self, k, speed=1):
        return 2 * math.pi * speed * k / self.frames

    def flicker(self, light, glow=None, depth=0.25, dropouts=1):
        """A flame or a failing bulb: brightness wanders, now and then dips."""
        base = light.data.energy
        gbase = None
        if glow is not None:
            for n in glow.node_tree.nodes:
                if n.type == "EMISSION":
                    gbase = n.inputs["Strength"].default_value
        seq = [1.0] + [1.0 + self.rng.uniform(-depth, depth * 0.4) for _ in range(self.frames - 1)]
        for _ in range(dropouts):
            seq[self.rng.randrange(1, self.frames)] = 0.35

        def f(k):
            light.data.energy = base * seq[k]
            if gbase is not None:
                reb.emit_strength(glow, gbase * seq[k])
        self.moves.append(f)

    def blink(self, light, glow=None, on=(0, 8)):
        """Lights on for frames on[0] .. on[1] - 1 of the loop: a hazard lamp, a warning light."""
        base = light.data.energy
        gbase = None
        if glow is not None:
            for n in glow.node_tree.nodes:
                if n.type == "EMISSION":
                    gbase = n.inputs["Strength"].default_value

        def f(k):
            lit = on[0] <= k < on[1]
            light.data.energy = base if lit else 0
            if gbase is not None:
                reb.emit_strength(glow, gbase if lit else 0.1)
        self.moves.append(f)

    def sway(self, ob, amount=0.07, along=(1.0, 0.4), every=3, tip=2):
        """Grass, reeds, cloth edges: every `every`th vertex from `tip` sways in a gust that rolls across."""
        rest = [v.co.copy() for v in ob.data.vertices]

        def f(k):
            ph = self.phase(k)
            for i in range(tip, len(rest), every):
                p = rest[i]
                w = math.sin(ph + p.x * 0.6 + p.y * 0.25)
                ob.data.vertices[i].co = (p.x + amount * w * along[0], p.y + amount * w * along[1], p.z)
            ob.data.update()
        self.moves.append(f)

    def swing(self, ob, axis=0, degrees=4, pivot_rest=None):
        """A hanging thing swinging: a lamp, a sign on one hook, a body on a rope."""
        rest = ob.rotation_euler.copy()

        def f(k):
            r = rest.copy()
            r[axis] += math.radians(degrees) * math.sin(self.phase(k))
            ob.rotation_euler = r
        self.moves.append(f)

    def spin(self, ob, axis=2, turns=1, symmetry=1):
        """A fan, a wheel, an anemometer: turns 1/symmetry of a revolution per loop
        times `turns`, so a blade lands where the next one was."""
        rest = ob.rotation_euler.copy()

        def f(k):
            r = rest.copy()
            r[axis] += 2 * math.pi * turns / symmetry * k / self.frames
            ob.rotation_euler = r
        self.moves.append(f)

    def bob(self, ob, height=0.03, speed=1):
        rest = ob.location.copy()

        def f(k):
            ob.location = rest + Vector((0, 0, height * math.sin(self.phase(k, speed))))
        self.moves.append(f)

    def flies(self, centre, count=9, radius=0.35, size=0.012):
        """Flies circling a body or a plate: each on its own looping orbit."""
        black = mat("black")
        bugs = []
        for i in range(count):
            b = reb.prim("sphere", "Fly", black, centre, (size * 1.6, size, size), segments=6)
            r = radius * self.rng.uniform(0.4, 1.0)
            h = self.rng.uniform(0.05, 0.4)
            speed = self.rng.choice((1, 2, -1, -2, 3))
            ph0 = self.rng.uniform(0, 2 * math.pi)
            wob = self.rng.uniform(0.3, 1.0)
            bugs.append((b, r, h, speed, ph0, wob))

        def f(k):
            for b, r, h, speed, ph0, wob in bugs:
                a = ph0 + self.phase(k, speed)
                b.location = (centre[0] + r * math.cos(a), centre[1] + r * math.sin(a) * wob, centre[2] + h + 0.06 * math.sin(2 * a))
        self.moves.append(f)

    def flap(self, wings, degrees=50):
        rests = [w.rotation_euler.copy() for w in wings]

        def f(k):
            for w, rest, side in zip(wings, rests, (-1, 1)):
                r = rest.copy()
                r[0] = side * math.radians(degrees) * math.sin(self.phase(k, 2))
                w.rotation_euler = r
        self.moves.append(f)

    def ripple(self, water_mat=None, speed=1):
        """Water: turns the ripple texture's phase round once a loop."""
        m = water_mat or mat("water")
        wave = m.node_tree.nodes["Ripples"]

        def f(k):
            wave.inputs["Phase Offset"].default_value = self.phase(k, speed)
        self.moves.append(f)

    def drip(self, at, fall=1.0, size=0.012, m=None):
        """A drop falling from `at` once a loop: a leak, blood from a table edge."""
        d = reb.prim("sphere", "Drop", m or mat("water"), at, (size, size, size * 1.6), segments=6)

        def f(k):
            t = k / self.frames
            d.location = (at[0], at[1], at[2] - fall * t * t)
            d.hide_render = t > 0.95
        self.moves.append(f)

    def custom(self, f):
        """Anything else: f(k) poses frame k."""
        self.moves.append(f)


def vista(rng, centre, toward, below=-60.0, ridges=3, far=(160, 420), spread=200, forest=(0.03, 0.06, 0.035), rock=(0.05, 0.08, 0.06), haze=(0.45, 0.5, 0.58)):
    """What lies beyond the edge: a valley floor `below` metres down, dark
    with forest, and ridge after ridge of mountains fading into the haze,
    toward the floor direction `toward` (dx, dy). Big, rough and far off: it
    only has to read at 320 x 240."""
    c = Vector((centre[0], centre[1], 0))
    fwd = Vector((toward[0], toward[1], 0)).normalized()
    side = Vector((-fwd.y, fwd.x, 0))
    floor_m = reb.mat_surface("Valley forest", [(0.0, tuple(v * 0.6 for v in forest)), (1.0, forest)], scale=0.08, bump=0.0)
    verts, faces = [], []
    n = 30
    for j in range(n + 1):
        for i in range(n + 1):
            u, v = (i / n - 0.5) * spread * 3, 30 + j / n * far[1]
            p = c + side * u + fwd * v
            verts.append((p.x, p.y, below + 8 * noise.noise(Vector((p.x * 0.01, p.y * 0.01, 2)))))
    for j in range(n):
        for i in range(n):
            a = j * (n + 1) + i
            faces.append((a, a + 1, a + n + 2, a + n + 1))
    reb.mesh_object("Valley floor", verts, faces, floor_m)
    for r in range(ridges):
        dist = far[0] + (far[1] - far[0]) * r / max(1, ridges - 1)
        fade = 0.25 + 0.55 * r / max(1, ridges - 1)
        rm = _ridge_material(f"Ridge {r}", forest, rock, haze, fade, below)
        verts, faces = [], []
        m, rows, depth = 70, 6, 60.0 + 25 * r
        seed = rng.uniform(0, 100)
        for j in range(rows + 1):
            for i in range(m + 1):
                u = (i / m - 0.5) * spread * (3 + r)
                peak = 70 + 90 * (0.5 + noise.noise(Vector((u * 0.005, seed, r)))) + 30 * noise.noise(Vector((u * 0.025, seed, 1)))
                t = j / rows
                base = c + fwd * (dist + depth * t) + side * u
                hgt = peak * (t ** 0.6) + 8 * noise.noise(Vector((u * 0.05, t * 3, seed)))
                verts.append((base.x, base.y, below - 10 + hgt))
        for j in range(rows):
            for i in range(m):
                a0 = j * (m + 1) + i
                faces.append((a0, a0 + 1, a0 + m + 2, a0 + m + 1))
        reb.mesh_object(f"Ridge {r}", verts, faces, rm)


def _ridge_material(name, forest, rock, haze, fade, below):
    """Forest on a ridge's lower slopes, bare rock above, all of it washed
    toward the haze by `fade` (0 near, 1 lost in it)."""
    m, nodes, links, bsdf = reb.nodes_material(name)
    bsdf.inputs["Roughness"].default_value = 1.0
    geo = nodes.new("ShaderNodeNewGeometry")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(geo.outputs["Position"], sep.inputs["Vector"])
    rng_ = nodes.new("ShaderNodeMapRange")
    rng_.inputs["From Min"].default_value = below
    rng_.inputs["From Max"].default_value = below + 150
    links.new(sep.outputs["Z"], rng_.inputs["Value"])
    n = reb.noise_tex(nodes, links, 0.05, 4, 0.6)
    add = nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    links.new(rng_.outputs["Result"], add.inputs[0])
    sub = nodes.new("ShaderNodeMath")
    sub.operation = "MULTIPLY_ADD"
    sub.inputs[1].default_value = 0.3
    sub.inputs[2].default_value = -0.15
    links.new(n.outputs["Fac"], sub.inputs[0])
    links.new(sub.outputs[0], add.inputs[1])
    mix = lambda c: tuple(x * (1 - fade) + h * fade for x, h in zip(c, haze))
    reb.ramp(nodes, links, add.outputs[0], [(0.0, mix(forest)), (0.45, mix(tuple(v * 1.3 for v in forest))), (0.6, mix(rock)), (1.0, mix(tuple(min(1, v * 1.8) for v in rock)))])
    r = [nd for nd in nodes if nd.type == "VALTORGB"][-1]
    links.new(r.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def time_light(time, sun_heading=None, sun_energy=None, mist=None, sky=None):
    """reb.light_for plus a sky gradient that suits the hour. mist: (centre, scale, density)."""
    if mist:
        reb.light_for(time, mist_box=(mist[0], mist[1]), mist_density=mist[2])
    else:
        reb.light_for(time)
    sun = bpy.data.objects["Sun" if time != "night" else "Moon"]
    if sun_heading is not None:
        sun.rotation_euler[2] = math.radians(sun_heading)
    if sun_energy is not None:
        sun.data.energy = sun_energy
    skies = {
        "dawn": ((0.9, 0.62, 0.48), (0.32, 0.38, 0.6), 0.8),
        "morning": ((0.82, 0.78, 0.68), (0.3, 0.45, 0.72), 0.95),
        "noon": ((0.66, 0.68, 0.7), (0.38, 0.45, 0.55), 0.85),
        "afternoon": ((0.78, 0.68, 0.55), (0.32, 0.4, 0.56), 0.85),
        "dusk": ((0.8, 0.36, 0.17), (0.1, 0.09, 0.18), 0.75),
        "night": ((0.03, 0.035, 0.05), (0.004, 0.006, 0.012), 1.0),
    }
    h, z, s = sky or skies[time]
    _sky(h, z, s, sun)
    return sun


def _sky(horizon, zenith, strength, sun):
    """The sky by elevation: `horizon` at the horizon and below, `zenith`
    overhead, and a glow round the sun. (A world shader's direction runs -1
    to 1; reb.gradient_sky reads it as 0 to 1, which puts its below-horizon
    colour across the low sky.)"""
    world = bpy.context.scene.world
    nodes, links = world.node_tree.nodes, world.node_tree.links
    bg = nodes["Background"]
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    r = nodes.new("ShaderNodeValToRGB")
    els = r.color_ramp.elements
    els[0].position, els[0].color = 0.0, (*horizon, 1)
    els[1].position, els[1].color = 0.55, (*zenith, 1)
    mid = els.new(0.12)
    mid.color = tuple((a * 2 + b) / 3 for a, b in zip(horizon, zenith)) + (1,)
    links.new(sep.outputs["Z"], r.inputs["Fac"])
    sun_dir = sun.matrix_world.to_quaternion() @ Vector((0, 0, 1))
    dot = nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    links.new(tc.outputs["Generated"], dot.inputs[0])
    dot.inputs[1].default_value = tuple(sun_dir)
    clamp = nodes.new("ShaderNodeClamp")
    links.new(dot.outputs["Value"], clamp.inputs[0])
    glow = nodes.new("ShaderNodeMath")
    glow.operation = "POWER"
    glow.inputs[1].default_value = 16.0
    links.new(clamp.outputs[0], glow.inputs[0])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "ADD"
    links.new(glow.outputs[0], mix.inputs["Factor"])
    links.new(r.outputs["Color"], mix.inputs["A"])
    mix.inputs["B"].default_value = (*[min(1.0, c * 1.2) for c in sun.data.color], 1)
    links.new(mix.outputs["Result"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
