"""
TEST ML ANALYSIS - How to test the complete ML integration
=========================================================

This file shows you exactly where to put your test code and how to use the system.
"""

# ============================================================================
# STEP 1: Where to put your Python code for testing
# ============================================================================

TEST_CODE_SAMPLE_1 = """
def calculate_fibonacci(n):
    '''Calculate fibonacci number at position n'''
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def process_data(data):
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            if data[i] > data[j]:
                result.append((i, j))
    return result

class DataProcessor:
    def __init__(self):
        self.cache = {}
    
    def analyze(self, dataset):
        x = 0
        y = 0
        z = 0
        for item in dataset:
            x += item
            y += item * 2
            z += item * 3
        return x, y, z
"""

TEST_CODE_SAMPLE_2 = """
def sort_array(arr):
    # Bubble sort - inefficient O(n²)
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

def find_max(arr):
    if not arr:
        return None
    max_val = arr[0]
    for val in arr:
        if val > max_val:
            max_val = val
    return max_val

def process_strings(strings):
    result = []
    for s in strings:
        # SQL injection vulnerability
        query = f"SELECT * FROM users WHERE name = '{s}'"
        result.append(query)
    return result
"""

TEST_CODE_SAMPLE_3 = """
def add(a, b):
    '''Add two numbers'''
    return a + b

def multiply(a, b):
    '''Multiply two numbers'''
    return a * b

def divide(a, b):
    '''Divide a by b with error handling'''
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

class Calculator:
    def __init__(self):
        self.history = []
    
    def compute(self, op, a, b):
        if op == '+':
            result = add(a, b)
        elif op == '*':
            result = multiply(a, b)
        elif op == '/':
            result = divide(a, b)
        else:
            raise ValueError(f"Unknown operation: {op}")
        
        self.history.append((op, a, b, result))
        return result
"""

# ============================================================================
# STEP 2: How to test via the Backend API
# ============================================================================

"""
Option A: Using cURL (Windows PowerShell)
==========================================

1. Start the backend first:
   cd d:\auto ai project
   .\env11\Scripts\activate.bat
   python -m uvicorn backend:app --reload

2. In another terminal, run the test:
   
   $body = @{
       code = @"
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"@
       file_type = "python"
       analysis_type = "all"
   } | ConvertTo-Json
   
   Invoke-WebRequest -Uri "http://localhost:8000/api/analyze" `
     -Method POST `
     -Body $body `
     -ContentType "application/json" | Select-Object -ExpandProperty Content


Option B: Using Python requests
================================

import requests
import json

code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''

response = requests.post(
    "http://localhost:8000/api/analyze",
    json={
        "code": code,
        "file_type": "python",
        "analysis_type": "all"
    }
)

print(json.dumps(response.json(), indent=2))


Option C: Using Frontend (Recommended)
======================================

1. Start the backend:
   cd d:\auto ai project
   .\env11\Scripts\activate.bat
   python -m uvicorn backend:app --reload

2. In another terminal, start the frontend:
   cd d:\auto ai project\frontend
   npm run dev

3. Open http://localhost:5173

4. Paste your Python code in the analysis area

5. Click "Analyze" button

6. Navigate to "ML Analysis" tab to see:
   - Quality score (0-100)
   - Issue classification (Minor/Moderate/Severe/Critical)
   - Confidence percentage
   - Code metrics (lines, tokens, complexity, etc.)
   - Auto-generated recommendations
"""

# ============================================================================
# STEP 3: Understanding the ML Analysis Response
# ============================================================================

EXAMPLE_ML_RESPONSE = {
    "success": True,
    "data": {
        "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
        "cfg": {
            "nodes": [...],
            "edges": [...]
        },
        "dfg": {
            "assignments": {...},
            "uses": {...}
        },
        "semantic": {
            "purpose": "Calculates fibonacci number recursively",
            "patterns": ["recursion"],
            "complexity": "High - exponential time complexity"
        },
        "quality": {
            "score": 45,
            "issues": ["Inefficient recursion", "No memoization"],
            "grade": "C"
        },
        "ml_analysis": {
            "quality_score": 52,
            "issue_type": "Moderate",
            "confidence": 0.87,
            "metrics": {
                "lines_of_code": 4,
                "cyclomatic_complexity": 2,
                "token_count": 23,
                "function_count": 1,
                "class_count": 0,
                "nesting_depth": 2
            },
            "recommendations": [
                "Add memoization to improve performance",
                "Consider iterative approach",
                "Add input validation"
            ]
        }
    },
    "analysis_type": "all"
}

