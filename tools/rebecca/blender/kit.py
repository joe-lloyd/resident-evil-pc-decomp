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

import bmesh
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
    def __init__(self, bounds, inside=False, shift=(0.0, 0.0)):
        """`shift` (metres, x and y) moves the whole scene at export, to make
        room on one side: the game's floor must stay within 0.6-19 m. The
        scene is still written in its own coordinates."""
        self.bounds = bounds
        self.inside = inside
        self.shift = shift
        self.cameras = []
        self.eyes = []
        self.notes = []
        self.doors = []
        self.checks = []
        self.voids = []
        self.saves = {}
        self.items = []
        self.spots = []
        self.states = []
        self.entry = None
        self.underfoot = None
        self.floors = []

    def camera(self, eye, look, fov=190, note=""):
        self.cameras.append({"from": G(*eye), "to": G(*look), "fov": fov})
        self.notes.append(note)
        self.eyes.append(Vector(eye))

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

    def save_room(self, typewriter, box, lid):
        """The room's typewriter and item box: the zones she faces to use them,
        each the furniture's footprint and the strip of floor in front where
        she stands, as RE1's are; and the box's lid, as item_box() placed it."""
        rect = lambda r: {"x0": reb.g(r[0]), "z0": reb.g(r[1]), "x1": reb.g(r[2]), "z1": reb.g(r[3])}
        self.saves = {"typewriter": rect(typewriter), "box": rect(box), "lid": dict(lid)}
    def item(self, step, at):
        """Where the key item the plan's `step` gives lies (items/items.ts): `at`
        is (x, y, height) in metres, on the floor or on what it rests on."""
        x, y, z = at
        self.items.append({"step": step, "x": reb.g(x), "y": -reb.g(z), "z": reb.g(y)})

    def spot(self, step, zone):
        """Where she works the plan's `step` here (day/events.ts): the zone she
        stands in to use an item or press the action button, in metres."""
        x0, y0, x1, y1 = zone
        self.spots.append({"step": step, "zone": {"x0": reb.g(x0), "z0": reb.g(y0), "x1": reb.g(x1), "z1": reb.g(y1)}})

    def state(self, step, pose, motion=None, cameras=None, loop=False):
        """How the room looks once the plan's `step` has happened
        (day/events.ts, or a key item on a lock: scripts.ts): pose(True)
        makes the change, pose(False) undoes it. Rendered as a second background per
        camera and shown while the step's flag is set (room.ts looks the
        flag up). It may not move a mask() object, and the floor's walls
        stay as they were.

        motion=(frames, ticks) plays the change as it happens, through
        `cameras` (default all): pose(t) then poses it part way, t from 0
        to 1 (True is 1), so it must set things outright rather than move
        them by a step.
        loop=True renders the changed room through the scene's Anim too, for
        a change in moving light; loop=f also calls f(k) on loop frame k, for
        something that only moves once the change has happened (a wheel the
        water now turns), f(0) being its rest."""
        st = {"name": step, "bank": 1, "bit": -1, "set": pose}
        if motion:
            st["motion"] = {"frames": motion[0], "ticks": motion[1]}
        if cameras is not None:
            st["cameras"] = list(cameras)
        if loop:
            st["loop"] = loop
        self.states.append(st)

    def ground(self, kind):
        """What the floor is underfoot, for her footsteps (sound/ground.ts):
        earth, gravel, boards, rock, water, concrete, metal, lino or carpet.
        Every room says."""
        self.underfoot = kind

    def floor(self, rect, kind):
        """A part of the floor that is another kind underfoot than the room's
        ground: a boardwalk over mud, a puddle on rock. Where parts overlap,
        the first one given wins. A room has four kinds at most."""
        x0, y0, x1, y1 = rect
        self.floors.append({"kind": kind, "x0": reb.g(x0), "z0": reb.g(y0), "x1": reb.g(x1), "z1": reb.g(y1)})

    def void(self, rect):
        """Floor inside the bounds that is not there: a drop, a pit, deep water."""
        x0, y0, x1, y1 = rect
        self.voids.append({"x0": reb.g(x0), "z0": reb.g(y0), "x1": reb.g(x1), "z1": reb.g(y1)})

    def _apply_shift(self):
        """Move everything by self.shift: the scene's objects under one parent
        (so animated objects keep their keyframes), and every record."""
        dx, dy = self.shift
        if not dx and not dy:
            return
        root = bpy.data.objects.new("Scene shift", None)
        bpy.context.scene.collection.objects.link(root)
        root.location = (dx, dy, 0.0)
        for ob in list(bpy.data.objects):
            if ob is not root and ob.parent is None:
                ob.parent = root
        bpy.context.view_layer.update()
        gx, gz = reb.g(dx), reb.g(dy)
        x0, y0, x1, y1 = self.bounds
        self.bounds = (x0 + dx, y0 + dy, x1 + dx, y1 + dy)
        for c in self.cameras:
            c["from"] = (c["from"][0] + gx, c["from"][1], c["from"][2] + gz)
            c["to"] = (c["to"][0] + gx, c["to"][1], c["to"][2] + gz)
        rects = [d["zone"] for d in self.doors] + [c["zone"] for c in self.checks] + [sp["zone"] for sp in self.spots] + self.voids + self.floors
        if self.saves:
            rects += [self.saves["typewriter"], self.saves["box"]]
            self.saves["lid"]["x"] += gx
            self.saves["lid"]["z"] += gz
        for r in rects:
            r["x0"] += gx
            r["x1"] += gx
            r["z0"] += gz
            r["z1"] += gz
        for d in self.doors:
            d["arrive"]["x"] += gx
            d["arrive"]["z"] += gz
        for it in self.items:
            it["x"] += gx
            it["z"] += gz

    def _clear_lenses(self, reach=2.2):
        """Take needles and fern fronds off within `reach` metres of a camera's
        eye: the ragged spruces' low whorls hang at camera height, and a
        branch against the lens fills the shot."""
        foliage = ("Needles", "Fern")
        for ob in bpy.data.objects:
            if ob.type != "MESH" or not any(m and m.name.startswith(foliage) for m in ob.data.materials):
                continue
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            world = ob.matrix_world
            near = [f for f in bm.faces if any((world @ f.calc_center_median() - e).length < reach for e in self.eyes)]
            if near:
                bmesh.ops.delete(bm, geom=near, context="FACES")
                bm.to_mesh(ob.data)
            bm.free()

    def _fill(self, strength):
        """RE1's rooms are dim but their walls always read; ours went to black
        away from the lamps. An indoor room gets a soft warm light in the
        middle of its floor, unseen by the camera and in reflections, with
        soft shadows so corners stay dark, its power by the floor's area:
        enough to read the walls, not enough to flatten the lamps' pools."""
        if not self.inside or strength <= 0:
            return
        x0, y0, x1, y1 = self.bounds
        area = (x1 - x0) * (y1 - y0)
        light = bpy.data.lights.new("Room fill", "POINT")
        light.energy = strength * area
        light.color = (1.0, 0.88, 0.72)
        light.shadow_soft_size = 1.5
        ob = bpy.data.objects.new("Room fill", light)
        ob.location = ((x0 + x1) / 2, (y0 + y1) / 2, 1.7)
        ob.visible_camera = False
        ob.visible_glossy = False
        bpy.context.scene.collection.objects.link(ob)
        # The ceiling: the cameras sit just under it and the fill reaches it
        # at a grazing angle, so it went black in a band across the top of
        # the frame. What lights a real ceiling is the floor's bounce: a weak
        # light just under it, facing up, over most of the room.
        top = self._ceiling((x0 + x1) / 2, (y0 + y1) / 2)
        if top is None:
            return
        up = bpy.data.lights.new("Ceiling bounce", "AREA")
        up.shape = "RECTANGLE"
        up.size, up.size_y = (x1 - x0) * 0.8, (y1 - y0) * 0.8
        up.energy = 0.2 * strength * area
        up.color = (1.0, 0.9, 0.78)
        ob = bpy.data.objects.new("Ceiling bounce", up)
        ob.location = ((x0 + x1) / 2, (y0 + y1) / 2, top - 0.25)
        ob.rotation_euler = (math.pi, 0, 0)
        ob.visible_camera = False
        ob.visible_glossy = False
        bpy.context.scene.collection.objects.link(ob)

    def _ceiling(self, x, y):
        """The height of the ceiling straight up from the floor at (x, y), or
        None: the first rendered surface whose object spans most of the room
        (not a table, a lamp or a beam)."""
        dg = bpy.context.evaluated_depsgraph_get()
        x0, y0, x1, y1 = self.bounds
        z = 0.05
        while z < 12:
            hit, at, _n, _i, ob, _m = bpy.context.scene.ray_cast(dg, Vector((x, y, z)), Vector((0, 0, 1)), distance=12)
            if not hit:
                return None
            if not ob.hide_render and ob.dimensions.x >= 0.5 * (x1 - x0) and ob.dimensions.y >= 0.5 * (y1 - y0):
                return at.z
            z = at.z + 0.01
        return None

    def export(self, anim=None, samples=256, states=()):
        self._fill(float(os.environ.get("RE1_FILL") or "6"))
        self._clear_lenses()
        self._apply_shift()
        x0, y0, x1, y1 = self.bounds
        if min(x0, y0) < 0.6 or max(x1, y1) > 19.0:
            raise ValueError(f"the floor {self.bounds} is outside 0.6-19 m: shift the room or shrink it")
        print(f"[kit] {len(bpy.data.objects)} objects", flush=True)
        wear(float(os.environ.get("RE1_WEAR", "1.3")))
        x0, y0, x1, y1 = self.bounds
        if self.underfoot is None:
            raise ValueError("the room says nothing of its floor: call room.ground(kind)")
        extra = {
            "bounds": {"x0": reb.g(x0), "z0": reb.g(y0), "x1": reb.g(x1), "z1": reb.g(y1)},
            "ground": self.underfoot,
            "floors": self.floors,
            "voids": self.voids,
            "doors": self.doors,
            "checks": self.checks,
            "saves": self.saves or None,
            "items": self.items,
            "spots": self.spots,
            "entry": self.entry,
            "notes": self.notes,
        }
        reb.export(self.cameras, OUT, samples=samples, extra=extra,
                   anim=anim.spec() if anim and anim.moves else None, states=[*states, *self.states])


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
        # Stones a few centimetres across: finer than this averages away at 320 x 240.
        "gravel": lambda: s("Gravel", [(0.0, (0.08, 0.075, 0.065)), (0.4, (0.2, 0.19, 0.17)), (0.6, (0.26, 0.25, 0.22)), (1.0, (0.36, 0.34, 0.3))], scale=9, bump=1.0),
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
    down, fine speckle in blocky texels `texel` metres across, coarser grit
    that stays bitty at the game's size, grime dark in the corners and where
    things touch, and the colour muddied a little.
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
        # Grit: what makes RE1's surfaces bitty at 320 x 240. Blocky texels
        # about two and a half centimetres across, features a few times that,
        # bright and dark, and the same pattern roughening the surface so
        # specks catch the light. The speckle above is finer than a pixel at
        # the game's size and averages away; this does not.
        gsnap = nodes.new("ShaderNodeVectorMath"); gsnap.operation = "SNAP"
        gsnap.inputs[1].default_value = (texel * 2.2,) * 3
        links.new(shift.outputs[0], gsnap.inputs[0])
        gn = nodes.new("ShaderNodeTexNoise")
        gn.inputs["Scale"].default_value = 18
        gn.inputs["Detail"].default_value = 6
        gn.inputs["Roughness"].default_value = 0.8
        links.new(gsnap.outputs[0], gn.inputs["Vector"])
        gr = nodes.new("ShaderNodeMapRange")
        gr.inputs["From Min"].default_value, gr.inputs["From Max"].default_value = 0.25, 0.75
        gr.inputs["To Min"].default_value, gr.inputs["To Max"].default_value = 1 - 0.42 * k, 1 + 0.25 * k
        links.new(gn.outputs["Fac"], gr.inputs["Value"])
        gs = nodes.new("ShaderNodeVectorMath"); gs.operation = "SCALE"
        links.new(out, gs.inputs[0]); links.new(gr.outputs["Result"], gs.inputs["Scale"])
        out = gs.outputs[0]
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = min(1.0, 0.3 * k)
        bump.inputs["Distance"].default_value = 0.01
        links.new(gn.outputs["Fac"], bump.inputs["Height"])
        normal = bsdf.inputs["Normal"]
        if normal.is_linked:
            links.new(normal.links[0].from_socket, bump.inputs["Normal"])
        links.new(bump.outputs["Normal"], normal)
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
    """Join objects into one (keeping their materials, and each part's
    modifiers made real first: Blender's join keeps only the first part's,
    and would smooth or bevel every part by them). The result has no turn or
    scale of its own and its origin at `origin`, or at the first part's
    location if None. Build a prop's parts around (0, 0, 0), join with
    origin=(0, 0, 0), then set its location and turn to place it."""
    parts = [p for p in parts if p is not None]
    if not parts:
        return None
    if len(parts) > 1 and any(p.modifiers for p in parts):
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        for p in parts:
            if p.type == "MESH" and p.modifiers:
                me = bpy.data.meshes.new_from_object(p.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
                p.modifiers.clear()
                p.data = me
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


def loft(name, sections, mats, ring=32, material_of=None, holes=None, shell=0.0, subdiv=2):
    """A smooth body through cross-sections along x: a fuselage, a cab, a
    bonnet. Each section is (x, half width, bottom z, top z, n): a rounded
    rectangle across y-z, squarer as n grows (2 is an ellipse). Both ends
    are closed. `mats` are its materials; `material_of(centre)` picks each
    face's (an index into mats, by the face's centre), and `holes(centre)`
    cuts the faces it is true for: doors, open hatches. `shell` gives it
    walls that thick, the inside in mats[-1]."""
    bm = bmesh.new()
    rings = []
    for x, hw, zb, zt, n in sections:
        mid, hh = (zb + zt) / 2, (zt - zb) / 2
        pts = []
        for k in range(ring):
            t = 2 * math.pi * k / ring
            c, s_ = math.cos(t), math.sin(t)
            y = hw * math.copysign(abs(c) ** (2 / n), c)
            z = mid + hh * math.copysign(abs(s_) ** (2 / n), s_)
            pts.append(bm.verts.new((x, y, z)))
        rings.append(pts)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(ring):
            bm.faces.new((r0[k], r0[(k + 1) % ring], r1[(k + 1) % ring], r1[k]))
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if holes:
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if holes(f.calc_center_median())], context="FACES")
    if material_of:
        for f in bm.faces:
            f.material_index = material_of(f.calc_center_median())
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if subdiv:
        sub = ob.modifiers.new("Smooth", "SUBSURF")
        sub.levels = sub.render_levels = subdiv
    if shell:
        sol = ob.modifiers.new("Shell", "SOLIDIFY")
        sol.thickness = shell
        sol.material_offset = len(mats) - 1
        sol.use_even_offset = True
    return ob


