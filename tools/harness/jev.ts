// Jev (TypeSafe System One) for the fuzzy calls in tests: which of a few
// actions to take next, and whether a checkpoint really passed. Jev reads text
// only, so the state goes in as a short JSON summary, never a screenshot.
//
// The key comes from TYPESAFE_API_KEY. In the lab: TYPESAFE_API_KEY=$(ssh vault get typesafe-api-key)

const endpoint = 'https://api.typesafe.ai/v1/systemone';

export interface ChoiceAnswer<K extends string> {
  choice: K;
  probabilities: Record<K, number>;
  confidence: number;
}

function apiKey(): string {
  const key = process.env.TYPESAFE_API_KEY;
  if (!key) throw new Error('TYPESAFE_API_KEY is not set');
  return key;
}

async function ask(state: unknown, questions: Record<string, unknown>): Promise<Record<string, unknown>> {
  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { Authorization: `Bearer ${apiKey()}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: 'jev-latest', state, questions }),
  });
  if (!res.ok) throw new Error(`Jev ${res.status}: ${(await res.text()).slice(0, 200)}`);
  const body: unknown = await res.json();
  if (typeof body !== 'object' || body === null || !('answers' in body)) throw new Error('Jev: no answers');
  const answers = (body as { answers: unknown }).answers;
  if (typeof answers !== 'object' || answers === null) throw new Error('Jev: answers is not an object');
  return answers as Record<string, unknown>;
}

/** Probability that the yes/no question is true for this state. */
export async function noul(state: unknown, question: string, criteria?: { true: string; false: string }): Promise<number> {
  const answers = await ask(state, { q: { type: 'noul', instructions: question, ...(criteria ? { criteria } : {}) } });
  const a = answers.q;
  if (typeof a !== 'object' || a === null || typeof (a as { noul?: unknown }).noul !== 'number') {
    throw new Error('Jev: bad noul answer');
  }
  return (a as { noul: number }).noul;
}

/** Pick one option. `options` maps each key to what it means. */
export async function choice<K extends string>(
  state: unknown,
  question: string,
  options: Record<K, string>,
): Promise<ChoiceAnswer<K>> {
  const answers = await ask(state, { q: { type: 'choice', instructions: question, criteria: options } });
  const a = answers.q;
  if (typeof a !== 'object' || a === null) throw new Error('Jev: bad choice answer');
  const { choice: picked, probabilities, confidence } = a as Record<string, unknown>;
  if (typeof picked !== 'string' || !(picked in options) || typeof confidence !== 'number') {
    throw new Error('Jev: choice outside the options');
  }
  return { choice: picked as K, probabilities: probabilities as Record<K, number>, confidence };
}
