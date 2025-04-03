# Guards & Robbers Deployment Checklist

*Version: 1.0.0*  
*Last Updated: April 3, 2025*

This document provides a step-by-step checklist for deploying the Guards & Robbers application to Heroku.

## Table of Contents

- [Pre-Deployment Preparation](#pre-deployment-preparation)
- [Environment Configuration](#environment-configuration)
- [GitHub Integration](#github-integration)
- [Deployment Process](#deployment-process)
- [Post-Deployment Verification](#post-deployment-verification)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)
- [Rollback Procedure](#rollback-procedure)

## Pre-Deployment Preparation

- [x] Create GitHub repository (https://github.com/DITreneris/guards)
- [x] Push code to GitHub
- [x] Create Heroku account
- [x] Install Heroku CLI
- [x] Create Heroku app (guards-robbers)
- [x] Verify `Procfile` exists and contains `web: gunicorn app:app`
- [x] Verify `requirements.txt` includes all dependencies (including gunicorn)
- [x] Run all tests locally to ensure they pass
- [ ] Create MongoDB Atlas free tier account (if not already done)
- [ ] Secure MongoDB connection with proper network access settings
- [ ] Verify MongoDB connection string works locally

## Environment Configuration

- [x] Set up MongoDB connection string in Heroku:
  ```
  heroku config:set MONGODB_URI="mongodb+srv://guards_robbers_app:your_password@guards-robbers-cluster.mongodb.net/guards_robbers_db?retryWrites=true&w=majority" --app guards-robbers
  ```
- [x] Set up database name in Heroku:
  ```
  heroku config:set MONGODB_DB="guards_robbers_db" --app guards-robbers
  ```
- [x] Set up collection name in Heroku:
  ```
  heroku config:set MONGODB_COLLECTION="leads" --app guards-robbers
  ```
- [ ] Set up any additional environment variables required by the application
  ```
  heroku config:set SECRET_KEY="your_secret_key" --app guards-robbers
  ```

## GitHub Integration

- [ ] Login to Heroku dashboard (https://dashboard.heroku.com/)
- [ ] Select "guards-robbers" app
- [ ] Navigate to the "Deploy" tab
- [ ] Under "Deployment method", select "GitHub"
- [ ] Connect to GitHub account
- [ ] Search for "guards" repository and connect it
- [ ] Choose the "main" branch for deployment
- [ ] Optional: Enable automatic deploys from the main branch
- [ ] Click "Deploy Branch" under "Manual deploy" section

## Deployment Process

- [ ] Monitor deployment progress in Heroku dashboard
- [ ] Check for any build errors in the deployment logs
- [ ] Verify dyno formation is active (at least 1 web dyno)
  ```
  heroku ps:scale web=1 --app guards-robbers
  ```
- [ ] Verify the application is running
  ```
  heroku open --app guards-robbers
  ```

## Post-Deployment Verification

- [ ] Verify the application loads correctly
- [ ] Test lead capture form submission
- [ ] Verify data is being saved to MongoDB Atlas
- [ ] Test all API endpoints
- [ ] Check application logs for any errors
  ```
  heroku logs --tail --app guards-robbers
  ```
- [ ] Test application on different browsers (Chrome, Firefox, Safari, Edge)
- [ ] Test application on different devices (desktop, tablet, mobile)

## Monitoring and Maintenance

- [ ] Set up Heroku application metrics
- [ ] Set up MongoDB Atlas monitoring
- [ ] Schedule regular database backups
- [ ] Configure alerts for application errors
- [ ] Set up uptime monitoring
- [ ] Document maintenance procedures and schedules

## Troubleshooting

### Common Issues and Solutions

1. **Application crashes on startup**
   - Check Heroku logs: `heroku logs --app guards-robbers`
   - Verify all required environment variables are set
   - Ensure `Procfile` is correctly formatted

2. **MongoDB connection issues**
   - Verify connection string in environment variables
   - Check MongoDB Atlas network access settings
   - Verify MongoDB user has the correct permissions

3. **Missing dependencies**
   - Update `requirements.txt` and redeploy
   - Ensure all dependencies are compatible with Heroku

4. **Memory/resource issues**
   - Check application metrics in Heroku dashboard
   - Consider upgrading to a paid dyno if necessary
   - Optimize code to reduce resource usage

## Rollback Procedure

1. **Rollback to previous version**
   - Go to the "Activity" tab in Heroku dashboard
   - Find the previous successful deployment
   - Click "Rollback to here"

2. **Emergency shutdown**
   - Scale down web dynos: `heroku ps:scale web=0 --app guards-robbers`
   - Fix issues locally and redeploy

3. **Full reset (if necessary)**
   - Backup all data from MongoDB Atlas
   - Reset the application: `heroku repo:reset --app guards-robbers`
   - Redeploy from GitHub

## Custom Domain Setup (Future)

- [ ] Purchase domain name (e.g., guardsrobbers.com)
- [ ] Add custom domain in Heroku dashboard
- [ ] Configure DNS settings with domain provider
- [ ] Set up SSL certificate
- [ ] Verify HTTPS is working correctly 