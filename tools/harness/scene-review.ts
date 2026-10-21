// A reviewed scene's route, walked with normal game input by record-scene.ts.
import { dayRooms } from '../rebecca/day/rooms.ts';

export type ReviewStep =
  | { action: 'walk'; x: number; z: number; camera?: number; picture?: string }
  | { action: 'look'; zone: { x: number; z: number; w: number; d: number }; picture?: string }
  | { action: 'hold'; frames: number; camera?: number; picture?: string }
  | { action: 'exit'; x: number; z: number; to: string; zone?: { x: number; z: number; w: number; d: number } };
export interface ReviewRoute { scene: string; steps: ReviewStep[] }

export function parseReviewRoute(value: unknown): ReviewRoute {
  if (!value || typeof value !== 'object') throw new Error('Expected review route');
  const { scene, steps } = value as ReviewRoute;
  const room = (slug: unknown) => typeof slug === 'string' && dayRooms.some((r) => r.slug === slug);
  if (!room(scene) || !Array.isArray(steps) || !steps.length) throw new Error('Expected scene and review steps');
  const coordinate = (n: unknown) => typeof n === 'number' && Number.isInteger(n) && n >= 0 && n <= 32767;
  for (const s of steps) {
    if (!s || typeof s !== 'object') throw new Error('Expected review step');
    if ('picture' in s && (typeof s.picture !== 'string' || !/^[a-z0-9-]+$/.test(s.picture))) throw new Error('Invalid picture name');
    if ('camera' in s && !coordinate(s.camera)) throw new Error('Invalid review camera');
    if ('zone' in s && s.zone && (!Object.values(s.zone).every(coordinate) || !s.zone.w || !s.zone.d || Object.keys(s.zone).sort().join() !== 'd,w,x,z')) throw new Error('Invalid review zone');
    if (s.action === 'walk' || s.action === 'exit') {
      if (!coordinate(s.x) || !coordinate(s.z)) throw new Error('Invalid review position');
      if (s.action === 'exit' && !room(s.to)) throw new Error('Invalid exit scene');
    } else if (s.action === 'hold') {
      if (!coordinate(s.frames) || s.frames < 1 || s.frames > 900) throw new Error('Invalid hold frames');
    } else if (s.action === 'look') {
      if (!s.zone || !Object.values(s.zone).every(coordinate) || !s.zone.w || !s.zone.d || Object.keys(s.zone).sort().join() !== 'd,w,x,z') throw new Error('Invalid review zone');
    } else throw new Error('Unknown review action');
  }
  if (steps.at(-1)?.action !== 'exit' || steps.slice(0, -1).some((s) => s.action === 'exit')) throw new Error('Finish the review with one exit');
  return { scene, steps };
}

