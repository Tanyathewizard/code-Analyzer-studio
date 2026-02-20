"""
ML Data Pipeline: Code Preprocessing and Feature Extraction
Converts raw code into ML-ready features and embeddings
"""

import re
import ast
import json
from typing import List, Dict, Any, Tuple
from pathlib import Path
import numpy as np


class CodePreprocessor:
    """Preprocess and tokenize source code"""
    
    def __init__(self):
        self.patterns = {
            'comments': r'#.*?$|/\*.*?\*/',
            'strings': r'["\'].*?["\']',
            'numbers': r'\b\d+\.?\d*\b',
            'operators': r'[+\-*/=<>!&|]',
        }
    
    def tokenize(self, code: str, remove_comments=True) -> List[str]:
        """Tokenize code into meaningful tokens"""
        if remove_comments:
            code = self._remove_comments(code)
        
        # Split by whitespace and special characters
        tokens = re.findall(r'\b\w+\b|[^\w\s]', code)
        return [t for t in tokens if t.strip()]
    
    def _remove_comments(self, code: str) -> str:
        """Remove comments from code"""
        # Python-style comments
        code = re.sub(r'#.*?$', '', code, flags=re.MULTILINE)
        # C-style comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        return code
    
    def normalize(self, code: str) -> str:
        """Normalize code formatting"""
        # Lowercase
        code = code.lower()
        # Remove extra whitespace
        code = re.sub(r'\s+', ' ', code)
        return code.strip()
    
    def extract_identifiers(self, code: str) -> List[str]:
        """Extract variable, function, and class names"""
        identifiers = re.findall(r'\b[a-zA-Z_]\w*\b', code)
        # Filter out keywords
        keywords = {
            'def', 'class', 'if', 'else', 'for', 'while', 'return',
            'import', 'from', 'try', 'except', 'function', 'const', 'let', 'var'
        }
        return [i for i in identifiers if i.lower() not in keywords]


