// generator (41B), written by day/scripts.ts from day/generator/scene.py: edit the scene, not this file.
// init procedure 0
// To washout.
door_aot_set(0, 4420, 1700, 1700, 1020, 0, 0, 0, 4, 0, ROOM_41A, 6460, 0, 19040, 1024, UNLOCKED, 193);
// To switch.
door_aot_set(1, 6460, 7140, 1360, 1020, 0, 0, 0, 4, 0, ROOM_41F, 3740, 0, 3570, 3072, UNLOCKED, 193);
aot_set(2, 3995, 3230, 1020, 1190, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 2040, 1700, 2040, 1020, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 4080, 3060, 1360, 1360, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 3910, 6630, 1190, 510, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 3230, 7140, 1020, 1020, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 6800, 2210, 1020, 1700, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 4080, 4420, 850, 1700, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(9, 6460, 6630, 1360, 510, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 224, 1)) {
    set(FG_COMMON, 224, 0);
    message(128, 255, 0);
}
return;
