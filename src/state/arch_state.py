
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class CriticFinding(BaseModel):
    severity: str = "WARNING"  # CRITICAL, WARNING, INFO
    category: str = "General"  # Latency, Availability, Compliance, Storage, Throughput
    message: str
    action_taken: Optional[str] = None


class ArchitectureOutput(BaseModel):
    topology: str = "Modular Monolith"
    compute_nodes: List[str] = Field(default_factory=list)
    infra_components: List[str] = Field(default_factory=list)

    data_stores: Dict[str, str] = Field(default_factory=dict)
    tables_ddl: Dict[str, List[str]] = Field(default_factory=dict)
    indexes: List[str] = Field(default_factory=list)

    # Backend API design
    api_endpoints: List[Dict[str, str]] = Field(default_factory=list)
    api_schemas: Dict[str, List[str]] = Field(default_factory=dict)
    api_request_schemas: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    api_response_schemas: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    api_authentication: List[str] = Field(default_factory=list)
    api_error_responses: List[str] = Field(default_factory=list)

    security_controls: List[str] = Field(default_factory=list)
    findings: List[CriticFinding] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    revision_count: int = 0
    revision_log: List[str] = Field(default_factory=list)
