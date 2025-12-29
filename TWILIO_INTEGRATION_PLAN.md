# Twilio Phone Integration Plan for Voice Query Agent

## Overview

This plan outlines the integration of Twilio phone services with your existing voice query agent to enable phone-based interactions with the Gemini Live API.

## Current Architecture Analysis

**Existing Audio Flow:**
1. **Input**: Browser captures microphone at 16kHz PCM → converts to base64 → sends via WebSocket as `realtime_input` messages
2. **Backend**: Pure proxy - forwards all WebSocket messages between browser and Gemini Live API
3. **Gemini**: Expects `audio/pcm` format in `realtime_input.media_chunks` structure
4. **Output**: Gemini sends PCM audio as base64 → browser converts to Float32 at 24kHz → plays via AudioWorklet

**Key Technical Details:**
- **Input Audio**: 16kHz PCM, chunked every 1000ms, base64 encoded
- **Output Audio**: 24kHz PCM from Gemini, Float32 conversion for playback
- **Message Format**: `{realtime_input: {media_chunks: [{mime_type: "audio/pcm", data: base64PCM}]}}`
- **Backend Role**: Transparent WebSocket proxy with authentication

## UPDATED Implementation Plan - Key Changes

### Major Architectural Simplification

**Critical Insight**: After analyzing the current implementation, the integration is much simpler than initially planned. The existing WebSocket proxy architecture can be reused with minimal changes.

**Key Technical Discoveries:**
1. **Message Format**: Gemini expects `{realtime_input: {media_chunks: [{mime_type: "audio/pcm", data: base64}]}}` 
2. **Current Audio Flow**: Browser sends 16kHz PCM as base64 every 1000ms
3. **Backend Role**: Pure WebSocket proxy with authentication - no audio processing
4. **Conversion Point**: Only need μ-law → PCM conversion, then use existing message format

**Simplified Approach:**
1. **Reuse Existing Proxy**: Each Twilio call creates a "virtual browser client" 
2. **Audio Format Bridge**: Convert Twilio μ-law to the same PCM format browsers send
3. **Message Format Compatibility**: Use existing `realtime_input` message structure
4. **Minimal Backend Changes**: Add HTTP endpoints for Twilio, keep WebSocket proxy unchanged

### Revised Architecture

```
Phone Call → Twilio Media Stream → Audio Converter → Virtual WebSocket Client → Existing Proxy → Gemini
     ↑                                                                                              ↓
     └─────── Audio Response ←─── Audio Converter ←─── Virtual WebSocket Client ←─── Existing Proxy ←┘
```

## Implementation Plan

### Phase 1: Twilio Setup and Basic Integration

#### 1.1 Twilio Account Configuration
- **Objective**: Set up Twilio phone number and webhooks
- **Tasks**:
  - Purchase Twilio phone number
  - Configure webhook URLs for incoming calls
  - Set up TwiML applications
  - Configure voice settings (codec, sample rate)

#### 1.2 Environment Configuration
- **Files to modify**: `.env`
- **New variables**:
  ```
  TWILIO_ACCOUNT_SID=your_account_sid
  TWILIO_AUTH_TOKEN=your_auth_token
  TWILIO_PHONE_NUMBER=your_twilio_number
  WEBHOOK_BASE_URL=https://your-domain.com
  ```

#### 1.3 Dependencies Update
- **File**: `backend/requirements.txt`
- **Add**:
  ```
  twilio==8.10.0
  fastapi==0.104.1
  uvicorn==0.24.0
  pydantic==2.5.0
  ```

### Phase 2: Backend Architecture Expansion

#### 2.1 Create Twilio WebHook Handler
- **New file**: `backend/twilio_handler.py`
- **Responsibilities**:
  - Handle incoming call webhooks
  - Generate TwiML responses
  - Initiate WebSocket connections to Gemini
  - Manage call state transitions

#### 2.2 Audio Bridge Implementation
- **New file**: `backend/audio_bridge.py`
- **Key functions**:
  - Convert Twilio's μ-law audio to PCM format for Gemini
  - Convert Gemini's audio response back to μ-law for Twilio
  - Handle real-time audio streaming
  - Buffer management for smooth audio flow

#### 2.3 Call Session Manager
- **New file**: `backend/call_manager.py`
- **Features**:
  - Track active call sessions
  - Map Twilio call SIDs to WebSocket connections
  - Handle call cleanup and resource management
  - Store call metadata and transcripts

#### 2.4 Enhanced Main Server - SIMPLIFIED APPROACH
- **File**: `backend/main.py`
- **Key Insight**: Minimal changes needed to existing proxy architecture
- **Modifications**:
  - Add FastAPI HTTP server for Twilio webhooks (separate port)
  - Create `TwilioCallHandler` class that mimics browser WebSocket client
  - Reuse existing `create_proxy()` and `proxy_task()` functions
  - Each phone call creates a virtual WebSocket client session

### Phase 3: Audio Processing Pipeline

#### 3.1 Twilio Audio Integration Challenge
**Critical Discovery**: The current system uses a specific WebSocket message format that Gemini expects:
```json
{
  "realtime_input": {
    "media_chunks": [
      {
        "mime_type": "audio/pcm", 
        "data": "base64_encoded_pcm_data"
      }
    ]
  }
}
```

**Twilio Audio Specifications:**
- **Format**: μ-law (G.711) encoded
- **Sample Rate**: 8kHz
- **Delivery**: Real-time WebSocket stream
- **Encoding**: Base64 over WebSocket

