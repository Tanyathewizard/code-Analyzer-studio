"""
Test UML generation endpoint integration
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# Test 1: Generate a class diagram
def test_class_diagram():
    print("\n" + "="*60)
    print("TEST 1: Class Diagram Generation")
    print("="*60)
    
    payload = {
        "data": {
            "name": "User",
            "attributes": [
                {"name": "id", "type": "int"},
                {"name": "username", "type": "str"},
                {"name": "email", "type": "str"},
                {"name": "created_at", "type": "datetime"}
            ],
            "methods": [
                {"name": "get_profile", "params": []},
                {"name": "update_email", "params": ["email: str"]},
                {"name": "delete_account", "params": []}
            ],
            "relationships": [
                {"from": "User", "type": "--|>", "to": "BaseModel"}
            ]
        },
        "diagram_type": "class"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/generate-uml", json=payload)
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print(f"✓ Class diagram generated successfully")
                print(f"\nDiagram (PlantUML):\n{result['diagram']}")
            else:
                print(f"✗ Error: {result['error']}")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"✗ Connection error: {e}")
        print("Make sure the backend is running: python backend.py")


# Test 2: Generate a sequence diagram
def test_sequence_diagram():
    print("\n" + "="*60)
    print("TEST 2: Sequence Diagram Generation")
    print("="*60)
    
    payload = {
        "data": {
            "calls": [
                {"caller": "Client", "callee": "AuthService", "method": "login"},
                {"caller": "AuthService", "callee": "Database", "method": "get_user"},
                {"caller": "Database", "callee": "AuthService", "method": "return_user_data"},
                {"caller": "AuthService", "callee": "Client", "method": "return_token"}
            ]
        },
        "diagram_type": "sequence"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/generate-uml", json=payload)
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print(f"✓ Sequence diagram generated successfully")
                print(f"\nDiagram (PlantUML):\n{result['diagram']}")
            else:
                print(f"✗ Error: {result['error']}")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Connection error: {e}")


# Test 3: Generate an ERD (Entity Relationship Diagram)
def test_erd_diagram():
    print("\n" + "="*60)
    print("TEST 3: Entity Relationship Diagram (ERD)")
    print("="*60)
    
    payload = {
        "data": {
            "entities": {
                "User": [
                    {"name": "id", "type": "INT PRIMARY KEY"},
                    {"name": "username", "type": "VARCHAR(50)"},
                    {"name": "email", "type": "VARCHAR(100)"}
                ],
                "Post": [
                    {"name": "id", "type": "INT PRIMARY KEY"},
                    {"name": "user_id", "type": "INT"},
                    {"name": "title", "type": "VARCHAR(200)"},
                    {"name": "content", "type": "TEXT"}
                ],
                "Comment": [
                    {"name": "id", "type": "INT PRIMARY KEY"},
                    {"name": "post_id", "type": "INT"},
                    {"name": "user_id", "type": "INT"},
                    {"name": "text", "type": "TEXT"}
                ]
            },
            "relations": [
                {"from": "User", "type": "||--o{", "to": "Post", "label": "creates"},
                {"from": "Post", "type": "||--o{", "to": "Comment", "label": "has"},
                {"from": "User", "type": "||--o{", "to": "Comment", "label": "writes"}
            ]
        },
        "diagram_type": "erd"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/generate-uml", json=payload)
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print(f"✓ ERD generated successfully")
                print(f"\nDiagram (PlantUML):\n{result['diagram']}")
            else:
                print(f"✗ Error: {result['error']}")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Connection error: {e}")


if __name__ == "__main__":
    print("\n🚀 UML Generator Backend Integration Tests")
    print("=" * 60)
    
    test_class_diagram()
    test_sequence_diagram()
    test_erd_diagram()
    
    print("\n" + "="*60)
    print("Tests complete!")
    print("To visualize the diagrams, paste the PlantUML output into:")
    print("https://www.plantuml.com/plantuml/uml/")
