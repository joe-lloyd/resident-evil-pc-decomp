// The papers Rebecca finds and reads on her day: every word of them, page by
// page, in one place so the texts are easy to read and change. pages.ts draws
// them and packs them for the game; review.ts lays them out for the owner.
//
// Writing a page:
// - A blank line starts a new paragraph; a single newline breaks the line.
// - Long lines wrap on their own. A page that runs past the paper fails.
// - '>' at the start of a line sets it to the right (a signature) and '^'
//   centres it (a heading).
// - On ledger paper, a line that opens with a time ("0305 " or "01.20 ")
//   writes the time in the ledger's time column.
// - `shaky` makes the hand unsteady: 1 for a bad night, 2 for the last
//   lines of someone who is turning.
//
// Each document fills one of the game's 16 file slots. The reader takes a
// file's page count from the slot (g_itemMaxCounts, 0x004d2620: 4, 6, 11, 4,
// 2, 6, 7, 7, 10, 5, 5, 4, 3, 3, 3, 4), so each document is written to the
// count of the slot it sits in, title page included.

/** The paper a page is drawn on. `black` is RE1's own look: light type on the reader's black. */
export type Paper = 'black' | 'notebook' | 'ledger' | 'letter';

/** A blood mark on a page, in page pixels. */
export type Mark = { kind: 'thumb'; x: number; y: number } | { kind: 'drip'; x: number; y: number; len: number };

export interface Calendar {
  kind: 'calendar';
  company: string;
  town: string;
  month: string;
  /** 0 is Sunday. */
  firstWeekday: number;
  days: number;
  circled: number[];
  notes: Record<number, string>;
  scrawl: string;
}

export interface MineMap {
  kind: 'map';
  heading: string;
  sub: string;
  labels: [string, number, number][];
  /** Red pencil in the margin. */
  notes: [string, number, number][];
  thumb: [number, number];
}

export interface Notice {
  kind: 'notice';
  heading: string;
  lines: string[];
  /** Where the paper tears, in page pixels from the top. */
  tearAt: number;
}

/** A day on the roster: a tick, SICK in red on the first day off sick (the days after stay empty), or nothing. */
export type Shift = 'in' | 'sick' | 'none';

export interface Roster {
  kind: 'roster';
  company: string;
  heading: string;
  rows: { name: string; days: [Shift, Shift, Shift, Shift, Shift]; struck?: boolean }[];
  /** Red pencil under the table. */
  foot?: string;
}

export type Page =
  | { kind: 'title' }
  | { kind: 'text'; text: string; shaky?: number; letterhead?: 'umbrella'; paper?: Paper; marks?: Mark[] }
  | Calendar
  | MineMap
  | Notice
  | Roster;

export interface Doc {
  /** As in the tracker (todo.ts): file-<id>. */
  id: string;
  title: string;
  subtitle?: string;
  writer: string;
  /** The room's folder under tools/rebecca/day/. */
  room: string;
  where: string;
  act: number;
  /** The file slot, 0 to 15: the item is 0x5F + slot. */
  slot: number;
  /** How the scene's check for it starts (renders/room.json): that check becomes the pickup. */
  check: string;
  paper: Paper;
  pages: Page[];
  /** Things the owner should decide. */
  notes?: string[];
}

/** Pages per file slot, from g_itemMaxCounts (0x004d2620). */
export const SLOT_PAGES = [4, 6, 11, 4, 2, 6, 7, 7, 10, 5, 5, 4, 3, 3, 3, 4] as const;

/**
 * Her FILE tab: two books of eight, in the order she comes to them. A file's
 * place here also gives its room-item flag, ITEM_FLAG_BASE + place, which
 * keeps it taken once she has it.
 */
export const BOOKS = ['logbook', 'quarantine', 'calendar', 'foreman-letters', 'walt-log', 'diary', 'rosters', 'mine-map', 'keeper-log', 'gardener-diary'] as const;

/** Room-item flags 230 to 239: free in her rooms (the cabin and the shed use 241 to 243). */
export const ITEM_FLAG_BASE = 230;

const title = { kind: 'title' } as const;

