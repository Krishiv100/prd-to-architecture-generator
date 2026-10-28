from pathlib import Path
from typing import Optional
import yaml
from src.agents.base_agent import BaseAgent
from src.state.prd_schema import PRDExtraction
from src.state.arch_state import ArchitectureOutput

class SystemArchitectAgent(BaseAgent):
    def __init__(self, rules_path: Optional[str] = None):
        if rules_path and Path(rules_path).exists():
            resolved_path = Path(rules_path)
        else:
            resolved_path = Path(__file__).resolve().parent.parent / "rules" / "topology_rules.yaml"

        with open(resolved_path, "r", encoding="utf-8") as f:
            self.rules = yaml.safe_load(f)

    def process(self, prd: PRDExtraction, arch: ArchitectureOutput) -> None:
        arch.infra_components = ["API_Gateway[API Gateway / Ingress Router]"]
        arch.compute_nodes = []

        ms_rules = self.rules.get("microservices_thresholds", {"min_rps": 5000, "min_entities": 6})
        cdn_rules = self.rules.get("cdn_thresholds", {"min_rps": 5000})

        # 1. Edge & CDN Tier
        if prd.expected_rps >= cdn_rules.get("min_rps", 5000):
            arch.infra_components.insert(0, "CDN[Global CDN & WAF Edge]")

        # 2. Topology Decision
        is_high_rps = prd.expected_rps >= ms_rules.get("min_rps", 5000)
        has_many_entities = len(prd.entities) >= ms_rules.get("min_entities", 6)

        if is_high_rps or (has_many_entities and prd.expected_rps > 1000):
            arch.topology = "Event-Driven Microservices"
            arch.infra_components.extend([
                "LB[Layer-7 Load Balancer]",
                "Kafka{{Apache Kafka Event Bus}}"
            ])
            for ent in prd.entities:
                arch.compute_nodes.append(f"{ent.name}Svc[{ent.name} Service]")
        else:
            arch.topology = "Modular Monolith"
            arch.compute_nodes.append("CoreService[Core Application Monolith]")

        # 3. Realtime WebSockets Gateway
        if prd.realtime_features:
            arch.infra_components.append("WSGateway[WebSocket Gateway]")
