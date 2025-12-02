# Voice Request Logging and Play/Stop Icon Fix

## Summary
Added comprehensive logging throughout the AWS Polly voice request flow and fixed the play/stop icon visibility issue on the landing page.

## Changes Made

### 1. Backend Logging (`routes/ai_agent.py`)

Added detailed logging to the `/api/ai/text-to-speech` endpoint:

- **Request logging**: Logs text length, voice gender, and text preview
- **Polly availability check**: Logs client status, credentials, and region
- **Text processing**: Logs original and cleaned text lengths
- **Voice selection**: Logs selected voice ID and gender
- **SSML generation**: Logs excitement level and SSML parameters
- **AWS API call**: Logs request parameters and timing
- **Response handling**: Logs audio stream size and base64 encoding
- **Error handling**: Comprehensive error logging with tracebacks

**Log Format**: All logs are prefixed with `[AWS POLLY]` for easy filtering.

### 2. Frontend Logging (`frontend/src/components/AIChat.js`)

Added detailed logging throughout the audio playback flow:

#### `speakText` Function:
- Initial state logging (voice enabled, Polly available, etc.)
- API request/response logging with timing
- Base64 decoding progress
- Blob creation and URL generation
- Audio event listeners setup
- Playback state changes
- Error handling with detailed context

#### `playMessage` Function:
- Logs when play button is clicked
- Logs message ID and content length
- Logs voice state before playing

#### `stopSpeaking` Function:
- Logs when stop is called
- Logs audio state before stopping

#### Audio Event Listeners:
- `loadstart`, `loadeddata`, `loadedmetadata`
- `canplay`, `playing`, `pause`
- `waiting`, `stalled`, `ended`, `error`

**Log Format**: All logs are prefixed with `[FRONTEND]` for easy filtering.

### 3. Play/Stop Icon Visibility Fix

#### CSS Changes (`frontend/src/components/AIChat.css`):
- Increased `padding-right` from 80px to 100px for better button spacing
- Added `!important` flags to ensure visibility
- Added `min-height: 40px` to message content
- Improved button opacity and visibility styles

#### Component Changes (`frontend/src/components/AIChat.js`):
- Increased `z-index` from 10 to 100
- Added explicit `visibility: visible`
- Added `minWidth: '60px'` for better button size
- Added `boxShadow` for better visibility
- Improved background color contrast
- Added click logging for debugging

## How to Use the Logs

### Backend Logs (Server Console)

1. **Start your Flask server** and watch the console
2. **Filter logs** by searching for `[AWS POLLY]`
3. **Key log points**:
   - Request received: `[AWS POLLY] Text-to-Speech Request Received`
   - Polly availability: `[AWS POLLY] Checking Polly availability...`
   - API call: `[AWS POLLY] Calling AWS Polly synthesize_speech...`
   - Success: `[AWS POLLY] ✅ SUCCESS: Returning audio response`
   - Errors: `[AWS POLLY] ❌ ERROR:` or `[AWS POLLY] ❌ EXCEPTION`

### Frontend Logs (Browser Console)

1. **Open browser DevTools** (F12)
2. **Go to Console tab**
3. **Filter logs** by searching for `[FRONTEND]`
4. **Key log points**:
   - Play button click: `[FRONTEND] 🎵 Play button clicked`
   - speakText called: `[FRONTEND] speakText called`
   - API request: `[FRONTEND] 📤 Sending POST request`
   - API response: `[FRONTEND] ✅ TTS API response received`
   - Audio events: `[FRONTEND] 🎵 Audio [event] event`
   - Playback: `[FRONTEND] ▶️ Attempting to play audio`
   - Errors: `[FRONTEND] ❌ ERROR:` or `[FRONTEND] ❌ EXCEPTION`

## Debugging Workflow

### Issue: Voice not playing

1. **Check backend logs**:
   - Is Polly available? Look for `polly_available: True`
   - Are credentials configured? Check `AWS_ACCESS_KEY_ID configured`
   - Did API call succeed? Look for `✅ Polly API call successful`

2. **Check frontend logs**:
   - Was speakText called? Look for `[FRONTEND] speakText called`
   - Did API request succeed? Look for `✅ TTS API response received`
   - Is audio loading? Look for `🎵 Audio canplay event`
   - Is audio playing? Look for `🎵 Audio playing event`

### Issue: Play/Stop icon not showing

1. **Check browser console**:
   - Are assistant messages rendering? Look for `🎨 Rendering assistant message`
   - Is button being created? Check DOM inspector

2. **Check CSS**:
   - Button should have `z-index: 100`
   - Message content should have `padding-right: 100px`
   - Button should have `visibility: visible !important`

3. **Visual inspection**:
   - Open DevTools → Elements
   - Find `.message-play-btn` in assistant messages
   - Check computed styles for visibility/display

## Testing Checklist

- [ ] Backend logs show Polly initialization
- [ ] Backend logs show request details when TTS is called
- [ ] Backend logs show successful API response
- [ ] Frontend logs show speakText being called
- [ ] Frontend logs show API request/response
- [ ] Frontend logs show audio events (canplay, playing, ended)
- [ ] Play/Stop icon is visible on assistant messages
- [ ] Play button works when clicked
- [ ] Stop button appears when audio is playing
- [ ] Icon is visible on landing page (Home.js)

## Performance Notes

- Logs include timing information (request time, decode time, etc.)
- All logs use console.log/print (not console.error unless actual errors)
- Logs are formatted for easy reading with separators (`===`)
- Emoji indicators (✅, ❌, 🎵, etc.) for quick visual scanning

## Next Steps

If issues persist after reviewing logs:

1. **Share backend logs** (filtered for `[AWS POLLY]`)
2. **Share frontend logs** (filtered for `[FRONTEND]`)
3. **Check network tab** for API request/response details
4. **Check audio element** in DOM inspector for state