class CodeFeatureExtractor:
    """Extract structural and complexity features from code"""
    
    def extract(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """
        Extract comprehensive features from code
        
        Features:
        - token_count: Number of tokens
        - line_count: Number of lines
        - avg_line_length: Average characters per line
        - nesting_depth: Maximum nesting level
        - cyclomatic_complexity: Approximate McCabe complexity
        - num_functions: Number of function definitions
        - num_classes: Number of class definitions
        - num_branches: If/else/switch statements
        - num_loops: For/while loops
        - code_to_comment_ratio: Code vs comment lines
        """
        
        preprocessor = CodePreprocessor()
        tokens = preprocessor.tokenize(code)
        lines = code.split('\n')
        
        features = {
            'token_count': len(tokens),
            'line_count': len(lines),
            'avg_line_length': np.mean([len(l) for l in lines]) if lines else 0,
            'nesting_depth': self._calculate_nesting_depth(code),
            'cyclomatic_complexity': self._calculate_complexity(code),
            'num_functions': len(re.findall(r'\bdef\b|\bfunction\b', code)),
            'num_classes': len(re.findall(r'\bclass\b', code)),
            'num_branches': len(re.findall(r'\bif\b|\belse\b|\bswitch\b', code)),
            'num_loops': len(re.findall(r'\bfor\b|\bwhile\b', code)),
            'num_comments': len(re.findall(r'#|//', code)),
            'has_error_handling': bool(re.search(r'\btry\b|\bexcept\b|\bcatch\b', code)),
            'code_length': len(code),
        }
        
        return features
    
    def _calculate_nesting_depth(self, code: str) -> int:
        """Calculate maximum nesting depth"""
        try:
            tree = ast.parse(code)
            max_depth = 0
            
            class DepthVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.depth = 0
                    self.max_depth = 0
                
                def generic_visit(self, node):
                    self.depth += 1
                    self.max_depth = max(self.max_depth, self.depth)
                    super().generic_visit(node)
                    self.depth -= 1
            
            visitor = DepthVisitor()
            visitor.visit(tree)
            return visitor.max_depth
        except:
            return 0
    
    def _calculate_complexity(self, code: str) -> int:
        """Calculate approximate cyclomatic complexity"""
        try:
            tree = ast.parse(code)
            complexity = 1
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
            
            return complexity
        except:
            return 1


class CodeDataset:
    """PyTorch-compatible dataset for code samples"""
    
    def __init__(self, code_samples: List[str], labels: List[float], 
                 embeddings: np.ndarray, features_list: List[Dict]):
        """
        Args:
            code_samples: List of code strings
            labels: Quality/complexity scores
            embeddings: Pre-computed embeddings (N x embedding_dim)
            features_list: List of extracted features for each sample
        """
        self.code_samples = code_samples
        self.labels = np.array(labels, dtype=np.float32)
        self.embeddings = embeddings.astype(np.float32)
        self.features_list = features_list
    
    def __len__(self) -> int:
        return len(self.code_samples)
    
    def __getitem__(self, idx: int) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Returns:
            embedding: Code embedding (768,)
            features: Extracted features (50,)
            label: Quality score or complexity
        """
        embedding = self.embeddings[idx]
        features_dict = self.features_list[idx]
        features = self._dict_to_array(features_dict)
        label = self.labels[idx]
        
        return embedding, features, label
    
    def _dict_to_array(self, features_dict: Dict) -> np.ndarray:
        """Convert feature dict to normalized array"""
        feature_keys = [
            'token_count', 'line_count', 'avg_line_length', 'nesting_depth',
            'cyclomatic_complexity', 'num_functions', 'num_classes',
            'num_branches', 'num_loops', 'num_comments'
        ]
        
        values = [features_dict.get(k, 0) for k in feature_keys]
        # Normalize to 0-1 range (approximate)
        normalized = np.array(values, dtype=np.float32)
        normalized = np.clip(normalized / (np.max(values) + 1), 0, 1)
        
        return normalized[:50]  # Pad or trim to 50 features


class EmbeddingGenerator:
    """Generate code embeddings using sentence-transformers"""
    
    def __init__(self, model_name: str = 'sentence-transformers/code-search-distilroberta-base'):
        """
        Initialize with pre-trained code embedding model
        
        Options:
        - 'sentence-transformers/code-search-distilroberta-base' (768-dim)
        - 'sentence-transformers/CodeBERTa-small-v1' (512-dim)
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = 768 if 'distilroberta' in model_name else 512
        except ImportError:
            raise ImportError("Install sentence-transformers: pip install sentence-transformers")
    
    def generate(self, code_samples: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple code samples
        
        Args:
            code_samples: List of code strings
            
        Returns:
            embeddings: (N, embedding_dim) array
        """
        embeddings = self.model.encode(code_samples, show_progress_bar=True)
        return embeddings.astype(np.float32)
    
    def generate_single(self, code: str) -> np.ndarray:
        """Generate embedding for single code sample"""
        embedding = self.model.encode([code])[0]
        return embedding.astype(np.float32)


class DataLoader:
    """Load and batch code datasets for training"""
    
    def __init__(self, dataset: CodeDataset, batch_size: int = 32, shuffle: bool = True):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.indices = np.arange(len(dataset))
        if shuffle:
            np.random.shuffle(self.indices)
    
    def __iter__(self):
        """Iterate over batches"""
        for i in range(0, len(self.dataset), self.batch_size):
            batch_indices = self.indices[i:i + self.batch_size]
            
            embeddings, features, labels = [], [], []
            for idx in batch_indices:
                e, f, l = self.dataset[idx]
                embeddings.append(e)
                features.append(f)
                labels.append(l)
            
            import torch
            yield (
                torch.tensor(np.array(embeddings)),
                torch.tensor(np.array(features)),
                torch.tensor(np.array(labels))
            )
    
    def __len__(self) -> int:
        return (len(self.dataset) + self.batch_size - 1) // self.batch_size


if __name__ == '__main__':
    # Example usage
    print("Code ML Data Pipeline")
    
    # Example code
    sample_code = """
    def calculate_fibonacci(n):
        if n <= 1:
            return n
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
    """
    
    # Test preprocessing
    print("\n1. Preprocessing:")
    preprocessor = CodePreprocessor()
    tokens = preprocessor.tokenize(sample_code)
    print(f"   Tokens: {tokens[:10]}...")
    
    # Test feature extraction
    print("\n2. Feature Extraction:")
    extractor = CodeFeatureExtractor()
    features = extractor.extract(sample_code)
    print(f"   Features: {json.dumps(features, indent=2)}")
    
    # Test embedding generation (requires sentence-transformers)
    print("\n3. Embedding Generation:")
    try:
        generator = EmbeddingGenerator()
        embedding = generator.generate_single(sample_code)
        print(f"   Embedding shape: {embedding.shape}")
        print(f"   First 5 values: {embedding[:5]}")
    except ImportError as e:
        print(f"   Note: {e}")
    
    print("\n✅ ML Data Pipeline Ready!")
