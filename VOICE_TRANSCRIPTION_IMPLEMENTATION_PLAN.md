# Voice Transcription Implementation Plan

## Overview
This document outlines the implementation plan for adding voice transcription capabilities to the existing voice query agent. The goal is to capture and display both input (user speech) and output (AI-generated speech) transcriptions in real-time.

## Current System Analysis

### Architecture
- **Backend**: Python WebSocket proxy server that forwards messages between frontend and Gemini Live API
- **Frontend**: HTML/JavaScript interface handling audio input/output via WebSockets
- **API**: Google Gemini Live API (Multimodal Live API) with bidirectional streaming

### Current Implementation Status
- ✅ Voice-to-voice conversation working
- ✅ Audio input capture and transmission
- ✅ Audio output playback
- ✅ WebSocket proxy communication
- ❌ No transcription display or handling
- ❌ Transcription configuration not enabled

## Gemini Live API Transcription Capabilities

Based on research, the Gemini Live API supports:

### Input Audio Transcription
- **Configuration**: `inputAudioTranscription: {}` in setup config
- **Response Field**: `response.serverContent.inputTranscription.text`
- **Behavior**: Real-time transcription of user speech sent back from server

### Output Audio Transcription  
- **Configuration**: `outputAudioTranscription: {}` in setup config
- **Response Field**: `response.serverContent.outputTranscription.text`
- **Behavior**: Real-time transcription of AI-generated speech

### Key Characteristics
- Transcriptions arrive in chunks, not complete sentences
- Transcriptions are sent independently of other messages
- No guaranteed ordering between transcriptions and audio data
- May include `<noise>` flags for non-speech audio

## Implementation Plan

### Phase 1: Backend Configuration (Priority: High)

#### 1.1 Update WebSocket Setup Message
**File**: `backend/main.py`
**Changes**:
- Modify the initial setup message sent to Gemini Live API
- Add transcription configuration parameters

```python
# Add to setup message
setup_message = {
    "setup": {
        "model": f"models/{MODEL}",
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            # existing config...
        },
        "inputAudioTranscription": {},  # Enable input transcription
        "outputAudioTranscription": {}  # Enable output transcription
    }
}
```

#### 1.2 Enhanced Message Processing
**File**: `backend/main.py`
**Changes**:
- Update `proxy_task` function to detect and log transcription messages
- Add transcription message forwarding to frontend

```python
async def proxy_task(client_websocket, server_websocket):
    async for message in client_websocket:
        try:
            data = json.loads(message)
            
            # Check for transcription data in server responses
            if "serverContent" in data:
                server_content = data["serverContent"]
                
                # Log input transcription
                if "inputTranscription" in server_content:
                    transcription = server_content["inputTranscription"]
                    if transcription.get("text"):
                        print(f"🎤 INPUT: {transcription['text']}")
                
                # Log output transcription  
                if "outputTranscription" in server_content:
                    transcription = server_content["outputTranscription"]
                    if transcription.get("text"):
                        print(f"🔊 OUTPUT: {transcription['text']}")
            
            await server_websocket.send(json.dumps(data))
        except Exception as e:
            print(f"Error processing message: {e}")
```

### Phase 2: Frontend Transcription Display (Priority: High)

#### 2.1 HTML UI Updates
**File**: `frontend/index.html`
**Changes**:
- Add transcription display containers
- Create separate areas for input and output transcriptions

```html
<!-- Add to existing UI -->
<div id="transcriptionContainer" class="transcription-container">
    <div class="transcription-section">
        <h3>Your Speech</h3>
        <div id="inputTranscription" class="transcription-text"></div>
    </div>
    <div class="transcription-section">
        <h3>AI Response</h3>
        <div id="outputTranscription" class="transcription-text"></div>
    </div>
</div>
```

#### 2.2 CSS Styling
**File**: `frontend/style.css` (create if needed)
**Changes**:
- Add styling for transcription containers
- Ensure readability and proper layout

```css
.transcription-container {
    display: flex;
    gap: 20px;
    margin-top: 20px;
    max-height: 300px;
    overflow-y: auto;
}

.transcription-section {
    flex: 1;
    border: 1px solid #ccc;
    padding: 15px;
    border-radius: 8px;
}

.transcription-text {
    min-height: 200px;
    font-family: monospace;
    font-size: 14px;
    line-height: 1.4;
    white-space: pre-wrap;
}
```

#### 2.3 JavaScript Message Handling
**File**: `frontend/script.js`
**Changes**:
- Update WebSocket message handler to process transcription data
- Implement transcription display logic

