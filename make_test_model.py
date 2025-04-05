#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Model Generator
Creates sample models for testing quantization functionality.
"""

import os
import sys
import pickle
import logging
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path if needed
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Model paths
MODELS_DIR = Path("ml/models")
INTENT_MODEL_PATH = MODELS_DIR / "intent_model.pkl"
SENTIMENT_MODEL_PATH = MODELS_DIR / "sentiment_model.pkl"
EMAIL_MODEL_PATH = MODELS_DIR / "email_categorization_model.pkl"

def save_model(model, path):
    """Save a model to the specified path"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Saved model to {path}")
    
    # Get file size
    size_bytes = os.path.getsize(path)
    logger.info(f"Model size: {size_bytes/1024:.2f} KB")
    
    return size_bytes

def create_intent_model():
    """Create a sample intent recognition model"""
    logger.info("Creating intent recognition model...")
    
    # Sample training data (very small for this example)
    texts = [
        "Hello", "Hi there", "Hey", "Greetings",  # greeting
        "Goodbye", "See you", "Bye", "Later",  # farewell
        "Help me", "I need help", "How do I", "Assist",  # help
        "Not working", "Issue", "Problem", "Error"  # problem (removed "Bug" to make counts match)
    ]
    
    labels = (
        ["greeting"] * 4 + 
        ["farewell"] * 4 + 
        ["help"] * 4 + 
        ["problem"] * 4
    )
    
    # Create a pipeline with TF-IDF and Random Forest
    model = Pipeline([
        ('vectorizer', TfidfVectorizer(max_features=1000)),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    # Fit the model
    model.fit(texts, labels)
    
    # Save the model
    return save_model(model, INTENT_MODEL_PATH)

def create_sentiment_model():
    """Create a sample sentiment analysis model"""
    logger.info("Creating sentiment analysis model...")
    
    # Sample training data (very small for this example)
    texts = [
        "I love this product", "Great experience", "Amazing features", "Very happy",  # positive
        "Terrible service", "Awful experience", "Bad quality", "Disappointed",  # negative
        "It's okay", "Not bad", "Could be better", "Average performance"  # neutral
    ]
    
    labels = (
        ["positive"] * 4 + 
        ["negative"] * 4 + 
        ["neutral"] * 4
    )
    
    # Create a pipeline with TF-IDF and SVM
    model = Pipeline([
        ('vectorizer', TfidfVectorizer(max_features=1000)),
        ('classifier', SVC(kernel='linear', probability=True, random_state=42))
    ])
    
    # Fit the model
    model.fit(texts, labels)
    
    # Save the model
    return save_model(model, SENTIMENT_MODEL_PATH)

def create_email_model():
    """Create a sample email categorization model"""
    logger.info("Creating email categorization model...")
    
    # Sample training data (very small for this example)
    texts = [
        "Please help with my account", "I need support", "Technical issue",  # support
        "I want to buy", "Pricing info", "Subscription options",  # sales
        "New feature suggestion", "Enhancement idea", "Product improvement",  # feature_request
        "I found a bug", "Application crashes", "Error when clicking",  # bug
        "Just saying hello", "Thank you", "General feedback"  # other
    ]
    
    labels = (
        ["support"] * 3 + 
        ["sales"] * 3 + 
        ["feature_request"] * 3 + 
        ["bug"] * 3 + 
        ["other"] * 3
    )
    
    # Create a pipeline with TF-IDF and Logistic Regression
    model = Pipeline([
        ('vectorizer', TfidfVectorizer(max_features=1000)),
        ('classifier', LogisticRegression(max_iter=1000, random_state=42))
    ])
    
    # Fit the model
    model.fit(texts, labels)
    
    # Save the model
    return save_model(model, EMAIL_MODEL_PATH)

def main():
    """Create all test models"""
    logger.info("Creating test models for quantization...")
    
    # Ensure models directory exists
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # Create models
    intent_size = create_intent_model()
    sentiment_size = create_sentiment_model()
    email_size = create_email_model()
    
    # Print summary
    total_size = intent_size + sentiment_size + email_size
    logger.info("Test models created successfully:")
    logger.info(f"  Intent model size:     {intent_size/1024:.2f} KB")
    logger.info(f"  Sentiment model size:  {sentiment_size/1024:.2f} KB")
    logger.info(f"  Email model size:      {email_size/1024:.2f} KB")
    logger.info(f"  Total size:            {total_size/1024:.2f} KB")

if __name__ == "__main__":
    main() 