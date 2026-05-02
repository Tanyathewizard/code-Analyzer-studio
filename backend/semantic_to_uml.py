from backend import semantic_extractor
import json

def semantic_to_uml(semantic_data, diagram_type="class"):
    """
    Accepts either:
     - list of class dicts: [{ "name": ..., "attributes": [...], "methods": [...], ... }, ...]
     - OR a semantic dict returned by semantic_extractor (with 'functions'/'outputs'/'name', etc.)
    Normalizes to a list-of-classes for class/sequence generation.
    """
    # Normalize input into a list of classes/participants
    class_list = _normalize_to_class_list(semantic_data)

    if diagram_type == "class":
        return build_class_diagram(class_list)
    elif diagram_type == "sequence":
        return build_sequence_diagram(class_list)
    elif diagram_type == "activity":
        return build_activity_diagram(semantic_data)
    elif diagram_type == "usecase":
        return build_usecase_diagram(semantic_data)
    elif diagram_type == "component":
        return build_component_diagram(class_list)
    else:
        return "@startuml\n' Invalid diagram type\n@enduml"

def _normalize_to_class_list(semantic_data):
    # If already a list, assume it's the class list
    if isinstance(semantic_data, list):
        return semantic_data

    # If dict with a 'classes' key, prefer that
    if isinstance(semantic_data, dict) and "classes" in semantic_data and isinstance(semantic_data["classes"], list):
        return semantic_data["classes"]

    # If dict shaped like our semantic_extractor fallback, build classes from "name"/"functions"/"outputs"
    if isinstance(semantic_data, dict):
        name = semantic_data.get("name")
        functions = semantic_data.get("functions", [])
        outputs = semantic_data.get("outputs", [])
        attrs = semantic_data.get("attributes", []) or semantic_data.get("dependencies", []) or []
        # If semantic_data is a module-level dict with multiple entities in 'entities' key, expand those
        if "entities" in semantic_data and isinstance(semantic_data["entities"], list):
            # Expect each entity to be class-like
            return semantic_data["entities"]
        # Build at least one entry based on name + functions
        if name:
            return [{
                "name": name,
                "attributes": attrs,
                "methods": functions,
                "relations": outputs or []
            }]
        # If no name but functions exist, create a pseudo-class
        if functions:
            return [{
                "name": "Module",
                "attributes": attrs,
                "methods": functions,
                "relations": outputs or []
            }]
    # Fallback: empty list
    return []

def build_class_diagram(data):
    uml = "@startuml\n"
    for cls in data:
        # safe name extraction
        cls_name = cls.get("name", "Unknown")
        uml += f"class {cls_name} {{\n"
        for a in cls.get("attributes", []):
            # attribute might be dict or string
            if isinstance(a, dict):
                uml += f"  +{a.get('name','attr')} : {a.get('type','')}\n"
            else:
                uml += f"  +{a}\n"
        for m in cls.get("methods", []):
            # method might be dict or string
            if isinstance(m, dict):
                params = m.get("params", [])
                uml += f"  +{m.get('name','method')}({', '.join(params)})\n"
            else:
                uml += f"  +{m}()\n"
        uml += "}\n"
        for r in cls.get("relations", []):
            uml += f"{cls_name} --> {r}\n"
    uml += "@enduml"
    return uml

def build_sequence_diagram(data):
    uml = "@startuml\n"
    # participants
    for item in data:
        name = item.get("name", "Unknown")
        uml += f"participant {name}\n"
    uml += "\n"
    # calls: we accept either "calls" under each item or "relations"
    for item in data:
        caller = item.get("name", "Unknown")
        calls = item.get("calls", [])
        # calls can be strings "Target:method" or dicts
        for call in calls:
            if isinstance(call, str):
                # attempt to split into callee and method
                if ":" in call:
                    callee, method = call.split(":", 1)
                    uml += f"{caller} -> {callee.strip()}: {method.strip()}\n"
                else:
                    uml += f"{caller} -> {call}: call()\n"
            elif isinstance(call, dict):
                callee = call.get("callee", "Unknown")
                method = call.get("method", "call")
                uml += f"{caller} -> {callee}: {method}\n"
    uml += "@enduml"
    return uml

def build_activity_diagram(data):
    uml = "@startuml\nstart\n"
    for step in data.get("steps", []):
        uml += f":{step};\n"
    uml += "stop\n@enduml"
    return uml

def build_usecase_diagram(data):
    uml = "@startuml\n"
    for actor in data.get("actors", []):
        uml += f"actor {actor}\n"
    for uc in data.get("usecases", []):
        uml += f"usecase {uc}\n"
    for rel in data.get("relations", []):
        uml += f"{rel.get('from')} --> {rel.get('to')}\n"
    uml += "@enduml"
    return uml

def build_component_diagram(data):
    uml = "@startuml\n"
    for comp in data:
        name = comp.get("name", "Component")
        uml += f"[{name}]\n"
        for dep in comp.get("depends_on", []):
            uml += f"{name} --> {dep}\n"
    uml += "@enduml"
    return uml
