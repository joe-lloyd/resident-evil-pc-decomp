// summit-trail (213), written by day/scripts.ts from day/summit-trail/scene.py: edit the scene, not this file.
// init procedure 0
// To mine-lift.
door_aot_set(0, 25330, 17170, 2210, 2040, 1, 14, 20, 64, 0, ROOM_509, 3315, 0, 3230, 3072, UNLOCKED, 193);
// To weather.
door_aot_set(1, 4930, 9010, 2550, 2040, 0, 1, 12, 7, 0, ROOM_214, 5015, 0, 5610, 1024, UNLOCKED, 193);
// To mast.
door_aot_set(2, 13600, 1700, 6800, 1020, 0, 15, 48, 4, 0, ROOM_215, 14280, 0, 29580, 1024, UNLOCKED, 1);
aot_set(3, 17595, 10710, 4675, 4080, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 11900, 7650, 3060, 2550, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 11560, 5950, 2210, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 13770, 1700, 3910, 4590, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 14960, 11730, 2635, 2040, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 22780, 17170, 2550, 2040, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 7650, 9010, 2380, 2040, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
enemy(5, 0, 222, 1, 2, 0, 0, 1392, 0, 0, 13960, 0, 24500, 0, 0, 0, 0);  // a crow
enemy(5, 0, 223, 1, 2, 0, 0, 2155, 0, 0, 31300, 0, 2400, 1, 0, 0, 0);  // a crow
enemy(5, 0, 224, 1, 2, 0, 0, 811, 0, 0, 2400, 0, 23480, 2, 0, 0, 0);  // a crow
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
