"""Rebecca's prologue room: a trail down the Arklay mountain at dawn.

Run inside Blender (5.x). Builds the scene from nothing, sets up the room's
cameras from CAMERAS (in game units) and renders one 320x240 background per
camera into OUT_DIR. tools/rebecca/new_room.ts turns those renders into the
room's .pak backgrounds and writes the matching RDT camera records.

Game space is millimetres with Y pointing down; the floor is Y = 0. Blender
space is metres with Z up. The mapping is Blender (x, y, z) = (X, Z, -Y) / 1000,
a proper rotation, so handedness is kept. The engine projects with
sx = X*f/Z + 160 and sy = -Y*f/Z + 120 on a 320x240 screen (GteMatrix.cpp), so
a 32 mm sensor with a focal length of f/10 mm matches it exactly.
"""
import math
import os
import random

import bpy
from mathutils import Vector

OUT_DIR = os.environ.get("RE1_OUT", r"C:\Users\joell\Documents\Blender\re1-rebecca\renders")

# The walkable trail: a strip along game Z, flat at Y = 0.
TRAIL_X = (2000, 5000)
TRAIL_Z = (0, 16000)

# Cameras in game units: position, look-at target, and the engine's fov value.
CAMERAS = [
    # 0: high above the top of the trail, looking down it towards the mansion.
    {"from": (3500, -4200, -1500), "to": (3600, -800, 7000), "fov": 230},
    # 1: low at the bottom of the trail, looking back up at Rebecca coming down.
    {"from": (3300, -1500, 16500), "to": (3500, -900, 7000), "fov": 230},
]


def game_to_blender(p):
    x, y, z = p
    return Vector((x / 1000.0, z / 1000.0, -y / 1000.0))


