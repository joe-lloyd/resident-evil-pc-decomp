// Rebecca's music: which piece plays where, as data. The research and the
// way we make it are in docs/REBECCA_MUSIC.md; the sketches are in
// tools/rebecca/music/.
//
// RE1 picks a room's music from a table: a group of up to three WAV channels,
// each switched on or off by the room's music state, which scripts can change
// (SoundSystem.cpp update_room_bgm). A room in the same group as the last one
// keeps the music going through the door. So a cue below is one group: an
// area theme whose channels change with what she has done, such as the
// generator hum joining once the power is on.
import type { Plan } from './plan.ts';
import type { Ambience } from '../sound/ambience.ts';

/**
 * - new: we write it.
 * - reuse: RE1's own track, played from the player's own files.
 * - ambience: no music, only the place's own sound: its channels are loops.
 */
export type CueKind = 'new' | 'reuse' | 'ambience';

/**
 * A step of day/events.ts that switches a channel as it happens: the room
 * script that does the step sets the music state of every room of the cue
 * (opcode 0x37), and starts or stops the channel at once if she is in one.
 */
export type Switched = { readonly on: string } | { readonly off: string };

/**
 * One of a cue's up to three WAV channels: a layer that rooms or steps switch
 * on and off. It plays a sketch's render, or a loop made by code
 * (sound/ambience.ts), or nothing yet. Every ambient sound of a room is one
 * channel of its cue, so one owner per sound (docs/REBECCA_SOUND.md).
 */
export type Channel = {
  readonly what: string;
  /** The cue's places it plays in; all of them when absent. */
  readonly in?: readonly string[];
  /** Off until a step, or on until one. */
  readonly switched?: Switched;
} & (
  | {
      /** The sketch in tools/rebecca/music/sketches that plays it, if there is one. */
      readonly sketch?: string;
      /** Its render's loudness in dB RMS (music/ps1.ts): RE1's tracks measure -21 to -26, so -24 when absent. A layer under a theme sits lower. */
      readonly level?: number;
      readonly loop?: undefined;
    }
  | {
      /** The loop that plays it, levelled under the music by ambience.ts. */
      readonly loop: Ambience;
      readonly sketch?: undefined;
      readonly level?: undefined;
    }
);

/**
 * A cue that takes over other places' music for a while, as their row's
 * second group: from the mine taking her gear on her first step into the
 * gallery (day/gear.ts), until she walks into one of `until`.
 */
export interface Takeover {
  readonly places: readonly string[];
  readonly from: 'gear-lost';
  readonly until: readonly string[];
}

export interface Cue {
  readonly id: string;
  readonly title: string;
  readonly kind: CueKind;
  /** The plan's places it plays in. Empty for a cue that only a cutscene or a script starts. */
  readonly places: readonly string[];
  /** The cutscenes (todo.ts) it scores. */
  readonly cutscenes: readonly string[];
  readonly mood: string;
  readonly sound: string;
  /** Up to three channels, as RE1's table allows. A layer that never switches is in its channel's sketch. */
  readonly channels: readonly Channel[];
  readonly takesOver?: Takeover;
  /** For reuse: RE1's file under sound/. */
  readonly file?: string;
}

/** RE1 plays up to three channels per room (SoundSystem.cpp, update_room_bgm). */
export const CHANNELS = 3;

