// kennels (21F), written by day/scripts.ts from day/kennels/scene.py: edit the scene, not this file.
// init procedure 0
// To estate-wall.
door_aot_set(0, 15810, 3400, 2380, 1020, 0, 16, 48, 4, 0, ROOM_21E, 17000, 0, 29750, 1024, UNLOCKED, 1);
// To back-garden.
door_aot_set(1, 15300, 22780, 3400, 1020, 0, 15, 48, 4, 0, ROOM_110, 17000, 0, 5780, 3072, UNLOCKED, 1);
// To cellar.
// Shut until she uses the cellar key on it: FG_LOCK 50 once she has.
if (ck(FG_LOCK, 50, 1)) {
    if (ck(FG_COMMON, 146, 0)) {
        aot_set(2, 19380, 20910, 2720, 1615, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
        aot_set(3, 19380, 20910, 2720, 1615, SCE_USEITEM, 1, 9, 0, 26, 0, 1, 0);   // the cellar key can be used here
    } else {
        aot_set(2, 19380, 20910, 2720, 1615, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
    }
} else {
    door_aot_set(2, 19380, 20910, 2720, 1615, 0, 0, 0, 4, 178, ROOM_11D, 7820, 0, 3400, 3072, 53, 193);
}
if (ck(FG_ITEM, 204, 0)) {  // greenHerb
    item_aot_set(4, 3690, 12870, 1200, 1200, 68, 1, 0, 255, 194, 16, 0, 0, 158, 52, 0, 0, 204, 129, 1, 0);
}
aot_set(5, 11050, 14450, 1530, 3910, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 4590, 13940, 6035, 4420, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 8500, 5780, 2550, 3910, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 11050, 5950, 1020, 12240, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(9, 20230, 7820, 2380, 3570, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
aot_set(10, 18700, 17510, 4080, 2380, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
aot_set(11, 12580, 8840, 4080, 5610, SCE_MESSAGE, 129, 138, 0, 255, 0, 0, 0);
if (ck(FG_COMMON, 146, 1)) {
    enemy(2, 1, 241, 1, 2, 0, 0, 4012, 0, 0, 4100, 0, 4100, 0, 0, 0, 0);  // a cerberus
    enemy(2, 1, 242, 1, 2, 0, 0, 3786, 0, 0, 6480, 0, 16000, 1, 0, 0, 0);  // a cerberus
    enemy(2, 1, 243, 1, 2, 0, 0, 2148, 0, 0, 27900, 0, 4100, 2, 0, 0, 0);  // a cerberus
}
// pen-pack (day/events.ts), FG_COMMON 146 once it has happened.
if (ck(FG_COMMON, 146, 1)) {
    aot_set(12, 10880, 18700, 2380, 2550, SCE_USEITEM, 1, 9, 0, 9, 0, 1, 0);   // the dog meat can be used here
    aot_set(13, 10880, 18700, 2380, 2550, SCE_MESSAGE, 129, 139, 0, 255, 0, 0, 0);
} else {
    aot_set(13, 10880, 18700, 2380, 2550, SCE_MESSAGE, 129, 140, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 146, 1)) {
    if (ck(FG_ROOM, 12, 1) && testitem(36)) {
        set(FG_ROOM, 12, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 12, 0) && cmpw(0, 4, 1, 0)) {
        set(FG_ROOM, 12, 1);
        if (item_ck(36)) {
            remove_item(36);
        }
        set(FG_COMMON, 146, 0);
        eml_state(0, 0, 3, 0, 0);
        set(FG_ENEMY, 241, 0);
        eml_state(0, 1, 3, 0, 0);
        set(FG_ENEMY, 242, 0);
        eml_state(0, 2, 3, 0, 0);
        set(FG_ENEMY, 243, 0);
        aot_set(13, 10880, 18700, 2380, 2550, SCE_MESSAGE, 129, 140, 0, 255, 0, 0, 0);
        message(141, 255, 0);
    }
}
if (ck(FG_COMMON, 146, 1) && ck(FG_ENEMY, 241, 0) && ck(FG_ENEMY, 242, 0) && ck(FG_ENEMY, 243, 0)) {
    set(FG_COMMON, 146, 0);
    aot_set(13, 10880, 18700, 2380, 2550, SCE_MESSAGE, 129, 140, 0, 255, 0, 0, 0);
}
if (ck(FG_LOCK, 50, 1)) {
    if (ck(FG_ROOM, 13, 1) && testitem(53)) {
        set(FG_ROOM, 13, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 13, 0) && cmpw(0, 4, 1, 0)) {
        set(FG_ROOM, 13, 1);
        set(FG_LOCK, 50, 0);
        if (item_ck(53)) {
            remove_item(53);
        }
        door_aot_set(2, 19380, 20910, 2720, 1615, 0, 0, 0, 4, 178, ROOM_11D, 7820, 0, 3400, 3072, 53, 193);
        message(131, 255, 0);
    }
}
return;
