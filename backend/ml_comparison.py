"""
Model Comparison Framework: Neural Networks vs Traditional ML
Comprehensive evaluation of all model types on same dataset
"""

import numpy as np
from typing import Dict, List, Tuple
import json
from datetime import datetime

from ml_data import CodeFeatureExtractor, EmbeddingGenerator, CodeDataset, DataLoader
from ml_models import QualityPredictorModel, CodeClassifierModel
from ml_traditional import TraditionalMLModels
from ml_training import RegressionMetrics, ClassificationMetrics, ModelEvaluator
import torch
import torch.nn as nn


class ComprehensiveModelComparison:
    """
    Compare all model types:
    - Neural Networks (PyTorch)
    - Logistic Regression
    - SVM (Linear, RBF, Poly)
    - Random Forest
    - XGBoost
    """
    
    def __init__(self):
        self.results = {
            'regression': {},
            'classification': {},
            'comparison': {}
        }
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    def prepare_data(self, code_samples: List[str], quality_labels: List[float],
                    clf_labels: List[int], split: float = 0.8):
        """
        Prepare data for all models
        
        Args:
            code_samples: List of code strings
            quality_labels: Quality scores (0-100)
            clf_labels: Classification labels (0-3)
            split: Train/test split ratio
        """
        print("📊 Preparing data for model comparison...")
        
        # Extract features and embeddings
        extractor = CodeFeatureExtractor()
        features_list = []
        embeddings_list = []
        
        print("   Extracting features...")
        for code in code_samples:
            features = extractor.extract(code)
            features_list.append(features)
        
        print("   Generating embeddings...")
        try:
            generator = EmbeddingGenerator()
            embeddings_array = generator.generate(code_samples)
        except Exception as e:
            print(f"   Note: Using random embeddings ({e})")
            embeddings_array = np.random.randn(len(code_samples), 768).astype(np.float32)
        
        # Convert features to array
        feature_keys = ['token_count', 'line_count', 'avg_line_length', 'nesting_depth',
                       'cyclomatic_complexity', 'num_functions', 'num_classes',
                       'num_branches', 'num_loops', 'num_comments']
        
        features_array = np.zeros((len(code_samples), 10))
        for i, feat_dict in enumerate(features_list):
            features_array[i] = [feat_dict.get(k, 0) for k in feature_keys]
        
        # Split data
        n_samples = len(code_samples)
        n_train = int(n_samples * split)
        indices = np.random.permutation(n_samples)
        train_idx = indices[:n_train]
        test_idx = indices[n_train:]
        
        # Prepare datasets
        X_train_features = features_array[train_idx]
        X_test_features = features_array[test_idx]
        X_train_embeddings = embeddings_array[train_idx]
        X_test_embeddings = embeddings_array[test_idx]
        
        y_train_quality = np.array(quality_labels)[train_idx]
        y_test_quality = np.array(quality_labels)[test_idx]
        y_train_clf = np.array(clf_labels)[train_idx]
        y_test_clf = np.array(clf_labels)[test_idx]
        
        print(f"   ✓ Train samples: {n_train}, Test samples: {len(test_idx)}")
        
        return {
            'X_train_features': X_train_features,
            'X_test_features': X_test_features,
            'X_train_embeddings': X_train_embeddings,
            'X_test_embeddings': X_test_embeddings,
            'y_train_quality': y_train_quality,
            'y_test_quality': y_test_quality,
            'y_train_clf': y_train_clf,
            'y_test_clf': y_test_clf,
        }
    
    def compare_regression_models(self, data: Dict) -> Dict:
        """
        Compare all regression models for quality prediction
        """
        print("\n" + "="*60)
        print("📊 REGRESSION COMPARISON: Quality Prediction (0-100)")
        print("="*60)
        
        results = {}
        
        # ===== TRADITIONAL ML =====
        print("\n🔹 Traditional ML Models:")
        ml_models = TraditionalMLModels()
        
        # SVM Regressor
        print("   Training SVM Regressor...")
        svm_result = ml_models.train_svm_regressor(data['X_train_features'], 
                                                   data['y_train_quality'])
        svm_pred = []
        for x in data['X_test_features']:
            svm_pred.append(ml_models.predict_svm_reg(x))
        svm_mae = RegressionMetrics.mae(np.array(svm_pred), data['y_test_quality'])
        svm_r2 = RegressionMetrics.r2_score(np.array(svm_pred), data['y_test_quality'])
        
        results['SVM Regressor'] = {
            'type': 'Traditional ML',
            'mae': float(svm_mae),
            'r2': float(svm_r2),
            'training_r2': svm_result['training_r2_score']
        }
        print(f"      Test MAE: {svm_mae:.4f}, R²: {svm_r2:.4f}")
        
        # Random Forest Regressor
        print("   Training Random Forest Regressor...")
        rf_result = ml_models.train_random_forest_regressor(data['X_train_features'],
                                                            data['y_train_quality'])
        rf_pred = []
        for x in data['X_test_features']:
            rf_pred.append(ml_models.predict_rf_reg(x))
        rf_mae = RegressionMetrics.mae(np.array(rf_pred), data['y_test_quality'])
        rf_r2 = RegressionMetrics.r2_score(np.array(rf_pred), data['y_test_quality'])
        
        results['Random Forest Regressor'] = {
            'type': 'Traditional ML',
            'mae': float(rf_mae),
            'r2': float(rf_r2),
            'training_r2': rf_result['training_r2_score']
        }
        print(f"      Test MAE: {rf_mae:.4f}, R²: {rf_r2:.4f}")
        
        # XGBoost Regressor
        print("   Training XGBoost Regressor...")
        xgb_result = ml_models.train_xgboost_regressor(data['X_train_features'],
                                                       data['y_train_quality'])
        if 'error' not in xgb_result:
            xgb_pred = []
            for x in data['X_test_features']:
                xgb_pred.append(ml_models.predict_xgb_reg(x))
            xgb_mae = RegressionMetrics.mae(np.array(xgb_pred), data['y_test_quality'])
            xgb_r2 = RegressionMetrics.r2_score(np.array(xgb_pred), data['y_test_quality'])
            
            results['XGBoost Regressor'] = {
                'type': 'Traditional ML',
                'mae': float(xgb_mae),
                'r2': float(xgb_r2),
                'training_r2': xgb_result['training_r2_score']
            }
            print(f"      Test MAE: {xgb_mae:.4f}, R²: {xgb_r2:.4f}")
        
        # ===== NEURAL NETWORK =====
        print("\n🔹 Deep Learning Model:")
        print("   Training PyTorch Neural Network...")
        
        # Prepare data for neural network
        X_train_nn = np.concatenate([data['X_train_embeddings'], 
                                     data['X_train_features']], axis=1)
        X_test_nn = np.concatenate([data['X_test_embeddings'],
                                    data['X_test_features']], axis=1)
        
        # Normalize features
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_train_nn = scaler.fit_transform(X_train_nn)
        X_test_nn = scaler.transform(X_test_nn)
        
        # Create model
        model = QualityPredictorModel()
        model.to(self.device)
        
        # Train
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        
        model.train()
        for epoch in range(20):
            optimizer.zero_grad()
            
            X_train_emb = torch.tensor(data['X_train_embeddings'], dtype=torch.float32).to(self.device)
            X_train_feat = torch.tensor(data['X_train_features'], dtype=torch.float32).to(self.device)
            y_train = torch.tensor(data['y_train_quality'], dtype=torch.float32).to(self.device)
            
            outputs = model(X_train_emb, X_train_feat)
            loss = criterion(outputs.squeeze(), y_train)
            loss.backward()
            optimizer.step()
        
        # Evaluate
        model.eval()
        with torch.no_grad():
            X_test_emb = torch.tensor(data['X_test_embeddings'], dtype=torch.float32).to(self.device)
            X_test_feat = torch.tensor(data['X_test_features'], dtype=torch.float32).to(self.device)
            y_test = torch.tensor(data['y_test_quality'], dtype=torch.float32).to(self.device)
            
            nn_pred = model(X_test_emb, X_test_feat).squeeze().cpu().numpy()
        
        nn_mae = RegressionMetrics.mae(nn_pred, data['y_test_quality'])
        nn_r2 = RegressionMetrics.r2_score(nn_pred, data['y_test_quality'])
        
        results['PyTorch Neural Network'] = {
            'type': 'Deep Learning',
            'mae': float(nn_mae),
            'r2': float(nn_r2),
            'training_r2': float(nn_r2)  # Approximation
        }
        print(f"      Test MAE: {nn_mae:.4f}, R²: {nn_r2:.4f}")
        
        self.results['regression'] = results
        return results
    
    def compare_classification_models(self, data: Dict) -> Dict:
        """
        Compare all classification models
        """
        print("\n" + "="*60)
        print("🏷️ CLASSIFICATION COMPARISON: Code Quality Issues")
        print("="*60)
        
        results = {}
        
        # ===== TRADITIONAL ML =====
        print("\n🔹 Traditional ML Models:")
        ml_models = TraditionalMLModels()
        
        # Logistic Regression
        print("   Training Logistic Regression...")
        lr_result = ml_models.train_logistic_regression(data['X_train_features'],
                                                        data['y_train_clf'])
        lr_pred = []
        for x in data['X_test_features']:
            pred, _ = ml_models.predict_lr(x)
            lr_pred.append(pred)
        lr_acc = ClassificationMetrics.accuracy(np.array(lr_pred), data['y_test_clf'])
        
        results['Logistic Regression'] = {
            'type': 'Traditional ML',
            'accuracy': float(lr_acc),
            'training_accuracy': lr_result['training_accuracy']
        }
        print(f"      Test Accuracy: {lr_acc:.4f}")
        
        # SVM Classifier
        print("   Training SVM Classifier...")
        svm_result = ml_models.train_svm_classifier(data['X_train_features'],
                                                    data['y_train_clf'])
        svm_pred = []
        for x in data['X_test_features']:
            pred, _ = ml_models.predict_svm_clf(x)
            svm_pred.append(pred)
        svm_acc = ClassificationMetrics.accuracy(np.array(svm_pred), data['y_test_clf'])
        
        results['SVM Classifier'] = {
            'type': 'Traditional ML',
            'accuracy': float(svm_acc),
            'training_accuracy': svm_result['training_accuracy']
        }
        print(f"      Test Accuracy: {svm_acc:.4f}")
        
        # Random Forest Classifier
        print("   Training Random Forest Classifier...")
        rf_result = ml_models.train_random_forest_classifier(data['X_train_features'],
                                                             data['y_train_clf'])
        rf_pred = []
        for x in data['X_test_features']:
            pred, _ = ml_models.predict_rf_clf(x)
            rf_pred.append(pred)
        rf_acc = ClassificationMetrics.accuracy(np.array(rf_pred), data['y_test_clf'])
        
        results['Random Forest Classifier'] = {
            'type': 'Traditional ML',
            'accuracy': float(rf_acc),
            'training_accuracy': rf_result['training_accuracy']
        }
        print(f"      Test Accuracy: {rf_acc:.4f}")
        
        # XGBoost Classifier
        print("   Training XGBoost Classifier...")
        xgb_result = ml_models.train_xgboost_classifier(data['X_train_features'],
                                                        data['y_train_clf'])
        if 'error' not in xgb_result:
            xgb_pred = []
            for x in data['X_test_features']:
                pred, _ = ml_models.predict_xgb_clf(x)
                xgb_pred.append(pred)
            xgb_acc = ClassificationMetrics.accuracy(np.array(xgb_pred), data['y_test_clf'])
            
            results['XGBoost Classifier'] = {
                'type': 'Traditional ML',
                'accuracy': float(xgb_acc),
                'training_accuracy': xgb_result['training_accuracy']
            }
            print(f"      Test Accuracy: {xgb_acc:.4f}")
        
        # ===== NEURAL NETWORK =====
        print("\n🔹 Deep Learning Model:")
        print("   Training PyTorch Neural Network...")
        
        # Prepare data
        X_train_nn = np.concatenate([data['X_train_embeddings'],
                                     data['X_train_features']], axis=1)
        X_test_nn = np.concatenate([data['X_test_embeddings'],
                                    data['X_test_features']], axis=1)
        
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_train_nn = scaler.fit_transform(X_train_nn)
        X_test_nn = scaler.transform(X_test_nn)
        
        # Create model
        model = CodeClassifierModel(num_classes=4)
        model.to(self.device)
        
        # Train
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        
        model.train()
        for epoch in range(20):
            optimizer.zero_grad()
            
            X_train_emb = torch.tensor(data['X_train_embeddings'], dtype=torch.float32).to(self.device)
            X_train_feat = torch.tensor(data['X_train_features'], dtype=torch.float32).to(self.device)
            y_train = torch.tensor(data['y_train_clf'], dtype=torch.long).to(self.device)
            
            outputs = model(X_train_emb, X_train_feat)
            loss = criterion(outputs, y_train)
            loss.backward()
            optimizer.step()
        
        # Evaluate
        model.eval()
        with torch.no_grad():
            X_test_emb = torch.tensor(data['X_test_embeddings'], dtype=torch.float32).to(self.device)
            X_test_feat = torch.tensor(data['X_test_features'], dtype=torch.float32).to(self.device)
            
            outputs = model(X_test_emb, X_test_feat)
            nn_pred = torch.argmax(outputs, dim=1).cpu().numpy()
        
        nn_acc = ClassificationMetrics.accuracy(nn_pred, data['y_test_clf'])
        
        results['PyTorch Neural Network'] = {
            'type': 'Deep Learning',
            'accuracy': float(nn_acc),
            'training_accuracy': float(nn_acc)
        }
        print(f"      Test Accuracy: {nn_acc:.4f}")
        
        self.results['classification'] = results
        return results
    
    def generate_comparison_report(self) -> Dict:
        """Generate comprehensive comparison report"""
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE COMPARISON REPORT")
        print("="*60)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'regression': self.results['regression'],
            'classification': self.results['classification'],
            'analysis': self._analyze_results()
        }
        
        # Save report
        with open('model_comparison_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\n✅ Report saved to: model_comparison_report.json")
        return report
    
    def _analyze_results(self) -> Dict:
        """Analyze and compare results"""
        analysis = {
            'regression_winner': None,
            'classification_winner': None,
            'recommendations': []
        }
        
        if self.results['regression']:
            best_reg = max(self.results['regression'].items(),
                          key=lambda x: x[1]['r2'])
            analysis['regression_winner'] = {
                'model': best_reg[0],
                'r2': best_reg[1]['r2']
            }
        
        if self.results['classification']:
            best_clf = max(self.results['classification'].items(),
                          key=lambda x: x[1]['accuracy'])
            analysis['classification_winner'] = {
                'model': best_clf[0],
                'accuracy': best_clf[1]['accuracy']
            }
        
        # Recommendations
        analysis['recommendations'] = [
            "✓ Use traditional ML (SVM, Random Forest) for quick training & inference",
            "✓ Use Neural Networks for large datasets (>10k samples)",
            "✓ Use XGBoost when you need feature importance & interpretability",
            "✓ Use Random Forest for production due to robustness & speed",
            "✓ Use Neural Networks when data has complex patterns"
        ]
        
        return analysis


if __name__ == '__main__':
    print("Model Comparison Framework\n")
    
    # Generate sample data
    print("Generating sample dataset...")
    np.random.seed(42)
    
    code_samples = [
        "def add(a, b): return a + b",
        "def complex_fn(x): return x**2 + 2*x + 1 if x > 0 else 0",
    ] * 50  # 100 samples
    
    quality_labels = np.random.rand(100) * 100  # 0-100
    clf_labels = np.random.randint(0, 4, 100)   # 4 classes
    
    # Run comparison
    comparison = ComprehensiveModelComparison()
    data = comparison.prepare_data(code_samples, quality_labels, clf_labels)
    
    print("\n🚀 Running model comparisons...")
    comparison.compare_regression_models(data)
    comparison.compare_classification_models(data)
    
    # Generate report
    report = comparison.generate_comparison_report()
    
    print("\n📊 Results Summary:")
    print(json.dumps(report['analysis'], indent=2))
