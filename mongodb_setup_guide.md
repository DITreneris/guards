# MongoDB Atlas Setup Guide for Guards & Robbers

This guide outlines the steps necessary to set up MongoDB Atlas for the Guards & Robbers marketing website.

*Related Documents:*
- [Implementation Summary](implementation_summary.md)
- [Security Documentation](security_documentation.md)
- [README](README.md)

## Table of Contents

- [1. Create a MongoDB Atlas Account](#1-create-a-mongodb-atlas-account)
- [2. Create a Cluster](#2-create-a-cluster)
- [3. Set Up Database Access](#3-set-up-database-access)
- [4. Configure Network Access](#4-configure-network-access)
- [5. Get Your Connection String](#5-get-your-connection-string)
- [6. Update Your .env File](#6-update-your-env-file)
- [7. Create Collections and Indexes](#7-create-collections-and-indexes)
- [8. Testing Your Connection](#8-testing-your-connection)
- [9. Security Considerations for Production](#9-security-considerations-for-production)
- [10. MongoDB Atlas Dashboard Features](#10-mongodb-atlas-dashboard-features)
- [Troubleshooting](#troubleshooting)

## 1. Create a MongoDB Atlas Account

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and click "Try Free"
2. Sign up with your email or use Google/GitHub authentication
3. Complete the initial setup questionnaire
4. Select the free tier ("Shared") for development purposes

## 2. Create a Cluster

1. Choose "Create" from the Clusters menu
2. Select the "M0 Sandbox" (free tier) option
3. Choose a cloud provider (AWS, GCP, or Azure) and region closest to your users
4. Name your cluster (e.g., "guards-robbers-cluster")
5. Click "Create Cluster" (creation may take a few minutes)

## 3. Set Up Database Access

1. Navigate to the "Database Access" section under Security
2. Click "Add New Database User"
3. Create a username and a strong password
   - Username: `guards_robbers_app`
   - Password: Generate a secure password
4. Select appropriate permissions:
   - For development: "Atlas admin" role
   - For production: Custom role with readWrite on specific database
5. Click "Add User"

## 4. Configure Network Access

1. Navigate to the "Network Access" section under Security
2. Click "Add IP Address"
3. For development, you can choose "Allow Access from Anywhere" (not recommended for production)
4. For production, add specific IP addresses of your application servers
5. Click "Confirm"

## 5. Get Your Connection String

1. Go back to the Clusters view and click "Connect" on your cluster
2. Select "Connect your application"
3. Choose your driver (Python) and version (3.6 or later)
4. Copy the connection string
5. Replace `<password>` with your database user's password
6. Replace `<dbname>` with `guards_robbers_db`

## 6. Update Your .env File

Add the MongoDB connection string to your `.env` file:

```
MONGODB_URI=mongodb+srv://guards_robbers_app:<password>@guards-robbers-cluster.mongodb.net/guards_robbers_db?retryWrites=true&w=majority
MONGODB_DB=guards_robbers_db
MONGODB_COLLECTION=leads
```

## 7. Create Collections and Indexes

After connecting to your MongoDB Atlas cluster, run the `mongodb_schema.py` script to:
1. Create the `leads` collection with proper schema validation
2. Set up required indexes for performance

```
python mongodb_schema.py
```

## 8. Testing Your Connection

1. Run the test script to verify MongoDB connection and operations:

```
python test_mongodb.py
```

2. If successful, you'll see confirmation messages for each test step

## 9. Security Considerations for Production

- Use environment variables for connection strings; never hardcode them
- Restrict IP access to only your application servers
- Use the principle of least privilege for database users
- Enable MongoDB Atlas backups
- Consider enabling encryption of data at rest

For comprehensive security implementation details, please refer to the [Security Documentation](security_documentation.md).

## 10. MongoDB Atlas Dashboard Features

- Monitor database performance in the Atlas dashboard
- Set up alerts for unusual activity
- Use the Data Explorer to view and manage your data
- Access logs for troubleshooting

## Troubleshooting

- If connection fails, check:
  1. Network access settings
  2. Username and password
  3. IP address restrictions
  4. Cluster status

- For "Authentication failed" errors:
  1. Verify your username and password
  2. Check if the user has access to the specified database

- For timeout errors:
  1. Check your network connection
  2. Verify IP whitelist settings

For a detailed overview of the MongoDB implementation, see the [Implementation Summary](implementation_summary.md). 