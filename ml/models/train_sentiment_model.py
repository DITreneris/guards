#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Train Sentiment Analysis Model

This script trains and saves a sentiment analysis model for the ML framework.
It uses generated data or existing data files for training.
"""

import os
import json
import logging
import argparse
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, accuracy_score, f1_score

# Set up path to ensure modules can be imported
import sys
module_path = str(Path(__file__).parent.parent.parent)
if module_path not in sys.path:
    sys.path.append(module_path)

from ml.models import save_model, SENTIMENT_MODEL_PATH
from ml.models.sentiment_analysis import SentimentExample, TextNormalizer
from ml.data.generate_sentiment_data import generate_sentiment_examples

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_examples(file_path: str) -> List[SentimentExample]:
    """
    Load training examples from a file.
    
    Args:
        file_path: Path to the JSON file with examples
        
    Returns:
        List of SentimentExample objects
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        examples = [SentimentExample.from_dict(item) for item in data]
        logger.info(f"Loaded {len(examples)} examples from {file_path}")
        return examples
    
    except Exception as e:
        logger.error(f"Error loading examples from {file_path}: {e}")
        return []

def generate_training_data(count_per_sentiment: int) -> List[SentimentExample]:
    """
    Generate synthetic training data.
    
    Args:
        count_per_sentiment: Number of examples per sentiment
        
    Returns:
        List of SentimentExample objects
    """
    # Generate raw examples as dictionaries
    examples_dict = generate_sentiment_examples(count_per_sentiment)
    
    # Convert to SentimentExample objects
    examples = [SentimentExample.from_dict(item) for item in examples_dict]
    
    logger.info(f"Generated {len(examples)} synthetic examples")
    return examples

def train_sentiment_model(examples: List[SentimentExample], test_size: float = 0.2, 
                         grid_search: bool = True) -> Dict[str, Any]:
    """
    Train a sentiment analysis model.
    
    Args:
        examples: List of training examples
        test_size: Proportion of data to use for testing
        grid_search: Whether to perform hyperparameter tuning
        
    Returns:
        Dictionary with training results and the trained model
    """
    # Normalize text
    normalizer = TextNormalizer()
    texts = [normalizer.normalize(ex.text) for ex in examples]
    sentiments = [ex.sentiment for ex in examples]
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        texts, sentiments, test_size=test_size, random_state=42, stratify=sentiments
    )
    
    # Set up text vectorizer
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=15000,
        min_df=2,
        sublinear_tf=True
    )
    
    # Choose classifier
    if len(examples) > 100:
        classifier = SVC(probability=True, kernel='rbf', class_weight='balanced')
        logger.info("Using SVM classifier for sentiment analysis")
    else:
        classifier = RandomForestClassifier(
            n_estimators=200,
            class_weight='balanced',
            random_state=42
        )
        logger.info("Using RandomForest classifier for sentiment analysis")
    
    # Set up pipeline
    pipeline = Pipeline([
        ('vectorizer', vectorizer),
        ('classifier', classifier)
    ])
    
    # Perform grid search if requested
    if grid_search and len(examples) > 50:
        logger.info("Performing grid search for sentiment model")
        
        param_grid = {}
        
        # Vectorizer parameters
        param_grid['vectorizer__max_features'] = [10000, 15000, 20000]
        param_grid['vectorizer__ngram_range'] = [(1, 2), (1, 3)]
        
        # Classifier parameters
        if isinstance(classifier, RandomForestClassifier):
            param_grid['classifier__n_estimators'] = [100, 200, 300]
        elif isinstance(classifier, SVC):
            param_grid['classifier__C'] = [0.1, 1.0, 10.0]
            param_grid['classifier__gamma'] = ['scale', 'auto', 0.1]
        
        # Set up grid search
        search = GridSearchCV(
            pipeline, param_grid, cv=3, scoring='f1_weighted', verbose=1, n_jobs=-1
        )
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
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    # Get sample predictions
    sample_indices = np.random.choice(len(X_test), min(5, len(X_test)), replace=False)
    sample_predictions = []
    for idx in sample_indices:
        sample_text = X_test[idx]
        true_sentiment = y_test[idx]
        pred_sentiment = y_pred[idx]
        sample_predictions.append({
            "text": sample_text,
            "true": true_sentiment,
            "predicted": pred_sentiment
        })
    
    logger.info(f"Sentiment model training complete. Accuracy: {accuracy:.2f}, F1: {f1:.2f}")
    
    results = {
        "model": pipeline,
        "accuracy": accuracy,
        "f1_score": f1,
        "examples_count": len(examples),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "sample_predictions": sample_predictions,
        "classification_report": report
    }
    
    return results

def save_sentiment_model(model, save_path: Optional[str] = None) -> bool:
    """
    Save the trained sentiment model.
    
    Args:
        model: Trained model to save
        save_path: Path to save the model (uses default if None)
        
    Returns:
        Success status
    """
    if save_path is None:
        save_path = SENTIMENT_MODEL_PATH
    
    try:
        save_model(model, save_path)
        logger.info(f"Saved sentiment model to {save_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving sentiment model: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Train sentiment analysis model')
    parser.add_argument('--data', type=str, help='Path to training data file')
    parser.add_argument('--generate', type=int, default=100, help='Number of examples to generate per sentiment')
    parser.add_argument('--output', type=str, help='Path to save the model')
    parser.add_argument('--no-grid-search', action='store_true', help='Disable grid search')
    args = parser.parse_args()
    
    # Load or generate examples
    examples = []
    if args.data:
        examples = load_examples(args.data)
    
    # If no data provided or loading failed, generate data
    if not examples:
        examples = generate_training_data(args.generate)
    
    # Train model
    results = train_sentiment_model(examples, grid_search=not args.no_grid_search)
    
    # Save model
    save_path = args.output if args.output else SENTIMENT_MODEL_PATH
    success = save_sentiment_model(results["model"], save_path)
    
    # Print results
    print("\nSentiment Model Training Results:")
    print(f"Examples Count: {results['examples_count']}")
    print(f"Accuracy: {results['accuracy']:.4f}")
    print(f"F1 Score: {results['f1_score']:.4f}")
    print(f"Model saved: {success}")
    
    # Print sample predictions
    print("\nSample Predictions:")
    for i, sample in enumerate(results['sample_predictions']):
        print(f"  Example {i+1}: '{sample['text']}'")
        print(f"  True: {sample['true']}")
        print(f"  Predicted: {sample['predicted']}")
        print("")
    
    # Print sentiment distribution
    sentiment_counts = {}
    for ex in examples:
        sentiment = ex.sentiment
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
    
    print("\nSentiment Distribution:")
    for sentiment, count in sentiment_counts.items():
        print(f"  {sentiment}: {count} examples")

if __name__ == "__main__":
    main() 