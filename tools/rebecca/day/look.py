"""Give a render the look of RE1's backgrounds: shrink a big render with a
sharp filter, crush the blacks, pull the colour toward the game's sickly
green-amber, darken the corners, lay a fixed grain over it, and round it to
the 15-bit colour the game shows.

    python3 tools/rebecca/day/look.py <in.png> <out.png> [strength 0..1]

A sample for now: build.ts does not run it. The grain is seeded, so the same
render always gets the same grain and an animated frame matches its still.
"""
import random
import sys

from PIL import Image, ImageChops, ImageEnhance, ImageFilter

W, H = 320, 240


def curve(strength):
    """Crush the blacks and steepen the mids: an S over 0..255."""
    lut = []
    for v in range(256):
        x = v / 255
        s = x * x * (3 - 2 * x)  # smoothstep
        y = x + (s - x) * 0.35 * strength
        y = max(0.0, (y - 0.015 * strength) / (1 - 0.015 * strength))
        lut.append(round(min(1.0, y) * 255))
    return lut


def tint(im, strength):
    """Shadows toward green-teal, highlights toward amber, a little less saturated."""
    im = ImageEnhance.Color(im).enhance(1 - 0.15 * strength)
    r, g, b = im.split()
    r = r.point(lambda v: round(v * (1 + 0.04 * strength * v / 255) - 4 * strength * (1 - v / 255)))
    g = g.point(lambda v: round(v + 3 * strength * (1 - v / 255)))
    b = b.point(lambda v: round(v * (1 - 0.1 * strength * v / 255)))
    return Image.merge("RGB", (r, g, b))


def vignette(im, strength):
    g = Image.radial_gradient("L").resize((W, H))  # 0 in the middle, 255 at the edge
    g = g.point(lambda v: round(255 - min(255, max(0, v - 90) * 1.5) * 0.3 * strength))
    return ImageChops.multiply(im, Image.merge("RGB", (g, g, g)))


def grain(im, strength, seed):
    random.seed(seed)
    n = Image.effect_noise((W, H), 4 * strength).point(lambda v: v)  # grey around 128
    noise = Image.merge("RGB", (n, n, n))
    # Add (noise - 128): mostly in the mids, as film and dithered textures do.
    return ImageChops.add(ImageChops.subtract(im, Image.new("RGB", (W, H), (0, 0, 0))), noise, 1.0, -128)


def to555(im):
    return im.point(lambda v: min(31, (v + 4) >> 3) * 255 // 31)


def look(im, strength=1.0, seed=0):
    im = im.convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
        im = im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=40, threshold=2))
    im = tint(im, strength).point(curve(strength) * 3)
    im = vignette(im, strength)
    im = grain(im, strength, seed)
    return to555(im)


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    s = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    look(Image.open(src), s).save(dst)
