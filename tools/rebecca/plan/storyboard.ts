// node tools/rebecca/plan/storyboard.ts <out dir>
// Source tables describe intent. Room scripts and renders show what is built.
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { day } from './day.ts';
import { check, type Place } from './plan.ts';
import { CUTSCENES as REFERENCED, sections, type RoomFacts } from './todo.ts';
import { CUES } from './music.ts';
import { SAVES } from './saves.ts';
import { FIRST_MAP_ITEM, MAP_ITEMS } from './maps.ts';
import { dayRooms } from '../day/rooms.ts';
import { CUTSCENES } from '../day/cutscenes.ts';
import type { Beat } from '../day/cutscene.ts';
import { FOES, FOE_KINDS } from '../day/foes.ts';
import { SUPPLIES, SUPPLY_KINDS } from '../day/supplies.ts';
import { GEAR, LOSS_ROOM } from '../day/gear.ts';
import { EVENTS } from '../day/events.ts';
import { KEY_ITEMS } from '../items/items.ts';
import { DOCUMENTS, type Page } from '../files/documents.ts';
import { mapIn } from '../maps/pickups.ts';

const HERE = dirname(fileURLToPath(import.meta.url));
const DAY = join(HERE, '..', 'day');
const REPO = resolve(HERE, '../../..');
const esc = (s: string) => s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const slugOf = (p: Place) => p.room ?? p.id;
const read = (file: string) => existsSync(file) ? readFileSync(file, 'utf8') : '';

// Only the fields this reader uses cross the JSON boundary.
function object(value: unknown): Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) throw new Error('Expected a room object');
  return Object.fromEntries(Object.entries(value));
}
function rows(value: unknown): Record<string, unknown>[] {
  if (value === undefined) return [];
  if (!Array.isArray(value)) throw new Error('Expected room rows');
  return value.map(object);
}
function text(value: unknown): string {
  if (typeof value !== 'string') throw new Error('Expected room text');
  return value;
}
export function roomEvidence(slug: string) {
  const file = join(DAY, slug, 'renders/room.json');
  const json: Record<string, unknown> = existsSync(file) ? object(JSON.parse(read(file))) : {};
  return {
    doors: rows(json.doors).map((d) => text(d.to)),
    checks: rows(json.checks).map((c) => text(c.text)),
    entry: json.entry == null ? '' : text(json.entry),
    items: rows(json.items).map((i) => text(i.step)),
    spots: rows(json.spots).map((s) => text(s.step)),
  };
}

/** Room messages retain their number and raw text so edits can locate the source. */
export function messages(source: string) {
  return [...source.matchAll(/^(\d+):\s*(.*)$/gm)].map((m) => {
    const raw = m[2] ?? '';
    const decoded = raw.replace(/\\o"?/g, '"').replace(/\\p\{\d+\}/g, '\n\n').replaceAll('\\n', '\n').replace(/\\[a-z](?:\{[^}]*\})?/gi, '').trim();
    return { n: Number(m[1]), raw, text: decoded || 'Timing controls only. No written words in this source message.' };
  });
}

function calls(script: string, name: string): string[][] {
  const clean = script.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/[^\n]*/g, '');
  return [...clean.matchAll(new RegExp(`\\b${name}\\(([^)]*)\\)`, 'g'))].map((m) => (m[1] ?? '').split(',').map((s) => s.trim()));
}
function numeric(s: string | undefined): number {
  if (s === undefined || !/^(?:0x[\da-f]+|\d+)$/i.test(s)) throw new Error(`Expected a numeric script operand: ${s}`);
  return Number(s);
}

export type ItemKind = 'ammo' | 'heal' | 'weapon' | 'key' | 'file' | 'map' | 'ribbons';
export interface StoryItem {
  id: string; room: string; act: number; name: string; kind: ItemKind; qty: number; rounds: number;
  placed: boolean; source: 'supplies' | 'script' | 'key' | 'file' | 'map' | 'start';
  step: string; detail: string;
}
export interface Missing {
  room: string | null; priority: number; title: string; detail: string;
}

function supplyKind(name: string): ItemKind {
  switch (name) {
    case 'clip': return 'ammo';
    case 'greenHerb': case 'redHerb': case 'spray': return 'heal';
    case 'beretta': return 'weapon';
    case 'ribbons': return 'ribbons';
    default: throw new Error(`Unknown supply ${name}`);
  }
}
const supplyName: Record<string, string> = {
  clip: 'Handgun rounds', greenHerb: 'Green herb', redHerb: 'Red herb', spray: 'First aid spray', beretta: 'Beretta', ribbons: 'Ink ribbons',
};

