# Guards & Robbers - Marketing Website

*Version: 1.2.0*  
*Last Updated: April 4, 2025*

A single-page marketing website for Guards & Robbers, an AI-powered cybersecurity platform that combines defense (ARP Guard) and offense (Evader) capabilities.

## Table of Contents

- [Features](#features)
- [Project Documentation](#project-documentation)
- [Quality Standards](#quality-standards)
- [Setup Instructions](#setup-instructions)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
- [Deployment](#deployment)
  - [Heroku Deployment](#heroku-deployment)
  - [Custom Domain Setup](#custom-domain-setup)
- [Project Structure](#project-structure)
- [Development](#development)
  - [Git Workflow](#git-workflow)
  - [Quality Assurance](#quality-assurance)
- [Admin Dashboard](#admin-dashboard)
- [MongoDB Fallback Mechanism](#mongodb-fallback-mechanism)
- [Email System](#email-system)
- [Testing](#testing)
- [Customization](#customization)
- [License](#license)
- [Contact](#contact)
- [Change Log](#change-log)

## Features

- Modern, responsive design with smooth animations
- Lead capture form with MongoDB integration
- Flask backend for handling form submissions
- Robust MongoDB fallback system: JSON file storage + in-memory cache
- Interactive problem visualization with network diagram
- Animated statistics with count-up effect
- Mobile-responsive navigation
- Secure admin dashboard with authentication
- Enhanced testimonials section with visual design and trust elements
- Comprehensive test suite for all features
- Health monitoring endpoints
- Newsletter subscription system with double opt-in
- Mock email system for local development

## Project Documentation

For a complete understanding of this project, please refer to our **[Documentation Portal](index.md)** which provides a comprehensive guide to all project documentation.

For specific areas, please refer to the following:

- **[Development Plan](dev_plan.md)**: Comprehensive project plan including objectives, scope, quality standards, and timeline
- **[Todo List](todo.md)**: Current implementation status and prioritized tasks
- **[Implementation Summary](implementation_summary.md)**: Overview of current implementation details
- **[MongoDB Setup Guide](mongodb_setup_guide.md)**: Instructions for setting up MongoDB Atlas
- **[Security Documentation](security_documentation.md)**: Details of the security implementation

For a guide to navigating all project documentation, see the [Documentation Hierarchy](documentation_hierarchy.md).

## Quality Standards

- Page load time: < 2 seconds on desktop, < 3 seconds on mobile
- W3C validated HTML/CSS
- Cross-browser compatibility (Chrome, Firefox, Safari, Edge)
- Fully responsive across all device sizes (320px+)
- OWASP Top 10 compliant
- Test coverage > 80%

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- MongoDB (local or Atlas account)

### Installation

1. Clone this repository:
```
git clone <repository-url>
cd guards-and-robbers
```

2. Create a virtual environment (recommended):
```
python -m venv venv
```

3. Activate the virtual environment:
   - Windows:
   ```
   venv\Scripts\activate
   ```
   - macOS/Linux:
   ```
   source venv/bin/activate
   ```

4. Install dependencies:
```
pip install -r requirements.txt
```

5. Set up environment variables:
   ```
   # MongoDB connection (optional, system will fall back to local storage if not available)
   export MONGODB_URI="your-connection-string"
   export MONGODB_DB="guards_robbers_db"
   export MONGODB_COLLECTION="leads"
   export MONGODB_SUBSCRIBERS_COLLECTION="subscribers"
   export USE_MONGODB="false"  # Set to "true" to use MongoDB
   
   # Email Configuration
   export SMTP_SERVER="smtp.gmail.com"
   export SMTP_PORT="587"
   export SMTP_USERNAME="your-email@gmail.com"
   export SMTP_PASSWORD="your-app-password"
   export SENDER_EMAIL="noreply@guardsnrobbers.com"
   export SENDER_NAME="Guards & Robbers"
   export BASE_URL="http://localhost:5000"
   export EMAIL_MOCK_MODE="true"  # Set to "false" to use actual SMTP
   
   # Admin authentication (default values will be generated if not set)
   export SECRET_KEY="your-secret-key"
   export DEFAULT_ADMIN_USER="admin"
   export DEFAULT_ADMIN_PASSWORD="your-secure-password"
   
   # Backup configuration
   export ENABLE_JSON_BACKUP="True"
   export JSON_BACKUP_PATH="data/leads.json"
   ```
   
   For Windows, use:
   ```
   set MONGODB_URI="your-connection-string"
   # (and so on for other variables)
   ```

### Running the Application

1. Start the Flask development server:
```
python app_simple.py
```

2. Open your browser and navigate to:
```
http://127.0.0.1:5000
```

3. Access the admin dashboard:
```
http://127.0.0.1:5000/admin/login
```

## Deployment

### Heroku Deployment

1. Install the Heroku CLI and log in
2. Create a Procfile in the project root:
```
web: gunicorn app_simple:app
```

3. Deploy to Heroku:
```
heroku create guards-robbers
git push heroku main
```

4. Set up your environment variables on Heroku:
```
heroku config:set MONGODB_URI="your-connection-string"
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set USE_MONGODB="true"
heroku config:set EMAIL_MOCK_MODE="false"
# (and other variables as needed)
```

### Custom Domain Setup

1. Purchase a domain (e.g., guardsrobbers.com)
2. Configure your DNS settings to point to your hosting provider
3. Set up SSL certificates for secure HTTPS connections

## Project Structure

- `app_simple.py` - Main Flask application
- `admin_auth.py` - Admin authentication module
- `utils/` - Utility modules
  - `email_sender.py` - Email sending functionality
- `templates/` - HTML templates
  - `index.html` - Main marketing page
  - `admin_login.html` - Admin login page
  - `admin_dashboard.html` - Admin dashboard for lead management
  - `admin_settings.html` - Admin settings page
  - `base.html` - Base template with common layout elements
  - `testimonials.html` - Testimonials and trust signals page
  - `subscription_confirmed.html` - Email subscription confirmation page
  - `unsubscribe.html` - Email unsubscribe page
  - `email_templates/` - Email HTML templates
    - `welcome_email.html` - Welcome email template
    - `newsletter_template.html` - Newsletter template
- `static/` - Static assets (CSS, JavaScript, images)
  - `css/` - Stylesheet files
    - `testimonials.css` - Styles for the testimonials section
  - `js/` - JavaScript functionality
  - `images/` - Image assets
    - `testimonials/` - Testimonial avatars, logos, and badges
- `data/` - Local data storage
  - `leads.json` - Local backup of form submissions
  - `subscribers.json` - Local storage for newsletter subscribers
  - `emails/` - Saved mock emails for testing
- `admin_users.json` - Admin user information (encrypted)
- `tests/` - Test scripts
  - `admin_auth_test.py` - Tests for admin authentication
  - `app_test.py` - Tests for Flask application
- `requirements.txt` - Python dependencies
- `Procfile` - Heroku deployment configuration

## Development

### Git Workflow

We follow a structured Git workflow:
- `main` branch: Production-ready code
- `develop` branch: Integration branch
- Feature branches: `feature/name-of-feature`
- Bug fixes: `bugfix/issue-description`

Commit messages follow the conventional format:
```
feat(scope): description
fix(scope): description
docs(scope): description
```

### Quality Assurance

Before submitting a PR:
- Ensure code follows PEP 8 (Python) and ESLint (JS) standards
- Run all unit tests (`pytest`)
- Verify responsive design across breakpoints
- Check performance in Lighthouse

## Admin Dashboard

The application includes a secure admin dashboard with the following features:

- **Authentication**: Secure login with salted password hashing
- **Lead Management**: View and manage all submitted leads
- **User Settings**: Change password and view environment information
- **Session Management**: Automatic timeout for security

To access the admin dashboard, navigate to `/admin/login` and use the default credentials (admin/password) or the credentials set in your environment variables.

## MongoDB Fallback Mechanism

The application features a robust fallback system for data storage:

1. **Primary**: MongoDB Atlas or local MongoDB instance
2. **Secondary**: Local JSON file storage
3. **Tertiary**: In-memory storage

If the MongoDB connection fails, the system automatically falls back to the local JSON file storage. All data is maintained in-memory during the application runtime for fast access.

The connection system includes:
- Exponential backoff retry logic (1s, 2s, 4s)
- Configurable SSL/TLS settings
- Environment variable control (USE_MONGODB)
- Detailed error logging

## Email System

The application includes a comprehensive email system for newsletter subscriptions:

1. **Double Opt-in**: New subscribers must confirm their email
2. **Templated Emails**: HTML templates for all communications
3. **Mock Mode**: Development mode saves emails to files instead of sending
4. **Fallback Logic**: If SMTP fails, falls back to mock mode

To view mock emails during development:
- Configure EMAIL_MOCK_MODE=true in your environment
- Check the data/emails/ directory for saved email files

## Testing

The application includes a comprehensive test suite:

1. Run admin authentication tests:
```
python admin_auth_test.py
```

2. Run application tests:
```
pytest app_test.py
```

Or run all tests:
```
pytest
```

## Customization

- Edit `templates/index.html` to change content
- Modify `static/css/styles.css` to customize styling
- Update `static/js/script.js` for interactive behavior

## License

This project is proprietary and confidential.

## Contact

For questions or support: info@guardsrobbers.com

## Change Log

### Version 1.2.0 (Current)

- Added newsletter subscription system with double opt-in confirmation
- Implemented mock email system for local development
- Enhanced MongoDB connection with retry logic and fallback
- Improved robustness of local file storage system
- Added detailed environment configuration options

### Version 1.1.0

- Added secure admin dashboard with authentication
- Implemented MongoDB fallback mechanism with JSON and in-memory storage
- Added comprehensive test suite with CI/CD integration
- Added enhanced testimonials section with visual design and trust elements 