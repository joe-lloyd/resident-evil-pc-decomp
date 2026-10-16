// Rebecca's day, sketch: the wind up the lookout tower, a layer on its stairs and at the top.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(10)
stack(
  s("pink").hpf(300).lpf(sine.range(800, 3000).slow(4)).gain(0.1),
  // the wind whistling in the rails
  note("<a6 ~ b6 ~>").s("sine").vib(3).vibmod(0.3).attack(1.5).release(2).gain(0.015)
)
