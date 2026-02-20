# symbol_table.py
import ast
from typing import Dict
from ir_model import FunctionInfo, ClassInfo, VariableInfo

def build_symbol_table(source: str):
    tree = ast.parse(source)
    functions: Dict[str, FunctionInfo] = {}
    classes: Dict[str, ClassInfo] = {}
    globals_vars = {}

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            fi = FunctionInfo(
                name=node.name,
                lineno=node.lineno,
                args=[arg.arg for arg in node.args.args]
            )
            functions[node.name] = fi
        elif isinstance(node, ast.ClassDef):
            ci = ClassInfo(name=node.name, lineno=node.lineno)
            for n in node.body:
                if isinstance(n, ast.FunctionDef):
                    mi = FunctionInfo(name=n.name, lineno=n.lineno, args=[a.arg for a in n.args.args])
                    ci.methods[n.name] = mi
            classes[node.name] = ci
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    globals_vars[t.id] = globals_vars.get(t.id, []) + [node.lineno]

    return {"functions": functions, "classes": classes, "globals": globals_vars}
