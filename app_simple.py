from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file
import os
import json
import logging
import sys
import secrets
import io
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, OperationFailure
from admin_auth import login_required, authenticate, init_admin_users
from PIL import Image, ImageDraw, ImageFont
from utils.email_sender import send_welcome_email
import hashlib
import time
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Set secret key for session management
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))

# Configure MongoDB settings
MONGODB_DB = os.getenv('MONGODB_DB', 'guards_db')
MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', 'leads')
MONGODB_SUBSCRIBERS_COLLECTION = os.getenv('MONGODB_SUBSCRIBERS_COLLECTION', 'subscribers')

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

# MongoDB connection
mongo_uri = os.getenv('MONGODB_URI', '')
try:
    if mongo_uri:
        client = MongoClient(mongo_uri, 
                           ssl=True,
                           ssl_cert_reqs=ssl.CERT_NONE,
                           connectTimeoutMS=30000,
                           socketTimeoutMS=45000)
        db = client.get_database()
        print("Successfully connected to MongoDB")
    else:
        print("No MongoDB URI provided, using in-memory storage")
        db = None
except Exception as e:
    print(f"Failed to connect to MongoDB: {str(e)}")
    print("Falling back to in-memory storage")
    db = None

# Initialize MongoDB client
mongo_client = None
db = None
leads_collection = None
subscribers_collection = None
leads = []
subscribers = []

# Check if we should use MongoDB
USE_MONGODB = os.getenv('USE_MONGODB', 'false').lower() == 'true'

if USE_MONGODB and mongo_uri and ('mongodb://' in mongo_uri or 'mongodb+srv://' in mongo_uri):
    max_retries = 3
    retry_count = 0
    retry_delay = 1
    
    while retry_count < max_retries:
        try:
            # Mask the password in logs
            log_uri = mongo_uri.split('@')[0] + '@...' if '@' in mongo_uri else 'mongodb://...'
            logger.info(f"Attempting to connect to MongoDB (Attempt {retry_count+1}/{max_retries}) with URI: {log_uri}")
            
            # Use a more robust connection setup
            mongo_client = MongoClient(
                mongo_uri,
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
            db = mongo_client[MONGODB_DB]
            leads_collection = db[MONGODB_COLLECTION]
            subscribers_collection = db[MONGODB_SUBSCRIBERS_COLLECTION]
            
            # Configure collection options if needed
            # For example, adding indexes
            leads_collection.create_index([("email", 1)], unique=True)
            subscribers_collection.create_index([("email", 1)], unique=True)
            
            logger.info(f"Successfully connected to MongoDB: {MONGODB_DB}.{MONGODB_COLLECTION}")
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
    try:
        # Try to render the original index.html template
        return render_template('index.html')
    except Exception as e:
        logger.warning(f"Failed to render index.html: {e}")
        
        try:
            # Try to render our simplified template as fallback
            return render_template('index_simple.html')
        except Exception as e2:
            logger.error(f"Failed to render index_simple.html: {e2}")
            
            # Last resort: return inline HTML
            return f"""
            <html>
                <head><title>Guards & Robbers</title></head>
                <body>
                    <h1>Guards & Robbers</h1>
                    <p>Welcome to our marketing website!</p>
                    <p>Template error: {str(e2)}</p>
                    <p>Debug info:</p>
                    <ul>
                        <li>App root: {app.root_path}</li>
                        <li>Templates path: {os.path.join(app.root_path, 'templates')}</li>
                        <li>Path exists: {os.path.exists(os.path.join(app.root_path, 'templates'))}</li>
                        <li>Templates available: {os.listdir(os.path.join(app.root_path, 'templates')) if os.path.exists(os.path.join(app.root_path, 'templates')) else 'None'}</li>
                    </ul>
                </body>
            </html>
            """

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
        "MONGODB_URI": mongo_uri.split('@')[0] + '@...' if mongo_uri and '@' in mongo_uri else "Not set",
        "MONGODB_DB": MONGODB_DB,
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
    dashboard_leads = []
    
    if mongo_client:
        try:
            dashboard_leads = list(leads_collection.find().sort('timestamp', -1))
            # Convert ObjectId to string for JSON serialization
            for lead in dashboard_leads:
                if '_id' in lead:
                    lead['_id'] = str(lead['_id'])
                if 'timestamp' in lead:
                    lead['timestamp'] = lead['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.error(f"Error retrieving leads from MongoDB: {e}")
            # Fall back to in-memory leads
            dashboard_leads = leads
    else:
        # Use in-memory fallback
        dashboard_leads = leads
    
    return render_template('admin_dashboard.html', leads=dashboard_leads, username=session.get('admin_username'))

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
def testimonials():
    """Render the testimonials page"""
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

def load_subscribers():
    try:
        if os.path.exists('subscribers.json'):
            with open('subscribers.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading subscribers: {str(e)}")
    return []

def save_subscribers(subscribers):
    try:
        with open('subscribers.json', 'w', encoding='utf-8') as f:
            json.dump(subscribers, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving subscribers: {str(e)}")

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
        import random
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 