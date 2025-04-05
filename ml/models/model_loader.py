#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Model Loader Module
Central repository for loading ML models and providing fallback implementations.
"""

import re
import random
import logging
import os
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

from ml.models import load_model, save_model, INTENT_MODEL_PATH, SENTIMENT_MODEL_PATH, EMAIL_CATEGORIZATION_MODEL_PATH
from ml.utils.model_quantization import ModelQuantizer, quantize_model_file

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fallback rules for intent recognition
INTENT_PATTERNS = {
    "greeting": [
        r"^(hello|hi|hey|greetings|good (morning|afternoon|evening))[\s\.,!]*$",
        r"^(what's up|howdy|sup)[\s\.,!]*$"
    ],
    "farewell": [
        r"^(goodbye|bye|see you|talk to you later|farewell)[\s\.,!]*$",
        r"^(have a (good|nice) (day|evening|weekend))[\s\.,!]*$"
    ],
    "help": [
        r"(help|assist|support).*",
        r"(how do I|how can I|how to).*",
        r"^(what|how).*\?$"
    ],
    "problem": [
        r"(issue|problem|error|not working|doesn't work|isn't working|bug|broken).*",
        r"(failed|failing|fails).*",
        r"(can't|cannot|won't|will not).*"
    ]
}

# Compile regex patterns
COMPILED_PATTERNS = {}
for intent, patterns in INTENT_PATTERNS.items():
    COMPILED_PATTERNS[intent] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]

class ModelLoader:
    """Base class for model loaders with fallback mechanisms."""
    
    def __init__(self, model_path: str, model_name: str, use_quantized: bool = False):
        """
        Initialize model loader.
        
        Args:
            model_path: Path to the saved model file
            model_name: Human-readable name for the model
            use_quantized: Whether to prefer quantized models if available
        """
        self.model_path = model_path
        self.model_name = model_name
        self.use_quantized = use_quantized
        self.model = self._load_model()
        self.quantization_info = {}
    
    def _load_model(self) -> Optional[Any]:
        """
        Load the model from disk.
        
        Returns:
            Loaded model or None if not found
        """
        # Check for quantized model if requested
        quantized_path = None
        if self.use_quantized:
            path_obj = Path(self.model_path)
            quantized_path = str(path_obj.parent / f"{path_obj.stem}_quantized{path_obj.suffix}")
            
            if os.path.exists(quantized_path):
                logger.info(f"Loading quantized {self.model_name} from {quantized_path}")
                model = load_model(quantized_path)
                if model is not None:
                    # Store quantization information
                    self.quantization_info = {
                        "using_quantized": True,
                        "path": quantized_path,
                        "original_path": self.model_path
                    }
                    return model
                logger.warning(f"Failed to load quantized {self.model_name}, falling back to original")
        
        # Load the original model
        model = load_model(self.model_path)
        if model is None:
            logger.warning(f"Failed to load {self.model_name} from {self.model_path}, fallback will be used")
        else:
            self.quantization_info = {
                "using_quantized": False,
                "path": self.model_path
            }
        
        return model
    
    def quantize(self, bit_depth: int = 16, weight_threshold: float = 0.001) -> Dict[str, Any]:
        """
        Quantize the loaded model to reduce memory footprint.
        
        Args:
            bit_depth: Target bit depth for quantization (8, 16, or 32)
            weight_threshold: Threshold for pruning small weights
            
        Returns:
            Dictionary with quantization statistics
        """
        if self.model is None:
            logger.error(f"Cannot quantize {self.model_name}: model not loaded")
            return {"error": "Model not loaded"}
        
        # Determine quantized model path
        path_obj = Path(self.model_path)
        quantized_path = str(path_obj.parent / f"{path_obj.stem}_quantized{path_obj.suffix}")
        
        try:
            # Quantize the model
            logger.info(f"Quantizing {self.model_name} to {bit_depth}-bit precision")
            
            # Create quantizer and apply to model in memory
            quantizer = ModelQuantizer(bit_depth=bit_depth, weight_threshold=weight_threshold)
            quantized_model, stats = quantizer.quantize_model(self.model, model_format="sklearn")
            
            # Save the quantized model
            logger.info(f"Saving quantized model to {quantized_path}")
            os.makedirs(os.path.dirname(quantized_path), exist_ok=True)
            save_model(quantized_model, quantized_path)
            
            # Update quantization info
            original_size = os.path.getsize(self.model_path) if os.path.exists(self.model_path) else 0
            quantized_size = os.path.getsize(quantized_path) if os.path.exists(quantized_path) else 0
            
            self.quantization_info = {
                "using_quantized": False,  # Still using original until reloaded
                "original_path": self.model_path,
                "quantized_path": quantized_path,
                "original_size_bytes": original_size,
                "quantized_size_bytes": quantized_size,
                "size_reduction_percent": (1 - (quantized_size / original_size)) * 100 if original_size > 0 else 0,
                "bit_depth": bit_depth,
                "weight_threshold": weight_threshold
            }
            
            return self.quantization_info
            
        except Exception as e:
            logger.error(f"Error quantizing {self.model_name}: {e}")
            return {"error": str(e)}
    
    def use_quantized_model(self, quantized: bool = True) -> bool:
        """
        Switch to using the quantized model (or back to the original).
        
        Args:
            quantized: Whether to use the quantized model
            
        Returns:
            True if successful, False otherwise
        """
        # Save current setting
        current_setting = self.use_quantized
        
        # Set new preference
        self.use_quantized = quantized
        
        # Reload the model
        self.model = self._load_model()
        
        # Check if reload was successful
        if self.model is None:
            # Revert to previous setting if loading failed
            self.use_quantized = current_setting
            self.model = self._load_model()
            logger.error(f"Failed to load {'quantized' if quantized else 'original'} model, reverting to previous")
            return False
        
        logger.info(f"Switched to {'quantized' if self.use_quantized else 'original'} model")
        return True
    
    def get_model_size_info(self) -> Dict[str, Any]:
        """
        Get information about model size and quantization status.
        
        Returns:
            Dictionary with model size information
        """
        original_path = self.model_path
        quantized_path = None
        
        # Check for quantized model
        path_obj = Path(self.model_path)
        quantized_path = str(path_obj.parent / f"{path_obj.stem}_quantized{path_obj.suffix}")
        
        original_exists = os.path.exists(original_path)
        quantized_exists = os.path.exists(quantized_path)
        
        info = {
            "model_name": self.model_name,
            "using_quantized": self.use_quantized,
            "original_model": {
                "exists": original_exists,
                "path": original_path,
                "size_bytes": os.path.getsize(original_path) if original_exists else 0
            },
            "quantized_model": {
                "exists": quantized_exists,
                "path": quantized_path,
                "size_bytes": os.path.getsize(quantized_path) if quantized_exists else 0
            }
        }
        
        # Calculate size reduction if both models exist
        if original_exists and quantized_exists:
            original_size = info["original_model"]["size_bytes"]
            quantized_size = info["quantized_model"]["size_bytes"]
            
            if original_size > 0:
                info["size_reduction_percent"] = (1 - (quantized_size / original_size)) * 100
        
        return info


class IntentModelLoader(ModelLoader):
    """Loader for intent recognition model with rule-based fallback."""
    
    def __init__(self, use_quantized: bool = False):
        """
        Initialize intent model loader.
        
        Args:
            use_quantized: Whether to prefer quantized models if available
        """
        super().__init__(INTENT_MODEL_PATH, "intent model", use_quantized)
    
    def predict_intent(self, text: str) -> Dict[str, Any]:
        """
        Predict intent from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with intent prediction results
        """
        if self.model is not None:
            try:
                # Use ML model for prediction
                probas = self.model.predict_proba([text])[0]
                indices = probas.argsort()[::-1]
                classes = self.model.classes_
                
                intent = classes[indices[0]]
                confidence = float(probas[indices[0]])
                
                return {
                    "intent": intent,
                    "confidence": confidence,
                    "method": "ml"
                }
            except Exception as e:
                logger.error(f"Error using ML intent model: {e}")
                # Fall back to rule-based
        
        # Rule-based fallback
        return self._rule_based_intent(text)
    
    def _rule_based_intent(self, text: str) -> Dict[str, Any]:
        """
        Rule-based intent recognition using regex patterns.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with intent prediction
        """
        text = text.strip().lower()
        
        # Check against patterns
        for intent, patterns in COMPILED_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(text):
                    logger.info(f"Rule-based method found intent: {intent}")
                    return {
                        "intent": intent,
                        "confidence": 0.7,  # Fixed confidence for rule-based
                        "method": "rule-based"
                    }
        
        # No match found
        logger.info("No intent patterns matched, returning 'unknown'")
        return {
            "intent": "unknown",
            "confidence": 0.1,
            "method": "rule-based"
        }


class SentimentModelLoader(ModelLoader):
    """Loader for enhanced sentiment analysis model with rule-based fallback."""
    
    def __init__(self, use_quantized: bool = False):
        """
        Initialize sentiment model loader.
        
        Args:
            use_quantized: Whether to prefer quantized models if available
        """
        super().__init__(SENTIMENT_MODEL_PATH, "sentiment model", use_quantized)
        
        # Import here to avoid circular imports
        try:
            from ml.models.sentiment_analysis import SentimentAnalysisModel, SentimentResult
            self.sentiment_model = SentimentAnalysisModel()
            self.enhanced_model_available = True
            logger.info("Using enhanced sentiment analysis model")
        except ImportError:
            self.enhanced_model_available = False
            logger.warning("Enhanced sentiment model not available, using basic fallback")
            
            # Keywords for rule-based sentiment (fallback if enhanced model is not available)
            self.positive_words = {"good", "great", "excellent", "awesome", "fantastic", 
                                "wonderful", "happy", "glad", "thank", "thanks", "please", 
                                "love", "perfect", "nice", "appreciate"}
            
            self.negative_words = {"bad", "terrible", "awful", "horrible", "issue", "problem", 
                                "error", "bug", "broken", "not working", "angry", "upset", 
                                "disappointed", "slow", "difficult", "hate", "dislike", "wrong"}
    
    def analyze_sentiment(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            context: Optional context information
            
        Returns:
            Dictionary with sentiment analysis results
        """
        # Use enhanced model if available
        if self.enhanced_model_available:
            try:
                result = self.sentiment_model.analyze_sentiment(text, context)
                return result.to_dict()
            except Exception as e:
                logger.error(f"Error using enhanced sentiment model: {e}")
                # Fall back to basic approach
        
        # If ML model is available, try that next
        if self.model is not None:
            try:
                # Use ML model for prediction
                sentiment = self.model.predict([text])[0]
                confidence = max(self.model.predict_proba([text])[0])
                
                return {
                    "overall": sentiment,
                    "confidence": float(confidence),
                    "method": "ml"
                }
            except Exception as e:
                logger.error(f"Error using ML sentiment model: {e}")
                # Fall back to rule-based
        
        # Rule-based fallback
        return self._rule_based_sentiment(text)
    
    def _rule_based_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Rule-based sentiment analysis using keyword matching.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        text = text.lower()
        
        # Count sentiment words
        positive_count = sum(1 for word in self.positive_words if word in text)
        negative_count = sum(1 for word in self.negative_words if word in text)
        
        # Determine sentiment
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        logger.info(f"Rule-based method found sentiment: {sentiment}")
        
        return {
            "overall": sentiment,
            "confidence": 0.6,  # Fixed confidence for rule-based
            "method": "rule-based"
        }


