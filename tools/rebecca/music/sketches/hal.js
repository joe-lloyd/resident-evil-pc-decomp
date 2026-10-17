// Rebecca's day, sketch: Hal. A kind, worn-out man: a slow hymn on an upright
// piano, a harmonica held back, a low drone.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(12)
stack(
  // the drone, low and steady
  note("[g1,d2]").slow(8).s("sawtooth").lpf(180).attack(2).release(3).gain(0.18),
  // the piano's left hand, broken chords
  note("<[g2 d3 b3 d3] [e2 b2 g3 b2] [c2 g2 e3 g2] [d2 a2 f#3 a2] [g2 d3 b3 d3] [b1 f#2 d3 f#2] [c2 g2 e3 g2] [d2 ~ ~ ~]>")
    .s("piano1").gain(0.4).room(0.5),
  // its tune
  note("<[b4@3 a4] [g4@2 ~ e4] [g4@3 ~] [f#4@2 e4 d4] [d5@3 b4] [a4@2 f#4 ~] [e4 g4 c5 b4] [a4@3 ~]>")
    .s("piano1").gain(0.4).room(0.5),
  // the harmonica, held back
  note("<~ [~ ~ d4@2] ~ [~ ~ c4@2] ~ ~ [~ ~ e4@2] d4>").s("harmonica_soft").gain(0.15).room(0.7)
).coarse(2)