# ============================================================================
# STEP 4: What Each Tab Shows
# ============================================================================

"""
After running analysis, you'll see multiple tabs:

1. DATA SECTIONS (first N-3 tabs)
   - Shows semantic analysis results
   - Shows quality metrics
   - Shows unified IR analysis

2. DIAGRAM SUITE (Graphs tab)
   - Control Flow Graph (CFG)
   - Data Flow Graph (DFG)

3. UML DIAGRAM (if semantic data exists)
   - Auto-generated UML from code structure

4. ML ANALYSIS (Latest tab - just integrated)
   - Quality score with color coding
   - Issue type classification
   - Confidence percentage
   - Code metrics dashboard
   - Auto-generated recommendations
"""

# ============================================================================
# STEP 5: Test Different Code Patterns
# ============================================================================

PROBLEMATIC_CODE = """
# This code has many issues for ML to detect
def process(data):
    x=1
    y=2
    z=3
    for i in range(len(data)):
        for j in range(len(data)):
            for k in range(len(data)):
                x = x + data[i] + data[j] + data[k]
    # SQL injection vulnerability
    query = "SELECT * FROM users WHERE id = '" + str(x) + "'"
    return query
"""

GOOD_CODE = """
def calculate_sum(numbers):
    '''Calculate sum of a list of numbers with validation.'''
    if not isinstance(numbers, list):
        raise TypeError("Input must be a list")
    if not numbers:
        return 0
    
    total = sum(numbers)
    return total

def process_data(data, batch_size=100):
    '''Process data in batches efficiently.'''
    results = []
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        results.extend([x * 2 for x in batch])
    return results
"""

# ============================================================================
# STEP 6: Quick API Endpoints Reference
# ============================================================================

"""
Endpoint: POST /api/analyze
----------------------------
Purpose: Run complete analysis (CFG, DFG, Semantic, Quality, IR, ML)
Input:
  {
    "code": "your python code here",
    "file_type": "python",
    "analysis_type": "all"  // or "semantic", "quality", "unified"
  }
Response:
  Contains: code, cfg, dfg, semantic, quality, ml_analysis, etc.

Endpoint: POST /api/ml/analyze
-------------------------------
Purpose: ML-only analysis (fast, no semantic/quality)
Input:
  {
    "code": "your code",
    "file_type": "python",
    "analysis_type": "ml"
  }
Response:
  {
    "ml_analysis": {
      "quality_score": 75,
      "issue_type": "Minor",
      "confidence": 0.92,
      "metrics": {...},
      "recommendations": [...]
    }
  }

Endpoint: POST /api/ml/batch-analyze
-------------------------------------
Purpose: Analyze multiple code samples at once
Input:
  {
    "samples": [
      {"code": "sample1", "label": "function1"},
      {"code": "sample2", "label": "function2"}
    ]
  }
Response:
  Array of ML analysis results

Endpoint: GET /health
---------------------
Purpose: Check if backend is running
Response: {"status": "ok", "ml_available": true}
"""

# ============================================================================
# STEP 7: Run this test script
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ML ANALYSIS TESTING GUIDE")
    print("=" * 70)
    print()
    print("✅ Test Code Sample 1 (with issues):")
    print(TEST_CODE_SAMPLE_1)
    print()
    print("✅ Test Code Sample 2 (with vulnerabilities):")
    print(TEST_CODE_SAMPLE_2)
    print()
    print("✅ Test Code Sample 3 (clean code):")
    print(TEST_CODE_SAMPLE_3)
    print()
    print("=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("1. Pick a code sample above")
    print("2. Copy it to your analysis tool (frontend or API)")
    print("3. Click 'Analyze' or send POST request")
    print("4. Navigate to 'ML Analysis' tab")
    print("5. See quality score, issues, and recommendations")
    print()
    print("=" * 70)
