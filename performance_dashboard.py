#!/usr/bin/env python
"""
Performance Dashboard - Visualizes ML performance and monitoring metrics
"""

import os
import json
import logging
import argparse
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create directories if they don't exist
os.makedirs('data/performance/charts', exist_ok=True)

def load_optimization_results(filepath: str) -> Dict:
    """Load optimization results from JSON file"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"Results file not found: {filepath}")
            return {}
    except Exception as e:
        logger.error(f"Error loading results: {e}")
        return {}

def load_latest_test_results() -> Dict:
    """Find and load the most recent optimization test results"""
    try:
        results_dir = 'data/performance'
        test_files = [f for f in os.listdir(results_dir) 
                    if f.startswith('optimization_test_') and f.endswith('.json')]
        
        if not test_files:
            logger.warning("No test result files found")
            return {}
        
        # Sort by timestamp in filename
        latest_file = sorted(test_files)[-1]
        
        return load_optimization_results(os.path.join(results_dir, latest_file))
    except Exception as e:
        logger.error(f"Error loading latest test results: {e}")
        return {}

def load_model_metrics() -> Dict:
    """Load model metrics from monitoring data"""
    try:
        metrics_file = 'data/monitoring/model_metrics.json'
        if os.path.exists(metrics_file):
            with open(metrics_file, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"Model metrics file not found: {metrics_file}")
            return {}
    except Exception as e:
        logger.error(f"Error loading model metrics: {e}")
        return {}

def generate_performance_comparison_chart(data: Dict, chart_name: str = "performance_comparison") -> str:
    """Generate a bar chart comparing standard vs optimized performance"""
    try:
        if not data or 'standard' not in data or 'optimized' not in data:
            logger.warning("Insufficient data for performance comparison chart")
            return ""
        
        # Extract data
        standard_data = data['standard']
        optimized_data = data['optimized']
        
        # Get metrics to compare
        metrics = ['total_time_sec', 'avg_time_per_prediction_ms', 
                  'metrics_collection_time_sec', 'predictions_per_second']
        
        # Set up the chart
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Position of bars on x-axis
        x = np.arange(len(metrics))
        width = 0.35
        
        # Extract values, handling potential missing keys
        standard_values = [standard_data.get(metric, 0) for metric in metrics]
        optimized_values = [optimized_data.get(metric, 0) for metric in metrics]
        
        # Normalize values for better visualization
        prediction_idx = metrics.index('predictions_per_second')
        standard_values[prediction_idx] /= 1000  # Convert to thousands
        optimized_values[prediction_idx] /= 1000
        
        # Create bars
        rects1 = ax.bar(x - width/2, standard_values, width, label='Standard')
        rects2 = ax.bar(x + width/2, optimized_values, width, label='Optimized')
        
        # Add labels and title
        ax.set_ylabel('Value')
        ax.set_title('Standard vs Optimized Performance')
        ax.set_xticks(x)
        
        # Format metric names for better display
        formatted_metrics = [m.replace('_', ' ').title() for m in metrics]
        formatted_metrics[prediction_idx] = 'Predictions/Sec (thousands)'
        ax.set_xticklabels(formatted_metrics)
        
        ax.legend()
        
        # Add improvement percentages
        for i, (std, opt) in enumerate(zip(standard_values, optimized_values)):
            if std > 0:
                # For metrics where lower is better (all except predictions_per_second)
                if i == prediction_idx:
                    pct_change = ((opt - std) / std) * 100  # Higher is better
                else:
                    pct_change = ((std - opt) / std) * 100  # Lower is better
                
                color = 'green' if pct_change > 0 else 'red'
                ax.annotate(f"{pct_change:.1f}%", 
                           xy=(i, max(std, opt) * 1.05),
                           xytext=(0, 5),
                           textcoords="offset points",
                           ha='center', va='bottom',
                           color=color, fontweight='bold')
        
        # Save the chart
        output_path = f"data/performance/charts/{chart_name}.png"
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Generated performance comparison chart: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error generating performance comparison chart: {e}")
        return ""

def generate_system_metrics_chart(data: Dict, chart_name: str = "system_metrics") -> str:
    """Generate a chart for system metrics"""
    try:
        if not data or 'memory' not in data or 'disk' not in data:
            logger.warning("Insufficient data for system metrics chart")
            return ""
        
        # Extract data
        memory_data = data['memory']
        disk_data = data['disk']
        
        # Set up the chart - 2 subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Memory chart (left)
        memory_before = memory_data.get('memory_used_before_percent', 0)
        memory_after = memory_data.get('memory_used_after_percent', 0)
        
        # Memory usage pie chart
        ax1.pie([memory_before, 100-memory_before], 
               labels=['Used', 'Free'],
               colors=['#ff9999', '#c2c2f0'],
               autopct='%1.1f%%',
               startangle=90)
        ax1.set_title('Memory Usage Before Optimization')
        
        # Disk usage pie chart
        disk_before = disk_data.get('disk_used_before_percent', 0)
        disk_after = disk_data.get('disk_used_after_percent', 0)
        
        ax2.pie([disk_before, 100-disk_before],
               labels=['Used', 'Free'],
               colors=['#ff9999', '#c2c2f0'],
               autopct='%1.1f%%',
               startangle=90)
        ax2.set_title('Disk Usage Before Optimization')
        
        # Add optimization impact text
        memory_impact = memory_data.get('memory_improvement_percent', 0)
        disk_impact = disk_data.get('disk_improvement_percent', 0)
        
        impact_text = (f"Memory Optimization Impact: {memory_impact:.2f}%\n"
                      f"Disk Optimization Impact: {disk_impact:.2f}%")
        
        fig.text(0.5, 0.01, impact_text, ha='center', fontsize=12, 
                color='blue' if memory_impact > 0 or disk_impact > 0 else 'red')
        
        # Save the chart
        output_path = f"data/performance/charts/{chart_name}.png"
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Generated system metrics chart: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error generating system metrics chart: {e}")
        return ""

def generate_model_performance_chart(metrics_data: Dict, chart_name: str = "model_performance") -> str:
    """Generate a chart showing model performance metrics"""
    try:
        if not metrics_data:
            logger.warning("No model metrics data available")
            return ""
        
        # Extract model metrics
        models = list(metrics_data.keys())
        
        if not models:
            logger.warning("No models found in metrics data")
            return ""
        
        # Set up chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Performance metrics for first subplot
        accuracy = []
        error_rate = []
        model_names = []
        
        for model_id in models:
            model_data = metrics_data[model_id]
            accuracy.append(float(model_data.get('accuracy', 0)))
            error_rate.append(float(model_data.get('error_rate', 0)))
            # Truncate long model names
            model_names.append(model_id[:15] + '...' if len(model_id) > 15 else model_id)
        
        # Bar chart for accuracy and error rate
        x = np.arange(len(model_names))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, accuracy, width, label='Accuracy')
        bars2 = ax1.bar(x + width/2, error_rate, width, label='Error Rate')
        
        ax1.set_ylabel('Rate')
        ax1.set_title('Model Accuracy & Error Rate')
        ax1.set_xticks(x)
        ax1.set_xticklabels(model_names, rotation=45, ha='right')
        ax1.legend()
        
        # Add threshold line for accuracy
        ax1.axhline(y=0.7, color='r', linestyle='-', alpha=0.3)
        ax1.text(0, 0.71, 'Accuracy Threshold (0.7)', color='r')
        
        # Second subplot for latency and throughput
        latency = []
        throughput = []
        
        for model_id in models:
            model_data = metrics_data[model_id]
            latency.append(float(model_data.get('latency_avg_ms', 0)))
            throughput.append(float(model_data.get('throughput_per_minute', 0)))
        
        # Create second axis for throughput
        ax2b = ax2.twinx()
        
        line1 = ax2.plot(model_names, latency, 'bo-', label='Avg Latency (ms)')
        line2 = ax2b.plot(model_names, throughput, 'go-', label='Throughput (per min)')
        
        ax2.set_ylabel('Latency (ms)')
        ax2b.set_ylabel('Throughput (per min)')
        ax2.set_title('Model Performance Metrics')
        ax2.set_xticklabels(model_names, rotation=45, ha='right')
        
        # Add latency threshold line
        ax2.axhline(y=100, color='r', linestyle='-', alpha=0.3)
        ax2.text(0, 105, 'Latency Threshold (100ms)', color='r')
        
        # Combine legends
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax2.legend(lines, labels, loc='upper right')
        
        # Save the chart
        output_path = f"data/performance/charts/{chart_name}.png"
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Generated model performance chart: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error generating model performance chart: {e}")
        return ""

def generate_dashboard(test_results: Dict, model_metrics: Dict) -> List[str]:
    """Generate performance dashboard with multiple charts"""
    charts = []
    
    # Extract monitor performance data
    if test_results and 'monitor' in test_results:
        monitor_data = {
            'standard': test_results['monitor'].get('standard', {}),
            'optimized': test_results['monitor'].get('optimized', {})
        }
        chart = generate_performance_comparison_chart(monitor_data)
        if chart:
            charts.append(chart)
    
    # Extract system metrics data
    if test_results:
        system_data = {
            'memory': test_results.get('memory', {}),
            'disk': test_results.get('disk', {})
        }
        chart = generate_system_metrics_chart(system_data)
        if chart:
            charts.append(chart)
    
    # Generate model performance chart
    chart = generate_model_performance_chart(model_metrics)
    if chart:
        charts.append(chart)
    
    return charts

def display_performance_insights(test_results: Dict, model_metrics: Dict) -> None:
    """Display text-based performance insights"""
    print("\n" + "="*80)
    print("PERFORMANCE OPTIMIZATION INSIGHTS".center(80))
    print("="*80)
    
    # Monitor performance insights
    if test_results and 'monitor' in test_results:
        monitor_data = test_results['monitor']
        standard = monitor_data.get('standard', {})
        optimized = monitor_data.get('optimized', {})
        
        std_throughput = standard.get('predictions_per_second', 0)
        opt_throughput = optimized.get('predictions_per_second', 0)
        
        if std_throughput > 0:
            throughput_improvement = ((opt_throughput - std_throughput) / std_throughput) * 100
            print(f"\nMonitoring System Performance:")
            print(f"  • Throughput increased from {std_throughput:.2f} to {opt_throughput:.2f} predictions/sec")
            print(f"  • Overall throughput improvement: {throughput_improvement:.2f}%")
            
            # Latency insights
            std_latency = standard.get('avg_time_per_prediction_ms', 0)
            opt_latency = optimized.get('avg_time_per_prediction_ms', 0)
            
            if std_latency > 0:
                latency_improvement = ((std_latency - opt_latency) / std_latency) * 100
                print(f"  • Average latency reduced from {std_latency:.3f}ms to {opt_latency:.3f}ms")
                print(f"  • Latency improvement: {latency_improvement:.2f}%")
    
    # System metrics insights
    if test_results:
        memory_data = test_results.get('memory', {})
        disk_data = test_results.get('disk', {})
        
        print("\nSystem Resource Optimization:")
        
        # Memory insights
        mem_improvement = memory_data.get('memory_improvement_percent', 0)
        mem_before = memory_data.get('memory_used_before_percent', 0)
        mem_after = memory_data.get('memory_used_after_percent', 0)
        
        print(f"  • Memory usage: {mem_before:.2f}% → {mem_after:.2f}%")
        print(f"  • Memory optimization impact: {mem_improvement:.2f}%")
        
        # Disk insights
        disk_improvement = disk_data.get('disk_improvement_percent', 0)
        disk_before = disk_data.get('disk_used_before_percent', 0)
        disk_after = disk_data.get('disk_used_after_percent', 0)
        
        print(f"  • Disk usage: {disk_before:.2f}% → {disk_after:.2f}%")
        print(f"  • Disk optimization impact: {disk_improvement:.2f}%")
    
    # Model health insights
    if model_metrics:
        print("\nModel Health Status:")
        
        for model_id, metrics in model_metrics.items():
            accuracy = float(metrics.get('accuracy', 0))
            latency = float(metrics.get('latency_avg_ms', 0))
            error_rate = float(metrics.get('error_rate', 0))
            
            # Determine health status
            if accuracy >= 0.7 and latency < 100 and error_rate < 0.05:
                health = "HEALTHY"
                status_color = "GREEN"
            elif accuracy >= 0.5 and latency < 150 and error_rate < 0.1:
                health = "WARNING"
                status_color = "YELLOW"
            else:
                health = "UNHEALTHY"
                status_color = "RED"
            
            print(f"  • Model: {model_id}")
            print(f"    - Health Status: {health} ({status_color})")
            print(f"    - Accuracy: {accuracy:.2f}")
            print(f"    - Avg Latency: {latency:.2f}ms")
            print(f"    - Error Rate: {error_rate:.4f}")
            print(f"    - Prediction Count: {metrics.get('prediction_count', 0)}")
    
    # Recommendations
    print("\nRecommendations:")
    
    # Monitoring recommendations
    if test_results and 'monitor' in test_results:
        monitor_perf = test_results['monitor']
        sampling_rate = monitor_perf.get('optimized', {}).get('sampling_rate', 0.2)
        
        print(f"  • Current sampling rate: {sampling_rate:.2f} - ", end="")
        if sampling_rate < 0.1:
            print("Consider increasing sampling rate for better accuracy")
        elif sampling_rate > 0.5:
            print("Consider reducing sampling rate for better performance")
        else:
            print("Optimal range")
    
    # Memory optimization recommendations
    if test_results and 'memory' in test_results and mem_after > 80:
        print("  • High memory usage detected - Consider implementing memory pooling")
    
    # Model recommendations
    if model_metrics:
        for model_id, metrics in model_metrics.items():
            accuracy = float(metrics.get('accuracy', 0))
            latency = float(metrics.get('latency_avg_ms', 0))
            
            if accuracy < 0.7:
                print(f"  • Model {model_id}: Low accuracy - Consider retraining with expanded dataset")
            
            if latency > 100:
                print(f"  • Model {model_id}: High latency - Consider model compression techniques")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Performance Dashboard Generator')
    parser.add_argument('--results', help='Path to optimization results JSON file')
    parser.add_argument('--text-only', action='store_true', help='Show text insights only (no charts)')
    args = parser.parse_args()
    
    # Load results data
    if args.results:
        test_results = load_optimization_results(args.results)
    else:
        test_results = load_latest_test_results()
    
    # Load model metrics
    model_metrics = load_model_metrics()
    
    # Generate text insights
    display_performance_insights(test_results, model_metrics)
    
    # Generate charts unless text-only mode is enabled
    if not args.text_only:
        charts = generate_dashboard(test_results, model_metrics)
        
        if charts:
            print(f"\nGenerated {len(charts)} performance charts:")
            for chart in charts:
                print(f"  • {chart}")
        else:
            print("\nNo charts were generated due to insufficient data")

if __name__ == "__main__":
    main() 