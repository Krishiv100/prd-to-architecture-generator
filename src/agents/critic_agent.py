from src.agents.base_agent import BaseAgent
from src.state.prd_schema import PRDExtraction
from src.state.arch_state import ArchitectureOutput, CriticFinding

class CollaborationCriticAgent(BaseAgent):
    """Cross-verifies outputs from Architect, Database, and Security agents.
    Acts as the peer-review feedback engine, performing automated conflict resolution."""

    def process(self, prd: PRDExtraction, arch: ArchitectureOutput) -> None:
        # Check 1: Ultra-low latency without cache
        if prd.max_latency_ms <= 50 and "CacheLayer" not in arch.data_stores:
            arch.data_stores["CacheLayer"] = "Redis Cluster (Auto-Injected by Critic for Sub-50ms Latency Budget)"
            msg = f"Critic Action: Injected Redis Cluster to satisfy {prd.max_latency_ms}ms latency budget."
            arch.warnings.append(msg)
            arch.revision_log.append(msg)
            arch.findings.append(CriticFinding(
                severity="CRITICAL",
                category="Latency",
                message=f"P99 latency budget of {prd.max_latency_ms}ms cannot be satisfied without an in-memory caching tier.",
                action_taken="Auto-injected Redis Cluster into data stores and routed read paths."
            ))
            arch.revision_count += 1

        # Check 2: PCI-DSS inside a shared monolith
        has_pci = any("PCI" in c.upper() for c in prd.compliance)
        if has_pci and arch.topology == "Modular Monolith":
            msg = "Compliance Advisory: PCI-DSS scope requires isolating Payment processing into a dedicated CDE (Cardholder Data Environment) service."
            arch.warnings.append(msg)
            arch.revision_log.append(msg)
            arch.findings.append(CriticFinding(
                severity="WARNING",
                category="Compliance",
                message="Monolithic topology exposes all internal services to PCI-DSS audit perimeter.",
                action_taken="Issued PCI-DSS CDE network isolation mandate."
            ))

        # Check 3: High availability SLA check (99.99% or higher)
        if prd.availability_sla in ["99.99%", "99.999%"]:
            has_lb = any("LB[" in c or "Load Balancer" in c for c in arch.infra_components)
            if not has_lb:
                arch.infra_components.append("LB[Layer-7 Load Balancer]")
                msg = f"Critic Action: Added Redundant Layer-7 Load Balancer to meet {prd.availability_sla} Availability SLA."
                arch.warnings.append(msg)
                arch.revision_log.append(msg)
                arch.findings.append(CriticFinding(
                    severity="CRITICAL",
                    category="Availability",
                    message=f"Availability SLA of {prd.availability_sla} requires redundant active-active load balancing.",
                    action_taken="Injected Layer-7 Load Balancer into Ingress tier."
                ))
                arch.revision_count += 1

            if "Single Primary" in arch.data_stores.get("PrimaryDB", ""):
                arch.data_stores["PrimaryDB"] = "PostgreSQL (Multi-AZ Primary + Auto-Failover Read Replicas)"
                msg = f"Critic Action: Upgraded PrimaryDB to Multi-AZ with Auto-Failover for {prd.availability_sla} SLA."
                arch.warnings.append(msg)
                arch.revision_log.append(msg)
                arch.findings.append(CriticFinding(
                    severity="CRITICAL",
                    category="Availability",
                    message="Single Primary database is a Single Point of Failure (SPOF) violating 4-nines uptime.",
                    action_taken="Upgraded to Multi-AZ Primary with synchronous replication and auto-failover."
                ))
                arch.revision_count += 1

        # Check 4: High Throughput Asynchronous Decoupling (RPS >= 10,000)
        if prd.expected_rps >= 10000:
            has_kafka = any("Kafka" in c for c in arch.infra_components)
            if not has_kafka:
                arch.infra_components.append("Kafka{{Apache Kafka Event Bus}}")
                msg = f"Critic Action: Injected Apache Kafka Event Bus to decouple high write ingress ({prd.expected_rps} req/s)."
                arch.warnings.append(msg)
                arch.revision_log.append(msg)
                arch.findings.append(CriticFinding(
                    severity="CRITICAL",
                    category="Throughput",
                    message=f"Throughput load of {prd.expected_rps} req/s requires asynchronous write buffering.",
                    action_taken="Injected Apache Kafka Event Bus for backpressure and queue management."
                ))
                arch.revision_count += 1

            if "HighWriteStore" not in arch.data_stores:
                arch.data_stores["HighWriteStore"] = "ScyllaDB / Apache Cassandra (Wide-Column Distributed Ingestion Store)"
                msg = f"Critic Action: Injected ScyllaDB to handle write throughput exceeding 10,000 req/s."
                arch.warnings.append(msg)
                arch.revision_log.append(msg)
                arch.findings.append(CriticFinding(
                    severity="WARNING",
                    category="Storage",
                    message="Relational database IOPS will bottleneck under extreme write ingestion.",
                    action_taken="Added ScyllaDB wide-column store for high-throughput write path."
                ))
                arch.revision_count += 1

        # Check 5: Real-time Feature Ingress
        if prd.realtime_features:
            has_ws = any("WSGateway" in c for c in arch.infra_components)
            if not has_ws:
                arch.infra_components.append("WSGateway[WebSocket Gateway]")
                msg = "Critic Action: Injected WebSocket Gateway for real-time bidirectional streaming."
                arch.warnings.append(msg)
                arch.revision_log.append(msg)
                arch.findings.append(CriticFinding(
                    severity="INFO",
                    category="Networking",
                    message="Real-time requirements detected without dedicated WebSocket ingress router.",
                    action_taken="Added WebSocket Gateway."
                ))
                arch.revision_count += 1
