"""
Player Verification Client - Real-time Monitoring
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

from verification import FaceVerification
from utils.device_fingerprint import get_machine_guid

class VerificationClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Player Verification - Real-time Monitor")
        self.root.geometry("800x700")
        
        self.face_verifier = FaceVerification()
        self.player_id = None
        self.server_url = "http://localhost:5000"
        self.machine_guid = get_machine_guid()
        
        self.is_running = False
        self.verification_interval = 30  # seconds
        self.cap = None
        
        self.setup_ui()
        self.prompt_player_id()
    
    def setup_ui(self):
        """Setup user interface"""
        # Header
        header_frame = tk.Frame(self.root, bg='#2E75B6', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="Player Verification System",
            font=('Arial', 18, 'bold'),
            bg='#2E75B6',
            fg='white'
        )
        title_label.pack(pady=15)
        
        # Main content
        content_frame = tk.Frame(self.root, padx=20, pady=20)
        content_frame.pack(fill='both', expand=True)
        
        # Player info
        info_frame = tk.Frame(content_frame)
        info_frame.pack(fill='x', pady=10)
        
        self.player_label = tk.Label(
            info_frame,
            text="Player: Not Verified",
            font=('Arial', 12, 'bold')
        )
        self.player_label.pack()
        
        self.device_label = tk.Label(
            info_frame,
            text=f"Device: {self.machine_guid[:30]}...",
            font=('Arial', 9),
            fg='gray'
        )
        self.device_label.pack()
        
        # Status display
        status_frame = tk.Frame(content_frame, bg='gray', height=150)
        status_frame.pack(fill='x', pady=20)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="WAITING",
            font=('Arial', 40, 'bold'),
            bg='gray',
            fg='white'
        )
        self.status_label.pack(expand=True)
        
        # Verification details
        details_frame = tk.Frame(content_frame)
        details_frame.pack(fill='x', pady=10)
        
        self.confidence_label = tk.Label(
            details_frame,
            text="Confidence: --",
            font=('Arial', 11)
        )
        self.confidence_label.pack()
        
        self.device_match_label = tk.Label(
            details_frame,
            text="Device Match: --",
            font=('Arial', 11)
        )
        self.device_match_label.pack()
        
        self.timestamp_label = tk.Label(
            details_frame,
            text="Last Check: --",
            font=('Arial', 9),
            fg='gray'
        )
        self.timestamp_label.pack()
        
        # Video preview
        self.video_label = tk.Label(content_frame, bg='black')
        self.video_label.pack(pady=10)
        
        # Controls
        control_frame = tk.Frame(content_frame)
        control_frame.pack(fill='x', pady=10)
        
        self.start_btn = tk.Button(
            control_frame,
            text="Start Verification",
            command=self.start_verification,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 12, 'bold'),
            width=20,
            height=2
        )
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = tk.Button(
            control_frame,
            text="Stop Verification",
            command=self.stop_verification,
            bg='#f44336',
            fg='white',
            font=('Arial', 12, 'bold'),
            width=20,
            height=2,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=5)
        
        # Status bar
        self.status_bar = tk.Label(
            self.root,
            text="Ready",
            bd=1,
            relief='sunken',
            anchor='w'
        )
        self.status_bar.pack(side='bottom', fill='x')
    
    def prompt_player_id(self):
        """Prompt for player ID"""
        # Try to load from file first
        if os.path.exists('player_credentials.txt'):
            with open('player_credentials.txt', 'r') as f:
                for line in f:
                    if line.startswith('Player ID:'):
                        self.player_id = line.split(':')[1].strip()
                        break
        
        if not self.player_id:
            self.player_id = simpledialog.askstring(
                "Player ID",
                "Enter your Player ID:",
                parent=self.root
            )
        
        if self.player_id:
            self.player_label.config(text=f"Player ID: {self.player_id}")
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
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        # Start camera
        self.cap = cv2.VideoCapture(0)
        
        # Start verification thread
        self.verification_thread = threading.Thread(target=self.verification_loop)
        self.verification_thread.daemon = True
        self.verification_thread.start()
        
        # Start video display
        self.update_video()
        
        self.status_bar.config(text="Verification active")
    
    def stop_verification(self):
        """Stop verification process"""
        self.is_running = False
        
        if self.cap:
            self.cap.release()
        
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        
        self.status_label.config(text="STOPPED", bg='gray')
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
        
        # Capture frame
        ret, frame = self.cap.read()
        if not ret:
            return
        
        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Get face encoding
        encoding = self.face_verifier.detect_and_encode_from_array(rgb_frame)
        
        if encoding is None:
            self.update_status("NO FACE", 'orange', None, None)
            return
        
        # Convert frame to base64
        _, buffer = cv2.imencode('.jpg', frame)
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
                
                self.update_status(status, 
                                 'green' if status == 'VERIFIED' else 'red',
                                 confidence,
                                 device_match)
            else:
                self.update_status("ERROR", 'red', None, None)
        
        except requests.exceptions.RequestException as e:
            self.update_status("OFFLINE", 'orange', None, None)
            print(f"Connection error: {e}")
    
    def update_status(self, status, color, confidence, device_match):
        """Update status display"""
        self.status_label.config(text=status, bg=color)
        
        if confidence is not None:
            self.confidence_label.config(
                text=f"Confidence: {confidence:.2%}"
            )
        else:
            self.confidence_label.config(text="Confidence: --")
        
        if device_match is not None:
            self.device_match_label.config(
                text=f"Device Match: {'✓ Yes' if device_match else '✗ No'}",
                fg='green' if device_match else 'red'
            )
        else:
            self.device_match_label.config(text="Device Match: --", fg='black')
        
        from datetime import datetime
        self.timestamp_label.config(
            text=f"Last Check: {datetime.now().strftime('%H:%M:%S')}"
        )
    
    def update_video(self):
        """Update video preview"""
        if self.is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            
            if ret:
                # Resize frame
                frame = cv2.resize(frame, (400, 300))
                
                # Convert to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Detect faces and draw rectangles
                import face_recognition
                face_locations = face_recognition.face_locations(rgb_frame)
                
                for (top, right, bottom, left) in face_locations:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                
                # Convert to PhotoImage
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                imgtk = ImageTk.PhotoImage(image=img)
                
                self.video_label.imgtk = imgtk
                self.video_label.config(image=imgtk)
        
        # Schedule next update
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
