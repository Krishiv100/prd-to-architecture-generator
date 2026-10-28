import pytest
from pathlib import Path
from src.orchestrator.pipeline import ArchitecturePipeline

def test_pipeline_fintech_sample(tmp_path):
    pipeline = ArchitecturePipeline()
    prd_path = Path("inputs/sample_fintech_prd.md")
    assert prd_path.exists()

    raw_prd = prd_path.read_text(encoding="utf-8")
    out_dir = tmp_path / "outputs"

    spec = pipeline.run(raw_prd, output_dir=str(out_dir))

    assert "FinTech Checkout & Ledger Platform" in spec
    assert "Event-Driven Microservices" in spec
    assert (out_dir / "specs" / "System_Design_Spec.md").exists()
    assert (out_dir / "diagrams" / "architecture.mmd").exists()
    assert (out_dir / "diagrams" / "er_diagram.mmd").exists()
    assert (out_dir / "schemas" / "schema.sql").exists()
    assert (out_dir / "infra" / "docker-compose.yml").exists()

def test_pipeline_healthcare_sample(tmp_path):
    pipeline = ArchitecturePipeline()
    prd_path = Path("inputs/sample_healthcare_prd.md")
    assert prd_path.exists()

    raw_prd = prd_path.read_text(encoding="utf-8")
    out_dir = tmp_path / "outputs"

    res = pipeline.run_with_state(raw_prd, output_dir=str(out_dir))
    prd = res["prd"]
    arch = res["arch"]

    assert prd.project_name == "Healthcare Telemedicine & EHR Platform"
    assert "HIPAA" in prd.compliance
    assert "BAA-Compliant" in " ".join(arch.security_controls)
    assert any("Patient" in n for n in arch.compute_nodes) or ("Patient" in arch.tables_ddl)

def test_pipeline_ecommerce_flashsale_sample(tmp_path):
    pipeline = ArchitecturePipeline()
    prd_path = Path("inputs/sample_ecommerce_flashsale_prd.md")
    assert prd_path.exists()

    raw_prd = prd_path.read_text(encoding="utf-8")
    out_dir = tmp_path / "outputs"

    res = pipeline.run_with_state(raw_prd, output_dir=str(out_dir))
    prd = res["prd"]
    arch = res["arch"]

    assert prd.expected_rps == 28000
    assert "HighWriteStore" in arch.data_stores
    assert "CacheLayer" in arch.data_stores
    assert "Kafka" in " ".join(arch.infra_components)

def test_pipeline_iot_stream_sample(tmp_path):
    pipeline = ArchitecturePipeline()
    prd_path = Path("inputs/sample_iot_stream_prd.md")
    assert prd_path.exists()

    raw_prd = prd_path.read_text(encoding="utf-8")
    out_dir = tmp_path / "outputs"

    res = pipeline.run_with_state(raw_prd, output_dir=str(out_dir))
    prd = res["prd"]
    arch = res["arch"]

    assert prd.expected_rps == 65000
    assert "ScyllaDB" in arch.data_stores.get("HighWriteStore", "")
