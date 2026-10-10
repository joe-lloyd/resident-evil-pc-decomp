// Start and stop test-mode games on the Windows machine that runs them, over
// SSH. The game needs a desktop session for its window, so it is launched
// through a scheduled task with an interactive logon, one task per port.
//
// RE1_LAB_HOST      ssh host of the Windows machine (default: jellybingus)
// RE1_LAB_GAME_DIR  folder with residentevil.exe, config.ini and USA\ (default: D:\Games\RE1-decomp)
// RE1_LAB_USER      Windows user that owns the desktop session (default: joell)
// RE1_LAB_REPO_DIR  clone of this fork on that machine, with a `fork` remote (default: C:\Users\joell\Tools\re1-decomp)
import { spawn, execFileSync, type ChildProcess } from 'node:child_process';
import { GameLink } from './link.ts';

const host = process.env.RE1_LAB_HOST ?? 'jellybingus';
const gameDir = process.env.RE1_LAB_GAME_DIR ?? 'D:\\Games\\RE1-decomp';
const user = process.env.RE1_LAB_USER ?? 'joell';
const repoDir = process.env.RE1_LAB_REPO_DIR ?? 'C:\\Users\\joell\\Tools\\re1-decomp';

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

/**
 * Build `branch` of the fork on the game machine and copy the exe into the
 * game folder. Stops any test games first, since a running exe cannot be
 * replaced. Returns the compiler errors, empty when the build succeeded.
 */
export function buildAndDeploy(branch: string): string[] {
  const out = powershell(`
    Get-Process residentevil -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '${gameDir}\\*' } | Stop-Process -Force
    Set-Location '${repoDir}'
    git fetch -q fork
    git checkout -q -B ${branch} fork/${branch}
    $env:RE1_TOOLSET = 'v142'
    $env:RE1_SDK = '10.0.19041.0'
    cmd /c build.bat 2>&1 | Out-File -Encoding utf8 build.log
    $errors = Select-String -Path build.log -Pattern ': error|fatal error|error LNK' | ForEach-Object { $_.Line }
    if (-not $errors -and -not (Test-Path 'bin\\Release\\residentevil.exe')) { $errors = 'no exe was built' }
    if ($errors) { $errors } else {
      # A game that is still exiting holds the exe: retry, then prove the copy.
      $built = (Get-FileHash 'bin\\Release\\residentevil.exe').Hash
      for ($i = 0; $i -lt 20; $i++) {
        Get-Process residentevil -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '${gameDir}\\*' } | Stop-Process -Force
        Copy-Item 'bin\\Release\\residentevil.exe' '${gameDir}' -Force -ErrorAction SilentlyContinue
        if ((Get-FileHash '${gameDir}\\residentevil.exe').Hash -eq $built) { 'DEPLOYED'; break }
        Start-Sleep 1
      }
    }
  `);
  const lines = out.split(/\r?\n/).filter(Boolean);
  return lines.includes('DEPLOYED') ? [] : lines;
}

/** Replace the game folder's `name` overlay (e.g. REB) with a local build of it. */
export function deployOverlay(localOverlayDir: string, name = 'REB'): void {
  powershell(`if (Test-Path '${gameDir}\\${name}') { Remove-Item -Recurse -Force '${gameDir}\\${name}' }`);
  execFileSync('scp', ['-q', '-r', '-o', 'BatchMode=yes', localOverlayDir, `${host}:${gameDir.replace(/\\/g, '/')}/${name}`]);
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
