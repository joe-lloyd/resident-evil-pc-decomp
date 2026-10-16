"""The dead, built once from MakeHuman bodies (MPFB, CC0 assets) and baked
into corpses.blend, which kit.body places in every room.

Each figure is made with its clothes, boots and hair, rigged with MPFB's
game-engine rig, posed to kit._POSES (on his back, face down, slumped
against a wall), and the pose baked into one mesh. The mesh keeps five
material slots, "skin", "top", "legs", "shoes" and "hair"; kit.body swaps
"top" and "legs" for the room's cloth. Each vertex carries a "part"
attribute naming the bone it moves with most (PARTS), so kit.body can take
a hand or a leg off.

Run by blender/build-corpses.ts on jellybingus, without --factory-startup:
MPFB is an add-on of the owner's Blender.
  blender -b --python corpses.py
Writes RE1_OUT/corpses.blend and RE1_OUT/corpses.png, every corpse side by side.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

from bl_ext.user_default.mpfb.services import AssetService, HumanService, ObjectService, TargetService  # noqa: E402

OUT = os.environ.get("RE1_OUT", os.path.dirname(os.path.abspath(__file__)))

# The bones a missing limb takes with it, in kit.body's terms: the bone
# ending at that joint and every bone below it.
PARTS = ["upperarm_l", "lowerarm_l", "hand_l", "upperarm_r", "lowerarm_r", "hand_r",
         "thigh_l", "calf_l", "foot_l", "thigh_r", "calf_r", "foot_r"]
_FINGERS = ("thumb", "index", "middle", "ring", "pinky")

FIGURES = {
    "man": {"macros": {"gender": 1.0, "age": 0.6, "muscle": 0.55, "weight": 0.6},
            "clothes": ["Male worksuit01", "Shoes02"], "hair": "Short02", "skin": "Middleage caucasian male"},
    "woman": {"macros": {"gender": 0.0, "age": 0.45, "muscle": 0.5, "weight": 0.5},
              "clothes": ["Female casualsuit01", "Shoes01"], "hair": "Bob01", "skin": "Young caucasian female"},
}

# Which way the front of the body faces in each pose, and how far the head
# has rolled onto one side.
_FACING = {"back": ((0, 0, 1), 0.7), "front": ((0, 0, -1), 1.2), "slumped": ((1, 0, 0), 0.4)}


def _asset(kind, name, ext="mhclo"):
    return AssetService.get_asset_list(kind, ext)[name]["full_path"]


def _pallor(m):
    """Drain the skin: the texture through less colour and a grey-green cast."""
    nodes, links = m.node_tree.nodes, m.node_tree.links
    for n in list(nodes):
        if n.type != "BSDF_PRINCIPLED" or not n.inputs["Base Color"].is_linked:
            continue
        src = n.inputs["Base Color"].links[0].from_socket
        hsv = nodes.new("ShaderNodeHueSaturation")
        hsv.inputs["Saturation"].default_value = 0.55
        hsv.inputs["Value"].default_value = 0.8
        mix = nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["Factor"].default_value = 0.22
        links.new(src, hsv.inputs["Color"])
        links.new(hsv.outputs["Color"], mix.inputs[6])
        mix.inputs[7].default_value = (0.32, 0.33, 0.27, 1)
        links.new(mix.outputs[2], n.inputs["Base Color"])


def _make(figure):
    """The figure standing in MakeHuman's rest pose: (armature, the meshes that go into the corpse)."""
    spec = FIGURES[figure]
    before = set(bpy.context.scene.objects)
    macros = TargetService.get_default_macro_info_dict()
    macros.update(spec["macros"])
    human = HumanService.create_human(macro_detail_dict=macros)
    rig = HumanService.add_builtin_rig(human, "game_engine")
    for c in spec["clothes"]:
        HumanService.add_mhclo_asset(_asset("clothes", c), human, asset_type="Clothes", subdiv_levels=0)
    HumanService.add_mhclo_asset(_asset("hair", spec["hair"]), human, asset_type="Hair", subdiv_levels=0)
    HumanService.set_character_skin(_asset("skins", spec["skin"], "mhmat"), human, skin_type="MAKESKIN")
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and o not in before]
    return rig, human, meshes


def _swapped(pose):
    """Whether kit._POSES's left is the body's right in this pose (lying on
    his back with his head toward +x, his left hand is at -y)."""
    j = kit._POSES[pose]
    front = Vector(_FACING[pose][0])
    up = (Vector(j["chest"]) - Vector(j["pelvis"])).normalized()
    return (Vector(j["l_hip"]) - Vector(j["r_hip"])).dot(up.cross(front)) < 0


