#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Model Quantization Utility
Provides functions for quantizing ML models to reduce memory footprint.
"""

import os
import pickle
import logging
import numpy as np
from typing import Any, Dict, Optional, Tuple, List, Union
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelQuantizer:
    """
    Utility class for quantizing machine learning models to reduce memory footprint.
    
    This class provides methods to quantize models by reducing the precision of 
    floating point values, pruning small weights, and applying other techniques
    to reduce model size while maintaining acceptable performance.
    """
    
    def __init__(self, 
                 bit_depth: int = 16, 
                 weight_threshold: float = 0.001,
                 use_dynamic_quantization: bool = True):
        """
        Initialize the model quantizer.
        
        Args:
            bit_depth: Target bit depth for quantization (8, 16, or 32)
            weight_threshold: Threshold for pruning small weights
            use_dynamic_quantization: Whether to use dynamic quantization
        """
        self.bit_depth = bit_depth
        self.weight_threshold = weight_threshold
        self.use_dynamic_quantization = use_dynamic_quantization
        
        # Validate bit depth
        if bit_depth not in [8, 16, 32]:
            logger.warning(f"Unsupported bit depth: {bit_depth}. Using 16 bits instead.")
            self.bit_depth = 16
        
        # Set dtype based on bit depth
        if bit_depth == 8:
            self.float_dtype = np.float16  # Actually using float16 even for int8 target
            self.int_dtype = np.int8
        elif bit_depth == 16:
            self.float_dtype = np.float16
            self.int_dtype = np.int16
        else:
            self.float_dtype = np.float32
            self.int_dtype = np.int32
            
    def quantize_model(self, 
                      model: Any,
                      model_format: str = "pickle",
                      calibration_data: Optional[Any] = None) -> Tuple[Any, Dict[str, Any]]:
        """
        Quantize a machine learning model to reduce memory footprint.
        
        Args:
            model: The model to quantize
            model_format: The format of the model ('pickle', 'sklearn', 'custom')
            calibration_data: Optional data for calibrating the quantization
            
        Returns:
            Tuple of (quantized model, quantization statistics)
        """
        logger.info(f"Starting model quantization with {self.bit_depth}-bit precision")
        
        # Get model size before quantization
        original_size = self._get_model_size(model)
        
        # Select quantization method based on model format
        if model_format == "pickle":
            quantized_model = self._quantize_pickle_model(model)
        elif model_format == "sklearn":
            quantized_model = self._quantize_sklearn_model(model, calibration_data)
        elif model_format == "custom":
            quantized_model = self._quantize_custom_model(model, calibration_data)
        else:
            logger.error(f"Unsupported model format: {model_format}")
            return model, {"error": "Unsupported model format"}
        
        # Get model size after quantization
        quantized_size = self._get_model_size(quantized_model)
        size_reduction = 1.0 - (quantized_size / original_size) if original_size > 0 else 0.0
        
        statistics = {
            "original_size_bytes": original_size,
            "quantized_size_bytes": quantized_size,
            "size_reduction_percent": size_reduction * 100,
            "bit_depth": self.bit_depth,
            "weight_threshold": self.weight_threshold,
            "dynamic_quantization": self.use_dynamic_quantization
        }
        
        logger.info(f"Model quantization complete. Size reduction: {size_reduction:.2%}")
        
        return quantized_model, statistics
    
    def _get_model_size(self, model: Any) -> int:
        """
        Get the approximate size of a model in bytes.
        
        Args:
            model: The model to measure
            
        Returns:
            Approximate size in bytes
        """
        try:
            # Serialize to bytes and measure length
            buffer = pickle.dumps(model)
            return len(buffer)
        except Exception as e:
            logger.error(f"Error measuring model size: {e}")
            return 0
    
    def _quantize_pickle_model(self, model: Any) -> Any:
        """
        Quantize a generic pickle-serializable model.
        
        Args:
            model: The model to quantize
            
        Returns:
            Quantized model
        """
        try:
            # For pickle models, we recursively process numpy arrays
            return self._process_object(model)
        except Exception as e:
            logger.error(f"Error quantizing pickle model: {e}")
            return model
    
    def _quantize_sklearn_model(self, model: Any, calibration_data: Optional[Any] = None) -> Any:
        """
        Quantize a scikit-learn model.
        
        Args:
            model: The sklearn model to quantize
            calibration_data: Optional data for calibration
            
        Returns:
            Quantized model
        """
        try:
            # Handle specific sklearn model types
            if hasattr(model, "feature_importances_"):
                model.feature_importances_ = self._quantize_array(model.feature_importances_)
            
            # Handle Pipeline objects
            if hasattr(model, "steps"):
                for name, estimator in model.steps:
                    self._quantize_sklearn_estimator(estimator)
            
            # Handle direct estimators
            self._quantize_sklearn_estimator(model)
            
            return model
        except Exception as e:
            logger.error(f"Error quantizing sklearn model: {e}")
            return model
    
    def _quantize_sklearn_estimator(self, estimator: Any) -> None:
        """
        Quantize a specific sklearn estimator in-place.
        
        Args:
            estimator: The estimator to quantize
        """
        # SVM coefficients and intercepts
        if hasattr(estimator, "coef_"):
            estimator.coef_ = self._quantize_array(estimator.coef_)
        if hasattr(estimator, "intercept_"):
            estimator.intercept_ = self._quantize_array(estimator.intercept_)
            
        # RandomForest and other tree-based models
        if hasattr(estimator, "estimators_"):
            for i, tree in enumerate(estimator.estimators_):
                self._quantize_sklearn_estimator(tree)
                
        # TF-IDF Vectorizer
        if hasattr(estimator, "idf_"):
            estimator.idf_ = self._quantize_array(estimator.idf_)
    
    def _quantize_custom_model(self, model: Any, calibration_data: Optional[Any] = None) -> Any:
        """
        Quantize a custom model with specific handling.
        
        Args:
            model: The custom model to quantize
            calibration_data: Optional data for calibration
            
        Returns:
            Quantized model
        """
        # This would implement custom model-specific quantization
        # For now, just use the generic method
        return self._quantize_pickle_model(model)
    
    def _process_object(self, obj: Any) -> Any:
        """
        Recursively process an object for quantization.
        
        Args:
            obj: The object to process
            
        Returns:
            Processed object
        """
        if isinstance(obj, np.ndarray):
            return self._quantize_array(obj)
        elif isinstance(obj, dict):
            return {k: self._process_object(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._process_object(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._process_object(item) for item in obj)
        else:
            return obj
    
    def _quantize_array(self, array: np.ndarray) -> np.ndarray:
        """
        Quantize a numpy array to lower precision.
        
        Args:
            array: The array to quantize
            
        Returns:
            Quantized array
        """
        if not isinstance(array, np.ndarray):
            return array
            
        # Skip small arrays (not worth quantizing)
        if array.size < 10:
            return array
            
        # Handle different dtypes
        if np.issubdtype(array.dtype, np.floating):
            # Apply pruning if applicable
            if self.weight_threshold > 0:
                small_indices = np.abs(array) < self.weight_threshold
                array = array.copy()  # Make a copy to avoid modifying the original
                array[small_indices] = 0
            
            # Apply quantization
            return array.astype(self.float_dtype)
            
        elif np.issubdtype(array.dtype, np.integer):
            # For integers, just convert to appropriate integer type
            return array.astype(self.int_dtype)
            
        # For other types, return as is
        return array

def quantize_model_file(input_path: str, 
                       output_path: Optional[str] = None, 
                       bit_depth: int = 16,
                       weight_threshold: float = 0.001,
                       model_format: str = "pickle") -> Dict[str, Any]:
    """
    Quantize a model file and save the quantized version.
    
    Args:
        input_path: Path to the model file to quantize
        output_path: Path to save the quantized model (if None, adds '_quantized' suffix)
        bit_depth: Target bit depth for quantization (8, 16, or 32)
        weight_threshold: Threshold for pruning small weights
        model_format: The format of the model ('pickle', 'sklearn', 'custom')
        
    Returns:
        Dictionary with quantization statistics
    """
    try:
        # Determine output path if not provided
        if output_path is None:
            path_obj = Path(input_path)
            output_path = str(path_obj.parent / f"{path_obj.stem}_quantized{path_obj.suffix}")
        
        # Load the model
        logger.info(f"Loading model from {input_path}")
        with open(input_path, 'rb') as f:
            model = pickle.load(f)
        
        # Create quantizer and quantize model
        quantizer = ModelQuantizer(bit_depth=bit_depth, weight_threshold=weight_threshold)
        quantized_model, statistics = quantizer.quantize_model(model, model_format=model_format)
        
        # Save the quantized model
        logger.info(f"Saving quantized model to {output_path}")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(quantized_model, f)
        
        # Update statistics with file paths
        statistics.update({
            "original_path": input_path,
            "quantized_path": output_path,
            "original_file_size": os.path.getsize(input_path),
            "quantized_file_size": os.path.getsize(output_path),
            "file_size_reduction_percent": 
                (1 - (os.path.getsize(output_path) / os.path.getsize(input_path))) * 100
                if os.path.exists(input_path) else 0
        })
        
        return statistics
        
    except Exception as e:
        logger.error(f"Error quantizing model file: {e}")
        return {"error": str(e)}

def compare_model_performance(original_model: Any, 
                             quantized_model: Any,
                             test_data: Any,
                             test_labels: Any) -> Dict[str, Any]:
    """
    Compare performance between original and quantized models.
    
    Args:
        original_model: Original model
        quantized_model: Quantized model
        test_data: Test data for evaluation
        test_labels: Test labels for evaluation
        
    Returns:
        Dictionary with performance comparison
    """
    try:
        # Get predictions
        original_preds = original_model.predict(test_data)
        quantized_preds = quantized_model.predict(test_data)
        
        # Calculate accuracy
        original_accuracy = np.mean(original_preds == test_labels)
        quantized_accuracy = np.mean(quantized_preds == test_labels)
        
        # Calculate prediction differences
        prediction_diff = np.mean(original_preds != quantized_preds)
        
        return {
            "original_accuracy": float(original_accuracy),
            "quantized_accuracy": float(quantized_accuracy),
            "accuracy_diff": float(original_accuracy - quantized_accuracy),
            "prediction_diff_percent": float(prediction_diff * 100)
        }
        
    except Exception as e:
        logger.error(f"Error comparing model performance: {e}")
        return {"error": str(e)}

def batch_quantize_models(model_dir: str, 
                         output_dir: Optional[str] = None,
                         bit_depth: int = 16,
                         weight_threshold: float = 0.001,
                         model_format: str = "pickle") -> Dict[str, Any]:
    """
    Batch quantize all model files in a directory.
    
    Args:
        model_dir: Directory containing model files
        output_dir: Directory to save quantized models (if None, uses model_dir)
        bit_depth: Target bit depth for quantization
        weight_threshold: Threshold for pruning small weights
        model_format: The format of the models
        
    Returns:
        Dictionary with quantization statistics for all models
    """
    if output_dir is None:
        output_dir = model_dir
    
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    total_size_before = 0
    total_size_after = 0
    
    # Process all pickle files in the directory
    for filename in os.listdir(model_dir):
        if filename.endswith('.pkl'):
            input_path = os.path.join(model_dir, filename)
            output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_quantized.pkl")
            
            logger.info(f"Quantizing {filename}...")
            stats = quantize_model_file(
                input_path=input_path,
                output_path=output_path,
                bit_depth=bit_depth,
                weight_threshold=weight_threshold,
                model_format=model_format
            )
            
            results[filename] = stats
            
            if 'original_file_size' in stats and 'quantized_file_size' in stats:
                total_size_before += stats['original_file_size']
                total_size_after += stats['quantized_file_size']
    
    # Add summary statistics
    if total_size_before > 0:
        overall_reduction = (1 - (total_size_after / total_size_before)) * 100
    else:
        overall_reduction = 0
        
    results['summary'] = {
        "total_original_size_bytes": total_size_before,
        "total_quantized_size_bytes": total_size_after,
        "overall_size_reduction_percent": overall_reduction,
        "models_processed": len(results) - 1  # Exclude summary
    }
    
    return results 