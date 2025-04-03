# Security Implementation for Guards & Robbers

This document outlines the security measures implemented for the Guards & Robbers application to protect developer interests, ensure data integrity, and control access to resources.

*Related Documents:*
- [Implementation Summary](implementation_summary.md)
- [MongoDB Setup Guide](mongodb_setup_guide.md)
- [README](README.md)

## Table of Contents

- [Overview](#overview)
- [Components](#components)
  - [1. Security Contract](#1-security-contract-security_contractpy)
  - [2. Secure MongoDB Wrapper](#2-secure-mongodb-wrapper-secure_mongodbpy)
  - [3. API Key Management Utility](#3-api-key-management-utility-manage_api_keyspy)
- [Security Flow](#security-flow)
- [Roles and Permissions](#roles-and-permissions)
- [Implementation Best Practices](#implementation-best-practices)
- [API Security Headers](#api-security-headers)
- [Usage Examples](#usage-examples)
  - [Securing an Endpoint](#securing-an-endpoint)
  - [Using the Secure MongoDB Client](#using-the-secure-mongodb-client)
  - [Creating an API Key](#creating-an-api-key)
- [Security Monitoring](#security-monitoring)
- [Emergency Procedures](#emergency-procedures)

## Overview

The application implements a comprehensive security system similar to a smart contract, including:

1. **Authentication and Authorization**: API key-based access control with role-based permissions
2. **Rate Limiting**: Prevents abuse by limiting request frequencies
3. **Access Logging and Auditing**: Records all database operations for accountability
4. **Database Access Controls**: Secures data operations through a wrapper layer
5. **Local Fallback Mechanisms**: Ensures data availability even during service disruptions

## Components

### 1. Security Contract (security_contract.py)

The security contract defines the rules and constraints for accessing the application's resources:

- **API Key Management**: Secure generation, storage, and validation of API keys
- **Role-Based Access Control**: Restricts endpoints based on user roles
- **Rate Limiting**: Limits requests per client within time windows
- **Access Logging**: Records all access attempts for auditing

### 2. Secure MongoDB Wrapper (secure_mongodb.py)

A wrapper around MongoDB operations that enforces security policies:

- **Access Logging**: Records all database operations
- **Error Handling**: Graceful handling of database failures
- **Connection Management**: Automatic reconnection and resource cleanup
- **Retry Logic**: Multiple attempts for transient failures

For detailed MongoDB setup instructions, see the [MongoDB Setup Guide](mongodb_setup_guide.md).

### 3. API Key Management Utility (manage_api_keys.py)

Command-line tool for managing API keys:

- **Create**: Generate new API keys with specific roles and rate limits
- **List**: View existing API keys and their properties
- **Revoke**: Disable compromised or unused API keys
- **Update**: Modify role assignments and rate limits

## Security Flow

1. **Client Authentication**:
   - Client includes API key in request header or query parameter
   - System validates API key and loads client profile
   - Rate limiting is enforced per client

2. **Authorization**:
   - Client role is checked against required roles for endpoint
   - Operation is allowed or denied based on role

3. **Database Operations**:
   - All operations are logged with client information
   - Operations are executed through the secure wrapper
   - Any errors are handled gracefully with appropriate responses

4. **Fallback Mechanisms**:
   - If database operations fail, local storage is used when enabled
   - All failures are logged for investigation

## Roles and Permissions

| Role       | Permissions                                       |
|------------|---------------------------------------------------|
| user       | Submit leads, view basic public information       |
| manager    | User permissions + view all leads                 |
| admin      | Manager permissions + modify and delete leads     |
| developer  | Full access to all system functions               |

## Implementation Best Practices

- **Environment Variables**: All sensitive configuration stored in environment variables
- **Secure Storage**: API keys stored with secure hashing
- **Minimal Exposure**: Only necessary information exposed in APIs
- **Defense in Depth**: Multiple security layers for critical operations
- **Fail Secure**: Default deny unless explicitly permitted

## API Security Headers

All sensitive API endpoints should include these security headers:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

## Usage Examples

### Securing an Endpoint

```python
@app.route('/admin/leads', methods=['GET'])
@requires_auth
@requires_role(['admin', 'manager'])
def get_all_leads():
    # Function implementation
```

### Using the Secure MongoDB Client

```python
from secure_mongodb import get_secure_mongo_client

# Get client
secure_mongo = get_secure_mongo_client()

# Insert document with automatic logging
doc_id = secure_mongo.insert_document(document)
```

### Creating an API Key

```bash
python manage_api_keys.py create --client "marketing-team" --role "manager" --rate-limit 200
```

## Security Monitoring

- Regular review of `db_access.log` for suspicious patterns
- Monitor rate limit violations in application logs
- Audit API key usage and rotate keys periodically

## Emergency Procedures

1. **Security Breach**:
   - Revoke all API keys with `python manage_api_keys.py list` and `python manage_api_keys.py revoke`
   - Reset MongoDB Atlas connection string
   - Review access logs to determine scope of breach

2. **Rate Limit Attacks**:
   - Temporarily lower rate limits in .env file
   - Block offending IPs at network level
   - Increase monitoring frequency 

For a comprehensive overview of the implementation, see the [Implementation Summary](implementation_summary.md). 