// workshop (415), written by day/scripts.ts from day/workshop/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-yard.
// Shut from this side until she opens it from the other (FG_LOCK 42).
if (ck(FG_LOCK, 42, 1)) {
    aot_set(0, 3740, 1190, 2550, 1360, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
} else {
    door_aot_set(0, 3740, 1190, 2550, 1360, 0, 1, 11, 3, 0, ROOM_31E, 25840, 0, 20740, 1024, UNLOCKED, 193);
}
if (ck(FG_COMMON, 138, 0) && ck(FG_ITEM, 163, 0)) {  // drive cog (cog)
    item_aot_set(1, 9365, 9110, 1500, 1500, 41, 1, 1, 255, 131, 39, 4, 252, 132, 38, 0, 0, 163, 129, 0, 0);
}
if (ck(FG_ITEM, 188, 0)) {  // clip
    item_aot_set(2, 10150, 6410, 1200, 1200, 11, 15, 0, 255, 254, 41, 0, 0, 98, 27, 0, 0, 188, 129, 0, 0);
}
aot_set(3, 8075, 8050, 3060, 1470, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 2550, 8415, 4080, 1785, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 6290, 3230, 2380, 1870, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 2465, 3910, 1445, 2040, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 3400, 6715, 3060, 1700, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 3230, 2040, 2890, 1870, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
// crane (day/events.ts), FG_COMMON 138 once it has happened.
if (ck(FG_COMMON, 138, 1)) {
    aot_set(9, 9265, 6630, 2210, 1419, SCE_USEITEM, 129, 4, 0, 12, 0, 1, 0);   // the action button here raises FG_ROOM 12
} else {
    aot_set(10, 9265, 6630, 2210, 1419, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 138, 1) && ck(FG_ROOM, 12, 0)) {
    set(FG_ROOM, 12, 1);
    if (ck(FG_COMMON, 137, 0)) {
        set(FG_COMMON, 138, 0);
        if (ck(FG_ITEM, 163, 0)) {
            item_aot_set(1, 9365, 9110, 1500, 1500, 41, 1, 1, 255, 131, 39, 4, 252, 132, 38, 0, 0, 163, 129, 0, 0);
        }
        aot_set(10, 9265, 6630, 2210, 1419, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
        message(138, 255, 0);
    } else {
        message(136, 255, 0);
    }
}
return;
