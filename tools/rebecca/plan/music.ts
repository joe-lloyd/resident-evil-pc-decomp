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

/**
 * - new: we write it.
 * - reuse: RE1's own track, played from the player's own files.
 * - ambience: no music, only the place's own sound.
 */
export type CueKind = 'new' | 'reuse' | 'ambience';

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
  /** Up to three channels, as RE1's table allows. */
  readonly channels: readonly string[];
  /** The sketch in tools/rebecca/music/sketches, if there is one. */
  readonly sketch?: string;
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
    channels: ['the chord and the harp', 'wind'],
  },
  {
    id: 'station', title: 'The station', kind: 'new', places: ['yard', 'woods', 'bridge', 'platform', 'shed'], cutscenes: ['cut-dog'],
    mood: 'The hub she keeps coming back to: uneasy, never resolving, quiet enough to bear on the tenth visit. It cuts out when the first dog comes.',
    sound: 'Low piano notes far apart, bowed vibraphone chords, wind, a far glass note.',
    channels: ['piano and bowed chords', 'wind', 'the generator hum, once the power is on'],
    sketch: 'yard',
  },
  {
    id: 'safe', title: 'A place to rest', kind: 'new', places: ['cabin'], cutscenes: [],
    mood: 'Her own save-room theme, for every room with a typewriter: safe for a minute, still sad. In the manner of RE1\'s, with our own tune.',
    sound: 'Two or three minor chords held under a slow harp arpeggio, a breathy lead on top.',
    channels: ['the chords and the harp', 'the lead'],
    sketch: 'safe',
  },
  {
    id: 'partner', title: 'The partner', kind: 'new', places: [], cutscenes: ['cut-partner', 'cut-den'],
    mood: "The ranger's partner's theme: tired, determined, a short phrase that comes back each time she turns up and in the credits.",
    sound: 'A recorder or ocarina phrase over low strings.',
    channels: ['the phrase', 'the strings'],
  },
  {
    id: 'hal', title: 'Hal', kind: 'new', places: [], cutscenes: ['cut-phone', 'cut-hal'],
    mood: 'A kind, worn-out man. Heard first under the phone call, then in full when he dies on the ore cart.',
    sound: 'Upright piano, a harmonica held back, a low drone.',
    channels: ['the piano', 'the harmonica', 'the drone'],
  },
  {
    id: 'camp', title: 'Logging Camp 4', kind: 'new',
    places: ['logging-road', 'camp-gate', 'camp-yard', 'bunkhouse', 'office', 'mess', 'depot', 'workshop', 'sawmill', 'pond', 'flume'], cutscenes: [],
    mood: 'Somewhere people worked until last week. Mechanical and tense, a slow beat like machinery left running.',
    sound: 'Muted metal hits, a low ostinato, slit drum, a far saw.',
    channels: ['the theme', 'the mill turning, once the race fills', 'water'],
  },
  {
    id: 'road', title: 'The forestry road', kind: 'new',
    places: ['road', 'washout', 'generator', 'tower-foot', 'tower-stairs', 'tower-top', 'switch', 'line-track'], cutscenes: ['cut-tower'],
    mood: 'Open and exposed. Higher up the tower the wind takes over.',
    sound: 'High bowed psaltery, a low pedal note, wind.',
    channels: ['the theme', 'wind, louder up the tower', 'the line humming, once the breakers close'],
  },
  {
    id: 'quarry', title: 'The quarry', kind: 'new', places: ['east-path', 'cottage', 'quarry', 'quarry-office'], cutscenes: [],
    mood: 'Dry and hard. The quarry rosters going red: everyone here got sick.',
    sound: 'Anvil and brake drum far off, a low synth drone, sparse timpani.',
    channels: ['the theme', 'the wind in the pit'],
  },
  {
    id: 'mine', title: 'The silver mine', kind: 'new',
    places: ['mine-entrance', 'tunnel', 'mine-office', 'junction', 'gallery', 'mine-lift'], cutscenes: [],
    mood: 'Close, wet and dark. Almost not music: a drone she stops noticing until it changes.',
    sound: 'A low drone, drips, a bowed glass note now and then.',
    channels: ['the drone', 'the water, until the pump drains it', 'the far bowed note'],
  },
  {
    id: 'chase', title: 'Unarmed', kind: 'new', places: [], cutscenes: ['cut-mine-collapse', 'cut-mine-chase'],
    mood: 'She has lost her gear and something is coming. The only fast piece in the game. A script switches the mine rooms to it once the floor gives way.',
    sound: 'A driving low ostinato, timpani, metal hits, a bowed cluster above.',
    channels: ['the ostinato and timpani', 'the metal and the cluster'],
    sketch: 'chase',
  },
  {
    id: 'summit', title: 'The summit', kind: 'new', places: ['summit-trail', 'weather', 'mast'], cutscenes: [],
    mood: 'Thin air and radio static. Lonely, the highest point of her day.',
    sound: 'Wineglass and handchimes, high wind, static.',
    channels: ['the theme', 'wind', 'radio static near the mast'],
  },
  {
    id: 'skyway', title: 'The line down', kind: 'new', places: ['car', 'pylon'], cutscenes: ['cut-gondola', 'cut-pylon'],
    mood: 'Relief that it moves, then dread when it stops.',
    sound: 'The cable and the bullwheel as rhythm, low strings rising.',
    channels: ['the strings', 'the cable'],
  },
  {
    id: 'valley', title: 'The valley at dusk', kind: 'new', places: ['valley-path', 'lower-yard', 'lower-station', 'creek', 'lodge'], cutscenes: [],
    mood: 'Dusk and grief. Bravo came down here last night.',
    sound: 'Steinway in the low middle, a harp, the creek.',
    channels: ['the theme', 'the creek'],
  },
  {
    id: 'quiet', title: 'Only the room', kind: 'ambience', places: ['den', 'booth', 'crash'], cutscenes: ['cut-kevin'],
    mood: 'The places that should be heard in silence: the ranger in the hollow, the phone ringing in the booth, Kevin at the controls.',
    sound: 'Wind, a creak, the phone. No music.',
    channels: ['the room\'s own sound'],
  },
  {
    id: 'estate', title: 'The grounds', kind: 'new', places: ['estate-wall', 'kennels', 'back-garden', 'garden-shed'], cutscenes: [],
    mood: 'The mansion is close. The music starts to sound like RE1\'s own, so she walks into the game the player knows.',
    sound: 'Pipe organ, quiet; low piano; dogs far off.',
    channels: ['the theme', 'the dogs, until the kennels are quiet'],
  },
  {
    id: 'underneath', title: 'Under the house', kind: 'ambience', places: ['cellar', 'wine', 'crawl'], cutscenes: [],
    mood: 'Dark and close, under the floor of a house she hasn\'t seen. Almost silent.',
    sound: 'Drips, boards above her, her own breathing in the crawl.',
    channels: ['drips', 'the house above'],
  },
  {
    id: 'save', title: "RE1's save room", kind: 'reuse', places: ['save'], cutscenes: ['cut-sleep', 'cut-chris'],
    mood: 'The theme every player knows: she has made it. It fades as she falls asleep, and the footsteps are Chris.',
    sound: "RE1's own save room music, from the player's own files.",
    channels: ['the save room theme'],
    file: 'Bgm_31',
  },
  {
    id: 'credits', title: 'Her credits', kind: 'new', places: [], cutscenes: ['cut-credits'],
    mood: 'The day in one piece: the dawn chord, the station, the partner\'s phrase, Hal\'s piano, ending on her save-room theme.',
    sound: 'Everything above, in order, about three minutes.',
    channels: ['the piece'],
  },
];

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
