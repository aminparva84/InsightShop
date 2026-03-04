/**
 * Maps product color names (from API/seed) to hex for swatches.
 * Keys are lowercase; use getColorHex(name) for lookup.
 * Covers all colors used in seed_products.py COLOR_CONFIG and product data.
 */
const COLOR_MAP = {
  // Basics
  black: '#000000',
  white: '#FFFFFF',
  grey: '#808080',
  gray: '#808080',
  red: '#C41E3A',
  blue: '#2563EB',
  green: '#16A34A',
  yellow: '#EAB308',
  pink: '#EC4899',
  purple: '#7C3AED',
  orange: '#EA580C',
  brown: '#78350F',
  navy: '#1E3A8A',
  beige: '#D4B896',
  maroon: '#800020',
  burgundy: '#722F37',
  teal: '#0D9488',
  cream: '#FFFDD0',
  tan: '#C4A574',
  gold: '#B8860B',
  silver: '#9CA3AF',
  charcoal: '#374151',
  'off-white': '#FAF9F6',
  'off white': '#FAF9F6',

  // Greens
  olive: '#6B8E23',
  'olive green': '#6B8E23',
  'forest green': '#228B22',
  'dark green': '#14532D',
  'sage green': '#87AE73',
  sage: '#87AE73',

  // Blues
  'light blue': '#7DD3FC',
  'sky blue': '#0EA5E9',

  // Browns / neutrals
  'dark brown': '#422006',
  'caramel brown': '#C68B59',
  'cognac brown': '#9A4638',
  'tan beige': '#D4B896',
  'light brown': '#A16207',

  // Plaids / multi (representative color)
  'teal & rust plaid': '#5F7C6F',
  'khaki & brown plaid': '#8B7355',
  'beige & light blue plaid': '#A8C5C5',
  'beige, tan & red plaid': '#B8956E',
  'red, orange & beige plaid': '#C47B5B',
  'dark olive & tan plaid': '#5C6B4D',
  'tan & dark brown plaid': '#6B5344',
  'brown & rust plaid': '#8B4513',
  'blue-grey to rust ombre': '#7D6E83',

  // Metals / accessories
  'rose gold': '#B76E79',
  bronze: '#CD7F32',
  gunmetal: '#2C3539',
  tortoise: '#8B6914',

  // Yellows
  'pale yellow': '#FEF08A',
  'light yellow': '#FEF9C3',
  mustard: '#E4A853',

  // Other
  rust: '#B7410E',
  sienna: '#A0522D',
};

/**
 * Returns hex for a product color name. Normalizes to lowercase for lookup.
 * If not in map, tries keyword fallback (e.g. "something blue" -> light blue).
 * Otherwise returns a soft neutral (not gray) so unknown colors still look intentional.
 */
export function getColorHex(colorName) {
  if (!colorName || typeof colorName !== 'string') return '#D4C4A8';
  const key = colorName.toLowerCase().trim();
  if (COLOR_MAP[key]) return COLOR_MAP[key];
  // Keyword fallbacks for unknown names
  if (/\bblue\b/i.test(key)) return '#7DD3FC';
  if (/\bgreen\b/i.test(key)) return '#6B8E23';
  if (/\bblack\b/i.test(key)) return '#000000';
  if (/\bwhite\b|off-white|cream\b/i.test(key)) return '#FAF9F6';
  if (/\bbrown\b|tan\b|beige\b|camel\b/i.test(key)) return '#C4A574';
  if (/\bred\b|burgundy\b|maroon\b/i.test(key)) return '#B91C1C';
  if (/\bgold\b/i.test(key)) return '#B8860B';
  if (/\bsilver\b|grey\b|gray\b/i.test(key)) return '#9CA3AF';
  if (/\bnavy\b/i.test(key)) return '#1E3A8A';
  if (/\bolive\b/i.test(key)) return '#6B8E23';
  if (/\bpink\b/i.test(key)) return '#EC4899';
  if (/\borange\b|rust\b/i.test(key)) return '#EA580C';
  if (/\bpurple\b/i.test(key)) return '#7C3AED';
  if (/\byellow\b/i.test(key)) return '#EAB308';
  return '#D4C4A8';
}
