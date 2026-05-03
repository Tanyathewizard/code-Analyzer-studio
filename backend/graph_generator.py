import os
import re
from graphviz import Digraph

# ================== STYLE ==================
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


# ================== UTIL ==================
def safe_node_id(raw: str) -> str:
    if raw is None:
        return "node_unknown"
    return re.sub(r'[^0-9A-Za-z_\-]', '_', str(raw))


def ensure_output_dir(path="output"):
    os.makedirs(path, exist_ok=True)
    return path


# ================== CFG GRAPH ==================
def generate_cfg_graph(cfg, output_path="output/cfg"):
    ensure_output_dir(os.path.dirname(output_path))

    if not cfg or "nodes" not in cfg:
        return None

    dot = Digraph(comment="CFG")
    dot.attr(rankdir="TB", bgcolor="white")

    # Nodes
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

        dot.node(
            nid,
            label,
            shape="box",
            style="filled,rounded",
            fillcolor=color,
            color=GRAPH_STYLE["node_border"],
            fontname=GRAPH_STYLE["fontname"]
        )

    # Edges
    for edge in cfg.get("edges", []):
        dot.edge(
            safe_node_id(edge.get("from")),
            safe_node_id(edge.get("to")),
            label=edge.get("type", ""),
            color=GRAPH_STYLE["edge_color"],
            fontname=GRAPH_STYLE["fontname"]
        )

    # Render
    paths = {}
    for fmt in ["png", "svg", "pdf"]:
        dot.render(f"{output_path}.{fmt}", format=fmt, cleanup=True)
        paths[fmt] = f"{output_path}.{fmt}"

    return paths


# ================== DFG GRAPH (NEW CLEAN VERSION) ==================
def generate_dfg_graph(dfg, output_path="output/dfg"):
    ensure_output_dir(os.path.dirname(output_path))

    if not dfg or "nodes" not in dfg:
        return None

    dot = Digraph(comment="DFG")
    dot.attr(rankdir="TB", bgcolor="white")

    # Nodes
    for node in dfg.get("nodes", []):
        dot.node(
            safe_node_id(node),
            node,
            shape="ellipse",
            style="filled,rounded",
            fillcolor="#e8f0ff",
            color=GRAPH_STYLE["node_border"],
            fontname=GRAPH_STYLE["fontname"]
        )

    # Edges
    for src, dst in dfg.get("edges", []):
        dot.edge(
            safe_node_id(src),
            safe_node_id(dst),
            color=GRAPH_STYLE["data_edge_color"]
        )

    # Render
    paths = {}
    for fmt in ["png", "svg", "pdf"]:
        dot.render(f"{output_path}.{fmt}", format=fmt, cleanup=True)
        paths[fmt] = f"{output_path}.{fmt}"

    return paths


# ================== COMBINED GRAPH ==================
def generate_graphs(cfg, dfg, output_dir="output"):
    ensure_output_dir(output_dir)

    paths = {}

    cfg_paths = generate_cfg_graph(cfg, f"{output_dir}/cfg")
    if cfg_paths:
        paths["cfg"] = cfg_paths

    dfg_paths = generate_dfg_graph(dfg, f"{output_dir}/dfg")
    if dfg_paths:
        paths["dfg"] = dfg_paths

    return paths


# ================== SVG HELPERS ==================
def generate_cfg_svg(cfg):
    if not cfg or "nodes" not in cfg:
        return None

    try:
        dot = Digraph(comment="CFG")
        dot.attr(rankdir="TB", bgcolor="white")

        for node in cfg.get("nodes", []):
            nid = safe_node_id(node.get("id"))

            label = f"{node.get('kind','').upper()}\n{node.get('name','')}\n(line {node.get('lineno', '')})"

            dot.node(nid, label)

        for edge in cfg.get("edges", []):
            dot.edge(
                safe_node_id(edge.get("from")),
                safe_node_id(edge.get("to"))
            )

        return dot.pipe(format="svg").decode("utf-8")

    except Exception:
        return None


def generate_dfg_svg(dfg):
    if not dfg or "nodes" not in dfg:
        return None

    try:
        dot = Digraph(comment="DFG")
        dot.attr(rankdir="TB", bgcolor="white")

        for node in dfg.get("nodes", []):
            dot.node(safe_node_id(node), node)

        for src, dst in dfg.get("edges", []):
            dot.edge(safe_node_id(src), safe_node_id(dst))

        return dot.pipe(format="svg").decode("utf-8")

    except Exception:
        return None
