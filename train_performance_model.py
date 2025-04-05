#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Guards & Robbers Web Performance Predictor - Training Script

This script trains the web performance predictor model using historical data
and saves the trained model for later use.

Usage:
    python train_performance_model.py [--model_type=random_forest] [--output=models/performance_model.pkl]

Version: 1.0.0
Created: June 17, 2025
"""

import os
import sys
import json
import argparse
import datetime
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

# Import our model
from performance_predictor import WebPerformancePredictor, PerformanceMetrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("performance_training.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("train_performance_model")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Train the web performance predictor model")
    
    parser.add_argument("--model_type", 
                      type=str, 
                      default="random_forest",
                      choices=["random_forest", "gradient_boosting", "elastic_net"],
                      help="Type of model to train")
    
    parser.add_argument("--output", 
                      type=str, 
                      default="models/performance_model.pkl",
                      help="Path to save the trained model")
    
    parser.add_argument("--sample_size", 
                      type=int, 
                      default=100,
                      help="Number of synthetic samples to generate if no data file is provided")
    
    parser.add_argument("--data_file",
                      type=str,
                      default=None,
                      help="Path to data file with performance metrics (if available)")
    
    parser.add_argument("--grid_search",
                      action="store_true",
                      help="Perform grid search for hyperparameter tuning")
    
    return parser.parse_args()

def generate_synthetic_data(n_samples: int) -> Tuple[List[PerformanceMetrics], Dict[str, List[float]]]:
    """
    Generate synthetic data for model training when real data is not available
    
    Args:
        n_samples: Number of samples to generate
        
    Returns:
        Tuple of (list of performance metrics, dictionary of target values)
    """
    logger.info(f"Generating {n_samples} synthetic data samples")
    
    np.random.seed(42)  # For reproducibility
    
    # Lists to store generated data
    metrics_list = []
    
    # Target value storage
    target_values = {
        "conversion_rate": [],
        "bounce_rate": [],
        "avg_session_duration": [],
        "engagement_score": []
    }
    
    # Page types and device types for variety
    page_types = ["home", "product", "contact", "about", "blog"]
    device_types = ["desktop", "mobile", "tablet"]
    connection_types = ["4g", "wifi", "3g", "2g", None]
    
    # Generate samples
    for i in range(n_samples):
        # Create timestamp with some variety
        days_ago = np.random.randint(0, 90)
        hours = np.random.randint(0, 24)
        minutes = np.random.randint(0, 60)
        timestamp = datetime.datetime.now() - datetime.timedelta(days=days_ago, hours=hours, minutes=minutes)
        
        # Page load metrics - random but correlated
        base_load_time = np.random.gamma(shape=7, scale=500)  # Base load time around 3.5s
        server_response_base = np.random.gamma(shape=3, scale=100)  # Server response time
        
        # Create correlations between metrics
        page_load_time = base_load_time * np.random.uniform(0.9, 1.1)  # Slight variation
        first_contentful_paint = base_load_time * np.random.uniform(0.4, 0.6)  # 40-60% of load time
        time_to_interactive = base_load_time * np.random.uniform(0.7, 1.3)  # 70-130% of load time
        largest_contentful_paint = base_load_time * np.random.uniform(0.5, 0.9)  # 50-90% of load time
        cumulative_layout_shift = np.random.beta(1.2, 10) * 0.5  # Usually small, occasionally larger
        
        # Server metrics
        server_response_time = server_response_base * np.random.uniform(0.9, 1.1)
        error_rate = np.random.beta(1, 20) * 10  # Usually very low error rate (0-10%)
        
        # User metrics - correlated with page load metrics
        bounce_rate_base = min(20 + (page_load_time / 1000) * 15, 100)  # Higher load time -> higher bounce rate
        bounce_rate = min(bounce_rate_base * np.random.uniform(0.8, 1.2), 100)
        
        session_duration_base = max(120 - (page_load_time / 1000) * 20, 10)  # Higher load time -> shorter session
        average_session_duration = session_duration_base * np.random.uniform(0.8, 1.2)
        
        pages_per_session_base = max(3 - (page_load_time / 5000), 1)  # Higher load time -> fewer pages
        pages_per_session = pages_per_session_base * np.random.uniform(0.8, 1.2)
        
        # Page metrics
        page_type = np.random.choice(page_types)
        page_size = np.random.gamma(shape=5, scale=300)  # Page size in KB
        number_of_resources = int(np.random.gamma(shape=10, scale=5))  # Number of resources
        number_of_dom_elements = int(np.random.gamma(shape=20, scale=10))  # Number of DOM elements
        
        # Device and network metrics
        device_type = np.random.choice(device_types)
        connection_type = np.random.choice(connection_types)
        viewport_width = None
        if device_type == "desktop":
            viewport_width = np.random.randint(1024, 2560)
        elif device_type == "mobile":
            viewport_width = np.random.randint(320, 480)
        elif device_type == "tablet":
            viewport_width = np.random.randint(768, 1024)
            
        # Create performance metrics object
        metrics = PerformanceMetrics(
            page_load_time=page_load_time,
            first_contentful_paint=first_contentful_paint,
            time_to_interactive=time_to_interactive,
            largest_contentful_paint=largest_contentful_paint,
            cumulative_layout_shift=cumulative_layout_shift,
            server_response_time=server_response_time,
            error_rate=error_rate,
            bounce_rate=bounce_rate,
            average_session_duration=average_session_duration,
            pages_per_session=pages_per_session,
            page_type=page_type,
            page_size=page_size,
            number_of_resources=number_of_resources,
            number_of_dom_elements=number_of_dom_elements,
            device_type=device_type,
            connection_type=connection_type,
            viewport_width=viewport_width,
            timestamp=timestamp
        )
        
        metrics_list.append(metrics)
        
        # Generate target values
        # Conversion rate - negatively correlated with load time and error rate
        conversion_base = 0.10 - (page_load_time / 20000) - (error_rate / 100)
        conversion_base = max(0.01, min(conversion_base, 0.20))  # Keep between 1-20%
        conversion_rate = conversion_base * np.random.uniform(0.8, 1.2)
        
        # Engagement score - combination of session duration and pages per session
        engagement_base = ((average_session_duration / 120) * 0.5 + (pages_per_session / 4) * 0.5) * 100
        engagement_score = engagement_base * np.random.uniform(0.9, 1.1)
        
        # Add to target values
        target_values["conversion_rate"].append(conversion_rate)
        target_values["bounce_rate"].append(bounce_rate)
        target_values["avg_session_duration"].append(average_session_duration)
        target_values["engagement_score"].append(engagement_score)
    
    logger.info(f"Generated {len(metrics_list)} synthetic performance metrics samples")
    
    return metrics_list, target_values 

def load_data(data_file: str) -> Tuple[List[PerformanceMetrics], Dict[str, List[float]]]:
    """
    Load performance metrics data from a file
    
    Args:
        data_file: Path to the data file
        
    Returns:
        Tuple of (list of performance metrics, dictionary of target values)
    """
    logger.info(f"Loading data from {data_file}")
    
    # Check if file exists
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    try:
        # Load data from the file
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        # Parse metrics
        metrics_list = []
        for item in data['metrics']:
            # Convert timestamp from string to datetime
            if 'timestamp' in item:
                item['timestamp'] = datetime.datetime.fromisoformat(item['timestamp'])
            
            # Create PerformanceMetrics object
            metrics = PerformanceMetrics(**item)
            metrics_list.append(metrics)
        
        # Parse target values
        target_values = data['targets']
        
        logger.info(f"Loaded {len(metrics_list)} metrics samples from file")
        
        return metrics_list, target_values
    
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise
        
def visualize_data(metrics_list: List[PerformanceMetrics], target_values: Dict[str, List[float]],
                  save_path: Optional[str] = None) -> None:
    """
    Create visualizations of the data for exploratory analysis
    
    Args:
        metrics_list: List of performance metrics
        target_values: Dictionary of target values
        save_path: Optional path to save visualizations
    """
    logger.info("Creating data visualizations")
    
    # Extract data for plotting
    data = []
    for metrics in metrics_list:
        item = {
            'page_load_time': metrics.page_load_time,
            'first_contentful_paint': metrics.first_contentful_paint,
            'time_to_interactive': metrics.time_to_interactive,
            'largest_contentful_paint': metrics.largest_contentful_paint,
            'cumulative_layout_shift': metrics.cumulative_layout_shift,
            'server_response_time': metrics.server_response_time,
            'error_rate': metrics.error_rate,
            'bounce_rate': metrics.bounce_rate,
            'average_session_duration': metrics.average_session_duration,
            'pages_per_session': metrics.pages_per_session,
            'page_size': metrics.page_size,
            'number_of_resources': metrics.number_of_resources,
            'number_of_dom_elements': metrics.number_of_dom_elements,
            'day_of_week': metrics.day_of_week,
            'hour_of_day': metrics.hour_of_day,
        }
        data.append(item)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Add target values
    for target, values in target_values.items():
        df[target] = values
    
    # Create a figure with multiple subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Performance Metrics vs. Business Outcomes', fontsize=16)
    
    # Plot 1: Page Load Time vs. Conversion Rate
    axes[0, 0].scatter(df['page_load_time'], df['conversion_rate'], alpha=0.6)
    axes[0, 0].set_title('Page Load Time vs. Conversion Rate')
    axes[0, 0].set_xlabel('Page Load Time (ms)')
    axes[0, 0].set_ylabel('Conversion Rate')
    axes[0, 0].grid(True)
    
    # Plot 2: Page Load Time vs. Bounce Rate
    axes[0, 1].scatter(df['page_load_time'], df['bounce_rate'], alpha=0.6, color='red')
    axes[0, 1].set_title('Page Load Time vs. Bounce Rate')
    axes[0, 1].set_xlabel('Page Load Time (ms)')
    axes[0, 1].set_ylabel('Bounce Rate (%)')
    axes[0, 1].grid(True)
    
    # Plot 3: Time to Interactive vs. Session Duration
    axes[1, 0].scatter(df['time_to_interactive'], df['avg_session_duration'], alpha=0.6, color='green')
    axes[1, 0].set_title('Time to Interactive vs. Session Duration')
    axes[1, 0].set_xlabel('Time to Interactive (ms)')
    axes[1, 0].set_ylabel('Avg. Session Duration (s)')
    axes[1, 0].grid(True)
    
    # Plot 4: Largest Contentful Paint vs. Engagement Score
    axes[1, 1].scatter(df['largest_contentful_paint'], df['engagement_score'], alpha=0.6, color='purple')
    axes[1, 1].set_title('Largest Contentful Paint vs. Engagement Score')
    axes[1, 1].set_xlabel('Largest Contentful Paint (ms)')
    axes[1, 1].set_ylabel('Engagement Score')
    axes[1, 1].grid(True)
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # Save or show the figure
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)
        logger.info(f"Saved visualization to {save_path}")
    else:
        plt.show()
    
    # Create histogram of page load times
    plt.figure(figsize=(10, 6))
    plt.hist(df['page_load_time'], bins=30, alpha=0.7)
    plt.title('Distribution of Page Load Times')
    plt.xlabel('Page Load Time (ms)')
    plt.ylabel('Frequency')
    plt.grid(True)
    
    # Save or show the histogram
    if save_path:
        hist_path = save_path.replace('.png', '_histogram.png')
        plt.savefig(hist_path)
        logger.info(f"Saved histogram to {hist_path}")
    else:
        plt.show()
    
    logger.info("Data visualization complete")
    
def run_training(metrics_list: List[PerformanceMetrics], 
                target_values: Dict[str, List[float]],
                model_type: str = "random_forest",
                output_path: str = "models/performance_model.pkl",
                grid_search: bool = False) -> WebPerformancePredictor:
    """
    Train the performance predictor model and save it
    
    Args:
        metrics_list: List of performance metrics
        target_values: Dictionary of target values
        model_type: Type of model to train
        output_path: Path to save the trained model
        grid_search: Whether to perform grid search for hyperparameter tuning
        
    Returns:
        Trained WebPerformancePredictor model
    """
    logger.info(f"Beginning model training with {model_type} model type")
    
    # Initialize the model
    model = WebPerformancePredictor(model_type=model_type)
    
    # Train the model
    training_metrics = model.train(
        metrics_list=metrics_list,
        target_values=target_values,
        validation_split=0.2,
        grid_search=grid_search
    )
    
    # Log results
    logger.info(f"Training complete. R²: {training_metrics['r2_score']:.3f}, "
                f"RMSE: {training_metrics['rmse']:.3f}")
    
    # Save the model
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    model.save_model(output_path)
    logger.info(f"Model saved to {output_path}")
    
    return model 

def run_demo_prediction(model: WebPerformancePredictor) -> None:
    """
    Run a demo prediction with the trained model
    
    Args:
        model: Trained WebPerformancePredictor model
    """
    logger.info("Running demo prediction with trained model")
    
    # Create a sample metrics object
    metrics = PerformanceMetrics(
        page_load_time=5000,  # 5 seconds (slow)
        first_contentful_paint=2000,
        time_to_interactive=4500,
        largest_contentful_paint=3000,
        cumulative_layout_shift=0.2,
        server_response_time=500,
        error_rate=1.0,
        bounce_rate=45.0,
        average_session_duration=60.0,
        pages_per_session=2.5,
        page_type="home",
        page_size=1500,
        number_of_resources=85,
        number_of_dom_elements=500,
        device_type="desktop",
        connection_type="wifi",
        viewport_width=1920
    )
    
    # Make prediction
    impact = model.predict(metrics)
    
    # Print results
    logger.info("Demo Prediction Results:")
    logger.info(f"Lead Conversion Impact: {impact.lead_conversion_impact:.2f}%")
    logger.info(f"Bounce Rate Impact: {impact.bounce_rate_impact:.2f}%")
    logger.info(f"Session Duration Impact: {impact.session_duration_impact:.2f}%")
    logger.info(f"Engagement Score Impact: {impact.engagement_score_impact:.2f}%")
    
    logger.info("Top Feature Impacts:")
    for feature, importance in sorted(impact.feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)[:5]:
        logger.info(f"  {feature}: {importance:.4f}")
    
    logger.info("Recommendations:")
    for i, recommendation in enumerate(impact.recommendations, 1):
        logger.info(f"  {i}. {recommendation}")
        
    # Visualize impact of improving page load time
    fig = model.visualize_impact(metrics, "page_load_time", 
                                value_range=np.linspace(1000, 8000, 20))
    
    # Save the visualization
    fig.savefig("demo_page_load_impact.png")
    logger.info("Saved impact visualization to demo_page_load_impact.png")
    
    return impact

def run_prediction_for_current_site(model: WebPerformancePredictor) -> PerformanceImpact:
    """
    Run a prediction with the trained model using the current site metrics
    
    Args:
        model: Trained WebPerformancePredictor model
        
    Returns:
        PerformanceImpact object with predictions
    """
    logger.info("Making prediction for current site metrics")
    
    # These values would ideally come from real measurements
    # For demo purposes, we're using estimates based on Lighthouse reports
    metrics = PerformanceMetrics(
        page_load_time=4200,  # Current site metrics
        first_contentful_paint=1950,
        time_to_interactive=3800,
        largest_contentful_paint=2800,
        cumulative_layout_shift=0.15,
        server_response_time=450,
        error_rate=1.5,
        bounce_rate=42.0,
        average_session_duration=65.0,
        pages_per_session=2.2,
        page_type="home",
        page_size=1800,
        number_of_resources=95,
        number_of_dom_elements=620,
        device_type="desktop",
        connection_type="wifi",
        viewport_width=1920
    )
    
    # Make prediction
    impact = model.predict(metrics)
    
    # Print results
    logger.info("Current Site Performance Impact:")
    logger.info(f"Lead Conversion Impact: {impact.lead_conversion_impact:.2f}%")
    logger.info(f"Bounce Rate Impact: {impact.bounce_rate_impact:.2f}%")
    logger.info(f"Session Duration Impact: {impact.session_duration_impact:.2f}%")
    logger.info(f"Engagement Score Impact: {impact.engagement_score_impact:.2f}%")
    
    logger.info("Recommendations for Current Site:")
    for i, recommendation in enumerate(impact.recommendations, 1):
        logger.info(f"  {i}. {recommendation}")
    
    return impact

def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()
    
    # Get data for training
    if args.data_file:
        try:
            metrics_list, target_values = load_data(args.data_file)
        except FileNotFoundError:
            logger.warning(f"Data file not found: {args.data_file}")
            logger.info("Falling back to synthetic data generation")
            metrics_list, target_values = generate_synthetic_data(args.sample_size)
    else:
        logger.info("No data file provided, generating synthetic data")
        metrics_list, target_values = generate_synthetic_data(args.sample_size)
    
    # Visualize the data
    visualize_data(metrics_list, target_values, save_path="data_visualization.png")
    
    # Train the model
    model = run_training(
        metrics_list=metrics_list,
        target_values=target_values,
        model_type=args.model_type,
        output_path=args.output,
        grid_search=args.grid_search
    )
    
    # Run a demo prediction
    run_demo_prediction(model)
    
    # Run prediction with current site metrics
    impact = run_prediction_for_current_site(model)
    
    # Save predictions to file
    prediction_data = {
        "lead_conversion_impact": impact.lead_conversion_impact,
        "bounce_rate_impact": impact.bounce_rate_impact,
        "session_duration_impact": impact.session_duration_impact,
        "engagement_score_impact": impact.engagement_score_impact,
        "recommendations": impact.recommendations,
        "feature_importance": impact.feature_importance,
        "timestamp": impact.prediction_timestamp.isoformat(),
        "model_version": impact.model_version
    }
    
    with open("current_site_prediction.json", "w") as f:
        json.dump(prediction_data, f, indent=2)
        
    logger.info("Saved current site prediction to current_site_prediction.json")
    
    logger.info("Performance predictor model training and testing complete")

if __name__ == "__main__":
    main()
    
"""
Sample usage:

# Train with default settings (random forest, synthetic data)
python train_performance_model.py

# Train with specific model type and grid search
python train_performance_model.py --model_type=gradient_boosting --grid_search

# Train with real data
python train_performance_model.py --data_file=data/performance_metrics.json

# Generate more synthetic samples
python train_performance_model.py --sample_size=200

# Save model to specific location
python train_performance_model.py --output=models/custom_performance_model.pkl
""" 