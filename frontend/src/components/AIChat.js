import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ProductCard from './ProductCard';
import './AIChat.css';

const AIChat = ({ onClose, onMinimize }) => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hi! I'm your AI shopping assistant. How can I help you find the perfect clothes today? When I show you products, I'll include their ID numbers so you can ask me to compare them!" }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestedProducts, setSuggestedProducts] = useState([]);
  const [selectedProductIds, setSelectedProductIds] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(() => {
    // Load voice preference from localStorage
    const saved = localStorage.getItem('aiVoiceEnabled');
    return saved === 'true';
  });
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const synthesisRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize text-to-speech
  useEffect(() => {
    if ('speechSynthesis' in window) {
      synthesisRef.current = window.speechSynthesis;
    }

    // Cleanup: stop speaking when component unmounts
    return () => {
      if (synthesisRef.current && synthesisRef.current.speaking) {
        synthesisRef.current.cancel();
      }
    };
  }, []);

  // Save voice preference to localStorage
  useEffect(() => {
    localStorage.setItem('aiVoiceEnabled', voiceEnabled.toString());
  }, [voiceEnabled]);

  // Function to speak text
  const speakText = (text) => {
    if (!voiceEnabled || !synthesisRef.current) return;

    // Stop any ongoing speech
    if (synthesisRef.current.speaking) {
      synthesisRef.current.cancel();
    }

    // Clean text - remove markdown, URLs, and special formatting
    const cleanText = text
      .replace(/Product\s*#\d+/gi, '') // Remove product IDs for cleaner speech
      .replace(/https?:\/\/[^\s]+/g, '') // Remove URLs
      .replace(/[*_`]/g, '') // Remove markdown formatting
      .replace(/\n+/g, '. ') // Replace newlines with periods
      .trim();

    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    
    // Configure voice settings
    utterance.rate = 1.0; // Normal speed
    utterance.pitch = 1.0; // Normal pitch
    utterance.volume = 0.8; // 80% volume
    
    // Try to use a natural-sounding voice
    const voices = synthesisRef.current.getVoices();
    const preferredVoice = voices.find(voice => 
      voice.name.includes('Google') || 
      voice.name.includes('Microsoft') ||
      voice.name.includes('Samantha') ||
      voice.name.includes('Alex')
    ) || voices.find(voice => voice.lang.startsWith('en'));
    
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    } else {
      utterance.lang = 'en-US';
    }

    utterance.onstart = () => {
      setIsSpeaking(true);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
    };

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event.error);
      setIsSpeaking(false);
    };

    synthesisRef.current.speak(utterance);
  };

  // Stop speaking
  const stopSpeaking = () => {
    if (synthesisRef.current && synthesisRef.current.speaking) {
      synthesisRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  // Toggle voice on/off
  const toggleVoice = () => {
    if (isSpeaking) {
      stopSpeaking();
    }
    setVoiceEnabled(prev => !prev);
  };

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(prev => prev + (prev ? ' ' : '') + transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const toggleVoiceInput = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in your browser. Please use Chrome or Edge.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    const userInputLower = input.toLowerCase();
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    // Check if user wants to see products in chat (explicit request) - check BEFORE API call
    const showInChatKeywords = ['show it here', 'show here', 'display here', 'list here', 'show me here', 'tell me here', 'show them here'];
    const wantsToSeeInChat = showInChatKeywords.some(keyword => 
      userInputLower.includes(keyword)
    );

    try {
      const response = await axios.post('/api/ai/chat', {
        message: input,
        history: messages,
        selected_product_ids: selectedProductIds
      });

      const aiMessage = {
        role: 'assistant',
        content: response.data.response
      };

      setMessages(prev => [...prev, aiMessage]);
      
      // Speak the AI's response if voice is enabled
      if (voiceEnabled && response.data.response) {
        // Small delay to ensure message is added to state
        setTimeout(() => {
          speakText(response.data.response);
        }, 100);
      }
      
      // Update selected products if new ones are mentioned
      if (response.data.suggested_products && response.data.suggested_products.length > 0) {
        const newProductIds = response.data.suggested_product_ids || 
                              response.data.suggested_products.map(p => p.id);
        
        // Add to selected products if not already there
        setSelectedProductIds(prev => {
          const combined = [...new Set([...prev, ...newProductIds])];
          return combined;
        });
      }
      
      // Handle comparison action - always navigate and minimize
      if (response.data.action === 'compare' && response.data.compare_ids) {
        const compareIds = response.data.compare_ids;
        navigate(`/compare?ids=${compareIds.join(',')}`);
        if (onMinimize) {
          onMinimize();
        } else if (onClose) {
          onClose();
        }
        return;
      }
      
      // Detect if this is a product list response
      // Check multiple conditions to ensure we catch all product list scenarios
      const hasProductIds = response.data.suggested_product_ids && response.data.suggested_product_ids.length > 0;
      const hasSuggestedProducts = response.data.suggested_products && response.data.suggested_products.length > 0;
      const isSearchResultsAction = response.data.action === 'search_results';
      
      // Debug logging
      console.log('AI Response Debug:', {
        hasProductIds,
        hasSuggestedProducts,
        isSearchResultsAction,
        productIdsCount: response.data.suggested_product_ids?.length || 0,
        productsCount: response.data.suggested_products?.length || 0,
        action: response.data.action,
        wantsToSeeInChat
      });
      
      // If user wants to see products in chat, format them as text list
      if (wantsToSeeInChat && hasSuggestedProducts && response.data.suggested_products.length > 0) {
        const productsList = response.data.suggested_products.map(p => 
          `Product #${p.id}: ${p.name} - $${parseFloat(p.price).toFixed(2)} (${p.category}, ${p.color || 'N/A'})`
        ).join('\n');
        
        // Replace the last AI message with the products list
        setMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1] = {
            role: 'assistant',
            content: `Here are the products you asked for:\n\n${productsList}`
          };
          return newMessages;
        });
        return; // Don't navigate, just show in chat
      }
      
      // If we have product IDs or suggested products with search_results action, treat as product list
      // Prioritize suggested_product_ids, but fall back to extracting from suggested_products
      // Also navigate if we have products and action is search_results, even without explicit IDs
      if (hasProductIds || (hasSuggestedProducts && isSearchResultsAction) || (hasSuggestedProducts && hasProductIds === false && response.data.action === 'search_results')) {
        let productIds = [];
        
        // First try to use suggested_product_ids
        if (hasProductIds) {
          productIds = response.data.suggested_product_ids;
        } 
        // If no IDs but we have products, extract IDs from products array
        else if (hasSuggestedProducts) {
          productIds = response.data.suggested_products.map(p => {
            const id = p.id || (typeof p === 'object' ? p.id : p);
            return id;
          }).filter(id => id != null && !isNaN(id));
        }
        
        if (productIds && productIds.length > 0) {
          console.log('Navigating to products page with IDs:', productIds);
          
          // Navigate to products page with product IDs immediately
          const idsParam = productIds.join(',');
          navigate(`/products?ai_results=${idsParam}`);
          
          // Update AI message to include navigation hint
          const updatedMessage = {
            role: 'assistant',
            content: `${response.data.response}\n\n✨ I found ${productIds.length} product${productIds.length !== 1 ? 's' : ''} for you! Check the products page to see them.`
          };
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = updatedMessage;
            return newMessages;
          });
          
          // Minimize chat immediately for product lists
          setTimeout(() => {
            if (onMinimize) {
              onMinimize();
            } else if (onClose) {
              onClose();
            }
          }, 100); // Small delay to ensure navigation happens first
          return;
        } else {
          console.warn('Products found but no valid IDs extracted:', {
            suggested_product_ids: response.data.suggested_product_ids,
            suggested_products: response.data.suggested_products?.map(p => ({ id: p.id, name: p.name }))
          });
        }
      }
      
      // Also check if response mentions product IDs in the text (fallback detection)
      const productIdPattern = /product\s*#?\s*(\d+)/gi;
      const mentionedIds = [];
      let match;
      while ((match = productIdPattern.exec(response.data.response)) !== null) {
        mentionedIds.push(parseInt(match[1]));
      }
      
      // If 3+ product IDs mentioned, treat as product list
      if (mentionedIds.length >= 3 && !hasProductIds) {
        const idsParam = [...new Set(mentionedIds)].join(',');
        navigate(`/products?ai_results=${idsParam}`);
        setTimeout(() => {
          if (onMinimize) {
            onMinimize();
          } else if (onClose) {
            onClose();
          }
        }, 100);
        return;
      }
      
      // For chat conversations (no products found), keep chat open
      // Don't navigate or minimize - just show the response
    } catch (error) {
      console.error('Error chatting with AI:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.response?.data?.error || error.message || 'Unknown error'}. The AI service may not be configured yet, but you can still browse products!`
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-chat">
      <div className="ai-chat-header">
        <h3>AI Shopping Assistant</h3>
        <div className="ai-chat-header-buttons">
          <button onClick={onMinimize || onClose} className="minimize-btn" title="Minimize">
            −
          </button>
          <button onClick={onClose} className="close-btn" title="Close">×</button>
        </div>
      </div>

      <div className="ai-chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.content.split('\n').map((line, lineIdx) => {
                // Highlight product IDs in the format "Product #ID:"
                const parts = line.split(/(Product\s*#\d+)/gi);
                return (
                  <React.Fragment key={lineIdx}>
                    {parts.map((part, partIdx) => {
                      const productIdMatch = part.match(/Product\s*#(\d+)/i);
                      if (productIdMatch) {
                        const productId = productIdMatch[1];
                        return (
                          <span key={partIdx} className="product-id-highlight">
                            {part}
                          </span>
                        );
                      }
                      return <span key={partIdx}>{part}</span>;
                    })}
                    {lineIdx < msg.content.split('\n').length - 1 && <br />}
                  </React.Fragment>
                );
              })}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {selectedProductIds.length > 0 && (
        <div className="selected-products-info">
          <p><strong>Selected Products:</strong> {selectedProductIds.join(', ')}</p>
          <p className="help-text">You can ask me to "compare selected items" or "compare product {selectedProductIds[0]} and {selectedProductIds[1]}"</p>
        </div>
      )}

      <form onSubmit={handleSend} className="ai-chat-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me about products, or say 'compare product 1, 2, 3' or 'compare selected items'..."
          disabled={loading || isListening}
        />
        <button
          type="button"
          onClick={toggleVoiceInput}
          className={`voice-btn ${isListening ? 'listening' : ''}`}
          title={isListening ? 'Stop listening' : 'Start voice input'}
          disabled={loading}
        >
          🎤
        </button>
        <button type="submit" disabled={loading || !input.trim() || isListening}>
          Send
        </button>
      </form>
    </div>
  );
};

export default AIChat;

