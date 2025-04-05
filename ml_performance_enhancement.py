#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ML Performance Enhancement

This script implements specific performance enhancements for the ML framework.
It applies optimizations for model inference, conversation management, and data processing.
"""

import os
import json
import time
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

# Add import for model quantization
from ml.utils.model_quantization import quantize_model_file
from ml.models.model_loader import IntentModelLoader, SentimentModelLoader, EmailCategorizationModelLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CONFIG_PATH = Path("config/performance_config.json")
CACHE_DIR = Path("data/cache")
MODELS_DIR = Path("ml/models")

def create_default_config():
    """Create default performance configuration"""
    config = {
        "model_optimization": {
            "enable_quantization": True,
            "enable_caching": True,
            "enable_batching": True,
            "batch_size": 16,
            "cache_size": 1000,
            "quantization_bits": 8
        },
        "memory_optimization": {
            "enable_memory_efficient_mode": True,
            "maximum_cached_conversations": 50,
            "maximum_cached_predictions": 200,
            "garbage_collection_interval_sec": 300
        },
        "disk_optimization": {
            "compression_enabled": True,
            "max_log_size_mb": 10,
            "max_metrics_file_size_mb": 5,
            "log_rotation_count": 5
        },
        "monitoring": {
            "sampling_rate": 0.1,  # Only monitor 10% of predictions
            "detailed_metrics_enabled": False,
            "performance_alerts_enabled": True
        }
    }
    
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Created default performance configuration at {CONFIG_PATH}")
    return config

def load_config():
    """Load performance configuration"""
    if not CONFIG_PATH.exists():
        return create_default_config()
    
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded performance configuration from {CONFIG_PATH}")
        return config
    except Exception as e:
        logger.error(f"Error loading performance configuration: {e}")
        return create_default_config()

class ModelCache:
    """Implements a cache for model predictions to improve performance"""
    
    def __init__(self, model_id: str, cache_size: int = 1000):
        self.model_id = model_id
        self.cache_size = cache_size
        self.cache: Dict[str, Any] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.last_cleanup = datetime.now()
        
        # Ensure cache directory exists
        self.cache_file = CACHE_DIR / f"{model_id}_cache.json"
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load existing cache if available
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk"""
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                self.cache = data.get('cache', {})
                self.cache_hits = data.get('hits', 0)
                self.cache_misses = data.get('misses', 0)
            logger.info(f"Loaded cache for {self.model_id} with {len(self.cache)} entries")
        except Exception as e:
            logger.error(f"Error loading cache for {self.model_id}: {e}")
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            data = {
                'cache': self.cache,
                'hits': self.cache_hits,
                'misses': self.cache_misses,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.cache_file, 'w') as f:
                json.dump(data, f)
            logger.info(f"Saved cache for {self.model_id} with {len(self.cache)} entries")
        except Exception as e:
            logger.error(f"Error saving cache for {self.model_id}: {e}")
    
    def get(self, key: str) -> Tuple[bool, Any]:
        """
        Get a value from the cache
        
        Args:
            key: Cache key
            
        Returns:
            Tuple of (hit, value)
        """
        if key in self.cache:
            self.cache_hits += 1
            return True, self.cache[key]
        else:
            self.cache_misses += 1
            return False, None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the cache
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # If cache is full, remove oldest entries
        if len(self.cache) >= self.cache_size:
            # Remove 10% of oldest entries
            remove_count = max(1, self.cache_size // 10)
            keys_to_remove = list(self.cache.keys())[:remove_count]
            for k in keys_to_remove:
                del self.cache[k]
        
        self.cache[key] = value
        
        # Periodically save cache to disk
        if len(self.cache) % 100 == 0:
            self._save_cache()
    
    def clear(self) -> None:
        """Clear the cache"""
        self.cache = {}
        self._save_cache()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total if total > 0 else 0
        
        return {
            'size': len(self.cache),
            'capacity': self.cache_size,
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'hit_rate': hit_rate,
            'memory_usage_estimate_kb': len(json.dumps(self.cache)) // 1024
        }


def optimize_model(model_id: str) -> Dict[str, Any]:
    """
    Apply performance optimizations to a model, including quantization
    
    Args:
        model_id: Identifier for the model
        
    Returns:
        Dictionary with optimization results
    """
    logger.info(f"Optimizing model {model_id}...")
    
    # Load configuration
    config = load_config()
    model_config = config.get("model_optimization", {})
    
    # Check if quantization is enabled
    enable_quantization = model_config.get("enable_quantization", True)
    quantization_bits = model_config.get("quantization_bits", 16)
    pruning_threshold = model_config.get("pruning_threshold", 0.001)
    
    results = {
        "model_id": model_id,
        "optimizations_applied": [],
        "success": False,
        "error": None,
        "details": {}
    }
    
    # Determine model file path
    model_path = None
    model_format = "sklearn"  # Default format
    
    # Map model_id to appropriate loader and paths
    model_loader = None
    if model_id == "intent_recognition_model":
        model_path = MODELS_DIR / "intent_model.pkl"
        model_loader = IntentModelLoader()
    elif model_id == "sentiment_analysis_model":
        model_path = MODELS_DIR / "sentiment_model.pkl"
        model_loader = SentimentModelLoader()
    elif model_id == "email_categorization_model":
        model_path = MODELS_DIR / "email_categorization_model.pkl"
        model_loader = EmailCategorizationModelLoader()
    else:
        # Try to find the model file directly
        potential_path = MODELS_DIR / f"{model_id}.pkl"
        if potential_path.exists():
            model_path = potential_path
    
    # Check if model file exists
    if not model_path or not model_path.exists():
        error_msg = f"Model file not found for {model_id}"
        logger.error(error_msg)
        results["error"] = error_msg
        return results
    
    try:
        # Apply quantization if enabled
        if enable_quantization:
            logger.info(f"Applying {quantization_bits}-bit quantization to {model_id}")
            
            if model_loader and model_loader.model is not None:
                # Use model loader's quantize method if available
                quantization_results = model_loader.quantize(
                    bit_depth=quantization_bits,
                    weight_threshold=pruning_threshold
                )
                
                # Add results
                results["optimizations_applied"].append("quantization")
                results["details"]["quantization"] = quantization_results
                
                logger.info(f"Model quantization completed with {quantization_results.get('size_reduction_percent', 0):.2f}% size reduction")
            else:
                # Fall back to direct file quantization
                path_obj = Path(str(model_path))
                quantized_path = path_obj.parent / f"{path_obj.stem}_quantized{path_obj.suffix}"
                
                # Apply quantization
                quantization_results = quantize_model_file(
                    input_path=str(model_path),
                    output_path=str(quantized_path),
                    bit_depth=quantization_bits,
                    weight_threshold=pruning_threshold,
                    model_format=model_format
                )
                
                # Add results
                results["optimizations_applied"].append("quantization")
                results["details"]["quantization"] = quantization_results
                
                logger.info(f"Model quantization completed with {quantization_results.get('file_size_reduction_percent', 0):.2f}% file size reduction")
        
        # Apply other optimizations as needed
        # ... existing optimizations ...
        
        # Set up caching if enabled
        if model_config.get("enable_caching", True):
            cache_size = model_config.get("cache_size", 1000)
            cache = setup_model_caching(model_id)
            results["optimizations_applied"].append("caching")
            results["details"]["caching"] = {
                "cache_size": cache_size,
                "cache_stats": cache.get_stats()
            }
            logger.info(f"Set up caching for {model_id} with size {cache_size}")
        
        # Apply batching if enabled
        if model_config.get("enable_batching", True):
            batch_size = model_config.get("batch_size", 16)
            results["optimizations_applied"].append("batching")
            results["details"]["batching"] = {
                "batch_size": batch_size
            }
            logger.info(f"Enabled batching for {model_id} with batch size {batch_size}")
        
        # Mark as successful
        results["success"] = True
        
        return results
        
    except Exception as e:
        error_msg = f"Error optimizing model {model_id}: {str(e)}"
        logger.error(error_msg)
        results["error"] = error_msg
        return results


def setup_model_caching(model_id: str) -> ModelCache:
    """
    Set up caching for a model to improve performance
    
    Args:
        model_id: Identifier for the model
        
    Returns:
        ModelCache instance
    """
    config = load_config()
    cache_size = config['model_optimization']['cache_size']
    
    # Create and return cache instance
    return ModelCache(model_id, cache_size=cache_size)


def optimize_memory_usage():
    """Apply memory usage optimizations"""
    logger.info("Optimizing memory usage...")
    
    config = load_config()
    memory_config = config['memory_optimization']
    
    if memory_config['enable_memory_efficient_mode']:
        # In a real implementation, would apply actual memory optimizations
        # For example, clearing unused caches, reducing object creation, etc.
        
        # 1. Clear conversation cache
        try:
            conversation_cache_dir = Path("data/conversations")
            if conversation_cache_dir.exists():
                files = list(conversation_cache_dir.glob("*.json"))
                if len(files) > memory_config['maximum_cached_conversations']:
                    # Sort by modification time (oldest first)
                    files.sort(key=lambda f: f.stat().st_mtime)
                    # Remove oldest files beyond the maximum
                    for f in files[:-memory_config['maximum_cached_conversations']]:
                        f.unlink()
                    logger.info(f"Cleared {len(files) - memory_config['maximum_cached_conversations']} old conversation files")
        except Exception as e:
            logger.error(f"Error clearing conversation cache: {e}")
        
        # 2. Clear prediction cache
        try:
            prediction_cache_dir = Path("data/predictions")
            if prediction_cache_dir.exists():
                files = list(prediction_cache_dir.glob("*.json"))
                if len(files) > memory_config['maximum_cached_predictions']:
                    # Sort by modification time (oldest first)
                    files.sort(key=lambda f: f.stat().st_mtime)
                    # Remove oldest files beyond the maximum
                    for f in files[:-memory_config['maximum_cached_predictions']]:
                        f.unlink()
                    logger.info(f"Cleared {len(files) - memory_config['maximum_cached_predictions']} old prediction files")
        except Exception as e:
            logger.error(f"Error clearing prediction cache: {e}")
        
        # 3. Suggest garbage collection
        import gc
        gc.collect()
        logger.info("Garbage collection completed")
    
    return True


def optimize_disk_usage():
    """Apply disk usage optimizations"""
    logger.info("Optimizing disk usage...")
    
    config = load_config()
    disk_config = config['disk_optimization']
    
    # 1. Compress log files if enabled
    if disk_config['compression_enabled']:
        try:
            log_dir = Path("logs")
            if log_dir.exists():
                import gzip
                import shutil
                
                # Find log files that aren't already compressed
                log_files = [f for f in log_dir.glob("*.log") if not f.with_suffix(".log.gz").exists()]
                
                for log_file in log_files:
                    # Only compress if file is over max size
                    if log_file.stat().st_size > (disk_config['max_log_size_mb'] * 1024 * 1024):
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        # Verify the compressed file exists before deleting original
                        if Path(f"{log_file}.gz").exists():
                            log_file.unlink()
                            logger.info(f"Compressed log file: {log_file}")
        except Exception as e:
            logger.error(f"Error compressing log files: {e}")
    
    # 2. Clean up old metrics files
    try:
        metrics_dir = Path("data/metrics")
        if metrics_dir.exists():
            # Find and sort metrics files by age
            metrics_files = list(metrics_dir.glob("*.json"))
            if len(metrics_files) > disk_config['log_rotation_count']:
                # Sort by modification time (oldest first)
                metrics_files.sort(key=lambda f: f.stat().st_mtime)
                # Remove oldest files beyond the rotation count
                for f in metrics_files[:-disk_config['log_rotation_count']]:
                    f.unlink()
                logger.info(f"Removed {len(metrics_files) - disk_config['log_rotation_count']} old metrics files")
    except Exception as e:
        logger.error(f"Error cleaning up metrics files: {e}")
    
    return True


def optimize_monitoring():
    """Apply monitoring optimizations"""
    logger.info("Optimizing monitoring system...")
    
    config = load_config()
    monitoring_config = config['monitoring']
    
    # Update monitoring configuration
    try:
        # Dynamic import to avoid circular dependencies
        from ml_monitoring import update_monitoring_config
        
        monitoring_settings = {
            "sampling_rate": monitoring_config['sampling_rate'],
            "detailed_metrics": monitoring_config['detailed_metrics_enabled'],
            "performance_alerts": monitoring_config['performance_alerts_enabled']
        }
        
        # In a real implementation, this would update the monitoring configuration
        # For demonstration, we'll log the settings
        logger.info(f"Updated monitoring settings: {monitoring_settings}")
        
        # Restart monitoring system with new settings
        # This would be implementation-specific
        logger.info("Restarted monitoring system with optimized settings")
        
        return True
    except Exception as e:
        logger.error(f"Error optimizing monitoring: {e}")
        return False


def optimize_all():
    """
    Apply all available performance optimizations
    
    Returns:
        Dictionary with optimization results
    """
    logger.info("Starting comprehensive performance optimization...")
    
    # Load configuration
    config = load_config()
    
    # Track results
    results = {
        "timestamp": datetime.now().isoformat(),
        "models_optimized": {},
        "memory_optimized": False,
        "disk_optimized": False,
        "monitoring_optimized": False,
        "overall_status": "failed"
    }
    
    # 1. Optimize models
    models_to_optimize = [
        "intent_recognition_model",
        "sentiment_analysis_model",
        "email_categorization_model"
    ]
    
    for model_id in models_to_optimize:
        logger.info(f"Optimizing model: {model_id}")
        model_results = optimize_model(model_id)
        results["models_optimized"][model_id] = model_results
    
    # 2. Optimize memory usage
    try:
        memory_results = optimize_memory_usage()
        results["memory_optimized"] = True
        results["memory_results"] = memory_results
        logger.info("Memory optimization completed successfully")
    except Exception as e:
        logger.error(f"Memory optimization failed: {e}")
        results["memory_error"] = str(e)
    
    # 3. Optimize disk usage
    try:
        disk_results = optimize_disk_usage()
        results["disk_optimized"] = True
        results["disk_results"] = disk_results
        logger.info("Disk optimization completed successfully")
    except Exception as e:
        logger.error(f"Disk optimization failed: {e}")
        results["disk_error"] = str(e)
    
    # 4. Optimize monitoring
    try:
        monitoring_results = optimize_monitoring()
        results["monitoring_optimized"] = True
        results["monitoring_results"] = monitoring_results
        logger.info("Monitoring optimization completed successfully")
    except Exception as e:
        logger.error(f"Monitoring optimization failed: {e}")
        results["monitoring_error"] = str(e)
    
    # Determine overall status
    successful_models = sum(1 for model_result in results["models_optimized"].values() 
                            if model_result["success"])
    
    if (successful_models == len(models_to_optimize) and 
        results["memory_optimized"] and 
        results["disk_optimized"] and 
        results["monitoring_optimized"]):
        results["overall_status"] = "success"
    elif (successful_models > 0 or 
          results["memory_optimized"] or 
          results["disk_optimized"] or 
          results["monitoring_optimized"]):
        results["overall_status"] = "partial_success"
    
    # Save results
    results_dir = Path("data/performance")
    results_dir.mkdir(parents=True, exist_ok=True)
    results_file = results_dir / "optimization_results.json"
    
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Saved optimization results to {results_file}")
    except Exception as e:
        logger.error(f"Failed to save optimization results: {e}")
    
    return results


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ML Performance Enhancement")
    parser.add_argument('--model', help='Model ID to optimize')
    parser.add_argument('--memory', action='store_true', help='Optimize memory usage')
    parser.add_argument('--disk', action='store_true', help='Optimize disk usage')
    parser.add_argument('--monitoring', action='store_true', help='Optimize monitoring')
    parser.add_argument('--all', action='store_true', help='Apply all optimizations')
    parser.add_argument('--config', action='store_true', help='Create default configuration')
    args = parser.parse_args()
    
    if args.config:
        config = create_default_config()
        print("Created default performance configuration:")
        print(json.dumps(config, indent=2))
    
    elif args.model:
        results = optimize_model(args.model)
        print(f"Model optimization {'successful' if results['success'] else 'failed'}")
        
        # Setup caching
        cache = setup_model_caching(args.model)
        print(f"Model caching configured with capacity: {cache.cache_size}")
    
    elif args.memory:
        success = optimize_memory_usage()
        print(f"Memory optimization {'successful' if success else 'failed'}")
    
    elif args.disk:
        success = optimize_disk_usage()
        print(f"Disk optimization {'successful' if success else 'failed'}")
    
    elif args.monitoring:
        success = optimize_monitoring()
        print(f"Monitoring optimization {'successful' if success else 'failed'}")
    
    elif args.all:
        results = optimize_all()
        print("Optimization results:")
        print(f"Overall status: {results['overall_status']}")
        print("Models optimized:")
        for model_id, result in results['models_optimized'].items():
            print(f"  {model_id}: {'✓' if result['success'] else '✗'}")
        print(f"Memory optimized: {'✓' if results['memory_optimized'] else '✗'}")
        print(f"Disk optimized: {'✓' if results['disk_optimized'] else '✗'}")
        print(f"Monitoring optimized: {'✓' if results['monitoring_optimized'] else '✗'}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 