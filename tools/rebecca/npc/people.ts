// The two people of her day, each an RE1 character model with its skeleton
// and animations kept and a skin of ours. build.ts writes their models into
// the REB overlay under the names LoadEntityEMD loads for the entity ids her
// rooms place them as; nothing in her day uses those characters otherwise
// (docs/REBECCA_NPC.md).
import { readEmd, readTexture, section, withSection, writeEmd, writeTexture } from './emd.ts';
import { paint, placeholder, surfaceMap, type Rgb, type Texel } from './paint.ts';
import { fitSkin } from './skin.ts';

export interface Person {
  readonly slug: string;
  /** The entity id her room scripts place, as in enemy(id, ...). */
  readonly entity: number;
  /** The model file g_emdPathTable names for that id (EntityModelLoader.cpp), in enemy/. */
  readonly model: string;
  readonly skin: (t: Texel) => Rgb;
}

export const people: readonly Person[] = [
  // Barry's model: the heavy man. Idle 0, walk 1, kneel 9, falls 4 and 54.
  { slug: 'hal', entity: 34, model: 'EM1022.EMD', skin: placeholder },
  // Rebecca's own NPC model: idle 0, walk 1, kneel 9, falls 4 and 59, sitting 61 and 62.
  { slug: 'partner', entity: 35, model: 'EM1023.EMD', skin: placeholder },
];

/** The player's model with our skin in place of its texture: same size, same everything else. */
export function personModel(file: Uint8Array, person: Person): Uint8Array {
  const emd = readEmd(file);
  const tim = section(emd, 'tim');
  const skin = fitSkin(readTexture(tim), paint(surfaceMap(file), person.skin));
  return writeEmd(withSection(emd, 'tim', writeTexture(tim, skin)));
}
