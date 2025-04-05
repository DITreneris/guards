"""
Guards & Robbers Communication Bot

This module implements the core functionality of the communication bot,
including NLP processing, response generation, and integration management.

Version: 1.0.0
Created: May 16, 2025
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("communication_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("communication_bot")

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

@dataclass
class Message:
    """Data class for storing message information"""
    content: str
    sender: str
    channel: str  # email, chat, support_ticket
    timestamp: datetime.datetime = datetime.datetime.now()
    message_id: Optional[str] = None
    context: Optional[Dict] = None
    metadata: Optional[Dict] = None

@dataclass
class Response:
    """Data class for storing response information"""
    content: str
    recipient: str
    channel: str
    timestamp: datetime.datetime = datetime.datetime.now()
    response_id: Optional[str] = None
    confidence: float = 1.0
    requires_human_review: bool = False
    metadata: Optional[Dict] = None

class NLPEngine:
    """
    Natural Language Processing engine for the communication bot.
    
    This class handles:
    1. Intent classification
    2. Entity extraction
    3. Sentiment analysis
    4. Context management
    """
    
    def __init__(self):
        """Initialize the NLP engine with required models and components"""
        # Load spaCy model for entity extraction
        self.nlp = spacy.load("en_core_web_sm")
        
        # Initialize transformers for intent classification and sentiment analysis
        self.intent_classifier = pipeline(
            "text-classification",
            model="distilbert-base-uncased",
            tokenizer="distilbert-base-uncased"
        )
        
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        
        # Initialize TF-IDF vectorizer for similarity matching
        self.vectorizer = TfidfVectorizer(
            stop_words=stopwords.words('english'),
            max_features=1000
        )
        
        # Load or create intent mapping
        self.intent_mapping = {
            "greeting": ["hello", "hi", "hey"],
            "farewell": ["goodbye", "bye", "see you"],
            "question": ["what", "how", "why", "when", "where"],
            "support": ["help", "issue", "problem", "error"],
            "pricing": ["cost", "price", "how much"],
            "feature": ["can it", "does it", "capability"],
            "schedule": ["meeting", "call", "demo", "appointment"]
        }
        
        logger.info("NLP Engine initialized")
    
    def process_message(self, message: Message) -> Dict:
        """
        Process a message through the NLP pipeline
        
        Args:
            message: Message object to process
            
        Returns:
            Dictionary with processed information
        """
        # Extract entities using spaCy
        doc = self.nlp(message.content)
        entities = {
            "people": [ent.text for ent in doc.ents if ent.label_ == "PERSON"],
            "organizations": [ent.text for ent in doc.ents if ent.label_ == "ORG"],
            "dates": [ent.text for ent in doc.ents if ent.label_ == "DATE"],
            "times": [ent.text for ent in doc.ents if ent.label_ == "TIME"]
        }
        
        # Classify intent
        intent_result = self.intent_classifier(message.content)[0]
        intent = intent_result["label"]
        intent_confidence = intent_result["score"]
        
        # Analyze sentiment
        sentiment_result = self.sentiment_analyzer(message.content)[0]
        sentiment = sentiment_result["label"]
        sentiment_score = sentiment_result["score"]
        
        # Update context
        context = message.context or {}
        context.update({
            "last_intent": intent,
            "last_entities": entities,
            "last_sentiment": sentiment,
            "timestamp": message.timestamp.isoformat()
        })
        
        return {
            "intent": intent,
            "intent_confidence": intent_confidence,
            "entities": entities,
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "context": context
        }
    
    def get_similar_intent(self, text: str) -> Tuple[str, float]:
        """
        Find the most similar intent for a given text
        
        Args:
            text: Text to classify
            
        Returns:
            Tuple of (intent, similarity_score)
        """
        # Vectorize the input text
        text_vector = self.vectorizer.transform([text])
        
        # Calculate similarity with each intent's examples
        max_similarity = 0
        best_intent = "unknown"
        
        for intent, examples in self.intent_mapping.items():
            if examples:
                examples_vector = self.vectorizer.transform(examples)
                similarity = cosine_similarity(text_vector, examples_vector).max()
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_intent = intent
        
        return best_intent, max_similarity

class ResponseGenerator:
    """
    Response generation system for the communication bot.
    
    This class handles:
    1. Template-based responses
    2. Dynamic content generation
    3. Response quality checking
    4. Brand voice consistency
    """
    
    def __init__(self):
        """Initialize the response generator"""
        # Load response templates
        self.templates = self._load_templates()
        
        # Initialize quality checker
        self.quality_checker = QualityChecker()
        
        # Initialize content generator
        self.content_generator = ContentGenerator()
        
        logger.info("Response Generator initialized")
    
    def _load_templates(self) -> Dict:
        """Load response templates from file"""
        try:
            with open("response_templates.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Template file not found, using default templates")
            return {
                "greeting": "Hello! How can I help you today?",
                "farewell": "Thank you for reaching out. Have a great day!",
                "question": "I understand you have a question about {topic}. Let me help you with that.",
                "support": "I'm sorry to hear you're experiencing an issue. Let me help you resolve this.",
                "pricing": "I'd be happy to provide information about our pricing options.",
                "feature": "Yes, our system can {feature}. Would you like more details?",
                "schedule": "I can help you schedule a {type}. When would you like to meet?",
                "fallback": "I'm not sure I understand. Could you please rephrase your question?"
            }
    
    def generate_response(self, 
                         processed_message: Dict,
                         message: Message) -> Response:
        """
        Generate a response based on the processed message
        
        Args:
            processed_message: Dictionary with processed NLP information
            message: Original message object
            
        Returns:
            Response object
        """
        intent = processed_message["intent"]
        entities = processed_message["entities"]
        context = processed_message["context"]
        
        # Get template-based response
        template = self.templates.get(intent, self.templates["fallback"])
        
        # Fill in template variables
        response_content = template
        if "{topic}" in template and entities:
            response_content = response_content.replace("{topic}", 
                entities.get("organizations", ["our services"])[0])
        if "{feature}" in template:
            response_content = response_content.replace("{feature}", 
                "that specific feature")
        if "{type}" in template:
            response_content = response_content.replace("{type}", 
                "meeting" if "meeting" in message.content.lower() else "call")
        
        # Generate dynamic content if needed
        if processed_message["intent_confidence"] < 0.7:
            dynamic_content = self.content_generator.generate(
                message.content,
                intent,
                entities,
                context
            )
            if dynamic_content:
                response_content = dynamic_content
        
        # Check response quality
        quality_check = self.quality_checker.validate(response_content)
        
        # Create response object
        response = Response(
            content=response_content,
            recipient=message.sender,
            channel=message.channel,
            confidence=processed_message["intent_confidence"],
            requires_human_review=not quality_check["is_valid"],
            metadata={
                "intent": intent,
                "quality_check": quality_check,
                "generation_method": "template" if quality_check["is_valid"] else "dynamic"
            }
        )
        
        return response

class QualityChecker:
    """
    Quality checking system for bot responses.
    
    This class handles:
    1. Grammar and spelling validation
    2. Brand voice consistency
    3. Response relevance scoring
    4. Context awareness verification
    """
    
    def __init__(self):
        """Initialize the quality checker"""
        # Load brand voice guidelines
        self.brand_voice = {
            "tone": "professional",
            "style": "clear and concise",
            "formality": "business casual",
            "key_phrases": ["Guards & Robbers", "security", "protection"]
        }
        
        # Initialize grammar checker
        self.grammar_checker = None  # Would integrate with actual grammar checking service
        
        logger.info("Quality Checker initialized")
    
    def validate(self, response: str) -> Dict:
        """
        Validate a response against quality criteria
        
        Args:
            response: Response text to validate
            
        Returns:
            Dictionary with validation results
        """
        # Basic length check
        if len(response) < 10 or len(response) > 500:
            return {
                "is_valid": False,
                "issues": ["Response length outside acceptable range"],
                "score": 0.0
            }
        
        # Brand voice check
        voice_score = self._check_brand_voice(response)
        
        # Grammar check (placeholder)
        grammar_score = 1.0  # Would be calculated by actual grammar checker
        
        # Calculate overall score
        overall_score = (voice_score + grammar_score) / 2
        
        is_valid = overall_score >= 0.7
        
        return {
            "is_valid": is_valid,
            "issues": [] if is_valid else ["Quality score below threshold"],
            "score": overall_score
        }
    
    def _check_brand_voice(self, text: str) -> float:
        """
        Check if text matches brand voice guidelines
        
        Args:
            text: Text to check
            
        Returns:
            Score between 0 and 1
        """
        score = 0.0
        
        # Check for key phrases
        for phrase in self.brand_voice["key_phrases"]:
            if phrase.lower() in text.lower():
                score += 0.2
        
        # Check tone indicators
        tone_words = {
            "professional": ["thank you", "please", "regards"],
            "clear": ["specifically", "in other words", "to clarify"],
            "concise": ["briefly", "in short", "to summarize"]
        }
        
        for category, words in tone_words.items():
            if any(word in text.lower() for word in words):
                score += 0.1
        
        return min(score, 1.0)

class ContentGenerator:
    """
    Dynamic content generation system.
    
    This class handles:
    1. Knowledge base integration
    2. FAQ matching
    3. Context-aware responses
    4. Learning from interactions
    """
    
    def __init__(self):
        """Initialize the content generator"""
        # Load knowledge base
        self.knowledge_base = self._load_knowledge_base()
        
        # Initialize FAQ matcher
        self.faq_matcher = FAQMatcher()
        
        logger.info("Content Generator initialized")
    
    def _load_knowledge_base(self) -> Dict:
        """Load knowledge base from file"""
        try:
            with open("knowledge_base.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Knowledge base file not found")
            return {}
    
    def generate(self, 
                 message: str,
                 intent: str,
                 entities: Dict,
                 context: Dict) -> Optional[str]:
        """
        Generate dynamic content based on message and context
        
        Args:
            message: Original message text
            intent: Classified intent
            entities: Extracted entities
            context: Conversation context
            
        Returns:
            Generated response text or None if no suitable content found
        """
        # Try FAQ matching first
        faq_response = self.faq_matcher.find_match(message)
        if faq_response:
            return faq_response
        
        # Search knowledge base
        if intent in self.knowledge_base:
            topic_content = self.knowledge_base[intent]
            
            # If entities match specific content, use that
            if entities.get("organizations"):
                org = entities["organizations"][0]
                if org in topic_content:
                    return topic_content[org]
            
            # Otherwise use general content
            return topic_content.get("general", None)
        
        return None

class FAQMatcher:
    """
    FAQ matching system for finding relevant answers.
    """
    
    def __init__(self):
        """Initialize the FAQ matcher"""
        # Load FAQs
        self.faqs = self._load_faqs()
        
        # Initialize TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            stop_words=stopwords.words('english'),
            max_features=1000
        )
        
        # Vectorize FAQ questions
        self.faq_vectors = None
        self._vectorize_faqs()
        
        logger.info("FAQ Matcher initialized")
    
    def _load_faqs(self) -> List[Dict]:
        """Load FAQs from file"""
        try:
            with open("faqs.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("FAQ file not found")
            return []
    
    def _vectorize_faqs(self) -> None:
        """Vectorize FAQ questions for similarity matching"""
        if self.faqs:
            questions = [faq["question"] for faq in self.faqs]
            self.vectorizer.fit(questions)
            self.faq_vectors = self.vectorizer.transform(questions)
    
    def find_match(self, message: str) -> Optional[str]:
        """
        Find the best matching FAQ for a message
        
        Args:
            message: Message text to match
            
        Returns:
            FAQ answer if good match found, None otherwise
        """
        if not self.faqs or not self.faq_vectors:
            return None
        
        # Vectorize the message
        message_vector = self.vectorizer.transform([message])
        
        # Calculate similarity with all FAQs
        similarities = cosine_similarity(message_vector, self.faq_vectors)[0]
        
        # Get best match
        best_match_idx = np.argmax(similarities)
        best_similarity = similarities[best_match_idx]
        
        # Return answer if similarity is high enough
        if best_similarity > 0.7:
            return self.faqs[best_match_idx]["answer"]
        
        return None

class CommunicationBot:
    """
    Main communication bot class that coordinates all components.
    
    This class:
    1. Processes incoming messages
    2. Generates appropriate responses
    3. Manages conversation context
    4. Handles integration with external systems
    """
    
    def __init__(self):
        """Initialize the communication bot"""
        self.nlp_engine = NLPEngine()
        self.response_generator = ResponseGenerator()
        self.conversation_history: Dict[str, List[Dict]] = {}
        
        logger.info("Communication Bot initialized")
    
    def process_message(self, message: Message) -> Response:
        """
        Process an incoming message and generate a response
        
        Args:
            message: Message object to process
            
        Returns:
            Response object
        """
        # Get conversation history
        history = self.conversation_history.get(message.sender, [])
        
        # Process message through NLP
        processed = self.nlp_engine.process_message(message)
        
        # Generate response
        response = self.response_generator.generate_response(processed, message)
        
        # Update conversation history
        history.append({
            "message": message.content,
            "response": response.content,
            "timestamp": message.timestamp.isoformat(),
            "intent": processed["intent"],
            "confidence": processed["intent_confidence"]
        })
        
        # Keep only last 10 messages in history
        if len(history) > 10:
            history = history[-10:]
        
        self.conversation_history[message.sender] = history
        
        return response
    
    def get_conversation_history(self, sender: str) -> List[Dict]:
        """
        Get conversation history for a sender
        
        Args:
            sender: Sender identifier
            
        Returns:
            List of conversation messages
        """
        return self.conversation_history.get(sender, [])


# Example usage
if __name__ == "__main__":
    # Initialize the bot
    bot = CommunicationBot()
    
    # Example message
    message = Message(
        content="Hi, I'm interested in your security services. Can you tell me more about your pricing?",
        sender="customer@example.com",
        channel="email"
    )
    
    # Process message and get response
    response = bot.process_message(message)
    
    print(f"Original message: {message.content}")
    print(f"Generated response: {response.content}")
    print(f"Confidence: {response.confidence:.2f}")
    print(f"Requires human review: {response.requires_human_review}") 