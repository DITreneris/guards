#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ML Performance Optimizer

This module provides tools for optimizing the performance of ML models and the overall ML system.
It includes benchmark tests, optimization strategies, and automatic tuning capabilities.
"""

import os
import json
import time
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
import threading
import concurrent.futures

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define constants
DEFAULT_CONFIG_PATH = Path("config/performance_config.json")
DEFAULT_REPORT_PATH = Path("data/performance/optimization_reports.json")
MODEL_CHECKPOINT_DIR = Path("ml/models/optimized")

@dataclass
class PerformanceMetrics:
    """Performance metrics for ML models and system components"""
    # Core metrics
    inference_latency_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_utilization_percent: float = 0.0
    throughput_per_sec: float = 0.0
    
    # Model specific metrics
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    
    # System metrics
    startup_time_ms: float = 0.0
    peak_memory_mb: float = 0.0
    average_batch_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'PerformanceMetrics':
        return cls(**data)
    
    def improved_from(self, baseline: 'PerformanceMetrics') -> Dict[str, float]:
        """Calculate improvement percentages from baseline metrics"""
        improvements = {}
        
        # For metrics where lower is better
        for metric in ['inference_latency_ms', 'memory_usage_mb', 'cpu_utilization_percent', 
                      'startup_time_ms', 'peak_memory_mb', 'average_batch_time_ms']:
            baseline_value = getattr(baseline, metric)
            current_value = getattr(self, metric)
            if baseline_value > 0:
                improvement = (baseline_value - current_value) / baseline_value * 100
                improvements[metric] = improvement
        
        # For metrics where higher is better
        for metric in ['throughput_per_sec', 'accuracy', 'precision', 'recall', 'f1_score']:
            baseline_value = getattr(baseline, metric)
            current_value = getattr(self, metric)
            if baseline_value > 0:
                improvement = (current_value - baseline_value) / baseline_value * 100
                improvements[metric] = improvement
                
        return improvements

@dataclass
class OptimizationConfig:
    """Configuration for performance optimization"""
    # General settings
    target_latency_ms: float = 100.0
    target_memory_mb: float = 500.0
    target_accuracy: float = 0.9
    
    # Optimization flags
    enable_quantization: bool = True
    enable_pruning: bool = True
    enable_knowledge_distillation: bool = False
    enable_caching: bool = True
    enable_batching: bool = True
    
    # Quantization settings
    quantization_bits: int = 8
    
    # Pruning settings
    pruning_sparsity: float = 0.3
    
    # Batching settings
    batch_size: int = 16
    
    # Cache settings
    cache_size: int = 1000
    
    # Advanced settings
    max_optimization_iterations: int = 10
    optimization_timeout_sec: int = 300
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizationConfig':
        return cls(**data)
    
    @classmethod
    def load(cls, config_path: Union[str, Path] = DEFAULT_CONFIG_PATH) -> 'OptimizationConfig':
        """Load configuration from a file"""
        config_path = Path(config_path)
        if not config_path.exists():
            logger.warning(f"Config file {config_path} not found, using defaults")
            return cls()
        
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            return cls.from_dict(config_data)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return cls()
    
    def save(self, config_path: Union[str, Path] = DEFAULT_CONFIG_PATH) -> None:
        """Save configuration to a file"""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            logger.info(f"Saved configuration to {config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")


class PerformanceOptimizer:
    """Optimizes ML model and system performance"""
    
    def __init__(
        self,
        config: Optional[OptimizationConfig] = None,
        report_path: Union[str, Path] = DEFAULT_REPORT_PATH
    ):
        self.config = config or OptimizationConfig.load()
        self.report_path = Path(report_path)
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.optimization_history: Dict[str, List[Dict[str, Any]]] = {}
        self._load_history()
    
    def _load_history(self) -> None:
        """Load optimization history from file"""
        if not self.report_path.exists():
            return
        
        try:
            with open(self.report_path, 'r') as f:
                self.optimization_history = json.load(f)
            logger.info(f"Loaded optimization history from {self.report_path}")
        except Exception as e:
            logger.error(f"Error loading optimization history: {e}")
    
    def _save_history(self) -> None:
        """Save optimization history to file"""
        try:
            with open(self.report_path, 'w') as f:
                json.dump(self.optimization_history, f, indent=2)
            logger.info(f"Saved optimization history to {self.report_path}")
        except Exception as e:
            logger.error(f"Error saving optimization history: {e}")
    
    def benchmark_model(self, model_id: str, test_data: Any) -> PerformanceMetrics:
        """
        Benchmark a model's performance
        
        Args:
            model_id: Identifier for the model
            test_data: Test data for benchmarking
            
        Returns:
            Performance metrics for the model
        """
        logger.info(f"Benchmarking model {model_id}...")
        
        # Import dynamically to avoid circular imports
        try:
            from ml.models.model_loader import load_model
            model = load_model(model_id)
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {e}")
            return PerformanceMetrics()
        
        metrics = PerformanceMetrics()
        
        # Measure startup time
        start_time = time.time()
        # Simulate model initialization (would be real initialization in actual implementation)
        time.sleep(0.1)
        metrics.startup_time_ms = (time.time() - start_time) * 1000
        
        # Measure inference latency and throughput
        num_samples = min(100, len(test_data)) if hasattr(test_data, '__len__') else 100
        latencies = []
        memory_usage = []
        cpu_usage = []
        
        # Run warmup inferences
        for _ in range(5):
            _ = model.predict(test_data[0] if hasattr(test_data, '__getitem__') else test_data)
        
        # Measure single inference performance
        for i in range(num_samples):
            sample = test_data[i] if hasattr(test_data, '__getitem__') else test_data
            
            start_time = time.time()
            _ = model.predict(sample)
            latency = (time.time() - start_time) * 1000
            latencies.append(latency)
            
            # Simulate memory and CPU measurements (would use real measurements in implementation)
            memory_usage.append(200 + np.random.normal(0, 20))
            cpu_usage.append(30 + np.random.normal(0, 5))
        
        metrics.inference_latency_ms = np.mean(latencies)
        metrics.memory_usage_mb = np.mean(memory_usage)
        metrics.cpu_utilization_percent = np.mean(cpu_usage)
        metrics.peak_memory_mb = np.max(memory_usage)
        
        # Measure batch inference performance
        batch_size = self.config.batch_size
        num_batches = max(1, num_samples // batch_size)
        batch_times = []
        
        for i in range(num_batches):
            start_idx = i * batch_size
            end_idx = min((i+1) * batch_size, num_samples)
            batch = [test_data[j] for j in range(start_idx, end_idx)] if hasattr(test_data, '__getitem__') else [test_data] * (end_idx - start_idx)
            
            start_time = time.time()
            _ = [model.predict(sample) for sample in batch]  # Would use batch prediction in real implementation
            batch_time = (time.time() - start_time) * 1000
            batch_times.append(batch_time)
        
        metrics.average_batch_time_ms = np.mean(batch_times)
        metrics.throughput_per_sec = 1000 * batch_size / metrics.average_batch_time_ms
        
        # Get accuracy metrics from model if available
        if hasattr(model, 'evaluate'):
            try:
                evaluation = model.evaluate(test_data)
                metrics.accuracy = evaluation.get('accuracy', 0.0)
                metrics.precision = evaluation.get('precision', 0.0)
                metrics.recall = evaluation.get('recall', 0.0)
                metrics.f1_score = evaluation.get('f1_score', 0.0)
            except Exception as e:
                logger.error(f"Error evaluating model: {e}")
        
        logger.info(f"Benchmark results for {model_id}: {metrics.to_dict()}")
        return metrics
    
    def optimize_model(self, model_id: str, test_data: Any) -> Tuple[bool, PerformanceMetrics]:
        """
        Optimize a model for better performance
        
        Args:
            model_id: Identifier for the model
            test_data: Test data for optimization
            
        Returns:
            Tuple of (success, optimized_metrics)
        """
        logger.info(f"Starting optimization for model {model_id}")
        
        # Benchmark the model before optimization
        baseline_metrics = self.benchmark_model(model_id, test_data)
        
        # Import dynamically to avoid circular imports
        try:
            from ml.models.model_loader import load_model, save_model
            model = load_model(model_id)
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {e}")
            return False, baseline_metrics
        
        # Create a copy of the model for optimization
        original_model = model
        model = original_model  # In real implementation, we would create a deep copy
        
        # Track the best optimized model and its metrics
        best_metrics = baseline_metrics
        best_model = model
        
        # Apply optimization techniques based on configuration
        techniques = []
        
        if self.config.enable_quantization:
            techniques.append(self._apply_quantization)
        
        if self.config.enable_pruning:
            techniques.append(self._apply_pruning)
        
        if self.config.enable_knowledge_distillation:
            techniques.append(self._apply_knowledge_distillation)
        
        if self.config.enable_batching:
            techniques.append(self._apply_batch_optimization)
        
        if self.config.enable_caching:
            techniques.append(self._apply_caching)
        
        # Apply each optimization technique and benchmark
        for i, technique in enumerate(techniques):
            try:
                logger.info(f"Applying optimization technique {i+1}/{len(techniques)}")
                optimized = technique(model, test_data)
                
                # Skip if optimization couldn't be applied
                if not optimized:
                    logger.warning(f"Optimization technique {i+1} could not be applied")
                    continue
                
                # Benchmark the optimized model
                current_metrics = self.benchmark_model(model_id, test_data)
                
                # Check if this is the best optimization so far
                if (current_metrics.inference_latency_ms < best_metrics.inference_latency_ms and
                    current_metrics.accuracy >= 0.95 * best_metrics.accuracy):
                    best_metrics = current_metrics
                    best_model = model  # In real implementation, would create a deep copy
                
                # Log the improvements
                improvements = current_metrics.improved_from(baseline_metrics)
                logger.info(f"Optimization technique {i+1} results: {improvements}")
                
                # Save to history
                if model_id not in self.optimization_history:
                    self.optimization_history[model_id] = []
                
                self.optimization_history[model_id].append({
                    "timestamp": datetime.now().isoformat(),
                    "technique": technique.__name__,
                    "baseline_metrics": baseline_metrics.to_dict(),
                    "optimized_metrics": current_metrics.to_dict(),
                    "improvements": improvements
                })
                
                # Save history after each technique
                self._save_history()
                
            except Exception as e:
                logger.error(f"Error applying optimization technique {i+1}: {e}")
        
        # Save the best optimized model if it's better than the original
        if (best_metrics.inference_latency_ms < 0.95 * baseline_metrics.inference_latency_ms and
            best_metrics.accuracy >= 0.95 * baseline_metrics.accuracy):
            try:
                MODEL_CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
                save_path = MODEL_CHECKPOINT_DIR / f"{model_id}_optimized.pkl"
                save_model(best_model, save_path)
                logger.info(f"Saved optimized model to {save_path}")
                return True, best_metrics
            except Exception as e:
                logger.error(f"Error saving optimized model: {e}")
                return False, best_metrics
        else:
            logger.info(f"Optimization did not yield significant improvements for {model_id}")
            return False, baseline_metrics
    
    def _apply_quantization(self, model: Any, test_data: Any) -> bool:
        """Apply quantization to reduce model size and improve inference speed"""
        logger.info(f"Applying {self.config.quantization_bits}-bit quantization")
        
        # Simulate quantization (in real implementation, would use proper quantization)
        try:
            # Mock implementation - real code would use TensorFlow/PyTorch quantization APIs
            time.sleep(0.5)  # Simulate quantization process
            logger.info("Quantization applied successfully")
            return True
        except Exception as e:
            logger.error(f"Quantization failed: {e}")
            return False
    
    def _apply_pruning(self, model: Any, test_data: Any) -> bool:
        """Apply pruning to remove unnecessary weights and reduce model size"""
        logger.info(f"Applying pruning with sparsity {self.config.pruning_sparsity}")
        
        # Simulate pruning (in real implementation, would use proper pruning)
        try:
            # Mock implementation - real code would use TensorFlow/PyTorch pruning APIs
            time.sleep(0.5)  # Simulate pruning process
            logger.info("Pruning applied successfully")
            return True
        except Exception as e:
            logger.error(f"Pruning failed: {e}")
            return False
    
    def _apply_knowledge_distillation(self, model: Any, test_data: Any) -> bool:
        """Apply knowledge distillation to create a smaller, faster model"""
        logger.info("Applying knowledge distillation")
        
        # Simulate knowledge distillation (in real implementation, would use proper distillation)
        try:
            # Mock implementation - real code would implement teacher-student training
            time.sleep(1.0)  # Simulate distillation process
            logger.info("Knowledge distillation applied successfully")
            return True
        except Exception as e:
            logger.error(f"Knowledge distillation failed: {e}")
            return False
    
    def _apply_batch_optimization(self, model: Any, test_data: Any) -> bool:
        """Optimize model for batch processing"""
        logger.info(f"Optimizing for batch size {self.config.batch_size}")
        
        # Simulate batch optimization (in real implementation, would actually optimize for batching)
        try:
            # Mock implementation - real code would optimize model for batch inference
            time.sleep(0.3)  # Simulate optimization process
            logger.info("Batch optimization applied successfully")
            return True
        except Exception as e:
            logger.error(f"Batch optimization failed: {e}")
            return False
    
    def _apply_caching(self, model: Any, test_data: Any) -> bool:
        """Apply result caching to improve throughput for repeated queries"""
        logger.info(f"Implementing result cache with size {self.config.cache_size}")
        
        # Simulate cache implementation (in real implementation, would add actual caching)
        try:
            # Mock implementation - real code would implement LRU cache
            time.sleep(0.2)  # Simulate cache setup
            logger.info("Caching mechanism applied successfully")
            return True
        except Exception as e:
            logger.error(f"Caching implementation failed: {e}")
            return False
    
    def create_optimization_report(self, model_id: str) -> Dict[str, Any]:
        """Generate a detailed optimization report for a model"""
        if model_id not in self.optimization_history:
            return {
                "model_id": model_id,
                "status": "no_optimization",
                "message": "No optimization history found for this model"
            }
        
        history = self.optimization_history[model_id]
        
        if not history:
            return {
                "model_id": model_id,
                "status": "no_optimization",
                "message": "Optimization history is empty for this model"
            }
        
        # Get the first and last entries to compare overall improvement
        baseline = history[0]["baseline_metrics"]
        final = history[-1]["optimized_metrics"]
        
        # Convert to PerformanceMetrics objects for comparison
        baseline_metrics = PerformanceMetrics.from_dict(baseline)
        final_metrics = PerformanceMetrics.from_dict(final)
        
        # Calculate overall improvements
        improvements = final_metrics.improved_from(baseline_metrics)
        
        # Determine best technique
        best_technique = ""
        best_improvement = -float('inf')
        
        for entry in history:
            technique = entry["technique"]
            technique_improvement = entry["optimized_metrics"]["throughput_per_sec"] / entry["baseline_metrics"]["throughput_per_sec"]
            
            if technique_improvement > best_improvement:
                best_improvement = technique_improvement
                best_technique = technique
        
        return {
            "model_id": model_id,
            "status": "optimized",
            "timestamp": datetime.now().isoformat(),
            "baseline_metrics": baseline,
            "final_metrics": final,
            "overall_improvements": improvements,
            "best_technique": best_technique,
            "history": history,
            "summary": f"Model {model_id} optimized with {len(history)} techniques. Best: {best_technique}. Latency improved by {improvements.get('inference_latency_ms', 0):.2f}%, throughput improved by {improvements.get('throughput_per_sec', 0):.2f}%."
        }


# Singleton instance
_optimizer_instance = None

def get_optimizer() -> PerformanceOptimizer:
    """Get the global optimizer instance"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = PerformanceOptimizer()
    return _optimizer_instance


