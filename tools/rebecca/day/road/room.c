// road (419), written by day/scripts.ts from day/road/scene.py: edit the scene, not this file.
// init procedure 0
// To yard.
door_aot_set(0, 31280, 8500, 1020, 6800, 0, 15, 48, 4, 0, ROOM_315, 6120, 0, 16600, 0, UNLOCKED, 1);
// To washout.
// Shut until she uses the bolt cutters on it: FG_LOCK 43 once she has.
if (ck(FG_LOCK, 43, 1)) {
    aot_set(1, 13600, 8500, 1530, 7310, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
    aot_set(2, 13600, 8500, 1530, 7310, SCE_USEITEM, 1, 9, 0, 1, 0, 1, 0);   // the bolt cutters can be used here
} else {
    door_aot_set(1, 13600, 8500, 1530, 7310, 0, 16, 48, 4, 171, ROOM_41A, 29580, 0, 11050, 2048, 28, 193);
}
if (ck(FG_ITEM, 250, 0)) {  // the road map (maps/pickups.ts)
    item_aot_set(3, 19880, 16140, 1800, 1800, 80, 1, 0, 255, 44, 81, 0, 0, 144, 66, 0, 0, 250, 129, 0, 0);
}
aot_set(4, 14110, 7310, 2040, 1190, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 14450, 8925, 2210, 2125, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 13600, 5440, 2550, 1870, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 18190, 5440, 2550, 2720, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 16830, 11050, 3740, 3060, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(9, 21250, 5440, 5780, 12920, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
aot_set(10, 14790, 15980, 3060, 2380, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
enemy(5, 0, 204, 1, 2, 0, 0, 3658, 0, 0, 22970, 0, 6650, 0, 0, 0, 0);  // a crow
enemy(5, 0, 205, 1, 2, 0, 0, 419, 0, 0, 22970, 0, 16850, 1, 0, 0, 0);  // a crow
enemy(5, 0, 206, 1, 2, 0, 0, 2847, 0, 0, 31470, 0, 6650, 2, 0, 0, 0);  // a crow
if (ck(FG_ITEM, 250, 0)) {
    set(FG_ROOM, 13, 0);
}
return;

// main procedure 0
if (ck(FG_LOCK, 43, 1)) {
    if (ck(FG_ROOM, 12, 1) && testitem(28)) {
        set(FG_ROOM, 12, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 12, 0) && cmpw(0, 4, 1, 0)) {
        set(FG_ROOM, 12, 1);
        set(FG_LOCK, 43, 0);
        if (ck(FG_LOCK, 41, 0)) {
            if (item_ck(28)) {
                remove_item(28);
            }
        }
        door_aot_set(1, 13600, 8500, 1530, 7310, 0, 16, 48, 4, 171, ROOM_41A, 29580, 0, 11050, 2048, 28, 193);
        message(130, 255, 0);
    }
}
if (ck(FG_ROOM, 13, 0) && ck(FG_ITEM, 250, 1)) {
    set(FG_ROOM, 13, 1);
    message(138, 255, 0);
}
return;
