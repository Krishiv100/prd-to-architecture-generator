import pytest
from src.agents.analyzer_agent import RequirementAnalyzerAgent

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
