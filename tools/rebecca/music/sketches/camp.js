// Rebecca's day, sketch: Logging Camp 4. Somewhere people worked until last
// week: a low ostinato like a belt left running, muted metal, a slit drum, a far saw.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(15)
stack(
  // the low ostinato
  note("f#1 ~ f#1 c#2 ~ f#1 ~ [g1 f#1]").s("sawtooth").lpf(sine.range(300, 700).slow(8)).decay(0.2).sustain(0).gain(0.3),
  // muted metal, off the beat
  s("~ brakedrum ~ ~ ~ ~ brakedrum ~").speed(0.7).lpf(1800).gain(0.25).room(0.4),
  // the slit drum, a slow tread
  s("slitdrum ~ ~ ~ slitdrum ~ ~ ~").n("<0 0 2 0>").speed(0.8).gain(0.5),
  // a far saw, once in a while: noise drawn through a narrow band, stroke by stroke
  s("<~ ~ ~ [white*8] ~ ~ ~ ~>").bpf("1300 1800").bpq(6).decay(0.22).sustain(0).gain(0.07).room(0.9)
).coarse(2)
