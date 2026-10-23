// switch (41F), written by day/scripts.ts from day/switch/scene.py: edit the scene, not this file.
// init procedure 0
// To generator.
door_aot_set(0, 3060, 1190, 1870, 1530, 0, 1, 11, 3, 0, ROOM_41B, 7140, 0, 6120, 1024, UNLOCKED, 193);
// To line-track.
door_aot_set(1, 6715, 3740, 1615, 1530, 0, 1, 11, 3, 0, ROOM_516, 4250, 0, 11305, 0, UNLOCKED, 193);
aot_set(2, 1190, 3910, 1870, 850, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 2380, 4250, 1530, 1530, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 4420, 5270, 2295, 2040, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 6290, 2550, 2040, 1190, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
// line-on (day/events.ts), FG_COMMON 132 once it has happened.
if (ck(FG_COMMON, 132, 1)) {
    aot_set(6, 1190, 2040, 1870, 1870, SCE_USEITEM, 129, 4, 0, 12, 0, 1, 0);   // the action button here raises FG_ROOM 12
} else {
    aot_set(7, 1190, 2040, 1870, 1870, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 132, 1) && ck(FG_ROOM, 12, 0)) {
    set(FG_ROOM, 12, 1);
    if (ck(FG_COMMON, 131, 0)) {
        set(FG_COMMON, 132, 0);
        aot_set(7, 1190, 2040, 1870, 1870, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
        tbl37_set(3, 31, 40);   // switch
        tbl37_set(4, 22, 40);   // line-track
        bgm_play(2);
        message(135, 255, 0);
    } else {
        message(133, 255, 0);
    }
}
return;
