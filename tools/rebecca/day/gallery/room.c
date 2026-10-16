// gallery (51F), written by day/scripts.ts from day/gallery/scene.py: edit the scene, not this file.
// init procedure 0
// To junction.
door_aot_set(0, 1700, 6120, 1020, 4760, 0, 1, 8, 0, 0, ROOM_51E, 10200, 0, 11560, 1024, UNLOCKED, 193);
if (ck(FG_ITEM, 167, 0)) {  // operator key (op-key)
    item_aot_set(1, 11810, 6710, 1200, 1200, 56, 1, 0, 255, 122, 48, 126, 249, 142, 28, 0, 0, 167, 129, 0, 0);
}
aot_set(2, 14790, 7990, 3740, 2550, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 10710, 6630, 3060, 2380, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 17340, 7820, 6460, 1020, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
if (ck(FG_COMMON, 118, 0) && ck(FG_COMMON, 119, 0)) {
    enemy(17, 0, 221, 1, 2, 0, 0, 1917, 0, 0, 24500, 0, 12600, 0, 0, 0, 0);  // a zombie
}
// cut-mine-collapse (day/cutscenes.ts): its people, and what starts it. FG_COMMON 118 once it has run.
// cut-hal (day/cutscenes.ts): its people, and what starts it. FG_COMMON 119 once it has run.
if (ck(FG_COMMON, 119, 1)) {
    enemy(34, 0, 255, 1, 2, 0, 0, 2048, 0, 0, 12300, 0, 9400, 6, 0, 0, 0);  // Hal
} else {
    enemy(34, 0, 255, 1, 2, 0, 0, 2048, 0, 0, 12300, 0, 9400, 6, 4, 29, 0);  // Hal
}
if (ck(FG_COMMON, 119, 1)) {
    aot_set(5, 8000, 3400, 2000, 7300, SCE_EVENT, 1, 9, 0, 1, 0, 0, 0);
}
// The floor is about to give way (day/gear.ts): the mine plays chase until she is out of it.
if (ck(FG_COMMON, 238, 1)) {
    tbl37_set(4, 27, 9);   // mine-entrance
    tbl37_set(4, 28, 9);   // tunnel
    tbl37_set(4, 30, 9);   // junction
    tbl37_set(4, 31, 9);   // gallery
    tbl37_set(4, 9, 9);   // mine-lift
}
return;

// main procedure 0
if (ck(FG_ROOM, 11, 0) && item_ck(1)) {
    remove_item(1);
}
if (ck(FG_ROOM, 11, 0) && item_ck(1)) {
    remove_item(1);
}
if (ck(FG_ROOM, 11, 0) && item_ck(1)) {
    remove_item(1);
}
if (ck(FG_ROOM, 11, 0) && item_ck(1)) {
    remove_item(1);
}
if (ck(FG_ROOM, 11, 0) && item_ck(1)) {
    remove_item(1);
}
if (ck(FG_ROOM, 11, 0) && item_ck(1)) {
    remove_item(1);
}
if (ck(FG_ROOM, 11, 0) && item_ck(2)) {
    remove_item(2);
}
if (ck(FG_ROOM, 11, 0) && item_ck(2)) {
    remove_item(2);
}
if (ck(FG_ROOM, 11, 0) && item_ck(2)) {
    remove_item(2);
}
if (ck(FG_ROOM, 11, 0) && item_ck(2)) {
    remove_item(2);
}
if (ck(FG_ROOM, 11, 0) && item_ck(2)) {
    remove_item(2);
}
if (ck(FG_ROOM, 11, 0) && item_ck(2)) {
    remove_item(2);
}
if (ck(FG_ROOM, 11, 0) && item_ck(3)) {
    remove_item(3);
}
if (ck(FG_ROOM, 11, 0) && item_ck(3)) {
    remove_item(3);
}
if (ck(FG_ROOM, 11, 0) && item_ck(3)) {
    remove_item(3);
}
if (ck(FG_ROOM, 11, 0) && item_ck(3)) {
    remove_item(3);
}
if (ck(FG_ROOM, 11, 0) && item_ck(3)) {
    remove_item(3);
}
if (ck(FG_ROOM, 11, 0) && item_ck(3)) {
    remove_item(3);
}
if (ck(FG_ROOM, 11, 0) && item_ck(4)) {
    remove_item(4);
}
if (ck(FG_ROOM, 11, 0) && item_ck(4)) {
    remove_item(4);
}
if (ck(FG_ROOM, 11, 0) && item_ck(4)) {
    remove_item(4);
}
if (ck(FG_ROOM, 11, 0) && item_ck(4)) {
    remove_item(4);
}
if (ck(FG_ROOM, 11, 0) && item_ck(4)) {
    remove_item(4);
}
if (ck(FG_ROOM, 11, 0) && item_ck(4)) {
    remove_item(4);
}
if (ck(FG_ROOM, 11, 0) && item_ck(5)) {
    remove_item(5);
}
if (ck(FG_ROOM, 11, 0) && item_ck(5)) {
    remove_item(5);
}
if (ck(FG_ROOM, 11, 0) && item_ck(5)) {
    remove_item(5);
}
if (ck(FG_ROOM, 11, 0) && item_ck(5)) {
    remove_item(5);
}
if (ck(FG_ROOM, 11, 0) && item_ck(5)) {
    remove_item(5);
}
if (ck(FG_ROOM, 11, 0) && item_ck(5)) {
    remove_item(5);
}
if (ck(FG_ROOM, 11, 0) && item_ck(6)) {
    remove_item(6);
}
if (ck(FG_ROOM, 11, 0) && item_ck(6)) {
    remove_item(6);
}
if (ck(FG_ROOM, 11, 0) && item_ck(6)) {
    remove_item(6);
}
if (ck(FG_ROOM, 11, 0) && item_ck(6)) {
    remove_item(6);
}
if (ck(FG_ROOM, 11, 0) && item_ck(6)) {
    remove_item(6);
}
if (ck(FG_ROOM, 11, 0) && item_ck(6)) {
    remove_item(6);
}
if (ck(FG_ROOM, 11, 0) && item_ck(7)) {
    remove_item(7);
}
if (ck(FG_ROOM, 11, 0) && item_ck(7)) {
    remove_item(7);
}
if (ck(FG_ROOM, 11, 0) && item_ck(7)) {
    remove_item(7);
}
if (ck(FG_ROOM, 11, 0) && item_ck(7)) {
    remove_item(7);
}
if (ck(FG_ROOM, 11, 0) && item_ck(7)) {
    remove_item(7);
}
if (ck(FG_ROOM, 11, 0) && item_ck(7)) {
    remove_item(7);
}
if (ck(FG_ROOM, 11, 0) && item_ck(8)) {
    remove_item(8);
}
if (ck(FG_ROOM, 11, 0) && item_ck(8)) {
    remove_item(8);
}
if (ck(FG_ROOM, 11, 0) && item_ck(8)) {
    remove_item(8);
}
if (ck(FG_ROOM, 11, 0) && item_ck(8)) {
    remove_item(8);
}
if (ck(FG_ROOM, 11, 0) && item_ck(8)) {
    remove_item(8);
}
if (ck(FG_ROOM, 11, 0) && item_ck(8)) {
    remove_item(8);
}
if (ck(FG_ROOM, 11, 0) && item_ck(9)) {
    remove_item(9);
}
if (ck(FG_ROOM, 11, 0) && item_ck(9)) {
    remove_item(9);
}
if (ck(FG_ROOM, 11, 0) && item_ck(9)) {
    remove_item(9);
}
if (ck(FG_ROOM, 11, 0) && item_ck(9)) {
    remove_item(9);
}
if (ck(FG_ROOM, 11, 0) && item_ck(9)) {
    remove_item(9);
}
if (ck(FG_ROOM, 11, 0) && item_ck(9)) {
    remove_item(9);
}
if (ck(FG_ROOM, 11, 0) && item_ck(10)) {
    remove_item(10);
}
if (ck(FG_ROOM, 11, 0) && item_ck(10)) {
    remove_item(10);
}
if (ck(FG_ROOM, 11, 0) && item_ck(10)) {
    remove_item(10);
}
if (ck(FG_ROOM, 11, 0) && item_ck(10)) {
    remove_item(10);
}
if (ck(FG_ROOM, 11, 0) && item_ck(10)) {
    remove_item(10);
}
if (ck(FG_ROOM, 11, 0) && item_ck(10)) {
    remove_item(10);
}
if (ck(FG_ROOM, 11, 0) && item_ck(11)) {
    remove_item(11);
}
if (ck(FG_ROOM, 11, 0) && item_ck(11)) {
    remove_item(11);
}
if (ck(FG_ROOM, 11, 0) && item_ck(11)) {
    remove_item(11);
}
if (ck(FG_ROOM, 11, 0) && item_ck(11)) {
    remove_item(11);
}
if (ck(FG_ROOM, 11, 0) && item_ck(11)) {
    remove_item(11);
}
if (ck(FG_ROOM, 11, 0) && item_ck(11)) {
    remove_item(11);
}
if (ck(FG_ROOM, 11, 0) && item_ck(12)) {
    remove_item(12);
}
if (ck(FG_ROOM, 11, 0) && item_ck(12)) {
    remove_item(12);
}
if (ck(FG_ROOM, 11, 0) && item_ck(12)) {
    remove_item(12);
}
if (ck(FG_ROOM, 11, 0) && item_ck(12)) {
    remove_item(12);
}
if (ck(FG_ROOM, 11, 0) && item_ck(12)) {
    remove_item(12);
}
if (ck(FG_ROOM, 11, 0) && item_ck(12)) {
    remove_item(12);
}
if (ck(FG_ROOM, 11, 0) && item_ck(13)) {
    remove_item(13);
}
if (ck(FG_ROOM, 11, 0) && item_ck(13)) {
    remove_item(13);
}
if (ck(FG_ROOM, 11, 0) && item_ck(13)) {
    remove_item(13);
}
if (ck(FG_ROOM, 11, 0) && item_ck(13)) {
    remove_item(13);
}
if (ck(FG_ROOM, 11, 0) && item_ck(13)) {
    remove_item(13);
}
if (ck(FG_ROOM, 11, 0) && item_ck(13)) {
    remove_item(13);
}
if (ck(FG_ROOM, 11, 0) && item_ck(14)) {
    remove_item(14);
}
if (ck(FG_ROOM, 11, 0) && item_ck(14)) {
    remove_item(14);
}
if (ck(FG_ROOM, 11, 0) && item_ck(14)) {
    remove_item(14);
}
if (ck(FG_ROOM, 11, 0) && item_ck(14)) {
    remove_item(14);
}
if (ck(FG_ROOM, 11, 0) && item_ck(14)) {
    remove_item(14);
}
if (ck(FG_ROOM, 11, 0) && item_ck(14)) {
    remove_item(14);
}
if (ck(FG_ROOM, 11, 0) && item_ck(15)) {
    remove_item(15);
}
if (ck(FG_ROOM, 11, 0) && item_ck(15)) {
    remove_item(15);
}
if (ck(FG_ROOM, 11, 0) && item_ck(15)) {
    remove_item(15);
}
if (ck(FG_ROOM, 11, 0) && item_ck(15)) {
    remove_item(15);
}
if (ck(FG_ROOM, 11, 0) && item_ck(15)) {
    remove_item(15);
}
if (ck(FG_ROOM, 11, 0) && item_ck(15)) {
    remove_item(15);
}
if (ck(FG_ROOM, 11, 0) && item_ck(16)) {
    remove_item(16);
}
if (ck(FG_ROOM, 11, 0) && item_ck(16)) {
    remove_item(16);
}
if (ck(FG_ROOM, 11, 0) && item_ck(16)) {
    remove_item(16);
}
if (ck(FG_ROOM, 11, 0) && item_ck(16)) {
    remove_item(16);
}
if (ck(FG_ROOM, 11, 0) && item_ck(16)) {
    remove_item(16);
}
if (ck(FG_ROOM, 11, 0) && item_ck(16)) {
    remove_item(16);
}
if (ck(FG_ROOM, 11, 0) && item_ck(17)) {
    remove_item(17);
}
if (ck(FG_ROOM, 11, 0) && item_ck(17)) {
    remove_item(17);
}
if (ck(FG_ROOM, 11, 0) && item_ck(17)) {
    remove_item(17);
}
if (ck(FG_ROOM, 11, 0) && item_ck(17)) {
    remove_item(17);
}
if (ck(FG_ROOM, 11, 0) && item_ck(17)) {
    remove_item(17);
}
if (ck(FG_ROOM, 11, 0) && item_ck(17)) {
    remove_item(17);
}
if (ck(FG_ROOM, 11, 0) && item_ck(18)) {
    remove_item(18);
}
if (ck(FG_ROOM, 11, 0) && item_ck(18)) {
    remove_item(18);
}
if (ck(FG_ROOM, 11, 0) && item_ck(18)) {
    remove_item(18);
}
if (ck(FG_ROOM, 11, 0) && item_ck(18)) {
    remove_item(18);
}
if (ck(FG_ROOM, 11, 0) && item_ck(18)) {
    remove_item(18);
}
if (ck(FG_ROOM, 11, 0) && item_ck(18)) {
    remove_item(18);
}
if (ck(FG_ROOM, 11, 0) && item_ck(65)) {
    remove_item(65);
}
if (ck(FG_ROOM, 11, 0) && item_ck(65)) {
    remove_item(65);
}
if (ck(FG_ROOM, 11, 0) && item_ck(65)) {
    remove_item(65);
}
if (ck(FG_ROOM, 11, 0) && item_ck(65)) {
    remove_item(65);
}
if (ck(FG_ROOM, 11, 0) && item_ck(65)) {
    remove_item(65);
}
if (ck(FG_ROOM, 11, 0) && item_ck(65)) {
    remove_item(65);
}
if (ck(FG_ROOM, 11, 0) && item_ck(67)) {
    remove_item(67);
}
if (ck(FG_ROOM, 11, 0) && item_ck(67)) {
    remove_item(67);
}
if (ck(FG_ROOM, 11, 0) && item_ck(67)) {
    remove_item(67);
}
if (ck(FG_ROOM, 11, 0) && item_ck(67)) {
    remove_item(67);
}
if (ck(FG_ROOM, 11, 0) && item_ck(67)) {
    remove_item(67);
}
if (ck(FG_ROOM, 11, 0) && item_ck(67)) {
    remove_item(67);
}
if (ck(FG_ROOM, 11, 0) && item_ck(68)) {
    remove_item(68);
}
if (ck(FG_ROOM, 11, 0) && item_ck(68)) {
    remove_item(68);
}
if (ck(FG_ROOM, 11, 0) && item_ck(68)) {
    remove_item(68);
}
if (ck(FG_ROOM, 11, 0) && item_ck(68)) {
    remove_item(68);
}
if (ck(FG_ROOM, 11, 0) && item_ck(68)) {
    remove_item(68);
}
if (ck(FG_ROOM, 11, 0) && item_ck(68)) {
    remove_item(68);
}
if (ck(FG_ROOM, 11, 0) && item_ck(69)) {
    remove_item(69);
}
if (ck(FG_ROOM, 11, 0) && item_ck(69)) {
    remove_item(69);
}
if (ck(FG_ROOM, 11, 0) && item_ck(69)) {
    remove_item(69);
}
if (ck(FG_ROOM, 11, 0) && item_ck(69)) {
    remove_item(69);
}
if (ck(FG_ROOM, 11, 0) && item_ck(69)) {
    remove_item(69);
}
if (ck(FG_ROOM, 11, 0) && item_ck(69)) {
    remove_item(69);
}
if (ck(FG_ROOM, 11, 0) && item_ck(70)) {
    remove_item(70);
}
if (ck(FG_ROOM, 11, 0) && item_ck(70)) {
    remove_item(70);
}
if (ck(FG_ROOM, 11, 0) && item_ck(70)) {
    remove_item(70);
}
if (ck(FG_ROOM, 11, 0) && item_ck(70)) {
    remove_item(70);
}
if (ck(FG_ROOM, 11, 0) && item_ck(70)) {
    remove_item(70);
}
if (ck(FG_ROOM, 11, 0) && item_ck(70)) {
    remove_item(70);
}
if (ck(FG_ROOM, 11, 0) && item_ck(71)) {
    remove_item(71);
}
if (ck(FG_ROOM, 11, 0) && item_ck(71)) {
    remove_item(71);
}
if (ck(FG_ROOM, 11, 0) && item_ck(71)) {
    remove_item(71);
}
if (ck(FG_ROOM, 11, 0) && item_ck(71)) {
    remove_item(71);
}
if (ck(FG_ROOM, 11, 0) && item_ck(71)) {
    remove_item(71);
}
if (ck(FG_ROOM, 11, 0) && item_ck(71)) {
    remove_item(71);
}
if (ck(FG_ROOM, 11, 0) && item_ck(72)) {
    remove_item(72);
}
if (ck(FG_ROOM, 11, 0) && item_ck(72)) {
    remove_item(72);
}
if (ck(FG_ROOM, 11, 0) && item_ck(72)) {
    remove_item(72);
}
if (ck(FG_ROOM, 11, 0) && item_ck(72)) {
    remove_item(72);
}
if (ck(FG_ROOM, 11, 0) && item_ck(72)) {
    remove_item(72);
}
if (ck(FG_ROOM, 11, 0) && item_ck(72)) {
    remove_item(72);
}
if (ck(FG_ROOM, 11, 0) && item_ck(73)) {
    remove_item(73);
}
if (ck(FG_ROOM, 11, 0) && item_ck(73)) {
    remove_item(73);
}
if (ck(FG_ROOM, 11, 0) && item_ck(73)) {
    remove_item(73);
}
if (ck(FG_ROOM, 11, 0) && item_ck(73)) {
    remove_item(73);
}
if (ck(FG_ROOM, 11, 0) && item_ck(73)) {
    remove_item(73);
}
if (ck(FG_ROOM, 11, 0) && item_ck(73)) {
    remove_item(73);
}
if (ck(FG_ROOM, 11, 0) && item_ck(74)) {
    remove_item(74);
}
if (ck(FG_ROOM, 11, 0) && item_ck(74)) {
    remove_item(74);
}
if (ck(FG_ROOM, 11, 0) && item_ck(74)) {
    remove_item(74);
}
if (ck(FG_ROOM, 11, 0) && item_ck(74)) {
    remove_item(74);
}
if (ck(FG_ROOM, 11, 0) && item_ck(74)) {
    remove_item(74);
}
if (ck(FG_ROOM, 11, 0) && item_ck(74)) {
    remove_item(74);
}
if (ck(FG_ROOM, 11, 0) && item_ck(75)) {
    remove_item(75);
}
if (ck(FG_ROOM, 11, 0) && item_ck(75)) {
    remove_item(75);
}
if (ck(FG_ROOM, 11, 0) && item_ck(75)) {
    remove_item(75);
}
if (ck(FG_ROOM, 11, 0) && item_ck(75)) {
    remove_item(75);
}
if (ck(FG_ROOM, 11, 0) && item_ck(75)) {
    remove_item(75);
}
if (ck(FG_ROOM, 11, 0) && item_ck(75)) {
    remove_item(75);
}
if (ck(FG_ROOM, 11, 0)) {
    set(FG_ROOM, 11, 1);
}
if (ck(FG_COMMON, 118, 1)) {
    set(FG_COMMON, 118, 0);
    evt_exec(0, 9, 0);
}
if (ck(FG_COMMON, 119, 1) && ck(FG_ROOM, 13, 1)) {
    if (ck(FG_ROOM, 12, 0)) {
        eml_state(0, 6, 2, 9, 0);
        set(FG_ROOM, 13, 0);
    }
    set(FG_ROOM, 12, 0);
}
return;

// event procedure 0
// cut-mine-collapse (day/cutscenes.ts)
scd {
    set(FG_COMMON, 118, 0);
    set(FG_STATUS, 15, 0);
    set(FG_6, 23, 1);
    return;
}
dir_set(0, 0, 0, 0, 4420, 0, 8500);  // her, in from junction
cutnext(0);
message(132, 0, 0);  // her
wait_voice();
// She walks to (6400, 11200).
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_pose(2, 6400, 11200, 62);
anim_end_release();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
set(FG_STATUS, 62, 0);
set(FG_ROOM, 11, 0);
sys_multi(0);
sleep(25);
message(133, 0, 0);  // her
wait_voice();
set(FG_STATUS, 62, 1);
message(134, 0, 0);  // her
wait_voice();
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

// event procedure 1
// cut-hal (day/cutscenes.ts)
scd {
    set(FG_COMMON, 119, 0);
    aot_reset(5, SCE_NONE, 129, 0, 0, 0);
    set(FG_STATUS, 15, 0);
    set(FG_6, 23, 1);
    return;
}
cutnext(3);
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(34, 63, 0);
    anim_flags(0, 16);
anim_end();
message(136, 0, 0);  // Hal
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
// She walks to (10500, 9500).
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_pose(2, 10500, 9500, 62);
anim_end_release();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_pose(6, 10500, 9500, 62);
anim_end();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
message(137, 0, 0);  // her
wait_voice();
cutnext(0);
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(33, 63, 0);
    anim_flags(0, 16);
anim_end();
message(138, 0, 0);  // Hal
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
message(139, 0, 0);  // her
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(37, 63, 0);
    anim_flags(0, 16);
anim_end();
message(140, 0, 0);  // Hal
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(35, 63, 0);
    anim_flags(0, 16);
anim_end();
message(141, 0, 0);  // Hal
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
// She takes the op-key.
scd {
    set(FG_6, 23, 0);
    give_item(1, 4, 129);
    return;
}
sleep(1);
set(FG_6, 23, 1);
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(34, 63, 0);
    anim_flags(0, 16);
anim_end();
message(142, 0, 0);  // Hal
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(9, 62, 0);
anim_end();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
message(143, 0, 0);  // her
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(4, 62, 0);
anim_end();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
sleep(30);
message(144, 0, 0);  // her
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
