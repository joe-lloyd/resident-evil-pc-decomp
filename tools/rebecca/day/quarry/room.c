// quarry (519), written by day/scripts.ts from day/quarry/scene.py: edit the scene, not this file.
// init procedure 0
// To east-path.
door_aot_set(0, 1700, 14620, 1020, 3060, 0, 15, 48, 4, 0, ROOM_517, 28900, 0, 13600, 2048, UNLOCKED, 1);
// To quarry-office.
door_aot_set(1, 5100, 20060, 2550, 1530, 0, 1, 8, 0, 174, ROOM_51A, 4675, 0, 3230, 3072, 60, 193);
// To mine-entrance.
door_aot_set(2, 31280, 9350, 1020, 4250, 0, 15, 48, 4, 0, ROOM_51B, 3570, 0, 11730, 0, UNLOCKED, 1);
aot_set(3, 16490, 17510, 4590, 3400, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 21080, 14790, 3060, 2720, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 4420, 19380, 3910, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 3910, 2550, 7480, 5440, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 12410, 8330, 11220, 3060, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 22950, 6630, 6460, 1700, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 29410, 7310, 2890, 2210, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(10, 21590, 22950, 11220, 2210, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
enemy(2, 1, 217, 1, 2, 0, 0, 3702, 0, 0, 15320, 0, 2740, 0, 0, 0, 0);  // a cerberus
// Out of the mine after the gallery scare: its rooms play their own music again, not chase.
if (ck(FG_COMMON, 118, 0) && ck(FG_COMMON, 135, 0)) {
    tbl37_set(4, 27, 8);   // mine-entrance
    tbl37_set(4, 28, 40);   // tunnel
    tbl37_set(4, 30, 40);   // junction
    tbl37_set(4, 31, 40);   // gallery
    tbl37_set(4, 9, 40);   // mine-lift
}
if (ck(FG_COMMON, 118, 0) && ck(FG_COMMON, 135, 1)) {
    tbl37_set(4, 27, 8);   // mine-entrance
    tbl37_set(4, 28, 56);   // tunnel
    tbl37_set(4, 30, 56);   // junction
    tbl37_set(4, 31, 40);   // gallery
    tbl37_set(4, 9, 40);   // mine-lift
}
return;

// main procedure 0
return;
