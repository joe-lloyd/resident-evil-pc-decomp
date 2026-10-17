// Rebecca's day, sketch: the creek, a layer by the creek.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(12)
stack(
  s("pink").bpf(sine.range(1200, 2200).slow(2)).bpq(1).gain(0.08),
  s("brown").lpf(600).gain(0.08),
  s("[~ shaker_small] [~ ~ shaker_small ~]").speed(1.5).gain(0.05).room(0.5)
)
