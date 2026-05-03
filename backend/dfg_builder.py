import ast
from typing import Dict, List

def build_dfg(source: str) -> Dict:
    try:
        tree = ast.parse(source)
    except Exception:
        return {"assignments": {}, "uses": {}}

    assigns: Dict[str, List[int]] = {}
    uses: Dict[str, List[int]] = {}

    def record_assign(name: str, lineno: int):
        # Replace ":" with "_" to avoid Graphviz errors
        name = str(name).replace(":", "_")
        if lineno not in assigns.get(name, []):
            assigns.setdefault(name, []).append(lineno)

    def record_use(name: str, lineno: int):
        name = str(name).replace(":", "_")
        if lineno not in uses.get(name, []):
            uses.setdefault(name, []).append(lineno)

    class Visitor(ast.NodeVisitor):
        def visit_Assign(self, node: ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    record_assign(t.id, node.lineno)
                elif isinstance(t, (ast.Tuple, ast.List)):
                    for elt in t.elts:
                        if isinstance(elt, ast.Name):
                            record_assign(elt.id, node.lineno)
            self.visit(node.value)
            self.generic_visit(node)

        def visit_AugAssign(self, node: ast.AugAssign):
            if isinstance(node.target, ast.Name):
                record_use(node.target.id, node.lineno)
                record_assign(node.target.id, node.lineno)
            self.visit(node.value)
            self.generic_visit(node)

        def visit_Name(self, node: ast.Name):
            if isinstance(node.ctx, ast.Load):
                record_use(node.id, node.lineno)
            elif isinstance(node.ctx, ast.Store):
                record_assign(node.id, node.lineno)

    try:
        Visitor().visit(tree)
    except Exception:
        return {"assignments": {}, "uses": {}}

    # Sort assignments and uses by variable name
    sorted_assigns = dict(sorted(assigns.items()))
    sorted_uses = dict(sorted(uses.items()))

    return {"assignments": sorted_assigns, "uses": sorted_uses}
