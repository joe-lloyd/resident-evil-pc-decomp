// Her key items in her mode (port addition). The table behind these is
// generated into RebItems.cpp by tools/rebecca/items/engine.ts.
#pragma once

// Her name for item `itemId`, or null when the item is not one of hers.
const unsigned char* reb_item_name(unsigned char itemId);

// Her description for item `itemId`, or null when the item is not one of hers.
const unsigned char* reb_item_description(unsigned char itemId);
