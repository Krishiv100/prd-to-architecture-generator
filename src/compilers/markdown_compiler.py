from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from src.state.prd_schema import PRDExtraction
from src.state.arch_state import ArchitectureOutput
from src.compilers.mermaid_compiler import MermaidCompiler

class MarkdownCompiler:
    def __init__(self, template_dir: Optional[str] = None):
        if template_dir and Path(template_dir).exists():
            resolved_dir = Path(template_dir)
        else:
            resolved_dir = Path(__file__).resolve().parent.parent / "templates"

        self.env = Environment(
            loader=FileSystemLoader(str(resolved_dir)),
            autoescape=select_autoescape(disabled_extensions=('md', 'j2')),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.template_name = "system_design_spec.md.j2"

    def compile(
        self,
        prd: PRDExtraction,
        arch: ArchitectureOutput,
        mermaid_code: str,
        sql_ddl: str,
        er_diagram: Optional[str] = None
    ) -> str:
        if er_diagram is None:
            er_diagram = MermaidCompiler.compile_er_diagram(arch, prd)

        template = self.env.get_template(self.template_name)
        return template.render(
            prd=prd,
            arch=arch,
            mermaid_code=mermaid_code,
            er_diagram=er_diagram,
            sql_ddl=sql_ddl
        )
