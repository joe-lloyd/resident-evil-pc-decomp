// switch (41F), written by day/scripts.ts from day/switch/scene.py: edit the scene, not this file.
// init procedure 0
// To generator.
door_aot_set(0, 3060, 1700, 1870, 1020, 0, 1, 11, 3, 0, ROOM_41B, 7140, 0, 6120, 1024, UNLOCKED, 193);
// To line-track.
door_aot_set(1, 6715, 3740, 1615, 1530, 0, 1, 11, 3, 0, ROOM_516, 4250, 0, 11305, 0, UNLOCKED, 193);
if (ck(FG_ITEM, 165, 0)) {  // fuses (fuses)
    item_aot_set(2, 3585, 5578, 1500, 1734, 39, 1, 0, 255, 239, 16, 141, 248, 162, 25, 0, 0, 165, 129, 0, 0);
}
aot_set(3, 3060, 2720, 850, 3434, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 1190, 6154, 1870, 1156, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 3060, 6154, 680, 1156, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 4420, 5270, 2295, 2040, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 6290, 2550, 2040, 1190, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
// line-on (day/events.ts): 5 switches thrown in the order 5, 4, 3, 2, 1; FG_COMMON 132 once they are.
if (ck(FG_COMMON, 132, 1)) {
    aot_set(8, 1190, 1224, 1870, 1394, SCE_USEITEM, 129, 4, 0, 12, 0, 1, 0);   // switch 1: FG_ROOM 12
    aot_set(9, 1190, 2618, 1870, 884, SCE_USEITEM, 129, 4, 0, 13, 0, 1, 0);   // switch 2: FG_ROOM 13
    aot_set(10, 1190, 3502, 1870, 884, SCE_USEITEM, 129, 4, 0, 14, 0, 1, 0);   // switch 3: FG_ROOM 14
    aot_set(11, 1190, 4386, 1870, 884, SCE_USEITEM, 129, 4, 0, 15, 0, 1, 0);   // switch 4: FG_ROOM 15
    aot_set(12, 1190, 5270, 1870, 884, SCE_USEITEM, 129, 4, 0, 16, 0, 1, 0);   // switch 5: FG_ROOM 16
} else {
    aot_set(8, 1190, 1224, 1870, 1394, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
    aot_set(9, 1190, 2618, 1870, 884, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
    aot_set(10, 1190, 3502, 1870, 884, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
    aot_set(11, 1190, 4386, 1870, 884, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
    aot_set(12, 1190, 5270, 1870, 884, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 132, 1) && ck(FG_ROOM, 16, 0)) {   // switch 5, thrown 1st
    set(FG_ROOM, 16, 1);
    if (ck(FG_COMMON, 131, 0)) {
        if (ck(FG_ROOM, 17, 1)) {
            set(FG_ROOM, 17, 0);
            message(137, 255, 0);
        } else {
            if (ck(FG_ROOM, 17, 0)) {
                message(137, 255, 0);
            } else {
                set(FG_ROOM, 17, 1);
                set(FG_ROOM, 18, 1);
                set(FG_ROOM, 19, 1);
                set(FG_ROOM, 20, 1);
                set(FG_ROOM, 21, 1);
                sys_multi(11, 12, 0);   // the shock: 12 health, never the last
                message(138, 255, 0);
            }
        }
    } else {
        message(134, 255, 0);
    }
}
if (ck(FG_COMMON, 132, 1) && ck(FG_ROOM, 15, 0)) {   // switch 4, thrown 2nd
    set(FG_ROOM, 15, 1);
    if (ck(FG_COMMON, 131, 0)) {
        if (ck(FG_ROOM, 17, 0) && ck(FG_ROOM, 18, 1)) {
            set(FG_ROOM, 18, 0);
            message(137, 255, 0);
        } else {
            if (ck(FG_ROOM, 18, 0)) {
                message(137, 255, 0);
            } else {
                set(FG_ROOM, 17, 1);
                set(FG_ROOM, 18, 1);
                set(FG_ROOM, 19, 1);
                set(FG_ROOM, 20, 1);
                set(FG_ROOM, 21, 1);
                sys_multi(11, 12, 0);   // the shock: 12 health, never the last
                message(138, 255, 0);
            }
        }
    } else {
        message(134, 255, 0);
    }
}
if (ck(FG_COMMON, 132, 1) && ck(FG_ROOM, 14, 0)) {   // switch 3, thrown 3rd
    set(FG_ROOM, 14, 1);
    if (ck(FG_COMMON, 131, 0)) {
        if (ck(FG_ROOM, 18, 0) && ck(FG_ROOM, 19, 1)) {
            set(FG_ROOM, 19, 0);
            message(137, 255, 0);
        } else {
            if (ck(FG_ROOM, 19, 0)) {
                message(137, 255, 0);
            } else {
                set(FG_ROOM, 17, 1);
                set(FG_ROOM, 18, 1);
                set(FG_ROOM, 19, 1);
                set(FG_ROOM, 20, 1);
                set(FG_ROOM, 21, 1);
                sys_multi(11, 12, 0);   // the shock: 12 health, never the last
                message(138, 255, 0);
            }
        }
    } else {
        message(134, 255, 0);
    }
}
if (ck(FG_COMMON, 132, 1) && ck(FG_ROOM, 13, 0)) {   // switch 2, thrown 4th
    set(FG_ROOM, 13, 1);
    if (ck(FG_COMMON, 131, 0)) {
        if (ck(FG_ROOM, 19, 0) && ck(FG_ROOM, 20, 1)) {
            set(FG_ROOM, 20, 0);
            message(137, 255, 0);
        } else {
            if (ck(FG_ROOM, 20, 0)) {
                message(137, 255, 0);
            } else {
                set(FG_ROOM, 17, 1);
                set(FG_ROOM, 18, 1);
                set(FG_ROOM, 19, 1);
                set(FG_ROOM, 20, 1);
                set(FG_ROOM, 21, 1);
                sys_multi(11, 12, 0);   // the shock: 12 health, never the last
                message(138, 255, 0);
            }
        }
    } else {
        message(134, 255, 0);
    }
}
if (ck(FG_COMMON, 132, 1) && ck(FG_ROOM, 12, 0)) {   // switch 1, thrown 5th
    set(FG_ROOM, 12, 1);
    if (ck(FG_COMMON, 131, 0)) {
        if (ck(FG_ROOM, 20, 0) && ck(FG_ROOM, 21, 1)) {
            set(FG_COMMON, 132, 0);
            aot_set(8, 1190, 1224, 1870, 1394, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
            aot_set(9, 1190, 2618, 1870, 884, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
            aot_set(10, 1190, 3502, 1870, 884, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
            aot_set(11, 1190, 4386, 1870, 884, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
            aot_set(12, 1190, 5270, 1870, 884, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
            tbl37_set(3, 31, 40);   // switch
            tbl37_set(4, 22, 40);   // line-track
            bgm_play(2);
            message(136, 255, 0);
        } else {
            if (ck(FG_ROOM, 21, 0)) {
                message(137, 255, 0);
            } else {
                set(FG_ROOM, 17, 1);
                set(FG_ROOM, 18, 1);
                set(FG_ROOM, 19, 1);
                set(FG_ROOM, 20, 1);
                set(FG_ROOM, 21, 1);
                sys_multi(11, 12, 0);   // the shock: 12 health, never the last
                message(138, 255, 0);
            }
        }
    } else {
        message(134, 255, 0);
    }
}
return;
