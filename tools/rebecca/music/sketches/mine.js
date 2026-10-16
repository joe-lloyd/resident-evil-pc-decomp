// Rebecca's day, sketch: the silver mine. Almost not music: a drone so low
// it is felt more than heard, drips never on the beat, a bowed glass note now and then.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(8)
stack(
  // the drone
  note("[bb0,bb1]").slow(6).s("sawtooth").lpf(140).attack(3).release(4).gain(0.3),
  note("f2").slow(6).s("sine").attack(3).release(4).gain(0.05),
  // drips
  note("<[~ ~ f6 ~ ~ ~ ~ ~] [~ ~ ~ ~ ~ c7 ~ ~] [~ bb6 ~ ~ ~ ~ ~ ~] ~ [~ ~ ~ ~ ~ ~ f6 ~] [~ ~ ~ db7 ~ ~ ~ ~]>")
    .s("marimba").decay(0.08).sustain(0).gain(0.18).room(0.9).size(0.8),
  // the bowed glass, a tritone off the drone
  note("<~ ~ [~ e5@3] ~ ~ ~>").s("wineglass_slow").gain(0.1).room(1)
).coarse(2)
