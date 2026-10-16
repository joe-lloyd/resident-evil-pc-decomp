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
enemy(17, 0, 221, 1, 2, 0, 0, 1917, 0, 0, 24500, 0, 12600, 0, 0, 0, 0);  // a zombie
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
if (ck(FG_COMMON, 238, 1)) {
    set(FG_COMMON, 238, 0);
    set(FG_ROOM, 11, 0);
    sys_multi(0);
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
    message(128, 255, 0);
}
return;
