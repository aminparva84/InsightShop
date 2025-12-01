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
  const [pollyAvailable, setPollyAvailable] = useState(true); // Assume available by default
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [uploadingImage, setUploadingImage] = useState(false);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const audioRef = useRef(null); // For AWS Polly audio playback
  const fileInputRef = useRef(null);

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

  // Initialize audio element for AWS Polly playback
  useEffect(() => {
    audioRef.current = new Audio();
    
    // Check Polly status on mount
    const checkPollyStatus = async () => {
      try {
        const response = await axios.get('/api/ai/text-to-speech/status');
        if (response.data) {
          setPollyAvailable(response.data.available || false);
          if (!response.data.available) {
            console.warn('AWS Polly not available:', response.data);
            if (!response.data.has_credentials) {
              console.warn('AWS credentials not configured. Voice feature requires AWS Polly setup.');
              console.warn('Add to .env: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY');
            }
          } else {
            console.log('✅ AWS Polly is available and ready');
          }
        }
      } catch (error) {
        console.error('Error checking Polly status:', error);
        setPollyAvailable(false);
      }
    };
    checkPollyStatus();
    
    // Cleanup: stop speaking when component unmounts
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
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
    if (voiceEnabled && messages.length === 1) {
      // Small delay to ensure everything is ready
      setTimeout(() => {
        speakText(initialMessage);
      }, 500);
    }
  }, []); // Only run on mount

  // Function to speak text with natural-sounding voice
  // Function to speak text using AWS Polly (natural, excited voice)
  const speakText = async (text) => {
    if (!voiceEnabled) {
      console.log('Voice is disabled');
      return;
    }
    
    if (!pollyAvailable) {
      console.warn('AWS Polly is not available. Voice playback disabled.');
      return;
    }
    
    if (!audioRef.current) {
      console.error('Audio ref not initialized');
      return;
    }

    // Stop any ongoing speech
    if (audioRef.current && !audioRef.current.paused) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }

    try {
      console.log('Calling TTS API with text length:', text.length);
      setIsSpeaking(true);
      
      // Call backend to get audio from AWS Polly
      const response = await axios.post('/api/ai/text-to-speech', {
        text: text,
        voice_gender: voiceGender
      }, {
        responseType: 'json'
      });

      console.log('TTS API response received:', response.data ? 'Has data' : 'No data', response.data?.format);

      if (response.data && response.data.audio) {
        // Convert base64 to blob URL
        const audioData = response.data.audio;
        const binaryString = atob(audioData);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const blob = new Blob([bytes], { type: 'audio/mpeg' });
        const audioUrl = URL.createObjectURL(blob);

        console.log('Audio blob created, URL:', audioUrl.substring(0, 50) + '...');

        // Set up event handlers first
        const handleEnded = () => {
          console.log('Audio playback ended');
          setIsSpeaking(false);
          URL.revokeObjectURL(audioUrl);
          // Remove listeners
          audioRef.current.removeEventListener('ended', handleEnded);
          audioRef.current.removeEventListener('error', handleError);
        };

        const handleError = (error) => {
          console.error('Audio playback error:', error);
          console.error('Audio error details:', {
            error: audioRef.current?.error,
            code: audioRef.current?.error?.code,
            message: audioRef.current?.error?.message,
            readyState: audioRef.current?.readyState
          });
          setIsSpeaking(false);
          URL.revokeObjectURL(audioUrl);
          // Remove listeners
          audioRef.current?.removeEventListener('ended', handleEnded);
          audioRef.current?.removeEventListener('error', handleError);
        };

        const handleCanPlay = async () => {
          console.log('Audio can play, attempting to play...');
          try {
            // Play audio - user has already interacted (sent message), so this should work
            const playPromise = audioRef.current.play();
            if (playPromise !== undefined) {
              await playPromise;
              console.log('Audio play() called successfully');
            }
          } catch (playError) {
            console.error('Error playing audio:', playError);
            console.error('Play error details:', {
              name: playError.name,
              message: playError.message
            });
            
            // If autoplay is blocked, user needs to interact
            if (playError.name === 'NotAllowedError') {
              console.warn('Autoplay blocked. Click the voice button to enable audio playback.');
            }
            
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
            audioRef.current?.removeEventListener('canplay', handleCanPlay);
            audioRef.current?.removeEventListener('ended', handleEnded);
            audioRef.current?.removeEventListener('error', handleError);
          }
        };

        // Clear previous source
        audioRef.current.src = '';
        audioRef.current.load();
        
        // Add event listeners
        audioRef.current.addEventListener('ended', handleEnded);
        audioRef.current.addEventListener('error', handleError);
        audioRef.current.addEventListener('canplay', handleCanPlay);
        
        // Set new source and properties
        audioRef.current.src = audioUrl;
        audioRef.current.volume = 0.95;
        audioRef.current.preload = 'auto';
        
        // Load the audio
        audioRef.current.load();
        
        // Fallback: try playing after a short delay if canplay doesn't fire
        let playTimeout;
        const cleanup = () => {
          if (playTimeout) {
            clearTimeout(playTimeout);
            playTimeout = null;
          }
        };
        
        playTimeout = setTimeout(async () => {
          cleanup();
          if (audioRef.current && audioRef.current.readyState >= 2 && audioRef.current.paused) {
            console.log('Fallback: Attempting to play audio after delay');
            try {
              const playPromise = audioRef.current.play();
              if (playPromise !== undefined) {
                await playPromise;
                console.log('Audio play() called successfully (fallback)');
              }
            } catch (playError) {
              console.error('Error playing audio (fallback):', playError);
              setIsSpeaking(false);
              URL.revokeObjectURL(audioUrl);
              audioRef.current?.removeEventListener('ended', handleEnded);
              audioRef.current?.removeEventListener('error', handleError);
              audioRef.current?.removeEventListener('canplay', handleCanPlay);
            }
          }
        }, 500);
        
        // Cleanup timeout if audio starts playing before timeout
        audioRef.current.addEventListener('play', cleanup);
      } else {
        console.error('No audio data received from API');
        setIsSpeaking(false);
      }
    } catch (error) {
      console.error('Error generating speech:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      });
      setIsSpeaking(false);
      // Fallback: show error but don't break the UI
      if (error.response?.data?.error) {
        console.error('TTS Error:', error.response.data.error);
        // Show user-friendly error message
        if (error.response.data.error.includes('Polly client not initialized')) {
          console.warn('AWS Polly not configured. Voice feature requires AWS credentials.');
        }
      }
    }
  };

  // Stop speaking
  const stopSpeaking = () => {
    if (audioRef.current && !audioRef.current.paused) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
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

  // Clear chat history
  const handleClearHistory = () => {
    setMessages([{ role: 'assistant', content: initialMessage }]);
    localStorage.setItem('aiChatHistory', JSON.stringify([{ role: 'assistant', content: initialMessage }]));
    setShowClearConfirm(false);
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
      if (audioRef.current && !audioRef.current.paused) {
        audioRef.current.pause();
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

  // Handle image upload
  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      alert('Please upload a valid image file (PNG, JPG, GIF, or WEBP)');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('Image is too large. Maximum size is 10MB');
      return;
    }

    setUploadingImage(true);

    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await axios.post('/api/ai/upload-image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data.success) {
        setUploadedImage({
          data: response.data.image_data,
          format: response.data.image_format,
          filename: file.name
        });

        // Add user message showing image was uploaded
        const imageMessage = {
          role: 'user',
          content: `[Image uploaded: ${file.name}]`,
          image: response.data.image_data
        };
        setMessages(prev => [...prev, imageMessage]);

        // Add AI response with analysis and metadata
        const aiResponse = {
          role: 'assistant',
          content: response.data.message || response.data.metadata_sentence || 'Image analyzed successfully!',
          similarProducts: response.data.similar_products || []
        };
        setMessages(prev => [...prev, aiResponse]);

        // Update selected products if similar products found
        if (response.data.similar_product_ids && response.data.similar_product_ids.length > 0) {
          setSelectedProductIds(prev => {
            const combined = [...new Set([...prev, ...response.data.similar_product_ids])];
            return combined;
          });
        }

        // If we have similar products, navigate to show them
        if (response.data.similar_products && response.data.similar_products.length > 0) {
          const productIds = response.data.similar_product_ids || response.data.similar_products.map(p => p.id);
          
          // Navigate to products page with similar products
          if (location.pathname === '/' && onProductsUpdate) {
            // Update products on Home page
            onProductsUpdate(productIds);
            
            // Update message to mention products are shown
            const updatedMessage = {
              role: 'assistant',
              content: `${response.data.message}\n\nCheck out the similar products I found below!`
            };
            setMessages(prev => {
              const newMessages = [...prev];
              newMessages[newMessages.length - 1] = updatedMessage;
              return newMessages;
            });
            
            // Scroll to products
            setTimeout(() => {
              document.querySelector('.featured-products')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 300);
          } else {
            // Navigate to products page
            const idsParam = productIds.join(',');
            navigate(`/products?ai_results=${encodeURIComponent(idsParam)}&tab=ai`);
            
            // Minimize chat if not inline
            if (!isInline) {
              setTimeout(() => {
                if (onMinimize) {
                  onMinimize();
                } else if (onClose) {
                  onClose();
                }
              }, 100);
            }
          }
        }

        // Speak the response if voice is enabled
        if (voiceEnabled && audioRef.current) {
          setTimeout(() => {
            if (audioRef.current) {
              speakText(aiResponse.content);
            }
          }, 300);
        }
      }
    } catch (error) {
      console.error('Error uploading image:', error);
      alert(error.response?.data?.error || 'Failed to upload image. Please try again.');
    } finally {
      setUploadingImage(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Analyze uploaded image
  const analyzeUploadedImage = async (query = 'What is this item and what would match it?') => {
    if (!uploadedImage) {
      alert('Please upload an image first');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post('/api/ai/analyze-image', {
        image_data: uploadedImage.data,
        query: query
      });

      if (response.data.success) {
        const analysisMessage = {
          role: 'assistant',
          content: response.data.analysis
        };
        setMessages(prev => [...prev, analysisMessage]);

        // Speak the response if voice is enabled
        if (voiceEnabled && audioRef.current) {
          setTimeout(() => {
            if (audioRef.current) {
              speakText(response.data.analysis);
            }
          }, 300);
        }
      }
    } catch (error) {
      console.error('Error analyzing image:', error);
      alert(error.response?.data?.error || 'Failed to analyze image. Please try again.');
    } finally {
      setLoading(false);
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
      if (voiceEnabled && response.data.response && audioRef.current) {
        // Small delay to ensure message is added to state and audio is ready
        setTimeout(() => {
          if (audioRef.current) {
            speakText(response.data.response);
          }
        }, 300);
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
        <div className="ai-chat-header-buttons">
          <button 
            onClick={() => setShowClearConfirm(true)} 
            className="clear-btn" 
            title="Clear chat history"
          >
            Clear
          </button>
          {!isInline && (
            <>
              <button onClick={onMinimize || onClose} className="minimize-btn" title="Minimize">
                −
              </button>
              <button onClick={onClose} className="close-btn" title="Close">×</button>
            </>
          )}
        </div>
      </div>

      <div className="ai-chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.image && (
                <div style={{ marginBottom: '10px' }}>
                  <img 
                    src={`data:image/${msg.image.includes('data:') ? '' : 'jpeg;base64,'}${msg.image}`}
                    alt="Uploaded"
                    style={{
                      maxWidth: '100%',
                      maxHeight: '200px',
                      borderRadius: '8px',
                      border: '1px solid rgba(255,255,255,0.2)'
                    }}
                  />
                </div>
              )}
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
              {msg.similarProducts && msg.similarProducts.length > 0 && (
                <div style={{ marginTop: '15px', paddingTop: '15px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                  <p style={{ marginBottom: '10px', fontWeight: 'bold' }}>Similar Products:</p>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '10px' }}>
                    {msg.similarProducts.slice(0, 4).map((product) => (
                      <div 
                        key={product.id} 
                        onClick={() => navigate(`/products?id=${product.id}`)}
                        style={{
                          cursor: 'pointer',
                          padding: '8px',
                          background: 'rgba(255,255,255,0.05)',
                          borderRadius: '8px',
                          border: '1px solid rgba(255,255,255,0.1)',
                          transition: 'all 0.2s'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                          e.currentTarget.style.transform = 'translateY(-2px)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                          e.currentTarget.style.transform = 'translateY(0)';
                        }}
                      >
                        {product.image_url && (
                          <img 
                            src={product.image_url} 
                            alt={product.name}
                            style={{
                              width: '100%',
                              height: '80px',
                              objectFit: 'cover',
                              borderRadius: '4px',
                              marginBottom: '5px'
                            }}
                          />
                        )}
                        <div style={{ fontSize: '12px', fontWeight: 'bold' }}>{product.name}</div>
                        <div style={{ fontSize: '11px', color: '#fbbf24' }}>${parseFloat(product.price).toFixed(2)}</div>
                      </div>
                    ))}
                  </div>
                  {msg.similarProducts.length > 4 && (
                    <p style={{ marginTop: '10px', fontSize: '12px', fontStyle: 'italic' }}>
                      And {msg.similarProducts.length - 4} more... Click to see all!
                    </p>
                  )}
                </div>
              )}
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
          type="file"
          ref={fileInputRef}
          accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
          onChange={handleImageUpload}
          style={{ display: 'none' }}
          disabled={loading || uploadingImage}
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="voice-btn"
          title="Upload image"
          disabled={loading || uploadingImage}
          style={{ 
            background: uploadingImage ? '#6b7280' : 'rgba(255, 255, 255, 0.1)',
            cursor: uploadingImage ? 'not-allowed' : 'pointer'
          }}
        >
          {uploadingImage ? '⏳' : '📷'}
        </button>
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
            className={`voice-btn ${voiceEnabled ? 'speaking-enabled' : ''} ${isSpeaking ? 'speaking' : ''} ${!pollyAvailable ? 'polly-unavailable' : ''}`}
            title={
              !pollyAvailable 
                ? 'AWS Polly not configured - Set AWS credentials in .env to enable voice' 
                : voiceEnabled 
                  ? (isSpeaking ? 'AI is speaking - Click to stop' : 'Voice enabled - Click to disable') 
                  : 'Enable AI voice responses'
            }
            disabled={loading || !pollyAvailable}
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
      
      {/* Clear History Confirmation Modal */}
      {showClearConfirm && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'white',
            padding: '24px',
            borderRadius: '12px',
            maxWidth: '400px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
          }}>
            <h3 style={{ marginTop: 0 }}>Clear Chat History?</h3>
            <p>Are you sure you want to clear all chat messages? This action cannot be undone.</p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '20px' }}>
              <button
                onClick={() => setShowClearConfirm(false)}
                style={{
                  padding: '8px 16px',
                  background: '#e5e7eb',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleClearHistory}
                style={{
                  padding: '8px 16px',
                  background: '#ef4444',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                Clear
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIChat;

