#!/usr/bin/env python
"""
MongoDB Connection Test Script

This script tests different connection configurations for MongoDB Atlas
to resolve SSL/TLS issues and establish a reliable connection.
"""

import os
import sys
import logging
import time
import json
import ssl
import certifi
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

def print_separator():
    print("-" * 80)

def test_connection(config_description, **config_options):
    print_separator()
    logger.info(f"Testing MongoDB connection with: {config_description}")
    
    masked_uri = uri.split('@')[0].split(':')[0] + ':***@' + uri.split('@')[1] if '@' in uri else uri
    logger.info(f"URI: {masked_uri}")
    
    try:
        # Create client with config options
        client = MongoClient(uri, **config_options)
        
        # Try to ping server with shorter timeout for faster feedback
        client.admin.command('ping', serverSelectionTimeoutMS=5000)
        logger.info("✓ Connected successfully!")
        
        # Test database access
        db = client[db_name]
        collections = db.list_collection_names()
        logger.info(f"✓ Found {len(collections)} collections in {db_name}: {', '.join(collections)}")
        
        # Test collection
        collection = db[collection_name]
        doc_count = collection.count_documents({})
        logger.info(f"✓ Collection '{collection_name}' contains {doc_count} documents")
        
        return True
    except Exception as e:
        logger.error(f"✗ Connection failed: {str(e)}")
        return False
    finally:
        print_separator()

if __name__ == "__main__":
    logger.info("Starting MongoDB connection tests")
    print(f"Python version: {sys.version}")
    print(f"PyMongo version: {version}")
    print(f"SSL version: {ssl.OPENSSL_VERSION}")
    print(f"Certifi version: {certifi.__version__}")
    print(f"Certifi path: {certifi.where()}")
    print_separator()
    
    # Test 1: With TLS completely disabled (use only for diagnostics!)
    test_connection(
        "TLS disabled",
        tls=False,
        tlsAllowInvalidCertificates=True
    )
    
    # Test 2: With SSL legacy options
    test_connection(
        "SSL Legacy options", 
        ssl=True,
        ssl_cert_reqs=ssl.CERT_NONE
    )
    
    # Test 3: With TLS allowInvalidCertificates
    test_connection(
        "TLS with allowInvalidCertificates only",
        tlsAllowInvalidCertificates=True
    )
    
    # Test 4: With TLS and Certifi
    test_connection(
        "TLS with Certifi",
        tls=True,
        tlsCAFile=certifi.where()
    )
    
    # Test 5: With modified URI parameters
    modified_uri = uri
    if '?' in uri:
        modified_uri = uri + '&tls=true&tlsInsecure=true'
    else:
        modified_uri = uri + '?tls=true&tlsInsecure=true'
        
    uri_original = uri
    os.environ['MONGODB_URI'] = modified_uri
    uri = modified_uri
    
    test_connection(
        "Modified URI parameters",
        serverSelectionTimeoutMS=10000
    )
    
    # Restore original URI
    uri = uri_original
    os.environ['MONGODB_URI'] = uri_original
    
    # Test 6: Comprehensive configuration
    test_connection(
        "Comprehensive configuration",
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        socketTimeoutMS=15000,
        ssl=True, 
        ssl_cert_reqs=ssl.CERT_NONE,
        tls=True,
        tlsAllowInvalidCertificates=True,
        retryWrites=True,
        appname="guards-robbers-test"
    )
    
    logger.info("MongoDB connection tests complete. Check the results above to determine the best configuration.") 