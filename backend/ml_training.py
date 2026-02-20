"""
ML Training Framework: Common training loop, evaluation metrics, and utilities
"""

import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader as TorchDataLoader
from typing import Tuple, Dict, List, Optional
from pathlib import Path
import numpy as np
from datetime import datetime


class Trainer:
    """
    General-purpose trainer for PyTorch models
    
    Handles:
    - Training loop with validation
    - Learning rate scheduling
    - Checkpointing
    - Early stopping
    - Metrics logging
    """
    
    def __init__(self, model: nn.Module, criterion: nn.Module, 
                 optimizer: optim.Optimizer, device: str = 'cpu',
                 learning_rate: float = 0.001):
        """
        Initialize trainer
        
        Args:
            model: PyTorch model
            criterion: Loss function
            optimizer: Optimizer (Adam, SGD, etc)
            device: 'cpu' or 'cuda'
            learning_rate: Initial learning rate
        """
        self.model = model.to(device)
        self.criterion = criterion
        self.optimizer = optimizer
        self.device = device
        self.learning_rate = learning_rate
        
        self.train_losses = []
        self.val_losses = []
        self.train_metrics = []
        self.val_metrics = []
        
        self.best_val_loss = float('inf')
        self.patience_counter = 0
    
    def train_epoch(self, train_loader: TorchDataLoader) -> float:
        """
        Train for one epoch
        
        Returns:
            average_loss: Average training loss
        """
        self.model.train()
        total_loss = 0
        batch_count = 0
        
        for batch_idx, batch in enumerate(train_loader):
            # Move batch to device
            if isinstance(batch, (list, tuple)):
                batch = [b.to(self.device) if isinstance(b, torch.Tensor) else b 
                        for b in batch]
            else:
                batch = batch.to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(*batch[:-1])  # All but last (label)
            labels = batch[-1]
            
            # Calculate loss
            loss = self.criterion(outputs.squeeze(), labels)
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            batch_count += 1
            
            if (batch_idx + 1) % 10 == 0:
                print(f"  Batch {batch_idx + 1}: loss = {loss.item():.4f}")
        
        avg_loss = total_loss / batch_count
        self.train_losses.append(avg_loss)
        return avg_loss
    
    def validate(self, val_loader: TorchDataLoader) -> float:
        """
        Validate on validation set
        
        Returns:
            average_loss: Average validation loss
        """
        self.model.eval()
        total_loss = 0
        batch_count = 0
        
        with torch.no_grad():
            for batch in val_loader:
                if isinstance(batch, (list, tuple)):
                    batch = [b.to(self.device) if isinstance(b, torch.Tensor) else b 
                            for b in batch]
                else:
                    batch = batch.to(self.device)
                
                outputs = self.model(*batch[:-1])
                labels = batch[-1]
                loss = self.criterion(outputs.squeeze(), labels)
                
                total_loss += loss.item()
                batch_count += 1
        
        avg_loss = total_loss / batch_count
        self.val_losses.append(avg_loss)
        return avg_loss
    
    def train(self, train_loader: TorchDataLoader, val_loader: TorchDataLoader,
              epochs: int = 50, save_path: str = 'model.pth',
              early_stopping_patience: int = 10, lr_scheduler=None):
        """
        Full training loop with validation
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            epochs: Number of epochs
            save_path: Path to save best model
            early_stopping_patience: Early stopping patience
            lr_scheduler: Optional learning rate scheduler
        """
        print(f"🚀 Starting training for {epochs} epochs...")
        print(f"   Device: {self.device}")
        print(f"   Model parameters: {sum(p.numel() for p in self.model.parameters()):,}")
        
        for epoch in range(1, epochs + 1):
            print(f"\n📊 Epoch {epoch}/{epochs}")
            
            # Train
            train_loss = self.train_epoch(train_loader)
            print(f"  Train loss: {train_loss:.4f}")
            
            # Validate
            val_loss = self.validate(val_loader)
            print(f"  Val loss:   {val_loss:.4f}")
            
            # Learning rate scheduling
            if lr_scheduler:
                lr_scheduler.step()
                current_lr = self.optimizer.param_groups[0]['lr']
                print(f"  Learning rate: {current_lr:.6f}")
            
            # Early stopping
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.patience_counter = 0
                self._save_checkpoint(save_path)
                print(f"  ✅ Best model saved to {save_path}")
            else:
                self.patience_counter += 1
                if self.patience_counter >= early_stopping_patience:
                    print(f"  ⚠️  Early stopping after {epoch} epochs")
                    break
        
        print(f"\n✅ Training complete!")
        print(f"   Best validation loss: {self.best_val_loss:.4f}")
        self._save_logs(save_path.replace('.pth', '_logs.json'))
    
    def _save_checkpoint(self, path: str):
        """Save model checkpoint"""
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        torch.save(self.model.state_dict(), path)
    
    def _save_logs(self, path: str):
        """Save training logs"""
        logs = {
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'best_val_loss': self.best_val_loss,
            'timestamp': datetime.now().isoformat()
        }
        with open(path, 'w') as f:
            json.dump(logs, f, indent=2)


