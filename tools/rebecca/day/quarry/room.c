// quarry (519), written by day/scripts.ts from day/quarry/scene.py: edit the scene, not this file.
// init procedure 0
// To east-path.
door_aot_set(0, 1700, 14620, 1020, 3060, 0, 15, 48, 4, 0, ROOM_517, 28900, 0, 13600, 2048, UNLOCKED, 1);
// To quarry-office.
door_aot_set(1, 5610, 20060, 1530, 1020, 0, 0, 0, 4, 0, ROOM_51A, 4675, 0, 3230, 3072, UNLOCKED, 129);
// To mine-entrance.
door_aot_set(2, 31280, 9350, 1020, 4250, 0, 15, 48, 4, 0, ROOM_51B, 4250, 0, 12580, 0, UNLOCKED, 1);
aot_set(3, 17000, 17510, 3910, 2890, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 21250, 15300, 2380, 2210, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 4930, 19890, 2890, 1190, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 4420, 3060, 6460, 4420, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 12920, 8330, 10710, 2550, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 22950, 7140, 5950, 1190, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 29920, 7820, 2380, 1700, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(10, 22100, 23460, 10200, 1190, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 232, 1)) {
    set(FG_COMMON, 232, 0);
    message(128, 255, 0);
}
return;
