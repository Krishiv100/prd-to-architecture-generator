from pathlib import Path
from typing import Optional, List, Dict, Set
import yaml
from src.agents.base_agent import BaseAgent
from src.state.prd_schema import PRDExtraction, EntitySpec
from src.state.arch_state import ArchitectureOutput

class DatabaseDesignerAgent(BaseAgent):
    def __init__(self, rules_path: Optional[str] = None):
        if rules_path and Path(rules_path).exists():
            resolved_path = Path(rules_path)
        else:
            resolved_path = Path(__file__).resolve().parent.parent / "rules" / "topology_rules.yaml"

        with open(resolved_path, "r", encoding="utf-8") as f:
            self.rules = yaml.safe_load(f)

    def _sort_entities_topologically(self, entities: List[EntitySpec]) -> List[EntitySpec]:
        """Topological sort so parent tables are created before dependent child tables."""
        name_to_entity = {e.name: e for e in entities}
        visited: Set[str] = set()
        visiting: Set[str] = set()
        sorted_entities: List[EntitySpec] = []

        def dfs(name: str):
            if name in visiting:
                # Cycle detected, break to avoid infinite loop
                return
            if name not in visited:
                visiting.add(name)
                entity = name_to_entity.get(name)
                if entity:
                    for dep in entity.relations:
                        if dep in name_to_entity:
                            dfs(dep)
                    visited.add(name)
                    visiting.remove(name)
                    sorted_entities.append(entity)

        for ent in entities:
            if ent.name not in visited:
                dfs(ent.name)

        return sorted_entities

    def process(self, prd: PRDExtraction, arch: ArchitectureOutput) -> None:
        # 1. Select Primary Database Topology
        multi_az_rules = self.rules.get("multi_az_thresholds", {"availability": ["99.99%", "99.999%"], "min_rps": 2000})
        is_multi_az = (
            prd.expected_rps >= multi_az_rules.get("min_rps", 2000)
            or prd.availability_sla in multi_az_rules.get("availability", ["99.99%", "99.999%"])
        )

        if is_multi_az:
            arch.data_stores["PrimaryDB"] = "PostgreSQL (Multi-AZ Primary + Read Replicas with Connection Pooling)"
        else:
            arch.data_stores["PrimaryDB"] = "PostgreSQL (Single Primary with Automated Backups)"

        # 2. Evaluate Caching Rules
        cache_rules = self.rules.get("caching_thresholds", {"max_latency_ms": 100, "min_rps": 3000})
        if prd.max_latency_ms <= cache_rules["max_latency_ms"] or prd.expected_rps >= cache_rules["min_rps"]:
            arch.data_stores["CacheLayer"] = "Redis Cluster (In-Memory Cache & Distributed Lock Manager)"

        # 3. Evaluate High-Throughput Write Store
        hw_rules = self.rules.get("high_write_thresholds", {"min_rps": 10000})
        if prd.expected_rps >= hw_rules["min_rps"]:
            arch.data_stores["HighWriteStore"] = "ScyllaDB / Apache Cassandra (Wide-Column Store for High Ingestion)"

        # 4. Topological Sort & DDL Generation
        ordered_entities = self._sort_entities_topologically(prd.entities)

        arch.tables_ddl = {}
        arch.indexes = []

        for ent in ordered_entities:
            cols = list(ent.fields)
            for target in ent.relations:
                fk_col = f"{target.lower()}_id UUID NOT NULL REFERENCES {target}(id) ON DELETE RESTRICT"
                if not any(target.lower() in c.lower() and "references" in c.lower() for c in cols):
                    cols.append(fk_col)

                # Generate foreign key index
                idx = f"CREATE INDEX IF NOT EXISTS idx_{ent.name.lower()}_{target.lower()}_id ON {ent.name} ({target.lower()}_id);"
                if idx not in arch.indexes:
                    arch.indexes.append(idx)

            arch.tables_ddl[ent.name] = cols