function pickups(place: Place, script: string): StoryItem[] {
  const slug = slugOf(place);
  const actual = new Map(calls(script, 'item_aot_set').map((a) => [numeric(a[17]), { item: numeric(a[5]), qty: numeric(a[6]) }]));
  const result: StoryItem[] = [];
  const claim = (id: number) => {
    for (const [flag, a] of actual) if (a.item === id) { actual.delete(flag); return a; }
    return undefined;
  };
  for (const [index, kind] of (SUPPLIES[slug] ?? []).entries()) {
    const spec = SUPPLY_KINDS[kind];
    const found = claim(spec.id);
    result.push({ id: `supply-${index}`, room: place.id, act: place.act, name: supplyName[kind], kind: supplyKind(kind), qty: spec.qty,
      rounds: kind === 'clip' || kind === 'beretta' ? spec.qty : 0, placed: found !== undefined, source: 'supplies', step: '', detail: `day/supplies.ts · ${kind}${found && found.qty !== spec.qty ? ` · script quantity differs: ${found.qty}` : ''}` });
  }
  for (const key of KEY_ITEMS) {
    const step = day.steps.find((s) => s.id === key.step);
    if (step?.at !== place.id) continue;
    const found = claim(key.id);
    result.push({ id: key.step, room: place.id, act: place.act, name: key.name, kind: 'key', qty: found?.qty ?? 1, rounds: 0,
      placed: found !== undefined, source: 'key', step: key.step, detail: key.description });
  }
  for (const doc of DOCUMENTS.filter((d) => d.room === slug)) {
    const found = claim(0x5f + doc.slot);
    result.push({ id: `file-${doc.id}`, room: place.id, act: place.act, name: doc.title, kind: 'file', qty: 1, rounds: 0,
      placed: found !== undefined, source: 'file', step: doc.id, detail: doc.where });
  }
  for (const [index, map] of MAP_ITEMS.entries()) {
    if (day.steps.find((s) => s.id === map.step)?.at !== place.id) continue;
    const found = claim(FIRST_MAP_ITEM + index);
    result.push({ id: map.id, room: place.id, act: place.act, name: map.name, kind: 'map', qty: 1, rounds: 0,
      placed: found !== undefined, source: 'map', step: map.step, detail: mapIn(slug)?.found ?? '' });
  }
  for (const [flag, a] of actual) {
    const supply = Object.entries(SUPPLY_KINDS).find(([, k]) => k.id === a.item);
    const label = script.match(new RegExp(`\\b${a.item}\\s*\\/\\*\\s*([^*]+)\\*\\/`))?.[1]?.trim();
    result.push({ id: `pickup-${flag}`, room: place.id, act: place.act, name: supply ? supplyName[supply[0]] ?? supply[0] : label ?? `Item ${a.item}`, kind: supply ? supplyKind(supply[0]) : 'key',
      qty: a.qty, rounds: supply && (supply[0] === 'clip' || supply[0] === 'beretta') ? a.qty : 0,
      placed: true, source: 'script', step: '', detail: `Hand-written script · item ${a.item} · flag ${flag}` });
  }
  return result;
}

function startKit(): StoryItem[] {
  const cpp = read(join(REPO, 'src/game/GameStart.cpp'));
  const kit = cpp.match(/\/\/ rebecca items[\s\S]*?ITEM_NONE/);
  if (!kit) throw new Error('Cannot read Rebecca start kit from GameStart.cpp');
  return [...kit[0].matchAll(/ITEM_(BERETTA|CLIP|KNIFE),\s*(\d+)/g)].map((m) => {
    const name = text(m[1]);
    const qty = Number(m[2]);
    return { id: `start-${name.toLowerCase()}`, room: day.start, act: 1, name: name === 'CLIP' ? 'Handgun rounds' : name === 'BERETTA' ? 'Beretta' : 'Knife', kind: name === 'CLIP' ? 'ammo' : 'weapon', qty: qty || 1,
      rounds: name === 'KNIFE' ? 0 : qty, placed: true, source: 'start', step: '', detail: 'Starting kit · src/game/GameStart.cpp' };
  });
}

export function filePage(page: Page): string {
  switch (page.kind) {
    case 'title': return 'Title page';
    case 'text': return page.text;
    case 'calendar': return [page.company, page.town, page.month, `Circled dates: ${page.circled.join(', ')}`, ...Object.entries(page.notes).map(([n, s]) => `${n}: ${s}`), page.scrawl].join('\n');
    case 'map': return [page.heading, page.sub, ...page.labels.map(([s]) => s), ...page.notes.map(([s]) => s)].join('\n');
    case 'notice': return [page.heading, ...page.lines].join('\n');
    case 'roster': return [page.company, page.heading, ...page.rows.map((r) => `${r.name}: ${r.days.join(', ')}${r.struck ? ' · struck out' : ''}`), page.foot ?? ''].join('\n');
    default: { const never: never = page; return never; }
  }
}
export function beatText(beat: Beat): string {
  switch (beat.kind) {
    case 'say': return `${beat.by === 'her' ? 'Rebecca' : beat.by}: ${beat.text}`;
    case 'cut': return `Camera ${beat.camera + 1}`;
    case 'place': return `Place ${beat.who} at ${JSON.stringify(beat.at)}`;
    case 'walk': return `${beat.run ? 'Run' : 'Walk'} ${beat.who} to ${JSON.stringify(beat.to)}`;
    case 'face': return `${beat.who} faces ${JSON.stringify(beat.to)}`;
    case 'anim': return `${beat.who} plays animation ${beat.anim}${beat.loop ? ' in a loop' : ''}`;
    case 'wait': return `Wait ${beat.frames} frames`;
    case 'fade': return `Fade to ${beat.to}`;
    case 'shake': return beat.on ? 'Start camera shake' : 'Stop camera shake';
    case 'gone': return `${beat.who} leaves`;
    case 'give': return `Give ${KEY_ITEMS.find((i) => i.step === beat.item)?.name ?? beat.item}`;
    case 'scd': return beat.lines.join('\n');
    default: { const never: never = beat; return never; }
  }
}

