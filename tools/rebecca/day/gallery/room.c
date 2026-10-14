// gallery (51F), written by day/scripts.ts from day/gallery/scene.py: edit the scene, not this file.
// init procedure 0
// To junction.
door_aot_set(0, 1700, 6120, 1020, 4760, 0, 0, 0, 4, 0, ROOM_51E, 10200, 0, 11560, 1024, UNLOCKED, 193);
aot_set(1, 14790, 7990, 3740, 2550, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 10710, 6630, 3060, 2380, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 17340, 7820, 6460, 1020, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 238, 1)) {
    set(FG_COMMON, 238, 0);
    message(128, 255, 0);
}
return;