def material(name, rgb, rough=0.9, scale=8.0, variation=0.35):
    """A rough surface whose colour and bump wander with noise, so flat
    low-poly shapes still read as dirt, rock or needles at 320x240."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 8
    ramp = nodes.new("ShaderNodeValToRGB")
    dark = tuple(c * (1 - variation) for c in rgb)
    light = tuple(min(1.0, c * (1 + variation)) for c in rgb)
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].color = (*light, 1)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.4
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def clear_scene():
    bpy.ops.wm.read_homefile(use_empty=True)


def ground(rng):
    # Rough mountainside with the trail cut in flat.
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=160, size=1)
    g = bpy.context.active_object
    g.name = "Mountainside"
    g.scale = (80, 140, 1)
    bpy.ops.object.transform_apply(scale=True)
    tx0, tx1 = TRAIL_X[0] / 1000, TRAIL_X[1] / 1000
    for v in g.data.vertices:
        x, y = v.co.x, v.co.y
        dist = min(abs(x - tx0), abs(x - tx1)) if not (tx0 <= x <= tx1) else 0.0
        # The slope rises away from the trail and climbs behind its top.
        bank = 0.0 if dist == 0 else min(dist * 0.35, 6.0)
        climb = max(0.0, -y) * 0.45
        # Past the foot of the trail the mountain falls away to the valley floor.
        fall = -min(max(0.0, y - 18.0) * 0.55, 14.0)
        v.co.z = bank + climb + fall + (rng.random() - 0.5) * 0.15 * min(dist, 1.0)
    g.data.materials.append(material("Earth", (0.2, 0.17, 0.11), scale=3.0))
    # The trail itself: packed dirt.
    bpy.ops.mesh.primitive_plane_add(size=1)
    t = bpy.context.active_object
    t.name = "Trail"
    t.scale = ((TRAIL_X[1] - TRAIL_X[0]) / 1000, (TRAIL_Z[1] - TRAIL_Z[0]) / 1000, 1)
    t.location = ((TRAIL_X[0] + TRAIL_X[1]) / 2000, (TRAIL_Z[0] + TRAIL_Z[1]) / 2000, 0.01)
    t.data.materials.append(material("Dirt path", (0.3, 0.23, 0.15), scale=14.0, variation=0.45))


def pine(name, loc, height, mats):
    trunk_h = height * 0.25
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=height * 0.035, depth=trunk_h, location=(loc[0], loc[1], loc[2] + trunk_h / 2))
    trunk = bpy.context.active_object
    trunk.name = f"{name} trunk"
    trunk.data.materials.append(mats["bark"])
    for i, (r, z) in enumerate(((0.32, 0.30), (0.25, 0.52), (0.17, 0.72))):
        bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=height * r, depth=height * 0.38, location=(loc[0], loc[1], loc[2] + height * z))
        cone = bpy.context.active_object
        cone.name = f"{name} needles {i}"
        cone.data.materials.append(mats["needles"])


def forest(rng, mats):
    placed = 0
    while placed < 140:
        x = rng.uniform(-16, 22)
        y = rng.uniform(-14, 30)
        # Keep the trail and a margin clear, and keep trees out from in front
        # of the cameras so no foreground masks are needed.
        if TRAIL_X[0] / 1000 - 3.5 < x < TRAIL_X[1] / 1000 + 3.5 and -4 < y < 20:
            continue
        if y > 20 and abs(x - 3.5) < 9:   # keep the view down the valley open
            continue
        z = 0.0
        tx0, tx1 = TRAIL_X[0] / 1000, TRAIL_X[1] / 1000
        dist = min(abs(x - tx0), abs(x - tx1))
        z = min(dist * 0.35, 6.0) + max(0.0, -y) * 0.45 - min(max(0.0, y - 18.0) * 0.55, 14.0)
        pine(f"Pine {placed}", (x, y, z - 0.2), rng.uniform(6, 12), mats)
        placed += 1


def rocks(rng, mats):
    for i in range(30):
        x = rng.choice([rng.uniform(0.8, 1.9), rng.uniform(5.1, 6.4)])
        y = rng.uniform(-1, 17)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rng.uniform(0.2, 0.7), location=(x, y, 0.1))
        r = bpy.context.active_object
        r.name = f"Rock {i}"
        r.scale = (1, rng.uniform(0.7, 1.4), rng.uniform(0.5, 0.8))
        for v in r.data.vertices:
            v.co *= 1 + (rng.random() - 0.5) * 0.35
        r.data.materials.append(mats["rock"])


def mansion(mats):
    # A dark silhouette far down the valley, seen from camera 0 only.
    base = Vector((3.5, 70.0, -14.0))
    for name, off, size in (
        ("Mansion body", (0, 0, 4), (22, 9, 8)),
        ("Mansion east wing", (14, 3, 3), (8, 12, 6)),
        ("Mansion west wing", (-14, 3, 3), (8, 12, 6)),
        ("Mansion roof", (0, 0, 9), (23, 10, 2.5)),
    ):
        bpy.ops.mesh.primitive_cube_add(size=1, location=base + Vector(off))
        b = bpy.context.active_object
        b.name = name
        b.scale = size
        b.data.materials.append(mats["mansion"])


def world_and_light():
    scene = bpy.context.scene
    world = bpy.data.worlds.new("Dawn")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    sky = world.node_tree.nodes.new("ShaderNodeTexSky")
    world.node_tree.links.new(sky.outputs["Color"], bg.inputs["Color"])
    sky.sun_elevation = math.radians(4)
    sky.sun_rotation = math.radians(200)
    bg.inputs["Strength"].default_value = 0.6
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(84), 0, math.radians(200)))
    sun = bpy.context.active_object
    sun.name = "Dawn sun"
    sun.data.energy = 3.5
    sun.data.color = (1.0, 0.72, 0.5)
    # Morning mist: a thin volume over the whole valley.
    bpy.ops.mesh.primitive_cube_add(size=1, location=(3.5, 30, 3))
    mist = bpy.context.active_object
    mist.name = "Mist"
    mist.scale = (160, 220, 10)
    mist.location = (3.5, 40, -8)
    m = bpy.data.materials.new("Mist")
    m.use_nodes = True
    nodes = m.node_tree.nodes
    nodes.remove(nodes["Principled BSDF"])
    vol = nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = 0.004
    vol.inputs["Color"].default_value = (0.78, 0.8, 0.86, 1)
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
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 320
    scene.render.resolution_y = 240
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
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
        "bark": material("Bark", (0.16, 0.11, 0.07)),
        "needles": material("Pine needles", (0.07, 0.16, 0.09)),
        "rock": material("Rock", (0.32, 0.31, 0.3)),
        "mansion": material("Mansion silhouette", (0.05, 0.05, 0.06)),
    }
    ground(rng)
    forest(rng, mats)
    rocks(rng, mats)
    mansion(mats)
    world_and_light()
    cams = add_cameras()
    return render(cams)


if __name__ == "__main__":
    build()
