
import re
from typing import List, Dict

from src.agents.base_agent import BaseAgent
from src.state.prd_schema import PRDExtraction
from src.state.arch_state import ArchitectureOutput


class BackendAPIDesignAgent(BaseAgent):
    """Generates REST API endpoints and structured request/response schemas."""

    @staticmethod
    def _resource_name(entity_name: str) -> str:
        """Convert entity names into lowercase, hyphenated API resources."""
        name = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", entity_name.strip())
        name = re.sub(r"[^a-zA-Z0-9]+", "-", name)
        return name.strip("-").lower() + "s"

    @staticmethod
    def _parse_field(field: str) -> tuple:
        """Extract a field name and infer its OpenAPI-compatible data type."""
        parts = field.strip().split()

        if not parts:
            return None, None

        field_name = parts[0]

        if field_name.upper() in {"PRIMARY", "FOREIGN"}:
            return None, None

        sql_definition = " ".join(parts[1:]).upper()

        if any(t in sql_definition for t in ["UUID"]):
            field_type = "string"
        elif any(t in sql_definition for t in ["INT", "SERIAL"]):
            field_type = "integer"
        elif any(t in sql_definition for t in ["DECIMAL", "NUMERIC", "FLOAT", "DOUBLE", "REAL"]):
            field_type = "number"
        elif any(t in sql_definition for t in ["BOOL"]):
            field_type = "boolean"
        elif any(t in sql_definition for t in ["DATE", "TIMESTAMP", "TIME"]):
            field_type = "string"
        else:
            field_type = "string"

        return field_name, field_type

    @classmethod
    def _build_schema(cls, fields: List[str]) -> Dict[str, str]:
        """Build a field-to-type mapping from SQL-like field definitions."""
        schema = {}

        for field in fields:
            field_name, field_type = cls._parse_field(field)

            if field_name:
                schema[field_name] = field_type

        return schema

    def process(
        self,
        prd: PRDExtraction,
        arch: ArchitectureOutput
    ) -> None:
        arch.api_endpoints = []
        arch.api_schemas = {}
        arch.api_request_schemas = {}
        arch.api_response_schemas = {}
        arch.api_authentication = []
        arch.api_error_responses = []

        # Generate CRUD endpoints and schemas for every PRD entity.
        for entity in prd.entities:
            resource = self._resource_name(entity.name)

            schema = self._build_schema(entity.fields)

            arch.api_schemas[entity.name] = list(schema.keys())
            arch.api_request_schemas[entity.name] = {
                key: value
                for key, value in schema.items()
                if key.lower() not in {"id", "created_at", "updated_at"}
            }
            arch.api_response_schemas[entity.name] = schema

            endpoints = [
                ("GET", f"/api/v1/{resource}", f"List {entity.name}"),
                ("POST", f"/api/v1/{resource}", f"Create {entity.name}"),
                ("GET", f"/api/v1/{resource}/{{id}}", f"Retrieve {entity.name}"),
                ("PUT", f"/api/v1/{resource}/{{id}}", f"Replace {entity.name}"),
                ("PATCH", f"/api/v1/{resource}/{{id}}", f"Update {entity.name}"),
                ("DELETE", f"/api/v1/{resource}/{{id}}", f"Delete {entity.name}"),
            ]

            for method, path, description in endpoints:
                arch.api_endpoints.append({
                    "method": method,
                    "path": path,
                    "description": description,
                })

        # Baseline authentication requirements.
        if prd.entities:
            arch.api_authentication = [
                "Bearer token authentication using OAuth 2.0 or JWT",
                "Validate authentication tokens on protected endpoints",
                "Enforce role-based authorization for sensitive operations",
                "Use TLS (HTTPS) for all API communication",
            ]

        # Standard API error responses.
        arch.api_error_responses = [
            "400 Bad Request - Invalid request payload or parameters",
            "401 Unauthorized - Missing or invalid authentication",
            "403 Forbidden - Insufficient permissions",
            "404 Not Found - Requested resource does not exist",
            "409 Conflict - Resource state conflict",
            "422 Unprocessable Entity - Validation failed",
            "429 Too Many Requests - Rate limit exceeded",
            "500 Internal Server Error - Unexpected server failure",
        ]
