#!/usr/bin/env python3
"""Index room visits from logs and video, or cut the committed index on pi-server.

python3 clips.py index recording-events.json source_dir image_dir manifest.json
python3 clips.py cut manifest.json source_dir publish_dir
Requires ffmpeg and ffprobe. Index also needs Pillow and NumPy.
"""
import argparse
import bisect
import hashlib
import json
from pathlib import Path
import subprocess


def run(*args):
    return subprocess.check_output([str(a) for a in args])


def probe(path):
    return json.loads(run('ffprobe', '-v', 'error', '-show_entries',
                          'format=duration:stream=codec_name,width,height', '-of', 'json', path))


def checked_source(source, q):
    path = source / q['video']
    if hashlib.sha256(path.read_bytes()).hexdigest() != q['sha256']:
        raise ValueError(f"Source hash differs: {path}")
    return path


def index(args):
    import numpy as np
    from PIL import Image
    recording = json.loads(args.input.read_text())
    refs, names = [], []
    for room in recording['rooms']:
        for image in sorted(args.images.glob(f"{room['slug']}-cam*.jpg")):
            refs.append(np.asarray(Image.open(image).convert('RGB').resize((64, 48)), dtype=np.float32)[6:42])
            names.append(room['room'])
    refs = np.array(refs)
    clips, quarters, counts = [], [], {}
    for q in recording['quarters']:
        source = checked_source(args.source, q)
        duration = float(probe(source)['format']['duration'])
        # Half-second samples. Crop letterbox bars, then discard the worst 30%
        # of pixel errors so Rebecca and dialogue do not dominate the background.
        cache = args.output.parent / f"{q['sha256']}-2fps.npy"
        if cache.exists():
            frames = np.load(cache)
        else:
            raw = run('ffmpeg', '-v', 'error', '-i', source, '-vf', 'fps=2,scale=64:48',
                      '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-')
            frames = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 48, 64, 3)[:, 6:42]
            np.save(cache, frames)
        frames = frames.astype(np.float32)
        visits = []
        for event in q['events']:
            if not visits or visits[-1]['room'] != event['room']:
                visits.append({'room': event['room'], 'events': []})
            visits[-1]['events'].append(event)
        log_starts = [v['events'][0]['t'] * q['scale'] + q['offset'] for v in visits]
        matches, distances = [], []
        for f, frame in enumerate(frames):
            current = max(0, bisect.bisect_right(log_starts, f / 2) - 1)
            # The log fixes the visit order. An entry scene may precede its log
            # stamp, so compare the current room and the next two rooms.
            # The boot intro is unlogged in quarters 2 to 4. Keep its ridge
            # render in the comparison so it cannot become a false room match.
            allowed = {'ridge'} | {v['room'] for v in visits[current:current + 3]}
            indices = [i for i, name in enumerate(names) if name in allowed]
            if not indices:
                matches.append(None)
                distances.append(float('inf'))
                continue
            errors = np.abs(refs[indices] - frame).mean(axis=3).reshape(len(indices), -1)
            keep = int(errors.shape[1] * .7)
            score = np.partition(errors, keep, axis=1)[:, :keep].mean(axis=1)
            best = int(score.argmin())
            matches.append(names[indices[best]])
            distances.append(float(score[best]))
        starts, posters, warnings = [], [], []
        for i, visit in enumerate(visits):
            first = visit['events'][0]['t'] * q['scale'] + q['offset']
            previous = visits[i - 1]['events'][-1]['t'] * q['scale'] + q['offset'] if i else 0
            # Do not count the opening ridge scene before a checkpoint restore.
            lo = max(0 if q['quarter'] == 1 else 22, previous - 1, (starts[-1] + .5) if starts else 0)
            hi = min(duration - .5, first + 12)
            candidates = [f for f in range(max(0, int(lo * 2)), min(len(frames) - 1, int(hi * 2)) + 1)
                          if matches[f] == visit['room'] and distances[f] < 20
                          and matches[min(f + 1, len(frames) - 1)] == visit['room']
                          and float(frames[f].std()) > 6 and float(frames[f].mean()) > 8]
            if candidates:
                first_frame = candidates[0]
                start = first_frame / 2
                poster = min(candidates, key=lambda f: distances[f]) / 2
                warning = ''
            elif manual := next((m for m in q['manualEntries'] if m['room'] == visit['room']), None):
                start, poster, warning = manual['start'], manual['poster'], manual['note']
            else:
                raise ValueError(f"No background match for q{q['quarter']} {visit['room']} near {first}: inspect video")
            if i == 0 and q['quarter'] == 1:
                start = 0  # Keep the opening text and ridge cutscene.
            if starts and start <= starts[-1]:
                raise ValueError(f"Overlapping visit starts: {visit['room']}")
            starts.append(start)
            posters.append(poster)
            warnings.append(warning)
        # Copy from real source keyframes. This preserves H.264 without another
        # lossy encode and gives every clip a decodable first frame.
        keyframes = json.loads(run('ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_packets', '-show_entries', 'packet=pts_time,flags', '-of', 'json', source))
        keys = sorted(float(p['pts_time']) for p in keyframes['packets'] if 'K' in p['flags'])
        for i, visit in enumerate(visits):
            room = visit['room']
            counts[room] = counts.get(room, 0) + 1
            # Three seconds of lead-in preserves the incoming door. End at the
            # next room's first matched frame, retaining the outgoing door too.
            wanted = max(0, starts[i] - 3)
            start = keys[max(0, bisect.bisect_right(keys, wanted) - 1)]
            # Capture shutdown truncated the final packet in each source. Stop
            # on a complete keyframe at least a second before the source tail.
            safe_end = keys[max(0, bisect.bisect_right(keys, duration - 1) - 1)]
            end = starts[i + 1] if i + 1 < len(starts) else safe_end
            file = f"clips/{room}-q{q['quarter']}-v{counts[room]:02}.mp4"
            clips.append({'room': room, 'quarter': q['quarter'], 'visit': counts[room],
                'start': round(start, 3), 'end': round(end, 3), 'roomStart': starts[i],
                'posterTime': posters[i], 'file': file, 'poster': file.replace('.mp4', '.jpg'),
                'note': warnings[i], 'events': visit['events']})
        quarters.append({k: v for k, v in q.items() if k != 'events'} | {'duration': duration})
        print(f"q{q['quarter']}: {len(visits)} visits, {duration:.1f} seconds", flush=True)
    manifest = {'recorded': recording['recorded'], 'method': 'Run logs, refined by 2 fps background matches',
        'timing': 'Wall-clock capture, scale 1, log offset -4 seconds. First sustained room match sets entry. Three-second door lead-in rounded back to a source keyframe. Final damaged packet excluded at the preceding complete keyframe.',
        'quarters': quarters, 'clips': clips,
        'noFootage': [r['room'] for r in recording['rooms'] if r['room'] not in counts]}
    args.output.write_text(json.dumps(manifest, indent=2) + '\n')
    print(f"{len(clips)} clips in {len(counts)} rooms; no footage: {', '.join(manifest['noFootage'])}")


