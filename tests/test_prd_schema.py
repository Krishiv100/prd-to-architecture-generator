import pytest
from pydantic import ValidationError

from src.state.prd_schema import EntitySpec, PRDExtraction


def test_default_prd_values():
    prd = PRDExtraction()

    assert prd.expected_rps == 500
    assert prd.max_latency_ms == 200
    assert prd.availability_sla == "99.9%"


def test_valid_entity_relationship():
    prd = PRDExtraction(
        entities=[
            EntitySpec(name="User"),
            EntitySpec(name="Order", relations=["User"]),
        ]
    )

    assert len(prd.entities) == 2


def test_empty_entity_name_rejected():
    with pytest.raises(ValidationError):
        EntitySpec(name="   ")


def test_duplicate_entity_names_rejected_case_insensitively():
    with pytest.raises(ValidationError):
        PRDExtraction(
            entities=[
                EntitySpec(name="User"),
                EntitySpec(name="user"),
            ]
        )


def test_unknown_entity_relationship_rejected():
    with pytest.raises(ValidationError):
        PRDExtraction(
            entities=[
                EntitySpec(name="Order", relations=["Customer"]),
            ]
        )


@pytest.mark.parametrize("rps", [0, -1])
def test_non_positive_rps_rejected(rps):
    with pytest.raises(ValidationError):
        PRDExtraction(expected_rps=rps)


@pytest.mark.parametrize("latency", [0, -1])
def test_non_positive_latency_rejected(latency):
    with pytest.raises(ValidationError):
        PRDExtraction(max_latency_ms=latency)


@pytest.mark.parametrize(
    "sla",
    ["abc%", "99", "0%", "-5%", "101%", ""],
)
def test_invalid_availability_sla_rejected(sla):
    with pytest.raises(ValidationError):
        PRDExtraction(availability_sla=sla)


@pytest.mark.parametrize(
    ("sla", "expected"),
    [
        ("99.9%", "99.9%"),
        ("100%", "100%"),
        (" 99.90% ", "99.9%"),
    ],
)
def test_valid_availability_sla_normalized(sla, expected):
    prd = PRDExtraction(availability_sla=sla)

    assert prd.availability_sla == expected
