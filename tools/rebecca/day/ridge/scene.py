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
import kit  # noqa: E402

# Laid out when a metre was taken as 1000 units, and its world stays that
# way (reb.UNITS = 1000): the cameras, the clearing and the valley keep their
# places. What grows or lies in it is GROW (1700 / 1000) times its real size,
# so it stands right next to her (reb.UNITS has the measured scale), and the
# trees stand back from the clearing to leave the view open.
reb.UNITS = 1000.0
GROW = 1.7
FRAMES = 16
from mathutils import Vector, noise  # noqa: E402

OUT = os.environ.get("RE1_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders"))

CAMERAS = [
    # 0: from the back of the clearing, out over the edge to the valley.
    {"from": (5600, -4300, 2400), "to": (8600, 2600, 20000), "fov": 240},
    # 1: from the cliff edge, back at the rock face and the trail out (east).
    {"from": (5200, -2600, 11200), "to": (8300, -400, 3500), "fov": 250},
]


def ground_height(x, y):
    """Metres. The clearing is flat; the rock face rises behind (y < 3), the
    slope climbs gently either side, and past the edge (y > 10) the mountain
    falls away to the valley."""
    h = 0.0
    if y < 3.0:
        h += min(2.0, (3.0 - y) * 0.7)
    if x < 3.0:
        h += (3.0 - x) * 0.35
    if x > 11.0 and not (3.8 < y < 6.8):
        h += (x - 11.0) * 0.3
    if y > 10.0:
        # The mountain falls away below the edge, steep at first, to a valley
        # floor some 80 m down.
        d = y - 10.0
        h -= 80.0 * (1.0 - math.exp(-d / 9.0))
    lumps = noise.noise(Vector((x * 0.4, y * 0.4, 0))) * 0.35 + noise.noise(Vector((x * 1.9, y * 1.9, 5))) * 0.06
    # The clearing floor stays nearly flat: the game's floor is Y = 0 everywhere.
    inside = 3.0 <= x <= 11.0 and 3.0 <= y <= 10.0
    return h + lumps * (0.15 if inside else 1.0)


