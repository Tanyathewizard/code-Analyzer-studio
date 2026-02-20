"""
ML Models: PyTorch Neural Networks for Code Analysis
Different architectures for different tasks
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple


class QualityPredictorModel(nn.Module):
    """
    Neural network for predicting code quality (0-100)
    
    Architecture:
    - Input: Code embeddings (768) + structural features (50)
    - Hidden layers: 256 → 128 neurons
    - Output: Quality score (1 value, 0-100)
    
    Use: Regression task - predicting continuous quality score
    """
    
    def __init__(self, embedding_dim: int = 768, feature_dim: int = 50, hidden_dim: int = 256):
        super().__init__()
        
        self.embedding_dim = embedding_dim
        self.feature_dim = feature_dim
        self.hidden_dim = hidden_dim
        
        # Input: embeddings + features combined
        input_dim = embedding_dim + feature_dim
        
        # Hidden layers
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.dropout1 = nn.Dropout(0.3)
        
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.bn2 = nn.BatchNorm1d(hidden_dim // 2)
        self.dropout2 = nn.Dropout(0.2)
        
        # Output layer: single value for quality score
        self.fc3 = nn.Linear(hidden_dim // 2, 1)
        
        # Activation functions
        self.relu = nn.ReLU()
    
    def forward(self, embeddings: torch.Tensor, features: torch.Tensor) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            embeddings: (batch_size, 768) - code embeddings
            features: (batch_size, 50) - structural features
            
        Returns:
            quality_scores: (batch_size, 1) - predicted quality 0-100
        """
        # Concatenate embeddings and features
        x = torch.cat([embeddings, features], dim=1)  # (batch_size, 818)
        
        # First hidden layer
        x = self.fc1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.dropout1(x)
        
        # Second hidden layer
        x = self.fc2(x)
        x = self.bn2(x)
        x = self.relu(x)
        x = self.dropout2(x)
        
        # Output layer (quality 0-100)
        x = self.fc3(x)
        quality = torch.sigmoid(x) * 100  # Scale to 0-100
        
        return quality


