// init procedure 0 @ 0xf4e4
door_aot_set(0, 15200, 2400, 2000, 2600, 9, 0, 0, 1, 0, ROOM_S09, 2700, 0, 8500, 0, UNLOCKED, 129);
door_aot_set(1, 1800, 1000, 2400, 1400, 2, 0, 30, 5, 64, ROOM_S17, 2900, 0, 10000, 0, UNLOCKED, 129);
door_aot_set(2, 7800, 5200, 1500, 1700, 1, 0, 1, 4, 216, ROOM_S19, 6300, 0, 2700, 3072, 54 /* Helmet Key */, 129);
// Rebecca's scenario: the bolted door to 10B now opens onto the 1F left stairs
// (arrival copied from 103's door to 101), her way to the save room.
door_aot_set(3, 10600, 5200, 2000, 1700, 2, 0, 0, 1, 0, ROOM_S01, 19000, 0, 20500, 2048, UNLOCKED, 129);
door_aot_set(4, 200, 10700, 2000, 2300, 0, 1, 8, 0, 64, ROOM_S1A, 4500, 0, 4100, 2048, UNLOCKED, 129);
enemy(17 /* Zombie (Green Coat) */, 0, 113, 1, 2, 0, 0, 0, 0, 0, 8272, 0, 2433, 0, 0, 0, 0);
enemy(17 /* Zombie (Green Coat) */, 0, 114, 1, 2, 0, 0, 1031, 0, 0, 3023, 0, 6864, 1, 0, 0, 0);
return;
