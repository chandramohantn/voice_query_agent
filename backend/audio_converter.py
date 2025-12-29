import base64
import struct
import logging
import numpy as np

logger = logging.getLogger(__name__)

class AudioConverter:
    """Handles audio format conversion between Twilio and Gemini formats"""
    
    @staticmethod
    def mulaw_to_pcm16(mulaw_data: bytes) -> bytes:
        """Convert μ-law audio to 16-bit PCM using a simple lookup approach"""
        try:
            if not mulaw_data:
                return b''
            
            # Convert μ-law bytes to numpy array
            mulaw_array = np.frombuffer(mulaw_data, dtype=np.uint8)
            
            # Simplified μ-law to linear conversion
            # Remove bias and get magnitude
            biased = mulaw_array ^ 0x55  # Remove bias
            sign = (biased & 0x80) != 0
            exponent = (biased & 0x70) >> 4
            mantissa = biased & 0x0F
            
            # Convert to linear scale
            linear = (mantissa * 2 + 33) << np.maximum(0, exponent - 1)
            linear = np.where(sign, -linear, linear)
            
            # Scale to 16-bit PCM range and convert to int16
            pcm16 = np.clip(linear * 4, -32768, 32767).astype(np.int16)
            
            return pcm16.tobytes()
            
        except Exception as e:
            logger.error(f"Error converting μ-law to PCM: {e}")
            # Return silence as fallback
            return b'\x00' * (len(mulaw_data) * 2)
    
    @staticmethod
    def pcm16_to_mulaw(pcm_data: bytes) -> bytes:
        """Convert 16-bit PCM to μ-law audio"""
        try:
            if not pcm_data:
                return b''
            
            # Convert PCM bytes to numpy array
            pcm_array = np.frombuffer(pcm_data, dtype=np.int16)
            
            # Simple linear to μ-law conversion
            sign = pcm_array < 0
            abs_pcm = np.abs(pcm_array.astype(np.int32))
            
            # Compress to μ-law range (simplified)
            compressed = np.clip(abs_pcm // 256, 0, 127)
            
            # Add sign bit and bias
            mulaw = compressed.astype(np.uint8)
            mulaw = np.where(sign, mulaw | 0x80, mulaw)
            mulaw = mulaw ^ 0x55  # Add bias
            
            return mulaw.tobytes()
            
        except Exception as e:
            logger.error(f"Error converting PCM to μ-law: {e}")
            # Return silence as fallback
            return b'\x55' * (len(pcm_data) // 2)
    
    @staticmethod
    def resample_audio(audio_data: bytes, from_rate: int, to_rate: int, sample_width: int = 2) -> bytes:
        """Resample audio from one rate to another using numpy"""
        try:
            if not audio_data or from_rate == to_rate:
                return audio_data
            
            # Convert to numpy array
            if sample_width == 2:
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
            else:
                audio_array = np.frombuffer(audio_data, dtype=np.uint8)
            
            if len(audio_array) == 0:
                return audio_data
            
            # Calculate resampling ratio
            ratio = to_rate / from_rate
            
            # Simple linear interpolation resampling
            original_length = len(audio_array)
            new_length = max(1, int(original_length * ratio))
            
            # Create new indices
            new_indices = np.linspace(0, original_length - 1, new_length)
            
            # Interpolate
            resampled = np.interp(new_indices, np.arange(original_length), audio_array.astype(np.float32))
            
            # Convert back to original dtype
            if sample_width == 2:
                resampled = np.clip(resampled, -32768, 32767).astype(np.int16)
            else:
                resampled = np.clip(resampled, 0, 255).astype(np.uint8)
            
            return resampled.tobytes()
            
        except Exception as e:
            logger.error(f"Error resampling audio from {from_rate}Hz to {to_rate}Hz: {e}")
            return audio_data
    
    @staticmethod
    def twilio_to_gemini_format(base64_mulaw: str) -> str:
        """
        Convert Twilio μ-law audio to Gemini PCM format
        
        Twilio: μ-law, 8kHz, base64 encoded
        Gemini: PCM, 16kHz, base64 encoded
        """
        try:
            if not base64_mulaw:
                return ""
            
            # Decode base64 μ-law data
            mulaw_data = base64.b64decode(base64_mulaw)
            
            # Convert μ-law to PCM (16-bit)
            pcm_8khz = AudioConverter.mulaw_to_pcm16(mulaw_data)
            
            # Resample from 8kHz to 16kHz
            pcm_16khz = AudioConverter.resample_audio(pcm_8khz, 8000, 16000)
            
            # Encode back to base64
            base64_pcm = base64.b64encode(pcm_16khz).decode('utf-8')
            
            return base64_pcm
            
        except Exception as e:
            logger.error(f"Error converting Twilio to Gemini format: {e}")
            return ""
    
    @staticmethod
    def gemini_to_twilio_format(base64_pcm: str) -> str:
        """
        Convert Gemini PCM audio to Twilio μ-law format
        
        Gemini: PCM, 24kHz, base64 encoded  
        Twilio: μ-law, 8kHz, base64 encoded
        """
        try:
            if not base64_pcm:
                return ""
            
            # Decode base64 PCM data
            pcm_data = base64.b64decode(base64_pcm)
            
            # Resample from 24kHz to 8kHz
            pcm_8khz = AudioConverter.resample_audio(pcm_data, 24000, 8000)
            
            # Convert PCM to μ-law
            mulaw_data = AudioConverter.pcm16_to_mulaw(pcm_8khz)
            
            # Encode back to base64
            base64_mulaw = base64.b64encode(mulaw_data).decode('utf-8')
            
            return base64_mulaw
            
        except Exception as e:
            logger.error(f"Error converting Gemini to Twilio format: {e}")
            return ""

    @staticmethod
    def create_gemini_audio_message(base64_pcm: str) -> dict:
        """Create Gemini-compatible realtime_input message"""
        return {
            "realtime_input": {
                "media_chunks": [
                    {
                        "mime_type": "audio/pcm",
                        "data": base64_pcm
                    }
                ]
            }
        }
