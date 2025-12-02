import React from 'react';
import './ColorSwatches.css';

const ColorSwatches = ({ colors = [], selectedColor, onColorSelect }) => {
  // Only show color selector if there are multiple colors available
  if (!colors || colors.length <= 1) {
    return null;
  }

  const getColorValue = (colorName) => {
    const colorMap = {
      'black': '#000000',
      'white': '#FFFFFF',
      'red': '#FF0000',
      'blue': '#0000FF',
      'green': '#008000',
      'yellow': '#FFFF00',
      'gray': '#808080',
      'grey': '#808080',
      'pink': '#FFC0CB',
      'purple': '#800080',
      'orange': '#FFA500',
      'brown': '#A52A2A',
      'navy': '#000080',
      'beige': '#F5F5DC',
      'maroon': '#800000',
      'teal': '#008080'
    };
    return colorMap[colorName?.toLowerCase()] || '#CCCCCC';
  };

  // Show all colors - no limit
  const displayColors = colors;

  return (
    <div className="color-swatches">
      <label className="swatch-label">Available Colors ({displayColors.length}):</label>
      <div className="swatch-container">
        {displayColors.map((color, index) => (
          <button
            key={index}
            className={`color-swatch ${selectedColor === color ? 'selected' : ''}`}
            style={{ backgroundColor: getColorValue(color) }}
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              if (onColorSelect) {
                onColorSelect(color);
              }
            }}
            title={color}
            aria-label={`Select color ${color}`}
          >
            {selectedColor === color && <span className="checkmark">✓</span>}
          </button>
        ))}
      </div>
    </div>
  );
};

export default ColorSwatches;

