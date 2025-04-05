"""
Simplified Guards & Robbers Communication Bot

This module implements a basic version of the communication bot with minimal dependencies.

Version: 1.0.0
Created: May 16, 2025
"""

import json
import logging
import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("communication_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("simple_bot")

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

class SimpleNLP:
    """
    Simple NLP engine using keyword matching and regular expressions
    """
    
    def __init__(self):
        """Initialize the NLP engine"""
        self.intent_patterns = {
            "greeting": r"\b(hi|hello|hey|greetings)\b",
            "farewell": r"\b(bye|goodbye|farewell|see you)\b",
            "pricing": r"\b(price|cost|pricing|how much)\b",
            "feature": r"\b(feature|capability|can it|does it)\b",
            "support": r"\b(help|issue|problem|support)\b",
            "schedule": r"\b(schedule|book|appointment|demo|meeting)\b"
        }
        
        # Load knowledge base
        try:
            with open("knowledge_base.json", "r") as f:
                self.knowledge_base = json.load(f)
        except FileNotFoundError:
            logger.warning("Knowledge base not found")
            self.knowledge_base = {}
        
        logger.info("Simple NLP initialized")
    
    def get_intent(self, text: str) -> tuple:
        """
        Get the intent from text using regex patterns
        
        Returns:
            Tuple of (intent, confidence)
        """
        text = text.lower()
        max_confidence = 0
        best_intent = "unknown"
        
        for intent, pattern in self.intent_patterns.items():
            matches = re.findall(pattern, text)
            confidence = len(matches) / (len(text.split()) + 1)  # Simple confidence score
            
            if confidence > max_confidence:
                max_confidence = confidence
                best_intent = intent
        
        return best_intent, max_confidence

class SimpleBot:
    """
    Simplified communication bot using basic pattern matching
    """
    
    def __init__(self):
        """Initialize the bot"""
        self.nlp = SimpleNLP()
        self.conversation_history = {}
        
        # Default templates
        self.default_templates = {
            "greeting": "Hello! How can I help you with our security services today?",
            "farewell": "Thank you for contacting Guards & Robbers. Have a great day!",
            "pricing": "I'd be happy to provide information about our pricing options. Our security services are tailored to your specific needs.",
            "feature": "Our security system includes advanced features. Would you like more details about any specific capability?",
            "support": "I'm sorry to hear you're experiencing an issue. Could you please provide more details about the problem?",
            "schedule": "I can help you schedule a consultation. When would you like to meet?",
            "unknown": "I'm not sure I understand. Could you please rephrase your question? I'm here to help with information about our security services."
        }
        
        # Load response templates
        try:
            with open("response_templates.json", "r") as f:
                self.templates = json.load(f)
        except FileNotFoundError:
            logger.warning("Templates not found, using defaults")
            self.templates = self.default_templates.copy()
        
        # Ensure unknown template exists
        if "unknown" not in self.templates:
            self.templates["unknown"] = self.default_templates["unknown"]
        
        logger.info("Simple Bot initialized")
    
    def process_message(self, message: Message) -> Response:
        """
        Process a message and generate a response
        
        Args:
            message: Message object to process
            
        Returns:
            Response object
        """
        # Get intent
        intent, confidence = self.nlp.get_intent(message.content)
        
        # Get response template
        response_content = self.templates.get(intent, self.templates["unknown"])
        
        # Try to get more specific content from knowledge base
        if intent in self.nlp.knowledge_base:
            kb_content = self.nlp.knowledge_base[intent].get("general")
            if kb_content:
                response_content = kb_content
        
        # Create response
        response = Response(
            content=response_content,
            recipient=message.sender,
            channel=message.channel,
            confidence=confidence,
            requires_human_review=confidence < 0.3,
            metadata={"intent": intent}
        )
        
        # Update conversation history
        if message.sender not in self.conversation_history:
            self.conversation_history[message.sender] = []
        
        self.conversation_history[message.sender].append({
            "message": message.content,
            "response": response.content,
            "timestamp": message.timestamp.isoformat(),
            "intent": intent,
            "confidence": confidence
        })
        
        # Keep only last 10 messages
        if len(self.conversation_history[message.sender]) > 10:
            self.conversation_history[message.sender] = self.conversation_history[message.sender][-10:]
        
        return response
    
    def get_conversation_history(self, sender: str) -> List[Dict]:
        """Get conversation history for a sender"""
        return self.conversation_history.get(sender, [])


def test_bot():
    """Test the bot with various scenarios"""
    print("Testing Simple Bot...")
    print("=" * 50)
    
    # Initialize bot
    bot = SimpleBot()
    
    # Test messages
    test_messages = [
        "Hello! I'm interested in your security services",
        "What are your pricing options?",
        "Can you tell me about your monitoring features?",
        "I need help with my account",
        "Can we schedule a demo?",
        "This is a random message",
        "Goodbye!"
    ]
    
    # Process each message
    for msg in test_messages:
        print(f"\nInput: {msg}")
        
        message = Message(
            content=msg,
            sender="test@example.com",
            channel="email"
        )
        
        response = bot.process_message(message)
        
        print(f"Intent: {response.metadata['intent']}")
        print(f"Confidence: {response.confidence:.2f}")
        print(f"Response: {response.content}")
        print(f"Requires review: {response.requires_human_review}")
        print("-" * 50)
    
    # Test conversation history
    print("\nConversation History:")
    history = bot.get_conversation_history("test@example.com")
    for entry in history:
        print(f"Time: {entry['timestamp']}")
        print(f"Message: {entry['message']}")
        print(f"Response: {entry['response']}")
        print(f"Intent: {entry['intent']}")
        print(f"Confidence: {entry['confidence']:.2f}")
        print("---")

if __name__ == "__main__":
    test_bot() 