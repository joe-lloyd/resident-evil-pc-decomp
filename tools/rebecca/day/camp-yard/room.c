// camp-yard (31E), written by day/scripts.ts from day/camp-yard/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-gate.
door_aot_set(0, 14620, 30600, 5100, 1020, 0, 15, 48, 4, 0, ROOM_31D, 17170, 0, 6460, 3072, UNLOCKED, 1);
// To bunkhouse.
door_aot_set(1, 18700, 2924, 1530, 1190, 1, 0, 7, 1, 0, ROOM_31F, 10965, 0, 7820, 1024, UNLOCKED, 193);
// To office.
door_aot_set(2, 4250, 6324, 1530, 1190, 1, 0, 33, 1, 168, ROOM_412, 3400, 0, 4675, 1024, 58, 193);
// To mess.
door_aot_set(3, 3604, 15300, 1190, 1530, 1, 0, 7, 1, 0, ROOM_413, 8500, 0, 9265, 2048, UNLOCKED, 193);
// To depot.
door_aot_set(4, 4420, 24820, 3060, 1020, 0, 16, 48, 4, 169, ROOM_414, 11050, 0, 4250, 3072, 28, 193);
// To workshop.
door_aot_set(5, 24820, 22066, 2040, 1190, 0, 1, 11, 3, 170, ROOM_415, 4760, 0, 3995, 3072, 59, 193);
// To sawmill.
door_aot_set(6, 30260, 10200, 1020, 5100, 1, 0, 7, 1, 0, ROOM_416, 4080, 0, 12750, 0, UNLOCKED, 193);
aot_set(7, 11560, 28900, 3400, 1700, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(8, 17000, 24480, 4760, 3060, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(9, 12920, 11900, 4760, 4420, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(10, 17680, 2890, 1020, 1530, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(11, 23120, 9520, 3740, 2720, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(12, 4420, 17680, 3740, 4080, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(13, 4420, 11560, 2040, 2040, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(14, 17680, 20060, 1360, 4080, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
aot_set(15, 9520, 4420, 7140, 2380, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
aot_set(16, 26860, 19720, 3740, 3400, SCE_MESSAGE, 129, 138, 0, 255, 0, 0, 0);
enemy(17, 0, 192, 1, 2, 0, 0, 2975, 0, 0, 30280, 0, 2400, 0, 0, 0, 0);  // a zombie
enemy(17, 0, 193, 1, 2, 0, 0, 1986, 0, 0, 16340, 0, 17020, 1, 0, 0, 0);  // a zombie
enemy(17, 0, 194, 1, 2, 0, 0, 1889, 0, 0, 12600, 0, 9880, 2, 0, 0, 0);  // a zombie
return;

// main procedure 0
if (ck(FG_COMMON, 213, 1)) {
    set(FG_COMMON, 213, 0);
    message(128, 255, 0);
}
return;
