
from src.agents.backend_api_agent import BackendAPIDesignAgent
from src.state.arch_state import ArchitectureOutput
from src.state.prd_schema import PRDExtraction, EntitySpec


def test_generates_crud_endpoints_for_each_entity():
    prd = PRDExtraction(
        entities=[
            EntitySpec(name="User", fields=["id UUID PRIMARY KEY", "email VARCHAR(255)"]),
            EntitySpec(name="Order", fields=["id UUID PRIMARY KEY", "total DECIMAL"]),
        ]
    )
    arch = ArchitectureOutput()

    BackendAPIDesignAgent().process(prd, arch)

    assert len(arch.api_endpoints) == 12
    assert any(
        endpoint["method"] == "GET"
        and endpoint["path"] == "/api/v1/users"
        for endpoint in arch.api_endpoints
    )
    assert any(
        endpoint["method"] == "DELETE"
        and endpoint["path"] == "/api/v1/orders/{id}"
        for endpoint in arch.api_endpoints
    )


def test_generates_multiword_resource_paths():
    prd = PRDExtraction(
        entities=[
            EntitySpec(name="Delivery Partner", fields=["id UUID PRIMARY KEY"])
        ]
    )
    arch = ArchitectureOutput()

    BackendAPIDesignAgent().process(prd, arch)

    assert any(
        endpoint["path"] == "/api/v1/delivery-partners"
        for endpoint in arch.api_endpoints
    )


def test_generates_api_schemas():
    prd = PRDExtraction(
        entities=[
            EntitySpec(
                name="User",
                fields=[
                    "id UUID PRIMARY KEY",
                    "email VARCHAR(255)",
                    "created_at TIMESTAMP",
                ],
            )
        ]
    )
    arch = ArchitectureOutput()

    BackendAPIDesignAgent().process(prd, arch)

    assert arch.api_schemas["User"] == ["id", "email", "created_at"]


def test_generates_authentication_requirements():
    prd = PRDExtraction(
        entities=[EntitySpec(name="User")]
    )
    arch = ArchitectureOutput()

    BackendAPIDesignAgent().process(prd, arch)

    assert arch.api_authentication
    assert any("OAuth 2.0" in item or "JWT" in item for item in arch.api_authentication)


def test_generates_standard_error_responses():
    prd = PRDExtraction(
        entities=[EntitySpec(name="User")]
    )
    arch = ArchitectureOutput()

    BackendAPIDesignAgent().process(prd, arch)

    expected_codes = ["400", "401", "403", "404", "409", "422", "429", "500"]

    for code in expected_codes:
        assert any(
            response.startswith(code)
            for response in arch.api_error_responses
        )
