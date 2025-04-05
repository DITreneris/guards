#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enhanced ML Framework - Training and Testing Script

This script demonstrates the enhanced ML capabilities by:
1. Generating synthetic training data for intent recognition
2. Generating synthetic training data for sentiment analysis 
3. Generating synthetic training data for email categorization
4. Training and saving all the models
5. Testing the models on sample data

Run this script to bootstrap the ML capabilities with pre-trained models.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure required directories exist
def ensure_dirs_exist():
    """Make sure all required directories exist"""
    dirs = [
        "ml/data",
        "ml/models"
    ]
    for directory in dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
    logger.info("Verified required directories exist")

def generate_intent_data(count_per_intent=50, save_path=None):
    """Generate training data for intent recognition"""
    try:
        from ml.data.generate_intent_data import generate_intent_examples
        
        examples = generate_intent_examples(count_per_intent)
        
        if save_path:
            from ml.data.generate_intent_data import save_examples
            save_examples(examples, save_path)
            logger.info(f"Generated and saved {len(examples)} intent examples")
        
        return examples
    except Exception as e:
        logger.error(f"Error generating intent data: {e}")
        return []

def generate_sentiment_data(count_per_sentiment=50, save_path=None):
    """Generate training data for sentiment analysis"""
    try:
        from ml.data.generate_sentiment_data import generate_sentiment_examples
        
        examples = generate_sentiment_examples(count_per_sentiment)
        
        if save_path:
            from ml.data.generate_sentiment_data import save_examples
            save_examples(examples, save_path)
            logger.info(f"Generated and saved {len(examples)} sentiment examples")
        
        return examples
    except Exception as e:
        logger.error(f"Error generating sentiment data: {e}")
        return []

def generate_email_data(count_per_category=30, save_path=None):
    """Generate training data for email categorization"""
    try:
        from ml.models.train_email_model import generate_email_examples, save_examples
        
        examples = generate_email_examples(count_per_category)
        
        if save_path:
            save_examples(examples, save_path)
            logger.info(f"Generated and saved {len(examples)} email examples")
        
        return examples
    except Exception as e:
        logger.error(f"Error generating email data: {e}")
        return []

def train_intent_model():
    """Train the intent recognition model"""
    try:
        from ml.models.intent_recognition import IntentRecognitionModel, IntentExample
        
        # Generate or load training data
        examples_path = "ml/data/intent_examples.json"
        
        if Path(examples_path).exists():
            # Load existing examples
            model = IntentRecognitionModel()
            examples = model.load_examples(examples_path)
        else:
            # Generate new examples
            examples_dict = generate_intent_data(80, examples_path)
            examples = [IntentExample.from_dict(ex) for ex in examples_dict]
        
        # Train model
        if examples:
            model = IntentRecognitionModel()
            result = model.train(examples, grid_search=True)
            logger.info(f"Intent model trained with {len(examples)} examples, accuracy: {result.get('accuracy', 0):.2f}")
            return True
        else:
            logger.error("No training examples for intent model")
            return False
    except Exception as e:
        logger.error(f"Error training intent model: {e}")
        return False

def train_sentiment_model():
    """Train the sentiment analysis model"""
    try:
        from ml.models.train_sentiment_model import train_sentiment_model, save_sentiment_model, generate_training_data
        
        # Generate training data
        examples = generate_training_data(70)
        
        # Train model
        if examples:
            results = train_sentiment_model(examples, grid_search=True)
            save_sentiment_model(results["model"])
            logger.info(f"Sentiment model trained with {len(examples)} examples, accuracy: {results['accuracy']:.2f}")
            return True
        else:
            logger.error("No training examples for sentiment model")
            return False
    except Exception as e:
        logger.error(f"Error training sentiment model: {e}")
        return False

def train_email_model():
    """Train the email categorization model"""
    try:
        from ml.models.train_email_model import generate_email_examples, train_email_model
        from ml.models import save_model, EMAIL_CATEGORIZATION_MODEL_PATH
        
        # Generate examples
        examples = generate_email_examples(25)
        
        # Train model
        if examples:
            results = train_email_model(examples, grid_search=True)
            save_model(results["model"], EMAIL_CATEGORIZATION_MODEL_PATH)
            logger.info(f"Email model trained with {len(examples)} examples, accuracy: {results['accuracy']:.2f}")
            return True
        else:
            logger.error("No training examples for email model")
            return False
    except Exception as e:
        logger.error(f"Error training email model: {e}")
        return False

