"""
MongoDB Atlas Setup Script for Guards & Robbers

This script helps to:
1. Test connection to MongoDB Atlas
2. Set up initial collections and indexes
3. Generate proper connection string for Heroku
"""

import os
import sys
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, OperationFailure

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default connection values
DEFAULT_URI = "mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER_URL/?retryWrites=true&w=majority"
DEFAULT_DB = "guards_robbers_db"
DEFAULT_COLLECTION = "leads"

def get_connection_info():
    """Get MongoDB connection details interactively"""
    mongo_uri = input(f"Enter MongoDB Atlas URI [{DEFAULT_URI}]: ") or DEFAULT_URI
    db_name = input(f"Enter database name [{DEFAULT_DB}]: ") or DEFAULT_DB
    collection_name = input(f"Enter collection name [{DEFAULT_COLLECTION}]: ") or DEFAULT_COLLECTION
    
    return mongo_uri, db_name, collection_name

def test_connection(uri, db_name, collection_name):
    """Test connection to MongoDB Atlas and set up collections"""
    logger.info("Testing MongoDB connection...")
    
    try:
        # Connect with default options for production
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            appname="guards-robbers-app"
        )
        
        # Test basic connection
        client.admin.command('ping')
        logger.info("✅ Connected to MongoDB Atlas")
        
        # Access database
        db = client[db_name]
        logger.info(f"✅ Accessed database: {db_name}")
        
        # Create collection if it doesn't exist
        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)
            logger.info(f"✅ Created collection: {collection_name}")
        else:
            logger.info(f"✅ Collection already exists: {collection_name}")
        
        collection = db[collection_name]
        
        # Create indexes for better performance
        collection.create_index([("email", ASCENDING)], unique=True)
        collection.create_index([("timestamp", ASCENDING)])
        logger.info("✅ Created indexes on email and timestamp fields")
        
        # Count documents
        doc_count = collection.count_documents({})
        logger.info(f"✅ Collection has {doc_count} documents")
        
        # Create test document to verify write permissions
        test_doc = {
            "company": "Test Company",
            "name": "Test User",
            "email": f"test_{datetime.now().timestamp()}@example.com",
            "network": "Test",
            "status": "Test Lead",
            "timestamp": datetime.now()
        }
        
        result = collection.insert_one(test_doc)
        logger.info(f"✅ Test document inserted with ID: {result.inserted_id}")
        
        # Clean up test document
        collection.delete_one({"_id": result.inserted_id})
        logger.info("✅ Test document cleaned up")
        
        # Generate Heroku config command
        masked_uri = uri.split('@')[0].split(':')[0] + ':******@' + uri.split('@')[1]
        logger.info(f"✅ Connection verified with URI: {masked_uri}")
        
        print("\n=== Heroku Configuration Command ===")
        print(f"heroku config:set MONGODB_URI=\"{uri}\" MONGODB_DB=\"{db_name}\" MONGODB_COLLECTION=\"{collection_name}\" --app guards-robbers")
        
        return True
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {str(e)}")
        return False

def create_sample_data(uri, db_name, collection_name, count=5):
    """Create sample lead data for testing"""
    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db[collection_name]
        
        sample_companies = ["Acme Corp", "Globex", "Initech", "Umbrella Corp", "Wayne Enterprises"]
        sample_names = ["John Doe", "Jane Smith", "Alice Johnson", "Bob Brown", "Charlie Davis"]
        sample_emails = ["john@example.com", "jane@example.com", "alice@example.com", 
                         "bob@example.com", "charlie@example.com"]
        sample_networks = ["1-10", "11-50", "51-200", "201+"]
        
        for i in range(count):
            lead = {
                "company": sample_companies[i % len(sample_companies)],
                "name": sample_names[i % len(sample_names)],
                "email": f"sample_{i}_{sample_emails[i % len(sample_emails)]}",
                "network": sample_networks[i % len(sample_networks)],
                "status": "Sample Lead",
                "timestamp": datetime.now()
            }
            
            try:
                collection.insert_one(lead)
                logger.info(f"✅ Sample lead {i+1} inserted")
            except Exception as e:
                logger.warning(f"⚠️ Could not insert sample lead {i+1}: {e}")
        
        logger.info(f"✅ Created {count} sample leads for testing")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create sample data: {str(e)}")
        return False

def main():
    print("=== Guards & Robbers MongoDB Atlas Setup ===")
    
    # Get connection info
    uri, db_name, collection_name = get_connection_info()
    
    # Test connection
    if test_connection(uri, db_name, collection_name):
        # Ask about sample data
        create_samples = input("Would you like to create sample lead data? (y/n): ").lower() == 'y'
        if create_samples:
            count = int(input("How many sample leads to create? [5]: ") or "5")
            create_sample_data(uri, db_name, collection_name, count)
    
    print("\nSetup complete!")

if __name__ == "__main__":
    main() 