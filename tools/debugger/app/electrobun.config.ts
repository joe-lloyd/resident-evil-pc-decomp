import type { ElectrobunConfig } from "electrobun";
import path from "node:path";
import { fileURLToPath } from "node:url";

// The bundled main process imports ../server.ts, which reads the page files
// and src/game/Types.h from the repo. Bundling moves the code, so the folder is
// baked in here.
const debuggerDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

export default {
	app: {
		name: "re1-debugger",
		identifier: "re1debugger.local",
		version: "0.0.1",
	},
	build: {
		mainProcess: "bun",
		bun: {
			entrypoint: "src/bun/index.ts",
			define: { RE1_DEBUGGER_DIR: JSON.stringify(debuggerDir) },
		},
		mac: { bundleCEF: false },
		linux: { bundleCEF: false },
		win: { bundleCEF: false },
	},
} satisfies ElectrobunConfig;
