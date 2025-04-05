from flask import Flask, render_template, request, jsonify, g, redirect, url_for, flash, session
import os
import json
from datetime import datetime
import logging
from dotenv import load_dotenv
from mongodb_schema import apply_schema_validation
from secure_mongodb import get_secure_mongo_client
from security_contract import requires_auth, requires_role, log_database_access

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret_key')  # Add secret key for flash messages

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize secure MongoDB client
secure_mongo = get_secure_mongo_client()

# Apply schema validation
try:
    apply_schema_validation()
    logger.info("MongoDB schema validation applied")
except Exception as e:
    logger.error(f"Error applying schema validation: {e}")

@app.route('/')
def index():
    return render_template('index.html')

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
        
        # Add to MongoDB using secure client
        doc_id = secure_mongo.insert_document(lead_document)
        
        if doc_id:
            return jsonify({'status': 'success', 'message': 'Lead submitted successfully!'}), 200
        elif os.getenv('ENABLE_JSON_BACKUP', 'True').lower() == 'true':
            logger.warning("MongoDB operation failed. Lead saved to local file only.")
            return jsonify({'status': 'success', 'message': 'Lead saved locally. MongoDB integration not available.'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Database connection failed and local backup is disabled.'}), 500
            
    except Exception as e:
        logger.error(f"Error submitting lead: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/leads/count', methods=['GET'])
def get_lead_count():
    try:
        # Try to get count from MongoDB using secure client
        count = secure_mongo.count_documents()
        if count is not None:
            return jsonify({'status': 'success', 'count': count}), 200
        
        # Fallback to counting lines in the backup file
        if os.getenv('ENABLE_JSON_BACKUP', 'True').lower() == 'true':
            json_path = os.getenv('JSON_BACKUP_PATH', 'leads.json')
            try:
                with open(json_path, 'r') as f:
                    json_count = sum(1 for _ in f)
                logger.info(f"JSON file lead count: {json_count}")
                return jsonify({'status': 'success', 'count': json_count}), 200
            except FileNotFoundError:
                logger.warning(f"JSON backup file not found at {json_path}")
                return jsonify({'status': 'success', 'count': 0}), 200
        
        # If we get here, both MongoDB and JSON failed
        return jsonify({'status': 'success', 'count': 0}), 200
    except Exception as e:
        logger.error(f"Error getting lead count: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Admin dashboard route
@app.route('/admin/dashboard')
@requires_auth
@requires_role(['admin', 'manager'])
def admin_dashboard():
    try:
        # Get query parameters for filtering and sorting
        status_filter = request.args.get('status', '')
        sort_by = request.args.get('sort', 'timestamp')
        sort_dir = request.args.get('dir', 'desc')
        search_query = request.args.get('q', '')
        
        # Build filter query
        filter_query = {}
        if status_filter and status_filter != 'all':
            filter_query['status'] = status_filter
            
        # Add search functionality
        if search_query:
            # Search in multiple fields
            filter_query['$or'] = [
                {'name': {'$regex': search_query, '$options': 'i'}},
                {'email': {'$regex': search_query, '$options': 'i'}},
                {'company': {'$regex': search_query, '$options': 'i'}},
                {'network': {'$regex': search_query, '$options': 'i'}}
            ]
        
        # Determine sort direction
        sort_direction = -1 if sort_dir == 'desc' else 1
        
        # Get leads with filtering and sorting
        leads = secure_mongo.find_documents(
            filter_query, 
            sort=[(sort_by, sort_direction)]
        )
        
        # Convert ObjectId to string and format timestamp for template
        serializable_leads = []
        for lead in leads:
            lead['_id'] = str(lead['_id'])
            lead['timestamp'] = lead['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            serializable_leads.append(lead)
        
        # Get available statuses for filter dropdown
        statuses = secure_mongo.distinct_values('status') or ['New Lead']
        
        # Get today's lead count for dashboard stats
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_leads_count = secure_mongo.count_documents({
            'timestamp': {'$gte': today}
        })
        
        # Pass username from session if available
        username = session.get('username', 'Admin')
        
        return render_template(
            'admin_dashboard.html',
            leads=serializable_leads,
            username=username,
            status_filter=status_filter,
            sort_by=sort_by,
            sort_dir=sort_dir,
            search_query=search_query,
            statuses=statuses,
            today_leads_count=today_leads_count
        )
    except Exception as e:
        logger.error(f"Error rendering admin dashboard: {e}")
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return render_template('admin_dashboard.html', leads=[], username='Admin')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash("You have been logged out successfully", "info")
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # Simple implementation - security is handled by requires_auth decorator
    if request.method == 'POST':
        username = request.form.get('username')
        session['username'] = username
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/leads/export', methods=['GET'])
@requires_auth
@requires_role(['admin', 'manager'])
def export_leads():
    try:
        # Get query parameters for filtering
        status_filter = request.args.get('status', '')
        search_query = request.args.get('q', '')
        
        # Build filter query
        filter_query = {}
        if status_filter and status_filter != 'all':
            filter_query['status'] = status_filter
            
        # Add search functionality
        if search_query:
            # Search in multiple fields
            filter_query['$or'] = [
                {'name': {'$regex': search_query, '$options': 'i'}},
                {'email': {'$regex': search_query, '$options': 'i'}},
                {'company': {'$regex': search_query, '$options': 'i'}},
                {'network': {'$regex': search_query, '$options': 'i'}}
            ]
        
        # Get leads with filtering
        leads = secure_mongo.find_documents(filter_query)
        
        # Convert to CSV format
        csv_data = "ID,Company,Name,Email,Network,Status,Timestamp\n"
        for lead in leads:
            # Format CSV row, handle potential commas in fields
            csv_row = [
                str(lead['_id']),
                f'"{lead["company"]}"',
                f'"{lead["name"]}"',
                lead["email"],
                f'"{lead["network"]}"',
                lead.get("status", "New Lead"),
                lead["timestamp"].strftime('%Y-%m-%d %H:%M:%S')
            ]
            csv_data += ",".join(csv_row) + "\n"
        
        # Return as downloadable CSV
        from flask import Response
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=leads_export.csv"}
        )
    except Exception as e:
        logger.error(f"Error exporting leads: {e}")
        flash(f"Error exporting leads: {str(e)}", "danger")
        return redirect(url_for('admin_dashboard'))

# Admin endpoints with security measures
@app.route('/admin/leads', methods=['GET'])
@requires_auth
@requires_role(['admin', 'manager'])
def get_all_leads():
    try:
        leads = secure_mongo.find_documents({})
        
        # Convert ObjectId to string for JSON serialization
        serializable_leads = []
        for lead in leads:
            lead['_id'] = str(lead['_id'])
            lead['timestamp'] = lead['timestamp'].isoformat()
            serializable_leads.append(lead)
            
        return jsonify({
            'status': 'success', 
            'count': len(serializable_leads),
            'leads': serializable_leads
        }), 200
    except Exception as e:
        logger.error(f"Error retrieving leads: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/leads/<lead_id>', methods=['GET'])
@requires_auth
@requires_role(['admin', 'manager'])
def get_lead(lead_id):
    try:
        from bson.objectid import ObjectId
        
        lead = secure_mongo.find_document({"_id": ObjectId(lead_id)})
        
        if not lead:
            return jsonify({'status': 'error', 'message': 'Lead not found'}), 404
        
        # Convert ObjectId to string for JSON serialization
        lead['_id'] = str(lead['_id'])
        lead['timestamp'] = lead['timestamp'].isoformat()
        
        return jsonify({'status': 'success', 'lead': lead}), 200
    except Exception as e:
        logger.error(f"Error retrieving lead: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/leads/<lead_id>', methods=['PUT'])
@requires_auth
@requires_role(['admin'])
def update_lead(lead_id):
    try:
        from bson.objectid import ObjectId
        
        data = request.get_json()
        
        # Don't allow changing the ID
        if '_id' in data:
            del data['_id']
        
        # Update the lead
        result = secure_mongo.update_document(
            {"_id": ObjectId(lead_id)},
            {"$set": data}
        )
        
        if result:
            return jsonify({'status': 'success', 'message': 'Lead updated successfully'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Failed to update lead'}), 404
    except Exception as e:
        logger.error(f"Error updating lead: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/leads/<lead_id>', methods=['DELETE'])
@requires_auth
@requires_role(['admin'])
def delete_lead(lead_id):
    try:
        from bson.objectid import ObjectId
        
        result = secure_mongo.delete_document({"_id": ObjectId(lead_id)})
        
        if result:
            return jsonify({'status': 'success', 'message': 'Lead deleted successfully'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Failed to delete lead'}), 404
    except Exception as e:
        logger.error(f"Error deleting lead: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.teardown_appcontext
def shutdown_session(exception=None):
    # Clean up Flask g object
    if hasattr(g, 'client_id'):
        delattr(g, 'client_id')
    if hasattr(g, 'role'):
        delattr(g, 'role')

if __name__ == '__main__':
    debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
    app.run(debug=debug_mode) 