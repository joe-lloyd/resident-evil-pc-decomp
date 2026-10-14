"""The flooded gallery under the junction: where Hal hid, and drowned.

What it tells: the old gallery has been under water for years: black,
still, knee deep, with the rails running on beneath it and the ore carts
left standing in it to the axles. In the north-east the floor drops away
into a winze, roped off long ago, DANGER on a board. Hal came down here to
hide from the things in the woods. He climbed onto an ore cart in the
middle, out of the water, with a blanket and his lantern, and waited. The
web spinners found him anyway: the roof over the cart is thick with web
and a strand still runs down to it, the blanket is bloody, and there is a
bloody handprint where he slid off the side. He floats face down at the
edge of the deep water by the rope, the gondola's drive key on a chain at
his neck. The lantern on the cart is still burning low.

Metres: the floor is x 1.0-15.0, y 2.0-8.0, under knee-deep water (its
surface 0.45 up), in a gallery 7 m wide under a rock arch about 4 high,
running east-west. The way back up to the junction is the west end, where
the floor climbs out of the water into the decline. The winze, the deep
water, is x 10.5-15.0, y 2.0-4.6, behind a rope on posts. Hal floats at x
10.0, y 5.2. The cart he hid on stands at x 7.2, y 4.6.

Moving: the water rippling; Hal's body rising and settling on it; the
lantern's flame low; drops from the roof.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reb  # noqa: E402
import kit  # noqa: E402
from kit import mat  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import bpy  # noqa: E402

X0, X1, Y0, Y1 = 1.0, 15.0, 2.0, 8.0
WATER = 0.45
DEEP = (10.5, Y0, X1, 4.6)
CART = (7.2, 4.6)
HAL = (10.0, 5.2)


def web_sheet(name, corner, a, b, size, rng, strands=9):
    """A thick web across a corner: fans of silk from `corner` along directions a and b, in one mesh."""
    verts, faces = [], []
    c = Vector(corner)
    a, b = Vector(a).normalized(), Vector(b).normalized()
    side = a.cross(b).normalized() * 0.006
    for i in range(strands):
        t = i / (strands - 1)
        d = (a * (1 - t) + b * t).normalized() * size * rng.uniform(0.75, 1.0)
        k = len(verts)
        verts += [tuple(c), tuple(c + d), tuple(c + d + side)]
        faces.append((k, k + 1, k + 2))
    for r in (0.3, 0.55, 0.8):
        for i in range(strands - 1):
            p = c + (a * (1 - i / (strands - 1)) + b * (i / (strands - 1))).normalized() * size * r
            q = c + (a * (1 - (i + 1) / (strands - 1)) + b * ((i + 1) / (strands - 1))).normalized() * size * r
            k = len(verts)
            verts += [tuple(p), tuple(q), tuple(q + Vector((0, 0, -0.01)))]
            faces.append((k, k + 1, k + 2))
    ob = reb.mesh_object(name, verts, faces, mat("web"), smooth=False)
    # A haze of silk filling the corner, mostly see-through.
    reb.mesh_object(f"{name} haze", [tuple(c), tuple(c + a * size * 0.75), tuple(c + b * size * 0.75)], [(0, 1, 2)], haze_material(), smooth=False).visible_shadow = False
    return ob


_haze = []


def haze_material():
    """Web silk seen as a film: mostly transparent, pale where it catches the light."""
    if _haze:
        return _haze[0]
    m, nodes, links, bsdf = reb.nodes_material("Web haze")
    bsdf.inputs["Base Color"].default_value = (0.7, 0.7, 0.68, 1)
    bsdf.inputs["Roughness"].default_value = 0.8
    clear = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.22
    links.new(clear.outputs[0], mix.inputs[1])
    links.new(bsdf.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], nodes["Material Output"].inputs["Surface"])
    _haze.append(m)
    return m


def ore_cart(name, m, at, yaw, roll=0.0, sink=0.0):
    """A side-tipping ore cart on four wheels, standing in the water (sink lowers it into the mud)."""
    parts = [
        reb.prim("cube", "tub", m, (0, 0, 0.62), (1.1, 0.8, 0.6), bevel=0.04),
        reb.prim("cube", "chassis", mat("iron"), (0, 0, 0.27), (1.2, 0.6, 0.1)),
    ]
    for dx in (-0.38, 0.38):
        for dy in (-0.3, 0.3):
            parts.append(reb.prim("cyl", "wheel", mat("iron"), (dx, dy, 0.17), (0.34, 0.34, 0.05), rot=(math.pi / 2, 0, 0), segments=12))
    for p in parts:
        bpy.ops.object.select_all(action="DESELECT")
        p.select_set(True)
        bpy.context.view_layer.objects.active = p
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob = kit.join(name, parts)
    ob.rotation_euler = (roll, 0, yaw)
    ob.location = (at[0], at[1], -sink)
    return ob


def build():
    rng = random.Random(83)
    reb.clear_scene()
    room = kit.Room(bounds=(X0, Y0, X1, Y1), inside=True)
    room.camera((1.8, 3.1, 2.25), (9.5, 5.6, 0.3), 200, "from the foot of the decline: the black water, the cart he hid on, Hal floating by the rope")
    room.camera((14.8, 6.8, 2.3), (6.0, 3.6, 0.3), 200, "from the far south-east: Hal at the edge of the deep water, the cart, the way back up")
    room.camera((7.0, 7.0, 2.25), (10.2, 4.6, 0.2), 200, "close on Hal, face down, the key on its chain at his neck, the rope and the DANGER board")
    room.camera((12.2, 3.2, 2.3), (5.0, 7.0, 0.3), 200, "from over the winze: the cart under its web, the carts in the water, the decline")

    rock = kit.dirtied(mat("wet rock"), 0.55, scale=0.8)
    timber = kit.dirtied(reb.mat_wood("Mine timber", (0.13, 0.09, 0.05)), 0.8)
    rust = mat("rust")
    water = mat("water")
    silk = reb.mat_plain("Silk", (0.68, 0.68, 0.66), 0.6)

    # ---- The gallery: a broad arch of rock east-west, its mud floor, the black water over it.
    kit.tunnel("Gallery", rock, [(-4.0, 5.0), (19.0, 5.0)], width=7.6, height=4.0, rough=0.12, seed=21, floor_m=mat("mud"))
    reb.prim("cube", "The dark east", mat("black"), (18.5, 5.0, 1.5), (0.2, 8.0, 4.0))
    # Not a mask: from the camera over Hal the water fills more than half the
    # frame, more than a camera's mask texture holds, so her legs show over it.
    reb.prim("cube", "Black water", water, ((X0 + X1) / 2 + 1.0, 5.0, WATER), (X1 - X0 + 6.0, 7.4, 0.01))
    # The way back up: the decline's floor climbing out of the water at the west end.
    reb.prim("cube", "Decline floor", kit.dirtied(mat("mud"), 0.5), (-1.2, 5.0, 0.2), (5.0, 3.6, 0.2), rot=(0, -0.26, 0))
    reb.prim("cube", "Decline wet edge", reb.mat_plain("Wet mud", (0.015, 0.012, 0.01), 0.1), (0.6, 5.0, WATER + 0.004), (0.7, 3.4, 0.004))
    for y in (3.15, 6.85):
        kit.rod("Decline set post", timber, (-0.2, y, 0.3), (-0.2, y, 2.9), 0.11, 6)
    kit.rod("Decline set cap", timber, (-0.2, 2.9, 2.9), (-0.2, 7.1, 2.9), 0.12, 6)
    reb.prim("cube", "Decline dark", mat("black"), (-3.8, 5.0, 1.6), (0.2, 4.0, 3.0))
    # Rails under the water, the deep water's broken edge marked by posts and a rope.
    for y in (4.75, 5.35):
        kit.rod("Rail", rust, (-1.0, y, 0.12), (10.3, y, 0.12), 0.03, 6)
    dx0, dy0, dx1, dy1 = DEEP
    post_xy = [(dx0, dy1), (dx0 + 1.5, dy1 + 0.05), (dx0 + 3.0, dy1 - 0.05), (X1 + 0.2, dy1), (dx0, dy0 + 1.2)]
    for i, (x, y) in enumerate(post_xy):
        tilt = rng.uniform(-0.12, 0.12)
        kit.rod("Rope post", timber, (x, y, 0.0), (x + tilt, y + tilt * 0.5, 1.15), 0.06, 6)
    for (ax, ay), (bx, by) in zip(post_xy[:4], post_xy[1:4]):
        for k in range(6):
            t0, t1 = k / 6, (k + 1) / 6
            z0 = 1.0 - 0.25 * math.sin(math.pi * t0)
            z1 = 1.0 - 0.25 * math.sin(math.pi * t1)
            kit.rod("Rope", reb.mat_plain("Rope", (0.25, 0.2, 0.12), 0.9), (ax + (bx - ax) * t0, ay + (by - ay) * t0, z0), (ax + (bx - ax) * t1, ay + (by - ay) * t1, z1), 0.012, 4)
    kit.rod("Rope", reb.mat_plain("Rope", (0.25, 0.2, 0.12), 0.9), (dx0, dy1, 1.0), (dx0, dy0 + 1.2, 0.6), 0.012, 4)
    reb.prim("cube", "Danger board", mat("red paint"), (dx0 + 1.5, dy1 + 0.07, 0.78), (0.7, 0.03, 0.3), rot=(0, 0.12, 0))
    kit.text("Danger words", "DANGER\nWINZE", mat("white paint"), (dx0 + 1.5, dy1 + 0.09, 0.78), size=0.08, rot=(math.pi / 2, 0.12, math.pi))
    reb.prim("cube", "Winze lip timber", timber, (dx0 + 2.2, dy1 - 0.15, WATER - 0.08), (4.4, 0.2, 0.18), rot=(0, 0, 0.02))
    reb.prim("cube", "Winze dark", reb.mat_plain("Deep water", (0.003, 0.004, 0.004), 0.05), ((dx0 + X1) / 2 + 1.0, (dy0 + dy1) / 2 - 0.4, WATER + 0.002), (X1 - dx0 + 2.0, dy1 - dy0 + 1.0, 0.004))

    # ---- Timber sets down the gallery; one broken.
    tparts = []
    for i, x in enumerate([1.8 + 2.6 * k for k in range(6)]):
        for y in (1.55, 8.45):
            if i == 4 and y > 8:
                tparts.append(kit.rod("Fallen post", timber, (x, y - 0.3, WATER - 0.05), (x + 1.4, y - 1.6, WATER + 0.1), 0.11, 6))
                continue
            tparts.append(kit.rod("Set post", timber, (x, y, 0), (x, y + (0.35 if y < 5 else -0.35), 2.5), 0.11, 6))
        if i == 4:
            tparts.append(kit.rod("Sagging cap", timber, (x, 1.9, 2.5), (x + 0.2, 7.6, 1.6), 0.12, 6))
        else:
            tparts.append(kit.rod("Set cap", timber, (x, 1.8, 2.55), (x, 8.2, 2.55), 0.12, 6))
    kit.join("Timber sets", tparts)

    # ---- The carts: the one he hid on, two more standing in the water, one over on its side.
    cx, cy = CART
    hid = ore_cart("Cart he hid on", rust, (cx, cy), 0.1, sink=0.05)
    reb.wall(hid)
    reb.mask(hid)
    reb.cloth("Blanket on the cart", reb.mat_plain("Grey blanket", (0.14, 0.14, 0.13), 0.95), (cx, cy, 0.95), (1.3, 1.0), rot=(0, 0, 0.1), cuts=12, lumps=0.06, seed=4)
    kit.splat("Blood on the blanket", mat("blood"), (cx + 0.1, cy - 0.05, 1.0), 0.18, seed=5, stretch=(1.2, 0.8))
    kit.splat("Hand sliding off", mat("blood"), (cx + 0.35, cy + 0.415, 0.75), 0.06, rot=(math.pi / 2, 0, math.pi + 0.1), seed=6, lumps=0.5)
    reb.prim("cube", "Smear down the cart", mat("old blood"), (cx + 0.35, cy + 0.414, 0.55), (0.05, 0.004, 0.35), rot=(0, 0, 0.1))
    lamp, lamp_light, lamp_flame = kit.lantern("Hal's lantern", (cx - 0.3, cy + 0.15, 0.95), energy=9)
    reb.prim("cyl", "Thermos lid cup", mat("steel"), (cx + 0.3, cy - 0.2, 0.98), (0.07, 0.07, 0.06), segments=10)
    for k, (x, y, yaw, sink) in enumerate(((4.0, 5.05, 0.0, 0.1), (12.6, 6.2, 0.15, 0.08))):
        c = ore_cart(f"Cart in the water {k}", rust, (x, y), yaw, sink=sink)
        reb.wall(c)
    over = ore_cart("Cart on its side", rust, (5.6, 7.0), 1.4, roll=math.radians(-90), sink=-0.38)
    reb.wall(reb.prim("cube", "Tipped cart footprint", None, (5.6, 7.0, 0.5), (1.0, 1.3, 1.0))).hide_render = True

    # ---- Hal: face down at the edge of the deep water, the key on its chain hanging under him.
    hx, hy = HAL
    float_pivot = reb.prim("sphere", "Hal floats", None, (hx, hy, WATER - 0.12), (0.02, 0.02, 0.02))
    float_pivot.hide_render = True
    hal = kit.body("Hal", (0, 0, 0), heading=2.75, pose="front", top=mat("flannel"), legs=reb.mat_plain("Work trousers", (0.08, 0.08, 0.06), 0.9), seed=12)
    hal.parent = float_pivot
    hal.matrix_parent_inverse = Matrix.Translation(Vector((-0.0, 0, 0)))
    reb.prim("cube", "Bandaged forearm", reb.mat_surface("Bandage, soaked", [(0.0, (0.45, 0.42, 0.37)), (0.6, (0.25, 0.04, 0.03)), (1.0, (0.12, 0.01, 0.01))], scale=12), Matrix.Rotation(2.75, 4, "Z") @ Vector((1.1, -0.41, 0.07)), (0.24, 0.1, 0.1), rot=(0, 0, 2.75)).parent = float_pivot
    head = Vector((1.6 * math.cos(2.75), 1.6 * math.sin(2.75), 0.0))
    chain = []
    for k in range(9):
        t = k / 8
        p = head * 0.85 + Vector((0.05 * math.sin(t * 3), 0.04, -0.12 - 0.35 * t))
        chain.append(reb.prim("sphere", "Chain link", mat("steel"), p, (0.025, 0.012, 0.03), segments=6))
    key = reb.prim("cube", "Drive key", reb.mat_metal("Brass", (0.55, 0.4, 0.15), 0.3), head * 0.85 + Vector((0.05, 0.04, -0.52)), (0.03, 0.01, 0.1))
    for p in chain + [key]:
        p.parent = float_pivot
    reb.cloth("His shirt floating", mat("flannel"), (hx + 0.2, hy + 0.1, WATER + 0.01), (0.9, 0.7), rot=(0, 0, 2.75), cuts=10, lumps=0.03, seed=13)
    hair = reb.prim("sphere", "Hair spread on the water", mat("black"), (hx + head.x, hy + head.y, WATER + 0.005), (0.3, 0.26, 0.01), segments=10)
    kit.splat("Blood in the water", reb.mat_plain("Blood clouding", (0.06, 0.006, 0.004), 0.05), (hx + 0.3, hy - 0.1, WATER + 0.003), 0.7, seed=14, stretch=(1.3, 0.9), lumps=0.6)
    reb.wall(reb.prim("cube", "Hal footprint", None, (hx - 0.2, hy + 0.2, 0.5), (1.8, 1.0, 1.0), rot=(0, 0, 0.3))).hide_render = True

    # ---- The webs: thick over the cart, strands down; sheets in the arch; a few sacs.
    web_sheet("Web over the cart", (cx, cy - 1.0, 3.1), (1, 0.6, -0.35), (-0.9, 0.7, -0.3), 1.9, rng, strands=15)
    web_sheet("Web over the cart 2", (cx + 0.4, cy + 1.0, 3.0), (0.8, -0.7, -0.4), (-1, -0.4, -0.3), 1.5, rng, strands=12)
    kit.rod("Strand to the cart", silk, (cx + 0.1, cy, 3.1), (cx + 0.05, cy + 0.1, 1.0), 0.006, 3)
    strands = []
    for _ in range(26):
        a = Vector((rng.uniform(X0, X1), rng.uniform(Y0 + 0.5, Y1 - 0.5), 3.0))
        b = a + Vector((rng.uniform(-1.2, 1.2), rng.uniform(-1.2, 1.2), -rng.uniform(1.0, 2.5)))
        strands.append(kit.rod("Strand", silk, a, b, 0.003, 3))
    kit.join("Strands", strands)
    for i, x in enumerate((1.8, 6.9, 12.1)):
        web_sheet(f"Arch web {i}", (x, 1.8, 2.55), (1, 0.3, 0.1), (0.1, 0.5, -1), 1.1, rng)
        web_sheet(f"Arch web {i} south", (x + 0.1, 8.2, 2.55), (1, -0.3, 0.1), (0.1, -0.5, -1), 1.0, rng)
    sv, sf = [], []
    for _ in range(8):
        reb.boulder(rng, (cx + rng.uniform(-1.2, 1.2), cy + rng.uniform(-1.0, 1.0), 2.85), rng.uniform(0.09, 0.15), sv, sf, squash=1.3)
    reb.mesh_object("Egg sacs", sv, sf, reb.mat_surface("Egg sac", [(0.0, (0.42, 0.4, 0.33)), (1.0, (0.62, 0.6, 0.52))], scale=18, rough=0.5, bump=0.6))

    # ---- Floating rubbish: timber, a hard hat, a lamp cable dangling into the water; the lamps.
    for k in range(5):
        reb.prim("cube", "Floating plank", timber, (rng.uniform(2.5, 14.0), rng.uniform(2.6, 7.6), WATER), (rng.uniform(0.6, 1.4), 0.14, 0.05), rot=(0, 0, rng.uniform(0, 3)))
    reb.prim("sphere", "Floating hard hat", mat("white paint"), (3.2, 6.9, WATER + 0.02), (0.28, 0.25, 0.18), rot=(math.pi, 0.3, 0))
    lamps = []
    for k, (x, y, e) in enumerate(((1.2, 5.0, 55), (9.0, 5.2, 40), (13.4, 4.6, 30))):
        glow = reb.mat_emit(f"Lamp glow {k}", (1.0, 0.72, 0.4), 12)
        pivot = reb.prim("sphere", f"Lamp hook {k}", mat("iron"), (x, y, 2.75), (0.03, 0.03, 0.03))
        kit.rod(f"Lamp flex {k}", mat("black"), (0, 0, 0), (0, 0, -0.4), 0.007, 4).parent = pivot
        reb.prim("sphere", f"Lamp bulb {k}", glow, (0, 0, -0.48), (0.08, 0.08, 0.11), segments=10).parent = pivot
        light = reb.point(f"Lamp {k}", (0, 0, -0.52), e, (1.0, 0.68, 0.38), 0.05)
        light.parent = pivot
        lamps.append((pivot, light, glow))
    kit.rod("Lamp cable", mat("black"), (-3.0, 5.0, 2.75), (1.2, 5.0, 2.75), 0.01, 4)
    kit.rod("Lamp cable", mat("black"), (1.2, 5.0, 2.75), (9.0, 5.2, 2.75), 0.01, 4)
    kit.rod("Lamp cable", mat("black"), (9.0, 5.2, 2.75), (13.4, 4.6, 2.75), 0.01, 4)
    kit.rod("Lamp cable down", mat("black"), (13.4, 4.6, 2.75), (14.6, 6.4, WATER), 0.01, 4)
    # Underground: no sky. The lamps, Hal's lantern and a cold fill under the arch.
    reb.point("Under-arch fill", (7.0, 5.0, 3.0), 40, (0.6, 0.65, 0.75), 3.0)
    reb.point("Fill over the winze", (12.5, 4.0, 3.0), 18, (0.6, 0.65, 0.75), 2.0)

    anim = kit.Anim(16)
    anim.ripple(water, speed=1)
    anim.custom(lambda k: setattr(float_pivot, "location", (hx, hy, WATER - 0.12 + 0.025 * math.sin(anim.phase(k)))))
    anim.custom(lambda k: setattr(float_pivot, "rotation_euler", (math.radians(2) * math.sin(anim.phase(k) + 1.0), 0, 0.04 * math.sin(anim.phase(k)))))
    anim.flicker(lamp_light, lamp_flame, depth=0.4, dropouts=1)
    for k, (pivot, light, glow) in enumerate(lamps):
        anim.flicker(light, glow, depth=0.1 if k == 0 else 0.45, dropouts=0 if k == 0 else 2)
    anim.drip((cx + 0.6, cy - 0.4, 3.0), fall=3.0 - WATER, size=0.015)

    # ---- What the game needs.
    room.void(DEEP)
    room.door("junction", (X0, 3.6, X0 + 0.6, 6.4), arrive=(2.6, 5.0), face=(1, 0))
    room.check((hx - 1.3, hy - 0.5, hx + 0.9, hy + 1.0), "Hal. Face down in the water. Something bit him: his arm's\nbandaged, black under it.\nThere's a key on a chain round his neck.")
    room.check((cx - 0.9, cy - 0.7, cx + 0.9, cy + 0.7), "He hid up on this cart, out of the water. Blanket, lantern.\nThere's blood where he slid off.")
    room.check((dx0 - 0.3, dy1, dx0 + 3.5, dy1 + 0.6), "DANGER. WINZE. The floor drops away under the water there.")
    room.entry = "The water's cold. It's black. I can't see the floor."
    room.export(anim)


build()
