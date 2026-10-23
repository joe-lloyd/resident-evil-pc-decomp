// line-track (516), written by day/scripts.ts from day/line-track/scene.py: edit the scene, not this file.
// init procedure 0
// To switch.
door_aot_set(0, 1190, 10370, 1530, 2380, 0, 1, 11, 3, 0, ROOM_41F, 5780, 0, 4505, 2048, UNLOCKED, 193);
// To platform.
if (ck(FG_COMMON, 133, 1)) {
    aot_set(1, 31280, 10200, 1020, 3400, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
} else {
    door_aot_set(1, 31280, 10200, 1020, 3400, 0, 16, 48, 4, 0, ROOM_318, 3400, 0, 11900, 0, UNLOCKED, 1);
}
aot_set(2, 16830, 13600, 4420, 1700, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 13260, 9690, 2210, 2040, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 15300, 11730, 2040, 1870, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 9010, 14110, 4080, 2380, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 1700, 8330, 1870, 2040, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
enemy(10, 1, 213, 1, 1, 0, 0, 1738, 0, 0, 16680, 0, 17700, 0, 0, 0, 0);  // a adder
enemy(10, 1, 214, 1, 1, 0, 0, 3758, 0, 0, 18720, 0, 5800, 1, 0, 0, 0);  // a adder
// line-gate (day/events.ts), FG_COMMON 133 once it has happened.
if (ck(FG_COMMON, 133, 1)) {
    aot_set(7, 29410, 13600, 2890, 2210, SCE_USEITEM, 129, 4, 0, 12, 0, 1, 0);   // the action button here raises FG_ROOM 12
} else {
    aot_set(8, 29410, 13600, 2890, 2210, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 133, 1) && ck(FG_ROOM, 12, 0)) {
    set(FG_ROOM, 12, 1);
    if (ck(FG_COMMON, 132, 0)) {
        set(FG_COMMON, 133, 0);
        door_aot_set(1, 31280, 10200, 1020, 3400, 0, 16, 48, 4, 0, ROOM_318, 3400, 0, 11900, 0, UNLOCKED, 1);
        aot_set(8, 29410, 13600, 2890, 2210, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
        message(137, 255, 0);
    } else {
        message(135, 255, 0);
    }
}
return;