export function buildStoryboard() {
  const scenes = day.places.map((place) => {
    const slug = slugOf(place);
    const stem = place.existing ? join(HERE, '../rooms', place.existing.replace('.RDT', '')) : join(DAY, slug, 'room');
    const script = read(`${stem}.c`);
    const msgs = messages(read(`${stem}.msg.txt`));
    const evidence = roomEvidence(slug);
    const renderDir = join(DAY, slug, 'renders');
    const images = existsSync(renderDir) ? readdirSync(renderDir).filter((f) => /^cam\d+\.png$/.test(f)).sort((a, b) => a.localeCompare(b, undefined, { numeric: true })) : [];
    const spec = dayRooms.find((r) => r.slug === slug);
    const cuts = CUTSCENES.filter((c) => c.room === slug);
    const entry = cuts.some((c) => c.trigger.on === 'enter') ? '' : /message\(128,\s*255,\s*0\)/.test(script) ? msgs.find((m) => m.n === 0)?.text ?? evidence.entry : '';
    const enemies = FOES[slug]?.map(([kind, count]) => ({ kind, count })) ?? Object.entries(FOE_KINDS).flatMap(([kind, k]) => {
      const count = calls(script, 'enemy').filter((a) => Number(a[0]) === k.id).length;
      return count ? [{ kind, count }] : [];
    });
    return { place, slug, script, msgs, evidence, images, entry, enemies, cuts, steps: day.steps.filter((s) => s.at === place.id),
      hour: spec && 'hour' in spec ? spec.hour : place.id === 'ridge' ? 'dawn' : place.act === 1 ? 'morning' : 'night',
      built: Boolean(script && (images.length || place.existing)),
      file: place.existing ?? (spec ? `ROOM${spec.stage + 1}${spec.room.toString(16).padStart(2, '0').toUpperCase()}0.RDT` : '') };
  });
  const items = [...startKit(), ...scenes.flatMap((s) => pickups(s.place, s.script))];
  const audit = scenes.filter((s) => s.entry).map((s) => ({ room: s.place.id, slug: s.slug, text: s.entry }));
  const balance = day.acts.map((a) => {
    const own = items.filter((i) => i.act === a.n && i.placed);
    const enemies = scenes.filter((s) => s.place.act === a.n).reduce((n, s) => n + s.enemies.reduce((m, e) => m + e.count, 0), 0);
    const rounds = own.reduce((n, i) => n + i.rounds, 0);
    const green = own.filter((i) => i.kind === 'heal' && /green/i.test(i.name)).reduce((n, i) => n + i.qty, 0);
    const red = own.filter((i) => i.kind === 'heal' && /red/i.test(i.name)).reduce((n, i) => n + i.qty, 0);
    const sprays = own.filter((i) => i.kind === 'heal' && /spray/i.test(i.name)).reduce((n, i) => n + i.qty, 0);
    const ratio = rounds / Math.max(1, enemies);
    const finding = ratio < 3 ? 'Looks starved if she fights everything' : ratio > 10 ? 'Looks flooded relative to placed enemies' : 'Needs a route test';
    return { act: a.n, rounds, green, red, sprays, enemies, finding };
  });
  const facts = new Map<string, RoomFacts>(scenes.filter((s) => s.images.length).map((s) => [s.slug, { doors: s.evidence.doors, checks: s.evidence.checks.length, entry: Boolean(s.entry) }]));
  const tracker = sections(day, { rooms: facts });
  const missing: Missing[] = [];
  for (const s of scenes) {
    for (const step of s.steps.filter((t) => t.kind === 'find')) {
      const mapped = items.some((i) => i.room === s.place.id && i.step === step.id);
      const supplyAtRoom = items.some((i) => i.room === s.place.id && i.source === 'supplies');
      // Generic supply goals have no item step id. A placed spray covers a spray goal.
      const sprayGoal = /first aid spray/i.test(step.label) && !/ammunition/i.test(step.label);
      if (!mapped && !(sprayGoal && items.some((i) => i.room === s.place.id && i.kind === 'heal' && /spray/i.test(i.name)))) {
        missing.push({ room: s.place.id, priority: step.optional ? 2 : 0, title: `Resolve item placement: ${step.label}`, detail: `${step.id} has no matching pickup step${supplyAtRoom ? '. Other supplies are placed here, but do not establish this goal' : ''}` });
      }
    }
    if (!s.built) missing.push({ room: s.place.id, priority: 0, title: `Build ${s.place.name}`, detail: s.place.there });
    if (!s.images.length) missing.push({ room: s.place.id, priority: 4, title: `Render ${s.place.name}`, detail: `${day.links.filter((l) => l.to === s.place.id || l.from === s.place.id).length} links reach a room without a camera render${s.place.existing ? '. The original room exists in the game' : ''}` });
    for (const i of items.filter((i) => i.room === s.place.id && !i.placed)) missing.push({ room: s.place.id, priority: day.steps.find((t) => t.id === i.step)?.optional ? 3 : 0, title: `Place ${i.name}`, detail: i.detail });
  }
  // These are references, including music-only scenes, rather than guessed scripts.
  const references = new Map(REFERENCED);
  for (const cue of CUES) for (const id of cue.cutscenes) if (!references.has(id)) references.set(id, `${id}: ${cue.title}`);
  for (const [id, label] of references) {
    if (CUTSCENES.some((c) => c.id === id) || id === 'cut-chris' && CUTSCENES.some((c) => c.id === 'cut-sleep' && c.beats.some((b) => b.kind === 'say' && b.by === 'chris'))) continue;
    const step = day.steps.find((s) => s.id === id.replace('cut-', ''));
    missing.push({ room: step?.at ?? (id === 'cut-mine-chase' ? 'tunnel' : day.start), priority: id === 'cut-credits' ? 0 : 2, title: `Write ${label}`, detail: `${id} is referenced in plan/todo.ts but absent from day/cutscenes.ts` });
  }
  for (const section of tracker) for (const row of section.items) {
    if (row.status === 'done' || /^(room-|cut-|find-)/.test(row.id)) continue;
    const step = day.steps.find((s) => row.id === `puzzle-${s.id}` || row.id === `moving-${s.id}`);
    const link = day.links.find((l) => row.id === `link-${l.from}-${l.to}`);
    const room = step?.at ?? link?.from ?? null;
    const priority = section.id === 'ways' && !link ? 1 : section.id === 'puzzles' ? 1 : 3;
    missing.push({ room, priority, title: row.title, detail: `${row.status === 'doing' ? 'Under way' : 'To do'} · tracker ${section.id}/${row.id}${row.note ? ` · ${row.note}` : ''}` });
  }
  missing.sort((a, b) => a.priority - b.priority || day.places.findIndex((p) => p.id === a.room) - day.places.findIndex((p) => p.id === b.room));
  return { scenes, items, audit, balance, missing, tracker };
}
export type Storyboard = ReturnType<typeof buildStoryboard>;

