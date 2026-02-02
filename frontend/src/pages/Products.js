import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import axios from 'axios';
import ProductGrid from '../components/ProductGrid';
import FilterBar from '../components/FilterBar';
import './Products.css';

const openAIChatPopup = () => {
  window.dispatchEvent(new CustomEvent('openAIChat'));
};

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
  
  // Fetch products on initial load (only once on mount)
  useEffect(() => {
    // Initial load - fetch all products for normal tab
    const fetchInitialProducts = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/products');
        if (response.data && response.data.products) {
          setProducts(response.data.products);
          setAllProducts(response.data.products);
          console.log('Products Page: Initial load - fetched', response.data.products.length, 'products');
        }
      } catch (error) {
        console.error('Error fetching initial products:', error);
        setProducts([]);
        setAllProducts([]);
      } finally {
        setLoading(false);
      }
    };
    
    // Only fetch on initial mount if no AI results in URL
    const hasAiResults = searchParams.get('ai_results');
    if (!hasAiResults) {
      fetchInitialProducts();
    }
  }, []); // Only run once on mount

  // Sync filters with URL searchParams when URL changes (e.g., AI navigation)
  useEffect(() => {
    const aiResultsFromUrl = searchParams.get('ai_results') || '';
    const tabParam = searchParams.get('tab');
    
    const newFilters = {
      category: searchParams.get('category') || '',
      color: searchParams.get('color') || '',
      size: searchParams.get('size') || '',
      fabric: searchParams.get('fabric') || '',
      minPrice: searchParams.get('minPrice') || '',
      maxPrice: searchParams.get('maxPrice') || '',
      search: searchParams.get('search') || '',
      ai_results: aiResultsFromUrl
    };
    
    console.log('Products Page: URL changed');
    console.log('Products Page: All URL params:', Object.fromEntries(searchParams.entries()));
    console.log('Products Page: ai_results from URL:', aiResultsFromUrl);
    console.log('Products Page: tab from URL:', tabParam);
    console.log('Products Page: new filters:', newFilters);
    
    // Switch to AI Dashboard tab FIRST if ai_results is in URL or tab=ai
    // This ensures activeTab is set before fetchProducts runs
    const shouldBeAiTab = tabParam === 'ai' || aiResultsFromUrl;
    if (shouldBeAiTab && activeTab !== 'ai') {
      console.log('Products Page: Switching to AI Dashboard tab');
      setActiveTab('ai');
    } else if (tabParam === 'normal' && activeTab !== 'normal' && !aiResultsFromUrl) {
      setActiveTab('normal');
    }
    
    // Always update filters when URL changes (especially for AI navigation)
    setFilters(newFilters);
  }, [searchParams]);

  // Fetch products when filters or activeTab changes
  useEffect(() => {
    // Get ai_results from multiple sources to catch it regardless of timing
    const aiResultsFromUrl = searchParams.get('ai_results') || '';
    const filtersAiResults = filters.ai_results || '';
    // Also check window.location as a fallback
    const urlParams = new URLSearchParams(window.location.search);
    const aiResultsFromWindow = urlParams.get('ai_results') || '';
    
    console.log('Products Page: Fetch effect triggered');
    console.log('Products Page: ai_results from searchParams:', aiResultsFromUrl);
    console.log('Products Page: ai_results from filters:', filtersAiResults);
    console.log('Products Page: ai_results from window.location:', aiResultsFromWindow);
    console.log('Products Page: activeTab:', activeTab);
    console.log('Products Page: All searchParams:', Object.fromEntries(searchParams.entries()));
    console.log('Products Page: Full URL:', window.location.href);
    
    // Use any source that has the value (URL, filters, or window.location)
    const hasAiResults = Boolean(aiResultsFromUrl || filtersAiResults || aiResultsFromWindow);
    const aiResultsToUse = aiResultsFromUrl || filtersAiResults || aiResultsFromWindow;
    
    // Determine current tab from URL to avoid race conditions with state
    const currentTabFromUrl = searchParams.get('tab') === 'ai' || aiResultsFromUrl ? 'ai' : 'normal';
    
    // Always fetch products when:
    // 1. AI results exist (regardless of tab - we need to fetch them)
    // 2. We're on normal tab (for regular browsing)
    // 3. Filters change (for filtering)
    if (hasAiResults || activeTab === 'normal') {
      console.log('Products Page: Triggering fetchProducts, hasAiResults:', hasAiResults, 'aiResultsToUse:', aiResultsToUse, 'activeTab:', activeTab, 'currentTabFromUrl:', currentTabFromUrl);
      // Use a small timeout to ensure URL params and tab state are fully processed
      const timeoutId = setTimeout(() => {
        fetchProducts();
      }, 50);
      return () => clearTimeout(timeoutId);
    } else if (activeTab === 'ai' && !hasAiResults) {
      // For AI Dashboard tab without AI results, just set loading to false
      console.log('Products Page: AI Dashboard with no results, setting loading to false');
      setLoading(false);
    }
  }, [searchParams, activeTab, filters.ai_results, filters.category, filters.color, filters.size, filters.fabric, filters.minPrice, filters.maxPrice, filters.search]); // Include all filter changes

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
      
      // Get current tab from URL to avoid race conditions with state
      const currentTab = searchParams.get('tab') === 'ai' || searchParams.get('ai_results') ? 'ai' : 'normal';
      
      // If AI results are specified, fetch those specific products
      // Check both URL and filters state to ensure we catch the value
      const aiResultsFromUrl = searchParams.get('ai_results') || '';
      const aiResultsFromFilters = filters.ai_results || '';
      const aiResultsParam = aiResultsFromUrl || aiResultsFromFilters;
      
      console.log('Products Page: fetchProducts called');
      console.log('Products Page: ai_results from URL:', aiResultsFromUrl);
      console.log('Products Page: ai_results from filters:', aiResultsFromFilters);
      console.log('Products Page: Using aiResultsParam:', aiResultsParam);
      if (aiResultsParam) {
        const productIds = aiResultsParam.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id) && id > 0);
        console.log('Products Page: AI results detected, product IDs:', productIds);
        console.log('Products Page: Current activeTab from state:', activeTab);
        console.log('Products Page: Current tab from URL:', currentTab);
        
        if (productIds.length > 0) {
          // Fetch products by IDs using the ids parameter
          const idsParam = productIds.join(',');
          try {
            console.log('Products Page: Fetching products with IDs:', idsParam);
            const response = await axios.get(`/api/products?ids=${idsParam}`);
            
            console.log('Products Page: Received products:', response.data.products?.length || 0);
            console.log('Products Page: Response data:', response.data);
            
            if (response.data.products && response.data.products.length > 0) {
              // ALWAYS set AI products when AI results are fetched
              console.log('Products Page: Setting AI products:', response.data.products.length);
              console.log('Products Page: Product IDs in response:', response.data.products.map(p => p.id));
              console.log('Products Page: Current tab when setting:', currentTab, 'activeTab:', activeTab);
              
              // CRITICAL: Always set aiProducts when fetching by IDs (this is for AI Dashboard)
              setAiProducts(response.data.products);
              
              // Also ensure we're on AI tab if we have AI results
              const shouldBeAiTab = searchParams.get('tab') === 'ai' || searchParams.get('ai_results');
              if (shouldBeAiTab && activeTab !== 'ai') {
                console.log('Products Page: Switching to AI tab after fetching products');
                setActiveTab('ai');
              }
              
              // Also set for normal tab if we're on normal tab (for backwards compatibility)
              if (currentTab === 'normal' || activeTab === 'normal') {
                setAllProducts(response.data.products);
                setProducts(response.data.products);
              }
            } else {
              console.warn('Products Page: No products returned from API');
              setAiProducts([]);
              if (currentTab === 'normal' || activeTab === 'normal') {
                setAllProducts([]);
                setProducts([]);
              }
            }
            setLoading(false);
            return;
          } catch (error) {
            console.error('Products Page: Error fetching AI results:', error);
            console.error('Products Page: Error response:', error.response?.data);
            setAiProducts([]);
            if (currentTab === 'normal' || activeTab === 'normal') {
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
          if (currentTab === 'normal' || activeTab === 'normal') {
            setAllProducts([]);
            setProducts([]);
          }
          setLoading(false);
          return;
        }
      }
      
      // For normal tab without AI results, clear AI products
      if ((currentTab === 'normal' || activeTab === 'normal') && !aiResultsParam) {
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
  
  // Debug logging - track state changes
  useEffect(() => {
    console.log('Products Page: State update - activeTab:', activeTab, 'aiProducts:', aiProducts.length, 'displayProducts:', displayProducts.length);
    if (activeTab === 'ai') {
      console.log('Products Page: AI Dashboard active');
      console.log('Products Page: aiProducts array:', aiProducts);
      console.log('Products Page: displayProducts array:', displayProducts);
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
                      <p>Open the AI Assistant to find products, and they'll appear here.</p>
                      <p>You can compare products, view AI recommendations, and more!</p>
                      <button
                        type="button"
                        className="btn btn-primary ai-open-chat-btn"
                        onClick={openAIChatPopup}
                      >
                        Open AI Assistant
                      </button>
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

