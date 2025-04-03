"""
MongoDB Atlas Connection Test Script

This script tests a connection to MongoDB Atlas with different configurations
to help diagnose connection issues.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from pymongo import MongoClient, version
from pymongo.server_api import ServerApi
import ssl
import certifi

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get MongoDB connection details
uri = os.getenv('MONGODB_URI', 'mongodb+srv://tomasstaniulis76:your_actual_mongodb_password@cluster0.c3edapt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db_name = os.getenv('MONGODB_DB', 'guards_robbers_db')
collection_name = os.getenv('MONGODB_COLLECTION', 'leads')

def print_separator():
    print("\n" + "-" * 80 + "\n")

def test_connection(config_description, **config_options):
    print_separator()
    logger.info(f"Testing MongoDB connection with: {config_description}")
    
    masked_uri = uri.split('@')[0].split(':')[0] + ':***@' + uri.split('@')[1] if '@' in uri else uri
    logger.info(f"URI: {masked_uri}")
    
    try:
        # Create client with config options
        client = MongoClient(uri, **config_options)
        
        # Try to ping server
        client.admin.command('ping')
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

def main():
    print("MongoDB Connection Test")
    print(f"PyMongo version: {version}")
    print(f"Python version: {sys.version}")
    print(f"Certifi version: {certifi.__version__}")
    print(f"SSL version: {ssl.OPENSSL_VERSION}")
    
    print("\nTesting different connection configurations:")
    
    # Test 1: Basic connection
    test_connection("Basic connection", 
                    serverSelectionTimeoutMS=5000)
    
    # Test 2: With server API
    test_connection("With server API v1", 
                    server_api=ServerApi('1'),
                    serverSelectionTimeoutMS=5000)
    
    # Test 3: With SSL options
    test_connection("With SSL options", 
                    ssl=True, 
                    ssl_cert_reqs=ssl.CERT_NONE,
                    serverSelectionTimeoutMS=5000)
    
    # Test 4: With Certifi CA
    test_connection("With Certifi CA bundle", 
                    tlsCAFile=certifi.where(),
                    serverSelectionTimeoutMS=5000)
    
    # Test 5: With TLS options
    test_connection("With TLS options", 
                    tls=True,
                    tlsAllowInvalidCertificates=True,
                    serverSelectionTimeoutMS=5000)
    
    # Test 6: With everything
    test_connection("With all options combined",
                    server_api=ServerApi('1'),
                    tls=True,
                    tlsAllowInvalidCertificates=True,
                    tlsCAFile=certifi.where(),
                    ssl=True,
                    ssl_cert_reqs=ssl.CERT_NONE,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000)

if __name__ == "__main__":
    main() 