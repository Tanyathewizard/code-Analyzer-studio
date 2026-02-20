# graph_viewer.py
from graph_generator import generate_graphs
import json
import os

def load_analysis(json_path):
    """Load analysis result JSON."""
    if not os.path.isfile(json_path):
        return {}
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def view_graphs(json_path, output_dir="output"):
    """Generates CFG + DFG graphs from analysis JSON and returns saved paths."""
    data = load_analysis(json_path)
    cfg = data.get("cfg")
    dfg = data.get("dfg")

    if not cfg and not dfg:
        print("⚠ No CFG/DFG data found in analysis.")
        return {}

    paths = generate_graphs(cfg, dfg, output_dir=output_dir)

    # Print saved files
    for key, formats in paths.items():
        print(f"✅ {key.upper()} graph saved:")
        for fmt, path in formats.items():
            print(f"   - {fmt.upper()}: {path}")

    return paths
