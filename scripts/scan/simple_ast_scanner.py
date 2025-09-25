#!/usr/bin/env python3
"""
Simple AST Scanner - Class and Method Oversight for Debugging
Focused tool for root cause analysis and bug fixes.
"""
import ast
import sys
from pathlib import Path
from typing import Dict, List


class SimpleCodeScanner:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.classes = {}
        self.functions = {}

    def scan_project(self):
        """Scan project for Python files, focusing on classes and methods."""
        python_files = list(self.project_root.rglob("*.py"))

        for file_path in python_files:
            # Skip common directories and focus on source code
            skip_dirs = ['.git', '__pycache__', '.pytest_cache', 'venv', '.venv', 'env',
                        'node_modules', 'site-packages', 'production', 'staging',
                        'development', '.mypy_cache', '.ruff_cache', 'dist', 'build']

            if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                continue

            # Only scan files in src/ and tests/ directories
            relative_path = file_path.relative_to(self.project_root)
            if (not relative_path.parts[0].startswith('.') and
                relative_path.parts[0] in ['src', 'tests']):
                self._scan_file(file_path)

    def _scan_file(self, file_path: Path):
        """Extract classes and functions from a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    self._process_class(node, file_path)
                elif isinstance(node, ast.FunctionDef):
                    self._process_function(node, file_path)

        except Exception as e:
            print(f"⚠️  Error scanning {file_path}: {e}")

    def _process_class(self, node: ast.ClassDef, file_path: Path):
        """Extract class information."""
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(f"{item.name}({', '.join(arg.arg for arg in item.args.args)})")

        base_classes = [self._get_name(base) for base in node.bases]

        self.classes[node.name] = {
            'file': str(file_path.relative_to(self.project_root)),
            'line': node.lineno,
            'methods': methods,
            'inherits_from': base_classes
        }

    def _process_function(self, node: ast.FunctionDef, file_path: Path):
        """Extract function information."""
        args = [arg.arg for arg in node.args.args]

        self.functions[node.name] = {
            'file': str(file_path.relative_to(self.project_root)),
            'line': node.lineno,
            'args': args
        }

    def _get_name(self, node):
        """Extract name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)

    def find_class(self, class_name: str) -> List[Dict]:
        """Find classes by name (supports partial matching)."""
        results = []
        search_term = class_name.lower()

        for name, info in self.classes.items():
            if search_term in name.lower():
                results.append({
                    'name': name,
                    'file': info['file'],
                    'line': info['line'],
                    'methods': info['methods'],
                    'inherits_from': info['inherits_from']
                })
        return results

    def find_method(self, method_name: str) -> List[Dict]:
        """Find classes that have a specific method (supports partial matching)."""
        results = []
        search_term = method_name.lower()

        for class_name, class_info in self.classes.items():
            for method in class_info['methods']:
                # Extract method name from "method_name(args)" format
                method_only = method.split('(')[0].lower()

                # Support partial matching
                if search_term in method_only:
                    results.append({
                        'class': class_name,
                        'method': method,
                        'file': class_info['file'],
                        'line': class_info['line']
                    })
        return results

    def show_overview(self):
        """Display overview for debugging."""
        print("🔍 Code Overview")
        print("=" * 50)

        print(f"📊 Summary:")
        print(f"  Classes: {len(self.classes)}")
        print(f"  Functions: {len(self.functions)}")
        print()

        if self.classes:
            print("📦 Classes:")
            for name, info in sorted(self.classes.items()):
                print(f"  {name} ({info['file']}:{info['line']})")
                if info['inherits_from']:
                    print(f"    ↳ inherits from: {', '.join(info['inherits_from'])}")
                print(f"    Methods ({len(info['methods'])}):")
                for method in info['methods']:  # Show ALL methods
                    print(f"      • {method}")
                print()

    def search_code(self, search_term: str):
        """Search for classes or methods containing term."""
        print(f"🔎 Search results for '{search_term}':")
        print("-" * 40)

        # Search classes
        for name, info in self.classes.items():
            if search_term.lower() in name.lower():
                print(f"📦 Class: {name} ({info['file']}:{info['line']})")

        # Search methods
        for class_name, class_info in self.classes.items():
            for method in class_info['methods']:
                if search_term.lower() in method.lower():
                    print(f"🔧 Method: {class_name}.{method} ({class_info['file']}:{class_info['line']})")

        # Search functions
        for name, info in self.functions.items():
            if search_term.lower() in name.lower():
                print(f"⚙️  Function: {name} ({info['file']}:{info['line']})")


def main():
    """Command line interface."""
    if len(sys.argv) < 2:
        print("Simple AST Scanner - Class and Method Overview")
        print("Usage:")
        print("  python simple_ast_scanner.py overview      # Show all classes and methods")
        print("  python simple_ast_scanner.py search <term> # Search for term in code")
        print("  python simple_ast_scanner.py class <name>  # Find specific class")
        print("  python simple_ast_scanner.py method <name> # Find method across classes")
        return

    scanner = SimpleCodeScanner()
    scanner.scan_project()

    command = sys.argv[1]

    if command == "overview":
        scanner.show_overview()

    elif command == "search" and len(sys.argv) > 2:
        scanner.search_code(sys.argv[2])

    elif command == "class" and len(sys.argv) > 2:
        class_results = scanner.find_class(sys.argv[2])
        if class_results:
            print(f"📦 Classes matching '{sys.argv[2]}':")
            for class_info in class_results:
                print(f"\n  {class_info['name']} ({class_info['file']}:{class_info['line']})")
                if class_info['inherits_from']:
                    print(f"    ↳ inherits from: {', '.join(class_info['inherits_from'])}")
                print(f"    Methods ({len(class_info['methods'])}):")
                for method in class_info['methods'][:5]:  # Show first 5 methods
                    print(f"      • {method}")
                if len(class_info['methods']) > 5:
                    print(f"      • ... and {len(class_info['methods']) - 5} more")
        else:
            print(f"❌ No classes found matching '{sys.argv[2]}'")

    elif command == "method" and len(sys.argv) > 2:
        results = scanner.find_method(sys.argv[2])
        if results:
            print(f"🔧 Method '{sys.argv[2]}' found in:")
            for result in results:
                print(f"  {result['class']}.{result['method']} ({result['file']}:{result['line']})")
        else:
            print(f"❌ Method '{sys.argv[2]}' not found")

    else:
        print("❌ Invalid command or missing argument")


if __name__ == "__main__":
    main()