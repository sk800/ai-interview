import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Azure Speech Services
try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_SPEECH_AVAILABLE = True
except ImportError:
    AZURE_SPEECH_AVAILABLE = False
    print("Warning: Azure Speech Services not available. Please install azure-cognitiveservices-speech")

class AudioService:
    def __init__(self):
        self.speech_config = None
        self.key = os.getenv("AZURE_SPEECH_KEY")
        self.region = os.getenv("AZURE_SPEECH_REGION", "eastus")
        self._initialize_speech_config()
        self.threshold = 0.5  # Voice verification threshold
        
    def _initialize_speech_config(self):
        """Initialize Azure Speech Services configuration"""
        if not AZURE_SPEECH_AVAILABLE:
            return
        
        if not self.key:
            print("Warning: AZURE_SPEECH_KEY not found in .env file")
            return
        
        try:
            self.speech_config = speechsdk.SpeechConfig(subscription=self.key, region=self.region)
            print("Azure Speech Services configured successfully")
        except Exception as e:
            print(f"Error initializing Azure Speech Services: {str(e)}")
            self.speech_config = None
    
    def _is_available(self) -> bool:
        """Check if Azure Speech Services is available"""
        return AZURE_SPEECH_AVAILABLE and self.speech_config is not None
    
    async def process_sample(self, audio_path: str) -> Optional[str]:
        """Process audio sample - returns the audio file path for later verification"""
        try:
            # Store the audio file path for verification
            # The audio file will be used to compare with live audio during interview
            print(f"Audio sample processed and stored at: {audio_path}")
            return audio_path  # Return path for verification
            
        except Exception as e:
            print(f"Error processing audio sample: {str(e)}")
            return None
    
    async def verify_audio(self, audio_path: str, stored_audio_path: str) -> bool:
        """Verify if audio matches stored audio sample - only matches human voice, ignores keyboard sounds"""
        try:
            if not stored_audio_path or not os.path.exists(stored_audio_path):
                print("No stored audio path or file not found, allowing verification")
                return True  # Allow if no stored audio
            
            if not os.path.exists(audio_path):
                print("Current audio file not found, allowing verification")
                return True  # Allow if current audio not found
            
            # First, check if there's actual human speech in the audio (not just keyboard sounds)
            has_speech = await self._has_human_speech(audio_path)
            if not has_speech:
                print("No human speech detected in audio (likely keyboard sounds) - allowing verification")
                return True  # Allow if no speech detected (user might be typing)
            
            # Use librosa for audio feature comparison (voice characteristics)
            try:
                import librosa
                import numpy as np
                
                # Load audio files
                y1, sr1 = librosa.load(audio_path, sr=16000, duration=2.0)  # Limit to 2 seconds
                y2, sr2 = librosa.load(stored_audio_path, sr=16000, duration=2.0)
                
                # Check if audio has sufficient energy (human voice has more energy than keyboard)
                energy1 = np.sum(y1 ** 2) / len(y1)
                energy2 = np.sum(y2 ** 2) / len(y2)
                
                # If current audio has very low energy, it's likely just background noise/keyboard
                if energy1 < 0.001:  # Very low energy threshold
                    print("Audio has very low energy (likely keyboard sounds) - allowing verification")
                    return True
                
                # Extract MFCC features (voice characteristics)
                mfcc1 = librosa.feature.mfcc(y=y1, sr=sr1, n_mfcc=13)
                mfcc2 = librosa.feature.mfcc(y=y2, sr=sr2, n_mfcc=13)
                
                # Calculate average MFCC
                avg_mfcc1 = np.mean(mfcc1, axis=1)
                avg_mfcc2 = np.mean(mfcc2, axis=1)
                
                # Calculate cosine similarity
                similarity = np.dot(avg_mfcc1, avg_mfcc2) / (
                    np.linalg.norm(avg_mfcc1) * np.linalg.norm(avg_mfcc2)
                )
                
                print(f"Audio verification similarity: {similarity:.3f} (threshold: {self.threshold})")
                
                # Return True if similarity is above threshold
                return similarity >= self.threshold
                
            except Exception as e:
                print(f"Error in audio feature comparison: {str(e)}")
                # Allow on error to avoid false positives
                return True
            
        except Exception as e:
            print(f"Error verifying audio: {str(e)}")
            # Allow on error to avoid false positives
            return True
    
    async def _has_human_speech(self, audio_path: str) -> bool:
        """Check if audio contains human speech (not just keyboard sounds)"""
        if not self._is_available():
            # If Azure Speech not available, use librosa-based detection
            try:
                import librosa
                import numpy as np
                
                y, sr = librosa.load(audio_path, sr=16000, duration=2.0)
                
                # Human speech typically has energy in specific frequency ranges
                # Keyboard sounds are more broadband and have different characteristics
                
                # Calculate spectral centroid (brightness) - speech has higher centroid
                spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
                avg_centroid = np.mean(spectral_centroids)
                
                # Speech typically has centroid between 1000-4000 Hz
                # Keyboard sounds usually have different characteristics
                if avg_centroid < 500 or avg_centroid > 5000:
                    return False  # Likely not human speech
                
                # Check zero crossing rate - speech has moderate ZCR
                zcr = librosa.feature.zero_crossing_rate(y)[0]
                avg_zcr = np.mean(zcr)
                
                # Speech typically has ZCR between 0.01 and 0.2
                if avg_zcr < 0.005 or avg_zcr > 0.3:
                    return False  # Likely not human speech
                
                return True
                
            except Exception as e:
                print(f"Error detecting speech: {str(e)}")
                return True  # Allow if detection fails
        
        # Use Azure Speech Services to detect if there's actual speech
        try:
            transcribed = await self.transcribe_audio(audio_path)
            # If we can transcribe something meaningful, it's likely human speech
            return len(transcribed.strip()) > 0
        except Exception as e:
            print(f"Error checking for speech with Azure: {str(e)}")
            return True  # Allow if check fails
    
    async def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio to text using Azure Speech Services"""
        if not self._is_available():
            return ""
        
        try:
            # Create audio config from file
            audio_config = speechsdk.audio.AudioConfig(filename=audio_path)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Recognize speech
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                print("No speech could be recognized")
                return ""
            else:
                print(f"Speech recognition error: {result.reason}")
                return ""
                
        except Exception as e:
            print(f"Error transcribing audio with Azure Speech Services: {str(e)}")
            return ""
