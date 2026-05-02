"""
Example ML Training Pipeline: Quality Predictor
Complete end-to-end training workflow with sample data
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader as TorchDataLoader
import numpy as np
from pathlib import Path

# Import our ML modules
from backend.ml_data import CodePreprocessor, CodeFeatureExtractor, CodeDataset, EmbeddingGenerator, DataLoader
from backend.ml_models import QualityPredictorModel
from backend.ml_training import Trainer, RegressionMetrics, ModelEvaluator


# Sample training data
SAMPLE_GOOD_CODE = [
    """
    def bubble_sort(arr):
        '''Sorts array using bubble sort algorithm'''
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
        return arr
    """,
    """
    class Calculator:
        '''Simple calculator with basic operations'''
        
        def add(self, a, b):
            return a + b
        
        def subtract(self, a, b):
            return a - b
        
        def multiply(self, a, b):
            return a * b
    """,
    """
    def find_max(numbers):
        '''Find maximum value in list'''
        if not numbers:
            return None
        max_val = numbers[0]
        for num in numbers[1:]:
            if num > max_val:
                max_val = num
        return max_val
    """,
]

SAMPLE_MEDIUM_CODE = [
    """
    def process_data(data):
        result = []
        for item in data:
            if item > 0:
                x = item * 2
                y = x + 1
                z = y * item
                result.append(z)
        return result
    """,
    """
    class DataProcessor:
        def __init__(self):
            self.data = []
        
        def add_data(self, item):
            self.data.append(item)
        
        def process(self):
            for i in range(len(self.data)):
                self.data[i] = self.data[i] * 2
            return self.data
    """,
]

SAMPLE_BAD_CODE = [
    """
    def x(d):
        r=[]
        for i in d:
            if i>0:
                r.append(i*2)
        return r
    """,
    """
    class A:
        def b(self):
            x=1;y=2;z=3;x=x+y;y=y+z;z=x+y;return x
    """,
    """
    def compute(a,b,c,d,e,f,g,h):
        return a+b+c+d+e+f+g+h if a>b and b>c and c>d and d>e and e>f and f>g and g>h else 0
    """,
]


def create_sample_dataset():
    """Create sample dataset with labels"""
    print("📊 Creating sample dataset...")
    
    # Code samples and quality labels (0-100)
    code_samples = SAMPLE_GOOD_CODE + SAMPLE_MEDIUM_CODE + SAMPLE_BAD_CODE
    labels = [90, 88, 92] + [65, 60] + [35, 40, 38]
    
    print(f"   Total samples: {len(code_samples)}")
    print(f"   Good code (80-100): {sum(1 for l in labels if l >= 80)}")
    print(f"   Medium code (50-79): {sum(1 for l in labels if 50 <= l < 80)}")
    print(f"   Bad code (0-49): {sum(1 for l in labels if l < 50)}")
    
    return code_samples, labels


def extract_features_and_embeddings(code_samples, batch_size=4):
    """Extract features and generate embeddings"""
    print("\n🔧 Extracting features and generating embeddings...")
    
    # Feature extraction
    extractor = CodeFeatureExtractor()
    features_list = []
    for code in code_samples:
        features = extractor.extract(code)
        features_list.append(features)
        print(f"   ✓ Extracted {len(features)} features")
    
    # Embedding generation
    print("\n   Generating embeddings (this may take a moment)...")
    try:
        generator = EmbeddingGenerator()
        embeddings = generator.generate(code_samples)
        print(f"   ✓ Generated embeddings shape: {embeddings.shape}")
        return features_list, embeddings
    except ImportError as e:
        print(f"   ⚠️  {e}")
        print("   Using random embeddings for demo...")
        embeddings = np.random.randn(len(code_samples), 768).astype(np.float32)
        return features_list, embeddings


def prepare_data(code_samples, labels, features_list, embeddings, split=0.8):
    """Prepare training/validation datasets"""
    print("\n📦 Preparing datasets...")
    
    # Create dataset
    dataset = CodeDataset(code_samples, labels, embeddings, features_list)
    
    # Split into train/val
    train_size = int(len(dataset) * split)
    val_size = len(dataset) - train_size
    
    indices = np.random.permutation(len(dataset))
    train_indices = indices[:train_size]
    val_indices = indices[train_size:]
    
    # Create subset datasets
    from torch.utils.data import Subset
    train_dataset = Subset(dataset, train_indices)
    val_dataset = Subset(dataset, val_indices)
    
    print(f"   Train samples: {len(train_dataset)}")
    print(f"   Val samples: {len(val_dataset)}")
    
    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=2, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=2, shuffle=False)
    
    return train_loader, val_loader, dataset


class TorchDataset(torch.utils.data.Dataset):
    """PyTorch-compatible dataset wrapper"""
    
    def __init__(self, code_dataset, indices):
        self.code_dataset = code_dataset
        self.indices = indices
    
    def __len__(self):
        return len(self.indices)
    
    def __getitem__(self, idx):
        actual_idx = self.indices[idx]
        embedding, features, label = self.code_dataset[actual_idx]
        return (
            torch.tensor(embedding, dtype=torch.float32),
            torch.tensor(features, dtype=torch.float32),
            torch.tensor(label, dtype=torch.float32)
        )


def train_quality_predictor():
    """Complete training pipeline for quality predictor"""
    print("="*60)
    print("🚀 ML QUALITY PREDICTOR TRAINING PIPELINE")
    print("="*60)
    
    # Step 1: Create dataset
    code_samples, labels = create_sample_dataset()
    
    # Step 2: Extract features and embeddings
    features_list, embeddings = extract_features_and_embeddings(code_samples)
    
    # Step 3: Prepare data
    code_dataset = CodeDataset(code_samples, labels, embeddings, features_list)
    
    # Split data
    train_size = int(len(code_dataset) * 0.8)
    val_size = len(code_dataset) - train_size
    train_indices = np.arange(train_size)
    val_indices = np.arange(train_size, len(code_dataset))
    
    train_dataset = TorchDataset(code_dataset, train_indices)
    val_dataset = TorchDataset(code_dataset, val_indices)
    
    train_loader = TorchDataLoader(train_dataset, batch_size=2, shuffle=True)
    val_loader = TorchDataLoader(val_dataset, batch_size=2, shuffle=False)
    
    print(f"   Train batches: {len(train_loader)}")
    print(f"   Val batches: {len(val_loader)}")
    
    # Step 4: Create model
    print("\n🧠 Creating Quality Predictor Model...")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = QualityPredictorModel(embedding_dim=768, feature_dim=50)
    
    # Loss and optimizer
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    lr_scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=3, verbose=True
    )
    
    # Step 5: Train
    print("\n📚 Training Model...")
    trainer = Trainer(model, criterion, optimizer, device=device)
    
    # Create custom training loop for our specific use case
    best_val_loss = float('inf')
    epochs = 20
    
    for epoch in range(1, epochs + 1):
        print(f"\n📊 Epoch {epoch}/{epochs}")
        
        # Training
        model.train()
        train_loss = 0
        for batch_idx, (embeddings_batch, features_batch, labels_batch) in enumerate(train_loader):
            embeddings_batch = embeddings_batch.to(device)
            features_batch = features_batch.to(device)
            labels_batch = labels_batch.to(device)
            
            optimizer.zero_grad()
            outputs = model(embeddings_batch, features_batch)
            loss = criterion(outputs.squeeze(), labels_batch)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        print(f"   Train loss: {train_loss:.4f}")
        
        # Validation
        model.eval()
        val_loss = 0
        predictions = []
        targets = []
        
        with torch.no_grad():
            for embeddings_batch, features_batch, labels_batch in val_loader:
                embeddings_batch = embeddings_batch.to(device)
                features_batch = features_batch.to(device)
                labels_batch = labels_batch.to(device)
                
                outputs = model(embeddings_batch, features_batch)
                loss = criterion(outputs.squeeze(), labels_batch)
                val_loss += loss.item()
                
                predictions.extend(outputs.squeeze().cpu().numpy())
                targets.extend(labels_batch.cpu().numpy())
        
        val_loss /= len(val_loader)
        print(f"   Val loss:   {val_loss:.4f}")
        
        # Calculate metrics
        predictions = np.array(predictions)
        targets = np.array(targets)
        mae = RegressionMetrics.mae(predictions, targets)
        r2 = RegressionMetrics.r2_score(predictions, targets)
        print(f"   MAE: {mae:.4f}, R²: {r2:.4f}")
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            os.makedirs('models', exist_ok=True)
            torch.save(model.state_dict(), 'models/quality_predictor.pth')
            print(f"   ✅ Model saved!")
    
    # Step 6: Evaluate
    print("\n📈 Final Evaluation:")
    print(f"   Best validation loss: {best_val_loss:.4f}")
    print(f"   Final MAE: {mae:.4f}")
    print(f"   Final R²: {r2:.4f}")
    
    return model


def demo_inference():
    """Demonstrate inference with trained model"""
    print("\n" + "="*60)
    print("🎯 INFERENCE DEMO")
    print("="*60)
    
    # Load model
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = QualityPredictorModel()
    model.load_state_dict(torch.load('models/quality_predictor.pth', map_location=device))
    model.to(device)
    model.eval()
    
    # Test code
    test_code = """
    def find_sum(numbers):
        '''Calculate sum of numbers in list'''
        total = 0
        for num in numbers:
            total += num
        return total
    """
    
    # Generate features and embedding
    extractor = CodeFeatureExtractor()
    features = extractor.extract(test_code)
    
    try:
        generator = EmbeddingGenerator()
        embedding = generator.generate_single(test_code)
    except ImportError:
        embedding = np.random.randn(768).astype(np.float32)
    
    # Prepare for inference
    embedding_tensor = torch.tensor(embedding, dtype=torch.float32).unsqueeze(0).to(device)
    
    # Convert features dict to tensor
    feature_keys = ['token_count', 'line_count', 'avg_line_length', 'nesting_depth',
                    'cyclomatic_complexity', 'num_functions', 'num_classes',
                    'num_branches', 'num_loops', 'num_comments']
    feature_values = np.array([features.get(k, 0) for k in feature_keys], dtype=np.float32)
    feature_values = np.clip(feature_values / (np.max(feature_values) + 1), 0, 1)[:50]
    features_tensor = torch.tensor(feature_values, dtype=torch.float32).unsqueeze(0).to(device)
    
    # Predict
    with torch.no_grad():
        quality_score = model(embedding_tensor, features_tensor)
    
    print(f"\n📝 Code:\n{test_code}")
    print(f"\n✅ Predicted quality score: {quality_score.item():.1f}/100")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("ML TRAINING PIPELINE: QUALITY PREDICTOR")
    print("="*60)
    
    # Train the model
    model = train_quality_predictor()
    
    # Demo inference
    try:
        demo_inference()
    except FileNotFoundError:
        print("\n⚠️  Model not found. Skipping inference demo.")
    
    print("\n✅ Training pipeline complete!")
    print("📁 Trained model saved to: models/quality_predictor.pth")
