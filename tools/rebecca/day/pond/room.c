// pond (417), written by day/scripts.ts from day/pond/scene.py: edit the scene, not this file.
// init procedure 0
// To sawmill.
door_aot_set(0, 1190, 16320, 1700, 2210, 1, 0, 7, 1, 0, ROOM_416, 29580, 0, 16490, 2048, UNLOCKED, 193);
// To flume.
door_aot_set(1, 5780, 3400, 2040, 1020, 0, 15, 48, 4, 0, ROOM_418, 10880, 0, 18530, 1024, UNLOCKED, 1);
aot_set(2, 12750, 15470, 5100, 2380, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 21590, 15470, 5100, 2380, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 3740, 5780, 2720, 4250, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 1700, 14790, 1870, 1530, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 5270, 4420, 3060, 1360, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
enemy(17, 0, 203, 1, 2, 0, 0, 1890, 0, 0, 27220, 0, 22800, 0, 0, 0, 0);  // a zombie
// mill-race (day/events.ts), FG_COMMON 137 once it has happened.
if (ck(FG_COMMON, 137, 1)) {
    aot_set(7, 8330, 4590, 3060, 2380, SCE_USEITEM, 1, 9, 0, 3, 0, 1, 0);   // the winch crank can be used here
    aot_set(8, 8330, 4590, 3060, 2380, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
} else {
    aot_set(8, 8330, 4590, 3060, 2380, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 137, 1)) {
    if (ck(FG_ROOM, 12, 1) && testitem(30)) {
        set(FG_ROOM, 12, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 12, 0) && cmpw(0, 4, 1, 0)) {
        sys_multi(7);
        set(FG_ROOM, 12, 1);
        if (item_ck(30)) {
            remove_item(30);
        }
        set(FG_COMMON, 137, 0);
        aot_set(8, 8330, 4590, 3060, 2380, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
        tbl37_set(2, 30, 24);   // camp-yard
        tbl37_set(3, 22, 24);   // sawmill
        tbl37_set(3, 23, 56);   // pond
        tbl37_set(3, 24, 24);   // flume
        bgm_play(1);
        message(136, 255, 0);
    }
}
return;
