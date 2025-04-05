#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enhanced Sentiment Analysis Model

Provides advanced sentiment analysis with fine-grained emotion detection,
contextual awareness, and domain-specific customization.
"""

import os
import re
import json
import logging
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV

from ml.config import get_nlp_config
from ml.models import load_model, save_model, SENTIMENT_MODEL_PATH

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SentimentExample:
    """Example for sentiment analysis training."""
    text: str
    sentiment: str  # "positive", "negative", "neutral"
    emotion: Optional[str] = None  # Optional fine-grained emotion
    intensity: float = 0.0  # Intensity of sentiment (0.0-1.0)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SentimentExample':
        """Create a SentimentExample from a dictionary."""
        return cls(
            text=data['text'],
            sentiment=data['sentiment'],
            emotion=data.get('emotion'),
            intensity=data.get('intensity', 0.0),
            metadata=data.get('metadata', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'text': self.text,
            'sentiment': self.sentiment,
            'emotion': self.emotion,
            'intensity': self.intensity,
            'metadata': self.metadata
        }

@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    overall: str  # "positive", "negative", "neutral"
    confidence: float
    method: str  # "ml", "rule-based", etc.
    emotion: Optional[str] = None
    emotion_confidence: Optional[float] = None
    intensity: float = 0.0  # Intensity score (0.0-1.0)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'overall': self.overall,
            'confidence': self.confidence,
            'method': self.method,
            'emotion': self.emotion,
            'emotion_confidence': self.emotion_confidence,
            'intensity': self.intensity,
            'details': self.details
        }

class TextNormalizer:
    """Normalize text for sentiment analysis."""
    
    def __init__(self):
        """Initialize text normalizer."""
        # Common contractions
        self.contractions = {
            "can't": "cannot",
            "won't": "will not",
            "don't": "do not",
            "doesn't": "does not",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "haven't": "have not",
            "hasn't": "has not",
            "hadn't": "had not",
            "couldn't": "could not",
            "shouldn't": "should not",
            "wouldn't": "would not",
        }
        
        # Sentiment modifiers
        self.intensifiers = {
            "very", "really", "extremely", "absolutely", "completely",
            "totally", "utterly", "highly", "especially", "particularly",
            "incredibly", "exceedingly", "vastly", "hugely", "immensely"
        }
        
        self.diminishers = {
            "somewhat", "slightly", "a bit", "a little", "fairly",
            "kind of", "kinda", "sort of", "moderately", "barely",
            "hardly", "scarcely", "marginally", "relatively"
        }
        
        self.negations = {
            "not", "no", "never", "none", "nothing", "nowhere", "neither",
            "nor", "barely", "hardly", "scarcely", "without"
        }
    
    def normalize(self, text: str) -> str:
        """
        Normalize text for sentiment analysis.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Expand contractions
        for contraction, expansion in self.contractions.items():
            text = text.replace(contraction, expansion)
        
        # Handle special characters
        text = re.sub(r'[^\w\s.,?!]', ' ', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Trim spaces
        text = text.strip()
        
        return text
    
    def detect_modifiers(self, text: str) -> Dict[str, Any]:
        """
        Detect sentiment modifiers in text.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary of modifier information
        """
        words = text.lower().split()
        
        # Check for modifiers
        modifiers = {
            "has_intensifier": any(word in self.intensifiers for word in words),
            "has_diminisher": any(word in self.diminishers for word in words),
            "has_negation": any(word in self.negations for word in words),
            "exclamation_count": text.count('!'),
            "question_count": text.count('?')
        }
        
        return modifiers

class SentimentAnalysisModel:
    """
    Enhanced sentiment analysis model with fine-grained emotion detection
    and contextual awareness.
    """
    
    def __init__(self):
        """Initialize the sentiment analysis model."""
        self.config = get_nlp_config()
        self.sentiment_model = self._load_sentiment_model()
        self.emotion_model = self._load_emotion_model()
        self.text_normalizer = TextNormalizer()
        
        # Load sentiment lexicons for rule-based analysis
        self.sentiment_lexicon = self._load_sentiment_lexicon()
        self.domain_specific_lexicon = self._load_domain_lexicon()
        
        logger.info("Enhanced sentiment analysis model initialized")
    
    def _load_sentiment_model(self) -> Optional[Any]:
        """
        Load the sentiment analysis ML model.
        
        Returns:
            Loaded model or None if not found
        """
        model = load_model(SENTIMENT_MODEL_PATH)
        if model is None:
            logger.warning(f"No sentiment model found at {SENTIMENT_MODEL_PATH}, using rule-based fallback")
        return model
    
    def _load_emotion_model(self) -> Optional[Any]:
        """
        Load the emotion detection ML model.
        
        Returns:
            Loaded model or None if not found
        """
        # Emotion model would typically be a separate model
        # For now, we'll use a rule-based approach
        return None
    
    def _load_sentiment_lexicon(self) -> Dict[str, float]:
        """
        Load sentiment lexicon for rule-based analysis.
        
        Returns:
            Dictionary mapping words to sentiment scores
        """
        # In a real implementation, this would load from a file
        # For now, using a minimal built-in lexicon
        lexicon = {
            # Positive words
            "good": 0.7,
            "great": 0.8,
            "excellent": 0.9,
            "amazing": 0.9,
            "wonderful": 0.8,
            "fantastic": 0.9,
            "helpful": 0.7,
            "useful": 0.6,
            "awesome": 0.9,
            "perfect": 1.0,
            "love": 0.9,
            "like": 0.6,
            "happy": 0.8,
            "pleased": 0.7,
            "satisfied": 0.7,
            "thank": 0.7,
            "thanks": 0.7,
            
            # Negative words
            "bad": -0.7,
            "terrible": -0.9,
            "awful": -0.8,
            "horrible": -0.9,
            "poor": -0.6,
            "disappointing": -0.7,
            "useless": -0.7,
            "hate": -0.9,
            "dislike": -0.6,
            "angry": -0.8,
            "upset": -0.7,
            "frustrated": -0.7,
            "annoying": -0.6,
            "difficult": -0.5,
            "problem": -0.5,
            "issue": -0.4,
            "error": -0.5,
            "bug": -0.5,
            "broken": -0.7,
            "crash": -0.8,
            "fail": -0.7,
            "failure": -0.7
        }
        return lexicon
    
    def _load_domain_lexicon(self) -> Dict[str, float]:
        """
        Load domain-specific sentiment lexicon.
        
        Returns:
            Dictionary mapping domain-specific terms to sentiment scores
        """
        # In a real implementation, this would load from a file
        # For now, using cybersecurity domain terms
        lexicon = {
            # Security-related terms (generally neutral in this domain)
            "breach": -0.7,
            "attack": -0.6,
            "vulnerability": -0.5,
            "threat": -0.6,
            "secure": 0.6,
            "protected": 0.7,
            "encrypted": 0.5,
            "detected": 0.4,
            "monitoring": 0.3,
            "alert": 0.0,  # Neutral in security domain
            "notification": 0.0,  # Neutral in security domain
            "unauthorized": -0.6,
            "suspicious": -0.5,
            "malware": -0.7,
            "virus": -0.7,
            "ransomware": -0.8,
            "phishing": -0.7,
            "firewall": 0.5,
            "patch": 0.6,
            "update": 0.4,
            "backup": 0.6,
            "recovery": 0.7
        }
        return lexicon
    
    def analyze_sentiment(self, text: str, context: Dict[str, Any] = None) -> SentimentResult:
        """
        Analyze sentiment of text with enhanced capabilities.
        
        Args:
            text: Text to analyze
            context: Optional context information for improved analysis
            
        Returns:
            SentimentResult with detailed sentiment information
        """
        # Normalize text
        normalized_text = self.text_normalizer.normalize(text)
        
        # Try ML model first
        ml_result = None
        if self.sentiment_model is not None:
            ml_result = self._ml_sentiment_analysis(normalized_text)
        
        # Use rule-based analysis
        rule_result = self._rule_based_sentiment(normalized_text)
        
        # Choose best result or combine them
        if ml_result and ml_result.confidence > rule_result.confidence:
            result = ml_result
        else:
            result = rule_result
        
        # Add emotion detection
        self._detect_emotion(normalized_text, result)
        
        # Apply context-aware adjustments if context is provided
        if context:
            self._apply_context_adjustments(result, context)
        
        return result
    
    def _ml_sentiment_analysis(self, text: str) -> SentimentResult:
        """
        Perform machine learning-based sentiment analysis.
        
        Args:
            text: Text to analyze
            
        Returns:
            SentimentResult with ML-based sentiment
        """
        try:
            # Predict sentiment
            sentiment = self.sentiment_model.predict([text])[0]
            probas = self.sentiment_model.predict_proba([text])[0]
            confidence = float(max(probas))
            
            # Calculate intensity based on confidence
            intensity = (confidence - 0.5) * 2 if confidence > 0.5 else 0.0
            
            return SentimentResult(
                overall=sentiment,
                confidence=confidence,
                method="ml",
                intensity=intensity
            )
        except Exception as e:
            logger.error(f"Error in ML sentiment analysis: {e}")
            return SentimentResult(
                overall="neutral",
                confidence=0.1,
                method="ml-fallback",
                intensity=0.0
            )
    
    def _rule_based_sentiment(self, text: str) -> SentimentResult:
        """
        Perform rule-based sentiment analysis using lexicons.
        
        Args:
            text: Text to analyze
            
        Returns:
            SentimentResult with rule-based sentiment
        """
        words = text.lower().split()
        
        # Get sentiment modifiers
        modifiers = self.text_normalizer.detect_modifiers(text)
        
        # Calculate sentiment score
        sentiment_scores = []
        for word in words:
            # Check general lexicon
            if word in self.sentiment_lexicon:
                sentiment_scores.append(self.sentiment_lexicon[word])
            
            # Check domain-specific lexicon
            if word in self.domain_specific_lexicon:
                sentiment_scores.append(self.domain_specific_lexicon[word] * 1.5)  # Give higher weight to domain terms
        
        # Calculate overall sentiment score
        if sentiment_scores:
            # Apply negation if needed
            if modifiers["has_negation"]:
                sentiment_scores = [-score for score in sentiment_scores]
            
            # Apply intensifiers
            modifier_factor = 1.0
            if modifiers["has_intensifier"]:
                modifier_factor *= 1.5
            if modifiers["has_diminisher"]:
                modifier_factor *= 0.7
            
            # Calculate weighted average score
            overall_score = sum(sentiment_scores) * modifier_factor / len(sentiment_scores)
            
            # Add impact of exclamations
            exclamation_impact = min(0.2, modifiers["exclamation_count"] * 0.1)
            if overall_score > 0:
                overall_score += exclamation_impact
            elif overall_score < 0:
                overall_score -= exclamation_impact
            
            # Determine sentiment category and confidence
            if overall_score > 0.1:
                sentiment = "positive"
                confidence = min(0.9, 0.5 + (overall_score / 2))
                intensity = min(1.0, abs(overall_score))
            elif overall_score < -0.1:
                sentiment = "negative"
                confidence = min(0.9, 0.5 + (abs(overall_score) / 2))
                intensity = min(1.0, abs(overall_score))
            else:
                sentiment = "neutral"
                confidence = 0.7 if -0.05 <= overall_score <= 0.05 else 0.5
                intensity = 0.0
        else:
            # No sentiment words found
            sentiment = "neutral"
            confidence = 0.6
            intensity = 0.0
        
        # Create result
        result = SentimentResult(
            overall=sentiment,
            confidence=confidence,
            method="rule-based",
            intensity=intensity,
            details={
                "score": overall_score if sentiment_scores else 0.0,
                "word_count": len(words),
                "sentiment_words": len(sentiment_scores),
                "modifiers": modifiers
            }
        )
        
        return result
    
    def _detect_emotion(self, text: str, result: SentimentResult) -> None:
        """
        Detect emotion in text and update result.
        
        Args:
            text: Text to analyze
            result: SentimentResult to update
        """
        # Define emotion mapping
        emotion_keywords = {
            "happy": ["happy", "joy", "delighted", "pleased", "glad", "thrilled", "excited"],
            "angry": ["angry", "mad", "furious", "outraged", "annoyed", "frustrated", "irritated"],
            "sad": ["sad", "unhappy", "disappointed", "depressed", "upset", "down", "heartbroken"],
            "surprised": ["surprised", "shocked", "amazed", "astonished", "stunned"],
            "fearful": ["afraid", "scared", "fearful", "anxious", "nervous", "worried", "terrified"],
            "disgusted": ["disgusted", "revolted", "repulsed", "sickened"]
        }
        
        # Count emotion words
        emotion_counts = {}
        words = text.lower().split()
        for emotion, keywords in emotion_keywords.items():
            count = sum(1 for word in words if word in keywords)
            if count > 0:
                emotion_counts[emotion] = count
        
        # Determine dominant emotion
        if emotion_counts:
            sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
            dominant_emotion, count = sorted_emotions[0]
            total_count = sum(emotion_counts.values())
            confidence = count / total_count
            
            # Update result with emotion
            result.emotion = dominant_emotion
            result.emotion_confidence = confidence
            result.details["emotions"] = emotion_counts
    
    def _apply_context_adjustments(self, result: SentimentResult, context: Dict[str, Any]) -> None:
        """
        Apply context-aware adjustments to sentiment analysis.
        
        Args:
            result: SentimentResult to adjust
            context: Context information
        """
        # Previous sentiment (if available)
        if "previous_sentiment" in context:
            prev_sentiment = context["previous_sentiment"]
            
            # If neutral with low confidence, lean towards previous sentiment
            if result.overall == "neutral" and result.confidence < 0.6 and prev_sentiment != "neutral":
                result.overall = prev_sentiment
                result.confidence *= 0.8  # Reduce confidence for this adjustment
                result.method += "+context"
                result.details["context_adjustment"] = f"Used previous sentiment: {prev_sentiment}"
        
        # Product context
        if "product" in context:
            product = context["product"]
            product_keywords = {
                "ARP Guard": ["arp", "guard", "network", "protection", "scan"],
                "Network Shield": ["shield", "network", "firewall", "protect", "defend"],
                "Perimeter Defender": ["perimeter", "defender", "defense", "boundary", "protect"]
            }
            
            # Check if text contains product-specific keywords
            if product in product_keywords:
                words = result.details.get("words", [])
                product_relevant_words = [word for word in words if word in product_keywords[product]]
                if product_relevant_words:
                    # Increase confidence slightly for product-relevant sentiment
                    result.confidence = min(0.95, result.confidence * 1.1)
                    result.details["product_relevance"] = len(product_relevant_words) / len(words) if words else 0
        
        # Message type context
        if "message_type" in context:
            msg_type = context["message_type"]
            
            # Different adjustments based on message type
            if msg_type == "complaint" and result.overall == "positive":
                # Reduce confidence in positive sentiment for complaints
                result.confidence *= 0.8
                result.details["context_note"] = "Reduced confidence for positive sentiment in complaint"
            elif msg_type == "feedback" and result.overall == "neutral" and result.confidence < 0.7:
                # For feedback, neutral with low confidence might lean negative
                result.overall = "slightly_negative"
                result.details["context_note"] = "Adjusted neutral to slightly negative for feedback"

# Create default model instance
default_model = SentimentAnalysisModel() 