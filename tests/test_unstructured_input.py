import pytest
from src.agents.analyzer_agent import RequirementAnalyzerAgent
from src.orchestrator.pipeline import ArchitecturePipeline

def test_unstructured_ride_sharing_prompt():
    raw_text = """
    Ride Sharing and Fleet App
    We want to build a service connecting riders and drivers.
    Riders can book trips and drivers accept rides.
    Drivers have cars and vehicles.
    Payments are handled via credit card and Stripe.
    Scale needs to support 25,000 req/s, sub 30ms latency, and 99.99% availability.
    We need realtime GPS tracking for vehicles.
    """
    analyzer = RequirementAnalyzerAgent()
    prd = analyzer.analyze(raw_text)

    entity_names = {e.name for e in prd.entities}
    assert "Driver" in entity_names or "Rider" in entity_names or "Trip" in entity_names
    assert "Payment" in entity_names
    assert prd.expected_rps == 25000
    assert prd.max_latency_ms == 30
    assert prd.availability_sla == "99.99%"
    assert "PCI-DSS" in prd.compliance
    assert prd.realtime_features is True

def test_unstructured_healthcare_prompt():
    raw_text = """
    Telehealth Patient Consultations
    Patients schedule appointments with doctors.
    Doctors view medical records and issue prescriptions.
    We require HIPAA compliance and high availability uptime.
    Expected traffic is 3000 requests per second.
    """
    analyzer = RequirementAnalyzerAgent()
    prd = analyzer.analyze(raw_text)

    entity_names = {e.name for e in prd.entities}
    assert "Patient" in entity_names
    assert "Doctor" in entity_names
    assert "HIPAA" in prd.compliance
    assert prd.expected_rps == 3000

def test_unstructured_chat_pipeline():
    pipeline = ArchitecturePipeline()
    raw_text = """
    Realtime Team Messaging
    Users create channels and post messages.
    We need 45k rps, sub-50ms latency, 99.99% uptime, and websockets for instant live chat.
    """
    res = pipeline.run_with_state(raw_text)
    prd = res["prd"]
    arch = res["arch"]

    assert prd.expected_rps == 45000
    assert arch.topology == "Event-Driven Microservices"
    assert "CacheLayer" in arch.data_stores
    assert "Kafka" in " ".join(arch.infra_components)
    assert any("User" in t for t in arch.tables_ddl)
    assert any("Message" in t for t in arch.tables_ddl)
