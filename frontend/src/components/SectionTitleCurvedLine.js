import React from 'react';

/**
 * Curved line SVG used to the right of section titles (same color as title).
 * Place inside .section-title-row after the title; it flexes to fill remaining space.
 */
const SectionTitleCurvedLine = ({ color = 'currentColor', className = 'section-title-curved-line' }) => (
  <div
    className={className}
    aria-hidden="true"
    style={{ color }}
  >
    <svg viewBox="0 0 200 32" preserveAspectRatio="none" aria-hidden="true">
      <path
        d="M 0 16 Q 50 0 100 16 Q 150 32 200 16"
        fill="none"
        stroke="currentColor"
        strokeWidth="4"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  </div>
);

export default SectionTitleCurvedLine;
