"""
Guards & Robbers ML Growth Control Module

This module coordinates all ML components to ensure balanced, sustainable growth
by monitoring metrics, controlling optimization parameters, and providing
feedback mechanisms.

Version: 1.0.0
Created: May 16, 2025
"""

import logging
import datetime
import json
from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ml_growth_control.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ml_growth_control")

# Constants
GROWTH_THRESHOLDS = {
    "aggressive": {
        "lead_quality_threshold": 0.3,
        "personalization_intensity": 0.8,
        "optimization_rate": 0.1
    },
    "balanced": {
        "lead_quality_threshold": 0.5,
        "personalization_intensity": 0.6,
        "optimization_rate": 0.05
    },
    "conservative": {
        "lead_quality_threshold": 0.7,
        "personalization_intensity": 0.4,
        "optimization_rate": 0.02
    }
}

@dataclass
class GrowthMetrics:
    """Data class for storing current growth metrics"""
    lead_conversion_rate: float
    lead_quality_score: float
    bounce_rate: float
    time_on_site: float
    pages_per_session: float
    newsletter_subscription_rate: float
    personalization_impact: float
    timestamp: datetime.datetime = datetime.datetime.now()

class GrowthAlert:
    """Alert generated when metrics exceed thresholds"""
    def __init__(self, 
                 metric_name: str, 
                 current_value: float, 
                 threshold: float, 
                 severity: str,
                 timestamp: datetime.datetime = datetime.datetime.now()):
        self.metric_name = metric_name
        self.current_value = current_value
        self.threshold = threshold
        self.severity = severity
        self.timestamp = timestamp

    def to_dict(self) -> Dict:
        return {
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat()
        }