class RegressionMetrics:
    """Calculate metrics for regression tasks (quality, complexity prediction)"""
    
    @staticmethod
    def mae(predictions: np.ndarray, targets: np.ndarray) -> float:
        """Mean Absolute Error"""
        return np.mean(np.abs(predictions - targets))
    
    @staticmethod
    def mse(predictions: np.ndarray, targets: np.ndarray) -> float:
        """Mean Squared Error"""
        return np.mean((predictions - targets) ** 2)
    
    @staticmethod
    def rmse(predictions: np.ndarray, targets: np.ndarray) -> float:
        """Root Mean Squared Error"""
        return np.sqrt(RegressionMetrics.mse(predictions, targets))
    
    @staticmethod
    def r2_score(predictions: np.ndarray, targets: np.ndarray) -> float:
        """R² Score (coefficient of determination)"""
        ss_res = np.sum((targets - predictions) ** 2)
        ss_tot = np.sum((targets - np.mean(targets)) ** 2)
        return 1 - (ss_res / ss_tot)
    
    @staticmethod
    def mape(predictions: np.ndarray, targets: np.ndarray) -> float:
        """Mean Absolute Percentage Error"""
        return np.mean(np.abs((targets - predictions) / targets)) * 100


class ClassificationMetrics:
    """Calculate metrics for classification tasks"""
    
    @staticmethod
    def accuracy(predictions: np.ndarray, targets: np.ndarray) -> float:
        """Accuracy: correct predictions / total predictions"""
        return np.mean(predictions == targets)
    
    @staticmethod
    def precision(predictions: np.ndarray, targets: np.ndarray, class_idx: int = 1) -> float:
        """Precision for binary/multiclass"""
        tp = np.sum((predictions == class_idx) & (targets == class_idx))
        fp = np.sum((predictions == class_idx) & (targets != class_idx))
        return tp / (tp + fp) if (tp + fp) > 0 else 0
    
    @staticmethod
    def recall(predictions: np.ndarray, targets: np.ndarray, class_idx: int = 1) -> float:
        """Recall (sensitivity) for binary/multiclass"""
        tp = np.sum((predictions == class_idx) & (targets == class_idx))
        fn = np.sum((predictions != class_idx) & (targets == class_idx))
        return tp / (tp + fn) if (tp + fn) > 0 else 0
    
    @staticmethod
    def f1_score(predictions: np.ndarray, targets: np.ndarray, class_idx: int = 1) -> float:
        """F1 Score: harmonic mean of precision and recall"""
        precision = ClassificationMetrics.precision(predictions, targets, class_idx)
        recall = ClassificationMetrics.recall(predictions, targets, class_idx)
        if precision + recall == 0:
            return 0
        return 2 * (precision * recall) / (precision + recall)
    
    @staticmethod
    def confusion_matrix(predictions: np.ndarray, targets: np.ndarray, num_classes: int):
        """Generate confusion matrix"""
        cm = np.zeros((num_classes, num_classes))
        for true, pred in zip(targets, predictions):
            cm[true, pred] += 1
        return cm


