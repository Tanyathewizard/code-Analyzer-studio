import ast
from typing import Dict, List, Tuple, Set


def build_dfg(source: str) -> Dict:
    try:
        tree = ast.parse(source)
    except Exception:
        return {"nodes": [], "edges": []}

    nodes: Set[str] = set()
    edges: Set[Tuple[str, str]] = set()   # ✅ use set to avoid duplicates

    class DFGVisitor(ast.NodeVisitor):

        # ================== ASSIGN ==================
        def visit_Assign(self, node: ast.Assign):
            targets = []

            for t in node.targets:
                if isinstance(t, ast.Name):
                    targets.append(t.id)
                    nodes.add(t.id)

            # RHS is variable
            if isinstance(node.value, ast.Name):
                source = node.value.id
                nodes.add(source)

                for target in targets:
                    edges.add((source, target))

            # RHS is function call
            elif isinstance(node.value, ast.Call):
                func_name = self.get_func_name(node.value)
                nodes.add(func_name)

                for target in targets:
                    edges.add((func_name, target))

                for arg in node.value.args:
                    if isinstance(arg, ast.Name):
                        nodes.add(arg.id)
                        edges.add((arg.id, func_name))

            self.generic_visit(node)

        # ================== AUGMENTED ASSIGN ==================
        def visit_AugAssign(self, node: ast.AugAssign):
            if isinstance(node.target, ast.Name):
                target = node.target.id
                nodes.add(target)

                if isinstance(node.value, ast.Name):
                    source = node.value.id
                    nodes.add(source)
                    edges.add((source, target))

            self.generic_visit(node)

        # ================== FUNCTION CALL ==================
        def visit_Call(self, node: ast.Call):
            func_name = self.get_func_name(node)
            nodes.add(func_name)

            # ✅ Handle method calls: obj.method()
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    obj = node.func.value.id
                    nodes.add(obj)
                    edges.add((func_name, obj))   # append → even_list

            # Arguments → function
            for arg in node.args:
                if isinstance(arg, ast.Name):
                    nodes.add(arg.id)
                    edges.add((arg.id, func_name))  # i → append / print

            self.generic_visit(node)

        # ================== FOR LOOP ==================
        def visit_For(self, node: ast.For):
            if isinstance(node.target, ast.Name):
                loop_var = node.target.id
                nodes.add(loop_var)

                if isinstance(node.iter, ast.Call):
                    func_name = self.get_func_name(node.iter)
                    nodes.add(func_name)

                    edges.add((func_name, loop_var))  # range → i

                    for arg in node.iter.args:
                        if isinstance(arg, ast.Name):
                            nodes.add(arg.id)
                            edges.add((arg.id, func_name))  # limit → range

            self.generic_visit(node)

        # ================== FUNCTION NAME ==================
        def get_func_name(self, node: ast.Call) -> str:
            if isinstance(node.func, ast.Name):
                return node.func.id
            elif isinstance(node.func, ast.Attribute):
                return node.func.attr
            return "call"

    # Run visitor
    try:
        DFGVisitor().visit(tree)
    except Exception:
        return {"nodes": [], "edges": []}

    return {
        "nodes": sorted(list(nodes)),
        "edges": list(edges)
    }