export const CUES: readonly Cue[] = [
  {
    id: 'dawn', title: 'Morning after', kind: 'new', places: ['ridge', 'trail'], cutscenes: ['cut-opening'],
    mood: 'Cold and still. She has just left Billy, and the day has not started yet.',
    sound: 'A held minor chord on a soft string pad, a few harp notes, wind.',
    channels: [{ what: 'the chord, the harp and the wind', sketch: 'dawn' }],
  },
  {
    id: 'station', title: 'The station', kind: 'new', places: ['yard', 'woods', 'bridge', 'platform', 'shed'], cutscenes: ['cut-dog'],
    mood: 'The hub she keeps coming back to: uneasy, never resolving, quiet enough to bear on the tenth visit. It cuts out when the first dog comes.',
    sound: 'Low piano notes far apart, bowed vibraphone chords, wind, a far glass note.',
    channels: [
      { what: 'piano, bowed chords and wind', sketch: 'yard' },
      { what: 'the generator hum, once the power is on', sketch: 'station-hum', switched: { on: 'generator-on' }, level: -34 },
      // The theme has the wind, so the woods' loop is only the leaves and the birds.
      { what: 'the forest', loop: 'forest', in: ['woods'] },
    ],
  },
  {
    id: 'partner', title: 'The partner', kind: 'new', places: [], cutscenes: ['cut-partner', 'cut-den'],
    mood: "The ranger's partner's theme: tired, determined, a short phrase that comes back each time she turns up and in the credits.",
    sound: 'A recorder or ocarina phrase over low strings.',
    channels: [{ what: 'the phrase over the strings', sketch: 'partner' }],
  },
  {
    id: 'hal', title: 'Hal', kind: 'new', places: [], cutscenes: ['cut-phone', 'cut-hal'],
    mood: 'A kind, worn-out man. Heard first under the phone call, then in full when he dies on the ore cart.',
    sound: 'Upright piano, a harmonica held back, a low drone.',
    channels: [{ what: 'the piano, the harmonica and the drone', sketch: 'hal' }],
  },
  {
    id: 'camp', title: 'Logging Camp 4', kind: 'new',
    places: ['logging-road', 'camp-gate', 'camp-yard', 'bunkhouse', 'mess', 'depot', 'workshop', 'sawmill', 'pond', 'flume'], cutscenes: [],
    mood: 'Somewhere people worked until last week. Mechanical and tense, a slow beat like machinery left running.',
    sound: 'Muted metal hits, a low ostinato, slit drum, a far saw.',
    channels: [
      { what: 'the theme', sketch: 'camp' },
      { what: 'the mill turning, once the race fills', sketch: 'camp-mill', in: ['camp-yard', 'sawmill', 'pond', 'flume'], switched: { on: 'mill-race' }, level: -30 },
      { what: 'water', sketch: 'camp-water', in: ['pond'], level: -32 },
    ],
  },
  {
    id: 'road', title: 'The forestry road', kind: 'new',
    places: ['road', 'washout', 'generator', 'tower-foot', 'tower-stairs', 'tower-top', 'switch', 'line-track'], cutscenes: ['cut-tower'],
    mood: 'Open and exposed. Higher up the tower the wind takes over.',
    sound: 'High bowed psaltery, a low pedal note, wind.',
    channels: [
      { what: 'the theme', sketch: 'road' },
      { what: 'wind, louder up the tower', sketch: 'road-wind', in: ['tower-stairs', 'tower-top'], level: -28 },
      { what: 'the line humming, once the breakers close', sketch: 'road-line', in: ['switch', 'line-track'], switched: { on: 'line-on' }, level: -32 },
    ],
  },
  {
    id: 'quarry', title: 'The quarry', kind: 'new', places: ['east-path', 'cottage', 'quarry', 'quarry-office'], cutscenes: [],
    mood: 'Dry and hard. The quarry rosters going red: everyone here got sick.',
    sound: 'Anvil and brake drum far off, a low synth drone, sparse timpani.',
    channels: [
      { what: 'the theme', sketch: 'quarry' },
      { what: 'the wind in the pit', sketch: 'quarry-wind', in: ['quarry'], level: -30 },
    ],
  },
  {
    id: 'mine', title: 'The silver mine', kind: 'new',
    places: ['mine-entrance', 'tunnel', 'junction', 'gallery', 'mine-lift'], cutscenes: [],
    mood: 'Close, wet and dark. Almost not music: a drone she stops noticing until it changes.',
    sound: 'A low drone, drips, a bowed glass note now and then.',
    channels: [
      { what: 'the drone, the drips and the far bowed note', sketch: 'mine' },
      { what: 'the water, until the pump drains it', sketch: 'mine-water', in: ['tunnel', 'junction'], switched: { off: 'drain' }, level: -31 },
      // The theme has the drips and channel 1 the water, so the loop is the air and the timber.
      { what: 'the air underground and the timber', loop: 'mine', in: ['tunnel', 'junction', 'gallery', 'mine-lift'] },
    ],
  },
  {
    id: 'chase', title: 'Unarmed', kind: 'new', places: [], cutscenes: ['cut-mine-collapse', 'cut-mine-chase'],
    mood: 'She has lost her gear and something is coming. The only fast piece in the game. A script switches the mine rooms to it once the floor gives way.',
    sound: 'A driving low ostinato, timpani, metal hits, a bowed cluster above.',
    channels: [{ what: 'the ostinato, the timpani, the metal and the cluster', sketch: 'chase' }],
    // The floor gives way in the gallery; the chase runs until she is out of
    // the mine, at the quarry or up the lift at the summit. The owner has
    // still to settle this.
    takesOver: { places: ['mine-entrance', 'tunnel', 'junction', 'gallery', 'mine-lift'], from: 'gear-lost', until: ['quarry', 'summit-trail'] },
  },
  {
    id: 'summit', title: 'The summit', kind: 'new', places: ['summit-trail', 'weather', 'mast'], cutscenes: [],
    mood: 'Thin air and radio static. Lonely, the highest point of her day.',
    sound: 'Wineglass and handchimes, high wind, static.',
    channels: [
      { what: 'the theme and the high wind', sketch: 'summit' },
      { what: 'radio static near the mast', sketch: 'summit-static', in: ['mast'], level: -33 },
    ],
  },
  {
    id: 'skyway', title: 'The line down', kind: 'new', places: ['car', 'pylon'], cutscenes: ['cut-gondola', 'cut-pylon'],
    mood: 'Relief that it moves, then dread when it stops.',
    sound: 'The cable and the bullwheel as rhythm, low strings rising.',
    channels: [
      { what: 'the strings over the cable', sketch: 'skyway' },
      { what: 'the gale round the car and the pylon', loop: 'gale' },
    ],
  },
  {
    id: 'valley', title: 'The valley at dusk', kind: 'new', places: ['valley-path', 'lower-yard', 'lower-station', 'creek'], cutscenes: [],
    mood: 'Dusk and grief. Bravo came down here last night.',
    sound: 'Steinway in the low middle, a harp, the creek.',
    channels: [
      { what: 'the theme', sketch: 'valley' },
      { what: 'the creek', sketch: 'valley-creek', in: ['creek'], level: -30 },
      { what: 'dusk: crickets, a breeze, a bird settling', loop: 'dusk', in: ['valley-path', 'lower-yard', 'creek'] },
    ],
  },
  {
    id: 'quiet', title: 'Only the room', kind: 'ambience', places: ['den', 'crash'], cutscenes: ['cut-kevin'],
    mood: 'The places that should be heard in silence: the ranger in the hollow, Kevin at the controls.',
    sound: 'Wind, a creak. No music.',
    channels: [
      { what: 'the forest round the hollow', loop: 'forest', in: ['den'] },
      { what: 'dusk round the crash', loop: 'dusk', in: ['crash'] },
    ],
  },
  {
    id: 'estate', title: 'The grounds', kind: 'new', places: ['estate-wall', 'kennels', 'back-garden', 'garden-shed'], cutscenes: [],
    mood: 'The mansion is close. The music starts to sound like RE1\'s own, so she walks into the game the player knows.',
    sound: 'Pipe organ, quiet; low piano; dogs far off.',
    // VCSL has no dog, and the night loop has none yet: the dogs far off are still to make.
    channels: [
      { what: 'the organ and the piano', sketch: 'estate' },
      { what: 'the night: crickets, the wind in the hedges, an owl', loop: 'night', in: ['estate-wall', 'kennels', 'back-garden'] },
    ],
  },
  {
    id: 'underneath', title: 'Under the house', kind: 'ambience', places: ['cellar', 'wine', 'crawl'], cutscenes: [],
    mood: 'Dark and close, under the floor of a house she hasn\'t seen. Almost silent.',
    sound: 'Drips, boards above her, her own breathing in the crawl.',
    channels: [{ what: 'drips and the boards of the house above', loop: 'cellar' }],
  },
  {
    id: 'save', title: "RE1's save room", kind: 'reuse',
    places: ['cabin', 'office', 'booth', 'mine-office', 'lodge', 'save'], cutscenes: ['cut-sleep', 'cut-chris'],
    mood: 'The theme every player knows, in every room with a typewriter (saves.ts): safe for a minute. In the mansion it fades as she falls asleep, and the footsteps are Chris.',
    sound: "RE1's own save room music, from the player's own files.",
    channels: [{ what: 'the save room theme' }],
    file: 'Bgm_31',
  },
  {
    id: 'credits', title: 'Her credits', kind: 'new', places: [], cutscenes: ['cut-credits'],
    mood: 'The day in one piece: the dawn chord, the station, the partner\'s phrase, Hal\'s piano, ending quietly on the dawn chord.',
    sound: 'Everything above, in order, about three minutes.',
    channels: [{ what: 'the piece', sketch: 'credits' }],
  },
];

