# Guards & Robbers ML Framework - Sales Ready Version

## Overview

This document provides a quick guide to the sales-ready components of the Guards & Robbers ML Framework. The system has been enhanced to support commercial deployment, with features for usage tracking, billing, and system health monitoring.

## Key Components

### 1. `ml_sales_config.py`

This module defines the commercial configuration for the ML system, including:
- Pricing tiers (Basic, Professional, Enterprise)
- Feature access per tier
- System requirements for different deployment scenarios
- SLA parameters

Usage:
```python
from ml_sales_config import get_sales_config, print_pricing_summary

# Get the current sales configuration
config = get_sales_config()

# Print a summary of pricing tiers
print_pricing_summary()
```

### 2. `ml_usage_metering.py`

This module handles tracking, billing, and usage metering for the ML system, including:
- Recording API calls, model inferences, and data storage
- Generating usage reports
- Calculating billing based on usage and tier
- Middleware for automatic tracking in web applications

Usage:
```python
from ml_usage_metering import UsageMeter, UsageMetric

# Create a meter instance
meter = UsageMeter()

# Record usage
meter.record_usage(
    client_id="client123",
    metric_type=UsageMetric.API_CALL,
    metadata={"endpoint": "/api/predict", "method": "POST"}
)

# Get usage summary for a client
summary = meter.get_usage_summary("client123")

# Calculate billing
billing = meter.calculate_billing(
    client_id="client123",
    tier="professional"
)
```

### 3. `ml_monitoring.py`

This module provides monitoring for ML models in production, including:
- Tracking model predictions and performance
- Calculating real-time metrics (accuracy, latency, throughput)
- Alerting on performance degradation
- Health status reporting

Usage:
```python
from ml_monitoring import create_default_monitor

# Create a monitor instance
monitor = create_default_monitor()

# Start the monitoring service
monitor.start()

# Track a prediction
monitor.track_prediction(
    model_name="intent_model",
    prediction="support_request",
    confidence=0.92,
    latency_ms=45,
    ground_truth=None  # Can be updated later
)
```

### 4. `ml_sales_demo.py`

This script provides an interactive demonstration of the ML capabilities for sales presentations, including:
- Intent recognition demo
- Sentiment analysis demo
- Email categorization demo
- Usage metrics and billing demo
- Model monitoring demo

Usage:
```bash
# Run the full demo
python ml_sales_demo.py

# Run specific components
python ml_sales_demo.py --intent
python ml_sales_demo.py --sentiment
python ml_sales_demo.py --email
python ml_sales_demo.py --usage
python ml_sales_demo.py --monitoring
```

### 5. `update_dev_plan.py`

This script updates the development plan to reflect the sales-ready status of the ML framework, including:
- Adding the commercialization strategy section
- Updating the current status and next steps
- Adding commercialization tasks to the roadmap
- Updating the change log

Usage:
```bash
python update_dev_plan.py
```

## Integration Guide

To integrate these components into your application:

1. **Configure Sales Settings**
   ```python
   from ml_sales_config import SalesConfig
   
   # Create and save a custom configuration
   config = SalesConfig.create_default()
   config.save()
   ```

2. **Add Usage Metering**
   ```python
   # For Flask applications
   from ml_usage_metering import create_flask_metering_middleware, UsageMeter
   
   meter = UsageMeter()
   create_flask_metering_middleware(app, meter, lambda req: req.headers.get('X-Client-ID'))
   ```

3. **Enable Model Monitoring**
   ```python
   from ml_monitoring import ModelMonitor, AlertConfig
   
   # Configure alerts
   alert_config = AlertConfig(
       accuracy_threshold=0.8,
       latency_threshold_ms=100.0,
       alert_channels=["log", "email"],
       recipients=["alerts@company.com"]
   )
   
   # Create and start monitor
   monitor = ModelMonitor(alert_config=alert_config)
   monitor.start()
   ```

## Pricing and Licensing

The ML Framework is available in three pricing tiers:

- **Basic**: $99.99/month
- **Professional**: $299.99/month
- **Enterprise**: $999.99/month

All tiers include a 14-day free trial and annual billing discounts.

Contact sales@guardsrobbers.com for custom enterprise pricing or to discuss partner programs.

## Support

For technical support or sales inquiries:
- Email: support@guardsrobbers.com
- Phone: (555) 123-4567
- Documentation: https://docs.guardsrobbers.com 

## How to Use

### Running the Sales Demo

The sales demo provides a comprehensive showcase of the framework's capabilities:

```bash
# Run the full demo
python ml_sales_demo.py

# Run specific components
python ml_sales_demo.py --intent     # Intent recognition only
python ml_sales_demo.py --sentiment  # Sentiment analysis only
python ml_sales_demo.py --email      # Email categorization only
python ml_sales_demo.py --usage      # Usage metrics & billing only
python ml_sales_demo.py --monitor    # Model monitoring only
```

### Pricing Tiers

The system offers three pricing tiers:

1. **Basic** ($99.99/month):
   - Intent Recognition
   - Sentiment Analysis
   - Email Categorization
   - Basic Entity Extraction
   - Email-only Support

2. **Professional** ($299.99/month):
   - All Basic features
   - Advanced Entity Extraction
   - Custom Entities
   - Model Fine-tuning
   - Priority Support (Email + Chat)
   - API Access
   - Dashboard Analytics

3. **Enterprise** ($999.99/month):
   - All Professional features
   - Custom Model Training
   - Multi-language Support
   - Advanced Analytics
   - Dedicated Support (Email + Chat + Phone)
   - SLA Guarantees

### Usage-Based Billing

Our pricing model combines base subscription fees with usage-based charges:

- **API Calls**: Base tier includes fixed number per minute, overages charged at $0.01 per call
- **Model Inferences**: First 10,000 included, overages charged at $0.001 per inference
- **Data Storage**: First 1GB included, overages charged at $0.05 per MB

## Recent Updates

### Version 1.1.0 (2025-04-05)
- Fixed billing calculation to properly handle date ranges
- Added robust error handling to usage metrics demo
- Updated configuration for enterprise tier to use numeric values instead of 'Unlimited'
- Enhanced README documentation with usage examples

## Deployment Options

The framework supports multiple deployment options:

1. **Cloud Deployment**:
   - Managed service with automatic scaling
   - 4 CPU cores, 8GB RAM minimum

2. **On-Premise Deployment**:
   - Self-hosted within your infrastructure
   - 8 CPU cores, 16GB RAM, 8GB GPU recommended

3. **Edge Deployment**:
   - Lightweight version for edge computing scenarios
   - 2 CPU cores, 4GB RAM minimum

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Initialize the configuration:
   ```bash
   python ml_sales_config.py --init
   ```

3. Run the demo:
   ```bash
   python ml_sales_demo.py
   ```

## Contact

For more information, please contact sales@guardsrobbers.com 