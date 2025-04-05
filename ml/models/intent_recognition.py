#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Intent Recognition Model for Bot Intelligence
Provides both rule-based and machine learning-based intent recognition capabilities.
"""

import os
import re
import json
import uuid
import logging
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler

from ml.config import get_nlp_config
from ml.models import load_model, save_model, INTENT_MODEL_PATH

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class IntentExample:
    """Training example for intent recognition."""
    text: str
    intent: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntentExample':
        """Create an IntentExample from a dictionary."""
        return cls(
            text=data['text'],
            intent=data['intent'],
            metadata=data.get('metadata', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'text': self.text,
            'intent': self.intent,
            'metadata': self.metadata
        }

@dataclass
class IntentRecognitionResult:
    """Result of intent recognition."""
    intent: str
    confidence: float
    method: str  # 'rule-based' or 'ml'
    alternatives: List[Tuple[str, float]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'intent': self.intent,
            'confidence': self.confidence,
            'method': self.method,
            'alternatives': [(intent, float(conf)) for intent, conf in self.alternatives],
            'context': self.context
        }

class ContextManager:
    """Manages context information for enhanced intent recognition."""
    
    def __init__(self):
        """Initialize the context manager."""
        self.current_context = {}
        self.intent_history = []
    
    def update_context(self, text: str, intent_result: IntentRecognitionResult) -> Dict[str, Any]:
        """
        Update context based on current text and intent.
        
        Args:
            text: Current user text
            intent_result: Recognized intent
            
        Returns:
            Updated context dictionary
        """
        # Store intent history (last 5 intents)
        self.intent_history.append(intent_result.intent)
        self.intent_history = self.intent_history[-5:]
        
        # Extract potential context clues
        # (Simple regex-based for the demo - in production would use proper NLP)
        context_clues = {
            'product_mentioned': self._extract_product_mention(text),
            'has_question': '?' in text,
            'intent_history': self.intent_history,
            'previous_intent': self.intent_history[-2] if len(self.intent_history) > 1 else None,
            'repeated_intent': self._check_repeated_intent()
        }
        
        # Update the current context
        self.current_context.update(context_clues)
        
        # Add to result context
        intent_result.context = self.current_context.copy()
        
        return self.current_context
    
    def _extract_product_mention(self, text: str) -> Optional[str]:
        """Extract product mentions from text."""
        products = ['ARP Guard', 'Network Shield', 'Perimeter Defender', 'Access Manager']
        for product in products:
            if product.lower() in text.lower():
                return product
        return None
    
    def _check_repeated_intent(self) -> bool:
        """Check if the same intent has been repeated."""
        if len(self.intent_history) < 2:
            return False
        return self.intent_history[-1] == self.intent_history[-2]
    
    def reset(self):
        """Reset context for a new conversation."""
        self.current_context = {}
        self.intent_history = []

class TextPreprocessor:
    """Preprocesses text for intent recognition."""
    
    def __init__(self):
        """Initialize the text preprocessor."""
        # Common contractions and their expansions
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
            "i'm": "i am",
            "you're": "you are",
            "he's": "he is",
            "she's": "she is",
            "it's": "it is",
            "we're": "we are",
            "they're": "they are",
            "i'll": "i will",
            "you'll": "you will",
            "he'll": "he will",
            "she'll": "she will",
            "it'll": "it will",
            "we'll": "we will",
            "they'll": "they will",
            "i'd": "i would",
            "you'd": "you would",
            "he'd": "he would",
            "she'd": "she would",
            "it'd": "it would",
            "we'd": "we would",
            "they'd": "they would",
            "i've": "i have",
            "you've": "you have",
            "we've": "we have",
            "they've": "they have"
        }
        
        # Common stopwords to remove
        self.stopwords = ["a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by"]
    
    def preprocess(self, text: str) -> str:
        """
        Preprocess text for intent recognition.
        
        Args:
            text: Input text
            
        Returns:
            Preprocessed text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Expand contractions
        for contraction, expansion in self.contractions.items():
            text = text.replace(contraction, expansion)
        
        # Replace special characters with space
        text = re.sub(r'[^\w\s\?\!\.]', ' ', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Trim spaces
        text = text.strip()
        
        return text

class IntentRecognitionModel:
    """
    Model for recognizing user intents from text.
    Supports both rule-based and ML-based approaches.
    """
    
    def __init__(self):
        """Initialize the intent recognition model."""
        self.config = get_nlp_config()
        self.intent_patterns = self._load_intent_patterns()
        self.ml_model = self._load_ml_model()
        self.fallback_intent = "unknown"
        self.min_confidence = self.config.get("intent_recognition", {}).get("confidence_threshold", 0.5)
        
        # Initialize supporting components
        self.context_manager = ContextManager()
        self.text_preprocessor = TextPreprocessor()
        
        # Intent transition logic
        self.intent_transitions = {
            "greeting": ["help", "problem", "pricing", "feature_request"],
            "help": ["problem", "feature_request", "greeting", "farewell"],
            "problem": ["help", "feature_request", "farewell"],
            "pricing": ["feature_request", "help", "farewell"],
            "feature_request": ["pricing", "help", "farewell"],
            "farewell": ["greeting", "help", "problem"]
        }
        
        logger.info("Enhanced intent recognition model initialized")
    
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """
        Load regex patterns for rule-based intent recognition.
        
        Returns:
            Dictionary mapping intent names to lists of regex patterns
        """
        patterns = {}
        
        # Load from config
        intent_config = self.config.get("intent_recognition", {})
        if "regex_patterns" in intent_config:
            patterns = intent_config.get("regex_patterns", {})
        
        # If no patterns in config, use defaults
        if not patterns:
            patterns = {
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
                    r"^(what|how).*\?$",
                    r"(guide|documentation|explain|instructions).*"
                ],
                "problem": [
                    r"(issue|problem|error|not working|doesn't work|isn't working|bug|broken).*",
                    r"(failed|failing|fails).*",
                    r"(can't|cannot|won't|will not).*",
                    r"(trouble|difficulty|confused|stuck).*"
                ],
                "feature_request": [
                    r"(feature|add|new|improvement|enhance|upgrade).*",
                    r"(would like to have|would like to see|wish you had).*",
                    r"(missing|lacking).*",
                    r"(suggest|suggestion|recommendation).*"
                ],
                "pricing": [
                    r"(cost|price|pricing|subscription|payment|pay|buy|purchase).*",
                    r"(how much|what is the cost of).*",
                    r"(discount|offer|deal|trial).*",
                    r"(plan|package|tier|license).*"
                ]
            }
        
        # Compile regex patterns for performance
        compiled_patterns = {}
        for intent, pattern_list in patterns.items():
            compiled_patterns[intent] = [re.compile(pattern, re.IGNORECASE) for pattern in pattern_list]
        
        return compiled_patterns
    
    def _load_ml_model(self) -> Optional[Any]:
        """
        Load the machine learning model for intent recognition.
        
        Returns:
            Trained model if available, None otherwise
        """
        model = load_model(INTENT_MODEL_PATH)
        if model is None:
            logger.warning(f"No ML model found at {INTENT_MODEL_PATH}, using rule-based fallback")
        return model
    
    def train(self, examples: List[IntentExample], test_size: float = 0.2, grid_search: bool = True) -> Dict[str, Any]:
        """
        Train the ML model for intent recognition.
        
        Args:
            examples: List of training examples
            test_size: Proportion of data to use for testing
            grid_search: Whether to perform hyperparameter tuning
            
        Returns:
            Dictionary with training results and metrics
        """
        if len(examples) < 10:
            logger.warning("Not enough training examples (need at least 10)")
            return {"status": "error", "message": "Not enough training examples"}
        
        # Extract texts and intents
        texts = [self.text_preprocessor.preprocess(ex.text) for ex in examples]
        intents = [ex.intent for ex in examples]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            texts, intents, test_size=test_size, random_state=42, stratify=intents
        )
        
        # Create default pipeline
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),  # Use 1-3 word ngrams
            max_features=15000,
            min_df=2,
            sublinear_tf=True  # Apply sublinear tf scaling
        )
        
        # Choose classifier based on dataset size
        if len(examples) > 100:
            classifier = SVC(probability=True, kernel='rbf', C=1.0, gamma='scale')
            logger.info("Using SVM classifier for larger dataset")
        else:
            classifier = RandomForestClassifier(
                n_estimators=200,
                max_depth=None,
                min_samples_split=2,
                random_state=42,
                class_weight='balanced'
            )
            logger.info("Using RandomForest classifier for smaller dataset")
        
        # Set up pipeline
        pipeline = Pipeline([
            ('vectorizer', vectorizer),
            ('classifier', classifier)
        ])
        
        # Perform grid search for hyperparameter tuning if requested
        if grid_search and len(examples) > 50:
            logger.info("Performing grid search for hyperparameter tuning")
            
            param_grid = {}
            
            # Vectorizer parameters
            param_grid['vectorizer__max_features'] = [10000, 15000, 20000]
            param_grid['vectorizer__ngram_range'] = [(1, 2), (1, 3)]
            
            # Classifier parameters
            if isinstance(classifier, RandomForestClassifier):
                param_grid['classifier__n_estimators'] = [100, 200, 300]
                param_grid['classifier__max_depth'] = [None, 10, 20]
            elif isinstance(classifier, SVC):
                param_grid['classifier__C'] = [0.1, 1.0, 10.0]
                param_grid['classifier__gamma'] = ['scale', 'auto', 0.01, 0.1]
            
            # Set up grid search with cross-validation
            search = GridSearchCV(pipeline, param_grid, cv=3, scoring='accuracy', verbose=1, n_jobs=-1)
            search.fit(X_train, y_train)
            
            # Get best pipeline
            pipeline = search.best_estimator_
            logger.info(f"Best parameters: {search.best_params_}")
        else:
            # Train with default parameters
            pipeline.fit(X_train, y_train)
        
        # Evaluate
        y_pred = pipeline.predict(X_test)
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # Save model
        self.ml_model = pipeline
        save_model(pipeline, INTENT_MODEL_PATH)
        
        # Get sample predictions for analysis
        sample_indices = np.random.choice(len(X_test), min(5, len(X_test)), replace=False)
        sample_predictions = []
        for idx in sample_indices:
            sample_text = X_test[idx]
            true_intent = y_test[idx]
            pred_intent = y_pred[idx]
            sample_predictions.append({
                "text": sample_text,
                "true": true_intent,
                "predicted": pred_intent
            })
        
        logger.info(f"Trained enhanced intent recognition model with {len(examples)} examples")
        
        return {
            "status": "success",
            "metrics": report,
            "examples_count": len(examples),
            "train_size": len(X_train),
            "test_size": len(X_test),
            "intents": list(set(intents)),
            "sample_predictions": sample_predictions,
            "best_params": getattr(pipeline, 'best_params_', None)
        }
    
    def recognize_intent(self, text: str, context: Dict[str, Any] = None) -> IntentRecognitionResult:
        """
        Recognize intent from text using rule-based and ML approaches.
        
        Args:
            text: Text to analyze
            context: Optional context information to enhance recognition
            
        Returns:
            IntentRecognitionResult with intent and confidence
        """
        # Preprocess the text
        processed_text = self.text_preprocessor.preprocess(text)
        
        # Try rule-based approach first
        rule_result = self._rule_based_recognition(processed_text)
        
        # Try ML approach if model is available
        ml_result = None
        if self.ml_model is not None:
            ml_result = self._ml_based_recognition(processed_text)
        
        # Choose best result (higher confidence)
        if ml_result and ml_result.confidence > rule_result.confidence:
            result = ml_result
        else:
            result = rule_result
        
        # Apply context-aware adjustments if context is provided
        if context:
            result = self._apply_context_adjustments(result, context)
        
        # Update context with new information
        self.context_manager.update_context(text, result)
        
        return result
    
    def _rule_based_recognition(self, text: str) -> IntentRecognitionResult:
        """
        Rule-based intent recognition using regex patterns.
        
        Args:
            text: Text to analyze
        
        Returns:
            IntentRecognitionResult with recognized intent
        """
        # Normalize text
        text = text.strip().lower()
        
        # Check against patterns
        matches = []
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    # Calculate a confidence score based on how much of the text matches
                    match = pattern.search(text)
                    match_length = match.end() - match.start()
                    coverage = match_length / len(text) if len(text) > 0 else 0
                    confidence = min(0.9, 0.5 + (coverage * 0.5))  # Cap at 0.9 for rule-based
                    matches.append((intent, confidence))
        
        # Sort matches by confidence
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Get top intent if there are matches, otherwise return unknown
        if matches:
            top_intent, confidence = matches[0]
            alternatives = matches[1:3]  # Include up to 2 alternatives
            return IntentRecognitionResult(
                intent=top_intent,
                confidence=confidence,
                method="rule-based",
                alternatives=alternatives
            )
        
        logger.info("No intent patterns matched, returning 'unknown'")
        return IntentRecognitionResult(
            intent=self.fallback_intent,
            confidence=0.1,  # Low confidence for unknown
            method="rule-based",
            alternatives=[]
        )
    
    def _ml_based_recognition(self, text: str) -> IntentRecognitionResult:
        """
        Machine learning-based intent recognition.
        
        Args:
            text: Text to analyze
        
        Returns:
            IntentRecognitionResult with recognized intent
        """
        try:
            # Get prediction probabilities
            probas = self.ml_model.predict_proba([text])[0]
            
            # Get top intents and probabilities
            indices = np.argsort(probas)[::-1]
            classes = self.ml_model.classes_
            
            top_intent = classes[indices[0]]
            confidence = probas[indices[0]]
            
            # Get alternatives
            alternatives = []
            for i in range(1, min(3, len(indices))):
                alt_intent = classes[indices[i]]
                alt_confidence = probas[indices[i]]
                alternatives.append((alt_intent, alt_confidence))
            
            return IntentRecognitionResult(
                intent=top_intent,
                confidence=confidence,
                method="ml",
                alternatives=alternatives
            )
        except Exception as e:
            logger.error(f"Error in ML-based intent recognition: {e}")
            return IntentRecognitionResult(
                intent=self.fallback_intent,
                confidence=0.1,
                method="ml-fallback",
                alternatives=[]
            )
    
    def _apply_context_adjustments(self, result: IntentRecognitionResult, context: Dict[str, Any]) -> IntentRecognitionResult:
        """
        Apply context-aware adjustments to intent recognition results.
        
        Args:
            result: Initial intent recognition result
            context: Context information
            
        Returns:
            Adjusted intent recognition result
        """
        # Get intent history if available
        intent_history = context.get('intent_history', [])
        previous_intent = intent_history[-1] if intent_history else None
        
        # Check for valid intent transitions
        if previous_intent and previous_intent in self.intent_transitions:
            valid_transitions = self.intent_transitions[previous_intent]
            
            # If the recognized intent is not a valid transition and confidence is low
            if result.intent not in valid_transitions and result.confidence < 0.7:
                # Check if any of the alternatives are valid transitions
                for alt_intent, alt_conf in result.alternatives:
                    if alt_intent in valid_transitions:
                        # If alternative is a valid transition with reasonable confidence, use it
                        if alt_conf > 0.3:
                            logger.info(f"Adjusted intent from {result.intent} to {alt_intent} based on context")
                            return IntentRecognitionResult(
                                intent=alt_intent,
                                confidence=alt_conf * 1.1,  # Slight boost for context relevance
                                method=f"{result.method}+context",
                                alternatives=[(result.intent, result.confidence)] + [
                                    alt for alt in result.alternatives if alt[0] != alt_intent
                                ]
                            )
        
        # Handle repeated questions (potential confusion)
        if context.get('repeated_intent', False) and result.confidence < 0.7:
            # Adjust confidence down for potential misunderstandings
            result.confidence *= 0.9
            logger.info("Reduced confidence due to repeated intent")
        
        # If a product is mentioned, boost confidence slightly
        if context.get('product_mentioned') and result.confidence < 0.95:
            result.confidence = min(0.95, result.confidence * 1.1)
            logger.info("Boosted confidence due to product mention")
        
        return result
    
    def save_examples(self, examples: List[IntentExample], file_path: str) -> bool:
        """
        Save training examples to a file.
        
        Args:
            examples: List of training examples
            file_path: Path to save the examples
            
        Returns:
            Success status
        """
        try:
            data = [ex.to_dict() for ex in examples]
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(examples)} training examples to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save training examples: {e}")
            return False
    
    def load_examples(self, file_path: str) -> List[IntentExample]:
        """
        Load training examples from a file.
        
        Args:
            file_path: Path to load the examples from
            
        Returns:
            List of training examples
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            examples = [IntentExample.from_dict(item) for item in data]
            logger.info(f"Loaded {len(examples)} training examples from {file_path}")
            return examples
        except Exception as e:
            logger.error(f"Failed to load training examples: {e}")
            return []

# Create default model instance
default_model = IntentRecognitionModel()

# Example usage
if __name__ == "__main__":
    # Create some training examples
    examples = [
        IntentExample(text="Hello there", intent="greeting"),
        IntentExample(text="Hi, how are you?", intent="greeting"),
        IntentExample(text="Good morning", intent="greeting"),
        IntentExample(text="Hey", intent="greeting"),
        IntentExample(text="What's up?", intent="greeting"),
        
        IntentExample(text="Goodbye", intent="farewell"),
        IntentExample(text="See you later", intent="farewell"),
        IntentExample(text="Bye for now", intent="farewell"),
        IntentExample(text="Have a nice day", intent="farewell"),
        IntentExample(text="Until next time", intent="farewell"),
        
        IntentExample(text="How do I reset my password?", intent="help"),
        IntentExample(text="I need help with setup", intent="help"),
        IntentExample(text="Can you assist me?", intent="help"),
        IntentExample(text="What are the system requirements?", intent="help"),
        IntentExample(text="How does this feature work?", intent="help"),
        
        IntentExample(text="The app is crashing", intent="problem"),
        IntentExample(text="I'm getting an error message", intent="problem"),
        IntentExample(text="It doesn't work on my device", intent="problem"),
        IntentExample(text="Login fails every time", intent="problem"),
        IntentExample(text="Something is broken", intent="problem"),
        
        IntentExample(text="How much does it cost?", intent="pricing"),
        IntentExample(text="What are your subscription options?", intent="pricing"),
        IntentExample(text="Do you offer discounts?", intent="pricing"),
        IntentExample(text="Can I get a trial?", intent="pricing"),
        IntentExample(text="What's included in the premium plan?", intent="pricing")
    ]
    
    # Train model
    model = IntentRecognitionModel()
    result = model.train(examples)
    
    # Test recognition
    test_texts = [
        "Hello, is anyone there?",
        "I'm having an issue with installation",
        "What is the price for enterprise?",
        "Thanks and goodbye",
        "Something weird is going on with my account"
    ]
    
    print("\nIntent Recognition Results:")
    for text in test_texts:
        intent_result = model.recognize_intent(text)
        print(f"Text: '{text}'")
        print(f"Intent: {intent_result.intent} (confidence: {intent_result.confidence:.2f}, method: {intent_result.method})")
        if intent_result.alternatives:
            alt_str = ", ".join([f"{i}:{c:.2f}" for i, c in intent_result.alternatives])
            print(f"Alternatives: {alt_str}")
        print()
        
        # Test with context
        context = {'intent_history': ['greeting'], 'product_mentioned': 'ARP Guard'}
        intent_result_with_context = model.recognize_intent(text, context)
        print(f"With context - Intent: {intent_result_with_context.intent} (confidence: {intent_result_with_context.confidence:.2f}, method: {intent_result_with_context.method})")
        print() 