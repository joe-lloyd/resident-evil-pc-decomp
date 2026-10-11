// The ranger's lookout (ROOM3140), inside: a log cabin on the mountain,
// morning. Nobody is home. The radio on the desk picks up S.T.A.R.S. chatter;
// the ranger's logbook tells of the "dog attacks"; a First Aid Spray stands
// on the table and the ranger's key lies on the desk.
//
// FG_COMMON 201: she has been in before. FG_ITEM 241: the spray is taken,
// 242: the key is taken (bit set = still there).
// item_aot_set operands after the model index: 255, the model's position
// (X, Y, Z as little-endian 16-bit pairs), two rotation bytes, the item flag,
// then 129 (taken with the action key), 0, 0.
// Room messages are 0x80 + index: 128 is message 0.
// init procedure 0
door_aot_set(0, 5400, 7600, 1200, 900, 0, 0, 0, 4, 0, ROOM_312, 3500, 0, 14400, 1024, UNLOCKED, 129);
// On the table: the First Aid Spray, model at (6300, -760, 6100).
if (ck(FG_ITEM, 241, 0)) {
    item_aot_set(1, 5600, 5500, 1400, 1300, 65 /* F-Aid Spray */, 1, 0, 255, 156, 24, 8, 253, 212, 23, 0, 0, 241, 129, 0, 0);
}
// On the desk: the ranger's key, model at (5300, -780, 3450).
if (ck(FG_ITEM, 242, 0)) {
    item_aot_set(2, 4900, 3000, 900, 1200, 61 /* Small Key */, 1, 1, 255, 180, 20, 244, 252, 122, 13, 0, 0, 242, 129, 0, 0);
}
aot_set(3, 3600, 3000, 1100, 1100, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 4700, 3000, 300, 1100, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 7900, 3800, 1100, 2300, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 3000, 5400, 1000, 1100, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 5900, 3000, 1400, 600, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 201, 1)) {
    set(FG_COMMON, 201, 0);
    message(128, 0, 0);
}
return;
