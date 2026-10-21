"""Cut one checked scene recording and replace only that scene in clips.json.

Run on pi-server (ffmpeg and ffprobe), with the recording JSON and MP4 in
one folder. Bounds are seconds in the source video, checked by eye first.

python3 replace-scene.py recording.json clips.json publish-dir \
    --start 0 --end 70 --poster 35 --note 'Frames checked at ...'
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


def run(*args):
    return subprocess.check_output([str(a) for a in args], stderr=subprocess.PIPE)


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def replace(clips, scene, replacement):
    first = next((i for i, c in enumerate(clips) if c['room'] == scene), len(clips))
    kept = [c for c in clips if c['room'] != scene]
    kept[first:first] = replacement
    return kept


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('recording', type=Path)
    p.add_argument('manifest', type=Path)
    p.add_argument('publish', type=Path)
    p.add_argument('--start', type=float, required=True)
    p.add_argument('--end', type=float, required=True)
    p.add_argument('--poster', type=float, required=True)
    p.add_argument('--note', required=True)
    args = p.parse_args()
    recording = json.loads(args.recording.read_text())
    scene = recording['scene']
    if not re.fullmatch(r'[a-z0-9-]+', scene) or recording['result'] != 'PASS':
        raise ValueError('Use a passed recording of one scene')
    if Path(recording['video']).name != recording['video']:
        raise ValueError('Video must be beside the recording JSON')
    source = args.recording.parent / recording['video']
    if sha(source) != recording['sha256']:
        raise ValueError('Recording video hash differs')
    duration = float(json.loads(run('ffprobe', '-v', 'error', '-show_format', '-of', 'json', source))['format']['duration'])
    if not 0 <= args.start <= args.poster < args.end <= duration - 1:
        raise ValueError('Check bounds and leave a second before the damaged capture tail')
    if not any(e['what'].startswith('arrived in ') for e in recording['events']):
        raise ValueError('Recording did not reach its exit')
    manifest = json.loads(args.manifest.read_text())
    previous = [c for c in manifest['clips'] if c['room'] == scene]
    stem = f"{scene}-review-{recording['recorded'].replace('-', '')}-{recording['sha256'][:8]}"
    video = f'clips/{stem}.mp4'
    poster = f'clips/{stem}.jpg'
    (args.publish / 'clips').mkdir(parents=True, exist_ok=True)
    (args.publish / 'recordings').mkdir(exist_ok=True)
    # Encode at the checked frame, so this review does not inherit the old
    # quarter's keyframe overlap or replace a neighbour's entrance footage.
    run('ffmpeg', '-y', '-v', 'error', '-ss', args.start, '-i', source,
        '-t', args.end - args.start, '-map', '0:v:0', '-c:v', 'libx264',
        '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p', '-an',
        '-movflags', '+faststart', args.publish / video)
    run('ffmpeg', '-y', '-v', 'error', '-ss', args.poster, '-i', source,
        '-frames:v', '1', '-q:v', '3', args.publish / poster)
    # Keep the source and log on the server, outside git, for the next cut.
    for file, target in ((source, args.publish / 'recordings' / source.name),
                         (args.recording, args.publish / 'recordings' / f'{stem}.json')):
        if file.resolve() != target.resolve():
            shutil.copyfile(file, target)
    review = {k: recording[k] for k in ('recorded', 'sha256', 'gameCommit', 'checkpoint', 'god', 'audio')}
    review['source'] = f'recordings/{source.name}'
    review['log'] = f'recordings/{stem}.json'
    review['logSha256'] = sha(args.recording)
    clip = {'room': scene, 'quarter': previous[0]['quarter'] if previous else 1,
            'visit': 1, 'start': args.start, 'end': args.end, 'roomStart': args.start,
            'posterTime': args.poster, 'file': video, 'poster': poster,
            'review': review, 'note': args.note, 'events': recording['events']}
    manifest['clips'] = replace(manifest['clips'], scene, [clip])
    manifest['noFootage'] = [r for r in manifest['noFootage'] if r != scene]
    args.manifest.write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Replaced {len(previous)} {scene} visits with {video}; other rooms preserved')


if __name__ == '__main__':
    main()
