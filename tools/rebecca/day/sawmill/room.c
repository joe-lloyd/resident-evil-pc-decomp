// sawmill (416), written by day/scripts.ts from day/sawmill/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-yard.
door_aot_set(0, 1700, 10200, 1190, 5100, 1, 0, 7, 1, 0, ROOM_31E, 28730, 0, 12750, 2048, UNLOCKED, 193);
// To pond.
door_aot_set(1, 31280, 14960, 1020, 3060, 1, 0, 7, 1, 0, ROOM_417, 4420, 0, 17170, 0, UNLOCKED, 193);
aot_set(2, 12920, 11900, 4420, 1360, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 13940, 12070, 6800, 1190, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 11900, 11220, 1700, 1020, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 19720, 8840, 3400, 1700, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 22100, 15470, 1700, 850, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 10880, 19720, 2040, 1020, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 28900, 14620, 2720, 1020, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(9, 24735, 15640, 2465, 1020, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
aot_set(10, 30260, 17340, 1020, 1020, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
enemy(17, 0, 201, 1, 2, 0, 0, 3579, 0, 0, 18380, 0, 5120, 0, 0, 0, 0);  // a zombie
enemy(17, 0, 202, 1, 2, 0, 0, 1702, 0, 0, 16000, 0, 19740, 1, 0, 0, 0);  // a zombie
if (ck(FG_ITEM, 188, 0)) {  // clip
    item_aot_set(11, 17480, 4220, 1800, 1800, 11, 15, 0, 255, 204, 71, 0, 0, 0, 20, 0, 0, 188, 129, 0, 0);
}
// crane (day/events.ts), FG_COMMON 138 once it has happened.
if (ck(FG_COMMON, 138, 1)) {
    aot_set(12, 7650, 8670, 3060, 1360, SCE_USEITEM, 129, 4, 0, 12, 0, 1, 0);   // the action button here raises FG_ROOM 12
} else {
    aot_set(13, 7650, 8670, 3060, 1360, SCE_MESSAGE, 129, 139, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 219, 1)) {
    set(FG_COMMON, 219, 0);
    message(128, 255, 0);
}
if (ck(FG_COMMON, 138, 1) && ck(FG_ROOM, 12, 0)) {
    set(FG_ROOM, 12, 1);
    if (ck(FG_COMMON, 137, 0)) {
        set(FG_COMMON, 138, 0);
        aot_set(13, 7650, 8670, 3060, 1360, SCE_MESSAGE, 129, 139, 0, 255, 0, 0, 0);
        message(140, 255, 0);
    } else {
        message(138, 255, 0);
    }
}
return;
