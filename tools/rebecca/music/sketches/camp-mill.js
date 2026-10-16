// Rebecca's day, sketch: the camp's mill turning, a layer that joins near the
// mill once the race fills. The wheel's thump as each paddle comes round, the axle's creak.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(20)
stack(
  s("timpani ~ timpani ~").note("c#2").lpf(500).gain(0.5).room(0.5),
  s("~ ~ guiro ~").speed(0.4).lpf(1200).gain(0.25).room(0.5),
  // the race pouring over it
  s("pink").lpf(900).gain(0.06)
)
