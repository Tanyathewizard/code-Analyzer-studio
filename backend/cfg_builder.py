import ast
from typing import Dict, List


def build_cfg(source: str) -> Dict:
    try:
        tree = ast.parse(source)
    except Exception:
        return {"nodes": [], "edges": []}

    nodes = {}
    edges = []

    def add_node(kind, name, lineno):
        node_id = f"{kind}_{name}_{lineno}"
        if node_id not in nodes:
            nodes[node_id] = {
                "id": node_id,
                "kind": kind,
                "name": name,
                "lineno": lineno
            }
        return node_id

    # 🔥 CORE: process block sequentially
    def process_block(statements, parent_id):
        prev_id = parent_id

        for stmt in statements:

            # ---- IF ----
            if isinstance(stmt, ast.If):
                nid = add_node("if", "if", stmt.lineno)
                edges.append({"from": prev_id, "to": nid, "type": "control"})

                # true branch
                true_end = process_block(stmt.body, nid)

                # false branch
                if stmt.orelse:
                    false_end = process_block(stmt.orelse, nid)
                else:
                    false_end = nid

                # merge point
                merge_id = add_node("merge", "merge", stmt.lineno)
                edges.append({"from": true_end, "to": merge_id, "type": "control"})
                edges.append({"from": false_end, "to": merge_id, "type": "control"})

                prev_id = merge_id

            # ---- LOOP ----
            elif isinstance(stmt, (ast.For, ast.While)):
                nid = add_node("loop", "loop", stmt.lineno)
                edges.append({"from": prev_id, "to": nid, "type": "control"})

                body_end = process_block(stmt.body, nid)

                # loop back edge
                edges.append({"from": body_end, "to": nid, "type": "loop"})

                prev_id = nid

            # ---- FUNCTION ----
            elif isinstance(stmt, ast.FunctionDef):
                nid = add_node("function", stmt.name, stmt.lineno)
                edges.append({"from": prev_id, "to": nid, "type": "control"})

                func_end = process_block(stmt.body, nid)
                prev_id = func_end

            # ---- FUNCTION CALL ----
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if isinstance(call.func, ast.Name):
                    cname = call.func.id
                elif isinstance(call.func, ast.Attribute):
                    cname = call.func.attr
                else:
                    cname = "call"

                nid = add_node("call", cname, stmt.lineno)
                edges.append({"from": prev_id, "to": nid, "type": "call"})
                prev_id = nid

            # ---- NORMAL STATEMENT ----
            else:
                nid = add_node("stmt", type(stmt).__name__, getattr(stmt, "lineno", 0))
                edges.append({"from": prev_id, "to": nid, "type": "control"})
                prev_id = nid

        return prev_id

    # 🔥 START NODE
    start_id = add_node("start", "start", 0)

    # 🔥 Process program sequentially
    end_id = process_block(tree.body, start_id)

    # 🔥 END NODE
    end_node = add_node("end", "end", 9999)
    edges.append({"from": end_id, "to": end_node, "type": "control"})

    return {
        "nodes": list(nodes.values()),
        "edges": edges
    }
