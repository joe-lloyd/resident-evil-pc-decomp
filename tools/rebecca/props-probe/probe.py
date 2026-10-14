"""Measure where a day scene's props land, without rendering.

Run in Blender from a folder holding kit.py, reb.py and <slug>/scene.py:

    blender -b --factory-startup --python probe.py -- <slug>

Wraps kit.body, bunk, chair, crate, shelves and crow to note each call's
arguments and the prop's bounding box as the kit placed it, then replaces
reb.export (and export_walk) so that, instead of rendering, it writes
<slug>/probe.json: for each prop its world bounding box in metres when the
scene is done, the box straight after the kit call, and the surfaces a ray
straight down meets under it. Objects named like a body, bunk, chair, crate,
shelf, crow, corpse or footlocker that the kit did not make are listed too.
"""
import json
import math
import os
import re
import sys
import traceback

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SLUG = sys.argv[sys.argv.index("--") + 1]
SCENE = os.path.join(HERE, SLUG, "scene.py")
sys.path.insert(0, HERE)

import reb  # noqa: E402
import kit  # noqa: E402

KINDS = ("body", "bunk", "chair", "crate", "shelves", "crow")
NAMED = re.compile(r"body|bunk|chair|crate|shel|crow|corpse|footlocker|locker|dead", re.I)
calls = []


def bbox(ob):
    """World bounding box of an object's evaluated mesh: [x0, y0, z0, x1, y1, z1]."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    try:
        me = ev.to_mesh()
    except RuntimeError:
        me = None
    if me is None or not len(me.vertices):
        pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    else:
        pts = [ev.matrix_world @ v.co for v in me.vertices]
    if me is not None:
        ev.to_mesh_clear()
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    return [round(v, 3) for v in lo + hi]


def wrap(kind):
    orig = getattr(kit, kind)

    def call(name, *a, **kw):
        before = set(bpy.data.objects)
        out = orig(name, *a, **kw)
        made = [o for o in bpy.data.objects if o not in before]
        bpy.context.view_layer.update()
        main = out[0] if isinstance(out, (list, tuple)) else out
        # The prop itself: kit.body with sheet=True returns the sheet, so
        # find the joined object by its name.
        ob = next((o for o in made if o.parent is None and o.type == "MESH" and re.fullmatch(re.escape(name) + r"(\.\d+)?", o.name)), main)
        args = dict(zip({"body": ("at",), "bunk": ("frame_m", "at"), "chair": ("m", "at"), "crate": ("m", "at"),
                         "shelves": ("m", "at"), "crow": ("at",)}[kind], a))
        args.update(kw)
        keep = {k: (list(v) if isinstance(v, (tuple, list, Vector)) else v) for k, v in args.items()
                if k in ("at", "heading", "rot", "pose", "tipped", "size", "levels", "sheet", "perched")}
        calls.append({"kind": kind, "name": name, "ob": ob.name, "made": {o.name for o in made}, "args": keep, "kit_box": bbox(ob)})
        return out

    setattr(kit, kind, call)


for k in KINDS:
    wrap(k)


def is_volume(ob):
    for slot in getattr(ob, "material_slots", ()):
        m = slot.material
        if not m or not m.use_nodes:
            continue
        for n in m.node_tree.nodes:
            if n.type == "OUTPUT_MATERIAL" and n.is_active_output:
                if not n.inputs["Surface"].is_linked and n.inputs["Volume"].is_linked:
                    return True
    return False


def family(ob):
    return {ob.name} | {c.name for c in ob.children_recursive}


def under(x, y, top, skip):
    """Surfaces straight down from (x, y, top): [(name, z)], up to eight."""
    dg = bpy.context.evaluated_depsgraph_get()
    scene = bpy.context.scene
    origin = Vector((x, y, top))
    hits = []
    for _ in range(400):
        ok, loc, _n, _i, ob, _m = scene.ray_cast(dg, origin, Vector((0, 0, -1)), distance=60.0)
        if not ok:
            break
        origin = loc - Vector((0, 0, 1e-4))
        if ob.name in skip or ob.hide_render or is_volume(ob):
            continue
        hits.append([ob.name, round(loc.z, 3)])
        if len(hits) >= 8:
            break
    return hits


def measure():
    bpy.context.view_layer.update()
    props, seen = [], set()
    for c in calls:
        ob = bpy.data.objects.get(c["ob"])
        if ob is None:
            props.append({"kind": c["kind"], "name": c["name"], "gone": True})
            continue
        seen.add(ob.name)
        box = bbox(ob)
        skip = c["made"] | family(ob)
        cx, cy = (box[0] + box[3]) / 2, (box[1] + box[4]) / 2
        top = box[5] + 0.002
        props.append({
            "kind": c["kind"], "name": ob.name, "args": c["args"], "box": box, "kit_box": c["kit_box"],
            "hidden": ob.hide_render, "parent": ob.parent.name if ob.parent else None,
            "under": under(cx, cy, top, skip),
            "under_at": under(c["args"]["at"][0], c["args"]["at"][1], top, skip) if "at" in c["args"] else None,
        })
    for ob in bpy.data.objects:
        if ob.name in seen or ob.type != "MESH" or not NAMED.search(ob.name):
            continue
        # Children and the kit's own extras (pools, sheets, blankets) of a noted prop.
        if any(ob.name in c["made"] for c in calls):
            continue
        box = bbox(ob)
        cx, cy = (box[0] + box[3]) / 2, (box[1] + box[4]) / 2
        props.append({"kind": "named", "name": ob.name, "box": box, "hidden": ob.hide_render,
                      "parent": ob.parent.name if ob.parent else None,
                      "under": under(cx, cy, box[5] + 0.002, family(ob))})
    # Every object's world box, to diff two runs: only what was meant to move should.
    every = {}
    for ob in bpy.data.objects:
        if ob.type in ("MESH", "CURVE", "FONT") and not ob.hide_render:
            pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
            every[ob.name] = [round(min(p[i] for p in pts), 3) for i in range(3)] + [round(max(p[i] for p in pts), 3) for i in range(3)]
    path = os.path.join(HERE, SLUG, "probe.json")
    with open(path, "w") as f:
        json.dump({"slug": SLUG, "props": props, "all": every}, f, indent=1)
    print(f"[probe] {SLUG}: {len(props)} props -> {path}", flush=True)


def export(cameras, out_dir, samples=512, extra=None, anim=None, states=()):
    if anim:
        anim["set"](0)
    measure()


def export_walk(*a, **kw):
    measure()


reb.export = export
reb.export_walk = export_walk

try:
    g = {"__name__": "__main__", "__file__": SCENE}
    with open(SCENE) as f:
        code = compile(f.read(), SCENE, "exec")
    exec(code, g)
except SystemExit:
    pass
except Exception:
    traceback.print_exc()
    sys.exit(1)
