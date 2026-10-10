// Start and stop test-mode games on the Windows machine that runs them, over
// SSH. The game needs a desktop session for its window, so it is launched
// through a scheduled task with an interactive logon, one task per port.
//
// RE1_LAB_HOST      ssh host of the Windows machine (default: jellybingus)
// RE1_LAB_GAME_DIR  folder with residentevil.exe, config.ini and USA\ (default: D:\Games\RE1-decomp)
// RE1_LAB_USER      Windows user that owns the desktop session (default: joell)
import { spawn, execFileSync, type ChildProcess } from 'node:child_process';
import { GameLink } from './link.ts';

const host = process.env.RE1_LAB_HOST ?? 'jellybingus';
const gameDir = process.env.RE1_LAB_GAME_DIR ?? 'D:\\Games\\RE1-decomp';
const user = process.env.RE1_LAB_USER ?? 'joell';

function powershell(script: string): string {
  const encoded = Buffer.from(`$ProgressPreference = 'SilentlyContinue'\n${script}`, 'utf16le').toString('base64');
  return execFileSync('ssh', ['-o', 'BatchMode=yes', host, `powershell -NoProfile -NonInteractive -EncodedCommand ${encoded}`], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore'],
  });
}

function taskName(port: number): string {
  return `RE1 Test ${port}`;
}

/** Launch a game in test mode on `port`, extra arguments appended (e.g. a mode flag). */
export function launch(port: number, extraArgs = ''): void {
  powershell(`
    $p = New-ScheduledTaskPrincipal -UserId '${user}' -LogonType Interactive -RunLevel Limited
    $a = New-ScheduledTaskAction -Execute '${gameDir}\\residentevil.exe' -Argument '--test-port ${port} ${extraArgs}' -WorkingDirectory '${gameDir}'
    Register-ScheduledTask -TaskName '${taskName(port)}' -Action $a -Principal $p -Force | Out-Null
    Start-ScheduledTask -TaskName '${taskName(port)}'
  `);
}

/** Stop the game started on `port`, if it is still running. */
export function stop(port: number): void {
  powershell(`
    Get-CimInstance Win32_Process -Filter "Name='residentevil.exe'" |
      Where-Object { $_.CommandLine -match '--test-port ${port}\\b' } |
      ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
  `);
}

/** Forward the game's localhost port to this machine. */
export function tunnel(port: number): ChildProcess {
  return spawn('ssh', ['-o', 'BatchMode=yes', '-o', 'ExitOnForwardFailure=yes', '-N', '-L', `${port}:127.0.0.1:${port}`, host], {
    stdio: 'ignore',
  });
}

/** Copy a file from the game machine, e.g. a screenshot taken with shot(). */
export function fetch(remotePath: string, localPath: string): void {
  execFileSync('scp', ['-q', '-o', 'BatchMode=yes', `${host}:${remotePath.replace(/\\/g, '/')}`, localPath]);
}

export interface Session {
  link: GameLink;
  port: number;
  end: () => void;
}

/** Launch, tunnel and connect. Task Scheduler takes up to about 40 s to start the game. */
export async function open(port: number, extraArgs = ''): Promise<Session> {
  stop(port);
  launch(port, extraArgs);
  const ssh = tunnel(port);
  try {
    const link = await GameLink.connect(port, '127.0.0.1', 180_000);
    return {
      link,
      port,
      end: () => {
        link.close();
        ssh.kill();
        stop(port);
      },
    };
  } catch (err) {
    ssh.kill();
    stop(port);
    throw err;
  }
}
