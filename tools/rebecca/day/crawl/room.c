// crawl (11F), written by day/scripts.ts from day/crawl/scene.py: edit the scene, not this file.
// init procedure 0
// To cellar.
door_aot_set(0, 1700, 7480, 1020, 2720, 1, 0, 7, 1, 0, ROOM_11D, 3570, 0, 9180, 0, UNLOCKED, 193);
// To save.
door_aot_set(1, 11560, 2040, 1360, 2890, 0, 11, 27, 64, 0, ROOM_100, 5200, 0, 5600, 443, UNLOCKED, 193);
aot_set(2, 11220, 4080, 2380, 2380, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 8840, 7480, 1700, 1190, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 5100, 7480, 3400, 2720, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 12580, 7480, 1020, 2720, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 110, 1)) {
    set(FG_COMMON, 110, 0);
    message(128, 255, 0);
}
return;
