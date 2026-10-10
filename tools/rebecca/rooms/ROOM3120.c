// init procedure 0 @ 0x0
// The foot of the mountain trail leads into the courtyard garden (ROOM_300)
// through its iron gate: she arrives just inside it at (23800, 27500) facing
// into the garden (angle 0x400, -Z), on the gate's camera 4. (The garden's
// own arrival from the falls is the lift, which made her ride up it.) The zone runs past the wall at Z 16000: a
// door fires when the point 600 units ahead of the player is inside it, and
// the wall stops her 390 units short of Z 16000. Flag 1 (no 0x80) makes it fire
// by walking into it, with no action key; a door with 0x80 waits for the key.
door_aot_set(0, 1500, 15200, 4000, 2000, 0, 0, 0, 4, 0, ROOM_300, 23800, 0, 27500, 1024, UNLOCKED, 1);
return;
