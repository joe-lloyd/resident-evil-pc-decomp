// mine-lift (509), written by day/scripts.ts from day/mine-lift/scene.py: edit the scene, not this file.
// init procedure 0
// To junction.
door_aot_set(0, 1870, 3570, 2890, 765, 0, 1, 8, 0, 0, ROOM_51E, 12240, 0, 6120, 3072, UNLOCKED, 193);
// To summit-trail.
if (ck(FG_COMMON, 136, 1)) {
    aot_set(1, 1870, 1700, 2890, 765, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
} else {
    door_aot_set(1, 1870, 1700, 2890, 765, 0, 14, 20, 64, 0, ROOM_213, 26180, 0, 16490, 1024, UNLOCKED, 193);
}
aot_set(2, 2380, 2499, 1530, 1037, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 1700, 2499, 680, 1037, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
// lift-up (day/events.ts), FG_COMMON 136 once it has happened.
if (ck(FG_COMMON, 136, 1)) {
    aot_set(4, 3910, 2499, 1020, 1037, SCE_USEITEM, 129, 4, 0, 12, 0, 1, 0);   // the action button here raises FG_ROOM 12
} else {
    aot_set(5, 3910, 2499, 1020, 1037, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 239, 1)) {
    set(FG_COMMON, 239, 0);
    message(128, 255, 0);
}
if (ck(FG_COMMON, 136, 1) && ck(FG_ROOM, 12, 0)) {
    set(FG_ROOM, 12, 1);
    if (ck(FG_COMMON, 131, 0)) {
        set(FG_COMMON, 136, 0);
        door_aot_set(1, 1870, 1700, 2890, 765, 0, 14, 20, 64, 0, ROOM_213, 26180, 0, 16490, 1024, UNLOCKED, 193);
        aot_set(5, 3910, 2499, 1020, 1037, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
        message(134, 255, 0);
    } else {
        message(132, 255, 0);
    }
}
return;
