"""
Main Flask Application - Player Verification System
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from functools import wraps
import os
from datetime import datetime, timedelta

# Import local modules
from models import Player, AdminUser, VerificationLog, init_db
from verification import FaceVerification
from utils.device_fingerprint import get_machine_guid, verify_device

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize face verification
face_verifier = FaceVerification(tolerance=0.6)

# Active sessions tracking
active_sessions = {}

def login_required(f):
    """Decorator for routes that require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator for admin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('admin_login'))
        if session.get('role') not in ['super_admin', 'tournament_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = AdminUser.verify_password(username, password)
        
        if user:
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            AdminUser.update_last_login(user['id'])
            
            return jsonify({
                'success': True,
                'redirect': url_for('admin_dashboard')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid credentials'
            }), 401
    
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    return render_template('admin_dashboard.html', 
                         username=session.get('username'),
                         role=session.get('role'))

@app.route('/api/players', methods=['GET'])
@admin_required
def get_players():
    """Get all players"""
    players = Player.get_all()
    return jsonify(players)

@app.route('/api/player/<player_id>/logs', methods=['GET'])
@admin_required
def get_player_logs(player_id):
    """Get verification logs for a player"""
    logs = VerificationLog.get_by_player(player_id)
    return jsonify(logs)

@app.route('/api/logs/recent', methods=['GET'])
@admin_required
def get_recent_logs():
    """Get recent verification logs"""
    limit = request.args.get('limit', 100, type=int)
    logs = VerificationLog.get_recent(limit)
    return jsonify(logs)

@app.route('/api/register', methods=['POST'])
def register_player():
    """Register a new player"""
    data = request.get_json()
    
    player_id = data.get('player_id')
    name = data.get('name')
    student_id = data.get('student_id')
    facial_encoding = data.get('facial_encoding')  # Should be sent as list
    machine_guid = data.get('machine_guid')
    
    if not all([player_id, name, facial_encoding, machine_guid]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Convert facial encoding to numpy array
        import numpy as np
        facial_encoding = np.array(facial_encoding)
        
        Player.create(player_id, name, student_id, facial_encoding, machine_guid)
        
        return jsonify({
            'success': True,
            'message': 'Player registered successfully',
            'player_id': player_id
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify', methods=['POST'])
def verify_player():
    """Verify a player"""
    data = request.get_json()
    
    player_id = data.get('player_id')
    captured_encoding = data.get('facial_encoding')  # As list
    current_machine_guid = data.get('machine_guid')
    image_data = data.get('image_data')  # Base64 encoded image
    
    if not all([player_id, captured_encoding, current_machine_guid]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        import numpy as np
        import base64
        from io import BytesIO
        from PIL import Image
        
        # Get registered player
        player = Player.get_by_id(player_id)
        
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Convert captured encoding to numpy array
        captured_encoding = np.array(captured_encoding)
        stored_encoding = np.array(player['facial_encoding'])
        
        # Verify device first
        is_device_match = verify_device(current_machine_guid, player['machine_guid'])
        
        # Simple distance-based verification (replace face_recognition)
        distance = np.linalg.norm(captured_encoding - stored_encoding)
        confidence = max(0, 1 - (distance / 50.0))  # Very lenient normalization
        is_face_match = distance < 25.0  # Very lenient threshold
        
        print(f"DEBUG: Verification details:")
        print(f"  - Distance: {distance:.4f}")
        print(f"  - Threshold: 25.0")
        print(f"  - Confidence: {confidence:.4f}")
        print(f"  - Face Match: {is_face_match}")
        print(f"  - Device Match: {is_device_match}")
        print(f"  - Captured shape: {captured_encoding.shape}")
        print(f"  - Stored shape: {stored_encoding.shape}")
        
        # Determine overall verification status
        verification_status = 'VERIFIED' if (is_face_match and is_device_match) else 'FAILED'
        
        # Save verification image if provided
        image_path = 'no_image.jpg'
        if image_data:
            try:
                # Decode base64 image
                image_bytes = base64.b64decode(image_data.split(',')[1] if ',' in image_data else image_data)
                image = Image.open(BytesIO(image_bytes))
                image_array = np.array(image)
                
                # Save image using OpenCV
                import cv2
                from datetime import datetime
                
                save_dir = os.path.join('server', 'verification_images')
                os.makedirs(save_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_path = os.path.join(save_dir, f"{player_id}_{timestamp}.jpg")
                
                # Convert RGB to BGR for OpenCV
                if len(image_array.shape) == 3:
                    image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                
                cv2.imwrite(image_path, image_array)
                print(f"Saved verification image: {image_path}")
            except Exception as img_err:
                print(f"Failed to save image: {img_err}")
                image_path = 'no_image.jpg'
        
        # Log verification
        log_id = VerificationLog.create(
            player_id,
            verification_status,
            confidence,
            image_path,
            is_device_match
        )
        
        # Emit to admin dashboard via WebSocket
        socketio.emit('verification_update', {
            'player_id': player_id,
            'player_name': player['name'],
            'status': verification_status,
            'confidence': float(confidence),
            'device_matched': bool(is_device_match),
            'timestamp': datetime.now().isoformat(),
            'log_id': log_id
        }, namespace='/')
        
        return jsonify({
            'success': True,
            'verification_status': verification_status,
            'face_match': bool(is_face_match),
            'device_match': bool(is_device_match),
            'confidence': float(confidence),
            'player_name': player['name'],
            'log_id': log_id
        })
    
    except Exception as e:
        print(f"Verification error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/session_start', methods=['POST'])
def start_session():
    """Start a verification session"""
    data = request.get_json()
    player_id = data.get('player_id')
    
    print(f"DEBUG: Session start request for player: {player_id}")
    
    if player_id:
        active_sessions[player_id] = {
            'player_id': player_id,
            'start_time': datetime.now().isoformat(),
            'status': 'ACTIVE'
        }
        print(f"DEBUG: Session started - Active sessions: {list(active_sessions.keys())}")
        
        # Emit to admin dashboard
        socketio.emit('session_started', {
            'player_id': player_id,
            'start_time': active_sessions[player_id]['start_time']
        })
    
    return jsonify({'success': True})

@app.route('/api/session_end', methods=['POST'])
def end_session():
    """End a verification session"""
    data = request.get_json()
    player_id = data.get('player_id')
    
    print(f"DEBUG: Session end request for player: {player_id}")
    
    if player_id in active_sessions:
        del active_sessions[player_id]
        print(f"DEBUG: Session ended - Active sessions: {list(active_sessions.keys())}")
        
        # Emit to admin dashboard
        socketio.emit('session_ended', {'player_id': player_id})
    
    return jsonify({'success': True})

@app.route('/api/active_sessions', methods=['GET'])
@admin_required
def get_active_sessions():
    """Get currently active verification sessions"""
    sessions = list(active_sessions.values())
    print(f"DEBUG: Active sessions requested - returning {len(sessions)} sessions")
    return jsonify(sessions)

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('Client connected')
    emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')

@socketio.on('player_session_start')
def handle_session_start(data):
    """Handle player verification session start"""
    player_id = data.get('player_id')
    
    active_sessions[player_id] = {
        'player_id': player_id,
        'start_time': datetime.now().isoformat(),
        'status': 'ACTIVE'
    }
    
    # Notify all admins
    emit('session_started', {
        'player_id': player_id,
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)

@socketio.on('player_session_end')
def handle_session_end(data):
    """Handle player verification session end"""
    player_id = data.get('player_id')
    
    if player_id in active_sessions:
        del active_sessions[player_id]
    
    # Notify all admins
    emit('session_ended', {
        'player_id': player_id,
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)

@app.route('/api/encode-face', methods=['POST'])
def encode_face():
    """Encode a face image using OpenCV LBPH - no face_recognition"""
    data = request.get_json()
    face_image_b64 = data.get('face_image')
    
    if not face_image_b64:
        return jsonify({'error': 'No face image provided'}), 400
    
    try:
        import base64
        import numpy as np
        from io import BytesIO
        from PIL import Image
        import cv2
        
        # Decode base64 image
        image_bytes = base64.b64decode(face_image_b64)
        image = Image.open(BytesIO(image_bytes))
        
        # Convert to grayscale numpy array
        gray_array = np.array(image.convert('L'))  # L = grayscale
        
        print(f"Server encoding: image shape={gray_array.shape}, dtype={gray_array.dtype}")
        
        # Resize to standard size for consistent encoding
        standard_size = (100, 100)
        gray_resized = cv2.resize(gray_array, standard_size)
        
        # Flatten to create feature vector
        # This is a simple but effective encoding method
        features = gray_resized.flatten().astype(np.float32)
        
        # Normalize
        features = features / 255.0
        
        print(f"✓ Server encoded face: {len(features)} features")
        
        return jsonify({
            'success': True,
            'encoding': features.tolist()
        })
        
    except Exception as e:
        print(f"Server encoding error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize database
    if not os.path.exists('database'):
        os.makedirs('database')
    
    init_db()
    
    print("=" * 60)
    print("Player Verification System - Server Starting")
    print("=" * 60)
    print("Server URL: http://localhost:5000")
    print("Admin Dashboard: http://localhost:5000/admin/login")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
