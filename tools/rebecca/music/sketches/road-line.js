// Rebecca's day, sketch: the power line humming, a layer at the switch house
// and on the line track once the breakers close.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(10)
stack(
  note("[a1,a2]").s("sawtooth").lpf(400).attack(0.05).release(0.3).gain(0.15),
  note("e4").s("square").lpf(1200).vib(8).vibmod(0.05).attack(0.05).release(0.3).gain(0.012),
  // crackle on the wire
  s("white*24").hpf(5000).decay(0.02).sustain(0).gain("0.02 0.01 0.03 0.01")
)
