#!/usr/bin/env python3
"""
API Key Management Utility for Guards & Robbers

This script provides commands to:
- Create new API keys
- List existing API keys
- Revoke API keys
- Update API key roles and rate limits
"""

import os
import sys
import json
import argparse
from datetime import datetime
from security_contract import create_api_key, revoke_api_key, load_api_keys, API_KEYS, save_api_keys

def list_keys():
    """List all API keys"""
    print("API Keys:")
    print("-" * 80)
    print(f"{'Client ID':<20} {'Role':<15} {'Rate Limit':<15} {'Created At':<30} {'API Key'}")
    print("-" * 80)
    
    for api_key, info in API_KEYS.items():
        created_at = info.get('created_at', 'Unknown')
        print(f"{info['client_id']:<20} {info['role']:<15} {info['rate_limit']:<15} {created_at:<30} {api_key}")
    
    print("-" * 80)
    print(f"Total: {len(API_KEYS)} API keys")

def create_key(client_id, role, rate_limit):
    """Create a new API key"""
    api_key = create_api_key(client_id, role, rate_limit)
    print(f"Created API key for client '{client_id}' with role '{role}':")
    print(f"API Key: {api_key}")
    print("IMPORTANT: Save this API key securely. It cannot be retrieved later.")

def revoke_key(api_key):
    """Revoke an API key"""
    if api_key in API_KEYS:
        client_id = API_KEYS[api_key]["client_id"]
        if revoke_api_key(api_key):
            print(f"Revoked API key for client '{client_id}'")
        else:
            print(f"Failed to revoke API key for client '{client_id}'")
    else:
        print(f"API key not found")

def update_key_role(api_key, role):
    """Update an API key's role"""
    if api_key in API_KEYS:
        API_KEYS[api_key]["role"] = role
        save_api_keys()
        print(f"Updated role for client '{API_KEYS[api_key]['client_id']}' to '{role}'")
    else:
        print(f"API key not found")

def update_key_rate_limit(api_key, rate_limit):
    """Update an API key's rate limit"""
    if api_key in API_KEYS:
        API_KEYS[api_key]["rate_limit"] = rate_limit
        save_api_keys()
        print(f"Updated rate limit for client '{API_KEYS[api_key]['client_id']}' to {rate_limit}")
    else:
        print(f"API key not found")

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description='API Key Management Utility')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List keys command
    list_parser = subparsers.add_parser('list', help='List all API keys')
    
    # Create key command
    create_parser = subparsers.add_parser('create', help='Create a new API key')
    create_parser.add_argument('--client', required=True, help='Client identifier')
    create_parser.add_argument('--role', required=True, choices=['user', 'manager', 'admin', 'developer'], 
                              help='Role for the API key')
    create_parser.add_argument('--rate-limit', type=int, default=100, 
                              help='Rate limit (requests per hour, default: 100)')
    
    # Revoke key command
    revoke_parser = subparsers.add_parser('revoke', help='Revoke an API key')
    revoke_parser.add_argument('--api-key', required=True, help='API key to revoke')
    
    # Update role command
    update_role_parser = subparsers.add_parser('update-role', help='Update an API key\'s role')
    update_role_parser.add_argument('--api-key', required=True, help='API key to update')
    update_role_parser.add_argument('--role', required=True, 
                                  choices=['user', 'manager', 'admin', 'developer'], 
                                  help='New role for the API key')
    
    # Update rate limit command
    update_rate_parser = subparsers.add_parser('update-rate', help='Update an API key\'s rate limit')
    update_rate_parser.add_argument('--api-key', required=True, help='API key to update')
    update_rate_parser.add_argument('--rate-limit', type=int, required=True, 
                                  help='New rate limit (requests per hour)')
    
    args = parser.parse_args()
    
    # Load API keys
    load_api_keys()
    
    # Execute command
    if args.command == 'list':
        list_keys()
    elif args.command == 'create':
        create_key(args.client, args.role, args.rate_limit)
    elif args.command == 'revoke':
        revoke_key(args.api_key)
    elif args.command == 'update-role':
        update_key_role(args.api_key, args.role)
    elif args.command == 'update-rate':
        update_key_rate_limit(args.api_key, args.rate_limit)
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 