def _tag(ob, human, rig, hip_z, swapped):
    """Before posing: each vertex's part, named as kit._POSES names the
    joints, and the material slots by what the mesh is."""
    me = ob.data
    names = {g.index: g.name for g in ob.vertex_groups if g.name in rig.data.bones}
    part = me.attributes.new("part", "INT", "POINT")
    for v in me.vertices:
        best = max((g for g in v.groups if g.group in names), key=lambda g: g.weight, default=None)
        bone = names.get(best.group, "") if best else ""
        if any(f in bone for f in _FINGERS):
            bone = "hand_" + bone[-1]
        if swapped and bone[-2:] in ("_l", "_r"):
            bone = bone[:-1] + ("r" if bone[-1] == "l" else "l")
        part.data[v.index].value = PARTS.index(bone) + 1 if bone in PARTS else 0
    what = ObjectService.get_object_type(ob)
    kind = "skin" if ob == human else "hair" if what == "Hair" else "shoes" if "shoe" in ob.name.lower() else "cloth"
    old = me.materials[0] if me.materials else None
    me.materials.clear()
    if kind != "cloth":
        if old is not None:
            old.name = kind
            me.materials.append(old)
        return kind
    # Top above the hips, legs below, by where each face sits standing.
    for slot, colour in (("top", (0.35, 0.05, 0.04)), ("legs", (0.06, 0.08, 0.15))):
        m = bpy.data.materials.new(slot)
        m.diffuse_color = (*colour, 1)
        me.materials.append(m)
    for p in me.polygons:
        p.material_index = 0 if (ob.matrix_world @ p.center).z > hip_z else 1
    return kind


def _pose(rig, pose):
    """Turn the rig so each limb points the way kit._POSES has it."""
    j = {k: Vector(v) for k, v in kit._POSES[pose].items()}
    front, roll = _FACING[pose]
    up = (j["chest"] - j["pelvis"]).normalized()
    front = Vector(front)
    front = (front - up * front.dot(up)).normalized()
    left = up.cross(front)
    if _swapped(pose):
        # The pose's left is the body's right as it lies: swap the names.
        j = {(k.replace("l_", "@").replace("r_", "l_").replace("@", "r_") if k[:2] in ("l_", "r_") else k): v for k, v in j.items()}

    bones = rig.pose.bones
    rest = {b.name: b.bone.matrix_local.copy() for b in bones}

    def frame(l, u, f):
        return Matrix((l, u, f)).transposed()

    r_left = (rest["thigh_l"].translation - rest["thigh_r"].translation).normalized()
    r_up = (rest["spine_03"].translation - rest["pelvis"].translation).normalized()
    r_up = (r_up - r_left * r_up.dot(r_left)).normalized()
    r0 = (frame(left, up, front) @ frame(r_left, r_up, r_left.cross(r_up)).inverted()).to_4x4()
    pelvis_rest = rest["pelvis"].translation

    def side(name):
        return left if name.endswith("_l") else -left

    targets = {
        "spine_03": j["neck"] - j["chest"],
        "neck_01": j["head"] - j["neck"], "head": j["head"] - j["neck"],
    }
    for s in ("l", "r"):
        targets[f"upperarm_{s}"] = j[f"{s}_elbow"] - j[f"{s}_shoulder"]
        targets[f"lowerarm_{s}"] = j[f"{s}_hand"] - j[f"{s}_elbow"]
        targets[f"hand_{s}"] = j[f"{s}_hand"] - j[f"{s}_elbow"]
        targets[f"thigh_{s}"] = j[f"{s}_knee"] - j[f"{s}_hip"]
        calf = j[f"{s}_foot"] - j[f"{s}_knee"]
        targets[f"calf_{s}"] = calf
        out = side(f"_{s}") * 0.8
        targets[f"foot_{s}"] = {"back": front + out, "front": calf.normalized() + front * 0.4, "slumped": up + out}[pose]

    posed = {}
    order = []

    def walk(b):
        order.append(b)
        for c in b.children:
            walk(c)

    walk(bones["Root"])
    for pb in order:
        name = pb.name
        if pb.parent is None:
            m = Matrix.Translation(j["pelvis"]) @ r0 @ Matrix.Translation(-pelvis_rest) @ rest[name]
        else:
            m = posed[pb.parent.name] @ rest[pb.parent.name].inverted() @ rest[name]
        if name in targets:
            d0 = m.to_3x3().col[1].normalized()
            q = d0.rotation_difference(Vector(targets[name]).normalized()).to_matrix()
            head = m.translation.copy()
            m = Matrix.Translation(head) @ q.to_4x4() @ Matrix.Translation(-head) @ m
        if name == "head":
            head = m.translation.copy()
            ax = m.to_3x3().col[1].normalized()
            m = Matrix.Translation(head) @ Matrix.Rotation(roll, 4, ax) @ Matrix.Translation(-head) @ m
        if any(f in name for f in _FINGERS):
            # The hand falls half closed.
            head = m.translation.copy()
            m = Matrix.Translation(head) @ Matrix.Rotation(0.35, 4, m.to_3x3().col[0]) @ Matrix.Translation(-head) @ m
        posed[name] = m
        pb.matrix = m
        bpy.context.view_layer.update()


