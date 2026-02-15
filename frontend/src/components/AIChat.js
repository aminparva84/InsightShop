import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import axios from 'axios';
import ProductCard from './ProductCard';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import { ScoopIcon, BowIcon, PaddingIcon, SlitIcon, getDressStyleIcon, MicrophoneIcon, SpeakerIcon, SpeakerOffIcon, StopIcon, PlayIcon } from './DressStyleIcons';
import './AIChat.css';

// Kendo-style toolbar icons (Copy, Retry, Download, More, Sparkles, Attachment)
const CopyIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
  </svg>
);
const RetryIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 4v6h6"/>
    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
  </svg>
);
const DownloadIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="7 10 12 15 17 10"/>
    <line x1="12" y1="15" x2="12" y2="3"/>
  </svg>
);
const MoreVerticalIcon = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="1"/>
    <circle cx="12" cy="5" r="1"/>
    <circle cx="12" cy="19" r="1"/>
  </svg>
);
const SparklesIcon = ({ size = 64 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z"/>
    <path d="M5 19l1.5-2L9 17.5 7.5 19 6 20.5l1.5-2L9 17.5"/>
    <path d="M19 5l-1.5 2L16 6.5 17.5 5 19 3.5l-1.5 2L16 6.5"/>
  </svg>
);
const AttachmentIcon = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
  </svg>
);
const TrashIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
    <line x1="10" y1="11" x2="10" y2="17"/>
    <line x1="14" y1="11" x2="14" y2="17"/>
  </svg>
);