def crag(rng, verts, faces, centre, size, floor=-0.35):
    """A mass of granite: lumpy, its facets a hand across, `size` (x, y, z
    half-sizes), flat underneath where it was split off. Into verts and
    faces, for one mesh of many (shade it flat)."""
    # Facets a hand across, not half a metre: at 4 the big blocks read as flat triangles.
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=6, radius=1)
    tmp = bpy.context.active_object
    seed = rng.uniform(0, 100)
    k = len(verts)
    for v in tmp.data.vertices:
        n = v.co.normalized()
        d = 1 + 0.4 * noise.noise(n * 1.4 + Vector((seed, 0, 0))) + 0.15 * noise.noise(n * 4.5 + Vector((0, seed, 0))) + 0.06 * noise.noise(n * 12 + Vector((seed, seed, 0))) + 0.025 * abs(noise.noise(n * 34 + Vector((seed, 0, seed))))
        p = n * d
        p.z = max(p.z, floor + 0.05 * noise.noise(n * 3 + Vector((0, 0, seed))))
        verts.append((centre[0] + p.x * size[0], centre[1] + p.y * size[1], centre[2] + p.z * size[2]))
    faces.extend([tuple(k + i for i in poly.vertices) for poly in tmp.data.polygons])
    bpy.data.objects.remove(tmp)


