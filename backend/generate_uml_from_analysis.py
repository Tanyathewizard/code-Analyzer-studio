"""
Generate UML diagram from semantic analysis result
Converts semantic_result.json to UML class diagram via backend API
"""

import json
import requests
import sys

# Load the analysis result
print("📂 Loading analysis result...")
try:
    with open('analysis_result.json', 'r') as f:
        analysis_data = json.load(f)
    print("✓ Loaded analysis result")
except Exception as e:
    print(f"✗ Error loading file: {e}")
    sys.exit(1)

# Extract classes and functions from CFG nodes
print("\n🔄 Extracting classes and functions from CFG...")

classes = []
functions = []

if 'cfg' in analysis_data and 'nodes' in analysis_data['cfg']:
    for node in analysis_data['cfg']['nodes']:
        node_name = node.get('name', '')
        node_kind = node.get('kind', '')

        if node_kind == 'stmt' and 'ClassDef' in node_name:
            # Extract class name from ClassDef statement
            class_name = node_name.replace('stmt_ClassDef_', '').split('_')[0]
            if class_name and class_name not in [c['name'] for c in classes]:
                classes.append({
                    "name": class_name,
                    "attributes": [],
                    "methods": []
                })

        elif node_kind == 'function':
            # Extract function name
            func_name = node_name.replace('function_', '').split('_')[0]
            if func_name and func_name not in [f['name'] for f in functions]:
                functions.append({
                    "name": func_name,
                    "params": []
                })

# Extract attributes from DFG assignments if available
if 'dfg' in analysis_data and 'assignments' in analysis_data['dfg']:
    for var, lines in analysis_data['dfg']['assignments'].items():
        if var not in ['_', '__name__']:  # Skip common variables
            # Try to associate with classes
            for cls in classes:
                if var.startswith(cls['name'].lower()) or var in ['a', 'b']:  # Simple heuristic
                    if not any(attr['name'] == var for attr in cls['attributes']):
                        cls['attributes'].append({"name": var, "type": "unknown"})

# Transform to UML format
print("\n🔄 Transforming to UML format...")

if classes:
    # Use the first class as main class
    main_class = classes[0]
    uml_data = {
        "name": main_class['name'],
        "attributes": main_class['attributes'],
        "methods": [{"name": f['name'], "params": f['params']} for f in functions],
        "relationships": []
    }
    print(f"✓ Transformed to UML class: {uml_data['name']}")
    print(f"  - Attributes: {len(uml_data['attributes'])}")
    print(f"  - Methods: {len(uml_data['methods'])}")
else:
    # Fallback to a generic class with extracted functions
    uml_data = {
        "name": "CodeModule",
        "attributes": [],
        "methods": [{"name": f['name'], "params": f['params']} for f in functions],
        "relationships": []
    }
    print(f"✓ Transformed to UML class: {uml_data['name']}")
    print(f"  - Methods: {len(uml_data['methods'])}")

# Call backend API to generate UML
print("\n🌐 Calling backend API...")
try:
    response = requests.post(
        'http://localhost:8000/api/generate-uml',
        json={
            "data": uml_data,
            "diagram_type": "class"
        },
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"✗ API Error: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    result = response.json()
    
    if not result['success']:
        print(f"✗ Generation failed: {result.get('error')}")
        sys.exit(1)
    
    diagram = result['diagram']
    print("✓ UML generated successfully!")
    
except requests.exceptions.ConnectionError:
    print("✗ Cannot connect to backend!")
    print("   Make sure backend is running: python backend.py")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

# Display the diagram
print("\n" + "="*70)
print("📊 GENERATED UML DIAGRAM (PlantUML)")
print("="*70)
print(diagram)
print("="*70)

# Save diagram to file
output_file = 'generated_diagram.puml'
try:
    with open(output_file, 'w') as f:
        f.write(diagram)
    print(f"\n✓ Saved to: {output_file}")
except Exception as e:
    print(f"✗ Error saving file: {e}")

# Instructions
print("\n📖 TO VIEW THE DIAGRAM:")
print("="*70)
print("Option 1: Online Viewer")
print("  1. Go to: https://www.plantuml.com/plantuml/uml/")
print("  2. Paste the diagram above")
print("  3. Click 'Render'")
print()
print("Option 2: VS Code")
print("  1. Install 'PlantUML' extension")
print("  2. Open generated_diagram.puml")
print("  3. Preview the diagram")
print()
print("Option 3: Python (if plantuml installed)")
print("  pip install plantuml")
print("  python -c \"from plantuml import PlantUML; PlantUML().processes(open('generated_diagram.puml').read())\"")
print("="*70)

print("\n✅ Done!")
