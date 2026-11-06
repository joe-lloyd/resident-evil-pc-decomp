// back-garden (110), written by day/scripts.ts from day/back-garden/scene.py: edit the scene, not this file.
// init procedure 0
// To kennels.
door_aot_set(0, 15300, 3400, 3400, 1020, 0, 15, 48, 4, 0, ROOM_21F, 17000, 0, 21420, 1024, UNLOCKED, 1);
// To garden-shed.
door_aot_set(1, 24310, 7310, 2040, 2380, 1, 0, 7, 1, 0, ROOM_119, 2975, 0, 4250, 0, UNLOCKED, 193);
// To cellar.
// Shut until she uses the crowbar on it: FG_LOCK 49 once she has.
if (ck(FG_LOCK, 49, 1)) {
    aot_set(2, 20400, 20400, 3230, 1020, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
    aot_set(3, 20400, 20400, 3230, 1020, SCE_USEITEM, 1, 9, 0, 16, 0, 1, 0);   // the crowbar can be used here
} else {
    door_aot_set(2, 20400, 20400, 3230, 1020, 1, 0, 7, 1, 177, ROOM_11D, 12410, 0, 3230, 3072, 43, 193);
}
aot_set(4, 10030, 21590, 3060, 2380, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 4760, 15470, 5270, 3570, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 19040, 19550, 1360, 1870, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 12920, 9520, 7650, 7650, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 20400, 11900, 4250, 4420, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(9, 17850, 21420, 2550, 2550, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
enemy(17, 0, 244, 1, 2, 0, 0, 120, 0, 0, 6140, 0, 22460, 0, 0, 0, 0);  // a zombie
if (ck(FG_LOCK, 49, 0) && ck(FG_COMMON, 146, 1)) {
    enemy(2, 1, 245, 1, 2, 0, 0, 270, 0, 0, 6140, 0, 10560, 1, 0, 0, 0);  // a cerberus
    enemy(2, 1, 246, 1, 2, 0, 0, 3784, 0, 0, 13620, 0, 15320, 2, 0, 0, 0);  // a cerberus
}
return;

// main procedure 0
if (ck(FG_LOCK, 49, 1)) {
    if (ck(FG_ROOM, 12, 1) && testitem(43)) {
        set(FG_ROOM, 12, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 12, 0) && cmpw(0, 4, 1, 0)) {
        set(FG_ROOM, 12, 1);
        set(FG_LOCK, 49, 0);
        if (ck(FG_LOCK, 47, 0)) {
            if (item_ck(43)) {
                remove_item(43);
            }
        }
        door_aot_set(2, 20400, 20400, 3230, 1020, 1, 0, 7, 1, 177, ROOM_11D, 12410, 0, 3230, 3072, 43, 193);
        message(130, 255, 0);
    }
}
return;