def wheel(name, at, r=0.38, width=0.27, rim=None, flat=0.0, detail=False):
    """A tyre on a steel rim, its axle along y, centred on `at`: the tyre's
    shoulders rounded, the rim dished with a hub cap. `flat` squashes it
    onto the ground (a slashed tyre). Returns the parts."""
    rim = rim or mat("steel")
    tyre = reb.prim("cyl", f"{name} tyre", mat("rubber"), at, (2 * r, 2 * r, width), rot=(math.pi / 2, 0, 0), segments=32)
    bev = tyre.modifiers.new("Shoulders", "BEVEL")
    bev.width = width * 0.3
    bev.segments = 3
    parts = [tyre]
    for side in (-1, 1):
        y = at[1] + side * (width / 2 - 0.01)
        parts.append(reb.prim("cyl", f"{name} rim", rim, (at[0], y, at[2]), (1.15 * r, 1.15 * r, 0.03), rot=(math.pi / 2, 0, 0), segments=24))
        parts.append(reb.prim("sphere", f"{name} hub", rim, (at[0], y + side * 0.02, at[2]), (0.4 * r, 0.12, 0.4 * r), segments=12))
    if detail:
        for side in (-1,1):
            for i in range(6):
                a=math.tau*i/6
                parts.append(reb.prim("cyl",f"{name} lug",mat("iron"),(at[0]+math.cos(a)*r*0.34,at[1]+side*(width/2+0.025),at[2]+math.sin(a)*r*0.34),(0.04,0.04,0.025),rot=(math.pi/2,0,0),segments=6))
        for i in range(28):
            a=math.tau*i/28
            parts.append(box(f"{name} tread",mat("rubber"),(at[0]+math.cos(a)*r,at[1],at[2]+math.sin(a)*r),(0.075,width*0.9,0.025),bevel=0.004))
            parts[-1].rotation_euler[1]=math.pi/2-a
    if flat:
        for p in parts:
            p.scale.z = 1 - flat
            p.location.z -= r * flat * 0.9
    return parts


