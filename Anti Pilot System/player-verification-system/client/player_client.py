"""
Player Verification Client - Esports Theme Real-time Monitor
"""
import tkinter as tk
from tkinter import messagebox, simpledialog
import cv2
import requests
import base64
import numpy as np
from PIL import Image, ImageTk
import threading
import time
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))

import face_recognition
from utils.device_fingerprint import get_machine_guid

class VerificationClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Player Verification — Live Monitor")
        self.root.geometry("1000x700")
        self.root.configure(bg='#0b0f1a')
        self.root.resizable(False, False)
        
        self.player_id = None
        self.server_url = "http://localhost:5000"
        self.machine_guid = get_machine_guid()
        
        self.is_running = False
        self.verification_interval = 30
        self.cap = None
        
        self.setup_ui()
        self.prompt_player_id()
    
    def setup_ui(self):
        """Setup user interface"""
        
        # Header
        header = tk.Frame(self.root, bg='#0d1117', height=70)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg='#0d1117')
        header_content.pack(fill='both', expand=True, padx=30)
        
        # Title
        title = tk.Label(
            header_content,
            text="VERIFICATION MONITOR",
            font=('Rajdhani', 22, 'bold'),
            bg='#0d1117',
            fg='#00d4ff'
        )
        title.pack(side='left', pady=20)
        
        # Live badge - removed, tkinter doesn't support rgba
        
        # Main content
        main_frame = tk.Frame(self.root, bg='#0b0f1a')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Left panel - Status
        left_panel = tk.Frame(main_frame, bg='#0f1520', width=380)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Player info section
        info_section = tk.Frame(left_panel, bg='#0a0e16')
        info_section.pack(fill='x', padx=20, pady=20)
        
        info_label = tk.Label(
            info_section,
            text="PLAYER INFO",
            font=('Barlow Condensed', 10, 'bold'),
            bg='#0a0e16',
            fg='#5a6a80'
        )
        info_label.pack(anchor='w', pady=(10, 10))
        
        self.player_label = tk.Label(
            info_section,
            text="Player: Not Verified",
            font=('Rajdhani', 14, 'bold'),
            bg='#0a0e16',
            fg='#dde4f0',
            anchor='w'
        )
        self.player_label.pack(fill='x', pady=(0, 5))
        
        self.device_label = tk.Label(
            info_section,
            text=f"Device: {self.machine_guid[:28]}...",
            font=('Barlow Condensed', 9),
            bg='#0a0e16',
            fg='#5a6a80',
            anchor='w'
        )
        self.device_label.pack(fill='x', pady=(0, 10))
        
        # Status display - large
        status_container = tk.Frame(left_panel, bg='#0f1520')
        status_container.pack(fill='x', padx=20, pady=20)
        
        status_label_small = tk.Label(
            status_container,
            text="VERIFICATION STATUS",
            font=('Barlow Condensed', 10, 'bold'),
            bg='#0f1520',
            fg='#5a6a80'
        )
        status_label_small.pack(anchor='w', pady=(0, 10))
        
        self.status_frame = tk.Frame(status_container, bg='#1a2436', height=120)
        self.status_frame.pack(fill='x')
        self.status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="WAITING",
            font=('Rajdhani', 36, 'bold'),
            bg='#1a2436',
            fg='#5a6a80'
        )
        self.status_label.pack(expand=True)
        
        # Details section
        details_section = tk.Frame(left_panel, bg='#0f1520')
        details_section.pack(fill='x', padx=20, pady=10)
        
        self.confidence_label = tk.Label(
            details_section,
            text="Confidence: --",
            font=('Barlow Condensed', 12),
            bg='#0f1520',
            fg='#8a9ab0',
            anchor='w'
        )
        self.confidence_label.pack(fill='x', pady=3)
        
        self.device_match_label = tk.Label(
            details_section,
            text="Device Match: --",
            font=('Barlow Condensed', 12),
            bg='#0f1520',
            fg='#8a9ab0',
            anchor='w'
        )
        self.device_match_label.pack(fill='x', pady=3)
        
        self.timestamp_label = tk.Label(
            details_section,
            text="Last Check: --",
            font=('Barlow Condensed', 10),
            bg='#0f1520',
            fg='#5a6a80',
            anchor='w'
        )
        self.timestamp_label.pack(fill='x', pady=3)
        
        # Separator
        sep = tk.Frame(left_panel, bg='#1a2436', height=1)
        sep.pack(fill='x', padx=20, pady=20)
        
        # Control buttons
        control_frame = tk.Frame(left_panel, bg='#0f1520')
        control_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.start_btn = tk.Button(
            control_frame,
            text="START VERIFICATION",
            command=self.start_verification,
            font=('Rajdhani', 13, 'bold'),
            bg='#00e676',
            fg='#000000',
            activebackground='#00ff88',
            activeforeground='#000000',
            bd=0,
            pady=12,
            cursor='hand2'
        )
        self.start_btn.pack(fill='x', pady=5)
        
        self.stop_btn = tk.Button(
            control_frame,
            text="STOP VERIFICATION",
            command=self.stop_verification,
            font=('Rajdhani', 13, 'bold'),
            bg='#0a0e16',
            fg='#3a4555',
            bd=0,
            pady=12,
            state='disabled',
            cursor='arrow'
        )
        self.stop_btn.pack(fill='x', pady=5)
        
        # Status bar at bottom
        self.status_bar = tk.Label(
            left_panel,
            text="Ready",
            font=('Barlow Condensed', 10),
            bg='#0a0e16',
            fg='#5a6a80',
            anchor='w',
            padx=20,
            pady=10
        )
        self.status_bar.pack(side='bottom', fill='x')
        
        # Right panel - Video preview
        right_panel = tk.Frame(main_frame, bg='#0f1520')
        right_panel.pack(side='left', fill='both', expand=True)
        
        # Preview header
        preview_header = tk.Frame(right_panel, bg='#0a0e16', height=50)
        preview_header.pack(fill='x')
        preview_header.pack_propagate(False)
        
        preview_title = tk.Label(
            preview_header,
            text="LIVE CAMERA FEED",
            font=('Rajdhani', 14, 'bold'),
            bg='#0a0e16',
            fg='#00d4ff'
        )
        preview_title.pack(pady=15)
        
        # Video display
        self.video_label = tk.Label(right_panel, bg='#000000')
        self.video_label.pack(fill='both', expand=True, padx=20, pady=20)
    
    def prompt_player_id(self):
        """Prompt for player ID"""
        # Try to load from file
        if os.path.exists('player_credentials.txt'):
            with open('player_credentials.txt', 'r') as f:
                for line in f:
                    if line.startswith('Player ID:'):
                        self.player_id = line.split(':')[1].strip()
                        break
        
        if not self.player_id:
            self.player_id = simpledialog.askstring(
                "Player ID Required",
                "Enter your Player ID:",
                parent=self.root
            )
        
        if self.player_id:
            self.player_label.config(text=f"Player: {self.player_id}")
            self.status_bar.config(text=f"Logged in as {self.player_id}")
        else:
            messagebox.showerror("Error", "Player ID is required")
            self.root.destroy()
    
    def start_verification(self):
        """Start verification process"""
        if not self.player_id:
            messagebox.showerror("Error", "No Player ID set")
            return
        
        self.is_running = True
        self.start_btn.config(state='disabled', bg='#0a0e16', fg='#3a4555', cursor='arrow')
        self.stop_btn.config(state='normal', bg='#ff3355', fg='#ffffff', cursor='hand2')
        
        # Start camera
        self.cap = cv2.VideoCapture(0)
        
        # Start video display
        self.update_video()
        
        # Start verification thread
        self.verification_thread = threading.Thread(target=self.verification_loop, daemon=True)
        self.verification_thread.start()
        
        self.status_bar.config(text="Verification active — monitoring in progress")
    
    def stop_verification(self):
        """Stop verification"""
        self.is_running = False
        
        if self.cap:
            self.cap.release()
        
        self.start_btn.config(state='normal', bg='#00e676', fg='#000000', cursor='hand2')
        self.stop_btn.config(state='disabled', bg='#0a0e16', fg='#3a4555', cursor='arrow')
        
        self.status_label.config(text="STOPPED", bg='#1a2436', fg='#5a6a80')
        self.status_bar.config(text="Verification stopped")
    
    def verification_loop(self):
        """Main verification loop"""
        while self.is_running:
            self.perform_verification()
            
            # Wait before next check
            for _ in range(self.verification_interval):
                if not self.is_running:
                    break
                time.sleep(1)
    
    def perform_verification(self):
        """Perform single verification"""
        if not self.cap or not self.cap.isOpened():
            return
        
        ret, frame = self.cap.read()
        if not ret:
            return
        
        # Ensure correct format
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        elif frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
        else:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Get face encoding
        try:
            face_locations = face_recognition.face_locations(frame)
            if len(face_locations) == 0:
                self.update_status("NO FACE", '#ff9500', None, None)
                return
            
            encodings = face_recognition.face_encodings(frame, face_locations)
            if len(encodings) == 0:
                self.update_status("NO FACE", '#ff9500', None, None)
                return
            
            encoding = encodings[0]
        except Exception as e:
            print(f"Face detection error: {e}")
            self.update_status("ERROR", '#ff3355', None, None)
            return
        
        # Convert frame to base64
        _, buffer = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        image_data = f"data:image/jpeg;base64,{image_base64}"
        
        # Send to server
        data = {
            'player_id': self.player_id,
            'facial_encoding': encoding.tolist(),
            'machine_guid': self.machine_guid,
            'image_data': image_data
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/api/verify",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result['verification_status']
                confidence = result['confidence']
                device_match = result['device_match']
                
                color = '#00ff88' if status == 'VERIFIED' else '#ff3355'
                self.update_status(status, color, confidence, device_match)
            else:
                self.update_status("ERROR", '#ff3355', None, None)
        
        except requests.exceptions.RequestException as e:
            self.update_status("OFFLINE", '#ff9500', None, None)
            print(f"Connection error: {e}")
    
    def update_status(self, status, color, confidence, device_match):
        """Update status display"""
        self.status_frame.config(bg=color)
        self.status_label.config(text=status, bg=color, fg='#000000' if status == 'VERIFIED' else '#ffffff')
        
        if confidence is not None:
            self.confidence_label.config(
                text=f"Confidence: {confidence:.1%}",
                fg='#00ff88' if confidence > 0.7 else '#ff9500'
            )
        else:
            self.confidence_label.config(text="Confidence: --", fg='#8a9ab0')
        
        if device_match is not None:
            self.device_match_label.config(
                text=f"Device Match: {'✓ MATCHED' if device_match else '✗ MISMATCH'}",
                fg='#00ff88' if device_match else '#ff3355'
            )
        else:
            self.device_match_label.config(text="Device Match: --", fg='#8a9ab0')
        
        from datetime import datetime
        self.timestamp_label.config(
            text=f"Last Check: {datetime.now().strftime('%H:%M:%S')}"
        )
    
    def update_video(self):
        """Update video preview"""
        if not self.is_running or not self.cap or not self.cap.isOpened():
            return
        
        ret, frame = self.cap.read()
        if ret:
            # Ensure correct format
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            elif frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            # Resize
            frame = cv2.resize(frame, (560, 420))
            
            # Convert to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            try:
                face_locations = face_recognition.face_locations(rgb_frame)
                for (top, right, bottom, left) in face_locations:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 136), 3)
            except:
                pass
            
            # Convert to PhotoImage
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=img)
            
            self.video_label.imgtk = imgtk
            self.video_label.config(image=imgtk)
        
        if self.is_running:
            self.root.after(30, self.update_video)
    
    def on_closing(self):
        """Handle window closing"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = VerificationClient(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == '__main__':
    main()