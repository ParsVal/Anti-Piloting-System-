"""
Test if server verification works independently
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from verification import FaceVerification

def test_verification():
    print("Testing server verification...")
    print("Press SPACE when your face is visible, ESC to cancel")
    
    verifier = FaceVerification()
    frame, encoding = verifier.capture_face_from_webcam()
    
    if encoding is not None:
        print(f"✓ SUCCESS! Got encoding of shape: {encoding.shape}")
        return True
    else:
        print("✗ FAILED - No face detected or encoding created")
        return False

if __name__ == '__main__':
    success = test_verification()
    input("Press Enter to exit...")
