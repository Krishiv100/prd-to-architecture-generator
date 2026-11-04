
from pathlib import Path
from typing import Dict, Any
import tempfile

from src.state.arch_state import ArchitectureOutput
from src.state.prd_schema import PRDExtraction

from src.agents.analyzer_agent import RequirementAnalyzerAgent
from src.agents.architect_agent import SystemArchitectAgent
from src.agents.database_agent import DatabaseDesignerAgent
from src.agents.backend_api_agent import BackendAPIDesignAgent
from src.agents.security_agent import SecurityInfrastructureAgent
from src.agents.critic_agent import CollaborationCriticAgent

from src.compilers.mermaid_compiler import MermaidCompiler
from src.compilers.sql_compiler import SQLCompiler
from src.compilers.markdown_compiler import MarkdownCompiler
from src.compilers.docker_compose_compiler import DockerComposeCompiler
from src.compilers.capacity_estimator import CapacityEstimator
from src.compilers.openapi_compiler import OpenAPICompiler


class ArchitecturePipeline:
    def __init__(self):
        self.analyzer = RequirementAnalyzerAgent()
        self.architect = SystemArchitectAgent()
        self.database = DatabaseDesignerAgent()
        self.api_designer = BackendAPIDesignAgent()
        self.security = SecurityInfrastructureAgent()
        self.critic = CollaborationCriticAgent()
        self.md_compiler = MarkdownCompiler()

    def _save_artifacts(
        self,
        output_dir: str,
        mermaid_code: str,
        er_diagram: str,
        sql_ddl: str,
        docker_compose: str,
        final_spec: str,
        api_spec: str = "",
        openapi_spec: str = ""
    ) -> None:
        """Save generated architecture artifacts safely."""

        try:
            out_path = Path(output_dir)

            for folder in ["diagrams", "schemas", "specs", "infra"]:
                (out_path / folder).mkdir(parents=True, exist_ok=True)

        except OSError:
            out_path = Path(tempfile.gettempdir()) / "outputs"

            for folder in ["diagrams", "schemas", "specs", "infra"]:
                (out_path / folder).mkdir(parents=True, exist_ok=True)

        artifacts = {
            "diagrams/architecture.mmd": mermaid_code,
            "diagrams/er_diagram.mmd": er_diagram,
            "schemas/schema.sql": sql_ddl,
            "infra/docker-compose.yml": docker_compose,
            "specs/System_Design_Spec.md": final_spec,
            "specs/api_spec.md": api_spec,
            "specs/openapi.json": openapi_spec,
        }

        for relative_path, content in artifacts.items():
            try:
                (out_path / relative_path).write_text(
                    content,
                    encoding="utf-8"
                )
            except OSError:
                pass

    @staticmethod
    def _compile_api_spec(arch: ArchitectureOutput) -> str:
        """Convert structured API design into readable Markdown."""

        lines = [
            "# Backend API Specification",
            "",
            "## API Overview",
            "",
            "Base URL: `/api/v1`",
            "",
            "Authentication: Bearer token authentication",
            "",
            "## Endpoints",
            "",
            "| Method | Endpoint | Description |",
            "|---|---|---|",
        ]

        for endpoint in arch.api_endpoints:
            lines.append(
                f"| {endpoint.get('method', '')} "
                f"| `{endpoint.get('path', '')}` "
                f"| {endpoint.get('description', '')} |"
            )

        lines.extend(["", "## Resource Schemas", ""])

        for entity_name, fields in arch.api_schemas.items():
            lines.extend([
                f"### {entity_name}",
                "",
                "**Fields:**",
                ""
            ])

            for field in fields:
                lines.append(f"- `{field}`")

            lines.append("")

        lines.extend([
            "## Authentication and Authorization",
            ""
        ])

        for control in arch.api_authentication:
            lines.append(f"- {control}")

        lines.extend([
            "",
            "## Standard Error Responses",
            ""
        ])

        for error in arch.api_error_responses:
            lines.append(f"- {error}")

        return "\n".join(lines)

    def _execute_agents(
        self,
        prd_state: PRDExtraction,
        arch_state: ArchitectureOutput
    ) -> None:
        """Execute specialist agents in dependency order."""

        self.architect.process(prd_state, arch_state)
        self.database.process(prd_state, arch_state)
        self.api_designer.process(prd_state, arch_state)
        self.security.process(prd_state, arch_state)
        self.critic.process(prd_state, arch_state)

    def _compile_artifacts(self, prd_state, arch_state):
        """Compile architecture, database and infrastructure artifacts."""

        mermaid_code = MermaidCompiler.compile(arch_state)

        er_diagram = MermaidCompiler.compile_er_diagram(
            arch_state,
            prd_state
        )

        sql_ddl = SQLCompiler.compile(arch_state)

        docker_compose = DockerComposeCompiler.compile(arch_state)

        capacity = CapacityEstimator.estimate(
            prd_state,
            arch_state
        )

        final_spec = self.md_compiler.compile(
            prd=prd_state,
            arch=arch_state,
            mermaid_code=mermaid_code,
            sql_ddl=sql_ddl,
            er_diagram=er_diagram
        )

        api_spec = self._compile_api_spec(arch_state)
        openapi_spec = OpenAPICompiler.compile(arch_state)

        return {
            "mermaid": mermaid_code,
            "er_diagram": er_diagram,
            "sql": sql_ddl,
            "docker_compose": docker_compose,
            "capacity": capacity,
            "spec": final_spec,
            "api_spec": api_spec,
            "openapi_spec": openapi_spec,
        }

    def _build_agent_logs(
        self,
        prd_state: PRDExtraction,
        arch_state: ArchitectureOutput
    ):
        """Build structured execution logs for the agents."""

        return [
            {
                "agent": "RequirementAnalyzerAgent",
                "icon": "🔍",
                "title": "Document Parsing & Entity Discovery",
                "details": (
                    f"Discovered {len(prd_state.entities)} domain entities "
                    f"({', '.join(e.name for e in prd_state.entities)}). "
                    f"Extracted {prd_state.expected_rps:,} peak RPS, "
                    f"{prd_state.max_latency_ms}ms latency budget, "
                    f"{prd_state.availability_sla} SLA."
                )
            },
            {
                "agent": "SystemArchitectAgent",
                "icon": "🏛️",
                "title": "Scalability & Architecture Design",
                "details": (
                    f"Selected '{arch_state.topology}' topology. "
                    f"Configured {len(arch_state.compute_nodes)} compute nodes "
                    f"and {len(arch_state.infra_components)} infrastructure components."
                )
            },
            {
                "agent": "DatabaseDesignerAgent",
                "icon": "🗄️",
                "title": "Database & Schema Design",
                "details": (
                    f"Selected PrimaryDB: "
                    f"{arch_state.data_stores.get('PrimaryDB', 'Not specified')}. "
                    f"Designed {len(arch_state.tables_ddl)} tables "
                    f"and {len(arch_state.indexes)} indexes."
                )
            },
            {
                "agent": "BackendAPIDesignAgent",
                "icon": "🔌",
                "title": "REST API Design",
                "details": (
                    f"Generated {len(arch_state.api_endpoints)} REST endpoints "
                    f"across {len(arch_state.api_schemas)} resource schemas. "
                    f"Defined {len(arch_state.api_authentication)} "
                    f"authentication controls and "
                    f"{len(arch_state.api_error_responses)} standard error responses."
                )
            },
            {
                "agent": "SecurityInfrastructureAgent",
                "icon": "🛡️",
                "title": "Security & Compliance Hardening",
                "details": (
                    f"Generated {len(arch_state.security_controls)} "
                    f"security infrastructure controls."
                )
            },
            {
                "agent": "CollaborationCriticAgent",
                "icon": "⚖️",
                "title": "Architecture Review & Conflict Resolution",
                "details": (
                    f"Performed {arch_state.revision_count} "
                    f"architectural revisions and recorded "
                    f"{len(arch_state.findings)} review findings."
                )
            }
        ]

    def run(
        self,
        prd_text: str,
        output_dir: str = "outputs"
    ) -> str:
        """Run the architecture pipeline and return the system design."""

        prd_state: PRDExtraction = self.analyzer.analyze(prd_text)
        arch_state = ArchitectureOutput()

        self._execute_agents(prd_state, arch_state)

        artifacts = self._compile_artifacts(prd_state, arch_state)

        self._save_artifacts(
            output_dir,
            artifacts["mermaid"],
            artifacts["er_diagram"],
            artifacts["sql"],
            artifacts["docker_compose"],
            artifacts["spec"],
            artifacts["api_spec"],
            artifacts["openapi_spec"]
        )

        return artifacts["spec"]

    def run_with_state(
        self,
        prd_text: str,
        output_dir: str = "outputs"
    ) -> Dict[str, Any]:
        """Run the pipeline and return structured state and all artifacts."""

        prd_state = self.analyzer.analyze(prd_text)
        arch_state = ArchitectureOutput()

        self._execute_agents(prd_state, arch_state)

        artifacts = self._compile_artifacts(prd_state, arch_state)

        self._save_artifacts(
            output_dir,
            artifacts["mermaid"],
            artifacts["er_diagram"],
            artifacts["sql"],
            artifacts["docker_compose"],
            artifacts["spec"],
            artifacts["api_spec"],
            artifacts["openapi_spec"]
        )

        agent_logs = self._build_agent_logs(
            prd_state,
            arch_state
        )

        return {
            "prd": prd_state,
            "arch": arch_state,
            "capacity": artifacts["capacity"],
            "agent_logs": agent_logs,
            "spec": artifacts["spec"],
            "api_spec": artifacts["api_spec"],
            "openapi_spec": artifacts["openapi_spec"],
            "api_endpoints": arch_state.api_endpoints,
            "api_schemas": arch_state.api_schemas,
            "mermaid": artifacts["mermaid"],
            "er_diagram": artifacts["er_diagram"],
            "sql": artifacts["sql"],
            "docker_compose": artifacts["docker_compose"],
        }
