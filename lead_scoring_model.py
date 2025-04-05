"""
Guards & Robbers Lead Scoring Model

This module implements a gradient boosting-based lead scoring model that predicts
the quality of leads based on form data and user behavior, with configurable
thresholds controlled by the ML Growth Control Module.

Version: 1.0.0
Created: May 16, 2025
"""

import os
import pickle
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple, Any
import logging
from dataclasses import dataclass
import datetime
import joblib
from sklearn.ensemble import GradientBoostingClassifier
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, precision_recall_curve, average_precision_score
import shap

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("lead_scoring.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("lead_scoring")

@dataclass
class LeadData:
    """Data class for storing lead information"""
    # Form data
    email: str
    company_size: Optional[str] = None
    industry: Optional[str] = None
    job_title: Optional[str] = None
    use_case: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    marketing_consent: bool = False
    
    # Behavioral data
    page_views: int = 0
    time_on_site: float = 0.0  # seconds
    pages_per_session: float = 0.0
    source: Optional[str] = None
    medium: Optional[str] = None
    campaign: Optional[str] = None
    device_type: Optional[str] = None
    visit_count: int = 1
    
    # Additional metadata
    timestamp: datetime.datetime = datetime.datetime.now()
    lead_id: Optional[str] = None

@dataclass
class ScoredLead:
    """Data class for storing scored lead information"""
    lead_data: LeadData
    quality_score: float
    quality_tier: str  # A, B, C
    confidence: float
    requires_review: bool
    explanation: Dict[str, float]  # Feature importance
    timestamp: datetime.datetime = datetime.datetime.now()

class LeadScoringModel:
    """
    Machine learning model for scoring leads based on form data and user behavior.
    
    This model:
    1. Processes both structured form data and behavioral signals
    2. Predicts lead quality score (0-1)
    3. Classifies leads into quality tiers (A, B, C)
    4. Provides explainability through SHAP values
    5. Integrates with the ML Growth Control Module for threshold adjustment
    """
    
    def __init__(self, 
                 model_type: str = "xgboost", 
                 model_path: Optional[str] = None,
                 control_params: Optional[Dict] = None):
        """
        Initialize the lead scoring model
        
        Args:
            model_type: Type of model to use (xgboost, gradient_boosting)
            model_path: Path to saved model file (for loading existing model)
            control_params: Parameters from growth control module
        """
        self.model_type = model_type
        self.model_path = model_path
        self.model = None
        self.feature_names = []
        self.preprocessor = None
        self.shap_explainer = None
        
        # Default control parameters (if not provided by growth control module)
        self.control_params = control_params or {
            "quality_threshold": 0.5,
            "confidence_threshold": 0.75,
            "review_threshold": 0.9
        }
        
        # Training metrics
        self.training_metrics = {
            "last_training_date": None,
            "auc_score": None,
            "average_precision": None,
            "data_size": None
        }
        
        # Quality tier thresholds
        self.tier_thresholds = {
            "A": 0.8,  # 80%+ likelihood of conversion
            "B": 0.5,  # 50-80% likelihood of conversion
            "C": 0.0   # <50% likelihood of conversion
        }
        
        # If model path is provided, load the existing model
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
            logger.info(f"Loaded lead scoring model from {model_path}")
        else:
            logger.info("Initialized new lead scoring model - training required")
    
    def update_control_params(self, new_params: Dict) -> None:
        """
        Update control parameters from the growth control module
        
        Args:
            new_params: New parameters from growth control module
        """
        self.control_params.update(new_params)
        logger.info(f"Updated control parameters: quality_threshold={self.control_params['quality_threshold']:.2f}")
    
    def preprocess_features(self, leads_data: List[LeadData], fit: bool = False) -> pd.DataFrame:
        """
        Preprocess lead data into features for the model
        
        Args:
            leads_data: List of lead data objects
            fit: Whether to fit the preprocessor (for training) or just transform
            
        Returns:
            DataFrame with preprocessed features
        """
        # Convert lead data to DataFrame
        data = []
        for lead in leads_data:
            lead_dict = {
                # Form features
                "company_size": lead.company_size,
                "industry": lead.industry,
                "job_title": lead.job_title,
                "use_case": lead.use_case,
                "budget_range": lead.budget_range,
                "timeline": lead.timeline,
                "marketing_consent": int(lead.marketing_consent),
                
                # Behavioral features
                "page_views": lead.page_views,
                "time_on_site": lead.time_on_site,
                "pages_per_session": lead.pages_per_session,
                "source": lead.source,
                "medium": lead.medium,
                "campaign": lead.campaign,
                "device_type": lead.device_type,
                "visit_count": lead.visit_count,
                
                # Time features
                "hour_of_day": lead.timestamp.hour,
                "day_of_week": lead.timestamp.weekday(),
                "weekend": 1 if lead.timestamp.weekday() >= 5 else 0
            }
            data.append(lead_dict)
        
        df = pd.DataFrame(data)
        
        # If fitting the preprocessor (training mode)
        if fit:
            # Define categorical and numerical features
            categorical_features = [
                "company_size", "industry", "job_title", 
                "use_case", "budget_range", "timeline",
                "source", "medium", "campaign", "device_type"
            ]
            
            numerical_features = [
                "page_views", "time_on_site", "pages_per_session", 
                "visit_count", "marketing_consent", 
                "hour_of_day", "day_of_week", "weekend"
            ]
            
            # Create column transformer for preprocessing
            self.preprocessor = ColumnTransformer(
                transformers=[
                    ("num", StandardScaler(), numerical_features),
                    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
                ],
                remainder="drop"
            )
            
            # Fit the preprocessor
            X_processed = self.preprocessor.fit_transform(df)
            
            # Get feature names
            num_feature_names = numerical_features
            
            # Get one-hot encoded feature names
            cat_encoder = self.preprocessor.named_transformers_["cat"]
            cat_feature_names = []
            for i, col in enumerate(categorical_features):
                cats = cat_encoder.categories_[i]
                cat_feature_names.extend([f"{col}_{cat}" for cat in cats])
            
            self.feature_names = num_feature_names + cat_feature_names
            
            # Some models need dense input, others can handle sparse
            if self.model_type == "xgboost":
                return pd.DataFrame(X_processed.toarray(), columns=self.feature_names)
            else:
                return X_processed
            
        # If just transforming (inference mode)
        else:
            if self.preprocessor is None:
                raise ValueError("Preprocessor not fitted. Cannot transform data.")
            
            X_processed = self.preprocessor.transform(df)
            
            # Some models need dense input
            if self.model_type == "xgboost":
                return pd.DataFrame(X_processed.toarray(), columns=self.feature_names)
            else:
                return X_processed
    
    def train(self, 
              leads_data: List[LeadData], 
              lead_outcomes: List[int],
              validation_split: float = 0.2) -> Dict:
        """
        Train the lead scoring model
        
        Args:
            leads_data: List of lead data objects
            lead_outcomes: Binary outcomes (1 for converted, 0 for not converted)
            validation_split: Proportion of data to use for validation
            
        Returns:
            Dictionary of training metrics
        """
        if len(leads_data) != len(lead_outcomes):
            raise ValueError("Length of leads_data and lead_outcomes must be the same")
        
        logger.info(f"Training lead scoring model on {len(leads_data)} samples")
        
        # Preprocess features
        X = self.preprocess_features(leads_data, fit=True)
        y = np.array(lead_outcomes)
        
        # Split into training and validation sets
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42, stratify=y
        )
        
        # Initialize and train model based on type
        if self.model_type == "xgboost":
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                min_child_weight=1,
                subsample=0.8,
                colsample_bytree=0.8,
                objective="binary:logistic",
                random_state=42
            )
        else:  # gradient_boosting
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                min_samples_split=2,
                min_samples_leaf=1,
                subsample=0.8,
                random_state=42
            )
        
        # Train the model
        self.model.fit(X_train, y_train)
        
        # Evaluate the model
        y_pred_proba = self.model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, y_pred_proba)
        avg_precision = average_precision_score(y_val, y_pred_proba)
        
        # Initialize SHAP explainer
        if self.model_type == "xgboost":
            self.shap_explainer = shap.TreeExplainer(self.model)
        else:
            self.shap_explainer = shap.TreeExplainer(self.model)
        
        # Store training metrics
        self.training_metrics = {
            "last_training_date": datetime.datetime.now().isoformat(),
            "auc_score": auc,
            "average_precision": avg_precision,
            "data_size": len(leads_data)
        }
        
        logger.info(f"Model training completed. AUC: {auc:.3f}, Avg Precision: {avg_precision:.3f}")
        
        return self.training_metrics
    
    def predict(self, lead_data: LeadData) -> ScoredLead:
        """
        Score a single lead
        
        Args:
            lead_data: Lead data object
            
        Returns:
            ScoredLead object with quality score, tier, and explanation
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded. Cannot make predictions.")
        
        # Preprocess the lead data
        X = self.preprocess_features([lead_data], fit=False)
        
        # Make prediction
        quality_score = float(self.model.predict_proba(X)[0, 1])
        
        # Determine quality tier
        quality_tier = "C"  # Default tier
        for tier, threshold in sorted(self.tier_thresholds.items(), key=lambda x: x[1], reverse=True):
            if quality_score >= threshold:
                quality_tier = tier
                break
        
        # Generate explanation using SHAP
        explanation = {}
        if self.shap_explainer is not None:
            shap_values = self.shap_explainer.shap_values(X)
            
            if isinstance(shap_values, list):  # Some models return a list for binary classification
                shap_values = shap_values[1]  # Get the values for the positive class
                
            # Get top features by importance
            feature_importance = dict(zip(self.feature_names, np.abs(shap_values[0])))
            top_features = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5])
            explanation = top_features
        
        # Determine confidence and review flag
        # Confidence is higher when score is far from decision boundary
        confidence = max(abs(quality_score - 0.5) * 2, 0.1)  # Scale to 0.1-1.0
        
        # Flag for manual review if quality score is high but confidence is low
        # or if score is very close to the quality threshold
        quality_threshold = self.control_params["quality_threshold"]
        confidence_threshold = self.control_params["confidence_threshold"]
        review_threshold = self.control_params["review_threshold"]
        
        requires_review = (
            (quality_score >= review_threshold and confidence < confidence_threshold) or
            (abs(quality_score - quality_threshold) < 0.05)
        )
        
        scored_lead = ScoredLead(
            lead_data=lead_data,
            quality_score=quality_score,
            quality_tier=quality_tier,
            confidence=confidence,
            requires_review=requires_review,
            explanation=explanation
        )
        
        return scored_lead
    
    def batch_predict(self, leads_data: List[LeadData]) -> List[ScoredLead]:
        """
        Score multiple leads
        
        Args:
            leads_data: List of lead data objects
            
        Returns:
            List of ScoredLead objects
        """
        return [self.predict(lead) for lead in leads_data]
    
    def save_model(self, filepath: str) -> None:
        """
        Save the model to disk
        
        Args:
            filepath: Path to save the model
        """
        if self.model is None:
            raise ValueError("Model not trained. Cannot save.")
        
        model_data = {
            "model": self.model,
            "preprocessor": self.preprocessor,
            "feature_names": self.feature_names,
            "training_metrics": self.training_metrics,
            "tier_thresholds": self.tier_thresholds,
            "model_type": self.model_type,
            "version": "1.0.0"
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str) -> None:
        """
        Load the model from disk
        
        Args:
            filepath: Path to load the model from
        """
        model_data = joblib.load(filepath)
        
        self.model = model_data["model"]
        self.preprocessor = model_data["preprocessor"]
        self.feature_names = model_data["feature_names"]
        self.training_metrics = model_data["training_metrics"]
        self.tier_thresholds = model_data["tier_thresholds"]
        self.model_type = model_data["model_type"]
        
        # Initialize SHAP explainer
        if self.model is not None:
            if self.model_type == "xgboost":
                self.shap_explainer = shap.TreeExplainer(self.model)
            else:
                self.shap_explainer = shap.TreeExplainer(self.model)
        
        logger.info(f"Model loaded from {filepath}")
    
    def get_model_info(self) -> Dict:
        """
        Get information about the model
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_type": self.model_type,
            "training_metrics": self.training_metrics,
            "tier_thresholds": self.tier_thresholds,
            "control_params": self.control_params,
            "feature_count": len(self.feature_names) if self.feature_names else 0,
            "is_trained": self.model is not None
        }


