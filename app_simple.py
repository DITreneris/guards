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

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Set secret key for session management
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))

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
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGODB_DB = os.getenv('MONGODB_DB', 'guards_robbers_db')
MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', 'leads')

# Initialize MongoDB client
mongo_client = None
db = None
leads_collection = None
leads = []  # In-memory fallback for leads when MongoDB is not available

# Only attempt MongoDB connection if URI is provided and looks valid
if MONGODB_URI and ('mongodb://' in MONGODB_URI or 'mongodb+srv://' in MONGODB_URI):
    try:
        # Mask the password in logs
        log_uri = MONGODB_URI.split('@')[0] + '@...' if '@' in MONGODB_URI else 'mongodb://...'
        logger.info(f"Attempting to connect to MongoDB with URI: {log_uri}")
        
        # Use a more tolerant connection setup
        mongo_client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            # Skip server certificate validation for now
            tlsAllowInvalidCertificates=True,
            # Use the latest driver version compatible with Atlas
            appname="guards-robbers-app"
        )
        
        # Test connection
        mongo_client.admin.command('ping')
        db = mongo_client[MONGODB_DB]
        leads_collection = db[MONGODB_COLLECTION]
        logger.info(f"Connected to MongoDB: {MONGODB_DB}.{MONGODB_COLLECTION}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
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
        except Exception as e:
            logger.error(f"Failed to load leads from JSON file: {e}")
else:
    logger.warning(f"No valid MongoDB URI provided. Using local JSON storage instead.")
    # Load any existing leads from JSON file
    try:
        json_path = os.getenv('JSON_BACKUP_PATH', 'leads.json')
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                for line in f:
                    if line.strip():
                        leads.append(json.loads(line))
            logger.info(f"Loaded {len(leads)} leads from local JSON file")
    except Exception as e:
        logger.error(f"Failed to load leads from JSON file: {e}")

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
        "MONGODB_URI": MONGODB_URI.split('@')[0] + '@...' if MONGODB_URI and '@' in MONGODB_URI else "Not set",
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

@app.route('/submit-lead', methods=['POST'])
def submit_lead():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['company', 'name', 'email', 'network']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400
        
        # Create lead document
        lead_document = {
            **data,
            'status': 'New Lead',
            'timestamp': datetime.now()
        }
        
        # Local JSON backup
        if os.getenv('ENABLE_JSON_BACKUP', 'True').lower() == 'true':
            json_path = os.getenv('JSON_BACKUP_PATH', 'leads.json')
            with open(json_path, 'a') as f:
                backup_data = {**lead_document, 'timestamp': lead_document['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
                f.write(json.dumps(backup_data) + '\n')
                
            # Also add to in-memory list with string timestamp
            memory_data = {**lead_document, 'timestamp': lead_document['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
            leads.append(memory_data)
            logger.info(f"Lead saved to local JSON file: {json_path}")
        
        # Add to MongoDB
        if mongo_client:
            try:
                result = leads_collection.insert_one(lead_document)
                logger.info(f"Lead saved to MongoDB with ID: {result.inserted_id}")
                return jsonify({'status': 'success', 'message': 'Lead submitted successfully!'}), 200
            except Exception as e:
                logger.error(f"Error saving to MongoDB: {e}")
                if os.getenv('ENABLE_JSON_BACKUP', 'True').lower() == 'true':
                    return jsonify({'status': 'success', 'message': 'Lead saved locally. MongoDB operation failed.'}), 200
                else:
                    return jsonify({'status': 'error', 'message': 'Database connection failed and local backup is disabled.'}), 500
        elif os.getenv('ENABLE_JSON_BACKUP', 'True').lower() == 'true':
            logger.warning("MongoDB client not available. Lead saved to local file only.")
            return jsonify({'status': 'success', 'message': 'Lead saved locally. MongoDB integration not available.'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Database connection failed and local backup is disabled.'}), 500
            
    except Exception as e:
        logger.error(f"Error submitting lead: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 