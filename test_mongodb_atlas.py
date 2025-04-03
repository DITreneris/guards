"""
MongoDB Atlas Connection Test for Guards & Robbers

This script tests:
1. Connection to MongoDB Atlas
2. Database and collection access
3. Basic CRUD operations
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv('MONGODB_URI')
MONGO_DB = os.getenv('MONGODB_DB', 'guards_robbers_db')

def test_atlas_connection():
    """Test connection to MongoDB Atlas"""
    logger.info("Attempting to connect to MongoDB Atlas...")
    
    try:
        # Create a new client and connect to the server with server API version 1
        client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
        
        # Send a ping to confirm connection
        client.admin.command('ping')
        logger.info("✅ Successfully connected to MongoDB Atlas!")
        
        # Get server info
        server_info = client.server_info()
        logger.info(f"MongoDB version: {server_info.get('version', 'Unknown')}")
        
        return client
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB Atlas: {e}")
        raise

def test_database_operations(client):
    """Test database and collection operations"""
    logger.info(f"Accessing database: {MONGO_DB}")
    
    try:
        # Access the database
        db = client[MONGO_DB]
        
        # List databases
        databases = client.list_database_names()
        logger.info(f"Available databases: {', '.join(databases)}")
        
        # Access or create leads collection
        leads_collection = db.leads
        
        # Create an index on email field if it doesn't exist
        index_info = leads_collection.index_information()
        if 'email_1' not in index_info:
            leads_collection.create_index("email")
            logger.info("Created index on 'email' field")
        else:
            logger.info("Index on 'email' field already exists")
        
        # List all collections in the database
        collections = db.list_collection_names()
        logger.info(f"Collections in {MONGO_DB}: {', '.join(collections) if collections else 'None'}")
        
        return leads_collection
    except Exception as e:
        logger.error(f"❌ Database operation failed: {e}")
        raise

def test_document_operations(collection):
    """Test CRUD operations on documents"""
    logger.info("Testing document operations (Create, Read, Update, Delete)...")
    
    try:
        # Create a test lead document
        test_lead = {
            "company": "Atlas Test Company",
            "name": "Atlas Test User",
            "email": f"atlas_test_{datetime.now().timestamp()}@example.com",
            "network": "cloud",
            "status": "Test Lead",
            "timestamp": datetime.now()
        }
        
        # Create - Insert document
        insert_result = collection.insert_one(test_lead)
        doc_id = insert_result.inserted_id
        logger.info(f"✅ Created: Inserted document with ID: {doc_id}")
        
        # Read - Find document
        found_doc = collection.find_one({"_id": doc_id})
        if found_doc:
            logger.info(f"✅ Read: Retrieved document: {found_doc['name']} from {found_doc['company']}")
        else:
            logger.error("❌ Read failed: Could not retrieve inserted document")
            return False
        
        # Update - Modify document
        update_result = collection.update_one(
            {"_id": doc_id},
            {"$set": {"status": "Test Lead Updated", "notes": "Added during Atlas test"}}
        )
        if update_result.modified_count == 1:
            logger.info("✅ Update: Modified document successfully")
        else:
            logger.warning("⚠️ Update: Document not modified (might be unchanged)")
        
        # Read - Verify update
        updated_doc = collection.find_one({"_id": doc_id})
        if updated_doc and updated_doc.get("notes") == "Added during Atlas test":
            logger.info(f"✅ Read: Update verified with new field 'notes': {updated_doc.get('notes')}")
        else:
            logger.error("❌ Read: Could not verify update")
            return False
        
        # Delete - Remove test document
        delete_result = collection.delete_one({"_id": doc_id})
        if delete_result.deleted_count == 1:
            logger.info("✅ Delete: Removed test document successfully")
        else:
            logger.error("❌ Delete: Failed to remove test document")
            return False
        
        # Verify deletion
        if not collection.find_one({"_id": doc_id}):
            logger.info("✅ Verified document deletion")
        else:
            logger.error("❌ Document still exists after deletion attempt")
            return False
        
        # Get total document count
        doc_count = collection.count_documents({})
        logger.info(f"Total documents in collection: {doc_count}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Document operation failed: {e}")
        return False

def main():
    """Main test function"""
    logger.info("=" * 50)
    logger.info("MongoDB Atlas Connection Test")
    logger.info("=" * 50)
    
    client = None
    try:
        # Test connection
        client = test_atlas_connection()
        
        # Test database operations
        collection = test_database_operations(client)
        
        # Test document operations
        success = test_document_operations(collection)
        
        # Summary
        logger.info("=" * 50)
        if success:
            logger.info("✅ All MongoDB Atlas tests completed successfully!")
        else:
            logger.warning("⚠️ Some MongoDB Atlas tests failed. Check logs for details.")
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
    finally:
        # Close connection
        if client:
            client.close()
            logger.info("MongoDB Atlas connection closed")

if __name__ == "__main__":
    main() 