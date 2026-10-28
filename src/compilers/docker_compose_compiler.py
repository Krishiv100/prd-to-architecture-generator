from src.state.arch_state import ArchitectureOutput

class DockerComposeCompiler:
    """Generates a runnable docker-compose.yml matching the architectural services."""

    @staticmethod
    def compile(arch: ArchitectureOutput) -> str:
        services = {}

        # 1. Primary PostgreSQL
        services["postgres"] = {
            "image": "postgres:16-alpine",
            "container_name": "app-postgres",
            "environment": [
                "POSTGRES_USER=postgres",
                "POSTGRES_PASSWORD=postgres",
                "POSTGRES_DB=app_db"
            ],
            "ports": ["5432:5432"],
            "volumes": ["postgres_data:/var/lib/postgresql/data"],
            "healthcheck": {
                "test": ["CMD-SHELL", "pg_isready -U postgres"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5
            }
        }

        # 2. Redis Cache Layer
        if "CacheLayer" in arch.data_stores:
            services["redis"] = {
                "image": "redis:7-alpine",
                "container_name": "app-redis",
                "command": "redis-server --appendonly yes",
                "ports": ["6379:6379"],
                "volumes": ["redis_data:/data"]
            }

        # 3. Kafka & Zookeeper Event Bus
        has_kafka = any("Kafka" in c for c in arch.infra_components)
        if has_kafka:
            services["zookeeper"] = {
                "image": "confluentinc/cp-zookeeper:7.5.0",
                "container_name": "app-zookeeper",
                "environment": [
                    "ZOOKEEPER_CLIENT_PORT=2181",
                    "ZOOKEEPER_TICK_TIME=2000"
                ],
                "ports": ["2181:2181"]
            }
            services["kafka"] = {
                "image": "confluentinc/cp-kafka:7.5.0",
                "container_name": "app-kafka",
                "depends_on": ["zookeeper"],
                "ports": ["9092:9092"],
                "environment": [
                    "KAFKA_BROKER_ID=1",
                    "KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181",
                    "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT",
                    "KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092",
                    "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1"
                ]
            }

        # 4. ScyllaDB High-Throughput Store
        if "HighWriteStore" in arch.data_stores:
            services["scylladb"] = {
                "image": "scylladb/scylla:5.2",
                "container_name": "app-scylla",
                "ports": ["9042:9042"],
                "volumes": ["scylla_data:/var/lib/scylla"]
            }

        # Build YAML output
        lines = [
            "# Auto-Generated docker-compose.yml",
            "# Configured by Multi-Agent PRD-to-Architecture Generator",
            "version: '3.8'",
            "",
            "services:"
        ]

        for s_name, cfg in services.items():
            lines.append(f"  {s_name}:")
            lines.append(f"    image: {cfg['image']}")
            lines.append(f"    container_name: {cfg['container_name']}")
            if "command" in cfg:
                lines.append(f"    command: {cfg['command']}")
            if "depends_on" in cfg:
                lines.append("    depends_on:")
                for d in cfg["depends_on"]:
                    lines.append(f"      - {d}")
            if "environment" in cfg:
                lines.append("    environment:")
                for env in cfg["environment"]:
                    lines.append(f"      - {env}")
            if "ports" in cfg:
                lines.append("    ports:")
                for p in cfg["ports"]:
                    lines.append(f"      - \"{p}\"")
            if "volumes" in cfg:
                lines.append("    volumes:")
                for v in cfg["volumes"]:
                    lines.append(f"      - {v}")
            if "healthcheck" in cfg:
                lines.append("    healthcheck:")
                test_str = ", ".join(f'"{t}"' for t in cfg["healthcheck"]["test"])
                lines.append(f"      test: [{test_str}]")
                lines.append(f"      interval: {cfg['healthcheck']['interval']}")
                lines.append(f"      timeout: {cfg['healthcheck']['timeout']}")
                lines.append(f"      retries: {cfg['healthcheck']['retries']}")
            lines.append("")

        lines.append("volumes:")
        lines.append("  postgres_data:")
        if "CacheLayer" in arch.data_stores:
            lines.append("  redis_data:")
        if "HighWriteStore" in arch.data_stores:
            lines.append("  scylla_data:")

        return "\n".join(lines)
