// Rebecca's day, sketch: the wind in the quarry pit, a layer in the quarry.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(12)
stack(
  s("brown").lpf(sine.range(200, 700).slow(4)).gain(0.15),
  s("pink").bpf(sine.range(600, 1600).slow(4)).bpq(3).gain(0.05),
  // grit trickling down the face
  s("<~ [~ shaker_small ~ ~] ~ ~>").speed(0.6).gain(0.08).room(0.6)
)
