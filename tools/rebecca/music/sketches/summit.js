// Rebecca's day, sketch: the summit. Thin air: high wind, handchimes far
// apart, a wineglass held under them, a soft pad far below.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(10)
stack(
  // high wind, thin
  s("pink").hpf(900).lpf(sine.range(2000, 5000).slow(8)).gain(0.04),
  // handchimes
  note("<[e5 ~ ~ ~] [~ ~ b5 ~] ~ [a#5 ~ ~ ~] [~ f#5 ~ ~] ~ [~ ~ ~ e6] ~>").s("handchimes").gain(0.35).room(0.9).size(0.95),
  // the wineglass
  note("<[b4,e5] ~ [a#4,f#5] ~>").slow(2).s("wineglass_slow").gain(0.12).room(1),
  // the pad
  note("<e3 c#3 b2 c#3>").slow(2).add(note("0,0.1")).s("sawtooth").lpf(500).attack(2).release(3).gain(0.08)
).coarse(2)
