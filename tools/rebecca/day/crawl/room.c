// crawl (11F), written by day/scripts.ts from day/crawl/scene.py: edit the scene, not this file.
// init procedure 0
// To cellar.
door_aot_set(0, 1190, 6970, 2040, 3740, 1, 0, 7, 1, 0, ROOM_11D, 3570, 0, 9180, 0, UNLOCKED, 193);
// To save.
door_aot_set(1, 11050, 1530, 1870, 3400, 0, 11, 27, 64, 0, ROOM_100, 5200, 0, 5600, 443, UNLOCKED, 193);
aot_set(2, 11220, 4080, 2890, 2890, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 8670, 6970, 2380, 1700, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 4590, 7480, 4080, 3230, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 12070, 6970, 2040, 3740, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
// cut-leave-gear (day/cutscenes.ts): its people, and what starts it. FG_COMMON 129 once it has run.
if (ck(FG_COMMON, 129, 1)) {
    aot_set(6, 10880, 6460, 2720, 1020, SCE_EVENT, 1, 9, 0, 0, 0, 0, 0);
}
return;

// main procedure 0
return;

// event procedure 0
// cut-leave-gear (day/cutscenes.ts)
scd {
    set(FG_COMMON, 129, 0);
    aot_reset(6, SCE_NONE, 129, 0, 0, 0);
    set(FG_STATUS, 15, 0);
    set(FG_6, 23, 1);
    return;
}
cutnext(2);
dir_set(0, 0, 1024, 0, 12240, 0, 6800);  // her
message(133, 0, 0);  // her
wait_voice();
message(134, 0, 0);  // her
wait_voice();
timer_setup(2, 0, 1, 7, 0);
sleep(120);
timer_setup(2, 0, 0, 7, 0);
scd {
    sys_multi(0);
    return;
}
scd {
    if (item_ck(1)) {
        remove_item(1);
    }
    if (item_ck(1)) {
        remove_item(1);
    }
    if (item_ck(1)) {
        remove_item(1);
    }
    if (item_ck(1)) {
        remove_item(1);
    }
    if (item_ck(1)) {
        remove_item(1);
    }
    if (item_ck(1)) {
        remove_item(1);
    }
    return;
}
scd {
    if (item_ck(3)) {
        remove_item(3);
    }
    if (item_ck(3)) {
        remove_item(3);
    }
    if (item_ck(3)) {
        remove_item(3);
    }
    if (item_ck(3)) {
        remove_item(3);
    }
    if (item_ck(3)) {
        remove_item(3);
    }
    if (item_ck(3)) {
        remove_item(3);
    }
    return;
}
scd {
    if (item_ck(4)) {
        remove_item(4);
    }
    if (item_ck(4)) {
        remove_item(4);
    }
    if (item_ck(4)) {
        remove_item(4);
    }
    if (item_ck(4)) {
        remove_item(4);
    }
    if (item_ck(4)) {
        remove_item(4);
    }
    if (item_ck(4)) {
        remove_item(4);
    }
    return;
}
scd {
    if (item_ck(5)) {
        remove_item(5);
    }
    if (item_ck(5)) {
        remove_item(5);
    }
    if (item_ck(5)) {
        remove_item(5);
    }
    if (item_ck(5)) {
        remove_item(5);
    }
    if (item_ck(5)) {
        remove_item(5);
    }
    if (item_ck(5)) {
        remove_item(5);
    }
    return;
}
scd {
    if (item_ck(6)) {
        remove_item(6);
    }
    if (item_ck(6)) {
        remove_item(6);
    }
    if (item_ck(6)) {
        remove_item(6);
    }
    if (item_ck(6)) {
        remove_item(6);
    }
    if (item_ck(6)) {
        remove_item(6);
    }
    if (item_ck(6)) {
        remove_item(6);
    }
    return;
}
scd {
    if (item_ck(7)) {
        remove_item(7);
    }
    if (item_ck(7)) {
        remove_item(7);
    }
    if (item_ck(7)) {
        remove_item(7);
    }
    if (item_ck(7)) {
        remove_item(7);
    }
    if (item_ck(7)) {
        remove_item(7);
    }
    if (item_ck(7)) {
        remove_item(7);
    }
    return;
}
scd {
    if (item_ck(8)) {
        remove_item(8);
    }
    if (item_ck(8)) {
        remove_item(8);
    }
    if (item_ck(8)) {
        remove_item(8);
    }
    if (item_ck(8)) {
        remove_item(8);
    }
    if (item_ck(8)) {
        remove_item(8);
    }
    if (item_ck(8)) {
        remove_item(8);
    }
    return;
}
scd {
    if (item_ck(9)) {
        remove_item(9);
    }
    if (item_ck(9)) {
        remove_item(9);
    }
    if (item_ck(9)) {
        remove_item(9);
    }
    if (item_ck(9)) {
        remove_item(9);
    }
    if (item_ck(9)) {
        remove_item(9);
    }
    if (item_ck(9)) {
        remove_item(9);
    }
    return;
}
scd {
    if (item_ck(10)) {
        remove_item(10);
    }
    if (item_ck(10)) {
        remove_item(10);
    }
    if (item_ck(10)) {
        remove_item(10);
    }
    if (item_ck(10)) {
        remove_item(10);
    }
    if (item_ck(10)) {
        remove_item(10);
    }
    if (item_ck(10)) {
        remove_item(10);
    }
    return;
}
scd {
    if (item_ck(11)) {
        remove_item(11);
    }
    if (item_ck(11)) {
        remove_item(11);
    }
    if (item_ck(11)) {
        remove_item(11);
    }
    if (item_ck(11)) {
        remove_item(11);
    }
    if (item_ck(11)) {
        remove_item(11);
    }
    if (item_ck(11)) {
        remove_item(11);
    }
    return;
}
scd {
    if (item_ck(12)) {
        remove_item(12);
    }
    if (item_ck(12)) {
        remove_item(12);
    }
    if (item_ck(12)) {
        remove_item(12);
    }
    if (item_ck(12)) {
        remove_item(12);
    }
    if (item_ck(12)) {
        remove_item(12);
    }
    if (item_ck(12)) {
        remove_item(12);
    }
    return;
}
scd {
    if (item_ck(13)) {
        remove_item(13);
    }
    if (item_ck(13)) {
        remove_item(13);
    }
    if (item_ck(13)) {
        remove_item(13);
    }
    if (item_ck(13)) {
        remove_item(13);
    }
    if (item_ck(13)) {
        remove_item(13);
    }
    if (item_ck(13)) {
        remove_item(13);
    }
    return;
}
scd {
    if (item_ck(14)) {
        remove_item(14);
    }
    if (item_ck(14)) {
        remove_item(14);
    }
    if (item_ck(14)) {
        remove_item(14);
    }
    if (item_ck(14)) {
        remove_item(14);
    }
    if (item_ck(14)) {
        remove_item(14);
    }
    if (item_ck(14)) {
        remove_item(14);
    }
    return;
}
scd {
    if (item_ck(15)) {
        remove_item(15);
    }
    if (item_ck(15)) {
        remove_item(15);
    }
    if (item_ck(15)) {
        remove_item(15);
    }
    if (item_ck(15)) {
        remove_item(15);
    }
    if (item_ck(15)) {
        remove_item(15);
    }
    if (item_ck(15)) {
        remove_item(15);
    }
    return;
}
scd {
    if (item_ck(16)) {
        remove_item(16);
    }
    if (item_ck(16)) {
        remove_item(16);
    }
    if (item_ck(16)) {
        remove_item(16);
    }
    if (item_ck(16)) {
        remove_item(16);
    }
    if (item_ck(16)) {
        remove_item(16);
    }
    if (item_ck(16)) {
        remove_item(16);
    }
    return;
}
scd {
    if (item_ck(17)) {
        remove_item(17);
    }
    if (item_ck(17)) {
        remove_item(17);
    }
    if (item_ck(17)) {
        remove_item(17);
    }
    if (item_ck(17)) {
        remove_item(17);
    }
    if (item_ck(17)) {
        remove_item(17);
    }
    if (item_ck(17)) {
        remove_item(17);
    }
    return;
}
scd {
    if (item_ck(18)) {
        remove_item(18);
    }
    if (item_ck(18)) {
        remove_item(18);
    }
    if (item_ck(18)) {
        remove_item(18);
    }
    if (item_ck(18)) {
        remove_item(18);
    }
    if (item_ck(18)) {
        remove_item(18);
    }
    if (item_ck(18)) {
        remove_item(18);
    }
    return;
}
scd {
    if (item_ck(65)) {
        remove_item(65);
    }
    if (item_ck(65)) {
        remove_item(65);
    }
    if (item_ck(65)) {
        remove_item(65);
    }
    if (item_ck(65)) {
        remove_item(65);
    }
    if (item_ck(65)) {
        remove_item(65);
    }
    if (item_ck(65)) {
        remove_item(65);
    }
    return;
}
scd {
    if (item_ck(67)) {
        remove_item(67);
    }
    if (item_ck(67)) {
        remove_item(67);
    }
    if (item_ck(67)) {
        remove_item(67);
    }
    if (item_ck(67)) {
        remove_item(67);
    }
    if (item_ck(67)) {
        remove_item(67);
    }
    if (item_ck(67)) {
        remove_item(67);
    }
    return;
}
scd {
    if (item_ck(68)) {
        remove_item(68);
    }
    if (item_ck(68)) {
        remove_item(68);
    }
    if (item_ck(68)) {
        remove_item(68);
    }
    if (item_ck(68)) {
        remove_item(68);
    }
    if (item_ck(68)) {
        remove_item(68);
    }
    if (item_ck(68)) {
        remove_item(68);
    }
    return;
}
scd {
    if (item_ck(69)) {
        remove_item(69);
    }
    if (item_ck(69)) {
        remove_item(69);
    }
    if (item_ck(69)) {
        remove_item(69);
    }
    if (item_ck(69)) {
        remove_item(69);
    }
    if (item_ck(69)) {
        remove_item(69);
    }
    if (item_ck(69)) {
        remove_item(69);
    }
    return;
}
scd {
    if (item_ck(70)) {
        remove_item(70);
    }
    if (item_ck(70)) {
        remove_item(70);
    }
    if (item_ck(70)) {
        remove_item(70);
    }
    if (item_ck(70)) {
        remove_item(70);
    }
    if (item_ck(70)) {
        remove_item(70);
    }
    if (item_ck(70)) {
        remove_item(70);
    }
    return;
}
scd {
    if (item_ck(71)) {
        remove_item(71);
    }
    if (item_ck(71)) {
        remove_item(71);
    }
    if (item_ck(71)) {
        remove_item(71);
    }
    if (item_ck(71)) {
        remove_item(71);
    }
    if (item_ck(71)) {
        remove_item(71);
    }
    if (item_ck(71)) {
        remove_item(71);
    }
    return;
}
scd {
    if (item_ck(72)) {
        remove_item(72);
    }
    if (item_ck(72)) {
        remove_item(72);
    }
    if (item_ck(72)) {
        remove_item(72);
    }
    if (item_ck(72)) {
        remove_item(72);
    }
    if (item_ck(72)) {
        remove_item(72);
    }
    if (item_ck(72)) {
        remove_item(72);
    }
    return;
}
scd {
    if (item_ck(73)) {
        remove_item(73);
    }
    if (item_ck(73)) {
        remove_item(73);
    }
    if (item_ck(73)) {
        remove_item(73);
    }
    if (item_ck(73)) {
        remove_item(73);
    }
    if (item_ck(73)) {
        remove_item(73);
    }
    if (item_ck(73)) {
        remove_item(73);
    }
    return;
}
scd {
    if (item_ck(74)) {
        remove_item(74);
    }
    if (item_ck(74)) {
        remove_item(74);
    }
    if (item_ck(74)) {
        remove_item(74);
    }
    if (item_ck(74)) {
        remove_item(74);
    }
    if (item_ck(74)) {
        remove_item(74);
    }
    if (item_ck(74)) {
        remove_item(74);
    }
    return;
}
scd {
    if (item_ck(75)) {
        remove_item(75);
    }
    if (item_ck(75)) {
        remove_item(75);
    }
    if (item_ck(75)) {
        remove_item(75);
    }
    if (item_ck(75)) {
        remove_item(75);
    }
    if (item_ck(75)) {
        remove_item(75);
    }
    if (item_ck(75)) {
        remove_item(75);
    }
    return;
}
sleep(20);
timer_setup(2, 0, 255, 7, 0);
sleep(150);
timer_setup(2, 0, 0, 7, 0);
// She walks to (12240, 5440).
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_pose(2, 12240, 5440, 62);
anim_end_release();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
message(135, 0, 0);  // her
wait_voice();
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_idle();
anim_end_release();
scd {
    set(FG_STATUS, 15, 1);
    cut_auto(0);
    set(FG_6, 23, 0);
    return;
}
return;
