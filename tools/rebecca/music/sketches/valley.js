// Rebecca's day, sketch: the valley at dusk. Grief: the Steinway in the low
// middle, a harp behind it, a low pad.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(10)
stack(
  // the Steinway
  note("<[f3 ~ c4 ~] [ab3 ~ ~ ~] [db3 ~ ab3 ~] [f3 ~ ~ ~] [bb2 ~ f3 ~] [db3 ~ ~ ~] [c3 ~ g3 ~] [e3 ~ ~ ~]>")
    .s("steinway").gain(0.5).room(0.7).size(0.8),
  // the harp
  note("<~ [~ ~ c5 ~] ~ [~ ~ ~ ab4] ~ [~ ~ f4 ~] ~ [~ ~ ~ g4]>").s("harp").gain(0.3).release(2).room(0.8),
  // the pad, dusk
  note("<f2 db2 bb1 c2>").slow(2).add(note("0,0.1")).s("sawtooth").lpf(400).attack(2).release(3).gain(0.1)
).coarse(2)
