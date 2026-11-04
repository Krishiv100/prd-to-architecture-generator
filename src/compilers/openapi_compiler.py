
import json
import re
from typing import Any, Dict, Optional

from src.state.arch_state import ArchitectureOutput


class OpenAPICompiler:
    """Compiles architecture API definitions into an OpenAPI 3.0 document."""

    @staticmethod
    def _schema_name(entity_name: str) -> str:
        """Convert entity names into valid component schema names."""
        parts = re.findall(r"[a-zA-Z0-9]+", entity_name)
        return "".join(part.capitalize() for part in parts) or "Resource"

    @staticmethod
    def _resource_name(entity_name: str) -> str:
        """Match the resource naming convention used by BackendAPIDesignAgent."""
        name = re.sub(
            r"([a-z0-9])([A-Z])",
            r"\1-\2",
            entity_name.strip()
        )
        name = re.sub(r"[^a-zA-Z0-9]+", "-", name)
        return name.strip("-").lower() + "s"

    @staticmethod
    def _operation_id(method: str, path: str) -> str:
        """Generate unique operation IDs."""
        parts = []

        for part in path.strip("/").split("/"):
            if part.startswith("{") and part.endswith("}"):
                parts.append("By" + part[1:-1].capitalize())
            else:
                parts.append(part.capitalize())

        return method.lower() + "".join(parts)

    @staticmethod
    def _property_schema(field_type: str) -> Dict[str, Any]:
        """Convert inferred field types into OpenAPI property definitions."""
        if field_type == "integer":
            return {"type": "integer"}

        if field_type == "number":
            return {"type": "number"}

        if field_type == "boolean":
            return {"type": "boolean"}

        return {"type": "string"}

    @classmethod
    def _build_schemas(
        cls,
        arch: ArchitectureOutput
    ) -> Dict[str, Any]:
        """Build request and response component schemas."""
        schemas = {}

        for entity_name, fields in arch.api_response_schemas.items():
            schema_name = cls._schema_name(entity_name)

            schemas[schema_name] = {
                "type": "object",
                "properties": {
                    field_name: cls._property_schema(field_type)
                    for field_name, field_type in fields.items()
                },
            }

        for entity_name, fields in arch.api_request_schemas.items():
            schema_name = cls._schema_name(entity_name) + "Request"

            schemas[schema_name] = {
                "type": "object",
                "properties": {
                    field_name: cls._property_schema(field_type)
                    for field_name, field_type in fields.items()
                },
            }

        return schemas

    @classmethod
    def _build_resource_mapping(
        cls,
        arch: ArchitectureOutput
    ) -> Dict[str, str]:
        """Map API collection paths to their corresponding entities."""
        mapping = {}

        for entity_name in arch.api_schemas:
            resource = cls._resource_name(entity_name)
            collection_path = f"/api/v1/{resource}"
            mapping[collection_path.rstrip("/")] = entity_name

        return mapping

    @staticmethod
    def _error_responses(
        errors: list
    ) -> Dict[str, Dict[str, str]]:
        """Convert standard API errors into OpenAPI responses."""
        responses = {}

        for error in errors:
            match = re.match(r"(\d{3})\s+(.+)", error)

            if match:
                status_code, description = match.groups()

                responses[status_code] = {
                    "description": description
                }

        return responses

    @classmethod
    def _build_operation(
        cls,
        endpoint: Dict[str, str],
        entity_name: Optional[str],
        schemas: Dict[str, Any],
        arch: ArchitectureOutput
    ) -> Dict[str, Any]:
        """Build an OpenAPI operation for an API endpoint."""

        method = endpoint["method"].lower()
        path = endpoint["path"]
        description = endpoint.get("description", "")

        schema_name = (
            cls._schema_name(entity_name)
            if entity_name else None
        )

        operation = {
            "summary": description,
            "operationId": cls._operation_id(method, path),
            "responses": {},
            "security": [{"BearerAuth": []}],
        }

        # Path parameters.
        path_parameters = re.findall(r"\{([^}]+)\}", path)

        if path_parameters:
            operation["parameters"] = [
                {
                    "name": parameter,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
                for parameter in path_parameters
            ]

        # Request bodies.
        if method in {"post", "put", "patch"} and schema_name:
            request_schema = schema_name + "Request"

            if request_schema in schemas:
                operation["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": (
                                    f"#/components/schemas/{request_schema}"
                                )
                            }
                        }
                    },
                }

        # Successful responses.
        if method == "delete":
            operation["responses"]["204"] = {
                "description": "Resource deleted successfully"
            }

        elif method == "get" and path_parameters and schema_name:
            operation["responses"]["200"] = {
                "description": "Resource retrieved successfully",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": f"#/components/schemas/{schema_name}"
                        }
                    }
                },
            }

        elif method == "get" and schema_name:
            operation["responses"]["200"] = {
                "description": "Resources retrieved successfully",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "array",
                            "items": {
                                "$ref": (
                                    f"#/components/schemas/{schema_name}"
                                )
                            },
                        }
                    }
                },
            }

        elif method == "post":
            operation["responses"]["201"] = {
                "description": "Resource created successfully"
            }

        else:
            operation["responses"]["200"] = {
                "description": "Resource updated successfully"
            }

        # Standard error responses.
        operation["responses"].update(
            cls._error_responses(arch.api_error_responses)
        )

        return operation

    @classmethod
    def compile(cls, arch: ArchitectureOutput) -> str:
        """Generate a serialized OpenAPI 3.0.3 JSON document."""

        schemas = cls._build_schemas(arch)
        resource_mapping = cls._build_resource_mapping(arch)

        paths = {}

        for endpoint in arch.api_endpoints:
            path = endpoint["path"]

            # Remove the final path parameter to identify its collection.
            collection_path = re.sub(
                r"/\{[^}]+\}$",
                "",
                path.rstrip("/")
            )

            entity_name = resource_mapping.get(collection_path)

            operation = cls._build_operation(
                endpoint,
                entity_name,
                schemas,
                arch
            )

            paths.setdefault(path, {})[
                endpoint["method"].lower()
            ] = operation

        document = {
            "openapi": "3.0.3",
            "info": {
                "title": "Generated Backend API",
                "version": "1.0.0",
                "description": (
                    "Automatically generated REST API specification."
                ),
            },
            "servers": [
                {"url": "/"}
            ],
            "paths": paths,
            "components": {
                "schemas": schemas,
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                    }
                },
            },
        }

        return json.dumps(document, indent=2)
