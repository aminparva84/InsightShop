import React, { useState } from 'react';
import './FilterBar.css';

const FilterBar = ({ 
  categories = [], 
  colors = [], 
  sizes = [],
  fabrics = [],
  seasons = [],
  clothingCategories = [],
  priceRange = { min: 0, max: 1000 },
  onFilterChange,
  activeFilters = {}
}) => {
  const [isOpen, setIsOpen] = useState({
    category: false,
    color: false,
    size: false,
    fabric: false,
    season: false,
    clothingCategory: false,
    price: false
  });

  const toggleDropdown = (filterType) => {
    setIsOpen(prev => ({
      ...prev,
      [filterType]: !prev[filterType]
    }));
  };

  const handleFilterSelect = (filterType, value) => {
    onFilterChange(filterType, value);
    setIsOpen(prev => ({
      ...prev,
      [filterType]: false
    }));
  };

  const clearFilter = (filterType) => {
    onFilterChange(filterType, '');
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (activeFilters.search) count++;
    if (activeFilters.category) count++;
    if (activeFilters.color) count++;
    if (activeFilters.size) count++;
    if (activeFilters.fabric) count++;
    if (activeFilters.season) count++;
    if (activeFilters.clothing_category) count++;
    if (activeFilters.minPrice || activeFilters.maxPrice) count++;
    return count;
  };

  const activeCount = getActiveFilterCount();

  return (
    <div className="filter-bar">
      <div className="filter-bar-container">
        <div className="filter-bar-header">
          <h3>Filters</h3>
          {activeCount > 0 && (
            <span className="active-filter-count">{activeCount} active</span>
          )}
        </div>

        {/* Search Input */}
        <div className="filter-search-container">
          <input
            type="text"
            value={activeFilters.search || ''}
            onChange={(e) => onFilterChange('search', e.target.value)}
            placeholder="Search products..."
            className="filter-search-input"
          />
        </div>

        <div className="filter-dropdowns">
          {/* Category Filter */}
          <div className="filter-dropdown">
            <button
              className={`filter-button ${activeFilters.category ? 'active' : ''}`}
              onClick={() => toggleDropdown('category')}
            >
              <span>Category</span>
              {activeFilters.category && (
                <span className="filter-value">{activeFilters.category}</span>
              )}
              <span className="dropdown-arrow">▼</span>
            </button>
            {isOpen.category && (
              <div className="dropdown-menu">
                <div className="dropdown-header">
                  <span>Select Category</span>
                  {activeFilters.category && (
                    <button onClick={() => clearFilter('category')} className="clear-btn">Clear</button>
                  )}
                </div>
                <div className="dropdown-options">
                  {categories.map(cat => (
                    <div
                      key={cat}
                      className={`dropdown-option ${activeFilters.category === cat ? 'selected' : ''}`}
                      onClick={() => handleFilterSelect('category', cat)}
                    >
                      {cat.charAt(0).toUpperCase() + cat.slice(1)}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Color Filter */}
          <div className="filter-dropdown">
            <button
              className={`filter-button ${activeFilters.color ? 'active' : ''}`}
              onClick={() => toggleDropdown('color')}
            >
              <span>Color</span>
              {activeFilters.color && (
                <span className="filter-value">{activeFilters.color}</span>
              )}
              <span className="dropdown-arrow">▼</span>
            </button>
            {isOpen.color && (
              <div className="dropdown-menu">
                <div className="dropdown-header">
                  <span>Select Color</span>
                  {activeFilters.color && (
                    <button onClick={() => clearFilter('color')} className="clear-btn">Clear</button>
                  )}
                </div>
                <div className="dropdown-options">
                  {colors.map(color => (
                    <div
                      key={color}
                      className={`dropdown-option ${activeFilters.color === color ? 'selected' : ''}`}
                      onClick={() => handleFilterSelect('color', color)}
                    >
                      <span className="color-indicator" style={{ backgroundColor: color.toLowerCase() }}></span>
                      {color}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Size Filter */}
          {sizes.length > 0 && (
            <div className="filter-dropdown">
              <button
                className={`filter-button ${activeFilters.size ? 'active' : ''}`}
                onClick={() => toggleDropdown('size')}
              >
                <span>Size</span>
                {activeFilters.size && (
                  <span className="filter-value">{activeFilters.size}</span>
                )}
                <span className="dropdown-arrow">▼</span>
              </button>
              {isOpen.size && (
                <div className="dropdown-menu">
                  <div className="dropdown-header">
                    <span>Select Size</span>
                    {activeFilters.size && (
                      <button onClick={() => clearFilter('size')} className="clear-btn">Clear</button>
                    )}
                  </div>
                  <div className="dropdown-options">
                    {sizes.map(size => (
                      <div
                        key={size}
                        className={`dropdown-option ${activeFilters.size === size ? 'selected' : ''}`}
                        onClick={() => handleFilterSelect('size', size)}
                      >
                        {size}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Fabric Filter */}
          {fabrics.length > 0 && (
            <div className="filter-dropdown">
              <button
                className={`filter-button ${activeFilters.fabric ? 'active' : ''}`}
                onClick={() => toggleDropdown('fabric')}
              >
                <span>Fabric</span>
                {activeFilters.fabric && (
                  <span className="filter-value">{activeFilters.fabric}</span>
                )}
                <span className="dropdown-arrow">▼</span>
              </button>
              {isOpen.fabric && (
                <div className="dropdown-menu">
                  <div className="dropdown-header">
                    <span>Select Fabric</span>
                    {activeFilters.fabric && (
                      <button onClick={() => clearFilter('fabric')} className="clear-btn">Clear</button>
                    )}
                  </div>
                  <div className="dropdown-options">
                    {fabrics.map(fabric => (
                      <div
                        key={fabric}
                        className={`dropdown-option ${activeFilters.fabric === fabric ? 'selected' : ''}`}
                        onClick={() => handleFilterSelect('fabric', fabric)}
                      >
                        {fabric}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Season Filter */}
          {seasons.length > 0 && (
            <div className="filter-dropdown">
              <button
                className={`filter-button ${activeFilters.season ? 'active' : ''}`}
                onClick={() => toggleDropdown('season')}
              >
                <span>Season</span>
                {activeFilters.season && (
                  <span className="filter-value">{activeFilters.season.replace('_', ' ')}</span>
                )}
                <span className="dropdown-arrow">▼</span>
              </button>
              {isOpen.season && (
                <div className="dropdown-menu">
                  <div className="dropdown-header">
                    <span>Select Season</span>
                    {activeFilters.season && (
                      <button onClick={() => clearFilter('season')} className="clear-btn">Clear</button>
                    )}
                  </div>
                  <div className="dropdown-options">
                    {seasons.map(season => (
                      <div
                        key={season}
                        className={`dropdown-option ${activeFilters.season === season ? 'selected' : ''}`}
                        onClick={() => handleFilterSelect('season', season)}
                      >
                        {season.replace('_', ' ')}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Clothing Category Filter */}
          {clothingCategories.length > 0 && (
            <div className="filter-dropdown">
              <button
                className={`filter-button ${activeFilters.clothing_category ? 'active' : ''}`}
                onClick={() => toggleDropdown('clothingCategory')}
              >
                <span>Clothing</span>
                {activeFilters.clothing_category && (
                  <span className="filter-value">{activeFilters.clothing_category.replace(/_/g, ' ')}</span>
                )}
                <span className="dropdown-arrow">▼</span>
              </button>
              {isOpen.clothingCategory && (
                <div className="dropdown-menu">
                  <div className="dropdown-header">
                    <span>Select clothing type</span>
                    {activeFilters.clothing_category && (
                      <button onClick={() => clearFilter('clothing_category')} className="clear-btn">Clear</button>
                    )}
                  </div>
                  <div className="dropdown-options">
                    {clothingCategories.map(cat => (
                      <div
                        key={cat}
                        className={`dropdown-option ${activeFilters.clothing_category === cat ? 'selected' : ''}`}
                        onClick={() => handleFilterSelect('clothing_category', cat)}
                      >
                        {cat.replace(/_/g, ' ')}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Price Range Filter */}
          <div className="filter-dropdown">
            <button
              className={`filter-button ${(activeFilters.minPrice || activeFilters.maxPrice) ? 'active' : ''}`}
              onClick={() => toggleDropdown('price')}
            >
              <span>Price</span>
              {(activeFilters.minPrice || activeFilters.maxPrice) && (
                <span className="filter-value">
                  ${activeFilters.minPrice || priceRange.min} - ${activeFilters.maxPrice || priceRange.max}
                </span>
              )}
              <span className="dropdown-arrow">▼</span>
            </button>
            {isOpen.price && (
              <div className="dropdown-menu price-menu">
                <div className="dropdown-header">
                  <span>Price Range</span>
                  {(activeFilters.minPrice || activeFilters.maxPrice) && (
                    <button onClick={() => {
                      clearFilter('minPrice');
                      clearFilter('maxPrice');
                    }} className="clear-btn">Clear</button>
                  )}
                </div>
                <div className="price-inputs">
                  <div className="price-input-group">
                    <label>Min Price</label>
                    <input
                      type="number"
                      min={priceRange.min}
                      max={priceRange.max}
                      value={activeFilters.minPrice || ''}
                      onChange={(e) => onFilterChange('minPrice', e.target.value)}
                      placeholder={`$${priceRange.min}`}
                    />
                  </div>
                  <div className="price-input-group">
                    <label>Max Price</label>
                    <input
                      type="number"
                      min={priceRange.min}
                      max={priceRange.max}
                      value={activeFilters.maxPrice || ''}
                      onChange={(e) => onFilterChange('maxPrice', e.target.value)}
                      placeholder={`$${priceRange.max}`}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Clear All Filters */}
          {activeCount > 0 && (
            <button
              className="clear-all-filters"
              onClick={() => {
                onFilterChange('clearAll', true);
                setIsOpen({
                  category: false,
                  color: false,
                  size: false,
                  fabric: false,
                  season: false,
                  clothingCategory: false,
                  price: false
                });
              }}
            >
              Clear All
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default FilterBar;

