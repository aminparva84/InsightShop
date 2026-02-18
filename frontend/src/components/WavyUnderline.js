import React from 'react';

/**
 * Decorative wavy underline SVG — smooth horizontal wave.
 * Used under section titles (e.g. Featured Products, Seasonal Shopping).
 */
const WavyUnderline = ({ color = '#373F2E', className = '', width = '100%', height = 20, strokeWidth = 6, ...props }) => (
  <svg
    className={className}
    width={width}
    height={height}
    viewBox="0 0 200 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
    {...props}
  >
    <path
      d="M 0 12 Q 50 2 100 12 Q 150 22 200 12"
      stroke={color}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export default WavyUnderline;