class MLGrowthControlModule:
    """
    Central control system for managing ML-driven growth.
    
    This module:
    1. Monitors key growth metrics
    2. Adjusts ML model parameters based on growth targets
    3. Generates alerts for anomalies
    4. Provides throttle mechanisms for controlled growth
    5. Implements feedback loops between ML systems and business metrics
    """
    
    def __init__(self, growth_strategy: str = "balanced"):
        """
        Initialize the ML Growth Control Module
        
        Args:
            growth_strategy: Strategy setting (aggressive, balanced, conservative)
        """
        self.growth_strategy = growth_strategy
        self.thresholds = GROWTH_THRESHOLDS[growth_strategy]
        self.metrics_history: List[GrowthMetrics] = []
        self.alerts: List[GrowthAlert] = []
        self.manual_review_queue: List[Dict] = []
        self.last_threshold_adjustment = datetime.datetime.now()
        
        # Model control parameters
        self.lead_scoring_params = {
            "quality_threshold": self.thresholds["lead_quality_threshold"],
            "confidence_threshold": 0.75,
            "review_threshold": 0.9
        }
        
        self.personalization_params = {
            "intensity": self.thresholds["personalization_intensity"],
            "diversity_factor": 0.3,
            "exploration_rate": 0.2
        }
        
        self.optimization_params = {
            "learning_rate": self.thresholds["optimization_rate"],
            "max_change_percent": 0.1,
            "rollout_percentage": 0.2
        }
        
        logger.info(f"ML Growth Control Module initialized with {growth_strategy} strategy")
    
    def update_metrics(self, new_metrics: GrowthMetrics) -> None:
        """
        Update the growth metrics and trigger control adjustments
        
        Args:
            new_metrics: Latest metrics from analytics system
        """
        self.metrics_history.append(new_metrics)
        
        # Keep only last 30 days of metrics for memory efficiency
        if len(self.metrics_history) > 30:
            self.metrics_history = self.metrics_history[-30:]
        
        # Check for anomalies and generate alerts
        self._detect_anomalies(new_metrics)
        
        # Adjust control parameters based on new metrics
        self._adjust_control_parameters(new_metrics)
        
        logger.info(f"Growth metrics updated: lead_conversion_rate={new_metrics.lead_conversion_rate:.2f}")
    
    def _detect_anomalies(self, metrics: GrowthMetrics) -> None:
        """
        Detect anomalies in metrics and generate alerts
        
        Args:
            metrics: Current metrics to check for anomalies
        """
        # Check if we have enough history for anomaly detection
        if len(self.metrics_history) < 3:
            return
        
        # Calculate means and standard deviations for key metrics
        conv_rates = [m.lead_conversion_rate for m in self.metrics_history[:-1]]
        mean_conv_rate = np.mean(conv_rates)
        std_conv_rate = np.std(conv_rates)
        
        # Check for anomalies (>2 standard deviations)
        if abs(metrics.lead_conversion_rate - mean_conv_rate) > 2 * std_conv_rate:
            severity = "high" if metrics.lead_conversion_rate < mean_conv_rate else "medium"
            alert = GrowthAlert(
                metric_name="lead_conversion_rate",
                current_value=metrics.lead_conversion_rate,
                threshold=mean_conv_rate,
                severity=severity
            )
            self.alerts.append(alert)
            logger.warning(f"Anomaly detected: {alert.to_dict()}")
    
    def _adjust_control_parameters(self, metrics: GrowthMetrics) -> None:
        """
        Adjust control parameters based on current metrics
        
        Args:
            metrics: Current metrics used for adjustment
        """
        # Ensure we don't adjust too frequently (once per day at most)
        now = datetime.datetime.now()
        if (now - self.last_threshold_adjustment).days < 1:
            return
        
        # Adjust lead quality threshold based on conversion rate trend
        if len(self.metrics_history) > 7:
            recent_conv_rates = [m.lead_conversion_rate for m in self.metrics_history[-7:]]
            trend = recent_conv_rates[-1] - recent_conv_rates[0]
            
            # If conversion rate is declining, increase quality threshold
            if trend < -0.01:
                self.lead_scoring_params["quality_threshold"] = min(
                    0.9, 
                    self.lead_scoring_params["quality_threshold"] + 0.05
                )
                logger.info(f"Increased lead quality threshold to {self.lead_scoring_params['quality_threshold']:.2f}")
            
            # If conversion rate is stable or increasing, we can be slightly more permissive
            elif trend > 0.01:
                self.lead_scoring_params["quality_threshold"] = max(
                    0.3, 
                    self.lead_scoring_params["quality_threshold"] - 0.03
                )
                logger.info(f"Decreased lead quality threshold to {self.lead_scoring_params['quality_threshold']:.2f}")
        
        # Adjust personalization intensity based on engagement metrics
        if metrics.bounce_rate > 0.45:  # High bounce rate
            self.personalization_params["intensity"] = min(0.9, self.personalization_params["intensity"] + 0.1)
            self.personalization_params["exploration_rate"] = min(0.3, self.personalization_params["exploration_rate"] + 0.05)
            logger.info(f"Increased personalization intensity to {self.personalization_params['intensity']:.2f}")
        
        self.last_threshold_adjustment = now
    
    def get_lead_scoring_parameters(self) -> Dict:
        """
        Get current lead scoring parameters for the lead scoring model
        
        Returns:
            Dictionary of parameters for lead scoring model
        """
        return self.lead_scoring_params
    
    def get_personalization_parameters(self) -> Dict:
        """
        Get current personalization parameters for the content personalization model
        
        Returns:
            Dictionary of parameters for personalization model
        """
        return self.personalization_params
    
    def get_optimization_parameters(self) -> Dict:
        """
        Get current optimization parameters for the conversion optimization model
        
        Returns:
            Dictionary of parameters for optimization model
        """
        return self.optimization_params
    
    def add_to_manual_review_queue(self, item_type: str, item_data: Dict, priority: str = "medium") -> None:
        """
        Add an item to the manual review queue
        
        Args:
            item_type: Type of item (lead, content, experiment)
            item_data: Data for the item to review
            priority: Priority (high, medium, low)
        """
        self.manual_review_queue.append({
            "type": item_type,
            "data": item_data,
            "priority": priority,
            "timestamp": datetime.datetime.now().isoformat()
        })
        logger.info(f"Added {item_type} to manual review queue with {priority} priority")
    
    def get_manual_review_queue(self, limit: int = 100) -> List[Dict]:
        """
        Get items from the manual review queue
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List of items for manual review
        """
        # Sort by priority and timestamp
        sorted_queue = sorted(
            self.manual_review_queue,
            key=lambda x: (
                0 if x["priority"] == "high" else 1 if x["priority"] == "medium" else 2,
                x["timestamp"]
            )
        )
        return sorted_queue[:limit]
    
    def change_growth_strategy(self, new_strategy: str) -> None:
        """
        Change the overall growth strategy
        
        Args:
            new_strategy: New strategy (aggressive, balanced, conservative)
        """
        if new_strategy not in GROWTH_THRESHOLDS:
            raise ValueError(f"Invalid growth strategy: {new_strategy}")
        
        self.growth_strategy = new_strategy
        self.thresholds = GROWTH_THRESHOLDS[new_strategy]
        
        # Apply new thresholds to all parameter sets
        self.lead_scoring_params["quality_threshold"] = self.thresholds["lead_quality_threshold"]
        self.personalization_params["intensity"] = self.thresholds["personalization_intensity"]
        self.optimization_params["learning_rate"] = self.thresholds["optimization_rate"]
        
        logger.info(f"Growth strategy changed to {new_strategy}")
    
    def get_growth_status_report(self) -> Dict:
        """
        Generate a comprehensive growth status report
        
        Returns:
            Dictionary with current status and recommendations
        """
        # Use only recent metrics
        recent_metrics = self.metrics_history[-7:] if len(self.metrics_history) >= 7 else self.metrics_history
        
        if not recent_metrics:
            return {"status": "insufficient_data"}
        
        # Calculate key trends
        lead_conv_rates = [m.lead_conversion_rate for m in recent_metrics]
        lead_quality_scores = [m.lead_quality_score for m in recent_metrics]
        
        lead_conv_trend = lead_conv_rates[-1] - lead_conv_rates[0] if len(lead_conv_rates) > 1 else 0
        lead_quality_trend = lead_quality_scores[-1] - lead_quality_scores[0] if len(lead_quality_scores) > 1 else 0
        
        # Generate growth status
        if lead_conv_trend > 0.02 and lead_quality_trend > 0.05:
            growth_status = "healthy_growth"
        elif lead_conv_trend > 0.02 and lead_quality_trend <= 0:
            growth_status = "quantity_over_quality"
        elif lead_conv_trend <= 0 and lead_quality_trend > 0.05:
            growth_status = "quality_over_quantity"
        elif lead_conv_trend <= 0 and lead_quality_trend <= 0:
            growth_status = "declining_performance"
        else:
            growth_status = "stable"
        
        # Generate recommendations
        recommendations = []
        if growth_status == "quantity_over_quality":
            recommendations.append({
                "action": "increase_quality_threshold",
                "description": "Increase lead quality threshold to improve lead quality",
                "current_value": self.lead_scoring_params["quality_threshold"],
                "recommended_value": min(0.9, self.lead_scoring_params["quality_threshold"] + 0.1)
            })
        elif growth_status == "quality_over_quantity":
            recommendations.append({
                "action": "decrease_quality_threshold",
                "description": "Decrease lead quality threshold to increase lead volume",
                "current_value": self.lead_scoring_params["quality_threshold"],
                "recommended_value": max(0.3, self.lead_scoring_params["quality_threshold"] - 0.1)
            })
        elif growth_status == "declining_performance":
            recommendations.append({
                "action": "increase_exploration_rate",
                "description": "Increase content exploration rate to discover new effective content",
                "current_value": self.personalization_params["exploration_rate"],
                "recommended_value": min(0.4, self.personalization_params["exploration_rate"] + 0.1)
            })
        
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "growth_status": growth_status,
            "metrics": {
                "lead_conversion_rate": recent_metrics[-1].lead_conversion_rate,
                "lead_quality_score": recent_metrics[-1].lead_quality_score,
                "lead_conversion_trend": lead_conv_trend,
                "lead_quality_trend": lead_quality_trend
            },
            "current_strategy": self.growth_strategy,
            "recommendations": recommendations,
            "alerts": [alert.to_dict() for alert in self.alerts[-5:]], # Last 5 alerts
            "review_queue_size": len(self.manual_review_queue)
        }
        
    def save_state(self, filepath: str) -> None:
        """
        Save the current state of the growth control module
        
        Args:
            filepath: Path to save the state file
        """
        state = {
            "growth_strategy": self.growth_strategy,
            "lead_scoring_params": self.lead_scoring_params,
            "personalization_params": self.personalization_params,
            "optimization_params": self.optimization_params,
            "last_threshold_adjustment": self.last_threshold_adjustment.isoformat(),
            "metrics_history": [
                {
                    "lead_conversion_rate": m.lead_conversion_rate,
                    "lead_quality_score": m.lead_quality_score,
                    "bounce_rate": m.bounce_rate,
                    "time_on_site": m.time_on_site,
                    "pages_per_session": m.pages_per_session,
                    "newsletter_subscription_rate": m.newsletter_subscription_rate,
                    "personalization_impact": m.personalization_impact,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in self.metrics_history
            ],
            "alerts": [alert.to_dict() for alert in self.alerts],
            "version": "1.0.0"
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"Growth control state saved to {filepath}")
    
    @classmethod
    def load_state(cls, filepath: str) -> 'MLGrowthControlModule':
        """
        Load a saved state
        
        Args:
            filepath: Path to the state file
            
        Returns:
            MLGrowthControlModule instance with restored state
        """
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        # Create instance with saved growth strategy
        instance = cls(growth_strategy=state.get("growth_strategy", "balanced"))
        
        # Restore parameters
        instance.lead_scoring_params = state.get("lead_scoring_params", instance.lead_scoring_params)
        instance.personalization_params = state.get("personalization_params", instance.personalization_params)
        instance.optimization_params = state.get("optimization_params", instance.optimization_params)
        
        # Restore last_threshold_adjustment
        instance.last_threshold_adjustment = datetime.datetime.fromisoformat(
            state.get("last_threshold_adjustment", datetime.datetime.now().isoformat())
        )
        
        # Restore metrics history
        instance.metrics_history = [
            GrowthMetrics(
                lead_conversion_rate=m["lead_conversion_rate"],
                lead_quality_score=m["lead_quality_score"],
                bounce_rate=m["bounce_rate"],
                time_on_site=m["time_on_site"],
                pages_per_session=m["pages_per_session"],
                newsletter_subscription_rate=m["newsletter_subscription_rate"],
                personalization_impact=m["personalization_impact"],
                timestamp=datetime.datetime.fromisoformat(m["timestamp"])
            )
            for m in state.get("metrics_history", [])
        ]
        
        # Restore alerts
        instance.alerts = [
            GrowthAlert(
                metric_name=a["metric_name"],
                current_value=a["current_value"],
                threshold=a["threshold"],
                severity=a["severity"],
                timestamp=datetime.datetime.fromisoformat(a["timestamp"])
            )
            for a in state.get("alerts", [])
        ]
        
        logger.info(f"Growth control state loaded from {filepath}")
        return instance


# Usage example
if __name__ == "__main__":
    # Initialize the control module
    growth_control = MLGrowthControlModule(growth_strategy="balanced")
    
    # Example metrics update
    metrics = GrowthMetrics(
        lead_conversion_rate=0.045,
        lead_quality_score=0.72,
        bounce_rate=0.38,
        time_on_site=125.0,  # seconds
        pages_per_session=2.3,
        newsletter_subscription_rate=0.028,
        personalization_impact=0.15
    )
    
    growth_control.update_metrics(metrics)
    
    # Get parameters for ML models
    lead_params = growth_control.get_lead_scoring_parameters()
    print(f"Lead scoring parameters: {lead_params}")
    
    # Generate status report
    status_report = growth_control.get_growth_status_report()
    print(f"Growth status: {status_report['growth_status']}")
    
    # Change growth strategy
    growth_control.change_growth_strategy("aggressive")
    
    # Save state
    growth_control.save_state("growth_control_state.json") 