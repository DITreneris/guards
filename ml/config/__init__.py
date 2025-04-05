"""
Configuration Module for ML Framework
Handles loading and accessing configuration settings.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default config path
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'ml_config.json')

class ConfigLoader:
    """Singleton class to load and access configuration."""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """Ensure only one instance of ConfigLoader exists."""
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._config = cls._instance._load_config()
            cls._instance._create_storage_directories()
        return cls._instance
    
    def _load_config(self, config_path: str = "ml/config/ml_config.json") -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    logger.info(f"Loaded configuration from {config_path}")
                    return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Using default configuration")
            
        return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """
        Create default configuration.
        
        Returns:
            Default configuration dictionary
        """
        default_config = {
            "version": "0.1.0",
            "storage_paths": {
                "conversation_storage_path": "data/conversations",
                "email_storage_path": "data/emails",
                "extraction_storage_path": "data/extractions"
            },
            "nlp": {
                "preprocessing": {
                    "lowercase": True,
                    "remove_punctuation": False,
                    "remove_stopwords": False
                },
                "intent_recognition": {
                    "confidence_threshold": 0.5,
                    "regex_patterns": {
                        "greeting": [
                            "hello", "hi", "hey", "greetings", "welcome"
                        ],
                        "help": [
                            "help", "assist", "support", "how do I", "how to"
                        ],
                        "setup": [
                            "setup", "configure", "install", "deployment"
                        ],
                        "error": [
                            "error", "issue", "problem", "not working", "fail"
                        ],
                        "feature": [
                            "feature", "functionality", "capability", "can it"
                        ],
                        "pricing": [
                            "price", "cost", "billing", "subscription", "pay"
                        ]
                    },
                    "ml_model_path": "models/intent_classifier.pkl"
                },
                "sentiment_analysis": {
                    "enabled": True,
                    "model_type": "rule-based",
                    "ml_model_path": "models/sentiment_analyzer.pkl"
                }
            },
            "email_processing": {
                "extract_attachments": True,
                "extract_html": True,
                "detect_auto_replies": True,
                "url_extraction": True,
                "client_matching": True,
                "thread_detection": True,
                "priority_calculation": True,
                "categorization": {
                    "enabled": True,
                    "ml_model_path": "models/email_categorizer.pkl"
                }
            },
            "data_extraction": {
                "extraction_methods": {
                    "regex": True,
                    "pattern_matching": True,
                    "dictionary_lookup": True
                },
                "confidence_thresholds": {
                    "high": 0.8,
                    "medium": 0.5,
                    "low": 0.3
                },
                "validation": {
                    "threshold": 0.6,
                    "enable_automated_validation": True
                }
            }
        }
        
        logger.info("Created default configuration")
        return default_config
    
    def _create_storage_directories(self) -> None:
        """Create storage directories if they don't exist."""
        for path_key, path in self.get_storage_config().items():
            try:
                os.makedirs(path, exist_ok=True)
                logger.info(f"Ensured storage directory exists: {path}")
            except Exception as e:
                logger.error(f"Error creating storage directory {path}: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the complete configuration.
        
        Returns:
            Configuration dictionary
        """
        return self._config
    
    def get_nlp_config(self) -> Dict[str, Any]:
        """
        Get NLP configuration.
        
        Returns:
            NLP configuration section
        """
        return self._config.get("nlp", {})
    
    def get_email_config(self) -> Dict[str, Any]:
        """
        Get email processing configuration.
        
        Returns:
            Email processing configuration section
        """
        return self._config.get("email_processing", {})
    
    def get_data_extraction_config(self) -> Dict[str, Any]:
        """
        Get data extraction configuration.
        
        Returns:
            Data extraction configuration section
        """
        return self._config.get("data_extraction", {})
    
    def get_storage_config(self) -> Dict[str, str]:
        """
        Get storage paths configuration.
        
        Returns:
            Storage paths configuration section
        """
        return self._config.get("storage_paths", {})


# Create a single instance of the config loader
_config_loader = ConfigLoader()

# Convenience functions to access configuration
def get_config() -> Dict[str, Any]:
    """Get the complete configuration."""
    return _config_loader.get_config()

def get_nlp_config() -> Dict[str, Any]:
    """Get NLP configuration."""
    return _config_loader.get_nlp_config()

def get_email_config() -> Dict[str, Any]:
    """Get email processing configuration."""
    return _config_loader.get_email_config()

def get_data_extraction_config() -> Dict[str, Any]:
    """Get data extraction configuration."""
    return _config_loader.get_data_extraction_config()

def get_storage_config() -> Dict[str, str]:
    """Get storage paths configuration."""
    return _config_loader.get_storage_config() 