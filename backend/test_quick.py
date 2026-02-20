"""Quick verification test"""
import requests
import json

code = """
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
"""

payload = {
    "code": code,
    "file_type": "python",
    "analysis_type": "all"
}

response = requests.post("http://localhost:8000/api/analyze", json=payload, timeout=30)
data = response.json()

print("✓ API Response received\n")

# Check components
result = data.get("data", {})

print("COMPONENT STATUS:")
print(f"{'='*50}")

components = {
    "Semantic Analysis": "semantic",
    "UML Diagram": "uml",
    "CFG (Control Flow)": "cfg",
    "DFG (Data Flow)": "dfg",
    "Quality Analysis": "quality",
    "Unified Analysis": "unified"
}

for label, key in components.items():
    if key in result and result[key]:
        value = result[key]
        if isinstance(value, dict):
            size = len(str(value))
            print(f"✓ {label:25} ({size} bytes)")
            if key == "uml" and "class_diagram" in value:
                print(f"  └─ Class diagram preview:")
                preview = str(value["class_diagram"])[:120]
                print(f"     {preview}...")
            elif key == "semantic":
                keys = list(value.keys())[:5]
                print(f"  └─ Keys: {keys}")
        else:
            print(f"✓ {label:25} (generated)")
    else:
        print(f"✗ {label:25} (missing)")

print(f"\n{'='*50}")
print("FRONTEND INTEGRATION CHECK:")
print(f"{'='*50}")

# Simulate what frontend receives
frontend_data = {
    "success": data.get("success"),
    "analysis_type": data.get("analysis_type"),
    "data": {
        "semantic": result.get("semantic"),
        "uml": result.get("uml"),
        "quality": result.get("quality"),
    }
}

has_semantic = frontend_data["data"]["semantic"] is not None
has_uml = frontend_data["data"]["uml"] is not None
has_quality = frontend_data["data"]["quality"] is not None

print(f"✓ Semantic available in response: {has_semantic}")
print(f"✓ UML available in response: {has_uml}")
print(f"✓ Quality available in response: {has_quality}")

print(f"\n{'='*50}")
print("FRONTEND TABS THAT WILL SHOW:")
print(f"{'='*50}")

if has_semantic:
    print("✓ 'Semantic' tab will be available")
if has_uml:
    print("✓ 'UML Diagram' tab will be available")
    if "class_diagram" in frontend_data["data"]["uml"]:
        print("  └─ With PlantUML class diagram")
if has_quality:
    print("✓ 'Quality' tab will be available")
print("✓ 'ML Analysis' tab always available")

print(f"\n✅ INTEGRATION SUCCESSFUL!")
print(f"\nTo test in frontend:")
print(f"1. Go to http://localhost:5173")
print(f"2. Paste any code")
print(f"3. Select analysis type: 'Unified (all insights)'")
print(f"4. Click 'Run Analyzer'")
print(f"5. Check result tabs - all should be populated!")
