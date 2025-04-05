"""
Bot Intelligence Module
Provides NLP processing and conversation state management for bots.
"""

# Export main components
from ml.bot_intelligence.nlp_pipeline import NLPPipeline, default_pipeline
from ml.bot_intelligence.conversation_state import ConversationManager, Conversation, ConversationState, Message, ClientProfile 