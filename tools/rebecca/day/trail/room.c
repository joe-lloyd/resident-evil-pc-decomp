// Outdoor doors walk rather than open: door bytes 0, 15, 48 play walk 0 with
// the footsteps of sound row 15 (src/game/PathWalk.cpp).
// init procedure 0 @ 0x0
// The top of the trail leads back up to the ridge (ROOM3130), on the action
// key; the foot leads to the ranger station's yard (ROOM3150), on touch: she
// comes in at its north-west corner by the sign, facing into the yard
// (+X +Z, angle 0xE00).
door_aot_set(0, 2000, 0, 3000, 600, 0, 15, 48, 4, 0, ROOM_313, 10300, 0, 5300, 2048, UNLOCKED, 129);
door_aot_set(1, 1500, 15200, 4000, 2000, 0, 15, 48, 4, 0, ROOM_315, 5610, 0, 4930, 3584, UNLOCKED, 1);
// Things to examine (room messages are 0x80 + index): the marker post at the
// turn on the east side (x 3.29 m, y 6.2 m in the scene), and the fallen
// spruce along the west bank (y 1.1-8.1 m).
aot_set(2, 4400, 9700, 600, 1700, SCE_MESSAGE, 129, 128, 0, 255, 0, 0, 0);  // the marker post
aot_set(3, 2000, 5100, 600, 3400, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);  // the fallen spruce
// Two crows on the path halfway down, facing up it (angle 0x400, -Z), kill
// flags 253 and 254 (day/foes.ts keeps those for the trail).
enemy(5, 0, 253, 1, 2, 0, 0, 1024, 0, 0, 3800, 0, 7000, 0, 0, 0, 0);
enemy(5, 0, 254, 1, 2, 0, 0, 1024, 0, 0, 2900, 0, 9600, 1, 0, 0, 0);
return;

// main procedure 0
return;
