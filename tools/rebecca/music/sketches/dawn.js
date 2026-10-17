// Rebecca's day, sketch: morning after, on the ridge and the trail down.
// Cold and still: a held minor chord on a soft string pad, a few harp notes, wind.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(12)
stack(
  // wind, slow to rise and fall
  s("pink").gain(0.05).hpf(150).lpf(sine.range(300, 1200).slow(8)),
  // the chord, a soft string pad, two bars on each
  note("<[e2,b2,g3] [c2,g2,e3] [a1,e2,c3] [b1,f#2,d3]>").slow(2)
    .add(note("0,0.12")).s("sawtooth").lpf(700).attack(2.5).release(3).gain(0.22).room(0.7).size(0.9),
  // a few harp notes, far apart
  note("<[~ b4 ~ ~] [~ ~ ~ g4] ~ [e5 ~ ~ ~] [~ c5 ~ ~] ~ [~ ~ f#4 ~] [b4 ~ ~ ~]>")
    .s("harp").gain(0.4).release(2).room(0.8).size(0.9)
).coarse(2)
