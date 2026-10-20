// Rebecca's day, sketch: the mine, running through the dark for the lift.
// A driving low ostinato, timpani, metal hits, a bowed cluster above.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(36)
stack(
  // the ostinato, opening and closing
  note("d2 d2 [d2 d2] eb2 d2 d2 [d2 d2] c2")
    .s("sawtooth").lpf(sine.range(400, 1600).slow(4)).decay(0.15).sustain(0).gain(0.35),
  // timpani
  s("timpani ~ ~ timpani ~ timpani ~ ~").note("d2").gain(0.8),
  // metal, once a bar, low
  s("<anvil ~ ~ ~>").speed(0.5).gain(0.4).room(0.4),
  // the bowed cluster
  note("<[d5,eb5] ~ [c#5,d5] ~>").s("psaltery_bow").gain(0.25).room(0.6)
).coarse(2)
