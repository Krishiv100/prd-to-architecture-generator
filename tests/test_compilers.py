import pytest
from src.state.arch_state import ArchitectureOutput
from src.state.prd_schema import PRDExtraction, EntitySpec
from src.compilers.mermaid_compiler import MermaidCompiler
from src.compilers.sql_compiler import SQLCompiler
from src.compilers.markdown_compiler import MarkdownCompiler
from src.compilers.docker_compose_compiler import DockerComposeCompiler

def test_mermaid_compiler_validity():
    arch = ArchitectureOutput(
        compute_nodes=["OrderSvc[Order Service]", "UserSvc[User Service]"],
        infra_components=["API_Gateway[Gateway]", "LB[Layer-7 Load Balancer]", "Kafka{{Apache Kafka Event Bus}}"],
        data_stores={"PrimaryDB": "PostgreSQL", "CacheLayer": "Redis Cluster"}
    )
    diagram = MermaidCompiler.compile(arch)

    assert "flowchart TD" in diagram
    assert "subgraph IngressTier" in diagram
    assert "subgraph ComputeTier" in diagram
    assert "subgraph MessagingTier" in diagram
    assert "subgraph DataTier" in diagram
    assert "Kafka{{\"📬 Apache Kafka Event Bus\"}}" in diagram
    assert "OrderSvc" in diagram
    assert "UserSvc" in diagram

def test_mermaid_er_diagram():
    user = EntitySpec(name="User", fields=["id UUID PRIMARY KEY", "email VARCHAR(255)"])
    order = EntitySpec(name="Order", fields=["id UUID PRIMARY KEY"], relations=["User"])
    prd = PRDExtraction(project_name="TestShop", entities=[user, order])
    arch = ArchitectureOutput()

    er = MermaidCompiler.compile_er_diagram(arch, prd)
    assert "erDiagram" in er
    assert "User ||--o{ Order" in er
    assert "User {" in er
    assert "Order {" in er

def test_sql_compiler_ddl():
    arch = ArchitectureOutput(
        tables_ddl={
            "User": ["id UUID PRIMARY KEY", "created_at TIMESTAMP"],
            "Account": ["id UUID PRIMARY KEY", "user_id UUID REFERENCES User(id)"]
        },
        indexes=["CREATE INDEX idx_account_user_id ON Account (user_id);"]
    )
    sql = SQLCompiler.compile(arch)

    assert "CREATE TABLE IF NOT EXISTS User" in sql
    assert "CREATE TABLE IF NOT EXISTS Account" in sql
    assert "REFERENCES User(id)" in sql
    assert "CREATE INDEX idx_account_user_id" in sql

def test_docker_compose_compiler():
    arch = ArchitectureOutput(
        infra_components=["Kafka{{Apache Kafka Event Bus}}"],
        data_stores={
            "PrimaryDB": "PostgreSQL",
            "CacheLayer": "Redis Cluster",
            "HighWriteStore": "ScyllaDB"
        }
    )
    compose = DockerComposeCompiler.compile(arch)

    assert "postgres:" in compose
    assert "redis:" in compose
    assert "kafka:" in compose
    assert "zookeeper:" in compose
    assert "scylladb:" in compose

def test_markdown_compiler():
    prd = PRDExtraction(project_name="PlatformX", expected_rps=2500)
    arch = ArchitectureOutput(topology="Modular Monolith")
    compiler = MarkdownCompiler()

    md = compiler.compile(
        prd=prd,
        arch=arch,
        mermaid_code="flowchart TD\n  A-->B",
        sql_ddl="CREATE TABLE Test (id UUID);",
        er_diagram="erDiagram\n  Test"
    )

    assert "# System Architecture Specification: PlatformX" in md
    assert "Modular Monolith" in md
    assert "flowchart TD" in md
    assert "CREATE TABLE Test" in md
