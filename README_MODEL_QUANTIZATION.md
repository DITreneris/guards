# Model Quantization System

![Model Optimization](https://img.shields.io/badge/Optimization-Quantization-blue)
![ML Performance](https://img.shields.io/badge/ML-Performance-green)

The Model Quantization System is a comprehensive solution for reducing model size and improving inference performance. It provides tools for converting model weights to lower precision representations while maintaining prediction accuracy.

## Features

- **Multiple Precision Options**: 8-bit, 16-bit, and 32-bit quantization
- **Weight Pruning**: Remove insignificant coefficients
- **Model-Specific Strategies**: Different approaches for various architectures
- **Automatic Fallback**: Seamless recovery if quantized models fail
- **Performance Comparison**: Compare original vs. quantized models
- **Command-Line Interface**: Easy to use from the command line

## Key Benefits

- **Reduced Model Size**: Up to 17% size reduction in our testing
- **Maintained Accuracy**: Zero prediction differences observed in test cases
- **Improved Inference Speed**: Contributes to overall performance gains
- **Memory Efficiency**: Smaller memory footprint for model storage and loading
- **Selective Application**: Apply only to models that benefit most

## Quick Start

### Command Line

```bash
# Quantize all models with 8-bit precision
python model_quantization_demo.py --bit-depth 8

# Quantize only a specific model
python model_quantization_demo.py --model email --bit-depth 16

# Adjust weight pruning threshold
python model_quantization_demo.py --weight-threshold 0.01
```

### Python API

```python
from ml.utils.model_quantization import quantize_model_file

# Quantize a single model
results = quantize_model_file(
    input_path="ml/models/my_model.pkl",
    bit_depth=8,
    weight_threshold=0.001
)

print(f"Size reduction: {results['file_size_reduction_percent']:.2f}%")
```

## Our Results

| Model Type | Original Size | Quantized Size | Reduction | Accuracy Impact |
|------------|---------------|----------------|-----------|-----------------|
| Email      | 5.55 KB       | 4.64 KB        | 16.51%    | None            |
| Intent     | 206.04 KB     | 206.75 KB      | -0.35%    | None            |
| Sentiment  | 4.93 KB       | 5.05 KB        | -2.39%    | None            |

## Components

The system consists of:

1. **ModelQuantizer Class**: Core quantization implementation
2. **Model Loaders**: Specialized handling for different model types
3. **Utility Functions**: Helpers for batch quantization and evaluation
4. **Command-Line Interface**: model_quantization_demo.py script

## Documentation

For detailed documentation, see:

- [Model Quantization](docs/model_quantization.md): Complete reference
- [Performance Optimization](docs/performance_optimization.md): Overall optimization strategy

## Best Practices

1. Always test quantized models before deploying to production
2. Adjust the bit depth based on model architecture and requirements
3. Apply quantization selectively to models that benefit most
4. Consider mixed precision for different parts of your system

## Future Improvements

1. Dynamic quantization with calibration data
2. Operation fusion for better inference performance
3. Hardware-specific optimizations
4. Quantization-aware training

## License

This project is licensed under the MIT License - see the LICENSE file for details. 