// Run the dashboard from a terminal; the options are in server.ts.
//   node tools/debugger/run.ts                  game already running, port tunnelled
//   node tools/debugger/run.ts --launch         start the game on the lab machine (lab.ts)
//   node tools/debugger/run.ts --exe <path>     start a local residentevil.exe (Windows)
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { optionsFromEnv, start } from './server.ts';

const dashboard = await start(optionsFromEnv(process.argv.slice(2), path.dirname(fileURLToPath(import.meta.url))));
console.log(`dashboard on ${dashboard.url}`);
const quit = () => {
  dashboard.close();
  process.exit(0);
};
process.on('SIGINT', quit);
process.on('SIGTERM', quit);
