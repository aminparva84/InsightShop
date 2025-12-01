# Voice Playback Troubleshooting Guide

## Issue Fixed
**Problem**: AI voice responses not playing after user sends a message
**Status**: ✅ Fixed with improved audio playback handling

## Changes Made

### 1. Backend Fix (`routes/ai_agent.py`)
- Fixed excitement_level calculation formatting
- No functional changes needed - backend was working correctly

### 2. Frontend Fix (`frontend/src/components/AIChat.js`)
- **Improved audio element initialization**
  - Properly clear and reset audio element before setting new source
  - Added `load()` call to ensure audio loads properly
  
- **Better event handling**
  - Use event listeners instead of inline handlers
  - Proper cleanup of event listeners
  - Added `canplay` event listener for reliable playback
  
- **Fallback mechanism**
  - Added timeout fallback if `canplay` event doesn't fire
  - Better error handling and logging
  
- **Browser autoplay policy handling**
  - Better error messages for autoplay blocking
  - User interaction is already present (they sent a message), so audio should play

## How to Test

### 1. Enable Voice
1. Open AI chat
2. Click the speaker icon (🔊) to enable voice
3. Icon should change to indicate voice is enabled

### 2. Send a Message
1. Type a message and send it
2. Wait for AI response
3. Audio should automatically play

### 3. Check Browser Console
Open browser DevTools (F12) and check Console tab for:
- "Calling TTS API with text length: X"
- "TTS API response received: Has data"
- "Audio blob created"
- "Audio can play, attempting to play..."
- "Audio play() called successfully"

### 4. Common Issues

#### Issue: "Polly client not initialized"
**Solution**: Configure AWS credentials in `.env` file:
```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

#### Issue: "NotAllowedError" or "Autoplay blocked"
**Solution**: 
- User interaction is required for first audio playback
- Since user already sent a message, this should work
- If still blocked, try clicking the voice button again
- Some browsers require explicit user interaction for audio

#### Issue: No audio data received
**Solution**: 
- Check backend logs for Polly errors
- Verify AWS credentials are correct
- Check network tab for API response

#### Issue: Audio element not initialized
**Solution**: 
- Refresh the page
- Check browser console for errors
- Ensure audioRef is properly initialized

## Debugging Steps

### 1. Check Voice is Enabled
```javascript
// In browser console
localStorage.getItem('aiVoiceEnabled') // Should be 'true'
```

### 2. Check API Response
Open Network tab in DevTools:
- Look for `/api/ai/text-to-speech` request
- Check if it returns 200 status
- Verify response has `audio` field with base64 data

### 3. Check Audio Element
```javascript
// In browser console (while on chat page)
// Find the audio element
document.querySelector('audio') // Should exist
```

### 4. Test Audio Playback Manually
```javascript
// In browser console
const audio = new Audio();
audio.src = 'data:audio/mpeg;base64,YOUR_BASE64_AUDIO';
audio.play().then(() => console.log('Playing')).catch(e => console.error(e));
```

## Browser Compatibility

### Supported Browsers
- ✅ Chrome/Edge (Chromium) - Full support
- ✅ Firefox - Full support
- ✅ Safari - May have stricter autoplay policies

### Browser Autoplay Policies
- Modern browsers block autoplay without user interaction
- Since user sends a message, this counts as interaction
- First audio might be blocked, subsequent ones should work

## Configuration

### AWS Polly Setup
1. Create AWS account
2. Enable Polly service
3. Create IAM user with Polly permissions
4. Add credentials to `.env`:
   ```env
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   ```

### Voice Selection
- **Woman**: Joanna (neural voice)
- **Man**: Matthew (neural voice)
- Select in chat interface using dropdown

## Expected Behavior

1. User enables voice (click speaker icon)
2. User sends message
3. AI responds with text
4. Audio automatically plays AI response
5. Speaker icon shows "speaking" state while playing
6. User can stop audio by clicking stop button

## Still Not Working?

1. **Check browser console** for errors
2. **Check network tab** for failed API calls
3. **Verify AWS credentials** are set correctly
4. **Try different browser** to rule out browser-specific issues
5. **Check backend logs** for Polly errors
6. **Verify voice is enabled** (speaker icon should be highlighted)

## Code Locations

- **Frontend**: `frontend/src/components/AIChat.js` (lines 107-250)
- **Backend**: `routes/ai_agent.py` (lines 859-939)
- **Config**: `config.py` (AWS configuration)

---

**Last Updated**: 2025-01-XX
**Status**: ✅ Fixed and Tested

