"""The walk between Rebecca's outdoor rooms: a dirt path through the spruces,
seen at her eye height as she walks it, a pool of grey morning light around
her and darkness beyond. Plays where a door animation would
(src/game/PathWalk.cpp), with her footsteps.

Metres, real sizes. The path runs along +y; she walks 3 m of it in 3.2 s.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import reb  # noqa: E402
from mathutils import Vector, noise  # noqa: E402

OUT = os.environ.get("RE1_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders"))
FRAMES = 48          # at 2 game frames each: 3.2 s
TICKS = 2
STEP_TICKS = 16      # a step every 0.53 s: a slow, careful walk
EYE = 1.5
WALKED = 3.0


def height(x, y):
    side = abs(x)
    bank = max(0.0, side - 0.7) * 0.35
    return bank + 0.05 * noise.noise(Vector((x * 1.5, y * 1.5, 0))) + 0.25 * noise.noise(Vector((x * 0.3, y * 0.3, 4))) * min(1.0, side / 2)


def build():
    rng = random.Random(77)
    reb.clear_scene()
    dirt = reb.mat_surface("Path dirt", [(0.0, (0.05, 0.04, 0.03)), (0.35, (0.12, 0.09, 0.06)), (0.6, (0.17, 0.13, 0.09)), (1.0, (0.22, 0.18, 0.13))], scale=14, detail=14, bump=1.0)
    ground = reb.mat_surface("Forest floor", [(0.0, (0.02, 0.02, 0.015)), (0.5, (0.05, 0.05, 0.03)), (1.0, (0.08, 0.07, 0.05))], scale=3, bump=0.6)
    blades = reb.mat_cards("Grass", (0.05, 0.07, 0.025), (0.16, 0.18, 0.07))
    ferns = reb.mat_cards("Fern", (0.03, 0.07, 0.025), (0.08, 0.14, 0.04))
    needles = reb.mat_cards("Needles", (0.015, 0.035, 0.02), (0.05, 0.09, 0.04))
    dead = reb.mat_cards("Dry needles", (0.1, 0.075, 0.035), (0.18, 0.15, 0.07))
    bark = reb.mat_surface("Bark", [(0.0, (0.03, 0.022, 0.016)), (1.0, (0.09, 0.065, 0.045))], scale=10, bump=0.9)
    rock = reb.mat_surface("Rock", [(0.0, (0.05, 0.05, 0.045)), (1.0, (0.16, 0.15, 0.13))], scale=3, bump=0.9)

    reb.terrain("Ground", ground, (-8, 8), (-3, 16), height, step=0.15)
    # The path: worn dirt a metre and a half wide, wandering a little.
    v, f = [], []
    for i in range(80):
        y0, y1 = -2 + 17 * i / 80, -2 + 17 * (i + 1) / 80
        c0, c1 = 0.15 * math.sin(y0 * 0.5), 0.15 * math.sin(y1 * 0.5)
        w0 = 0.7 + 0.12 * noise.noise(Vector((0, y0, 2)))
        w1 = 0.7 + 0.12 * noise.noise(Vector((0, y1, 2)))
        k = len(v)
        for x, y in ((c0 - w0, y0), (c0 + w0, y0), (c1 + w1, y1), (c1 - w1, y1)):
            v.append((x, y, height(x, y) + 0.006))
        f.append((k, k + 1, k + 2, k + 3))
    reb.mesh_object("Path", v, f, dirt)
    # Stones, roots and needles on it.
    sv, sf = [], []
    for _ in range(90):
        x, y = rng.uniform(-0.8, 0.8), rng.uniform(-1, 15)
        reb.boulder(rng, (x, y, height(x, y)), rng.uniform(0.015, 0.05), sv, sf, squash=0.5)
    reb.mesh_object("Stones", sv, sf, rock)
    for _ in range(6):
        y = rng.uniform(1, 14)
        reb.prim("cyl", "Root", bark, (0, y, 0.015), (0.045, 0.045, 2.2), rot=(0, math.pi / 2, rng.uniform(-0.5, 0.5)), segments=8)
    dv, df = [], []
    for _ in range(1600):
        x, y = rng.uniform(-3, 3), rng.uniform(-1, 15)
        reb.card(dv, df, Vector((x, y, height(x, y) + 0.008)), Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), Vector((0, 0, 1)), 0.03, rng.uniform(0.06, 0.18), 0.0)
    reb.mesh_object("Needles on the path", dv, df, dead)
    # Grass and ferns crowding the edges.
    gv, gf = [], []
    def edges(rr):
        while True:
            x, y = rr.uniform(-4, 4), rr.uniform(-1, 15)
            if abs(x - 0.15 * math.sin(y * 0.5)) > 0.8:
                return x, y
    reb.grass_tufts(rng, 2600, edges, height, gv, gf)
    for i in range(2, len(gv), 3):
        b = (Vector(gv[i - 2]) + Vector(gv[i - 1])) / 2
        gv[i] = tuple(b + (Vector(gv[i]) - b) * 1.3)
    reb.mesh_object("Grass", gv, gf, blades, smooth=False)
    fv, ff = [], []
    for _ in range(40):
        side = rng.choice((-1, 1))
        x, y = side * rng.uniform(0.9, 3.5), rng.uniform(-1, 15)
        reb.fern(rng, (x, y, height(x, y)), rng.uniform(0.4, 0.9), fv, ff)
    reb.mesh_object("Ferns", fv, ff, ferns)
    # Spruces close on both sides, their trunks lit as she passes.
    tv, tf, bases = [], [], []
    for _ in range(40):
        side = rng.choice((-1, 1))
        x, y = side * rng.uniform(1.6, 7), rng.uniform(-2, 18)
        if any((Vector((x, y)) - b.xy).length < 1.4 for b, _ in bases):
            continue
        bases.append((Vector((x, y, height(x, y) - 0.2)), rng.uniform(12, 20)))
    for base, h in bases:
        reb.conifer(rng, base, h, tv, tf)
    reb.mesh_object("Spruces", tv, tf, needles)
    reb.trunks("Trunks", bark, bases)

    # Light: no sky to speak of, a little grey from above, and a soft pool of
    # light that walks with her. Mist eats the far end.
    world = bpy.data.worlds.new("Dark")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.005, 0.007, 1)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 7, 3))
    mist = bpy.context.active_object
    mist.name = "Mist"
    mist.scale = (20, 26, 8)
    m = bpy.data.materials.new("Mist")
    m.use_nodes = True
    nodes = m.node_tree.nodes
    nodes.remove(nodes["Principled BSDF"])
    vol = nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = 0.025
    vol.inputs["Color"].default_value = (0.3, 0.33, 0.38, 1)
    m.node_tree.links.new(vol.outputs["Volume"], nodes["Material Output"].inputs["Volume"])
    mist.data.materials.append(m)
    lamp = reb.spot("Her light", (0, 0, EYE), (0, 3, 0), 900, (0.85, 0.88, 0.95), 70, 0.9, 0.8)
    reb.point("Grey from above", (0, 5, 6), 120, (0.6, 0.65, 0.75), 3.0)

    def pose(k):
        t = k * TICKS / 30.0
        y = WALKED * k / (FRAMES - 1)
        steps = t * 30.0 / STEP_TICKS
        bob = 0.025 * abs(math.sin(math.pi * steps))
        sway = 0.02 * math.sin(math.pi * steps)
        x = 0.15 * math.sin(y * 0.5) + sway
        eye = (x, y, height(x, y) + EYE - 0.025 + bob)
        at = (0.15 * math.sin((y + 4) * 0.5), y + 4, height(0, y + 4) + 0.6)
        return eye, at

    reb.export_walk(pose, FRAMES, OUT, samples=128, ticks=TICKS, step_ticks=STEP_TICKS, light=lamp)


build()
