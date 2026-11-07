// camp-yard (31E), written by day/scripts.ts from day/camp-yard/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-gate.
door_aot_set(0, 14620, 30600, 5100, 1020, 0, 15, 48, 4, 0, ROOM_31D, 17170, 0, 6460, 3072, UNLOCKED, 1);
// To bunkhouse.
door_aot_set(1, 18700, 2414, 2040, 1700, 1, 0, 7, 1, 0, ROOM_31F, 10965, 0, 7820, 1024, UNLOCKED, 193);
// To office.
door_aot_set(2, 3740, 5814, 2550, 2210, 1, 0, 33, 1, 168, ROOM_412, 3400, 0, 4675, 1024, 58, 193);
// To mess.
door_aot_set(3, 3094, 14790, 2210, 2295, 1, 0, 7, 1, 0, ROOM_413, 8500, 0, 9265, 2048, UNLOCKED, 193);
// To depot.
// Shut until she uses the bolt cutters on it: FG_LOCK 41 once she has.
if (ck(FG_LOCK, 41, 1)) {
    aot_set(4, 3910, 24820, 4080, 1530, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
    aot_set(5, 3910, 24820, 4080, 1530, SCE_USEITEM, 1, 9, 0, 1, 0, 1, 0);   // the bolt cutters can be used here
} else {
    door_aot_set(4, 3910, 24820, 4080, 1530, 0, 16, 48, 4, 169, ROOM_414, 11050, 0, 4250, 3072, 28, 193);
}
// To workshop.
// Shut until she uses the workshop key or the bolt cutters on it: FG_LOCK 42 once she has.
if (ck(FG_LOCK, 42, 1)) {
    aot_set(6, 24310, 22066, 2550, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
    aot_set(7, 24310, 22066, 2550, 1700, SCE_USEITEM, 1, 9, 0, 32, 0, 1, 0);   // the workshop key can be used here
    aot_set(8, 24310, 22066, 2550, 1700, SCE_USEITEM, 1, 9, 0, 1, 0, 1, 0);   // and the bolt cutters
} else {
    door_aot_set(6, 24310, 22066, 2550, 1700, 0, 1, 11, 3, 170, ROOM_415, 4760, 0, 3995, 3072, 59, 193);
}
// To sawmill.
door_aot_set(9, 29750, 9690, 2040, 6120, 1, 0, 7, 1, 0, ROOM_416, 4080, 0, 12750, 0, UNLOCKED, 193);
aot_set(10, 17510, 24480, 5780, 3570, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(11, 12410, 11390, 5780, 5440, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(12, 17170, 2890, 1530, 2040, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
aot_set(13, 22610, 9010, 4760, 3740, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
aot_set(14, 3230, 17085, 2720, 6205, SCE_MESSAGE, 129, 138, 0, 255, 0, 0, 0);
aot_set(15, 17170, 19550, 2380, 4930, SCE_MESSAGE, 129, 139, 0, 255, 0, 0, 0);
aot_set(16, 9010, 3910, 8160, 3400, SCE_MESSAGE, 129, 140, 0, 255, 0, 0, 0);
aot_set(17, 26860, 19210, 4250, 3910, SCE_MESSAGE, 129, 141, 0, 255, 0, 0, 0);
aot_set(18, 3230, 23290, 5440, 1530, SCE_MESSAGE, 129, 142, 0, 255, 0, 0, 0);
if (ck(FG_COMMON, 143, 1)) {
    enemy(17, 0, 192, 1, 2, 0, 0, 1299, 0, 0, 30280, 0, 30620, 0, 0, 0, 0);  // a zombie
    enemy(17, 0, 193, 1, 2, 0, 0, 1986, 0, 0, 16340, 0, 17020, 1, 0, 0, 0);  // a zombie
    enemy(17, 0, 194, 1, 2, 0, 0, 2947, 0, 0, 30280, 0, 4780, 2, 0, 0, 0);  // a zombie
}
if (ck(FG_COMMON, 158, 0) && ck(FG_COMMON, 143, 1)) {
    enemy(17, 0, 195, 1, 2, 0, 0, 1889, 0, 0, 12600, 0, 9880, 3, 0, 0, 0);  // a zombie
    enemy(17, 0, 196, 1, 2, 0, 0, 2653, 0, 0, 9200, 0, 2400, 4, 0, 0, 0);  // a zombie
}
// ring-bell (day/events.ts), FG_COMMON 143 once it has happened.
if (ck(FG_COMMON, 143, 1)) {
    aot_set(19, 4165, 12240, 2550, 2380, SCE_USEITEM, 129, 4, 0, 12, 0, 1, 0);   // the action button here raises FG_ROOM 12
} else {
    aot_set(20, 4165, 12240, 2550, 2380, SCE_MESSAGE, 129, 144, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 143, 1) && ck(FG_ROOM, 12, 0)) {
    set(FG_ROOM, 12, 1);
    set(FG_COMMON, 143, 0);
    eml_state(0, 0, 3, 0, 0);
    set(FG_ENEMY, 192, 0);
    eml_state(0, 1, 3, 0, 0);
    set(FG_ENEMY, 193, 0);
    eml_state(0, 2, 3, 0, 0);
    set(FG_ENEMY, 194, 0);
    eml_state(0, 3, 3, 0, 0);
    set(FG_ENEMY, 195, 0);
    eml_state(0, 4, 3, 0, 0);
    set(FG_ENEMY, 196, 0);
    aot_set(20, 4165, 12240, 2550, 2380, SCE_MESSAGE, 129, 144, 0, 255, 0, 0, 0);
    message(145, 255, 0);
}
if (ck(FG_LOCK, 41, 1)) {
    if (ck(FG_ROOM, 13, 1) && testitem(28)) {
        set(FG_ROOM, 13, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 13, 0) && cmpw(0, 4, 1, 0)) {
        set(FG_ROOM, 13, 1);
        set(FG_LOCK, 41, 0);
        if (ck(FG_LOCK, 42, 0) && ck(FG_LOCK, 43, 0)) {
            if (item_ck(28)) {
                remove_item(28);
            }
        }
        door_aot_set(4, 3910, 24820, 4080, 1530, 0, 16, 48, 4, 169, ROOM_414, 11050, 0, 4250, 3072, 28, 193);
        message(130, 255, 0);
    }
}
if (ck(FG_LOCK, 42, 1)) {
    if (ck(FG_ROOM, 14, 1) && testitem(59)) {
        set(FG_ROOM, 14, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 14, 0) && cmpw(0, 4, 1, 0)) {
        set(FG_ROOM, 14, 1);
        set(FG_LOCK, 42, 0);
        if (item_ck(59)) {
            remove_item(59);
        }
        if (ck(FG_LOCK, 41, 0) && ck(FG_LOCK, 43, 0)) {
            if (item_ck(28)) {
                remove_item(28);
            }
        }
        door_aot_set(6, 24310, 22066, 2550, 1700, 0, 1, 11, 3, 170, ROOM_415, 4760, 0, 3995, 3072, 59, 193);
        message(132, 255, 0);
    }
}
if (ck(FG_LOCK, 42, 1)) {
    if (ck(FG_ROOM, 15, 1) && testitem(28)) {
        set(FG_ROOM, 15, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 15, 0) && cmpw(0, 4, 1, 0)) {
        set(FG_ROOM, 15, 1);
        set(FG_LOCK, 42, 0);
        set(FG_COMMON, 158, 0);
        if (ck(FG_LOCK, 41, 0) && ck(FG_LOCK, 43, 0)) {
            if (item_ck(28)) {
                remove_item(28);
            }
        }
        if (item_ck(59)) {
            remove_item(59);
        }
        door_aot_set(6, 24310, 22066, 2550, 1700, 0, 1, 11, 3, 170, ROOM_415, 4760, 0, 3995, 3072, 59, 193);
        message(133, 255, 0);
    }
}
return;
