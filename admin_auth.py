"""
Admin Authentication Module for Guards & Robbers

This module handles the authentication for the admin dashboard.
It provides functions for:
- Creating admin users
- Validating login credentials
- Managing sessions
"""

import os
import sys
import json
import logging
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import request, session, redirect, url_for, flash
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Admin user configuration
ADMIN_FILE = os.getenv('ADMIN_FILE', 'admin_users.json')
SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 3600))  # 1 hour by default

def init_admin_users():
    """Initialize admin users file if it doesn't exist"""
    if not os.path.exists(ADMIN_FILE):
        try:
            # Create a default admin user if none exists
            default_username = os.getenv('DEFAULT_ADMIN_USER', 'admin')
            default_password = os.getenv('DEFAULT_ADMIN_PASSWORD', secrets.token_urlsafe(12))
            
            # Hash password with salt
            salt = secrets.token_hex(16)
            password_hash = hash_password(default_password, salt)
            
            admin_users = {
                default_username: {
                    'password_hash': password_hash,
                    'salt': salt,
                    'created_at': datetime.now().isoformat(),
                    'is_active': True
                }
            }
            
            # Save to file
            with open(ADMIN_FILE, 'w') as f:
                json.dump(admin_users, f, indent=4)
            
            logger.info(f"Created default admin user: {default_username}")
            logger.info(f"Default password: {default_password}")
            logger.info("Please change the default password after first login")
            return True
        except Exception as e:
            logger.error(f"Failed to create admin users file: {e}")
            return False
    return True

def hash_password(password, salt):
    """Hash password with salt using SHA-256"""
    # Combine password and salt, then hash
    password_salt = (password + salt).encode('utf-8')
    return hashlib.sha256(password_salt).hexdigest()

def get_admin_users():
    """Get all admin users"""
    if not os.path.exists(ADMIN_FILE):
        init_admin_users()
    
    try:
        with open(ADMIN_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load admin users: {e}")
        return {}

def authenticate(username, password):
    """Authenticate an admin user"""
    admin_users = get_admin_users()
    
    if username not in admin_users:
        logger.warning(f"Login attempt with unknown username: {username}")
        return False
    
    user = admin_users[username]
    
    if not user.get('is_active', False):
        logger.warning(f"Login attempt with inactive user: {username}")
        return False
    
    # Get stored salt and hash the provided password
    salt = user.get('salt', '')
    password_hash = hash_password(password, salt)
    
    # Compare hashes
    if password_hash == user.get('password_hash', ''):
        logger.info(f"Successful login for user: {username}")
        return True
    
    logger.warning(f"Failed login attempt for user: {username}")
    return False

def create_admin_user(username, password, is_active=True):
    """Create a new admin user"""
    admin_users = get_admin_users()
    
    if username in admin_users:
        logger.warning(f"Admin user already exists: {username}")
        return False
    
    # Generate salt and hash password
    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)
    
    # Create user
    admin_users[username] = {
        'password_hash': password_hash,
        'salt': salt,
        'created_at': datetime.now().isoformat(),
        'is_active': is_active
    }
    
    # Save to file
    try:
        with open(ADMIN_FILE, 'w') as f:
            json.dump(admin_users, f, indent=4)
        logger.info(f"Created admin user: {username}")
        return True
    except Exception as e:
        logger.error(f"Failed to save admin user: {e}")
        return False

def update_admin_password(username, new_password):
    """Update an admin user's password"""
    admin_users = get_admin_users()
    
    if username not in admin_users:
        logger.warning(f"Admin user does not exist: {username}")
        return False
    
    # Generate new salt and hash password
    salt = secrets.token_hex(16)
    password_hash = hash_password(new_password, salt)
    
    # Update user
    admin_users[username]['password_hash'] = password_hash
    admin_users[username]['salt'] = salt
    admin_users[username]['updated_at'] = datetime.now().isoformat()
    
    # Save to file
    try:
        with open(ADMIN_FILE, 'w') as f:
            json.dump(admin_users, f, indent=4)
        logger.info(f"Updated password for admin user: {username}")
        return True
    except Exception as e:
        logger.error(f"Failed to update admin password: {e}")
        return False

def login_required(f):
    """Decorator for routes that require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if not session.get('admin_logged_in', False):
            flash('Please log in to access this page')
            return redirect(url_for('admin_login'))
        
        # Check session timeout
        last_activity = session.get('last_activity', 0)
        if time.time() - last_activity > SESSION_TIMEOUT:
            session.clear()
            flash('Your session has expired. Please log in again')
            return redirect(url_for('admin_login'))
        
        # Update last activity
        session['last_activity'] = time.time()
        
        return f(*args, **kwargs)
    return decorated_function

# Initialize admin users on module load
# We don't initialize on module load to allow for tests to override settings
# init_admin_users() 