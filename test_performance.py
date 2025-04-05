#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Performance Test Script

This script tests the performance of the ML framework with and without optimizations.
It provides benchmarks to quantify the improvements made by the optimization system.
"""

import os
import time
import logging
import random
from datetime import datetime
from pathlib import Path
import argparse
from typing import Dict, List, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import performance enhancement modules
try:
    from ml_performance_enhancement import optimize_memory_usage, optimize_disk_usage, optimize_monitoring
    from ml_monitoring import ModelMonitor, create_default_monitor, optimize_monitor_performance, get_system_performance_metrics
    OPTIMIZATION_AVAILABLE = True
except ImportError:
    logger.warning("Performance optimization modules not available")
    OPTIMIZATION_AVAILABLE = False

# Define test configurations
TEST_INPUTS = [
    "How do I configure the firewall?",
    "What's the pricing for enterprise plan?",
    "My network is under attack!",
    "Can you explain the security features?",
    "I'd like to upgrade my subscription",
    "Is there a free trial available?",
    "How secure is the cloud storage?",
    "What happens if there's a breach?",
    "Do you offer 24/7 support?",
    "How quickly can you respond to incidents?"
]

def measure_execution_time(func, *args, **kwargs) -> Tuple[float, Any]:
    """
    Measure the execution time of a function
    
    Args:
        func: Function to measure
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        Tuple of (execution_time, result)
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    execution_time = time.time() - start_time
    return execution_time, result

def test_monitor_performance(iterations: int = 1000, optimize: bool = False) -> Dict[str, float]:
    """
    Test the performance of the monitoring system
    
    Args:
        iterations: Number of predictions to process
        optimize: Whether to apply optimizations
        
    Returns:
        Dictionary with performance metrics
    """
    if not OPTIMIZATION_AVAILABLE:
        logger.warning("Optimization modules not available, skipping test")
        return {}
    
    # Create monitor
    monitor = create_default_monitor()
    
    # Apply optimizations if requested
    if optimize:
        optimize_monitor_performance(monitor)
        logger.info("Applied monitor performance optimizations")
    
    # Measure prediction tracking performance
    start_time = time.time()
    model_id = "test_model"
    
    for i in range(iterations):
        input_text = random.choice(TEST_INPUTS)
        prediction = "support" if "help" in input_text or "attack" in input_text else "sales"
        confidence = 0.7 + random.random() * 0.3
        latency = 20 + random.random() * 100
        
        monitor.track_prediction(
            model_id=model_id,
            input_data=f"test_{i}_{input_text[:10]}",
            prediction=prediction,
            confidence=confidence,
            latency_ms=latency
        )
        
        # Add ground truth for some predictions
        if i % 10 == 0:
            monitor.record_ground_truth(
                model_id=model_id,
                input_data=f"test_{i}_{input_text[:10]}",
                ground_truth=prediction if random.random() > 0.2 else ("support" if prediction == "sales" else "sales")
            )
    
    total_time = time.time() - start_time
    avg_time_per_prediction = total_time / iterations * 1000  # In milliseconds
    
    # Get health check performance
    health_check_time, health = measure_execution_time(monitor.get_model_health, model_id)
    
    # Get system metrics
    metrics_collection_time, _ = measure_execution_time(get_system_performance_metrics)
    
    # Prepare results
    results = {
        "total_time_sec": total_time,
        "avg_time_per_prediction_ms": avg_time_per_prediction,
        "health_check_time_sec": health_check_time,
        "metrics_collection_time_sec": metrics_collection_time,
        "predictions_per_second": iterations / total_time,
        "optimized": optimize
    }
    
    logger.info(f"Monitor performance test results ({iterations} iterations, optimized={optimize}):")
    for key, value in results.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.4f}")
        else:
            logger.info(f"  {key}: {value}")
    
    return results

def test_memory_optimization() -> Dict[str, float]:
    """
    Test memory optimization performance
    
    Returns:
        Dictionary with performance metrics
    """
    if not OPTIMIZATION_AVAILABLE:
        logger.warning("Optimization modules not available, skipping test")
        return {}
    
    # Measure memory usage before optimization
    before_metrics = get_system_performance_metrics()
    
    # Apply memory optimization
    optimization_time, _ = measure_execution_time(optimize_memory_usage)
    
    # Measure memory usage after optimization
    after_metrics = get_system_performance_metrics()
    
    # Calculate improvements
    memory_improvement = before_metrics.get('memory_used_percent', 0) - after_metrics.get('memory_used_percent', 0)
    
    results = {
        "optimization_time_sec": optimization_time,
        "memory_used_before_percent": before_metrics.get('memory_used_percent', 0),
        "memory_used_after_percent": after_metrics.get('memory_used_percent', 0),
        "memory_improvement_percent": memory_improvement
    }
    
    logger.info("Memory optimization test results:")
    for key, value in results.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.4f}")
        else:
            logger.info(f"  {key}: {value}")
    
    return results

