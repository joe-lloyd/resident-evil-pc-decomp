// Act 1, dawn to morning: from the ridge down to the far side of the gorge.
// The first loop (the cabin, the shed, the winch) is built; the rest is the
// plan in docs/REBECCA_DAY.md, widened so that once the dog has come she has
// three threads to work on at once: the trail down, the woods and the fuel.
// `node tools/rebecca/plan/page.ts <out dir>` draws it; plan.test.ts checks it.
import type { Act } from './plan.ts';

export const act1: Act = {
  title: 'Act 1: the mountain, dawn to morning',
  start: 'ridge',
  places: [
    {
      id: 'ridge', name: 'The ridge', built: 'built', room: 'ridge', at: [6, 0],
      there: 'Where the game opens', moves: 'Smoke from the facility, grass', enemies: '',
      story: 'Billy has gone; the training facility burns below',
    },
    {
      id: 'trail', name: 'The mountain trail', built: 'built', room: 'trail', at: [6, 1.2],
      there: 'Down through the spruces', moves: 'Ferns in the wind', enemies: 'Crows',
      story: 'Alone for the first time',
    },
    {
      id: 'yard', name: 'The station yard', built: 'built', room: 'yard', at: [6, 3],
      there: 'The hub: the pine across the trail, the truck and its winch, his rifle', moves: 'Chimney smoke, hazard lights',
      enemies: 'A Cerberus, once she has the shed key', story: 'Someone was here this morning',
    },
    {
      id: 'cabin', name: 'The cabin', built: 'built', room: 'lookout', at: [8.4, 2.4],
      there: 'The logbook, the radio, the shed key', moves: 'The lamp flame, a fly', enemies: '',
      story: 'He left in a hurry, mid-breakfast; a rifle rack, empty',
    },
    {
      id: 'shed', name: 'The tool shed', built: 'built', room: 'shed', at: [8.4, 3.6],
      there: 'The winch crank, an empty jerrycan, spare fuses', moves: 'Dust in the light', enemies: '',
      story: 'He tried to mend the chainsaw first',
    },
    {
      id: 'woods', name: 'The woods', built: 'planned', at: [3.8, 2],
      there: 'Where the drag marks lead: the ranger, dead; a water pump and its hose', moves: 'Flies over the body, branches',
      enemies: 'Cerberus, two', story: 'What took him; the truck keys in his jacket',
    },
    {
      id: 'road', name: 'The forestry road', built: 'planned', at: [1.6, 2],
      there: 'A chained gate across the road', moves: 'A torn notice on the gate', enemies: 'Crows',
      story: 'The way the loggers drive up',
    },
    {
      id: 'generator', name: 'The generator hut', built: 'planned', at: [1.6, 4],
      there: 'The generator, dry; a bolted gate down to the yard', moves: 'A fan once it runs; the lights come on',
      enemies: 'Adders', story: 'Power for the station and the ferry',
    },
    {
      id: 'tower', name: 'The lookout tower, foot', built: 'planned', at: [-0.6, 2],
      there: 'The stairs up', moves: 'The tower creaking in the wind', enemies: '',
      story: '',
    },
    {
      id: 'tower-top', name: 'The lookout tower, top', built: 'planned', at: [-0.6, 0.6],
      there: 'The ferry key; the valley seen from above', moves: 'Smoke from the valley, cloud', enemies: 'Crows',
      story: "Smoke where Bravo's helicopter came down",
    },
    {
      id: 'bridge', name: 'The gorge, near bank', built: 'built', room: 'bridge', at: [6, 4.8],
      there: 'The footbridge, out in the middle; the cable ferry', moves: 'The river far below, the cable swaying',
      enemies: 'Adders', story: 'Built with the bridge whole; the plan breaks it',
    },
    {
      id: 'far-bank', name: 'The gorge, far bank', built: 'planned', at: [6, 6.4],
      there: "The valley trail on down; the lever for the bridge's missing section", moves: 'Spray from the falls',
      enemies: '', story: 'The way down to the logging camp (Act 2)',
    },
  ],
  links: [
    { from: 'ridge', to: 'trail', kind: 'walk' },
    { from: 'trail', to: 'yard', kind: 'walk' },
    { from: 'yard', to: 'cabin', kind: 'door' },
    { from: 'yard', to: 'shed', kind: 'door', opens: 'unlock-shed' },
    { from: 'yard', to: 'woods', kind: 'walk', opens: 'dog' },
    { from: 'woods', to: 'road', kind: 'walk' },
    { from: 'road', to: 'generator', kind: 'walk', opens: 'cut-chain' },
    { from: 'road', to: 'tower', kind: 'walk', opens: 'cut-chain' },
    { from: 'tower', to: 'tower-top', kind: 'ladder' },
    { from: 'generator', to: 'yard', kind: 'walk', opens: 'back-gate', shortcut: true },
    { from: 'yard', to: 'bridge', kind: 'walk', opens: 'winch-pine' },
    { from: 'bridge', to: 'far-bank', kind: 'ferry', opens: 'ride-ferry' },
    { from: 'far-bank', to: 'bridge', kind: 'walk', opens: 'lower-bridge', shortcut: true },
  ],
  steps: [
    { id: 'arrive', label: 'Reach the ranger station', at: 'yard', kind: 'learn', needs: [], built: 'built' },
    { id: 'logbook', label: "Read the logbook: the crank's in the shed", at: 'cabin', kind: 'learn', needs: ['arrive'], built: 'built', optional: true },
    { id: 'shed-key', label: 'Take the shed key', at: 'cabin', kind: 'find', needs: ['arrive'], built: 'built' },
    { id: 'dog', label: 'Survive the dog that comes for her', at: 'yard', kind: 'do', needs: ['shed-key'], built: 'built' },
    { id: 'unlock-shed', label: 'Unlock the shed', at: 'yard', kind: 'do', needs: ['shed-key'], built: 'built' },
    { id: 'crank', label: 'Take the winch crank', at: 'shed', kind: 'find', needs: ['unlock-shed'], built: 'built' },
    { id: 'jerrycan', label: 'Take the empty jerrycan', at: 'shed', kind: 'find', needs: ['unlock-shed'], built: 'planned' },
    { id: 'fuses', label: 'See the spare fuses (Act 2 sends her back)', at: 'shed', kind: 'learn', needs: ['unlock-shed'], built: 'planned', optional: true },
    { id: 'winch-pine', label: 'Winch the pine off the trail', at: 'yard', kind: 'do', needs: ['crank'], built: 'built' },
    { id: 'see-ferry', label: 'Find the bridge out and the ferry dead', at: 'bridge', kind: 'learn', needs: ['winch-pine'], built: 'planned', optional: true },
    { id: 'truck-keys', label: "Find the ranger: his truck keys", at: 'woods', kind: 'find', needs: ['dog'], built: 'planned' },
    { id: 'hose', label: 'Take the hose from the pump', at: 'woods', kind: 'find', needs: ['dog'], built: 'planned' },
    { id: 'fuel', label: "Siphon the truck's tank into the can", at: 'yard', kind: 'do', needs: ['jerrycan', 'hose'], built: 'planned' },
    { id: 'cutters', label: "Open the truck's toolbox: bolt cutters", at: 'yard', kind: 'find', needs: ['truck-keys'], built: 'planned' },
    { id: 'cut-chain', label: 'Cut the chain on the road gate', at: 'road', kind: 'do', needs: ['cutters'], built: 'planned' },
    { id: 'generator-on', label: 'Fuel the generator: the lights come on', at: 'generator', kind: 'do', needs: ['cut-chain', 'fuel'], built: 'planned' },
    { id: 'back-gate', label: 'Unbolt the gate down to the yard', at: 'generator', kind: 'shortcut', needs: ['cut-chain'], built: 'planned', optional: true },
    { id: 'radio', label: "The cabin radio works: Alpha's plans", at: 'cabin', kind: 'learn', needs: ['generator-on'], built: 'planned', optional: true },
    { id: 'ferry-key', label: "Climb the tower: the ferry key, and Bravo's smoke", at: 'tower-top', kind: 'find', needs: ['cut-chain'], built: 'planned' },
    { id: 'ride-ferry', label: 'Ride the cable ferry across', at: 'bridge', kind: 'do', needs: ['winch-pine', 'generator-on', 'ferry-key'], built: 'planned' },
    { id: 'lower-bridge', label: "Lower the bridge's missing section", at: 'far-bank', kind: 'shortcut', needs: ['ride-ferry'], built: 'planned', optional: true },
    { id: 'valley', label: 'On down the valley trail', at: 'far-bank', kind: 'goal', needs: ['ride-ferry'], built: 'planned' },
  ],
};
