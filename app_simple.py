import os
import sys
import json
import re
import uuid
import random
import datetime
import logging
import time
import math
import csv
import io
import ssl
import secrets
import smtplib
import hashlib
from io import StringIO
from functools import wraps
from urllib.parse import quote_plus
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Third-party imports
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file, make_response
from flask_compress import Compress
from flask_caching import Cache
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, OperationFailure
from PIL import Image, ImageDraw, ImageFont

# Local imports
from admin_auth import login_required, authenticate, init_admin_users
from utils.email_sender import send_welcome_email

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Apply proxy fix for proper client IP behind proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Initialize compression
Compress(app)

# Set secret key for session management
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))

# Setup Flask caching
cache_config = {
    'CACHE_TYPE': os.getenv('CACHE_TYPE', 'SimpleCache'),
    'CACHE_DEFAULT_TIMEOUT': int(os.getenv('CACHE_TIMEOUT', 300)),
}
if os.getenv('REDIS_URL'):
    cache_config['CACHE_TYPE'] = 'RedisCache'
    cache_config['CACHE_REDIS_URL'] = os.getenv('REDIS_URL')

cache = Cache(app, config=cache_config)

# Configure MongoDB settings
mongodb_uri = os.getenv("MONGODB_URI", "")
mongodb_dbname = os.getenv("MONGODB_DBNAME", "guardsAndRobbers")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "leads")
MONGODB_SUBSCRIBERS_COLLECTION = os.getenv("MONGODB_SUBSCRIBERS_COLLECTION", "subscribers")
MONGODB_ADMIN_COLLECTION = os.getenv("MONGODB_ADMIN_COLLECTION", "admins")
mongodb_connected = False

# Make sure admin users are initialized
init_admin_users()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Debug template folder location
logger.info(f"Flask app root path: {app.root_path}")
logger.info(f"Template folder path: {os.path.join(app.root_path, 'templates')}")
logger.info(f"Template folder exists: {os.path.exists(os.path.join(app.root_path, 'templates'))}")
if os.path.exists(os.path.join(app.root_path, 'templates')):
    logger.info(f"Template folder contents: {os.listdir(os.path.join(app.root_path, 'templates'))}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Directory contents: {os.listdir(os.getcwd())}")

# Setup MongoDB connection
try:
    if mongodb_uri and not os.environ.get('DISABLE_MONGODB', '').lower() == 'true':
        # Use the updated parameters for MongoDB client
        ssl_settings = {
            'ssl': True,
            'tls': True,
            'tlsAllowInvalidCertificates': True
        }
        
        client = MongoClient(
            mongodb_uri,
            server_api=ServerApi('1'),
            **ssl_settings
        )
        
        # Test the connection
        try:
            client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            db = client.get_database(mongodb_dbname)
            leads_collection = db[MONGODB_COLLECTION]
            subscribers_collection = db[MONGODB_SUBSCRIBERS_COLLECTION]
            mongodb_connected = True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            mongodb_connected = False
    else:
        logger.warning("MongoDB connection disabled or no valid MongoDB URI provided. Using in-memory storage.")
        mongodb_connected = False
except Exception as e:
    logger.error(f"Failed to setup MongoDB: {e}")
    mongodb_connected = False

# Initialize MongoDB client
mongo_client = None
db = None
leads_collection = None
subscribers_collection = None
leads = []
subscribers = []

# Check if we should use MongoDB
USE_MONGODB = os.getenv('USE_MONGODB', 'false').lower() == 'true'