def test_disk_optimization() -> Dict[str, float]:
    """
    Test disk optimization performance
    
    Returns:
        Dictionary with performance metrics
    """
    if not OPTIMIZATION_AVAILABLE:
        logger.warning("Optimization modules not available, skipping test")
        return {}
    
    # Measure disk usage before optimization
    before_metrics = get_system_performance_metrics()
    
    # Apply disk optimization
    optimization_time, _ = measure_execution_time(optimize_disk_usage)
    
    # Measure disk usage after optimization
    after_metrics = get_system_performance_metrics()
    
    # Calculate improvements
    disk_improvement = before_metrics.get('disk_used_percent', 0) - after_metrics.get('disk_used_percent', 0)
    
    results = {
        "optimization_time_sec": optimization_time,
        "disk_used_before_percent": before_metrics.get('disk_used_percent', 0),
        "disk_used_after_percent": after_metrics.get('disk_used_percent', 0),
        "disk_improvement_percent": disk_improvement
    }
    
    logger.info("Disk optimization test results:")
    for key, value in results.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.4f}")
        else:
            logger.info(f"  {key}: {value}")
    
    return results

def run_full_optimization_test() -> Dict[str, Any]:
    """
    Run full set of optimization tests
    
    Returns:
        Dictionary with all test results
    """
    logger.info("Starting full optimization test suite")
    
    # Test monitor performance without optimization
    standard_monitor_results = test_monitor_performance(iterations=500, optimize=False)
    
    # Test monitor performance with optimization
    optimized_monitor_results = test_monitor_performance(iterations=500, optimize=True)
    
    # Test memory optimization
    memory_results = test_memory_optimization()
    
    # Test disk optimization
    disk_results = test_disk_optimization()
    
    # Calculate overall improvements
    monitor_speedup = 0
    if standard_monitor_results.get('avg_time_per_prediction_ms', 0) > 0:
        monitor_speedup = (
            standard_monitor_results.get('avg_time_per_prediction_ms', 0) - 
            optimized_monitor_results.get('avg_time_per_prediction_ms', 0)
        ) / standard_monitor_results.get('avg_time_per_prediction_ms', 0) * 100
    
    # Compile full results
    results = {
        "timestamp": datetime.now().isoformat(),
        "standard_monitor": standard_monitor_results,
        "optimized_monitor": optimized_monitor_results,
        "memory_optimization": memory_results,
        "disk_optimization": disk_results,
        "system_metrics": get_system_performance_metrics(),
        "summary": {
            "monitor_speedup_percent": monitor_speedup,
            "memory_improvement_percent": memory_results.get('memory_improvement_percent', 0),
            "disk_improvement_percent": disk_results.get('disk_improvement_percent', 0)
        }
    }
    
    # Save results
    results_dir = Path("data/performance")
    results_dir.mkdir(parents=True, exist_ok=True)
    results_file = results_dir / f"optimization_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    import json
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved test results to {results_file}")
    
    # Print summary
    print("\nPerformance Optimization Test Summary:")
    print(f"Monitor speed improvement: {monitor_speedup:.2f}%")
    print(f"Memory usage improvement: {memory_results.get('memory_improvement_percent', 0):.2f}%")
    print(f"Disk usage improvement: {disk_results.get('disk_improvement_percent', 0):.2f}%")
    
    # Print monitor throughput
    std_throughput = standard_monitor_results.get('predictions_per_second', 0)
    opt_throughput = optimized_monitor_results.get('predictions_per_second', 0)
    print(f"\nMonitor throughput (predictions/second):")
    print(f"  Standard: {std_throughput:.2f}")
    print(f"  Optimized: {opt_throughput:.2f}")
    
    return results

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Performance Test Script")
    parser.add_argument('--monitor', action='store_true', help='Test monitor performance')
    parser.add_argument('--memory', action='store_true', help='Test memory optimization')
    parser.add_argument('--disk', action='store_true', help='Test disk optimization')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--iterations', type=int, default=1000, help='Number of iterations for tests')
    args = parser.parse_args()
    
    if args.monitor:
        print("\n=== Standard Monitor Performance ===")
        test_monitor_performance(iterations=args.iterations, optimize=False)
        
        print("\n=== Optimized Monitor Performance ===")
        test_monitor_performance(iterations=args.iterations, optimize=True)
    
    elif args.memory:
        print("\n=== Memory Optimization Performance ===")
        test_memory_optimization()
    
    elif args.disk:
        print("\n=== Disk Optimization Performance ===")
        test_disk_optimization()
    
    elif args.all:
        print("\n=== Full Optimization Test Suite ===")
        run_full_optimization_test()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 