def cut(args):
    manifest = json.loads(args.input.read_text())
    sources = {q['quarter']: checked_source(args.source, q) for q in manifest['quarters']}
    (args.publish / 'clips').mkdir(parents=True, exist_ok=True)
    total = 0
    for clip in manifest['clips']:
        target = args.publish / clip['file']
        # Manifest milliseconds may round a 30 fps keyframe down. Seek just
        # after that instant, or the demuxer can choose the previous GOP.
        seek = f"{clip['start'] + .001:.6f}"
        run('ffmpeg', '-y', '-v', 'error', '-ss', seek, '-i', sources[clip['quarter']],
            '-t', round(clip['end'] - clip['start'], 3), '-map', '0:v:0', '-c', 'copy',
            '-avoid_negative_ts', 'make_zero', '-movflags', '+faststart', target)
        run('ffmpeg', '-y', '-v', 'error', '-ss', clip['posterTime'], '-i', sources[clip['quarter']],
            '-frames:v', 1, '-q:v', 3, args.publish / clip['poster'])
        info = probe(target)
        stream = info['streams'][0]
        duration = float(info['format']['duration'])
        if stream['codec_name'] != 'h264' or stream['width'] != 640 or duration <= 0 or abs(duration - (clip['end'] - clip['start'])) >= 1:
            raise ValueError(f"Invalid clip: {target}")
        total += target.stat().st_size
        print(f"{clip['file']}: {float(info['format']['duration']):.1f}s", flush=True)
    print(f"Total video: {total} bytes, {total / 1024 ** 2:.2f} MiB")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    indexing = sub.add_parser('index')
    indexing.add_argument('input', type=Path)
    indexing.add_argument('source', type=Path)
    indexing.add_argument('images', type=Path)
    indexing.add_argument('output', type=Path)
    cutting = sub.add_parser('cut')
    cutting.add_argument('input', type=Path)
    cutting.add_argument('source', type=Path)
    cutting.add_argument('publish', type=Path)
    args = parser.parse_args()
    (index if args.command == 'index' else cut)(args)
