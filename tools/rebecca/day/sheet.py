"""A contact sheet of a room's cameras, to look at a scene in one picture.

    python3 tools/rebecca/day/sheet.py <renders dir> <out.png> [scale]

Every cam<N>.png in the folder side by side, two to a row, scaled up
(default 2x) and labelled.
"""
import sys, glob, os, re
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]
cams = sorted(glob.glob(os.path.join(d, 'cam*.png')), key=lambda p: p)
cams = [p for p in cams if re.search(r'cam\d+\.png$', p)]
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 2
w, h = int(320 * scale), int(240 * scale)
cols = 2 if len(cams) > 1 else 1
rows = (len(cams) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, rows * h), (0, 0, 0))
for i, p in enumerate(cams):
    im = Image.open(p).convert('RGB').resize((w, h), Image.NEAREST)
    ImageDraw.Draw(im).text((6, 4), os.path.basename(p), fill=(255, 255, 0))
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out)
