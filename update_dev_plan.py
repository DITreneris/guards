#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Update Dev Plan

This script updates the dev_plan.md file with sales-readiness information
to prepare for the board meeting and commercialization of the ML system.
"""

import re
from pathlib import Path
from datetime import datetime

# Configuration
DEV_PLAN_PATH = Path("dev_plan.md")
VERSION = "2.0.0"
CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")

def read_dev_plan():
    """Read the current dev_plan.md file"""
    try:
        with open(DEV_PLAN_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        print(f"Error: {DEV_PLAN_PATH} not found")
        return None

def update_version_and_date(content):
    """Update the version and date at the top of the document"""
    # Define the pattern for the version and date lines
    version_pattern = r"\*Version: [0-9.]+\*"
    date_pattern = r"\*Last Updated: .*\*"
    
    # Replace with new version and date
    content = re.sub(version_pattern, f"*Version: {VERSION}*", content)
    content = re.sub(date_pattern, f"*Last Updated: {CURRENT_DATE}*", content)
    
    return content

def add_commercialization_section(content):
    """Add a new commercialization section to the document"""
    commercialization_section = """
## ML Commercialization Strategy

### Pricing & Packaging

The ML framework is now available in three pricing tiers:

1. **Basic Tier** ($99.99/month)
   - Intent Recognition
   - Sentiment Analysis
   - Email Categorization
   - Basic Entity Extraction
   - Standard Support
   - API Rate Limit: 60 requests/minute
   - Max Users: 5

2. **Professional Tier** ($299.99/month)
   - All Basic features plus:
   - Advanced Entity Extraction
   - Custom Entities
   - Model Fine-tuning
   - Priority Support
   - API Access
   - Dashboard Analytics
   - API Rate Limit: 300 requests/minute
   - Max Users: 20

3. **Enterprise Tier** ($999.99/month)
   - All Professional features plus:
   - Custom Model Training
   - Multi-language Support
   - Advanced Analytics
   - Dedicated Support
   - SLA Guarantees
   - API Rate Limit: 1000 requests/minute
   - Unlimited Users

All tiers include a 14-day free trial and annual billing discounts.

### Self-Sustainability Features

The ML framework has been enhanced with the following self-sustainability features:

1. **Usage Metering**
   - Detailed tracking of API calls, model inferences, and data storage
   - Real-time usage monitoring and reporting
   - Transparent billing with overage calculations

2. **Automatic Model Monitoring**
   - Real-time performance metrics (accuracy, latency, throughput)
   - Automatic alerts for model degradation
   - Self-healing capabilities for common issues

3. **Scalability Improvements**
   - Auto-scaling infrastructure based on demand
   - Load balancing across multiple servers
   - Resource optimization for cost efficiency

4. **Operational Dashboard**
   - Real-time system health monitoring
   - Usage and billing metrics
   - Customer usage patterns and insights

### Sales Enablement

The following sales tools have been created to support the commercial launch:

1. **Demo Environment**
   - Interactive demo of all ML capabilities
   - Customizable for prospect-specific use cases
   - Deployable in isolated environments for security

2. **ROI Calculator**
   - Customizable calculator to demonstrate customer value
   - Industry-specific templates for common use cases
   - Integration with CRM for sales tracking

3. **Technical Documentation**
   - Comprehensive API documentation
   - Integration guides for common platforms
   - Security and compliance documentation

4. **Sales Collateral**
   - Product datasheets for each tier
   - Competitive comparison charts
   - Case studies and success stories
"""
    
    # Find the position to insert the new section
    if "## Risk Management" in content:
        # Insert before Risk Management section
        content = content.replace("## Risk Management", f"{commercialization_section}\n\n## Risk Management")
    else:
        # Append to the end if Risk Management section not found
        content += f"\n{commercialization_section}\n"
    
    return content

def update_next_steps(content):
    """Update the Next Steps section to include commercialization tasks"""
    commercialization_tasks = """