const AIChat = ({ onClose, onMinimize, isInline = false, onProductsUpdate = null }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { fetchCart } = useCart();
  const { user } = useAuth();
  const isAdmin = !!(user?.is_admin || user?.is_superadmin);
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
  const [headerMenuOpen, setHeaderMenuOpen] = useState(false);
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

  // Kendo-style suggestions (clickable prompts)
  const SUGGESTIONS = [
    { id: 'show_blue', text: 'Show me blue shirts' },
    { id: 'compare', text: 'Compare products by ID' },
    { id: 'on_sale', text: "What's on sale?" },
    { id: 'style_advice', text: 'Style advice for an interview' }
  ];

  const handleSuggestionClick = (suggestion) => {
    if (loading) return;
    performSend(suggestion.text, messages);
  };

  // Toolbar actions for AI messages (Copy, Retry, Download)
  const handleToolbarAction = (actionId, msg, msgIndex) => {
    switch (actionId) {
      case 'copy':
        if (msg.content) {
          navigator.clipboard.writeText(msg.content).catch(() => {});
        }
        break;
      case 'retry':
        if (msgIndex > 0) {
          const prevMsg = messages[msgIndex - 1];
          if (prevMsg.role === 'user' && prevMsg.content) {
            const historyForRequest = messages.slice(0, msgIndex - 1);
            performSend(prevMsg.content, historyForRequest);
          }
        }
        break;
      case 'download':
        if (msg.content) {
          const blob = new Blob([msg.content], { type: 'text/plain' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `message_${msgIndex}.txt`;
          a.style.display = 'none';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }
        break;
      default:
        break;
    }
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

  // Core send: set messages (history + user message), call API, then handle response. Used by handleSend and Retry.
  const performSend = async (userText, historyForRequest) => {
    const userInputLower = userText.toLowerCase();
    setMessages([...historyForRequest, { role: 'user', content: userText }]);
    setLoading(true);

    if (location.pathname === '/products') {
      const currentParams = new URLSearchParams(window.location.search);
      const hasAiResults = currentParams.get('ai_results');
      if (currentParams.get('tab') !== 'ai' && !hasAiResults) {
        currentParams.set('tab', 'ai');
        navigate(`/products?${currentParams.toString()}`);
      }
    }

    setTimeout(() => {
      if (messagesEndRef.current) messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      if (inputRef.current) inputRef.current.focus();
    }, 50);

    const showInChatKeywords = ['show it here', 'show here', 'display here', 'list here', 'show me here', 'tell me here', 'show them here'];
    const wantsToSeeInChat = showInChatKeywords.some(keyword => userInputLower.includes(keyword));

    try {
      const chatUrl = isAdmin ? '/api/ai/chat-with-tools' : '/api/ai/chat';
      const payload = {
        message: userText,
        history: historyForRequest,
        selected_product_ids: selectedProductIds
      };
      const response = await axios.post(chatUrl, payload);

      const aiMessage = {
        role: 'assistant',
        content: response.data.response || response.data.message || 'No response.'
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

      // Admin: redirect to Admin page with product form prefill (create or edit from assistant)
      if (response.data.redirect_prefill && isAdmin) {
        const r = response.data.redirect_prefill;
        navigate(r.path || '/admin', {
          state: {
            fromAssistant: true,
            tab: r.tab || 'products',
            openProductForm: r.openProductForm || false,
            prefillProduct: r.prefill || null,
            editProductId: r.editProductId || null,
          },
        });
        if (onClose) onClose();
        return;
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

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    performSend(input, messages);
    setInput('');
  };

  const showEmptyState = messages.length <= 1 && messages[0]?.role === 'assistant';
  const handleDownloadConversation = () => {
    setHeaderMenuOpen(false);
    const text = messages.map(m => `${m.role === 'user' ? 'You' : 'AI'}: ${m.content || ''}`).join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'conversation.txt';
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div
      className={`ai-chat ai-chat-kendo ${isInline ? 'ai-chat-inline' : ''}`}
      role="region"
      aria-label="AI Shopping Assistant chat"
    >
      <div className="ai-chat-header kendo-header">
        <div className="kendo-header-avatar">
          <div className="kendo-avatar" aria-hidden="true" />
        </div>
        <div className="kendo-header-title">AI Shopping Assistant</div>
        <div className="kendo-header-spacer" />
        <div className="kendo-header-actions">
          <div className="kendo-dropdown-wrap">
            <button
              type="button"
              className="kendo-header-menu-btn"
              onClick={() => setHeaderMenuOpen(prev => !prev)}
              aria-haspopup="true"
              aria-expanded={headerMenuOpen}
              title="Menu"
            >
              <MoreVerticalIcon size={20} />
            </button>
            {headerMenuOpen && (
              <>
                <div className="kendo-dropdown-backdrop" onClick={() => setHeaderMenuOpen(false)} aria-hidden="true" />
                <div className="kendo-dropdown-menu">
                  <button type="button" className="kendo-dropdown-item" onClick={handleDownloadConversation}>
                    <DownloadIcon size={16} /> Download conversation
                  </button>
                  <button type="button" className="kendo-dropdown-item" onClick={() => { setShowClearConfirm(true); setHeaderMenuOpen(false); }}>
                    <TrashIcon size={16} /> Clear conversation
                  </button>
                </div>
              </>
            )}
          </div>
          {!isInline && (
            <>
              <button type="button" onClick={onMinimize || onClose} className="kendo-header-icon-btn" title="Minimize">−</button>
              <button type="button" onClick={onClose} className="kendo-header-icon-btn" title="Close">×</button>
            </>
          )}
        </div>
      </div>

      <div className="ai-chat-messages" role="log" aria-live="polite" aria-label="Chat messages">
        {showEmptyState ? (
          <div className="kendo-empty-state">
            <div className="kendo-empty-icon">
              <SparklesIcon size={64} />
            </div>
            <p className="kendo-empty-title">Ask AI</p>
            <p className="kendo-empty-subtitle">Start conversation by typing a message or selecting a prompt.</p>
            <div className="kendo-suggestions-chips">
              {SUGGESTIONS.map(s => (
                <button key={s.id} type="button" className="kendo-suggestion-chip" onClick={() => handleSuggestionClick(s)}>
                  {s.text}
                </button>
              ))}
            </div>
          </div>
        ) : null}
        {!showEmptyState && messages.map((msg, idx) => {
          const messageId = `msg-${idx}`;
          const isCurrentlyPlaying = currentlyPlayingMessageId === messageId;
          
          return (
          <div key={idx} className={`message ${msg.role}`} role="article" aria-label={msg.role === 'user' ? 'Your message' : 'Assistant message'}>
            <div className="message-content">
              {/* Kendo-style toolbar for assistant messages: Copy, Retry, Download + Play */}
              {msg.role === 'assistant' && (
                <div className="kendo-message-toolbar">
                  <button type="button" className="kendo-toolbar-btn" title="Copy" onClick={() => handleToolbarAction('copy', msg, idx)}>
                    <CopyIcon size={14} /> Copy
                  </button>
                  <button type="button" className="kendo-toolbar-btn" title="Retry" onClick={() => handleToolbarAction('retry', msg, idx)} disabled={loading || idx === 0}>
                    <RetryIcon size={14} /> Retry
                  </button>
                  <button type="button" className="kendo-toolbar-btn" title="Download" onClick={() => handleToolbarAction('download', msg, idx)}>
                    <DownloadIcon size={14} /> Download
                  </button>
                  <button
                    type="button"
                    className="kendo-toolbar-btn kendo-toolbar-play"
                    title={isCurrentlyPlaying ? 'Stop' : 'Play voice'}
                    disabled={loading}
                    onClick={() => isCurrentlyPlaying ? stopSpeaking() : playMessage(msg.content, messageId)}
                  >
                    {isCurrentlyPlaying ? <StopIcon size={14} /> : <PlayIcon size={14} />}
                    {isCurrentlyPlaying ? ' Stop' : ' Play'}
                  </button>
                </div>
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


      <form onSubmit={handleSend} className="ai-chat-input kendo-type-box">
        <input
          type="file"
          ref={fileInputRef}
          accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
          onChange={handleImageUpload}
          style={{ display: 'none' }}
          disabled={loading || uploadingImage}
        />
        <div className="kendo-type-box-inner">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="kendo-type-box-icon kendo-attach-btn"
            title="Attach image"
            disabled={loading || uploadingImage}
          >
            <AttachmentIcon size={20} />
          </button>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onFocus={() => {
              if (messagesEndRef.current) messagesEndRef.current.scrollIntoView = () => {};
            }}
            onBlur={() => {
              if (messagesEndRef.current) {
                messagesEndRef.current.scrollIntoView = function(options) {
                  Element.prototype.scrollIntoView.call(this, options);
                };
              }
            }}
            placeholder="Type a message..."
            disabled={loading || isListening}
            aria-label="Message to AI assistant"
            className="kendo-type-box-input"
          />
          <button
            type="button"
            onClick={toggleVoiceInput}
            className={`kendo-type-box-icon kendo-mic-btn ${isListening ? 'listening' : ''}`}
            title={isListening ? 'Stop listening' : 'Microphone'}
            disabled={loading}
          >
            <MicrophoneIcon size={20} />
          </button>
          <button
            type="button"
            onClick={toggleVoice}
            className={`kendo-type-box-icon kendo-speaker-btn ${voiceEnabled ? 'on' : ''} ${!pollyAvailable ? 'unavailable' : ''}`}
            title={voiceEnabled ? 'Voice on' : 'Voice off'}
            disabled={loading || !pollyAvailable}
          >
            {voiceEnabled ? <SpeakerIcon size={20} /> : <SpeakerOffIcon size={20} />}
          </button>
          {isSpeaking && (
            <button type="button" onClick={stopSpeaking} className="kendo-type-box-icon kendo-stop-btn" title="Stop speaking">
              <StopIcon size={20} />
            </button>
          )}
          <button
            type="submit"
            className="kendo-send-btn"
            disabled={loading || !input.trim() || isListening}
            title="Send"
          >
            Send
          </button>
        </div>
      </form>
      
      {/* Kendo-style clear conversation dialog */}
      {showClearConfirm && (
        <div className="ai-chat-modal-overlay kendo-dialog-overlay" role="dialog" aria-modal="true" aria-labelledby="ai-chat-clear-title" onClick={(e) => e.target === e.currentTarget && setShowClearConfirm(false)}>
          <div className="ai-chat-modal kendo-dialog">
            <h3 id="ai-chat-clear-title" className="kendo-dialog-title">Delete conversation</h3>
            <p className="kendo-dialog-body">Are you sure you want to delete the <b>&#39;AI Shopping Assistant&#39;</b> conversation?</p>
            <div className="kendo-dialog-actions">
              <button type="button" onClick={handleClearHistory} className="kendo-dialog-primary">
                Delete
              </button>
              <button type="button" onClick={() => setShowClearConfirm(false)} className="kendo-dialog-cancel">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIChat;

