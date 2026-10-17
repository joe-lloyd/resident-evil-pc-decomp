// Rebecca's day, sketch: the station's generator hum, a layer that joins the
// station's music once the power is on. Two octaves of C under its piano, the engine thudding.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(10)
stack(
  // the hum
  note("[c2,c3]").s("sawtooth").lpf(220).attack(0.05).release(0.3).gain(0.25),
  note("g3").s("sine").attack(0.05).release(0.3).gain(0.04),
  // the engine, thudding away in its hut
  s("brown*12").lpf(140).decay(0.25).sustain(0).gain(0.4)
)
