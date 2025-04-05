#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ML Model Monitoring Service

This module provides monitoring for ML models in production to ensure 
they maintain accuracy, performance, and reliability over time.
"""

import os
import json
import time
import logging
import threading
import queue
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable
from dataclasses import dataclass, field, asdict
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define constants
MONITOR_DATA_DIR = Path("data/monitoring")
DEFAULT_STORAGE_PATH = MONITOR_DATA_DIR / "model_metrics.json"
ALERT_THRESHOLD_MINUTES = 60  # How long to wait before sending repeat alerts

@dataclass
class ModelPrediction:
    """ML model prediction record"""
    model_id: str
    input_data: str  # Input data or reference to it
    prediction: Any  # Prediction result
    confidence: float  # Confidence score (0.0 to 1.0)
    latency_ms: float  # Prediction latency in milliseconds
    timestamp: datetime = field(default_factory=datetime.now)
    ground_truth: Optional[Any] = None  # Actual correct value if known
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional information
    id: str = field(default_factory=lambda: str(uuid.uuid4()))  # Unique identifier
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "model_id": self.model_id,
            "input_data": self.input_data,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp.isoformat(),
            "ground_truth": self.ground_truth,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelPrediction':
        """Create from dictionary"""
        return cls(
            model_id=data["model_id"],
            input_data=data["input_data"],
            prediction=data["prediction"],
            confidence=data["confidence"],
            latency_ms=data["latency_ms"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            ground_truth=data.get("ground_truth"),
            metadata=data.get("metadata", {})
        )

@dataclass
class ModelMetrics:
    """Performance metrics for a model"""
    model_id: str
    accuracy: float = 0.0
    latency_avg_ms: float = 0.0
    latency_p95_ms: float = 0.0
    latency_p99_ms: float = 0.0
    throughput_per_minute: float = 0.0
    error_rate: float = 0.0
    prediction_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "model_id": self.model_id,
            "accuracy": self.accuracy,
            "latency_avg_ms": self.latency_avg_ms,
            "latency_p95_ms": self.latency_p95_ms,
            "latency_p99_ms": self.latency_p99_ms,
            "throughput_per_minute": self.throughput_per_minute,
            "error_rate": self.error_rate,
            "prediction_count": self.prediction_count,
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelMetrics':
        """Create from dictionary"""
        return cls(
            model_id=data["model_id"],
            accuracy=data["accuracy"],
            latency_avg_ms=data["latency_avg_ms"],
            latency_p95_ms=data["latency_p95_ms"],
            latency_p99_ms=data["latency_p99_ms"],
            throughput_per_minute=data["throughput_per_minute"],
            error_rate=data["error_rate"],
            prediction_count=data["prediction_count"],
            last_updated=datetime.fromisoformat(data["last_updated"])
        )

@dataclass
class AlertConfig:
    """Configuration for model monitoring alerts"""
    accuracy_threshold: float = 0.7
    latency_threshold_ms: float = 500.0
    error_rate_threshold: float = 0.05
    check_interval_sec: int = 300  # 5 minutes
    alert_channels: List[str] = field(default_factory=lambda: ["log"])
    recipients: List[str] = field(default_factory=list)

class ModelMonitor:
    """Monitors ML model performance in production"""
    
    def __init__(
        self,
        storage_path: Union[str, Path] = DEFAULT_STORAGE_PATH,
        alert_config: Optional[AlertConfig] = None,
        max_predictions_per_model: int = 10000
    ):
        self.storage_path = Path(storage_path)
        self.alert_config = alert_config or AlertConfig()
        self.max_predictions_per_model = max_predictions_per_model
        self.predictions: Dict[str, List[ModelPrediction]] = {}
        self.metrics: Dict[str, ModelMetrics] = {}
        self.alert_history: Dict[str, datetime] = {}
        self.prediction_queue = queue.Queue()
        self.running = False
        self.monitor_thread = None
        
        # Performance optimization properties
        self.sampling_rate = 1.0  # Process all predictions by default
        self.detailed_metrics = True  # Collect detailed metrics by default
        self.batch_processing = False  # Process predictions individually by default
        self.batch_size = 1  # Process one prediction at a time by default
        
        # Ensure storage directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing metrics
        self._load_metrics()
    
    def _load_metrics(self):
        """Load metrics from storage"""
        if not self.storage_path.exists():
            logger.info(f"No metrics file found at {self.storage_path}")
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                metrics_data = json.load(f)
            
            for model_id, metrics_dict in metrics_data.items():
                self.metrics[model_id] = ModelMetrics.from_dict(metrics_dict)
            
            logger.info(f"Loaded metrics for {len(self.metrics)} models from {self.storage_path}")
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")
    
    def _save_metrics(self):
        """Save metrics to storage"""
        try:
            metrics_data = {
                model_id: metrics.to_dict()
                for model_id, metrics in self.metrics.items()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            logger.debug(f"Saved metrics for {len(self.metrics)} models to {self.storage_path}")
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def track_prediction(
        self,
        model_id: str,
        input_data: str,
        prediction: str,
        confidence: float = 1.0,
        latency_ms: float = 0.0,
        ground_truth: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Track a model prediction
        
        Args:
            model_id: Identifier for the model
            input_data: Input text or reference
            prediction: Predicted output
            confidence: Confidence score (0-1)
            latency_ms: Processing time in milliseconds
            ground_truth: Actual correct output (if known)
            metadata: Additional information
            
        Returns:
            Prediction ID
        """
        # Apply sampling - only process a fraction of predictions based on sampling rate
        if self.sampling_rate < 1.0:
            import random
            if random.random() > self.sampling_rate:
                # Skip this prediction
                return "sampled_out"
        
        prediction_id = str(uuid.uuid4())
        
        pred = ModelPrediction(
            id=prediction_id,
            model_id=model_id,
            input_data=input_data,
            prediction=prediction,
            confidence=confidence,
            latency_ms=latency_ms,
            ground_truth=ground_truth,
            metadata=metadata or {},
            timestamp=datetime.now()
        )
        
        # Add to processing queue
        self.prediction_queue.put(pred)
        
        # Start monitoring service if not running
        if not self.running:
            self.start()
        
        return prediction_id
    
    def record_ground_truth(
        self,
        model_id: str,
        input_data: str,
        ground_truth: Any
    ):
        """
        Record ground truth for a prediction
        
        Args:
            model_id: Identifier for the model
            input_data: Input data for the prediction
            ground_truth: The actual correct value
        """
        # Find matching prediction
        if model_id not in self.predictions:
            logger.warning(f"No predictions found for model {model_id}")
            return
        
        matched = False
        for pred in self.predictions[model_id]:
            if pred.input_data == input_data:  # Compare with input_data
                pred.ground_truth = ground_truth
                matched = True
                break
        
        if not matched:
            logger.warning(f"No matching prediction found for {input_data}")
        else:
            # Update metrics with new ground truth
            self._update_metrics(model_id)
    
    def _process_prediction(self, prediction: ModelPrediction):
        """Process a prediction for monitoring"""
        model_id = prediction.model_id
        
        # Initialize predictions list for model if needed
        if model_id not in self.predictions:
            self.predictions[model_id] = []
        
        # Add prediction to model's history
        self.predictions[model_id].append(prediction)
        
        # Limit the number of stored predictions
        if len(self.predictions[model_id]) > self.max_predictions_per_model:
            self.predictions[model_id] = self.predictions[model_id][-self.max_predictions_per_model:]
        
        # Update metrics for this model
        self._update_metrics(model_id)
    
    def _update_metrics(self, model_id: str):
        """Update metrics for a model based on recent predictions"""
        if model_id not in self.predictions or not self.predictions[model_id]:
            return
        
        # Get predictions for this model
        model_predictions = self.predictions[model_id]
        
        # Calculate metrics
        latencies = [p.latency_ms for p in model_predictions]
        latencies.sort()
        
        # Calculate accuracy using available ground truth
        correct = 0
        total_with_ground_truth = 0
        
        for pred in model_predictions:
            if pred.ground_truth is not None:
                total_with_ground_truth += 1
                if pred.prediction == pred.ground_truth:
                    correct += 1
        
        accuracy = correct / total_with_ground_truth if total_with_ground_truth > 0 else 0.0
        
        # For detailed metrics mode, calculate percentiles
        # For simple mode, use more efficient calculations
        if self.detailed_metrics:
            # Calculate percentiles
            p95_index = int(len(latencies) * 0.95)
            p99_index = int(len(latencies) * 0.99)
            
            latency_avg = sum(latencies) / len(latencies)
            latency_p95 = latencies[p95_index] if p95_index < len(latencies) else latencies[-1]
            latency_p99 = latencies[p99_index] if p99_index < len(latencies) else latencies[-1]
        else:
            # Simplified calculations for performance
            latency_avg = sum(latencies) / len(latencies)
            latency_p95 = latency_avg * 1.5  # Estimate
            latency_p99 = latency_avg * 2.0  # Estimate
        
        # Calculate throughput (predictions per minute)
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        recent_predictions = [p for p in model_predictions if p.timestamp >= one_minute_ago]
        throughput = len(recent_predictions)
        
        # Create or update metrics
        if model_id not in self.metrics:
            self.metrics[model_id] = ModelMetrics(model_id=model_id)
        
        metrics = self.metrics[model_id]
        metrics.accuracy = accuracy
        metrics.latency_avg_ms = latency_avg
        metrics.latency_p95_ms = latency_p95
        metrics.latency_p99_ms = latency_p99
        metrics.throughput_per_minute = throughput
        metrics.prediction_count = len(model_predictions)
        metrics.last_updated = now
        
        # Save metrics
        self._save_metrics()
        
        # Check for alerts
        self._check_alerts(model_id)
    
    def _check_alerts(self, model_id: str):
        """Check if any alerts should be triggered for a model"""
        if model_id not in self.metrics:
            return
        
        metrics = self.metrics[model_id]
        config = self.alert_config
        alerts = []
        
        # Check accuracy
        if (metrics.accuracy < config.accuracy_threshold and 
            metrics.prediction_count > 100):  # Only alert if we have enough data
            alerts.append(f"Model accuracy below threshold: {metrics.accuracy:.2f} < {config.accuracy_threshold:.2f}")
        
        # Check latency
        if metrics.latency_p95_ms > config.latency_threshold_ms:
            alerts.append(f"Model latency (P95) above threshold: {metrics.latency_p95_ms:.2f}ms > {config.latency_threshold_ms:.2f}ms")
        
        # Check error rate
        if metrics.error_rate > config.error_rate_threshold:
            alerts.append(f"Model error rate above threshold: {metrics.error_rate:.2f} > {config.error_rate_threshold:.2f}")
        
        # Send alerts if needed
        if alerts:
            # Check if we've already sent an alert recently
            alert_key = f"{model_id}_{'_'.join(a[:10] for a in alerts)}"
            now = datetime.now()
            last_alert = self.alert_history.get(alert_key)
            
            if not last_alert or (now - last_alert).total_seconds() > (ALERT_THRESHOLD_MINUTES * 60):
                self._send_alert(model_id, alerts)
                self.alert_history[alert_key] = now
    
    def _send_alert(self, model_id: str, alert_messages: List[str]):
        """Send alerts through configured channels"""
        alert_text = f"ALERT for model {model_id}:\n" + "\n".join(f"- {msg}" for msg in alert_messages)
        
        for channel in self.alert_config.alert_channels:
            if channel == "log":
                logger.warning(alert_text)
            elif channel == "email":
                self._send_email_alert(alert_text)
            elif channel == "slack":
                self._send_slack_alert(alert_text)
    
    def _send_email_alert(self, alert_text: str):
        """Send alert via email"""
        if not self.alert_config.recipients:
            logger.warning("Email alert configured but no recipients specified")
            return
        
        try:
            # This is a placeholder - implement actual email sending
            logger.info(f"Would send email to {self.alert_config.recipients}: {alert_text}")
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    def _send_slack_alert(self, alert_text: str):
        """Send alert via Slack"""
        try:
            # This is a placeholder - implement actual Slack integration
            logger.info(f"Would send Slack message: {alert_text}")
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        logger.info("Model monitoring service started")
        
        while self.running:
            try:
                # Process queued predictions
                try:
                    # Process predictions in batches if enabled
                    if self.batch_processing and self.batch_size > 1:
                        batch = []
                        try:
                            # Collect a batch of predictions
                            while len(batch) < self.batch_size:
                                prediction = self.prediction_queue.get(block=False)
                                batch.append(prediction)
                                self.prediction_queue.task_done()
                        except queue.Empty:
                            pass
                        
                        # Process the batch if we have any predictions
                        if batch:
                            # Group predictions by model_id
                            by_model = {}
                            for pred in batch:
                                if pred.model_id not in by_model:
                                    by_model[pred.model_id] = []
                                by_model[pred.model_id].append(pred)
                            
                            # Process each model's predictions
                            for model_id, model_preds in by_model.items():
                                for pred in model_preds:
                                    self._process_prediction(pred)
                    else:
                        # Process predictions individually (original behavior)
                        while True:
                            prediction = self.prediction_queue.get(block=False)
                            self._process_prediction(prediction)
                            self.prediction_queue.task_done()
                except queue.Empty:
                    pass
                
                # Save metrics periodically
                self._save_metrics()
                
                # Sleep until next check
                time.sleep(self.alert_config.check_interval_sec)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Sleep briefly before retrying
    
    def start(self):
        """Start the monitoring service"""
        if self.running:
            logger.warning("Monitor already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Started model monitoring service")
    
    def stop(self):
        """Stop the monitoring service"""
        if not self.running:
            logger.warning("Monitor not running")
            return
        
        logger.info("Stopping model monitoring service")
        self.running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        
        # Process any remaining items in queue
        try:
            while True:
                prediction = self.prediction_queue.get(block=False)
                self._process_prediction(prediction)
                self.prediction_queue.task_done()
        except queue.Empty:
            pass
        
        # Save final metrics
        self._save_metrics()
        logger.info("Model monitoring service stopped")
    
    def get_model_health(self, model_id: str) -> Dict[str, Any]:
        """
        Get health status for a model
        
        Args:
            model_id: Identifier for the model
            
        Returns:
            Dictionary with health information
        """
        if model_id not in self.metrics:
            return {
                "model_id": model_id,
                "status": "unknown",
                "message": "No metrics available for this model"
            }
        
        metrics = self.metrics[model_id]
        config = self.alert_config
        
        # Determine status
        issues = []
        
        if metrics.accuracy < config.accuracy_threshold:
            issues.append(f"Low accuracy: {metrics.accuracy:.2f} < {config.accuracy_threshold:.2f}")
        
        if metrics.latency_p95_ms > config.latency_threshold_ms:
            issues.append(f"High latency: {metrics.latency_p95_ms:.2f}ms > {config.latency_threshold_ms:.2f}ms")
        
        if metrics.error_rate > config.error_rate_threshold:
            issues.append(f"High error rate: {metrics.error_rate:.2f} > {config.error_rate_threshold:.2f}")
        
        if issues:
            status = "unhealthy"
            message = f"Found {len(issues)} issues: " + "; ".join(issues)
        else:
            status = "healthy"
            message = "All metrics within acceptable thresholds"
        
        return {
            "model_id": model_id,
            "status": status,
            "message": message,
            "metrics": metrics.to_dict(),
            "last_checked": datetime.now().isoformat()
        }
    
    def get_all_models_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Get health status for all monitored models
        
        Returns:
            Dictionary with model IDs as keys and health status as values
        """
        return {
            model_id: self.get_model_health(model_id)
            for model_id in self.metrics
        }

def create_default_monitor() -> ModelMonitor:
    """Create a monitor with default configuration"""
    config = AlertConfig(
        accuracy_threshold=0.7,
        latency_threshold_ms=500.0,
        error_rate_threshold=0.05,
        alert_channels=["log"]
    )
    
    return ModelMonitor(alert_config=config)

def update_monitoring_config(config: Dict[str, Any]) -> bool:
    """
    Update monitoring configuration for performance optimization
    
    Args:
        config: New configuration settings
        
    Returns:
        True if update was successful, False otherwise
    """
    try:
        sampling_rate = config.get('sampling_rate', 1.0)
        detailed_metrics = config.get('detailed_metrics', True)
        performance_alerts = config.get('performance_alerts', True)
        
        # Create a global monitor instance with updated settings
        monitor = create_default_monitor()
        
        # Apply sampling rate - only process a fraction of predictions for efficiency
        monitor.sampling_rate = sampling_rate
        
        # Control metrics detail level
        monitor.detailed_metrics = detailed_metrics
        
        # Enable/disable performance alerts
        monitor.alert_config.latency_alerts_enabled = performance_alerts
        
        # Adjust alert thresholds based on detailed metrics setting
        if not detailed_metrics:
            # If not using detailed metrics, make thresholds more lenient
            monitor.alert_config.latency_threshold_ms *= 1.5
            monitor.alert_config.check_interval_sec *= 2
        
        logger.info(f"Updated monitoring configuration: sampling_rate={sampling_rate}, "
                   f"detailed_metrics={detailed_metrics}, performance_alerts={performance_alerts}")
        
        return True
    except Exception as e:
        logger.error(f"Error updating monitoring configuration: {e}")
        return False

def get_system_performance_metrics() -> Dict[str, float]:
    """
    Get system-level performance metrics
    
    Returns:
        Dictionary with system metrics
    """
    metrics = {}
    
    try:
        import psutil
        # CPU metrics
        metrics['cpu_percent'] = psutil.cpu_percent(interval=0.1)
        metrics['cpu_count'] = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        metrics['memory_used_percent'] = memory.percent
        metrics['memory_available_mb'] = memory.available / (1024 * 1024)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        metrics['disk_used_percent'] = disk.percent
        metrics['disk_free_gb'] = disk.free / (1024 * 1024 * 1024)
        
        # Process metrics
        process = psutil.Process()
        metrics['process_cpu_percent'] = process.cpu_percent(interval=0.1)
        metrics['process_memory_mb'] = process.memory_info().rss / (1024 * 1024)
        metrics['process_threads'] = process.num_threads()
        
        logger.info(f"Collected system performance metrics")
        return metrics
    except ImportError:
        logger.warning("psutil not installed, using simulated system metrics")
        
        # Simulated metrics
        import random
        metrics['cpu_percent'] = 30 + random.random() * 20
        metrics['memory_used_percent'] = 40 + random.random() * 30
        metrics['disk_used_percent'] = 50 + random.random() * 20
        metrics['process_memory_mb'] = 200 + random.random() * 100
        
        return metrics
    except Exception as e:
        logger.error(f"Error getting system performance metrics: {e}")
        return {
            'cpu_percent': 0,
            'memory_used_percent': 0,
            'disk_used_percent': 0,
            'process_memory_mb': 0
        }

def optimize_monitor_performance(monitor: ModelMonitor) -> bool:
    """
    Apply performance optimizations to the monitoring system
    
    Args:
        monitor: ModelMonitor instance to optimize
        
    Returns:
        True if optimization was successful, False otherwise
    """
    try:
        # 1. Implement prediction sampling
        monitor.sampling_rate = 0.2  # Only process 20% of predictions
        
        # 2. Reduce logging frequency
        monitor.alert_config.check_interval_sec = 60  # Check less frequently
        
        # 3. Limit stored predictions
        if monitor.max_predictions_per_model > 5000:
            monitor.max_predictions_per_model = 5000
        
        # 4. Enable batch processing of predictions
        monitor.batch_processing = True
        monitor.batch_size = 10
        
        # 5. Implement efficient metric storage
        import time
        current_time = int(time.time())
        
        # Clean up old metrics (older than 7 days)
        for model_id in list(monitor.metrics.keys()):
            if hasattr(monitor.metrics[model_id], 'last_updated'):
                last_updated = monitor.metrics[model_id].last_updated
                if isinstance(last_updated, datetime):
                    age_seconds = (datetime.now() - last_updated).total_seconds()
                    if age_seconds > 7 * 24 * 60 * 60:  # 7 days
                        del monitor.metrics[model_id]
                        logger.info(f"Removed old metrics for {model_id}")
        
        logger.info("Applied performance optimizations to monitoring system")
        return True
    except Exception as e:
        logger.error(f"Error optimizing monitor performance: {e}")
        return False

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ML Model Monitoring")
    parser.add_argument('--track', help='Track a prediction for a model')
    parser.add_argument('--model', help='Model ID to check')
    parser.add_argument('--all', action='store_true', help='Check health of all models')
    parser.add_argument('--optimize', action='store_true', help='Apply performance optimizations')
    parser.add_argument('--system', action='store_true', help='Show system performance metrics')
    args = parser.parse_args()
    
    if args.track and args.model:
        monitor = create_default_monitor()
        
        # Example tracking
        monitor.track_prediction(
            model_id=args.model,
            input_data="Example input",
            prediction="example_prediction",
            confidence=0.9,
            latency_ms=50.0
        )
        
        print(f"Tracked prediction for {args.model}")
    
    elif args.model:
        monitor = create_default_monitor()
        health = monitor.get_model_health(args.model)
        
        print(f"\nModel: {args.model}")
        print(f"Status: {health['status']}")
        print(f"Message: {health['message']}")
        print("Metrics:")
        for k, v in health['metrics'].items():
            if k != 'model_id' and k != 'last_updated':
                print(f"  {k}: {v}")
    
    elif args.all:
        monitor = ModelMonitor()
        health = monitor.get_all_models_health()
        for model_id, model_health in health.items():
            print(f"\nModel: {model_id}")
            print(f"Status: {model_health['status']}")
            print(f"Message: {model_health['message']}")
            print("Metrics:")
            for k, v in model_health['metrics'].items():
                if k != 'model_id' and k != 'last_updated':
                    print(f"  {k}: {v}")
    
    elif args.optimize:
        monitor = create_default_monitor()
        success = optimize_monitor_performance(monitor)
        print(f"Performance optimization {'successful' if success else 'failed'}")
    
    elif args.system:
        metrics = get_system_performance_metrics()
        print("\nSystem Performance Metrics:")
        for k, v in metrics.items():
            print(f"  {k}: {v}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 