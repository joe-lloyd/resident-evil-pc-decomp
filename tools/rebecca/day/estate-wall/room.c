// estate-wall (21E), written by day/scripts.ts from day/estate-wall/scene.py: edit the scene, not this file.
// init procedure 0
// To creek.
door_aot_set(0, 19380, 1105, 4760, 1020, 0, 15, 48, 4, 0, ROOM_21C, 20740, 0, 21420, 1024, UNLOCKED, 1);
// To kennels.
door_aot_set(1, 15810, 31280, 2380, 1020, 0, 16, 48, 4, 176, ROOM_21F, 17000, 0, 5780, 3072, 52, 193);
aot_set(2, 15810, 30770, 2380, 1530, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 13940, 31110, 1700, 1190, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 15300, 29580, 2720, 1190, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 13770, 28390, 1700, 1700, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 11050, 26520, 3570, 1700, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 22780, 2210, 1360, 1530, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 21760, 6120, 1360, 1700, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
enemy(5, 0, 230, 1, 2, 0, 0, 3431, 0, 0, 8180, 0, 15405, 0, 0, 0, 0);  // a crow
enemy(5, 0, 231, 1, 2, 0, 0, 2530, 0, 0, 27900, 0, 19825, 1, 0, 0, 0);  // a crow
return;

// main procedure 0
if (ck(FG_COMMON, 251, 1)) {
    set(FG_COMMON, 251, 0);
    message(128, 255, 0);
}
return;
