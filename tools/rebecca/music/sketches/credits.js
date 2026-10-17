// Rebecca's day, sketch: her credits. The day in one piece, about three
// minutes: the dawn chord, the station, the partner's phrase, Hal's piano,
// and the dawn chord again to end, quietly.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(12)
const dawn = stack(
  s("pink").gain(0.04).hpf(150).lpf(sine.range(300, 1200).slow(4)),
  note("<[e2,b2,g3] [c2,g2,e3]>").slow(2).add(note("0,0.12")).s("sawtooth").lpf(700).attack(2.5).release(3).gain(0.22).room(0.7),
  note("<[~ b4 ~ ~] ~ [e5 ~ ~ ~] [~ ~ g4 ~]>").s("harp").gain(0.4).release(2).room(0.8)
)
const station = stack(
  note("<c2 ~ ~ c2 ~ db2 ~ ~>").s("steinway").gain(0.6).room(0.8),
  note("<[eb4,g4] ~ [d4,ab4] ~>").slow(2).s("vibraphone_bowed").gain(0.3).room(0.7)
)
const partner = stack(
  note("<[a1,e2,c3] [f1,c2,a2] [g1,d2,b2] [e1,b1,g#2]>").slow(2).add(note("0,0.12")).s("sawtooth").lpf(600).attack(1.5).release(2.5).gain(0.2).room(0.6),
  note("<[e5 d5 a4 ~] [c5@3 ~] [b4 g4 e4 ~] ~ [e5 d5 a4 ~] [c5 d5 e5 ~] [g#4@3 ~] ~>").s("recorder_alto_vib").gain(0.45).release(0.4).room(0.6)
)
const hal = stack(
  note("<[g2 d3 b3 d3] [e2 b2 g3 b2] [c2 g2 e3 g2] [d2 a2 f#3 a2] [g2 d3 b3 d3] [b1 f#2 d3 f#2] [c2 g2 e3 g2] [d2 ~ ~ ~]>").s("piano1").gain(0.4).room(0.5),
  note("<[b4@3 a4] [g4@2 ~ e4] [g4@3 ~] [f#4@2 e4 d4] [d5@3 b4] [a4@2 f#4 ~] [e4 g4 c5 b4] [a4@3 ~]>").s("piano1").gain(0.4).room(0.5),
  note("<~ [~ ~ d4@2] ~ [~ ~ c4@2] ~ ~ [~ ~ e4@2] d4>").s("harmonica_soft").gain(0.15).room(0.7)
)
const end = stack(
  s("pink").gain(0.03).hpf(150).lpf(sine.range(300, 900).slow(4)),
  note("<[e2,b2,g3] [e2,b2,g3] [c2,g2,e3] [e2,b2,g3]>").slow(2).add(note("0,0.12")).s("sawtooth").lpf(600).attack(3).release(4).gain(0.2).room(0.8),
  note("<[~ b4 ~ ~] ~ [~ ~ e5 ~] ~ [g4 ~ ~ ~] ~ ~ ~>").s("harp").gain(0.35).release(3).room(0.9)
)
arrange([4, dawn], [8, station], [8, partner], [8, hal], [8, end]).coarse(2)