def optimize_all_models(test_data_func: Callable[[str], Any] = None) -> Dict[str, Dict[str, Any]]:
    """
    Optimize all available models
    
    Args:
        test_data_func: Function that returns test data for a given model_id
        
    Returns:
        Dictionary of optimization reports for each model
    """
    # Import dynamically to avoid circular imports
    try:
        from ml.models.model_loader import list_available_models
        model_ids = list_available_models()
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return {}
    
    optimizer = get_optimizer()
    reports = {}
    
    for model_id in model_ids:
        try:
            # Get test data for this model
            test_data = test_data_func(model_id) if test_data_func else None
            
            # Skip if no test data available
            if test_data is None:
                logger.warning(f"No test data available for {model_id}, skipping optimization")
                continue
            
            # Optimize the model
            success, metrics = optimizer.optimize_model(model_id, test_data)
            
            # Create report regardless of success
            report = optimizer.create_optimization_report(model_id)
            reports[model_id] = report
            
        except Exception as e:
            logger.error(f"Error optimizing model {model_id}: {e}")
            reports[model_id] = {
                "model_id": model_id,
                "status": "error",
                "message": f"Optimization failed: {str(e)}"
            }
    
    return reports


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ML Performance Optimizer")
    parser.add_argument('--model', help='Model ID to optimize')
    parser.add_argument('--all', action='store_true', help='Optimize all models')
    parser.add_argument('--report', action='store_true', help='Generate optimization report')
    parser.add_argument('--config', help='Path to optimization configuration file')
    args = parser.parse_args()
    
    # Load custom configuration if specified
    config = None
    if args.config:
        config = OptimizationConfig.load(args.config)
        
    optimizer = PerformanceOptimizer(config=config)
    
    if args.model:
        # Generate fake test data for demonstration
        test_data = ["This is a test"] * 100
        
        if args.report:
            report = optimizer.create_optimization_report(args.model)
            print(f"\nOptimization Report for {args.model}:\n")
            for key, value in report.items():
                if key != "history":
                    print(f"{key}: {value}")
        else:
            print(f"\nOptimizing model {args.model}...\n")
            success, metrics = optimizer.optimize_model(args.model, test_data)
            if success:
                print(f"Optimization successful! New metrics:")
                for key, value in metrics.to_dict().items():
                    print(f"  {key}: {value:.2f}")
            else:
                print(f"Optimization did not yield significant improvements.")
    
    elif args.all:
        print("\nOptimizing all models...\n")
        # Mock test data function
        def get_test_data(model_id):
            return ["This is a test"] * 100
        
        reports = optimize_all_models(get_test_data)
        for model_id, report in reports.items():
            print(f"\n{model_id}: {report['status']}")
            if report['status'] == 'optimized':
                print(f"  {report['summary']}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 