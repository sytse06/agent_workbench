#!/usr/bin/env python3
"""
Functional Architecture Scanner for Agent Workbench Chat App

Analyzes the complete codebase to map classes, methods, and dependencies
organized by layer: API, Core, Models, Services, UI.
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple


class ArchitectureAnalyzer(ast.NodeVisitor):
    """Analyzes Python files to extract architectural information."""

    def __init__(self, file_path: str, layer: str):
        self.file_path = file_path
        self.layer = layer
        self.classes = []
        self.functions = []
        self.imports = []
        self.current_class = None

    def visit_Import(self, node: ast.Import):
        """Capture import statements."""
        for alias in node.names:
            self.imports.append({"type": "import", "module": alias.name})
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Capture from ... import statements."""
        if node.module:
            for alias in node.names:
                self.imports.append(
                    {"type": "from", "module": node.module, "name": alias.name}
                )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Capture class definitions."""
        class_info = {
            "name": node.name,
            "bases": [self._get_base_name(base) for base in node.bases],
            "methods": [],
            "properties": [],
            "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
            "docstring": ast.get_docstring(node),
            "line": node.lineno,
        }

        # Visit methods
        prev_class = self.current_class
        self.current_class = class_info
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self.visit_FunctionDef(item, is_method=True)
        self.current_class = prev_class

        self.classes.append(class_info)

    def visit_FunctionDef(self, node: ast.FunctionDef, is_method=False):
        """Capture function/method definitions."""
        func_info = {
            "name": node.name,
            "args": [arg.arg for arg in node.args.args],
            "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
            "docstring": ast.get_docstring(node),
            "line": node.lineno,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
        }

        if is_method and self.current_class:
            # Determine method type
            if node.name.startswith("__") and node.name.endswith("__"):
                method_type = "magic"
            elif any(d == "property" for d in func_info["decorators"]):
                method_type = "property"
                self.current_class["properties"].append(func_info)
                return
            elif "staticmethod" in func_info["decorators"]:
                method_type = "static"
            elif "classmethod" in func_info["decorators"]:
                method_type = "class"
            elif node.name.startswith("_") and not node.name.startswith("__"):
                method_type = "private"
            else:
                method_type = "public"

            func_info["method_type"] = method_type
            self.current_class["methods"].append(func_info)
        else:
            self.functions.append(func_info)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Capture async function definitions."""
        self.visit_FunctionDef(node, is_method=False)

    def _get_base_name(self, node: ast.expr) -> str:
        """Extract base class name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_base_name(node.value)}.{node.attr}"
        return str(node)

    def _get_decorator_name(self, node: ast.expr) -> str:
        """Extract decorator name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
            elif isinstance(node.func, ast.Attribute):
                return node.func.attr
        elif isinstance(node, ast.Attribute):
            return node.attr
        return str(node)


