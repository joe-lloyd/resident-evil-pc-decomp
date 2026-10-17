// Rebecca's day, sketch: the mill pond's water, a layer in the pond.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(15)
stack(
  s("brown").lpf(sine.range(400, 800).slow(2)).gain(0.12),
  s("~ oceandrum ~ ~").speed(0.5).lpf(1500).gain(0.15).room(0.6)
)
