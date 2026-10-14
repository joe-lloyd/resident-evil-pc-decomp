"""The trapdoor in the mansion's save room (ROOM1000), closed, where Rebecca
comes up from the crawl space. Rendered through the room's own six cameras
(read from ROOM1000.RDT: from, to, lens) onto a transparent film with a
shadow-catching floor, to lay over the original backgrounds.

A sample: nothing builds the patch from it yet. HX and HZ place it in game
units (default 5200, 5600: the open floor in the middle of camera 0). OUT is
the folder for closed<N>.png.

Looks: five uneven boards in the room's own dark olive brown, each its own
shade, with uneven gaps showing black, chipped edges, a chunk gone from one
board's end, one board sitting proud where its nail let go, nail heads, iron
strap hinges and a ring lying flat.
"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh, reb, kit
from kit import mat
from mathutils import Vector, noise
CAMS = [((3960, -3132, 11538), (5274, -2430, 5652), 221), ((2862, -3006, 3222), (4716, -2070, 9306), 230),
        ((5940, -3006, 4698), (3312, -1800, 2124), 221), ((2322, -756, 5796), (7650, -2214, 2610), 230),
        ((3456, -3906, 7884), (7740, -612, 9378), 230), ((3564, -4320, 7506), (3204, -1566, 9090), 230)]
HX, HZ = float(os.environ.get("HX", 5200)) / 1700, float(os.environ.get("HZ", 5600)) / 1700
SX, SY = 0.66, 0.78  # across the boards, along them
rng = random.Random(int(os.environ.get("SEED", 7)))
reb.clear_scene()
sc = bpy.context.scene


def wood(name, rgb, grime=0.5):
    """Old boards: the room's dark olive brown, grain streaks along y, blotches of grime, rough."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; L = nt.links
    bsdf = n["Principled BSDF"]; bsdf.inputs["Roughness"].default_value = 0.85
    tc = n.new("ShaderNodeTexCoord"); mp = n.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (60, 3, 60)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    grain = n.new("ShaderNodeTexNoise"); grain.inputs["Scale"].default_value = 3.0; grain.inputs["Detail"].default_value = 8
    L.new(mp.outputs["Vector"], grain.inputs["Vector"])
    blot = n.new("ShaderNodeTexNoise"); blot.inputs["Scale"].default_value = 9.0; blot.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], blot.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    r, g, b = rgb
    ramp.color_ramp.elements[0].color = (r * 0.45, g * 0.45, b * 0.45, 1)
    ramp.color_ramp.elements[1].color = (r * 1.4, g * 1.4, b * 1.35, 1)
    L.new(grain.outputs["Fac"], ramp.inputs["Fac"])
    mix = n.new("ShaderNodeMixRGB"); mix.blend_type = "MULTIPLY"
    L.new(ramp.outputs["Color"], mix.inputs[1])
    gr = n.new("ShaderNodeValToRGB"); gr.color_ramp.elements[0].position = 0.35; gr.color_ramp.elements[0].color = (0.35, 0.33, 0.3, 1)
    gr.color_ramp.elements[1].position = 0.7
    L.new(blot.outputs["Fac"], gr.inputs["Fac"]); L.new(gr.outputs["Color"], mix.inputs[2]); mix.inputs[0].default_value = grime
    L.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.6
    L.new(grain.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def plank(name, m, x0, x1, y0, y1, z, thick=0.03):
    """A worn board: its top a grid, dished and split, its edges chipped back at random."""
    bm = bmesh.new()
    nx, ny = 6, 18
    top, bot = {}, {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            u, v = i / nx, j / ny
            x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * v
            edge = min(u, 1 - u, v, 1 - v)
            dz = noise.noise(Vector((x * 7, y * 2, z * 3 + hash(name) % 97))) * 0.004 - 0.002 * math.sin(math.pi * u)
            # Chips: bites out of the edges and corners, where boots and the lid's lifting wore it.
            if edge == 0 and rng.random() < 0.35:
                inward = 0.012 + rng.random() * 0.03
                if u in (0, 1):
                    x += inward if u == 0 else -inward
                if v in (0, 1):
                    y += inward if v == 0 else -inward
                dz -= rng.uniform(0.004, 0.015)
            top[i, j] = bm.verts.new((x, y, z + dz))
            bot[i, j] = bm.verts.new((x, y, z - thick))
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((top[i, j], top[i + 1, j], top[i + 1, j + 1], top[i, j + 1]))
            bm.faces.new((bot[i, j + 1], bot[i + 1, j + 1], bot[i + 1, j], bot[i, j]))
    ring = [(i, 0) for i in range(nx)] + [(nx, j) for j in range(ny)] + [(i, ny) for i in range(nx, 0, -1)] + [(0, j) for j in range(ny, 0, -1)]
    for k in range(len(ring)):
        a, b = ring[k], ring[(k + 1) % len(ring)]
        bm.faces.new((top[a], bot[a], bot[b], top[b]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob); me.materials.append(m)
    return ob


shades = [wood(f"Hatch board {k}", c, g) for k, (c, g) in enumerate((((0.05, 0.044, 0.028), 0.4), ((0.07, 0.066, 0.052), 0.6),
          ((0.04, 0.034, 0.021), 0.3), ((0.058, 0.05, 0.032), 0.5), ((0.046, 0.042, 0.031), 0.5)))]
frame_m = wood("Hatch frame", (0.03, 0.026, 0.017), 0.6)
# The pit under it: black, so the gaps between the boards show it.
kit.box("Pit", mat("black"), (HX, HZ, -0.6), (SX + 0.1, SY + 0.1, 0.55))
# The frame round the opening, flush with the floor, the room's boards butting up to it.
for i, (dx, dy, w, d) in enumerate(((-SX / 2 - 0.03, 0, 0.05, SY + 0.11), (SX / 2 + 0.03, 0, 0.05, SY + 0.11),
                                     (0, -SY / 2 - 0.03, SX + 0.01, 0.05), (0, SY / 2 + 0.03, SX + 0.01, 0.05))):
    plank(f"Frame {i}", frame_m, HX + dx - w / 2, HX + dx + w / 2, HZ + dy - d / 2, HZ + dy + d / 2, -0.001, 0.05)
# Five uneven boards with gaps, one sitting proud and twisted where its nail let go.
x = HX - SX / 2 + 0.004
widths = [rng.uniform(0.11, 0.15) for _ in range(5)]
gaps = [rng.uniform(0.008, 0.016) for _ in range(4)]
scale = (SX - 0.008 - sum(gaps)) / sum(widths)
for k, w in enumerate(widths):
    w *= scale
    lift = 0.012 if k == 3 else rng.uniform(-0.004, 0.002)
    # Board 1 has lost a chunk off its near end; board 4 is split down its length.
    y1 = HZ + SY / 2 - 0.004 - (0.09 if k == 1 else 0)
    ob = plank(f"Board {k}", shades[k], x, x + w, HZ - SY / 2 + 0.004, y1, lift)
    if k == 1:
        plank("Board 1 stub", shades[k], x + w * 0.45, x + w, y1 + 0.012, HZ + SY / 2 - 0.004, lift - 0.006)
    for end in (HZ - SY / 2 + 0.05, HZ + SY / 2 - 0.05, HZ):
        kit.box("Nail", mat("iron"), (x + w / 2 + rng.uniform(-0.02, 0.02), end, lift + 0.001), (0.012, 0.012, 0.003))
    if k == 3:
        ob.rotation_euler = (0.025, -0.02, 0.01)
    x += w + (gaps[k] if k < 4 else 0)
# A strap hinge on each side of the far end, rusted, and the ring, lying flat in its worn hollow.
for dx in (-0.2, 0.2):
    kit.box("Hinge", mat("iron"), (HX + dx, HZ - SY / 2 + 0.06, 0.0), (0.05, 0.2, 0.004))
    kit.box("Hinge pin", mat("iron"), (HX + dx, HZ - SY / 2 - 0.02, 0.0), (0.06, 0.025, 0.012))
bpy.ops.mesh.primitive_torus_add(major_radius=0.045, minor_radius=0.007, location=(HX + 0.01, HZ + SY / 2 - 0.1, 0.006))
r = bpy.context.active_object; r.rotation_euler = (0, 0, 0.3); r.data.materials.append(mat("iron"))
kit.box("Ring plate", mat("iron"), (HX + 0.01, HZ + SY / 2 - 0.055, 0.0), (0.05, 0.025, 0.004))
# Dirt trodden into it and a smear where something was dragged over the edge.
kit.splat("Old smear", mat("grime"), (HX + 0.22, HZ + SY / 2 - 0.02, 0.005), 0.06, seed=9, stretch=(0.5, 1.6))
# The floor catches shadows and light only; its hole shows the gaps.
bpy.ops.mesh.primitive_plane_add(size=12, location=(HX, HZ, 0.0))
floor = bpy.context.active_object; floor.is_shadow_catcher = True
bpy.ops.mesh.primitive_cube_add(size=1, location=(HX, HZ, 0)); cut = bpy.context.active_object
cut.scale = (SX + 0.16, SY + 0.16, 0.5)
mod = floor.modifiers.new("hole", "BOOLEAN"); mod.object = cut; mod.operation = "DIFFERENCE"
cut.hide_render = True
# The room's light: soft and warm from the lamp by the desk, a dim fill.
reb.point("Lamp", (2.2, 4.8, 2.4), 60, (1.0, 0.85, 0.62), 0.8)
reb.point("Fill", (HX + 0.8, HZ + 1.2, 2.4), 18, (0.95, 0.92, 0.82), 1.5)
w = bpy.data.worlds.new("w"); w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.048, 0.04, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = float(os.environ.get("AMB", 1.0)); sc.world = w
sc.render.engine = "CYCLES"; sc.cycles.device = "GPU"; sc.cycles.samples = 256
sc.render.resolution_x, sc.render.resolution_y = 320, 240
sc.render.film_transparent = True
sc.view_settings.view_transform = "Standard"
out = os.environ["OUT"]
for i, (f, t, fov) in enumerate(CAMS):
    ob = reb.add_camera(i, {"from": f, "to": t, "fov": fov}); sc.camera = ob
    sc.render.filepath = os.path.join(out, f"closed{i}.png"); bpy.ops.render.render(write_still=True)
