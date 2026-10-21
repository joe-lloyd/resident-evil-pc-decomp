import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { parseReviewRoute } from './scene-review.ts';

test('ridge review walks both cameras and leaves through its only exit', () => {
  const route = parseReviewRoute(JSON.parse(readFileSync(new URL('../rebecca/day/ridge/review.json', import.meta.url), 'utf8')));
  assert.equal(route.scene, 'ridge');
  assert.deepEqual(route.steps.filter((s) => s.action === 'hold').map((s) => s.camera), [0, 1]);
  assert.deepEqual(route.steps.at(-1), { action: 'exit', x: 12800, z: 5300, to: 'trail' });
  assert.throws(() => parseReviewRoute({ scene: 'ridge', steps: [{ action: 'walk', x: -1, z: 0 }] }), /position/);
  assert.throws(() => parseReviewRoute({ scene: 'ridge', steps: [{ action: 'hold', frames: 30 }] }), /one exit/);
});

test('replacing one scene leaves all other visits untouched', async () => {
  const { execFileSync } = await import('node:child_process');
  const script = new URL('../rebecca/plan/storyboard/replace-scene.py', import.meta.url).pathname;
  execFileSync('python3', ['-c', `import runpy, sys
replace = runpy.run_path(sys.argv[1])['replace']
clips = [{'room': 'ridge', 'file': 'old'}, {'room': 'trail', 'file': 'keep'}, {'room': 'ridge', 'file': 'old2'}]
new = {'room': 'ridge', 'file': 'new'}
result = replace(clips, 'ridge', [new])
assert result == [new, clips[1]]
assert result[1] is clips[1]
assert len(clips) == 3
`, script]);
});
