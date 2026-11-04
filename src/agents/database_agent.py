
from pathlib import Path
from typing import Optional, List, Set
import re

import yaml

from src.agents.base_agent import BaseAgent
from src.state.prd_schema import PRDExtraction, EntitySpec
from src.state.arch_state import ArchitectureOutput


class DatabaseDesignerAgent(BaseAgent):
    def __init__(self, rules_path: Optional[str] = None):
        if rules_path and Path(rules_path).exists():
            resolved_path = Path(rules_path)
        else:
            resolved_path = (
                Path(__file__).resolve().parent.parent
                / "rules"
                / "topology_rules.yaml"
            )

        with open(resolved_path, "r", encoding="utf-8") as f:
            self.rules = yaml.safe_load(f)

    @staticmethod
    def _sql_identifier(name: str) -> str:
        """Convert an entity name into a safe SQL identifier."""
        identifier = re.sub(r"[^a-zA-Z0-9_]+", "_", name.strip())
        identifier = re.sub(r"_+", "_", identifier).strip("_")
        return identifier.lower()

    def _sort_entities_topologically(
        self,
        entities: List[EntitySpec]
    ) -> List[EntitySpec]:
        """Create parent tables before dependent child tables."""

        name_to_entity = {e.name: e for e in entities}
        visited: Set[str] = set()
        visiting: Set[str] = set()
        sorted_entities: List[EntitySpec] = []

        def dfs(name: str):
            if name in visiting:
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

        for entity in entities:
            if entity.name not in visited:
                dfs(entity.name)

        return sorted_entities

    def process(
        self,
        prd: PRDExtraction,
        arch: ArchitectureOutput
    ) -> None:
        # 1. Select primary database topology.
        multi_az_rules = self.rules.get(
            "multi_az_thresholds",
            {
                "availability": ["99.99%", "99.999%"],
                "min_rps": 2000
            }
        )

        is_multi_az = (
            prd.expected_rps >= multi_az_rules.get("min_rps", 2000)
            or prd.availability_sla in multi_az_rules.get(
                "availability",
                ["99.99%", "99.999%"]
            )
        )

        if is_multi_az:
            arch.data_stores["PrimaryDB"] = (
                "PostgreSQL (Multi-AZ Primary + Read Replicas "
                "with Connection Pooling)"
            )
        else:
            arch.data_stores["PrimaryDB"] = (
                "PostgreSQL (Single Primary with Automated Backups)"
            )

        # 2. Evaluate caching rules.
        cache_rules = self.rules.get(
            "caching_thresholds",
            {"max_latency_ms": 100, "min_rps": 3000}
        )

        if (
            prd.max_latency_ms <= cache_rules["max_latency_ms"]
            or prd.expected_rps >= cache_rules["min_rps"]
        ):
            arch.data_stores["CacheLayer"] = (
                "Redis Cluster (In-Memory Cache & Distributed Lock Manager)"
            )

        # 3. Evaluate high-throughput write store.
        hw_rules = self.rules.get(
            "high_write_thresholds",
            {"min_rps": 10000}
        )

        if prd.expected_rps >= hw_rules["min_rps"]:
            arch.data_stores["HighWriteStore"] = (
                "ScyllaDB / Apache Cassandra "
                "(Wide-Column Store for High Ingestion)"
            )

        # 4. Sort entities and generate DDL.
        ordered_entities = self._sort_entities_topologically(prd.entities)

        arch.tables_ddl = {}
        arch.indexes = []

        for entity in ordered_entities:
            cols = list(entity.fields)
            table_name = self._sql_identifier(entity.name)

            for target in entity.relations:
                target_table = self._sql_identifier(target)
                fk_column = f"{target_table}_id"

                fk_definition = (
                    f"{fk_column} UUID NOT NULL "
                    f"REFERENCES {target_table}(id) ON DELETE RESTRICT"
                )

                # Avoid duplicate foreign-key definitions.
                if not any(
                    fk_column.lower() in col.lower()
                    and "references" in col.lower()
                    for col in cols
                ):
                    cols.append(fk_definition)

                # Generate a foreign-key index.
                index_name = (
                    f"idx_{table_name}_{fk_column}"
                )

                index_sql = (
                    f"CREATE INDEX IF NOT EXISTS {index_name} "
                    f"ON {table_name} ({fk_column});"
                )

                if index_sql not in arch.indexes:
                    arch.indexes.append(index_sql)

            arch.tables_ddl[entity.name] = cols
