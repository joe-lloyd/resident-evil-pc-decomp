// Rebecca's day, sketch: radio static by the mast, a layer at the mast.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(15)
stack(
  s("white*16").hpf(2500).decay(0.15).sustain(0.3).gain("0.03 0.05 0.02 0.04 0.06 0.02 0.03 0.05 0.02 0.04 0.03 0.06 0.02 0.03 0.05 0.02"),
  // a carrier whine coming and going
  note("<f#6 ~ ~ g6>").s("sine").attack(0.5).release(1).gain(0.01)
)
