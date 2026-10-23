// creek (21C), written by day/scripts.ts from day/creek/scene.py: edit the scene, not this file.
// init procedure 0
// To valley-path.
door_aot_set(0, 15300, 3400, 5100, 1020, 0, 15, 48, 4, 0, ROOM_218, 17000, 0, 26180, 1024, UNLOCKED, 1);
// To lodge.
// Shut until she uses the crowbar on it: FG_LOCK 47 once she has.
if (ck(FG_LOCK, 47, 1)) {
    aot_set(1, 10370, 19210, 1530, 2550, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
    aot_set(2, 10370, 19210, 1530, 2550, SCE_USEITEM, 1, 9, 0, 16, 0, 1, 0);   // the crowbar can be used here
} else {
    door_aot_set(1, 10370, 19210, 1530, 2550, 1, 0, 33, 1, 175, ROOM_21D, 7820, 0, 3655, 2048, 43, 193);
}
// To estate-wall.
door_aot_set(3, 18700, 22780, 4250, 1020, 0, 15, 48, 4, 0, ROOM_21E, 21760, 0, 3910, 3072, UNLOCKED, 1);
if (ck(FG_ITEM, 199, 0)) {  // greenHerb
    item_aot_set(4, 3350, 8790, 1200, 1200, 68, 1, 0, 255, 110, 15, 0, 0, 174, 36, 0, 0, 199, 129, 1, 0);
}
aot_set(5, 10880, 18700, 1870, 3570, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 5270, 15640, 3400, 2210, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 21590, 9690, 5100, 2720, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 10710, 22270, 3740, 2040, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 16830, 15640, 3740, 2890, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(10, 15810, 8500, 3060, 2720, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
aot_set(11, 9690, 15300, 3400, 2890, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
enemy(10, 1, 228, 1, 1, 0, 0, 161, 0, 0, 4100, 0, 9200, 0, 0, 0, 0);  // a adder
enemy(10, 1, 229, 1, 1, 0, 0, 1763, 0, 0, 27900, 0, 10560, 1, 0, 0, 0);  // a adder
return;

// main procedure 0
if (ck(FG_LOCK, 47, 1)) {
    if (ck(FG_ROOM, 12, 1) && testitem(43)) {
        set(FG_ROOM, 12, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 12, 0) && cmpw(0, 4, 1, 0)) {
        set(FG_ROOM, 12, 1);
        set(FG_LOCK, 47, 0);
        if (item_ck(43)) {
            remove_item(43);
        }
        door_aot_set(1, 10370, 19210, 1530, 2550, 1, 0, 33, 1, 175, ROOM_21D, 7820, 0, 3655, 2048, 43, 193);
        message(130, 255, 0);
    }
}
return;
