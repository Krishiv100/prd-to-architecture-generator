import pytest
from src.agents.critic_agent import CollaborationCriticAgent
from src.state.prd_schema import PRDExtraction
from src.state.arch_state import ArchitectureOutput

def test_critic_low_latency_auto_injection():
    critic = CollaborationCriticAgent()
    prd = PRDExtraction(
        project_name="UltraLowLatencyService",
        max_latency_ms=15,  # Requires cache
        expected_rps=500
    )
    arch = ArchitectureOutput()
    arch.data_stores = {"PrimaryDB": "PostgreSQL"}

    critic.process(prd, arch)

    assert "CacheLayer" in arch.data_stores
    assert arch.revision_count >= 1
    assert any("Latency" == f.category for f in arch.findings)
    assert any("Redis" in w for w in arch.warnings)

def test_critic_pci_compliance_advisory():
    critic = CollaborationCriticAgent()
    prd = PRDExtraction(
        project_name="BoutiqueCheckout",
        compliance=["PCI-DSS"],
        expected_rps=200
    )
    arch = ArchitectureOutput(topology="Modular Monolith")

    critic.process(prd, arch)

    assert any("PCI-DSS" in w for w in arch.warnings)
    assert any("Compliance" == f.category for f in arch.findings)

def test_critic_availability_sla_enforcement():
    critic = CollaborationCriticAgent()
    prd = PRDExtraction(
        project_name="CriticalCore",
        availability_sla="99.99%",
        expected_rps=300
    )
    arch = ArchitectureOutput()
    arch.infra_components = ["API_Gateway[Gateway]"]
    arch.data_stores = {"PrimaryDB": "PostgreSQL (Single Primary)"}

    critic.process(prd, arch)

    assert any("LB[" in c for c in arch.infra_components)
    assert "Multi-AZ" in arch.data_stores["PrimaryDB"]
    assert arch.revision_count >= 2

def test_critic_extreme_write_kafka_injection():
    critic = CollaborationCriticAgent()
    prd = PRDExtraction(
        project_name="HighIngestion",
        expected_rps=15000
    )
    arch = ArchitectureOutput()
    arch.infra_components = ["API_Gateway[Gateway]"]

    critic.process(prd, arch)

    assert any("Kafka" in c for c in arch.infra_components)
    assert "HighWriteStore" in arch.data_stores
    assert arch.revision_count >= 2
