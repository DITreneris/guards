#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Train Email Categorization Model

This script trains and saves an email categorization model for the ML framework.
It creates a model to classify emails into various categories based on content.
"""

import os
import json
import logging
import argparse
import random
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, accuracy_score, f1_score

# Set up path to ensure modules can be imported
import sys
module_path = str(Path(__file__).parent.parent.parent)
if module_path not in sys.path:
    sys.path.append(module_path)

from ml.models import save_model, EMAIL_CATEGORIZATION_MODEL_PATH

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class EmailExample:
    """Example for email categorization training."""
    subject: str
    body: str
    category: str
    priority: Optional[str] = None  # high, medium, low
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailExample':
        """Create an EmailExample from a dictionary."""
        return cls(
            subject=data['subject'],
            body=data['body'],
            category=data['category'],
            priority=data.get('priority'),
            metadata=data.get('metadata', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'subject': self.subject,
            'body': self.body,
            'category': self.category,
            'priority': self.priority,
            'metadata': self.metadata
        }
    
    def get_text(self) -> str:
        """Get combined text for analysis."""
        return f"{self.subject} {self.body}"

# Email categories and their descriptions
EMAIL_CATEGORIES = {
    "inquiry": "General information requests, product questions",
    "support": "Technical support, troubleshooting, help requests",
    "feedback": "Product feedback, suggestions, reviews",
    "complaint": "Issues, problems, dissatisfaction",
    "sales": "Purchasing, pricing, quotes, licensing",
    "partnership": "Business partnerships, collaborations, integrations",
    "legal": "Legal inquiries, compliance, data requests"
}

# Templates for generating synthetic emails
EMAIL_TEMPLATES = {
    "inquiry": [
        {
            "subject": "Question about {product}",
            "body": "Hello,\n\nI'm interested in {product} and would like to know {inquiry_type}. Can you provide me with more information?\n\nThanks,\n{name}"
        },
        {
            "subject": "Information about {product} {feature}",
            "body": "Hi there,\n\nCould you tell me more about the {feature} in {product}? I'm specifically wondering {inquiry_detail}.\n\nBest regards,\n{name}\n{position}\n{company}"
        },
        {
            "subject": "Does {product} support {technology}?",
            "body": "Hello Support,\n\nWe're evaluating {product} for our company and need to know if it supports {technology}. This is important for our {use_case}.\n\nRegards,\n{name}"
        }
    ],
    
    "support": [
        {
            "subject": "{product} {issue_type} issue",
            "body": "Hi,\n\nI'm having a problem with {product}. When I try to {action}, I get {error}. This started happening after {trigger}.\n\nCan you help me resolve this?\n\n{name}"
        },
        {
            "subject": "Urgent: {product} not working",
            "body": "Support Team,\n\nWe have an urgent issue with {product}. It's {issue_description} and we need this fixed as soon as possible since it's affecting our {impact}.\n\nPlease help,\n{name}\n{position}\n{company}"
        },
        {
            "subject": "Help with {feature} configuration",
            "body": "Hello,\n\nI need assistance configuring the {feature} in {product}. I've tried {attempted_solution} but it's not working correctly.\n\nThanks,\n{name}"
        }
    ],
    
    "feedback": [
        {
            "subject": "Feedback on {product}",
            "body": "Hello,\n\nI've been using {product} for {time_period} and wanted to share some feedback. I {feedback_sentiment} the {feature} because {reason}.\n\nRegards,\n{name}"
        },
        {
            "subject": "Suggestion for {product}",
            "body": "Hi team,\n\nI have a suggestion for {product}. It would be great if you could add {suggested_feature}. This would help with {benefit}.\n\nBest,\n{name}"
        },
        {
            "subject": "{product} user experience feedback",
            "body": "To whom it may concern,\n\nI wanted to provide feedback about my experience with {product}. Overall, it's been {feedback_rating}. The {positive_aspect} is excellent, but the {negative_aspect} could use improvement.\n\nRegards,\n{name}\n{company}"
        }
    ],
    
    "complaint": [
        {
            "subject": "Frustrated with {product} {issue_type}",
            "body": "Hello,\n\nI'm very disappointed with {product}. The {issue_type} is {issue_description} and it's causing significant problems for our team. This has been ongoing for {time_period} despite multiple attempts to resolve it.\n\nI expect a solution soon,\n{name}"
        },
        {
            "subject": "Complaint about {product} reliability",
            "body": "Support,\n\nI need to file a complaint about {product}. We've experienced {issue_count} outages this month alone, which is unacceptable for a product at this price point. Our {impact} has been severely affected.\n\n{name}\n{position}\n{company}"
        },
        {
            "subject": "{product} not meeting expectations",
            "body": "To the support team,\n\nWe purchased {product} {time_period} ago, and it's not meeting our expectations. Specifically, the {feature} is {issue_description} and we're considering {alternative_action} if this isn't addressed soon.\n\n{name}"
        }
    ],
    
    "sales": [
        {
            "subject": "Interested in purchasing {product}",
            "body": "Hello Sales Team,\n\nI'm interested in purchasing {product} for our organization. Could you provide information about {pricing_inquiry}?\n\nThanks,\n{name}\n{position}\n{company}"
        },
        {
            "subject": "{product} license renewal",
            "body": "Hi,\n\nOur {product} license is expiring on {date}. We'd like to renew for {time_period} for {user_count} users. Could you send us a quote?\n\nBest regards,\n{name}"
        },
        {
            "subject": "Quote request for {product}",
            "body": "Hello,\n\nWe're looking to implement {product} across our {department}. Can you provide a quote for {user_count} users with {feature_requirements}?\n\nThank you,\n{name}\n{company}"
        }
    ],
    
    "partnership": [
        {
            "subject": "Partnership opportunity with {company}",
            "body": "Hello,\n\nI'm reaching out from {company} to explore partnership opportunities with your team. We specialize in {specialty} and believe there's potential for {partnership_type} with your {product}.\n\nWould you be interested in discussing this further?\n\n{name}\n{position}\n{company}"
        },
        {
            "subject": "Integration between {product} and our solution",
            "body": "Hi,\n\nWe're developing a {solution_type} and would like to integrate with {product}. Our customers have been asking for this integration, and we believe it would benefit both our companies.\n\nCan we schedule a call to discuss?\n\n{name}\n{position}\n{company}"
        },
        {
            "subject": "Reseller inquiry for {product}",
            "body": "To whom it may concern,\n\nWe're interested in becoming a reseller for {product} in the {region} market. Our company has {experience} years of experience in {industry} and a strong customer base that would benefit from your solution.\n\nLooking forward to your response,\n{name}\n{company}"
        }
    ],
    
    "legal": [
        {
            "subject": "Data deletion request",
            "body": "Hello Legal Team,\n\nI'm writing to request the deletion of all my personal data in accordance with {regulation}. My account is registered under {email}.\n\nPlease confirm when this has been completed.\n\n{name}"
        },
        {
            "subject": "Compliance question regarding {product}",
            "body": "Legal Department,\n\nOur organization needs to confirm that {product} is compliant with {regulation} before we can proceed with implementation. Can you provide documentation certifying compliance?\n\nThank you,\n{name}\n{position}\n{company}"
        },
        {
            "subject": "Terms of Service clarification",
            "body": "Hello,\n\nI have a question about your Terms of Service. Section {section} states {terms_content}, but I'm unsure how this applies to our {use_case}. Could you please clarify?\n\nRegards,\n{name}\n{company}"
        }
    ]
}

# Variables for template substitution
EMAIL_VARIABLES = {
    "product": ["ARP Guard", "Network Shield", "Perimeter Defender", "Access Manager", "Guard Console", "Security Monitor"],
    "feature": ["dashboard", "reporting", "notifications", "alerts", "integration", "API", "monitoring", "settings", "user management", "authentication", "password reset", "network scanning", "threat detection", "vulnerability assessment", "email notifications", "mobile app"],
    "name": ["John Smith", "Emma Johnson", "Michael Chen", "Sarah Williams", "David Rodriguez", "Maria Garcia", "James Wilson", "Lisa Brown", "Robert Taylor", "Jennifer Anderson"],
    "position": ["IT Manager", "Security Engineer", "Network Administrator", "CTO", "IT Director", "Systems Engineer", "DevOps Engineer", "CISO", "Security Analyst", "IT Specialist"],
    "company": ["Acme Corporation", "TechSolutions Inc", "GlobalSecure", "DataSafe Systems", "InfoTech Industries", "SecureNet", "CyberDefense LLC", "EnterpriseIT", "NetGuard Solutions", "TrustedSystems"],
    "inquiry_type": ["more about its features", "about pricing options", "if it's compatible with our systems", "how it compares to competitors", "about implementation requirements", "about the onboarding process"],
    "inquiry_detail": ["how to configure it", "if it integrates with our existing tools", "what the system requirements are", "if it supports multiple users", "what the licensing model is"],
    "technology": ["Windows", "Mac", "Linux", "cloud", "API", "REST", "SOAP", "Docker", "Kubernetes", "OAuth", "SAML", "SSO", "2FA", "biometrics", "LDAP", "Active Directory"],
    "use_case": ["security monitoring", "compliance requirements", "network management", "access control", "threat detection", "vulnerability scanning"],
    "issue_type": ["installation", "configuration", "connection", "performance", "activation", "login", "update", "synchronization"],
    "issue_description": ["not working", "crashing frequently", "extremely slow", "showing error messages", "not connecting properly", "failing to start", "losing data", "inconsistent", "unreliable"],
    "error": ["an error message", "error code 404", "a connection timeout", "authentication failure", "a permission denied message", "unexpected behavior", "a crash", "a critical error", "a blue screen"],
    "trigger": ["a recent update", "installation", "changing settings", "restarting the system", "connecting to our network", "integrating with another tool"],
    "impact": ["business operations", "production environment", "security monitoring", "client services", "internal systems", "data collection"],
    "attempted_solution": ["restarting the system", "reinstalling the software", "clearing the cache", "updating drivers", "consulting the documentation", "contacting our IT team"],
    "time_period": ["2 weeks", "a month", "3 months", "6 months", "a year", "several years"],
    "feedback_sentiment": ["really like", "appreciate", "am impressed by", "am disappointed with", "find issues with", "am confused by"],
    "reason": ["it saves us time", "it's intuitive to use", "it's improved our security", "it's too complicated", "it lacks important features", "it's unreliable"],
    "suggested_feature": ["a mobile app", "better reporting", "more customization options", "integration with other tools", "stronger authentication", "an API"],
    "benefit": ["our workflow efficiency", "security monitoring", "compliance reporting", "user experience", "system management"],
    "feedback_rating": ["excellent", "very good", "satisfactory", "mixed", "disappointing", "frustrating"],
    "positive_aspect": ["user interface", "performance", "reliability", "feature set", "support", "documentation"],
    "negative_aspect": ["setup process", "learning curve", "error handling", "performance", "compatibility", "user interface"],
    "issue_count": ["3", "5", "7", "10", "numerous", "several"],
    "alternative_action": ["switching to a competitor", "requesting a refund", "downgrading our plan", "not renewing our contract", "deploying an alternative solution"],
    "pricing_inquiry": ["pricing for 25 users", "different license tiers", "enterprise pricing", "volume discounts", "educational pricing", "non-profit discounts"],
    "date": ["January 15", "March 31", "June 30", "September 1", "October 15", "December 31"],
    "user_count": ["10", "25", "50", "100", "250", "500", "1000"],
    "feature_requirements": ["advanced security features", "administrator access", "API integration", "custom reporting", "mobile access", "premium support"],
    "department": ["IT department", "security team", "marketing department", "development team", "entire organization", "regional office"],
    "specialty": ["cybersecurity", "network infrastructure", "cloud services", "managed IT services", "software development", "system integration"],
    "partnership_type": ["a technical integration", "a reseller agreement", "a co-marketing initiative", "a joint solution", "a referral program"],
    "solution_type": ["security platform", "management console", "monitoring tool", "compliance solution", "mobile application", "cloud service"],
    "region": ["North American", "European", "Asia-Pacific", "Latin American", "global", "SMB"],
    "experience": ["5", "10", "15", "20", "25"],
    "industry": ["cybersecurity", "IT services", "healthcare", "financial services", "education", "government"],
    "regulation": ["GDPR", "CCPA", "HIPAA", "SOC 2", "ISO 27001", "PCI DSS"],
    "email": ["john.smith@example.com", "emma.johnson@example.org", "michael.chen@example.net", "sarah.williams@example.com", "david.rodriguez@example.org"],
    "section": ["3.2", "4.5", "6.1", "7.3", "9.2", "12.4"],
    "terms_content": ["usage limitations", "data processing terms", "liability limitations", "user responsibilities", "service level agreements", "intellectual property rights"]
}

def generate_email(category: str) -> EmailExample:
    """
    Generate a synthetic email for a given category.
    
    Args:
        category: Email category
        
    Returns:
        EmailExample object
    """
    # Select random template for the category
    template = random.choice(EMAIL_TEMPLATES[category])
    
    # Initialize subject and body
    subject = template["subject"]
    body = template["body"]
    
    # Replace variables in subject and body
    for var_name in EMAIL_VARIABLES:
        if "{" + var_name + "}" in subject:
            value = random.choice(EMAIL_VARIABLES[var_name])
            subject = subject.replace("{" + var_name + "}", value)
        
        if "{" + var_name + "}" in body:
            value = random.choice(EMAIL_VARIABLES[var_name])
            body = body.replace("{" + var_name + "}", value)
    
    # Determine priority based on content and category
    priority = None
    if "urgent" in subject.lower() or "urgent" in body.lower():
        priority = "high"
    elif category in ["complaint", "support"] and ("critical" in body.lower() or "important" in body.lower()):
        priority = "high"
    elif category in ["feedback", "partnership", "inquiry"]:
        priority = "medium"
    else:
        priority = random.choice(["high", "medium", "low"])
    
    # Create metadata
    metadata = {}
    for product in EMAIL_VARIABLES["product"]:
        if product in subject or product in body:
            metadata["product"] = product
            break
    
    for company in EMAIL_VARIABLES["company"]:
        if company in body:
            metadata["company"] = company
            break
    
    # Create EmailExample
    example = EmailExample(
        subject=subject,
        body=body,
        category=category,
        priority=priority,
        metadata=metadata
    )
    
    return example

def generate_email_examples(count_per_category: int) -> List[EmailExample]:
    """
    Generate synthetic email examples.
    
    Args:
        count_per_category: Number of examples per category
        
    Returns:
        List of EmailExample objects
    """
    examples = []
    
    for category in EMAIL_CATEGORIES:
        for _ in range(count_per_category):
            example = generate_email(category)
            examples.append(example)
    
    # Shuffle examples
    random.shuffle(examples)
    
    logger.info(f"Generated {len(examples)} synthetic email examples")
    return examples

def save_examples(examples: List[EmailExample], file_path: str):
    """
    Save examples to a JSON file.
    
    Args:
        examples: List of example objects
        file_path: Path to save the file
    """
    data = [example.to_dict() for example in examples]
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(examples)} examples to {file_path}")

def train_email_model(examples: List[EmailExample], test_size: float = 0.2,
                     grid_search: bool = True) -> Dict[str, Any]:
    """
    Train an email categorization model.
    
    Args:
        examples: List of training examples
        test_size: Proportion of data to use for testing
        grid_search: Whether to perform hyperparameter tuning
        
    Returns:
        Dictionary with training results and the trained model
    """
    # Extract texts and categories
    texts = [example.get_text() for example in examples]
    categories = [example.category for example in examples]
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        texts, categories, test_size=test_size, random_state=42, stratify=categories
    )
    
    # Create vectorizer
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=15000,
        min_df=2
    )
    
    # Create classifier
    classifier = RandomForestClassifier(
        n_estimators=200,
        class_weight='balanced',
        random_state=42
    )
    
    # Create pipeline
    pipeline = Pipeline([
        ('vectorizer', vectorizer),
        ('classifier', classifier)
    ])
    
    # Perform grid search if requested
    if grid_search and len(examples) > 50:
        logger.info("Performing grid search for email categorization model")
        
        param_grid = {
            'vectorizer__max_features': [10000, 15000, 20000],
            'vectorizer__ngram_range': [(1, 2), (1, 3)],
            'classifier__n_estimators': [100, 200, 300]
        }
        
        search = GridSearchCV(
            pipeline, param_grid, cv=3, scoring='f1_weighted', verbose=1, n_jobs=-1
        )
        search.fit(X_train, y_train)
        
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
        true_category = y_test[idx]
        pred_category = y_pred[idx]
        sample_predictions.append({
            "text": sample_text[:100] + "...",  # Truncate for display
            "true": true_category,
            "predicted": pred_category
        })
    
    logger.info(f"Email categorization model training complete. Accuracy: {accuracy:.2f}, F1: {f1:.2f}")
    
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

def main():
    parser = argparse.ArgumentParser(description='Train email categorization model')
    parser.add_argument('--data', type=str, help='Path to training data file')
    parser.add_argument('--generate', type=int, default=30, help='Number of examples per category')
    parser.add_argument('--output', type=str, help='Path to save the model')
    parser.add_argument('--save-examples', type=str, help='Path to save generated examples')
    parser.add_argument('--no-grid-search', action='store_true', help='Disable grid search')
    args = parser.parse_args()
    
    # Generate synthetic examples
    examples = generate_email_examples(args.generate)
    
    # Save examples if requested
    if args.save_examples:
        save_examples(examples, args.save_examples)
    
    # Train model
    results = train_email_model(examples, grid_search=not args.no_grid_search)
    
    # Save model
    save_path = args.output if args.output else EMAIL_CATEGORIZATION_MODEL_PATH
    try:
        save_model(results["model"], save_path)
        logger.info(f"Saved email categorization model to {save_path}")
        
        # Print results
        print("\nEmail Categorization Model Training Results:")
        print(f"Examples Count: {results['examples_count']}")
        print(f"Accuracy: {results['accuracy']:.4f}")
        print(f"F1 Score: {results['f1_score']:.4f}")
        
        # Print sample predictions
        print("\nSample Predictions:")
        for i, sample in enumerate(results['sample_predictions']):
            print(f"  Example {i+1}: '{sample['text']}'")
            print(f"  True: {sample['true']}")
            print(f"  Predicted: {sample['predicted']}")
            print("")
        
        # Print category distribution
        category_counts = {}
        for ex in examples:
            category = ex.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        print("\nCategory Distribution:")
        for category, count in category_counts.items():
            print(f"  {category}: {count} examples")
        
    except Exception as e:
        logger.error(f"Error saving model: {e}")

if __name__ == "__main__":
    main() 