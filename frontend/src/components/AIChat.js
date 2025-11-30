import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import ProductCard from './ProductCard';
import { ScoopIcon, BowIcon, PaddingIcon, SlitIcon, getDressStyleIcon, MicrophoneIcon, SpeakerIcon, SpeakerOffIcon, StopIcon } from './DressStyleIcons';
import './AIChat.css';

const AIChat = ({ onClose, onMinimize, isInline = false, onProductsUpdate = null }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const initialMessage = "Hi! I'm your AI shopping assistant. How can I help you find the perfect clothes today? When I show you products, I'll include their ID numbers so you can ask me to compare them!";
  
  // Load chat history from localStorage
  const loadChatHistory = () => {
    try {
      const saved = localStorage.getItem('aiChatHistory');
      if (saved) {
        const parsed = JSON.parse(saved);
        // Ensure we have at least the initial message
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
    // Return default initial message
    return [{ role: 'assistant', content: initialMessage }];
  };
  
  const [messages, setMessages] = useState(loadChatHistory);
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
  const [voiceGender, setVoiceGender] = useState(() => {
    // Load voice gender preference from localStorage, default to 'woman'
    const saved = localStorage.getItem('aiVoiceGender');
    return saved || 'woman';
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

  // Save chat history to localStorage whenever messages change
  useEffect(() => {
    try {
      localStorage.setItem('aiChatHistory', JSON.stringify(messages));
    } catch (error) {
      console.error('Error saving chat history:', error);
    }
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

  // Save voice preferences to localStorage
  useEffect(() => {
    localStorage.setItem('aiVoiceEnabled', voiceEnabled.toString());
  }, [voiceEnabled]);

  useEffect(() => {
    localStorage.setItem('aiVoiceGender', voiceGender);
  }, [voiceGender]);

  // Speak initial greeting when voice is enabled on mount
  useEffect(() => {
    if (voiceEnabled && synthesisRef.current && messages.length === 1) {
      // Small delay to ensure voices are loaded
      setTimeout(() => {
        speakText(initialMessage);
      }, 500);
    }
  }, []); // Only run on mount

  // Function to speak text with natural-sounding voice
  const speakText = (text) => {
    if (!voiceEnabled || !synthesisRef.current) return;

    // Stop any ongoing speech
    if (synthesisRef.current.speaking) {
      synthesisRef.current.cancel();
    }

    // Enhanced text preprocessing for more natural speech
    let cleanText = text
      // Remove product IDs but keep the context
      .replace(/Product\s*#\d+/gi, '')
      // Remove URLs
      .replace(/https?:\/\/[^\s]+/g, '')
      // Remove markdown formatting
      .replace(/[*_`]/g, '')
      // Remove emojis (they don't speak well)
      .replace(/[^\w\s.,!?;:()\-'"]/g, ' ')
      // Add pauses for better flow - convert multiple newlines to longer pauses
      .replace(/\n\n+/g, '. ')
      // Convert single newlines to short pauses
      .replace(/\n/g, ', ')
      // Clean up multiple spaces
      .replace(/\s+/g, ' ')
      // Add natural pauses after sentences
      .replace(/\.\s+/g, '. ')
      .replace(/\?\s+/g, '? ')
      .replace(/!\s+/g, '! ')
      // Ensure proper spacing around punctuation
      .replace(/\s*([.,!?;:])\s*/g, '$1 ')
      .trim();

    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    
    // More natural speech parameters
    utterance.rate = 0.95; // Slightly slower for more natural speech (was 1.0)
    utterance.pitch = 1.1; // Slightly higher pitch for more warmth (was 1.0)
    utterance.volume = 0.9; // Slightly louder (was 0.8)
    
    // Get all available voices and prioritize neural/premium voices
    const voices = synthesisRef.current.getVoices();
    
    // Gender-specific voice patterns
    const femaleVoicePatterns = [
      /neural.*female|female.*neural/i,
      /premium.*female|female.*premium/i,
      /zira/i,           // Microsoft female
      /samantha/i,       // Apple female
      /victoria/i,       // Apple female
      /karen/i,          // Australian female
      /fiona/i,          // Scottish female
      /tessa/i,         // South African female
      /google.*female|female.*google/i,
      /polly.*joanna|joanna/i,  // Amazon Polly female
      /polly.*amy|amy/i,
      /polly.*emma|emma/i
    ];
    
    const maleVoicePatterns = [
      /neural.*male|male.*neural/i,
      /premium.*male|male.*premium/i,
      /david/i,          // Microsoft male
      /alex/i,           // Apple male
      /daniel/i,         // British male
      /thomas/i,         // British male
      /google.*male|male.*google/i,
      /polly.*matthew|matthew/i,  // Amazon Polly male
      /polly.*joey|joey/i,
      /polly.*justin|justin/i
    ];
    
    // Priority list for natural-sounding voices (neural voices first)
    const voicePriority = [
      // Neural/premium voices (most natural)
      { pattern: /neural/i, priority: 1 },
      { pattern: /premium/i, priority: 1 },
      { pattern: /enhanced/i, priority: 1 },
      // Google voices (usually good quality)
      { pattern: /google.*english/i, priority: 2 },
      { pattern: /google/i, priority: 3 },
      // Microsoft voices
      { pattern: /microsoft/i, priority: 3 },
      // Apple voices (Mac/iOS)
      { pattern: /samantha|alex|victoria|daniel/i, priority: 2 },
      // Amazon Polly voices (if available)
      { pattern: /polly/i, priority: 2 },
      // Other English voices
      { pattern: /english/i, priority: 4 }
    ];
    
    // Filter voices by gender preference and prioritize American English (en-US)
    const genderPatterns = voiceGender === 'woman' ? femaleVoicePatterns : maleVoicePatterns;
    
    // First, filter for American English voices (en-US) with gender preference
    const americanGenderVoices = voices.filter(voice => {
      if (voice.lang !== 'en-US') return false;
      return genderPatterns.some(pattern => pattern.test(voice.name));
    });
    
    // If no American gender-specific voices, try any American English voice
    const americanVoices = americanGenderVoices.length > 0 
      ? americanGenderVoices 
      : voices.filter(voice => voice.lang === 'en-US');
    
    // Fallback to any English voice with gender preference
    const genderVoices = americanVoices.length > 0 
      ? americanVoices 
      : voices.filter(voice => {
          if (!voice.lang.startsWith('en')) return false;
          return genderPatterns.some(pattern => pattern.test(voice.name));
        });
    
    // Final fallback to any English voice
    const scoredVoices = genderVoices.length > 0 
      ? genderVoices 
      : (americanVoices.length > 0 
          ? americanVoices 
          : voices.filter(voice => voice.lang.startsWith('en')));
    
    const sortedVoices = scoredVoices
      .map(voice => {
        let score = 999; // Default low priority
        
        // Prioritize American English (en-US)
        if (voice.lang === 'en-US') {
          score = 0; // Highest priority for American English
        } else if (voice.lang.startsWith('en-US')) {
          score = 1; // Second priority for en-US variants
        } else if (voice.lang.startsWith('en')) {
          score = 100; // Lower priority for other English variants
        }
        
        // Then apply voice quality priority
        for (const { pattern, priority } of voicePriority) {
          if (pattern.test(voice.name)) {
            score += priority; // Add to existing score
          }
        }
        return { voice, score };
      })
      .sort((a, b) => a.score - b.score);
    
    // Use the best available voice matching gender preference and American accent
    const selectedVoice = sortedVoices.length > 0 ? sortedVoices[0].voice : null;
    
    if (selectedVoice) {
      utterance.voice = selectedVoice;
      // Ensure American English is set
      utterance.lang = 'en-US';
    } else {
      // Fallback: set to American English
      utterance.lang = 'en-US';
      // Try to find any American English voice
      const anyAmericanVoice = voices.find(voice => voice.lang === 'en-US');
      if (anyAmericanVoice) {
        utterance.voice = anyAmericanVoice;
      }
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

    // Add a small delay to ensure voices are loaded (especially on first use)
    if (voices.length === 0) {
      // Wait for voices to load
      const checkVoices = setInterval(() => {
        const availableVoices = synthesisRef.current.getVoices();
        if (availableVoices.length > 0) {
          clearInterval(checkVoices);
          // Re-run with voices now available
          speakText(text);
        }
      }, 100);
      setTimeout(() => clearInterval(checkVoices), 2000); // Timeout after 2 seconds
      return;
    }

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

    // Load voices for text-to-speech (some browsers need this)
    if ('speechSynthesis' in window) {
      const loadVoices = () => {
        // Voices are loaded asynchronously, so we call this when they're ready
        if (synthesisRef.current) {
          const voices = synthesisRef.current.getVoices();
          // Only log in development
          if (process.env.NODE_ENV === 'development') {
            console.log('Available voices:', voices.length);
            const neuralVoices = voices.filter(v => /neural|premium|enhanced/i.test(v.name));
            if (neuralVoices.length > 0) {
              console.log('Neural/Premium voices found:', neuralVoices.map(v => v.name));
            }
          }
        }
      };
      loadVoices();
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = loadVoices;
      }
      // Also try loading voices after a short delay (some browsers need this)
      setTimeout(loadVoices, 500);
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (synthesisRef.current && synthesisRef.current.speaking) {
        synthesisRef.current.cancel();
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
    
    // NOTE: Don't navigate here - let the response handler navigate with ai_results
    // Only switch tab if we're already on products page and no ai_results exists
    // This prevents overwriting the ai_results parameter that will be set by the response handler
    if (location.pathname === '/products') {
      const currentParams = new URLSearchParams(window.location.search);
      const hasAiResults = currentParams.get('ai_results');
      // Only switch tab if no ai_results exists (to avoid interfering with product navigation)
      if (currentParams.get('tab') !== 'ai' && !hasAiResults) {
        currentParams.set('tab', 'ai');
        navigate(`/products?${currentParams.toString()}`);
      }
    }

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
      
      // Handle comparison action - always navigate and minimize (only if not inline)
      if (response.data.action === 'compare' && response.data.compare_ids) {
        const compareIds = response.data.compare_ids;
        navigate(`/compare?ids=${compareIds.join(',')}`);
        if (!isInline) {
          if (onMinimize) {
            onMinimize();
          } else if (onClose) {
            onClose();
          }
        }
        return;
      }
      
      // Log the full response to debug
      console.log('AI Chat: Full response received:', {
        action: response.data.action,
        hasSuggestedProductIds: !!response.data.suggested_product_ids,
        suggestedProductIdsLength: response.data.suggested_product_ids?.length || 0,
        suggestedProductIds: response.data.suggested_product_ids,
        hasSuggestedProducts: !!response.data.suggested_products,
        suggestedProductsLength: response.data.suggested_products?.length || 0,
        firstProduct: response.data.suggested_products?.[0],
        fullResponse: response.data
      });
      
      // Detect if this is a product list response
      // Check multiple conditions to ensure we catch all product list scenarios
      // IMPORTANT: Check if array exists AND has length > 0
      const hasProductIds = Array.isArray(response.data.suggested_product_ids) && response.data.suggested_product_ids.length > 0;
      const hasSuggestedProducts = Array.isArray(response.data.suggested_products) && response.data.suggested_products.length > 0;
      const isSearchResultsAction = response.data.action === 'search_results';
      
      // Also check if action is undefined but we have products (backend might have missed setting action)
      const hasProductsButNoAction = (hasProductIds || hasSuggestedProducts) && !response.data.action;
      
      console.log('AI Chat: Detection results:', {
        hasProductIds,
        hasSuggestedProducts,
        isSearchResultsAction,
        action: response.data.action
      });
      
      // Debug logging (only log if there's an issue)
      if (!hasProductIds && !hasSuggestedProducts && response.data.action === 'search_results') {
        console.warn('AI Response - action is search_results but no products found');
      }
      
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
      
      // CRITICAL: Only navigate if we have products AND action is search_results
      // If no products found (especially with strict filters), stay in chat to show the "no results" message
      // Navigate if:
      // 1. We have product IDs AND action is search_results, OR
      // 2. We have suggested products AND action is search_results
      // IMPORTANT: Don't navigate if action is null/undefined (means no products found)
      const shouldNavigate = (hasProductIds || hasSuggestedProducts) && 
                            (response.data.action === 'search_results');
      
      console.log('AI Chat: Should navigate?', shouldNavigate, {
        hasProductIds,
        hasSuggestedProducts,
        isSearchResultsAction,
        action: response.data.action,
        hasProductsButNoAction,
        condition1: hasProductIds,
        condition2: (hasSuggestedProducts && isSearchResultsAction),
        condition3: (hasSuggestedProducts && response.data.action === 'search_results'),
        condition4: (hasSuggestedProducts && hasProductsButNoAction)
      });
      
      if (shouldNavigate) {
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
        
        // If we still don't have IDs but have products, try one more extraction
        if (!productIds || productIds.length === 0) {
          if (hasSuggestedProducts && response.data.suggested_products) {
            productIds = response.data.suggested_products
              .map(p => {
                try {
                  const id = p?.id || (typeof p === 'number' ? p : null);
                  return id ? parseInt(id) : null;
                } catch {
                  return null;
                }
              })
              .filter(id => id != null && !isNaN(id) && id > 0);
          }
        }
        
        if (productIds && productIds.length > 0) {
          // Check if we're on Home page and have update callback
          const isHomePage = location.pathname === '/';
          
          // Log for debugging
          console.log('AI Chat: Product IDs extracted:', productIds);
          console.log('AI Chat: Suggested products from response:', response.data.suggested_products?.map(p => ({ id: p.id, name: p.name, category: p.category })));
          
          if (isHomePage && onProductsUpdate) {
            // Update products on Home page by fetching exact product IDs
            // This ensures 100% match between chat and grid
            console.log('AI Chat: Updating products on Home page with IDs:', productIds);
            console.log('AI Chat: Product IDs count:', productIds.length);
            console.log('AI Chat: Verifying IDs match suggested products...');
            
            // CRITICAL: Always use suggested_product_ids from backend if available
            // This ensures we get the exact products the AI found
            if (response.data.suggested_product_ids && response.data.suggested_product_ids.length > 0) {
              const backendIds = response.data.suggested_product_ids;
              console.log('AI Chat: Using backend suggested_product_ids:', backendIds);
              console.log('AI Chat: Verifying these match suggested_products...');
              
              // Verify the IDs match the products
              if (response.data.suggested_products) {
                const productIdsFromProducts = response.data.suggested_products.map(p => p.id || p).filter(id => id != null);
                console.log('AI Chat: Product IDs from suggested_products:', productIdsFromProducts);
                console.log('AI Chat: Categories from suggested_products:', response.data.suggested_products.map(p => ({ id: p.id, category: p.category, name: p.name })));
              }
              
              onProductsUpdate(backendIds);
            } else if (response.data.suggested_products && response.data.suggested_products.length > 0) {
              // Fallback: extract IDs from suggested_products
              const suggestedIds = response.data.suggested_products.map(p => p.id || p).filter(id => id != null);
              console.log('AI Chat: Using IDs extracted from suggested_products:', suggestedIds);
              onProductsUpdate(suggestedIds);
            } else {
              // Last resort: use extracted IDs
              console.log('AI Chat: Using extracted product IDs:', productIds);
              onProductsUpdate(productIds);
            }
            
            // Update AI message
            const updatedMessage = {
              role: 'assistant',
              content: `${response.data.response}\n\nI found ${productIds.length} product${productIds.length !== 1 ? 's' : ''} for you! They're displayed below.`
            };
            setMessages(prev => {
              const newMessages = [...prev];
              newMessages[newMessages.length - 1] = updatedMessage;
              return newMessages;
            });
            
            // Scroll to products section
            setTimeout(() => {
              document.querySelector('.featured-products')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 300);
            return;
          }
          
          // Otherwise, navigate to products page with product IDs and switch to AI Dashboard tab
          const idsParam = productIds.join(',');
          console.log('AI Chat: Navigating to products page with IDs:', productIds);
          console.log('AI Chat: IDs param:', idsParam);
          console.log('AI Chat: Full URL will be:', `/products?ai_results=${idsParam}&tab=ai`);
          
          // Use navigate with state to ensure parameters are preserved
          const targetUrl = `/products?ai_results=${encodeURIComponent(idsParam)}&tab=ai`;
          console.log('AI Chat: Encoded URL:', targetUrl);
          navigate(targetUrl, { replace: false });
          
          // Verify navigation happened
          setTimeout(() => {
            console.log('AI Chat: After navigation, current URL:', window.location.href);
          }, 100);
          
          // Update AI message to include navigation hint
          const updatedMessage = {
            role: 'assistant',
            content: `${response.data.response}\n\nI found ${productIds.length} product${productIds.length !== 1 ? 's' : ''} for you! Check the AI Dashboard tab to see them.`
          };
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = updatedMessage;
            return newMessages;
          });
          
          // Minimize chat immediately for product lists (only if not inline)
          if (!isInline) {
            setTimeout(() => {
              if (onMinimize) {
                onMinimize();
              } else if (onClose) {
                onClose();
              }
            }, 100); // Small delay to ensure navigation happens first
          }
          return;
        } else if (hasSuggestedProducts && response.data.suggested_products?.length > 0) {
          // Last resort: log detailed error for debugging
          console.error('Failed to extract product IDs:', {
            suggested_product_ids: response.data.suggested_product_ids,
            suggested_products: response.data.suggested_products,
            firstProduct: response.data.suggested_products[0]
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
        const targetUrl = `/products?ai_results=${encodeURIComponent(idsParam)}&tab=ai`;
        console.log('AI Chat: Second navigation, URL:', targetUrl);
        navigate(targetUrl, { replace: false });
        
        // Verify navigation happened
        setTimeout(() => {
          console.log('AI Chat: After second navigation, current URL:', window.location.href);
        }, 100);
        if (!isInline) {
          setTimeout(() => {
            if (onMinimize) {
              onMinimize();
            } else if (onClose) {
              onClose();
            }
          }, 100);
        }
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
    <div className={`ai-chat ${isInline ? 'ai-chat-inline' : ''}`}>
      <div className="ai-chat-header">
        <h3>AI Shopping Assistant</h3>
        {!isInline && (
          <div className="ai-chat-header-buttons">
            <button onClick={onMinimize || onClose} className="minimize-btn" title="Minimize">
              −
            </button>
            <button onClick={onClose} className="close-btn" title="Close">×</button>
          </div>
        )}
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
          <p className="help-text">
            <strong>What I can do:</strong> Compare products, find similar items, get styling advice, 
            search by color/size/category/dress style (scoop, bow, padding, slit, v-neck, etc.), or ask "show me blue shirts for women"
          </p>
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
          <MicrophoneIcon size={18} />
        </button>
        <div className="voice-controls">
          <button
            type="button"
            onClick={toggleVoice}
            className={`voice-btn ${voiceEnabled ? 'speaking-enabled' : ''} ${isSpeaking ? 'speaking' : ''}`}
            title={voiceEnabled ? (isSpeaking ? 'AI is speaking - Click to stop' : 'Voice enabled - Click to disable') : 'Enable AI voice responses'}
            disabled={loading}
          >
            {isSpeaking ? <SpeakerIcon size={18} /> : voiceEnabled ? <SpeakerIcon size={18} /> : <SpeakerOffIcon size={18} />}
          </button>
          {voiceEnabled && (
            <select
              className="voice-gender-select"
              value={voiceGender}
              onChange={(e) => {
                setVoiceGender(e.target.value);
                if (isSpeaking) stopSpeaking();
              }}
              title="Select voice gender"
            >
              <option value="woman">Woman</option>
              <option value="man">Man</option>
            </select>
          )}
          {isSpeaking && (
            <button
              type="button"
              onClick={stopSpeaking}
              className="voice-btn"
              title="Stop speaking"
              style={{ background: '#ef4444', borderColor: '#dc2626' }}
            >
              <StopIcon size={18} />
            </button>
          )}
        </div>
        <button type="submit" disabled={loading || !input.trim() || isListening}>
          Send
        </button>
      </form>
    </div>
  );
};

export default AIChat;

