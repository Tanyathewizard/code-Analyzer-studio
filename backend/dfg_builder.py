import ast
from typing import Dict, List, Tuple, Set


def build_dfg(source: str) -> Dict:
    try:
        tree = ast.parse(source)
    except Exception:
        return {"nodes": [], "edges": []}

    nodes: Set[str] = set()
    edges: List[Tuple[str, str]] = []

    class DFGVisitor(ast.NodeVisitor):

        # ✅ Handle assignments (a = b)
        def visit_Assign(self, node: ast.Assign):
            targets = []

            # Collect target variables
            for t in node.targets:
                if isinstance(t, ast.Name):
                    targets.append(t.id)
                    nodes.add(t.id)

            # Handle RHS value
            if isinstance(node.value, ast.Name):
                source = node.value.id
                nodes.add(source)

                for target in targets:
                    edges.append((source, target))

            # Handle function calls in RHS
            elif isinstance(node.value, ast.Call):
                func_name = self.get_func_name(node.value)
                nodes.add(func_name)

                for target in targets:
                    edges.append((func_name, target))

                for arg in node.value.args:
                    if isinstance(arg, ast.Name):
                        nodes.add(arg.id)
                        edges.append((arg.id, func_name))

            self.generic_visit(node)

        # ✅ Handle augmented assignments (a += b)
        def visit_AugAssign(self, node: ast.AugAssign):
            if isinstance(node.target, ast.Name):
                target = node.target.id
                nodes.add(target)

                if isinstance(node.value, ast.Name):
                    source = node.value.id
                    nodes.add(source)
                    edges.append((source, target))

            self.generic_visit(node)

        # ✅ Handle function calls (print(x), range(n), etc.)
        def visit_Call(self, node: ast.Call):
            func_name = self.get_func_name(node)
            nodes.add(func_name)

            for arg in node.args:
                if isinstance(arg, ast.Name):
                    nodes.add(arg.id)
                    edges.append((arg.id, func_name))

            self.generic_visit(node)

        # ✅ Handle for-loops (for i in range(n))
        def visit_For(self, node: ast.For):
            if isinstance(node.target, ast.Name):
                loop_var = node.target.id
                nodes.add(loop_var)

                if isinstance(node.iter, ast.Call):
                    func_name = self.get_func_name(node.iter)
                    nodes.add(func_name)

                    edges.append((func_name, loop_var))

                    for arg in node.iter.args:
                        if isinstance(arg, ast.Name):
                            nodes.add(arg.id)
                            edges.append((arg.id, func_name))

            self.generic_visit(node)

        # ✅ Utility to extract function name
        def get_func_name(self, node: ast.Call) -> str:
            if isinstance(node.func, ast.Name):
                return node.func.id
            elif isinstance(node.func, ast.Attribute):
                return node.func.attr
            return "unknown_func"

    # Run visitor
    try:
        DFGVisitor().visit(tree)
    except Exception:
        return {"nodes": [], "edges": []}

    return {
        "nodes": sorted(list(nodes)),
        "edges": edges
    }
