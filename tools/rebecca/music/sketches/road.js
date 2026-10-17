// Rebecca's day, sketch: the forestry road. Open and exposed: a low pedal
// note that never moves, wind, high bowed psaltery far apart, a far knock.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(10)
stack(
  // the pedal
  note("[d2,a2]").slow(8).s("sawtooth").lpf(260).attack(2).release(3).gain(0.2),
  // wind across the open road
  s("pink").hpf(200).lpf(sine.range(400, 1400).slow(4)).gain(0.05),
  // high bowed psaltery
  note("<[a5@3 ~] ~ [~ e6@2 ~] [d6@2 ~ ~] ~ [~ ~ f#5@2] [g5@3 ~] ~>").s("psaltery_bow").gain(0.22).room(0.9).size(0.9),
  // a far knock, as if something is out there
  s("<~ ~ ~ ~ [~ ~ ~ woodblock] ~ ~ ~>").speed(0.5).gain(0.15).room(1)
).coarse(2)
