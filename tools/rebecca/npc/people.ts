// The two people of her day, each an RE1 character model with its skeleton
// and animations kept and a skin of ours. build.ts writes their models into
// the REB overlay under the names LoadEntityEMD loads for the entity ids her
// rooms place them as; nothing in her day uses those characters otherwise
// (docs/REBECCA_NPC.md).
import { moveVertices, readEmd, readTexture, section, withSection, writeEmd, writeTexture, type Vec3 } from './emd.ts';
import { ownIsland, type Island } from './island.ts';
import { paint, surfaceMap, type Rgb, type Texel } from './paint.ts';
import { fitSkin } from './skin.ts';
import { campaignHat, hal, partner } from './skins.ts';

export interface Person {
  readonly slug: string;
  /** The entity id her room scripts place, as in enemy(id, ...). */
  readonly entity: number;
  /** The model file g_emdPathTable names for that id (EntityModelLoader.cpp), in enemy/. */
  readonly model: string;
  /**
   * The animation they idle in. The NPC code's looping idle (behaviour 9,
   * npc_idle_play_anim) always plays animation 0, which in these models is a
   * still pose, so the build swaps this one into place 0.
   */
  readonly idle: number;
  /** Triangles given their own place on the sheet (island.ts), so paint shows on them alone. */
  readonly ownIslands: readonly Island[];
  /** Small changes to the mesh where a skin alone can't carry the look: vertices moved, nothing added. */
  readonly reshape: readonly { readonly part: number; readonly move: (v: Vec3) => Vec3 }[];
  readonly skin: (t: Texel) => Rgb;
}

export const people: readonly Person[] = [
  // Barry's model: the heavy man. Stand 0, walk 1, kneel 9, falls 4 and 54;
  // 42 is a 20-frame standing loop that shifts his weight.
  // His cheeks get texels of their own, apart from the crown they share with,
  // and so does his left forearm, so the bandage is on the right only. The
  // larger move goes first.
  { slug: 'hal', entity: 34, model: 'EM1022.EMD', idle: 42, ownIslands: [{ part: 1, apart: 120 }, { part: 10 }], reshape: [], skin: hal },
  // Rebecca's own NPC model: stand 0, walk 1, kneel 9, falls 4 and 59,
  // sitting 61 and 62, a kneeling loop 63; 42 is a 20-frame standing loop.
  // The flare of the bob at the back of her head becomes a hat's brim.
  { slug: 'partner', entity: 35, model: 'EM1023.EMD', idle: 42, ownIslands: [], reshape: [{ part: 1, move: campaignHat }], skin: partner },
];

/**
 * The animation list with animation 0 and `idle` swapped (each entry is a
 * frame count and the offset of its frames). Swapping rather than copying
 * keeps the still pose in the list and keeps entry 0's place: the list's
 * length is the lowest frame offset any entry holds.
 */
export function idleFirst(edd: Uint8Array, idle: number): Uint8Array {
  const out = edd.slice();
  out.set(edd.subarray(idle * 4, idle * 4 + 4), 0);
  out.set(edd.subarray(0, 4), idle * 4);
  return out;
}

/**
 * The player's model with our skin in place of its texture, any reshaping,
 * any parts moved to their own islands, and its idle swapped into animation
 * 0: the same size, and every other byte as it was.
 */
export function personModel(file: Uint8Array, person: Person): Uint8Array {
  const emd = readEmd(file);
  const shaped = person.reshape.reduce((tmd, r) => moveVertices(tmd, r.part, r.move), section(emd, 'tmd'));
  const moved = withSection(emd, 'tmd', person.ownIslands.reduce(ownIsland, shaped));
  const tim = section(emd, 'tim');
  const skin = fitSkin(readTexture(tim), paint(surfaceMap(writeEmd(moved)), person.skin));
  const skinned = withSection(moved, 'tim', writeTexture(tim, skin));
  return writeEmd(withSection(skinned, 'edd', idleFirst(section(emd, 'edd'), person.idle)));
}
