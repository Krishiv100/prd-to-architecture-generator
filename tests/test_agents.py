import pytest

from src.agents.architect_agent import SystemArchitectAgent
from src.agents.database_agent import DatabaseDesignerAgent
from src.agents.security_agent import SecurityInfrastructureAgent
from src.state.prd_schema import PRDExtraction, EntitySpec
from src.state.arch_state import ArchitectureOutput

def test_table_identifier_pluralization():
    test_cases = {
        "User": "users",
        "Users": "users",
        "Product": "products",
        "Products": "products",
        "Category": "categories",
        "Categories": "categories",
        "Person": "people",
        "People": "people",
        "Child": "children",
        "Children": "children",
        "Order": "orders",
        "Orders": "orders",
        "Analysis": "analyses",
        "Analyses": "analyses",
    }

    for entity_name, expected in test_cases.items():
        actual = DatabaseDesignerAgent._table_identifier(entity_name)
        assert actual == expected, (
            f"{entity_name}: expected {expected}, got {actual}"
        )

def test_architect_microservices_trigger():
    agent = SystemArchitectAgent()
    prd = PRDExtraction(
        project_name="ScaleApp",
        expected_rps=8000,
        entities=[EntitySpec(name="Order"), EntitySpec(name="User")]
    )
    arch = ArchitectureOutput()
    agent.process(prd, arch)

    assert arch.topology == "Event-Driven Microservices"
    assert any("Kafka" in c for c in arch.infra_components)
    assert any("OrderSvc" in c for c in arch.compute_nodes)
    assert any("CDN" in c for c in arch.infra_components)


def test_architect_monolith_trigger():
    agent = SystemArchitectAgent()
    prd = PRDExtraction(
        project_name="SimpleApp",
        expected_rps=400,
        entities=[EntitySpec(name="Task"), EntitySpec(name="User")]
    )
    arch = ArchitectureOutput()
    agent.process(prd, arch)

    assert arch.topology == "Modular Monolith"
    assert any("CoreService" in c for c in arch.compute_nodes)


def test_database_designer_topological_sort_and_engines():
    agent = DatabaseDesignerAgent()
    user_ent = EntitySpec(name="User")
    order_ent = EntitySpec(name="Order", relations=["User"])
    payment_ent = EntitySpec(name="Payment", relations=["Order", "User"])

    prd = PRDExtraction(
        project_name="StoreApp",
        expected_rps=12000,
        max_latency_ms=25,
        availability_sla="99.99%",
        entities=[payment_ent, order_ent, user_ent]
    )
    arch = ArchitectureOutput()
    agent.process(prd, arch)

    # Verify Multi-AZ and Caching
    assert "Multi-AZ" in arch.data_stores["PrimaryDB"]
    assert "CacheLayer" in arch.data_stores
    assert "HighWriteStore" in arch.data_stores

    # Verify topological order in DDL
    table_names = list(arch.tables_ddl.keys())
    assert table_names.index("User") < table_names.index("Order")
    assert table_names.index("Order") < table_names.index("Payment")

    # Verify foreign key and index generation
    assert any("user_id" in col for col in arch.tables_ddl["Order"])
    assert any("idx_orders_user_id" in idx for idx in arch.indexes)


def test_database_designer_multiword_entity_foreign_key():
    agent = DatabaseDesignerAgent()

    order_ent = EntitySpec(
        name="Order",
        relations=["Delivery Partner"]
    )
    delivery_partner_ent = EntitySpec(
        name="Delivery Partner"
    )

    prd = PRDExtraction(
        project_name="FoodDeliveryApp",
        entities=[order_ent, delivery_partner_ent]
    )

    arch = ArchitectureOutput()
    agent.process(prd, arch)

    order_columns = arch.tables_ddl["Order"]

    # Verify the multi-word entity becomes a valid SQL identifier
    assert any(
        "delivery_partner_id UUID NOT NULL" in column
        for column in order_columns
    )

    # Verify the foreign key references the normalized table name
    assert any(
        "REFERENCES delivery_partners(id)" in column
        for column in order_columns
    )

    # Verify the corresponding foreign-key index is generated
    assert any(
        "idx_orders_delivery_partner_id" in index
        for index in arch.indexes
    )


def test_security_infrastructure_compliance():
    agent = SecurityInfrastructureAgent()
    prd = PRDExtraction(
        project_name="MedApp",
        compliance=["HIPAA", "PII"],
        expected_rps=6000,
        realtime_features=True
    )
    arch = ArchitectureOutput()
    agent.process(prd, arch)

    # Baseline + HIPAA + PII + Scale controls
    controls_text = " ".join(arch.security_controls)
    assert "TLS 1.3" in controls_text
    assert "BAA-Compliant" in controls_text
    assert "AES-256 KMS" in controls_text
    assert "DDoS" in controls_text
    assert "WebSocket" in controls_text