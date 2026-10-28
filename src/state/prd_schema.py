from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class EntitySpec(BaseModel):
    name: str
    fields: List[str] = Field(
        default_factory=lambda: ["id UUID PRIMARY KEY", "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"]
    )
    relations: List[str] = Field(default_factory=list)
    description: Optional[str] = None

class PRDExtraction(BaseModel):
    project_name: str = "SystemService"
    description: str = "Enterprise Distributed System"
    entities: List[EntitySpec] = Field(default_factory=list)
    expected_rps: int = 500
    max_latency_ms: int = 200
    availability_sla: str = "99.9%"
    compliance: List[str] = Field(default_factory=list)
    realtime_features: bool = False
    extra_nfrs: Dict[str, str] = Field(default_factory=dict)