#### Phase 6: Commercialization (Priority: Highest)
- [ ] Launch pricing tiers and self-service signup
- [ ] Implement automated billing and invoicing
- [ ] Create sales enablement training for the team
- [ ] Develop partner integration program
- [ ] Set up customer success workflows
- [ ] Implement feedback collection and analysis system
"""
    
    # Find the Next Steps section and add commercialization tasks
    if "### Next Steps" in content:
        # Pattern to find the end of the Next Steps section
        next_steps_end_pattern = r"### Next Steps.*?(?=###|$)"
        
        # Extract the Next Steps section
        next_steps_match = re.search(next_steps_end_pattern, content, re.DOTALL)
        if next_steps_match:
            next_steps_section = next_steps_match.group(0)
            updated_section = next_steps_section + commercialization_tasks
            content = content.replace(next_steps_section, updated_section)
    
    return content

def update_current_status(content):
    """Update the Current Status section to reflect sales readiness"""
    sales_ready_status = """
### Current Status (Updated: CURRENT_DATE)
- ✓ Basic Flask application deployed to Heroku
- ✓ Landing page with lead collection form implemented
- ✓ Lead storage system with MongoDB integration
- ✓ Fallback mechanism for MongoDB using local JSON storage
- ✓ Admin dashboard with authentication
- ✓ Health monitoring endpoints
- ✓ Comprehensive test suite
- ✓ Newsletter subscription system with double opt-in confirmation
- ✓ Enhanced testimonials section with trust signals
- ✓ Enhanced MongoDB connection with retry logic
- ✓ ML framework core components implemented and functional
- ✓ Bot intelligence with NLP and conversation management
- ✓ Email processing system with entity extraction
- ✓ Data collection with structured information extraction
- ✓ ML demo system with comprehensive testing capabilities
- ✓ Usage metering system for billing and monitoring
- ✓ Model monitoring with real-time alerts
- ✓ Tiered pricing structure implemented
- ✓ Sales demo environment for customer presentations
- ✓ Self-sustainability features for commercial deployment
- → Partner integration capabilities in development
- → Enhanced analytics dashboard in progress
- → Customer success workflows being implemented
""".replace("CURRENT_DATE", CURRENT_DATE)
    
    # Find and replace the Current Status section
    current_status_pattern = r"### Current Status.*?(?=###|$)"
    if re.search(current_status_pattern, content, re.DOTALL):
        content = re.sub(current_status_pattern, sales_ready_status, content, flags=re.DOTALL)
    
    return content

def update_change_log(content):
    """Update the Change Log with the new sales-ready version"""
    change_log_entry = f"""| {VERSION} | {CURRENT_DATE} | Sales Director | Commercialization update: Added tiered pricing structure, usage metering, model monitoring, self-sustainability features, and sales enablement tools. ML system now ready for commercial deployment. |"""
    
    # Find the Change Log section
    if "## Change Log" in content:
        change_log_pattern = r"## Change Log.*?(?=\n\n##|$)"
        change_log_match = re.search(change_log_pattern, content, re.DOTALL)
        
        if change_log_match:
            change_log = change_log_match.group(0)
            
            # Find the table in the Change Log
            table_pattern = r"\|.*?\|.*?\|.*?\|.*?\|"
            table_matches = re.findall(table_pattern, change_log, re.DOTALL)
            
            if table_matches:
                # Add new entry after the header row
                updated_table = table_matches[0] + "\n" + change_log_entry
                for entry in table_matches[1:]:
                    updated_table += "\n" + entry
                
                # Replace the old table with the updated one
                content = content.replace("\n".join(table_matches), updated_table)
    
    return content

def write_dev_plan(content):
    """Write the updated content back to dev_plan.md"""
    try:
        with open(DEV_PLAN_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing to {DEV_PLAN_PATH}: {e}")
        return False

def update_plan():
    """Update the development plan"""
    # Read the current dev_plan.md
    content = read_dev_plan()
    if not content:
        return False
    
    # Make the updates
    content = update_version_and_date(content)
    content = add_commercialization_section(content)
    content = update_next_steps(content)
    content = update_current_status(content)
    content = update_change_log(content)
    
    # Write the updated content back
    success = write_dev_plan(content)
    
    if success:
        print(f"Successfully updated {DEV_PLAN_PATH} to version {VERSION}")
        print(f"Added commercialization section and updated status for sales readiness")
    
    return success

if __name__ == "__main__":
    update_plan() 