def pickup(name, paint, door_open=None, door_side=1, glass_gone=False, flat=0.0):
    """A 1970s pickup, nose toward +x, wheels on z = 0, centred on the
    origin, 5.4 m long: cab and bonnet one rounded body with its windscreen,
    side and back windows; the bed open on top; wheel arches cut round the
    tyres; chrome grille, bumpers and mirrors. `door_open` swings the
    driver's door (on the +y side, or -y with door_side -1) that far out,
    radians, leaving its doorway open. `glass_gone` leaves the windows empty.
    Returns (body, the door's hinge or None): put what hangs on the door on
    the hinge."""
    chrome = reb.mat_metal("Chrome", (0.6, 0.6, 0.58), 0.25)
    glass = reb.mat_glass("Pickup glass", (0.35, 0.4, 0.4))
    dark = mat("black")
    inside = reb.mat_plain("Cab inside", (0.04, 0.035, 0.03), 0.8)
    wheels_x = (1.72, -1.68)

    def arch(c):
        x, y, z = c
        return abs(y) > 0.55 and any(math.hypot(x - wx, z - 0.38) < 0.5 for wx in wheels_x)

    def window(c):
        x, y, z = c
        if 0.98 < x < 1.4 and z > 1.22 and abs(y) < 0.82:
            return True                                    # windscreen
        if abs(y) > 0.7 and 1.3 < z < 1.78 and -0.06 < x < 1.0:
            return True                                    # side windows
        return False

    def doorway(c):
        x, y, z = c
        return door_open is not None and y * door_side > 0.55 and -0.08 < x < 1.32 and 0.58 < z < 1.84

    def cab_faces(c):
        x, y, z = c
        if window(c):
            return 1
        if x > 2.7:
            return 2                                       # the nose: dark behind the grille's bars
        return 0

    cab = loft(f"{name} cab", [
        (2.74, 0.84, 0.56, 1.0, 8), (2.66, 0.92, 0.5, 1.08, 10), (1.5, 0.93, 0.5, 1.14, 10), (1.38, 0.93, 0.5, 1.19, 10),
        (0.98, 0.88, 0.5, 1.86, 8), (-0.06, 0.9, 0.5, 1.88, 8), (-0.18, 0.9, 0.5, 1.84, 8)],
        [paint, glass, dark, inside], ring=40, material_of=cab_faces,
        holes=lambda c: arch(c) or doorway(c) or (glass_gone and window(c)), shell=0.03)
    bed = loft(f"{name} bed", [(-0.28, 0.92, 0.5, 1.2, 10), (-2.6, 0.92, 0.5, 1.2, 10), (-2.66, 0.9, 0.52, 1.18, 8)],
               [paint, inside], ring=40, holes=lambda c: arch(c) or (c[2] > 1.1 and abs(c[1]) < 0.86 and -2.58 < c[0] < -0.32), shell=0.04)
    parts = [cab, bed,
             reb.prim("cube", f"{name} bed floor", mat("planks"), (-1.45, 0, 0.82), (2.25, 1.74, 0.04)),
             reb.prim("cube", f"{name} chassis", dark, (0.05, 0, 0.42), (5.0, 1.3, 0.2)),
             reb.prim("cube", f"{name} seat", reb.mat_plain("Seat vinyl", (0.08, 0.06, 0.05), 0.5), (0.25, 0, 0.98), (0.55, 1.6, 0.16), bevel=0.04),
             reb.prim("cube", f"{name} seat back", reb.mat_plain("Seat vinyl", (0.08, 0.06, 0.05), 0.5), (0.0, 0, 1.3), (0.14, 1.6, 0.6), rot=(0, -0.15, 0), bevel=0.04),
             reb.prim("cube", f"{name} dash", inside, (1.2, 0, 1.12), (0.35, 1.7, 0.22)),
             reb.prim("cube", f"{name} back window", glass if not glass_gone else inside, (-0.2, 0, 1.55), (0.02, 1.2, 0.36)),
             reb.prim("cyl", f"{name} wheel", dark, (0.95, 0.42 * door_side, 1.32), (0.4, 0.4, 0.03), rot=(0, 1.1, 0), segments=16)]
    # Grille bars and its frame, the lamps in it, the bumpers wrapping the corners.
    for z in (0.7, 0.81, 0.92):
        parts.append(reb.prim("cube", f"{name} grille bar", chrome, (2.75, 0, z), (0.03, 1.2, 0.025)))
    parts.append(reb.prim("cube", f"{name} grille frame", chrome, (2.745, 0, 0.81), (0.03, 1.66, 0.4)))
    for y in (-0.66, 0.66):
        parts.append(reb.prim("cube", f"{name} lamp bezel", chrome, (2.74, y, 0.85), (0.05, 0.3, 0.3), bevel=0.02))
        parts.append(reb.prim("cyl", f"{name} headlamp", reb.mat_plain("Headlamp glass", (0.7, 0.7, 0.62), 0.1), (2.77, y, 0.85), (0.22, 0.22, 0.03), rot=(0, math.pi / 2, 0), segments=16))
        parts.append(reb.prim("cube", f"{name} tail lamp", reb.mat_plain("Tail lamp", (0.4, 0.03, 0.02), 0.3), (-2.68, y * 1.3, 1.0), (0.04, 0.12, 0.26)))
    for x, d in ((2.86, 1), (-2.74, -1)):
        parts.append(reb.prim("cube", f"{name} bumper", chrome, (x, 0, 0.55), (0.12, 1.86, 0.2), bevel=0.03))
        for y in (-0.9, 0.9):
            parts.append(reb.prim("cube", f"{name} bumper end", chrome, (x - d * 0.12, y, 0.55), (0.24, 0.1, 0.2), rot=(0, 0, d * math.copysign(0.4, y)), bevel=0.03))
    for y in (-1, 1):
        parts.append(rod(f"{name} mirror arm", chrome, (1.0, y * 0.9, 1.3), (1.05, y * 1.12, 1.5), 0.012, 6))
        parts.append(reb.prim("cube", f"{name} mirror", dark, (1.05, y * 1.14, 1.55), (0.05, 0.12, 0.2), bevel=0.01))
        parts.append(reb.prim("cube", f"{name} handle", chrome, (0.05, y * 0.935, 1.28), (0.16, 0.02, 0.03)))
        # Rails along the top of the bed's sides.
        parts.append(reb.prim("cube", f"{name} bed rail", paint, (-1.45, y * 0.9, 1.21), (2.32, 0.1, 0.03), bevel=0.01))
    for wx in wheels_x:
        for y in (-0.8, 0.8):
            parts += wheel(f"{name} wheel", (wx, y, 0.38), flat=flat if (wx > 0 and y < 0) or (wx < 0 and y > 0) else 0.0)
    body = join(name, parts, origin=(0, 0, 0))
    hinge = None
    if door_open is not None:
        hinge = reb.prim("sphere", f"{name} door hinge", dark, (1.3, door_side * 0.93, 1.15), (0.03, 0.03, 0.03))
        door = reb.prim("cube", f"{name} door", paint, (-0.68, 0.0, -0.2), (1.36, 0.06, 0.62), bevel=0.02)
        frame = [reb.prim("cube", f"{name} door frame", paint, (-0.68, 0.0, 0.62), (1.36, 0.05, 0.04)),
                 reb.prim("cube", f"{name} door frame", paint, (-1.33, 0.0, 0.36), (0.05, 0.05, 0.5)),
                 reb.prim("cube", f"{name} door frame", paint, (-0.03, 0.0, 0.36), (0.05, 0.05, 0.5), rot=(0, -0.3, 0))]
        pane = [] if glass_gone else [reb.prim("cube", f"{name} door glass", glass, (-0.68, 0.0, 0.36), (1.25, 0.015, 0.5))]
        trim = reb.prim("cube", f"{name} door inside", inside, (-0.68, -door_side * 0.035, -0.2), (1.3, 0.01, 0.58))
        for p in [door, trim] + frame + pane:
            p.parent = hinge
        # Out from the cab: the door runs back (-x) from its hinge.
        hinge.rotation_euler = (0, 0, -door_side * door_open)
        hinge.parent = body
    return body, hinge


