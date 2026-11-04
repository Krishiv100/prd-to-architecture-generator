from typing import List, Dict, Optional

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)


class EntitySpec(BaseModel):
    name: str

    fields: List[str] = Field(
        default_factory=lambda: [
            "id UUID PRIMARY KEY",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ]
    )

    relations: List[str] = Field(default_factory=list)
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Entity name cannot be empty")

        return value

    @field_validator("fields")
    @classmethod
    def validate_fields(cls, value: List[str]) -> List[str]:
        cleaned = [field.strip() for field in value]

        if any(not field for field in cleaned):
            raise ValueError("Entity fields cannot contain empty values")

        if len(cleaned) != len(set(cleaned)):
            raise ValueError("Entity fields cannot contain duplicates")

        return cleaned

    @field_validator("relations")
    @classmethod
    def validate_relations(cls, value: List[str]) -> List[str]:
        cleaned = [relation.strip() for relation in value]

        if any(not relation for relation in cleaned):
            raise ValueError(
                "Entity relationships cannot contain empty values"
            )

        if len(cleaned) != len(set(cleaned)):
            raise ValueError(
                "Entity relationships cannot contain duplicates"
            )

        return cleaned


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

    @field_validator("expected_rps")
    @classmethod
    def validate_expected_rps(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Expected RPS must be greater than zero")
        return value

    @field_validator("max_latency_ms")
    @classmethod
    def validate_max_latency(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Maximum latency must be greater than zero")
        return value

    @field_validator("availability_sla")
    @classmethod
    def validate_availability_sla(cls, value: str) -> str:
        value = value.strip()

        if not value.endswith("%"):
            raise ValueError("Availability SLA must be expressed as a percentage")

        try:
            percentage = float(value[:-1])
        except ValueError:
            raise ValueError("Availability SLA must be a valid percentage")

        if not 0 < percentage <= 100:
            raise ValueError("Availability SLA must be greater than 0% and at most 100%")

        return f"{percentage:g}%"

    @model_validator(mode="after")
    def validate_entity_relationships(self):
        entity_names = {
            entity.name.casefold()
            for entity in self.entities
        }

        if len(entity_names) != len(self.entities):
            raise ValueError("Entity names must be unique")

        for entity in self.entities:
            for relation in entity.relations:
                if relation.casefold() not in entity_names:
                    raise ValueError(
                        f"Entity '{entity.name}' references "
                        f"unknown entity '{relation}'"
                    )

        return self
