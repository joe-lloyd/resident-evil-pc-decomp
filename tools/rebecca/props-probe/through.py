"""One-off: does a body pass through what is under it? blender -b --python through.py -- <slug> <body name>
Samples the body along its length; at each point lists, top down, the surfaces a ray meets."""
import json, os, sys
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
slug, target = sys.argv[sys.argv.index("--") + 1:][:2]
sys.path.insert(0, HERE)
import reb
def export(*a, **kw):
    anim = kw.get("anim") or (a[4] if len(a) > 4 else None)
    if anim:
        anim["set"](0)
    bpy.context.view_layer.update()
    ob = bpy.data.objects[target]
    dg = bpy.context.evaluated_depsgraph_get()
    pts = [ob.matrix_world @ v.co for v in ob.data.vertices]
    out = []
    for k in range(9):
        t = k / 8
        # Along the body's own x axis (feet at 0, head at about 1.7 m).
        p = ob.matrix_world @ Vector((t * 1.7, 0, 0.13))
        o = Vector((p.x, p.y, 5.0)); hits = []
        for _ in range(60):
            ok, loc, _n, _i, h, _m = bpy.context.scene.ray_cast(dg, o, Vector((0, 0, -1)), distance=20)
            if not ok: break
            o = loc - Vector((0, 0, 1e-3))
            if h.hide_render: continue
            hits.append((h.name[:18], round(loc.z, 2)))
        out.append({"t": t, "at": [round(p.x, 2), round(p.y, 2), round(p.z, 2)], "hits": hits[:10]})
    with open(os.path.join(HERE, slug, "through.json"), "w") as f:
        json.dump(out, f, indent=0)
reb.export = export
scene = os.path.join(HERE, slug, "scene.py")
exec(compile(open(scene).read(), scene, "exec"), {"__name__": "__main__", "__file__": scene})
