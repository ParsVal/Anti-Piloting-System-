"""
Working Registration GUI using OpenCV DNN face detection
Replaces face_recognition face_locations with OpenCV DNN
"""
import tkinter as tk
from tkinter import messagebox
import cv2
import requests
import uuid
import numpy as np
from PIL import Image, ImageTk
import sys
import os

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
        
        self.facial_encodings = []
        self.machine_guid = None
        self.cap = None
        self.is_previewing = False
        self.current_angle = 0
        
        self.angles = [
            ("ANGLE 1", "Face straight to camera", "↓"),
            ("ANGLE 2", "Turn your head LEFT", "←"),
            ("ANGLE 3", "Turn your head RIGHT", "→"),
            ("ANGLE 4", "Tilt your head UP", "↑"),
            ("ANGLE 5", "Tilt your head DOWN", "↓")
        ]
        
        # Load OpenCV DNN face detector (more robust than Haar)
        self.load_face_detector()
        
        self.setup_ui()
    
    def load_face_detector(self):
        """Load OpenCV DNN face detector"""
        # Use OpenCV's built-in face detection (no external models needed)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        print("Face detector loaded")
    
    def detect_face_opencv(self, frame):
        """Detect face using OpenCV Haar cascade - returns (x, y, w, h) or None"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return None
        
        # Return largest face
        largest = max(faces, key=lambda f: f[2] * f[3])
        return largest
    
    def setup_ui(self):
        """Setup the user interface"""
        # Header
        header = tk.Frame(self.root, bg='#0d1117', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="PLAYER REGISTRATION", font=('Rajdhani', 18, 'bold'),
                bg='#0d1117', fg='#00d4ff', pady=15).pack()
        
        # Main container
        main = tk.Frame(self.root, bg='#0b0f1a')
        main.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Left panel - Form
        left = tk.Frame(main, bg='#0f1520', width=360)
        left.pack(side='left', fill='y', padx=(0, 10))
        left.pack_propagate(False)
        
        form = tk.Frame(left, bg='#0f1520')
        form.pack(padx=20, pady=20, fill='both', expand=True)
        
        # Consent
        self.consent_var = tk.BooleanVar()
        tk.Checkbutton(form, text="I consent to biometric data collection",
                      variable=self.consent_var, font=('Barlow Condensed', 9),
                      bg='#0f1520', fg='#00d4ff', selectcolor='#0a0e16').pack(anchor='w', pady=(0,15))
        
        # Name
        tk.Label(form, text="FULL NAME", font=('Barlow Condensed', 9, 'bold'),
                bg='#0f1520', fg='#5a6a80').pack(anchor='w', pady=(0,4))
        self.name_entry = tk.Entry(form, font=('Exo 2', 10), bg='#0a0e16', fg='#dde4f0',
                                  insertbackground='#00d4ff', bd=0)
        self.name_entry.pack(fill='x', ipady=7, pady=(0,12))
        
        # Student ID
        tk.Label(form, text="STUDENT ID", font=('Barlow Condensed', 9, 'bold'),
                bg='#0f1520', fg='#5a6a80').pack(anchor='w', pady=(0,4))
        self.student_entry = tk.Entry(form, font=('Exo 2', 10), bg='#0a0e16', fg='#dde4f0',
                                     insertbackground='#00d4ff', bd=0)
        self.student_entry.pack(fill='x', ipady=7, pady=(0,12))
        
        # Server URL
        tk.Label(form, text="SERVER URL", font=('Barlow Condensed', 9, 'bold'),
                bg='#0f1520', fg='#5a6a80').pack(anchor='w', pady=(0,4))
        self.server_entry = tk.Entry(form, font=('Exo 2', 10), bg='#0a0e16', fg='#dde4f0',
                                    insertbackground='#00d4ff', bd=0)
        self.server_entry.insert(0, "http://localhost:5000")
        self.server_entry.pack(fill='x', ipady=7, pady=(0,12))
        
        tk.Frame(form, bg='#1a2436', height=1).pack(fill='x', pady=15)
        
        # Status
        self.status_label = tk.Label(form, text="Ready", font=('Barlow Condensed', 9),
                                     bg='#0f1520', fg='#5a6a80', wraplength=300, justify='left')
        self.status_label.pack(pady=(0,10))
        
        # Start camera
        self.start_btn = tk.Button(form, text="START CAMERA", command=self.start_camera,
                                   font=('Rajdhani', 11, 'bold'), bg='#00d4ff', fg='#000000',
                                   bd=0, pady=9, cursor='hand2')
        self.start_btn.pack(fill='x', pady=4)
        
        # Device fingerprint
        self.device_btn = tk.Button(form, text="GET DEVICE FINGERPRINT", command=self.get_device_fingerprint,
                                    font=('Rajdhani', 11, 'bold'), bg='#00e676', fg='#000000',
                                    bd=0, pady=9, cursor='hand2')
        self.device_btn.pack(fill='x', pady=4)
        
        # Register
        self.register_btn = tk.Button(form, text="COMPLETE REGISTRATION", command=self.register_player,
                                      font=('Rajdhani', 11, 'bold'), bg='#0a0e16', fg='#3a4555',
                                      bd=0, pady=9, cursor='arrow', state='disabled')
        self.register_btn.pack(fill='x', pady=4)
        
        # Right panel - Camera preview
        right = tk.Frame(main, bg='#0f1520')
        right.pack(side='left', fill='both', expand=True)
        
        # Preview header
        preview_header = tk.Frame(right, bg='#0a0e16', height=50)
        preview_header.pack(fill='x')
        preview_header.pack_propagate(False)
        
        header_container = tk.Frame(preview_header, bg='#0a0e16')
        header_container.pack(fill='both', expand=True, padx=20)
        
        tk.Label(header_container, text="CAMERA PREVIEW", font=('Rajdhani', 14, 'bold'),
                bg='#0a0e16', fg='#00d4ff').pack(side='left', pady=15)
        
        self.face_indicator = tk.Label(header_container, text="● NO FACE",
                                       font=('Barlow Condensed', 11, 'bold'),
                                       bg='#0a0e16', fg='#ff3355')
        self.face_indicator.pack(side='right', pady=15)
        
        # Video display
        self.video_label = tk.Label(right, bg='#000000')
        self.video_label.pack(padx=20, pady=20, fill='both', expand=False)
        
        # Instructions panel
        instruction_panel = tk.Frame(right, bg='#0f1520')
        instruction_panel.pack(fill='x', padx=20, pady=(0,20))
        
        self.arrow_label = tk.Label(instruction_panel, text="", font=('Rajdhani', 36, 'bold'),
                                    bg='#0f1520', fg='#00d4ff')
        self.arrow_label.pack(pady=2)
        
        self.instruction_label = tk.Label(instruction_panel, text="Click 'START CAMERA' to begin",
                                         font=('Barlow Condensed', 12, 'bold'),
                                         bg='#0f1520', fg='#8a9ab0')
        self.instruction_label.pack(pady=2)
        
        # Capture button
        self.capture_btn = tk.Button(instruction_panel, text="CAPTURE", command=self.capture_current_angle,
                                     font=('Rajdhani', 16, 'bold'), bg='#0a0e16', fg='#3a4555',
                                     bd=0, pady=10, cursor='arrow', state='disabled')
        self.capture_btn.pack(fill='x', pady=5)
        
        # Progress bars
        progress_container = tk.Frame(instruction_panel, bg='#0f1520')
        progress_container.pack(fill='x', pady=5)
        
        self.progress_bars = []
        for i in range(5):
            bar = tk.Frame(progress_container, bg='#1a2436', height=6, bd=0)
            bar.pack(side='left', fill='x', expand=True, padx=2)
            self.progress_bars.append(bar)
    
    def start_camera(self):
        """Start camera preview"""
        if not self.consent_var.get():
            messagebox.showerror("Error", "Please provide consent")
            return
        
        if not self.name_entry.get().strip():
            messagebox.showerror("Error", "Please enter your name")
            return
        
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Cannot access camera")
            return
        
        self.is_previewing = True
        self.current_angle = 0
        self.facial_encodings = []
        
        self.start_btn.config(state='disabled', bg='#0a0e16', fg='#3a4555', cursor='arrow')
        self.capture_btn.config(state='normal', bg='#00ff88', fg='#000000', cursor='hand2')
        
        self.update_instruction()
        self.update_preview()
    
    def update_preview(self):
        """Update camera preview with face detection"""
        if not self.is_previewing or not self.cap:
            return
        
        ret, frame = self.cap.read()
        if not ret:
            return
        
        try:
            # Flip for mirror effect
            display_frame = cv2.flip(frame, 1)
            display_frame = cv2.resize(display_frame, (640, 400))
            
            # Detect face with Haar
            face = self.detect_face_opencv(display_frame)
            
            if face is not None:
                self.face_indicator.config(text="● FACE DETECTED", fg='#00ff88')
                x, y, w, h = face
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 136), 3)
            else:
                self.face_indicator.config(text="● NO FACE", fg='#ff3355')
            
            # Convert to RGB for display
            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            
            self.video_label.imgtk = imgtk
            self.video_label.config(image=imgtk)
        
        except Exception as e:
            print(f"Preview error: {e}")
        
        if self.is_previewing:
            self.root.after(30, self.update_preview)
    
    def update_instruction(self):
        """Update instruction text"""
        if self.current_angle < 5:
            angle, desc, arrow = self.angles[self.current_angle]
            self.arrow_label.config(text=arrow)
            self.instruction_label.config(text=f"{angle}: {desc}\nPress CAPTURE when ready", fg='#00d4ff')
            self.status_label.config(text=f"Capturing angle {self.current_angle + 1} of 5...", fg='#00d4ff')
    
    def capture_current_angle(self):
        """Capture face and send to server for encoding - non-blocking"""
        if not self.cap:
            return
        
        # Stop preview temporarily
        self.is_previewing = False
        
        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Error", "Failed to capture frame")
            self.is_previewing = True
            self.update_preview()
            return
        
        # Process capture in background to avoid freezing GUI
        self.root.after(100, lambda: self._process_capture(frame))
    
    def _process_capture(self, frame):
        """Process the actual capture (runs after GUI update)"""
        try:
            print(f"Capturing angle {self.current_angle + 1}...")
            
            # Flip frame
            frame = cv2.flip(frame, 1)
            
            # Detect face
            face = self.detect_face_opencv(frame)
            
            if face is None:
                messagebox.showerror("Error", "No face detected.")
                self.is_previewing = True
                self.update_preview()
                return
            
            # Get face region with padding
            x, y, w, h = face
            padding = 30
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(frame.shape[1] - x, w + 2*padding)
            h = min(frame.shape[0] - y, h + 2*padding)
            
            # Extract face region
            face_region = frame[y:y+h, x:x+w]
            
            # Convert to grayscale for encoding
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Encode grayscale face image as base64 to send to server
            import base64
            _, buffer = cv2.imencode('.jpg', gray_face)
            face_b64 = base64.b64encode(buffer).decode('utf-8')
            
            # Send to server for encoding
            server_url = self.server_entry.get().strip()
            try:
                response = requests.post(
                    f"{server_url}/api/encode-face",
                    json={'face_image': face_b64},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    encoding = np.array(data['encoding'])
                    self.facial_encodings.append(encoding)
                    print(f"✓ Angle {self.current_angle + 1} encoded by server: {encoding.shape}")
                    
                    # Update UI
                    self.progress_bars[self.current_angle].config(bg='#00ff88')
                    self.current_angle += 1
                    
                    if self.current_angle < 5:
                        self.update_instruction()
                        # Restart preview after successful capture
                        self.is_previewing = True
                        self.update_preview()
                    else:
                        self.finish_capture()
                else:
                    messagebox.showerror("Error", f"Server encoding failed: {response.text}")
                    self.is_previewing = True
                    self.update_preview()
            except Exception as e:
                messagebox.showerror("Error", f"Cannot connect to server: {str(e)}")
                self.is_previewing = True
                self.update_preview()
        
        except Exception as e:
            messagebox.showerror("Error", f"Capture failed: {str(e)}")
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            self.is_previewing = True
            self.update_preview()
    
    def finish_capture(self):
        """Finish capture sequence"""
        self.is_previewing = False
        if self.cap:
            self.cap.release()
        
        self.video_label.config(image='', bg='#000000')
        self.face_indicator.config(text="● CAMERA OFF", fg='#5a6a80')
        self.arrow_label.config(text="✓")
        self.instruction_label.config(text="All angles captured successfully!", fg='#00ff88')
        self.capture_btn.config(state='disabled', bg='#0a0e16', fg='#3a4555', cursor='arrow')
        
        self.status_label.config(text="✓ Facial data captured!\nNow get device fingerprint.", fg='#00ff88')
        messagebox.showinfo("Success", "All 5 angles captured successfully!")
        
        self.check_ready()
    
    def get_device_fingerprint(self):
        """Get device fingerprint"""
        if not self.consent_var.get():
            messagebox.showerror("Error", "Please provide consent")
            return
        
        self.machine_guid = get_machine_guid()
        device_info = get_device_info()
        
        self.status_label.config(
            text=f"✓ Device: {self.machine_guid[:28]}...\n{device_info['platform']} {device_info['platform_release']}",
            fg='#00ff88'
        )
        
        self.device_btn.config(state='disabled', bg='#0a0e16', fg='#3a4555', cursor='arrow')
        messagebox.showinfo("Device Fingerprint", f"Device ID obtained!\n\nPlatform: {device_info['platform']}\nDevice ID: {self.machine_guid}")
        
        self.check_ready()
    
    def check_ready(self):
        """Check if ready to register"""
        if len(self.facial_encodings) == 5 and self.machine_guid:
            self.register_btn.config(state='normal', bg='#7b2fff', fg='#ffffff', cursor='hand2')
    
    def register_player(self):
        """Register player with server"""
        name = self.name_entry.get().strip()
        student_id = self.student_entry.get().strip()
        server_url = self.server_entry.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Enter your name")
            return
        
        if len(self.facial_encodings) != 5:
            messagebox.showerror("Error", f"Only {len(self.facial_encodings)}/5 angles captured")
            return
        
        if not self.machine_guid:
            messagebox.showerror("Error", "Get device fingerprint first")
            return
        
        # Average encodings
        avg_encoding = np.mean(self.facial_encodings, axis=0)
        player_id = f"PLAYER_{uuid.uuid4().hex[:8].upper()}"
        
        data = {
            'player_id': player_id,
            'name': name,
            'student_id': student_id,
            'facial_encoding': avg_encoding.tolist(),
            'machine_guid': self.machine_guid
        }
        
        try:
            response = requests.post(f"{server_url}/api/register", json=data, timeout=10)
            
            if response.status_code == 200:
                messagebox.showinfo("Success", f"Registration complete!\n\nPlayer ID: {player_id}\nName: {name}")
                
                with open('player_credentials.txt', 'w') as f:
                    f.write(f"Player ID: {player_id}\n")
                    f.write(f"Name: {name}\n")
                    f.write(f"Student ID: {student_id}\n")
                
                self.root.destroy()
            else:
                error = response.json().get('error', 'Unknown error')
                messagebox.showerror("Failed", f"Error: {error}")
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")

def main():
    root = tk.Tk()
    app = RegistrationGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
