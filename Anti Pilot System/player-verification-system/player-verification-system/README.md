# Player Verification and Anti-Cheating System

A comprehensive facial recognition and device fingerprinting system designed to prevent piloting (unauthorized player substitution) in school-based online gaming tournaments.

## 🎯 Features

- **Facial Recognition**: AI-powered face verification using OpenCV and face_recognition library
- **Device Fingerprinting**: Unique MachineGuid tracking for device authentication
- **Real-time Monitoring**: Continuous verification every 30-60 seconds during gameplay
- **Admin Dashboard**: Web-based interface for tournament oversight
- **Verification Backlog**: Complete audit trail with timestamped images
- **Multi-platform Support**: Works on Windows, Linux, and macOS
- **Secure Authentication**: Role-based access control with encrypted passwords

## 📋 System Requirements

### Hardware
- Processor: Dual-core (Intel i3 or AMD equivalent)
- RAM: Minimum 4 GB
- Camera: Built-in webcam (480p or 720p minimum)
- Network: Stable internet connection (2 Mbps minimum)

### Software
- Operating System: Windows 10, Linux Ubuntu 20.04+, or macOS
- Python: 3.7 or higher
- Node.js: Not required (pure Python implementation)

## 🚀 Installation

### 1. Clone or Download the Repository

```bash
cd player-verification-system
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note**: On some systems, you may need additional dependencies for face_recognition:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install cmake
sudo apt-get install python3-dev
```

**macOS:**
```bash
brew install cmake
```

**Windows:**
- Install Visual Studio Build Tools if prompted

### 3. Initialize the Database

```bash
cd server
python models.py
```

### 4. Create Admin Account

```bash
cd ../scripts
python create_admin.py --interactive
```

Follow the prompts to create your first admin account.

**Alternatively, use command-line mode:**
```bash
python create_admin.py --username admin --email admin@school.edu --role super_admin
```

## 📖 Usage Guide

### For Players

#### Step 1: Registration
1. Run the registration client:
   ```bash
   cd client
   python registration_gui.py
   ```

2. Follow the on-screen instructions:
   - Provide consent for data collection
   - Enter your name and student ID
   - Capture 5 facial photos from different angles
   - Get your device fingerprint
   - Complete registration

3. Save your Player ID (automatically saved to `player_credentials.txt`)

#### Step 2: Tournament Day Verification
1. Launch the verification client:
   ```bash
   python player_client.py
   ```

2. Enter your Player ID when prompted

3. Click "Start Verification"

4. Keep the application running during your entire tournament session

5. The system will:
   - Verify your face every 30-60 seconds
   - Display verification status (VERIFIED/FAILED)
   - Show your webcam feed with face detection
   - Log all verification attempts

### For Administrators

#### Step 1: Start the Server
```bash
cd server
python app.py
```

The server will start at: http://localhost:5000

#### Step 2: Access Admin Dashboard
1. Open your browser and navigate to: http://localhost:5000/admin/login

2. Login with your admin credentials

3. You will see:
   - Real-time verification statistics
   - Recent verification logs
   - List of registered players
   - Live updates via WebSocket

#### Step 3: Monitor Tournament
- View real-time verification status for all active players
- Check verification history and confidence scores
- Review captured images for flagged incidents
- Export reports for post-tournament analysis

## 🏗️ Project Structure

