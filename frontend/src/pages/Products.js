import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import axios from 'axios';
import ProductGrid from '../components/ProductGrid';
import FilterBar from '../components/FilterBar';
import './Products.css';

const Products = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [allProducts, setAllProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState([]);
  const [colors, setColors] = useState([]);
  const [sizes, setSizes] = useState([]);
  const [fabrics, setFabrics] = useState([]);
  const [priceRange, setPriceRange] = useState({ min: 0, max: 1000 });
  const [selectedForCompare, setSelectedForCompare] = useState([]);
  const [filters, setFilters] = useState({
    category: searchParams.get('category') || '',
    color: searchParams.get('color') || '',
    size: searchParams.get('size') || '',
    fabric: searchParams.get('fabric') || '',
    minPrice: searchParams.get('minPrice') || '',
    maxPrice: searchParams.get('maxPrice') || '',
    search: searchParams.get('search') || '',
    ai_results: searchParams.get('ai_results') || ''
  });

  useEffect(() => {
    fetchCategories();
    fetchColors();
    fetchSizes();
    fetchFabrics();
    fetchPriceRange();
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [filters]);

  const fetchCategories = async () => {
    try {
      const response = await axios.get('/api/products/categories');
      setCategories(response.data.categories);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchColors = async () => {
    try {
      const response = await axios.get('/api/products/colors');
      setColors(response.data.colors);
    } catch (error) {
      console.error('Error fetching colors:', error);
    }
  };

  const fetchSizes = async () => {
    try {
      const response = await axios.get('/api/products/sizes');
      setSizes(response.data.sizes || []);
    } catch (error) {
      console.error('Error fetching sizes:', error);
    }
  };

  const fetchFabrics = async () => {
    try {
      const response = await axios.get('/api/products/fabrics');
      setFabrics(response.data.fabrics || []);
    } catch (error) {
      console.error('Error fetching fabrics:', error);
    }
  };

  const fetchPriceRange = async () => {
    try {
      const response = await axios.get('/api/products/price-range');
      if (response.data.min !== undefined && response.data.max !== undefined) {
        setPriceRange({ min: response.data.min, max: response.data.max });
      }
    } catch (error) {
      console.error('Error fetching price range:', error);
    }
  };

  const fetchProducts = async () => {
    try {
      setLoading(true);
      
      // If AI results are specified, fetch those specific products
      if (filters.ai_results) {
        const productIds = filters.ai_results.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
        console.log('AI Results - Product IDs:', productIds);
        
        if (productIds.length > 0) {
          // Fetch products by IDs using the ids parameter
          const idsParam = productIds.join(',');
          const response = await axios.get(`/api/products?ids=${idsParam}`);
          
          console.log('Products fetched by IDs:', response.data.products.length);
          console.log('AI Products:', response.data.products.map(p => ({ id: p.id, name: p.name })));
          
          setAllProducts(response.data.products);
          setProducts(response.data.products);
          setLoading(false);
          return;
        }
      }
      
      // Regular filtering
      const params = new URLSearchParams();
      if (filters.category) params.append('category', filters.category);
      if (filters.color) params.append('color', filters.color);
      if (filters.size) params.append('size', filters.size);
      if (filters.fabric) params.append('fabric', filters.fabric);
      if (filters.minPrice) params.append('min_price', filters.minPrice);
      if (filters.maxPrice) params.append('max_price', filters.maxPrice);
      if (filters.search) params.append('search', filters.search);

      const response = await axios.get(`/api/products?${params.toString()}`);
      setProducts(response.data.products);
      setAllProducts(response.data.products);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    if (key === 'clearAll') {
      handleClearFilters();
      return;
    }
    
    const newFilters = { ...filters, [key]: value };
    // Clear AI results when manually filtering
    if (key !== 'ai_results') {
      newFilters.ai_results = '';
    }
    setFilters(newFilters);
    const params = { ...newFilters };
    if (!params.ai_results) delete params.ai_results;
    // Remove empty filter values
    Object.keys(params).forEach(k => {
      if (params[k] === '' || params[k] === null || params[k] === undefined) {
        delete params[k];
      }
    });
    setSearchParams(params);
  };
  
  const handleClearFilters = () => {
    const clearedFilters = {
      category: '',
      color: '',
      size: '',
      fabric: '',
      minPrice: priceRange.min,
      maxPrice: priceRange.max,
      search: '',
      ai_results: filters.ai_results // Keep AI results if they exist
    };
    setFilters(clearedFilters);
    setSearchParams({});
    setSelectedForCompare([]);
  };

  const toggleCompare = (productId) => {
    setSelectedForCompare(prev => {
      if (prev.includes(productId)) {
        return prev.filter(id => id !== productId);
      } else if (prev.length < 4) { // Limit to 4 products for comparison
        return [...prev, productId];
      } else {
        // Will be handled by notification system if needed
        return prev;
      }
    });
  };

  return (
    <div className="products-page">
      <div className="container">
        <h1 className="page-title">All Products</h1>

        {/* Filter Bar */}
        <FilterBar
          categories={categories}
          colors={colors}
          sizes={sizes}
          fabrics={fabrics}
          priceRange={priceRange}
          activeFilters={filters}
          onFilterChange={(filterType, value) => {
            if (filterType === 'clearAll') {
              handleClearFilters();
            } else {
              handleFilterChange(filterType, value);
            }
          }}
        />


        <div className="products-layout">
          <main className="products-main">
            {loading ? (
              <div className="spinner"></div>
            ) : (
              <>
                      <div className="products-header">
                        <div className="products-count">
                          {filters.ai_results ? (
                            <span>AI found {products.length} product{products.length !== 1 ? 's' : ''} for you</span>
                          ) : (
                            <span>{products.length} product{products.length !== 1 ? 's' : ''} found</span>
                          )}
                        </div>
                        {selectedForCompare.length > 0 && (
                          <Link 
                            to={`/compare?ids=${selectedForCompare.join(',')}`}
                            className="btn btn-primary btn-compare"
                          >
                            Compare {selectedForCompare.length} Product{selectedForCompare.length !== 1 ? 's' : ''}
                          </Link>
                        )}
                      </div>
                {filters.ai_results && (
                  <div className="ai-results-banner">
                    <span>✨ AI Search Results</span>
                    <button 
                      onClick={() => handleFilterChange('ai_results', '')}
                      className="btn-link"
                    >
                      Show All Products
                    </button>
                  </div>
                )}
                <ProductGrid 
                  products={products} 
                  onToggleCompare={toggleCompare}
                  selectedForCompare={selectedForCompare}
                  showCompareCheckbox={true}
                />
              </>
            )}
          </main>
        </div>
      </div>
    </div>
  );
};

export default Products;

