"""
Player Registration Client - Manual Capture Mode
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
        self.root.resizable(True, True)  # Allow resizing and maximize
        self.root.state('zoomed')  # Start maximized on Windows
        
        # State
        self.facial_encodings = []
        self.machine_guid = None
        self.cap = None
        self.is_previewing = False
        self.current_angle = 0
        
        # Angles
        self.angles = [
            ("ANGLE 1", "Face straight to camera", "↓"),
            ("ANGLE 2", "Turn your head LEFT", "←"),
            ("ANGLE 3", "Turn your head RIGHT", "→"),
            ("ANGLE 4", "Tilt your head UP", "↑"),
            ("ANGLE 5", "Tilt your head DOWN", "↓")
        ]
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup user interface"""
        
        # Header
        header = tk.Frame(self.root, bg='#0d1117', height=70)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        title = tk.Label(
            header,
            text="PLAYER REGISTRATION",
            font=('Rajdhani', 24, 'bold'),
            bg='#0d1117',
            fg='#00d4ff',
            pady=20
        )
        title.pack()
        
        # Main content
        main_frame = tk.Frame(self.root, bg='#0b0f1a')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Left panel - Form
        left_panel = tk.Frame(main_frame, bg='#0f1520', width=350)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Form content
        form_content = tk.Frame(left_panel, bg='#0f1520')
        form_content.pack(padx=25, pady=25, fill='both', expand=True)
        
        # Instructions
        instructions = tk.Label(
            form_content,
            text="ANTI-CHEAT REGISTRATION\n\nCapture your face from 5 different angles.\nFollow instructions on the right.",
            font=('Barlow Condensed', 10),
            bg='#0f1520',
            fg='#5a6a80',
            justify='left'
        )
        instructions.pack(pady=(0, 15))
        
        # Consent
        self.consent_var = tk.BooleanVar()
        consent_check = tk.Checkbutton(
            form_content,
            text="I consent to biometric data collection",
            variable=self.consent_var,
            font=('Barlow Condensed', 9),
            bg='#0f1520',
            fg='#00d4ff',
            selectcolor='#0a0e16',
            activebackground='#0f1520',
            activeforeground='#00d4ff',
            bd=0,
            highlightthickness=0
        )
        consent_check.pack(anchor='w', pady=(0, 15))
        
        # Name
        self.create_field(form_content, "FULL NAME", "name_entry")
        
        # Student ID
        self.create_field(form_content, "STUDENT ID", "student_entry")
        
        # Server URL
        self.create_field(form_content, "SERVER URL", "server_entry", "http://localhost:5000")
        
        # Separator
        sep = tk.Frame(form_content, bg='#1a2436', height=1)
        sep.pack(fill='x', pady=15)
        
        # Status
        self.status_label = tk.Label(
            form_content,
            text="",
            font=('Barlow Condensed', 9),
            bg='#0f1520',
            fg='#5a6a80',
            wraplength=300,
            justify='left'
        )
        self.status_label.pack(pady=(0, 10))
        
        # Start camera button
        self.start_camera_btn = tk.Button(
            form_content,
            text="START CAMERA",
            command=self.start_camera,
            font=('Rajdhani', 11, 'bold'),
            bg='#00d4ff',
            fg='#000000',
            activebackground='#00e6ff',
            bd=0,
            pady=9,
            cursor='hand2'
        )
        self.start_camera_btn.pack(fill='x', pady=4)
        
        # Device fingerprint
        self.device_btn = tk.Button(
            form_content,
            text="GET DEVICE FINGERPRINT",
            command=self.get_device_fingerprint,
            font=('Rajdhani', 11, 'bold'),
            bg='#00e676',
            fg='#000000',
            activebackground='#00ff88',
            bd=0,
            pady=9,
            cursor='hand2'
        )
        self.device_btn.pack(fill='x', pady=4)
        
        # Register
        self.register_btn = tk.Button(
            form_content,
            text="COMPLETE REGISTRATION",
            command=self.register_player,
            font=('Rajdhani', 11, 'bold'),
            bg='#0a0e16',
            fg='#3a4555',
            bd=0,
            pady=9,
            cursor='arrow',
            state='disabled'
        )
        self.register_btn.pack(fill='x', pady=4)
        
        # Right panel - Camera
        right_panel = tk.Frame(main_frame, bg='#0f1520')
        right_panel.pack(side='left', fill='both', expand=True)  # expand=True makes it take remaining space
        
        # Preview header
        preview_header = tk.Frame(right_panel, bg='#0a0e16', height=50)
        preview_header.pack(fill='x')
        preview_header.pack_propagate(False)
        
        header_container = tk.Frame(preview_header, bg='#0a0e16')
        header_container.pack(fill='both', expand=True, padx=20)
        
        preview_title = tk.Label(
            header_container,
            text="CAMERA PREVIEW",
            font=('Rajdhani', 14, 'bold'),
            bg='#0a0e16',
            fg='#00d4ff'
        )
        preview_title.pack(side='left', pady=15)
        
        # Live face detection indicator
        self.face_indicator = tk.Label(
            header_container,
            text="● NO FACE",
            font=('Barlow Condensed', 11, 'bold'),
            bg='#0a0e16',
            fg='#ff3355'
        )
        self.face_indicator.pack(side='right', pady=15)
        
        # Camera display - remove fixed width/height, let it size to content
        self.video_label = tk.Label(right_panel, bg='#000000')
        self.video_label.pack(padx=20, pady=20, fill='both', expand=False)
        
        # Instruction panel
        instruction_panel = tk.Frame(right_panel, bg='#0f1520', height=200)
        instruction_panel.pack(fill='x', padx=20, pady=(0, 20))
        instruction_panel.pack_propagate(True)  # Allow contents to control size
        
        # Current angle instruction
        self.arrow_label = tk.Label(
            instruction_panel,
            text="",
            font=('Rajdhani', 36, 'bold'),
            bg='#0f1520',
            fg='#00d4ff'
        )
        self.arrow_label.pack(pady=2)
        
        self.instruction_label = tk.Label(
            instruction_panel,
            text="Click 'START CAMERA' to begin",
            font=('Barlow Condensed', 12, 'bold'),
            bg='#0f1520',
            fg='#8a9ab0'
        )
        self.instruction_label.pack(pady=2)
        
        # Capture button
        self.capture_btn = tk.Button(
            instruction_panel,
            text="CAPTURE",
            command=self.capture_current_angle,
            font=('Rajdhani', 16, 'bold'),
            bg='#0a0e16',
            fg='#3a4555',
            activebackground='#00ff88',
            activeforeground='#000000',
            bd=0,
            pady=10,
            cursor='arrow',
            state='disabled'
        )
        self.capture_btn.pack(fill='x', pady=5)
        
        # Progress indicators
        progress_container = tk.Frame(instruction_panel, bg='#0f1520')
        progress_container.pack(fill='x', pady=5)
        
        self.progress_bars = []
        for i in range(5):
            bar = tk.Frame(progress_container, bg='#1a2436', height=6, bd=0)
            bar.pack(side='left', fill='x', expand=True, padx=2)
            self.progress_bars.append(bar)
    
    def create_field(self, parent, label_text, attr_name, default=""):
        """Create input field"""
        label = tk.Label(
            parent,
            text=label_text,
            font=('Barlow Condensed', 9, 'bold'),
            bg='#0f1520',
            fg='#5a6a80'
        )
        label.pack(anchor='w', pady=(0, 4))
        
        entry = tk.Entry(
            parent,
            font=('Exo 2', 10),
            bg='#0a0e16',
            fg='#dde4f0',
            insertbackground='#00d4ff',
            bd=0,
            highlightthickness=1,
            highlightbackground='#1a2436',
            highlightcolor='#00d4ff'
        )
        entry.pack(fill='x', ipady=7, pady=(0, 12))
        if default:
            entry.insert(0, default)
        
        setattr(self, attr_name, entry)
    
    def start_camera(self):
        """Start camera preview"""
        if not self.consent_var.get():
            messagebox.showerror("Error", "Please provide consent")
            return
        
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter your name")
            return
        
        # Open camera
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Cannot access camera")
            return
        
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
                # Ensure correct format
                if len(frame.shape) == 2:
                    # Grayscale to BGR for display
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                elif frame.shape[2] == 4:
                    # BGRA to BGR
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                # If already BGR (shape[2] == 3), leave it
                
                # Ensure 8-bit
                if frame.dtype != np.uint8:
                    frame = frame.astype(np.uint8)
                
                # Flip for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Resize
                frame = cv2.resize(frame, (640, 400))
                
                # Convert to RGB for face detection
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Detect face for live indicator and rectangle
                face_detected = False
                try:
                    face_locations = face_recognition.face_locations(rgb_frame)
                    
                    if len(face_locations) > 0:
                        face_detected = True
                        self.face_indicator.config(text="● FACE DETECTED", fg='#00ff88')
                        
                        # Draw GREEN rectangle around face (good to capture)
                        top, right, bottom, left = face_locations[0]
                        cv2.rectangle(rgb_frame, (left, top), (right, bottom), (0, 255, 136), 3)
                        
                        # Draw corner brackets for better visibility
                        bracket_len = 25
                        thickness = 3
                        color = (0, 255, 136)  # Green
                        
                        # Top-left corner
                        cv2.line(rgb_frame, (left, top), (left + bracket_len, top), color, thickness)
                        cv2.line(rgb_frame, (left, top), (left, top + bracket_len), color, thickness)
                        
                        # Top-right corner
                        cv2.line(rgb_frame, (right, top), (right - bracket_len, top), color, thickness)
                        cv2.line(rgb_frame, (right, top), (right, top + bracket_len), color, thickness)
                        
                        # Bottom-left corner
                        cv2.line(rgb_frame, (left, bottom), (left + bracket_len, bottom), color, thickness)
                        cv2.line(rgb_frame, (left, bottom), (left, bottom - bracket_len), color, thickness)
                        
                        # Bottom-right corner
                        cv2.line(rgb_frame, (right, bottom), (right - bracket_len, bottom), color, thickness)
                        cv2.line(rgb_frame, (right, bottom), (right, bottom - bracket_len), color, thickness)
                        
                    else:
                        # No face detected - draw RED frame around entire preview area
                        self.face_indicator.config(text="● NO FACE", fg='#ff3355')
                        
                        # Draw red border around entire frame
                        height, width = rgb_frame.shape[:2]
                        cv2.rectangle(rgb_frame, (5, 5), (width-5, height-5), (255, 51, 85), 3)
                        
                        # Add "NO FACE DETECTED" text overlay
                        cv2.putText(rgb_frame, "NO FACE DETECTED", 
                                  (width//2 - 120, 30), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 
                                  0.7, (255, 51, 85), 2)
                        
                except Exception as e:
                    # If face detection fails, show warning with orange border
                    self.face_indicator.config(text="● CHECKING...", fg='#ff9500')
                    height, width = rgb_frame.shape[:2]
                    cv2.rectangle(rgb_frame, (5, 5), (width-5, height-5), (255, 149, 0), 3)
                
                # Convert to PhotoImage
                img = Image.fromarray(rgb_frame)
                imgtk = ImageTk.PhotoImage(image=img)
                
                self.video_label.imgtk = imgtk
                self.video_label.config(image=imgtk)
            
            except Exception as e:
                print(f"Preview error: {e}")
                # Continue anyway
        
        if self.is_previewing:
            self.root.after(30, self.update_preview)
    
    def update_instruction(self):
        """Update instruction for current angle"""
        if self.current_angle < 5:
            angle_name, instruction, arrow = self.angles[self.current_angle]
            self.arrow_label.config(text=arrow)
            self.instruction_label.config(
                text=f"{angle_name}: {instruction}\nPress CAPTURE when ready",
                fg='#00d4ff'
            )
            self.status_label.config(
                text=f"Capturing angle {self.current_angle + 1} of 5...",
                fg='#00d4ff'
            )
    
    def capture_current_angle(self):
        """Capture face at current angle"""
        if not self.cap or not self.cap.isOpened():
            return
        
        # Capture frame
        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Error", "Failed to capture frame")
            return
        
        # Force convert to RGB - handle all possible formats
        try:
            # Check frame format and convert
            if len(frame.shape) == 2:
                # Grayscale - convert to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            elif frame.shape[2] == 4:
                # BGRA - convert to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
            elif frame.shape[2] == 3:
                # BGR - convert to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                raise ValueError(f"Unexpected frame shape: {frame.shape}")
            
            # Ensure it's 8-bit
            if frame.dtype != np.uint8:
                frame = frame.astype(np.uint8)
            
        except Exception as e:
            messagebox.showerror("Error", f"Image format error: {str(e)}\n\nPlease restart the camera.")
            print(f"Format conversion error: {e}")
            return
        
        # Get face encoding
        try:
            face_locations = face_recognition.face_locations(frame)
            
            if len(face_locations) == 0:
                messagebox.showerror("Error", "No face detected. Please position your face in view and try again.")
                return
            
            encodings = face_recognition.face_encodings(frame, face_locations)
            
            if len(encodings) == 0:
                messagebox.showerror("Error", "Could not encode face. Please try again.")
                return
            
            # Store encoding
            self.facial_encodings.append(encodings[0])
            
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
            messagebox.showerror("Error", f"Face detection error: {str(e)}\n\nPlease try again with better lighting.")
            print(f"Face encoding error: {e}")
    
    def finish_capture(self):
        """Finish capture sequence"""
        # Stop preview
        self.is_previewing = False
        if self.cap:
            self.cap.release()
        
        # Update UI
        self.video_label.config(image='', bg='#000000')
        self.face_indicator.config(text="● CAMERA OFF", fg='#5a6a80')
        self.arrow_label.config(text="✓")
        self.instruction_label.config(text="All angles captured successfully!", fg='#00ff88')
        self.capture_btn.config(state='disabled', bg='#0a0e16', fg='#3a4555', cursor='arrow')
        
        self.status_label.config(
            text="✓ Facial data captured successfully!\nNow get device fingerprint.",
            fg='#00ff88'
        )
        
        messagebox.showinfo("Success", "All 5 angles captured successfully!")
        
        self.check_registration_ready()
    
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
        
        messagebox.showinfo(
            "Device Fingerprint",
            f"Device ID obtained!\n\nPlatform: {device_info['platform']}\nDevice ID: {self.machine_guid}"
        )
        
        self.check_registration_ready()
    
    def check_registration_ready(self):
        """Check if ready to register"""
        if len(self.facial_encodings) == 5 and self.machine_guid is not None:
            self.register_btn.config(
                state='normal',
                bg='#7b2fff',
                fg='#ffffff',
                cursor='hand2'
            )
    
    def register_player(self):
        """Register player with server"""
        name = self.name_entry.get().strip()
        student_id = self.student_entry.get().strip()
        server_url = self.server_entry.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Enter your name")
            return
        
        if len(self.facial_encodings) != 5:
            messagebox.showerror("Error", "Capture facial data first")
            return
        
        if not self.machine_guid:
            messagebox.showerror("Error", "Get device fingerprint first")
            return
        
        # Average encodings
        avg_encoding = np.mean(self.facial_encodings, axis=0)
        
        # Generate player ID
        player_id = f"PLAYER_{uuid.uuid4().hex[:8].upper()}"
        
        # Prepare data
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
                messagebox.showinfo(
                    "Registration Successful",
                    f"Registration complete!\n\nPlayer ID: {player_id}\nName: {name}"
                )
                
                # Save credentials
                with open('player_credentials.txt', 'w') as f:
                    f.write(f"Player ID: {player_id}\n")
                    f.write(f"Name: {name}\n")
                    f.write(f"Student ID: {student_id}\n")
                
                self.root.destroy()
            else:
                error = response.json().get('error', 'Unknown error')
                messagebox.showerror("Failed", f"Error: {error}")
        
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Cannot connect to server.\n\n{str(e)}")

def main():
    root = tk.Tk()
    app = RegistrationGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
