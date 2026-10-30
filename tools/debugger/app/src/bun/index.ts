// The desktop shell: start the dashboard server in this process and show its
// page in a native window. The game stays its own process (README.md).
import { BrowserWindow } from "electrobun/main";
import { optionsFromEnv, start } from "../../../server.ts";

declare const RE1_DEBUGGER_DIR: string;

const dashboard = await start(optionsFromEnv(process.argv.slice(2), RE1_DEBUGGER_DIR));

new BrowserWindow({
	title: "RE1 debugger",
	url: dashboard.url,
	frame: { width: 1400, height: 900, x: 80, y: 60 },
	// Open behind whatever has focus: it is watched, not typed into.
	activate: false,
});

process.on("exit", () => dashboard.close());