def test_models():
    """Test all ML models with sample inputs"""
    results = {
        "intent_recognition": {},
        "sentiment_analysis": {},
        "email_categorization": {}
    }
    
    # Test intent recognition
    try:
        from ml.models.intent_recognition import default_model as intent_model
        
        test_texts = [
            "Hello, I need some assistance",
            "I'm having trouble configuring ARP Guard",
            "What are the pricing options for Network Shield?",
            "Thanks for your help, goodbye",
            "The latest update broke my installation"
        ]
        
        intent_results = []
        for text in test_texts:
            result = intent_model.recognize_intent(text)
            intent_results.append({
                "text": text,
                "intent": result.intent,
                "confidence": result.confidence,
                "method": result.method
            })
        
        results["intent_recognition"] = {
            "status": "success",
            "sample_results": intent_results
        }
        logger.info("Intent recognition model tested successfully")
    except Exception as e:
        results["intent_recognition"] = {
            "status": "error",
            "message": str(e)
        }
        logger.error(f"Error testing intent model: {e}")
    
    # Test sentiment analysis
    try:
        from ml.models.model_loader import sentiment_model
        
        test_texts = [
            "I really love the new features, they're fantastic!",
            "This product is terrible. I keep getting errors.",
            "Could you tell me how to configure the firewall?",
            "I'm not very happy with how this works.",
            "Thanks for fixing that issue, much better now!"
        ]
        
        sentiment_results = []
        for text in test_texts:
            result = sentiment_model.analyze_sentiment(text)
            sentiment_results.append({
                "text": text,
                "sentiment": result.get("overall", "neutral"),
                "confidence": result.get("confidence", 0.0),
                "method": result.get("method", "unknown")
            })
        
        results["sentiment_analysis"] = {
            "status": "success",
            "sample_results": sentiment_results
        }
        logger.info("Sentiment analysis model tested successfully")
    except Exception as e:
        results["sentiment_analysis"] = {
            "status": "error",
            "message": str(e)
        }
        logger.error(f"Error testing sentiment model: {e}")
    
    # Test email categorization
    try:
        from ml.models.model_loader import email_categorization_model
        
        test_emails = [
            {
                "subject": "Need help with ARP Guard installation",
                "body": "Hello, I'm having trouble installing ARP Guard on our server. Can you help me resolve this issue?"
            },
            {
                "subject": "Pricing for Enterprise license",
                "body": "I'm interested in purchasing Enterprise licenses for our company. Could you provide pricing information for 50 users?"
            },
            {
                "subject": "Feedback on the new dashboard",
                "body": "I wanted to share some feedback on the new dashboard. The layout is much better, but the reporting feature is still confusing."
            }
        ]
        
        email_results = []
        for email in test_emails:
            result = email_categorization_model.categorize_email(email["subject"], email["body"])
            email_results.append({
                "subject": email["subject"],
                "category": result.get("primary_category", "unknown"),
                "confidence": result.get("confidence", 0.0),
                "method": result.get("method", "unknown")
            })
        
        results["email_categorization"] = {
            "status": "success",
            "sample_results": email_results
        }
        logger.info("Email categorization model tested successfully")
    except Exception as e:
        results["email_categorization"] = {
            "status": "error",
            "message": str(e)
        }
        logger.error(f"Error testing email model: {e}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Enhanced ML Framework - Training and Testing')
    parser.add_argument('--skip-intent', action='store_true', help='Skip intent model training')
    parser.add_argument('--skip-sentiment', action='store_true', help='Skip sentiment model training')
    parser.add_argument('--skip-email', action='store_true', help='Skip email model training')
    parser.add_argument('--test-only', action='store_true', help='Only test existing models')
    parser.add_argument('--output', type=str, help='Path to save test results')
    args = parser.parse_args()
    
    # Ensure required directories exist
    ensure_dirs_exist()
    
    # Train models
    if not args.test_only:
        print("\n=== TRAINING ML MODELS ===\n")
        
        if not args.skip_intent:
            print("Training intent recognition model...")
            intent_success = train_intent_model()
            print(f"Intent model training {'successful' if intent_success else 'failed'}\n")
        
        if not args.skip_sentiment:
            print("Training sentiment analysis model...")
            sentiment_success = train_sentiment_model()
            print(f"Sentiment model training {'successful' if sentiment_success else 'failed'}\n")
        
        if not args.skip_email:
            print("Training email categorization model...")
            email_success = train_email_model()
            print(f"Email model training {'successful' if email_success else 'failed'}\n")
    
    # Test models
    print("\n=== TESTING ML MODELS ===\n")
    test_results = test_models()
    
    # Print test results
    if test_results["intent_recognition"].get("status") == "success":
        print("\nIntent Recognition Results:")
        for result in test_results["intent_recognition"]["sample_results"]:
            print(f"  Text: '{result['text']}'")
            print(f"  Intent: {result['intent']} (confidence: {result['confidence']:.2f}, method: {result['method']})")
            print()
    
    if test_results["sentiment_analysis"].get("status") == "success":
        print("\nSentiment Analysis Results:")
        for result in test_results["sentiment_analysis"]["sample_results"]:
            print(f"  Text: '{result['text']}'")
            print(f"  Sentiment: {result['sentiment']} (confidence: {result['confidence']:.2f}, method: {result['method']})")
            print()
    
    if test_results["email_categorization"].get("status") == "success":
        print("\nEmail Categorization Results:")
        for result in test_results["email_categorization"]["sample_results"]:
            print(f"  Subject: '{result['subject']}'")
            print(f"  Category: {result['category']} (confidence: {result['confidence']:.2f}, method: {result['method']})")
            print()
    
    # Save test results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(test_results, f, indent=2)
        print(f"\nTest results saved to {args.output}")
    
    print("\n=== ENHANCED ML FRAMEWORK SETUP COMPLETE ===\n")

if __name__ == "__main__":
    main() 