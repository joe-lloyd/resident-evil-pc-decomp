// Rebecca's day, sketch: the line down. The cable clacking over the sheaves
// and the bullwheel's turn as rhythm, low strings rising.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(14)
stack(
  // the cable over the sheaves
  s("woodblock ~ ~ woodblock ~ ~ ~ ~").speed(0.4).lpf(1200).gain(0.3).room(0.3),
  // the bullwheel
  note("g1 ~ ~ ~ d2 ~ ~ ~").s("sawtooth").lpf(200).decay(0.6).sustain(0).gain(0.3),
  // the strings, rising a step at a time
  note("<[g2,d3,bb3] [g2,d3,bb3] [ab2,eb3,c4] [ab2,eb3,c4] [a2,e3,c4] [bb2,f3,d4] [b2,f#3,d4] [c3,g3,eb4]>")
    .add(note("0,0.12")).s("sawtooth").lpf(sine.range(500, 1100).slow(8)).attack(1.5).release(2).gain(0.18).room(0.6)
).coarse(2)
