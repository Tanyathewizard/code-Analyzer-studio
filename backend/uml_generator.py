import json

# ===============================================================
#  AUTO-MAPPER FUNCTIONS
#  Convert backend semantic output → UML-friendly format
# ===============================================================

def map_semantic_to_class_uml(semantic):
    """
    Converts full semantic output to the correct input format
    for generate_class_diagram()
    """
    classes = semantic.get("classes", [])
    if not classes:
        return {}

    cls = classes[0]  # take first class for UML (simple version)

    return {
        "name": cls.get("name", "Unknown"),
        "attributes": [
            {"name": a.get("name", ""), "type": a.get("type", "any")}
            for a in cls.get("attributes", [])
        ],
        "methods": [
            {"name": m.get("name", ""), "params": m.get("params", [])}
            for m in cls.get("methods", [])
        ],
        "relationships": cls.get("relationships", [])
    }


def map_semantic_to_sequence_uml(semantic):
    """
    Converts semantic output for sequence diagram generation.
    Expects: {"calls": [{"caller": "...", "callee": "...", "method": "..."}]}
    """
    calls = semantic.get("calls", [])
    return {
        "calls": [
            {
                "caller": c.get("caller", "Unknown"),
                "callee": c.get("callee", "Unknown"),
                "method": c.get("method", "call")
            }
            for c in calls
        ]
    }


def map_semantic_to_erd(semantic):
    """
    Converts semantic output to ERD-friendly format
    """
    classes = semantic.get("classes", [])

    entities = {}
    relations = []

    for cls in classes:
        name = cls.get("name", "Unknown")
        fields = [
            {"name": a.get("name", ""), "type": a.get("type", "any")}
            for a in cls.get("attributes", [])
        ]
        entities[name] = fields

        for rel in cls.get("relationships", []):
            relations.append({
                "from": rel.get("from", name),
                "to": rel.get("to", ""),
                "type": rel.get("type", "-->"),
                "label": rel.get("label", "")
            })

    return {
        "entities": entities,
        "relations": relations
    }


# ===============================================================
#  UML DIAGRAM GENERATORS
# ===============================================================

def generate_class_diagram(data):
    name = data.get("name", "Unknown")
    attributes = data.get("attributes", [])
    methods = data.get("methods", [])
    relationships = data.get("relationships", [])

    lines = ["@startuml", f"class {name} {{"]

    # attributes
    for attr in attributes:
        lines.append(f"  - {attr['name']} : {attr.get('type', 'any')}")

    # methods
    for m in methods:
        params = ", ".join(m.get("params", []))
        lines.append(f"  + {m['name']}({params})")

    lines.append("}")

    # relations
    for rel in relationships:
        lines.append(f"{rel['from']} {rel['type']} {rel['to']}")

    lines.append("@enduml")

    return "\n".join(lines)


def generate_sequence_diagram(data):
    steps = data.get("calls", [])

    lines = ["@startuml"]

    for step in steps:
        caller = step["caller"]
        callee = step["callee"]
        method = step["method"]

        lines.append(f"{caller} -> {callee}: {method}()")
        lines.append(f"{callee} --> {caller}: return")

    lines.append("@enduml")
    return "\n".join(lines)


def generate_erd(data):
    entities = data.get("entities", {})
    relations = data.get("relations", [])

    lines = ["@startuml"]

    for name, fields in entities.items():
        lines.append(f"entity {name} {{")
        for f in fields:
            lines.append(f"  * {f['name']} : {f['type']}")
        lines.append("}")

    for r in relations:
        lines.append(f"{r['from']} {r['type']} {r['to']} : {r.get('label', '')}")

    lines.append("@enduml")
    return "\n".join(lines)


# ===============================================================
#  MAIN DISPATCH FUNCTION
# ===============================================================

def generate_uml(data, diagram_type="class"):
    """
    Main export used by backend.py
    Automatically parses JSON strings too
    """
    if isinstance(data, str):
        data = json.loads(data)

    if diagram_type == "class":
        return generate_class_diagram(data)

    if diagram_type == "sequence":
        return generate_sequence_diagram(data)

    if diagram_type == "erd":
        return generate_erd(data)

    raise ValueError(f"Invalid diagram type: {diagram_type}")
