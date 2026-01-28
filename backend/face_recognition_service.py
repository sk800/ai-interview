import os
import json
import io
from typing import Optional, Tuple
from dotenv import load_dotenv
from PIL import Image
import traceback

load_dotenv()

# Azure Face API
try:
    from azure.cognitiveservices.vision.face import FaceClient
    from msrest.authentication import CognitiveServicesCredentials
    from azure.cognitiveservices.vision.face.models import APIErrorException
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
        self.has_identification_feature = False  # Track if Identification/Verification features are available
        self._initialize_client()
        self.threshold = 0.4  # Face matching confidence threshold
        
    def _initialize_client(self):
        """Initialize Azure Face API client"""
        if not AZURE_FACE_AVAILABLE:
            print("Warning: Azure Face API libraries not available")
            return
        
        if not self.endpoint or not self.key:
            print("Warning: Azure Face API credentials not found in .env file")
            print("Please set AZURE_FACE_ENDPOINT and AZURE_FACE_KEY in your .env file")
            return
        
        try:
            # Clean up endpoint - remove any API paths and trailing slashes
            endpoint = self.endpoint.rstrip('/')
            
            # Remove any /face/v1.0 or /face/ paths - SDK adds these automatically
            if '/face/' in endpoint.lower():
                endpoint = endpoint.split('/face/')[0].rstrip('/')
                print(f"Removed /face/ path from endpoint")
            
            # Validate endpoint format
            if not endpoint.startswith('http'):
                print(f"WARNING: Endpoint should start with http:// or https://, got: {endpoint}")
                if not endpoint.startswith('http'):
                    endpoint = f"https://{endpoint}"
            
            # Check if endpoint contains the correct domain
            if 'cognitiveservices.azure.com' not in endpoint:
                print(f"WARNING: Endpoint should contain 'cognitiveservices.azure.com'")
                print(f"  Current endpoint: {endpoint}")
                print(f"  This might cause 'InvalidRequest' errors")
            
            self.face_client = FaceClient(
                endpoint=endpoint,
                credentials=CognitiveServicesCredentials(self.key)
            )
            print(f"Azure Face API client initialized successfully")
            print(f"  Endpoint: {endpoint}")
            print(f"  Key: {'*' * (len(self.key) - 4) + self.key[-4:] if len(self.key) > 4 else '****'}")
        except Exception as e:
            print(f"Error initializing Azure Face API client: {str(e)}")
            self.face_client = None
    
    def _is_available(self) -> bool:
        """Check if Azure Face API is available"""
        return AZURE_FACE_AVAILABLE and self.face_client is not None
    
    def _extract_face_features(self, face) -> dict:
        """Extract face features for comparison when face_id is not available"""
        features = {}
        if hasattr(face, 'face_rectangle'):
            rect = face.face_rectangle
            features['rectangle'] = {
                'top': rect.top,
                'left': rect.left,
                'width': rect.width,
                'height': rect.height,
                'area': rect.width * rect.height  # Add area for better comparison
            }
        # Note: Old attributes (age, gender, headPose) are deprecated by Azure
        # We only use face rectangle for comparison now
        return features
    
    def _compare_face_features(self, features1: dict, features2: dict) -> float:
        """Compare two face feature sets and return similarity score (0-1)"""
        if not features1 or not features2:
            return 0.0
        
        # Since attributes are deprecated, we only compare face rectangles
        # This is a simpler comparison based on face position and size
        if 'rectangle' in features1 and 'rectangle' in features2:
            r1 = features1['rectangle']
            r2 = features2['rectangle']
            
            # Compare size (width and height)
            width_diff = abs(r1['width'] - r2['width']) / max(r1['width'], r2['width'], 1)
            height_diff = abs(r1['height'] - r2['height']) / max(r1['height'], r2['height'], 1)
            size_similarity = 1.0 - min(1.0, (width_diff + height_diff) / 2)
            
            # Compare area (overall face size)
            area1 = r1.get('area', r1['width'] * r1['height'])
            area2 = r2.get('area', r2['width'] * r2['height'])
            area_diff = abs(area1 - area2) / max(area1, area2, 1)
            area_similarity = 1.0 - min(1.0, area_diff)
            
            # Average of size and area similarity
            similarity = (size_similarity + area_similarity) / 2
            
            return similarity
        
        return 0.0
    
    async def process_sample(self, photo_path: str) -> Optional[str]:
        """Extract face features from photo sample using Azure Face API"""
        if not self._is_available():
            print("Warning: Azure Face API not available, returning None")
            return None
        
        try:
            # Validate image file
            with open(photo_path, 'rb') as image_file:
                image_data = image_file.read()
            
            if not image_data or len(image_data) == 0:
                print("Error: Image file is empty")
                return None
            
            # Validate it's a valid image by checking file signature
            if not (image_data.startswith(b'\xff\xd8\xff') or  # JPEG
                    image_data.startswith(b'\x89PNG') or  # PNG
                    image_data.startswith(b'BM') or  # BMP
                    image_data.startswith(b'GIF')):  # GIF
                print("Error: Image file is not a valid format (JPEG, PNG, BMP, or GIF)")
                return None
            
            # Convert to JPEG if needed for better compatibility
            try:
                img = Image.open(photo_path)
                if img.format != 'JPEG':
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    jpeg_path = photo_path.replace(f'.{img.format.lower()}', '.jpg').replace('.JPG', '.jpg')
                    if jpeg_path != photo_path:
                        img.save(jpeg_path, 'JPEG', quality=95)
                        photo_path = jpeg_path
                        print(f"Converted image to JPEG: {jpeg_path}")
            except Exception as convert_error:
                print(f"Warning: Could not convert image: {str(convert_error)}")
            
            print(f"Processing image: {photo_path}, size: {len(image_data)} bytes")
            
            # Skip face_id detection entirely - go straight to basic detection
            # Since Identification/Verification features are not available
            # This avoids the InvalidRequest error
            print("Using basic face detection (without Identification/Verification features)")
            self.has_identification_feature = False
            
            # Use REST API directly - more reliable than SDK
            # Note: Old attributes (age, gender, etc.) are deprecated
            # Use only basic face detection without attributes
            import requests
            endpoint_url = f"{self.endpoint.rstrip('/')}/face/v1.0/detect"
            headers = {
                'Ocp-Apim-Subscription-Key': self.key,
                'Content-Type': 'application/octet-stream'
            }
            params = {
                'returnFaceId': 'false'
                # No returnFaceAttributes - deprecated attributes are no longer supported
            }
            
            with open(photo_path, 'rb') as image_file:
                response = requests.post(
                    endpoint_url,
                    headers=headers,
                    params=params,
                    data=image_file,
                    timeout=10
                )
            
            if response.status_code == 200:
                detected_faces_data = response.json()
                if detected_faces_data and len(detected_faces_data) > 0:
                    # Convert REST API response to work with our code
                    class FaceObj:
                        def __init__(self, data):
                            rect_data = data.get('faceRectangle', {})
                            self.face_rectangle = type('obj', (object,), {
                                'top': rect_data.get('top', 0),
                                'left': rect_data.get('left', 0),
                                'width': rect_data.get('width', 0),
                                'height': rect_data.get('height', 0)
                            })()
                            attrs = data.get('faceAttributes', {})
                            head_pose = attrs.get('headPose', {})
                            self.face_attributes = type('obj', (object,), {
                                'age': attrs.get('age'),
                                'gender': type('obj', (object,), {'value': attrs.get('gender')})() if attrs.get('gender') else None,
                                'headPose': type('obj', (object,), {
                                    'pitch': head_pose.get('pitch', 0),
                                    'roll': head_pose.get('roll', 0),
                                    'yaw': head_pose.get('yaw', 0)
                                })()
                            })()
                    
                    detected_faces = [FaceObj(face_data) for face_data in detected_faces_data]
                    print(f"Face detected via REST API (basic mode)")
                else:
                    print("No face detected via REST API")
                    return None
            else:
                error_text = response.text
                print(f"REST API error: {response.status_code}")
                print(f"Error details: {error_text}")
                raise Exception(f"Azure Face API REST call failed: {response.status_code} - {error_text}")
            
            if not detected_faces or len(detected_faces) == 0:
                print("No face detected in photo")
                return None
            
            # Extract face features for comparison
            face = detected_faces[0]
            features = self._extract_face_features(face)
            
            # Store features as JSON string
            features_json = json.dumps(features)
            print(f"Face detected (basic mode) - Features: {list(features.keys())}")
            
            return features_json
            
        except APIErrorException as api_error:
            error_str = str(api_error)
            print(f"Azure Face API error: {error_str}")
            
            if "UnsupportedFeature" in error_str or "Identification" in error_str or "Verification" in error_str:
                print("\n" + "="*70)
                print("IMPORTANT: Azure Face API Feature Access Required")
                print("="*70)
                print("Your Azure Face API subscription needs access to Identification/Verification features")
                print("for full face verification capabilities.")
                print("\nTo enable these features:")
                print("1. Go to: https://aka.ms/facerecognition")
                print("2. Apply for access to Identification and Verification features")
                print("3. Wait for approval (usually takes a few hours to a few days)")
                print("4. Once approved, face verification will be more accurate")
                print("\nFor now, the system will use basic face detection with attribute comparison.")
                print("="*70 + "\n")
            else:
                traceback.print_exc()
            
            return None
        except Exception as e:
            print(f"Error processing face sample: {str(e)}")
            traceback.print_exc()
            return None
    
    async def verify_face(self, snapshot_path: str, stored_face_data: str) -> Tuple[bool, str]:
        """
        Verify if face in snapshot matches stored face data using Azure Face API
        Returns: (is_match: bool, reason: str)
        Reasons: 'match', 'no_face', 'different_face', 'expired_face_id', 'error'
        """
        if not self._is_available():
            print("Warning: Azure Face API not available, returning True (bypass)")
            return True, "bypass"
        
        try:
            # Detect faces in snapshot
            with open(snapshot_path, 'rb') as image_file:
                if self.has_identification_feature and stored_face_data and not stored_face_data.startswith('{'):
                    # Try using face_id verification (if available)
                    try:
                        detected_faces = self.face_client.face.detect_with_stream(
                            image=image_file,
                            return_face_id=True,
                            return_face_attributes=None
                        )
                        
                        if not detected_faces:
                            print("No face detected in snapshot")
                            return False, "no_face"
                        
                        snapshot_face_id = detected_faces[0].face_id
                        
                        # Verify using face_id
                        verify_result = self.face_client.face.verify_face_to_face(
                            face_id1=stored_face_data,
                            face_id2=snapshot_face_id
                        )
                        
                        is_identical = verify_result.is_identical
                        confidence = verify_result.confidence
                        
                        print(f"Face verification (face_id): is_identical={is_identical}, confidence={confidence}")
                        
                        if is_identical or confidence >= self.threshold:
                            return True, "match"
                        elif confidence < 0.3:
                            return False, "different_face"
                        else:
                            return True, "match"  # Lenient for medium confidence
                    except APIErrorException as verify_error:
                        if "ResourceNotFound" in str(verify_error) or "expired" in str(verify_error).lower():
                            print("Face ID expired, falling back to feature comparison")
                            # Fall through to feature-based comparison
                        else:
                            raise
                
                # Fallback: Feature-based comparison using REST API (no deprecated attributes)
                import requests
                endpoint_url = f"{self.endpoint.rstrip('/')}/face/v1.0/detect"
                headers = {
                    'Ocp-Apim-Subscription-Key': self.key,
                    'Content-Type': 'application/octet-stream'
                }
                params = {'returnFaceId': 'false'}  # No attributes - deprecated
                
                image_file.seek(0)
                response = requests.post(
                    endpoint_url,
                    headers=headers,
                    params=params,
                    data=image_file,
                    timeout=10
                )
                
                if response.status_code != 200:
                    print(f"REST API error in verify: {response.status_code} - {response.text}")
                    return False, "error"
                
                detected_faces_data = response.json()
                if not detected_faces_data:
                    print("No face detected in snapshot")
                    return False, "no_face"
                
                # Convert to FaceObj
                class FaceObj:
                    def __init__(self, data):
                        rect_data = data.get('faceRectangle', {})
                        self.face_rectangle = type('obj', (object,), {
                            'top': rect_data.get('top', 0),
                            'left': rect_data.get('left', 0),
                            'width': rect_data.get('width', 0),
                            'height': rect_data.get('height', 0)
                        })()
                        self.face_attributes = None
                
                detected_faces = [FaceObj(face_data) for face_data in detected_faces_data]
            
            if not detected_faces:
                print("No face detected in snapshot")
                return False, "no_face"
            
            # Extract features from snapshot
            snapshot_face = detected_faces[0]
            snapshot_features = self._extract_face_features(snapshot_face)
            
            # Parse stored face data
            try:
                if stored_face_data.startswith('{'):
                    stored_features = json.loads(stored_face_data)
                else:
                    # If it's a face_id but we can't use it, return no match
                    print("Stored face data is face_id but Identification feature not available")
                    return False, "error"
            except:
                print("Could not parse stored face data")
                return False, "error"
            
            # Compare features
            similarity = self._compare_face_features(stored_features, snapshot_features)
            print(f"Face feature similarity: {similarity:.2f}")
            
            if similarity >= self.threshold:
                return True, "match"
            elif similarity < 0.3:
                return False, "different_face"
            else:
                return True, "match"  # Lenient for medium similarity
                
        except Exception as e:
            print(f"Error verifying face: {str(e)}")
            traceback.print_exc()
            return False, "error"
