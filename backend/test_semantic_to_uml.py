#!/usr/bin/env python3
"""
Test script for the new /api/semantic-to-uml endpoint
"""

import requests
import json

def test_semantic_to_uml_endpoint():
    """Test the semantic to UML conversion endpoint"""

    # Sample semantic data (similar to what semantic_extractor might produce)
    test_data = {
        "semantic_data": {
            "classes": [
                {
                    "name": "User",
                    "attributes": [
                        {"name": "id", "type": "int"},
                        {"name": "email", "type": "str"}
                    ],
                    "methods": [
                        {"name": "login", "params": []},
                        {"name": "logout", "params": []}
                    ]
                },
                {
                    "name": "AuthService",
                    "attributes": [
                        {"name": "token", "type": "str"}
                    ],
                    "methods": [
                        {"name": "genToken", "params": []},
                        {"name": "validate", "params": []}
                    ]
                }
            ],
            "relationships": [
                {"from": "User", "to": "AuthService", "type": "-->"}
            ]
        },
        "diagram_type": "class"
    }

    try:
        # Test class diagram
        print("Testing class diagram generation...")
        response = requests.post(
            "http://127.0.0.1:8000/api/semantic-to-uml",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Class diagram test successful!")
            print(f"Diagram type: {result.get('diagram_type')}")
            print(f"Diagram length: {len(result.get('diagram', ''))}")
            print("Sample diagram output:")
            print(result.get('diagram', '')[:200] + "..." if len(result.get('diagram', '')) > 200 else result.get('diagram', ''))
        else:
            print(f"❌ Class diagram test failed: {response.text}")

        # Test sequence diagram
        print("\nTesting sequence diagram generation...")
        sequence_data = {
            "semantic_data": {
                "calls": [
                    {"caller": "User", "callee": "AuthService", "method": "authenticate"},
                    {"caller": "AuthService", "callee": "Database", "method": "get_user"}
                ]
            },
            "diagram_type": "sequence"
        }

        response = requests.post(
            "http://127.0.0.1:8000/api/semantic-to-uml",
            json=sequence_data,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Sequence diagram test successful!")
            print(f"Diagram type: {result.get('diagram_type')}")
            print(f"Diagram length: {len(result.get('diagram', ''))}")
            print("Sample diagram output:")
            print(result.get('diagram', '')[:200] + "..." if len(result.get('diagram', '')) > 200 else result.get('diagram', ''))
        else:
            print(f"❌ Sequence diagram test failed: {response.text}")

        # Test error cases
        print("\nTesting error cases...")

        # Empty semantic data
        error_data = {"semantic_data": {}, "diagram_type": "class"}
        response = requests.post(
            "http://127.0.0.1:8000/api/semantic-to-uml",
            json=error_data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 400:
            print("✅ Empty data error handling works")
        else:
            print(f"❌ Empty data test failed: {response.status_code}")

        # Invalid diagram type
        invalid_data = {"semantic_data": {"test": "data"}, "diagram_type": "invalid"}
        response = requests.post(
            "http://127.0.0.1:8000/api/semantic-to-uml",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 400:
            print("✅ Invalid diagram type error handling works")
        else:
            print(f"❌ Invalid type test failed: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the backend running?")
    except Exception as e:
        print(f"❌ Test error: {str(e)}")

if __name__ == "__main__":
    test_semantic_to_uml_endpoint()
