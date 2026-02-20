"""
Traditional ML Models: Logistic Regression, SVM, XGBoost, Random Forest
Compare traditional ML with deep learning approaches
"""

import numpy as np
from typing import Tuple, Dict, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC, SVR
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import json
from pathlib import Path


class TraditionalMLModels:
    """
    Collection of traditional ML models for code analysis
    Models included:
    - Logistic Regression (classification)
    - Support Vector Machine (classification & regression)
    - Random Forest (classification & regression)
    - XGBoost (requires installation)
    """
    
    def __init__(self, model_dir: str = 'models/traditional'):
        """Initialize traditional ML models directory"""
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.scaler = StandardScaler()
        self.models = {}
    
    # ==================== CLASSIFICATION MODELS ====================
    
    def train_logistic_regression(self, X_train: np.ndarray, y_train: np.ndarray,
                                  C: float = 1.0, max_iter: int = 1000) -> Dict:
        """
        Train Logistic Regression for code classification
        
        Args:
            X_train: Training features (N, features)
            y_train: Training labels (N,)
            C: Inverse of regularization strength
            max_iter: Max iterations
            
        Returns:
            metrics: Training metrics
        """
        print("🔹 Training Logistic Regression...")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Create and train model
        model = LogisticRegression(C=C, max_iter=max_iter, random_state=42)
        model.fit(X_train_scaled, y_train)
        
        # Save model
        self.models['logistic_regression'] = (model, self.scaler)
        joblib.dump(model, f"{self.model_dir}/logistic_regression.pkl")
        joblib.dump(self.scaler, f"{self.model_dir}/scaler_lr.pkl")
        
        # Get accuracy
        train_score = model.score(X_train_scaled, y_train)
        
        print(f"   ✓ Training accuracy: {train_score:.4f}")
        
        return {
            'model': 'Logistic Regression',
            'training_accuracy': train_score,
            'parameters': {'C': C, 'max_iter': max_iter}
        }
    
    def train_svm_classifier(self, X_train: np.ndarray, y_train: np.ndarray,
                            kernel: str = 'rbf', C: float = 1.0) -> Dict:
        """
        Train SVM (Support Vector Machine) for classification
        
        Args:
            X_train: Training features
            y_train: Training labels (0/1)
            kernel: 'linear', 'rbf', 'poly'
            C: Regularization parameter
            
        Returns:
            metrics: Training metrics
        """
        print("🔹 Training SVM Classifier...")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Create and train model
        model = SVC(kernel=kernel, C=C, random_state=42, probability=True)
        model.fit(X_train_scaled, y_train)
        
        # Save model
        self.models['svm_classifier'] = (model, self.scaler)
        joblib.dump(model, f"{self.model_dir}/svm_classifier.pkl")
        joblib.dump(self.scaler, f"{self.model_dir}/scaler_svm.pkl")
        
        # Get accuracy
        train_score = model.score(X_train_scaled, y_train)
        
        print(f"   ✓ Training accuracy: {train_score:.4f}")
        
        return {
            'model': 'SVM Classifier',
            'training_accuracy': train_score,
            'parameters': {'kernel': kernel, 'C': C}
        }
    
    def train_random_forest_classifier(self, X_train: np.ndarray, y_train: np.ndarray,
                                       n_estimators: int = 100) -> Dict:
        """
        Train Random Forest for classification
        
        Args:
            X_train: Training features
            y_train: Training labels
            n_estimators: Number of trees
            
        Returns:
            metrics: Training metrics
        """
        print("🔹 Training Random Forest Classifier...")
        
        # No scaling needed for tree-based models
        model = RandomForestClassifier(n_estimators=n_estimators, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        
        # Save model
        self.models['random_forest_classifier'] = model
        joblib.dump(model, f"{self.model_dir}/random_forest_classifier.pkl")
        
        # Get accuracy
        train_score = model.score(X_train, y_train)
        
        print(f"   ✓ Training accuracy: {train_score:.4f}")
        
        # Feature importance
        importance = dict(zip(range(len(model.feature_importances_)), 
                            model.feature_importances_))
        
        return {
            'model': 'Random Forest Classifier',
            'training_accuracy': train_score,
            'parameters': {'n_estimators': n_estimators},
            'feature_importance': importance
        }
    
    # ==================== REGRESSION MODELS ====================
    
    def train_svm_regressor(self, X_train: np.ndarray, y_train: np.ndarray,
                           kernel: str = 'rbf', C: float = 1.0) -> Dict:
        """
        Train SVM for regression (quality prediction)
        
        Args:
            X_train: Training features
            y_train: Training targets (continuous)
            kernel: 'linear', 'rbf', 'poly'
            C: Regularization parameter
            
        Returns:
            metrics: Training metrics
        """
        print("🔹 Training SVM Regressor...")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Create and train model
        model = SVR(kernel=kernel, C=C)
        model.fit(X_train_scaled, y_train)
        
        # Save model
        self.models['svm_regressor'] = (model, self.scaler)
        joblib.dump(model, f"{self.model_dir}/svm_regressor.pkl")
        
        # Get R² score
        r2_score = model.score(X_train_scaled, y_train)
        
        print(f"   ✓ Training R² score: {r2_score:.4f}")
        
        return {
            'model': 'SVM Regressor',
            'training_r2_score': r2_score,
            'parameters': {'kernel': kernel, 'C': C}
        }
    
    def train_random_forest_regressor(self, X_train: np.ndarray, y_train: np.ndarray,
                                      n_estimators: int = 100) -> Dict:
        """
        Train Random Forest for regression (quality prediction)
        
        Args:
            X_train: Training features
            y_train: Training targets (0-100)
            n_estimators: Number of trees
            
        Returns:
            metrics: Training metrics
        """
        print("🔹 Training Random Forest Regressor...")
        
        # Create and train model
        model = RandomForestRegressor(n_estimators=n_estimators, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        
        # Save model
        self.models['random_forest_regressor'] = model
        joblib.dump(model, f"{self.model_dir}/random_forest_regressor.pkl")
        
        # Get R² score
        r2_score = model.score(X_train, y_train)
        
        print(f"   ✓ Training R² score: {r2_score:.4f}")
        
        # Feature importance
        importance = dict(zip(range(len(model.feature_importances_)), 
                            model.feature_importances_))
        
        return {
            'model': 'Random Forest Regressor',
            'training_r2_score': r2_score,
            'parameters': {'n_estimators': n_estimators},
            'feature_importance': importance
        }
    
    # ==================== XGBOOST MODELS ====================
    
    def train_xgboost_classifier(self, X_train: np.ndarray, y_train: np.ndarray,
                                max_depth: int = 6, n_estimators: int = 100) -> Dict:
        """
        Train XGBoost classifier
        
        Args:
            X_train: Training features
            y_train: Training labels
            max_depth: Tree depth
            n_estimators: Number of boosting stages
            
        Returns:
            metrics: Training metrics
        """
        try:
            import xgboost as xgb
        except ImportError:
            print("   ⚠️  XGBoost not installed. Install with: pip install xgboost")
            return {'error': 'XGBoost not installed'}
        
        print("🔹 Training XGBoost Classifier...")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Create and train model
        model = xgb.XGBClassifier(
            max_depth=max_depth,
            n_estimators=n_estimators,
            random_state=42,
            eval_metric='logloss'
        )
        model.fit(X_train_scaled, y_train)
        
        # Save model
        self.models['xgboost_classifier'] = (model, self.scaler)
        model.save_model(f"{self.model_dir}/xgboost_classifier.json")
        
        # Get accuracy
        train_score = model.score(X_train_scaled, y_train)
        
        print(f"   ✓ Training accuracy: {train_score:.4f}")
        
        return {
            'model': 'XGBoost Classifier',
            'training_accuracy': train_score,
            'parameters': {'max_depth': max_depth, 'n_estimators': n_estimators}
        }
    
    def train_xgboost_regressor(self, X_train: np.ndarray, y_train: np.ndarray,
                               max_depth: int = 6, n_estimators: int = 100) -> Dict:
        """
        Train XGBoost regressor (quality prediction)
        
        Args:
            X_train: Training features
            y_train: Training targets (0-100)
            max_depth: Tree depth
            n_estimators: Number of boosting stages
            
        Returns:
            metrics: Training metrics
        """
        try:
            import xgboost as xgb
        except ImportError:
            print("   ⚠️  XGBoost not installed. Install with: pip install xgboost")
            return {'error': 'XGBoost not installed'}
        
        print("🔹 Training XGBoost Regressor...")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Create and train model
        model = xgb.XGBRegressor(
            max_depth=max_depth,
            n_estimators=n_estimators,
            random_state=42
        )
        model.fit(X_train_scaled, y_train)
        
        # Save model
        self.models['xgboost_regressor'] = (model, self.scaler)
        model.save_model(f"{self.model_dir}/xgboost_regressor.json")
        
        # Get R² score
        r2_score = model.score(X_train_scaled, y_train)
        
        print(f"   ✓ Training R² score: {r2_score:.4f}")
        
        return {
            'model': 'XGBoost Regressor',
            'training_r2_score': r2_score,
            'parameters': {'max_depth': max_depth, 'n_estimators': n_estimators}
        }
    
    # ==================== PREDICTION ====================
    
    def predict_lr(self, features: np.ndarray) -> Tuple[int, float]:
        """Predict with Logistic Regression"""
        if 'logistic_regression' not in self.models:
            model, scaler = joblib.load(f"{self.model_dir}/logistic_regression.pkl"), \
                           joblib.load(f"{self.model_dir}/scaler_lr.pkl")
            self.models['logistic_regression'] = (model, scaler)
        
        model, scaler = self.models['logistic_regression']
        features_scaled = scaler.transform(features.reshape(1, -1))
        prediction = model.predict(features_scaled)[0]
        probability = model.predict_proba(features_scaled)[0]
        
        return prediction, max(probability)
    
    def predict_svm_clf(self, features: np.ndarray) -> Tuple[int, float]:
        """Predict with SVM Classifier"""
        if 'svm_classifier' not in self.models:
            model, scaler = joblib.load(f"{self.model_dir}/svm_classifier.pkl"), \
                           joblib.load(f"{self.model_dir}/scaler_svm.pkl")
            self.models['svm_classifier'] = (model, scaler)
        
        model, scaler = self.models['svm_classifier']
        features_scaled = scaler.transform(features.reshape(1, -1))
        prediction = model.predict(features_scaled)[0]
        probability = model.predict_proba(features_scaled)[0]
        
        return prediction, max(probability)
    
    def predict_rf_clf(self, features: np.ndarray) -> Tuple[int, float]:
        """Predict with Random Forest Classifier"""
        if 'random_forest_classifier' not in self.models:
            self.models['random_forest_classifier'] = joblib.load(
                f"{self.model_dir}/random_forest_classifier.pkl"
            )
        
        model = self.models['random_forest_classifier']
        prediction = model.predict(features.reshape(1, -1))[0]
        probability = model.predict_proba(features.reshape(1, -1))[0]
        
        return prediction, max(probability)
    
    def predict_svm_reg(self, features: np.ndarray) -> float:
        """Predict with SVM Regressor"""
        if 'svm_regressor' not in self.models:
            model, scaler = joblib.load(f"{self.model_dir}/svm_regressor.pkl"), \
                           joblib.load(f"{self.model_dir}/scaler_svm.pkl")
            self.models['svm_regressor'] = (model, scaler)
        
        model, scaler = self.models['svm_regressor']
        features_scaled = scaler.transform(features.reshape(1, -1))
        prediction = model.predict(features_scaled)[0]
        
        return float(np.clip(prediction, 0, 100))
    
    def predict_rf_reg(self, features: np.ndarray) -> float:
        """Predict with Random Forest Regressor"""
        if 'random_forest_regressor' not in self.models:
            self.models['random_forest_regressor'] = joblib.load(
                f"{self.model_dir}/random_forest_regressor.pkl"
            )
        
        model = self.models['random_forest_regressor']
        prediction = model.predict(features.reshape(1, -1))[0]
        
        return float(np.clip(prediction, 0, 100))
    
    def predict_xgb_clf(self, features: np.ndarray) -> Tuple[int, float]:
        """Predict with XGBoost Classifier"""
        try:
            import xgboost as xgb
            if 'xgboost_classifier' not in self.models:
                model = xgb.XGBClassifier()
                model.load_model(f"{self.model_dir}/xgboost_classifier.json")
                scaler = joblib.load(f"{self.model_dir}/scaler_svm.pkl")
                self.models['xgboost_classifier'] = (model, scaler)
            
            model, scaler = self.models['xgboost_classifier']
            features_scaled = scaler.transform(features.reshape(1, -1))
            prediction = model.predict(features_scaled)[0]
            probability = model.predict_proba(features_scaled)[0]
            
            return int(prediction), float(max(probability))
        except ImportError:
            return 0, 0.0
    
    def predict_xgb_reg(self, features: np.ndarray) -> float:
        """Predict with XGBoost Regressor"""
        try:
            import xgboost as xgb
            if 'xgboost_regressor' not in self.models:
                model = xgb.XGBRegressor()
                model.load_model(f"{self.model_dir}/xgboost_regressor.json")
                scaler = joblib.load(f"{self.model_dir}/scaler_svm.pkl")
                self.models['xgboost_regressor'] = (model, scaler)
            
            model, scaler = self.models['xgboost_regressor']
            features_scaled = scaler.transform(features.reshape(1, -1))
            prediction = model.predict(features_scaled)[0]
            
            return float(np.clip(prediction, 0, 100))
        except ImportError:
            return 0.0


if __name__ == '__main__':
    print("Traditional ML Models Module\n")
    
    # Generate sample data
    print("Generating sample data...")
    np.random.seed(42)
    X_train = np.random.randn(100, 50)  # 100 samples, 50 features
    y_train_clf = np.random.randint(0, 2, 100)  # Binary classification
    y_train_reg = np.random.rand(100) * 100  # Regression (0-100)
    
    # Initialize models
    ml_models = TraditionalMLModels()
    
    print("\n=== Classification Models ===")
    print("\n1. Logistic Regression:")
    lr_metrics = ml_models.train_logistic_regression(X_train, y_train_clf)
    print(f"   Accuracy: {lr_metrics['training_accuracy']:.4f}")
    
    print("\n2. SVM Classifier:")
    svm_clf_metrics = ml_models.train_svm_classifier(X_train, y_train_clf)
    print(f"   Accuracy: {svm_clf_metrics['training_accuracy']:.4f}")
    
    print("\n3. Random Forest Classifier:")
    rf_clf_metrics = ml_models.train_random_forest_classifier(X_train, y_train_clf)
    print(f"   Accuracy: {rf_clf_metrics['training_accuracy']:.4f}")
    
    print("\n=== Regression Models ===")
    print("\n1. SVM Regressor:")
    svm_reg_metrics = ml_models.train_svm_regressor(X_train, y_train_reg)
    print(f"   R² Score: {svm_reg_metrics['training_r2_score']:.4f}")
    
    print("\n2. Random Forest Regressor:")
    rf_reg_metrics = ml_models.train_random_forest_regressor(X_train, y_train_reg)
    print(f"   R² Score: {rf_reg_metrics['training_r2_score']:.4f}")
    
    print("\n=== XGBoost Models ===")
    print("\n1. XGBoost Classifier:")
    xgb_clf_metrics = ml_models.train_xgboost_classifier(X_train, y_train_clf)
    if 'error' not in xgb_clf_metrics:
        print(f"   Accuracy: {xgb_clf_metrics['training_accuracy']:.4f}")
    
    print("\n2. XGBoost Regressor:")
    xgb_reg_metrics = ml_models.train_xgboost_regressor(X_train, y_train_reg)
    if 'error' not in xgb_reg_metrics:
        print(f"   R² Score: {xgb_reg_metrics['training_r2_score']:.4f}")
    
    print("\n✅ Traditional ML models trained successfully!")
