"""
Flask Application Tests for Guards & Robbers

This script tests:
1. Flask application routes
2. Form submission with MongoDB integration
3. Lead count retrieval
4. Fallback to JSON when MongoDB is unavailable
"""

import os
import json
import pytest
import shutil
import tempfile
from datetime import datetime
from app import app as flask_app
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@pytest.fixture
def app():
    """Configure the Flask app for testing"""
    # Set testing configurations
    flask_app.config.update({
        "TESTING": True,
    })
    
    # Create temporary directory for JSON fallback testing
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, 'test_leads.json')
    
    # Store original path and set environment to use test file
    old_json_path = os.getenv('JSON_BACKUP_PATH', 'leads.json')
    os.environ['JSON_BACKUP_PATH'] = temp_file_path
    
    yield flask_app
    
    # Cleanup after tests
    os.environ['JSON_BACKUP_PATH'] = old_json_path
    try:
        shutil.rmtree(temp_dir)
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not delete temporary directory: {e}")

@pytest.fixture
def client(app):
    """Create a test client for the Flask app"""
    return app.test_client()

def test_index_route(client):
    """Test if the index route returns the marketing page"""
    response = client.get('/')
    assert response.status_code == 200
    # Check for key elements in the response
    assert b'Guards & Robbers' in response.data
    assert b'AI-Powered Cybersecurity' in response.data
    assert b'lead-form' in response.data

def test_submit_lead(client):
    """Test lead submission endpoint with valid data"""
    # Create test lead data
    test_lead = {
        "company": "Test Company",
        "name": "Test User",
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "network": "hybrid"
    }
    
    # Submit lead
    response = client.post('/submit-lead', 
                         json=test_lead,
                         content_type='application/json')
    
    # Check response
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data['status'] == 'success'
    
    # Verify that lead was saved (either to MongoDB or JSON)
    assert 'Lead' in response_data['message'] and 'success' in response_data['message']

def test_submit_lead_missing_field(client):
    """Test lead submission with missing required field"""
    # Create incomplete test lead data (missing email)
    incomplete_lead = {
        "company": "Test Company",
        "name": "Test User",
        "network": "hybrid"
    }
    
    # Submit incomplete lead
    response = client.post('/submit-lead', 
                         json=incomplete_lead,
                         content_type='application/json')
    
    # Check response
    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert response_data['status'] == 'error'
    assert 'Missing required field: email' in response_data['message']

def test_leads_count(client):
    """Test lead count endpoint"""
    # Submit a test lead first
    test_lead = {
        "company": "Count Test Company",
        "name": "Count Test User",
        "email": f"count_test_{datetime.now().timestamp()}@example.com",
        "network": "cloud"
    }
    
    client.post('/submit-lead', 
              json=test_lead,
              content_type='application/json')
    
    # Get lead count
    response = client.get('/leads/count')
    
    # Check response
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data['status'] == 'success'
    assert 'count' in response_data
    assert isinstance(response_data['count'], int)
    assert response_data['count'] >= 1  # At least our test lead should be counted

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main(['-xvs', __file__]) 