def build():
    rng = random.Random(31)
    reb.clear_scene()
    earth = reb.mat_surface("Earth", [(0.0, (0.03, 0.025, 0.02)), (0.4, (0.09, 0.07, 0.05)), (0.7, (0.06, 0.07, 0.04)), (1.0, (0.13, 0.11, 0.09))], scale=3)
    rock = reb.mat_surface("Rock", [(0.25, (0.04, 0.04, 0.04)), (0.5, (0.12, 0.115, 0.11)), (0.7, (0.2, 0.19, 0.18)), (0.9, (0.07, 0.08, 0.05))], scale=1.8, detail=14, bump=1.2)
    needles = reb.mat_cards("Needles", (0.012, 0.03, 0.018), (0.06, 0.12, 0.06))
    grass = reb.mat_cards("Grass", (0.04, 0.05, 0.02), (0.14, 0.15, 0.07))
    bark = reb.mat_wood("Bark", (0.07, 0.05, 0.035))

    reb.terrain("Mountain top", earth, (-30, 45), (-25, 60), ground_height, step=0.45)

    # The rock face behind the clearing: a cliff, its face displaced into
    # ledges and cracks, with fallen boulders at its foot.
    verts, faces = [], []
    nx, nz = 90, 40
    for j in range(nz + 1):
        z = -1.0 + 16.0 * j / nz
        for i in range(nx + 1):
            x = -6.0 + 26.0 * i / nx
            ledge = noise.noise(Vector((x * 0.25, 0, z * 0.6))) * 1.4 + noise.noise(Vector((x * 1.3, 3, z * 1.3))) * 0.35
            y = 1.6 - 0.12 * z + ledge - max(0.0, (z - 9.0)) * 0.5
            verts.append((x, y, z))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    reb.wall(reb.mesh_object("Rock face", verts, faces, rock))
    verts, faces = [], []
    for i in range(14):
        x = rng.uniform(-1, 15)
        y = rng.uniform(2.2, 3.0)
        reb.boulder(rng, (x, y, ground_height(x, y) + 0.2), rng.uniform(0.35, 0.9) * GROW, verts, faces)
    reb.mesh_object("Fallen rocks", verts, faces, rock)
    # Pines along the top of the rock face, against the sky.
    tv, tf, tb = [], [], []
    for i in range(12):
        x = rng.uniform(-4, 18)
        base = Vector((x, rng.uniform(-3.5, -1.5), 14.5))
        h = rng.uniform(7, 11) * GROW
        reb.conifer(rng, base, h, tv, tf)
        tb.append((base, h))
    reb.mesh_object("Cliff-top pines", tv, tf, needles, smooth=False)
    reb.trunks("Cliff-top trunks", bark, tb)

    # Boulders in the clearing, two near camera 1 that she can walk behind.
    for name, (x, y, r, in_front) in {
        "Boulder west": (4.0, 8.2, 0.7, True),
        "Boulder east": (9.6, 8.6, 0.6, True),
        "Boulder north": (8.6, 4.2, 0.55, False),
    }.items():
        verts, faces = [], []
        reb.boulder(rng, (x, y, ground_height(x, y) + r * 0.3 * GROW), r * GROW, verts, faces)
        ob = reb.wall(reb.mesh_object(name, verts, faces, rock), "circle")
        if in_front:
            reb.mask(ob)

    # Pines around the clearing: the west edge, the east edge either side of
    # the trail out, and the forest down the valley.
    needle_v, needle_f, bases = [], [], []
    ring = []
    for _ in range(30):
        x, y = rng.uniform(-8, 1.2), rng.uniform(1, 13)
        ring.append((x, y))
    for _ in range(30):
        x, y = rng.uniform(12.8, 23), rng.uniform(0.5, 13)
        if 2.5 < y < 8.0 and x < 19:
            continue  # the trail out
        ring.append((x, y))
    for x, y in ring:
        h = rng.uniform(8, 14) * GROW
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
    fire_m = reb.mat_emit("Fire glow", (1.0, 0.35, 0.08), 60)
    reb.mesh_object("Fire", verts, faces, fire_m, smooth=False)
    fire = reb.point("Fire light", (base.x, base.y - 9, base.z + 6), 400000, (1.0, 0.42, 0.12), 4.0)
    import bpy  # noqa: E402

    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=4, radius2=22, depth=120, location=(base.x - 4, base.y + 4, base.z + 62))
    smoke = bpy.context.active_object
    smoke.name = "Smoke"
    m = bpy.data.materials.new("Smoke")
    m.use_nodes = True
    nodes = m.node_tree.nodes
    nodes.remove(nodes["Principled BSDF"])
    vol = nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.08, 0.075, 0.07, 1)
    # Billowing: noise drives the density. Two layers rise through the plume,
    # half a loop apart, each fading out as it wraps, so the loop is seamless.
    links = m.node_tree.links
    tc = nodes.new("ShaderNodeTexCoord")
    layers = []
    for _ in range(2):
        mapping = nodes.new("ShaderNodeMapping")
        links.new(tc.outputs["Generated"], mapping.inputs["Vector"])
        tex = nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = 3.0
        tex.inputs["Detail"].default_value = 6
        links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
        layers.append((mapping, tex))
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    links.new(layers[0][1].outputs["Fac"], mix.inputs["A"])
    links.new(layers[1][1].outputs["Fac"], mix.inputs["B"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].color = (0.6, 0.6, 0.6, 1)
    links.new(mix.outputs["Result"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], vol.inputs["Density"])
    m.node_tree.links.new(vol.outputs["Volume"], nodes["Material Output"].inputs["Volume"])
    smoke.data.materials.append(m)

    # Grass about the clearing.
    gv, gf = [], []
    def patchy(r):
        while True:
            x, y = r.uniform(2.5, 11.5), r.uniform(2.6, 10.3)
            if noise.noise(Vector((x * 0.35, y * 0.35, 9))) > -0.1:
                return x, y
    reb.grass_tufts(rng, 1800, patchy, ground_height, gv, gf)
    # Tufts made for a 1000-unit metre: stretch them up to her scale.
    for i in range(2, len(gv), 3):
        b = (Vector(gv[i - 2]) + Vector(gv[i - 1])) / 2
        gv[i] = tuple(b + (Vector(gv[i]) - b) * GROW)
    # Stones scattered over the bare patches.
    sv, sf = [], []
    for _ in range(60):
        x, y = rng.uniform(3.0, 11.0), rng.uniform(3.2, 10.0)
        r = rng.uniform(0.05, 0.16) * GROW
        reb.boulder(rng, (x, y, ground_height(x, y)), r, sv, sf, squash=0.6)
    reb.mesh_object("Stones", sv, sf, rock)
    grass_ob = reb.mesh_object("Grass", gv, gf, grass, smooth=False)
    grass_rest = [Vector(p) for p in gv]
    # Birds wheeling over the valley.
    bird_m = reb.mat_plain("Bird", (0.01, 0.01, 0.012), 0.6)
    birds = []
    for i in range(4):
        bv = [(-0.5, 0, 0), (0, 0.1, 0), (0.5, 0, 0), (0, -0.25, 0)]
        birds.append((reb.mesh_object(f"Bird {i}", bv, [(0, 1, 3), (1, 2, 3)], bird_m, smooth=False), rng.uniform(0, 1), rng.uniform(8, 16), rng.uniform(-2, 2)))

    # Ridges beyond the valley, one behind another, fading into the mist.
    for i, (dist, top, col) in enumerate(((180, 60, (0.03, 0.04, 0.05)), (320, 110, (0.06, 0.065, 0.09)), (520, 170, (0.1, 0.1, 0.14)))):
        verts, faces = [], []
        n = 80
        for j in range(n + 1):
            x = -500 + 1100 * j / n
            peak = top * (0.55 + 0.45 * noise.noise(Vector((x * 0.004 + i * 7, 0, 0))) + 0.2 * noise.noise(Vector((x * 0.02, i, 0))))
            verts.append((x, dist, -80))
            verts.append((x, dist + 30, -80 + peak))
        for j in range(n):
            a = 2 * j
            faces.append((a, a + 2, a + 3, a + 1))
        reb.mesh_object(f"Ridge {i}", verts, faces, reb.mat_surface(f"Far ridge {i}", [(0.3, tuple(c * 0.5 for c in col)), (0.6, col), (0.8, tuple(c * 1.4 for c in col))], scale=0.08, detail=10, bump=0.0))

    reb.light_for("dawn", mist_box=((10, 140, -70), (500, 300, 40)), mist_density=0.0018)
    sun_dir = Vector((0.85, 0.35, 0.08)).normalized()
    reb.gradient_sky((1.0, 0.55, 0.32), (0.12, 0.16, 0.32), below=(0.05, 0.05, 0.07), strength=1.0, sun_dir=sun_dir)
    # A soft key on the clearing, from the cameras' side, for the RE look.
    reb.spot("Key", (7.0, 3.5, 9.0), (7.0, 8.0, 0.0), 2500, (1.0, 0.8, 0.65), 110, 1.0, 2.0)
    reb.spot("Back key", (6.0, 11.0, 8.0), (8.0, 4.0, 0.0), 1800, (0.8, 0.85, 1.0), 110, 1.0, 2.0)
    fflick = [1.0] + [1.0 + random.Random(i).uniform(-0.25, 0.2) for i in range(1, FRAMES)]

    def pose(k):
        t = k / FRAMES
        phase = 2 * math.pi * t
        for idx in range(2, len(grass_rest), 3):
            p = grass_rest[idx]
            w = math.sin(phase + p.x * 0.7 + p.y * 0.4)
            grass_ob.data.vertices[idx].co = (p.x + 0.08 * w, p.y + 0.03 * w, p.z)
        grass_ob.data.update()
        # The smoke rises: layer A drifts up through the loop, layer B half a loop behind.
        rise = 0.35
        layers[0][0].inputs["Location"].default_value = (0, 0, -rise * t)
        layers[1][0].inputs["Location"].default_value = (0, 0, -rise * ((t + 0.5) % 1.0))
        mix.inputs["Factor"].default_value = math.cos(math.pi * t) ** 2
        reb.emit_strength(fire_m, 60 * fflick[k])
        fire.data.energy = 400000 * fflick[k]
        # Birds circle slowly far out over the valley.
        for ob, start, radius, dz in birds:
            a = 2 * math.pi * ((start + t) % 1.0)
            ob.location = (8 + radius * math.cos(a), 45 + radius * 0.6 * math.sin(a), 6 + dz)
            ob.rotation_euler = (0.5 if k % 2 else -0.5, 0, a + math.pi)
            ob.scale = (1.8, 1.8, 1.8)

    # The kit's worn, bitty surfaces, as every kit room has.

    kit.wear(float(os.environ.get("RE1_WEAR", "1.3")))

    reb.export(
        CAMERAS,
        OUT,
        anim={"frames": FRAMES, "ticks": 3, "set": pose},
        extra={
            # The walls the game needs, in game units: the rock face, the pines
            # either side, and the cliff edge, which has no object of its own.
            # The west edge stops short of the pines: both cameras lose her there.
            "bounds": {"x0": 3900, "z0": 3000, "x1": 11000, "z1": 10000},
            "exit": {"x0": 11000, "z0": 3800, "x1": 13000, "z1": 6800},
        },
    )


build()
