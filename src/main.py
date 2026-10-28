import sys
import argparse
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.orchestrator.pipeline import ArchitecturePipeline

# Vercel Serverless Function entry point exports
try:
    from src.gui.server import ArchitectureGUIHandler
    handler = ArchitectureGUIHandler
    app = ArchitectureGUIHandler
    application = ArchitectureGUIHandler
except Exception:
    pass

def parse_args():
    parser = argparse.ArgumentParser(
        description="Multi-Agent PRD-to-Architecture Generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        default=None,
        help="Path to an input PRD file (.md, .txt, etc.), or '-' to read from standard input"
    )
    parser.add_argument(
        "-i", "--input",
        dest="input_file_flag",
        default=None,
        help="Alternative flag to specify input PRD document path"
    )
    parser.add_argument(
        "-t", "--text",
        default=None,
        help="Directly pass arbitrary requirements or PRD text via command line"
    )
    parser.add_argument(
        "-I", "--interactive",
        action="store_true",
        help="Interactive mode: prompt to type or paste requirements in terminal"
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="outputs",
        help="Directory to save generated architectural artifacts"
    )
    parser.add_argument(
        "-s", "--summary-only",
        action="store_true",
        help="Print only the executive summary and artifact locations instead of full spec"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the interactive Multi-Agent Architecture Studio Web GUI"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port number for the GUI web server"
    )
    return parser.parse_args()

def main():
    args = parse_args()

    # Launch GUI if requested
    if args.gui:
        from src.gui.server import start_gui_server
        start_gui_server(port=args.port)
        return

    raw_prd = None
    input_source_desc = ""

    # Priority 1: Interactive Prompt
    if args.interactive:
        print("=" * 70)
        print("✍️ INTERACTIVE PRD INPUT MODE")
        print("=" * 70)
        print("Type or paste your requirements, user stories, or PRD document below.")
        print("When finished, press Enter then:")
        print("  - On Windows: press Ctrl+Z then Enter")
        print("  - On Linux/macOS: press Ctrl+D")
        print("-" * 70)
        try:
            raw_prd = sys.stdin.read()
        except KeyboardInterrupt:
            print("\n[!] Aborted by user.")
            sys.exit(0)
        input_source_desc = "Interactive Terminal Input"

    # Priority 2: Direct text argument
    elif args.text:
        raw_prd = args.text
        input_source_desc = f"Direct Command-Line Text ({len(raw_prd)} chars)"

    # Priority 3: Stdin '-'
    elif args.input_path == "-" or args.input_file_flag == "-":
        print("[*] Reading PRD from standard input (stdin)...")
        raw_prd = sys.stdin.read()
        input_source_desc = "Standard Input (stdin pipe)"

    # Priority 4: File Path
    else:
        target_path_str = args.input_file_flag if args.input_file_flag else args.input_path
        if not target_path_str:
            target_path_str = "inputs/sample_fintech_prd.md"

        target_path = Path(target_path_str)
        if not target_path.exists():
            print(f"[!] Error: Specified input document not found at: {target_path}")
            sys.exit(1)

        raw_prd = target_path.read_text(encoding="utf-8")
        input_source_desc = f"File: {target_path}"

    if not raw_prd or not raw_prd.strip():
        print("[!] Error: No input requirements text was provided.")
        sys.exit(1)

    print("=" * 70)
    print("[*] MULTI-AGENT PRD-TO-ARCHITECTURE GENERATOR")
    print("=" * 70)
    print(f"Input Source       : {input_source_desc}")
    print(f"Output Destination : {args.output_dir}/")
    print("-" * 70)

    pipeline = ArchitecturePipeline()

    print("Agent Pipeline Execution in Progress:")
    print("   [1/5] RequirementAnalyzerAgent      : Discovering entities, NFRs & compliance...")
    print("   [2/5] SystemArchitectAgent          : Evaluating scale thresholds & topology...")
    print("   [3/5] DatabaseDesignerAgent         : Designing polyglot persistence & DDL...")
    print("   [4/5] SecurityInfrastructureAgent   : Hardening compliance & perimeter controls...")
    print("   [5/5] CollaborationCriticAgent      : Peer-reviewing cross-domain SLAs & SPOFs...")

    results = pipeline.run_with_state(raw_prd, output_dir=args.output_dir)
    prd = results["prd"]
    arch = results["arch"]

    print("\n[+] Architectural Synthesis & Peer-Review Succeeded!")
    print("=" * 70)
    print(f"Project Name       : {prd.project_name}")
    print(f"Topology Selected  : {arch.topology}")
    print(f"Target Throughput  : {prd.expected_rps:,} req/s")
    print(f"Latency Budget     : {prd.max_latency_ms} ms")
    print(f"Availability SLA   : {prd.availability_sla}")
    print(f"Compliance Scope   : {', '.join(prd.compliance) if prd.compliance else 'Standard Baseline'}")
    print(f"Critic Revisions   : {arch.revision_count} automated corrections applied")
    print(f"Entities Mapped    : {len(prd.entities)} ({', '.join(e.name for e in prd.entities)})")
    print("-" * 70)
    print("Generated Artifacts:")
    print(f"   * Specification    : {args.output_dir}/specs/System_Design_Spec.md")
    print(f"   * Topology Diagram : {args.output_dir}/diagrams/architecture.mmd")
    print(f"   * ER Data Diagram  : {args.output_dir}/diagrams/er_diagram.mmd")
    print(f"   * Database DDL     : {args.output_dir}/schemas/schema.sql")
    print(f"   * Docker Compose   : {args.output_dir}/infra/docker-compose.yml")
    print("=" * 70)

    if not args.summary_only:
        print("\n" + results["spec"])

if __name__ == "__main__":
    main()
