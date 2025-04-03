"""
Security Implementation Tests for Guards & Robbers

This script tests:
1. API key generation and validation
2. Role-based authorization
3. Rate limiting
4. Secure MongoDB operations
5. Access logging
"""

import os
import json
import time
import unittest
import tempfile
from datetime import datetime
from flask import Flask, g
from security_contract import (
    create_api_key, revoke_api_key, authenticate, requires_auth, 
    requires_role, log_database_access, API_KEYS, DEFAULT_RATE_LIMIT
)
from secure_mongodb import SecureMongoClient
from unittest.mock import patch, MagicMock, mock_open

class SecurityContractTests(unittest.TestCase):
    """Tests for the security contract functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a test Flask app
        self.app = Flask(__name__)
        
        # Create a temporary file for API keys
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        
        # Save original API keys
        self.original_api_keys = API_KEYS.copy()
        
        # Clear API keys for tests
        API_KEYS.clear()
        
        # Create test API keys
        self.admin_key = create_api_key("test-admin", "admin", 100)
        self.user_key = create_api_key("test-user", "user", 10)
        
        # Set up environment for tests
        os.environ['API_KEYS_FILE'] = self.temp_file.name
        
        # Create a log file for testing
        self.log_file = tempfile.NamedTemporaryFile(delete=False, suffix='.log')
        self.log_file.close()
        os.environ['DB_ACCESS_LOG'] = self.log_file.name
    
    def tearDown(self):
        """Clean up after tests"""
        # Restore original API keys
        API_KEYS.clear()
        API_KEYS.update(self.original_api_keys)
        
        # Clean up temp files
        for file_path in [self.temp_file.name, self.log_file.name]:
            if os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except (OSError, PermissionError):
                    pass
    
    def test_api_key_creation(self):
        """Test API key creation"""
        # Test that keys were created in setUp
        self.assertIn(self.admin_key, API_KEYS)
        self.assertIn(self.user_key, API_KEYS)
        
        # Verify properties
        self.assertEqual(API_KEYS[self.admin_key]['client_id'], "test-admin")
        self.assertEqual(API_KEYS[self.admin_key]['role'], "admin")
        self.assertEqual(API_KEYS[self.user_key]['client_id'], "test-user")
        self.assertEqual(API_KEYS[self.user_key]['role'], "user")
    
    def test_api_key_revocation(self):
        """Test API key revocation"""
        # Verify key exists
        self.assertIn(self.user_key, API_KEYS)
        
        # Revoke key
        result = revoke_api_key(self.user_key)
        
        # Verify revocation
        self.assertTrue(result)
        self.assertNotIn(self.user_key, API_KEYS)
    
    def test_authentication(self):
        """Test authentication process"""
        # Set up mock request with API key
        with self.app.test_request_context(f'/?api_key={self.admin_key}'):
            # Test authentication
            client_info = authenticate()
            
            # Verify authentication succeeded
            self.assertIsNotNone(client_info)
            self.assertEqual(client_info['client_id'], "test-admin")
            self.assertEqual(client_info['role'], "admin")
            
            # Verify Flask g object was populated
            self.assertEqual(g.client_id, "test-admin")
            self.assertEqual(g.role, "admin")
    
    def test_authentication_failure(self):
        """Test authentication failure with invalid key"""
        # Set up mock request with invalid API key
        with self.app.test_request_context('/?api_key=invalid-key'):
            # Test authentication
            client_info = authenticate()
            
            # Verify authentication failed
            self.assertIsNone(client_info)
            
            # Verify Flask g object was not populated
            self.assertFalse(hasattr(g, 'client_id'))
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Create a key with very low rate limit
        low_limit_key = create_api_key("rate-limited", "user", 2)
        
        # Make multiple requests within rate limit
        with self.app.test_request_context(f'/?api_key={low_limit_key}'):
            # First request
            client_info = authenticate()
            self.assertIsNotNone(client_info)
            
            # Second request
            client_info = authenticate()
            self.assertIsNotNone(client_info)
            
            # Third request - should fail due to rate limit
            client_info = authenticate()
            self.assertIsNone(client_info)
    
    def test_requires_auth_decorator(self):
        """Test requires_auth decorator"""
        # Create test route with auth
        @self.app.route('/test')
        @requires_auth
        def test_route():
            return 'OK'
        
        # Test with valid key
        with self.app.test_client() as client:
            response = client.get(f'/test?api_key={self.admin_key}')
            self.assertEqual(response.status_code, 200)
        
        # Test with invalid key
        with self.app.test_client() as client:
            response = client.get('/test?api_key=invalid-key')
            self.assertEqual(response.status_code, 401)
    
    def test_requires_role_decorator(self):
        """Test requires_role decorator"""
        # Create test route with role requirement
        @self.app.route('/admin-only')
        @requires_role(['admin'])
        def admin_route():
            return 'OK'
        
        # Test with admin role
        with self.app.test_client() as client:
            response = client.get(f'/admin-only?api_key={self.admin_key}')
            self.assertEqual(response.status_code, 200)
        
        # Test with user role (insufficient)
        with self.app.test_client() as client:
            response = client.get(f'/admin-only?api_key={self.user_key}')
            self.assertEqual(response.status_code, 403)
    
    def test_log_database_access(self):
        """Test database access logging"""
        # Set client ID and role in Flask g
        with self.app.test_request_context():
            g.client_id = "test-logger"
            g.role = "admin"
            
            # Log a test operation
            log_database_access("test_collection", "find", query={"test": "value"})
            
            # Verify log file was written
            with open(self.log_file.name, 'r') as f:
                log_data = json.loads(f.read().strip())
                
                # Check log contents
                self.assertEqual(log_data['client_id'], "test-logger")
                self.assertEqual(log_data['role'], "admin")
                self.assertEqual(log_data['collection'], "test_collection")
                self.assertEqual(log_data['operation'], "find")
                self.assertIn("query", log_data)
                self.assertIn("test", log_data['query'])

class SecureMongoClientTests(unittest.TestCase):
    """Tests for the secure MongoDB client"""
    
    def setUp(self):
        """Set up test environment with mocks"""
        # Create mock MongoDB client
        self.mock_mongo_client = MagicMock()
        self.mock_db = MagicMock()
        self.mock_collection = MagicMock()
        
        # Configure mocks
        self.mock_mongo_client.__getitem__.return_value = self.mock_db
        self.mock_db.__getitem__.return_value = self.mock_collection
        
        # Create patchers
        self.mongo_patcher = patch('secure_mongodb.MongoClient', return_value=self.mock_mongo_client)
        self.log_patcher = patch('secure_mongodb.log_database_access')
        
        # Start patchers
        self.mock_mongo = self.mongo_patcher.start()
        self.mock_log = self.log_patcher.start()
        
        # Create secure client
        self.secure_client = SecureMongoClient(
            uri="mongodb://example.com:27017/",
            db_name="test_db",
            collection_name="test_collection"
        )
    
    def tearDown(self):
        """Clean up mocks"""
        self.mongo_patcher.stop()
        self.log_patcher.stop()
    
    def test_client_initialization(self):
        """Test client initialization"""
        # Verify MongoDB client was created
        self.mock_mongo.assert_called_once()
        
        # Verify database and collection access
        self.assertEqual(self.secure_client.db_name, "test_db")
        self.assertEqual(self.secure_client.collection_name, "test_collection")
    
    def test_insert_document(self):
        """Test document insertion with logging"""
        # Set up mock for insert_one
        mock_result = MagicMock()
        mock_result.inserted_id = "test_id"
        self.mock_collection.insert_one.return_value = mock_result
        
        # Test document insertion
        test_doc = {"name": "Test Document"}
        result = self.secure_client.insert_document(test_doc)
        
        # Verify MongoDB operation
        self.mock_collection.insert_one.assert_called_once_with(test_doc)
        
        # Verify logging
        self.mock_log.assert_called_once()
        
        # Verify result
        self.assertEqual(result, "test_id")
    
    def test_find_document(self):
        """Test document retrieval with logging"""
        # Set up mock for find_one
        mock_doc = {"_id": "test_id", "name": "Test Document"}
        self.mock_collection.find_one.return_value = mock_doc
        
        # Test document retrieval
        test_query = {"name": "Test Document"}
        result = self.secure_client.find_document(test_query)
        
        # Verify MongoDB operation
        self.mock_collection.find_one.assert_called_once_with(test_query)
        
        # Verify logging
        self.mock_log.assert_called_once()
        
        # Verify result
        self.assertEqual(result, mock_doc)
    
    def test_update_document(self):
        """Test document update with logging"""
        # Set up mock for update_one
        mock_result = MagicMock()
        mock_result.modified_count = 1
        self.mock_collection.update_one.return_value = mock_result
        
        # Test document update
        test_query = {"name": "Test Document"}
        test_update = {"$set": {"status": "updated"}}
        result = self.secure_client.update_document(test_query, test_update)
        
        # Verify MongoDB operation
        self.mock_collection.update_one.assert_called_once_with(test_query, test_update)
        
        # Verify logging
        self.mock_log.assert_called_once()
        
        # Verify result
        self.assertTrue(result)
    
    def test_delete_document(self):
        """Test document deletion with logging"""
        # Set up mock for delete_one
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        self.mock_collection.delete_one.return_value = mock_result
        
        # Test document deletion
        test_query = {"name": "Test Document"}
        result = self.secure_client.delete_document(test_query)
        
        # Verify MongoDB operation
        self.mock_collection.delete_one.assert_called_once_with(test_query)
        
        # Verify logging
        self.mock_log.assert_called_once()
        
        # Verify result
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main() 