class ModelEvaluator:
    """Comprehensive model evaluation"""
    
    @staticmethod
    def evaluate_regression(model: nn.Module, test_loader: TorchDataLoader,
                          device: str = 'cpu') -> Dict:
        """Evaluate regression model"""
        model.eval()
        predictions = []
        targets = []
        
        with torch.no_grad():
            for batch in test_loader:
                batch = [b.to(device) if isinstance(b, torch.Tensor) else b for b in batch]
                outputs = model(*batch[:-1])
                labels = batch[-1]
                
                predictions.extend(outputs.squeeze().cpu().numpy())
                targets.extend(labels.cpu().numpy())
        
        predictions = np.array(predictions)
        targets = np.array(targets)
        
        return {
            'mae': RegressionMetrics.mae(predictions, targets),
            'mse': RegressionMetrics.mse(predictions, targets),
            'rmse': RegressionMetrics.rmse(predictions, targets),
            'r2': RegressionMetrics.r2_score(predictions, targets),
            'mape': RegressionMetrics.mape(predictions, targets),
        }
    
    @staticmethod
    def evaluate_classification(model: nn.Module, test_loader: TorchDataLoader,
                               num_classes: int, device: str = 'cpu') -> Dict:
        """Evaluate classification model"""
        model.eval()
        predictions = []
        targets = []
        
        with torch.no_grad():
            for batch in test_loader:
                batch = [b.to(device) if isinstance(b, torch.Tensor) else b for b in batch]
                outputs = model(*batch[:-1])
                labels = batch[-1]
                
                preds = torch.argmax(outputs, dim=1).cpu().numpy()
                predictions.extend(preds)
                targets.extend(labels.cpu().numpy())
        
        predictions = np.array(predictions)
        targets = np.array(targets)
        
        metrics = {
            'accuracy': ClassificationMetrics.accuracy(predictions, targets),
            'confusion_matrix': ClassificationMetrics.confusion_matrix(
                predictions, targets, num_classes
            ).tolist()
        }
        
        # Per-class metrics
        for class_idx in range(num_classes):
            metrics[f'class_{class_idx}_precision'] = ClassificationMetrics.precision(
                predictions, targets, class_idx
            )
            metrics[f'class_{class_idx}_recall'] = ClassificationMetrics.recall(
                predictions, targets, class_idx
            )
            metrics[f'class_{class_idx}_f1'] = ClassificationMetrics.f1_score(
                predictions, targets, class_idx
            )
        
        return metrics


if __name__ == '__main__':
    print("ML Training Framework\n")
    
    # Example: Create dummy data
    print("1. Testing Regression Metrics:")
    pred_reg = np.array([85.2, 72.1, 91.5, 68.9])
    target_reg = np.array([80.0, 75.0, 90.0, 70.0])
    
    print(f"   MAE:  {RegressionMetrics.mae(pred_reg, target_reg):.4f}")
    print(f"   MSE:  {RegressionMetrics.mse(pred_reg, target_reg):.4f}")
    print(f"   RMSE: {RegressionMetrics.rmse(pred_reg, target_reg):.4f}")
    print(f"   R²:   {RegressionMetrics.r2_score(pred_reg, target_reg):.4f}\n")
    
    print("2. Testing Classification Metrics:")
    pred_clf = np.array([0, 1, 1, 2, 3])
    target_clf = np.array([0, 1, 0, 2, 3])
    
    print(f"   Accuracy: {ClassificationMetrics.accuracy(pred_clf, target_clf):.4f}")
    print(f"   Precision (class 1): {ClassificationMetrics.precision(pred_clf, target_clf, 1):.4f}")
    print(f"   Recall (class 1): {ClassificationMetrics.recall(pred_clf, target_clf, 1):.4f}")
    print(f"   F1 (class 1): {ClassificationMetrics.f1_score(pred_clf, target_clf, 1):.4f}\n")
    
    print("✅ Training framework ready!")