if USE_MONGODB and mongodb_uri and ('mongodb://' in mongodb_uri or 'mongodb+srv://' in mongodb_uri):
    max_retries = 3
    retry_count = 0
    retry_delay = 1
    
    while retry_count < max_retries:
        try:
            # Mask the password in logs
            log_uri = mongodb_uri.split('@')[0] + '@...' if '@' in mongodb_uri else 'mongodb://...'
            logger.info(f"Attempting to connect to MongoDB (Attempt {retry_count+1}/{max_retries}) with URI: {log_uri}")
            
            # Use a more robust connection setup
            mongo_client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=10000,  # Increased timeout
                connectTimeoutMS=10000,          # Increased timeout
                socketTimeoutMS=15000,           # Increased timeout
                ssl=True,                        # Enable SSL
                tlsAllowInvalidCertificates=True,# Skip certificate validation
                retryWrites=True,                # Enable retry writes
                appname="guards-robbers-app"     # App name
            )
            
            # Test connection with timeout
            mongo_client.admin.command('ping', serverSelectionTimeoutMS=5000)
            db = mongo_client[mongodb_dbname]
            leads_collection = db[MONGODB_COLLECTION]
            subscribers_collection = db[MONGODB_SUBSCRIBERS_COLLECTION]
            
            # Configure collection options if needed
            # For example, adding indexes
            leads_collection.create_index([("email", 1)], unique=True)
            subscribers_collection.create_index([("email", 1)], unique=True)
            
            logger.info(f"Successfully connected to MongoDB: {mongodb_dbname}.{MONGODB_COLLECTION}")
            break  # Exit the retry loop on success
            
        except Exception as e:
            retry_count += 1
            logger.error(f"Failed to connect to MongoDB (Attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count >= max_retries:
                logger.error(f"Maximum retry attempts ({max_retries}) reached. Falling back to local storage.")
                mongo_client = None
                
                # Load any existing leads from JSON file as fallback
                try:
                    json_path = os.getenv('JSON_BACKUP_PATH', 'leads.json')
                    if os.path.exists(json_path):
                        with open(json_path, 'r') as f:
                            for line in f:
                                if line.strip():
                                    leads.append(json.loads(line))
                        logger.info(f"Loaded {len(leads)} leads from local JSON file as fallback")
                except Exception as json_err:
                    logger.error(f"Failed to load leads from JSON file: {json_err}")
            else:
                # Exponential backoff: 1s, 2s, 4s, etc.
                wait_time = retry_delay * (2 ** (retry_count - 1))
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
else:
    logger.warning(f"MongoDB connection disabled or no valid MongoDB URI provided. Using in-memory storage.")
    # Load any existing leads from JSON file
    try:
        json_path = os.getenv('JSON_BACKUP_PATH', 'data/leads.json')
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                for line in f:
                    if line.strip():
                        leads.append(json.loads(line))
            logger.info(f"Loaded {len(leads)} leads from local JSON file")
    except Exception as e:
        logger.error(f"Failed to load leads from JSON file: {e}")
        
    # Initialize subscribers list
    try:
        json_path = 'data/subscribers.json'
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                subscribers = json.load(f)
            logger.info(f"Loaded {len(subscribers)} subscribers from local JSON file")
    except Exception as e:
        logger.error(f"Failed to load subscribers from JSON file: {e}")
        subscribers = []

# Placeholder image generator for testimonials
def generate_placeholder_image(width, height, text, bg_color=(240, 240, 240), text_color=(100, 100, 100)):
    """Generate a placeholder image with text"""
    try:
        # Create a new image with the given background color
        image = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(image)
        
        # Try to use a default font, or use PIL's default if not available
        try:
            font = ImageFont.truetype("arial.ttf", size=width//10)
        except IOError:
            font = ImageFont.load_default()
        
        # Calculate text position to center it
        text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else (width//2, height//2)
        position = ((width - text_width) // 2, (height - text_height) // 2)
        
        # Draw the text
        draw.text(position, text, font=font, fill=text_color)
        
        # Save the image to a BytesIO object
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return img_byte_arr
    except Exception as e:
        logger.error(f"Error generating placeholder image: {e}")
        # Return a simple colored box if image generation fails
        image = Image.new('RGB', (width, height), color=bg_color)
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

@app.route('/static/images/testimonials/<path:filename>')
def placeholder_images(filename):
    """Serve placeholder images if the requested image doesn't exist"""
    file_path = os.path.join(app.root_path, 'static', 'images', 'testimonials', filename)
    
    # If the file exists, serve it directly
    if os.path.exists(file_path):
        return send_file(file_path)
    
    # Otherwise, generate a placeholder image
    if filename.endswith(('.jpg', '.jpeg', '.png')):
        # Extract dimensions from filename if possible (e.g., "avatar-100x100.jpg")
        width, height = 200, 200  # Default size
        
        # Generate different placeholders based on file type
        if 'logo' in filename:
            # Company logo placeholder
            company_name = filename.split('-')[0].title()
            placeholder = generate_placeholder_image(300, 150, company_name, 
                                                 bg_color=(230, 240, 255), 
                                                 text_color=(70, 100, 150))
        elif 'badge' in filename:
            # Badge/certification placeholder
            cert_name = filename.split('-')[0].upper()
            placeholder = generate_placeholder_image(120, 120, cert_name, 
                                                  bg_color=(240, 255, 240), 
                                                  text_color=(60, 120, 60))
        else:
            # Avatar placeholder
            name = filename.split('.')[0].replace('-', ' ').title()
            placeholder = generate_placeholder_image(width, height, name[0].upper(), 
                                                  bg_color=(200, 215, 245), 
                                                  text_color=(60, 80, 120))
        
        return send_file(placeholder, mimetype=f'image/{filename.split(".")[-1]}')
    
    # For any other file type, return a 404
    return "Image not found", 404

@app.route('/')
def index():
    # Make sure OG image exists for social media previews
    og_image_path = os.path.join(app.root_path, 'static', 'images', 'og-image.png')
    if not os.path.exists(og_image_path):
        # Trigger OG image creation via the serve_og_image function
        app.view_functions['serve_og_image']()
    
    return render_template('index.html')

@app.route('/health')
def health():
    mongodb_status = "Not configured"
    
    if mongo_client:
        try:
            # Test MongoDB connection
            mongo_client.admin.command('ping')
            mongodb_status = "Connected"
        except Exception as e:
            mongodb_status = f"Error: {str(e)}"
    
    # Get environment info
    env_info = {
        "MONGODB_URI": mongodb_uri.split('@')[0] + '@...' if mongodb_uri and '@' in mongodb_uri else "Not set",
        "MONGODB_DB": mongodb_dbname,
        "MONGODB_COLLECTION": MONGODB_COLLECTION,
        "JSON_BACKUP_ENABLED": os.getenv('ENABLE_JSON_BACKUP', 'True').lower() == 'true',
        "FLASK_ENV": os.getenv('FLASK_ENV', 'production'),
        "APP_ROOT": app.root_path,
        "TEMPLATES_EXIST": os.path.exists(os.path.join(app.root_path, 'templates')),
    }
    
    if env_info["TEMPLATES_EXIST"]:
        env_info["TEMPLATE_FILES"] = os.listdir(os.path.join(app.root_path, 'templates'))
        
    return {
        "status": "ok", 
        "message": "Application is healthy",
        "environment": env_info,
        "mongodb": mongodb_status,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

# Email configuration
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', '')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '')

def send_email(to, subject, body):
    try:
        if not all([MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD]):
            print("Email configuration incomplete")
            return False
            
        msg = MIMEMultipart()
        msg['From'] = MAIL_DEFAULT_SENDER or MAIL_USERNAME
        msg['To'] = to
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
        server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {to}")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

@app.route('/submit_lead', methods=['POST'])
def submit_lead():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        message = data.get('message', '').strip()
        
        if not all([name, email, phone]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({'error': 'Invalid email format'}), 400
            
        # Validate phone format (basic validation)
        if not re.match(r"^\+?[\d\s-]{8,}$", phone):
            return jsonify({'error': 'Invalid phone format'}), 400
            
        # Store lead in database
        lead = {
            'name': name,
            'email': email,
            'phone': phone,
            'message': message,
            'timestamp': datetime.utcnow(),
            'status': 'new'
        }
        
        if db:
            leads_collection.insert_one(lead)
        else:
            leads.append(lead)
            
        # Send confirmation email to lead
        confirmation_subject = "Thank you for your interest!"
        confirmation_body = f"""
        <html>
            <body>
                <h2>Thank you for contacting us!</h2>
                <p>Dear {name},</p>
                <p>We have received your message and will get back to you shortly.</p>
                <p>Best regards,<br>Guards & Robbers Team</p>
            </body>
        </html>
        """
        send_email(email, confirmation_subject, confirmation_body)
        
        # Send notification to admin
        if ADMIN_EMAIL:
            admin_subject = f"New Lead: {name}"
            admin_body = f"""
            <html>
                <body>
                    <h2>New Lead Received</h2>
                    <p><strong>Name:</strong> {name}</p>
                    <p><strong>Email:</strong> {email}</p>
                    <p><strong>Phone:</strong> {phone}</p>
                    <p><strong>Message:</strong> {message}</p>
                </body>
            </html>
            """
            send_email(ADMIN_EMAIL, admin_subject, admin_body)
            
        return jsonify({'message': 'Lead submitted successfully'}), 200
        
    except Exception as e:
        print(f"Error processing lead: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/leads/count', methods=['GET'])
def leads_count():
    try:
        if mongo_client:
            count = leads_collection.count_documents({})
            return jsonify({'status': 'success', 'count': count}), 200
        else:
            # Use in-memory fallback
            return jsonify({'status': 'success', 'count': len(leads), 'source': 'memory'}), 200
    except Exception as e:
        logger.error(f"Error counting leads: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if authenticate(username, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['last_activity'] = datetime.now().timestamp()
            flash('Login successful!')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    # Get filter parameters from request
    search_query = request.args.get('q', '')
    status_filter = request.args.get('status', 'all')
    sort_by = request.args.get('sort_by', 'timestamp')
    sort_order = request.args.get('sort_order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Define available statuses
    statuses = ['new', 'contacted', 'qualified', 'converted', 'rejected', 'closed']
    
    dashboard_leads = []
    total_count = 0
    today_leads_count = 0
    status_counts = []
    trend_data = []
    conversion_rate = 0
    avg_response_time = 'N/A'
    
    # Calculate today's date (for today's leads count)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate dates for trend analysis (last 30 days)
    trend_start_date = today - timedelta(days=29)
    date_range = [(trend_start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
    
    try:
        if mongo_client:
            # Build the filter query
            query = {}
            
            # Add search query if provided
            if search_query:
                query['$or'] = [
                    {'name': {'$regex': search_query, '$options': 'i'}},
                    {'email': {'$regex': search_query, '$options': 'i'}},
                    {'phone': {'$regex': search_query, '$options': 'i'}},
                    {'message': {'$regex': search_query, '$options': 'i'}}
                ]
            
            # Add status filter if not 'all'
            if status_filter != 'all':
                query['status'] = status_filter
            
            # Get total count and today's leads count
            total_count = leads_collection.count_documents(query)
            today_query = query.copy()
            today_query['timestamp'] = {'$gte': today}
            today_leads_count = leads_collection.count_documents(today_query)
            
            # Calculate status distribution
            for status in statuses:
                status_query = query.copy()
                status_query['status'] = status
                count = leads_collection.count_documents(status_query)
                status_counts.append({'status': status.title(), 'count': count})
            
            # Calculate conversion rate (converted / total * 100)
            converted_count = leads_collection.count_documents({'status': 'converted'})
            if total_count > 0:
                conversion_rate = round((converted_count / total_count) * 100, 1)
            
            # Calculate lead acquisition trend (last 30 days)
            for date_str in date_range:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                next_date = date_obj + timedelta(days=1)
                trend_query = {'timestamp': {'$gte': date_obj, '$lt': next_date}}
                daily_count = leads_collection.count_documents(trend_query)
                trend_data.append({'date': date_str, 'count': daily_count})
            
            # Determine sort direction
            sort_direction = -1 if sort_order == 'desc' else 1
            
            # Get paginated leads
            skip_count = (page - 1) * per_page
            dashboard_leads = list(leads_collection.find(query)
                                  .sort(sort_by, sort_direction)
                                  .skip(skip_count)
                                  .limit(per_page))
            
            # Convert ObjectId to string for JSON serialization
            for lead in dashboard_leads:
                if '_id' in lead:
                    lead['_id'] = str(lead['_id'])
                if 'timestamp' in lead:
                    lead['timestamp'] = lead['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        else:
            # In-memory filtering and sorting for fallback
            all_leads = leads.copy()
            filtered_leads = []
            
            # Filter leads
            for lead in all_leads:
                match = True
                
                # Apply search query filter
                if search_query:
                    search_text = f"{lead.get('name', '')} {lead.get('email', '')} {lead.get('phone', '')} {lead.get('message', '')}"
                    if search_query.lower() not in search_text.lower():
                        match = False
                
                # Apply status filter
                if status_filter != 'all' and lead.get('status') != status_filter:
                    match = False
                
                if match:
                    filtered_leads.append(lead)
            
            # Count today's leads
            today_leads_count = sum(1 for lead in all_leads if lead.get('timestamp', datetime.min) >= today)
            
            # Get total count
            total_count = len(filtered_leads)
            
            # Calculate status distribution
            for status in statuses:
                count = sum(1 for lead in all_leads if lead.get('status') == status)
                status_counts.append({'status': status.title(), 'count': count})
            
            # Calculate conversion rate (converted / total * 100)
            converted_count = sum(1 for lead in all_leads if lead.get('status') == 'converted')
            if len(all_leads) > 0:
                conversion_rate = round((converted_count / len(all_leads)) * 100, 1)
            
            # Calculate lead acquisition trend (last 30 days)
            for date_str in date_range:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                next_date = date_obj + timedelta(days=1)
                daily_count = sum(1 for lead in all_leads if 
                                 'timestamp' in lead and 
                                 date_obj <= lead['timestamp'] < next_date)
                trend_data.append({'date': date_str, 'count': daily_count})
            
            # Sort leads
            sort_reverse = sort_order == 'desc'
            filtered_leads.sort(key=lambda x: x.get(sort_by, ''), reverse=sort_reverse)
            
            # Paginate leads
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            dashboard_leads = filtered_leads[start_idx:end_idx]
    
    except Exception as e:
        logger.error(f"Error retrieving leads: {e}")
        flash('Error retrieving leads', 'danger')
    
    # Calculate pagination values
    total_pages = (total_count + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    return render_template('admin_dashboard.html', 
                          leads=dashboard_leads,
                          username=session.get('admin_username'),
                          search_query=search_query,
                          status_filter=status_filter,
                          statuses=statuses,
                          sort_by=sort_by,
                          sort_order=sort_order,
                          page=page,
                          per_page=per_page,
                          total_count=total_count,
                          total_pages=total_pages,
                          has_prev=has_prev,
                          has_next=has_next,
                          today_leads_count=today_leads_count,
                          status_counts=status_counts,
                          trend_data=trend_data,
                          conversion_rate=conversion_rate,
                          avg_response_time=avg_response_time)

@app.route('/admin/settings')
@login_required
def admin_settings():
    return render_template('admin_settings.html', username=session.get('admin_username'))

@app.route('/admin/change-password', methods=['POST'])
@login_required
def admin_change_password():
    from admin_auth import update_admin_password
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    username = session.get('admin_username')
    
    if not all([current_password, new_password, confirm_password]):
        flash('All fields are required')
        return redirect(url_for('admin_settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match')
        return redirect(url_for('admin_settings'))
    
    if not authenticate(username, current_password):
        flash('Current password is incorrect')
        return redirect(url_for('admin_settings'))
    
    if update_admin_password(username, new_password):
        flash('Password updated successfully')
    else:
        flash('Failed to update password')
    
    return redirect(url_for('admin_settings'))

@app.route('/testimonials')
@cache.cached(timeout=3600)  # Cache for 1 hour
def testimonials():
    # Make sure OG image exists for social media previews
    og_image_path = os.path.join(app.root_path, 'static', 'images', 'og-image.png')
    if not os.path.exists(og_image_path):
        # Trigger OG image creation via the serve_og_image function
        app.view_functions['serve_og_image']()
        
    return render_template('testimonials.html')

@app.route('/subscribers/count', methods=['GET'])
@login_required
def subscribers_count():
    """Get count of newsletter subscribers"""
    try:
        if mongo_client:
            count = subscribers_collection.count_documents({})
            return jsonify({'status': 'success', 'count': count}), 200
        else:
            # Use in-memory fallback
            return jsonify({'status': 'success', 'count': len(subscribers), 'source': 'memory'}), 200
    except Exception as e:
        logger.error(f"Error counting subscribers: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/confirm-subscription')
def confirm_subscription():
    email = request.args.get('email')
    token = request.args.get('token')
    
    if not email or not token:
        return render_template('subscription_confirmed.html', error="Invalid confirmation link")
    
    # Validate token here (simplified for example)
    try:
        # Find the subscriber in MongoDB
        if mongo_uri and subscribers_collection:
            subscriber = subscribers_collection.find_one({"email": email})
            if subscriber:
                # Update confirmation status
                subscribers_collection.update_one(
                    {"email": email},
                    {"$set": {"confirmed": True, "confirmed_at": datetime.now().isoformat()}}
                )
                
                # Log successful confirmation
                logger.info(f"Subscription confirmed for: {email}")
                return render_template('subscription_confirmed.html', success=True)
            else:
                logger.warning(f"Confirmation attempted for unknown email: {email}")
                return render_template('subscription_confirmed.html', error="Email not found in our records")
        else:
            # Fallback to local storage
            with open('data/subscribers.json', 'r') as f:
                subscribers = json.load(f)
                
            updated = False
            for subscriber in subscribers:
                if subscriber.get('email') == email:
                    subscriber['confirmed'] = True
                    subscriber['confirmed_at'] = datetime.now().isoformat()
                    updated = True
                    break
                    
            if updated:
                with open('data/subscribers.json', 'w') as f:
                    json.dump(subscribers, f, indent=2)
                logger.info(f"Subscription confirmed locally for: {email}")
                return render_template('subscription_confirmed.html', success=True)
            else:
                logger.warning(f"Confirmation attempted for unknown email: {email}")
                return render_template('subscription_confirmed.html', error="Email not found in our records")
                
    except Exception as e:
        logger.error(f"Error confirming subscription: {str(e)}")
        return render_template('subscription_confirmed.html', error="An error occurred processing your request")

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    email = request.args.get('email') or request.form.get('email')
    token = request.args.get('token') or request.form.get('token')
    
    if not email or not token:
        return render_template('unsubscribe.html', error="Invalid unsubscribe link")
    
    if request.method == 'POST':
        # Process unsubscribe request
        reason = request.form.get('reason')
        other_reason = request.form.get('other_reason')
        
        try:
            if mongo_uri and subscribers_collection:
                # Log the unsubscribe reason
                if reason:
                    subscribers_collection.update_one(
                        {"email": email},
                        {"$set": {
                            "unsubscribed": True, 
                            "unsubscribed_at": datetime.now().isoformat(),
                            "unsubscribe_reason": reason,
                            "unsubscribe_other_reason": other_reason if reason == "other" else ""
                        }}
                    )
                
                # Remove or mark as unsubscribed
                subscribers_collection.update_one(
                    {"email": email},
                    {"$set": {"active": False, "unsubscribed": True}}
                )
                
                logger.info(f"User unsubscribed: {email}, reason: {reason}")
                return render_template('unsubscribe.html', success=True)
            else:
                # Fallback to local storage
                with open('data/subscribers.json', 'r') as f:
                    subscribers = json.load(f)
                    
                updated = False
                for subscriber in subscribers:
                    if subscriber.get('email') == email:
                        subscriber['active'] = False
                        subscriber['unsubscribed'] = True
                        subscriber['unsubscribed_at'] = datetime.now().isoformat()
                        subscriber['unsubscribe_reason'] = reason
                        if reason == "other":
                            subscriber['unsubscribe_other_reason'] = other_reason
                        updated = True
                        break
                        
                if updated:
                    with open('data/subscribers.json', 'w') as f:
                        json.dump(subscribers, f, indent=2)
                    logger.info(f"User unsubscribed locally: {email}, reason: {reason}")
                    return render_template('unsubscribe.html', success=True)
                else:
                    logger.warning(f"Unsubscribe attempted for unknown email: {email}")
                    return render_template('unsubscribe.html', error="Email not found in our records")
                    
        except Exception as e:
            logger.error(f"Error processing unsubscribe: {str(e)}")
            return render_template('unsubscribe.html', error="An error occurred processing your request")
    
    # Display unsubscribe confirmation form
    return render_template('unsubscribe.html', email=email, token=token)

@app.route('/admin/subscribers/count')
@login_required
def count_subscribers():
    try:
        if mongo_uri and subscribers_collection:
            # Count active confirmed subscribers
            count = subscribers_collection.count_documents({"active": True, "confirmed": True})
            return jsonify({'success': True, 'count': count})
        else:
            # Fallback to local storage
            try:
                with open('data/subscribers.json', 'r') as f:
                    subscribers = json.load(f)
                    
                # Count active confirmed subscribers
                count = sum(1 for s in subscribers if s.get('active', False) and s.get('confirmed', False))
                return jsonify({'success': True, 'count': count})
            except Exception as e:
                logger.error(f"Error counting local subscribers: {str(e)}")
                return jsonify({'success': False, 'message': 'Error counting subscribers'}), 500
    except Exception as e:
        logger.error(f"Error counting subscribers: {str(e)}")
        return jsonify({'success': False, 'message': 'Error counting subscribers'}), 500

def load_subscribers_from_json():
    try:
        subscribers_file = os.path.join(app.root_path, 'data', 'subscribers.json')
        if os.path.exists(subscribers_file):
            try:
                with open(subscribers_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except UnicodeDecodeError:
                # Try with different encodings if UTF-8 fails
                with open(subscribers_file, 'r', encoding='latin-1') as f:
                    return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Failed to load subscribers from JSON file: {e}")
        return []

def save_subscribers_to_json(subscribers):
    try:
        os.makedirs(os.path.join(app.root_path, 'data'), exist_ok=True)
        subscribers_file = os.path.join(app.root_path, 'data', 'subscribers.json')
        with open(subscribers_file, 'w', encoding='utf-8') as f:
            json.dump(subscribers, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save subscribers to JSON file: {e}")

def process_message(message):
    try:
        # Preprocess the message
        message = message.lower().strip()
        
        # Check for common greetings
        greetings = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        if any(greeting in message for greeting in greetings):
            return "Hello! How can I help you today?"
            
        # Check for common questions
        questions = {
            'what is guards and robbers': 'Guards & Robbers is a cybersecurity company that helps protect businesses from digital threats.',
            'what services do you offer': 'We offer a range of cybersecurity services including network security, threat detection, and incident response.',
            'how can i contact you': 'You can contact us through our website form or email us at info@guardsandrobbers.com',
            'what are your prices': 'Our pricing depends on your specific needs. Please contact us for a customized quote.',
            'do you offer free consultation': 'Yes, we offer a free initial consultation to assess your security needs.',
            'security': 'Security is our top priority. We offer comprehensive security solutions for businesses of all sizes.',
            'network': 'We provide network security solutions including firewall setup, VPN configuration, and intrusion detection systems.',
            'incident': 'Our incident response team is available 24/7 to help you manage and recover from security incidents.',
            'threat': 'We offer threat detection and prevention services to identify and mitigate potential security risks.',
            'assessment': 'Our security assessment services help identify vulnerabilities in your systems before they can be exploited.',
            'training': 'We provide security awareness training for your employees to help prevent social engineering attacks.',
            'compliance': 'We can help your business achieve and maintain compliance with industry regulations like GDPR, HIPAA, and PCI DSS.',
            'malware': 'Our anti-malware solutions protect your systems from viruses, ransomware, and other malicious software.',
            'data protection': 'We offer data protection services including encryption, backup solutions, and secure data storage.',
            'cloud security': 'Our cloud security services ensure your cloud-based applications and data remain protected.'
        }
        
        # Check if any question keywords are in the message
        for key, value in questions.items():
            if key in message:
                return value
                
        # Fallback responses when no match is found
        fallback_responses = [
            "I understand you're asking about that. Could you please provide more details?",
            "That's an interesting question. Let me get back to you with more information.",
            "I'd be happy to help with that. Please contact our team for personalized assistance.",
            "Thank you for your question. We'll have our experts answer that for you soon.",
            "For more specific information on that topic, please email us at info@guardsandrobbers.com"
        ]
        return random.choice(fallback_responses)
            
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        return "I'm sorry, I encountered an error. Please try again."

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
            
        response = process_message(message)
        return jsonify({'response': response}), 200
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Add headers to all responses
@app.after_request
def add_header(response):
    # Cache static resources for 1 week
    if request.path.startswith('/static'):
        if '.css' in request.path or '.js' in request.path:
            cache_timeout = 604800  # 1 week in seconds
            response.headers['Cache-Control'] = f'public, max-age={cache_timeout}'
        elif '.png' in request.path or '.jpg' in request.path or '.svg' in request.path or '.ico' in request.path:
            cache_timeout = 2592000  # 30 days in seconds
            response.headers['Cache-Control'] = f'public, max-age={cache_timeout}'
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    return response

# Cache static assets when in production
USE_MINIFIED_ASSETS = os.getenv('USE_MINIFIED_ASSETS', 'false').lower() == 'true'

@app.context_processor
def inject_asset_paths():
    """Add asset path helpers to template context"""
    def css_url(filename):
        if USE_MINIFIED_ASSETS and filename == 'styles.css':
            return url_for('static', filename='dist/styles.min.css')
        return url_for('static', filename=f'css/{filename}')
    
    def js_url(filename):
        if USE_MINIFIED_ASSETS and filename == 'script.js':
            return url_for('static', filename='dist/script.min.js')
        return url_for('static', filename=f'js/{filename}')
        
    return dict(css_url=css_url, js_url=js_url)

@app.route('/admin/export-leads')
@login_required
def export_leads():
    """Export leads as CSV or JSON"""
    file_format = request.args.get('format', 'csv').lower()
    search_query = request.args.get('q', '')
    status_filter = request.args.get('status', 'all')
    
    try:
        # Build filter query
        query = {}
        
        # Add search query if provided
        if search_query:
            if mongo_client:
                query['$or'] = [
                    {'name': {'$regex': search_query, '$options': 'i'}},
                    {'email': {'$regex': search_query, '$options': 'i'}},
                    {'phone': {'$regex': search_query, '$options': 'i'}},
                    {'message': {'$regex': search_query, '$options': 'i'}}
                ]
        
        # Add status filter if not 'all'
        if status_filter != 'all':
            query['status'] = status_filter
        
        # Get leads based on filters
        if mongo_client:
            # MongoDB data source
            export_leads = list(leads_collection.find(query).sort('timestamp', -1))
            # Convert ObjectId to string for JSON serialization
            for lead in export_leads:
                if '_id' in lead:
                    lead['_id'] = str(lead['_id'])
                if 'timestamp' in lead and isinstance(lead['timestamp'], datetime):
                    lead['timestamp'] = lead['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        else:
            # In-memory data source
            export_leads = []
            for lead in leads:
                match = True
                
                # Apply search query filter
                if search_query:
                    search_text = f"{lead.get('name', '')} {lead.get('email', '')} {lead.get('phone', '')} {lead.get('message', '')}"
                    if search_query.lower() not in search_text.lower():
                        match = False
                
                # Apply status filter
                if status_filter != 'all' and lead.get('status') != status_filter:
                    match = False
                
                if match:
                    export_leads.append(lead)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"leads_export_{timestamp}"
        
        if file_format == 'json':
            # Export as JSON
            response_data = json.dumps(export_leads, indent=2)
            mimetype = 'application/json'
            attachment_filename = f"{filename}.json"
        else:
            # Default: Export as CSV
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header row
            csv_columns = ['name', 'email', 'phone', 'message', 'status', 'timestamp']
            writer.writerow(csv_columns)
            
            # Write data rows
            for lead in export_leads:
                row = [lead.get(col, '') for col in csv_columns]
                writer.writerow(row)
            
            response_data = output.getvalue()
            mimetype = 'text/csv'
            attachment_filename = f"{filename}.csv"
        
        # Create response
        response = app.response_class(
            response=response_data,
            mimetype=mimetype
        )
        response.headers.set('Content-Disposition', f'attachment; filename={attachment_filename}')
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting leads: {e}")
        flash('Error exporting leads', 'danger')
        return redirect(url_for('admin_dashboard'))
        
@app.route('/admin/update-lead-status', methods=['POST'])
@login_required
def update_lead_status():
    """Update the status of a lead"""
    lead_id = request.form.get('lead_id')
    new_status = request.form.get('status')
    
    if not lead_id or not new_status:
        flash('Missing required fields', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        if mongo_client:
            # Convert string ID to ObjectId for MongoDB
            from bson.objectid import ObjectId
            result = leads_collection.update_one(
                {'_id': ObjectId(lead_id)},
                {'$set': {
                    'status': new_status,
                    'updated_at': datetime.now()
                }}
            )
            
            if result.modified_count > 0:
                flash(f'Lead status updated to {new_status}', 'success')
            else:
                flash('No changes made to lead status', 'warning')
        else:
            # In-memory fallback
            updated = False
            for lead in leads:
                if str(lead.get('_id', '')) == lead_id:
                    lead['status'] = new_status
                    lead['updated_at'] = datetime.now()
                    updated = True
                    break
            
            if updated:
                # Save to JSON file if available
                if os.getenv('ENABLE_JSON_BACKUP', 'True').lower() == 'true':
                    json_path = os.getenv('JSON_BACKUP_PATH', 'data/leads.json')
                    os.makedirs(os.path.dirname(json_path), exist_ok=True)
                    with open(json_path, 'w') as f:
                        for lead_data in leads:
                            json.dump(lead_data, f)
                            f.write('\n')
                
                flash(f'Lead status updated to {new_status}', 'success')
            else:
                flash('Lead not found', 'danger')
    
    except Exception as e:
        logger.error(f"Error updating lead status: {e}")
        flash('Error updating lead status', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/static/images/og-image.png')
def serve_og_image():
    """Serve the Open Graph image, generating it if it doesn't exist"""
    image_path = os.path.join(app.root_path, 'static', 'images', 'og-image.png')
    
    if not os.path.exists(image_path):
        # Create a simple OG image if it doesn't exist
        width, height = 1200, 630
        image = Image.new('RGB', (width, height), color=(10, 25, 50))
        draw = ImageDraw.Draw(image)
        
        # Add simple blocks of color
        draw.rectangle([(0, 0), (width, height//3)], fill=(0, 30, 70))
        draw.rectangle([(0, height//3), (width, 2*height//3)], fill=(10, 40, 100))
        draw.rectangle([(0, 2*height//3), (width, height)], fill=(20, 60, 130))
        
        # Get a font - try several alternatives
        font_large = None
        font_small = None
        
        # List of fonts to try, from most preferred to default
        font_paths = [
            "arial.ttf",
            "Arial.ttf", 
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
        
        # Try to load a font
        for font_path in font_paths:
            try:
                font_large = ImageFont.truetype(font_path, 60)
                font_small = ImageFont.truetype(font_path, 40)
                logger.info(f"Successfully loaded font: {font_path}")
                break
            except (IOError, OSError):
                continue
                
        # If no fonts loaded successfully, use default
        if font_large is None:
            logger.warning("Could not load any fonts, using default")
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
            
        # Draw the text - be careful with text positioning
        draw.text((width//10, height//4), "GUARDS & ROBBERS", fill=(255, 255, 255), font=font_large)
        draw.text((width//10, height//2), "AI-Powered Cybersecurity", fill=(200, 220, 255), font=font_small)
        
        # Save the image
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        try:
            image.save(image_path, "PNG")
            logger.info(f"Successfully created OG image at {image_path}")
        except Exception as e:
            logger.error(f"Failed to save OG image: {e}")
            # Return a placeholder image if we can't save
            response = make_response(image.tobytes())
            response.headers.set('Content-Type', 'image/png')
            return response
    
    return send_file(image_path, mimetype='image/png')

@app.route('/generate-og-image')
def generate_og_image():
    """Generate Open Graph image for social media previews"""
    try:
        # Define image dimensions (standard OG size)
        width, height = 1200, 630
        
        # Create image with dark background
        image = Image.new('RGB', (width, height), color=(18, 18, 18))
        draw = ImageDraw.Draw(image)
        
        # Simple background with blocks of color
        # Top block (dark blue)
        draw.rectangle([(0, 0), (width, height//3)], fill=(0, 40, 90))
        
        # Middle block (medium blue)
        draw.rectangle([(0, height//3), (width, 2*height//3)], fill=(10, 50, 120))
        
        # Bottom block (lighter blue with gradient effect)
        for i in range(10):
            y_start = 2*height//3 + (i * (height//3)//10)
            y_end = 2*height//3 + ((i+1) * (height//3)//10)
            blue_val = 120 + (i * 10)
            draw.rectangle([(0, y_start), (width, y_end)], fill=(20, 80, blue_val))
        
        # Get a font - try several alternatives
        logo_font = None
        title_font = None
        subtitle_font = None
        
        # List of fonts to try, from most preferred to default
        font_paths = [
            "arial.ttf",
            "Arial.ttf", 
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
        
        # Try to load a font
        for font_path in font_paths:
            try:
                logo_font = ImageFont.truetype(font_path, 60)
                title_font = ImageFont.truetype(font_path, 72)
                subtitle_font = ImageFont.truetype(font_path, 36)
                logger.info(f"Successfully loaded font: {font_path}")
                break
            except (IOError, OSError):
                continue
                
        # If no fonts loaded successfully, use default
        if logo_font is None:
            logger.warning("Could not load any fonts, using default")
            logo_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # Add text
        logo_text = "GUARDS & ROBBERS"
        title_text = "AI-Powered Cybersecurity"
        subtitle_text = "Outsmart threats. Secure your network."
        
        # Position text (simple fixed positions)
        draw.text((width//6, height//4), logo_text, fill=(130, 180, 255), font=logo_font)
        draw.text((width//6, height//2 - 30), title_text, fill=(255, 255, 255), font=title_font)
        draw.text((width//6, height//2 + 60), subtitle_text, fill=(220, 220, 220), font=subtitle_font)
        
        # Save the image
        image_path = os.path.join(app.root_path, 'static', 'images', 'og-image.png')
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        
        try:
            image.save(image_path, "PNG")
            logger.info(f"Successfully created OG image at {image_path}")
            return jsonify({"status": "success", "message": "OG image generated successfully"}), 200
        except Exception as e:
            logger.error(f"Failed to save OG image: {e}")
            return jsonify({"status": "error", "message": f"Failed to save image: {str(e)}"}), 500
        
    except Exception as e:
        logger.error(f"Error generating OG image: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/og-image-template')
def og_image_template():
    """Template for creating the Open Graph image"""
    return render_template('og_image_template.html')

# Initialize in-memory storage as a fallback
SUBSCRIBERS = []
if not mongodb_connected:
    # Load subscribers from JSON file if MongoDB is not available
    SUBSCRIBERS = load_subscribers_from_json()

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email', '').strip().lower()
    name = request.form.get('name', '').strip()
    
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'success': False, 'message': 'Please enter a valid email address'}), 400
    
    subscriber = {
        'email': email,
        'name': name,
        'subscription_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'unsubscribe_token': str(uuid.uuid4())
    }
    
    # If MongoDB is connected, save to database
    if mongodb_connected:
        try:
            try:
                result = subscribers_collection.update_one(
                    {'email': email},
                    {'$set': subscriber},
                    upsert=True
                )
                
                if result.modified_count > 0 or result.upserted_id:
                    logger.info(f"Subscriber saved to MongoDB: {email}")
                else:
                    logger.warning(f"Failed to save subscriber to MongoDB: {email}")
            except Exception as e:
                error_message = str(e)
                logger.error(f"Error updating subscriber in MongoDB: {error_message}")
                
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error saving to MongoDB: {error_message}")
    # Otherwise save to in-memory list and JSON file
    else:
        try:
            # Check if email already exists
            existing = False
            for i, sub in enumerate(SUBSCRIBERS):
                if sub['email'] == email:
                    # Update existing subscriber
                    SUBSCRIBERS[i] = subscriber
                    existing = True
                    break
            
            if not existing:
                SUBSCRIBERS.append(subscriber)
            
            # Save to JSON file
            save_subscribers_to_json(SUBSCRIBERS)
            logger.info(f"Subscriber saved to JSON: {email}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
    
    # Send welcome email
    try:
        result = send_welcome_email(email, name, subscriber['unsubscribe_token'])
        if result:
            logger.info(f"Welcome email sent to {email}")
        else:
            logger.warning(f"Failed to send welcome email to {email}")
    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")
    
    return jsonify({'success': True, 'message': 'Thank you for subscribing!'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 