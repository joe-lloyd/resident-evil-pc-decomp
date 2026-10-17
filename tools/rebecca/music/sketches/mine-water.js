// Rebecca's day, sketch: the flooded mine's water, a layer in the tunnel and
// the junction until the pump drains it.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(8)
stack(
  s("brown").lpf(500).gain(0.18),
  s("[~ oceandrum] ~").speed(0.4).lpf(900).gain(0.15).room(0.8),
  // the sump gurgling
  note("~ c3 ~ ~ ~ eb3 ~ ~").s("sine").decay(0.12).sustain(0).lpf(600).gain(0.05).room(0.7)
)
