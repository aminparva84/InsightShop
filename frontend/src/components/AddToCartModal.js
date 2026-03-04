import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Modal from './Modal';
import ColorSwatches from './ColorSwatches';
import SizeSelector from './SizeSelector';
import { useCart } from '../contexts/CartContext';
import { useNotification } from '../contexts/NotificationContext';
import { isCombinationInStock, getFirstInStockColorForSize, getFirstInStockSizeForColor } from '../utils/variationAvailability';
import './AddToCartModal.css';

const baseUrl = process.env.PUBLIC_URL || '';
const placeholderImage = 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop&q=80';

function getFirstInStockCombination(productData) {
  const sizes = productData?.available_sizes || (productData?.size ? [productData.size] : []);
  const colors = productData?.available_colors || (productData?.color ? [productData.color] : []);
  const availability = productData?.variation_availability || [];
  if (!sizes.length || !colors.length) return { size: sizes[0], color: colors[0] };
  const norm = (s) => String(s).trim().toLowerCase();
  for (const sz of sizes) {
    for (const cl of colors) {
      const v = availability.find(
        (x) => norm(x.size) === norm(sz) && norm(x.color) === norm(cl) && Number(x.stock_quantity) > 0
      );
      if (v) return { size: sz, color: cl };
    }
  }
  return { size: sizes[0], color: colors[0] };
}