```javascript
// Add transcription handling to existing WebSocket message handler
function handleWebSocketMessage(event) {
    const data = JSON.parse(event.data);
    
    // Handle transcription messages
    if (data.serverContent) {
        // Input transcription (user speech)
        if (data.serverContent.inputTranscription) {
            const text = data.serverContent.inputTranscription.text;
            if (text) {
                appendTranscription('inputTranscription', text, 'user');
            }
        }
        
        // Output transcription (AI speech)
        if (data.serverContent.outputTranscription) {
            const text = data.serverContent.outputTranscription.text;
            if (text) {
                appendTranscription('outputTranscription', text, 'ai');
            }
        }
    }
    
    // Continue with existing message handling...
}

function appendTranscription(containerId, text, speaker) {
    const container = document.getElementById(containerId);
    const timestamp = new Date().toLocaleTimeString();
    
    // Create transcription entry
    const entry = document.createElement('div');
    entry.className = `transcription-entry ${speaker}`;
    entry.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${text}`;
    
    container.appendChild(entry);
    container.scrollTop = container.scrollHeight;
}
```

### Phase 3: Enhanced Features (Priority: Medium)

#### 3.1 Transcription Management
**Features**:
- Clear transcription history
- Export transcriptions to text file
- Toggle transcription display on/off
- Search within transcriptions

#### 3.2 Real-time Transcription Improvements
**Features**:
- Chunk aggregation for better readability
- Sentence completion detection
- Noise filtering (`<noise>` tag handling)
- Confidence indicators (if available)

#### 3.3 Accessibility Enhancements
**Features**:
- Screen reader compatibility
- High contrast mode for transcriptions
- Font size adjustment
- Keyboard navigation

### Phase 4: Advanced Features (Priority: Low)

#### 4.1 Transcription Analytics
**Features**:
- Word count statistics
- Speaking time analysis
- Conversation flow visualization
- Export to various formats (JSON, CSV, PDF)

#### 4.2 Integration Features
**Features**:
- Save transcriptions to local storage
- Integration with note-taking apps
- Real-time collaboration features
- Multi-language support

## Implementation Steps

### Step 1: Backend Setup Configuration
1. Update `backend/main.py` to include transcription config in setup message
2. Test connection with transcription enabled
3. Verify transcription messages are received in logs

### Step 2: Basic Frontend Display
1. Add HTML containers for transcription display
2. Update CSS for proper styling
3. Implement basic JavaScript transcription handling
4. Test end-to-end transcription flow

### Step 3: Enhanced Message Processing
1. Improve transcription chunk handling
2. Add timestamp and speaker identification
3. Implement scrolling and display management
4. Add basic controls (clear, toggle)

### Step 4: Testing and Refinement
1. Test with various speech patterns and lengths
2. Verify transcription accuracy and timing
3. Optimize UI/UX based on testing
4. Add error handling and edge cases

### Step 5: Advanced Features
1. Implement export functionality
2. Add search and filter capabilities
3. Enhance accessibility features
4. Performance optimization

## Technical Considerations

### Message Flow
```
User Speech → Frontend → Backend → Gemini API
                ↓
Gemini API → Backend → Frontend → Display Input Transcription

Gemini API Response → Backend → Frontend → Display Output Transcription
                ↓
Audio Output → User
```

### Error Handling
- Network disconnection during transcription
- Malformed transcription messages
- Audio input/output failures
- API rate limiting or errors

### Performance Considerations
- Efficient DOM updates for real-time transcription
- Memory management for long conversations
- Throttling for rapid transcription updates
- Cleanup of old transcription data

### Security Considerations
- Transcription data privacy
- Local storage security
- Export data sanitization
- User consent for transcription recording

## Testing Strategy

### Unit Tests
- Transcription message parsing
- UI component functionality
- Export/import features
- Error handling scenarios

### Integration Tests
- End-to-end transcription flow
- WebSocket message handling
- Audio-transcription synchronization
- Multi-browser compatibility

### User Acceptance Tests
- Real conversation scenarios
- Accessibility compliance
- Performance under load
- User experience validation

## Success Metrics

### Functional Metrics
- ✅ Input transcription displays in real-time
- ✅ Output transcription displays in real-time
- ✅ Transcriptions are accurate and readable
- ✅ UI is responsive and user-friendly

### Performance Metrics
- Transcription latency < 500ms
- UI updates without lag
- Memory usage remains stable
- No audio quality degradation

### User Experience Metrics
- Intuitive transcription interface
- Easy to read and follow conversations
- Accessible to users with disabilities
- Minimal learning curve

## Conclusion

This implementation plan provides a structured approach to adding voice transcription capabilities to the existing voice query agent. The phased approach ensures that core functionality is implemented first, followed by enhancements and advanced features. The plan leverages the existing Gemini Live API transcription capabilities while maintaining the current voice-to-voice functionality.

The implementation should result in a more accessible, transparent, and useful voice interaction system that provides both audio and text-based communication channels.