def _bake(figure, pose, rig, meshes):
    """The posed meshes as one, lying on the ground (and against x = 0 if slumped)."""
    dg = bpy.context.evaluated_depsgraph_get()
    obs = []
    for ob in meshes:
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        me.transform(ob.matrix_world)
        new = bpy.data.objects.new(ob.name + " baked", me)
        bpy.context.scene.collection.objects.link(new)
        obs.append(new)
    pts = [v.co for o in obs for v in o.data.vertices]
    shift = Vector((0, 0, -min(p.z for p in pts) - 0.01))
    if pose == "slumped":
        shift.x = -min(p.x for p in pts if p.z > 0.35)
    for o in obs:
        o.data.transform(Matrix.Translation(shift))
    for ob in [rig] + meshes:
        bpy.data.objects.remove(ob)
    out = kit.join(f"Corpse {figure} {pose}", obs, origin=(0, 0, 0))
    out.data.name = out.name
    return out


def sheet(corpses, path):
    """Every corpse on its own floor and wall, seen from high to one side, for checking them."""
    scene = bpy.context.scene
    grey = kit.reb.mat_plain("Floor", (0.3, 0.3, 0.3), 0.8)
    props = []
    for i, ob in enumerate(corpses):
        at = Vector(((i % 3) * 3.2, (i // 3) * 3.6, 0))
        ob.location = at
        props.append(kit.reb.prim("cube", "Floor", grey, at + Vector((0.9, 0, -0.05)), (3.0, 3.4, 0.1)))
        props.append(kit.reb.prim("cube", "Wall", grey, at + Vector((-0.06, 0, 0.5)), (0.1, 3.4, 1.0)))
    cam = bpy.data.objects.new("Sheet camera", bpy.data.cameras.new("Sheet camera"))
    scene.collection.objects.link(cam)
    mid = Vector((4.1, 1.8, 0.0))
    cam.location = mid + Vector((2.5, -6.0, 9.0))
    cam.rotation_euler = (mid - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 35
    scene.camera = cam
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3
    sun.rotation_euler = (0.6, 0.3, 0.8)
    scene.collection.objects.link(sun)
    scene.world = bpy.data.worlds.new("Sheet world")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.3, 0.32, 0.35, 1)
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.render.resolution_x, scene.render.resolution_y = 1600, 1000
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in props + [cam, sun]:
        bpy.data.objects.remove(o)


def main():
    bpy.ops.wm.read_homefile(use_empty=True)
    corpses = []
    for figure in FIGURES:
        for pose in kit._POSES:
            rig, human, meshes = _make(figure)
            bpy.context.view_layer.update()
            hip_z = (rig.matrix_world @ rig.pose.bones["thigh_l"].head).z + 0.06
            for ob in meshes:
                kind = _tag(ob, human, rig, hip_z, _swapped(pose))
                if kind == "skin":
                    _pallor(ob.data.materials[0])
            _pose(rig, pose)
            corpses.append(_bake(figure, pose, rig, meshes))
            print(f"[corpses] {figure} {pose}: {len(corpses[-1].data.vertices)} vertices", flush=True)
    for img in bpy.data.images:
        if img.filepath and not img.packed_file:
            img.pack()
    os.makedirs(OUT, exist_ok=True)
    bpy.data.libraries.write(os.path.join(OUT, "corpses.blend"), set(corpses), fake_user=True, compress=True)
    sheet(corpses, os.path.join(OUT, "corpses.png"))


main()
