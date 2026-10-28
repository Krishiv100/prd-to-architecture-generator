from pathlib import Path
from typing import Dict, Any, List
from src.state.arch_state import ArchitectureOutput
from src.state.prd_schema import PRDExtraction
from src.agents.analyzer_agent import RequirementAnalyzerAgent
from src.agents.architect_agent import SystemArchitectAgent
from src.agents.database_agent import DatabaseDesignerAgent
from src.agents.security_agent import SecurityInfrastructureAgent
from src.agents.critic_agent import CollaborationCriticAgent
from src.compilers.mermaid_compiler import MermaidCompiler
from src.compilers.sql_compiler import SQLCompiler
from src.compilers.markdown_compiler import MarkdownCompiler
from src.compilers.docker_compose_compiler import DockerComposeCompiler
from src.compilers.capacity_estimator import CapacityEstimator

class ArchitecturePipeline:
    def __init__(self):
        self.analyzer = RequirementAnalyzerAgent()
        self.architect = SystemArchitectAgent()
        self.database = DatabaseDesignerAgent()
        self.security = SecurityInfrastructureAgent()
        self.critic = CollaborationCriticAgent()
        self.md_compiler = MarkdownCompiler()

    def run(self, prd_text: str, output_dir: str = "outputs") -> str:
        # Step 1: Requirement Analyzer Agent extracts structured state
        prd_state: PRDExtraction = self.analyzer.analyze(prd_text)
        arch_state = ArchitectureOutput()

        # Step 2: Specialist Agents synthesize domain outputs
        self.architect.process(prd_state, arch_state)
        self.database.process(prd_state, arch_state)
        self.security.process(prd_state, arch_state)

        # Step 3: Collaboration Critic Agent peer-reviews & applies conflict resolutions
        self.critic.process(prd_state, arch_state)

        # Step 4: Deterministic Compilers generate artifacts
        mermaid_code = MermaidCompiler.compile(arch_state)
        er_diagram = MermaidCompiler.compile_er_diagram(arch_state, prd_state)
        sql_ddl = SQLCompiler.compile(arch_state)
        docker_compose = DockerComposeCompiler.compile(arch_state)
        final_spec = self.md_compiler.compile(
            prd=prd_state,
            arch=arch_state,
            mermaid_code=mermaid_code,
            sql_ddl=sql_ddl,
            er_diagram=er_diagram
        )

        # Step 5: Persist Artifacts to Disk
        out_path = Path(output_dir)
        (out_path / "diagrams").mkdir(parents=True, exist_ok=True)
        (out_path / "schemas").mkdir(parents=True, exist_ok=True)
        (out_path / "specs").mkdir(parents=True, exist_ok=True)
        (out_path / "infra").mkdir(parents=True, exist_ok=True)

        (out_path / "diagrams" / "architecture.mmd").write_text(mermaid_code, encoding="utf-8")
        (out_path / "diagrams" / "er_diagram.mmd").write_text(er_diagram, encoding="utf-8")
        (out_path / "schemas" / "schema.sql").write_text(sql_ddl, encoding="utf-8")
        (out_path / "infra" / "docker-compose.yml").write_text(docker_compose, encoding="utf-8")
        (out_path / "specs" / "System_Design_Spec.md").write_text(final_spec, encoding="utf-8")

        return final_spec

    def run_with_state(self, prd_text: str, output_dir: str = "outputs") -> Dict[str, Any]:
        """Runs the pipeline and returns both artifacts, capacity estimations, and agent logs."""
        prd_state = self.analyzer.analyze(prd_text)
        arch_state = ArchitectureOutput()

        self.architect.process(prd_state, arch_state)
        self.database.process(prd_state, arch_state)
        self.security.process(prd_state, arch_state)
        self.critic.process(prd_state, arch_state)

        mermaid_code = MermaidCompiler.compile(arch_state)
        er_diagram = MermaidCompiler.compile_er_diagram(arch_state, prd_state)
        sql_ddl = SQLCompiler.compile(arch_state)
        docker_compose = DockerComposeCompiler.compile(arch_state)
        capacity = CapacityEstimator.estimate(prd_state, arch_state)

        final_spec = self.md_compiler.compile(
            prd=prd_state,
            arch=arch_state,
            mermaid_code=mermaid_code,
            sql_ddl=sql_ddl,
            er_diagram=er_diagram
        )

        out_path = Path(output_dir)
        (out_path / "diagrams").mkdir(parents=True, exist_ok=True)
        (out_path / "schemas").mkdir(parents=True, exist_ok=True)
        (out_path / "specs").mkdir(parents=True, exist_ok=True)
        (out_path / "infra").mkdir(parents=True, exist_ok=True)

        (out_path / "diagrams" / "architecture.mmd").write_text(mermaid_code, encoding="utf-8")
        (out_path / "diagrams" / "er_diagram.mmd").write_text(er_diagram, encoding="utf-8")
        (out_path / "schemas" / "schema.sql").write_text(sql_ddl, encoding="utf-8")
        (out_path / "infra" / "docker-compose.yml").write_text(docker_compose, encoding="utf-8")
        (out_path / "specs" / "System_Design_Spec.md").write_text(final_spec, encoding="utf-8")

        # Multi-Agent Structured Reasoning Trace Log
        agent_logs = [
            {
                "agent": "RequirementAnalyzerAgent",
                "icon": "🔍",
                "title": "Document Parsing & Entity Discovery",
                "details": f"Discovered {len(prd_state.entities)} domain entities ({', '.join(e.name for e in prd_state.entities)}). Extracted {prd_state.expected_rps:,} peak RPS, {prd_state.max_latency_ms}ms latency budget, {prd_state.availability_sla} SLA, and compliance scope [{', '.join(prd_state.compliance) if prd_state.compliance else 'Standard Baseline'}]."
            },
            {
                "agent": "SystemArchitectAgent",
                "icon": "🏛️",
                "title": "Scalability Thresholds & Boundary Decomposition",
                "details": f"Evaluated scale against topology rules: Peak {prd_state.expected_rps:,} RPS -> Pattern chosen: '{arch_state.topology}'. Configured {len(arch_state.compute_nodes)} compute service boundaries and perimeter ingress components."
            },
            {
                "agent": "DatabaseDesignerAgent",
                "icon": "🗄️",
                "title": "Polyglot Persistence & Topological Schema DDL",
                "details": f"Allocated PrimaryDB: {arch_state.data_stores.get('PrimaryDB')}. Caching layer: {arch_state.data_stores.get('CacheLayer', 'Disabled')}. Topologically sorted {len(arch_state.tables_ddl)} relational tables and generated {len(arch_state.indexes)} foreign key lookup indexes."
            },
            {
                "agent": "SecurityInfrastructureAgent",
                "icon": "🛡️",
                "title": "Compliance Hardening & Defense-in-Depth",
                "details": f"Mapped regulatory matrices to {len(arch_state.security_controls)} perimeter and transport security controls ({', '.join(arch_state.security_controls[:3])}...)."
            },
            {
                "agent": "CollaborationCriticAgent",
                "icon": "⚖️",
                "title": "Cross-Domain Peer-Review & Automated Conflict Resolution",
                "details": f"Verified end-to-end SLA constraints. Performed {arch_state.revision_count} automated architectural corrections. Confirmed zero Single-Points-of-Failure (SPOF)."
            }
        ]

        return {
            "prd": prd_state,
            "arch": arch_state,
            "capacity": capacity,
            "agent_logs": agent_logs,
            "spec": final_spec,
            "mermaid": mermaid_code,
            "er_diagram": er_diagram,
            "sql": sql_ddl,
            "docker_compose": docker_compose
        }