```
player-verification-system/
├── server/
│   ├── app.py                    # Main Flask application
│   ├── models.py                 # Database models
│   ├── verification.py           # Facial recognition engine
│   ├── templates/
│   │   ├── index.html           # Home page
│   │   ├── login.html           # Admin login
│   │   └── admin_dashboard.html # Dashboard interface
│   └── utils/
│       └── device_fingerprint.py # MachineGuid extraction
├── client/
│   ├── registration_gui.py      # Player registration GUI
│   └── player_client.py         # Verification client
├── database/
│   └── verification_system.db   # SQLite database (auto-created)
├── logs/
│   └── images/                  # Verification images (auto-created)
├── scripts/
│   └── create_admin.py          # Admin account generator
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🔧 Configuration

### Server Configuration
Edit `server/app.py` to configure:

```python
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
```

### Face Recognition Tolerance
Adjust recognition strictness in `server/verification.py`:

```python
face_verifier = FaceVerification(tolerance=0.6)  # Lower = more strict
```

### Verification Interval
Change check frequency in `client/player_client.py`:

```python
self.verification_interval = 30  # seconds between checks
```

## 🔐 Security Features

- **Password Hashing**: bcrypt with 12 salt rounds
- **Session Management**: Secure HTTP-only cookies with 8-hour expiration
- **Rate Limiting**: Protection against brute-force attacks (can be added)
- **Data Encryption**: Facial encodings stored securely
- **Consent-based**: Explicit user consent required for data collection

## 📊 Database Schema

### Players Table
- `player_id` (PRIMARY KEY)
- `name`
- `student_id`
- `facial_encoding` (BLOB)
- `machine_guid`
- `registered_at`

### Admin Users Table
- `id` (PRIMARY KEY)
- `username`
- `email`
- `password_hash`
- `role` (super_admin/tournament_admin)
- `created_at`
- `last_login`
- `is_active`

### Verification Logs Table
- `log_id` (PRIMARY KEY)
- `player_id` (FOREIGN KEY)
- `timestamp`
- `verification_status`
- `confidence_score`
- `image_path`
- `device_matched`

## 🧪 Testing the System

### Test 1: Camera Access
```bash
cd server
python verification.py
```

### Test 2: Device Fingerprinting
```bash
cd server/utils
python device_fingerprint.py
```

### Test 3: Face Recognition
1. Run registration with test data
2. Run verification client
3. Verify face is detected and matched

## 🐛 Troubleshooting

### Issue: Camera not detected
**Solution**: 
- Check camera permissions
- Try different camera index in OpenCV (0, 1, 2)
- Ensure no other application is using the camera

### Issue: Face recognition fails
**Solution**:
- Ensure adequate lighting
- Position face clearly in camera view
- Register with multiple angles during setup
- Adjust tolerance threshold

### Issue: Database errors
**Solution**:
```bash
cd database
rm verification_system.db  # Delete old database
cd ../server
python models.py  # Reinitialize
```

### Issue: Module not found
**Solution**:
```bash
pip install -r requirements.txt --upgrade
```

### Issue: face_recognition installation fails
**Solution**:
- Install cmake first
- Ensure Python development headers are installed
- Try: `pip install dlib` separately first

## 📝 API Endpoints

### Public Endpoints
- `POST /api/register` - Register new player
- `POST /api/verify` - Verify player identity

### Admin Endpoints (Authentication Required)
- `GET /api/players` - Get all registered players
- `GET /api/player/<id>/logs` - Get player verification logs
- `GET /api/logs/recent` - Get recent verification logs
- `GET /api/active_sessions` - Get active verification sessions

### WebSocket Events
- `verification_update` - Real-time verification results
- `player_session_start` - Player started verification
- `player_session_end` - Player stopped verification

## 🔮 Future Enhancements

- Mobile app version for smartphone-based verification
- Machine learning for suspicious pattern detection
- Integration with popular tournament platforms
- Behavioral biometrics (typing patterns, mouse movements)
- Cloud deployment for scalability
- Advanced analytics and reporting
- Multi-camera support
- Voice recognition as additional factor

## 📄 License

This project is for educational and research purposes. Please ensure compliance with privacy laws and regulations in your jurisdiction when deploying.

## 👥 Contributors

Developed for school-based gaming tournament integrity research.

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review server logs: `server/app.py` console output
3. Check client logs in application windows

## 🎓 Academic Use

This system was developed as part of a software engineering research project on anti-cheating mechanisms in online gaming tournaments. When citing this work, please reference the complete system design documentation.

---

**Last Updated**: 2024
**Version**: 1.0.0
**Status**: Research/Educational Implementation
