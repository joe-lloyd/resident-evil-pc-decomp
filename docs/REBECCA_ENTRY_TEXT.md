# Entry text in Rebecca's day

There are no standalone entry thoughts. The allow-list in day/scripts.ts
is empty. A new entry line in scene.py or renders/room.json fails the unit
check, and the generator rejects a room record outside that list.

All 51 kit-room entry records below are removed at both sources. Some were
already suppressed by greeting cutscenes. Message slot 0 stays as an unused
placeholder so every check and cutscene keeps its message id. Existing
cutscenes still mark their story beats.

The five older hand-written rooms also lose their entry messages: trail,
lookout, yard, shed and bridge. Those room.c files are authored sources,
with only the marked sections written by scripts.ts. The trail's radio
thought now belongs to its marker-post check. The lookout's radio, warm
stove and broken-window checks already tell the cabin's story. The other
three introductions just restated their backgrounds.

No entry thoughts are kept, so there are no exceptions to justify.

| Room | Removed entry line | Disposition |
| --- | --- | --- |
| back-garden | The back of the mansion. The house is dark. | Cut the background observation. The room and its existing checks already show it. |
| booth | The heater's still on. He can't have gone long. | Cut the heater observation. The phone scene establishes that Hal has just left. |
| bunkhouse | It stinks of sickness in here. | Cut the background observation. The room and its existing checks already show it. |
| camp-gate | They shut themselves in. It didn't help. | Cut the background observation. The room and its existing checks already show it. |
| camp-yard | Camp 4. The gate was shut from inside. | Cut the background observation. The room and its existing checks already show it. |
| car | It's stopped. We're hanging over the trees. There's a pylon right ahead. | Keep the stopped car and pylon in cut-pylon. Remove the duplicate entry line. |
| cellar | Candles. Someone's down here. | Cut the background observation. The room and its existing checks already show it. |
| cottage | The radio's still on. | Cut the background observation. The room and its existing checks already show it. |
| crash | The helicopter. This is where we came down. | Keep the helicopter recognition in cut-kevin. Remove the duplicate entry line. |
| crawl | Under the house. I can hear someone walking around up there. | The existing footsteps check carries the story beat. Remove the duplicate entry line. |
| creek | Running water. And a light, across the creek. | Cut the background observation. The room and its existing checks already show it. |
| den | The smell hits first. Then the flies. | Keep the smell and flies in cut-den. Remove the duplicate entry line. |
| depot | Diesel. The whole place reeks of it. | Cut the background observation. The room and its existing checks already show it. |
| east-path | Blood on the path. He came this way. | Cut the background observation. The room and its existing checks already show it. |
| estate-wall | The Spencer estate. There's a light on, up at the house. | Cut the background observation. The room and its existing checks already show it. |
| flume | The flume. It runs all the way down the mountain. | Cut the background observation. The room and its existing checks already show it. |
| gallery | The water's cold. It's black. I can't see the floor. | Keep the cold water and hidden floor in cut-mine-collapse. Remove the duplicate entry line. |
| garden-shed | A potting shed. The lantern's lit. | Cut the background observation. The room and its existing checks already show it. |
| generator | Cold. It hasn't run for hours. | Cut the background observation. The room and its existing checks already show it. |
| junction | The roof is covered in egg sacs. | Cut the background observation. The room and its existing checks already show it. |
| kennels | Kennels. All the runs are empty. | Cut the background observation. The room and its existing checks already show it. |
| line-track | The power line. Not a hum from it. | Cut the background observation. The room and its existing checks already show it. |
| lodge | Someone left the lamp burning. | Cut the background observation. The room and its existing checks already show it. |
| logging-road | A logging truck, stopped dead in the ruts. | Cut the background observation. The room and its existing checks already show it. |
| lower-station | Blood on the counter. Glass on the floor. | Cut the background observation. The room and its existing checks already show it. |
| lower-yard | The bottom of the gondola. Someone left their car door open. | Cut the background observation. The room and its existing checks already show it. |
| mast | The mast. Its light's still blinking. | Cut the background observation. The room and its existing checks already show it. |
| mess | Flies. Hundreds of them. | Cut the background observation. The room and its existing checks already show it. |
| mine-entrance | Webs. Thick ones. | Cut the background observation. The room and its existing checks already show it. |
| mine-lift | The cage creaks under me. | Cut the background observation. The room and its existing checks already show it. |
| mine-office | Candles. Someone lit these today. | Cut the background observation. The room and its existing checks already show it. |
| office | The smell hits first. | Cut the background observation. The room and its existing checks already show it. |
| platform | A gondola station. Down the mountain, into the valley. If it ran. | The station sign and OUT OF SERVICE check already explain the route and the dead gondola. |
| pond | The mill pond. The wheel's stopped. | Cut the background observation. The room and its existing checks already show it. |
| pylon | Pylon 7. It's a long way down. | Cut the background observation. The room and its existing checks already show it. |
| quarry | A quarry. Something's been feeding here. | Cut the background observation. The room and its existing checks already show it. |
| quarry-office | Burnt coffee. The hot plate's still on. | Cut the background observation. The room and its existing checks already show it. |
| road | The forestry road. The gate's chained shut. | Cut the background observation. The room and its existing checks already show it. |
| sawmill | Sawdust, and the smell of blood. | Cut the background observation. The room and its existing checks already show it. |
| summit-trail | The top of the mountain. Nothing grows up here. Just rock, and crows. | Cut the background observation. The room and its existing checks already show it. |
| switch | It smells of burnt rubber. | Cut the background observation. The room and its existing checks already show it. |
| tower-foot | The tower creaks in the wind. | Cut the background observation. The room and its existing checks already show it. |
| tower-stairs | The wind's stronger up here. The whole tower sways. | Cut the background observation. The room and its existing checks already show it. |
| tower-top | The lookout. You can see half the mountain from here. | Keep the valley view in cut-tower. Remove the duplicate entry line. |
| tunnel | The lamps are lit. Someone's been down here. | Cut the background observation. The room and its existing checks already show it. |
| valley-path | Down. Smoke in the west. That could be the helicopter. | Cut the distant smoke observation. The S.T.A.R.S. patch check and cut-kevin carry the search for Bravo. |
| washout | Half the road's gone. | Cut the background observation. The room and its existing checks already show it. |
| weather | A radio. It's on. Someone could hear me. | Cut the background observation. The room and its existing checks already show it. |
| wine | The wine store. It smells of wine. And something else. | Cut the background observation. The room and its existing checks already show it. |
| woods | The drag marks go on into the trees. So does the blood. | Keep the drag marks and blood in cut-partner. Remove the duplicate entry line. |
| workshop | Oil and something worse. | Cut the background observation. The room and its existing checks already show it. |