function edit(room: string, field: string, old: string, mode: 'edit' | 'note' = 'note', label = 'Notes'): string {
  return `<label class="edit-label">${esc(label)}<textarea rows="${mode === 'edit' ? 2 : 1}" data-room="${esc(room)}" data-field="${esc(field)}" data-old="${esc(old)}" data-mode="${mode}" aria-label="${esc(`${room}: ${field}`)}">${mode === 'edit' ? esc(old) : ''}</textarea></label>`;
}
function dialogue(room: string, field: string, line: string, label: string): string {
  return `<div class="dialogue"><small>${esc(label)}</small><p class="words">${esc(line)}</p>${edit(room, field, line)}</div>`;
}
function itemTable(items: StoryItem[], compact = false): string {
  return `<div class="table-scroll"><table><thead><tr><th>Item</th><th>Kind</th><th>Quantity</th>${compact ? '' : '<th>Room and act</th>'}<th>Status and source</th><th>Your notes</th></tr></thead><tbody>${items.map((i) => `<tr data-item="${esc(`${i.room}/${i.id}`)}"><td>${esc(i.name)}</td><td>${i.kind}</td><td>${i.qty}${i.rounds ? ` · ${i.rounds} rounds` : ''}</td>${compact ? '' : `<td><a href="#scene-${i.room}">${esc(i.room)}</a> · ${i.act}</td>`}<td>${i.placed ? i.source === 'start' ? 'Starting kit' : 'Placed' : 'Missing placement'}<small>${esc(i.detail)}</small></td><td>${edit(i.room, `item ${i.id}`, `${i.name} · ${i.qty} · ${i.detail}`)}</td></tr>`).join('')}</tbody></table></div>`;
}

