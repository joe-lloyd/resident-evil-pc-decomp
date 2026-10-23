// washout (41A), written by day/scripts.ts from day/washout/scene.py: edit the scene, not this file.
// init procedure 0
// To road.
// Shut from this side until she opens it from the other (FG_LOCK 43).
if (ck(FG_LOCK, 43, 1)) {
    aot_set(0, 31280, 7650, 1020, 6800, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
} else {
    door_aot_set(0, 31280, 7650, 1020, 6800, 0, 16, 48, 4, 0, ROOM_419, 16320, 0, 11900, 0, UNLOCKED, 1);
}
// To tower-foot.
door_aot_set(1, 1700, 7820, 1020, 5100, 0, 15, 48, 4, 0, ROOM_41C, 29410, 0, 11900, 2048, UNLOCKED, 1);
// To generator.
door_aot_set(2, 4930, 19890, 2550, 1870, 0, 1, 11, 3, 0, ROOM_41B, 5270, 0, 3400, 3072, UNLOCKED, 193);
aot_set(3, 17680, 9180, 4250, 2040, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 12410, 9180, 5270, 2040, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 14450, 4590, 5100, 2720, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 21930, 7990, 6460, 6120, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 7140, 18530, 4250, 1360, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 2550, 15130, 3740, 2550, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(9, 1700, 12920, 2550, 2210, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
enemy(10, 1, 207, 1, 1, 0, 0, 2275, 0, 0, 17020, 0, 5800, 0, 0, 0, 0);  // a adder
enemy(10, 1, 208, 1, 1, 0, 0, 616, 0, 0, 22800, 0, 20420, 1, 0, 0, 0);  // a adder
return;

// main procedure 0
return;
