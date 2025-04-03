"""
Test script for the Guards & Robbers Flask application.
This script tests:
1. Basic routes and health check
2. Lead submission and retrieval
3. Admin authentication
4. MongoDB fallback mechanism
"""

import os
import sys
import json
import logging
import tempfile
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set environment variables for testing
os.environ['FLASK_ENV'] = 'testing'
os.environ['SECRET_KEY'] = 'test_secret_key'
os.environ['ADMIN_FILE'] = 'test_admin_users.json'
os.environ['DEFAULT_ADMIN_USER'] = 'testadmin'
os.environ['DEFAULT_ADMIN_PASSWORD'] = 'testpassword'
os.environ['JSON_BACKUP_PATH'] = 'test_leads.json'

# Import the Flask app
from app_simple import app as flask_app

# Create a test client
@pytest.fixture
def client():
    # Configure the Flask application for testing
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    # Create a test client
    with flask_app.test_client() as client:
        # Establish application context
        with flask_app.app_context():
            yield client

@pytest.fixture
def cleanup():
    # Setup - create any test files needed
    
    yield
    
    # Teardown - clean up test files
    if os.path.exists('test_admin_users.json'):
        os.remove('test_admin_users.json')
    
    if os.path.exists('test_leads.json'):
        os.remove('test_leads.json')

def test_index_route(client, cleanup):
    """Test the main index route"""
    response = client.get('/')
    
    # Check if the response is successful
    assert response.status_code == 200
    
    # Check if response contains expected content
    assert b'Guards & Robbers' in response.data

def test_health_route(client, cleanup):
    """Test the health check route"""
    response = client.get('/health')
    
    # Check if the response is successful
    assert response.status_code == 200
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check if the response contains the expected fields
    assert 'status' in data
    assert data['status'] == 'ok'
    assert 'message' in data
    assert 'environment' in data
    assert 'mongodb' in data
    assert 'timestamp' in data

def test_submit_lead(client, cleanup):
    """Test lead submission"""
    # Test data
    lead_data = {
        'company': 'Test Company',
        'name': 'Test User',
        'email': 'test@example.com',
        'network': 'Small (1-50 employees)'
    }
    
    # Submit a lead
    response = client.post('/submit-lead', 
                          json=lead_data,
                          content_type='application/json')
    
    # Check if the response is successful
    assert response.status_code == 200
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check if lead was successfully submitted
    assert data['status'] == 'success'
    
    # Check if lead was saved to the test JSON file
    assert os.path.exists('test_leads.json')
    
    # Verify lead count
    count_response = client.get('/leads/count')
    count_data = json.loads(count_response.data)
    
    assert count_data['status'] == 'success'
    # Simply check that we have at least one lead rather than an exact count
    # as there might be other leads from previous tests
    assert count_data['count'] >= 1

@patch('app_simple.authenticate')
def test_admin_login(mock_authenticate, client, cleanup):
    """Test admin login functionality"""
    # Configure the mock to return True for successful authentication
    mock_authenticate.return_value = True
    
    # Test login with valid credentials
    response = client.post('/admin/login', 
                          data={'username': 'testadmin', 'password': 'testpassword'},
                          follow_redirects=True)
    
    # Check if login was successful and redirected to admin dashboard
    assert response.status_code == 200
    assert b'Lead Management Dashboard' in response.data
    
    # Configure the mock to return False for failed authentication
    mock_authenticate.return_value = False
    
    # Test login with invalid credentials
    response = client.post('/admin/login', 
                          data={'username': 'testadmin', 'password': 'wrongpassword'},
                          follow_redirects=True)
    
    # Check if login failed and stayed on login page
    assert response.status_code == 200
    assert b'Admin Login' in response.data
    assert b'Invalid username or password' in response.data

@patch('app_simple.authenticate')
def test_admin_access_control(mock_authenticate, client, cleanup):
    """Test admin routes access control"""
    # Configure the mock to return False (not authenticated)
    mock_authenticate.return_value = False
    
    # Try to access admin dashboard without login
    response = client.get('/admin', follow_redirects=True)
    
    # Should redirect to login page
    assert response.status_code == 200
    assert b'Admin Login' in response.data
    
    # Configure the mock to return True (authenticated)
    mock_authenticate.return_value = True
    
    # Login
    client.post('/admin/login', 
               data={'username': 'testadmin', 'password': 'testpassword'})
    
    # Now try to access admin dashboard
    response = client.get('/admin')
    
    # Should be able to access dashboard
    assert response.status_code == 200
    assert b'Lead Management Dashboard' in response.data
    
    # Test logout
    response = client.get('/admin/logout', follow_redirects=True)
    
    # Should redirect to login page
    assert response.status_code == 200
    assert b'Admin Login' in response.data
    assert b'You have been logged out' in response.data

@patch('app_simple.MongoClient')
def test_mongodb_fallback(mock_mongo_client, client, cleanup):
    """Test MongoDB fallback mechanism"""
    # Configure the mock to simulate MongoDB connection failure
    mock_mongo_client.side_effect = Exception("MongoDB connection failed")
    
    # Mock setup should happen before app initialization/requests
    with patch('app_simple.mongo_client', None):
        with patch('app_simple.db', None):
            with patch('app_simple.leads_collection', None):
                # Test lead submission with MongoDB unavailable
                lead_data = {
                    'company': 'Fallback Company',
                    'name': 'Fallback User',
                    'email': 'fallback@example.com',
                    'network': 'Medium (51-200 employees)'
                }
                
                # Submit a lead - should be saved to JSON file
                response = client.post('/submit-lead', 
                                      json=lead_data,
                                      content_type='application/json')
                
                # Check if the response is successful despite MongoDB failure
                assert response.status_code == 200
                
                # Parse the JSON response
                data = json.loads(response.data)
                
                # Should succeed but indicate fallback
                assert data['status'] == 'success'
                
                # Verify lead count still works
                count_response = client.get('/leads/count')
                count_data = json.loads(count_response.data)
                
                assert count_data['status'] == 'success'
                # Should use in-memory fallback
                assert 'source' in count_data
                assert count_data['source'] == 'memory'

if __name__ == "__main__":
    # Manual test runner
    import pytest
    sys.exit(pytest.main(['-xvs', __file__])) 