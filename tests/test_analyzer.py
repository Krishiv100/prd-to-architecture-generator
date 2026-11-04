
import pytest
from types import SimpleNamespace

from src.agents.analyzer_agent import RequirementAnalyzerAgent
from src.state.prd_schema import EntitySpec


def test_analyzer_basic_extraction():
    raw_prd = """
    # Payment Ledger Platform
    A high-throughput platform for ledger transactions.

    ## Functional Entities
    - Entity: User
    - Entity: Account -> User
    - Entity: Transaction -> Account, User

    ## Non-Functional Requirements
    - Throughput: 15000 req/s
    - Latency: 20 ms
    - Availability: 99.99%
    - Compliance: PCI-DSS, PII, SOC2
    - Features: Realtime alerts via websocket
    """

    analyzer = RequirementAnalyzerAgent()
    prd = analyzer.analyze(raw_prd)

    assert prd.project_name == "Payment Ledger Platform"
    assert len(prd.entities) == 3
    assert prd.expected_rps == 15000
    assert prd.max_latency_ms == 20
    assert prd.availability_sla == "99.99%"
    assert "PCI-DSS" in prd.compliance
    assert "PII" in prd.compliance
    assert "SOC2" in prd.compliance
    assert prd.realtime_features is True


def test_analyzer_with_fields():
    raw_prd = """
    # HealthPortal
    ## Functional Entities
    - Entity: Patient (mrn, email, full_name)
    - Entity: Doctor (license_number, specialty)
    - Entity: Appointment (scheduled_time, status) -> Patient, Doctor

    ## Non-Functional Requirements
    - Throughput: 2k rps
    - Latency: 50ms
    - Availability: 99.9%
    - Compliance: HIPAA
    """

    analyzer = RequirementAnalyzerAgent()
    prd = analyzer.analyze(raw_prd)

    assert prd.project_name == "HealthPortal"
    assert len(prd.entities) == 3
    assert prd.expected_rps == 2000
    assert prd.max_latency_ms == 50
    assert "HIPAA" in prd.compliance

    patient = next(e for e in prd.entities if e.name == "Patient")
    assert any("email" in f for f in patient.fields)
    assert any("mrn" in f for f in patient.fields)


def test_gemini_fields_are_merged_with_inferred_fields(monkeypatch):
    monkeypatch.setenv("USE_GEMINI", "true")

    entity = EntitySpec(
        name="Delivery Partner",
        fields=["delivery_status"],
        relations=[]
    )

    fake_result = SimpleNamespace(entities=[entity])

    class FakeGeminiPRDExtractor:
        def extract(self, raw_prd):
            return fake_result

    monkeypatch.setattr(
        "src.agents.analyzer_agent.GeminiPRDExtractor",
        FakeGeminiPRDExtractor
    )

    analyzer = RequirementAnalyzerAgent()
    prd = analyzer.analyze("Build a food delivery platform.")

    delivery_partner = prd.entities[0]
    fields = delivery_partner.fields

    assert "delivery_status" in fields
    assert any(f.startswith("id ") for f in fields)
    assert any(f.startswith("created_at ") for f in fields)
    assert any(f.startswith("email ") for f in fields)
    assert any(f.startswith("full_name ") for f in fields)
    assert any(f.startswith("status ") for f in fields)

    assert len(fields) == len(set(fields))


def test_gemini_relationships_are_normalized(monkeypatch):
    monkeypatch.setenv("USE_GEMINI", "true")

    entities = [
        EntitySpec(
            name="Customer",
            fields=[],
            relations=["places Order", "makes Payment"]
        ),
        EntitySpec(
            name="Order",
            fields=[],
            relations=[
                "placed by Customer",
                "accepted by Delivery Partner"
            ]
        ),
        EntitySpec(
            name="Payment",
            fields=[],
            relations=["associated with Order"]
        ),
        EntitySpec(
            name="Delivery Partner",
            fields=[],
            relations=["accepts Order"]
        ),
    ]

    fake_result = SimpleNamespace(entities=entities)

    class FakeGeminiPRDExtractor:
        def extract(self, raw_prd):
            return fake_result

    monkeypatch.setattr(
        "src.agents.analyzer_agent.GeminiPRDExtractor",
        FakeGeminiPRDExtractor
    )

    analyzer = RequirementAnalyzerAgent()
    result = analyzer.analyze("Build a food delivery platform.")

    relationships = {
        entity.name: entity.relations
        for entity in result.entities
    }

    assert relationships["Customer"] == ["Order", "Payment"]
    assert relationships["Order"] == ["Customer", "Delivery Partner"]
    assert relationships["Payment"] == ["Order"]
    assert relationships["Delivery Partner"] == ["Order"]