# Example usage
if __name__ == "__main__":
    # Create some example lead data for demonstration
    example_leads = [
        LeadData(
            email="high_value@example.com",
            company_size="100-500",
            industry="Finance",
            job_title="CTO",
            use_case="Security",
            budget_range="$50k-$100k",
            timeline="1-3 months",
            marketing_consent=True,
            page_views=15,
            time_on_site=450.0,
            pages_per_session=5.2,
            source="google",
            medium="organic",
            device_type="desktop",
            visit_count=3
        ),
        LeadData(
            email="medium_value@example.com",
            company_size="1-50",
            industry="Retail",
            job_title="IT Manager",
            use_case="Compliance",
            budget_range="$10k-$50k",
            timeline="3-6 months",
            marketing_consent=True,
            page_views=8,
            time_on_site=180.0,
            pages_per_session=3.1,
            source="linkedin",
            medium="social",
            device_type="mobile",
            visit_count=2
        ),
        LeadData(
            email="low_value@example.com",
            company_size="1-50",
            industry="Education",
            job_title="Staff",
            use_case="General",
            budget_range="Under $10k",
            timeline="6-12 months",
            marketing_consent=False,
            page_views=2,
            time_on_site=45.0,
            pages_per_session=1.5,
            source="direct",
            medium="none",
            device_type="tablet",
            visit_count=1
        )
    ]
    
    # Simulate conversion outcomes
    # In a real scenario, these would come from CRM data
    outcomes = [1, 1, 0]  # High and medium converted, low didn't
    
    # Initialize and train model
    lead_model = LeadScoringModel(model_type="xgboost")
    
    # Train the model
    metrics = lead_model.train(example_leads, outcomes)
    print(f"Training metrics: {metrics}")
    
    # Score a new lead
    new_lead = LeadData(
        email="prospect@example.com",
        company_size="500+",
        industry="Healthcare",
        job_title="CISO",
        use_case="Compliance",
        budget_range="$50k-$100k",
        timeline="1-3 months",
        marketing_consent=True,
        page_views=12,
        time_on_site=320.0,
        pages_per_session=4.2,
        source="bing",
        medium="paid",
        device_type="desktop",
        visit_count=2
    )
    
    scored_lead = lead_model.predict(new_lead)
    print(f"Lead score: {scored_lead.quality_score:.2f}, Tier: {scored_lead.quality_tier}")
    print(f"Top factors: {scored_lead.explanation}")
    
    # Save the model
    lead_model.save_model("lead_scoring_model.joblib")
    
    # Update control parameters (as if from growth control module)
    lead_model.update_control_params({"quality_threshold": 0.6})
    
    # Score same lead with new parameters
    scored_lead_updated = lead_model.predict(new_lead)
    print(f"Updated lead score: {scored_lead_updated.quality_score:.2f}, Tier: {scored_lead_updated.quality_tier}") 