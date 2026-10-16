// summit-trail (213), written by day/scripts.ts from day/summit-trail/scene.py: edit the scene, not this file.
// init procedure 0
// To mine-lift.
door_aot_set(0, 25330, 17680, 1700, 1020, 1, 14, 20, 64, 0, ROOM_509, 3315, 0, 3230, 3072, UNLOCKED, 193);
// To weather.
door_aot_set(1, 5440, 9520, 1530, 1020, 0, 1, 12, 7, 0, ROOM_214, 5015, 0, 5610, 1024, UNLOCKED, 193);
// To mast.
door_aot_set(2, 13600, 1700, 6800, 1020, 0, 15, 48, 4, 0, ROOM_215, 14280, 0, 29580, 1024, UNLOCKED, 1);
aot_set(3, 18020, 11220, 3740, 3060, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 11900, 7650, 2550, 2040, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 12070, 6460, 1700, 1190, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 14280, 1700, 3400, 4080, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 15470, 12240, 1700, 1020, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 23290, 17680, 2040, 1020, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 8160, 9520, 1360, 1020, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
enemy(5, 0, 222, 1, 2, 0, 0, 1392, 0, 0, 13960, 0, 24500, 0, 0, 0, 0);  // a crow
enemy(5, 0, 223, 1, 2, 0, 0, 2155, 0, 0, 31300, 0, 2400, 1, 0, 0, 0);  // a crow
enemy(5, 0, 224, 1, 2, 0, 0, 811, 0, 0, 2400, 0, 23480, 2, 0, 0, 0);  // a crow
// Out of the mine once it has taken her gear: its rooms play their own music again, not chase.
if (ck(FG_COMMON, 238, 0) && ck(FG_COMMON, 135, 0)) {
    tbl37_set(4, 27, 8);   // mine-entrance
    tbl37_set(4, 28, 8);   // tunnel
    tbl37_set(4, 30, 8);   // junction
    tbl37_set(4, 31, 8);   // gallery
    tbl37_set(4, 9, 8);   // mine-lift
}
if (ck(FG_COMMON, 238, 0) && ck(FG_COMMON, 135, 1)) {
    tbl37_set(4, 27, 8);   // mine-entrance
    tbl37_set(4, 28, 24);   // tunnel
    tbl37_set(4, 30, 24);   // junction
    tbl37_set(4, 31, 8);   // gallery
    tbl37_set(4, 9, 8);   // mine-lift
}
return;

// main procedure 0
if (ck(FG_COMMON, 240, 1)) {
    set(FG_COMMON, 240, 0);
    message(128, 255, 0);
}
return;
