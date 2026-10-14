# Render an RE1 character model, as tools/rebecca/npc/export.ts writes it, on
# its skeleton with its texture: front, side and back, and optionally the
# texture's UV layout as a painting guide.
#
#   blender -b --factory-startup --python view.py -- <model dir> <out dir> <pose> [--bones] [--uv] [--size N]
#
# <model dir> holds model.json and texture.png. <pose> is one of the poses the
# export wrote: rest, or anim:frame. Writes <out dir>/<pose>-front.png,
# -side.png and -back.png (and uv.png with --uv). The game's axes are X
# forward, Y down and Z to the character's left; here they become Blender's
# -Y forward, Z up and X across, at 1700 game units to the metre, as the
# rooms are built.
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

args = sys.argv[sys.argv.index("--") + 1:]
model_dir, out_dir, pose_name = args[0], args[1], args[2]
show_bones = "--bones" in args
want_uv = "--uv" in args
size = int(args[args.index("--size") + 1]) if "--size" in args else 512
os.makedirs(out_dir, exist_ok=True)

UNIT = 1 / 1700
# Game (x, y, z) to Blender (z, -x, -y): a proper rotation, so faces keep their winding.
AXES = Matrix(((0, 0, 1), (-1, 0, 0), (0, -1, 0)))


def to_blender(v):
    return AXES @ Vector(v) * UNIT


with open(os.path.join(model_dir, "model.json")) as f:
    model = json.load(f)
joints = model["pose"] if "pose" in model else model["poses"][pose_name]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

image = bpy.data.images.load(os.path.join(model_dir, "texture.png"))
mat = bpy.data.materials.new("skin")
mat.use_nodes = True
nodes = mat.node_tree.nodes
bsdf = nodes["Principled BSDF"]
bsdf.inputs["Roughness"].default_value = 1.0
tex = nodes.new("ShaderNodeTexImage")
tex.image = image
tex.interpolation = "Closest"
mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])


def joint_matrix(j):
    m = joints[j]["m"]
    rot = Matrix(((m[0], m[1], m[2]), (m[3], m[4], m[5]), (m[6], m[7], m[8])))
    return AXES @ rot @ AXES.inverted(), to_blender(joints[j]["t"])


objs = []
for i, o in enumerate(model["objects"]):
    if o["joint"] is None:
        continue
    rot, loc = joint_matrix(o["joint"])
    verts = [to_blender(v) for v in o["vertices"]]
    tris = o["triangles"]
    mesh = bpy.data.meshes.new(f"object{i}")
    mesh.from_pydata(verts, [], [t["v"] for t in tris])
    uv = mesh.uv_layers.new(name="UV")
    for poly, t in zip(mesh.polygons, tris):
        for k, loop in enumerate(poly.loop_indices):
            u, v = t["uv"][k]
            uv.data[loop].uv = (u / 256, 1 - v / 256)
    mesh.materials.append(mat)
    for p in mesh.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(f"object{i}", mesh)
    ob.matrix_world = Matrix.Translation(loc) @ rot.to_4x4()
    scene.collection.objects.link(ob)
    objs.append(ob)

if show_bones:
    arm = bpy.data.armatures.new("skeleton")
    rig = bpy.data.objects.new("skeleton", arm)
    scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for j, joint in enumerate(model["joints"]):
        if joint["parent"] < 0:
            continue
        b = arm.edit_bones.new(f"joint{j}")
        b.head = to_blender(joints[joint["parent"]]["t"])
        b.tail = to_blender(joints[j]["t"])
        if (b.tail - b.head).length < 1e-4:
            b.tail = b.head + Vector((0, 0, 0.02))
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.show_in_front = True
    arm.display_type = "STICK"

# Frame the model: its bounds in Blender space.
pts = [ob.matrix_world @ Vector(c) for ob in objs for c in ob.bound_box]
lo = Vector([min(p[k] for p in pts) for k in range(3)])
hi = Vector([max(p[k] for p in pts) for k in range(3)])
centre = (lo + hi) / 2
extent = max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z) * 1.1

for name in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        scene.render.engine = name
        break
    except TypeError:
        pass
scene.render.resolution_x = size
scene.render.resolution_y = size
scene.render.film_transparent = False
world = bpy.data.worlds.new("world")
world.color = (0.08, 0.08, 0.08)
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.09, 0.085, 0.08, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
scene.view_settings.view_transform = "Standard"

key = bpy.data.objects.new("key", bpy.data.lights.new("key", "SUN"))
key.data.energy = 3.0
key.rotation_euler = (math.radians(50), 0, math.radians(-30))
scene.collection.objects.link(key)
fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "SUN"))
fill.data.energy = 1.2
fill.rotation_euler = (math.radians(60), 0, math.radians(150))
scene.collection.objects.link(fill)

cam = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = extent
scene.collection.objects.link(cam)
scene.camera = cam

# The model faces Blender's -Y. Each camera stands level and looks back at it:
# its position, then its turn about Z (a camera at 90 degrees about X looks along +Y).
views = {"front": ((0, -1), 0), "side": ((1, 0), 90), "back": ((0, 1), 180)}
for view, ((dx, dy), turn) in views.items():
    cam.location = centre + Vector((dx, dy, 0)) * 10
    cam.rotation_euler = (math.radians(90), 0, math.radians(turn))
    scene.render.filepath = os.path.join(out_dir, f"{pose_name.replace(':', '-')}-{view}.png")
    bpy.ops.render.render(write_still=True)

if want_uv:
    # The texture's UV islands drawn over the sheet: the guide a skin is painted to.
    for ob in objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.export_layout(filepath=os.path.join(out_dir, "uv.png"), size=(1024, 1024), opacity=0.0)
    bpy.ops.object.mode_set(mode="OBJECT")

print("view.py wrote", out_dir)
