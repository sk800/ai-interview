import os
import json
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# Azure Face API
try:
    from azure.cognitiveservices.vision.face import FaceClient
    from msrest.authentication import CognitiveServicesCredentials
    import requests
    AZURE_FACE_AVAILABLE = True
except ImportError:
    AZURE_FACE_AVAILABLE = False
    print("Warning: Azure Face API not available. Please install azure-cognitiveservices-vision-face")

class FaceRecognitionService:
    def __init__(self):
        self.face_client = None
        self.endpoint = os.getenv("AZURE_FACE_ENDPOINT")
        self.key = os.getenv("AZURE_FACE_KEY")
        self._initialize_client()
        # Confidence threshold for considering two faces as the same person.
        # Slightly lenient to reduce false alerts, but strict enough to catch cheating.
        self.threshold = 0.5
        
    def _initialize_client(self):
        """Initialize Azure Face API client"""
        if not AZURE_FACE_AVAILABLE:
            print("Warning: Azure Face API libraries not available")
            return
        
        if not self.endpoint or not self.key:
            print("Warning: Azure Face API credentials not found in .env file")
            return
        
        try:
            self.face_client = FaceClient(
                endpoint=self.endpoint,
                credentials=CognitiveServicesCredentials(self.key)
            )
            print("Azure Face API client initialized successfully")
        except Exception as e:
            print(f"Error initializing Azure Face API client: {str(e)}")
            self.face_client = None
    
    def _is_available(self) -> bool:
        """Check if Azure Face API is available"""
        return AZURE_FACE_AVAILABLE and self.face_client is not None
    
    async def process_sample(self, photo_path: str) -> Optional[str]:
        """Extract face ID from photo sample using Azure Face API"""
        if not self._is_available():
            print("Warning: Azure Face API not available, returning None")
            return None
        
        try:
            # Read image file
            with open(photo_path, 'rb') as image_file:
                image_data = image_file.read()
            
            # Detect faces in the image
            detected_faces = self.face_client.face.detect_with_stream(
                image=image_data,
                detection_model='detection_01',  # or 'detection_02' or 'detection_03'
                return_face_id=True,
                return_face_attributes=None
            )
            
            if not detected_faces:
                print("No face detected in photo")
                return None
            
            # Use the first detected face
            face_id = detected_faces[0].face_id
            print(f"Face detected with ID: {face_id}")
            
            # Store face_id as string (Azure Face API uses GUIDs)
            return face_id
            
        except Exception as e:
            print(f"Error processing face sample with Azure Face API: {str(e)}")
            return None
    
    async def verify_face(self, snapshot_path: str, stored_face_id: str) -> Tuple[bool, str]:
        """
        Verify if face in snapshot matches stored face ID using Azure Face API
        Returns: (is_match: bool, reason: str)
        Reasons: 'match', 'no_face', 'different_face', 'expired_face_id', 'error'
        """
        if not self._is_available():
            print("Warning: Azure Face API not available, returning True (bypass)")
            return True, "bypass"  # Bypass verification if not available

        try:
            if not stored_face_id:
                # If for some reason we don't have a stored face ID, allow (graceful degradation)
                print("No stored face ID found for user - allowing verification")
                return True, "no_stored_face"

            # Read snapshot image
            with open(snapshot_path, 'rb') as image_file:
                image_data = image_file.read()

            # Detect faces in the snapshot
            detected_faces = self.face_client.face.detect_with_stream(
                image=image_data,
                detection_model='detection_01',
                return_face_id=True,
                return_face_attributes=None
            )

            if not detected_faces:
                # No face detected - this is a violation
                print("No face detected in snapshot")
                return False, "no_face"

            # Get face ID from snapshot
            snapshot_face_id = detected_faces[0].face_id

            # Verify faces using Azure Face API
            try:
                verify_result = self.face_client.face.verify_face_to_face(
                    face_id1=stored_face_id,
                    face_id2=snapshot_face_id
                )

                # Check if faces match
                is_identical = verify_result.is_identical
                confidence = verify_result.confidence

                print(f"Face verification: is_identical={is_identical}, confidence={confidence}")

                # More lenient matching - if Azure says identical OR confidence is reasonably high
                # Lower threshold to 0.4 to reduce false positives for same person
                if is_identical:
                    print("Face verified as identical by Azure")
                    return True, "match"
                
                # If confidence is reasonably high (>= 0.4), consider it a match
                # This handles cases where lighting/angle changes slightly
                if confidence >= 0.4:
                    print(f"Face match with confidence {confidence} (above lenient threshold 0.4)")
                    return True, "match"

                # If confidence is very low (< 0.3), it's likely a completely different person
                if confidence < 0.3:
                    print(f"Face verification failed: very low confidence {confidence} - likely different person")
                    return False, "different_face"
                
                # Medium confidence (0.3-0.4) - might be same person with different angle/lighting
                # Be lenient and allow it
                print(f"Face verification: medium confidence {confidence} - allowing (lenient)")
                return True, "match"

            except Exception as verify_error:
                # Handle case where face ID might have expired (Azure Face IDs expire after 24 hours)
                if "FaceId" in str(verify_error) or "expired" in str(verify_error).lower() or "ResourceNotFound" in str(verify_error):
                    print(f"Face ID may have expired: {str(verify_error)} - allowing verification")
                    # Allow if face ID expired (graceful degradation)
                    return True, "expired_face_id"
                print(f"Error in face verification: {str(verify_error)}")
                # On other errors, allow to avoid false positives
                return True, "error"

        except Exception as e:
            print(f"Error verifying face with Azure Face API: {str(e)}")
            # On generic errors, allow to avoid false positives
            return True, "error"
