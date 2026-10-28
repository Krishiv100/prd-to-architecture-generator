import pytest
from src.agents.architect_agent import SystemArchitectAgent
from src.agents.database_agent import DatabaseDesignerAgent
from src.agents.security_agent import SecurityInfrastructureAgent
from src.state.prd_schema import PRDExtraction, EntitySpec
from src.state.arch_state import ArchitectureOutput

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
        entities=[payment_ent, order_ent, user_ent]  # Intentionally out of dependency order
    )
    arch = ArchitectureOutput()
    agent.process(prd, arch)

    # Verify Multi-AZ and Caching
    assert "Multi-AZ" in arch.data_stores["PrimaryDB"]
    assert "CacheLayer" in arch.data_stores
    assert "HighWriteStore" in arch.data_stores

    # Verify topological order in DDL: User should appear before Order and Payment
    table_names = list(arch.tables_ddl.keys())
    assert table_names.index("User") < table_names.index("Order")
    assert table_names.index("Order") < table_names.index("Payment")

    # Verify foreign key and index generation
    assert any("user_id" in col for col in arch.tables_ddl["Order"])
    assert any("idx_order_user_id" in idx for idx in arch.indexes)

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
