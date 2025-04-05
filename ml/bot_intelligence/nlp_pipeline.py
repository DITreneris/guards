#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NLP Pipeline for Bot Intelligence
Processes text for intent recognition, sentiment analysis, and other NLP tasks.
"""

import re
import uuid
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

from ml.config import get_nlp_config
from ml.models.intent_recognition import default_model as intent_model
from ml.models.model_loader import sentiment_model
from ml.storage import conversation_storage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NLPPipeline:
    """
    Natural Language Processing pipeline for analyzing user input.
    """
    
    def __init__(self, config=None):
        """
        Initialize NLP pipeline with configuration.
        
        Args:
            config: Optional custom configuration
        """
        logger.info("Initializing NLP Pipeline")
        self.config = config or get_nlp_config()
        self.preprocessing_config = self.config.get("preprocessing", {})
        
        # Initialize pipeline configuration
        self.lowercase = self.preprocessing_config.get("lowercase", True)
        self.remove_punctuation = self.preprocessing_config.get("remove_punctuation", True)
        self.remove_stopwords = self.preprocessing_config.get("remove_stopwords", True)
        
        logger.info(f"NLP Pipeline configured with preprocessing: "
                   f"lowercase={self.lowercase}, "
                   f"remove_punctuation={self.remove_punctuation}, "
                   f"remove_stopwords={self.remove_stopwords}")
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text according to configuration.
        
        Args:
            text: Text to preprocess
            
        Returns:
            Preprocessed text
        """
        # Apply preprocessing steps
        if self.lowercase:
            text = text.lower()
        
        if self.remove_punctuation:
            text = re.sub(r'[^\w\s]', '', text)
        
        if self.remove_stopwords:
            # Simple English stopword list
            stopwords = {
                'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 
                'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 
                'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 
                'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 
                'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 
                'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 
                'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 
                'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 
                'with', 'about', 'against', 'between', 'into', 'through', 'during', 
                'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 
                'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 
                'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 
                'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 
                'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very'
            }
            
            # Split, filter, and re-join
            words = text.split()
            filtered_words = [word for word in words if word.lower() not in stopwords]
            text = ' '.join(filtered_words)
        
        return text
    
    def process_text(self, text: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process text through NLP pipeline.
        
        Args:
            text: Text to process
            conversation_id: Optional conversation ID for context
            
        Returns:
            Dictionary with analysis results
        """
        analysis_id = str(uuid.uuid4())
        
        # Preprocess text for analysis (not affecting original text)
        preprocessed_text = self.preprocess_text(text)
        
        # Initialize analysis results
        analysis = {
            "id": analysis_id,
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "preprocessed_text": preprocessed_text,
            "conversation_id": conversation_id
        }
        
        # Recognize intent
        intent_result = intent_model.recognize_intent(text)
        analysis["intent"] = {
            "intent": intent_result.intent,
            "confidence": intent_result.confidence,
            "method": intent_result.method,
            "alternatives": [{"intent": i, "confidence": c} for i, c in intent_result.alternatives]
        }
        
        # Analyze sentiment
        sentiment_result = sentiment_model.analyze_sentiment(text)
        analysis["sentiment"] = sentiment_result
        
        # Store analysis results if conversation_id is provided
        if conversation_id:
            self._store_analysis(conversation_id, analysis)
            logger.info(f"Stored analysis results for conversation {conversation_id}")
        
        logger.info(f"Completed text analysis for ID {analysis_id}")
        return analysis
    
    def _store_analysis(self, conversation_id: str, analysis: Dict[str, Any]) -> bool:
        """
        Store analysis results in conversation storage.
        
        Args:
            conversation_id: Conversation ID
            analysis: Analysis results
            
        Returns:
            True if successful, False otherwise
        """
        if conversation_storage:
            try:
                # Load existing conversation data
                conversation_data = conversation_storage.load_conversation(conversation_id)
                
                # If conversation doesn't exist, create basic structure
                if not conversation_data:
                    conversation_data = {
                        "id": conversation_id,
                        "messages": [],
                        "analysis_results": []
                    }
                
                # Add analysis to results
                if "analysis_results" not in conversation_data:
                    conversation_data["analysis_results"] = []
                    
                conversation_data["analysis_results"].append(analysis)
                
                # Save updated conversation data
                return conversation_storage.save_conversation(conversation_id, conversation_data)
            except Exception as e:
                logger.error(f"Error storing analysis: {e}")
                return False
        else:
            logger.warning("Conversation storage not available")
            return False

# Create default pipeline instance
default_pipeline = NLPPipeline()

# Example usage
if __name__ == "__main__":
    # Initialize the pipeline
    pipeline = NLPPipeline()
    
    # Test with some example messages
    test_messages = [
        "Hello! I'm interested in your security services",
        "What are your pricing options?",
        "Can you tell me about your monitoring features?",
        "I need help with my account",
        "This is a very complicated request that should trigger human review",
        "I'm really unhappy with the service quality",
        "Thank you for your help! Goodbye!"
    ]
    
    for message in test_messages:
        result = pipeline.process_text(message)
        print(f"\nInput: {message}")
        print(f"Intent: {result['intent']['intent']}")
        print(f"Confidence: {result['intent']['confidence']:.2f}")
        print(f"Sentiment: {result['sentiment']['overall']} ({result['sentiment']['score']:.2f})")
        print(f"Conversation ID: {result['conversation_id']}") 