"""Check published clips, posters, range responses and the research links."""
import argparse
import concurrent.futures
from datetime import datetime, timezone
import json
from pathlib import Path
import urllib.request

manifest = json.loads(Path(__file__).with_name('clips.json').read_text())
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('url', nargs='?', default='https://home.arpa/research/rebecca-storyboard/')
args = parser.parse_args()
base = args.url.rstrip('/') + '/'


def head(path):
    request = urllib.request.Request(base + path, method='HEAD')
    with urllib.request.urlopen(request, timeout=20) as response:
        expected = 'video/mp4' if path.endswith('.mp4') else 'image/jpeg'
        assert response.status == 200, (path, response.status)
        assert response.headers.get_content_type() == expected, (path, dict(response.headers))
        assert int(response.headers['Content-Length']) > 0


print(f'Checked at {datetime.now(timezone.utc).isoformat()}')
paths = [path for clip in manifest['clips'] for path in [clip['file'], clip['poster']]]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    list(pool.map(head, paths))
print(f'HTTP 200 and content types: {len(paths)} assets')
samples = [next(c for c in manifest['clips'] if c['quarter'] == quarter and c['room'] not in ['ridge', 'workshop', 'switch', 'booth']) for quarter in range(1, 5)]
samples.append(next(c for c in manifest['clips'] if c['file'] == 'clips/booth-q4-v03.mp4'))
for clip in samples:
    with urllib.request.urlopen(base + clip['file'], timeout=20) as response:
        assert response.status == 200 and response.headers.get_content_type() == 'video/mp4'
        assert len(response.read(1024)) == 1024
    request = urllib.request.Request(base + clip['file'], headers={'Range': 'bytes=0-1023'})
    with urllib.request.urlopen(request, timeout=20) as response:
        assert response.status == 206, (clip['file'], response.status)
        assert response.headers.get_content_type() == 'video/mp4'
        assert response.headers['Content-Range'].startswith('bytes 0-1023/')
        assert len(response.read()) == 1024
        print(f"Range 206: {clip['file']} {response.headers['Content-Range']}")
with urllib.request.urlopen(base, timeout=20) as response:
    html = response.read().decode()
    assert 'src="/research/rebecca-day/nav.js"' in html
    assert html.count('<video controls preload="none"') == len(manifest['clips'])
    print('Published page: all players and shared navigation tag')
with urllib.request.urlopen('https://home.arpa/research/rebecca-day/', timeout=20) as response:
    assert 'rebecca-storyboard/' in response.read().decode()
    print('Research index card remains linked')
