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
        
        # Verify face
        is_face_match, confidence = face_verifier.verify_face(
            captured_encoding,
            player['facial_encoding']
        )
        
        # Verify device
        is_device_match = verify_device(current_machine_guid, player['machine_guid'])
        
        # Determine overall verification status
        verification_status = 'VERIFIED' if (is_face_match and is_device_match) else 'FAILED'
        
        # Save verification image if provided
        image_path = 'no_image.jpg'
        if image_data:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1])
            image = Image.open(BytesIO(image_bytes))
            image_array = np.array(image)
            
            # Save image
            image_path = face_verifier.save_verification_image(
                image_array,
                player_id
            )
        
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
            'device_matched': is_device_match,
            'timestamp': datetime.now().isoformat(),
            'log_id': log_id
        }, namespace='/')
        
        return jsonify({
            'success': True,
            'verification_status': verification_status,
            'face_match': is_face_match,
            'device_match': is_device_match,
            'confidence': float(confidence),
            'player_name': player['name'],
            'log_id': log_id
        })
    
    except Exception as e:
        print(f"Verification error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/active_sessions', methods=['GET'])
@admin_required
def get_active_sessions():
    """Get currently active verification sessions"""
    return jsonify(list(active_sessions.values()))

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
