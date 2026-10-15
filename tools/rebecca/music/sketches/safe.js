// Rebecca's day, sketch: her safe room. Our own melody, in RE1's manner:
// a few minor chords held under a slow plucked arpeggio, a breathy lead on top.
// Only CC0 sounds (VCSL) and Strudel's own synths, pinned to one commit.
samples('https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json')
setcpm(14)
stack(
  // the held chords, a soft string pad
  note("<[d3,f3,a3] [d3,f3,a3] [bb2,d3,f3] [a2,c#3,e3]>")
    .s("sawtooth").lpf(650).attack(1.2).release(3).gain(0.16).room(0.6),
  // the arpeggio on the harp
  n("0 2 4 2 7 4 2 4")
    .scale("<D3:minor D3:minor Bb2:major A2:major>")
    .s("harp").gain(0.55).release(1.2).room(0.5),
  // the lead, one slow phrase a bar
  note("<[~ a4@3] [g4@2 f4@2] [~ f4@3] [e4@3 ~]>")
    .s("ocarina_vib").gain(0.3).room(0.7)
).coarse(2)
