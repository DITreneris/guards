"""
Guards & Robbers ML Framework
Machine learning capabilities for Guards & Robbers products.
"""

__version__ = "0.1.0"
__author__ = "Guards & Robbers Team"
__email__ = "info@guardsrobbers.com"

# Import main components for easier access
from ml.bot_intelligence.nlp_pipeline import NLPPipeline
from ml.bot_intelligence.conversation_state import ConversationManager, Conversation, ConversationState
from ml.email_intelligence.email_processor import EmailProcessor, ProcessedEmail
from ml.data_collection.data_extractor import DataExtractor 