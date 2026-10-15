// Rebecca's map screen in her mode (port addition). The tables behind these
// are generated into RebMaps.cpp by tools/rebecca/maps/engine.ts.
#pragma once

// One of her rooms: where it is, which area's map draws it and in which
// palette block, and its "visited" bit in g_RoomFlags.
struct RebMapRoom {
    unsigned char stage;
    unsigned char room;
    unsigned char area;
    unsigned char slot;
    unsigned char bit;
};

// A browser sprite: where it is in the overview picture, and on the screen.
struct RebMapRect {
    unsigned char u, v;
    short x, y;
    unsigned char w, h;
};

struct RebMaps {
    const RebMapRoom* rooms;
    int roomCount;
    unsigned char areaRooms[11];
    unsigned char areaItem[11];     // map index (item 0x4E + index); 0xff: none
    unsigned char areaStage[11];
    unsigned char stageAreas[4][4]; // 0xff past the stage's last area
    unsigned char stageCount[4];
    RebMapRect markers[4];
    RebMapRect labels[11];
    short arrowX;
};

extern const RebMaps g_RebMaps;

// Her room at (stage, room), or null when it is not one of hers.
const RebMapRoom* reb_map_room(int stage, int room);

// The visited bit of an area's room by its palette block, or -1.
int reb_map_visited_bit(int area, int slot);