export const DOCUMENTS: Doc[] = [
  {
    id: 'logbook',
    title: "Ranger's logbook",
    subtitle: 'Ranger Station 3',
    writer: 'The ranger, who is dead in the hollow by noon',
    room: 'lookout',
    where: 'The cabin, act 1: open on the desk. It tells her the winch crank is in the shed.',
    act: 1,
    slot: 0,
    check: "The ranger's logbook.",
    paper: 'ledger',
    pages: [
      title,
      {
        kind: 'text',
        text: `
^JULY 22 1998
0715 Fog till nine. Trails quiet.
1130 Sheriff's office called. Two more hikers missing, a couple from Ohio. Their car is still in the lower lot.
1600 Walked the north ridge. Dog tracks again. Big ones. Not wolves. A print as wide as my hand.
1840 Found a boot. Nothing else.
`,
      },
      {
        kind: 'text',
        text: `
^JULY 23
0800 County order: the Arklay trails are closed after the killings.
1300 Gondola still running. Told Hal he should shut it. He says the company decides.
1800 Chained and locked the gate on Forest Road 7.
2210 Storm. The radio's busy. S.T.A.R.S. lost a helicopter up here. Saw no lights.
`,
      },
      {
        kind: 'text',
        text: `
^JULY 24
0500 The storm brought a pine down across the lower trail. The truck can't get past.
0510 I'll winch it clear after breakfast. Crank's in the shed.
0540 Dogs. On the porch. Taking the
`,
      },
    ],
  },
  {
    id: 'calendar',
    title: 'Bunkhouse calendar',
    writer: 'Ricky, one of the loggers, on the back of a supply company calendar',
    room: 'bunkhouse',
    where: "The bunkhouse, act 2: on the wall by the stove. The numbers open the foreman's safe.",
    act: 2,
    slot: 12,
    check: 'A calendar from a supply company.',
    paper: 'letter',
    pages: [
      title,
      {
        kind: 'calendar',
        company: 'MARBLE RIVER SUPPLY',
        town: 'Saws, Rope, Hardware',
        month: 'JULY 1998',
        firstWeekday: 3,
        days: 31,
        circled: [17, 31, 8],
        notes: { 4: '4TH', 12: 'MOM', 22: 'DOC?', 26: 'BALL' },
        scrawl: '17 31 8',
      },
      {
        kind: 'text',
        shaky: 1,
        text: `
Written on the back, in pencil:

The boss changes the safe every spring and then forgets it. He yells till somebody finds it for him.

So it's on here now. 17, 31, 8.

Don't tell him.
>Ricky
`,
      },
    ],
  },
  {
    id: 'diary',
    title: "Hal's diary",
    writer: 'Hal, the gondola operator, writing to his daughter Katie',
    room: 'cottage',
    where: "The operator's cottage, act 2: open on the table. He went to hide in the mine.",
    act: 2,
    slot: 1,
    check: 'His diary, open.',
    paper: 'notebook',
    pages: [
      title,
      {
        kind: 'text',
        text: `
July 22
Katie,
Your mother says you're counting the days. So am I. Nine more.

Fixed the bunk in the spare room. Found your old rod in the shed, red float and all.

Twelve riders today. People keep going missing up here.
`,
      },
      {
        kind: 'text',
        text: `
July 23
The company says we keep running, trails or no trails. Two crates went up for Camp 4 in car 2, cold box, company tape. I signed like always. I don't ask.

Pete at the bottom station says the estate's gardener came up again, raving the dogs are loose.

Shut the line at six. Storm.
`,
      },
      {
        kind: 'text',
        text: `
July 24, 3:30 in the morning
Pete rang the line phone. A woman from the lot, bitten by a dog. His phone is dead and I've got the radio, so he's sending her up in 4.

I ran the line out of hours.

4:50. The power went with 4 nearly in. It hit the dock and sheared the drive cog. Blew a fuse.
`,
      },
      {
        kind: 'text',
        shaky: 1,
        text: `
She wasn't sick, Katie. She was something else. She came out of that car like the door was paper.

She came at the booth glass. I got my hand up.

I wrote it all on the board like they taught us. Then I took the drive key and came home. Nobody runs the line without me.
`,
      },
      {
        kind: 'text',
        shaky: 2,
        text: `
Bolted the door. Barred it. The hand is bad, hot and swelling. The radio is only hiss.

Something walks the path. I watch it from the window.

I love you, Katie. Stay at your mother's. Don't come up.

it itches. hide in the mine till they come.
`,
      },
    ],
  },
  {
    id: 'mine-map',
    title: 'Mine map',
    writer: 'The mine\'s shift boss, 1987, with a Skyway engineer\'s note from 1996',
    room: 'mine-office',
    where: 'The mine office, act 2: pinned over the desk. It shows the pump and the lift.',
    act: 2,
    slot: 13,
    check: 'A map of the workings.',
    paper: 'notebook',
    pages: [
      title,
      {
        kind: 'map',
        heading: 'ARKLAY SILVER MINE No.2',
        sub: 'Plan of workings, 1987',
        labels: [
          ['ADIT', 24, 78],
          ['TO QUARRY', 18, 102],
          ['OFFICE', 63, 48],
          ['LIFT', 168, 44],
          ['TO SUMMIT', 168, 56],
          ['PUMP', 194, 70],
          ['JUNCTION', 156, 108],
          ['No.3 LEVEL', 44, 132],
          ['FLOODED', 100, 157],
          ['OLD WINZE', 130, 186],
        ],
        notes: [
          ['Pump drains No.3.', 20, 206],
          ['Lift runs on line power.', 20, 222],
        ],
        thumb: [70, 160],
      },
      {
        kind: 'text',
        paper: 'letter',
        text: `
^ARKLAY MINING CO.
^NOTICE TO ALL SHIFTS

No.3 level floods to the roof in a day if the pump stops. Nobody goes below the junction without the pump running.

The winze stays roped.
>J. Talley, 1987

1996: the pump and the lift now run off the Skyway's line. No station power, no lift.
`,
      },
    ],
  },
  {
    id: 'keeper-log',
    title: 'Lower station log',
    subtitle: 'Arklay Skyway',
    writer: 'Pete, the keeper of the gondola\'s lower station',
    room: 'lower-station',
    where: 'The lower station, act 3: on his desk. The estate gardener came up the day before.',
    act: 3,
    slot: 9,
    check: "The keeper's log.",
    paper: 'ledger',
    pages: [
      title,
      {
        kind: 'text',
        text: `
^22 JULY
0800 Line open. Wind light.
1230 Sheriff's car in the lot again. Still asking after the couple from Ohio.
1700 Line closed. 41 riders.
`,
      },
      {
        kind: 'text',
        text: `
^23 JULY
0800 Line open. County says the trails are closed. Company says we run. We run.
0930 Two crates up in 2 for Camp 4. Company tape, cold box.
1610 The estate gardener came up for supplies again. Said the dogs have got out. Scratching at his arm the whole time.
1800 Line closed. Storm.
`,
      },
      {
        kind: 'text',
        text: `
^24 JULY
0305 Woman from the lot, bitten by a dog. Bad. Phone's dead. Bandaged her, sent her up in 4 to Hal. He's got the radio.
0320 Blood all over the counter. 4 is crawling up the line.
0340 Something at the window.
`,
      },
      {
        kind: 'text',
        shaky: 1,
        text: `
0344 Not a dog. It's a man. He won't answer me.
0346 Two of them. The glass is going.
0347 The machine room has a bolt. Going
`,
      },
    ],
  },
  {
    id: 'gardener-diary',
    title: "Gardener's diary",
    writer: "The Spencer estate's gardener",
    room: 'lodge',
    where: "The gardener's lodge, act 3: on the table by the lamp. The itching, day by day.",
    act: 3,
    slot: 5,
    check: 'His diary. Day after day',
    paper: 'notebook',
    notes: [
      "The last line is the scene's own (lodge/scene.py), and it all but quotes RE1's Keeper's Diary. Keep the nod or reword it in both places.",
    ],
    pages: [
      title,
      {
        kind: 'text',
        text: `
July 20
Scott hasn't come to see to the dogs in three days. Nobody answers at the house.

Fed them myself. A big one went for me through the wire and caught my wrist.

Iodine. The dogs are wrong this summer. Thin, and they stink.
`,
      },
      {
        kind: 'text',
        text: `
July 21

Kennel gate open this morning. Every chain snapped. The dogs are gone up the mountain.

Wrist is red and hot. It itches under the bandage.

Planted out the late beans anyway. Blight on the roses by the south wall.
`,
      },
      {
        kind: 'text',
        text: `
July 22

Itches. Couldn't sleep for it. Scratched it open in the night. The skin comes away under my nails.

Everything in the seed trays has died. The water's fine. I don't understand it.
`,
      },
      {
        kind: 'text',
        shaky: 1,
        text: `
July 23

Walked up to the Skyway for supplies. Told Pete the dogs are loose. He looked at my arm and asked was I all right.

I'm all right.

Bandages, lamp oil, tins. So hungry. Ate two tins on the walk back. Still hungry.
`,
      },
      {
        kind: 'text',
        shaky: 2,
        text: `
july 24

hot. cold. hot.

cant sleep. scratch. scratch.

itchy. itchy. scott came. ugly face so i killed him. tasty
`,
      },
    ],
  },
  {
    id: 'foreman-letters',
    title: "Foreman's letters",
    writer: 'Umbrella to Earl Mathis, foreman of Camp 4, and his own last letter, never sent',
    room: 'office',
    where: "The foreman's office, act 2: on his desk. Umbrella paid for the gondola.",
    act: 2,
    slot: 6,
    check: 'Letters on Umbrella letterhead.',
    paper: 'letter',
    notes: [
      "The last letter makes Umbrella's split crate the start of the camp's sickness. That is a story call: keep it, or cut it back to the foreman's suspicion.",
    ],
    pages: [
      title,
      {
        kind: 'text',
        letterhead: 'umbrella',
        text: `
April 2, 1996

Mr. Earl Mathis
Foreman, Camp 4
Arklay Timber Co.

Dear Mr. Mathis,
The gondola contract is approved in full. Umbrella will meet the cost of the upper station and the line.
`,
      },
      {
        kind: 'text',
        text: `
The Skyway will carry your camp's freight at no charge.

In return, Camp 4 will take in company freight at the upper station and hold it in your cold store until our people collect it. Your crew is not to handle the contents.

We look forward to a long and quiet partnership.
>M. Prescott
>Facilities Management
`,
      },
      {
        kind: 'text',
        letterhead: 'umbrella',
        text: `
July 9, 1998
Mr. Mathis,
The samples are to be kept cold and are not to be opened. A damaged crate is to be set aside, sealed, for our people.

Discretion is a condition of the contract.
>M. Prescott
`,
      },
      {
        kind: 'text',
        letterhead: 'umbrella',
        text: `
July 20, 1998
Mr. Mathis,
We have your letter of the 16th. Illness among your crew is a matter for your own doctor. It has no connection with our freight.

Collection is delayed. Keep the cold store locked.
>M. Prescott
`,
      },
      {
        kind: 'text',
        letterhead: 'umbrella',
        text: `
^COLD FREIGHT
For: Camp 4, cold store
Via: Arklay Skyway, car 2
Date: July 23, 1998
Crates: 2, SAMPLES

Keep below 40 F. Do not open.
Received at the upper station:
>Hal
`,
      },
      {
        kind: 'text',
        shaky: 1,
        text: `
July 23. Not sent.

Prescott,
There is no doctor. I have three men who can stand.

The crate that split on the 14th. Gus sealed it up with his bare hands like you said. Gus was first.

I never told the county. I'm telling whoever reads this.
>E. Mathis
`,
      },
    ],
  },
  {
    id: 'walt-log',
    title: 'Lookout log',
    subtitle: 'Tower 6',
    writer: 'Walt, the fire lookout, in capitals',
    room: 'tower-top',
    where: "The lookout tower's top, act 2: on the desk. The night Bravo came down.",
    act: 2,
    slot: 10,
    check: 'The log. 01.20',
    paper: 'ledger',
    pages: [
      title,
      {
        kind: 'text',
        text: `
^JULY 23 1998
08.00 ON DUTY. VIS 40 MI. WIND SW 5.
11.30 HAZE NW. NO SMOKE.
14.00 ALL QUIET. PEREGRINE ON THE RAIL AGAIN.
16.40 DOGS BAYING DOWN BY THE ROAD. A PACK, 5 OR 6.
19.00 THUNDERHEADS BUILDING W.
`,
      },
      {
        kind: 'text',
        text: `
21.50 LIGHTNING. NO STRIKES SEEN. ON THE STOOL.
22.30 HELICOPTER OVER, LOW, HEADED NE. ENGINE DIDN'T SOUND RIGHT.
23.15 RAIN. HEAVY.
`,
      },
      {
        kind: 'text',
        text: `
^JULY 24
01.20 SMOKE SIGHTED, NE, BRG 047. AIRCRAFT? RADIOED. NO ANSWER.
01.45 RADIOED AGAIN. NOTHING.
02.10 DOWN TO THE TANK FOR WATER. DOG OUT OF THE DARK. GOT MY CALF. MADE THE STAIRS.
03.00 DOGS AT THE FOOT OF THE TOWER.
`,
      },
      {
        kind: 'text',
        shaky: 1,
        text: `
04.40 BURNING UP. CANT STOP SCRATCHING.
05.15 RADIO DEAD.
05.30 I CAN HEAR THEM.

THEY'RE ON THE STAIRS.
`,
      },
    ],
  },
  {
    id: 'quarantine',
    title: 'Quarantine notice',
    writer: "Camp 4's foreman, nailed to a spruce on the logging road",
    room: 'logging-road',
    where: 'The logging road, act 2: torn on a tree by the verge. Whatever was in the camp got out.',
    act: 2,
    slot: 4,
    check: 'QUARANTINE.',
    paper: 'letter',
    pages: [
      title,
      {
        kind: 'notice',
        heading: 'QUARANTINE',
        lines: ['SICKNESS IN CAMP 4', 'NO ENTRY', 'TURN BACK', '', 'ANYONE BITTEN BY A DOG', 'OR BY A MAN OF THIS CAMP', 'MUST NOT'],
        tearAt: 168,
      },
    ],
  },
  {
    id: 'rosters',
    title: 'Quarry rosters',
    writer: 'Ray Teague, the quarry foreman',
    room: 'quarry-office',
    where: 'The quarry office, act 2: on the board over the desk. The week going red.',
    act: 2,
    slot: 3,
    check: 'The shift rosters.',
    paper: 'ledger',
    pages: [
      title,
      {
        kind: 'roster',
        company: 'ARKLAY GRANITE CO.',
        heading: 'DAY SHIFT, WEEK OF JULY 20',
        rows: [
          { name: 'D. BRODY', days: ['in', 'in', 'in', 'in', 'in'] },
          { name: 'R. KOWALSKI', days: ['in', 'sick', 'sick', 'sick', 'sick'], struck: true },
          { name: 'E. FINCH', days: ['in', 'in', 'sick', 'sick', 'sick'], struck: true },
          { name: 'T. RUIZ', days: ['in', 'in', 'in', 'sick', 'sick'], struck: true },
          { name: 'P. LINDQVIST', days: ['in', 'in', 'sick', 'sick', 'sick'], struck: true },
          { name: 'C. HAINES', days: ['in', 'in', 'in', 'in', 'sick'], struck: true },
          { name: 'J. TALBOT', days: ['in', 'in', 'in', 'sick', 'sick'], struck: true },
          { name: 'L. BARRETT', days: ['in', 'in', 'in', 'in', 'in'] },
        ],
        foot: 'FRI: 2 MEN. SHUT THE CUT.',
      },
      {
        kind: 'roster',
        company: 'ARKLAY GRANITE CO.',
        heading: 'NIGHTS, WEEK OF JULY 20',
        rows: [
          { name: 'H. DORSEY', days: ['in', 'in', 'sick', 'sick', 'sick'], struck: true },
          { name: 'E. PRUITT', days: ['in', 'sick', 'sick', 'sick', 'sick'], struck: true },
          { name: 'W. CARLIN', days: ['in', 'in', 'in', 'sick', 'sick'], struck: true },
          { name: 'B. YATES', days: ['in', 'in', 'in', 'in', 'sick'], struck: true },
          { name: 'G. MARSH', days: ['in', 'in', 'sick', 'sick', 'sick'], struck: true },
          { name: 'A. VOSS', days: ['in', 'in', 'in', 'in', 'none'] },
        ],
        foot: 'NO NIGHTS. NOBODY LEFT.',
      },
      {
        kind: 'text',
        paper: 'notebook',
        text: `
July 23
No night shift. There's nobody left. Go home.

Anybody bitten, by a dog or a man, goes to the hospital in town. Not home.

Last one out locks the hut. My key's on me. Hal at the Skyway has the spare.
>R. Teague
`,
      },
    ],
  },
];
