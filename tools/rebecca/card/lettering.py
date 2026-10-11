"""Draw the lettering for Rebecca's police ID: her name, her number and her
signature, as an ink mask the size of the ID half of a select-screen card
(112 x 128). Black is full ink, white is none. card.ts lays it over the ID it
builds from the player's own select-screen sheet.

Run once with Pillow on a Mac (it uses the system's Courier New Bold and
Snell Roundhand); the mask it writes is committed, so a build needs neither.

    python3 tools/rebecca/card/lettering.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = "/System/Library/Fonts/Supplemental"
W, H = 112, 128
SCALE = 4  # draw large, shrink: smoother strokes at card size


def draw():
    big = Image.new("L", (W * SCALE, H * SCALE), 255)
    d = ImageDraw.Draw(big)
    type_font = ImageFont.truetype(os.path.join(FONTS, "Courier New Bold.ttf"), 10 * SCALE)
    sign_font = ImageFont.truetype(os.path.join(FONTS, "SnellRoundhand.ttc"), 11 * SCALE, index=2)

    def centred(text, font, cx, top, stroke=0):
        x0, y0, x1, y1 = d.textbbox((0, 0), text, font=font, stroke_width=stroke)
        d.text((cx * SCALE - (x1 - x0) / 2 - x0, top * SCALE - y0), text, font=font, fill=0, stroke_width=stroke, stroke_fill=0)

    # Typed like the others: heavy, in the card's typewriter.
    centred("Rebecca Chambers", type_font, 56, 29.5, stroke=SCALE // 3)
    centred("0 6 1 9", type_font, 77, 71, stroke=SCALE // 3)
    # Signed over the line, smaller than her typed name.
    centred("Rebecca Chambers", sign_font, 53, 46.5, stroke=SCALE // 4)
    small = big.resize((W, H), Image.LANCZOS).convert("RGB")
    small.save(os.path.join(HERE, "rebecca-id-lettering.png"))


draw()
