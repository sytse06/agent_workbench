#!/usr/bin/env python3
"""
UI Building Analyzer - Smart AST-based analysis of UI building relationships
Extends the existing SimpleCodeScanner to provide transparency into UI building complexity.
"""
import sys
from pathlib import Path

# Add the scan directory to the path
scan_dir = Path(__file__).parent / "scan"
sys.path.append(str(scan_dir))

from simple_ast_scanner import SimpleCodeScanner


class UIBuildingAnalyzer(SimpleCodeScanner):
    """Smart AST-based analysis of UI building relationships"""

    def analyze_ui_building_flow(self):
        """Analyze the complete UI building flow using AST"""
        print("🔧 UI Building Flow Analysis")
        print("=" * 50)

        # 1. Find the entry point (main.py)
        entry_functions = self._find_ui_entry_points()

        # 2. Map mode factory relationships
        mode_mappings = self._analyze_mode_factory()

        # 3. Trace UI creation functions
        ui_creators = self._find_ui_creators()

        # 4. Show the complete flow
        self._display_ui_flow(entry_functions, mode_mappings, ui_creators)

        return self.get_ui_building_test_insights()

    def _find_ui_entry_points(self):
        """Find main.py UI mounting functions"""
        results = []
        for name, info in self.functions.items():
            if 'main.py' in info['file'] and any(keyword in name.lower()
                for keyword in ['mount', 'create', 'interface', 'gradio', 'app']):
                results.append((name, info))
        return results

    def _analyze_mode_factory(self):
        """Analyze ModeFactory class and its relationships"""
        mode_factory = self.classes.get('ModeFactory', {})
        if not mode_factory:
            return {}

        print(f"📦 ModeFactory ({mode_factory.get('file', 'unknown')}:{mode_factory.get('line', 0)})")
        for method in mode_factory.get('methods', []):
            print(f"  • {method}")

        return {
            'class': 'ModeFactory',
            'file': mode_factory.get('file'),
            'methods': mode_factory.get('methods', [])
        }

    def _find_ui_creators(self):
        """Find all create_*_app functions"""
        creators = []
        for name, info in self.functions.items():
            if name.startswith('create_') and ('app' in name or 'interface' in name):
                creators.append({
                    'name': name,
                    'file': info['file'],
                    'line': info['line'],
                    'args': info['args']
                })
        return creators

    def _display_ui_flow(self, entry_points, mode_mappings, ui_creators):
        """Display the complete UI building flow"""
        print("\n🗺️  UI Building Flow Map:")
        print("-" * 30)

        print("1️⃣ Entry Points (main.py):")
        for name, info in entry_points:
            print(f"   {name}() → {info['file']}:{info['line']}")

        if mode_mappings:
            print(f"\n2️⃣ Mode Factory ({mode_mappings['file']}):")
            for method in mode_mappings['methods']:
                if 'create_interface' in method:
                    print(f"   🔀 {method}")
                if '_determine_mode' in method:
                    print(f"   🎯 {method}")

        print("\n3️⃣ UI Creators:")
        for creator in ui_creators:
            mode = "workbench" if "workbench" in creator['name'] else "seo_coach" if "seo" in creator['name'] else "unknown"
            print(f"   📱 {creator['name']}() → {creator['file']}:{creator['line']} [{mode}]")

        # Show relationships
        print("\n🔗 Relationships:")
        print("   main.py → ModeFactory.create_interface() → mode-specific create_*_app()")

        complexity = len(entry_points) + len(ui_creators)
        if complexity > 5:
            print(f"\n⚠️  High complexity detected: {complexity} components")
        else:
            print(f"\n✅ Manageable complexity: {complexity} components")

    def get_ui_building_test_insights(self):
        """Generate test insights for the integration test"""
        insights = {
            'entry_points': self._find_ui_entry_points(),
            'mode_factory_methods': [],
            'ui_creators': self._find_ui_creators(),
            'complexity_score': 0
        }

        # Calculate complexity
        mode_factory = self.classes.get('ModeFactory', {})
        if mode_factory:
            insights['mode_factory_methods'] = mode_factory.get('methods', [])
            insights['complexity_score'] = len(insights['entry_points']) + len(insights['ui_creators'])

        return insights

    def show_unclear_references(self):
        """Show potentially unclear references that cause complexity"""
        print("\n🚨 Unclear Reference Analysis:")
        print("-" * 30)

        # Find functions that might be unclear
        unclear_patterns = ['mount', 'complex', 'safe', 'determine']

        for pattern in unclear_patterns:
            matches = []
            for name, info in self.functions.items():
                if pattern in name.lower() and ('main.py' in info['file'] or 'mode_factory' in info['file']):
                    matches.append(f"{name}() in {info['file']}:{info['line']}")

            if matches:
                print(f"🔍 '{pattern}' pattern:")
                for match in matches:
                    print(f"   {match}")

        # Show mode factory complexity
        mode_factory = self.classes.get('ModeFactory', {})
        if mode_factory and len(mode_factory.get('methods', [])) > 3:
            print(f"\n⚠️  ModeFactory has {len(mode_factory['methods'])} methods - potential complexity")


def main():
    """Command line interface for UI building analysis"""
    if len(sys.argv) > 1 and sys.argv[1] == "unclear":
        analyzer = UIBuildingAnalyzer()
        analyzer.scan_project()
        analyzer.show_unclear_references()
        return

    analyzer = UIBuildingAnalyzer()
    analyzer.scan_project()
    insights = analyzer.analyze_ui_building_flow()

    print(f"\n📊 Summary for Integration Testing:")
    print(f"   Entry Points: {len(insights['entry_points'])}")
    print(f"   UI Creators: {len(insights['ui_creators'])}")
    print(f"   Complexity Score: {insights['complexity_score']}")

    return insights


if __name__ == "__main__":
    main()