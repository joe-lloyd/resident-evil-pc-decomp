// Rebecca's files in her mode (port addition). The tables behind these are
// generated into RebFiles.cpp by tools/rebecca/files/engine.ts.
#pragma once

// Her name for file item `itemId` (0x5F + slot), or null when the slot is not hers.
const unsigned char* reb_file_name(unsigned char itemId);

// Her x for a file title in the FILE tab, in the units of the USA title table.
short reb_file_title_x(unsigned char fileIndex);

// Fill both characters' halves of the 32-entry FILE book list with her books.
void reb_file_books(unsigned char* list);
