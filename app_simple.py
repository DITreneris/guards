from flask import Flask, render_template, request, jsonify
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGODB_DB = os.getenv('MONGODB_DB', 'guards_robbers_db')
MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', 'leads')

# Initialize MongoDB client
mongo_client = None
try:
    mongo_client = MongoClient(MONGODB_URI)
    # Test connection
    mongo_client.admin.command('ping')
    db = mongo_client[MONGODB_DB]
    leads_collection = db[MONGODB_COLLECTION]
    logger.info(f"Connected to MongoDB: {MONGODB_DB}.{MONGODB_COLLECTION}")
except (ConnectionFailure, OperationFailure) as e:
    logger.error(f"Failed to connect to MongoDB: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    if mongo_client:
        try:
            # Test MongoDB connection
            mongo_client.admin.command('ping')
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
    else:
        db_status = "not connected"
        
    return {
        "status": "ok", 
        "message": "Application is healthy",
        "mongodb": db_status
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