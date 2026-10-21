// Restore or save Rebecca's rendered build inputs in the private Forgejo repo.
//
//   node tools/rebecca/assets.ts pull
//   node tools/rebecca/assets.ts push [scene ...]
//
// Node 24 and git, with access to https://git.home.arpa/joe/re1-rebecca-assets.
// RE1_REBECCA_ASSETS_DIR overrides ~/.cache/re1-rebecca-assets.
// RE1_REBECCA_ASSETS_URL overrides the clone URL, including for a local mirror.
// pull overwrites local assets. After copying renders back from jellybingus,
// run push before pulling newer assets. Missing local files are kept remotely.
import { execFileSync } from 'node:child_process';
import { copyFileSync, existsSync, mkdirSync, realpathSync, statSync } from 'node:fs';
import { homedir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const cache = path.resolve(process.env.RE1_REBECCA_ASSETS_DIR ?? path.join(homedir(), '.cache/re1-rebecca-assets'));
const url = process.env.RE1_REBECCA_ASSETS_URL ?? 'https://git.home.arpa/joe/re1-rebecca-assets.git';
const command = process.argv[2];
const scenes = process.argv.slice(3);
if ((command !== 'pull' && command !== 'push') || (command === 'pull' && scenes.length) || scenes.some((s) => !/^[a-z0-9-]+$/.test(s))) {
  throw new Error('usage: node tools/rebecca/assets.ts pull | push [scene ...]');
}

function git(dir: string, ...args: string[]): string {
  return execFileSync('git', ['-C', dir, ...args], {
    encoding: 'utf8', stdio: ['ignore', 'pipe', 'inherit'], maxBuffer: 16 << 20,
  }).trimEnd();
}

// Only preserve render inputs. Music WAVs and Python caches are reproducible.
function isAsset(file: string): boolean {
  return /^tools\/rebecca\/(day\/[^/]+\/renders\/[^/]+\.png|items\/(icons\/[^/]+\.png|models\/[^/]+\.(json|png))|saveroom\/renders\/[^/]+\.png|card\/rebecca-id-lettering\.png)$/.test(file);
}

function files(output: string): string[] {
  return output.split('\0').filter((file) => file.length > 0);
}

function copy(from: string, to: string, list: string[]): void {
  for (const file of list) {
    const target = path.join(to, file);
    mkdirSync(path.dirname(target), { recursive: true });
    copyFileSync(path.join(from, file), target);
  }
}

if (!existsSync(cache)) {
  mkdirSync(path.dirname(cache), { recursive: true });
  execFileSync('git', ['clone', '--', url, cache], { stdio: 'inherit' });
} else {
  if (realpathSync(git(cache, 'rev-parse', '--show-toplevel')) !== realpathSync(cache) || realpathSync(cache) === realpathSync(root)) {
    throw new Error(`Use a separate assets clone at ${cache}`);
  }
  if (git(cache, 'status', '--porcelain')) throw new Error(`Commit or discard changes in ${cache} first`);
  git(cache, 'pull', '--rebase');
}

if (command === 'pull') {
  const list = files(git(cache, 'ls-files', '-z', '--', 'tools/rebecca'));
  for (const file of list) {
    if (!isAsset(file)) throw new Error(`Unexpected asset path: ${file}`);
  }
  if (!list.length) throw new Error(`No Rebecca assets in ${cache}`);
  copy(cache, root, list);
  process.stdout.write(`Restored ${list.length} assets from ${cache}\n`);
} else {
  const list: string[] = [];
  for (const file of files(git(root, 'ls-files', '--others', '--ignored', '--exclude-standard', '-z', '--', 'tools/rebecca'))) {
    if (isAsset(file)) {
      // Concurrent scene work must not overwrite another worktree's renders.
      if (!scenes.length || scenes.some((s) => file.startsWith(`tools/rebecca/day/${s}/renders/`))) list.push(file);
    }
    else if (!/(^|\/)__pycache__\/|^tools\/rebecca\/music\/renders\/|\.log$/.test(file)) {
      throw new Error(`Unrecognized ignored file: ${file}. Add its asset path to assets.ts before pushing.`);
    }
  }
  // This lettering is already tracked in the game repo. Mirror it as well.
  const lettering = 'tools/rebecca/card/rebecca-id-lettering.png';
  if (!scenes.length && existsSync(path.join(root, lettering)) && !list.includes(lettering)) list.push(lettering);
  if (!list.length) throw new Error('No Rebecca assets to save');
  // Finish a previously interrupted push before copying the next batch.
  git(cache, 'push');
  const commit = git(root, 'rev-parse', 'HEAD');
  let changed = 0;
  function save(batch: string[]): void {
    copy(root, cache, batch);
    git(cache, 'add', '--', ...batch);
    const changes = files(git(cache, 'diff', '--cached', '--name-only', '-z'));
    if (!changes.length) return;
    git(cache, 'commit', '-m', `Update Rebecca assets for game commit ${commit}`);
    git(cache, 'push');
    changed += changes.length;
  }
  // The home Forgejo proxy rejects a full render set in one HTTP request.
  let batch: string[] = [];
  let bytes = 0;
  for (const file of list) {
    const size = statSync(path.join(root, file)).size;
    if (batch.length && bytes + size > 32 * 1024 * 1024) {
      save(batch);
      batch = [];
      bytes = 0;
    }
    batch.push(file);
    bytes += size;
  }
  save(batch);
  process.stdout.write(changed
    ? `Saved ${changed} changed assets for game commit ${commit}\n`
    : 'No asset changes; no commit made.\n');
}
