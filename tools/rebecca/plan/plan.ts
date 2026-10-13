// The shape of the game's plan, and the check that it can be played through.
//
// The day is planned as places joined by links, and steps: the things she
// finds, does and learns, each at a place and each needing earlier steps.
// The steps are a puzzle dependency chart (Ron Gilbert's, from Maniac
// Mansion and Monkey Island): drawn as a graph, a long thin chart is a
// corridor and a wide one gives her several things to work on at once.
// Places and steps belong to acts, which only decide how the page groups
// them; the check plays the whole day as one.
//
// check() plays the plan the way a player could and reports what would go
// wrong in the game: a step she can never reach, a step at a place its
// needs don't get her to, a find that is never used.

export type Built = 'built' | 'planned';

export interface ActInfo {
  readonly n: number;
  readonly title: string;
  readonly time: string;
  readonly summary: string;
}

export interface Place {
  readonly id: string;
  readonly name: string;
  readonly act: number;
  readonly built: Built;
  /** The room's folder under day/, once it has one. */
  readonly room?: string;
  /** A room of the original game she passes through, by its file. */
  readonly existing?: string;
  /** Camera angles: the real count once built, the plan's guess before. */
  readonly cameras: number;
  /** Where the place sits on the map, in grid squares. */
  readonly at: readonly [x: number, y: number];
  /** The beat chart: what is there, what moves, what attacks, what it tells. */
  readonly there: string;
  readonly moves: string;
  readonly enemies: string;
  readonly story: string;
}

export type LinkKind = 'door' | 'walk' | 'ladder' | 'ride' | 'lift';

export interface Link {
  readonly from: string;
  readonly to: string;
  readonly kind: LinkKind;
  /** The step that opens it. An unlocked link is open from the start. */
  readonly opens?: string;
  /** A shortcut: its opening step is on the `from` side, the far side from the way she came. */
  readonly shortcut?: true;
}

export type StepKind = 'find' | 'do' | 'learn' | 'shortcut' | 'milestone' | 'goal';

export interface Step {
  readonly id: string;
  readonly label: string;
  readonly act: number;
  readonly at: string;
  readonly kind: StepKind;
  readonly needs: readonly string[];
  readonly built: Built;
  /** Nothing later needs it: a reward, a clue or a shortcut. */
  readonly optional?: true;
}

export interface Plan {
  readonly title: string;
  readonly start: string;
  readonly acts: readonly ActInfo[];
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
}

/** The places she can reach from the start once `done` steps are done. */
export function reachable(plan: Plan, done: ReadonlySet<string>): Set<string> {
  const seen = new Set([plan.start]);
  for (let grew = true; grew; ) {
    grew = false;
    for (const l of plan.links) {
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

export function check(plan: Plan): Report {
  const errors: string[] = [];
  const warnings: string[] = [];
  const places = new Set(plan.places.map((p) => p.id));
  const steps = new Map(plan.steps.map((s) => [s.id, s]));
  const acts = new Set(plan.acts.map((a) => a.n));
  if (steps.size !== plan.steps.length) errors.push('two steps share an id');
  if (places.size !== plan.places.length) errors.push('two places share an id');
  if (!places.has(plan.start)) errors.push(`the start ${plan.start} is not a place`);
  for (const p of plan.places) if (!acts.has(p.act)) errors.push(`${p.id} is in act ${p.act}, which is not an act`);
  for (const s of plan.steps) {
    if (!acts.has(s.act)) errors.push(`${s.id} is in act ${s.act}, which is not an act`);
    if (!places.has(s.at)) errors.push(`${s.id} is at ${s.at}, which is not a place`);
    for (const n of s.needs) if (!steps.has(n)) errors.push(`${s.id} needs ${n}, which is not a step`);
  }
  for (const l of plan.links) {
    for (const end of [l.from, l.to]) if (!places.has(end)) errors.push(`a link goes to ${end}, which is not a place`);
    if (l.opens && !steps.has(l.opens)) errors.push(`the link ${l.from}-${l.to} is opened by ${l.opens}, which is not a step`);
  }
  const goals = plan.steps.filter((s) => s.kind === 'goal');
  if (goals.length !== 1) errors.push(`the day has one goal, this plan has ${goals.length}`);
  if (errors.length) return { errors, warnings, order: [], open: [] };

  // The needs behind each step, with a loop of needs as an error.
  const behind = new Map<string, Set<string>>();
  const visit = (id: string, path: string[]): Set<string> => {
    const known = behind.get(id);
    if (known) return known;
    if (path.includes(id)) {
      errors.push(`the needs go round in a loop: ${[...path.slice(path.indexOf(id)), id].join(' > ')}`);
      return new Set();
    }
    const all = new Set<string>();
    for (const n of steps.get(id)!.needs) {
      all.add(n);
      for (const m of visit(n, [...path, id])) all.add(m);
    }
    behind.set(id, all);
    return all;
  };
  for (const s of plan.steps) visit(s.id, []);
  if (errors.length) return { errors, warnings, order: [], open: [] };

  // A step's needs have to be what gets her to its place, so the chart shows
  // every lock between her and it.
  for (const s of plan.steps) {
    if (!reachable(plan, behind.get(s.id)!).has(s.at)) {
      errors.push(`${s.id} is at ${s.at}, but what it needs doesn't get her there`);
    }
  }

  // Play it: each time, the first open step in the plan's order.
  const done = new Set<string>();
  const order: string[] = [];
  const open: number[] = [];
  for (;;) {
    const here = reachable(plan, done);
    const next = plan.steps.filter((s) => !done.has(s.id) && here.has(s.at) && s.needs.every((n) => done.has(n)));
    if (!next.length) break;
    open.push(next.length);
    order.push(next[0]!.id);
    done.add(next[0]!.id);
  }
  for (const s of plan.steps) if (!done.has(s.id)) errors.push(`${s.id} can never be done`);

  const needed = new Set(plan.steps.flatMap((s) => s.needs).concat(plan.links.flatMap((l) => (l.opens ? [l.opens] : []))));
  for (const s of plan.steps) {
    if (s.kind !== 'goal' && !s.optional && !needed.has(s.id)) warnings.push(`nothing needs ${s.id}: mark it optional or use it`);
  }
  for (const p of plan.places) {
    if (!plan.links.some((l) => l.from === p.id || l.to === p.id)) warnings.push(`${p.id} is not joined to anything`);
  }
  return { errors, warnings, order, open };
}
