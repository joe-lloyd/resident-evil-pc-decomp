#!/bin/bash
# Probe where day scenes' props land, on jellybingus, without rendering.
#   bash tools/rebecca/props-probe/run.sh <repo> <out-dir> <slug> [<slug> ...]
#   python3 tools/rebecca/props-probe/check.py <out-dir>
# Copies kit.py, reb.py, probe.py and each scene.py to
# C:\Users\joell\Documents\Blender\re1-rebecca\probe-props, runs Blender
# headless on one scene at a time and fetches <out-dir>/<slug>.json.
set -u
repo=$1; out=$2; shift 2
host=jellybingus
win='C:\Users\joell\Documents\Blender\re1-rebecca\probe-props'
fwd='C:/Users/joell/Documents/Blender/re1-rebecca/probe-props'
exe='C:\Program Files\Blender Foundation\Blender 5.1\blender.exe'
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$out"
ssh -o BatchMode=yes $host "powershell -NoProfile -Command \"New-Item -ItemType Directory -Force '$win' | Out-Null\""
scp -q -o BatchMode=yes "$here/probe.py" "$repo/tools/rebecca/blender/kit.py" "$repo/tools/rebecca/blender/reb.py" "$host:$fwd/"
for slug in "$@"; do
  ssh -o BatchMode=yes $host "powershell -NoProfile -Command \"New-Item -ItemType Directory -Force '$win\\$slug' | Out-Null; Remove-Item -Force -ErrorAction SilentlyContinue '$win\\$slug\\probe.json'\""
  scp -q -o BatchMode=yes "$repo/tools/rebecca/day/$slug/scene.py" "$host:$fwd/$slug/"
  ssh -o BatchMode=yes $host "cmd /c \"set RE1_OUT=$win\\$slug\\out&& \"$exe\" -b --factory-startup --python-exit-code 1 --python \"$win\\probe.py\" -- $slug > \"$win\\$slug\\probe.log\" 2>&1\""
  if scp -q -o BatchMode=yes "$host:$fwd/$slug/probe.json" "$out/$slug.json" 2>/dev/null; then
    echo "$slug ok"
  else
    echo "$slug FAILED"; ssh -o BatchMode=yes $host "powershell -NoProfile -Command \"Get-Content -Tail 15 '$win\\$slug\\probe.log'\""
  fi
done
