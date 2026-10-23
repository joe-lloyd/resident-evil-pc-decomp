// lodge (21D), written by day/scripts.ts from day/lodge/scene.py: edit the scene, not this file.
// init procedure 0
// To creek.
// Shut from this side until she opens it from the other (FG_LOCK 47).
if (ck(FG_LOCK, 47, 1)) {
    aot_set(0, 8330, 2890, 1360, 1530, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
} else {
    door_aot_set(0, 8330, 2890, 1360, 1530, 1, 0, 33, 1, 0, ROOM_21C, 12750, 0, 20485, 0, UNLOCKED, 193);
}
// The typewriter and the item box, its lid on the body the scene paints.
aot_set(1, 5525, 1700, 1275, 1275, SCE_TYPEWRITER, 129, 0, 0, 0, 0, 0, 0);
aot_set(2, 3315, 5865, 2074, 1955, SCE_ITEMBOX, 129, 0, 0, 0, 0, 0, 0);
obj(0, 17, 255, 4310, -1440, 7809, 1024, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
if (ck(FG_ITEM, 253, 0)) {  // the grounds plan (maps/pickups.ts)
    item_aot_set(3, 4370, 1990, 1200, 1200, 83, 1, 3, 255, 106, 19, 0, 0, 30, 10, 0, 0, 253, 129, 0, 0);
}
if (ck(FG_ITEM, 169, 0)) {  // gate key (gate-key)
    item_aot_set(4, 8294, 4605, 1500, 1500, 52, 1, 4, 255, 84, 35, 180, 246, 235, 20, 0, 0, 169, 129, 0, 0);
}
if (ck(FG_ITEM, 200, 0)) {  // spray
    item_aot_set(5, 1990, 4370, 1200, 1200, 65, 1, 0, 255, 30, 10, 0, 0, 106, 19, 0, 0, 200, 129, 0, 0);
}
if (ck(FG_ITEM, 201, 0)) {  // redHerb
    item_aot_set(6, 1990, 2670, 1200, 1200, 67, 1, 1, 255, 30, 10, 0, 0, 198, 12, 0, 0, 201, 129, 1, 0);
}
if (ck(FG_ITEM, 202, 0)) {  // ribbons
    item_aot_set(7, 4370, 5050, 1200, 1200, 47, 3, 2, 255, 106, 19, 0, 0, 18, 22, 0, 0, 202, 129, 0, 0);
}
// Gardener's diary, a file.
if (ck(FG_ITEM, 239, 0)) {
    item_aot_set(8, 3060, 3145, 1530, 2125, 101, 1, 5, 255, 0, 0, 0, 0, 0, 0, 0, 0, 239, 129, 0, 0);
}
aot_set(9, 4590, 3145, 1530, 1912, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(10, 4930, 5355, 3995, 1360, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(11, 7480, 1190, 1700, 1700, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(12, 8160, 4675, 1530, 1105, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(13, 1190, 2380, 1530, 3230, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(14, 1870, 1190, 3060, 1700, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(15, 6120, 3060, 2210, 1615, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
if (ck(FG_ITEM, 253, 0)) {
    set(FG_ROOM, 12, 0);
}
return;

// main procedure 0
if (ck(FG_ROOM, 12, 0) && ck(FG_ITEM, 253, 1)) {
    set(FG_ROOM, 12, 1);
    message(137, 255, 0);
}
return;
