#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Intent Data Generator

This script generates additional training data for the intent recognition model
by using templates and variations to create a larger dataset.
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

# Intent templates - each intent has a list of templates where {variables} can be substituted
INTENT_TEMPLATES = {
    "greeting": [
        "Hello{exclamation}",
        "Hi{exclamation}",
        "Hey{exclamation}",
        "Good {time_of_day}{exclamation}",
        "{greeting} there{exclamation}",
        "{greeting}, how are you{question}",
        "{greeting}, how's it going{question}",
        "{greeting}, how can I get help today{question}",
        "I need some assistance{exclamation}"
    ],
    
    "farewell": [
        "Goodbye{exclamation}",
        "Bye{exclamation}",
        "See you later{exclamation}",
        "Talk to you soon{exclamation}",
        "Have a {adjective} day{exclamation}",
        "Thanks for your help{exclamation}",
        "That's all I needed{exclamation}",
        "I'm done for now{exclamation}",
        "I'll get back to you later{exclamation}"
    ],
    
    "help": [
        "How do I {action} {product}{question}",
        "I need help with {action}",
        "Can you help me {action}{question}",
        "Could you assist me with {product}{question}",
        "I'm trying to {action} but I can't figure it out",
        "What's the best way to {action}{question}",
        "Is there a guide for {action}{question}",
        "Where can I find information about {product}{question}",
        "How does {feature} work{question}",
        "I'm looking for documentation on {feature}",
        "Can you explain how to {action}{question}",
        "I need assistance with {product}"
    ],
    
    "problem": [
        "{product} is {problem_state}",
        "I'm getting {error} when trying to {action}",
        "There's an issue with {feature}",
        "Something's wrong with {product}",
        "I can't {action} because {reason}",
        "The {feature} doesn't work as expected",
        "I'm experiencing {problem} with {product}",
        "When I try to {action}, {product} {problem_state}",
        "{feature} isn't working properly",
        "I'm stuck with {error} in {product}",
        "The system gives me {error} when I {action}"
    ],
    
    "feature_request": [
        "Could you add {feature} to {product}{question}",
        "I'd like to request {feature} functionality",
        "It would be great if {product} had {feature}",
        "I wish {product} could {action}",
        "The product is missing {feature}",
        "Would it be possible to implement {feature}{question}",
        "Can you add support for {technology}{question}",
        "Please consider adding {feature}",
        "Is there a plan to add {feature} in the future{question}",
        "I suggest adding {feature} to improve user experience"
    ],
    
    "pricing": [
        "How much does {product} cost{question}",
        "What's the price of {product}{question}",
        "Do you offer {discount_type} discounts{question}",
        "Is there a free trial available{question}",
        "What's included in the {plan} plan{question}",
        "How does the licensing work{question}",
        "Is there a {time_period} subscription option{question}",
        "How much for {quantity} licenses{question}",
        "What are your pricing tiers{question}",
        "Can I get information about enterprise pricing{question}",
        "I'd like to know about upgrading my plan"
    ]
}

# Variables to substitute in the templates
VARIABLES = {
    "exclamation": ["!", "", "."],
    "question": ["?", ""],
    "greeting": ["Hello", "Hi", "Hey", "Greetings"],
    "time_of_day": ["morning", "afternoon", "evening", "day"],
    "adjective": ["nice", "great", "wonderful", "good", "fantastic"],
    "product": ["ARP Guard", "ARP Guard Pro", "Network Shield", "Perimeter Defender", "Access Manager", "Guard Console", "Security Monitor", "your product", "the software", "the tool", "the dashboard"],
    "action": ["set up", "configure", "install", "use", "upgrade", "connect", "integrate", "customize", "deploy", "monitor", "secure", "update", "access", "log in", "export data", "generate reports", "reset my password", "find settings", "change my account"],
    "feature": ["dashboard", "reporting", "notifications", "alerts", "integration", "API", "monitoring", "settings", "user management", "authentication", "password reset", "network scanning", "threat detection", "vulnerability assessment", "email notifications", "mobile app"],
    "problem_state": ["not working", "crashing", "showing errors", "very slow", "freezing", "not responding", "displaying an error message", "failing to start", "not detecting threats", "not connecting", "giving false positives"],
    "error": ["an error", "error code 404", "error NW-5523", "a connection timeout", "authentication failure", "a permission denied message", "unexpected behavior", "a crash", "a blue screen", "a critical failure"],
    "reason": ["of an error", "it's not responding", "the server is down", "I don't have permission", "I'm missing credentials", "the configuration is wrong", "there's a network issue", "it requires admin rights"],
    "problem": ["problems", "issues", "errors", "difficulties", "bugs", "glitches", "unexpected behavior", "performance issues"],
    "discount_type": ["educational", "non-profit", "bulk", "enterprise", "loyalty", "early payment", "referral"],
    "time_period": ["monthly", "annual", "quarterly", "3-year", "lifetime"],
    "quantity": ["5", "10", "25", "50", "100", "enterprise", "team", "department"]
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

def generate_intent_examples(count_per_intent: int = 50) -> List[Dict[str, Any]]:
    """
    Generate intent examples using the templates.
    
    Args:
        count_per_intent: Number of examples to generate per intent
        
    Returns:
        List of example dictionaries with text and intent
    """
    examples = []
    
    for intent, templates in INTENT_TEMPLATES.items():
        for _ in range(count_per_intent):
            # Select a random template
            template = random.choice(templates)
            
            # Generate an utterance
            text = generate_utterance(template)
            
            # Add metadata
            metadata = {}
            
            # Randomly add product info to metadata
            if "product" in template and random.random() < 0.7:
                for product in VARIABLES["product"]:
                    if product in text and product not in ["your product", "the software", "the tool", "the dashboard"]:
                        metadata["product"] = product
                        break
            
            examples.append({
                "text": text,
                "intent": intent,
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
    parser = argparse.ArgumentParser(description='Generate intent recognition training data')
    parser.add_argument('--count', type=int, default=50, help='Number of examples per intent')
    parser.add_argument('--output', type=str, default='generated_intent_examples.json', help='Output file name')
    args = parser.parse_args()
    
    # Generate examples
    examples = generate_intent_examples(args.count)
    
    # Save to file
    output_path = data_dir / args.output
    save_examples(examples, str(output_path))
    
    # Print intent distribution
    intent_counts = {}
    for example in examples:
        intent = example["intent"]
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    print("\nIntent distribution:")
    for intent, count in sorted(intent_counts.items()):
        print(f"  {intent}: {count} examples")
    
    print(f"\nTotal: {len(examples)} examples")
    print(f"Examples saved to: {output_path}")

if __name__ == "__main__":
    main() 