function mapGraph(act: number, board: Storyboard): string {
  const own = board.scenes.filter((s) => s.place.act === act);
  const links = day.links.filter((l) => own.some((s) => s.place.id === l.from || s.place.id === l.to));
  const ids = new Set(links.flatMap((l) => [l.from, l.to]));
  const nodes = board.scenes.filter((s) => ids.has(s.place.id));
  const minX = Math.min(...nodes.map((s) => s.place.at[0]));
  const minY = Math.min(...nodes.map((s) => s.place.at[1]));
  const pos = (p: Place) => ({ x: 20 + (p.at[0] - minX) * 102, y: 30 + (p.at[1] - minY) * 83 });
  const width = Math.max(...nodes.map((s) => pos(s.place).x)) + 200;
  const height = Math.max(...nodes.map((s) => pos(s.place).y)) + 90;
  const edges = links.map((l) => {
    const a = nodes.find((s) => s.place.id === l.from);
    const b = nodes.find((s) => s.place.id === l.to);
    if (!a || !b) return '';
    const x = pos(a.place); const y = pos(b.place);
    return `<path d="M${x.x + 85} ${x.y + 33} L${y.x + 85} ${y.y + 33}" class="${l.shortcut ? 'shortcut' : l.opens ? 'locked' : ''}"><title>${esc(`${l.from} to ${l.to} · ${l.kind}${l.opens ? ` · ${l.opens}` : ''}`)}</title></path>`;
  }).join('');
  return `<div class="graph-scroll"><svg viewBox="0 0 ${width} ${height}" style="min-width:${width}px" role="img" aria-label="Act ${act} room links"><g class="edges">${edges}</g>${nodes.map((s) => {
    const p = pos(s.place);
    return `<a href="#scene-${s.place.id}" class="graph-node ${s.place.act !== act ? 'ghost' : ''}"><title>${esc(s.place.name)}</title><rect x="${p.x}" y="${p.y}" width="174" height="66" rx="5"/><text x="${p.x + 10}" y="${p.y + 22}">${String(board.scenes.indexOf(s) + 1).padStart(2, '0')} · ${esc(s.place.id)}</text><text class="node-status" x="${p.x + 10}" y="${p.y + 47}">Act ${s.place.act} · ${s.built ? 'built' : 'planned'}${day.steps.some((t) => t.at === s.place.id) && day.steps.filter((t) => t.at === s.place.id).every((t) => t.optional) ? ' · optional' : ''}</text></a>`;
  }).join('')}</svg></div>`;
}

