"""
Facial Recognition Verification Engine
"""
import cv2
import face_recognition
import numpy as np
from datetime import datetime
import os

class FaceVerification:
    """Face verification system using face_recognition library"""
    
    def __init__(self, tolerance=0.6):
        """
        Initialize face verification
        
        Args:
            tolerance: Lower is more strict (default: 0.6)
        """
        self.tolerance = tolerance
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    def capture_face_from_webcam(self, save_path=None):
        """
        Capture face from webcam
        
        Args:
            save_path: Path to save captured image
            
        Returns:
            tuple: (image_array, face_encoding) or (None, None) if no face detected
        """
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Cannot access webcam")
            return None, None
        
        print("Press SPACE to capture, ESC to cancel")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to RGB for face_recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            face_locations = face_recognition.face_locations(rgb_frame)
            
            # Draw rectangles around faces
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # Display
            cv2.imshow('Face Capture - Press SPACE to capture', frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            # Space key to capture
            if key == 32 and len(face_locations) > 0:
                # Get face encoding
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                if len(face_encodings) > 0:
                    # Save image if path provided
                    if save_path:
                        cv2.imwrite(save_path, frame)
                    
                    cap.release()
                    cv2.destroyAllWindows()
                    return rgb_frame, face_encodings[0]
            
            # ESC key to cancel
            elif key == 27:
                break
        
        cap.release()
        cv2.destroyAllWindows()
        return None, None
    
    def capture_multiple_faces(self, count=5, save_dir=None):
        """
        Capture multiple face images for registration
        
        Args:
            count: Number of images to capture
            save_dir: Directory to save images
            
        Returns:
            list: List of face encodings
        """
        encodings = []
        
        for i in range(count):
            print(f"\nCapturing image {i+1}/{count}")
            print("Please adjust your face angle slightly...")
            
            save_path = None
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, f"capture_{i+1}.jpg")
            
            _, encoding = self.capture_face_from_webcam(save_path)
            
            if encoding is not None:
                encodings.append(encoding)
                print(f"✓ Image {i+1} captured successfully!")
            else:
                print(f"✗ Failed to capture image {i+1}")
                return None
        
        # Return average encoding
        if len(encodings) == count:
            avg_encoding = np.mean(encodings, axis=0)
            return avg_encoding
        
        return None
    
    def verify_face(self, captured_encoding, registered_encoding):
        """
        Verify if captured face matches registered face
        
        Args:
            captured_encoding: Face encoding from current capture
            registered_encoding: Stored face encoding
            
        Returns:
            tuple: (is_match, distance)
        """
        # Calculate face distance
        distance = face_recognition.face_distance([registered_encoding], captured_encoding)[0]
        
        # Check if match
        is_match = distance <= self.tolerance
        
        # Convert to confidence score (0-1, higher is better)
        confidence = 1 - distance
        
        return is_match, confidence
    
    def detect_and_encode_from_image(self, image_path):
        """
        Detect face and generate encoding from image file
        
        Args:
            image_path: Path to image file
            
        Returns:
            Face encoding or None
        """
        # Load image
        image = face_recognition.load_image_file(image_path)
        
        # Get face encodings
        face_encodings = face_recognition.face_encodings(image)
        
        if len(face_encodings) > 0:
            return face_encodings[0]
        
        return None
    
    def detect_and_encode_from_array(self, image_array):
        """
        Detect face and generate encoding from numpy array
        
        Args:
            image_array: Image as numpy array (RGB)
            
        Returns:
            Face encoding or None
        """
        face_encodings = face_recognition.face_encodings(image_array)
        
        if len(face_encodings) > 0:
            return face_encodings[0]
        
        return None
    
    def save_verification_image(self, image_array, player_id, logs_dir='logs/images'):
        """
        Save verification image with timestamp
        
        Args:
            image_array: Image to save (RGB)
            player_id: Player identifier
            logs_dir: Directory to save logs
            
        Returns:
            Path to saved image
        """
        os.makedirs(logs_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{player_id}_{timestamp}.jpg"
        filepath = os.path.join(logs_dir, filename)
        
        # Convert RGB to BGR for OpenCV
        bgr_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        cv2.imwrite(filepath, bgr_image)
        
        return filepath

def test_camera():
    """Test if camera is accessible"""
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("✓ Camera is accessible")
        cap.release()
        return True
    else:
        print("✗ Camera not accessible")
        return False

if __name__ == '__main__':
    # Test camera
    test_camera()
    
    # Test face verification
    verifier = FaceVerification()
    print("\nTesting face capture...")
    image, encoding = verifier.capture_face_from_webcam()
    
    if encoding is not None:
        print("✓ Face captured and encoded successfully!")
        print(f"Encoding shape: {encoding.shape}")
    else:
        print("✗ No face detected")
