// Research: where each place sits on the mountain, in metres (x east, y
// south, down the slope), laid out by hand so the map reads as country, not
// a diagram. The summit is top right, the ranger station in the middle, the
// camp and the road west, the quarry and the mine east, the skyway drops
// south to the valley, and the estate is at the bottom.
export const LAYOUT: Record<string, readonly [number, number]> = {
  // The ranger station and the gorge.
  ridge: [300, 18],
  trail: [302, 52],
  yard: [300, 96],
  cabin: [327, 86],
  shed: [324, 110],
  woods: [258, 104],
  den: [246, 74],
  bridge: [300, 148],
  platform: [300, 190],
  booth: [323, 183],
  // Logging Camp 4, north-west.
  'logging-road': [205, 76],
  'camp-gate': [170, 74],
  'camp-yard': [128, 78],
  bunkhouse: [126, 56],
  office: [101, 62],
  mess: [100, 82],
  depot: [106, 101],
  workshop: [130, 101],
  sawmill: [152, 47],
  pond: [184, 38],
  flume: [222, 36],
  // The forestry road and the lookout, south-west.
  road: [246, 142],
  washout: [206, 152],
  generator: [204, 173],
  'tower-foot': [160, 150],
  'tower-stairs': [146, 141],
  'tower-top': [134, 133],
  switch: [214, 203],
  'line-track': [256, 206],
  // Hal's cottage and the quarry, east.
  'east-path': [366, 204],
  cottage: [370, 182],
  quarry: [428, 204],
  'quarry-office': [432, 183],
  // The silver mine, further east and up.
  'mine-entrance': [472, 186],
  tunnel: [486, 162],
  'mine-office': [500, 162],
  junction: [486, 136],
  gallery: [465, 129],
  'mine-lift': [489, 116],
  // The summit, top right.
  'summit-trail': [478, 62],
  weather: [456, 47],
  mast: [520, 34],
  // The skyway down.
  car: [300, 245],
  pylon: [300, 300],
  // The valley.
  'valley-path': [300, 352],
  'lower-yard': [352, 360],
  'lower-station': [378, 354],
  crash: [244, 362],
  creek: [300, 398],
  lodge: [336, 406],
  // The estate.
  'estate-wall': [300, 446],
  kennels: [300, 476],
  'back-garden': [300, 512],
  'garden-shed': [331, 508],
  cellar: [300, 542],
  wine: [318, 545],
  crawl: [300, 558],
  save: [300, 574],
};
