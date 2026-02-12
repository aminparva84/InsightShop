import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import axios from 'axios';
import ProductCard from './ProductCard';
import { useCart } from '../contexts/CartContext';
import { ScoopIcon, BowIcon, PaddingIcon, SlitIcon, getDressStyleIcon, MicrophoneIcon, SpeakerIcon, SpeakerOffIcon, StopIcon, PlayIcon } from './DressStyleIcons';
import './AIChat.css';

const AIChat = ({ onClose, onMinimize, isInline = false, onProductsUpdate = null }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { fetchCart } = useCart();
  const [initialMessage, setInitialMessage] = useState("Hi! I'm your AI shopping assistant. How can I help you find the perfect clothes today? When I show you products, I'll include their ID numbers so you can ask me to compare them!");
  
  // Load current date and sales context for initial message
  useEffect(() => {
    const loadSalesContext = async () => {
      try {
        const response = await axios.get('/api/sales/current-context');
        if (response.data) {
          const { current_date_formatted, active_sales, upcoming_holidays, current_events } = response.data;
          
          let message = `Hi! I'm your AI shopping assistant. Today is ${current_date_formatted}. `;
          
          // Celebrate active sales
          if (active_sales && active_sales.length > 0) {
            message += `🎉 Great news! We have ${active_sales.length} special ${active_sales.length === 1 ? 'sale' : 'sales'} running right now! `;
            active_sales.forEach((sale, index) => {
              message += `${sale.name} - ${sale.discount_percentage}% off`;
              if (index < active_sales.length - 1) message += ', ';
            });
            message += '! ';
          }
          
          // Celebrate current holidays/events
          if (current_events && current_events.length > 0) {
            const eventNames = current_events.map(e => e.name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())).join(', ');
            message += `We're celebrating ${eventNames}! `;
          }
          
          // Mention upcoming holidays
          if (upcoming_holidays && upcoming_holidays.length > 0) {
            const nextHoliday = upcoming_holidays[0];
            const holidayName = nextHoliday.name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
            if (nextHoliday.days_until === 0) {
              message += `Today is ${holidayName}! `;
            } else if (nextHoliday.days_until === 1) {
              message += `${holidayName} is tomorrow! `;
            } else if (nextHoliday.days_until <= 7) {
              message += `${holidayName} is coming up in ${nextHoliday.days_until} days! `;
            }
          }
          
          message += "How can I help you find the perfect clothes today? When I show you products, I'll include their ID numbers so you can ask me to compare them!";
          setInitialMessage(message);
        }
      } catch (error) {
        console.error('Error loading sales context:', error);
        // Use default message if error
      }
    };
    
    loadSalesContext();
  }, []);
  
  // Load chat history from sessionStorage so each new browser tab/session starts fresh
  const loadChatHistory = () => {
    try {
      const saved = sessionStorage.getItem('aiChatHistory');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
    return [{ role: 'assistant', content: initialMessage }];
  };
  
  const [messages, setMessages] = useState(loadChatHistory);
  
  // Update messages when initial message changes (same session only)
  useEffect(() => {
    if (messages.length === 1 && messages[0].role === 'assistant') {
      setMessages([{ role: 'assistant', content: initialMessage }]);
      sessionStorage.setItem('aiChatHistory', JSON.stringify([{ role: 'assistant', content: initialMessage }]));
    }
  }, [initialMessage]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestedProducts, setSuggestedProducts] = useState([]);
  const [selectedProductIds, setSelectedProductIds] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [usedSpeechInput, setUsedSpeechInput] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentlyPlayingMessageId, setCurrentlyPlayingMessageId] = useState(null); // Track which message is playing
  const [voiceEnabled, setVoiceEnabled] = useState(() => {
    // Load voice preference from localStorage
    const saved = localStorage.getItem('aiVoiceEnabled');
    return saved === 'true';
  });
  const [voiceId, setVoiceId] = useState(() => {
    // Load voice ID preference from localStorage, default to 'Joanna'
    const saved = localStorage.getItem('aiVoiceId');
    return saved || 'Joanna';
  });
  const [speechSpeed, setSpeechSpeed] = useState(() => {
    // Load speech speed preference from localStorage, default to 1.1
    const saved = localStorage.getItem('aiSpeechSpeed');
    return saved ? parseFloat(saved) : 1.1;
  });
  const [voiceVolume, setVoiceVolume] = useState(() => {
    // Load voice volume preference from localStorage, default to 0.5 (middle)
    const saved = localStorage.getItem('aiVoiceVolume');
    return saved ? parseFloat(saved) : 0.5;
  });
  const [pollyAvailable, setPollyAvailable] = useState(true); // Assume available by default
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [imageMetadata, setImageMetadata] = useState(null);
  const [imageSimilarProductIds, setImageSimilarProductIds] = useState([]);
  const [findingMatches, setFindingMatches] = useState(false);
  const [matchedProducts, setMatchedProducts] = useState([]);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const audioRef = useRef(null); // For AWS Polly audio playback
  const fileInputRef = useRef(null);
  const inputRef = useRef(null); // For input focus management

  const scrollToBottom = () => {
    // Only scroll if user is not typing (input is empty or not focused)
    if (!input.trim() && document.activeElement?.tagName !== 'INPUT') {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    // Delay scroll to avoid interfering with typing
    const timer = setTimeout(() => {
      scrollToBottom();
    }, 100);
    return () => clearTimeout(timer);
  }, [messages]);

  // Save chat history to sessionStorage whenever messages change (cleared when tab closes)
  useEffect(() => {
    try {
      sessionStorage.setItem('aiChatHistory', JSON.stringify(messages));
    } catch (error) {
      console.error('Error saving chat history:', error);
    }
  }, [messages]);

  // Initialize audio element for AWS Polly playback
  useEffect(() => {
    audioRef.current = new Audio();
    // Set volume from state
    audioRef.current.volume = voiceVolume;
    
    // Check Polly status on mount (only once, silently)
    const checkPollyStatus = async () => {
      try {
        const response = await axios.get('/api/ai/text-to-speech/status');
        if (response.data) {
          setPollyAvailable(response.data.available || false);
          if (!response.data.available && !response.data.has_credentials) {
            // Only log once as info, not warning
            console.info('Voice feature disabled: AWS credentials not configured. Add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to .env to enable.');
          } else if (response.data.available) {
            console.log('✅ AWS Polly is available and ready');
          }
        }
      } catch (error) {
        // Silently handle errors - voice is optional
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
    localStorage.setItem('aiVoiceId', voiceId);
  }, [voiceId]);

  useEffect(() => {
    localStorage.setItem('aiSpeechSpeed', speechSpeed.toString());
  }, [speechSpeed]);

  useEffect(() => {
    localStorage.setItem('aiVoiceVolume', voiceVolume.toString());
    // Update audio volume when it changes
    if (audioRef.current) {
      audioRef.current.volume = voiceVolume;
    }
  }, [voiceVolume]);

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
  const speakText = async (text, messageId = null) => {
    console.log('='.repeat(80));
    console.log('[FRONTEND] speakText called');
    console.log('='.repeat(80));
      console.log('[FRONTEND] Initial state:', { 
      voiceEnabled, 
      pollyAvailable, 
      hasAudioRef: !!audioRef.current, 
      textLength: text?.length, 
      messageId, 
      usedSpeechInput,
      voiceId 
    });
    
    // If voice is disabled but user used mic, enable it
    if (!voiceEnabled && usedSpeechInput) {
      console.log('[FRONTEND] Auto-enabling voice because user used microphone');
      setVoiceEnabled(true);
      localStorage.setItem('aiVoiceEnabled', 'true');
    }
    
    // Check if we should speak (voice enabled OR user used mic)
    const shouldSpeak = voiceEnabled || usedSpeechInput;
    if (!shouldSpeak) {
      console.log('[FRONTEND] ⚠️ Voice is disabled and user did not use mic - aborting');
      console.log('='.repeat(80));
      return;
    }
    
    // Try to use Polly, but don't block if it's not available - try anyway
    // The backend will handle the error gracefully
    if (!audioRef.current) {
      console.log('[FRONTEND] ❌ ERROR: Audio ref is not initialized');
      console.log('='.repeat(80));
      return;
    }

    // Stop any ongoing speech
    if (audioRef.current && !audioRef.current.paused) {
      console.log('[FRONTEND] Stopping any currently playing audio...');
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }

    try {
      setIsSpeaking(true);
      if (messageId) {
        setCurrentlyPlayingMessageId(messageId);
        console.log(`[FRONTEND] Set currently playing message ID: ${messageId}`);
      }
      
      // Count words in the text
      const wordCount = text.trim().split(/\s+/).filter(word => word.length > 0).length;
      console.log(`[FRONTEND] Text word count: ${wordCount}`);
      
      // If text is longer than 100 words, summarize it first
      let textToSpeak = text;
      if (wordCount > 100) {
        console.log('[FRONTEND] Text exceeds 100 words, summarizing before speaking...');
        try {
          const summarizeResponse = await axios.post('/api/ai/summarize', {
            text: text
          });
          
          if (summarizeResponse.data && summarizeResponse.data.summary) {
            textToSpeak = summarizeResponse.data.summary;
            console.log(`[FRONTEND] ✅ Text summarized: ${wordCount} words → ${textToSpeak.trim().split(/\s+/).filter(word => word.length > 0).length} words`);
          } else {
            console.log('[FRONTEND] ⚠️ Summarization failed, using original text');
          }
        } catch (summarizeError) {
          console.error('[FRONTEND] ❌ Error summarizing text:', summarizeError);
          console.log('[FRONTEND] Using original text for TTS');
          // Continue with original text if summarization fails
        }
      }
      
      console.log('[FRONTEND] Preparing TTS API request...');
      console.log(`[FRONTEND]   - Text length: ${textToSpeak.length} characters`);
      console.log(`[FRONTEND]   - Voice ID: ${voiceId}`);
      console.log(`[FRONTEND]   - Text preview: ${textToSpeak.substring(0, 100)}${textToSpeak.length > 100 ? '...' : ''}`);
      
      const requestStartTime = performance.now();
      
      // Determine gender from voice ID for backend compatibility
      const womanVoices = ['Kendra', 'Amy', 'Kimberly', 'Salli', 'Joanna', 'Ivy'];
      const voiceGender = womanVoices.includes(voiceId) ? 'woman' : 'man';
      
      // Call backend to get audio from AWS Polly
      console.log('[FRONTEND] 📤 Sending POST request to /api/ai/text-to-speech...');
      const response = await axios.post('/api/ai/text-to-speech', {
        text: textToSpeak,
        voice_gender: voiceGender,
        voice_id: voiceId,
        speech_speed: speechSpeed
      }, {
        responseType: 'json'
      });
      
      const requestTime = performance.now() - requestStartTime;
      console.log(`[FRONTEND] ✅ TTS API response received (took ${requestTime.toFixed(2)}ms)`);
      console.log('[FRONTEND] Response details:', { 
        hasAudio: !!response.data?.audio, 
        format: response.data?.format,
        voice: response.data?.voice,
        audioLength: response.data?.audio?.length || 0
      });

      if (response.data && response.data.audio) {
        // Convert base64 to blob URL
        console.log('[FRONTEND] Converting base64 audio to blob...');
        const audioData = response.data.audio;
        const base64Length = audioData.length;
        console.log(`[FRONTEND]   - Base64 length: ${base64Length} characters`);
        
        const decodeStartTime = performance.now();
        const binaryString = atob(audioData);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const decodeTime = performance.now() - decodeStartTime;
        console.log(`[FRONTEND] ✅ Base64 decoded (took ${decodeTime.toFixed(2)}ms): ${bytes.length} bytes`);
        
        const blob = new Blob([bytes], { type: 'audio/mpeg' });
        const audioUrl = URL.createObjectURL(blob);
        console.log(`[FRONTEND] ✅ Blob created: ${blob.size} bytes, URL: ${audioUrl.substring(0, 50)}...`);

        // Set up event handlers first
        const handleEnded = () => {
          console.log('[FRONTEND] 🎵 Audio playback ended');
          setIsSpeaking(false);
          setCurrentlyPlayingMessageId(null);
          URL.revokeObjectURL(audioUrl);
          console.log('[FRONTEND] Cleaned up audio URL and state');
          // Remove listeners
          audioRef.current.removeEventListener('ended', handleEnded);
          audioRef.current.removeEventListener('error', handleError);
          console.log('='.repeat(80));
        };

        const handleError = (error) => {
          console.error('[FRONTEND] ❌ Audio playback error:', error);
          console.error('[FRONTEND] Audio error details:', {
            error: audioRef.current?.error,
            code: audioRef.current?.error?.code,
            message: audioRef.current?.error?.message,
            readyState: audioRef.current?.readyState,
            networkState: audioRef.current?.networkState,
            src: audioRef.current?.src?.substring(0, 100)
          });
          setIsSpeaking(false);
          setCurrentlyPlayingMessageId(null);
          URL.revokeObjectURL(audioUrl);
          // Remove listeners
          audioRef.current?.removeEventListener('ended', handleEnded);
          audioRef.current?.removeEventListener('error', handleError);
          console.log('='.repeat(80));
        };

        const handleCanPlay = async () => {
          console.log('[FRONTEND] 🎵 Audio canplay event fired');
          console.log('[FRONTEND]   - readyState:', audioRef.current?.readyState, `(${['HAVE_NOTHING', 'HAVE_METADATA', 'HAVE_CURRENT_DATA', 'HAVE_FUTURE_DATA', 'HAVE_ENOUGH_DATA'][audioRef.current?.readyState] || 'UNKNOWN'})`);
          console.log('[FRONTEND]   - networkState:', audioRef.current?.networkState);
          console.log('[FRONTEND]   - duration:', audioRef.current?.duration, 'seconds');
          console.log('[FRONTEND]   - paused:', audioRef.current?.paused);
          
          try {
            // Play audio - user has already interacted (sent message), so this should work
            console.log('[FRONTEND] ▶️ Attempting to play audio...');
            console.log('[FRONTEND] Audio state before play:', {
              paused: audioRef.current?.paused,
              readyState: audioRef.current?.readyState,
              currentTime: audioRef.current?.currentTime,
              duration: audioRef.current?.duration,
              src: audioRef.current?.src?.substring(0, 100)
            });
            
            const playStartTime = performance.now();
            const playPromise = audioRef.current.play();
            if (playPromise !== undefined) {
              await playPromise;
              const playTime = performance.now() - playStartTime;
              console.log(`[FRONTEND] ✅ Audio play() promise resolved successfully (took ${playTime.toFixed(2)}ms)`);
              console.log('[FRONTEND] Audio is now playing!');
              setIsSpeaking(true); // Ensure speaking state is set
            }
          } catch (playError) {
            // Log all errors for debugging
            console.error('[FRONTEND] ❌ Error playing audio in canplay handler:', playError);
            console.error('[FRONTEND] Error details:', {
              name: playError.name,
              message: playError.message,
              readyState: audioRef.current?.readyState,
              paused: audioRef.current?.paused,
              src: audioRef.current?.src?.substring(0, 50)
            });
            
            // Try one more time after a short delay
            setTimeout(async () => {
              try {
                console.log('[FRONTEND] 🔄 Retrying audio play after error...');
                await audioRef.current.play();
                console.log('[FRONTEND] ✅ Retry successful');
              } catch (retryError) {
                console.error('[FRONTEND] ❌ Retry also failed:', retryError);
                setIsSpeaking(false);
                setCurrentlyPlayingMessageId(null);
                URL.revokeObjectURL(audioUrl);
              }
            }, 200);
          }
        };

        // Clear previous source
        console.log('[FRONTEND] Clearing previous audio source...');
        audioRef.current.src = '';
        audioRef.current.load();
        
        // Add event listeners
        console.log('[FRONTEND] Setting up audio event listeners...');
        audioRef.current.addEventListener('ended', handleEnded);
        audioRef.current.addEventListener('error', handleError);
        audioRef.current.addEventListener('canplay', handleCanPlay);
        audioRef.current.addEventListener('loadstart', () => console.log('[FRONTEND] 🎵 Audio loadstart event'));
        audioRef.current.addEventListener('loadeddata', () => console.log('[FRONTEND] 🎵 Audio loadeddata event'));
        audioRef.current.addEventListener('loadedmetadata', () => console.log('[FRONTEND] 🎵 Audio loadedmetadata event'));
        audioRef.current.addEventListener('playing', () => console.log('[FRONTEND] 🎵 Audio playing event'));
        audioRef.current.addEventListener('pause', () => console.log('[FRONTEND] 🎵 Audio pause event'));
        audioRef.current.addEventListener('waiting', () => console.log('[FRONTEND] 🎵 Audio waiting event'));
        audioRef.current.addEventListener('stalled', () => console.log('[FRONTEND] 🎵 Audio stalled event'));
        
        // Set new source and properties
        console.log('[FRONTEND] Setting audio source and properties...');
        audioRef.current.src = audioUrl;
        // Use current volume from state
        audioRef.current.volume = voiceVolume;
        audioRef.current.preload = 'auto';
        console.log('[FRONTEND]   - src set to:', audioUrl.substring(0, 50) + '...');
        console.log('[FRONTEND]   - volume:', audioRef.current.volume);
        console.log('[FRONTEND]   - preload:', audioRef.current.preload);
        
        // Load the audio
        console.log('[FRONTEND] Calling audio.load()...');
        audioRef.current.load();
        console.log('[FRONTEND] ✅ Audio load() called, waiting for canplay event...');
        
        // Fallback: try playing after a short delay if canplay doesn't fire
        let playTimeout;
        const cleanup = () => {
          if (playTimeout) {
            clearTimeout(playTimeout);
            playTimeout = null;
            console.log('[FRONTEND] Cleaned up play timeout');
          }
        };
        
        // Also try playing immediately if ready
        const tryPlayImmediate = async () => {
          if (audioRef.current && audioRef.current.readyState >= 4) {
            console.log('[FRONTEND] ⚡ Audio is ready (HAVE_ENOUGH_DATA), attempting immediate play');
            try {
              await audioRef.current.play();
              console.log('[FRONTEND] ✅ Immediate play successful');
              cleanup();
            } catch (playError) {
              console.log('[FRONTEND] ⚠️ Immediate play failed, will wait for canplay:', playError.name);
            }
          } else {
            console.log(`[FRONTEND] ⏳ Audio not ready yet (readyState: ${audioRef.current?.readyState}), waiting for canplay...`);
          }
        };
        
        // Try immediate play
        tryPlayImmediate();
        
        playTimeout = setTimeout(async () => {
          cleanup();
          console.log('[FRONTEND] ⏰ Fallback timeout fired');
          console.log('[FRONTEND]   - readyState:', audioRef.current?.readyState);
          console.log('[FRONTEND]   - paused:', audioRef.current?.paused);
          if (audioRef.current && audioRef.current.readyState >= 2 && audioRef.current.paused) {
            try {
              console.log('[FRONTEND] 🔄 Attempting fallback play...');
              await audioRef.current.play();
              console.log('[FRONTEND] ✅ Fallback play successful');
            } catch (playError) {
              console.error('[FRONTEND] ❌ Fallback play error:', playError);
              setIsSpeaking(false);
              setCurrentlyPlayingMessageId(null);
              URL.revokeObjectURL(audioUrl);
              audioRef.current?.removeEventListener('ended', handleEnded);
              audioRef.current?.removeEventListener('error', handleError);
              audioRef.current?.removeEventListener('canplay', handleCanPlay);
            }
          } else {
            console.log('[FRONTEND] ⚠️ Fallback play skipped (audio not ready or already playing)');
          }
        }, 1000); // Increased timeout to 1 second
        
        // Cleanup timeout if audio starts playing before timeout
        audioRef.current.addEventListener('play', () => {
          console.log('[FRONTEND] 🎵 Audio play event fired - audio is now playing');
          cleanup();
        });
      } else {
        // No audio data
        console.error('[FRONTEND] ❌ ERROR: No audio data in response');
        console.error('[FRONTEND] Response data:', response.data);
        setIsSpeaking(false);
        setCurrentlyPlayingMessageId(null);
        console.log('='.repeat(80));
      }
    } catch (error) {
      setIsSpeaking(false);
      setCurrentlyPlayingMessageId(null);
      // Log all TTS errors for debugging
      console.error('[FRONTEND] ❌ EXCEPTION in speakText');
      console.error('[FRONTEND] Error type:', error.name);
      console.error('[FRONTEND] Error message:', error.message);
      console.error('[FRONTEND] Error details:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        error: error.response?.data?.error || error.message,
        serviceUnavailable: error.response?.status === 503,
        hasResponse: !!error.response,
        responseData: error.response?.data
      });
      
      // Show user-friendly message if it's not a service unavailable error
      if (error.response?.status && error.response.status !== 503) {
        console.error('[FRONTEND] TTS Error:', error.response?.data?.error || error.message);
      }
      console.log('='.repeat(80));
    }
  };

  // Stop speaking
  const stopSpeaking = () => {
    console.log('[FRONTEND] 🛑 stopSpeaking called');
    
    // Stop audio playback completely
    if (audioRef.current) {
      console.log('[FRONTEND] Stopping audio playback...');
      console.log('[FRONTEND]   - Current state:', {
        paused: audioRef.current.paused,
        currentTime: audioRef.current.currentTime,
        readyState: audioRef.current.readyState
      });
      
      // Remove all event listeners to prevent any callbacks
      const audioElement = audioRef.current;
      const newAudio = new Audio();
      
      // Copy any needed properties, then replace
      audioRef.current = newAudio;
      
      // Stop the old audio
      audioElement.pause();
      audioElement.currentTime = 0;
      audioElement.src = '';
      audioElement.load();
      
      // Clear all event listeners by removing src
      if (audioElement.src) {
        URL.revokeObjectURL(audioElement.src);
      }
      
      console.log('[FRONTEND] ✅ Audio element reset and stopped');
    }
    
    // Reset all state
    setIsSpeaking(false);
    setCurrentlyPlayingMessageId(null);
    
    console.log('[FRONTEND] ✅ All audio state cleared');
  };
  
  // Play specific message
  const playMessage = (messageContent, messageId) => {
    console.log('[FRONTEND] 🎵 playMessage called');
    console.log('[FRONTEND]   - messageId:', messageId);
    console.log('[FRONTEND]   - messageContent length:', messageContent?.length);
    console.log('[FRONTEND]   - current voiceEnabled:', voiceEnabled);
    console.log('[FRONTEND]   - current pollyAvailable:', pollyAvailable);
    console.log('[FRONTEND]   - isCurrentlyPlaying:', currentlyPlayingMessageId === messageId);
    
    // If clicking on the same message that's playing, stop it
    if (currentlyPlayingMessageId === messageId && isSpeaking) {
      console.log('[FRONTEND] Same message is playing - stopping it');
      stopSpeaking();
      return; // Don't restart, just stop
    }
    
    // Stop any currently playing audio
    if (audioRef.current && !audioRef.current.paused) {
      console.log('[FRONTEND] Stopping currently playing audio...');
      stopSpeaking();
      // Wait a moment for cleanup
      setTimeout(() => {
        // Enable voice if not already enabled
        if (!voiceEnabled) {
          console.log('[FRONTEND] Auto-enabling voice for manual play');
          setVoiceEnabled(true);
          localStorage.setItem('aiVoiceEnabled', 'true');
        }
        
        // Speak the message
        console.log('[FRONTEND] Calling speakText with messageId:', messageId);
        speakText(messageContent, messageId);
      }, 100);
    } else {
      // Enable voice if not already enabled
      if (!voiceEnabled) {
        console.log('[FRONTEND] Auto-enabling voice for manual play');
        setVoiceEnabled(true);
        localStorage.setItem('aiVoiceEnabled', 'true');
      }
      
      // Speak the message
      console.log('[FRONTEND] Calling speakText with messageId:', messageId);
      speakText(messageContent, messageId);
    }
  };

  // Toggle voice on/off
  const toggleVoice = () => {
    if (isSpeaking) {
      stopSpeaking();
    }
    setVoiceEnabled(prev => !prev);
  };

  // Clear chat history and reset voice settings to defaults
  const handleClearHistory = () => {
    setMessages([{ role: 'assistant', content: initialMessage }]);
    sessionStorage.setItem('aiChatHistory', JSON.stringify([{ role: 'assistant', content: initialMessage }]));
    
    // Reset voice settings to defaults: Joanna, speed 1.1, volume 0.5 (middle)
    setVoiceId('Joanna');
    setSpeechSpeed(1.1);
    setVoiceVolume(0.5);
    
    // Reset audio volume to middle (0.5)
    if (audioRef.current) {
      audioRef.current.volume = 0.5;
    }
    
    // Save defaults to localStorage
    localStorage.setItem('aiVoiceId', 'Joanna');
    localStorage.setItem('aiSpeechSpeed', '1.1');
    localStorage.setItem('aiVoiceVolume', '0.5');
    
    // Stop any ongoing speech
    if (isSpeaking) {
      stopSpeaking();
    }
    
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
        setUsedSpeechInput(true); // Mark that user used speech input
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
        
        // Store metadata and similar product IDs for match finding
        setImageMetadata(response.data.metadata || {});
        setImageSimilarProductIds(response.data.similar_product_ids || []);
        setMatchedProducts([]); // Reset matched products

        // Store response data for action buttons
        const imageResponseData = {
          similar_products: response.data.similar_products || [],
          similar_product_ids: response.data.similar_product_ids || [],
          metadata: response.data.metadata || {},
          message: response.data.message || response.data.metadata_sentence || 'Image analyzed successfully!'
        };
        
        // Add user message showing image thumbnail with action buttons
        const imageMessage = {
          role: 'user',
          content: `[Image uploaded: ${file.name}]`,
          image: response.data.image_data,
          showImageActions: true, // Flag to show action buttons
          imageMetadata: imageResponseData.metadata,
          imageSimilarProductIds: imageResponseData.similar_product_ids,
          imageResponseData: imageResponseData // Store full response for action buttons
        };
        setMessages(prev => [...prev, imageMessage]);

        // Don't automatically add AI response - let user choose action first
        // The action buttons will trigger the appropriate response
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

  // Find matching products for uploaded image
  const findMatchesForImage = async () => {
    if (!uploadedImage || (!imageMetadata && imageSimilarProductIds.length === 0)) {
      alert('Please upload an image first');
      return;
    }

    setFindingMatches(true);

    try {
      const response = await axios.post('/api/ai/find-matches-for-image', {
        metadata: imageMetadata,
        similar_product_ids: imageSimilarProductIds
      });

      if (response.data.success) {
        const matched = response.data.matched_products || [];
        setMatchedProducts(matched);

        // Add message with matched products
        const matchMessage = {
          role: 'assistant',
          content: `I found ${matched.length} matching item${matched.length !== 1 ? 's' : ''} that would go great with your uploaded image!`,
          matchedProducts: matched,
          matchExplanations: response.data.match_explanations || []
        };
        setMessages(prev => [...prev, matchMessage]);

        // Update selected products
        if (matched.length > 0) {
          const matchedIds = matched.map(p => p.id);
          setSelectedProductIds(prev => {
            const combined = [...new Set([...prev, ...matchedIds])];
            return combined;
          });

          // Navigate to show matched products
          if (location.pathname === '/' && onProductsUpdate) {
            onProductsUpdate(matchedIds);
            // Keep focus on chat input instead of scrolling
            setTimeout(() => {
              if (inputRef.current) {
                inputRef.current.focus();
              }
            }, 100);
          } else {
            const idsParam = matchedIds.join(',');
            navigate(`/products?ai_results=${encodeURIComponent(idsParam)}&tab=ai`);
          }
        }
      }
    } catch (error) {
      console.error('Error finding matches:', error);
      alert(error.response?.data?.error || 'Failed to find matches. Please try again.');
    } finally {
      setFindingMatches(false);
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
    
    // Scroll chat messages to bottom and keep input focused
    setTimeout(() => {
      // Scroll chat messages container to show new message
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
      // Keep input focused
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }, 50);

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

      // When agent executed a cart action: refresh cart, redirect if requested, then close chat
      if (response.data.action === 'agent_executed') {
        if (fetchCart) fetchCart();
        const redirectTo = response.data.redirect_to;
        if (redirectTo) {
          navigate(redirectTo);
          if (onClose) onClose();
          return;
        }
      }
      
      // Scroll chat to show new AI message and keep input focused
      setTimeout(() => {
        if (messagesEndRef.current) {
          messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        if (inputRef.current) {
          inputRef.current.focus();
        }
      }, 100);
      
      // Speak the AI's response if voice is enabled OR user used mic
      // Auto-enable voice if user used speech input (they clearly want voice interaction)
      const shouldSpeak = voiceEnabled || usedSpeechInput;
      if (shouldSpeak && response.data.response && audioRef.current) {
        // Small delay to ensure message is added to state and audio is ready
        setTimeout(() => {
          if (audioRef.current) {
            // Auto-enable voice if user used speech input (they clearly want voice interaction)
            if (usedSpeechInput && !voiceEnabled) {
              setVoiceEnabled(true);
              localStorage.setItem('aiVoiceEnabled', 'true');
            }
            // Use message index as ID for tracking
            const messageId = `msg-${messages.length + 1}`; // +1 because we just added the AI message
            speakText(response.data.response, messageId);
          }
        }, 300);
      }
      
      // Reset speech input flag after processing
      if (usedSpeechInput) {
        setUsedSpeechInput(false);
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
      
      // Handle comparison action - navigate in background; keep chat open (user closes when they want)
      if (response.data.action === 'compare' && response.data.compare_ids) {
        const compareIds = response.data.compare_ids;
        navigate(`/compare?ids=${compareIds.join(',')}`);
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
      
      // Process AI response
      
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
          // Extract product IDs from response
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
              
              onProductsUpdate(backendIds);
            } else if (response.data.suggested_products && response.data.suggested_products.length > 0) {
              // Fallback: extract IDs from suggested_products
              const suggestedIds = response.data.suggested_products.map(p => p.id || p).filter(id => id != null);
              onProductsUpdate(suggestedIds);
            } else {
              // Last resort: use extracted IDs
              onProductsUpdate(productIds);
            }
            
            // Update AI message (use backend response as-is; do not append "I found X products")
            const updatedMessage = {
              role: 'assistant',
              content: response.data.response
            };
            setMessages(prev => {
              const newMessages = [...prev];
              newMessages[newMessages.length - 1] = updatedMessage;
              return newMessages;
            });
            
            // Keep focus on chat input instead of scrolling to products
            setTimeout(() => {
              if (inputRef.current) {
                inputRef.current.focus();
              }
            }, 100);
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
          
          // Update AI message (use backend response as-is; do not append default summary)
          const updatedMessage = {
            role: 'assistant',
            content: response.data.response
          };
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = updatedMessage;
            return newMessages;
          });
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
    <div
      className={`ai-chat ${isInline ? 'ai-chat-inline' : ''}`}
      role="region"
      aria-label="AI Shopping Assistant chat"
    >
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

      <div className="ai-chat-messages" role="log" aria-live="polite" aria-label="Chat messages">
        {messages.map((msg, idx) => {
          const messageId = `msg-${idx}`;
          const isCurrentlyPlaying = currentlyPlayingMessageId === messageId;
          
          // Debug log for assistant messages
          if (msg.role === 'assistant' && idx === messages.length - 1) {
            console.log('[FRONTEND] 🎨 Rendering assistant message:', {
              messageId,
              idx,
              contentLength: msg.content?.length,
              isCurrentlyPlaying,
              totalMessages: messages.length
            });
          }
          
          return (
          <div key={idx} className={`message ${msg.role}`} role="article" aria-label={msg.role === 'user' ? 'Your message' : 'Assistant message'}>
            <div className="message-content">
              {/* Play button for assistant messages - always show, handle errors gracefully */}
              {msg.role === 'assistant' && (
                <button
                  onClick={() => {
                    if (isCurrentlyPlaying) {
                      console.log('[FRONTEND] 🛑 Stop button clicked for message:', messageId);
                      stopSpeaking();
                    } else {
                      console.log('[FRONTEND] 🎵 Play button clicked for message:', messageId);
                      playMessage(msg.content, messageId);
                    }
                  }}
                  className="message-play-btn"
                  title={isCurrentlyPlaying ? "Click to stop playback" : "Play voice"}
                  disabled={loading}
                  style={{
                    position: 'absolute',
                    top: '8px',
                    right: '8px',
                    background: isCurrentlyPlaying ? '#ef4444' : 'rgba(212, 175, 55, 0.15)',
                    border: isCurrentlyPlaying ? '1px solid #dc2626' : '1px solid #d4af37',
                    borderRadius: '4px',
                    padding: '4px 8px',
                    cursor: loading ? 'default' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '12px',
                    color: isCurrentlyPlaying ? '#ffffff' : '#1a2332',
                    transition: 'all 0.2s',
                    zIndex: 100,
                    visibility: 'visible',
                    opacity: 0.9,
                    minWidth: '60px',
                    fontWeight: '500',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                  }}
                >
                  {isCurrentlyPlaying ? (
                    <>
                      <StopIcon size={14} />
                      <span>Stop</span>
                    </>
                  ) : (
                    <>
                      <PlayIcon size={14} />
                      <span>Play</span>
                    </>
                  )}
                </button>
              )}
              {msg.image && (
                <div style={{ marginBottom: '10px' }}>
                  <img 
                    src={`data:image/${msg.image.includes('data:') ? '' : 'jpeg;base64,'}${msg.image}`}
                    alt="Uploaded"
                    style={{
                      maxWidth: '100%',
                      maxHeight: '200px',
                      borderRadius: '8px',
                      border: '1px solid rgba(255,255,255,0.2)',
                      objectFit: 'contain'
                    }}
                  />
                  {/* Show action buttons for uploaded images */}
                  {msg.showImageActions && (
                    <div style={{ 
                      marginTop: '12px', 
                      display: 'flex', 
                      gap: '8px', 
                      flexWrap: 'wrap' 
                    }}>
                      <button
                        onClick={async () => {
                          // Find similar items using stored response data
                          setLoading(true);
                          try {
                            const imageData = msg.imageResponseData || {};
                            const similarProducts = imageData.similar_products || [];
                            const productIds = imageData.similar_product_ids || [];
                            
                            if (similarProducts.length === 0 && productIds.length === 0) {
                              // If no data stored, re-analyze
                              const formData = new FormData();
                              const blob = await fetch(`data:image/jpeg;base64,${msg.image}`).then(r => r.blob());
                              formData.append('image', blob, 'uploaded-image.jpg');
                              
                              const similarResponse = await axios.post('/api/ai/upload-image', formData, {
                                headers: { 'Content-Type': 'multipart/form-data' }
                              });
                              
                              if (similarResponse.data.success) {
                                const aiResponse = {
                                  role: 'assistant',
                                  content: similarResponse.data.message || `I found ${similarResponse.data.similar_products?.length || 0} similar item${(similarResponse.data.similar_products?.length || 0) !== 1 ? 's' : ''} in our store!`,
                                  similarProducts: similarResponse.data.similar_products || [],
                                  showMatchButtons: false
                                };
                                setMessages(prev => [...prev, aiResponse]);
                                
                                const ids = similarResponse.data.similar_product_ids || [];
                                if (ids.length > 0) {
                                  setSelectedProductIds(prev => {
                                    const combined = [...new Set([...prev, ...ids])];
                                    return combined;
                                  });
                                  
                                  if (location.pathname === '/' && onProductsUpdate) {
                                    onProductsUpdate(ids);
                                    // Keep focus on chat input instead of scrolling
                                    setTimeout(() => {
                                      if (inputRef.current) {
                                        inputRef.current.focus();
                                      }
                                    }, 100);
                                  } else {
                                    const idsParam = ids.join(',');
                                    navigate(`/products?ai_results=${encodeURIComponent(idsParam)}&tab=ai`);
                                  }
                                }
                                
                                if (voiceEnabled && audioRef.current) {
                                  setTimeout(() => {
                                    speakText(aiResponse.content);
                                  }, 300);
                                }
                              }
                            } else {
                              // Use stored data
                              const aiResponse = {
                                role: 'assistant',
                                content: imageData.message || `I found ${similarProducts.length} similar item${similarProducts.length !== 1 ? 's' : ''} in our store!`,
                                similarProducts: similarProducts,
                                showMatchButtons: false
                              };
                              setMessages(prev => [...prev, aiResponse]);
                              
                              if (productIds.length > 0) {
                                setSelectedProductIds(prev => {
                                  const combined = [...new Set([...prev, ...productIds])];
                                  return combined;
                                });
                                
                                if (location.pathname === '/' && onProductsUpdate) {
                                  onProductsUpdate(productIds);
                                  // Keep focus on chat input instead of scrolling
                                  setTimeout(() => {
                                    if (inputRef.current) {
                                      inputRef.current.focus();
                                    }
                                  }, 100);
                                } else {
                                  const idsParam = productIds.join(',');
                                  navigate(`/products?ai_results=${encodeURIComponent(idsParam)}&tab=ai`);
                                }
                              }
                              
                              if (voiceEnabled && audioRef.current) {
                                setTimeout(() => {
                                  speakText(aiResponse.content);
                                }, 300);
                              }
                            }
                          } catch (error) {
                            console.error('Error finding similar items:', error);
                            alert(error.response?.data?.error || 'Failed to find similar items. Please try again.');
                          } finally {
                            setLoading(false);
                          }
                        }}
                        disabled={loading}
                        style={{
                          padding: '8px 16px',
                          background: loading ? '#9ca3af' : '#667eea',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: loading ? 'not-allowed' : 'pointer',
                          fontSize: '14px',
                          fontWeight: '500',
                          transition: 'all 0.2s'
                        }}
                      >
                        {loading ? '🔍 Searching...' : '🔍 Find Similar Item'}
                      </button>
                      <button
                        onClick={async () => {
                          // Find fashion match
                          setFindingMatches(true);
                          try {
                            const matchResponse = await axios.post('/api/ai/find-matches-for-image', {
                              metadata: msg.imageMetadata,
                              similar_product_ids: msg.imageSimilarProductIds || []
                            });
                            
                            if (matchResponse.data.success) {
                              const matched = matchResponse.data.matched_products || [];
                              const aiResponse = {
                                role: 'assistant',
                                content: `I found ${matched.length} matching item${matched.length !== 1 ? 's' : ''} that would create a complete outfit!`,
                                matchedProducts: matched,
                                matchExplanations: matchResponse.data.match_explanations || []
                              };
                              setMessages(prev => [...prev, aiResponse]);
                              
                              if (matched.length > 0) {
                                const matchedIds = matched.map(p => p.id);
                                setSelectedProductIds(prev => {
                                  const combined = [...new Set([...prev, ...matchedIds])];
                                  return combined;
                                });
                                
                                if (location.pathname === '/' && onProductsUpdate) {
                                  onProductsUpdate(matchedIds);
                                  // Keep focus on chat input instead of scrolling
                                  setTimeout(() => {
                                    if (inputRef.current) {
                                      inputRef.current.focus();
                                    }
                                  }, 100);
                                } else {
                                  const idsParam = matchedIds.join(',');
                                  navigate(`/products?ai_results=${encodeURIComponent(idsParam)}&tab=ai`);
                                }
                              }
                              
                              // Speak the response if voice is enabled
                              if (voiceEnabled && audioRef.current) {
                                setTimeout(() => {
                                  speakText(aiResponse.content);
                                }, 300);
                              }
                            }
                          } catch (error) {
                            console.error('Error finding matches:', error);
                            alert(error.response?.data?.error || 'Failed to find matches. Please try again.');
                          } finally {
                            setFindingMatches(false);
                          }
                        }}
                        disabled={findingMatches}
                        style={{
                          padding: '8px 16px',
                          background: findingMatches ? '#9ca3af' : '#10b981',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: findingMatches ? 'not-allowed' : 'pointer',
                          fontSize: '14px',
                          fontWeight: '500',
                          transition: 'all 0.2s'
                        }}
                      >
                        {findingMatches ? '🎯 Finding Match...' : '👔 Find Fashion Match'}
                      </button>
                    </div>
                  )}
                </div>
              )}
              
              {/* Show match buttons after image upload analysis - show if this is an assistant message after an image upload */}
              {msg.role === 'assistant' && uploadedImage && (msg.showMatchButtons || msg.hasImageUpload || idx === messages.length - 1) && (
                <div style={{ marginTop: '12px', marginBottom: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <button
                    onClick={findMatchesForImage}
                    disabled={findingMatches}
                    style={{
                      padding: '8px 16px',
                      background: findingMatches ? '#9ca3af' : '#667eea',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: findingMatches ? 'not-allowed' : 'pointer',
                      fontSize: '14px',
                      fontWeight: '500',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      if (!findingMatches) e.target.style.background = '#5568d3';
                    }}
                    onMouseLeave={(e) => {
                      if (!findingMatches) e.target.style.background = '#667eea';
                    }}
                  >
                    {findingMatches ? '🔍 Finding Matches...' : '🎯 Find Matching Items'}
                  </button>
                  {msg.similarProducts && msg.similarProducts.length > 0 && (
                    <button
                      onClick={() => {
                        const productIds = msg.similarProducts.map(p => p.id);
                        if (location.pathname === '/' && onProductsUpdate) {
                          onProductsUpdate(productIds);
                          // Keep focus on chat input instead of scrolling
                          setTimeout(() => {
                            if (inputRef.current) {
                              inputRef.current.focus();
                            }
                          }, 100);
                        } else {
                          const idsParam = productIds.join(',');
                          navigate(`/products?ai_results=${encodeURIComponent(idsParam)}&tab=ai`);
                        }
                      }}
                      style={{
                        padding: '8px 16px',
                        background: 'rgba(102, 126, 234, 0.1)',
                        color: '#667eea',
                        border: '1px solid #667eea',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        fontWeight: '500',
                        transition: 'all 0.2s'
                      }}
                      onMouseEnter={(e) => {
                        e.target.style.background = 'rgba(102, 126, 234, 0.2)';
                      }}
                      onMouseLeave={(e) => {
                        e.target.style.background = 'rgba(102, 126, 234, 0.1)';
                      }}
                    >
                      👀 View Similar Items ({msg.similarProducts.length})
                    </button>
                  )}
                </div>
              )}
              
              {msg.content.split('\n').map((line, lineIdx) => {
                // Match "Product #ID" or "Product ID" so product mentions are clickable
                const productPattern = /(Product\s*#?\s*\d+)/gi;
                const parts = line.split(productPattern);
                return (
                  <React.Fragment key={lineIdx}>
                    {parts.map((part, partIdx) => {
                      const productIdMatch = part.match(/Product\s*#?\s*(\d+)/i);
                      if (productIdMatch) {
                        const productId = productIdMatch[1];
                        return (
                          <Link
                            key={`${lineIdx}-${partIdx}-${productId}`}
                            to={`/products/${productId}`}
                            className="product-id-highlight product-id-link"
                            style={{ display: 'inline', pointerEvents: 'auto', cursor: 'pointer' }}
                            onClick={(e) => {
                              e.stopPropagation();
                              e.preventDefault();
                              navigate(`/products/${productId}`);
                              if (onClose) onClose();
                            }}
                          >
                            {part}
                          </Link>
                        );
                      }
                      return <span key={`${lineIdx}-${partIdx}`}>{part}</span>;
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
              
              {/* Display matched products */}
              {msg.matchedProducts && msg.matchedProducts.length > 0 && (
                <div style={{ marginTop: '16px', paddingTop: '15px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                  <div style={{ 
                    fontSize: '14px', 
                    fontWeight: '600', 
                    color: '#faf0e6', 
                    marginBottom: '12px' 
                  }}>
                    🎯 Matching Items:
                  </div>
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', 
                    gap: '12px' 
                  }}>
                    {msg.matchedProducts.slice(0, 4).map((product) => (
                      <div
                        key={product.id}
                        onClick={() => navigate(`/products/${product.id}`)}
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
                        <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#faf0e6' }}>
                          {product.name}
                        </div>
                        <div style={{ fontSize: '11px', color: '#fbbf24' }}>
                          ${product.price?.toFixed(2)}
                        </div>
                      </div>
                    ))}
                  </div>
                  {msg.matchedProducts.length > 4 && (
                    <div style={{ 
                      marginTop: '12px', 
                      fontSize: '12px', 
                      color: '#faf0e6',
                      textAlign: 'center',
                      fontStyle: 'italic'
                    }}>
                      And {msg.matchedProducts.length - 4} more matching items...
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
          );
        })}
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
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            // Keep focus on input when typing
            if (inputRef.current && document.activeElement !== inputRef.current) {
              inputRef.current.focus();
            }
          }}
          onFocus={() => {
            // Prevent scrolling when input is focused
            if (messagesEndRef.current) {
              messagesEndRef.current.scrollIntoView = () => {}; // Disable auto-scroll
            }
          }}
          onBlur={() => {
            // Re-enable scrolling when input loses focus
            if (messagesEndRef.current) {
              messagesEndRef.current.scrollIntoView = function(options) {
                Element.prototype.scrollIntoView.call(this, options);
              };
            }
          }}
          placeholder="Ask about products, compare items, or describe what you're looking for..."
          disabled={loading || isListening}
          aria-label="Message to AI assistant"
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
            <>
              <select
                className="voice-gender-select"
                value={voiceId}
                onChange={(e) => {
                  setVoiceId(e.target.value);
                  if (isSpeaking) stopSpeaking();
                }}
                title="Select voice"
                style={{ minWidth: '140px' }}
              >
                <optgroup label="Women's Voices">
                  <option value="Joanna">Joanna (Neural) - Default</option>
                  <option value="Kendra">Kendra (Warm)</option>
                  <option value="Amy">Amy (Expressive)</option>
                  <option value="Kimberly">Kimberly (Smooth)</option>
                  <option value="Salli">Salli (Clear)</option>
                  <option value="Ivy">Ivy (Young)</option>
                </optgroup>
                <optgroup label="Men's Voices">
                  <option value="Joey">Joey (Energetic)</option>
                  <option value="Justin">Justin (Expressive)</option>
                  <option value="Matthew">Matthew (Calm)</option>
                  <option value="Kevin">Kevin (Neural)</option>
                  <option value="Brian">Brian (British)</option>
                  <option value="Russell">Russell (Australian)</option>
                </optgroup>
              </select>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '0 4px' }}>
                <label style={{ fontSize: '11px', color: '#1a2332', whiteSpace: 'nowrap' }}>Speed:</label>
                <input
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  value={speechSpeed}
                  onChange={(e) => {
                    setSpeechSpeed(parseFloat(e.target.value));
                    if (isSpeaking) stopSpeaking();
                  }}
                  title={`Speech speed: ${speechSpeed}x`}
                  style={{ width: '60px', cursor: 'pointer' }}
                />
                <span style={{ fontSize: '11px', color: '#1a2332', minWidth: '30px' }}>{speechSpeed.toFixed(1)}x</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '0 4px' }}>
                <label style={{ fontSize: '11px', color: '#1a2332', whiteSpace: 'nowrap' }}>Volume:</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={voiceVolume}
                  onChange={(e) => {
                    setVoiceVolume(parseFloat(e.target.value));
                    if (isSpeaking) stopSpeaking();
                  }}
                  title={`Volume: ${Math.round(voiceVolume * 100)}%`}
                  style={{ width: '60px', cursor: 'pointer' }}
                />
                <span style={{ fontSize: '11px', color: '#1a2332', minWidth: '35px' }}>{Math.round(voiceVolume * 100)}%</span>
              </div>
            </>
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
        <div
          className="ai-chat-modal-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="ai-chat-clear-title"
          aria-describedby="ai-chat-clear-desc"
          onClick={(e) => e.target === e.currentTarget && setShowClearConfirm(false)}
        >
          <div className="ai-chat-modal">
            <h3 id="ai-chat-clear-title" style={{ marginTop: 0 }}>Clear Chat History?</h3>
            <p id="ai-chat-clear-desc">Are you sure you want to clear all chat messages? This action cannot be undone.</p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '20px' }}>
              <button
                type="button"
                onClick={() => setShowClearConfirm(false)}
                className="ai-chat-modal-cancel"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleClearHistory}
                className="ai-chat-modal-confirm"
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

