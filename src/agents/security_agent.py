from pathlib import Path
from typing import Optional
import yaml
from src.agents.base_agent import BaseAgent
from src.state.prd_schema import PRDExtraction
from src.state.arch_state import ArchitectureOutput

class SecurityInfrastructureAgent(BaseAgent):
    def __init__(self, rules_path: Optional[str] = None):
        if rules_path and Path(rules_path).exists():
            resolved_path = Path(rules_path)
        else:
            resolved_path = Path(__file__).resolve().parent.parent / "rules" / "compliance_matrix.yaml"

        with open(resolved_path, "r", encoding="utf-8") as f:
            self.matrix = yaml.safe_load(f)

    def process(self, prd: PRDExtraction, arch: ArchitectureOutput) -> None:
        controls = list(self.matrix.get("baseline", []))
        standards_map = self.matrix.get("standards", {})

        for tag in prd.compliance:
            normalized_tag = tag.upper().strip()
            # Match directly or by prefix/key
            matched = False
            for std_key, std_controls in standards_map.items():
                if normalized_tag == std_key.upper():
                    matched = True
                    for ctrl in std_controls:
                        if ctrl not in controls:
                            controls.append(ctrl)
            if not matched and normalized_tag in ["PII", "GDPR", "PCI-DSS", "HIPAA", "SOC2", "ISO27001"]:
                # fallback lookup
                for ctrl in standards_map.get(normalized_tag, []):
                    if ctrl not in controls:
                        controls.append(ctrl)

        # Scale-triggered security controls
        if prd.expected_rps >= 5000:
            scale_ctrl = "Distributed DDoS Shield & Per-Client Leaky Bucket Rate Limiting"
            if scale_ctrl not in controls:
                controls.append(scale_ctrl)

        if prd.realtime_features:
            ws_ctrl = "mTLS / Ephemeral Token-Based Handshake for WebSocket Gateways"
            if ws_ctrl not in controls:
                controls.append(ws_ctrl)

        arch.security_controls = controls
