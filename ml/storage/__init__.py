"""
Storage Module
This module handles data storage for the ML Framework.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from ml.config import get_storage_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Storage:
    """Base storage class for ML data."""
    
    def __init__(self, storage_path: str):
        """
        Initialize storage.
        
        Args:
            storage_path: Path to store data
        """
        self.storage_path = storage_path
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self) -> None:
        """Ensure the storage directory exists."""
        try:
            os.makedirs(self.storage_path, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating storage directory {self.storage_path}: {e}")
    
    def _get_file_path(self, item_id: str) -> str:
        """
        Get the file path for an item.
        
        Args:
            item_id: ID of the item
            
        Returns:
            File path for the item
        """
        return os.path.join(self.storage_path, f"{item_id}.json")
    
    def save(self, item_id: str, data: Dict[str, Any]) -> bool:
        """
        Save data to storage.
        
        Args:
            item_id: ID of the item
            data: Data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self._get_file_path(item_id)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved data to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving data to {file_path}: {e}")
            return False
    
    def load(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Load data from storage.
        
        Args:
            item_id: ID of the item
            
        Returns:
            Loaded data, or None if the load failed
        """
        try:
            file_path = self._get_file_path(item_id)
            if not os.path.exists(file_path):
                logger.warning(f"File not found at {file_path}")
                return None
                
            with open(file_path, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded data from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {e}")
            return None
    
    def delete(self, item_id: str) -> bool:
        """
        Delete data from storage.
        
        Args:
            item_id: ID of the item
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self._get_file_path(item_id)
            if not os.path.exists(file_path):
                logger.warning(f"File not found at {file_path}")
                return False
                
            os.remove(file_path)
            logger.info(f"Deleted data from {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting data from {file_path}: {e}")
            return False
    
    def list_items(self) -> List[str]:
        """
        List all items in storage.
        
        Returns:
            List of item IDs
        """
        try:
            files = os.listdir(self.storage_path)
            item_ids = [os.path.splitext(file)[0] for file in files if file.endswith('.json')]
            return item_ids
        except Exception as e:
            logger.error(f"Error listing items in {self.storage_path}: {e}")
            return []


class ConversationStorage(Storage):
    """Storage for conversation data."""
    
    def __init__(self):
        """Initialize conversation storage."""
        storage_config = get_storage_config()
        storage_path = storage_config.get('conversation_storage_path', 'data/conversations')
        super().__init__(storage_path)
    
    def save_conversation(self, conversation_dict: Dict[str, Any]) -> bool:
        """
        Save a conversation.
        
        Args:
            conversation_dict: Conversation data to save
            
        Returns:
            True if successful, False otherwise
        """
        conversation_id = conversation_dict.get('id')
        if not conversation_id:
            logger.error("No conversation ID provided")
            return False
        
        return self.save(conversation_id, conversation_dict)
    
    def load_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Conversation data, or None if the load failed
        """
        return self.load(conversation_id)


class EmailStorage(Storage):
    """Storage for email data."""
    
    def __init__(self):
        """Initialize email storage."""
        storage_config = get_storage_config()
        storage_path = storage_config.get('email_storage_path', 'data/emails')
        super().__init__(storage_path)
    
    def save_email(self, email_dict: Dict[str, Any]) -> bool:
        """
        Save an email.
        
        Args:
            email_dict: Email data to save
            
        Returns:
            True if successful, False otherwise
        """
        email_id = email_dict.get('id')
        if not email_id:
            logger.error("No email ID provided")
            return False
        
        return self.save(email_id, email_dict)
    
    def load_email(self, email_id: str) -> Optional[Dict[str, Any]]:
        """
        Load an email.
        
        Args:
            email_id: ID of the email
            
        Returns:
            Email data, or None if the load failed
        """
        return self.load(email_id)


class ExtractionStorage(Storage):
    """Storage for data extraction results."""
    
    def __init__(self):
        """Initialize extraction storage."""
        storage_config = get_storage_config()
        storage_path = storage_config.get('extraction_storage_path', 'data/extractions')
        super().__init__(storage_path)
    
    def save_extraction(self, extraction_dict: Dict[str, Any]) -> bool:
        """
        Save an extraction result.
        
        Args:
            extraction_dict: Extraction data to save
            
        Returns:
            True if successful, False otherwise
        """
        extraction_id = extraction_dict.get('id')
        if not extraction_id:
            logger.error("No extraction ID provided")
            return False
        
        return self.save(extraction_id, extraction_dict)
    
    def load_extraction(self, extraction_id: str) -> Optional[Dict[str, Any]]:
        """
        Load an extraction result.
        
        Args:
            extraction_id: ID of the extraction
            
        Returns:
            Extraction data, or None if the load failed
        """
        return self.load(extraction_id)


# Create default instances
conversation_storage = ConversationStorage()
email_storage = EmailStorage()
extraction_storage = ExtractionStorage() 