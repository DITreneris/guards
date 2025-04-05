"""
Guards & Robbers Web Performance Predictor

This module implements a machine learning model that predicts the relationship
between website performance metrics and lead conversion data.
It helps identify performance bottlenecks that affect business outcomes.

Version: 1.0.0
Created: June 17, 2025
"""

import os
import pickle
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple, Any
import logging
from dataclasses import dataclass, field, asdict
import datetime
import joblib
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder, RobustScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("performance_prediction.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("performance_predictor")

@dataclass
class PerformanceMetrics:
    """Data class for storing website performance metrics"""
    # Page load metrics
    page_load_time: float  # milliseconds
    first_contentful_paint: float  # milliseconds
    time_to_interactive: float  # milliseconds
    largest_contentful_paint: float  # milliseconds
    cumulative_layout_shift: float
    
    # Server metrics
    server_response_time: float  # milliseconds
    error_rate: float  # percentage
    
    # User metrics
    bounce_rate: float  # percentage
    average_session_duration: float  # seconds
    pages_per_session: float
    
    # Page metrics
    page_type: str  # e.g., "home", "product", "contact"
    page_size: float  # KB
    number_of_resources: int
    number_of_dom_elements: int
    
    # Device and network metrics
    device_type: str  # e.g., "desktop", "mobile", "tablet"
    connection_type: Optional[str] = None  # e.g., "4g", "wifi", "3g"
    viewport_width: Optional[int] = None
    
    # Contextual data
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    day_of_week: int = field(init=False)
    hour_of_day: int = field(init=False)
    
    def __post_init__(self):
        """Calculate derived fields"""
        self.day_of_week = self.timestamp.weekday()
        self.hour_of_day = self.timestamp.hour

@dataclass
class PerformanceImpact:
    """Data class for storing the predicted impact of performance metrics"""
    # Predicted business impacts
    lead_conversion_impact: float  # percentage impact on lead conversion rate
    bounce_rate_impact: float  # percentage impact on bounce rate
    session_duration_impact: float  # percentage impact on session duration
    engagement_score_impact: float  # percentage impact on engagement score
    
    # Feature importance
    feature_importance: Dict[str, float]
    
    # Recommendations
    recommendations: List[str]
    
    # Metadata
    model_version: str
    prediction_timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

class WebPerformancePredictor:
    """
    Machine learning model that predicts the impact of web performance metrics
    on business outcomes like lead conversion rates and engagement.
    
    This model:
    1. Analyzes the relationship between performance metrics and conversions
    2. Identifies performance bottlenecks affecting business outcomes
    3. Makes recommendations for performance improvements
    4. Provides visualizations showing the impact of different metrics
    """
    
    def __init__(self, 
                 model_type: str = "random_forest", 
                 model_path: Optional[str] = None):
        """
        Initialize the web performance predictor model
        
        Args:
            model_type: Type of model to use (random_forest, gradient_boosting, elastic_net)
            model_path: Path to saved model file (for loading existing model)
        """
        self.model_type = model_type
        self.model_path = model_path
        self.model = None
        self.feature_names = []
        self.preprocessor = None
        self.target_names = [
            "conversion_rate", 
            "bounce_rate", 
            "avg_session_duration", 
            "engagement_score"
        ]
        
        # Training metrics
        self.training_metrics = {
            "last_training_date": None,
            "r2_score": None,
            "rmse": None,
            "data_size": None
        }
        
        # Performance thresholds based on industry standards
        self.performance_thresholds = {
            "page_load_time": 3000,  # 3 seconds
            "first_contentful_paint": 1800,  # 1.8 seconds
            "time_to_interactive": 3500,  # 3.5 seconds
            "largest_contentful_paint": 2500,  # 2.5 seconds
            "cumulative_layout_shift": 0.1,
            "server_response_time": 200,  # 200 milliseconds
        }
        
        # If model path is provided, load the existing model
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
            logger.info(f"Loaded web performance predictor model from {model_path}")
        else:
            logger.info("Initialized new web performance predictor model - training required")
    
    def preprocess_features(self, 
                           metrics_list: List[PerformanceMetrics], 
                           fit: bool = False) -> pd.DataFrame:
        """
        Preprocess performance metrics into features for the model
        
        Args:
            metrics_list: List of performance metrics objects
            fit: Whether to fit the preprocessor (for training) or just transform
            
        Returns:
            DataFrame with preprocessed features
        """
        # Convert metrics to DataFrame
        data = [asdict(metrics) for metrics in metrics_list]
        df = pd.DataFrame(data)
        
        # Remove timestamp column as it's already processed
        if 'timestamp' in df.columns:
            df = df.drop('timestamp', axis=1)
        
        # If fitting the preprocessor (training mode)
        if fit:
            # Define categorical and numerical features
            categorical_features = [
                "page_type", "device_type", "connection_type"
            ]
            
            numerical_features = [
                "page_load_time", "first_contentful_paint", "time_to_interactive",
                "largest_contentful_paint", "cumulative_layout_shift", "server_response_time",
                "error_rate", "bounce_rate", "average_session_duration", "pages_per_session",
                "page_size", "number_of_resources", "number_of_dom_elements",
                "viewport_width", "day_of_week", "hour_of_day"
            ]
            
            # Filter out any columns that don't exist in the DataFrame
            numerical_features = [col for col in numerical_features if col in df.columns]
            categorical_features = [col for col in categorical_features if col in df.columns]
            
            # Create column transformer for preprocessing
            self.preprocessor = ColumnTransformer(
                transformers=[
                    ("num", RobustScaler(), numerical_features),
                    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
                ],
                remainder="drop"
            )
            
            # Fit the preprocessor
            X_processed = self.preprocessor.fit_transform(df)
            
            # Get feature names
            self.numerical_features = numerical_features
            self.categorical_features = categorical_features
            
            # Create feature names for processed data
            feature_names = numerical_features.copy()
            
            # Add one-hot encoded feature names
            cat_encoder = self.preprocessor.named_transformers_["cat"]
            for i, col in enumerate(categorical_features):
                cats = cat_encoder.categories_[i]
                feature_names.extend([f"{col}_{cat}" for cat in cats])
            
            self.feature_names = feature_names
            
            # Return as dense array for all model types
            return X_processed
            
        # If just transforming (inference mode)
        else:
            if self.preprocessor is None:
                raise ValueError("Preprocessor not fitted. Cannot transform data.")
            
            X_processed = self.preprocessor.transform(df)
            return X_processed
    
    def train(self, 
             metrics_list: List[PerformanceMetrics], 
             target_values: Dict[str, List[float]],
             validation_split: float = 0.2,
             grid_search: bool = True) -> Dict:
        """
        Train the performance predictor model
        
        Args:
            metrics_list: List of performance metrics objects
            target_values: Dictionary with target values (conversion_rate, bounce_rate, etc.)
            validation_split: Proportion of data to use for validation
            grid_search: Whether to perform hyperparameter tuning
            
        Returns:
            Dictionary of training metrics
        """
        # Validate inputs
        required_targets = ["conversion_rate", "bounce_rate", "avg_session_duration", "engagement_score"]
        for target in required_targets:
            if target not in target_values or len(target_values[target]) != len(metrics_list):
                raise ValueError(f"Target values for '{target}' are required and must match the length of metrics_list")
        
        logger.info(f"Training web performance predictor model on {len(metrics_list)} samples")
        
        # Preprocess features
        X = self.preprocess_features(metrics_list, fit=True)
        
        # Create target DataFrame
        y = pd.DataFrame({
            "conversion_rate": target_values["conversion_rate"],
            "bounce_rate": target_values["bounce_rate"],
            "avg_session_duration": target_values["avg_session_duration"],
            "engagement_score": target_values["engagement_score"]
        })
        
        # Split into training and validation sets
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42
        )
        
        # Initialize and train model based on type
        if self.model_type == "random_forest":
            base_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=None,
                min_samples_split=2,
                random_state=42,
                n_jobs=-1
            )
            
            param_grid = {
                "n_estimators": [50, 100, 200],
                "max_depth": [None, 10, 20, 30],
                "min_samples_split": [2, 5, 10]
            } if grid_search else {}
            
        elif self.model_type == "gradient_boosting":
            base_model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=3,
                random_state=42
            )
            
            param_grid = {
                "n_estimators": [50, 100, 200],
                "learning_rate": [0.01, 0.1, 0.2],
                "max_depth": [3, 5, 7]
            } if grid_search else {}
            
        elif self.model_type == "elastic_net":
            base_model = ElasticNet(
                alpha=1.0,
                l1_ratio=0.5,
                random_state=42,
                max_iter=10000
            )
            
            param_grid = {
                "alpha": [0.1, 0.5, 1.0, 2.0],
                "l1_ratio": [0.1, 0.5, 0.7, 0.9]
            } if grid_search else {}
            
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        # Train a separate model for each target
        models = {}
        metrics = {}
        
        for target in self.target_names:
            logger.info(f"Training model for target: {target}")
            
            # Perform grid search if requested
            if grid_search and len(metrics_list) >= 50:
                search = GridSearchCV(
                    base_model, param_grid, cv=3, scoring='neg_mean_squared_error', n_jobs=-1
                )
                search.fit(X_train, y_train[target])
                model = search.best_estimator_
                logger.info(f"Best parameters for {target}: {search.best_params_}")
            else:
                model = base_model.__class__(**base_model.get_params())
                model.fit(X_train, y_train[target])
            
            # Make predictions on validation set
            y_pred = model.predict(X_val)
            
            # Calculate metrics
            mse = mean_squared_error(y_val[target], y_pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_val[target], y_pred)
            mae = mean_absolute_error(y_val[target], y_pred)
            
            logger.info(f"Model for {target}: R² = {r2:.3f}, RMSE = {rmse:.3f}, MAE = {mae:.3f}")
            
            # Store model and metrics
            models[target] = model
            metrics[target] = {
                "r2_score": r2,
                "rmse": rmse,
                "mae": mae
            }
            
            # Get feature importance if available
            if hasattr(model, 'feature_importances_'):
                # Sort features by importance
                importance = model.feature_importances_
                indices = np.argsort(importance)[::-1]
                
                # Log top 10 features
                for i in range(min(10, len(self.feature_names))):
                    idx = indices[i]
                    if idx < len(self.feature_names):
                        logger.info(f"  {i+1}. {self.feature_names[idx]} ({importance[idx]:.4f})")
        
        # Store the trained models
        self.model = models
        
        # Update training metrics
        avg_r2 = np.mean([m["r2_score"] for m in metrics.values()])
        avg_rmse = np.mean([m["rmse"] for m in metrics.values()])
        
        self.training_metrics = {
            "last_training_date": datetime.datetime.now().isoformat(),
            "r2_score": avg_r2,
            "rmse": avg_rmse,
            "data_size": len(metrics_list),
            "metrics_by_target": metrics
        }
        
        logger.info(f"Model training completed. Avg R²: {avg_r2:.3f}, Avg RMSE: {avg_rmse:.3f}")
        
        return self.training_metrics
        
    def predict(self, metrics: PerformanceMetrics) -> PerformanceImpact:
        """
        Predict the impact of performance metrics on business outcomes
        
        Args:
            metrics: Performance metrics object
            
        Returns:
            PerformanceImpact object with predictions and recommendations
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded. Cannot make predictions.")
        
        # Preprocess the metrics
        X = self.preprocess_features([metrics], fit=False)
        
        # Make predictions for each target
        predictions = {}
        for target in self.target_names:
            if target in self.model:
                predictions[target] = float(self.model[target].predict(X)[0])
            else:
                predictions[target] = None
        
        # Generate feature importance
        feature_importance = {}
        baseline_metrics = self._get_baseline_metrics(metrics)
        
        # Calculate impact of each numerical feature
        for feature in self.numerical_features:
            # Skip if feature isn't in our thresholds
            if feature not in self.performance_thresholds:
                continue
                
            # Create two versions of the input, one with optimal value
            optimal_metrics = PerformanceMetrics(**asdict(metrics))
            setattr(optimal_metrics, feature, self.performance_thresholds[feature])
            
            # Predict with optimal value
            X_optimal = self.preprocess_features([optimal_metrics], fit=False)
            
            # Calculate impact on conversion rate
            if "conversion_rate" in self.model:
                baseline_conv = self.model["conversion_rate"].predict(X)[0]
                optimal_conv = self.model["conversion_rate"].predict(X_optimal)[0]
                impact = (optimal_conv - baseline_conv) / baseline_conv if baseline_conv != 0 else 0
                feature_importance[feature] = float(impact)
        
        # Calculate impacts on each business metric
        baseline_conv = predictions["conversion_rate"]
        baseline_bounce = predictions["bounce_rate"]
        baseline_duration = predictions["avg_session_duration"]
        baseline_engagement = predictions["engagement_score"]
        
        # Create optimized metrics using recommended thresholds
        optimized_metrics = self._get_optimized_metrics(metrics)
        X_optimized = self.preprocess_features([optimized_metrics], fit=False)
        
        optimized_predictions = {}
        for target in self.target_names:
            if target in self.model:
                optimized_predictions[target] = float(self.model[target].predict(X_optimized)[0])
            else:
                optimized_predictions[target] = None
        
        # Calculate percentage improvements
        lead_conversion_impact = (
            (optimized_predictions["conversion_rate"] - baseline_conv) / baseline_conv 
            if baseline_conv != 0 else 0
        ) * 100
        
        bounce_rate_impact = (
            (baseline_bounce - optimized_predictions["bounce_rate"]) / baseline_bounce 
            if baseline_bounce != 0 else 0
        ) * 100
        
        session_duration_impact = (
            (optimized_predictions["avg_session_duration"] - baseline_duration) / baseline_duration 
            if baseline_duration != 0 else 0
        ) * 100
        
        engagement_score_impact = (
            (optimized_predictions["engagement_score"] - baseline_engagement) / baseline_engagement 
            if baseline_engagement != 0 else 0
        ) * 100
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, feature_importance)
        
        return PerformanceImpact(
            lead_conversion_impact=lead_conversion_impact,
            bounce_rate_impact=bounce_rate_impact,
            session_duration_impact=session_duration_impact,
            engagement_score_impact=engagement_score_impact,
            feature_importance=feature_importance,
            recommendations=recommendations,
            model_version="1.0.0"
        )
    
    def _get_baseline_metrics(self, metrics: PerformanceMetrics) -> Dict[str, float]:
        """Get baseline performance metrics values"""
        baseline = {}
        for feature in self.numerical_features:
            if hasattr(metrics, feature):
                baseline[feature] = getattr(metrics, feature)
        return baseline
        
    def _get_optimized_metrics(self, metrics: PerformanceMetrics) -> PerformanceMetrics:
        """Create optimized version of metrics using recommended thresholds"""
        optimized = PerformanceMetrics(**asdict(metrics))
        
        # Apply threshold values to the performance metrics
        for feature, threshold in self.performance_thresholds.items():
            if hasattr(optimized, feature):
                setattr(optimized, feature, threshold)
                
        return optimized
    
    def _generate_recommendations(self, 
                                metrics: PerformanceMetrics, 
                                importance: Dict[str, float]) -> List[str]:
        """Generate recommendations based on metrics and feature importance"""
        recommendations = []
        
        # Sort features by their impact
        sorted_features = sorted(importance.items(), key=lambda x: abs(x[1]), reverse=True)
        
        # Generate recommendations for top issues
        for feature, impact in sorted_features[:3]:
            if impact <= 0:
                continue
                
            current_value = getattr(metrics, feature)
            threshold = self.performance_thresholds.get(feature)
            
            if not threshold:
                continue
                
            if current_value > threshold:
                if feature == "page_load_time":
                    recommendations.append(
                        f"Reduce page load time from {current_value:.1f}ms to under {threshold}ms "
                        f"(potential {impact*100:.1f}% conversion improvement)"
                    )
                elif feature == "first_contentful_paint":
                    recommendations.append(
                        f"Optimize First Contentful Paint from {current_value:.1f}ms to under {threshold}ms "
                        f"(potential {impact*100:.1f}% conversion improvement)"
                    )
                elif feature == "largest_contentful_paint":
                    recommendations.append(
                        f"Improve Largest Contentful Paint from {current_value:.1f}ms to under {threshold}ms "
                        f"(potential {impact*100:.1f}% conversion improvement)"
                    )
                elif feature == "time_to_interactive":
                    recommendations.append(
                        f"Reduce Time to Interactive from {current_value:.1f}ms to under {threshold}ms "
                        f"(potential {impact*100:.1f}% conversion improvement)"
                    )
                elif feature == "cumulative_layout_shift":
                    recommendations.append(
                        f"Minimize Cumulative Layout Shift from {current_value:.2f} to under {threshold} "
                        f"(potential {impact*100:.1f}% conversion improvement)"
                    )
                elif feature == "server_response_time":
                    recommendations.append(
                        f"Improve server response time from {current_value:.1f}ms to under {threshold}ms "
                        f"(potential {impact*100:.1f}% conversion improvement)"
                    )
        
        # Add general recommendations if we don't have enough specific ones
        if len(recommendations) < 2:
            if metrics.page_size > 2000:  # 2MB
                recommendations.append(
                    "Reduce page size by optimizing images and minifying CSS/JS"
                )
            if metrics.number_of_resources > 80:
                recommendations.append(
                    "Reduce number of resource requests through bundling or lazy loading"
                )
        
        return recommendations
    
    def batch_predict(self, metrics_list: List[PerformanceMetrics]) -> List[PerformanceImpact]:
        """
        Make predictions for multiple sets of performance metrics
        
        Args:
            metrics_list: List of performance metrics objects
            
        Returns:
            List of PerformanceImpact objects
        """
        return [self.predict(metrics) for metrics in metrics_list]
    
    def save_model(self, filepath: str) -> None:
        """
        Save the model to disk
        
        Args:
            filepath: Path to save the model
        """
        if self.model is None:
            raise ValueError("Model not trained. Cannot save.")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        model_data = {
            "model": self.model,
            "preprocessor": self.preprocessor,
            "feature_names": self.feature_names,
            "numerical_features": self.numerical_features,
            "categorical_features": self.categorical_features,
            "training_metrics": self.training_metrics,
            "performance_thresholds": self.performance_thresholds,
            "model_type": self.model_type,
            "version": "1.0.0"
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str) -> None:
        """
        Load a model from disk
        
        Args:
            filepath: Path to the saved model
        """
        if not os.path.exists(filepath):
            raise ValueError(f"Model file does not exist: {filepath}")
        
        try:
            model_data = joblib.load(filepath)
            
            self.model = model_data["model"]
            self.preprocessor = model_data["preprocessor"]
            self.feature_names = model_data["feature_names"]
            self.numerical_features = model_data["numerical_features"]
            self.categorical_features = model_data["categorical_features"]
            self.training_metrics = model_data["training_metrics"]
            self.performance_thresholds = model_data["performance_thresholds"]
            self.model_type = model_data["model_type"]
            
            logger.info(f"Loaded model from {filepath}")
            logger.info(f"Model type: {self.model_type}, Version: {model_data.get('version', 'unknown')}")
            logger.info(f"Number of features: {len(self.feature_names)}")
            
            if "last_training_date" in self.training_metrics:
                logger.info(f"Last training date: {self.training_metrics['last_training_date']}")
            
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def get_model_info(self) -> Dict:
        """
        Get information about the model
        
        Returns:
            Dictionary with model info
        """
        return {
            "model_type": self.model_type,
            "training_metrics": self.training_metrics,
            "performance_thresholds": self.performance_thresholds,
            "feature_count": len(self.feature_names) if self.feature_names else 0,
            "is_trained": self.model is not None,
            "version": "1.0.0"
        }
    
    def visualize_impact(self, 
                        metrics: PerformanceMetrics, 
                        target_feature: str,
                        value_range: Optional[List[float]] = None) -> plt.Figure:
        """
        Visualize the impact of changing a specific feature on predictions
        
        Args:
            metrics: Base performance metrics
            target_feature: Feature to vary
            value_range: Range of values to try for the feature
            
        Returns:
            Matplotlib figure with visualization
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded. Cannot make predictions.")
        
        if target_feature not in self.numerical_features:
            raise ValueError(f"Target feature must be a numerical feature: {self.numerical_features}")
        
        # Set default range if not provided
        if value_range is None:
            base_value = getattr(metrics, target_feature)
            # Create range from 50% to 200% of current value
            value_range = np.linspace(max(0.5 * base_value, 0.1), 2.0 * base_value, 20)
        
        # Create predictions for each value
        results = []
        for value in value_range:
            # Create copy of metrics with new value
            new_metrics = PerformanceMetrics(**asdict(metrics))
            setattr(new_metrics, target_feature, value)
            
            # Make prediction
            impact = self.predict(new_metrics)
            
            results.append({
                "value": value,
                "lead_conversion_impact": impact.lead_conversion_impact,
                "bounce_rate_impact": impact.bounce_rate_impact,
                "session_duration_impact": impact.session_duration_impact,
                "engagement_score_impact": impact.engagement_score_impact
            })
        
        # Create DataFrame from results
        df = pd.DataFrame(results)
        
        # Create figure with 2x2 grid of plots
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle(f'Impact of {target_feature} on Business Metrics', fontsize=16)
        
        # Plot lead conversion impact
        axes[0, 0].plot(df['value'], df['lead_conversion_impact'], 'b-')
        axes[0, 0].axhline(y=0, color='r', linestyle='--')
        axes[0, 0].set_title('Lead Conversion Impact')
        axes[0, 0].set_xlabel(target_feature)
        axes[0, 0].set_ylabel('% Impact')
        axes[0, 0].grid(True)
        
        # Plot bounce rate impact
        axes[0, 1].plot(df['value'], df['bounce_rate_impact'], 'g-')
        axes[0, 1].axhline(y=0, color='r', linestyle='--')
        axes[0, 1].set_title('Bounce Rate Impact')
        axes[0, 1].set_xlabel(target_feature)
        axes[0, 1].set_ylabel('% Impact')
        axes[0, 1].grid(True)
        
        # Plot session duration impact
        axes[1, 0].plot(df['value'], df['session_duration_impact'], 'm-')
        axes[1, 0].axhline(y=0, color='r', linestyle='--')
        axes[1, 0].set_title('Session Duration Impact')
        axes[1, 0].set_xlabel(target_feature)
        axes[1, 0].set_ylabel('% Impact')
        axes[1, 0].grid(True)
        
        # Plot engagement score impact
        axes[1, 1].plot(df['value'], df['engagement_score_impact'], 'c-')
        axes[1, 1].axhline(y=0, color='r', linestyle='--')
        axes[1, 1].set_title('Engagement Score Impact')
        axes[1, 1].set_xlabel(target_feature)
        axes[1, 1].set_ylabel('% Impact')
        axes[1, 1].grid(True)
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        return fig 