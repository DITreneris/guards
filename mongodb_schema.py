"""
MongoDB Schema Validation for Guards & Robbers

This script contains the schema validation rules for MongoDB collections
and functions to apply those rules to the database.
"""

import os
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import OperationFailure

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGODB_DB = os.getenv('MONGODB_DB', 'guards_robbers_db')

# Schema validation for leads collection
LEADS_SCHEMA = {
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["company", "name", "email", "network", "timestamp", "status"],
            "properties": {
                "company": {
                    "bsonType": "string",
                    "description": "Company name is required and must be a string"
                },
                "name": {
                    "bsonType": "string",
                    "description": "Contact name is required and must be a string"
                },
                "email": {
                    "bsonType": "string",
                    "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                    "description": "Email address is required and must be a valid email format"
                },
                "network": {
                    "enum": ["on-premise", "cloud", "hybrid"],
                    "description": "Network type must be one of: on-premise, cloud, hybrid"
                },
                "phone": {
                    "bsonType": ["string", "null"],
                    "description": "Phone number must be a string if provided"
                },
                "company_size": {
                    "bsonType": ["string", "null"],
                    "description": "Company size must be a string if provided"
                },
                "message": {
                    "bsonType": ["string", "null"],
                    "description": "Message must be a string if provided"
                },
                "status": {
                    "bsonType": "string",
                    "description": "Lead status is required and must be a string"
                },
                "timestamp": {
                    "bsonType": "date",
                    "description": "Timestamp is required and must be a date"
                },
                "source": {
                    "bsonType": ["string", "null"],
                    "description": "Lead source must be a string if provided"
                },
                "campaign": {
                    "bsonType": ["string", "null"],
                    "description": "Campaign identifier must be a string if provided"
                },
                "tags": {
                    "bsonType": ["array", "null"],
                    "description": "Tags must be an array of strings if provided",
                    "items": {
                        "bsonType": "string"
                    }
                }
            }
        }
    },
    "validationLevel": "moderate",
    "validationAction": "warn"
}

def apply_schema_validation():
    """Apply schema validation to MongoDB collections"""
    try:
        # Connect to MongoDB
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_DB]
        logger.info(f"Connected to database: {MONGODB_DB}")
        
        # Check if leads collection exists
        collection_names = db.list_collection_names()
        
        if "leads" in collection_names:
            # Collection exists, modify validation schema
            logger.info("Leads collection exists, updating schema validation")
            try:
                db.command({
                    "collMod": "leads",
                    **LEADS_SCHEMA
                })
                logger.info("✅ Schema validation updated for leads collection")
            except OperationFailure as e:
                logger.error(f"Failed to update schema validation: {e}")
        else:
            # Create collection with validation schema
            logger.info("Leads collection does not exist, creating with schema validation")
            db.create_collection("leads", **LEADS_SCHEMA)
            
            # Create indexes
            db.leads.create_index("email", unique=True)
            db.leads.create_index("timestamp")
            db.leads.create_index("status")
            
            logger.info("✅ Created leads collection with schema validation and indexes")
        
        # Check validation status
        collection_info = db.command("listCollections", filter={"name": "leads"})
        validation_info = next(iter(collection_info["cursor"]["firstBatch"]))
        
        if "options" in validation_info and "validator" in validation_info["options"]:
            logger.info("✅ Validation schema is applied to leads collection")
        else:
            logger.warning("⚠️ Validation schema not found on leads collection")
        
        return True
    except Exception as e:
        logger.error(f"❌ Schema validation setup failed: {e}")
        return False
    finally:
        client.close()
        logger.info("MongoDB connection closed")

if __name__ == "__main__":
    logger.info("=== Applying MongoDB Schema Validation ===")
    success = apply_schema_validation()
    
    if success:
        logger.info("Schema validation setup completed successfully")
    else:
        logger.error("Schema validation setup failed") 