// Theme tokens for the four ProjectBrief theme keys. Starting palette from
// docs/healthtech/ux/03_SCREENS_DESIGN.md; semantic tokens added here. The
// "-inspired" themes make no official KMITL/ICT identity claim and use no logos.
const lightSemantic = {
  dangerBg: '#FDECEC', dangerText: '#8A1C1C',
  warningBg: '#FFF4D6', warningText: '#6B4500',
  successBg: '#E7F5EC', successText: '#1D5C33',
  infoBg: '#E8F0FB', infoText: '#1D4A86',
  syntheticBg: '#F3E8FF', syntheticText: '#5B2A86',
  markBg: '#FFE08A', markText: '#172033',
};

export const THEMES = {
  'formal-light': {
    canvas: '#F5F7FA', surface: '#FFFFFF', surfaceAlt: '#EEF2F7', text: '#172033', mutedText: '#475569', border: '#6B7A90',
    primary: '#173F6B', onPrimary: '#FFFFFF', focusRing: '#215EB0', ...lightSemantic,
  },
  'formal-dark': {
    canvas: '#0B1220', surface: '#152033', surfaceAlt: '#1C2A42', text: '#E8EDF5', mutedText: '#B8C4D6', border: '#7F8FA8',
    primary: '#9DC6F0', onPrimary: '#0B1220', focusRing: '#9DC6F0',
    dangerBg: '#3A1518', dangerText: '#FFB4B4', warningBg: '#3A2C0A', warningText: '#FFD98A',
    successBg: '#12301F', successText: '#9BE3B4', infoBg: '#132B4A', infoText: '#A9CDF5',
    syntheticBg: '#2E1C45', syntheticText: '#DCC2FF', markBg: '#6B5410', markText: '#FFF4D0',
  },
  'kmitl-inspired': {
    canvas: '#FAF7F3', surface: '#FFFFFF', surfaceAlt: '#F3EDE6', text: '#28201B', mutedText: '#62544A', border: '#8A7868',
    primary: '#93400A', onPrimary: '#FFFFFF', focusRing: '#93400A', ...lightSemantic, markText: '#28201B',
  },
  'ict-inspired': {
    canvas: '#F4F8F9', surface: '#FFFFFF', surfaceAlt: '#E6F0F2', text: '#102E38', mutedText: '#415D67', border: '#5F7E88',
    primary: '#0A5967', onPrimary: '#FFFFFF', focusRing: '#0A5967', ...lightSemantic, markText: '#102E38',
  },
};

export const THEME_KEYS = Object.keys(THEMES);

/** Foreground/background pairs actually used by the stylesheet, with WCAG minimums. */
export const USED_PAIRS = [
  ['text', 'canvas', 4.5], ['text', 'surface', 4.5], ['text', 'surfaceAlt', 4.5],
  ['mutedText', 'canvas', 4.5], ['mutedText', 'surface', 4.5], ['mutedText', 'surfaceAlt', 4.5],
  ['primary', 'surface', 4.5], ['primary', 'canvas', 4.5], ['onPrimary', 'primary', 4.5],
  ['dangerText', 'dangerBg', 4.5], ['warningText', 'warningBg', 4.5], ['successText', 'successBg', 4.5],
  ['infoText', 'infoBg', 4.5], ['syntheticText', 'syntheticBg', 4.5], ['markText', 'markBg', 4.5],
  ['focusRing', 'canvas', 3], ['focusRing', 'surface', 3], ['border', 'surface', 3], ['border', 'canvas', 3],
];

export function luminance(hex) {
  const rgb = [1, 3, 5].map((j) => parseInt(hex.slice(j, j + 2), 16) / 255);
  const lin = rgb.map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
}

export function contrast(a, b) {
  const [x, y] = [luminance(a), luminance(b)].sort((p, q) => p - q);
  return (y + 0.05) / (x + 0.05);
}

export function applyTheme(root, key) {
  const theme = THEMES[key] || THEMES['formal-light'];
  for (const [name, value] of Object.entries(theme)) root.style.setProperty(`--${name}`, value);
  root.dataset.theme = THEMES[key] ? key : 'formal-light';
  root.style.colorScheme = key === 'formal-dark' ? 'dark' : 'light';
}
