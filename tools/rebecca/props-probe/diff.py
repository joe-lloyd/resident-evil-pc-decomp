"""Objects whose world box changed between two probe runs: python3 diff.py <before> <after> slug..."""
import json, os, sys
a, b = sys.argv[1], sys.argv[2]
for slug in sys.argv[3:]:
    x = json.load(open(os.path.join(a, slug + ".json")))["all"]
    y = json.load(open(os.path.join(b, slug + ".json")))["all"]
    moved = [n for n in x if n in y and max(abs(p - q) for p, q in zip(x[n], y[n])) > 0.005]
    only = sorted(set(x) ^ set(y))
    print(f"== {slug}: {len(moved)} moved, {len(only)} added/removed")
    for n in moved:
        print("   ", n, x[n], "->", y[n])
    for n in only[:10]:
        print("    only in", "before" if n in x else "after", n)
