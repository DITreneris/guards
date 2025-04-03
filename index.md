# Guards & Robbers Documentation Portal

*Version: 1.0.0*  
*Last Updated: April 3, 2025*

Welcome to the Guards & Robbers project documentation portal. This page serves as your central hub for all project documentation.

The Guards & Robbers marketing website has recently undergone significant upgrades, transitioning from Google Sheets to MongoDB for lead data storage. This change enhances security, scalability, and reliability while maintaining the sleek user interface and experience. The documentation in this portal reflects these changes and provides comprehensive guidance on all aspects of the project.

## Table of Contents

- [Project Overview](#project-overview)
- [Implementation Documentation](#implementation-documentation)
- [Technical Reference](#technical-reference)
  - [Core Files](#core-files)
  - [Tests](#tests)
  - [Utilities](#utilities)
- [Quality Assurance](#quality-assurance)
- [Quick Links](#quick-links)
  - [For New Team Members](#for-new-team-members)
  - [For Development](#for-development)
  - [For Deployment](#for-deployment)
- [Documentation Maintenance](#documentation-maintenance)

## Project Overview

- [**README.md**](README.md): The primary entry point for the project with features, setup instructions, and key information.
- [**Development Plan**](dev_plan.md): Comprehensive project plan including objectives, scope, quality standards, and timeline.
- [**Todo List**](todo.md): Current implementation status and prioritized tasks organized by priority and category.
- [**Documentation Hierarchy**](documentation_hierarchy.md): Guide to navigating and understanding the project documentation structure.

## Implementation Documentation

- [**Implementation Summary**](implementation_summary.md): Overview of implemented features, focusing on MongoDB integration and security.
- [**MongoDB Setup Guide**](mongodb_setup_guide.md): Step-by-step instructions for setting up and configuring MongoDB Atlas.
- [**Security Documentation**](security_documentation.md): Detailed explanation of the security implementation, including authentication, authorization, and access controls.

## Quality Assurance

- [**Cross-Browser Testing**](cross_browser_testing.md): Results of compatibility testing across Chrome, Firefox, Safari, and Edge.
- [**Responsive Design Testing**](responsive_design_testing.md): Results of layout testing across mobile, tablet, desktop, and large desktop breakpoints.
- [**Lighthouse Audit**](lighthouse_audit.md): Performance, accessibility, and best practices audit results with optimization details.
- [**W3C Validation**](w3c_validation.md): HTML and CSS validation results ensuring compliance with web standards.

## Technical Reference

### Core Files

- **app.py**: Main Flask application with API endpoints and route handlers.
- **mongodb_schema.py**: Database schema definition with validation rules.
- **security_contract.py**: Security system implementation with API key management and access controls.
- **secure_mongodb.py**: Secure MongoDB wrapper enforcing access policies and logging.

### Tests

- **test_app.py**: Tests for the Flask application endpoints.
- **test_mongodb.py**: Tests for MongoDB connectivity and operations.
- **test_mongodb_atlas.py**: Tests for MongoDB Atlas integration.
- **test_security.py**: Tests for the security implementation.

### Utilities

- **manage_api_keys.py**: Command-line utility for managing API keys.

## Quick Links

### For New Team Members

1. Start with the [README.md](README.md) for project overview
2. Review the [Development Plan](dev_plan.md) for project strategy
3. Check the [Todo List](todo.md) for current priorities
4. Follow the [MongoDB Setup Guide](mongodb_setup_guide.md) to set up your environment

### For Development

1. Refer to [Todo List](todo.md) for current tasks
2. Use the [Implementation Summary](implementation_summary.md) to understand current state
3. Follow the [Security Documentation](security_documentation.md) when working with sensitive endpoints

### For Deployment

1. Review the deployment section in [README.md](README.md)
2. Ensure MongoDB Atlas is configured according to the [MongoDB Setup Guide](mongodb_setup_guide.md)
3. Verify all security measures are in place as per [Security Documentation](security_documentation.md)

## Documentation Maintenance

This documentation is maintained according to the standards described in the [Documentation Hierarchy](documentation_hierarchy.md). All team members are responsible for keeping documentation up-to-date when making changes to the codebase.

For questions about the documentation, please contact the project manager. 