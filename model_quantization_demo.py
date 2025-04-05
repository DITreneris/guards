#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Model Quantization Demonstration
Shows how to use the model quantization utilities to reduce model memory footprint.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path if needed
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ml.models.model_loader import (
    IntentModelLoader, 
    SentimentModelLoader, 
    EmailCategorizationModelLoader
)
from ml.utils.model_quantization import (
    batch_quantize_models,
    compare_model_performance
)

def get_sample_data(model_type: str) -> Dict[str, Any]:
    """
    Get sample data for testing models.
    
    Args:
        model_type: Type of model to get data for
        
    Returns:
        Dictionary with test data and labels
    """
    if model_type == "intent":
        return {
            "data": [
                "Hello, how are you?",
                "I need help with my account",
                "What features does your product have?",
                "Goodbye for now",
                "I'm having an issue with login"
            ],
            "labels": ["greeting", "help", "info", "farewell", "problem"]
        }
    elif model_type == "sentiment":
        return {
            "data": [
                "I love your product, it's amazing!",
                "This doesn't work at all, very frustrating",
                "It's okay, but could be better",
                "Thank you for your help, much appreciated",
                "Why is this so complicated to use?"
            ],
            "labels": ["positive", "negative", "neutral", "positive", "negative"]
        }
    elif model_type == "email":
        return {
            "data": [
                ("Support request", "I need help with my account, please assist"),
                ("Feature suggestion", "Would be great if you could add this feature"),
                ("Bug report", "The application crashes when I click this button"),
                ("Sales inquiry", "Can you send me pricing information?"),
                ("Other", "Just wanted to say hello")
            ],
            "labels": ["support", "feature_request", "bug", "sales", "other"]
        }
    
    # Default empty data
    return {"data": [], "labels": []}

