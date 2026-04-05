/**
 * Theme color constants shared between CSS (styles.css) and d3 rendering.
 * Keep in sync with the @theme block in styles.css.
 */
export const THEME = {
  // Surface layers
  panelBase: '#05080f',
  panel: '#0b1121',
  panelRaised: '#111a2e',

  // Borders
  edge: '#1a2744',
  edgeBright: '#263a5c',

  // Signal accents
  signalClear: '#22c55e',
  signalClearDim: '#16a34a',
  signalCaution: '#eab308',
  signalCautionDim: '#ca8a04',
  signalInfo: '#38bdf8',
  signalInfoDim: '#0ea5e9',

  // Text
  ink: '#c8d1de',
  inkMuted: '#6b7f99',
} as const;