export function renderStoryboard(board: Storyboard): string {
  const stepLabel = (id: string) => day.steps.find((s) => s.id === id)?.label ?? id;
  const roomName = (id: string) => day.places.find((p) => p.id === id)?.name ?? id;
  const cards = day.acts.map((a) => `<section class="act" data-act="${a.n}"><div class="act-heading"><small>Act ${a.n} · ${esc(a.time)}</small><h2>${esc(a.title)}</h2><p>${esc(a.summary)}</p></div><div class="branch-map" hidden>${mapGraph(a.n, board)}</div><div class="route-cards">${board.scenes.filter((s) => s.place.act === a.n).map((s) => `<a class="route-card" data-card="${s.place.id}" href="#scene-${s.place.id}">${s.images[0] ? `<img src="img/${s.slug}-${s.images[0].replace('.png', '.jpg')}" alt="${esc(s.place.name)}" loading="lazy" width="640" height="480">` : `<div class="placeholder">${s.place.existing ? 'Original mansion room' : 'Scene not rendered'}</div>`}<div><small>${String(board.scenes.indexOf(s) + 1).padStart(2, '0')} · ${esc(s.hour)} · ${s.built ? 'Built' : 'Planned'}</small><h3>${esc(s.place.name)}</h3><p>${esc(s.place.there)}</p><span class="card-id">${esc(s.place.id)}${s.steps.length && s.steps.every((t) => t.optional) ? ' · optional stop' : ''}</span></div></a>`).join('')}</div></section>`).join('');

  const scenes = board.scenes.map((s, index) => {
    const main = s.steps.filter((t) => !t.optional).map((t) => t.label).join('\n') || `Continue through ${s.place.name.toLowerCase()}`;
    const secondary = s.steps.filter((t) => t.optional).map((t) => t.label).join('\n');
    const required = [...new Set(s.steps.flatMap((t) => t.needs))];
    const needs = required.filter((id) => KEY_ITEMS.some((k) => k.step === id));
    const known = required.filter((id) => day.steps.find((t) => t.id === id)?.kind === 'learn');
    const ownItems = board.items.filter((i) => i.room === s.place.id);
    const gaps = board.missing.filter((m) => m.room === s.place.id);
    const cues = CUES.filter((c) => c.places.includes(s.place.id) || c.cutscenes.some((id) => s.cuts.some((c) => c.id === id)));
    const save = SAVES.find((v) => v.place === s.place.id);
    return `<article class="scene" id="scene-${s.place.id}" hidden><div class="scene-heading"><div><small>Scene ${index + 1} of ${board.scenes.length} · Act ${s.place.act} · ${esc(s.hour)}</small><h2>${esc(s.place.name)}</h2><p>${esc(s.place.id)} · ${esc(s.file)} · ${s.built ? 'Built' : 'Planned'} · plan label: ${s.place.built}</p></div><div class="scene-nav">${index > 0 ? `<a href="#scene-${board.scenes[index - 1]?.place.id}">← Previous</a>` : ''}<a href="#flow">All rooms</a>${index < board.scenes.length - 1 ? `<a href="#scene-${board.scenes[index + 1]?.place.id}">Next →</a>` : ''}</div></div>
    <div class="scene-top"><div><div class="gallery">${s.images.length ? s.images.map((image, n) => `<figure><img src="img/${s.slug}-${image.replace('.png', '.jpg')}" alt="${esc(s.place.name)} · camera ${n + 1}" loading="lazy" width="640" height="480"><figcaption>Camera ${n + 1}</figcaption></figure>`).join('') : `<div class="placeholder"><h3>${s.place.existing ? 'Original mansion save room' : 'Planned scene'}</h3><p>${esc(s.place.there)}</p><p>${esc(s.place.story)}</p></div>`}</div><p class="hint">Swipe or scroll to see each camera. <a href="https://home.arpa/research/rebecca-playthrough.html" target="_blank" rel="noreferrer">Full playthrough recording</a>. The recording uses an older room layout, so room timestamps are not assigned here.</p></div>
    <div class="goals">${edit(s.place.id, 'main goal', main, 'edit', 'Main goal')}${edit(s.place.id, 'secondary goal', secondary, 'edit', 'Secondary goal')}${edit(s.place.id, 'scene notes', '', 'note', 'Scene notes')}<p class="hint">Edits save in this browser. Copy them when you are ready to send them back.</p></div></div>
    <div class="facts-grid"><section><h3>Rebecca here</h3><p>${esc(s.place.story || 'No new story beat planned.')}</p><p>${s.place.id === 'ridge' ? `Starts with ${board.items.filter((i) => i.source === 'start').map((i) => `${i.name}${i.rounds ? ` · ${i.rounds} rounds` : ''}`).join(', ')}.` : s.place.id === LOSS_ROOM ? `The mine takes her weapons, rounds and healing. Her keys stay. Removed item ids: ${GEAR.join(', ')}.` : s.place.act >= 3 ? 'After the mine she has no combat gear until Kevin’s Beretta at the helicopter. Pickups and spending decide what remains.' : 'She can still have her starting handgun and knife until the gallery collapse. The mountain branches can be visited in different orders.'}</p><p>Keys needed by local steps: ${esc(needs.map(stepLabel).join('; ') || 'None listed')}.</p><p>Knows from required clues: ${esc(known.map(stepLabel).join('; ') || 'No explicit learned prerequisite')}.</p><p class="hint">This is a plan state. Inventory and current HP depend on the route, pickups and combat. Her bag has six slots.</p></section>
    <section><h3>Risk and rewards</h3><p>${s.enemies.length ? s.enemies.map((e) => `${e.count} ${e.kind}`).join(', ') : 'No enemy spawns listed'}. Enemy HP is not given in foes.ts.</p><p>Health risk: ${s.enemies.length ? `${s.enemies.reduce((n, e) => n + e.count, 0)} attackers can spend her health and ammunition` : 'no placed attackers'}. Current HP depends on earlier combat.</p><p>Planned threat: ${esc(s.place.enemies || 'None')}.</p><p>Moves: ${esc(s.place.moves || 'None listed')}.</p><p>${save ? esc(save.props) : s.place.id === 'save' ? 'Original typewriter and shared item box.' : 'No save point here.'}</p><p>Music: ${esc(cues.map((c) => `${c.title}: ${c.sound}`).join('\n') || 'No cue listed')}.</p></section></div>
    <section><h3>What is needed to leave</h3><p>Local prerequisites: ${esc(required.map(stepLabel).join('; ') || 'None')}.</p><ul class="exits">${day.links.filter((l) => l.from === s.place.id || l.to === s.place.id).map((l) => {
      const to = l.from === s.place.id ? l.to : l.from;
      return `<li><a href="#scene-${to}">${esc(roomName(to))}</a> · ${l.kind}${l.shortcut ? ' · shortcut' : ''} · ${l.opens ? `opens after ${esc(stepLabel(l.opens))}` : 'open from the start'}</li>`;
    }).join('')}</ul><details><summary>Every local step</summary><ul>${s.steps.map((t) => `<li>${esc(t.label)} · ${t.kind}${t.optional ? ' · optional' : ''} · ${t.built}<small>Needs: ${esc(t.needs.map(stepLabel).join('; ') || 'nothing')}</small></li>`).join('')}</ul></details></section>
    <section><h3>Items here</h3>${ownItems.length ? itemTable(ownItems, true) : '<p>No items listed.</p>'}</section>
    <section><h3>Cutscenes · ${s.cuts.length}</h3>${s.cuts.map((c) => `<details class="cutscene" open><summary>${esc(c.id)} · ${esc(JSON.stringify(c.trigger))}</summary>${c.cast ? `<p>Cast: ${esc(JSON.stringify(c.cast))}</p>` : ''}<ol>${c.beats.map((b, n) => `<li>${b.kind === 'say' ? dialogue(s.place.id, `${c.id} beat ${n}`, b.text, b.by === 'her' ? 'Rebecca' : b.by) : `<span class="direction">${esc(beatText(b))}</span>`}</li>`).join('')}</ol>${c.after ? dialogue(s.place.id, `${c.id} after`, c.after, 'Check after the scene') : ''}</details>`).join('') || '<p>No written cutscene in this room.</p>'}</section>
    <section><h3>Messages and checks · ${s.msgs.length}</h3>${s.entry ? `<p class="flag">Entry thought without a cutscene. Review this interruption in the <a href="#audit">dialogue audit</a>.</p>` : ''}<details><summary>Every message in ${esc(s.slug)} · raw source beside readable text</summary>${s.place.existing ? '<p class="hint">This source also retains original messages that her scenario does not call. Her written ending is shown in full under Cutscenes.</p>' : ''}${s.msgs.map((m) => `${dialogue(s.place.id, `message ${m.n}`, m.text, `Message ${m.n}${m.n === 0 && s.entry ? ' · standalone entry thought' : ''}`)}<details class="raw"><summary>Raw message ${m.n}</summary><pre>${esc(m.raw)}</pre></details>`).join('')}</details>${s.evidence.checks.length ? `<details><summary>Checks recorded in the scene · ${s.evidence.checks.length}</summary>${s.evidence.checks.map((line, n) => dialogue(s.place.id, `check ${n}`, line, `Check ${n + 1}`)).join('')}</details>` : ''}${EVENTS.filter((e) => e.room === s.slug).map((e) => `<details><summary>Puzzle ${esc(e.step)}</summary>${dialogue(s.place.id, `${e.step} look`, e.look, 'Before')}${dialogue(s.place.id, `${e.step} done`, e.done, 'As it happens')}${dialogue(s.place.id, `${e.step} after`, e.after, 'After')}${e.opens ? dialogue(s.place.id, `${e.step} blocked`, e.opens.blocked, 'Blocked exit') : ''}</details>`).join('')}</section>
    <section><h3>Files to read</h3>${DOCUMENTS.filter((d) => d.room === s.slug).map((d) => `<details open><summary>${esc(d.title)} · ${esc(d.where)}</summary>${d.subtitle ? `<p>${esc(d.subtitle)}</p>` : ''}<p>${esc(d.writer)}</p>${d.notes?.length ? `<p>Open writing decisions: ${esc(d.notes.join(' '))}</p>` : ''}${d.pages.map((p, n) => dialogue(s.place.id, `file ${d.id} page ${n}`, p.kind === 'title' ? [d.title, d.subtitle ?? ''].filter(Boolean).join('\n') : filePage(p), `Page ${n + 1}`)).join('')}</details>`).join('') || '<p>No file here.</p>'}</section>
    <section><h3>Build status and missing parts</h3><p>${s.built ? 'Room script and scene art exist' : 'The room needs a script or scene art'}. ${s.images.length} camera renders. Plan label: ${s.place.built}.</p><ul>${gaps.map((m) => `<li>${esc(m.title)}<small>${esc(m.detail)}</small></li>`).join('') || '<li>No missing parts found by these checks.</li>'}</ul></section></article>`;
  }).join('');
  const data = JSON.stringify({ counts: { rooms: board.scenes.length, built: board.scenes.filter((s) => s.built).length, cutscenes: CUTSCENES.length, entryThoughts: board.audit.length, items: board.items.length }, balance: board.balance, missing: board.missing }).replaceAll('<', '\\u003c');
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rebecca's day: storyboard</title><script src="/research/rebecca-day/nav.js" defer></script><style>${read(join(HERE, 'storyboard/style.css'))}</style></head><body>
  <header><small class="eyebrow">Ridge at dawn. Mansion at night.</small><h1>Rebecca's day</h1><p class="intro">Walk the whole game, read each scene and leave edits for the next pass.</p><p class="counts">${board.scenes.length} rooms · ${board.scenes.filter((s) => s.built).length} built · ${CUTSCENES.length} cutscenes · ${board.audit.length} entry thoughts · ${board.items.length} item rows</p></header>
  <nav class="toolbar" aria-label="Storyboard"><div class="views"><a href="#flow">Flow</a><a href="#audit">Dialogue audit <span>${board.audit.length}</span></a><a href="#items">Items and balance</a><a href="#missing">Missing <span>${board.missing.length}</span></a></div><div class="edit-tools"><button id="copy">Copy my edits</button><button id="clear">Clear edits</button><span id="save-status" role="status" aria-live="polite">Edits stay in this browser</span></div></nav>
  <main><section id="flow" class="view"><div class="section-title"><div><h2>The whole day</h2><p>Cards follow the plan's order. The mountain branches have no single play order. Open a scene, then use its exits to walk your own route.</p></div><div class="flow-tools"><label>Act <select id="act-filter"><option value="all">All acts</option>${day.acts.map((a) => `<option value="${a.n}">${a.n} · ${esc(a.title)}</option>`).join('')}</select></label><button id="map-toggle" aria-pressed="false">Show branches</button></div></div><p id="map-key" hidden>Solid lines are open paths. Gold lines need a step. Dotted purple lines are shortcuts. Faded cards belong to the next or previous act. Scroll the map to follow a spoke. Open a card for each exit's lock and key.</p>${cards}</section>
  <section id="audit" class="view" hidden><h2>Dialogue audit · ${board.audit.length} entry thoughts</h2><p>These messages pause Rebecca on her first visit without an entry cutscene. Leave a note to cut the line, move it to a check, or write it into a cutscene. Rooms greeted by an entry cutscene are excluded, as in scripts.ts.</p>${board.audit.map((a) => `<article class="audit-row" data-audit="${a.room}"><h3><a href="#scene-${a.room}">${esc(roomName(a.room))}</a> <small>${esc(a.room)}</small></h3>${dialogue(a.room, 'message 0', a.text, 'Standalone entry thought')}</article>`).join('')}</section>
  <section id="items" class="view" hidden><h2>Items and balance</h2><p>${board.items.length} rows include starting kit, supplies, key items, files, maps and the original save room's pickup. Missing placements do not enter the act totals.</p><div class="table-scroll"><table><thead><tr><th>Act</th><th>Rounds</th><th>Green herbs</th><th>Red herbs</th><th>Sprays</th><th>Enemies</th><th>First check</th></tr></thead><tbody>${board.balance.map((b) => `<tr><td>${b.act}</td><td>${b.rounds}</td><td>${b.green}</td><td>${b.red}</td><td>${b.sprays}</td><td>${b.enemies}</td><td>${esc(b.finding)}</td></tr>`).join('')}</tbody></table></div><p class="flag">Act 2 loses carried combat gear and healing in the gallery. She must cross the mine and return to the gondola with whatever remains accessible after that loss. Act totals cannot prove that route is survivable.</p><p>Counts include the hand-written trail, yard and bridge spawns. foes.ts has no HP values. A red herb cannot heal alone. Starved means fewer than 3 rounds per enemy; flooded means more than 10. These are review prompts, not damage estimates. Avoided enemies, herb mixing and route order change the result.</p>${itemTable(board.items)}</section>
  <section id="missing" class="view" hidden><h2>Missing to finish the game · ${board.missing.length}</h2><p>Required placements and unbuilt rooms come first, then route work and the ending, unwritten scenes, polish and missing review renders. Tracker rows marked under way still need proof in the game. Plan labels alone do not mark a built room as missing.</p><ol class="missing-list">${board.missing.map((m) => `<li>${m.room ? `<a href="#scene-${m.room}">${esc(m.title)}</a>` : esc(m.title)}<small>${esc(m.detail)}</small></li>`).join('')}</ol></section>${scenes}</main>
  <dialog id="export-dialog"><h2>Your edits</h2><p id="copy-result">Copy this markdown and paste it back to the agent.</p><textarea id="export-text" readonly aria-label="Edits markdown" rows="14"></textarea><button id="close-export">Close</button></dialog><dialog id="clear-dialog"><h2>Clear saved edits?</h2><p>This removes the notes and goal edits saved by this storyboard in this browser.</p><button id="confirm-clear">Clear all edits</button><button id="cancel-clear">Keep edits</button></dialog>
  <script id="storyboard-data" type="application/json">${data}</script><script>${read(join(HERE, 'storyboard/client.js'))}</script></body></html>`;
}

export function generate(outDir: string): Storyboard {
  const report = check(day);
  if (report.errors.length) throw new Error(report.errors.join('\n'));
  const board = buildStoryboard();
  mkdirSync(join(outDir, 'img'), { recursive: true });
  const images = board.scenes.flatMap((s) => s.images.map((image) => ({ from: join(DAY, s.slug, 'renders', image), to: join(outDir, 'img', `${s.slug}-${image.replace('.png', '.jpg')}`) })));
  // sips is built into macOS. ImageMagick handles the same output on Linux.
  for (const i of images) {
    if (process.platform === 'darwin') execFileSync('sips', ['-s', 'format', 'jpeg', '-s', 'formatOptions', '78', '--resampleWidth', '640', i.from, '--out', i.to], { stdio: 'ignore' });
    else execFileSync('magick', [i.from, '-resize', '640x>', '-quality', '78', i.to], { stdio: 'ignore' });
  }
  writeFileSync(join(outDir, 'index.html'), renderStoryboard(board));
  process.stdout.write(`Storyboard: ${board.scenes.length} rooms, ${board.audit.length} entry thoughts, ${board.items.length} item rows, ${images.length} images\n`);
  return board;
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const out = process.argv[2];
  if (!out || process.argv.length !== 3) throw new Error('Usage: node tools/rebecca/plan/storyboard.ts <out dir>');
  generate(resolve(out));
}