const AddToCartModal = ({ productId, isOpen, onClose, initialProduct = null }) => {
  const { addToCart } = useCart();
  const { showSuccess, showError } = useNotification();
  const [product, setProduct] = useState(initialProduct);
  const [loading, setLoading] = useState(!initialProduct);
  const [fetchError, setFetchError] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [selectedColor, setSelectedColor] = useState(null);
  const [selectedSize, setSelectedSize] = useState(null);
  const [variation, setVariation] = useState(null);
  const [variationLoading, setVariationLoading] = useState(false);
  const [adding, setAdding] = useState(false);
  const [validationMessage, setValidationMessage] = useState('');

  const hasMultipleColors = product?.available_colors && product.available_colors.length > 1;
  const hasMultipleSizes = product?.available_sizes && product.available_sizes.length > 1;
  const hasVariations = hasMultipleColors || hasMultipleSizes || (product?.available_colors?.length === 1 && product?.available_sizes?.length === 1);

  const colorRequired = hasMultipleColors;
  const sizeRequired = hasMultipleSizes;
  const colorValid = !colorRequired || (selectedColor && product?.available_colors?.includes(selectedColor));
  const sizeValid = !sizeRequired || (selectedSize && product?.available_sizes?.includes(selectedSize));
  const variationStock = variation?.stock_quantity;
  const inStock = variation === null ? (product?.stock_quantity === undefined || product?.stock_quantity > 0) : (variationStock !== undefined && variationStock > 0);
  const quantityInRange = variation === null
    ? (product?.stock_quantity === undefined || (quantity >= 1 && quantity <= (product?.stock_quantity ?? 99)))
    : (variationStock !== undefined && quantity >= 1 && quantity <= variationStock);
  const canAdd = product && inStock && colorValid && sizeValid && quantity >= 1 && quantityInRange;

  useEffect(() => {
    if (!isOpen || !productId) return;
    if (initialProduct && initialProduct.id === productId) {
      setProduct(initialProduct);
      setLoading(false);
      setFetchError(null);
      const { size, color } = getFirstInStockCombination(initialProduct);
      if (initialProduct.available_colors?.length) setSelectedColor(color);
      if (initialProduct.available_sizes?.length) setSelectedSize(size);
      setQuantity(1);
      setValidationMessage('');
      return;
    }
    setProduct(null);
    setLoading(true);
    setFetchError(null);
    setQuantity(1);
    setSelectedColor(null);
    setSelectedSize(null);
    setValidationMessage('');

    const fetchProduct = async () => {
      try {
        const response = await axios.get(`/api/products/${productId}`);
        const productData = response.data.product;
        setProduct(productData);
        const { size, color } = getFirstInStockCombination(productData);
        if (productData.available_colors?.length) setSelectedColor(color);
        if (productData.available_sizes?.length) setSelectedSize(size);
      } catch (err) {
        setFetchError(err.response?.data?.error || 'Failed to load product');
      } finally {
        setLoading(false);
      }
    };
    fetchProduct();
  }, [isOpen, productId]);

  useEffect(() => {
    if (!productId || !product || !selectedColor || !selectedSize) {
      setVariation(null);
      setVariationLoading(false);
      return;
    }
    setVariationLoading(true);
    const controller = new AbortController();
    axios.get(`/api/products/${productId}/variation`, {
      params: { size: selectedSize, color: selectedColor },
      signal: controller.signal
    })
      .then((res) => { setVariation(res.data); setVariationLoading(false); })
      .catch(() => { setVariation(null); setVariationLoading(false); });
    return () => controller.abort();
  }, [productId, product, selectedColor, selectedSize]);

  const availability = product?.variation_availability || [];
  const sizes = product?.available_sizes || (product?.size ? [product.size] : []);
  const colors = product?.available_colors || (product?.color ? [product.color] : []);

  const handleSizeSelect = (size) => {
    setSelectedSize(size);
    if (availability.length && selectedColor && !isCombinationInStock(availability, size, selectedColor)) {
      setSelectedColor(getFirstInStockColorForSize(availability, size, colors));
    }
  };

  const handleColorSelect = (color) => {
    setSelectedColor(color);
    if (availability.length && selectedSize && !isCombinationInStock(availability, selectedSize, color)) {
      setSelectedSize(getFirstInStockSizeForColor(availability, color, sizes));
    }
  };

  useEffect(() => {
    setValidationMessage('');
    if (!canAdd && product && !loading) {
      if (variation !== null && variation?.stock_quantity === 0) setValidationMessage('This variation is out of stock.');
      else if (colorRequired && !selectedColor) setValidationMessage('Please select a color.');
      else if (sizeRequired && !selectedSize) setValidationMessage('Please select a size.');
    }
  }, [canAdd, product, loading, colorRequired, sizeRequired, selectedColor, selectedSize, variation]);

  const handleAddToCart = async () => {
    if (!canAdd || adding) return;
    setValidationMessage('');
    setAdding(true);
    try {
      const result = await addToCart(product.id, quantity, selectedColor, selectedSize, variation?.variation_id ?? null);
      if (result.success) {
        showSuccess('Added to cart!');
        onClose();
        const remaining = typeof result.remaining_stock === 'number' ? result.remaining_stock : (variation?.stock_quantity ?? null);
        if (remaining !== null && remaining >= 1 && remaining <= 5) {
          setTimeout(() => showSuccess(`Only ${remaining} left in stock.`, 6000), 100);
        }
      } else {
        showError(result.error || 'Failed to add to cart');
      }
    } catch (err) {
      showError('Failed to add to cart');
    } finally {
      setAdding(false);
    }
  };

  const imageSrc = product?.image_url
    ? (product.image_url.startsWith('/') ? baseUrl + product.image_url : product.image_url)
    : placeholderImage;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      className="add-to-cart-modal"
      ariaLabelledBy="add-to-cart-modal-title"
      closeOnOverlayClick={true}
    >
      <div className="add-to-cart-modal-inner">
        {loading && (
          <div className="add-to-cart-modal-loading" aria-live="polite">
            <div className="add-to-cart-spinner" aria-label="Loading product" />
            <p>Loading product...</p>
          </div>
        )}

        {fetchError && (
          <div className="add-to-cart-modal-error">
            <p>{fetchError}</p>
            <button type="button" className="add-to-cart-btn-secondary" onClick={onClose}>
              Close
            </button>
          </div>
        )}

        {!loading && !fetchError && product && (
          <>
            <button
              type="button"
              className="add-to-cart-modal-close"
              onClick={onClose}
              aria-label="Close modal"
            >
              ×
            </button>
            <h2 id="add-to-cart-modal-title" className="add-to-cart-modal-title">
              Add to Cart
            </h2>
            <div className="add-to-cart-modal-body">
              <div className="add-to-cart-modal-image-wrap">
                <img
                  src={imageSrc}
                  alt={product.name}
                  onError={(e) => { e.target.src = placeholderImage; }}
                />
              </div>
              <div className="add-to-cart-modal-details">
                <h3 className="add-to-cart-product-name">{product.name}</h3>
                <div className="add-to-cart-modal-price">
                  {product.on_sale ? (
                    <>
                      <span className="add-to-cart-sale-price">${product.price.toFixed(2)}</span>
                      <span className="add-to-cart-original-price">${product.original_price?.toFixed(2) || product.price.toFixed(2)}</span>
                    </>
                  ) : (
                    <span>${product.price.toFixed(2)}</span>
                  )}
                </div>

                {hasMultipleColors && (
                  <ColorSwatches
                    colors={product.available_colors}
                    selectedColor={selectedColor}
                    onColorSelect={handleColorSelect}
                    variationAvailability={product.variation_availability}
                    selectedSize={selectedSize}
                  />
                )}
                {hasMultipleSizes && (
                  <SizeSelector
                    sizes={product.available_sizes}
                    selectedSize={selectedSize}
                    onSizeSelect={handleSizeSelect}
                    stockBySize={product.size_stock || product.stock_by_size || {}}
                    variationAvailability={product.variation_availability}
                    selectedColor={selectedColor}
                  />
                )}

                <div className="add-to-cart-quantity-row">
                  <label htmlFor="add-to-cart-quantity">Quantity:</label>
                  <input
                    id="add-to-cart-quantity"
                    type="number"
                    min={1}
                    max={hasVariations ? (variation?.stock_quantity ?? 99) : (product.stock_quantity ?? 99)}
                    value={quantity}
                    onChange={(e) => {
                      const maxQ = hasVariations ? (variation?.stock_quantity ?? 99) : (product.stock_quantity ?? 99);
                      const raw = parseInt(e.target.value, 10);
                      const clamped = Number.isNaN(raw) ? 1 : Math.min(maxQ, Math.max(1, raw));
                      setQuantity(clamped);
                    }}
                    className="add-to-cart-quantity-input"
                    aria-describedby={validationMessage ? 'add-to-cart-validation' : undefined}
                  />
                </div>

                {(hasVariations || product.stock_quantity != null) && (
                  <div className="add-to-cart-stock">
                    {hasVariations ? (
                      variationLoading && selectedColor && selectedSize ? (
                        <span className="add-to-cart-checking">Checking availability…</span>
                      ) : variation != null ? (
                        variation.stock_quantity > 0 ? (
                          <span className="add-to-cart-in-stock">In stock ({variation.stock_quantity} available)</span>
                        ) : (
                          <span className="add-to-cart-out-of-stock">Out of stock</span>
                        )
                      ) : (selectedColor && selectedSize) ? (
                        <span className="add-to-cart-out-of-stock">Out of stock</span>
                      ) : (
                        <span className="add-to-cart-select-options">Select size and color to see availability</span>
                      )
                    ) : product.stock_quantity > 0 ? (
                      <span className="add-to-cart-in-stock">In stock ({product.stock_quantity} available)</span>
                    ) : (
                      <span className="add-to-cart-out-of-stock">Out of stock</span>
                    )}
                  </div>
                )}

                {validationMessage && (
                  <p id="add-to-cart-validation" className="add-to-cart-validation" role="alert">
                    {validationMessage}
                  </p>
                )}

                <div className="add-to-cart-modal-actions">
                  <button
                    type="button"
                    className="add-to-cart-btn-primary"
                    onClick={handleAddToCart}
                    disabled={!canAdd || adding}
                  >
                    {adding ? 'Adding...' : 'Add to Cart'}
                  </button>
                  <button type="button" className="add-to-cart-btn-secondary" onClick={onClose}>
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
};

export default AddToCartModal;
