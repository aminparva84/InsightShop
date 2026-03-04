/**
 * Variation availability helpers: used to keep size/color selection in sync with in-stock combinations.
 * All comparisons use normalized (trimmed, lowercased) strings.
 */

const norm = (s) => String(s).trim().toLowerCase();

export function isCombinationInStock(availability, size, color) {
  if (!availability?.length) return false;
  const v = availability.find(
    (x) => norm(x.size) === norm(size) && norm(x.color) === norm(color) && Number(x.stock_quantity) > 0
  );
  return !!v;
}

/** First color that has stock for the given size. */
export function getFirstInStockColorForSize(availability, size, colors) {
  if (!availability?.length || !colors?.length) return colors[0];
  for (const c of colors) {
    const v = availability.find(
      (x) => norm(x.size) === norm(size) && norm(x.color) === norm(c) && Number(x.stock_quantity) > 0
    );
    if (v) return c;
  }
  return colors[0];
}

/** First size that has stock for the given color. */
export function getFirstInStockSizeForColor(availability, color, sizes) {
  if (!availability?.length || !sizes?.length) return sizes[0];
  for (const s of sizes) {
    const v = availability.find(
      (x) => norm(x.size) === norm(s) && norm(x.color) === norm(color) && Number(x.stock_quantity) > 0
    );
    if (v) return s;
  }
  return sizes[0];
}
