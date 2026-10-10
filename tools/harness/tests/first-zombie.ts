// New Chris game, jump to the corridor where Kenneth is eaten, and check the
// first zombie is there. With the vanilla rooms it is type 0x11, the green coat.
import { open } from '../lab.ts';
import { inControl } from '../flows.ts';
import { roomLabel } from '../state.ts';

const expectedType = Number(process.env.EXPECT_TYPE ?? 0x11);
const session = await open(Number(process.env.PORT ?? 7801), '--boot chris:0:4');
try {
  const s = await session.link.waitFor((st) => st.stage === 0 && st.room === 4 && inControl(st), 'control in ROOM104', 120_000);
  console.log(`control in room ${roomLabel(s)}, hp ${s.player.hp}/${s.player.maxHp}`);
  const types = s.enemies.map((e) => e.type);
  console.log(`room ${roomLabel(s)} enemies [${types.map((t) => t.toString(16)).join(', ')}]`);
  await session.link.shot('C:\\Users\\joell\\Tools\\wintool\\first-zombie.bmp');

  if (!types.includes(expectedType)) {
    console.error(`FAIL: no enemy of type ${expectedType.toString(16)} in ROOM104`);
    process.exitCode = 1;
  } else {
    console.log('PASS');
  }
} finally {
  session.end();
}
