from flask import Flask, render_template, request, jsonify
import os
import json
import logging
import sys
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, OperationFailure

# Load environment variables
load_dotenv()

app = Flask(__name__)

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
else:
    logger.warning(f"No valid MongoDB URI provided. MongoDB functionality will be disabled.")

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
            return jsonify({'status': 'error', 'message': 'MongoDB connection not available'}), 503
    except Exception as e:
        logger.error(f"Error counting leads: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin')
def admin_dashboard():
    leads = []
    if mongo_client:
        try:
            leads = list(leads_collection.find().sort('timestamp', -1))
            # Convert ObjectId to string for JSON serialization
            for lead in leads:
                if '_id' in lead:
                    lead['_id'] = str(lead['_id'])
                if 'timestamp' in lead:
                    lead['timestamp'] = lead['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.error(f"Error retrieving leads: {e}")
    
    return render_template('admin_dashboard.html', leads=leads)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 