#### 3.2 Audio Conversion Pipeline
**Twilio → Gemini Flow:**
1. Receive μ-law audio chunks from Twilio Media Stream
2. Decode μ-law to linear PCM
3. Upsample from 8kHz to 16kHz (to match current browser input)
4. Convert to base64
5. Wrap in `realtime_input` message structure
6. Send to existing Gemini WebSocket connection

**Gemini → Twilio Flow:**
1. Receive PCM audio response from Gemini (24kHz)
2. Downsample to 8kHz
3. Convert PCM to μ-law
4. Stream back to Twilio Media WebSocket

#### 3.3 Simplified Architecture Insight
**Key Realization**: We can reuse the existing WebSocket proxy architecture by:
- Creating a "virtual browser client" for each phone call
- Converting Twilio audio to the same format the browser sends
- Using the existing `proxy_task` functions in `main.py`
- No changes needed to Gemini Live API integration

### Phase 4: Call Flow Implementation

#### 4.1 Incoming Call Workflow
```
1. Twilio receives call → Webhook to /incoming-call
2. Generate TwiML with <Stream> verb
3. Establish WebSocket connection for audio
4. Create Gemini Live API session
5. Start audio bridging
6. Handle conversation loop
7. Clean up on call end
```

#### 4.2 TwiML Response Generation
- **Initial Response**: Start audio streaming
- **Fallback Handling**: Error recovery mechanisms
- **Call Termination**: Proper cleanup procedures

#### 4.3 Real-time Communication Loop
```
Phone Caller ←→ Twilio ←→ Your Backend ←→ Gemini Live API
     ↑                                           ↓
     └─────── Audio Response ←──────────────────┘
```

### Phase 5: Error Handling and Resilience

#### 5.1 Connection Management
- WebSocket reconnection logic
- Twilio connection monitoring
- Gemini API error handling
- Network failure recovery

#### 5.2 Audio Quality Assurance
- Audio dropout detection
- Silence detection and handling
- Echo cancellation considerations
- Latency optimization

#### 5.3 Call State Management
- Handle unexpected disconnections
- Implement call timeouts
- Resource cleanup on errors
- Logging and monitoring

### Phase 6: Configuration and Deployment

#### 6.1 Webhook Configuration
- **Twilio Console Settings**:
  - Voice webhook URL: `https://your-domain.com/incoming-call`
  - HTTP method: POST
  - Fallback URL for error handling

#### 6.2 Security Considerations
- Webhook signature validation
- HTTPS enforcement
- Rate limiting
- Input sanitization

#### 6.3 Monitoring and Logging
- Call analytics and metrics
- Audio quality monitoring
- Error tracking and alerting
- Performance optimization

## Technical Specifications

### Audio Requirements
- **Twilio Input**: μ-law (G.711), 8kHz, mono, base64 over WebSocket
- **Current Browser**: PCM, 16kHz, mono, base64 in `realtime_input` messages  
- **Gemini Requirement**: PCM format in `realtime_input.media_chunks` structure
- **Gemini Output**: PCM, 24kHz, mono, base64 in response messages
- **Conversion Strategy**: Twilio μ-law → PCM 16kHz → existing message format

### WebSocket Connections
- **Browser Client**: Existing WebSocket connection (port 8080)
- **Twilio Media**: New WebSocket connection for audio streaming
- **Gemini API**: Existing connection pattern, extended for phone calls

### HTTP Endpoints
```
POST /incoming-call     - Handle incoming call webhook
POST /call-status       - Handle call status updates
GET  /health           - Health check endpoint
POST /end-call         - Manual call termination
```

## File Structure After Implementation

```
voice_query_agent/
├── backend/
│   ├── main.py                 # Enhanced main server
│   ├── twilio_handler.py       # Twilio webhook handler
│   ├── audio_bridge.py         # Audio format conversion
│   ├── call_manager.py         # Call session management
│   ├── gemini_client.py        # Gemini API client (extracted)
│   └── requirements.txt        # Updated dependencies
├── frontend/                   # Existing frontend (unchanged)
├── config/
│   └── twilio_config.py        # Twilio configuration
└── logs/                       # Call logs and transcripts
```

## Testing Strategy

### Unit Testing
- Audio conversion accuracy
- WebSocket connection handling
- Call state management
- Error scenarios

### Integration Testing
- End-to-end call flow
- Audio quality validation
- Latency measurements
- Load testing with multiple calls

### Manual Testing
- Test calls from different phone types
- Network condition variations
- Edge case scenarios
- User experience validation

## Deployment Considerations

### Infrastructure Requirements
- Public HTTPS endpoint for Twilio webhooks
- WebSocket support for real-time audio
- Sufficient bandwidth for audio streaming
- Low-latency hosting (preferably same region as Twilio)

### Scaling Considerations
- Concurrent call handling
- Resource management per call
- Database for call logs (optional)
- Load balancing for high volume

## Success Metrics

- **Call Connection Rate**: >95% successful connections
- **Audio Quality**: Clear, understandable speech both ways
- **Latency**: <500ms end-to-end response time
- **Reliability**: <1% call drops due to technical issues

## Next Steps

1. **Phase 1**: Set up Twilio account and basic webhook
2. **Phase 2**: Implement audio bridge and test conversion
3. **Phase 3**: Create call management system
4. **Phase 4**: End-to-end integration testing
5. **Phase 5**: Production deployment and monitoring

This plan provides a comprehensive roadmap for integrating Twilio phone services with your existing voice query agent while maintaining the current browser-based functionality.
