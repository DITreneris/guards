# Guards & Robbers - Marketing Website

*Version: 1.0.0*  
*Last Updated: April 3, 2025*

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
- [Customization](#customization)
- [License](#license)
- [Contact](#contact)
- [Change Log](#change-log)

## Features

- Modern, responsive design with smooth animations
- Lead capture form with MongoDB integration
- Flask backend for handling form submissions
- Fallback local storage of leads in JSON format
- Interactive problem visualization with network diagram
- Animated statistics with count-up effect
- Mobile-responsive navigation

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

5. Set up MongoDB:
   - Create a MongoDB Atlas account or use local MongoDB instance
   - Set up database and collection for leads
   - Configure connection string in environment variables:
     ```
     export MONGODB_URI="your-connection-string"
     ```
     For Windows, use:
     ```
     set MONGODB_URI="your-connection-string"
     ```

### Running the Application

1. Start the Flask development server:
```
python app.py
```

2. Open your browser and navigate to:
```
http://127.0.0.1:5000
```

## Deployment

### Heroku Deployment

1. Install the Heroku CLI and log in
2. Create a Procfile in the project root:
```
web: gunicorn app:app
```

3. Deploy to Heroku:
```
heroku create guards-robbers
git push heroku main
```

4. Set up your environment variables on Heroku:
```
heroku config:set MONGODB_URI="your-connection-string"
```

### Custom Domain Setup

1. Purchase a domain (e.g., guardsrobbers.com)
2. Configure your DNS settings to point to your hosting provider
3. Set up SSL certificates for secure HTTPS connections

## Project Structure

- `app.py` - Main Flask application
- `templates/` - HTML templates
- `static/` - Static assets (CSS, JavaScript, images)
  - `css/` - Stylesheet files
  - `js/` - JavaScript functionality
  - `images/` - Image assets
- `leads.json` - Local backup of form submissions
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

## Customization

- Edit `templates/index.html` to change content
- Modify `static/css/styles.css` to customize styling
- Update `static/js/script.js` for interactive behavior

## License

This project is proprietary and confidential.

## Contact

For questions or support: info@guardsrobbers.com

## Change Log

| Version | Date | Description |
|---------|------|-------------|
| 0.1.0 | 2025-03-30 | Initial setup and structure |
| 1.0.0 | 2025-04-03 | First production release with MongoDB integration | 