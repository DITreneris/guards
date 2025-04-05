#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ML Sales Configuration

This module contains configuration settings for the ML framework in a commercial environment.
It defines pricing tiers, feature access, and system requirements for the sales-ready version.
"""

import os
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Union, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define constants
CONFIG_DIR = Path("config")
SALES_CONFIG_PATH = CONFIG_DIR / "sales_config.json"

@dataclass
class MLModelConfig:
    """Configuration for ML model deployment in production"""
    name: str
    version: str
    accuracy_threshold: float = 0.75
    latency_threshold_ms: int = 200
    memory_limit_mb: int = 512
    auto_retrain: bool = False
    daily_request_limit: Optional[int] = None
    failover_enabled: bool = True
    monitoring_interval_min: int = 15

@dataclass
class PricingTier:
    """Defines a pricing tier for the ML system"""
    name: str
    price_monthly: float
    price_yearly: float
    features: List[str]
    api_rate_limit: int  # requests per minute
    support_level: str
    max_models: int
    max_users: int
    custom_training: bool
    model_config: MLModelConfig
    
    def calculate_discount(self) -> float:
        """Calculate yearly discount percentage"""
        monthly_yearly = self.price_monthly * 12
        return round((1 - (self.price_yearly / monthly_yearly)) * 100, 1)

@dataclass
class SystemRequirements:
    """System requirements for different deployment scenarios"""
    cpu_cores: int
    ram_gb: int
    storage_gb: int
    gpu_required: bool = False
    gpu_memory_gb: Optional[int] = None
    network_bandwidth_mbps: int = 100
    supports_docker: bool = True
    supports_kubernetes: bool = False

@dataclass
class SalesConfig:
    """Main configuration class for ML sales and deployment"""
    version: str = "1.0.0"
    pricing_tiers: Dict[str, PricingTier] = field(default_factory=dict)
    system_requirements: Dict[str, SystemRequirements] = field(default_factory=dict)
    trial_period_days: int = 14
    sla_uptime_percentage: float = 99.9
    support_hours: str = "9am-5pm EST, Monday-Friday"
    emergency_support: bool = False
    refund_policy_days: int = 30
    
    def save(self, filepath: Union[str, Path] = SALES_CONFIG_PATH):
        """Save the configuration to a JSON file"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict
        config_dict = asdict(self)
        
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)
        logger.info(f"Sales configuration saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: Union[str, Path] = SALES_CONFIG_PATH) -> 'SalesConfig':
        """Load configuration from a JSON file"""
        filepath = Path(filepath)
        
        if not filepath.exists():
            logger.warning(f"Configuration file {filepath} not found, creating default")
            config = cls.create_default()
            config.save(filepath)
            return config
        
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        
        # Reconstruct nested objects
        pricing_tiers = {}
        for tier_name, tier_dict in config_dict.get('pricing_tiers', {}).items():
            model_config_dict = tier_dict.pop('model_config', {})
            model_config = MLModelConfig(**model_config_dict)
            pricing_tiers[tier_name] = PricingTier(**tier_dict, model_config=model_config)
        
        system_requirements = {}
        for env_name, req_dict in config_dict.get('system_requirements', {}).items():
            system_requirements[env_name] = SystemRequirements(**req_dict)
        
        # Create config object
        config = cls(
            version=config_dict.get('version', "1.0.0"),
            pricing_tiers=pricing_tiers,
            system_requirements=system_requirements,
            trial_period_days=config_dict.get('trial_period_days', 14),
            sla_uptime_percentage=config_dict.get('sla_uptime_percentage', 99.9),
            support_hours=config_dict.get('support_hours', "9am-5pm EST, Monday-Friday"),
            emergency_support=config_dict.get('emergency_support', False),
            refund_policy_days=config_dict.get('refund_policy_days', 30)
        )
        
        logger.info(f"Sales configuration loaded from {filepath}")
        return config
    
    @classmethod
    def create_default(cls) -> 'SalesConfig':
        """Create default sales configuration"""
        # Create model configs
        basic_model = MLModelConfig(
            name="basic_ml_suite",
            version="1.0.0",
            accuracy_threshold=0.7,
            latency_threshold_ms=300,
            memory_limit_mb=256,
            auto_retrain=False,
            daily_request_limit=1000,
            failover_enabled=True,
            monitoring_interval_min=30
        )
        
        professional_model = MLModelConfig(
            name="professional_ml_suite",
            version="1.0.0",
            accuracy_threshold=0.8,
            latency_threshold_ms=200,
            memory_limit_mb=512,
            auto_retrain=True,
            daily_request_limit=5000,
            failover_enabled=True,
            monitoring_interval_min=15
        )
        
        enterprise_model = MLModelConfig(
            name="enterprise_ml_suite",
            version="1.0.0",
            accuracy_threshold=0.85,
            latency_threshold_ms=100,
            memory_limit_mb=1024,
            auto_retrain=True,
            daily_request_limit=None,  # Unlimited
            failover_enabled=True,
            monitoring_interval_min=5
        )
        
        # Create pricing tiers
        pricing_tiers = {
            "basic": PricingTier(
                name="Basic",
                price_monthly=99.99,
                price_yearly=999.99,
                features=[
                    "Intent Recognition",
                    "Sentiment Analysis",
                    "Email Categorization",
                    "Basic Entity Extraction",
                    "Standard Support"
                ],
                api_rate_limit=60,
                support_level="Email only",
                max_models=2,
                max_users=5,
                custom_training=False,
                model_config=basic_model
            ),
            "professional": PricingTier(
                name="Professional",
                price_monthly=299.99,
                price_yearly=2999.99,
                features=[
                    "Intent Recognition",
                    "Sentiment Analysis",
                    "Email Categorization",
                    "Advanced Entity Extraction",
                    "Custom Entities",
                    "Model Fine-tuning",
                    "Priority Support",
                    "API Access",
                    "Dashboard Analytics"
                ],
                api_rate_limit=300,
                support_level="Email + Chat",
                max_models=5,
                max_users=20,
                custom_training=True,
                model_config=professional_model
            ),
            "enterprise": PricingTier(
                name="Enterprise",
                price_monthly=999.99,
                price_yearly=9999.99,
                features=[
                    "Intent Recognition",
                    "Sentiment Analysis",
                    "Email Categorization",
                    "Advanced Entity Extraction",
                    "Custom Entities",
                    "Model Fine-tuning",
                    "Priority Support",
                    "API Access",
                    "Dashboard Analytics",
                    "Custom Model Training",
                    "Multi-language Support",
                    "Advanced Analytics",
                    "Dedicated Support",
                    "SLA Guarantees"
                ],
                api_rate_limit=1000,
                support_level="Email + Chat + Phone",
                max_models=999,  # Use a large number instead of 'Unlimited'
                max_users=999,   # Use a large number instead of 'Unlimited'
                custom_training=True,
                model_config=enterprise_model
            )
        }
        
        # Create system requirements
        system_requirements = {
            "cloud": SystemRequirements(
                cpu_cores=4,
                ram_gb=8,
                storage_gb=50,
                gpu_required=False,
                network_bandwidth_mbps=100,
                supports_docker=True,
                supports_kubernetes=True
            ),
            "on_premise": SystemRequirements(
                cpu_cores=8,
                ram_gb=16,
                storage_gb=100,
                gpu_required=True,
                gpu_memory_gb=8,
                network_bandwidth_mbps=1000,
                supports_docker=True,
                supports_kubernetes=True
            ),
            "edge": SystemRequirements(
                cpu_cores=2,
                ram_gb=4,
                storage_gb=20,
                gpu_required=False,
                network_bandwidth_mbps=10,
                supports_docker=True,
                supports_kubernetes=False
            )
        }
        
        return cls(
            version="1.0.0",
            pricing_tiers=pricing_tiers,
            system_requirements=system_requirements,
            trial_period_days=14,
            sla_uptime_percentage=99.9,
            support_hours="9am-5pm EST, Monday-Friday",
            emergency_support=False,
            refund_policy_days=30
        )

def get_sales_config() -> SalesConfig:
    """Get the current sales configuration"""
    return SalesConfig.load()

def print_pricing_summary():
    """Print a summary of the pricing tiers for quick reference"""
    config = get_sales_config()
    
    print("\n=== GUARDS & ROBBERS ML PRICING SUMMARY ===\n")
    
    for tier_name, tier in config.pricing_tiers.items():
        print(f"{tier.name} Tier")
        print(f"  Monthly: ${tier.price_monthly:.2f}")
        print(f"  Yearly: ${tier.price_yearly:.2f} (Save {tier.calculate_discount()}%)")
        print(f"  Features: {', '.join(tier.features[:3])}...")
        print(f"  API Rate Limit: {tier.api_rate_limit} requests/minute")
        print(f"  Support Level: {tier.support_level}")
        print()
    
    print(f"Trial Period: {config.trial_period_days} days")
    print(f"SLA Uptime: {config.sla_uptime_percentage}%")
    print(f"Support Hours: {config.support_hours}")
    print(f"Emergency Support: {'Yes' if config.emergency_support else 'No'}")
    print(f"Refund Policy: {config.refund_policy_days} days")

def main():
    """Main function to manage sales configuration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ML Sales Configuration Tool")
    parser.add_argument('--init', action='store_true', help='Initialize default configuration')
    parser.add_argument('--summary', action='store_true', help='Print summary of pricing tiers')
    args = parser.parse_args()
    
    if args.init:
        config = SalesConfig.create_default()
        config.save()
        print(f"Default sales configuration created at {SALES_CONFIG_PATH}")
    
    if args.summary:
        print_pricing_summary()
    
    if not any([args.init, args.summary]):
        print_pricing_summary()

if __name__ == "__main__":
    main() 