class EmailCategorizationModelLoader(ModelLoader):
    """Loader for email categorization model with rule-based fallback."""
    
    def __init__(self, use_quantized: bool = False):
        """
        Initialize email categorization model loader.
        
        Args:
            use_quantized: Whether to prefer quantized models if available
        """
        super().__init__(EMAIL_CATEGORIZATION_MODEL_PATH, "email categorization model", use_quantized)
        
        # Keywords for rule-based categorization
        self.category_keywords = {
            "inquiry": ["question", "inquire", "information", "details", "learn more", "interested", "looking for"],
            "support": ["help", "issue", "problem", "not working", "error", "bug", "fix", "support", "assistance"],
            "feedback": ["feedback", "suggest", "suggestion", "improve", "review", "opinion"],
            "complaint": ["complaint", "disappointed", "unhappy", "frustrated", "refund", "cancel"],
            "sales": ["purchase", "buy", "price", "cost", "discount", "deal", "order", "quote"],
            "partnership": ["partner", "collaboration", "affiliate", "work together", "joint", "opportunity"]
        }
    
    def categorize_email(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Categorize email based on subject and body.
        
        Args:
            subject: Email subject
            body: Email body text
            
        Returns:
            Dictionary with categorization results
        """
        if self.model is not None:
            try:
                # Combine subject and body for analysis
                text = f"{subject} {body}"
                
                # Use ML model for prediction
                category = self.model.predict([text])[0]
                probas = self.model.predict_proba([text])[0]
                confidence = max(probas)
                
                # Get top 3 categories
                indices = probas.argsort()[::-1][:3]
                categories = [
                    {"category": self.model.classes_[i], "confidence": float(probas[i])}
                    for i in indices
                ]
                
                return {
                    "enabled": True,
                    "primary_category": category,
                    "confidence": float(confidence),
                    "categories": categories,
                    "method": "ml"
                }
            except Exception as e:
                logger.error(f"Error using ML categorization model: {e}")
                # Fall back to rule-based
        
        # Rule-based fallback
        return self._rule_based_categorization(subject, body)
    
    def _rule_based_categorization(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Rule-based email categorization using keyword matching.
        
        Args:
            subject: Email subject
            body: Email body text
            
        Returns:
            Dictionary with categorization results
        """
        # Combine and lowercase text
        text = (subject + " " + body).lower()
        
        # Count category keywords
        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text)
            category_scores[category] = score
        
        # Sort categories by score
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        
        # If no matches, default to inquiry
        if sorted_categories[0][1] == 0:
            primary_category = "inquiry"
            logger.info(f"Rule-based method categorized email as: {primary_category}")
            categories = [{"category": "inquiry", "confidence": 0.5}]
        else:
            primary_category = sorted_categories[0][0]
            logger.info(f"Rule-based method categorized email as: {primary_category}")
            
            # Calculate relative confidence
            total_score = sum(score for _, score in sorted_categories if score > 0)
            categories = []
            
            if total_score > 0:
                for category, score in sorted_categories[:3]:
                    if score > 0:
                        confidence = score / total_score
                        categories.append({"category": category, "confidence": confidence})
        
        return {
            "enabled": True,
            "primary_category": primary_category,
            "confidence": categories[0]["confidence"] if categories else 0.5,
            "categories": categories,
            "method": "rule-based"
        }


# Create singleton instances
intent_model = IntentModelLoader()
sentiment_model = SentimentModelLoader()
email_categorization_model = EmailCategorizationModelLoader() 