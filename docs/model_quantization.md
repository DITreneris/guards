# Model Quantization System

## Overview

The Model Quantization System reduces model size and improves inference performance by converting model weights to lower precision representations. This documentation explains how to use the quantization utilities, their benefits, and important considerations.

## Key Features

- **Multiple Precision Options**: Support for 8-bit and 16-bit quantization
- **Weight Pruning**: Removes insignificant coefficients below a configurable threshold
- **Model-Specific Optimization**: Different strategies for various model architectures
- **Automatic Fallback**: Seamless fallback to original models if quantized versions fail
- **Performance Comparison**: Built-in tools to compare original vs. quantized model performance

## Getting Started

### Basic Usage

```python
from ml.utils.model_quantization import quantize_model_file

# Quantize a single model file
results = quantize_model_file(
    input_path="ml/models/my_model.pkl",
    bit_depth=8,                 # Use 8-bit quantization
    weight_threshold=0.001       # Prune weights below 0.001
)

print(f"Size reduction: {results['file_size_reduction_percent']:.2f}%")
```

### Batch Quantization

```python
from ml.utils.model_quantization import batch_quantize_models

# Quantize all models in a directory
results = batch_quantize_models(
    model_dir="ml/models",
    output_dir="ml/models/quantized",
    bit_depth=16,
    weight_threshold=0.001
)

print(f"Overall size reduction: {results['summary']['overall_size_reduction_percent']:.2f}%")
```

### Using ModelLoader with Quantization

```python
from ml.models.model_loader import IntentModelLoader

# Create loader with quantization enabled
model_loader = IntentModelLoader(use_quantized=True)

# Switch between original and quantized models
model_loader.use_quantized_model(True)   # Use quantized
model_loader.use_quantized_model(False)  # Use original

# Get size information
size_info = model_loader.get_model_size_info()
print(f"Size reduction: {size_info.get('size_reduction_percent', 0):.2f}%")
```

## Command-Line Interface

The `model_quantization_demo.py` script provides a convenient command-line interface:

```shell
# Quantize all models with 8-bit precision
python model_quantization_demo.py --bit-depth 8

# Quantize only the intent model
python model_quantization_demo.py --model intent --bit-depth 16

# Specify weight threshold
python model_quantization_demo.py --weight-threshold 0.0005
```

## Performance Considerations

Our testing has shown:

1. **Model-Dependent Results**: Not all models benefit equally from quantization
   - Email categorization model: ~16.5% size reduction with 8-bit quantization
   - Intent and sentiment models: Minimal or negative size reduction

2. **Accuracy Impact**: No measurable impact on prediction accuracy in test scenarios

3. **Trade-offs**:
   - Lower precision (8-bit) offers better size reduction but may impact accuracy
   - Higher precision (16-bit) preserves accuracy but offers less size reduction
   - Weight pruning can significantly reduce size but may impact performance for sparse models

## Implementation Details

The quantization system consists of:

1. **ModelQuantizer Class**: Core class for quantizing model weights
   - Handles different data types (float32, float16, int8, etc.)
   - Implements array conversion and pruning

2. **Model Loaders**: Specialized loaders for different model types
   - Provides fallback mechanisms if quantized models have issues
   - Handles model switching at runtime

3. **Utilities**: Helper functions for batch processing and comparison
   - `quantize_model_file`: Quantizes a single model file
   - `batch_quantize_models`: Quantizes multiple models
   - `compare_model_performance`: Compares original vs. quantized

## Advanced Configuration

For more control, you can create a `ModelQuantizer` instance directly:

```python
from ml.utils.model_quantization import ModelQuantizer

quantizer = ModelQuantizer(
    bit_depth=8,                    # 8, 16, or 32
    weight_threshold=0.001,         # Pruning threshold
    use_dynamic_quantization=True   # Use dynamic range
)

quantized_model, stats = quantizer.quantize_model(
    model,
    model_format="sklearn",         # sklearn, pickle, or custom
    calibration_data=train_data     # Optional calibration data
)
```

## Best Practices

1. **Test Before Deployment**: Always compare quantized model performance before deploying
2. **Model-Specific Tuning**: Adjust bit depth and threshold based on model architecture
3. **Selective Application**: Apply quantization selectively to models that benefit most
4. **Mixed Precision**: Consider using different precision for different parts of your system

## Troubleshooting

Common issues:

1. **Accuracy Loss**: If accuracy decreases, try:
   - Increasing bit depth from 8 to 16
   - Decreasing weight threshold to preserve more coefficients

2. **Size Increase**: Some models may increase in size after quantization due to:
   - Serialization overhead
   - Small model size where overhead exceeds savings
   - Try quantizing only larger models

3. **Compatibility Issues**: Some sklearn models may not be compatible with all quantization types
   - Error messages will indicate incompatible components
   - Try model-specific quantization strategies

## Future Improvements

Planned enhancements:

1. **Dynamic Quantization**: Adjusting quantization parameters per layer/component
2. **Operation Fusion**: Combining operations for better inference performance
3. **Hardware-Specific Optimization**: Targeting specific hardware accelerators
4. **Quantization-Aware Training**: Training models with quantization in mind 