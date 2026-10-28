from typing import Optional
from src.state.arch_state import ArchitectureOutput
from src.state.prd_schema import PRDExtraction

class MermaidCompiler:
    @staticmethod
    def compile(arch: ArchitectureOutput) -> str:
        lines = [
            "flowchart TD",
            "    %% Edge & Ingress Tier",
            "    subgraph IngressTier [\"🌐 Ingress & Edge Tier\"]",
            "        Client([\"📱 Clients / Browsers\"])"
        ]

        has_cdn = any("CDN[" in c for c in arch.infra_components)
        has_lb = any("LB[" in c or "Load Balancer" in c for c in arch.infra_components)
        has_ws = any("WSGateway[" in c for c in arch.infra_components)

        if has_cdn:
            lines.append("        CDN[\"🌍 Global CDN & WAF Edge\"]")
            lines.append("        Client -->|HTTPS| CDN")
            edge_entry = "CDN"
        else:
            edge_entry = "Client"

        lines.append("        API_Gateway[\"🚪 API Gateway / Reverse Proxy\"]")
        lines.append(f"        {edge_entry} -->|HTTPS / REST / gRPC| API_Gateway")

        if has_lb:
            lines.append("        LB[\"⚖️ Layer-7 Load Balancer\"]")
            lines.append("        API_Gateway --> LB")
            upstream = "LB"
        else:
            upstream = "API_Gateway"

        if has_ws:
            lines.append("        WSGateway[\"⚡ WebSocket Gateway\"]")
            lines.append("        Client <-->|WSS Realtime Stream| WSGateway")

        lines.append("    end")
        lines.append("")

        # Compute Tier
        lines.append("    %% Compute Services Tier")
        lines.append("    subgraph ComputeTier [\"⚙️ Application & Service Layer\"]")
        for node in arch.compute_nodes:
            # extract clean name and label
            node_clean = node.replace("[", "[\"").replace("]", "\"]")
            lines.append(f"        {node_clean}")
        lines.append("    end")
        lines.append("")

        # Messaging Tier
        has_kafka = any("Kafka" in c for c in arch.infra_components)
        if has_kafka:
            lines.append("    %% Messaging Tier")
            lines.append("    subgraph MessagingTier [\"📨 Event Streaming & Decoupling\"]")
            lines.append("        Kafka{{\"📬 Apache Kafka Event Bus\"}}")
            lines.append("    end")
            lines.append("")

        # Data Tier
        lines.append("    %% Data Persistence & Cache Tier")
        lines.append("    subgraph DataTier [\"💾 Storage & Caching Layer\"]")
        if "CacheLayer" in arch.data_stores:
            lines.append("        Redis[(\"⚡ Redis Cluster (Cache & Sessions)\")]")
        lines.append("        PrimaryDB[(\"🗄️ PostgreSQL (Primary DB)\")]")
        if "HighWriteStore" in arch.data_stores:
            lines.append("        Scylla[(\"📊 ScyllaDB (High-Throughput Store)\")]")
        lines.append("    end")
        lines.append("")

        # Interconnections
        lines.append("    %% Topology Interconnections")
        for node in arch.compute_nodes:
            node_id = node.split("[")[0]
            lines.append(f"    {upstream} --> {node_id}")

            if has_ws:
                lines.append(f"    WSGateway -.-> {node_id}")

            if "CacheLayer" in arch.data_stores:
                lines.append(f"    {node_id} -->|Read/Write Cache| Redis")

            lines.append(f"    {node_id} -->|Relational Data| PrimaryDB")

            if "HighWriteStore" in arch.data_stores:
                lines.append(f"    {node_id} -->|High-Volume Writes| Scylla")

            if has_kafka:
                lines.append(f"    {node_id} -.->|Publish / Subscribe| Kafka")

        return "\n".join(lines)

    @staticmethod
    def compile_er_diagram(arch: ArchitectureOutput, prd: Optional[PRDExtraction] = None) -> str:
        """Generates a Mermaid erDiagram showing entities and foreign key links."""
        lines = ["erDiagram"]

        if prd and prd.entities:
            for ent in prd.entities:
                for target in ent.relations:
                    lines.append(f"    {target} ||--o{{ {ent.name} : \"has / references\"")

                lines.append(f"    {ent.name} {{")
                for col in ent.fields:
                    col_parts = col.split()
                    col_name = col_parts[0]
                    col_type = col_parts[1] if len(col_parts) > 1 else "string"
                    # clean up types for Mermaid ER syntax
                    col_type_clean = col_type.replace("(", "_").replace(")", "").replace(",", "_")
                    lines.append(f"        {col_type_clean} {col_name}")
                lines.append("    }")
        else:
            for table_name, cols in arch.tables_ddl.items():
                lines.append(f"    {table_name} {{")
                for col in cols:
                    parts = col.split()
                    c_name = parts[0]
                    c_type = parts[1] if len(parts) > 1 else "string"
                    c_clean = c_type.replace("(", "_").replace(")", "").replace(",", "_")
                    lines.append(f"        {c_clean} {c_name}")
                lines.append("    }")

        return "\n".join(lines)
