// The shape of an act's plan, and the check that it can be played through.
//
// An act is planned as places joined by links, and steps: the things she
// finds, does and learns, each at a place and each needing earlier steps.
// The steps are a puzzle dependency chart (Ron Gilbert's, from Maniac
// Mansion and Monkey Island): drawn as a graph, a long thin chart is a
// corridor and a wide one gives her several things to work on at once.
//
// check() plays the plan the way a player could and reports what would go
// wrong in the game: a step she can never reach, a step at a place its
// needs don't get her to, a find that is never used.

export type Built = 'built' | 'planned';

export interface Place {
  readonly id: string;
  readonly name: string;
  readonly built: Built;
  /** The room's folder under day/, once it has one. */
  readonly room?: string;
  /** Where the place sits on the map, in grid squares. */
  readonly at: readonly [x: number, y: number];
  /** The beat chart: what is there, what moves, what attacks, what it tells. */
  readonly there: string;
  readonly moves: string;
  readonly enemies: string;
  readonly story: string;
}

export type LinkKind = 'door' | 'walk' | 'ladder' | 'ferry';

export interface Link {
  readonly from: string;
  readonly to: string;
  readonly kind: LinkKind;
  /** The step that opens it. An unlocked link is open from the start. */
  readonly opens?: string;
  /** A shortcut: its opening step is on the `from` side, the far side from the way she came. */
  readonly shortcut?: true;
}

export type StepKind = 'find' | 'do' | 'learn' | 'shortcut' | 'goal';

export interface Step {
  readonly id: string;
  readonly label: string;
  readonly at: string;
  readonly kind: StepKind;
  readonly needs: readonly string[];
  readonly built: Built;
  /** Nothing later needs it: a reward, a clue or a setup for a later act. */
  readonly optional?: true;
}

export interface Act {
  readonly title: string;
  readonly start: string;
  readonly places: readonly Place[];
  readonly links: readonly Link[];
  readonly steps: readonly Step[];
}

export interface Report {
  readonly errors: readonly string[];
  readonly warnings: readonly string[];
  /** The order a player taking the first open step each time would play it in. */
  readonly order: readonly string[];
  /** How many steps were open to her before each step of `order`. */
  readonly open: readonly number[];
  /** Each step's column in the chart: the longest chain of needs behind it. */
  readonly depth: ReadonlyMap<string, number>;
}

/** The places she can reach from the start once `done` steps are done. */
export function reachable(act: Act, done: ReadonlySet<string>): Set<string> {
  const seen = new Set([act.start]);
  for (let grew = true; grew; ) {
    grew = false;
    for (const l of act.links) {
      if (l.opens && !done.has(l.opens)) continue;
      for (const [a, b] of [[l.from, l.to], [l.to, l.from]] as const) {
        if (seen.has(a) && !seen.has(b)) {
          seen.add(b);
          grew = true;
        }
      }
    }
  }
  return seen;
}

export function check(act: Act): Report {
  const errors: string[] = [];
  const warnings: string[] = [];
  const places = new Set(act.places.map((p) => p.id));
  const steps = new Map(act.steps.map((s) => [s.id, s]));
  if (steps.size !== act.steps.length) errors.push('two steps share an id');
  if (places.size !== act.places.length) errors.push('two places share an id');
  if (!places.has(act.start)) errors.push(`the start ${act.start} is not a place`);
  for (const s of act.steps) {
    if (!places.has(s.at)) errors.push(`${s.id} is at ${s.at}, which is not a place`);
    for (const n of s.needs) if (!steps.has(n)) errors.push(`${s.id} needs ${n}, which is not a step`);
  }
  for (const l of act.links) {
    for (const end of [l.from, l.to]) if (!places.has(end)) errors.push(`a link goes to ${end}, which is not a place`);
    if (l.opens && !steps.has(l.opens)) errors.push(`the link ${l.from}-${l.to} is opened by ${l.opens}, which is not a step`);
  }
  const goals = act.steps.filter((s) => s.kind === 'goal');
  if (goals.length !== 1) errors.push(`an act has one goal, this one has ${goals.length}`);
  if (errors.length) return { errors, warnings, order: [], open: [], depth: new Map() };

  // Depth, and the needs behind each step, with a loop of needs as an error.
  const depth = new Map<string, number>();
  const behind = new Map<string, Set<string>>();
  const visit = (id: string, path: string[]): number => {
    if (depth.has(id)) return depth.get(id)!;
    if (path.includes(id)) {
      errors.push(`the needs go round in a loop: ${[...path.slice(path.indexOf(id)), id].join(' > ')}`);
      return 0;
    }
    const s = steps.get(id)!;
    const all = new Set<string>();
    let d = 0;
    for (const n of s.needs) {
      d = Math.max(d, visit(n, [...path, id]) + 1);
      all.add(n);
      for (const m of behind.get(n) ?? []) all.add(m);
    }
    depth.set(id, d);
    behind.set(id, all);
    return d;
  };
  for (const s of act.steps) visit(s.id, []);
  if (errors.length) return { errors, warnings, order: [], open: [], depth };

  // A step's needs have to be what gets her to its place, so the chart shows
  // every lock between her and it.
  for (const s of act.steps) {
    if (!reachable(act, behind.get(s.id)!).has(s.at)) {
      errors.push(`${s.id} is at ${s.at}, but what it needs doesn't get her there`);
    }
  }

  // Play it: each time, the first open step in the plan's order.
  const done = new Set<string>();
  const order: string[] = [];
  const open: number[] = [];
  for (;;) {
    const here = reachable(act, done);
    const next = act.steps.filter((s) => !done.has(s.id) && here.has(s.at) && s.needs.every((n) => done.has(n)));
    if (!next.length) break;
    open.push(next.length);
    order.push(next[0]!.id);
    done.add(next[0]!.id);
  }
  for (const s of act.steps) if (!done.has(s.id)) errors.push(`${s.id} can never be done`);

  const needed = new Set(act.steps.flatMap((s) => s.needs).concat(act.links.flatMap((l) => (l.opens ? [l.opens] : []))));
  for (const s of act.steps) {
    if (s.kind !== 'goal' && !s.optional && !needed.has(s.id)) warnings.push(`nothing needs ${s.id}: mark it optional or use it`);
  }
  for (const p of act.places) {
    if (!act.steps.some((s) => s.at === p.id) && !act.links.some((l) => l.from === p.id || l.to === p.id)) {
      warnings.push(`${p.id} is not joined to anything`);
    }
  }
  return { errors, warnings, order, open, depth };
}
