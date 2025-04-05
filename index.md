# Guards & Robbers Documentation Portal

*Version: 2.0.0*  
*Last Updated: June 14, 2025*

Welcome to the Guards & Robbers project documentation portal. This page serves as your central hub for all project documentation.

The Guards & Robbers marketing website has recently undergone significant upgrades, including ML framework integration for advanced customer interaction and commercialization features for sales readiness. The documentation in this portal reflects these changes and provides comprehensive guidance on all aspects of the project.

## Table of Contents

- [Project Overview](#project-overview)
- [Implementation Documentation](#implementation-documentation)
- [ML Framework](#ml-framework)
- [Commercial Resources](#commercial-resources)
- [Technical Reference](#technical-reference)
  - [Core Files](#core-files)
  - [Tests](#tests)
  - [Utilities](#utilities)
- [Quality Assurance](#quality-assurance)
- [Deployment](#deployment)
- [Quick Links](#quick-links)
  - [For New Team Members](#for-new-team-members)
  - [For Developers](#for-developers)
  - [For ML Engineers](#for-ml-engineers)
  - [For Sales Teams](#for-sales-teams)
  - [For Deployment](#for-deployment)
- [Documentation Maintenance](#documentation-maintenance)

## Project Overview

- [**README.md**](README.md): The primary entry point for the project with features, setup instructions, and key information.
- [**Development Plan**](dev_plan.md): Comprehensive project plan including objectives, scope, quality standards, and timeline.
- [**Todo List**](todo.md): Current implementation status and prioritized tasks organized by priority and category.
- [**Documentation Hierarchy**](documentation_hierarchy.md): Guide to navigating and understanding the project documentation structure.
- [**Roadmap**](roadmap.md): Future development plans and feature priorities.
- [**Version Management**](version_management.md): Guidelines for versioning and release management.

## Implementation Documentation

- [**Implementation Summary**](implementation_summary.md): Overview of implemented features, focusing on MongoDB integration and security.
- [**MongoDB Setup Guide**](mongodb_setup_guide.md): Step-by-step instructions for setting up and configuring MongoDB Atlas.
- [**Security Documentation**](security_documentation.md): Detailed explanation of the security implementation, including authentication, authorization, and access controls.
- [**Deployment Checklist**](deployment_checklist.md): Comprehensive checklist for deploying the application to Heroku.

## ML Framework

- [**ML Strategy**](ml_strategy.md): Overall strategy for ML implementation and integration.
- [**ML Implementation Plan**](ml_implementation_plan.md): Detailed plan for implementing ML features.
- [**ML Enhancement Plan**](ml_enhancement_plan.md): Roadmap for enhancing ML capabilities.
- [**Sales-Ready ML Framework**](README_SALES_ML.md): Comprehensive guide to the commercial ML framework components.
- [**Communication Bot**](communication_bot.md): Implementation details for the ML-powered communication bot.

## Commercial Resources

- [**Sales Configuration**](ml_sales_config.py): Configuration for ML system pricing tiers and features.
- [**Usage Metering**](ml_usage_metering.py): Implementation of usage tracking and billing.
- [**Sales Demo**](ml_sales_demo.py): Interactive demonstration of commercial ML capabilities.

## Quality Assurance

- [**Cross-Browser Testing**](cross_browser_testing.md): Results of compatibility testing across Chrome, Firefox, Safari, and Edge.
- [**Responsive Design Testing**](responsive_design_testing.md): Results of layout testing across mobile, tablet, desktop, and large desktop breakpoints.
- [**Lighthouse Audit**](lighthouse_audit.md): Performance, accessibility, and best practices audit results with optimization details.
- [**W3C Validation**](w3c_validation.md): HTML and CSS validation results ensuring compliance with web standards.

## Deployment

- [**Deployment Checklist**](deployment_checklist.md): Comprehensive checklist for deploying the application to Heroku.

## Technical Reference

### Core Files

- **app.py**: Main Flask application with API endpoints and route handlers.
- **mongodb_schema.py**: Database schema definition with validation rules.
- **security_contract.py**: Security system implementation with API key management and access controls.
- **secure_mongodb.py**: Secure MongoDB wrapper enforcing access policies and logging.

### ML Components

- **ml_demo.py**: Demonstration of ML framework capabilities.
- **ml_sales_demo.py**: Commercial demo of ML capabilities for sales presentations.
- **ml_usage_metering.py**: Usage tracking and billing for ML services.
- **ml_sales_config.py**: Commercial configuration for ML services.

### Tests

- **test_app.py**: Tests for the Flask application endpoints.
- **test_mongodb.py**: Tests for MongoDB connectivity and operations.
- **test_mongodb_atlas.py**: Tests for MongoDB Atlas integration.
- **test_security.py**: Tests for the security implementation.
- **test_ml_components.py**: Tests for ML components and integration.

### Utilities

- **manage_api_keys.py**: Command-line utility for managing API keys.
- **update_dev_plan.py**: Utility for updating the development plan.

## Quick Links

### For New Team Members

1. Start with the [README.md](README.md) for project overview
2. Review the [Development Plan](dev_plan.md) for project strategy
3. Check the [Todo List](todo.md) for current priorities
4. Follow the [MongoDB Setup Guide](mongodb_setup_guide.md) to set up your environment
5. Review the [Documentation Hierarchy](documentation_hierarchy.md) for navigation

### For Developers

1. Refer to [Todo List](todo.md) for current tasks
2. Use the [Implementation Summary](implementation_summary.md) to understand current state
3. Follow the [Security Documentation](security_documentation.md) when working with sensitive endpoints

### For ML Engineers

1. Review the [ML Strategy](ml_strategy.md) for ML implementation approach
2. Check the [ML Implementation Plan](ml_implementation_plan.md) for detailed tasks
3. Read the [ML Enhancement Plan](ml_enhancement_plan.md) for future directions
4. Use the [README_SALES_ML.md](README_SALES_ML.md) for commercial ML framework details

### For Sales Teams

1. Explore the [Sales-Ready ML Framework](README_SALES_ML.md) documentation
2. Run the demo with `python ml_sales_demo.py` to show capabilities
3. Refer to pricing tiers in [ml_sales_config.py](ml_sales_config.py)
4. Understand usage metering in [ml_usage_metering.py](ml_usage_metering.py)

### For Deployment

1. Review the deployment section in [README.md](README.md)
2. Ensure MongoDB Atlas is configured according to the [MongoDB Setup Guide](mongodb_setup_guide.md)
3. Verify all security measures are in place as per [Security Documentation](security_documentation.md)
4. Follow the [Deployment Checklist](deployment_checklist.md) for a comprehensive verification

## Documentation Maintenance

This documentation is maintained according to the standards described in the [Documentation Hierarchy](documentation_hierarchy.md). All team members are responsible for keeping documentation up-to-date when making changes to the codebase.

For questions about the documentation, please contact the project lead. 