def quantize_single_model(model_type: str, bit_depth: int, weight_threshold: float) -> Dict[str, Any]:
    """
    Quantize a single model and test performance.
    
    Args:
        model_type: Type of model to quantize ("intent", "sentiment", or "email")
        bit_depth: Target bit depth for quantization
        weight_threshold: Threshold for pruning small weights
        
    Returns:
        Dictionary with quantization results
    """
    logger.info(f"Quantizing {model_type} model with {bit_depth}-bit precision")
    
    # Select appropriate loader based on model type
    if model_type == "intent":
        loader = IntentModelLoader()
        model_name = "Intent Recognition"
        prediction_fn = lambda m, x: m.predict_intent(x)
    elif model_type == "sentiment":
        loader = SentimentModelLoader()
        model_name = "Sentiment Analysis"
        prediction_fn = lambda m, x: m.analyze_sentiment(x)
    elif model_type == "email":
        loader = EmailCategorizationModelLoader()
        model_name = "Email Categorization"
        prediction_fn = lambda m, x, s: m.categorize_email(s, x)
    else:
        logger.error(f"Invalid model type: {model_type}")
        return {"error": f"Invalid model type: {model_type}"}
    
    # Check if model was loaded
    if loader.model is None:
        logger.error(f"{model_name} model not found")
        return {"error": f"{model_name} model not found"}
    
    # Get model size info before quantization
    size_before = loader.get_model_size_info()
    logger.info(f"Original model size: {size_before['original_model']['size_bytes'] / 1024:.2f} KB")
    
    # Perform quantization
    quantization_result = loader.quantize(bit_depth=bit_depth, weight_threshold=weight_threshold)
    
    # Check if quantization was successful
    if "error" in quantization_result:
        logger.error(f"Quantization failed: {quantization_result['error']}")
        return {"error": quantization_result["error"]}
    
    # Get model size info after quantization
    size_after = loader.get_model_size_info()
    logger.info(f"Quantized model size: {size_after['quantized_model']['size_bytes'] / 1024:.2f} KB")
    
    # Calculate size reduction
    if size_before["original_model"]["size_bytes"] > 0:
        size_reduction = 1.0 - (size_after["quantized_model"]["size_bytes"] / size_before["original_model"]["size_bytes"])
        logger.info(f"Size reduction: {size_reduction:.2%}")
    else:
        size_reduction = 0.0
    
    # Test with sample data if available
    performance_comparison = {}
    try:
        sample_data = get_sample_data(model_type)
        if sample_data["data"]:
            # Test original model
            logger.info("Testing original model performance...")
            original_predictions = []
            for item in sample_data["data"]:
                if model_type == "email" and isinstance(item, tuple):
                    subject, body = item
                    prediction = prediction_fn(loader, body, subject)
                else:
                    prediction = prediction_fn(loader, item)
                original_predictions.append(prediction)
            
            # Switch to quantized model
            logger.info("Switching to quantized model...")
            if loader.use_quantized_model(True):
                # Test quantized model
                logger.info("Testing quantized model performance...")
                quantized_predictions = []
                for item in sample_data["data"]:
                    if model_type == "email" and isinstance(item, tuple):
                        subject, body = item
                        prediction = prediction_fn(loader, body, subject)
                    else:
                        prediction = prediction_fn(loader, item)
                    quantized_predictions.append(prediction)
                
                # Compare predictions
                differences = 0
                for orig, quant in zip(original_predictions, quantized_predictions):
                    if orig != quant:
                        differences += 1
                
                performance_comparison = {
                    "sample_count": len(sample_data["data"]),
                    "differences": differences,
                    "difference_percent": (differences / len(sample_data["data"])) * 100 if sample_data["data"] else 0,
                    "original_predictions": original_predictions,
                    "quantized_predictions": quantized_predictions
                }
                
                logger.info(f"Prediction differences: {differences}/{len(sample_data['data'])} ({performance_comparison['difference_percent']:.2f}%)")
            else:
                logger.warning("Failed to switch to quantized model for testing")
    except Exception as e:
        logger.error(f"Error testing model performance: {e}")
        performance_comparison = {"error": str(e)}
    
    # Return to original model
    loader.use_quantized_model(False)
    
    # Prepare result summary
    return {
        "model_type": model_type,
        "model_name": model_name,
        "bit_depth": bit_depth,
        "weight_threshold": weight_threshold,
        "original_size_bytes": size_before["original_model"]["size_bytes"],
        "quantized_size_bytes": size_after["quantized_model"]["size_bytes"],
        "size_reduction_percent": size_reduction * 100,
        "performance_comparison": performance_comparison,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def batch_quantize_all_models(bit_depth: int, weight_threshold: float) -> Dict[str, Any]:
    """
    Quantize all available models.
    
    Args:
        bit_depth: Target bit depth for quantization
        weight_threshold: Threshold for pruning small weights
        
    Returns:
        Dictionary with quantization results for all models
    """
    logger.info(f"Batch quantizing all models with {bit_depth}-bit precision")
    
    results = {}
    models_to_quantize = ["intent", "sentiment", "email"]
    
    for model_type in models_to_quantize:
        logger.info(f"Processing {model_type} model...")
        result = quantize_single_model(model_type, bit_depth, weight_threshold)
        results[model_type] = result
    
    # Calculate overall statistics
    total_original_size = sum(r["original_size_bytes"] for r in results.values() if isinstance(r, dict) and "original_size_bytes" in r)
    total_quantized_size = sum(r["quantized_size_bytes"] for r in results.values() if isinstance(r, dict) and "quantized_size_bytes" in r)
    
    if total_original_size > 0:
        overall_reduction = (1 - (total_quantized_size / total_original_size)) * 100
    else:
        overall_reduction = 0
    
    results["summary"] = {
        "total_original_size_bytes": total_original_size,
        "total_quantized_size_bytes": total_quantized_size,
        "overall_size_reduction_percent": overall_reduction,
        "models_processed": len(models_to_quantize),
        "bit_depth": bit_depth,
        "weight_threshold": weight_threshold,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    logger.info(f"Overall size reduction: {overall_reduction:.2f}%")
    
    return results

def save_results(results: Dict[str, Any], output_dir: str = "data/quantization") -> str:
    """
    Save quantization results to JSON file.
    
    Args:
        results: Quantization results to save
        output_dir: Directory to save results to
        
    Returns:
        Path to saved file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename based on timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"quantization_results_{timestamp}.json"
    output_path = os.path.join(output_dir, filename)
    
    # Save results to JSON file
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Saved quantization results to {output_path}")
    
    return output_path

def print_comparison_table(results: Dict[str, Any]) -> None:
    """
    Print a comparison table of quantization results.
    
    Args:
        results: Quantization results
    """
    print("\n" + "="*80)
    print(" MODEL QUANTIZATION COMPARISON ".center(80, "="))
    print("="*80)
    
    format_str = "| {:<15} | {:>15} | {:>15} | {:>15} | {:>10} |"
    
    print(format_str.format("Model Type", "Original (KB)", "Quantized (KB)", "Reduction", "Diff (%)"))
    print("|" + "-"*17 + "|" + "-"*17 + "|" + "-"*17 + "|" + "-"*17 + "|" + "-"*12 + "|")
    
    for model_type, result in results.items():
        if model_type == "summary":
            continue
            
        if isinstance(result, dict) and "original_size_bytes" in result:
            original_kb = result["original_size_bytes"] / 1024
            quantized_kb = result["quantized_size_bytes"] / 1024
            reduction = result["size_reduction_percent"]
            
            diff_percent = "N/A"
            if "performance_comparison" in result and "difference_percent" in result["performance_comparison"]:
                diff_percent = f"{result['performance_comparison']['difference_percent']:.2f}%"
            
            print(format_str.format(
                model_type,
                f"{original_kb:.2f}",
                f"{quantized_kb:.2f}",
                f"{reduction:.2f}%",
                diff_percent
            ))
    
    # Print summary row
    if "summary" in results:
        summary = results["summary"]
        original_kb = summary["total_original_size_bytes"] / 1024
        quantized_kb = summary["total_quantized_size_bytes"] / 1024
        reduction = summary["overall_size_reduction_percent"]
        
        print("|" + "-"*17 + "|" + "-"*17 + "|" + "-"*17 + "|" + "-"*17 + "|" + "-"*12 + "|")
        print(format_str.format(
            "TOTAL",
            f"{original_kb:.2f}",
            f"{quantized_kb:.2f}",
            f"{reduction:.2f}%",
            "N/A"
        ))
    
    print("="*80)
    print(f" Bit Depth: {results['summary']['bit_depth']}-bit ".center(80, " "))
    print(f" Weight Threshold: {results['summary']['weight_threshold']} ".center(80, " "))
    print("="*80 + "\n")

def main():
    """Main function for model quantization demonstration."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Model Quantization Demonstration")
    parser.add_argument("--model", choices=["intent", "sentiment", "email", "all"], 
                       default="all", help="Model to quantize")
    parser.add_argument("--bit-depth", type=int, choices=[8, 16, 32], default=16,
                       help="Target bit depth for quantization")
    parser.add_argument("--weight-threshold", type=float, default=0.001,
                       help="Threshold for pruning small weights")
    parser.add_argument("--output-dir", type=str, default="data/quantization",
                       help="Directory to save results to")
    parser.add_argument("--no-table", action="store_true",
                       help="Don't print comparison table")
    
    args = parser.parse_args()
    
    # Perform quantization
    if args.model == "all":
        results = batch_quantize_all_models(args.bit_depth, args.weight_threshold)
    else:
        results = {
            args.model: quantize_single_model(args.model, args.bit_depth, args.weight_threshold),
            "summary": {
                "bit_depth": args.bit_depth,
                "weight_threshold": args.weight_threshold,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    
    # Save results
    save_results(results, args.output_dir)
    
    # Print comparison table
    if not args.no_table:
        print_comparison_table(results)

if __name__ == "__main__":
    main() 