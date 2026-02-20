# graph_generator.py
import os
import re
from graphviz import Digraph

GRAPH_STYLE = {
    "fontname": "Arial",
    "fontsize": "12",
    "node_fill": "#f5f5f5",
    "node_border": "#333333",
    "call_fill": "#e8f0ff",
    "if_fill": "#fff3cd",
    "loop_fill": "#e2f7e1",
    "edge_color": "#1a73e8",
    "data_edge_color": "#d62728"
}

def safe_node_id(raw: str) -> str:
    """Sanitize node IDs for Graphviz."""
    if raw is None:
        return "node_unknown"
    return re.sub(r'[^0-9A-Za-z_\-]', '_', str(raw))

def ensure_output_dir(path="output"):
    os.makedirs(path, exist_ok=True)
    return path

def generate_cfg_graph(cfg, output_path="output/cfg"):
    ensure_output_dir(os.path.dirname(output_path))
    if not cfg or "nodes" not in cfg or not cfg["nodes"]:
        return None

    dot = Digraph(comment="CFG")
    dot.attr(rankdir="TB", bgcolor="white")

    # Nodes
    for node in cfg["nodes"]:
        nid = safe_node_id(node["id"])
        color = GRAPH_STYLE["node_fill"]
        if node["kind"] == "if":
            color = GRAPH_STYLE["if_fill"]
        elif node["kind"] == "loop":
            color = GRAPH_STYLE["loop_fill"]
        elif node["kind"] == "call":
            color = GRAPH_STYLE["call_fill"]

        label = f"{node['kind'].upper()}\n{node['name']}\n(line {node['lineno']})"
        dot.node(nid, label, shape="box", style="filled,rounded", fillcolor=color,
                 color=GRAPH_STYLE["node_border"], fontname=GRAPH_STYLE["fontname"])

    # Edges
    for edge in cfg.get("edges", []):
        dot.edge(safe_node_id(edge["from"]), safe_node_id(edge["to"]),
                 color=GRAPH_STYLE["edge_color"], label=edge.get("type", ""),
                 fontname=GRAPH_STYLE["fontname"])

    # Render
    paths = {}
    for fmt in ["png", "svg", "pdf"]:
        dot.render(f"{output_path}.{fmt}", format=fmt, cleanup=True)
        paths[fmt] = f"{output_path}.{fmt}"
    return paths

def generate_dfg_graph(dfg, output_path="output/dfg"):
    ensure_output_dir(os.path.dirname(output_path))
    if not dfg or "assignments" not in dfg:
        return None

    dot = Digraph(comment="DFG")
    dot.attr(rankdir="TB", bgcolor="white")

    # Assignment nodes
    for var, assigns in dfg.get("assignments", {}).items():
        safe_var = safe_node_id(var)
        for ln in assigns:
            nid = f"assign_{safe_var}_{ln}"
            dot.node(nid, f"ASSIGN\n{var}\n(line {ln})", shape="oval",
                     style="filled,rounded", fillcolor=GRAPH_STYLE["loop_fill"],
                     color=GRAPH_STYLE["node_border"], fontname=GRAPH_STYLE["fontname"])

    # Use nodes
    for var, uses in dfg.get("uses", {}).items():
        safe_var = safe_node_id(var)
        for ln in uses:
            uid = f"use_{safe_var}_{ln}"
            dot.node(uid, f"USE\n{var}\n(line {ln})", shape="ellipse",
                     style="filled,rounded", fillcolor=GRAPH_STYLE["call_fill"],
                     color=GRAPH_STYLE["node_border"], fontname=GRAPH_STYLE["fontname"])
            # Connect assigns → uses
            assigns = dfg.get("assignments", {}).get(var, [])
            for assign_ln in assigns:
                dot.edge(f"assign_{safe_var}_{assign_ln}", uid,
                         color=GRAPH_STYLE["data_edge_color"])

    # Render
    paths = {}
    for fmt in ["png", "svg", "pdf"]:
        dot.render(f"{output_path}.{fmt}", format=fmt, cleanup=True)
        paths[fmt] = f"{output_path}.{fmt}"
    return paths

