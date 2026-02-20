"""
ML Inference Module: Load and use trained models in production
Provides simple API for predictions
"""

import os
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Optional, List, Tuple
from pathlib import Path

from ml_models import (
    QualityPredictorModel,
    CodeClassifierModel,
    AnomalyDetectorModel,
    ComplexityPredictorModel,
    SemanticSimilarityModel
)
from ml_data import CodeFeatureExtractor, EmbeddingGenerator


class ModelPredictor:
    """
    General-purpose model predictor for inference
    
    Usage:
        predictor = ModelPredictor('models/quality_predictor.pth', 'quality')
        score = predictor.predict_quality(code)
    """
    
    def __init__(self, model_path: str, model_type: str, device: str = 'cpu'):
        """
        Initialize predictor
        
        Args:
            model_path: Path to saved model weights
            model_type: 'quality', 'classifier', 'anomaly', 'complexity', 'similarity'
            device: 'cpu' or 'cuda'
        """
        self.model_path = model_path
        self.model_type = model_type
        self.device = device
        
        # Load model
        self.model = self._load_model()
        
        # Initialize helpers
        self.feature_extractor = CodeFeatureExtractor()
        try:
            self.embedding_generator = EmbeddingGenerator()
        except ImportError:
            self.embedding_generator = None
    
    def _load_model(self) -> nn.Module:
        """Load model from checkpoint"""
        if self.model_type == 'quality':
            model = QualityPredictorModel()
        elif self.model_type == 'classifier':
            model = CodeClassifierModel(num_classes=4)
        elif self.model_type == 'anomaly':
            model = AnomalyDetectorModel()
        elif self.model_type == 'complexity':
            model = ComplexityPredictorModel()
        elif self.model_type == 'similarity':
            model = SemanticSimilarityModel()
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        # Load weights
        if os.path.exists(self.model_path):
            model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            print(f"✓ Loaded model from {self.model_path}")
        else:
            print(f"⚠️  Model file not found: {self.model_path}")
        
        model.to(self.device)
        model.eval()
        
        return model
    
    def _prepare_features(self, code: str) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare embeddings and features from code"""
        # Extract features
        features_dict = self.feature_extractor.extract(code)
        features = self._dict_to_array(features_dict)
        
        # Generate embeddings
        if self.embedding_generator:
            embedding = self.embedding_generator.generate_single(code)
        else:
            # Fallback: random embeddings
            embedding = np.random.randn(768).astype(np.float32)
        
        return embedding, features
    
    def _dict_to_array(self, features_dict: Dict) -> np.ndarray:
        """Convert feature dict to normalized array"""
        feature_keys = [
            'token_count', 'line_count', 'avg_line_length', 'nesting_depth',
            'cyclomatic_complexity', 'num_functions', 'num_classes',
            'num_branches', 'num_loops', 'num_comments'
        ]
        
        values = [features_dict.get(k, 0) for k in feature_keys]
        normalized = np.array(values, dtype=np.float32)
        
        # Normalize to 0-1
        max_val = np.max(values) if np.max(values) > 0 else 1
        normalized = np.clip(normalized / max_val, 0, 1)
        
        return normalized[:50]
    
    def predict_quality(self, code: str) -> float:
        """
        Predict code quality (0-100)
        
        Args:
            code: Source code string
            
        Returns:
            quality_score: Predicted quality (0-100)
        """
        if self.model_type != 'quality':
            raise ValueError("Model type must be 'quality'")
        
        embedding, features = self._prepare_features(code)
        
        # Prepare tensors
        embedding_tensor = torch.tensor(embedding, dtype=torch.float32).unsqueeze(0).to(self.device)
        features_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(self.device)
        
        # Predict
        with torch.no_grad():
            quality = self.model(embedding_tensor, features_tensor)
        
        return quality.item()
    
    def predict_classification(self, code: str) -> Dict:
        """
        Classify code (Clean, Bug, Performance Issue, Security Issue)
        
        Args:
            code: Source code string
            
        Returns:
            classification: {
                'class': predicted class name,
                'probabilities': {class_name: probability, ...},
                'confidence': confidence score
            }
        """
        if self.model_type != 'classifier':
            raise ValueError("Model type must be 'classifier'")
        
        embedding, features = self._prepare_features(code)
        
        embedding_tensor = torch.tensor(embedding, dtype=torch.float32).unsqueeze(0).to(self.device)
        features_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            logits = self.model(embedding_tensor, features_tensor)
            probabilities = torch.softmax(logits, dim=1)
        
        class_names = ['Clean', 'Bug', 'Performance Issue', 'Security Issue']
        probs = probabilities[0].cpu().numpy()
        predicted_class = class_names[np.argmax(probs)]
        confidence = float(np.max(probs))
        
        return {
            'class': predicted_class,
            'probabilities': {name: float(prob) for name, prob in zip(class_names, probs)},
            'confidence': confidence
        }
    
    def predict_anomaly(self, code: str, threshold: float = 0.5) -> Dict:
        """
        Detect anomalies in code
        
        Args:
            code: Source code string
            threshold: Anomaly score threshold (higher = more anomalous)
            
        Returns:
            anomaly: {
                'is_anomaly': bool,
                'anomaly_score': score,
                'threshold': threshold
            }
        """
        if self.model_type != 'anomaly':
            raise ValueError("Model type must be 'anomaly'")
        
        embedding, features = self._prepare_features(code)
        combined = np.concatenate([embedding, features])
        
        combined_tensor = torch.tensor(combined, dtype=torch.float32).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            anomaly_score = self.model.anomaly_score(combined_tensor)
        
        score = float(anomaly_score[0].cpu().numpy())
        is_anomaly = score > threshold
        
        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': score,
            'threshold': threshold
        }
    
    def predict_complexity(self, code: str) -> float:
        """
        Predict code complexity (1-10)
        
        Args:
            code: Source code string
            
        Returns:
            complexity_score: Predicted complexity (1-10)
        """
        if self.model_type != 'complexity':
            raise ValueError("Model type must be 'complexity'")
        
        _, features = self._prepare_features(code)
        
        features_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            complexity = self.model(features_tensor)
        
        return float(complexity[0].cpu().numpy())
    
    def predict_similarity(self, code1: str, code2: str) -> float:
        """
        Calculate semantic similarity between two code snippets
        
        Args:
            code1: First code snippet
            code2: Second code snippet
            
        Returns:
            similarity: Cosine similarity (-1 to 1)
        """
        if self.model_type != 'similarity':
            raise ValueError("Model type must be 'similarity'")
        
        embedding1, _ = self._prepare_features(code1)
        embedding2, _ = self._prepare_features(code2)
        
        embedding1_tensor = torch.tensor(embedding1, dtype=torch.float32).unsqueeze(0).to(self.device)
        embedding2_tensor = torch.tensor(embedding2, dtype=torch.float32).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            similarity = self.model(embedding1_tensor, embedding2_tensor)
        
        return float(similarity[0].cpu().numpy())


class MultiModelPredictor:
    """
    Predictor that uses multiple models for comprehensive analysis
    """
    
    def __init__(self, model_dir: str = 'models', device: str = 'cpu'):
        """
        Initialize with multiple models
        
        Args:
            model_dir: Directory containing saved models
            device: 'cpu' or 'cuda'
        """
        self.device = device
        self.models = {}
        
        # Load available models
        model_configs = [
            ('quality_predictor.pth', 'quality'),
            ('code_classifier.pth', 'classifier'),
            ('anomaly_detector.pth', 'anomaly'),
            ('complexity_predictor.pth', 'complexity'),
            ('semantic_similarity.pth', 'similarity'),
        ]
        
        for model_file, model_type in model_configs:
            model_path = os.path.join(model_dir, model_file)
            if os.path.exists(model_path):
                try:
                    self.models[model_type] = ModelPredictor(model_path, model_type, device)
                except Exception as e:
                    print(f"⚠️  Failed to load {model_type}: {e}")
    
    def analyze(self, code: str) -> Dict:
        """
        Comprehensive code analysis using all available models
        
        Args:
            code: Source code string
            
        Returns:
            analysis: Dictionary with all predictions
        """
        results = {'code_preview': code[:100] + '...' if len(code) > 100 else code}
        
        # Quality prediction
        if 'quality' in self.models:
            results['quality'] = self.models['quality'].predict_quality(code)
        
        # Classification
        if 'classifier' in self.models:
            results['classification'] = self.models['classifier'].predict_classification(code)
        
        # Anomaly detection
        if 'anomaly' in self.models:
            results['anomaly'] = self.models['anomaly'].predict_anomaly(code)
        
        # Complexity
        if 'complexity' in self.models:
            results['complexity'] = self.models['complexity'].predict_complexity(code)
        
        return results


if __name__ == '__main__':
    print("ML Inference Module\n")
    
    # Test code
    test_code = """
    def calculate(a, b):
        return a + b
    """
    
    print("1. Quality Prediction:")
    try:
        predictor = ModelPredictor('models/quality_predictor.pth', 'quality')
        score = predictor.predict_quality(test_code)
        print(f"   Quality score: {score:.1f}/100")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n2. Complexity Prediction:")
    try:
        predictor = ModelPredictor('models/complexity_predictor.pth', 'complexity')
        complexity = predictor.predict_complexity(test_code)
        print(f"   Complexity: {complexity:.1f}/10")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n3. Multi-Model Analysis:")
    try:
        multi_predictor = MultiModelPredictor()
        analysis = multi_predictor.analyze(test_code)
        print(f"   Analysis: {analysis}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n✅ Inference module ready!")
