// quarry (519), written by day/scripts.ts from day/quarry/scene.py: edit the scene, not this file.
// init procedure 0
// To east-path.
door_aot_set(0, 1700, 14620, 1020, 3060, 0, 15, 48, 4, 0, ROOM_517, 28900, 0, 13600, 2048, UNLOCKED, 1);
// To quarry-office.
door_aot_set(1, 5610, 20060, 1530, 1020, 0, 1, 8, 0, 174, ROOM_51A, 4675, 0, 3230, 3072, 60, 193);
// To mine-entrance.
door_aot_set(2, 31280, 9350, 1020, 4250, 0, 15, 48, 4, 0, ROOM_51B, 3570, 0, 11730, 0, UNLOCKED, 1);
aot_set(3, 17000, 17510, 3910, 2890, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 21250, 15300, 2380, 2210, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 4930, 19890, 2890, 1190, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 4420, 3060, 6460, 4420, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 12920, 8330, 10710, 2550, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 22950, 7140, 5950, 1190, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 29920, 7820, 2380, 1700, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(10, 22100, 23460, 10200, 1190, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
enemy(2, 1, 217, 1, 2, 0, 0, 2635, 0, 0, 14980, 0, 2400, 0, 0, 0, 0);  // a cerberus
// Out of the mine once it has taken her gear: its rooms play their own music again, not chase.
if (ck(FG_COMMON, 238, 0) && ck(FG_COMMON, 135, 0)) {
    tbl37_set(4, 27, 8);   // mine-entrance
    tbl37_set(4, 28, 40);   // tunnel
    tbl37_set(4, 30, 40);   // junction
    tbl37_set(4, 31, 40);   // gallery
    tbl37_set(4, 9, 40);   // mine-lift
}
if (ck(FG_COMMON, 238, 0) && ck(FG_COMMON, 135, 1)) {
    tbl37_set(4, 27, 8);   // mine-entrance
    tbl37_set(4, 28, 56);   // tunnel
    tbl37_set(4, 30, 56);   // junction
    tbl37_set(4, 31, 40);   // gallery
    tbl37_set(4, 9, 40);   // mine-lift
}
return;

// main procedure 0
if (ck(FG_COMMON, 232, 1)) {
    set(FG_COMMON, 232, 0);
    message(128, 255, 0);
}
return;
