import { readFileSync } from 'node:fs';

function object(value: unknown): Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) throw new Error('Expected footage object');
  return Object.fromEntries(Object.entries(value));
}
function text(value: unknown): string {
  if (typeof value !== 'string') throw new Error('Expected footage text');
  return value;
}
function number(value: unknown): number {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) throw new Error('Expected nonnegative footage number');
  return value;
}
function list(value: unknown): unknown[] {
  if (!Array.isArray(value)) throw new Error('Expected footage list');
  return value;
}
function asset(value: unknown, extension: string): string {
  const path = text(value);
  if (!new RegExp(`^clips/[a-z0-9-]+\\.${extension}$`).test(path)) throw new Error(`Invalid clip path: ${path}`);
  return path;
}
function review(value: unknown) {
  if (value === undefined) return undefined;
  const r = object(value);
  const date = text(r.recorded);
  const source = text(r.source);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !/^recordings\/[a-z0-9-]+\.mp4$/.test(source)) throw new Error('Invalid scene recording');
  if (typeof r.god !== 'boolean' || typeof r.audio !== 'boolean') throw new Error('Expected scene recording settings');
  return { recorded: date, source, god: r.god, audio: r.audio, checkpoint: r.checkpoint !== null };
}
export function parseFootage(value: unknown) {
  const root = object(value);
  const clips = list(root.clips).map((value) => {
    const c = object(value);
    const start = number(c.start); const end = number(c.end);
    const quarter = number(c.quarter); const visit = number(c.visit);
    if (end <= start || !Number.isInteger(quarter) || quarter < 1 || quarter > 4 || !Number.isInteger(visit) || visit < 1) throw new Error('Invalid clip span or visit');
    return { room: text(c.room), quarter, visit, start, end, review: review(c.review), file: asset(c.file, 'mp4'), poster: asset(c.poster, 'jpg'), note: text(c.note),
      events: list(c.events).map((value) => { const e = object(value); return { t: number(e.t), what: text(e.what) }; }) };
  });
  if (new Set(clips.map((c) => c.file)).size !== clips.length) throw new Error('Duplicate clip file');
  return { clips, noFootage: list(root.noFootage).map(text) };
}
export const footage = parseFootage(JSON.parse(readFileSync(new URL('./clips.json', import.meta.url), 'utf8')));
export type Clip = typeof footage.clips[number];
const esc = (s: string) => s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const clock = (t: number) => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, '0')}`;
// Keep the log's words, with asides written as part of the label.
const label = (s: string) => s.replace(/\s*\(([^)]*)\)/g, ': $1').replace(/[—–]/g, ',');
export function renderClips(clips: Clip[], roomName: string): string {
  return `<section class="footage"><h3>Recorded visits</h3>${clips.length ? `<p class="hint">${clips.some((c) => c.review) ? 'Scene review recording. Settings and date are shown below each clip.' : '17 October recording. God mode was on. No sound. Each clip keeps the nearby doors. <a href="https://home.arpa/research/rebecca-whole-day/">Watch the four quarters</a>.'}</p><div class="clips">${clips.map((c) => `<figure class="clip"><video controls preload="none" playsinline poster="${esc(c.poster)}" aria-label="${esc(`${roomName}, ${c.review ? "scene review" : `quarter ${c.quarter}`}, visit ${c.visit}`)}"><source src="${esc(c.file)}" type="video/mp4"><a href="${esc(c.file)}">Open this clip</a></video><figcaption>${c.review ? `${esc(c.review.recorded)} · Scene review · Visit ${c.visit}` : `Quarter ${c.quarter} · Visit ${c.visit}`}<small>${esc(label(c.events.find((e) => /^(done:|took |killed |cranked |listened )/.test(e.what))?.what ?? (c.review ? (c.review.checkpoint ? 'Scene route from a played checkpoint' : 'Opening and scene route') : c.events[0]?.what) ?? 'Room visit'))}</small><small>${clock(c.start)} to ${clock(c.end)} in the ${c.review ? 'scene recording' : 'quarter'} · ${Math.round(c.end - c.start)} seconds</small>${c.review ? `<small>${c.review.god ? 'God mode' : 'Normal damage'} · ${c.review.audio ? 'With sound' : 'No sound'} · ${c.review.checkpoint ? 'Played checkpoint' : 'New Rebecca game'} · <a href="${esc(c.review.source)}">Source recording</a></small>` : ''}</figcaption><details><summary>Run events · ${c.events.length}</summary><ul>${c.events.map((e) => `<li>${esc(label(e.what))}</li>`).join('')}</ul></details>${c.note ? `<p class="recording-note">${esc(c.note)}</p>` : ''}</figure>`).join('')}</div>` : '<p>No footage of this room in the four-quarter recording.</p>'}</section>`;
}
