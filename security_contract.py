"""
Security Contract for Guards & Robbers Application

This module implements security measures that protect developer interests and ensure
proper usage of the application's resources including:
- Authentication and authorization
- Rate limiting for API endpoints
- Access logging and auditing
- Database access controls
"""

import os
import time
import json
import logging
import functools
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import request, jsonify, g
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Security settings
API_KEYS = {}  # Will store {api_key: {client_id, rate_limit, last_reset, request_count}}
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
DEFAULT_RATE_LIMIT = 100  # requests per hour
ADMIN_ROLES = ['admin', 'developer']

# Load API keys from environment or file
def load_api_keys():
    """Load API keys from environment variable or file"""
    api_keys_file = os.getenv('API_KEYS_FILE', 'api_keys.json')
    
    # First try to load from environment
    env_api_keys = os.getenv('API_KEYS')
    if env_api_keys:
        try:
            API_KEYS.update(json.loads(env_api_keys))
            logger.info(f"Loaded {len(API_KEYS)} API keys from environment")
            return
        except json.JSONDecodeError:
            logger.warning("Failed to parse API keys from environment, trying file")
    
    # Then try to load from file
    try:
        if os.path.exists(api_keys_file):
            with open(api_keys_file, 'r') as f:
                API_KEYS.update(json.load(f))
                logger.info(f"Loaded {len(API_KEYS)} API keys from file")
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load API keys: {e}")
        # Create default admin API key if none exist
        if not API_KEYS:
            create_api_key("admin", "admin", DEFAULT_RATE_LIMIT * 5)

def create_api_key(client_id, role, rate_limit=DEFAULT_RATE_LIMIT):
    """Create a new API key"""
    # Generate a secure random API key
    api_key = secrets.token_hex(16)
    
    # Store API key info
    API_KEYS[api_key] = {
        "client_id": client_id,
        "role": role,
        "rate_limit": rate_limit,
        "last_reset": time.time(),
        "request_count": 0,
        "created_at": datetime.now().isoformat()
    }
    
    # Save updated API keys
    save_api_keys()
    
    logger.info(f"Created API key for client '{client_id}' with role '{role}'")
    return api_key

def save_api_keys():
    """Save API keys to file"""
    api_keys_file = os.getenv('API_KEYS_FILE', 'api_keys.json')
    
    try:
        with open(api_keys_file, 'w') as f:
            json.dump(API_KEYS, f, indent=2)
        logger.info(f"Saved {len(API_KEYS)} API keys to file")
    except IOError as e:
        logger.error(f"Failed to save API keys: {e}")

def revoke_api_key(api_key):
    """Revoke an API key"""
    if api_key in API_KEYS:
        client_id = API_KEYS[api_key]["client_id"]
        del API_KEYS[api_key]
        save_api_keys()
        logger.info(f"Revoked API key for client '{client_id}'")
        return True
    return False

def authenticate():
    """Authenticate request using API key"""
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    
    if not api_key:
        logger.warning("Authentication failed: No API key provided")
        return None
    
    if api_key not in API_KEYS:
        logger.warning(f"Authentication failed: Invalid API key")
        return None
    
    client_info = API_KEYS[api_key]
    
    # Check rate limiting
    current_time = time.time()
    if current_time - client_info["last_reset"] > RATE_LIMIT_WINDOW:
        # Reset rate limit counter if window has passed
        client_info["last_reset"] = current_time
        client_info["request_count"] = 0
    
    # Increment request count
    client_info["request_count"] += 1
    
    # Check if rate limit exceeded
    if client_info["request_count"] > client_info["rate_limit"]:
        logger.warning(f"Rate limit exceeded for client '{client_info['client_id']}'")
        return None
    
    # Store client info in Flask g object for access in view functions
    g.client_id = client_info["client_id"]
    g.role = client_info["role"]
    
    # Log access
    logger.info(f"Authenticated request from client '{client_info['client_id']}' with role '{client_info['role']}'")
    
    return client_info

def requires_auth(f):
    """Decorator for requiring authentication"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        client_info = authenticate()
        if not client_info:
            return jsonify({
                "status": "error", 
                "message": "Authentication failed or rate limit exceeded"
            }), 401
        return f(*args, **kwargs)
    return decorated

def requires_role(roles):
    """Decorator for requiring specific roles"""
    def decorator(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            client_info = authenticate()
            if not client_info:
                return jsonify({
                    "status": "error", 
                    "message": "Authentication failed or rate limit exceeded"
                }), 401
            
            if client_info["role"] not in roles:
                logger.warning(f"Access denied: Client '{client_info['client_id']}' with role '{client_info['role']}' attempted to access restricted resource")
                return jsonify({
                    "status": "error", 
                    "message": "Access denied"
                }), 403
                
            return f(*args, **kwargs)
        return decorated
    return decorator

def log_database_access(collection, operation, query=None, document=None, result=None):
    """Log database access for auditing"""
    # Get client info from Flask g if available
    client_id = getattr(g, 'client_id', 'system')
    role = getattr(g, 'role', 'system')
    
    # Create log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "client_id": client_id,
        "role": role,
        "collection": collection,
        "operation": operation
    }
    
    # Add additional info if available
    if query:
        log_entry["query"] = str(query)
    if document:
        # Don't log full document content for privacy
        log_entry["document_id"] = str(document.get("_id", "unknown"))
    if result:
        log_entry["result"] = f"{result}"[:100]  # Truncate long results
    
    # Log to file
    try:
        log_file = os.getenv('DB_ACCESS_LOG', 'db_access.log')
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except IOError as e:
        logger.error(f"Failed to write database access log: {e}")
    
    # Also log via logger
    logger.info(f"DB Access: {operation} on {collection} by {client_id}")

# Initialize security when module is imported
load_api_keys()

# Check for existing API keys, create default if needed
if not API_KEYS:
    default_api_key = create_api_key("admin", "admin", DEFAULT_RATE_LIMIT * 5)
    logger.info(f"Created default admin API key: {default_api_key}") 