#!/usr/bin/env python3
"""
Camera and Face Detection Debug Script
Tests camera access and face detection with different methods
"""
import cv2
import face_recognition
import numpy as np
import sys
import os

def test_camera_access():
    """Test basic camera access"""
    print("=== Testing Camera Access ===")
    
    # Try different camera indices
    for camera_index in range(3):
        print(f"\nTrying camera index {camera_index}...")
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print(f"❌ Camera {camera_index}: Cannot access")
            continue
        
        # Try to read a frame
        ret, frame = cap.read()
        if not ret:
            print(f"❌ Camera {camera_index}: Cannot read frame")
            cap.release()
            continue
        
        print(f"✅ Camera {camera_index}: Working - Resolution: {frame.shape}")
        cap.release()
        return camera_index
    
    print("❌ No working camera found!")
    return None

def test_opencv_face_detection(camera_index=0):
    """Test OpenCV Haar Cascade face detection"""
    print(f"\n=== Testing OpenCV Haar Cascade Face Detection ===")
    
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ Cannot access camera")
        return False
    
    # Load Haar Cascade
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    
    if face_cascade.empty():
        print("❌ Cannot load Haar Cascade classifier")
        cap.release()
        return False
    
    print("Press SPACE to test face detection, ESC to exit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert to grayscale for Haar Cascade
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        # Draw rectangles
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Display status
        status = f"Faces detected: {len(faces)}" if len(faces) > 0 else "No faces detected"
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "OpenCV Haar Cascade", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow('OpenCV Face Detection Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key == 32:  # SPACE
            print(f"Haar Cascade detected {len(faces)} face(s)")
    
    cap.release()
    cv2.destroyAllWindows()
    return len(faces) > 0

def test_face_recognition_library(camera_index=0):
    """Test face_recognition library"""
    print(f"\n=== Testing face_recognition Library ===")
    
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ Cannot access camera")
        return False
    
    print("Press SPACE to test face detection, ESC to exit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert to RGB for face_recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces using face_recognition
        try:
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        except Exception as e:
            print(f"❌ face_recognition error: {e}")
            face_locations = []
            face_encodings = []
        
        # Draw rectangles
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        
        # Display status
        status = f"Faces detected: {len(face_locations)}" if len(face_locations) > 0 else "No faces detected"
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "face_recognition library", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Encodings: {len(face_encodings)}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow('face_recognition Library Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key == 32:  # SPACE
            print(f"face_recognition detected {len(face_locations)} face(s), {len(face_encodings)} encoding(s)")
    
    cap.release()
    cv2.destroyAllWindows()
    return len(face_locations) > 0

def test_different_face_detection_methods(camera_index=0):
    """Test different face detection models/methods"""
    print(f"\n=== Testing Different Face Detection Methods ===")
    
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ Cannot access camera")
        return
    
    # Load Haar Cascade
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    
    print("Press SPACE to test all methods, ESC to exit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Method 1: Haar Cascade (grayscale)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        haar_faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        # Method 2: face_recognition (RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        try:
            fr_faces = face_recognition.face_locations(rgb_frame)
            fr_encodings = face_recognition.face_encodings(rgb_frame, fr_faces)
        except:
            fr_faces = []
            fr_encodings = []
        
        # Method 3: face_recognition with different model
        try:
            fr_faces_cnn = face_recognition.face_locations(rgb_frame, model="cnn")
            fr_encodings_cnn = face_recognition.face_encodings(rgb_frame, fr_faces_cnn)
        except:
            fr_faces_cnn = []
            fr_encodings_cnn = []
        
        # Draw results
        display_frame = frame.copy()
        
        # Haar Cascade results (red rectangles)
        for (x, y, w, h) in haar_faces:
            cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
        
        # face_recognition HOG results (green rectangles)
        for (top, right, bottom, left) in fr_faces:
            cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)
        
        # face_recognition CNN results (blue rectangles)
        for (top, right, bottom, left) in fr_faces_cnn:
            cv2.rectangle(display_frame, (left, top), (right, bottom), (255, 0, 0), 2)
        
        # Display summary
        y_offset = 30
        cv2.putText(display_frame, f"Haar Cascade: {len(haar_faces)} faces", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        y_offset += 25
        cv2.putText(display_frame, f"face_recognition HOG: {len(fr_faces)} faces, {len(fr_encodings)} encodings", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        y_offset += 25
        cv2.putText(display_frame, f"face_recognition CNN: {len(fr_faces_cnn)} faces, {len(fr_encodings_cnn)} encodings", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        y_offset += 25
        cv2.putText(display_frame, "Press SPACE to capture, ESC to exit", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow('All Face Detection Methods Comparison', display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key == 32:  # SPACE
            print(f"\n=== Face Detection Results ===")
            print(f"Haar Cascade: {len(haar_faces)} face(s)")
            print(f"face_recognition HOG: {len(fr_faces)} face(s), {len(fr_encodings)} encoding(s)")
            print(f"face_recognition CNN: {len(fr_faces_cnn)} face(s), {len(fr_encodings_cnn)} encoding(s)")
            
            # Save a test image
            test_path = "debug_face_test.jpg"
            cv2.imwrite(test_path, frame)
            print(f"Test image saved to: {test_path}")
    
    cap.release()
    cv2.destroyAllWindows()

def main():
    print("🔍 Camera and Face Detection Debug Tool")
    print("=" * 50)
    
    # Test camera access
    camera_index = test_camera_access()
    if camera_index is None:
        print("\n❌ No working camera found. Please check:")
        print("  - Camera is connected and not in use by other apps")
        print("  - Camera permissions are granted")
        print("  - Camera drivers are installed")
        return
    
    print(f"\n✅ Using camera index {camera_index}")
    
    # Test different face detection methods
    print("\n" + "=" * 50)
    print("Choose test mode:")
    print("1. OpenCV Haar Cascade only")
    print("2. face_recognition library only") 
    print("3. Compare all methods (recommended)")
    print("4. Run all tests sequentially")
    
    try:
        choice = input("\nEnter choice (1-4): ").strip()
    except:
        choice = "3"  # Default to compare all methods
    
    if choice == "1":
        test_opencv_face_detection(camera_index)
    elif choice == "2":
        test_face_recognition_library(camera_index)
    elif choice == "3":
        test_different_face_detection_methods(camera_index)
    elif choice == "4":
        print("\nRunning all tests sequentially...")
        
        print("\n1. Testing OpenCV Haar Cascade...")
        haar_result = test_opencv_face_detection(camera_index)
        
        print("\n2. Testing face_recognition library...")
        fr_result = test_face_recognition_library(camera_index)
        
        print("\n3. Comparing all methods...")
        test_different_face_detection_methods(camera_index)
        
        print(f"\n=== SUMMARY ===")
        print(f"OpenCV Haar Cascade: {'✅ Working' if haar_result else '❌ Failed'}")
        print(f"face_recognition library: {'✅ Working' if fr_result else '❌ Failed'}")
    else:
        print("Invalid choice, running comparison test...")
        test_different_face_detection_methods(camera_index)

if __name__ == "__main__":
    main()
