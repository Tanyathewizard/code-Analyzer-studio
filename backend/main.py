import os
import json
from dataclasses import asdict, is_dataclass
from unified_agent import UnifiedAnalyzer
from graph_viewer import view_graphs  # updated import
from quality_agent import CodeQualityEvaluator

# --------------------------
# Utilities
# --------------------------
def serialize(obj):
    if is_dataclass(obj):
        return asdict(obj)
    elif isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize(i) for i in obj]
    else:
        return obj

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def save_output(path, content):
    """Save content to file and always print path"""
    try:
        j = json.loads(content)
        content = json.dumps(j, indent=4)
    except:
        pass
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ File saved → {path}")

# --------------------------
# Language mapping
# --------------------------
LANG = {
    "py": "Python",
    "js": "JavaScript",
    "jsx": "JavaScript",
    "java": "Java",
    "cpp": "C++",
    "c": "C",
    "cs": "C#",
    "ts": "TypeScript",
}

# --------------------------
# Project scanner
# --------------------------
def scan_project(path):
    folder = os.path.dirname(path)
    result = []
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.endswith((".py", ".js", ".java", ".ts", ".cpp", ".c", ".cs")):
                full = os.path.join(root, f)
                if full != path:
                    result.append((full, read_file(full)))
    return result

# --------------------------
# Main workflow
# --------------------------
def main():
    fp = input("Enter path of the source file: ").strip()
    if not os.path.isfile(fp):
        print("❌ Invalid file path.")
        return

    code = read_file(fp)
    ext = fp.split(".")[-1].lower()
    lang = LANG.get(ext, ext.title())

    analyzer = UnifiedAnalyzer()

    # IR Analysis
    print("\n🔹 Running IR Analysis ...")
    ir = analyzer.run("IR", lang, code)
    ir_serialized = serialize(ir)
    save_output("analysis_result.json", json.dumps(ir_serialized))

    # Semantic Analysis
    print("\n🔹 Running Semantic Analysis ...")
    sem = analyzer.run("SEMANTIC", lang, code)
    sem_serialized = serialize(sem)
    save_output("semantic_result.json", json.dumps(sem_serialized))

    # Quality Analysis (silent)
    print("\n🔹 Running Quality Analysis ...")
    quality = CodeQualityEvaluator()
    quality_result = quality.evaluate(
        code,
        language=lang,
        analyzer_results=ir_serialized,
        semantic_results=sem_serialized
    )
    save_output("quality_result.json", json.dumps(serialize(quality_result)))

    # Graph generation
    if "cfg" in ir_serialized or "dfg" in ir_serialized:
        choice = input("\nDo you want to generate CFG/DFG graphs? (y/n): ").strip().lower()
        if choice == "y":
            try:
                paths = view_graphs("analysis_result.json", output_dir="output")
                if paths:
                    print("\n✅ Graphs generated successfully:")
                    for key, formats in paths.items():
                        print(f"\n--- {key.upper()} ---")
                        for fmt, path in formats.items():
                            print(f"{fmt.upper()}: {path}")
                else:
                    print("⚠ No graphs were generated.")
            except Exception as e:
                print("⚠ Failed to generate graphs. Ensure Graphviz is installed.")
                print("Error:", e)

if __name__ == "__main__":
    main()
