"""
MongoDB Connection Test Script for Guards & Robbers

This script tests:
1. MongoDB connection
2. Creating and accessing collections
3. Basic document operations (insert, find, update, delete)
4. Error handling and retry logic
"""

import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGO_DB = os.getenv('MONGODB_DB', 'guards_robbers_db')
MONGO_COLLECTION = os.getenv('MONGODB_COLLECTION', 'leads')

def test_connection():
    """Test MongoDB connection with retry logic"""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to MongoDB (Attempt {attempt+1}/{max_retries})")
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Force a connection to verify
            client.admin.command('ping')
            logger.info("✅ MongoDB connection successful")
            return client
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ Connection failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Maximum retry attempts reached. Could not connect to MongoDB.")
                raise

def test_database_operations(client):
    """Test basic database operations"""
    try:
        # Access database
        db = client[MONGO_DB]
        logger.info(f"✅ Accessed database: {MONGO_DB}")
        
        # List all collections
        collections = db.list_collection_names()
        logger.info(f"Collections in database: {collections}")
        
        # Access or create collection
        collection = db[MONGO_COLLECTION]
        logger.info(f"✅ Accessed collection: {MONGO_COLLECTION}")
        
        # Create an index on email field
        collection.create_index("email")
        logger.info("✅ Created index on 'email' field")
        
        return collection
    except Exception as e:
        logger.error(f"❌ Database operation failed: {e}")
        raise

def test_document_operations(collection):
    """Test document operations (CRUD)"""
    try:
        # Test document to insert
        test_lead = {
            "company": "Test Company",
            "name": "Test User",
            "email": f"test_{datetime.now().timestamp()}@example.com",
            "network": "hybrid",
            "status": "Test Lead",
            "timestamp": datetime.now()
        }
        
        # Insert document
        result = collection.insert_one(test_lead)
        doc_id = result.inserted_id
        logger.info(f"✅ Inserted document with ID: {doc_id}")
        
        # Find document
        found_doc = collection.find_one({"_id": doc_id})
        if found_doc:
            logger.info(f"✅ Retrieved document: {found_doc['name']} from {found_doc['company']}")
        else:
            logger.error("❌ Could not retrieve inserted document")
        
        # Update document
        update_result = collection.update_one(
            {"_id": doc_id},
            {"$set": {"status": "Test Lead Updated"}}
        )
        if update_result.modified_count == 1:
            logger.info("✅ Updated document successfully")
        
        # Verify update
        updated_doc = collection.find_one({"_id": doc_id})
        if updated_doc and updated_doc["status"] == "Test Lead Updated":
            logger.info(f"✅ Update verified: Status is now '{updated_doc['status']}'")
        
        # Delete document
        delete_result = collection.delete_one({"_id": doc_id})
        if delete_result.deleted_count == 1:
            logger.info("✅ Deleted test document successfully")
        
        # Count all documents
        total_docs = collection.count_documents({})
        logger.info(f"Total documents in collection: {total_docs}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Document operation failed: {e}")
        return False

def main():
    """Main test function"""
    logger.info("=== MongoDB Connection Test ===")
    try:
        # Test connection
        client = test_connection()
        
        # Test database operations
        collection = test_database_operations(client)
        
        # Test document operations
        success = test_document_operations(collection)
        
        # Close connection
        client.close()
        logger.info("MongoDB connection closed")
        
        # Summary
        if success:
            logger.info("✅ All MongoDB tests completed successfully!")
        else:
            logger.warning("⚠️ Some MongoDB tests failed. Check logs for details.")
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    main() 