class CodeClassifierModel(nn.Module):
    """
    Neural network for classifying code snippets
    Classes: Clean, Bug, Performance Issue, Security Issue
    
    Architecture:
    - Input: Code embeddings (768) + features (50)
    - Hidden layers: 256 → 128 neurons
    - Output: 4 classes (softmax probabilities)
    
    Use: Classification task - categorize code quality issues
    """
    
    def __init__(self, embedding_dim: int = 768, feature_dim: int = 50, 
                 num_classes: int = 4, hidden_dim: int = 256):
        super().__init__()
        
        self.embedding_dim = embedding_dim
        self.feature_dim = feature_dim
        self.num_classes = num_classes
        
        input_dim = embedding_dim + feature_dim
        
        # Hidden layers
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.dropout1 = nn.Dropout(0.3)
        
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.bn2 = nn.BatchNorm1d(hidden_dim // 2)
        self.dropout2 = nn.Dropout(0.2)
        
        # Classification output
        self.fc3 = nn.Linear(hidden_dim // 2, num_classes)
        
        self.relu = nn.ReLU()
    
    def forward(self, embeddings: torch.Tensor, features: torch.Tensor) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            embeddings: (batch_size, 768)
            features: (batch_size, 50)
            
        Returns:
            logits: (batch_size, num_classes) - class logits
        """
        x = torch.cat([embeddings, features], dim=1)
        
        x = self.fc1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.dropout1(x)
        
        x = self.fc2(x)
        x = self.bn2(x)
        x = self.relu(x)
        x = self.dropout2(x)
        
        logits = self.fc3(x)
        return logits


class AnomalyDetectorModel(nn.Module):
    """
    Autoencoder for detecting anomalous code patterns
    
    Architecture:
    - Encoder: Features (800) → 128 → latent (32)
    - Decoder: latent (32) → 128 → reconstructed (800)
    - Training: Minimize reconstruction error on normal code
    - Detection: High reconstruction error → anomaly
    
    Use: Unsupervised anomaly detection, outlier discovery
    """
    
    def __init__(self, input_dim: int = 818, latent_dim: int = 32, hidden_dim: int = 128):
        super().__init__()
        
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, latent_dim),
        )
        
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, input_dim),
        )
    
    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Encode to latent space"""
        return self.encoder(x)
    
    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Decode from latent space"""
        return self.decoder(z)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass
        
        Args:
            x: (batch_size, input_dim) - combined embeddings + features
            
        Returns:
            reconstructed: (batch_size, input_dim) - reconstructed input
            latent: (batch_size, latent_dim) - latent representation
        """
        latent = self.encode(x)
        reconstructed = self.decode(latent)
        return reconstructed, latent
    
    def anomaly_score(self, x: torch.Tensor) -> torch.Tensor:
        """
        Calculate anomaly score based on reconstruction error
        
        Returns:
            scores: (batch_size,) - reconstruction error for each sample
        """
        reconstructed, _ = self.forward(x)
        # Mean squared error as anomaly score
        scores = torch.mean((x - reconstructed) ** 2, dim=1)
        return scores


class ComplexityPredictorModel(nn.Module):
    """
    Neural network for predicting code complexity (1-10)
    
    Uses structural features (no embeddings)
    Architecture:
    - Input: Structural features (50)
    - Hidden layers: 64 → 32 neurons
    - Output: Complexity score (1-10)
    
    Use: Fast complexity prediction from features only
    """
    
    def __init__(self, feature_dim: int = 50, hidden_dim: int = 64):
        super().__init__()
        
        self.feature_dim = feature_dim
        
        self.fc1 = nn.Linear(feature_dim, hidden_dim)
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.dropout1 = nn.Dropout(0.2)
        
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.bn2 = nn.BatchNorm1d(hidden_dim // 2)
        self.dropout2 = nn.Dropout(0.15)
        
        self.fc3 = nn.Linear(hidden_dim // 2, 1)
        
        self.relu = nn.ReLU()
    
    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            features: (batch_size, 50) - structural features
            
        Returns:
            complexity: (batch_size, 1) - predicted complexity 1-10
        """
        x = self.fc1(features)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.dropout1(x)
        
        x = self.fc2(x)
        x = self.bn2(x)
        x = self.relu(x)
        x = self.dropout2(x)
        
        complexity = self.fc3(x)
        # Scale to 1-10 range
        complexity = torch.clamp(complexity, 0, 1) * 9 + 1
        
        return complexity


class SemanticSimilarityModel(nn.Module):
    """
    Siamese network for learning code semantic similarity
    
    Architecture:
    - Shared embedding network (embeddings → 256 → 128)
    - Distance metric: Cosine similarity
    - Training: Contrastive loss (similar/dissimilar pairs)
    
    Use: Find similar functions, code search, recommendations
    """
    
    def __init__(self, embedding_dim: int = 768, output_dim: int = 128):
        super().__init__()
        
        # Shared network to project embeddings
        self.projection = nn.Sequential(
            nn.Linear(embedding_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, output_dim),
            nn.BatchNorm1d(output_dim),
        )
    
    def forward(self, embeddings1: torch.Tensor, embeddings2: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for similarity
        
        Args:
            embeddings1: (batch_size, embedding_dim) - first set of embeddings
            embeddings2: (batch_size, embedding_dim) - second set of embeddings
            
        Returns:
            similarity: (batch_size,) - cosine similarity scores [-1, 1]
        """
        # Project both embeddings
        proj1 = self.projection(embeddings1)
        proj2 = self.projection(embeddings2)
        
        # Normalize
        proj1 = F.normalize(proj1, p=2, dim=1)
        proj2 = F.normalize(proj2, p=2, dim=1)
        
        # Cosine similarity
        similarity = torch.sum(proj1 * proj2, dim=1)
        return similarity
    
    def get_embedding(self, embeddings: torch.Tensor) -> torch.Tensor:
        """Get projected embedding for a set of codes"""
        proj = self.projection(embeddings)
        return F.normalize(proj, p=2, dim=1)


if __name__ == '__main__':
    print("ML Models Test\n")
    
    # Test Quality Predictor
    print("1. Quality Predictor Model:")
    model = QualityPredictorModel()
    embeddings = torch.randn(4, 768)
    features = torch.randn(4, 50)
    output = model(embeddings, features)
    print(f"   Input: embeddings {embeddings.shape}, features {features.shape}")
    print(f"   Output shape: {output.shape}")
    print(f"   Output values (quality 0-100): {output.squeeze().tolist()}\n")
    
    # Test Code Classifier
    print("2. Code Classifier Model:")
    clf_model = CodeClassifierModel(num_classes=4)
    logits = clf_model(embeddings, features)
    probs = torch.softmax(logits, dim=1)
    print(f"   Output shape: {logits.shape}")
    print(f"   Predictions: {probs[0].tolist()}\n")
    
    # Test Anomaly Detector
    print("3. Anomaly Detector (Autoencoder):")
    autoencoder = AnomalyDetectorModel()
    combined = torch.cat([embeddings, features], dim=1)
    reconstructed, latent = autoencoder(combined)
    anomaly_scores = autoencoder.anomaly_score(combined)
    print(f"   Input shape: {combined.shape}")
    print(f"   Reconstructed shape: {reconstructed.shape}")
    print(f"   Latent shape: {latent.shape}")
    print(f"   Anomaly scores: {anomaly_scores.tolist()}\n")
    
    # Test Complexity Predictor
    print("4. Complexity Predictor Model:")
    complexity_model = ComplexityPredictorModel()
    complexity = complexity_model(features)
    print(f"   Output shape: {complexity.shape}")
    print(f"   Predicted complexity (1-10): {complexity.squeeze().tolist()}\n")
    
    # Test Semantic Similarity
    print("5. Semantic Similarity Model:")
    similarity_model = SemanticSimilarityModel()
    embeddings2 = torch.randn(4, 768)
    similarity = similarity_model(embeddings, embeddings2)
    print(f"   Similarity shape: {similarity.shape}")
    print(f"   Similarity scores [-1, 1]: {similarity.tolist()}\n")
    
    print("✅ All models tested successfully!")
