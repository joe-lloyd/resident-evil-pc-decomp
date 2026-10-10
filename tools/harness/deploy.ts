// Build a branch of the fork on the game machine and install the exe.
//   node tools/harness/deploy.ts [branch]
import { execFileSync } from 'node:child_process';
import { buildAndDeploy } from './lab.ts';

const branch = process.argv[2] ?? execFileSync('git', ['branch', '--show-current'], { encoding: 'utf8' }).trim();
const errors = buildAndDeploy(branch);
if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}
console.log(`built and deployed ${branch}`);
