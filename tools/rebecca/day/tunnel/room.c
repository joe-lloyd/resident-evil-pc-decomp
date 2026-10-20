// tunnel (51C), written by day/scripts.ts from day/tunnel/scene.py: edit the scene, not this file.
// init procedure 0
// To mine-entrance.
door_aot_set(0, 6800, 31280, 3400, 1020, 0, 1, 8, 0, 0, ROOM_51B, 21080, 0, 7820, 3072, UNLOCKED, 193);
// To mine-office.
door_aot_set(1, 20570, 12206, 1530, 1020, 1, 0, 7, 1, 0, ROOM_51D, 4845, 0, 5100, 1024, UNLOCKED, 193);
// To junction.
door_aot_set(2, 31280, 12920, 1020, 3400, 0, 1, 8, 0, 0, ROOM_51E, 4080, 0, 9860, 0, UNLOCKED, 193);
aot_set(3, 8500, 15725, 2210, 1700, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 22270, 12206, 1360, 1190, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 7480, 22440, 3230, 4420, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 28560, 12920, 2550, 3400, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 21930, 12920, 2550, 3400, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
enemy(3, 2, 218, 1, 2, 0, 0, 4073, 0, 0, 7670, 0, 15490, 0, 0, 0, 0);  // a spinner
return;

// main procedure 0
return;
