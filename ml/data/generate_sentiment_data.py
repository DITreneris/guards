#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sentiment Data Generator

This script generates training data for the sentiment analysis model by using
templates and variations to create a diverse dataset.
"""

import os
import json
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Ensure the data directory exists
data_dir = Path(__file__).parent
data_dir.mkdir(exist_ok=True)

# Sentiment templates - each sentiment has a list of templates where {variables} can be substituted
SENTIMENT_TEMPLATES = {
    "positive": [
        "I {positive_verb} {product}, it's {positive_adj}!",
        "The {feature} is {positive_adj} and {positive_adj}.",
        "Thanks for the {positive_adj} {support}.",
        "{product} {positive_verb} my expectations{exclamation}",
        "Great job on the {feature}, it's {positive_adj}.",
        "I'm {positive_emotion} with how {product} {positive_verb}.",
        "The {feature} {positive_verb} perfectly{exclamation}",
        "{product} has {positive_adj} {feature} that I {positive_verb}.",
        "Your {support} was {positive_adj} and {positive_adj}.",
        "I {positive_verb} how {easy} it is to {action}.",
        "What a {positive_adj} {product} you've built{exclamation}",
        "{positive_adv} {positive_adj} work on the {feature}!",
        "This is exactly what I needed, {positive_adj} job!",
        "I {positive_verb} the {feature}, it {positive_verb} so {positive_adv}.",
        "The new {feature} is a {positive_adj} addition."
    ],
    
    "negative": [
        "I {negative_verb} {product}, it's {negative_adj}.",
        "The {feature} is {negative_adj} and {negative_adj}.",
        "Your {support} was {negative_adj} and {negative_adj}.",
        "{product} {negative_verb} my expectations.",
        "I'm {negative_emotion} with how {product} {negative_verb}.",
        "The {feature} {negative_verb} completely{exclamation}",
        "This is the {negative_adj} {product} I've ever used.",
        "{product} has a {negative_adj} {feature} that I {negative_verb}.",
        "I {negative_verb} how {difficult} it is to {action}.",
        "Your {support} team {negative_verb} to help me.",
        "Why is the {feature} so {negative_adj}?",
        "I'm having a {negative_adj} time with {product}.",
        "The {feature} is {negative_adv} {negative_adj} and needs fixing.",
        "I'm getting {error} when I try to {action}.",
        "This is not what I expected, very {negative_adj}."
    ],
    
    "neutral": [
        "I'm using {product} for {task}.",
        "Could you tell me how to {action}?",
        "I'm looking for information about {feature}.",
        "Does {product} support {technology}?",
        "When will the next update be released?",
        "I need documentation for {feature}.",
        "How do I {action} with {product}?",
        "Is there a guide for {task}?",
        "What are the system requirements for {product}?",
        "I'm trying to {action} but I'm not sure how.",
        "Does the {plan} plan include {feature}?",
        "I'd like to know more about {feature}.",
        "Can you explain how {feature} works?",
        "I need to {action} for my project.",
        "Which version of {product} supports {technology}?"
    ]
}

# Variables to substitute in the templates
VARIABLES = {
    "exclamation": ["!", "!!", "!!!"],
    "product": ["ARP Guard", "Network Shield", "Perimeter Defender", "Access Manager", "Guard Console", "Security Monitor", "your product", "your software", "your tool"],
    "feature": ["dashboard", "reporting", "notifications", "alerts", "integration", "API", "monitoring", "settings", "user management", "authentication", "password reset", "network scanning", "threat detection", "vulnerability assessment", "email notifications", "mobile app"],
    "support": ["support", "customer service", "help desk", "technical team", "service", "assistance"],
    "action": ["set up", "configure", "install", "use", "upgrade", "connect", "integrate", "customize", "deploy", "monitor", "secure", "update", "access", "log in", "export data", "generate reports"],
    "task": ["network monitoring", "security analysis", "penetration testing", "vulnerability assessment", "compliance checking", "threat detection", "password management", "system maintenance", "data backup", "risk assessment"],
    "technology": ["Windows", "Mac", "Linux", "cloud", "API", "REST", "SOAP", "Docker", "Kubernetes", "OAuth", "SAML", "SSO", "2FA", "biometrics", "LDAP", "Active Directory"],
    "plan": ["basic", "standard", "premium", "enterprise", "professional", "free", "trial", "business", "team", "starter"],
    "error": ["an error", "error code 404", "error NW-5523", "a connection timeout", "authentication failure", "a permission denied message", "unexpected behavior", "a crash", "a blue screen", "a critical failure"],
    
    # Positive words
    "positive_adj": ["amazing", "excellent", "fantastic", "great", "awesome", "wonderful", "impressive", "outstanding", "superb", "brilliant", "helpful", "intuitive", "reliable", "solid", "innovative", "user-friendly", "powerful", "efficient", "effective", "valuable"],
    "positive_verb": ["love", "like", "enjoy", "appreciate", "recommend", "admire", "value", "praise", "celebrate", "endorse", "adore", "prefer", "cherish", "treasure", "respect"],
    "positive_emotion": ["happy", "pleased", "delighted", "satisfied", "impressed", "thrilled", "excited", "glad", "grateful", "content", "relieved", "optimistic", "enthusiastic"],
    "positive_adv": ["incredibly", "extremely", "remarkably", "exceptionally", "surprisingly", "wonderfully", "impressively", "outstandingly", "exceedingly", "tremendously"],
    "easy": ["easy", "simple", "straightforward", "effortless", "intuitive", "user-friendly", "accessible", "convenient", "smooth", "uncomplicated"],
    
    # Negative words
    "negative_adj": ["terrible", "awful", "horrible", "poor", "disappointing", "frustrating", "useless", "confusing", "difficult", "complicated", "unreliable", "buggy", "flawed", "problematic", "cumbersome", "slow", "inefficient", "unstable", "defective", "inadequate"],
    "negative_verb": ["hate", "dislike", "regret", "despise", "criticize", "complain", "disapprove", "detest", "avoid", "dismiss", "reject", "resent", "doubt", "distrust", "condemn"],
    "negative_emotion": ["unhappy", "disappointed", "frustrated", "annoyed", "upset", "angry", "dissatisfied", "displeased", "irritated", "concerned", "worried", "troubled", "distressed"],
    "negative_adv": ["extremely", "highly", "seriously", "terribly", "horribly", "awfully", "ridiculously", "absurdly", "unbelievably", "impossibly"],
    "difficult": ["difficult", "hard", "complicated", "complex", "challenging", "cumbersome", "troublesome", "problematic", "inconvenient", "confusing"]
}

# Emotion categories
EMOTIONS = {
    "positive": ["happy", "joyful", "excited", "grateful", "satisfied", "delighted", "proud", None],
    "negative": ["angry", "frustrated", "sad", "disappointed", "fearful", "worried", "annoyed", None],
    "neutral": [None]
}

def generate_utterance(template: str) -> str:
    """
    Generate an utterance by substituting variables in a template.
    
    Args:
        template: Template string with {variable} placeholders
        
    Returns:
        Completed utterance with variables substituted
    """
    utterance = template
    
    # Find all variables in the template
    import re
    variables = re.findall(r'\{(\w+)\}', template)
    
    # Substitute each variable
    for var in variables:
        if var in VARIABLES:
            value = random.choice(VARIABLES[var])
            utterance = utterance.replace(f"{{{var}}}", value)
    
    return utterance

def generate_sentiment_examples(count_per_sentiment: int = 50) -> List[Dict[str, Any]]:
    """
    Generate sentiment examples using the templates.
    
    Args:
        count_per_sentiment: Number of examples to generate per sentiment
        
    Returns:
        List of example dictionaries with text and sentiment
    """
    examples = []
    
    for sentiment, templates in SENTIMENT_TEMPLATES.items():
        for _ in range(count_per_sentiment):
            # Select a random template
            template = random.choice(templates)
            
            # Generate an utterance
            text = generate_utterance(template)
            
            # Calculate intensity (0.0-1.0) - higher for clear positives and negatives
            if sentiment == "positive":
                intensity = random.uniform(0.5, 1.0)
            elif sentiment == "negative":
                intensity = random.uniform(0.5, 1.0)
            else:
                intensity = random.uniform(0.0, 0.3)
            
            # Add emotion if applicable
            emotion = random.choice(EMOTIONS[sentiment])
            
            # Add metadata
            metadata = {}
            
            # Randomly add product info to metadata
            if "product" in template and random.random() < 0.7:
                for product in VARIABLES["product"]:
                    if product in text and product not in ["your product", "your software", "your tool"]:
                        metadata["product"] = product
                        break
            
            examples.append({
                "text": text,
                "sentiment": sentiment,
                "emotion": emotion,
                "intensity": intensity,
                "metadata": metadata
            })
    
    # Shuffle examples
    random.shuffle(examples)
    
    return examples

def save_examples(examples: List[Dict[str, Any]], file_path: str):
    """
    Save examples to a JSON file.
    
    Args:
        examples: List of example dictionaries
        file_path: Path to save the file
    """
    with open(file_path, 'w') as f:
        json.dump(examples, f, indent=2)
    print(f"Saved {len(examples)} examples to {file_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate sentiment analysis training data')
    parser.add_argument('--count', type=int, default=50, help='Number of examples per sentiment')
    parser.add_argument('--output', type=str, default='generated_sentiment_examples.json', help='Output file name')
    args = parser.parse_args()
    
    # Generate examples
    examples = generate_sentiment_examples(args.count)
    
    # Save to file
    output_path = data_dir / args.output
    save_examples(examples, str(output_path))
    
    # Print sentiment distribution
    sentiment_counts = {}
    for example in examples:
        sentiment = example["sentiment"]
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
    
    print("\nSentiment distribution:")
    for sentiment, count in sorted(sentiment_counts.items()):
        print(f"  {sentiment}: {count} examples")
    
    print(f"\nTotal: {len(examples)} examples")
    print(f"Examples saved to: {output_path}")

if __name__ == "__main__":
    main() 