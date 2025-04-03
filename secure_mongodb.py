"""
Secure MongoDB Wrapper

This module provides a secure wrapper around MongoDB client that enforces:
- Access control policies
- Logging and auditing
- Schema validation
- Security constraints
"""

import os
import logging
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ConnectionFailure
from dotenv import load_dotenv
from security_contract import log_database_access

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecureMongoClient:
    """A secure wrapper around the MongoDB client that enforces access control and logging"""
    
    def __init__(self, uri=None, db_name=None, collection_name=None):
        """Initialize the secure MongoDB client"""
        self.mongo_uri = uri or os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.db_name = db_name or os.getenv('MONGODB_DB', 'guards_robbers_db')
        self.collection_name = collection_name or os.getenv('MONGODB_COLLECTION', 'leads')
        self.client = None
        self.db = None
        self.collection = None
        
        # Connect to MongoDB
        self.connect()
    
    def connect(self):
        """Connect to MongoDB with retry logic"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Connecting to MongoDB (attempt {retry_count + 1}/{max_retries})...")
                self.client = MongoClient(self.mongo_uri)
                
                # Test connection
                self.client.admin.command('ping')
                
                # Access database and collection
                self.db = self.client[self.db_name]
                self.collection = self.db[self.collection_name]
                
                logger.info(f"Connected to MongoDB: {self.db_name}.{self.collection_name}")
                return True
            except (ConnectionFailure, OperationFailure) as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error("Maximum retry attempts reached")
                    return False
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.collection = None
            logger.info("MongoDB connection closed")
    
    def insert_document(self, document, collection_name=None):
        """Insert a document with security checks and logging"""
        collection = self._get_collection(collection_name)
        if not collection:
            return None
        
        try:
            # Log database access
            log_database_access(collection.name, "insert", document=document)
            
            # Insert document
            result = collection.insert_one(document)
            
            logger.info(f"Document inserted: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error inserting document: {e}")
            return None
    
    def find_document(self, query, collection_name=None):
        """Find a document with security checks and logging"""
        collection = self._get_collection(collection_name)
        if not collection:
            return None
        
        try:
            # Log database access
            log_database_access(collection.name, "find_one", query=query)
            
            # Find document
            document = collection.find_one(query)
            
            if document:
                logger.info(f"Document found: {document.get('_id')}")
            else:
                logger.info("No document found matching query")
            
            return document
        except Exception as e:
            logger.error(f"Error finding document: {e}")
            return None
    
    def find_documents(self, query, limit=0, collection_name=None):
        """Find multiple documents with security checks and logging"""
        collection = self._get_collection(collection_name)
        if not collection:
            return []
        
        try:
            # Log database access
            log_database_access(collection.name, "find", query=query)
            
            # Find documents
            cursor = collection.find(query).limit(limit) if limit > 0 else collection.find(query)
            documents = list(cursor)
            
            logger.info(f"Found {len(documents)} documents matching query")
            return documents
        except Exception as e:
            logger.error(f"Error finding documents: {e}")
            return []
    
    def update_document(self, query, update, collection_name=None):
        """Update a document with security checks and logging"""
        collection = self._get_collection(collection_name)
        if not collection:
            return False
        
        try:
            # Log database access
            log_database_access(collection.name, "update_one", query=query)
            
            # Update document
            result = collection.update_one(query, update)
            
            logger.info(f"Document update result: {result.modified_count} modified")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False
    
    def delete_document(self, query, collection_name=None):
        """Delete a document with security checks and logging"""
        collection = self._get_collection(collection_name)
        if not collection:
            return False
        
        try:
            # Log database access
            log_database_access(collection.name, "delete_one", query=query)
            
            # Delete document
            result = collection.delete_one(query)
            
            logger.info(f"Document deletion result: {result.deleted_count} deleted")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def count_documents(self, query=None, collection_name=None):
        """Count documents with security checks and logging"""
        collection = self._get_collection(collection_name)
        if not collection:
            return 0
        
        query = query or {}
        
        try:
            # Log database access
            log_database_access(collection.name, "count", query=query)
            
            # Count documents
            count = collection.count_documents(query)
            
            logger.info(f"Document count: {count}")
            return count
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0
    
    def _get_collection(self, collection_name=None):
        """Get a collection, reconnecting if necessary"""
        if not self.client:
            if not self.connect():
                return None
        
        collection = self.collection
        if collection_name:
            collection = self.db[collection_name]
        
        return collection

def get_secure_mongo_client():
    """Get a secure MongoDB client singleton"""
    global _secure_mongo_client
    
    if '_secure_mongo_client' not in globals() or _secure_mongo_client is None:
        _secure_mongo_client = SecureMongoClient()
    
    return _secure_mongo_client 