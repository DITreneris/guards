#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ML Sales Demo

A compact demo that showcases the commercial capabilities 
of the Guards & Robbers ML Framework.
"""

import os
import time
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def demo_intent_recognition():
    """Demonstrate intent recognition capabilities"""
    print("\n=== Intent Recognition Demo ===\n")
    
    # Sample customer messages
    messages = [
        "I need help setting up my firewall",
        "What's the price for the enterprise plan?",
        "My network is under attack, help!",
        "How do I configure the ARP Guard feature?",
        "I'd like to upgrade my subscription"
    ]
    
    print("Processing customer inquiries with our intent recognition engine...\n")
    time.sleep(1)
    
    # Simulate intent recognition
    for i, message in enumerate(messages):
        print(f"Customer: \"{message}\"")
        time.sleep(0.5)
        
        # Simulate processing
        print("Processing", end="")
        for _ in range(3):
            print(".", end="", flush=True)
            time.sleep(0.2)
        print()
        
        # Determine intent based on message content
        if "help" in message.lower() or "setting" in message.lower() or "configure" in message.lower():
            intent = "support_request"
            confidence = 0.92
        elif "price" in message.lower() or "upgrade" in message.lower() or "subscription" in message.lower():
            intent = "sales_inquiry"
            confidence = 0.88
        elif "attack" in message.lower():
            intent = "emergency"
            confidence = 0.98
        else:
            intent = "general_inquiry"
            confidence = 0.75
        
        # Display results
        print(f"Intent: {intent} (confidence: {confidence:.2f})")
        print(f"Response: {get_intent_response(intent)}\n")
    
    print("Our intent recognition system automatically categorizes customer inquiries")
    print("and routes them to the appropriate team or automated response system.")
    print("This ensures faster response times and higher customer satisfaction.")

def get_intent_response(intent):
    """Get a sample response for an intent"""
    responses = {
        "support_request": "I'd be happy to help you with that! Let me connect you with our support team.",
        "sales_inquiry": "Thank you for your interest! Our sales team will provide you with pricing details.",
        "emergency": "We understand this is urgent. Activating emergency response protocol.",
        "general_inquiry": "Thanks for reaching out. Let me find the right information for you."
    }
    return responses.get(intent, "I'll help you with that request.")

def demo_sentiment_analysis():
    """Demonstrate sentiment analysis capabilities"""
    print("\n=== Sentiment Analysis Demo ===\n")
    
    # Sample customer feedback
    feedback = [
        "I'm extremely satisfied with your product, it works flawlessly!",
        "The response time could be better, but overall it's okay",
        "Your support team is terrible. I've been waiting for days with no response!",
        "I'm considering switching to a different provider due to reliability issues",
        "Thank you for the quick fix, my problem was resolved immediately"
    ]
    
    print("Analyzing customer feedback with our sentiment analysis engine...\n")
    time.sleep(1)
    
    # Simulate sentiment analysis
    for i, text in enumerate(feedback):
        print(f"Customer Feedback: \"{text}\"")
        
        # Simulate processing
        print("Analyzing", end="")
        for _ in range(3):
            print(".", end="", flush=True)
            time.sleep(0.2)
        print()
        
        # Determine sentiment based on content
        if any(word in text.lower() for word in ["satisfied", "flawlessly", "thank", "quick", "great"]):
            sentiment = "positive"
            score = 0.8 + (0.2 * (i % 2))  # Vary the score slightly
        elif any(word in text.lower() for word in ["terrible", "switching", "reliability issues"]):
            sentiment = "negative"
            score = 0.7 + (0.2 * (i % 2))
        else:
            sentiment = "neutral"
            score = 0.6 + (0.2 * (i % 2))
        
        # Display results
        print(f"Sentiment: {sentiment} (score: {score:.2f})")
        print(f"Action: {get_sentiment_action(sentiment)}\n")
    
    print("Our sentiment analysis system automatically evaluates customer feedback")
    print("and triggers appropriate response workflows based on sentiment.")
    print("This allows you to address negative feedback quickly and capitalize on positive sentiment.")

def get_sentiment_action(sentiment):
    """Get a sample action for a sentiment"""
    actions = {
        "positive": "Flag for testimonial opportunity and customer loyalty program",
        "neutral": "Standard follow-up with satisfaction survey",
        "negative": "Escalate to customer success team for immediate attention"
    }
    return actions.get(sentiment, "Standard follow-up")

def demo_email_categorization():
    """Demonstrate email categorization capabilities"""
    print("\n=== Email Categorization Demo ===\n")
    
    # Sample emails
    emails = [
        {
            "subject": "Urgent: Security Breach Detected",
            "body": "Our system detected unusual traffic on port 443. We believe we're under a DDoS attack. Need immediate assistance."
        },
        {
            "subject": "Question about Enterprise Pricing",
            "body": "I'm interested in deploying ARP Guard across our organization of 500 employees. Could you provide details about enterprise pricing?"
        },
        {
            "subject": "Feature Request: Improved Reporting",
            "body": "The dashboard analytics are great, but we'd love to see more granular reporting options for network traffic patterns."
        },
        {
            "subject": "License renewal help",
            "body": "My license key ABC-123-XYZ expires next week. I need help with the renewal process. Is there an automatic renewal option?"
        },
        {
            "subject": "Thank you for the quick resolution",
            "body": "Just wanted to say thanks to your support team for resolving our firewall configuration issue so quickly. Great service!"
        }
    ]
    
    print("Processing incoming emails with our categorization engine...\n")
    time.sleep(1)
    
    # Simulate email categorization
    for i, email in enumerate(emails):
        print(f"Subject: \"{email['subject']}\"")
        print(f"Body: \"{email['body'][:100]}{'...' if len(email['body']) > 100 else ''}\"")
        
        # Simulate processing
        print("Categorizing", end="")
        for _ in range(3):
            print(".", end="", flush=True)
            time.sleep(0.2)
        print()
        
        # Extract entities and determine category
        entities = extract_entities(email['subject'] + " " + email['body'])
        
        # Determine category based on content
        if "attack" in email['body'].lower() or "breach" in email['subject'].lower() or "urgent" in email['subject'].lower():
            category = "emergency"
            priority = "high"
        elif "pricing" in email['body'].lower() or "quote" in email['body'].lower() or "cost" in email['body'].lower():
            category = "sales"
            priority = "medium"
        elif "feature" in email['subject'].lower() or "request" in email['subject'].lower():
            category = "product_feedback"
            priority = "low"
        elif "license" in email['body'].lower() or "renewal" in email['body'].lower():
            category = "support"
            priority = "medium"
        elif "thank" in email['body'].lower() or "great" in email['body'].lower():
            category = "feedback"
            priority = "low"
        else:
            category = "general"
            priority = "medium"
        
        # Display results
        print(f"Category: {category} (Priority: {priority})")
        print(f"Detected Entities: {', '.join(entities)}")
        print(f"Action: {get_email_action(category, priority)}\n")
    
    print("Our email categorization system automatically classifies incoming emails,")
    print("extracts key entities, and determines priority levels.")
    print("This ensures that urgent matters receive immediate attention")
    print("and all communications are routed to the appropriate teams.")

def extract_entities(text):
    """Extract sample entities from text"""
    entities = []
    
    # Very simple entity extraction simulation
    if "port" in text.lower():
        entities.append("Port: 443")
    
    if "attack" in text.lower() or "breach" in text.lower():
        entities.append("Threat: DDoS")
    
    if "enterprise" in text.lower():
        entities.append("Customer Segment: Enterprise")
    
    if any(word in text.lower() for word in ["pricing", "cost", "price"]):
        entities.append("Intent: Purchase")
    
    if "license" in text.lower():
        entities.append("Product: License")
        if "ABC-123-XYZ" in text:
            entities.append("License Key: ABC-123-XYZ")
    
    if "firewall" in text.lower():
        entities.append("Product: Firewall")
    
    if "500 employees" in text.lower():
        entities.append("Organization Size: 500")
    
    # Ensure we have at least one entity
    if not entities:
        entities.append("General Inquiry")
    
    return entities

def get_email_action(category, priority):
    """Get a sample action for an email category"""
    actions = {
        "emergency": "Route to security response team for immediate action",
        "sales": "Forward to sales team with lead scoring information",
        "product_feedback": "Log in product management system and send acknowledgment",
        "support": "Create support ticket and route to customer success team",
        "feedback": "Log positive feedback and send thank-you response",
        "general": "Analyze further and route to appropriate department"
    }
    
    base_action = actions.get(category, "Standard processing")
    
    if priority == "high":
        return f"{base_action} with HIGH priority flag"
    elif priority == "medium":
        return base_action
    else:
        return f"{base_action} (scheduled processing)"

def demo_usage_metrics():
    """Demonstrate usage metrics and billing capabilities"""
    print("\n=== Usage Metrics & Billing Demo ===\n")
    
    # Import the usage metering (with fallback if not available)
    try:
        from ml_usage_metering import UsageMeter, UsageMetric
        meter_available = True
    except ImportError:
        meter_available = False
    
    client_id = "demo_client_123"
    
    if meter_available:
        # Create a meter instance
        meter = UsageMeter()
        
        # Record some sample usage
        print("Recording sample usage data for demonstration...\n")
        
        # API calls
        for i in range(50):
            meter.record_usage(
                client_id=client_id,
                metric_type=UsageMetric.API_CALL,
                metadata={
                    "endpoint": f"/api/{'predict' if i % 3 == 0 else 'analyze' if i % 3 == 1 else 'extract'}",
                    "method": "POST"
                }
            )
        
        # Model inferences
        for i in range(30):
            meter.record_usage(
                client_id=client_id,
                metric_type=UsageMetric.MODEL_INFERENCE,
                metadata={
                    "model": f"{'intent' if i % 3 == 0 else 'sentiment' if i % 3 == 1 else 'entity'}_model",
                    "latency_ms": 50 + (i % 10)
                }
            )
        
        # Data storage
        meter.record_usage(
            client_id=client_id,
            metric_type=UsageMetric.DATA_STORAGE,
            value=512.5,  # MB
            metadata={
                "data_type": "customer_data"
            }
        )
        
        # Generate usage report
        print(f"Usage Report for {client_id}:\n")
        summary = meter.get_usage_summary(client_id)
        
        for metric_type, value in summary.items():
            print(f"  {metric_type}: {value:.2f}")
        
        # Calculate billing for different tiers
        print("\nBilling Estimates:\n")
        
        for tier in ["basic", "professional", "enterprise"]:
            try:
                billing = meter.calculate_billing(
                    client_id=client_id,
                    tier=tier
                )
                
                print(f"{tier.capitalize()} Tier:")
                print(f"  Base Price: ${billing['base_price']:.2f}")
                
                if billing['overage_charges']:
                    print(f"  Overage Charges:")
                    for charge_type, amount in billing['overage_charges'].items():
                        print(f"    {charge_type}: ${amount:.2f}")
                
                print(f"  Total: ${billing['total_price']:.2f}")
                print()
            except Exception as e:
                logger.error(f"Error calculating billing for {tier} tier: {str(e)}")
                print(f"{tier.capitalize()} Tier: Error calculating billing - {str(e)}")
                print()
    else:
        # Simulate metrics if module not available
        print("Simulating usage metrics (ml_usage_metering module not available)\n")
        
        print(f"Usage Report for {client_id}:\n")
        print("  api_call: 50.00")
        print("  model_inference: 30.00")
        print("  data_storage: 512.50")
        
        print("\nBilling Estimates:\n")
        
        print("Basic Tier:")
        print("  Base Price: $99.99")
        print("  Total: $99.99")
        print()
        
        print("Professional Tier:")
        print("  Base Price: $299.99")
        print("  Total: $299.99")
        print()
        
        print("Enterprise Tier:")
        print("  Base Price: $999.99")
        print("  Total: $999.99")
        print()
    
    print("Our usage-based billing system accurately tracks all API calls,")
    print("model inferences, and data storage to provide transparent pricing.")
    print("Customers only pay for what they use, with tiered pricing plans")
    print("that offer increasing capabilities and volume discounts.")

def demo_model_monitoring():
    """Demonstrate model monitoring capabilities"""
    print("\n=== Model Monitoring Demo ===\n")
    
    # Import the model monitoring (with fallback if not available)
    try:
        from ml_monitoring import ModelMonitor, create_default_monitor
        monitor_available = True
    except ImportError:
        monitor_available = False
    
    if monitor_available:
        # Create a monitor instance
        monitor = create_default_monitor()
        
        # Record some sample predictions
        print("Recording sample predictions for demonstration...\n")
        
        # Add predictions for intent model
        for i in range(50):
            # Vary the latency and confidence to create some interesting patterns
            latency = 20 + (i % 5) * 10
            confidence = 0.7 + (i % 3) * 0.1
            
            # Every 10th prediction is slower
            if i % 10 == 0:
                latency = 150
            
            monitor.track_prediction(
                model_id="intent_recognition_model",
                input_data=f"input_{i}",
                prediction="support" if i % 3 == 0 else "sales" if i % 3 == 1 else "general",
                confidence=confidence,
                latency_ms=latency
            )
        
        # Add ground truth for some predictions
        for i in range(0, 50, 4):
            # Make some predictions correct, some incorrect
            correct = i % 8 != 0
            ground_truth = "support" if i % 3 == 0 else "sales" if i % 3 == 1 else "general"
            
            # For incorrect ones, provide a different ground truth
            if not correct:
                if ground_truth == "support":
                    ground_truth = "sales"
                else:
                    ground_truth = "support"
            
            monitor.record_ground_truth(
                model_id="intent_recognition_model",
                input_data=f"input_{i}",
                ground_truth=ground_truth
            )
        
        # Get health report
        print("Model Health Report:\n")
        health = monitor.get_model_health("intent_recognition_model")
        
        print(f"Model: intent_recognition_model")
        print(f"Status: {health['status']}")
        print(f"Message: {health['message']}")
        print(f"Metrics:")
        
        metrics = health['metrics']
        for key, value in metrics.items():
            if key not in ['model_id', 'last_updated']:
                if isinstance(value, float):
                    print(f"  {key}: {value:.2f}")
                else:
                    print(f"  {key}: {value}")
    else:
        # Simulate metrics if module not available
        print("Simulating model monitoring (ml_monitoring module not available)\n")
        
        print("Model Health Report:\n")
        print("Model: intent_recognition_model")
        print("Status: healthy")
        print("Message: All metrics within acceptable thresholds")
        print("Metrics:")
        print("  accuracy: 0.87")
        print("  latency_avg_ms: 38.25")
        print("  latency_p95_ms: 120.00")
        print("  latency_p99_ms: 145.00")
        print("  throughput_per_minute: 15.00")
        print("  error_rate: 0.02")
        print("  prediction_count: 50")
    
    print("\nOur model monitoring system continuously tracks model performance,")
    print("detecting issues before they impact your customers.")
    print("Automatic alerts notify you of accuracy degradation, latency spikes,")
    print("or other anomalies, ensuring optimal system performance at all times.")

def run_full_demo():
    """Run the full sales demo"""
    print("\n" + "=" * 80)
    print("GUARDS & ROBBERS ML FRAMEWORK - COMMERCIAL DEMO".center(80))
    print("=" * 80 + "\n")
    
    print("Welcome to the Guards & Robbers ML Framework commercial demo!")
    print("This demonstration will showcase our key ML capabilities:")
    print("  1. Intent Recognition")
    print("  2. Sentiment Analysis")
    print("  3. Email Categorization")
    print("  4. Usage Metrics & Billing")
    print("  5. Model Monitoring\n")
    
    input("Press Enter to begin the demo...")
    
    # Run each demo
    demo_intent_recognition()
    input("\nPress Enter to continue to Sentiment Analysis...")
    
    demo_sentiment_analysis()
    input("\nPress Enter to continue to Email Categorization...")
    
    demo_email_categorization()
    input("\nPress Enter to continue to Usage Metrics & Billing...")
    
    demo_usage_metrics()
    input("\nPress Enter to continue to Model Monitoring...")
    
    demo_model_monitoring()
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE".center(80))
    print("=" * 80 + "\n")
    
    print("Thank you for experiencing the Guards & Robbers ML Framework!")
    print("Our sales team is ready to discuss how these capabilities")
    print("can be customized to meet your specific security and customer engagement needs.")
    print("\nFor more information or to start your free trial, contact sales@guardsrobbers.com")

def main():
    """Main function for the sales demo"""
    parser = argparse.ArgumentParser(description="Guards & Robbers ML Framework Sales Demo")
    parser.add_argument('--intent', action='store_true', help='Demo intent recognition only')
    parser.add_argument('--sentiment', action='store_true', help='Demo sentiment analysis only')
    parser.add_argument('--email', action='store_true', help='Demo email categorization only')
    parser.add_argument('--usage', action='store_true', help='Demo usage metrics only')
    parser.add_argument('--monitoring', action='store_true', help='Demo model monitoring only')
    args = parser.parse_args()
    
    # Check if specific demos were requested
    specific_demos = any([
        args.intent, args.sentiment, args.email, 
        args.usage, args.monitoring
    ])
    
    if not specific_demos:
        # Run the full demo by default
        run_full_demo()
    else:
        # Run specific demos
        if args.intent:
            demo_intent_recognition()
        
        if args.sentiment:
            demo_sentiment_analysis()
        
        if args.email:
            demo_email_categorization()
        
        if args.usage:
            demo_usage_metrics()
        
        if args.monitoring:
            demo_model_monitoring()

if __name__ == "__main__":
    main() 