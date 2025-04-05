#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Conversation State Management System for Bot Intelligence Enhancement
This module manages the state and context of bot conversations.
"""

import uuid
import json
import time
import logging
from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

from ml.bot_intelligence.nlp_pipeline import default_pipeline as nlp_pipeline
from ml.storage import conversation_storage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConversationState(Enum):
    """Enumeration of possible conversation states."""
    NEW = "new"
    GREETING = "greeting"
    INFORMATION_GATHERING = "information_gathering"
    PRODUCT_INQUIRY = "product_inquiry"
    PRICING_INQUIRY = "pricing_inquiry"
    SUPPORT_REQUEST = "support_request"
    WAITING_FOR_RESPONSE = "waiting_for_response"
    HUMAN_HANDOFF = "human_handoff"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

@dataclass
class Message:
    """Represents a single message in a conversation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    sender: str = "user"  # "user" or "bot"
    content: str = ""
    intent: str = "unknown"
    confidence: float = 0.0
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    requires_human_review: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

@dataclass
class ClientProfile:
    """Information collected about the client during conversation."""
    client_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    interests: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    # Track extracted entity information
    entities: Dict[str, Any] = field(default_factory=dict)
    
    def update_from_message(self, message: Message) -> None:
        """
        Update profile with information extracted from a message.
        This is a placeholder - in production, would use NER to extract entities.
        
        Args:
            message: Message to extract information from
        """
        # Simple email pattern matching
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, message.content)
        if email_match and not self.email:
            self.email = email_match.group(0)
            logger.info(f"Extracted email: {self.email}")
        
        # Update interests based on intent
        if message.intent in ["feature", "product_inquiry"] and message.confidence > 0.3:
            # Extract keywords that might indicate product interests
            keywords = ["security", "monitoring", "protection", "guard", "detection", 
                      "analysis", "scanning", "assessment", "compliance"]
            for keyword in keywords:
                if keyword in message.content.lower() and keyword not in self.interests:
                    self.interests.append(keyword)
                    logger.info(f"Added interest: {keyword}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

@dataclass
class Conversation:
    """Represents a full conversation between a user and the bot."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    state: ConversationState = ConversationState.NEW
    messages: List[Message] = field(default_factory=list)
    client_profile: ClientProfile = field(default_factory=ClientProfile)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: Message) -> None:
        """
        Add a message to the conversation and update state.
        
        Args:
            message: Message to add
        """
        self.messages.append(message)
        self.updated_at = time.time()
        
        # Update client profile with any extractable information
        if message.sender == "user":
            self.client_profile.update_from_message(message)
        
        # Update conversation state based on message intent
        self._update_state(message)
    
    def _update_state(self, message: Message) -> None:
        """
        Update conversation state based on message intent.
        
        Args:
            message: Message to process for state transition
        """
        # Only process user messages for state transitions
        if message.sender != "user":
            return
        
        current_state = self.state
        intent = message.intent
        
        # State transitions
        if current_state == ConversationState.NEW:
            if intent == "greeting":
                self.state = ConversationState.GREETING
            else:
                # Skip greeting state if user starts with a specific inquiry
                if intent == "pricing":
                    self.state = ConversationState.PRICING_INQUIRY
                elif intent in ["feature", "product_inquiry"]:
                    self.state = ConversationState.PRODUCT_INQUIRY
                elif intent == "support":
                    self.state = ConversationState.SUPPORT_REQUEST
                else:
                    self.state = ConversationState.INFORMATION_GATHERING
        
        elif current_state == ConversationState.GREETING:
            if intent == "pricing":
                self.state = ConversationState.PRICING_INQUIRY
            elif intent in ["feature", "product_inquiry"]:
                self.state = ConversationState.PRODUCT_INQUIRY
            elif intent == "support":
                self.state = ConversationState.SUPPORT_REQUEST
            elif intent not in ["greeting", "farewell"]:
                self.state = ConversationState.INFORMATION_GATHERING
        
        # Check for conversation end
        if intent == "farewell":
            self.state = ConversationState.COMPLETED
        
        # Check for human handoff needed
        if message.requires_human_review:
            # Store previous state to return to after human intervention
            self.context["previous_state"] = self.state.value
            self.state = ConversationState.HUMAN_HANDOFF
        
        logger.info(f"Conversation state updated: {current_state.value} -> {self.state.value}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary."""
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "state": self.state.value,
            "messages": [msg.to_dict() for msg in self.messages],
            "client_profile": self.client_profile.to_dict(),
            "context": self.context,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """Convert conversation to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create conversation from dictionary."""
        conversation = cls(
            id=data.get("id", str(uuid.uuid4())),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            state=ConversationState(data.get("state", ConversationState.NEW.value)),
            context=data.get("context", {}),
            metadata=data.get("metadata", {})
        )
        
        # Reconstruct messages
        for msg_data in data.get("messages", []):
            message = Message(
                id=msg_data.get("id", str(uuid.uuid4())),
                timestamp=msg_data.get("timestamp", time.time()),
                sender=msg_data.get("sender", "user"),
                content=msg_data.get("content", ""),
                intent=msg_data.get("intent", "unknown"),
                confidence=msg_data.get("confidence", 0.0),
                sentiment=msg_data.get("sentiment", "neutral"),
                sentiment_score=msg_data.get("sentiment_score", 0.0),
                requires_human_review=msg_data.get("requires_human_review", False),
                metadata=msg_data.get("metadata", {})
            )
            conversation.messages.append(message)
        
        # Reconstruct client profile
        profile_data = data.get("client_profile", {})
        conversation.client_profile = ClientProfile(
            client_id=profile_data.get("client_id", str(uuid.uuid4())),
            name=profile_data.get("name"),
            email=profile_data.get("email"),
            company=profile_data.get("company"),
            interests=profile_data.get("interests", []),
            preferences=profile_data.get("preferences", {}),
            entities=profile_data.get("entities", {})
        )
        
        return conversation


class ConversationManager:
    """
    Manages conversation state and context between the bot and users.
    """
    
    def __init__(self, conversation_id: Optional[str] = None):
        """
        Initialize a new conversation manager.
        
        Args:
            conversation_id: Optional ID for existing conversation. If None, a new ID is generated.
        """
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.state = self._load_or_create_state()
        logger.info(f"Conversation manager initialized with ID: {self.conversation_id}")
    
    def _load_or_create_state(self) -> Dict[str, Any]:
        """
        Load existing conversation state or create a new one.
        
        Returns:
            Dictionary containing conversation state
        """
        # Try to load existing conversation
        if conversation_storage is not None:
            existing_conversation = conversation_storage.load_conversation(self.conversation_id)
            if existing_conversation:
                logger.info(f"Loaded existing conversation: {self.conversation_id}")
                
                # Use saved state or initialize it
                return existing_conversation.get("state", self._initialize_state())
        
        # Create new state if no existing conversation found
        return self._initialize_state()
    
    def _initialize_state(self) -> Dict[str, Any]:
        """
        Initialize a new conversation state.
        
        Returns:
            Dictionary with initial conversation state
        """
        initial_state = {
            "current_topic": None,
            "topics_discussed": set(),
            "user_profile": {
                "known_interests": set(),
                "concerns": set(),
                "detected_sentiment": None,
                "detected_satisfaction": None
            },
            "session": {
                "start_time": datetime.now().isoformat(),
                "message_count": 0,
                "last_user_message_time": None,
                "last_bot_message_time": None
            },
            "flags": {
                "needs_human_intervention": False,
                "user_frustrated": False,
                "urgent": False
            },
            "context_memory": []
        }
        
        # Convert sets to lists for JSON serialization
        initial_state["topics_discussed"] = list(initial_state["topics_discussed"])
        initial_state["user_profile"]["known_interests"] = list(initial_state["user_profile"]["known_interests"])
        initial_state["user_profile"]["concerns"] = list(initial_state["user_profile"]["concerns"])
        
        return initial_state
    
    def _save_state(self) -> bool:
        """
        Save the current conversation state.
        
        Returns:
            True if successful, False otherwise
        """
        # Create conversation object
        conversation_data = {
            "id": self.conversation_id,
            "state": self.state,
            "updated_at": datetime.now().isoformat()
        }
        
        # Save using conversation storage
        if conversation_storage is not None:
            saved = conversation_storage.save_conversation(conversation_data)
            if saved:
                logger.info(f"Saved conversation state for ID: {self.conversation_id}")
            else:
                logger.error(f"Failed to save conversation state for ID: {self.conversation_id}")
            return saved
        
        logger.warning("Conversation storage not available, state not saved")
        return False
    
    def process_message(self, message: str) -> Dict[str, Any]:
        """
        Process a user message and update conversation state.
        
        Args:
            message: User message text
            
        Returns:
            Dictionary with analysis results and updated state
        """
        # Update basic session info
        self.state["session"]["message_count"] += 1
        self.state["session"]["last_user_message_time"] = datetime.now().isoformat()
        
        # Analyze message text
        try:
            from ml.bot_intelligence.nlp_pipeline import default_pipeline as nlp_pipeline
            analysis_result = nlp_pipeline.process_text(message, self.conversation_id)
        except Exception as e:
            logger.error(f"Error analyzing message: {e}")
            analysis_result = {
                "id": str(uuid.uuid4()),
                "text": message,
                "intent": {"intent": "unknown", "confidence": 0.1},
                "sentiment": {"overall": "neutral", "score": 0.0}
            }
        
        # Extract intent and confidence
        intent = analysis_result.get("intent", {}).get("intent", "unknown")
        confidence = analysis_result.get("intent", {}).get("confidence", 0.1)
        
        # Extract sentiment
        sentiment = "neutral"  # Default value
        if analysis_result:
            sentiment = analysis_result.get("sentiment", {}).get("overall", "neutral")
        
        # Update conversation state based on analysis
        self._update_state_from_analysis(intent, confidence, sentiment)
        
        # Save updated state
        self._save_state()
        
        # Return combined results with conversation state
        return {
            "message_id": analysis_result.get("id"),
            "conversation_id": self.conversation_id,
            "intent": intent,
            "confidence": confidence,
            "sentiment": sentiment,
            "requires_human": self.state["flags"]["needs_human_intervention"],
            "current_topic": self.state["current_topic"],
            "message_count": self.state["session"]["message_count"]
        }
    
    def _update_state_from_analysis(self, intent: str, confidence: float, sentiment: str = "neutral") -> None:
        """
        Update conversation state based on message analysis.
        
        Args:
            intent: Detected intent
            confidence: Intent confidence score
            sentiment: Detected sentiment (default: neutral)
        """
        # Update current topic if we have a confident intent
        if confidence >= 0.5 and intent != "unknown":
            self.state["current_topic"] = intent
            # Add to topics discussed if not already there
            if isinstance(self.state["topics_discussed"], list) and intent not in self.state["topics_discussed"]:
                self.state["topics_discussed"].append(intent)
        
        # Update user profile
        if sentiment:
            self.state["user_profile"]["detected_sentiment"] = sentiment
        
        # Check for user frustration based on negative sentiment
        if sentiment == "negative":
            self.state["flags"]["user_frustrated"] = True
        
        # Flag for human intervention if confidence is low or user seems frustrated
        if confidence < 0.3 or self.state["flags"]["user_frustrated"]:
            self.state["flags"]["needs_human_intervention"] = True
        
        # Add to context memory
        self.state["context_memory"].append({
            "time": datetime.now().isoformat(),
            "type": "user_message",
            "intent": intent,
            "sentiment": sentiment
        })
        
        # Limit context memory to 10 items
        if len(self.state["context_memory"]) > 10:
            self.state["context_memory"] = self.state["context_memory"][-10:]
    
    def add_bot_response(self, response: str) -> None:
        """
        Add a bot response to the conversation state.
        
        Args:
            response: Bot response text
        """
        # Update session state
        self.state["session"]["last_bot_message_time"] = datetime.now().isoformat()
        
        # Add to context memory
        self.state["context_memory"].append({
            "time": datetime.now().isoformat(),
            "type": "bot_message",
            "content": response
        })
        
        # Limit context memory to 10 items
        if len(self.state["context_memory"]) > 10:
            self.state["context_memory"] = self.state["context_memory"][-10:]
        
        # Save updated state
        self._save_state()
    
    def get_conversation_context(self) -> List[Dict[str, Any]]:
        """
        Get the current conversation context.
        
        Returns:
            List of context memory items
        """
        return self.state["context_memory"]
    
    def get_full_conversation_analysis(self) -> Dict[str, Any]:
        """
        Get a full analysis of the entire conversation.
        
        Returns:
            Dictionary with conversation analysis
        """
        return nlp_pipeline.get_conversation_analysis(self.conversation_id)
    
    def reset_session(self) -> None:
        """Reset the session state but keep user profile."""
        # Save user profile and topics discussed
        user_profile = self.state["user_profile"]
        topics_discussed = self.state["topics_discussed"]
        
        # Re-initialize state
        self.state = self._initialize_state()
        
        # Restore user profile and topics
        self.state["user_profile"] = user_profile
        self.state["topics_discussed"] = topics_discussed
        
        # Save updated state
        self._save_state()
        logger.info(f"Session reset for conversation: {self.conversation_id}")

    def add_user_message(self, text: str, analysis: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a user message to the conversation.
        
        Args:
            text: Message text
            analysis: Optional pre-computed analysis results
            
        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Update conversation state
        self.state["session"]["message_count"] += 1
        self.state["session"]["last_user_message_time"] = datetime.now().isoformat()
        
        # Analyze text using NLP pipeline
        if analysis is None:
            try:
                from ml.bot_intelligence.nlp_pipeline import default_pipeline as nlp_pipeline
                analysis_result = nlp_pipeline.process_text(text, self.conversation_id)
                
                # Extract intent and confidence
                intent = analysis_result['intent']['intent']
                confidence = analysis_result['intent']['confidence']
            except Exception as e:
                logger.error(f"Error analyzing message: {e}")
                intent = "unknown"
                confidence = 0.1
                analysis_result = None
        else:
            intent = analysis.get('intent', {}).get('intent', 'unknown')
            confidence = analysis.get('intent', {}).get('confidence', 0.1)
            analysis_result = analysis
        
        # Extract sentiment
        sentiment = "neutral"  # Default value
        if analysis_result:
            sentiment = analysis_result.get("sentiment", {}).get("overall", "neutral")
        
        # Update conversation state based on analysis
        self._update_state_from_analysis(intent, confidence, sentiment)
        
        # Create message object
        message = {
            "id": message_id,
            "text": text,
            "sender": "user",
            "timestamp": timestamp,
            "analysis": analysis_result
        }
        
        # Add to state context memory
        if "messages" not in self.state:
            self.state["messages"] = []
        self.state["messages"].append(message)
        
        # Save conversation state
        self._save_state()
        
        # Return message ID for reference
        return message_id

    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a message by ID.
        
        Args:
            message_id: Message ID to find
            
        Returns:
            Message dict or None if not found
        """
        if "messages" not in self.state:
            return None
            
        for message in self.state["messages"]:
            if message.get("id") == message_id:
                return message
                
        return None

    def add_bot_message(self, text: str) -> str:
        """
        Add a bot response to the conversation.
        
        Args:
            text: Bot response text
            
        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Update session state
        self.state["session"]["last_bot_message_time"] = datetime.now().isoformat()
        
        # Create message object
        message = {
            "id": message_id,
            "text": text,
            "sender": "bot",
            "timestamp": timestamp
        }
        
        # Add to state messages
        if "messages" not in self.state:
            self.state["messages"] = []
        self.state["messages"].append(message)
        
        # Add to context memory
        self.state["context_memory"].append({
            "time": datetime.now().isoformat(),
            "type": "bot_message",
            "content": text
        })
        
        # Limit context memory to 10 items
        if len(self.state["context_memory"]) > 10:
            self.state["context_memory"] = self.state["context_memory"][-10:]
        
        # Save updated state
        self._save_state()
        
        return message_id


# For testing
if __name__ == "__main__":
    # Create a new conversation
    manager = ConversationManager()
    
    # Process some test messages
    test_messages = [
        "Hello, I need help with your product",
        "I'm having trouble setting it up",
        "This is very frustrating!",
        "Can I speak to a human please?"
    ]
    
    for message in test_messages:
        print(f"\nProcessing: {message}")
        result = manager.process_message(message)
        print(f"Intent: {result['intent']}")
        print(f"Sentiment: {result['sentiment']}")
        print(f"Requires human: {result['requires_human']}")
        
        # Add a mock bot response
        bot_response = f"I understand you're asking about {result['intent']}. How can I help?"
        manager.add_bot_response(bot_response)
    
    # Get conversation analysis
    analysis = manager.get_full_conversation_analysis()
    print("\nConversation Analysis:")
    print(f"Total messages: {analysis.get('total_messages', 0)}")
    print(f"Intent distribution: {analysis.get('intent_distribution', {})}")
    print(f"Sentiment progression: {analysis.get('sentiment_progression', [])}") 