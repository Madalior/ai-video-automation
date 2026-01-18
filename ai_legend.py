#!/usr/bin/env python3
"""
AI Legend - Intelligent Prompt Generator for Antigravity

Transforms high-level goals into optimized, context-rich prompts
that maximize Antigravity's effectiveness.

Usage:
    python ai_legend.py "fix the parallel director bug"
    python ai_legend.py "add batch processing to info pipeline"
"""

import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.genkit_client import genkit
from modules.codebase_scanner import CodebaseScanner

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠ Installing 'rich' for better output: pip install rich")

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False
    print("⚠ Installing 'pyperclip' for clipboard support: pip install pyperclip")

logging.basicConfig(level=logging.WARNING)  # Suppress info logs for cleaner output
logger = logging.getLogger(__name__)


class AILegend:
    """AI Legend - Prompt optimizer for Antigravity"""
    
    def __init__(self, project_root: str = "."):
        """Initialize AI Legend"""
        self.project_root = Path(project_root).resolve()
        self.scanner = CodebaseScanner(str(self.project_root))
        self.console = Console() if RICH_AVAILABLE else None
        
        # Create prompts directory
        self.prompts_dir = self.project_root / "prompts" / "history"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
    def print_header(self):
        """Print header"""
        if self.console:
            self.console.print()
            self.console.print("╔" + "═" * 58 + "╗", style="bold cyan")
            self.console.print("║" + "  AI LEGEND - Antigravity Prompt Generator".center(58) + "║", style="bold cyan")
            self.console.print("╚" + "═" * 58 + "╝", style="bold cyan")
            self.console.print()
        else:
            print("\n" + "=" * 60)
            print("  AI LEGEND - Antigravity Prompt Generator".center(60))
            print("=" * 60 + "\n")
    
    def print_status(self, message: str, status: str = "info"):
        """Print status message"""
        icons = {"info": "ℹ", "success": "✓", "warning": "⚠", "error": "✗", "working": "⚙"}
        colors = {"info": "blue", "success": "green", "warning": "yellow", "error": "red", "working": "cyan"}
        
        if self.console:
            self.console.print(f"{icons.get(status, 'ℹ')} {message}", style=colors.get(status, "white"))
        else:
            print(f"{icons.get(status, 'ℹ')} {message}")
    
    def gather_context(self, goal: str) -> dict:
        """Gather codebase context"""
        self.print_status("Gathering codebase context...", "working")
        
        context = self.scanner.gather_context(goal)
        
        # Display what we found
        if self.console:
            table = Table(title="Context Analysis", box=box.ROUNDED)
            table.add_column("Category", style="cyan")
            table.add_column("Details", style="white")
            
            table.add_row("Project Type", context.get("project_type", "unknown"))
            table.add_row("Relevant Files", str(len(context.get("files", []))))
            table.add_row("Recent Errors", str(len(context.get("recent_errors", []))))
            
            self.console.print(table)
        else:
            print(f"  Project Type: {context.get('project_type', 'unknown')}")
            print(f"  Relevant Files: {len(context.get('files', []))}")
            print(f"  Recent Errors: {len(context.get('recent_errors', []))}")
        
        return context
    
    def optimize_prompt(self, goal: str, context: dict) -> dict:
        """Call Genkit service to optimize prompt"""
        self.print_status("Optimizing prompt with AI...", "working")
        
        result = genkit.optimize_antigravity_prompt(
            goal=goal,
            codebase_context=context
        )
        
        if not result:
            self.print_status("Failed to optimize prompt - Genkit service unavailable", "error")
            return None
            
        return result
    
    def display_result(self, result: dict, goal: str):
        """Display the optimized prompt"""
        if not result:
            return
        
        optimized_prompt = result.get('optimized_prompt', '')
        context_summary = result.get('context_summary', '')
        relevant_files = result.get('relevant_files', [])
        complexity = result.get('estimated_complexity', 'unknown')
        
        print()
        
        if self.console:
            # Context Summary
            self.console.print(Panel(
                context_summary,
                title="[bold cyan]🎯 Context Understanding[/bold cyan]",
                border_style="cyan",
                box=box.ROUNDED
            ))
            
            # Complexity
            complexity_colors = {"simple": "green", "medium": "yellow", "complex": "red"}
            self.console.print(f"\n📊 Estimated Complexity: [{complexity_colors.get(complexity, 'white')}]{complexity.upper()}[/]")
            
            # Relevant Files
            if relevant_files:
                self.console.print("\n📁 Relevant Files:", style="bold")
                for file in relevant_files:
                    self.console.print(f"  • {file}", style="dim")
            
            # Optimized Prompt
            self.console.print()
            self.console.print(Panel(
                optimized_prompt,
                title="[bold green]✨ OPTIMIZED PROMPT FOR ANTIGRAVITY[/bold green]",
                border_style="green",
                box=box.DOUBLE,
                padding=(1, 2)
            ))
        else:
            print("━" * 60)
            print("🎯 CONTEXT UNDERSTANDING")
            print("━" * 60)
            print(context_summary)
            print()
            print(f"📊 Estimated Complexity: {complexity.upper()}")
            
            if relevant_files:
                print("\n📁 Relevant Files:")
                for file in relevant_files:
                    print(f"  • {file}")
            
            print("\n" + "━" * 60)
            print("✨ OPTIMIZED PROMPT FOR ANTIGRAVITY")
            print("━" * 60)
            print(optimized_prompt)
            print("━" * 60)
    
    def save_to_history(self, goal: str, result: dict):
        """Save prompt to history"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        # Create safe filename from goal
        safe_goal = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in goal[:50])
        filename = f"{timestamp}_{safe_goal}.md"
        filepath = self.prompts_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# AI Legend Prompt - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"## Original Goal\n{goal}\n\n")
                f.write(f"## Context Summary\n{result.get('context_summary', '')}\n\n")
                f.write(f"## Complexity\n{result.get('estimated_complexity', 'unknown')}\n\n")
                
                if result.get('relevant_files'):
                    f.write("## Relevant Files\n")
                    for file in result['relevant_files']:
                        f.write(f"- {file}\n")
                    f.write("\n")
                
                f.write(f"## Optimized Prompt\n\n{result.get('optimized_prompt', '')}\n")
            
            self.print_status(f"Saved to: {filepath.relative_to(self.project_root)}", "success")
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def copy_to_clipboard(self, text: str):
        """Copy text to clipboard"""
        if CLIPBOARD_AVAILABLE:
            try:
                pyperclip.copy(text)
                self.print_status("Copied to clipboard! Paste to Antigravity.", "success")
            except Exception as e:
                logger.error(f"Failed to copy to clipboard: {e}")
        else:
            self.print_status("Clipboard not available. Install pyperclip: pip install pyperclip", "warning")
    
    def run(self, goal: str):
        """Main execution flow"""
        self.print_header()
        self.print_status(f"Your Goal: {goal}", "info")
        print()
        
        # Step 1: Gather context
        context = self.gather_context(goal)
        
        # Step 2: Optimize prompt
        result = self.optimize_prompt(goal, context)
        
        if not result:
            return
        
        # Step 3: Display result
        self.display_result(result, goal)
        
        # Step 4: Copy to clipboard
        self.copy_to_clipboard(result.get('optimized_prompt', ''))
        
        # Step 5: Save to history
        self.save_to_history(goal, result)
        
        print()
        if self.console:
            self.console.print("✨ Done! Paste the prompt to Antigravity for best results.", style="bold green")
        else:
            print("✨ Done! Paste the prompt to Antigravity for best results.")
        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AI Legend - Transform goals into optimized Antigravity prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ai_legend.py "fix the parallel director bug"
  python ai_legend.py "add batch processing to info pipeline"
  python ai_legend.py "optimize video generation performance"
        """
    )
    
    parser.add_argument(
        "goal",
        type=str,
        help="Your high-level goal or objective"
    )
    
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Project root directory (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Run AI Legend
    legend = AILegend(project_root=args.project_root)
    legend.run(args.goal)


if __name__ == "__main__":
    main()
