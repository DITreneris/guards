"""
Test script for the Guards & Robbers Communication Bot

This script tests various scenarios and interactions with the communication bot,
including different message types, intents, and response quality.

Version: 1.0.0
Created: May 16, 2025
"""

import sys
import json
from datetime import datetime
from communication_bot import CommunicationBot, Message, Response

def test_greeting():
    """Test greeting message handling"""
    print("\n=== Testing Greeting Message ===")
    message = Message(
        content="Hello! I'm interested in your security services",
        sender="test@example.com",
        channel="email"
    )
    response = bot.process_message(message)
    print(f"Input: {message.content}")
    print(f"Response: {response.content}")
    print(f"Confidence: {response.confidence:.2f}")
    print(f"Requires Review: {response.requires_human_review}")

def test_pricing_inquiry():
    """Test pricing inquiry handling"""
    print("\n=== Testing Pricing Inquiry ===")
    message = Message(
        content="What are your pricing options for security services?",
        sender="test@example.com",
        channel="email"
    )
    response = bot.process_message(message)
    print(f"Input: {message.content}")
    print(f"Response: {response.content}")
    print(f"Confidence: {response.confidence:.2f}")
    print(f"Requires Review: {response.requires_human_review}")

def test_support_request():
    """Test support request handling"""
    print("\n=== Testing Support Request ===")
    message = Message(
        content="I'm having issues with my account access. Can you help?",
        sender="test@example.com",
        channel="email"
    )
    response = bot.process_message(message)
    print(f"Input: {message.content}")
    print(f"Response: {response.content}")
    print(f"Confidence: {response.confidence:.2f}")
    print(f"Requires Review: {response.requires_human_review}")

def test_feature_inquiry():
    """Test feature inquiry handling"""
    print("\n=== Testing Feature Inquiry ===")
    message = Message(
        content="Does your security system include real-time monitoring?",
        sender="test@example.com",
        channel="email"
    )
    response = bot.process_message(message)
    print(f"Input: {message.content}")
    print(f"Response: {response.content}")
    print(f"Confidence: {response.confidence:.2f}")
    print(f"Requires Review: {response.requires_human_review}")

def test_scheduling():
    """Test scheduling request handling"""
    print("\n=== Testing Scheduling Request ===")
    message = Message(
        content="I'd like to schedule a demo of your security system",
        sender="test@example.com",
        channel="email"
    )
    response = bot.process_message(message)
    print(f"Input: {message.content}")
    print(f"Response: {response.content}")
    print(f"Confidence: {response.confidence:.2f}")
    print(f"Requires Review: {response.requires_human_review}")

def test_conversation_history():
    """Test conversation history tracking"""
    print("\n=== Testing Conversation History ===")
    sender = "test@example.com"
    
    # Send multiple messages
    messages = [
        "Hello, I'm interested in your services",
        "What are your pricing options?",
        "Can you tell me more about your monitoring features?"
    ]
    
    for msg in messages:
        message = Message(
            content=msg,
            sender=sender,
            channel="email"
        )
        response = bot.process_message(message)
        print(f"\nMessage: {msg}")
        print(f"Response: {response.content}")
    
    # Get conversation history
    history = bot.get_conversation_history(sender)
    print("\nConversation History:")
    for entry in history:
        print(f"Time: {entry['timestamp']}")
        print(f"Message: {entry['message']}")
        print(f"Response: {entry['response']}")
        print(f"Intent: {entry['intent']}")
        print(f"Confidence: {entry['confidence']:.2f}")
        print("---")

def test_unknown_intent():
    """Test handling of unknown or unclear intents"""
    print("\n=== Testing Unknown Intent ===")
    message = Message(
        content="This is a random message that doesn't fit any category",
        sender="test@example.com",
        channel="email"
    )
    response = bot.process_message(message)
    print(f"Input: {message.content}")
    print(f"Response: {response.content}")
    print(f"Confidence: {response.confidence:.2f}")
    print(f"Requires Review: {response.requires_human_review}")

def run_all_tests():
    """Run all test scenarios"""
    print("Starting Communication Bot Tests...")
    print("=" * 50)
    
    test_greeting()
    test_pricing_inquiry()
    test_support_request()
    test_feature_inquiry()
    test_scheduling()
    test_conversation_history()
    test_unknown_intent()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    # Initialize the bot
    bot = CommunicationBot()
    
    # Run all tests
    run_all_tests() 