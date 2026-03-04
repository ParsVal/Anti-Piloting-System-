#!/usr/bin/env python3
"""
Admin Account Generator Script
"""
import sys
import os
import argparse
import getpass

# Add server directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))

from models import AdminUser, init_db

def create_admin_account(username, email, password, role):
    """
    Create a new admin account
    
    Args:
        username: Admin username
        email: Admin email
        password: Admin password
        role: Admin role (super_admin or tournament_admin)
    """
    # Validate role
    if role not in ['super_admin', 'tournament_admin']:
        print("Error: Role must be 'super_admin' or 'tournament_admin'")
        return False
    
    # Create account
    user_id = AdminUser.create(username, email, password, role)
    
    if user_id:
        print("\n" + "=" * 60)
        print("✓ Admin Account Created Successfully!")
        print("=" * 60)
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Role: {role}")
        print(f"User ID: {user_id}")
        print("=" * 60)
        print("\nYou can now log in to the admin dashboard at:")
        print("http://localhost:5000/admin/login")
        print("=" * 60)
        return True
    else:
        print("\n✗ Error: Failed to create admin account")
        print("Possible reasons:")
        print("  - Username or email already exists")
        print("  - Database connection error")
        return False

def interactive_mode():
    """Interactive account creation"""
    print("\n" + "=" * 60)
    print("Admin Account Creation - Interactive Mode")
    print("=" * 60)
    
    # Get username
    username = input("\nEnter username: ").strip()
    if not username:
        print("Error: Username cannot be empty")
        return
    
    # Get email
    email = input("Enter email: ").strip()
    if not email or '@' not in email:
        print("Error: Invalid email address")
        return
    
    # Get password
    while True:
        password = getpass.getpass("Enter password: ")
        password_confirm = getpass.getpass("Confirm password: ")
        
        if password != password_confirm:
            print("Error: Passwords do not match. Try again.")
            continue
        
        if len(password) < 6:
            print("Error: Password must be at least 6 characters")
            continue
        
        break
    
    # Get role
    print("\nSelect role:")
    print("  1. Super Admin (full system access)")
    print("  2. Tournament Admin (monitoring only)")
    
    role_choice = input("Enter choice (1 or 2): ").strip()
    
    if role_choice == '1':
        role = 'super_admin'
    elif role_choice == '2':
        role = 'tournament_admin'
    else:
        print("Error: Invalid choice")
        return
    
    # Create account
    create_admin_account(username, email, password, role)

def main():
    parser = argparse.ArgumentParser(
        description='Create admin accounts for Player Verification System'
    )
    
    parser.add_argument(
        '--username',
        help='Admin username'
    )
    
    parser.add_argument(
        '--email',
        help='Admin email address'
    )
    
    parser.add_argument(
        '--password',
        help='Admin password (prompted if not provided)'
    )
    
    parser.add_argument(
        '--role',
        choices=['super_admin', 'tournament_admin'],
        default='tournament_admin',
        help='Admin role (default: tournament_admin)'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Interactive mode'
    )
    
    args = parser.parse_args()
    
    # Initialize database
    print("Initializing database...")
    init_db()
    print("✓ Database ready")
    
    # Interactive mode
    if args.interactive or (not args.username and not args.email):
        interactive_mode()
        return
    
    # Command line mode
    if not args.username or not args.email:
        print("Error: --username and --email are required")
        print("Use --interactive for interactive mode")
        parser.print_help()
        return
    
    # Get password
    if args.password:
        password = args.password
        print("Warning: Providing password via command line is insecure")
    else:
        password = getpass.getpass("Enter password: ")
    
    # Create account
    create_admin_account(args.username, args.email, password, args.role)

if __name__ == '__main__':
    main()
