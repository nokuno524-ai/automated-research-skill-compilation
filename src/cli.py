"""CLI for Paper-to-Skill Pipeline."""
import argparse
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Paper-to-Skill Pipeline: Convert research papers into structured skill artifacts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py paper.md -o output/transformer-skill
  python cli.py https://arxiv.org/abs/1706.03762 -o output/transformer-skill
  python cli.py paper.html -o output/skill
        """
    )
    parser.add_argument("input", help="Paper file (markdown/HTML) or arXiv URL")
    parser.add_argument("-o", "--output", required=True, help="Output skill directory")
    parser.add_argument("--llm", action="store_true", help="Use LLM for enhanced extraction (requires API key)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input) and not args.input.startswith("http"):
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    
    results = run_pipeline(args.input, args.output, use_llm=args.llm)
    
    if "error" in results:
        print(f"Error: {results['error']}", file=sys.stderr)
        sys.exit(1)
    
    print(f"\n✅ Pipeline complete!")


if __name__ == "__main__":
    main()