def generate_graphs(cfg, dfg, output_dir="output"):
    """Generates CFG + DFG graphs and returns saved file paths."""
    ensure_output_dir(output_dir)
    paths = {}
    cfg_paths = generate_cfg_graph(cfg, f"{output_dir}/cfg")
    if cfg_paths:
        paths["cfg"] = cfg_paths
    dfg_paths = generate_dfg_graph(dfg, f"{output_dir}/dfg")
    if dfg_paths:
        paths["dfg"] = dfg_paths
    return paths


# Inline SVG helpers
def _dot_cfg_from_cfg(cfg):
    """Return a graphviz.Digraph built from cfg JSON (not rendered)."""
    dot = Digraph(comment="CFG")
    dot.attr(rankdir="TB", bgcolor="white")

    for node in cfg.get("nodes", []):
        nid = safe_node_id(node.get("id"))
        color = GRAPH_STYLE["node_fill"]
        if node.get("kind") == "if":
            color = GRAPH_STYLE["if_fill"]
        elif node.get("kind") == "loop":
            color = GRAPH_STYLE["loop_fill"]
        elif node.get("kind") == "call":
            color = GRAPH_STYLE["call_fill"]

        label = f"{node.get('kind','').upper()}\n{node.get('name','')}\n(line {node.get('lineno', '')})"
        dot.node(nid, label, shape="box", style="filled,rounded", fillcolor=color,
                 color=GRAPH_STYLE["node_border"], fontname=GRAPH_STYLE["fontname"]) 

    for edge in cfg.get("edges", []):
        dot.edge(safe_node_id(edge.get("from")), safe_node_id(edge.get("to")),
                 color=GRAPH_STYLE["edge_color"], label=edge.get("type", ""),
                 fontname=GRAPH_STYLE["fontname"]) 

    return dot


def _dot_dfg_from_dfg(dfg):
    dot = Digraph(comment="DFG")
    dot.attr(rankdir="TB", bgcolor="white")

    for var, assigns in dfg.get("assignments", {}).items():
        safe_var = safe_node_id(var)
        for ln in assigns:
            nid = f"assign_{safe_var}_{ln}"
            dot.node(nid, f"ASSIGN\n{var}\n(line {ln})", shape="oval",
                     style="filled,rounded", fillcolor=GRAPH_STYLE["loop_fill"],
                     color=GRAPH_STYLE["node_border"], fontname=GRAPH_STYLE["fontname"]) 

    for var, uses in dfg.get("uses", {}).items():
        safe_var = safe_node_id(var)
        for ln in uses:
            uid = f"use_{safe_var}_{ln}"
            dot.node(uid, f"USE\n{var}\n(line {ln})", shape="ellipse",
                     style="filled,rounded", fillcolor=GRAPH_STYLE["call_fill"],
                     color=GRAPH_STYLE["node_border"], fontname=GRAPH_STYLE["fontname"]) 
            assigns = dfg.get("assignments", {}).get(var, [])
            for assign_ln in assigns:
                dot.edge(f"assign_{safe_var}_{assign_ln}", uid,
                         color=GRAPH_STYLE["data_edge_color"]) 

    return dot


def generate_cfg_svg(cfg):
    """Return an SVG string for the provided cfg JSON. Returns None on failure."""
    if not cfg or "nodes" not in cfg:
        return None
    try:
        dot = _dot_cfg_from_cfg(cfg)
        raw = dot.pipe(format="svg")
        return raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
    except Exception:
        return None


def generate_dfg_svg(dfg):
    """Return an SVG string for the provided dfg JSON. Returns None on failure."""
    if not dfg or "assignments" not in dfg:
        return None
    try:
        dot = _dot_dfg_from_dfg(dfg)
        raw = dot.pipe(format="svg")
        return raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
    except Exception:
        return None