/** Every sketch a cue's channel names. */
export const SKETCHES: readonly string[] = [...new Set(CUES.flatMap((c) => c.channels.flatMap((ch) => (ch.sketch ? [ch.sketch] : []))))];

/** Everything wrong with the music against the plan and the cutscene list; empty when they fit. */
export function checkMusic(plan: Plan, cutscenes: readonly string[]): string[] {
  const errors: string[] = [];
  const placeCue = new Map<string, string>();
  const sceneCue = new Map<string, string>();
  const ids = new Set<string>();
  for (const c of CUES) {
    if (ids.has(c.id)) errors.push(`cue ${c.id} is listed twice`);
    ids.add(c.id);
    if (c.channels.length < 1 || c.channels.length > CHANNELS) errors.push(`${c.id} has ${c.channels.length} channels; RE1 plays 1 to ${CHANNELS}`);
    if (c.places.length === 0 && c.cutscenes.length === 0) errors.push(`${c.id} plays nowhere`);
    if (c.kind === 'reuse' && !c.file) errors.push(`${c.id} reuses RE1's music but names no file`);
    for (const ch of c.channels) {
      for (const p of ch.in ?? []) if (!c.places.includes(p)) errors.push(`${c.id}: ${ch.what} plays in ${p}, which is not one of its places`);
    }
    // One step per cue: a step's script then sets each room's whole state byte without asking what else has happened.
    const steps = new Set(c.channels.flatMap((ch) => (ch.switched ? ['on' in ch.switched ? ch.switched.on : ch.switched.off] : [])));
    if (steps.size > 1) errors.push(`${c.id}: its channels switch at ${[...steps].join(' and ')}; one step per cue`);
    if (c.takesOver) {
      const owners = new Set(c.takesOver.places.map((p) => CUES.find((o) => o.places.includes(p))?.id));
      if (owners.size !== 1 || owners.has(undefined)) errors.push(`${c.id} takes over places of ${owners.size} cues; one cue's, as a second group in their rows`);
      for (const p of c.takesOver.until) if (!plan.places.some((x) => x.id === p)) errors.push(`${c.id} ends in ${p}, which is not in the plan`);
    }
    for (const p of c.places) {
      if (!plan.places.some((x) => x.id === p)) errors.push(`${c.id} plays in ${p}, which is not in the plan`);
      if (placeCue.has(p)) errors.push(`${p} has two cues: ${placeCue.get(p)} and ${c.id}`);
      placeCue.set(p, c.id);
    }
    for (const s of c.cutscenes) {
      if (!cutscenes.includes(s)) errors.push(`${c.id} scores ${s}, which is not a cutscene`);
      if (sceneCue.has(s)) errors.push(`${s} has two cues: ${sceneCue.get(s)} and ${c.id}`);
      sceneCue.set(s, c.id);
    }
  }
  for (const p of plan.places) if (!placeCue.has(p.id)) errors.push(`${p.id} has no music decided`);
  for (const s of cutscenes) if (!sceneCue.has(s)) errors.push(`cutscene ${s} has no music decided`);
  return errors;
}