def analyze_file(file_path: Path, layer: str) -> Dict:
    """Analyze a single Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        analyzer = ArchitectureAnalyzer(str(file_path), layer)
        analyzer.visit(tree)

        return {
            "file": str(file_path.relative_to(Path.cwd())),
            "layer": layer,
            "classes": analyzer.classes,
            "functions": analyzer.functions,
            "imports": analyzer.imports,
        }
    except Exception as e:
        return {
            "file": str(file_path),
            "layer": layer,
            "error": str(e),
        }


def get_layer(file_path: Path) -> str:
    """Determine the architectural layer of a file."""
    parts = file_path.parts
    if "api" in parts:
        if "routes" in parts:
            return "api_routes"
        return "api"
    elif "models" in parts:
        return "models"
    elif "services" in parts:
        return "services"
    elif "ui" in parts:
        if "components" in parts:
            return "ui_components"
        return "ui"
    elif "core" in parts:
        return "core"
    return "other"


def scan_architecture() -> Dict:
    """Scan entire codebase for architectural analysis."""
    src_path = Path("src/agent_workbench")

    layers = {
        "api": [],
        "api_routes": [],
        "core": [],
        "models": [],
        "services": [],
        "ui": [],
        "ui_components": [],
        "other": [],
    }

    # Scan all Python files
    for py_file in src_path.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue

        layer = get_layer(py_file)
        file_info = analyze_file(py_file, layer)
        layers[layer].append(file_info)

    return layers


def print_layer_summary(layer_name: str, files: List[Dict]):
    """Print summary of a layer."""
    print(f"\n{'=' * 80}")
    print(f"{layer_name.upper().replace('_', ' ')} LAYER")
    print(f"{'=' * 80}\n")

    total_classes = 0
    total_methods = 0
    total_functions = 0

    for file_info in files:
        if "error" in file_info:
            print(f"❌ {file_info['file']}: {file_info['error']}")
            continue

        if not file_info["classes"] and not file_info["functions"]:
            continue

        print(f"📄 {file_info['file']}")

        # Print classes
        for cls in file_info["classes"]:
            total_classes += 1
            total_methods += len(cls["methods"])

            bases_str = f" ({', '.join(cls['bases'])})" if cls["bases"] else ""
            print(f"   ├─ class {cls['name']}{bases_str} @ line {cls['line']}")

            if cls["docstring"]:
                doc_preview = cls["docstring"].split("\n")[0][:60]
                print(f"   │  ↳ {doc_preview}...")

            # Group methods by type
            methods_by_type = {}
            for method in cls["methods"]:
                method_type = method.get("method_type", "unknown")
                if method_type not in methods_by_type:
                    methods_by_type[method_type] = []
                methods_by_type[method_type].append(method)

            # Print public methods
            if "public" in methods_by_type:
                print(f"   │  📌 Public Methods:")
                for method in sorted(
                    methods_by_type["public"], key=lambda m: m["line"]
                ):
                    async_marker = "async " if method["is_async"] else ""
                    args_str = ", ".join(method["args"])
                    print(
                        f"   │     • {async_marker}{method['name']}({args_str}) @ {method['line']}"
                    )

            # Print private methods
            if "private" in methods_by_type:
                print(f"   │  🔒 Private Methods: {len(methods_by_type['private'])}")

            # Print special methods
            if "magic" in methods_by_type:
                magic_names = [m["name"] for m in methods_by_type["magic"]]
                print(f"   │  ✨ Magic: {', '.join(magic_names)}")

            # Print properties
            if cls["properties"]:
                prop_names = [p["name"] for p in cls["properties"]]
                print(f"   │  📊 Properties: {', '.join(prop_names)}")

        # Print module-level functions
        if file_info["functions"]:
            print(f"   ├─ Functions ({len(file_info['functions'])})")
            total_functions += len(file_info["functions"])
            for func in file_info["functions"][:5]:  # Show first 5
                async_marker = "async " if func["is_async"] else ""
                print(f"   │  • {async_marker}{func['name']}() @ {func['line']}")
            if len(file_info["functions"]) > 5:
                print(f"   │  ... and {len(file_info['functions']) - 5} more")

        print()

    print(f"📊 Summary: {total_classes} classes, {total_methods} methods, {total_functions} functions\n")


def analyze_dependencies(layers: Dict) -> Dict:
    """Analyze cross-layer dependencies."""
    dependencies = {
        "api_to_services": set(),
        "api_to_models": set(),
        "services_to_models": set(),
        "ui_to_api": set(),
        "ui_to_services": set(),
        "services_to_services": set(),
    }

    for layer_name, files in layers.items():
        for file_info in files:
            if "imports" not in file_info:
                continue

            for imp in file_info["imports"]:
                module = imp.get("module", "")

                # API → Services
                if layer_name.startswith("api") and "services" in module:
                    dependencies["api_to_services"].add(module)

                # API → Models
                if layer_name.startswith("api") and "models" in module:
                    dependencies["api_to_models"].add(module)

                # Services → Models
                if layer_name == "services" and "models" in module:
                    dependencies["services_to_models"].add(module)

                # UI → API
                if layer_name.startswith("ui") and "api" in module:
                    dependencies["ui_to_api"].add(module)

                # UI → Services
                if layer_name.startswith("ui") and "services" in module:
                    dependencies["ui_to_services"].add(module)

                # Services → Services
                if layer_name == "services" and "services" in module:
                    dependencies["services_to_services"].add(module)

    return {k: sorted(list(v)) for k, v in dependencies.items()}


def main():
    """Main execution."""
    print("\n" + "=" * 80)
    print("🔍 AGENT WORKBENCH - FUNCTIONAL ARCHITECTURE SCAN")
    print("=" * 80)

    # Scan architecture
    layers = scan_architecture()

    # Print each layer
    layer_order = [
        "models",
        "core",
        "services",
        "api",
        "api_routes",
        "ui",
        "ui_components",
    ]

    for layer_name in layer_order:
        if layers[layer_name]:
            print_layer_summary(layer_name, layers[layer_name])

    # Analyze dependencies
    print("\n" + "=" * 80)
    print("🔗 CROSS-LAYER DEPENDENCIES")
    print("=" * 80 + "\n")

    deps = analyze_dependencies(layers)
    for dep_type, modules in deps.items():
        if modules:
            print(f"{dep_type.replace('_', ' → ').upper()}:")
            for module in modules[:10]:  # Show first 10
                print(f"  • {module}")
            if len(modules) > 10:
                print(f"  ... and {len(modules) - 10} more")
            print()

    # Save to JSON
    output = {
        "layers": layers,
        "dependencies": deps,
    }

    output_path = Path("docs/architecture_scan.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Full scan saved to: {output_path}")


if __name__ == "__main__":
    main()
