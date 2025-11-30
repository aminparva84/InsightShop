import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import axios from 'axios';
import ProductGrid from '../components/ProductGrid';
import FilterBar from '../components/FilterBar';
import './Products.css';

const Products = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState(() => {
    // Check URL for tab parameter or ai_results
    const tabParam = searchParams.get('tab');
    if (tabParam === 'ai' || searchParams.get('ai_results')) {
      return 'ai';
    }
    return 'normal';
  });
  const [products, setProducts] = useState([]);
  const [allProducts, setAllProducts] = useState([]);
  const [aiProducts, setAiProducts] = useState([]); // Products for AI Dashboard tab
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

  // Sync filters with URL searchParams when URL changes (e.g., AI navigation)
  useEffect(() => {
    const newFilters = {
      category: searchParams.get('category') || '',
      color: searchParams.get('color') || '',
      size: searchParams.get('size') || '',
      fabric: searchParams.get('fabric') || '',
      minPrice: searchParams.get('minPrice') || '',
      maxPrice: searchParams.get('maxPrice') || '',
      search: searchParams.get('search') || '',
      ai_results: searchParams.get('ai_results') || ''
    };
    
    console.log('Products Page: URL changed, new filters:', newFilters);
    
    // Always update filters when URL changes (especially for AI navigation)
    setFilters(newFilters);
    
    // Switch to AI Dashboard tab if ai_results is in URL or tab=ai
    const tabParam = searchParams.get('tab');
    if (tabParam === 'ai' || newFilters.ai_results) {
      console.log('Products Page: Switching to AI Dashboard tab');
      setActiveTab('ai');
    } else if (tabParam === 'normal') {
      setActiveTab('normal');
    }
  }, [searchParams]);

  useEffect(() => {
    // Always fetch products when filters change (including AI results)
    // If AI results exist, fetch them regardless of tab
    if (filters.ai_results || activeTab === 'normal') {
      fetchProducts();
    } else if (activeTab === 'ai' && !filters.ai_results) {
      // For AI Dashboard tab without AI results, just set loading to false
      setLoading(false);
    }
  }, [filters, activeTab]);

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
      // Silently handle 404 - sizes are optional
      if (error.response?.status !== 404) {
        console.error('Error fetching sizes:', error);
      }
      setSizes([]);
    }
  };

  const fetchFabrics = async () => {
    try {
      const response = await axios.get('/api/products/fabrics');
      setFabrics(response.data.fabrics || []);
    } catch (error) {
      // Silently handle 404 - fabrics are optional
      if (error.response?.status !== 404) {
        console.error('Error fetching fabrics:', error);
      }
      setFabrics([]);
    }
  };

  const fetchPriceRange = async () => {
    try {
      const response = await axios.get('/api/products/price-range');
      if (response.data.min !== undefined && response.data.max !== undefined) {
        setPriceRange({ min: response.data.min, max: response.data.max });
      }
    } catch (error) {
      // Silently handle 404 - price range is optional
      if (error.response?.status !== 404) {
        console.error('Error fetching price range:', error);
      }
      // Set default price range
      setPriceRange({ min: 0, max: 1000 });
    }
  };

  const fetchProducts = async () => {
    try {
      setLoading(true);
      
      // If AI results are specified, fetch those specific products
      if (filters.ai_results) {
        const productIds = filters.ai_results.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id) && id > 0);
        console.log('Products Page: AI results detected, product IDs:', productIds);
        console.log('Products Page: Current activeTab:', activeTab);
        
        if (productIds.length > 0) {
          // Fetch products by IDs using the ids parameter
          const idsParam = productIds.join(',');
          try {
            console.log('Products Page: Fetching products with IDs:', idsParam);
            const response = await axios.get(`/api/products?ids=${idsParam}`);
            
            console.log('Products Page: Received products:', response.data.products?.length || 0);
            
            if (response.data.products && response.data.products.length > 0) {
              // Always set AI products for AI Dashboard tab (regardless of current tab)
              console.log('Products Page: Setting AI products:', response.data.products.length);
              setAiProducts(response.data.products);
              // Only set for normal tab if we're on normal tab
              if (activeTab === 'normal') {
                setAllProducts(response.data.products);
                setProducts(response.data.products);
              }
            } else {
              console.warn('Products Page: No products returned from API');
              setAiProducts([]);
              if (activeTab === 'normal') {
                setAllProducts([]);
                setProducts([]);
              }
            }
            setLoading(false);
            return;
          } catch (error) {
            console.error('Products Page: Error fetching AI results:', error);
            setAiProducts([]);
            if (activeTab === 'normal') {
              setAllProducts([]);
              setProducts([]);
            }
            setLoading(false);
            return;
          }
        } else {
          console.warn('Products Page: AI results filter exists but no valid product IDs found');
          // Set empty arrays when AI results are requested but no valid IDs
          setAiProducts([]);
          if (activeTab === 'normal') {
            setAllProducts([]);
            setProducts([]);
          }
          setLoading(false);
          return;
        }
      }
      
      // For normal tab without AI results, clear AI products
      if (activeTab === 'normal' && !filters.ai_results) {
        setAiProducts([]);
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
      console.error('Error details:', error.response?.data || error.message);
      // Set empty arrays on error to prevent showing stale data
      setProducts([]);
      setAllProducts([]);
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

  // Get products to display based on active tab
  const displayProducts = activeTab === 'ai' ? aiProducts : products;
  const displayAllProducts = activeTab === 'ai' ? aiProducts : allProducts;
  
  // Debug logging
  useEffect(() => {
    if (activeTab === 'ai') {
      console.log('Products Page: AI Dashboard active, aiProducts:', aiProducts.length);
      console.log('Products Page: displayProducts:', displayProducts.length);
    }
  }, [activeTab, aiProducts, displayProducts]);

  return (
    <div className="products-page">
      <div className="container">
        <h1 className="page-title">All Products</h1>

        {/* Tabs */}
        <div className="products-tabs">
          <button
            className={`products-tab ${activeTab === 'normal' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('normal');
              // Clear AI results when switching to normal tab
              if (filters.ai_results) {
                handleFilterChange('ai_results', '');
              }
            }}
          >
            Products
          </button>
          <button
            className={`products-tab ${activeTab === 'ai' ? 'active' : ''}`}
            onClick={() => setActiveTab('ai')}
          >
            AI Dashboard
          </button>
        </div>

        {/* Filter Bar - only show on normal tab */}
        {activeTab === 'normal' && (
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
        )}

        <div className="products-layout">
          <main className="products-main">
            {loading ? (
              <div className="spinner"></div>
            ) : (
              <>
                <div className="products-header">
                  <div className="products-count">
                    {activeTab === 'ai' ? (
                      <span>
                        {aiProducts.length > 0 
                          ? `AI Dashboard: ${aiProducts.length} product${aiProducts.length !== 1 ? 's' : ''}`
                          : 'AI Dashboard: No products yet. Ask the AI assistant to find products!'}
                      </span>
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
                
                {activeTab === 'ai' && aiProducts.length === 0 && (
                  <div className="ai-dashboard-empty">
                    <div className="ai-dashboard-empty-content">
                      <h2>🤖 AI Dashboard</h2>
                      <p>This is your AI-powered product discovery space.</p>
                      <p>Ask the AI assistant to find products, and they'll appear here.</p>
                      <p>You can compare products, view AI recommendations, and more!</p>
                    </div>
                  </div>
                )}
                
                {activeTab === 'ai' && aiProducts.length > 0 && (
                  <div className="ai-results-banner">
                    <span>✨ AI Search Results</span>
                    <button 
                      onClick={() => {
                        setAiProducts([]);
                        handleFilterChange('ai_results', '');
                      }}
                      className="btn-link"
                    >
                      Clear Results
                    </button>
                  </div>
                )}
                
                <ProductGrid 
                  products={displayProducts} 
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

