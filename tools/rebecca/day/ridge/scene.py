"""The ridge, where Rebecca's day begins: a clearing on the mountain top at
dawn. A rock face behind, pines either side, the cliff edge in front, and far
below in the valley the training facility still burning. The trail down
leaves through the trees on the east side.

Run in Blender with reb.py beside it: RE1_OUT names the output folder.
Game units: the clearing floor is X 3000-11000, Z 3000-10000, Y = 0.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
from mathutils import Vector, noise  # noqa: E402

OUT = os.environ.get("RE1_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders"))

CAMERAS = [
    # 0: from the back of the clearing, out over the edge to the valley.
    {"from": (7000, -1900, 2600), "to": (7300, 300, 14000), "fov": 260},
    # 1: from the cliff edge, back at the rock face and the trail out (east).
    {"from": (5200, -2600, 11200), "to": (8300, -400, 3500), "fov": 250},
]


def ground_height(x, y):
    """Metres. The clearing is flat; the rock face rises behind (y < 3), the
    slope climbs gently either side, and past the edge (y > 10) the mountain
    falls away to the valley."""
    h = 0.0
    if y < 3.0:
        h += (3.0 - y) ** 1.6 * 0.9
    if x < 3.0:
        h += (3.0 - x) * 0.35
    if x > 11.0 and not (3.8 < y < 6.8):
        h += (x - 11.0) * 0.3
    if y > 10.0:
        h -= (y - 10.0) ** 1.35 * 2.2
    lumps = noise.noise(Vector((x * 0.4, y * 0.4, 0))) * 0.35 + noise.noise(Vector((x * 1.9, y * 1.9, 5))) * 0.06
    # The clearing floor stays nearly flat: the game's floor is Y = 0 everywhere.
    inside = 3.0 <= x <= 11.0 and 3.0 <= y <= 10.0
    return h + lumps * (0.15 if inside else 1.0)


def build():
    rng = random.Random(31)
    reb.clear_scene()
    earth = reb.mat_surface("Earth", [(0.0, (0.03, 0.025, 0.02)), (0.4, (0.09, 0.07, 0.05)), (0.7, (0.06, 0.07, 0.04)), (1.0, (0.13, 0.11, 0.09))], scale=3)
    rock = reb.mat_surface("Rock", [(0.3, (0.05, 0.05, 0.05)), (0.6, (0.16, 0.15, 0.14)), (0.85, (0.3, 0.28, 0.26))], scale=2.5, bump=0.9)
    needles = reb.mat_cards("Needles", (0.012, 0.03, 0.018), (0.06, 0.12, 0.06))
    grass = reb.mat_cards("Grass", (0.04, 0.05, 0.02), (0.14, 0.15, 0.07))
    bark = reb.mat_wood("Bark", (0.07, 0.05, 0.035))

    reb.terrain("Mountain top", earth, (-30, 45), (-25, 60), ground_height, step=0.45)

    # The rock face behind the clearing: a wall of boulders.
    verts, faces = [], []
    for i in range(26):
        x = rng.uniform(-2, 16)
        y = rng.uniform(-3.5, -1.2)
        reb.boulder(rng, (x, y, ground_height(x, y) + rng.uniform(0.2, 1.4)), rng.uniform(1.0, 1.8), verts, faces, squash=1.1)
    reb.wall(reb.mesh_object("Rock face", verts, faces, rock))

    # Boulders in the clearing, two near camera 1 that she can walk behind.
    for name, (x, y, r, in_front) in {
        "Boulder west": (4.0, 8.2, 0.7, True),
        "Boulder east": (9.6, 8.6, 0.6, True),
        "Boulder north": (8.6, 4.2, 0.55, False),
    }.items():
        verts, faces = [], []
        reb.boulder(rng, (x, y, ground_height(x, y) + r * 0.3), r, verts, faces)
        ob = reb.wall(reb.mesh_object(name, verts, faces, rock), "circle")
        if in_front:
            reb.mask(ob)

    # Pines around the clearing: the west edge, the east edge either side of
    # the trail out, and the forest down the valley.
    needle_v, needle_f, bases = [], [], []
    ring = []
    for _ in range(40):
        x, y = rng.uniform(-6, 2.6), rng.uniform(2, 11)
        ring.append((x, y))
    for _ in range(40):
        x, y = rng.uniform(11.6, 20), rng.uniform(1.5, 11)
        if 3.6 < y < 7.0 and x < 15:
            continue  # the trail out
        ring.append((x, y))
    for x, y in ring:
        h = rng.uniform(8, 14)
        base = Vector((x, y, ground_height(x, y) - 0.2))
        reb.conifer(rng, base, h, needle_v, needle_f)
        bases.append((base, h))
    reb.mesh_object("Pines", needle_v, needle_f, needles, smooth=False)
    # The pines' footprint is the clearing's edge (room.json "bounds"), not their own.
    reb.trunks("Pine trunks", bark, bases)

    # The valley below: forest as dark cones, cheaper than cards at this range.
    verts, faces = [], []
    for _ in range(900):
        x, y = rng.uniform(-60, 80), rng.uniform(25, 160)
        z = ground_height(x, y)
        h = rng.uniform(8, 16)
        k = len(verts)
        r = h * 0.25
        verts.append((x, y, z + h))
        for s in range(6):
            a = 2 * math.pi * s / 6
            verts.append((x + math.cos(a) * r, y + math.sin(a) * r, z))
        for s in range(6):
            faces.append((k, k + 1 + s, k + 1 + (s + 1) % 6))
    reb.mesh_object("Valley forest", verts, faces, reb.mat_cards("Far needles", (0.01, 0.025, 0.02), (0.035, 0.06, 0.045)), smooth=False)

    # The training facility, burning far down the valley, and its smoke.
    verts, faces = [], []
    base = Vector((14.0, 120.0, ground_height(14.0, 120.0)))
    for off, size in (((0, 0, 4), (24, 12, 8)), ((16, 4, 3), (10, 10, 6)), ((-6, 8, 9), (4, 4, 18))):
        reb.box(verts, faces, tuple(base + Vector(off)), size)
    reb.mesh_object("Training facility", verts, faces, reb.mat_surface("Concrete", [(0.0, (0.03, 0.03, 0.03)), (1.0, (0.08, 0.08, 0.08))]))
    verts, faces = [], []
    for wx in (-9, -4, 3, 8):
        reb.box(verts, faces, (base.x + wx, base.y - 6.1, base.z + 5), (2.0, 0.2, 1.2))
    reb.mesh_object("Fire", verts, faces, reb.mat_emit("Fire glow", (1.0, 0.35, 0.08), 18), smooth=False)
    reb.point("Fire light", (base.x, base.y - 9, base.z + 4), 60000, (1.0, 0.45, 0.15), 3.0)
    import bpy  # noqa: E402

    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=7, depth=70, location=(base.x - 2, base.y + 2, base.z + 40))
    smoke = bpy.context.active_object
    smoke.name = "Smoke"
    m = bpy.data.materials.new("Smoke")
    m.use_nodes = True
    nodes = m.node_tree.nodes
    nodes.remove(nodes["Principled BSDF"])
    vol = nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = 0.35
    vol.inputs["Color"].default_value = (0.2, 0.18, 0.17, 1)
    m.node_tree.links.new(vol.outputs["Volume"], nodes["Material Output"].inputs["Volume"])
    smoke.data.materials.append(m)

    # Grass about the clearing.
    gv, gf = [], []
    reb.grass_tufts(rng, 3500, lambda r: (r.uniform(2.5, 11.5), r.uniform(2.6, 10.3)), ground_height, gv, gf)
    reb.mesh_object("Grass", gv, gf, grass, smooth=False)

    reb.light_for("dawn", mist_box=((10, 70, -20), (160, 160, 30)))
    # A soft key on the clearing, from the cameras' side, for the RE look.
    reb.spot("Key", (7.0, 3.5, 9.0), (7.0, 8.0, 0.0), 2500, (1.0, 0.8, 0.65), 110, 1.0, 2.0)
    reb.spot("Back key", (6.0, 11.0, 8.0), (8.0, 4.0, 0.0), 1800, (0.8, 0.85, 1.0), 110, 1.0, 2.0)
    reb.export(
        CAMERAS,
        OUT,
        extra={
            # The walls the game needs, in game units: the rock face, the pines
            # either side, and the cliff edge, which has no object of its own.
            "bounds": {"x0": 3000, "z0": 3000, "x1": 11000, "z1": 10000},
            "exit": {"x0": 11000, "z0": 3800, "x1": 13000, "z1": 6800},
        },
    )


build()
