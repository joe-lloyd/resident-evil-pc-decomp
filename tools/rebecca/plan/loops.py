"""Animated WebP loops of a room's cameras, for the planning page.

    python3 tools/rebecca/plan/loops.py <renders dir> <out dir> <prefix> <frames> <ticks>

For each cam<N>.png with cam<N>.a1.png .. a<frames-1>.png beside it, writes
<prefix>-cam<N>.webp looping the frames at the game's speed (ticks game
frames, 30 a second, for each picture). Prints the names written.
"""
import glob
import os
import re
import sys

from PIL import Image

src, out, prefix, frames, ticks = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
for still in sorted(glob.glob(os.path.join(src, "cam*.png"))):
    m = re.search(r"cam(\d+)\.png$", still)
    if not m:
        continue
    n = m.group(1)
    paths = [still] + [os.path.join(src, f"cam{n}.a{k}.png") for k in range(1, frames)]
    if not all(os.path.exists(p) for p in paths):
        continue
    images = [Image.open(p).convert("RGB") for p in paths]
    name = f"{prefix}-cam{n}.webp"
    images[0].save(os.path.join(out, name), save_all=True, append_images=images[1:], duration=round(ticks * 1000 / 30), loop=0, quality=82, method=4)
    print(name)
