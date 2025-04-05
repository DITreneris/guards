#!/usr/bin/env python
"""
MongoDB Connection Fix Script

This script implements a reliable connection to MongoDB Atlas
with an optimized configuration to resolve SSL/TLS issues.
"""

import os
import sys
import logging
import ssl
import certifi
import time
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient, version
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get MongoDB connection details
uri = os.getenv('MONGODB_URI')
db_name = os.getenv('MONGODB_DB', 'guards_robbers_db')
collection_name = os.getenv('MONGODB_COLLECTION', 'leads')

if not uri:
    logger.error("MongoDB URI is not set in environment variables")
    sys.exit(1)

# Display environment information
logger.info(f"Python version: {sys.version}")
logger.info(f"PyMongo version: {version}")
logger.info(f"SSL version: {ssl.OPENSSL_VERSION}")
logger.info(f"Certifi version: {certifi.__version__}")

# Extract the MongoDB host from the URI
host = uri.split('@')[1].split('/')[0] if '@' in uri else None
logger.info(f"Connecting to MongoDB host: {host}")

# Clean the URI - remove any TLS parameters that might be causing issues
if '?' in uri:
    base_uri = uri.split('?')[0]
    params = uri.split('?')[1].split('&')
    clean_params = [p for p in params if not p.startswith(('tls', 'ssl'))]
    
    # Add back the most essential parameters
    clean_params.append('retryWrites=true')
    
    # Reconstruct the clean URI
    clean_uri = f"{base_uri}?{'&'.join(clean_params)}"
else:
    clean_uri = uri

logger.info("Attempting to connect with optimized settings...")

try:
    # Create client with optimal configuration for SSL/TLS issues
    client = MongoClient(
        clean_uri,
        serverSelectionTimeoutMS=30000,      # Longer timeout for initial connection
        connectTimeoutMS=30000,              # Longer timeout for initial connection
        socketTimeoutMS=45000,               # Longer timeout for operations
        ssl=True,                            # Enable SSL
        tlsAllowInvalidCertificates=True,    # Allow invalid certificates
        retryWrites=True,                    # Enable retry writes for operations
        appname="guards-robbers-fix"         # App name for tracking
    )
    
    # Force a connection
    logger.info("Testing connection...")
    client.admin.command('ping')
    logger.info("✅ Connected successfully to MongoDB Atlas!")
    
    # Test database access
    db = client[db_name]
    collections = db.list_collection_names()
    logger.info(f"✅ Found {len(collections)} collections in database '{db_name}'")
    
    # Test collection access and count documents
    collection = db[collection_name]
    doc_count = collection.count_documents({})
    logger.info(f"✅ Collection '{collection_name}' contains {doc_count} documents")
    
    # Insert a test document
    test_doc = {
        "source": "connection_test",
        "timestamp": {"$date": {"$numberLong": str(int(time.time() * 1000))}},
        "test": True,
        "message": "Connection test successful"
    }
    
    # Test write operation
    result = collection.insert_one(test_doc)
    logger.info(f"✅ Test document inserted with ID: {result.inserted_id}")
    
    # Clean up test document
    collection.delete_one({"_id": result.inserted_id})
    logger.info("✅ Test document removed successfully")
    
    # Generate Heroku configuration command
    print("\n=== Configuration for Heroku ===")
    print(f"heroku config:set MONGODB_URI=\"{clean_uri}\" MONGODB_DB=\"{db_name}\" "
          f"MONGODB_COLLECTION=\"{collection_name}\" MONGODB_TLS_INSECURE=true --app guards-robbers")
    
    # Update local .env file
    with open('.env', 'r') as f:
        env_lines = f.readlines()
    
    updated_lines = []
    for line in env_lines:
        if line.startswith('MONGODB_URI='):
            updated_lines.append(f'MONGODB_URI={clean_uri}\n')
        elif line.startswith('MONGODB_TLS_INSECURE='):
            updated_lines.append('MONGODB_TLS_INSECURE=true\n')
        else:
            updated_lines.append(line)
    
    # Add the parameter if not present
    if not any(line.startswith('MONGODB_TLS_INSECURE=') for line in updated_lines):
        updated_lines.append('MONGODB_TLS_INSECURE=true\n')
    
    with open('.env', 'w') as f:
        f.writelines(updated_lines)
    
    logger.info("✅ Updated .env file with working MongoDB configuration")
    
    # Update app_simple.py with the working connection parameters
    print("\n=== MongoDB Connection Parameters for app_simple.py ===")
    print("""
    mongo_client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=10000,      
        connectTimeoutMS=10000,              
        socketTimeoutMS=15000,               
        ssl=True,                            
        tlsAllowInvalidCertificates=True,    
        retryWrites=True,                    
        appname="guards-robbers-app"         
    )
    """)
    
    logger.info("✅ Connection fix complete. The application should work correctly now.")

except Exception as e:
    logger.error(f"❌ Connection failed: {str(e)}")
    sys.exit(1) 