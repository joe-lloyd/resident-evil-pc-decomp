// New Chris game, jump to the corridor where Kenneth is eaten, and check the
// first zombie is there. With the vanilla rooms it is type 0x11, the green coat.
import { open } from '../lab.ts';
import { newGame } from '../flows.ts';
import { roomLabel } from '../state.ts';

const expectedType = Number(process.env.EXPECT_TYPE ?? 0x11);
const session = await open(Number(process.env.PORT ?? 7801));
try {
  const start = await newGame(session.link, 'chris');
  console.log(`control in room ${roomLabel(start)}, hp ${start.player.hp}/${start.player.maxHp}`);

  const s = await session.link.room(0, 4);
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
