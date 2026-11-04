
import json

from src.compilers.openapi_compiler import OpenAPICompiler
from src.state.arch_state import ArchitectureOutput
from openapi_spec_validator import validate


def create_test_architecture():
    return ArchitectureOutput(
        api_endpoints=[
            {
                "method": "GET",
                "path": "/api/v1/users",
                "description": "List users",
            },
            {
                "method": "POST",
                "path": "/api/v1/users",
                "description": "Create User",
            },
            {
                "method": "GET",
                "path": "/api/v1/users/{id}",
                "description": "Retrieve User",
            },
            {
                "method": "DELETE",
                "path": "/api/v1/users/{id}",
                "description": "Delete User",
            },
        ],
        api_schemas={
            "User": ["id", "email", "age", "active"],
        },
        api_request_schemas={
            "User": {
                "email": "string",
                "age": "integer",
                "active": "boolean",
            },
        },
        api_response_schemas={
            "User": {
                "id": "string",
                "email": "string",
                "age": "integer",
                "active": "boolean",
            },
        },
        api_error_responses=[
            "400 Bad Request - Invalid request",
            "401 Unauthorized - Authentication required",
        ],
    )


def test_openapi_document_version():
    arch = create_test_architecture()

    document = json.loads(OpenAPICompiler.compile(arch))

    assert document["openapi"] == "3.0.3"


def test_openapi_generates_paths():
    arch = create_test_architecture()

    document = json.loads(OpenAPICompiler.compile(arch))

    assert "/api/v1/users" in document["paths"]
    assert "get" in document["paths"]["/api/v1/users"]
    assert "post" in document["paths"]["/api/v1/users"]


def test_openapi_generates_path_parameters():
    arch = create_test_architecture()

    document = json.loads(OpenAPICompiler.compile(arch))

    operation = document["paths"]["/api/v1/users/{id}"]["get"]

    assert operation["parameters"][0]["name"] == "id"
    assert operation["parameters"][0]["in"] == "path"
    assert operation["parameters"][0]["required"] is True


def test_openapi_generates_request_and_response_schemas():
    arch = create_test_architecture()

    document = json.loads(OpenAPICompiler.compile(arch))

    schemas = document["components"]["schemas"]

    assert "User" in schemas
    assert "UserRequest" in schemas

    assert schemas["User"]["properties"]["id"]["type"] == "string"
    assert schemas["User"]["properties"]["age"]["type"] == "integer"
    assert schemas["UserRequest"]["properties"]["active"]["type"] == "boolean"


def test_openapi_generates_bearer_authentication():
    arch = create_test_architecture()

    document = json.loads(OpenAPICompiler.compile(arch))

    auth = document["components"]["securitySchemes"]["BearerAuth"]

    assert auth["type"] == "http"
    assert auth["scheme"] == "bearer"
    assert auth["bearerFormat"] == "JWT"


def test_openapi_generates_error_responses():
    arch = create_test_architecture()

    document = json.loads(OpenAPICompiler.compile(arch))

    operation = document["paths"]["/api/v1/users"]["get"]

    assert "400" in operation["responses"]
    assert "401" in operation["responses"]

def test_openapi_document_is_valid():
    arch = create_test_architecture()
    document = json.loads(OpenAPICompiler.compile(arch))

    validate(document)