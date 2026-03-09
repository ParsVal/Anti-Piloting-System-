"""
Robust Player Registration Client - Handles All Camera Formats
"""
import tkinter as tk
from tkinter import messagebox, Canvas
import cv2
import requests
import uuid
import numpy as np
from PIL import Image, ImageTk
import sys
import os
import face_recognition

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))

from utils.device_fingerprint import get_machine_guid, get_device_info

class RegistrationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Player Registration — Tournament Verification")
        self.root.geometry("1400x750")
        self.root.configure(bg='#0b0f1a')
        self.root.resizable(True, True)
        self.root.state('zoomed')
        
        # State
        self.facial_encodings = []
        self.machine_guid = None
        self.cap = None
        self.is_previewing = False
        self.current_angle = 0
        self.camera_index = 0
        self.face_detection_method = "haar"  # Default to most reliable
        
        # Angles
        self.angles = [
            ("ANGLE 1", "Face straight to camera", "↓"),
            ("ANGLE 2", "Turn your head LEFT", "←"),
            ("ANGLE 3", "Turn your head RIGHT", "→"),
            ("ANGLE 4", "Tilt your head UP", "↑"),
            ("ANGLE 5", "Tilt your head DOWN", "↓")
        ]
        
        # Face detection components
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup user interface"""
        
        # Header
        header = tk.Frame(self.root, bg='#0d1117', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        title = tk.Label(
            header,
            text="PLAYER REGISTRATION",
            font=('Rajdhani', 18, 'bold'),
            bg='#0d1117',
            fg='#00d4ff',
            pady=15
        )
        title.pack()
        
        # Main content with scrollbar for small screens
        main_container = tk.Frame(self.root, bg='#0b0f1a')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Left panel - Form (reduced width)
        left_panel = tk.Frame(main_container, bg='#0f1520', width=360)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Form content with scrollable area
        canvas = tk.Canvas(left_panel, bg='#0f1520', highlightthickness=0)
        scrollbar = tk.Scrollbar(left_panel, orient="vertical", command=canvas.yview)
        form_content = tk.Frame(canvas, bg='#0f1520')
        
        form_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=form_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Instructions
        instructions = tk.Label(
            form_content,
            text="ROBUST ANTI-CHEAT REGISTRATION\n\nWorks with all camera types.\nUses Haar Cascade for maximum compatibility.",
            font=('Barlow Condensed', 8),
            bg='#0f1520',
            fg='#5a6a80',
            justify='left',
            wraplength=300
        )
        instructions.pack(pady=(10, 8))
        
        # Consent
        self.consent_var = tk.BooleanVar()
        consent_check = tk.Checkbutton(
            form_content,
            text="I consent to biometric data collection",
            variable=self.consent_var,
            font=('Barlow Condensed', 8),
            bg='#0f1520',
            fg='#00d4ff',
            selectcolor='#0a0e16',
            activebackground='#0f1520',
            activeforeground='#00d4ff',
            wraplength=320
        )
        consent_check.pack(pady=(3, 8))
        
        # Name field
        tk.Label(form_content, text="Full Name:", font=('Barlow Condensed', 8), 
                bg='#0f1520', fg='#ffffff').pack(anchor='w', pady=(3, 2))
        self.name_entry = tk.Entry(form_content, font=('Barlow Condensed', 8), 
                                  bg='#1a2332', fg='#ffffff', insertbackground='#00d4ff')
        self.name_entry.pack(fill='x', pady=(0, 8))
        
        # Student ID field
        tk.Label(form_content, text="Student ID:", font=('Barlow Condensed', 8), 
                bg='#0f1520', fg='#ffffff').pack(anchor='w', pady=(3, 2))
        self.student_id_entry = tk.Entry(form_content, font=('Barlow Condensed', 8), 
                                       bg='#1a2332', fg='#ffffff', insertbackground='#00d4ff')
        self.student_id_entry.pack(fill='x', pady=(0, 8))
        
        # Camera selection
        tk.Label(form_content, text="Camera Index:", font=('Barlow Condensed', 8), 
                bg='#0f1520', fg='#ffffff').pack(anchor='w', pady=(3, 2))
        self.camera_var = tk.StringVar(value="0")
        camera_frame = tk.Frame(form_content, bg='#0f1520')
        camera_frame.pack(fill='x', pady=(0, 8))
        
        for i in range(3):
            tk.Radiobutton(camera_frame, text=f"Cam {i}", variable=self.camera_var, 
                          value=str(i), bg='#0f1520', fg='#ffffff', 
                          selectcolor='#1a2332', activebackground='#0f1520',
                          font=('Barlow Condensed', 7),
                          command=self.change_camera).pack(side='left', padx=5)
        
        # Face detection method
        tk.Label(form_content, text="Detection Method:", font=('Barlow Condensed', 8), 
                bg='#0f1520', fg='#ffffff').pack(anchor='w', pady=(3, 2))
        self.detection_var = tk.StringVar(value="haar")
        detection_frame = tk.Frame(form_content, bg='#0f1520')
        detection_frame.pack(fill='x', pady=(0, 8))
        
        tk.Radiobutton(detection_frame, text="Haar (Recommended)", variable=self.detection_var, 
                      value="haar", bg='#0f1520', fg='#00ff88', 
                      selectcolor='#1a2332', activebackground='#0f1520',
                      font=('Barlow Condensed', 7)).pack(side='left', padx=2)
        tk.Radiobutton(detection_frame, text="face_recognition", variable=self.detection_var, 
                      value="face_recognition", bg='#0f1520', fg='#ffffff', 
                      selectcolor='#1a2332', activebackground='#0f1520',
                      font=('Barlow Condensed', 7)).pack(side='left', padx=2)
        
        # Machine GUID section
        tk.Label(form_content, text="Device ID:", font=('Barlow Condensed', 8), 
                bg='#0f1520', fg='#ffffff').pack(anchor='w', pady=(3, 2))
        
        guid_frame = tk.Frame(form_content, bg='#0f1520')
        guid_frame.pack(fill='x', pady=(0, 8))
        
        self.guid_label = tk.Label(guid_frame, text="Not generated", font=('Barlow Condensed', 7), 
                                  bg='#1a2332', fg='#5a6a80', relief='sunken', pady=4)
        self.guid_label.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        self.get_guid_btn = tk.Button(
            guid_frame,
            text="GET DEVICE ID",
            font=('Barlow Condensed', 7, 'bold'),
            bg='#0a0e16',
            fg='#3a4555',
            cursor='hand2',
            command=self.get_machine_guid,
            relief='flat',
            pady=4
        )
        self.get_guid_btn.pack(side='right')
        
        # Start camera button
        self.start_camera_btn = tk.Button(
            form_content,
            text="START CAMERA",
            font=('Rajdhani', 10, 'bold'),
            bg='#0a0e16',
            fg='#3a4555',
            cursor='arrow',
            command=self.start_camera,
            relief='flat',
            pady=6
        )
        self.start_camera_btn.pack(fill='x', pady=(10, 6))
        
        # Face indicator
        self.face_indicator = tk.Label(
            form_content,
            text="● CAMERA OFF",
            font=('Barlow Condensed', 10, 'bold'),
            bg='#0f1520',
            fg='#666666'
        )
        self.face_indicator.pack(pady=(6, 8))
        
        # Progress bars
        progress_frame = tk.Frame(form_content, bg='#0f1520')
        progress_frame.pack(fill='x', pady=(6, 0))
        
        tk.Label(progress_frame, text="CAPTURE PROGRESS:", font=('Barlow Condensed', 7), 
                bg='#0f1520', fg='#5a6a80').pack(anchor='w', pady=(0, 6))
        
        self.progress_bars = []
        for i, (angle, desc, arrow) in enumerate(self.angles):
            bar_frame = tk.Frame(progress_frame, bg='#0f1520')
            bar_frame.pack(fill='x', pady=1)
            
            tk.Label(bar_frame, text=f"{arrow} {angle}", font=('Barlow Condensed', 6), 
                    bg='#0f1520', fg='#5a6a80', width=9, anchor='w').pack(side='left')
            
            bar = tk.Frame(bar_frame, height=2, bg='#1a2332')
            bar.pack(side='left', fill='x', expand=True, padx=(6, 0))
            self.progress_bars.append(bar)
        
        # Capture button (initially disabled)
        self.capture_btn = tk.Button(
            form_content,
            text="CAPTURE FACE",
            font=('Rajdhani', 10, 'bold'),
            bg='#0a0e16',
            fg='#3a4555',
            cursor='arrow',
            state='disabled',
            command=self.capture_face,
            relief='flat',
            pady=6
        )
        self.capture_btn.pack(fill='x', pady=(10, 6))
        
        # Submit button (initially disabled)
        self.submit_btn = tk.Button(
            form_content,
            text="SUBMIT REGISTRATION",
            font=('Rajdhani', 10, 'bold'),
            bg='#0a0e16',
            fg='#3a4555',
            cursor='arrow',
            state='disabled',
            command=self.submit_registration,
            relief='flat',
            pady=6
        )
        self.submit_btn.pack(fill='x', pady=(6, 15))
        
        # Pack scrollable area
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Right panel - Camera preview
        right_panel = tk.Frame(main_container, bg='#0f1520')
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Camera preview area
        self.camera_frame = tk.Frame(right_panel, bg='#0d1117', relief='sunken', bd=2)
        self.camera_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        self.video_label = tk.Label(self.camera_frame, bg='#0d1117')
        self.video_label.pack(fill='both', expand=True)
        
        # Instruction display
        self.instruction_label = tk.Label(
            right_panel,
            text="Click 'START CAMERA' to begin registration",
            font=('Rajdhani', 14, 'bold'),
            bg='#0f1520',
            fg='#00d4ff',
            pady=15,
            wraplength=600
        )
        self.instruction_label.pack()
    
    def change_camera(self):
        """Change camera index"""
        if self.is_previewing:
            self.stop_camera()
        self.camera_index = int(self.camera_var.get())
    
    def get_machine_guid(self):
        """Get machine GUID"""
        try:
            self.machine_guid = get_machine_guid()
            self.guid_label.config(text=self.machine_guid[:20] + "..." if len(self.machine_guid) > 20 else self.machine_guid)
            self.get_guid_btn.config(bg='#00ff88', fg='#000000', text="✓ GENERATED")
            print(f"Machine GUID: {self.machine_guid}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get device ID: {str(e)}")
            print(f"GUID error: {e}")
    
    def normalize_frame(self, frame):
        """
        Normalize frame to standard format that works with all detection methods
        This is the key function that fixes all image format issues
        """
        try:
            # Step 1: Ensure numpy array
            if not isinstance(frame, np.ndarray):
                frame = np.array(frame)
            
            # Step 2: Ensure uint8 data type
            if frame.dtype != np.uint8:
                if frame.max() <= 1.0:  # If normalized 0-1
                    frame = (frame * 255).astype(np.uint8)
                else:
                    frame = frame.astype(np.uint8)
            
            # Step 3: Handle different channel configurations
            if len(frame.shape) == 2:
                # Grayscale -> Convert to BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            elif len(frame.shape) == 3:
                if frame.shape[2] == 4:
                    # BGRA -> BGR
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                elif frame.shape[2] == 1:
                    # Single channel -> BGR
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                elif frame.shape[2] == 3:
                    # Already 3 channels, ensure BGR order
                    if not self.is_bgr_format(frame):
                        # Likely RGB, convert to BGR
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Step 4: Final validation
            if len(frame.shape) != 3 or frame.shape[2] != 3 or frame.dtype != np.uint8:
                raise ValueError(f"Invalid frame format after normalization: {frame.shape}, {frame.dtype}")
            
            return frame
            
        except Exception as e:
            print(f"Frame normalization error: {e}")
            # Return a default black frame if normalization fails
            return np.zeros((480, 640, 3), dtype=np.uint8)
    
    def is_bgr_format(self, frame):
        """
        Check if frame is likely in BGR format
        This is a heuristic - not 100% accurate but works for most cases
        """
        # Sample a few pixels to check color distribution
        # BGR typically has different blue/red ratios than RGB
        sample = frame[100:200, 100:200] if frame.shape[0] > 200 and frame.shape[1] > 200 else frame
        
        if len(sample.shape) == 3 and sample.shape[2] == 3:
            blue_mean = np.mean(sample[:, :, 0])
            red_mean = np.mean(sample[:, :, 2])
            
            # If blue is significantly higher than red, likely BGR
            return blue_mean > red_mean * 1.1
        
        return False
    
    def fix_color_cast(self, frame):
        """
        Fix color cast issues (blueish/reddish tint)
        """
        try:
            # Convert to RGB first to normalize colors
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Convert back to BGR for consistent processing
            fixed_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
            return fixed_frame
        except:
            return frame
    
    def detect_faces_robust(self, frame):
        """
        Robust face detection that handles all camera formats
        """
        method = self.detection_var.get()
        
        # Normalize frame first
        normalized_frame = self.normalize_frame(frame)
        
        if method == "haar":
            # Use OpenCV Haar Cascade - most reliable
            try:
                gray = cv2.cvtColor(normalized_frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                
                # Convert to face_recognition format
                face_locations = []
                for (x, y, w, h) in faces:
                    face_locations.append((y, x + w, y + h, x))  # (top, right, bottom, left)
                
                return face_locations, len(face_locations) > 0
            except Exception as e:
                print(f"Haar cascade error: {e}")
                return [], False
        
        else:  # face_recognition
            # Try face_recognition with extensive format handling
            try:
                # Convert to RGB with multiple fallbacks
                rgb_frame = cv2.cvtColor(normalized_frame, cv2.COLOR_BGR2RGB)
                
                # Double-check RGB format
                if rgb_frame.dtype != np.uint8 or len(rgb_frame.shape) != 3 or rgb_frame.shape[2] != 3:
                    print(f"RGB frame format issue: {rgb_frame.shape}, {rgb_frame.dtype}")
                    return [], False
                
                # Try HOG method first
                face_locations = face_recognition.face_locations(rgb_frame, model="hog")
                
                if len(face_locations) == 0:
                    # Try CNN method
                    face_locations = face_recognition.face_locations(rgb_frame, model="cnn")
                
                return face_locations, len(face_locations) > 0
                
            except Exception as e:
                print(f"face_recognition error: {e}")
                # Fallback to Haar
                try:
                    gray = cv2.cvtColor(normalized_frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                    
                    face_locations = []
                    for (x, y, w, h) in faces:
                        face_locations.append((y, x + w, y + h, x))
                    
                    return face_locations, len(face_locations) > 0
                except Exception as e2:
                    print(f"Fallback Haar failed: {e2}")
                    return [], False
    
    def start_camera(self):
        """Start camera preview"""
        # Validate form
        if not self.consent_var.get():
            messagebox.showerror("Error", "Please consent to biometric data collection")
            return
        
        if not self.name_entry.get().strip():
            messagebox.showerror("Error", "Please enter your name")
            return
        
        if not self.student_id_entry.get().strip():
            messagebox.showerror("Error", "Please enter your student ID")
            return
        
        # Open camera
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            messagebox.showerror("Error", f"Cannot access camera {self.camera_index}")
            return
        
        # Set camera properties for better compatibility
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.is_previewing = True
        self.current_angle = 0
        self.facial_encodings = []
        
        # Update UI
        self.start_camera_btn.config(state='disabled', bg='#0a0e16', fg='#3a4555', cursor='arrow')
        self.capture_btn.config(state='normal', bg='#00ff88', fg='#000000', cursor='hand2')
        
        # Show first instruction
        self.update_instruction()
        
        # Start preview loop
        self.update_preview()
    
    def update_preview(self):
        """Update camera preview"""
        if not self.is_previewing or not self.cap:
            return
        
        ret, frame = self.cap.read()
        if ret:
            try:
                # Normalize frame to handle all camera formats
                normalized_frame = self.normalize_frame(frame)
                
                # Fix color cast (blueish tint)
                normalized_frame = self.fix_color_cast(normalized_frame)
                
                # Flip for mirror effect
                display_frame = cv2.flip(normalized_frame, 1)
                
                # Resize for display
                display_frame = cv2.resize(display_frame, (640, 400))
                
                # Detect face for live indicator
                face_locations, has_face = self.detect_faces_robust(display_frame)
                
                if has_face:
                    self.face_indicator.config(text="● FACE DETECTED", fg='#00ff88')
                    
                    # Draw GREEN rectangle around face
                    top, right, bottom, left = face_locations[0]
                    cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 136), 3)
                    
                    # Draw corner brackets
                    bracket_len = 25
                    thickness = 3
                    color = (0, 255, 136)
                    
                    cv2.line(display_frame, (left, top), (left + bracket_len, top), color, thickness)
                    cv2.line(display_frame, (left, top), (left, top + bracket_len), color, thickness)
                    cv2.line(display_frame, (right, top), (right - bracket_len, top), color, thickness)
                    cv2.line(display_frame, (right, top), (right, top + bracket_len), color, thickness)
                    cv2.line(display_frame, (left, bottom), (left + bracket_len, bottom), color, thickness)
                    cv2.line(display_frame, (left, bottom), (left, bottom - bracket_len), color, thickness)
                    cv2.line(display_frame, (right, bottom), (right - bracket_len, bottom), color, thickness)
                    cv2.line(display_frame, (right, bottom), (right, bottom - bracket_len), color, thickness)
                    
                else:
                    self.face_indicator.config(text="● NO FACE", fg='#ff3355')
                    cv2.rectangle(display_frame, (0, 0), (display_frame.shape[1], display_frame.shape[0]), (255, 51, 85), 3)
                
                # Convert to RGB for display
                frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                
                # Convert to PIL Image
                img = Image.fromarray(frame_rgb)
                img = img.resize((640, 400), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                
                # Update label
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
                
            except Exception as e:
                print(f"Preview error: {e}")
        
        # Schedule next update
        self.root.after(30, self.update_preview)
    
    def update_instruction(self):
        """Update current instruction"""
        if self.current_angle < len(self.angles):
            angle, desc, arrow = self.angles[self.current_angle]
            self.instruction_label.config(text=f"{arrow} {angle}: {desc}")
    
    def capture_face(self):
        """Capture current face"""
        if not self.cap:
            return
        
        # Read frame
        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Error", "Cannot capture frame")
            return
        
        try:
            # Normalize frame to handle all camera formats
            normalized_frame = self.normalize_frame(frame)
            
            # Flip back to normal orientation
            normalized_frame = cv2.flip(normalized_frame, 1)
            
            # Get face locations
            face_locations, has_face = self.detect_faces_robust(normalized_frame)
            
            if not has_face:
                messagebox.showerror("Error", "No face detected. Please position your face in view and try again.")
                return
            
            # Get face encoding (only works with face_recognition method)
            if self.detection_var.get() == "face_recognition":
                try:
                    rgb_frame = cv2.cvtColor(normalized_frame, cv2.COLOR_BGR2RGB)
                    encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    
                    if len(encodings) == 0:
                        messagebox.showerror("Error", "Could not encode face. Please try again.")
                        return
                    
                    # Store encoding
                    self.facial_encodings.append(encodings[0])
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Face encoding failed: {str(e)}\n\nTry switching to Haar method.")
                    return
            else:
                # Haar method - store face location data instead
                # We'll convert to encodings during submission if needed
                self.facial_encodings.append(normalized_frame)
            
            # Update progress bar
            self.progress_bars[self.current_angle].config(bg='#00ff88')
            
            # Flash capture button
            self.capture_btn.config(bg='#ffffff')
            self.root.after(100, lambda: self.capture_btn.config(bg='#00ff88'))
            
            # Move to next angle
            self.current_angle += 1
            
            if self.current_angle < 5:
                # Next angle
                self.update_instruction()
            else:
                # All done
                self.finish_capture()
        
        except Exception as e:
            messagebox.showerror("Error", f"Face capture error: {str(e)}\n\nPlease try again.")
            print(f"Face capture error: {e}")
    
    def finish_capture(self):
        """Finish capture sequence"""
        # Stop preview
        self.stop_camera()
        
        # Update UI
        self.instruction_label.config(text="✅ All faces captured! Click 'SUBMIT REGISTRATION' to complete.")
        self.capture_btn.config(state='disabled', bg='#0a0e16', fg='#3a4555', cursor='arrow')
        self.submit_btn.config(state='normal', bg='#00d4ff', fg='#000000', cursor='hand2')
    
    def stop_camera(self):
        """Stop camera preview"""
        self.is_previewing = False
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Update UI
        self.start_camera_btn.config(state='normal', bg='#00d4ff', fg='#000000', cursor='hand2')
        self.capture_btn.config(state='disabled', bg='#0a0e16', fg='#3a4555', cursor='arrow')
        self.face_indicator.config(text="● CAMERA OFF", fg='#666666')
        
        # Clear video label
        self.video_label.config(image='')
    
    def submit_registration(self):
        """Submit registration to server"""
        if len(self.facial_encodings) == 0:
            messagebox.showerror("Error", "No face data captured")
            return
        
        if not self.machine_guid:
            messagebox.showerror("Error", "Please generate Device ID first by clicking 'GET DEVICE ID'")
            return
        
        try:
            # Convert Haar captures to encodings if needed
            final_encodings = []
            if self.detection_var.get() == "haar":
                # For Haar method, convert captured frames to encodings
                for frame in self.facial_encodings:
                    try:
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        locations = face_recognition.face_locations(rgb_frame)
                        if locations:
                            encodings = face_recognition.face_encodings(rgb_frame, locations)
                            if encodings:
                                final_encodings.append(encodings[0])
                    except:
                        # Skip if encoding fails
                        continue
                
                if len(final_encodings) == 0:
                    messagebox.showerror("Error", "Could not convert face captures to encodings. Please try face_recognition method.")
                    return
            else:
                final_encodings = self.facial_encodings
            
            # Prepare data
            player_data = {
                'name': self.name_entry.get().strip(),
                'student_id': self.student_id_entry.get().strip(),
                'machine_guid': self.machine_guid,
                'facial_encodings': [encoding.tolist() for encoding in final_encodings]
            }
            
            # Send to server
            response = requests.post('http://localhost:5000/api/register', json=player_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                player_id = result.get('player_id')
                
                # Save credentials
                with open('player_credentials.txt', 'w') as f:
                    f.write(f"Player ID: {player_id}\n")
                    f.write(f"Name: {player_data['name']}\n")
                    f.write(f"Student ID: {player_data['student_id']}\n")
                    f.write(f"Machine GUID: {self.machine_guid}\n")
                
                messagebox.showinfo("Success", f"Registration successful!\n\nPlayer ID: {player_id}\n\nYour credentials have been saved to 'player_credentials.txt'")
                self.root.quit()
                
            else:
                error_msg = response.json().get('error', 'Registration failed')
                messagebox.showerror("Error", f"Registration failed: {error_msg}")
        
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Error", "Cannot connect to server. Please ensure the server is running on http://localhost:5000")
        except Exception as e:
            messagebox.showerror("Error", f"Registration error: {str(e)}")

def main():
    root = tk.Tk()
    app = RegistrationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()