def tube(name, m, points, r, segments=12):
    """A round tube of radius r bending smoothly through `points` (a skid, a
    rail, a pipe), its ends capped: a mesh, like rod's."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("NURBS")
    sp.points.add(len(points) - 1)
    for p, q in zip(sp.points, points):
        p.co = (*q, 1)
    sp.order_u = min(3, len(points))
    sp.use_endpoint_u = True
    sp.resolution_u = 8
    cu.bevel_depth = r
    cu.bevel_resolution = max(1, segments // 4 - 1)
    cu.use_fill_caps = True
    tmp = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(tmp)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    for poly in me.polygons:
        poly.use_smooth = True
    me.materials.clear()
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
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


def box_center(name, m, at, size, rot=0.0, bevel=0.0):
    """A box positioned by its centre, turned about z. box() uses its foot."""
    return reb.prim("cube", name, m, at, size, rot=(0, 0, rot), bevel=bevel)


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


def typewriter(name, at, rot=0.0, body_m=None, page=True):
    """A heavy black office typewriter standing on `at` (its bottom centre),
    its keys toward +y turned by `rot` about z, a page wound into it. One
    mesh, about 0.36 x 0.32 m: big shapes that still read at 320 x 240."""
    body = body_m or reb.mat_metal("Typewriter enamel", (0.018, 0.018, 0.02), 0.25)
    keys = reb.mat_plain("Typewriter keys", (0.5, 0.48, 0.42), 0.5)
    platen = mat("rubber")
    parts = [
        reb.prim("cube", "frame", body, (0, -0.02, 0.05), (0.34, 0.24, 0.1), bevel=0.012),
        # The keyboard's slope down toward her.
        reb.prim("cube", "deck", body, (0, 0.1, 0.04), (0.32, 0.12, 0.05), rot=(-0.35, 0, 0), bevel=0.008),
        # The type basket's hood and the carriage across the back.
        reb.prim("cyl", "hood", body, (0, -0.02, 0.1), (0.26, 0.12, 0.08), rot=(0, math.pi / 2, 0), segments=16),
        reb.prim("cube", "carriage", body, (0, -0.1, 0.15), (0.4, 0.07, 0.05), bevel=0.006),
        reb.prim("cyl", "platen", platen, (0, -0.1, 0.18), (0.05, 0.05, 0.42), rot=(0, math.pi / 2, 0), segments=14),
    ]
    for side in (-1, 1):
        parts.append(reb.prim("cyl", "knob", platen, (side * 0.225, -0.1, 0.18), (0.045, 0.045, 0.03), rot=(0, math.pi / 2, 0), segments=12))
        parts.append(reb.prim("cyl", "spool", body, (side * 0.1, -0.02, 0.145), (0.06, 0.06, 0.015), segments=12))
    parts.append(rod("return lever", mat("steel"), (-0.2, -0.08, 0.2), (-0.27, 0.0, 0.24), 0.006))
    for row in range(4):
        for k in range(10 - (row == 3) * 2):
            x = (k - 4.5 + (row == 3)) * 0.028 + row * 0.006
            parts.append(reb.prim("cyl", "key", keys, (x, 0.145 - row * 0.03, 0.07 + row * 0.011), (0.02, 0.02, 0.012), segments=8))
    parts.append(reb.prim("cube", "space bar", keys, (0, 0.17, 0.06), (0.16, 0.018, 0.01)))
    if page:
        paper = reb.prim("cube", "page", mat("paper"), (0, -0.13, 0.3), (0.21, 0.004, 0.24), rot=(-0.25, 0, 0))
        parts.append(paper)
    ob = join(name, parts, origin=(0, 0, 0))
    ob.location = at
    ob.rotation_euler = (0, 0, rot)
    return ob


# RE1's item box: its lid is a 3D object of the game's own, the same in every
# save room (object model 0 of ROOM1000, 1440 x 2160 units, hinged along one
# long edge), placed by the room script on a body painted into the background.
ITEM_BOX_DEPTH = 1440 / reb.UNITS
ITEM_BOX_WIDTH = 2160 / reb.UNITS
# The lid sits at game Y -1440 and reaches 51 units below that: the body's top.
ITEM_BOX_HEIGHT = (1440 - 51) / reb.UNITS
ITEM_BOX_LID_Y = -1440


def item_box(name, at, face, scale=1.0):
    """The body of RE1's item box on the floor at `at` (x, y: its middle), its
    front toward `face` (one of the four axis directions), in the look of the
    game's lid: dark rusted metal in dull embossed trim. `scale` shrinks it
    and the lid together, for a small room. Not masked: it stands against a
    wall, and a mask would draw over the lid. Returns the lid's placement for
    the room script: game x, y, z of its hinge, its angle and its scale."""
    fx, fy = face
    w, d, h = ITEM_BOX_WIDTH * scale, ITEM_BOX_DEPTH * scale, ITEM_BOX_HEIGHT * scale
    rust = reb.mat_surface("Item box rust", [(0.0, (0.06, 0.035, 0.025)), (0.6, (0.12, 0.07, 0.045)), (1.0, (0.24, 0.11, 0.05))], scale=14, rough=0.6, bump=0.35)
    trim = reb.mat_surface("Item box trim", [(0.0, (0.1, 0.095, 0.09)), (0.5, (0.18, 0.17, 0.16)), (1.0, (0.26, 0.25, 0.23))], scale=40, rough=0.45, bump=0.8)
    # Built facing +y (south), then turned.
    parts = [reb.prim("cube", "body", rust, (0, 0, h / 2), (w - 0.02, d - 0.02, h), bevel=0.006)]
    t = 0.07 * scale
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(reb.prim("cube", "corner", trim, (sx * (w / 2 - t / 2), sy * (d / 2 - t / 2), h / 2), (t, t, h), bevel=0.008))
    parts.append(reb.prim("cube", "rim", trim, (0, 0, h - t / 2), (w, d, t), bevel=0.008))
    parts.append(reb.prim("cube", "plinth", trim, (0, 0, 0.04 * scale), (w + 0.01, d + 0.01, 0.08 * scale), bevel=0.008))
    parts.append(reb.prim("cube", "front panel frame", trim, (0, d / 2 - 0.004, h * 0.48), (w * 0.62, 0.012, h * 0.55), bevel=0.004))
    parts.append(reb.prim("cube", "front panel", rust, (0, d / 2 + 0.002, h * 0.48), (w * 0.56, 0.012, h * 0.47)))
    parts.append(reb.prim("cube", "lock plate", trim, (0, d / 2 + 0.01, h - 0.11 * scale), (0.12 * scale, 0.012, 0.1 * scale), bevel=0.003))
    ob = join(name, parts, origin=(0, 0, 0))
    ob.location = (at[0], at[1], 0.0)
    # Front +y turned to `face`: +y is angle 3072, the game's south.
    yaw = math.atan2(fy, fx) - math.pi / 2
    ob.rotation_euler = (0, 0, yaw)
    reb.wall(ob)
    hinge = (at[0] - fx * d / 2, at[1] - fy * d / 2)
    return {"x": reb.g(hinge[0]), "z": reb.g(hinge[1]), "y": round(ITEM_BOX_LID_Y * scale), "angle": angle(face), "scale": scale}


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
# (legs out toward +x). Left side is +y. corpses.py poses each MakeHuman body
# to these; body() lays a pool or a sheet by them.
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

# What corpses.py baked into each vertex's "part": 1 + an index here.
_PARTS = ["upperarm_l", "lowerarm_l", "hand_l", "upperarm_r", "lowerarm_r", "hand_r",
          "thigh_l", "calf_l", "foot_l", "thigh_r", "calf_r", "foot_r"]
# A missing joint takes the bone ending there and every bone below it.
_BELOW = {"elbow": ("upperarm", "lowerarm", "hand"), "hand": ("lowerarm", "hand"),
          "knee": ("thigh", "calf", "foot"), "foot": ("calf", "foot")}
_LIBRARY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "corpses.blend")
_corpses = {}


def _corpse(figure, pose):
    """The baked corpse from corpses.blend (blender/build-corpses.ts), appended once."""
    key = f"Corpse {figure} {pose}"
    if key not in _corpses:
        if not os.path.exists(_LIBRARY):
            raise RuntimeError(f"{_LIBRARY} is missing: run tools/rebecca/blender/build-corpses.ts")
        with bpy.data.libraries.load(_LIBRARY) as (_, dst):
            dst.objects = [key]
        _corpses[key] = dst.objects[0]
    return _corpses[key]


def _cut(me, missing, mirror, flesh):
    """Take the missing limbs off the mesh and close each stump with `flesh`."""
    gone = set()
    for joint in missing:
        side, what = joint.split("_", 1)
        if mirror:
            side = "r" if side == "l" else "l"
        gone |= {_PARTS.index(f"{b}_{side}") + 1 for b in _BELOW[what]}
    bm = bmesh.new()
    bm.from_mesh(me)
    part = bm.verts.layers.int.get("part")
    for e in bm.edges:
        e.tag = e.is_boundary
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[part] in gone], context="VERTS")
    me.materials.append(flesh)
    stumps = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary and not e.tag], sides=0)
    for f in stumps["faces"]:
        f.material_index = len(me.materials) - 1
    bm.to_mesh(me)
    bm.free()


def body(name, at, heading=0.0, pose="back", top=None, legs=None, bloody=0.0, seed=0, sheet=False, missing=(), figure="man"):
    """A dead man (or, `figure` "woman", a woman): `pose` back, front or
    slumped; head toward `heading` (radians from +x). `top` and `legs` are
    clothing materials; `bloody` lays a pool under him; `sheet` covers him;
    `missing` lists parts gone ("l_hand", "r_knee"...: the limb below that
    joint). An odd `seed` lays him out mirrored."""
    rng = random.Random(seed)
    j = {k: Vector(v) for k, v in _POSES[pose].items()}
    me = _corpse(figure, pose).data.copy()
    mirror = seed % 2 == 1
    if mirror:
        me.transform(Matrix.Scale(-1, 4, (0, 1, 0)))
        me.flip_normals()
    for i, m in enumerate(me.materials):
        slot = m.name.split(".")[0]
        if slot in ("top", "legs"):
            me.materials[i] = (top or mat("flannel")) if slot == "top" else (legs or mat("denim"))
    if missing:
        _cut(me, missing, mirror, mat("old blood"))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
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
    # The valley's forest, speckled with single trees like the ridges', or it reads as a flat lake from above.
    floor_m = _ridge_material("Valley forest", forest, rock, haze, 0.2, below)
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
        m, rows, depth = 220, 16, 60.0 + 25 * r
        seed = rng.uniform(0, 100)
        for j in range(rows + 1):
            for i in range(m + 1):
                u = (i / m - 0.5) * spread * (3 + r)
                peak = 70 + 90 * (0.5 + noise.noise(Vector((u * 0.005, seed, r)))) + 30 * noise.noise(Vector((u * 0.025, seed, 1)))
                # Crags along the crest, sharp where the noise turns.
                peak += 14 * (0.5 - abs(noise.noise(Vector((u * 0.06, seed, 3)))))
                t = j / rows
                base = c + fwd * (dist + depth * t) + side * u
                hgt = peak * (t ** 0.6) + 8 * noise.noise(Vector((u * 0.05, t * 3, seed)))
                # Gullies down the face: cut deepest mid-slope, so the sun
                # catches one side of each spur and leaves the other dark.
                hgt -= 9 * abs(noise.noise(Vector((u * 0.035, t * 0.8, seed + 7)))) * math.sin(math.pi * min(1.0, t * 1.2))
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
    # Bits: single trees and boulders a pixel or two across at this range,
    # dark and light, lost in the haze with the colour.
    speck = reb.noise_tex(nodes, links, 0.7, 2, 0.5)
    sr = nodes.new("ShaderNodeMapRange")
    sr.inputs["From Min"].default_value = 0.35
    sr.inputs["From Max"].default_value = 0.65
    sr.inputs["To Min"].default_value = 1 - 0.55 * (1 - fade)
    sr.inputs["To Max"].default_value = 1 + 0.35 * (1 - fade)
    links.new(speck.outputs["Fac"], sr.inputs["Value"])
    mul = nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    links.new(r.outputs["Color"], mul.inputs["A"])
    links.new(sr.outputs["Result"], mul.inputs["B"])
    links.new(mul.outputs["Result"], bsdf.inputs["Base Color"])
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

def path_distance(x, y, paths):
    """Distance to the nearest segment of any footpath, in metres."""
    p = Vector((x, y))
    nearest = float('inf')
    for path in paths:
        for a, b in zip(path, path[1:]):
            a, b = Vector(a), Vector(b)
            d = b - a
            t = max(0.0, min(1.0, (p - a).dot(d) / max(d.length_squared, 1e-9)))
            nearest = min(nearest, (p - a - d * t).length)
    return nearest


def tree_roots(rng, bases, height, keep_out=lambda x, y: False):
    """Buried, tapering root flares, needles and tufts at each trunk foot.
    Each root follows the actual ground rather than a horizontal base disc.
    """
    v, f, gv, gf, dv, df = [], [], [], [], [], []
    for base, h in bases:
        for j in range(5):
            a = j * math.tau / 5 + rng.uniform(-0.4, 0.4)
            direction = Vector((math.cos(a), math.sin(a)))
            side = Vector((-direction.y, direction.x))
            length = rng.uniform(0.65, 1.3) * h / 14
            k = len(v)
            for t, w, rise in ((0, h * 0.025, 0.45), (0.5, 0.12, 0.13), (1, 0.025, -0.025)):
                p = base.xy + direction * length * t
                for s, z in ((-1, 0), (0, rise), (1, 0)):
                    q = p + side * w * s
                    v.append((q.x, q.y, height(q.x, q.y) + z))
            for n in range(2):
                for s in range(2):
                    i = k + n * 3 + s
                    f.append((i, i + 1, i + 4, i + 3))
        def foot(rr):
            for _ in range(100):
                a, r = rr.uniform(0, math.tau), rr.uniform(0.35, 1.35)
                x, y = base.x + math.cos(a) * r, base.y + math.sin(a) * r
                if not keep_out(x, y):
                    return x, y
            return base.x, base.y
        reb.grass_tufts(rng, 30, foot, height, gv, gf)
        for _ in range(24):
            x, y = foot(rng)
            reb.card(dv, df, Vector((x, y, height(x, y) + 0.012)), Vector((1, 0, 0)), Vector((0, 0, 1)), 0.04, 0.18, 0)
    reb.mesh_object("Exposed tapering roots", v, f, mat("bark"))
    reb.mesh_object("Grass round roots", gv, gf, mat("blades"), smooth=False)
    reb.mesh_object("Root litter", dv, df, mat("dead needles"))


def mountain_forest(rng, centre, near=40.0, below=-65.0, count=60000):
    """A continuous wooded mountainside and distant mountain folds all round
    the room. Real tiered tree silhouettes cover the slope below the path;
    broad, irregular mountain spurs overlap beyond them. Cameras need a
    2000 m far plane. This backdrop does not enter collision or masks.
    """
    cx, cy = centre
    def hill(x, y):
        dx, dy = x - cx, y - cy
        r = math.hypot(dx, dy)
        a = math.atan2(dy, dx)
        fall = below * (1 - math.exp(-max(0, r - near + 45) / 65))
        return fall + 13 * math.sin(a * 3 + r * 0.012) + 32 * math.sin(a*4+r*0.012) * min(1,max(0,r-near)/90) + 7 * noise.noise(Vector((x * 0.025, y * 0.025, 7)))
    v, f = [], []
    rings, sides = 65, 240
    for j in range(rings + 1):
        r = near + (860 - near) * j / rings
        for i in range(sides):
            a = math.tau * i / sides
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
            v.append((x, y, hill(x, y)))
    for j in range(rings):
        for i in range(sides):
            a, b = j * sides + i, j * sides + (i + 1) % sides
            f.append((a, b, b + sides, a + sides))
    reb.mesh_object("Continuous wooded slopes", v, f, reb.mat_surface("Forest under canopy", [(0, (0.018, 0.032, 0.02)), (1, (0.055, 0.08, 0.04))], scale=0.08, bump=0))
    layers = [([], []) for _ in range(3)]
    for _ in range(count):
        r = near + (780 - near) * rng.random() ** 1.8
        a = rng.uniform(0, math.tau)
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        z, h = hill(x, y) - 0.2, rng.uniform(7, 12)
        tv, tf = layers[0 if r < 140 else 1 if r < 330 else 2]
        for tier in range(3):
            k = len(tv)
            tv.append((x, y, z + h * (0.65 + tier * 0.175)))
            for s in range(7):
                b = math.tau * s / 7
                radius = h * (0.24 - tier * 0.055)
                tv.append((x + math.cos(b) * radius, y + math.sin(b) * radius, z + tier * h * 0.23))
            tf.extend((k, k + 1 + s, k + 1 + (s + 1) % 7) for s in range(7))
    for i, (tv, tf) in enumerate(layers):
        c = i * 0.018
        reb.mesh_object(f"Mountain canopy {i}", tv, tf, reb.mat_surface(f"Mountain pine {i}", [(0,(0.012+c,0.028+c,0.018+c)),(1,(0.045+c,0.075+c,0.04+c))],scale=0.8,rough=1,bump=0), smooth=False)
    for layer in range(3):
        v, f = [], []
        for j in range(13):
            t = j / 12
            r = 680 + layer * 170 + t * 220
            for i in range(sides + 1):
                a = math.tau * i / sides
                crest = 185 + 58 * math.sin(a * 5 + layer * 2) + 35 * math.sin(a * 17 + layer) + 45 * noise.noise(Vector((a * 6, layer, 4)))
                z = below - 30 + crest * math.sin(t * math.pi / 2) + 25 * math.sin(a * 19 + t * 3) * math.sin(t * math.pi)
                v.append((cx + math.cos(a) * r, cy + math.sin(a) * r, z))
        for j in range(12):
            for i in range(sides):
                k = j * (sides + 1) + i
                f.append((k, k + 1, k + sides + 2, k + sides + 1))
        c = layer * 0.025
        m = reb.mat_surface(f"Distant forested mountain {layer}", [(0, (0.04+c, 0.065+c, 0.055+c)), (1, (0.10+c, 0.135+c, 0.12+c))], scale=0.06, detail=6, bump=0.3)
        reb.mesh_object(f"Folded mountain {layer}", v, f, m)


def soaked_blood(name="Soaked blood"):
    """Dried, rough blood broken by dusty pores rather than glossy red paint."""
    return reb.mat_surface(name, [(0.2, (0.045, 0.018, 0.012)), (0.43, (0.085, 0.025, 0.016)), (0.6, (0.13, 0.05, 0.032)), (0.76, (0.19, 0.16, 0.12))], scale=85, detail=4, rough=0.96, bump=0.15)
