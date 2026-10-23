// camp-yard (31E), written by day/scripts.ts from day/camp-yard/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-gate.
door_aot_set(0, 14620, 30600, 5100, 1020, 0, 15, 48, 4, 0, ROOM_31D, 17170, 0, 6460, 3072, UNLOCKED, 1);
// To bunkhouse.
door_aot_set(1, 18700, 2414, 2040, 1700, 1, 0, 7, 1, 0, ROOM_31F, 10965, 0, 7820, 1024, UNLOCKED, 193);
// To office.
door_aot_set(2, 3740, 5814, 2550, 2210, 1, 0, 33, 1, 168, ROOM_412, 3400, 0, 4675, 1024, 58, 193);
// To mess.
door_aot_set(3, 3094, 14790, 2210, 2295, 1, 0, 7, 1, 0, ROOM_413, 8453, 0, 9194, 2048, UNLOCKED, 193);
// To depot.
// Shut until she uses the bolt cutters on it: FG_LOCK 41 once she has.
if (ck(FG_LOCK, 41, 1)) {
    aot_set(4, 3910, 24820, 4080, 1530, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
    aot_set(5, 3910, 24820, 4080, 1530, SCE_USEITEM, 1, 9, 0, 1, 0, 1, 0);   // the bolt cutters can be used here
} else {
    door_aot_set(4, 3910, 24820, 4080, 1530, 0, 16, 48, 4, 169, ROOM_414, 11050, 0, 4250, 3072, 28, 193);
}
// To workshop.
door_aot_set(6, 24310, 22066, 2550, 1700, 0, 1, 11, 3, 170, ROOM_415, 4760, 0, 3995, 3072, 59, 193);
// To sawmill.
door_aot_set(7, 29750, 9690, 2040, 6120, 1, 0, 7, 1, 0, ROOM_416, 4080, 0, 12750, 0, UNLOCKED, 193);
aot_set(8, 17510, 24480, 5780, 3570, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(9, 12410, 11390, 5780, 5440, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(10, 17170, 2890, 1530, 2040, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(11, 22610, 9010, 4760, 3740, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(12, 3230, 17085, 2720, 6205, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(13, 3910, 11050, 3060, 3060, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
aot_set(14, 17170, 19550, 2380, 4930, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
aot_set(15, 9010, 3910, 8160, 3400, SCE_MESSAGE, 129, 138, 0, 255, 0, 0, 0);
aot_set(16, 26860, 19210, 4250, 3910, SCE_MESSAGE, 129, 139, 0, 255, 0, 0, 0);
aot_set(17, 3230, 23290, 5440, 1530, SCE_MESSAGE, 129, 140, 0, 255, 0, 0, 0);
enemy(17, 0, 192, 1, 2, 0, 0, 1986, 0, 0, 16340, 0, 17020, 0, 0, 0, 0);  // a zombie
enemy(17, 0, 193, 1, 2, 0, 0, 1889, 0, 0, 12600, 0, 9880, 1, 0, 0, 0);  // a zombie
enemy(17, 0, 194, 1, 2, 0, 0, 2653, 0, 0, 9200, 0, 2400, 2, 0, 0, 0);  // a zombie
return;

// main procedure 0
if (ck(FG_LOCK, 41, 1)) {
    if (ck(FG_ROOM, 12, 1) && testitem(28)) {
        set(FG_ROOM, 12, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 12, 0) && cmpw(0, 4, 1, 0)) {
        set(FG_ROOM, 12, 1);
        set(FG_LOCK, 41, 0);
        if (ck(FG_LOCK, 43, 0)) {
            if (item_ck(28)) {
                remove_item(28);
            }
        }
        door_aot_set(4, 3910, 24820, 4080, 1530, 0, 16, 48, 4, 169, ROOM_414, 11050, 0, 4250, 3072, 28, 193);
        message(130, 255, 0);
    }
}
return;
