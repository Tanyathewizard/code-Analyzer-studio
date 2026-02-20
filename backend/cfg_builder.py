import ast
from typing import Dict

def build_cfg(source: str) -> Dict:
    try:
        tree = ast.parse(source)
    except Exception:
        return {"nodes": [], "edges": []}

    nodes = {}
    edges = []

    def add_node(kind, name, lineno):
        node_id = f"{kind}_{name}_{lineno}"  # <- replace ":" with "_"
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, "kind": kind, "name": name, "lineno": lineno}
        return node_id

    def walk_block(parent_id, block):
        for n in ast.iter_child_nodes(block):
            if isinstance(n, ast.If):
                nid = add_node("if", f"if_{n.lineno}", n.lineno)
                if parent_id:
                    edges.append({"from": parent_id, "to": nid, "type": "control"})
                walk_block(nid, n)
                continue

            if isinstance(n, (ast.For, ast.While)):
                nid = add_node("loop", f"loop_{n.lineno}", n.lineno)
                if parent_id:
                    edges.append({"from": parent_id, "to": nid, "type": "control"})
                walk_block(nid, n)
                continue

            if isinstance(n, ast.Call):
                if isinstance(n.func, ast.Name):
                    cname = n.func.id
                elif isinstance(n.func, ast.Attribute):
                    cname = n.func.attr
                else:
                    cname = "unknown"
                cid = add_node("call", cname, getattr(n, "lineno", 0))
                if parent_id:
                    edges.append({"from": parent_id, "to": cid, "type": "call"})
                continue

            walk_block(parent_id, n)

    start_id = add_node("start", "start", 0)

    for stmt in getattr(tree, "body", []):
        if isinstance(stmt, ast.FunctionDef):
            fid = add_node("function", stmt.name, stmt.lineno)
            edges.append({"from": start_id, "to": fid, "type": "control"})
            walk_block(fid, stmt)
        elif isinstance(stmt, ast.If):
            nid = add_node("if", f"if_{stmt.lineno}", stmt.lineno)
            edges.append({"from": start_id, "to": nid, "type": "control"})
        elif isinstance(stmt, (ast.For, ast.While)):
            nid = add_node("loop", f"loop_{stmt.lineno}", stmt.lineno)
            edges.append({"from": start_id, "to": nid, "type": "control"})
        else:
            nid = add_node("stmt", type(stmt).__name__, getattr(stmt, "lineno", 0))
            edges.append({"from": start_id, "to": nid, "type": "control"})

    return {"nodes": list(nodes.values()), "edges": edges}
