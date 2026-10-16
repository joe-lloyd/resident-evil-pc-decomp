// init procedure 0 @ 0x55e8
door_aot_set(0, 2500, 9400, 1700, 2000, 1, 0, 29, 5, 0, ROOM_S01, 15000, 0, 18800, 3072, UNLOCKED, 129);
item_aot_set(1, 6500, 9100, 500, 900, 28 /* Broken Shotgun */, 1, 0, 255, 184, 26, 54, 247, 198, 37, 48, 248, 48, 129, 0, 0);
eml_rot(0, 156, 255, 180, 251);
item_aot_set(2, 0, 0, 0, 0, 12 /* Shells */, 7, 1, 255, 24, 11, 102, 254, 22, 8, 232, 3, 49, 0, 0, 0);
eml_rot(1, 0, 0, 180, 251);
setbyte(1, 0, 0);
item_aot_set(3, 4540, 8470, 1800, 1800, 11 /* Clip */, 15, 2, 255, 64, 21, 204, 247, 154, 36, 0, 0, 50, 129, 0, 0);
aot_set(4, 2000, 2237, 1750, 700, SCE_HIKIDASHI, 129, 30, 0, 2, 0, 3, 0);
// Rebecca's scenario: a lab-coat zombie waits in the vacant room.
enemy(0 /* Zombie (White Coat) */, 0, 250, 1, 2, 0, 0, 0, 0, 0, 4500, 0, 6000, 0, 0, 0, 0);
return;
