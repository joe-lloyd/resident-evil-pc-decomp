// Rebecca's day, sketch: the quarry. Dry and hard: a low drone with a
// semitone rubbing against it, sparse timpani, anvil and brake drum far off.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(12)
stack(
  // the drone
  note("[c#2,g#2]").slow(8).s("sawtooth").lpf(300).attack(2).release(3).gain(0.2),
  note("<c#3 c#3 d3 d3 c#3 c#3 c3 c3>").s("sine").attack(1.5).release(2).gain(0.05),
  // timpani, sparse
  s("<timpani ~ ~ [~ ~ timpani ~] timpani ~ ~ ~>").note("c#2").gain(0.6).room(0.6),
  // metal far off, as if work were still going on somewhere
  s("<[~ ~ anvil ~] ~ ~ ~ [~ ~ ~ brakedrum] ~ [~ anvil ~ ~] ~>").speed(0.6).lpf(2000).gain(0.2).room(0.95).size(0.95)
).coarse(2)
