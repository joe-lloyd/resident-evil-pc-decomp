// Rebecca's day, sketch: the station yard, the hub she keeps coming back to.
// Wind, a low piano note now and then, a bowed chord that never resolves.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(10)
stack(
  // wind, rising and falling
  s("brown").gain(0.07).lpf(sine.range(250, 900).slow(8)),
  // the low piano
  note("<c2 ~ ~ c2 ~ db2 ~ ~>").s("steinway").gain(0.6).room(0.8).size(0.9),
  // bowed vibraphone chords, slower still
  note("<[eb4,g4] ~ [d4,ab4] ~>").slow(2).s("vibraphone_bowed").gain(0.3).room(0.7),
  // a glass note, far off
  note("~ ~ ~ <b5 ~ c6 ~>").slow(2).s("wineglass").gain(0.12).room(1)
).coarse(2)
