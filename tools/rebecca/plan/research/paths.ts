// Research, not the plan: the small path places that would sit between the
// day's big rooms, so getting from one to the next is a walk through
// somewhere. Each is narrow and irregular, one or two cameras, with one
// thing in it worth seeing. Nothing reads this but the map research.
//
// A path splits one of the plan's links: `between` names its two ends, and
// the path takes the link's place on the map.
//
// Decided 2026-10-14: no new rooms. A path is built into `host`, the
// neighbour with space to grow toward the other (floors must stay within
// 0.6-19 m, as every RE1 room does); a path with no host is dropped, its
// neighbours being full already.

export interface PathPlace {
  readonly id: string;
  readonly name: string;
  readonly between: readonly [string, string];
  /** Its shape on the map: a winding trail, a ledge, a lane between walls, a slope. */
  readonly shape: 'trail' | 'ledge' | 'lane' | 'slope';
  /** Roughly how long the walk through it is, in metres. */
  readonly length: number;
  /** What's there. */
  readonly beat: string;
  /** The room it is built into, or undefined when it is dropped. */
  readonly host?: string;
}

export const PATHS: readonly PathPlace[] = [
  { id: 'fire-road', name: 'The fire road bend', between: ['yard', 'road'], shape: 'trail', length: 40, beat: "The truck's tyre tracks swing wide through mud; a ranger's glove, the fingers chewed." },
  { id: 'skid-trail', name: 'The skid trail', between: ['woods', 'logging-road'], shape: 'trail', length: 45, beat: 'A rutted log-skidding track through stumps; drag marks of something heavier than a log.' },
  { id: 'cliff-path', name: 'The cliff path', between: ['platform', 'east-path'], shape: 'ledge', length: 60, beat: 'A narrow ledge along the gorge with a rope rail; one stake pulled out and the rope hanging over the drop.', host: 'platform' },
  { id: 'lookout-trail', name: 'The lookout trail', between: ['washout', 'tower-foot'], shape: 'trail', length: 45, beat: 'Switchbacks up through firs to the tower; a dropped lookout logbook page pinned by a stone.' },
  { id: 'log-deck', name: 'The log deck', between: ['camp-yard', 'sawmill'], shape: 'lane', length: 30, beat: 'A lane between stacked logs; one stack has rolled, and boots stick out from under it.' },
  { id: 'mill-race', name: 'The mill race', between: ['sawmill', 'pond'], shape: 'trail', length: 30, beat: 'A plank walk along the race; the water runs dark and something turns in it.', host: 'sawmill' },
  { id: 'spoil-heap', name: 'The spoil heap', between: ['east-path', 'quarry'], shape: 'slope', length: 35, beat: "Loose quarry tailings to climb; a lunch tin and a hard hat halfway up." },
  { id: 'ore-track', name: 'The ore track', between: ['quarry', 'mine-entrance'], shape: 'ledge', length: 50, beat: 'Rusted cart rails on a trestle over a ravine; a cart tipped on its side, web strung from it.', host: 'mine-entrance' },
  { id: 'ridge-walk', name: 'The ridge walk', between: ['summit-trail', 'mast'], shape: 'ledge', length: 70, beat: 'A bare knife-edge in the wind between cairns; crows ride the updraught level with her.', host: 'mast' },
  { id: 'burnt-swath', name: 'The burnt swath', between: ['valley-path', 'crash'], shape: 'trail', length: 40, beat: "Trees snapped off where the helicopter came down through them; a rotor blade sunk in a trunk.", host: 'crash' },
  { id: 'station-lane', name: 'The station lane', between: ['valley-path', 'lower-yard'], shape: 'lane', length: 30, beat: "A gravel lane under dripping alders; a child's shoe on a fence post where someone put it.", host: 'lower-yard' },
  { id: 'wall-path', name: 'The wall path', between: ['creek', 'estate-wall'], shape: 'trail', length: 45, beat: "A path along the estate wall, broken glass set in its top; claw marks down the stone.", host: 'estate-wall' },
];
