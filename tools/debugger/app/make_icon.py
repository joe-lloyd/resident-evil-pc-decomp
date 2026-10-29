"""Draw the debugger's app icon: a top-down room map in the dashboard's colours.

    python3 tools/debugger/app/make_icon.py

Writes icon.png (1024 px, the Windows and Linux icon) and icon.iconset/ (macOS)
next to this script. Needs Pillow. Everything is drawn at 4x and scaled down,
which is the antialiasing.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
S = 4096  # working size
U = S / 1024  # one unit of the 1024 px design


def p(*xy):
    return [v * U for v in xy]


def layer():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def draw_icon() -> Image.Image:
    # Background: a rounded square with a dark vertical gradient.
    grad = Image.new("RGBA", (S, S))
    gd = ImageDraw.Draw(grad)
    for y in range(S):
        t = y / S
        c = tuple(round(a + (b - a) * t) for a, b in zip((24, 29, 36), (9, 11, 14)))
        gd.line([(0, y), (S, y)], fill=c + (255,))
    mask = layer()
    ImageDraw.Draw(mask).rounded_rectangle(p(40, 40, 984, 984), radius=220 * U, fill=(255, 255, 255, 255))
    icon = layer()
    icon.paste(grad, (0, 0), mask)

    # Faint grid, clipped to the square.
    grid = layer()
    g = ImageDraw.Draw(grid)
    for v in range(104, 984, 80):
        g.line(p(v, 40, v, 984), fill=(111, 179, 255, 18), width=round(3 * U))
        g.line(p(40, v, 984, v), fill=(111, 179, 255, 18), width=round(3 * U))
    icon.alpha_composite(Image.composite(grid, layer(), mask))

    d = ImageDraw.Draw(icon)

    # Walls: one room with a doorway in the south wall and a partition.
    wall = (70, 82, 98, 255)
    for box in [(170, 170, 854, 230), (170, 170, 230, 854), (794, 170, 854, 854), (170, 794, 430, 854), (594, 794, 854, 854), (520, 170, 580, 380)]:
        d.rounded_rectangle(p(*box), radius=12 * U, fill=wall)

    # A camera switch zone in the far corner: a blue quad, tinted inside.
    zone = layer()
    ImageDraw.Draw(zone).polygon(p(624, 280, 750, 272, 756, 432, 630, 440), fill=(111, 179, 255, 52), outline=(111, 179, 255, 255), width=round(10 * U))
    icon.alpha_composite(zone)

    # The camera: a yellow eye in the corner and its view cone across the room.
    eye = (292, 292)
    reach, half = 560, math.radians(15)
    aim = math.atan2(670 - eye[1], 700 - eye[0])  # at the enemy
    pts = [eye] + [(eye[0] + reach * math.cos(aim + a), eye[1] + reach * math.sin(aim + a)) for a in (-half, half)]
    cone = layer()
    ImageDraw.Draw(cone).polygon([v * U for xy in pts for v in xy], fill=(231, 184, 75, 72))
    icon.alpha_composite(cone)
    d.ellipse(p(eye[0] - 34, eye[1] - 34, eye[0] + 34, eye[1] + 34), fill=(231, 184, 75, 255))

    # The player's trail: dashes in from the doorway, curving into the arrow.
    def bez(t):
        a, b, c = (512, 830), (500, 640), (370, 560)
        return tuple((1 - t) ** 2 * a[i] + 2 * (1 - t) * t * b[i] + t * t * c[i] for i in (0, 1))

    trail = [bez(i / 18) for i in range(19)]
    for i in range(0, 16, 2):
        d.line(p(*trail[i], *trail[i + 1]), fill=(52, 140, 100, 255), width=round(20 * U))

    # An enemy with a soft red glow.
    glow = layer()
    ImageDraw.Draw(glow).ellipse(p(610, 580, 790, 760), fill=(239, 100, 97, 150))
    icon.alpha_composite(glow.filter(ImageFilter.GaussianBlur(26 * U)))
    d.ellipse(p(660, 630, 740, 710), fill=(239, 100, 97, 255))

    # The player: the dashboard's green arrow, heading along the trail.
    tip = trail[-1]
    a = math.atan2(trail[-1][1] - trail[-2][1], trail[-1][0] - trail[-2][0])
    fx, fy = math.cos(a), math.sin(a)
    head = (tip[0] + fx * 80, tip[1] + fy * 80)
    left = (tip[0] - fx * 36 - fy * 56, tip[1] - fy * 36 + fx * 56)
    right = (tip[0] - fx * 36 + fy * 56, tip[1] - fy * 36 - fx * 56)
    d.polygon([v * U for xy in (head, left, right) for v in xy], fill=(79, 195, 138, 255))

    # A thin rim so the icon holds its edge on a dark taskbar.
    ImageDraw.Draw(icon).rounded_rectangle(p(40, 40, 984, 984), radius=220 * U, outline=(52, 61, 73, 255), width=round(6 * U))
    return icon.resize((1024, 1024), Image.LANCZOS)


def main() -> None:
    icon = draw_icon()
    icon.save(HERE / "icon.png")
    iconset = HERE / "icon.iconset"
    iconset.mkdir(exist_ok=True)
    for size in (16, 32, 128, 256, 512):
        icon.resize((size, size), Image.LANCZOS).save(iconset / f"icon_{size}x{size}.png")
        icon.resize((size * 2, size * 2), Image.LANCZOS).save(iconset / f"icon_{size}x{size}@2x.png")


if __name__ == "__main__":
    main()
