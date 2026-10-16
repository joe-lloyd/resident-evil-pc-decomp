// Rebecca's day, sketch: the estate's grounds. The mansion is close, and the
// music starts to sound like RE1's own: a quiet pipe organ, low piano, a few notes on top.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(12)
stack(
  // the pipe organ, quiet
  note("<[bb2,db3,f3] [bb2,db3,f3] [gb2,bb2,db3] [gb2,bb2,db3] [eb2,gb2,bb2] [eb2,gb2,bb2] [f2,a2,c3] [f2,a2,c3]>")
    .s("pipeorgan_quiet").gain(0.35).room(0.8).size(0.9),
  // low piano under it
  note("<bb1 ~ gb1 ~ eb1 ~ f1 [~ ~ ~ e1]>").s("steinway").gain(0.5).room(0.6),
  // a voice on top
  note("<~ [~ ~ f4 ~] [gb4@3 ~] ~ ~ [~ ~ eb4 ~] [db4@2 c4@2] ~>").s("pipeorgan_quiet").gain(0.18).room(0.8)
).coarse(2)
