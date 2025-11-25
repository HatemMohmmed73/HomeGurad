"""
Anomaly Detection Module using Isolation Forest
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime
from typing import Dict, Any, List

from config import settings
from database.models import AnomalyResult


class AnomalyDetector:
    """ML-based anomaly detection for network traffic"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.threshold = settings.ANOMALY_THRESHOLD
        self.feature_names = [
            'duration', 'orig_bytes', 'resp_bytes', 'orig_pkts', 
            'resp_pkts', 'orig_ip_bytes', 'resp_ip_bytes', 'port'
        ]
        self.protocol_mapping = {'tcp': 0, 'udp': 1, 'icmp': 2, 'other': 3}
        
        # Model metadata
        self.model_loaded = False
        self.last_trained = None
        self.total_predictions = 0
        self.anomaly_count = 0
        
        # Load existing model if available
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained model from disk"""
        try:
            if os.path.exists(settings.MODEL_PATH) and os.path.exists(settings.SCALER_PATH):
                self.model = joblib.load(settings.MODEL_PATH)
                self.scaler = joblib.load(settings.SCALER_PATH)
                self.model_loaded = True
                print(f"✅ ML Model loaded from {settings.MODEL_PATH}")
            else:
                print("⚠️  No pre-trained model found. Creating default model.")
                self._create_default_model()
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self._create_default_model()
    
    def _create_default_model(self):
        """Create a default Isolation Forest model"""
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.1,
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        
        # Generate dummy data to fit the model
        dummy_data = np.random.randn(100, len(self.feature_names))
        self.scaler.fit(dummy_data)
        self.model.fit(self.scaler.transform(dummy_data))
        
        self.model_loaded = True
        print("✅ Default ML model created")
    
    def _preprocess_features(self, features: Dict[str, Any]) -> np.ndarray:
        """Preprocess raw features for model input"""
        # Extract numeric features
        feature_values = []
        for feature_name in self.feature_names:
            if feature_name == 'port':
                # Normalize port number
                feature_values.append(features.get(feature_name, 0) / 65535.0)
            else:
                feature_values.append(features.get(feature_name, 0))
        
        # Convert protocol to numeric
        protocol = features.get('protocol', 'other').lower()
        protocol_value = self.protocol_mapping.get(protocol, 3)
        feature_values.append(protocol_value)
        
        return np.array(feature_values).reshape(1, -1)
    
    def predict(self, features: Dict[str, Any]) -> AnomalyResult:
        """
        Run anomaly detection on network flow features
        
        Args:
            features: Dictionary containing flow features
            
        Returns:
            AnomalyResult with prediction and explanation
        """
        if not self.model_loaded:
            raise RuntimeError("ML model not loaded")
        
        # Preprocess features
        X = self._preprocess_features(features)
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Predict
        prediction = self.model.predict(X_scaled)[0]  # -1 for anomaly, 1 for normal
        anomaly_score_raw = self.model.score_samples(X_scaled)[0]
        
        # Convert score to 0-1 range (higher = more anomalous)
        # Isolation Forest scores are negative, so we transform them
        anomaly_score = self._normalize_score(anomaly_score_raw)
        
        # Determine if anomaly
        is_anomaly = anomaly_score > self.threshold
        
        # Update metrics
        self.total_predictions += 1
        if is_anomaly:
            self.anomaly_count += 1
        
        # Generate explanation
        explanation = self._generate_explanation(features, anomaly_score, is_anomaly)
        
        # Calculate confidence
        confidence = abs(anomaly_score - self.threshold)
        
        return AnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_score=round(anomaly_score, 3),
            confidence=round(min(confidence, 1.0), 3),
            explanation=explanation
        )
    
    def _normalize_score(self, score: float) -> float:
        """
        Normalize Isolation Forest score to 0-1 range
        Isolation Forest returns negative scores, more negative = more anomalous
        """
        # Typical range is around -0.5 to 0.5
        # We'll map this to 0-1 where 1 is most anomalous
        normalized = 1 / (1 + np.exp(score * 2))  # Sigmoid transformation
        return float(normalized)
    
    def _generate_explanation(self, features: Dict[str, Any], score: float, is_anomaly: bool) -> str:
        """Generate human-readable explanation"""
        if not is_anomaly:
            return "Traffic appears normal based on learned patterns."
        
        # Analyze which features are unusual
        explanations = []
        
        # Check data volume
        total_bytes = features.get('orig_bytes', 0) + features.get('resp_bytes', 0)
        if total_bytes > 1_000_000:  # > 1MB
            explanations.append("unusually high data volume")
        
        # Check duration
        duration = features.get('duration', 0)
        if duration > 300:  # > 5 minutes
            explanations.append("prolonged connection duration")
        elif duration < 0.1:
            explanations.append("very short connection")
        
        # Check port
        port = features.get('port', 0)
        if port > 49151:  # Dynamic/private port
            explanations.append("connection to unusual port")
        
        # Check packet counts
        orig_pkts = features.get('orig_pkts', 0)
        if orig_pkts > 1000:
            explanations.append("high packet count")
        
        if explanations:
            reason = "Detected: " + ", ".join(explanations)
        else:
            reason = f"Behavioral pattern deviates from normal (score: {score:.2f})"
        
        return reason
    
    def retrain(self, training_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrain the model with new data
        
        Args:
            training_data: List of feature dictionaries
            
        Returns:
            Training results and metrics
        """
        if training_data is None or len(training_data) < 50:
            return {
                "status": "skipped",
                "reason": "Insufficient training data (minimum 50 samples required)"
            }
        
        # Preprocess training data
        X = []
        for features in training_data:
            X.append(self._preprocess_features(features).flatten())
        
        X = np.array(X)
        
        # Fit scaler and model
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.1,
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X_scaled)
        
        # Save model
        os.makedirs(os.path.dirname(settings.MODEL_PATH), exist_ok=True)
        joblib.dump(self.model, settings.MODEL_PATH)
        joblib.dump(self.scaler, settings.SCALER_PATH)
        
        self.last_trained = datetime.utcnow()
        
        return {
            "status": "success",
            "samples_trained": len(training_data),
            "timestamp": self.last_trained.isoformat()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get model status and metadata"""
        return {
            "model_loaded": self.model_loaded,
            "model_type": "Isolation Forest",
            "threshold": self.threshold,
            "last_trained": self.last_trained.isoformat() if self.last_trained else None,
            "total_predictions": self.total_predictions,
            "anomaly_count": self.anomaly_count,
            "anomaly_rate": round(self.anomaly_count / max(self.total_predictions, 1), 3)
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get model performance metrics"""
        return {
            "total_predictions": self.total_predictions,
            "anomaly_count": self.anomaly_count,
            "normal_count": self.total_predictions - self.anomaly_count,
            "anomaly_rate": round(self.anomaly_count / max(self.total_predictions, 1), 3),
            "current_threshold": self.threshold
        }
    
    def update_threshold(self, new_threshold: float):
        """Update anomaly detection threshold"""
        if not 0 <= new_threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        self.threshold = new_threshold
        print(f"✅ Anomaly threshold updated to {new_threshold}")

