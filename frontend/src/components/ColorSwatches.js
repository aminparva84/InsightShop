import React from 'react';
import './ColorSwatches.css';

/** Inline color lookup to avoid circular dependency with utils/colorMap (used by ProductCard). */
function getColorHex(colorName) {
  if (!colorName || typeof colorName !== 'string') return '#D4C4A8';
  const key = colorName.toLowerCase().trim();
  const map = {
    black: '#000000', white: '#FFFFFF', grey: '#808080', gray: '#808080', red: '#C41E3A',
    blue: '#2563EB', green: '#16A34A', yellow: '#EAB308', pink: '#EC4899', purple: '#7C3AED',
    orange: '#EA580C', brown: '#78350F', navy: '#1E3A8A', beige: '#D4B896', maroon: '#800020',
    burgundy: '#722F37', teal: '#0D9488', cream: '#FFFDD0', tan: '#C4A574', gold: '#B8860B',
    silver: '#9CA3AF', charcoal: '#374151', 'off-white': '#FAF9F6', 'off white': '#FAF9F6',
    olive: '#6B8E23', 'olive green': '#6B8E23', 'forest green': '#228B22', 'dark green': '#14532D',
    'sage green': '#87AE73', sage: '#87AE73', 'light blue': '#7DD3FC', 'sky blue': '#0EA5E9',
    'dark brown': '#422006', 'caramel brown': '#C68B59', 'cognac brown': '#9A4638',
    'tan beige': '#D4B896', 'light brown': '#A16207', 'teal & rust plaid': '#5F7C6F',
    'khaki & brown plaid': '#8B7355', 'beige & light blue plaid': '#A8C5C5',
    'beige, tan & red plaid': '#B8956E', 'red, orange & beige plaid': '#C47B5B',
    'dark olive & tan plaid': '#5C6B4D', 'tan & dark brown plaid': '#6B5344',
    'brown & rust plaid': '#8B4513', 'blue-grey to rust ombre': '#7D6E83',
    'rose gold': '#B76E79', bronze: '#CD7F32', gunmetal: '#2C3539', tortoise: '#8B6914',
    'pale yellow': '#FEF08A', 'light yellow': '#FEF9C3', mustard: '#E4A853',
    rust: '#B7410E', sienna: '#A0522D',
  };
  if (map[key]) return map[key];
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

/**
 * Whether a color is in stock.
 * - If variationAvailability is provided: in stock if there exists (selectedSize or any size, color) with stock_quantity > 0.
 * - Otherwise all colors are selectable (no variation data).
 */
function isColorInStock(color, variationAvailability, selectedSize) {
  if (!variationAvailability || variationAvailability.length === 0) return true;
  const norm = (s) => String(s).trim().toLowerCase();
  if (selectedSize) {
    const v = variationAvailability.find(
      (x) => norm(x.size) === norm(selectedSize) && norm(x.color) === norm(color)
    );
    return v && Number(v.stock_quantity) > 0;
  }
  return variationAvailability.some(
    (v) => norm(v.color) === norm(color) && Number(v.stock_quantity) > 0
  );
}

const ColorSwatches = ({
  colors = [],
  selectedColor,
  onColorSelect,
  variationAvailability = null,
  selectedSize = null,
}) => {
  if (!colors || colors.length <= 1) {
    return null;
  }

  const displayColors = colors;

  return (
    <div className="color-swatches">
      <label className="swatch-label">Colors:</label>
      <div className="swatch-container">
        {displayColors.map((color, index) => {
          const inStock = isColorInStock(color, variationAvailability, selectedSize);
          const isOutOfStock = !inStock;
          return (
            <button
              key={index}
              type="button"
              className={`color-swatch ${selectedColor === color ? 'selected' : ''} ${isOutOfStock ? 'out-of-stock' : ''}`}
              style={{ backgroundColor: getColorHex(color) }}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                if (!isOutOfStock && onColorSelect) {
                  onColorSelect(color);
                }
              }}
              disabled={isOutOfStock}
              tabIndex={isOutOfStock ? -1 : 0}
              aria-disabled={isOutOfStock}
              aria-label={isOutOfStock ? `${color} – Unavailable` : `Select color ${color}`}
              title={
                isOutOfStock
                  ? 'This color is not available' + (selectedSize ? ` in size ${selectedSize}` : '')
                  : color
              }
            >
              {selectedColor === color && !isOutOfStock && <span className="checkmark">✓</span>}
              {isOutOfStock && <span className="color-swatch-strike" aria-hidden />}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default ColorSwatches;

