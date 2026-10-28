import pytest
from src.compilers.capacity_estimator import CapacityEstimator
from src.state.prd_schema import PRDExtraction, EntitySpec
from src.state.arch_state import ArchitectureOutput

def test_capacity_estimator_high_traffic():
    prd = PRDExtraction(
        project_name="HighScaleApp",
        expected_rps=35000,
        availability_sla="99.99%",
        entities=[EntitySpec(name="Order"), EntitySpec(name="User")]
    )
    arch = ArchitectureOutput(
        data_stores={"PrimaryDB": "PostgreSQL Multi-AZ", "HighWriteStore": "ScyllaDB", "CacheLayer": "Redis Cluster"},
        infra_components=["Kafka{{Apache Kafka}}"]
    )

    cap = CapacityEstimator.estimate(prd, arch)

    assert cap["peak_rps"] == 35000
    assert cap["read_qps"] > 0
    assert cap["write_qps"] > 0
    assert cap["recommended_pods"] > 10
    assert "r6g" in cap["primary_db_tier"]
    assert cap["cost_min"] > 1000
    assert cap["network_mbps"] > 0

def test_capacity_estimator_low_traffic():
    prd = PRDExtraction(
        project_name="SmallBlog",
        expected_rps=200,
        availability_sla="99.9%",
        entities=[EntitySpec(name="Post"), EntitySpec(name="User")]
    )
    arch = ArchitectureOutput(
        data_stores={"PrimaryDB": "PostgreSQL Single Primary"}
    )

    cap = CapacityEstimator.estimate(prd, arch)

    assert cap["peak_rps"] == 200
    assert cap["recommended_pods"] >= 2
    assert cap["cost_min"] < 500
