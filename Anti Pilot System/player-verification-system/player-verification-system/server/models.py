"""
Database models for Player Verification System
"""
import sqlite3
import pickle
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Always resolve path relative to THIS file, not the working directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'verification_system.db')

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create players table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            player_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            student_id TEXT UNIQUE,
            facial_encoding BLOB NOT NULL,
            machine_guid TEXT NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create admin_users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Create verification_logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verification_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verification_status TEXT NOT NULL,
            confidence_score REAL,
            image_path TEXT NOT NULL,
            device_matched BOOLEAN NOT NULL,
            FOREIGN KEY (player_id) REFERENCES players (player_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

class Player:
    """Player model"""
    
    @staticmethod
    def create(player_id, name, student_id, facial_encoding, machine_guid):
        """Create a new player"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Serialize facial encoding
        encoding_blob = pickle.dumps(facial_encoding)
        
        cursor.execute('''
            INSERT INTO players (player_id, name, student_id, facial_encoding, machine_guid)
            VALUES (?, ?, ?, ?, ?)
        ''', (player_id, name, student_id, encoding_blob, machine_guid))
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_by_id(player_id):
        """Get player by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM players WHERE player_id = ?', (player_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'player_id': row['player_id'],
                'name': row['name'],
                'student_id': row['student_id'],
                'facial_encoding': pickle.loads(row['facial_encoding']),
                'machine_guid': row['machine_guid'],
                'registered_at': row['registered_at']
            }
        return None
    
    @staticmethod
    def get_all():
        """Get all players"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT player_id, name, student_id, registered_at FROM players')
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

class AdminUser:
    """Admin user model"""
    
    @staticmethod
    def create(username, email, password, role='tournament_admin'):
        """Create a new admin user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        password_hash = generate_password_hash(password)
        
        try:
            cursor.execute('''
                INSERT INTO admin_users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, role))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    @staticmethod
    def get_by_username(username):
        """Get admin user by username"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admin_users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    @staticmethod
    def verify_password(username, password):
        """Verify admin password"""
        user = AdminUser.get_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None
    
    @staticmethod
    def update_last_login(user_id):
        """Update last login timestamp"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE admin_users 
            SET last_login = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (user_id,))
        conn.commit()
        conn.close()

class VerificationLog:
    """Verification log model"""
    
    @staticmethod
    def create(player_id, verification_status, confidence_score, image_path, device_matched):
        """Create a new verification log"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO verification_logs 
            (player_id, verification_status, confidence_score, image_path, device_matched)
            VALUES (?, ?, ?, ?, ?)
        ''', (player_id, verification_status, confidence_score, image_path, device_matched))
        
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return log_id
    
    @staticmethod
    def get_by_player(player_id, limit=50):
        """Get verification logs for a player"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM verification_logs 
            WHERE player_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (player_id, limit))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_recent(limit=100):
        """Get recent verification logs"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT vl.*, p.name as player_name 
            FROM verification_logs vl
            JOIN players p ON vl.player_id = p.player_id
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

if __name__ == '__main__':
    init_db()