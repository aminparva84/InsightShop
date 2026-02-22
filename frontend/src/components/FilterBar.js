import React, { useState, useRef, useEffect } from 'react';
import './FilterBar.css';

const CLOSED_STATE = {
  category: false,
  color: false,
  size: false,
  fabric: false,
  season: false,
  clothingCategory: false,
  price: false,
  onSale: false
};

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
  const [isOpen, setIsOpen] = useState({ ...CLOSED_STATE });
  const filterBarRef = useRef(null);

  // Close all dropdowns when clicking outside the filter bar
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (filterBarRef.current && !filterBarRef.current.contains(e.target)) {
        setIsOpen({ ...CLOSED_STATE });
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleDropdown = (filterType) => {
    setIsOpen(prev => ({
      ...CLOSED_STATE,
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
    if (activeFilters.on_sale) count++;
    return count;
  };

  const activeCount = getActiveFilterCount();

  return (
    <div className="filter-bar" ref={filterBarRef}>
      <div className="filter-bar-container">
        <div className="filter-bar-header">
          <h3>Filters</h3>
          {activeCount > 0 && (
            <span className="active-filter-count">{activeCount} active</span>
          )}
        </div>

        {/* Search Input – same style as navbar search bar */}
        <div className="filter-search-container">
          <div className="filter-search-bar">
            <svg className="filter-search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M21 21L16.65 16.65M19 11C19 15.4183 15.4183 19 11 19C6.58172 19 3 15.4183 3 11C3 6.58172 6.58172 3 11 3C15.4183 3 19 6.58172 19 11Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <input
              type="search"
              value={activeFilters.search || ''}
              onChange={(e) => onFilterChange('search', e.target.value)}
              placeholder="SEARCH"
              className="filter-search-input"
              aria-label="Search products"
              autoComplete="off"
            />
          </div>
        </div>

        <div className="filter-dropdowns">
          {/* On Sale Filter */}
          <div className={`filter-dropdown ${isOpen.onSale ? 'open' : ''}`}>
            <button
              className={`filter-button ${activeFilters.on_sale ? 'active' : ''}`}
              onClick={() => toggleDropdown('onSale')}
            >
              <span>Sales</span>
              {activeFilters.on_sale && (
                <span className="filter-value">On sale</span>
              )}
              <span className="dropdown-arrow">▼</span>
            </button>
            {isOpen.onSale && (
              <div className="dropdown-menu">
                <div className="dropdown-header">
                  <span>Show</span>
                  {activeFilters.on_sale && (
                    <button onClick={() => clearFilter('on_sale')} className="clear-btn">Clear</button>
                  )}
                </div>
                <div className="dropdown-options">
                  <div
                    className={`dropdown-option ${activeFilters.on_sale ? 'selected' : ''}`}
                    onClick={() => handleFilterSelect('on_sale', '1')}
                  >
                    On sale only
                  </div>
                  <div
                    className={`dropdown-option ${!activeFilters.on_sale ? 'selected' : ''}`}
                    onClick={() => handleFilterSelect('on_sale', '')}
                  >
                    All products
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Gender Filter */}
          <div className={`filter-dropdown ${isOpen.category ? 'open' : ''}`}>
            <button
              className={`filter-button ${activeFilters.category ? 'active' : ''}`}
              onClick={() => toggleDropdown('category')}
            >
              <span>Gender</span>
              {activeFilters.category && (
                <span className="filter-value">{activeFilters.category}</span>
              )}
              <span className="dropdown-arrow">▼</span>
            </button>
            {isOpen.category && (
              <div className="dropdown-menu">
                <div className="dropdown-header">
                  <span>Select Gender</span>
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
          <div className={`filter-dropdown ${isOpen.color ? 'open' : ''}`}>
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
            <div className={`filter-dropdown ${isOpen.size ? 'open' : ''}`}>
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
            <div className={`filter-dropdown ${isOpen.fabric ? 'open' : ''}`}>
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
            <div className={`filter-dropdown ${isOpen.season ? 'open' : ''}`}>
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
            <div className={`filter-dropdown ${isOpen.clothingCategory ? 'open' : ''}`}>
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
          <div className={`filter-dropdown ${isOpen.price ? 'open' : ''}`}>
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
                setIsOpen({ ...CLOSED_STATE });
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

