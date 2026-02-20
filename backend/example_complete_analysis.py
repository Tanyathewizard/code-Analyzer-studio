"""
Complete Working Example: Traditional ML + Neural Networks
Shows how to use all models together for code analysis
"""

import numpy as np
from ml_data import CodeFeatureExtractor
from ml_traditional import TraditionalMLModels
from ml_comparison import ComprehensiveModelComparison
import json
from datetime import datetime


class ProductionCodeAnalyzer:
    """
    Complete code analysis system combining all models
    Ready for production use
    """
    
    def __init__(self):
        self.ml_models = TraditionalMLModels()
        self.feature_extractor = CodeFeatureExtractor()
        self.analysis_history = []
    
    def analyze_code(self, code: str, use_ensemble: bool = True):
        """
        Comprehensive code analysis using all available models
        
        Args:
            code: Code sample to analyze
            use_ensemble: Use ensemble voting or single model
        
        Returns:
            Complete analysis report
        """
        
        print("\n" + "="*60)
        print("📊 CODE ANALYSIS REPORT")
        print("="*60)
        
        # Extract features
        print("\n1️⃣ Extracting Features...")
        features_dict = self.feature_extractor.extract(code)
        features_array = self._dict_to_array(features_dict)
        
        print(f"   Lines of code: {features_dict['line_count']}")
        print(f"   Cyclomatic complexity: {features_dict['cyclomatic_complexity']}")
        print(f"   Nesting depth: {features_dict['nesting_depth']}")
        print(f"   Functions: {features_dict['num_functions']}")
        print(f"   Classes: {features_dict['num_classes']}")
        
        # Quality Analysis
        print("\n2️⃣ Quality Analysis (0-100)...")
        quality_analysis = self._analyze_quality(features_array)
        print(f"   Random Forest: {quality_analysis['rf']:.1f}")
        print(f"   XGBoost: {quality_analysis['xgb']:.1f}")
        print(f"   Ensemble: {quality_analysis['ensemble']:.1f}")
        
        # Issue Classification
        print("\n3️⃣ Issue Classification...")
        issue_analysis = self._analyze_issues(features_array, use_ensemble)
        print(f"   Type: {issue_analysis['type']}")
        print(f"   Severity: {issue_analysis['severity']}/4")
        print(f"   Confidence: {issue_analysis['confidence']*100:.1f}%")
        
        # Recommendations
        print("\n4️⃣ Recommendations...")
        recommendations = self._generate_recommendations(features_dict, quality_analysis)
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        # Compile report
        report = {
            'timestamp': datetime.now().isoformat(),
            'code_stats': features_dict,
            'quality': quality_analysis,
            'issues': issue_analysis,
            'recommendations': recommendations,
            'code_snippet': code[:100] + '...' if len(code) > 100 else code
        }
        
        self.analysis_history.append(report)
        return report
    
    def batch_analyze(self, code_samples: dict):
        """
        Analyze multiple code samples
        
        Args:
            code_samples: {"file1.py": "code...", "file2.py": "code..."}
        
        Returns:
            Analysis for all files with summary
        """
        
        print("\n" + "="*60)
        print("📊 BATCH CODE ANALYSIS")
        print(f"   Analyzing {len(code_samples)} files...")
        print("="*60)
        
        results = {}
        statistics = {
            'total_files': len(code_samples),
            'avg_quality': 0,
            'issue_distribution': {0: 0, 1: 0, 2: 0, 3: 0},
            'files_by_severity': {'Critical': [], 'Severe': [], 'Moderate': [], 'Minor': []}
        }
        
        for filename, code in code_samples.items():
            print(f"\nAnalyzing {filename}...")
            
            features_dict = self.feature_extractor.extract(code)
            features_array = self._dict_to_array(features_dict)
            
            # Quick analysis
            quality = self._analyze_quality(features_array)['ensemble']
            issue = self._analyze_issues(features_array, use_ensemble=True)
            
            results[filename] = {
                'quality': quality,
                'issue_type': issue['type'],
                'severity': issue['severity'],
                'confidence': issue['confidence']
            }
            
            # Update statistics
            statistics['avg_quality'] += quality
            statistics['issue_distribution'][issue['severity']] += 1
            
            severity_names = {0: 'Minor', 1: 'Moderate', 2: 'Severe', 3: 'Critical'}
            statistics['files_by_severity'][severity_names[issue['severity']]].append(filename)
        
        statistics['avg_quality'] /= len(code_samples)
        
        # Print summary
        print("\n" + "="*60)
        print("📈 BATCH ANALYSIS SUMMARY")
        print("="*60)
        print(f"Average Quality: {statistics['avg_quality']:.1f}/100")
        print(f"\nIssue Distribution:")
        severity_names = ['Minor', 'Moderate', 'Severe', 'Critical']
        for i, name in enumerate(severity_names):
            count = statistics['issue_distribution'][i]
            print(f"  {name}: {count} files")
        
        return {
            'results': results,
            'statistics': statistics,
            'timestamp': datetime.now().isoformat()
        }
    
    def compare_with_baseline(self, code: str, baseline_quality: float):
        """
        Compare current code with baseline quality score
        """
        
        current_analysis = self.analyze_code(code)
        current_quality = current_analysis['quality']['ensemble']
        
        improvement = current_quality - baseline_quality
        improvement_pct = (improvement / baseline_quality * 100) if baseline_quality > 0 else 0
        
        print("\n" + "="*60)
        print("📊 COMPARISON WITH BASELINE")
        print("="*60)
        print(f"Baseline Quality: {baseline_quality:.1f}/100")
        print(f"Current Quality: {current_quality:.1f}/100")
        print(f"Change: {improvement:+.1f} ({improvement_pct:+.1f}%)")
        
        if improvement > 0:
            print("✅ Quality improved!")
        elif improvement < 0:
            print("⚠️  Quality decreased")
        else:
            print("➡️  No change")
        
        return {
            'baseline': baseline_quality,
            'current': current_quality,
            'improvement': improvement,
            'improvement_pct': improvement_pct
        }
    
    def _dict_to_array(self, features_dict: dict) -> np.ndarray:
        """Convert feature dict to array"""
        feature_keys = ['token_count', 'line_count', 'avg_line_length', 'nesting_depth',
                       'cyclomatic_complexity', 'num_functions', 'num_classes',
                       'num_branches', 'num_loops', 'num_comments']
        return np.array([features_dict.get(k, 0) for k in feature_keys])
    
    def _analyze_quality(self, features_array: np.ndarray) -> dict:
        """Predict code quality using multiple models"""
        
        rf_quality = self.ml_models.predict_rf_reg(features_array)
        xgb_quality = self.ml_models.predict_xgb_reg(features_array)
        
        ensemble_quality = (rf_quality + xgb_quality) / 2
        
        return {
            'rf': float(rf_quality),
            'xgb': float(xgb_quality),
            'ensemble': float(ensemble_quality)
        }
    
    def _analyze_issues(self, features_array: np.ndarray, use_ensemble: bool) -> dict:
        """Classify code issues"""
        
        if use_ensemble:
            # Get predictions from multiple models
            rf_issue, rf_conf = self.ml_models.predict_rf_clf(features_array)
            xgb_issue, xgb_conf = self.ml_models.predict_xgb_clf(features_array)
            
            # Vote on most confident prediction
            if rf_conf > xgb_conf:
                issue_type = int(rf_issue)
                confidence = float(rf_conf)
                model_used = "Random Forest"
            else:
                issue_type = int(xgb_issue)
                confidence = float(xgb_conf)
                model_used = "XGBoost"
        else:
            # Single model (fastest)
            issue_type, confidence = self.ml_models.predict_lr(features_array)
            issue_type = int(issue_type)
            confidence = float(confidence)
            model_used = "Logistic Regression"
        
        issue_names = ["Minor", "Moderate", "Severe", "Critical"]
        
        return {
            'type': issue_names[issue_type],
            'severity': issue_type,
            'confidence': confidence,
            'model': model_used
        }
    
    def _generate_recommendations(self, features_dict: dict, quality_analysis: dict) -> list:
        """Generate actionable recommendations"""
        
        recommendations = []
        quality = quality_analysis['ensemble']
        
        # Based on quality score
        if quality < 40:
            recommendations.append("🔴 Critical: Code quality is very low. Consider refactoring.")
        elif quality < 60:
            recommendations.append("🟠 Warning: Code quality is below acceptable. Review and improve.")
        elif quality < 80:
            recommendations.append("🟡 Code quality is acceptable but could be improved.")
        else:
            recommendations.append("🟢 Good code quality!")
        
        # Based on complexity
        complexity = features_dict['cyclomatic_complexity']
        if complexity > 10:
            recommendations.append(f"Complexity is high ({complexity}). Break into smaller functions.")
        
        # Based on nesting
        nesting = features_dict['nesting_depth']
        if nesting > 5:
            recommendations.append(f"Nesting depth is high ({nesting}). Flatten control flow.")
        
        # Based on size
        lines = features_dict['line_count']
        if lines > 100:
            recommendations.append(f"Function is long ({lines} lines). Consider splitting.")
        
        # Based on comments
        comments = features_dict['num_comments']
        if comments == 0 and lines > 10:
            recommendations.append("No comments found. Add documentation.")
        
        return recommendations


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == '__main__':
    
    print("🚀 Production Code Analyzer - Complete Example\n")
    
    # Initialize analyzer
    analyzer = ProductionCodeAnalyzer()
    
    # ===== EXAMPLE 1: Single File Analysis =====
    print("\n" + "█"*60)
    print("EXAMPLE 1: Single File Analysis")
    print("█"*60)
    
    code_sample_1 = """
def calculate_statistics(numbers):
    '''Calculate mean and standard deviation'''
    if not numbers:
        return None
    
    total = sum(numbers)
    mean = total / len(numbers)
    
    squared_diffs = [(x - mean) ** 2 for x in numbers]
    variance = sum(squared_diffs) / len(numbers)
    std_dev = variance ** 0.5
    
    return {'mean': mean, 'std_dev': std_dev}
"""
    
    report1 = analyzer.analyze_code(code_sample_1.strip())
    
    # ===== EXAMPLE 2: Poor Quality Code =====
    print("\n" + "█"*60)
    print("EXAMPLE 2: Poor Quality Code Analysis")
    print("█"*60)
    
    code_sample_2 = """
def f(x):
    if x>0:
        if x<10:
            if x==5:
                for i in range(x):
                    for j in range(x):
                        for k in range(x):
                            print(i,j,k)
"""
    
    report2 = analyzer.analyze_code(code_sample_2.strip())
    
    # ===== EXAMPLE 3: Batch Analysis =====
    print("\n" + "█"*60)
    print("EXAMPLE 3: Batch File Analysis")
    print("█"*60)
    
    code_samples = {
        "utils.py": """
def add(a, b):
    '''Add two numbers'''
    return a + b
""",
        "validator.py": """
def validate_email(email):
    if '@' in email and '.' in email:
        return True
    return False
""",
        "complex_logic.py": """
def process_data(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                for i in range(x):
                    for j in range(y):
                        for k in range(z):
                            result = i * j * k
    return result
"""
    }
    
    batch_report = analyzer.batch_analyze(code_samples)
    
    # ===== EXAMPLE 4: Baseline Comparison =====
    print("\n" + "█"*60)
    print("EXAMPLE 4: Baseline Comparison")
    print("█"*60)
    
    improved_code = """
def calculate_statistics(numbers):
    '''Calculate mean and standard deviation'''
    if not numbers:
        return None
    
    mean = sum(numbers) / len(numbers)
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    std_dev = variance ** 0.5
    
    return {'mean': mean, 'std_dev': std_dev}
"""
    
    comparison = analyzer.compare_with_baseline(improved_code.strip(), baseline_quality=72.5)
    
    # ===== SAVE RESULTS =====
    print("\n" + "="*60)
    print("💾 Saving results...")
    print("="*60)
    
    # Combine all analysis
    all_results = {
        'single_file': report1,
        'poor_quality': report2,
        'batch_analysis': batch_report,
        'baseline_comparison': comparison,
        'analysis_summary': {
            'total_analyses': len(analyzer.analysis_history),
            'timestamp': datetime.now().isoformat()
        }
    }
    
    # Save to JSON
    with open('analysis_results.json', 'w') as f:
        # Convert numpy types to native Python for JSON serialization
        results_json = json.dumps(all_results, indent=2, default=str)
        f.write(results_json)
    
    print("✅ Results saved to: analysis_results.json")
    
    print("\n" + "="*60)
    print("✨ Analysis Complete!")
    print("="*60)
    print(f"Total analyses performed: {len(analyzer.analysis_history)}")
    print(f"Timestamp: {datetime.now().isoformat()}")
