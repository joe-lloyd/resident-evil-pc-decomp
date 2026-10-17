@echo off
rem Records a test game's window: re1-record.cmd <out.mp4> "RESIDENT EVIL <port>".
rem Started by the scheduled task "RE1 Record <port>" so it runs in the desktop session.
rem Fragmented MP4, one fragment a second: stopping ffmpeg with taskkill /F
rem loses at most the last second. The window is scaled by Windows (1120x840)
rem but the game draws in its top-left 640x480, which is what is kept.
rem gdigrab manages about 26 frames a second; wall-clock timestamps and a
rem constant 30 fps output keep the video in step with real time.
set OUT=%~1
set TITLE=%~2
"C:\Users\joell\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe" -y -hide_banner -use_wallclock_as_timestamps 1 -f gdigrab -framerate 30 -draw_mouse 0 -i title="%TITLE%" -vf crop=640:480:0:0 -fps_mode cfr -r 30 -c:v libx264 -preset veryfast -crf 22 -g 30 -pix_fmt yuv420p -movflags frag_keyframe+empty_moov+default_base_moof -f mp4 "%OUT%" > "%OUT%.log" 2>&1
