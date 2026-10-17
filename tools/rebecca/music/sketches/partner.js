// Rebecca's day, sketch: the ranger's partner. Tired and determined: a short
// recorder phrase that comes back each time she turns up, over low strings.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(14)
stack(
  // low strings
  note("<[a1,e2,c3] [f1,c2,a2] [g1,d2,b2] [e1,b1,g#2]>").slow(2)
    .add(note("0,0.12")).s("sawtooth").lpf(600).attack(1.5).release(2.5).gain(0.2).room(0.6),
  // the phrase on the alto recorder: four notes, a held one, an answer
  note("<[e5 d5 a4 ~] [c5@3 ~] [b4 g4 e4 ~] ~ [e5 d5 a4 ~] [c5 d5 e5 ~] [g#4@3 ~] ~>")
    .s("recorder_alto_vib").gain(0.45).release(0.4).room(0.6),
  // a low tread under it
  s("<timpani ~ timpani ~ timpani ~ timpani ~>").note("<a1 ~ f1 ~ g1 ~ e1 ~>").gain(0.3).room(0.5)
).coarse(2)
