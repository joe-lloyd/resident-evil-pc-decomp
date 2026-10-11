// ROOM40C0, Plant 42's room, in Rebecca's scenario (Chapter 4). With the roots
// in ROOM4080 dead (FG_ENEMY 96 set), the plant lies dead and the Helmet Key
// can be taken; otherwise it is alive, as when Chris comes in the first time.
// Once she has the key, the way out is a chapter break to the lab (ROOM5110).
// Chris's events and Rebecca's NPC are left out.
// init procedure 0
if (ck(FG_ITEM, 88, 1)) {
    door_aot_set(0, 1100, 8000, 1500, 3900, 11, 0, 0, 1, 0, ROOM_511, 3500, 0, 9000, 1024, UNLOCKED, 129);
} else {
    door_aot_set(0, 1100, 8000, 1500, 3900, 11, 0, 0, 1, 0, ROOM_S08, 26000, 0, 4000, 2048, UNLOCKED, 129);
}
aot_set(1, 1000, 12400, 1500, 3000, SCE_MESSAGE, 129, 140, 0, 255, 0, 0, 0);
eml_rot(0, 250, 0, 28, 248);
tbl37_set(3, 12, 8);
if (ck(FG_ENEMY, 96, 0)) {
    enemy(8 /* Plant 42 */, 4, 255, 1, 2, 0, 0, 1024, 0, 0, 10800, 200, 10800, 0, 0, 0, 0);
    tbl37_set(3, 12, 255);
    item_aot_set(3, 9800, 17700, 2200, 1800, 54 /* Helmet Key */, 3, 0, 255, 54, 41, 52, 254, 90, 70, 0, 4, 88, 129, 0, 0);
} else {
    enemy(8 /* Plant 42 */, 64, 96, 1, 2, 0, 0, 3572, 0, 0, 10800, -7000, 10800, 0, 0, 0, 0);
    enemy(8 /* Plant 42 */, 65, 255, 1, 2, 0, 0, 0, 0, 0, 11200, -7000, 10800, 1, 0, 0, 0);
    enemy(8 /* Plant 42 */, 65, 255, 1, 2, 0, 0, 1024, 0, 0, 10800, -7000, 11200, 2, 0, 0, 0);
    enemy(8 /* Plant 42 */, 65, 255, 1, 2, 0, 0, 2048, 0, 0, 11200, -7000, 11200, 3, 0, 0, 0);
    enemy(8 /* Plant 42 */, 69, 255, 1, 2, 0, 0, 500, 0, 0, 10400, -7000, 10800, 4, 0, 0, 0);
    enemy(8 /* Plant 42 */, 65, 255, 1, 2, 0, 0, 1500, 0, 0, 10800, -7000, 10400, 5, 0, 0, 0);
}
set(FG_SCENARIO, 68, 0);
return;

// main procedure 0
// She took the Helmet Key: the door leads on to the lab.
if (ck(FG_ITEM, 88, 1) && ck(FG_COMMON, 223, 1)) {
    set(FG_COMMON, 223, 0);
    door_aot_set(0, 1100, 8000, 1500, 3900, 11, 0, 0, 1, 0, ROOM_511, 3500, 0, 9000, 1024, UNLOCKED, 129);
}
return;
