from typing import Dict, Any
from src.state.prd_schema import PRDExtraction
from src.state.arch_state import ArchitectureOutput

class CapacityEstimator:
    """Calculates quantitative infrastructure sizing, bandwidth, memory,
    storage growth, and monthly cloud cost estimation."""

    @staticmethod
    def estimate(prd: PRDExtraction, arch: ArchitectureOutput) -> Dict[str, Any]:
        rps = max(prd.expected_rps, 100)
        num_entities = max(len(prd.entities), 2)

        # 1. Traffic Breakdown
        read_ratio = 0.80 if "HighWriteStore" not in arch.data_stores else 0.65
        write_ratio = 1.0 - read_ratio
        read_qps = int(rps * read_ratio)
        write_qps = int(rps * write_ratio)

        # 2. Network Bandwidth (assuming 2.5 KB avg payload)
        avg_payload_kb = 2.5
        network_mbps = round((rps * avg_payload_kb * 8) / 1024, 1)  # Megabits per second
        bandwidth_gb_day = round((rps * avg_payload_kb * 86400) / (1024 * 1024), 2)

        # 3. Storage Growth Rate
        # avg row size 0.8 KB * write QPS * 86400
        daily_storage_gb = round((write_qps * 0.8 * 86400) / (1024 * 1024), 2)
        monthly_storage_gb = round(daily_storage_gb * 30, 1)

        # 4. Compute Pod / Instance Sizing
        # 1 container pod (1 vCPU, 2GB RAM) handles ~1,500 RPS comfortably
        pods_needed = max(2, int(rps / 1200) + 1)
        # Redundancy multiplier for 99.99% SLA
        if prd.availability_sla in ["99.99%", "99.999%"]:
            pods_needed = max(4, int(pods_needed * 1.5))

        # 5. Database Sizing
        if rps >= 10000:
            db_tier = "db.r6g.4xlarge (16 vCPU, 128 GB RAM) Multi-AZ + Read Replicas"
            cache_nodes = "Redis Cluster (3 Primary + 3 Replicas, cache.r6g.xlarge)"
            base_monthly_cost = 2400
        elif rps >= 3000:
            db_tier = "db.r6g.xlarge (4 vCPU, 32 GB RAM) Multi-AZ"
            cache_nodes = "Redis Cluster (2 Nodes, cache.t4g.medium)"
            base_monthly_cost = 780
        else:
            db_tier = "db.t4g.large (2 vCPU, 8 GB RAM) Single Primary"
            cache_nodes = "Redis Standalone / In-Memory Tier" if "CacheLayer" in arch.data_stores else "None (Direct DB)"
            base_monthly_cost = 190

        # Adjust cost based on compute pods and extra stores
        compute_cost = pods_needed * 45  # ~$45/pod/mo on EKS/GKE
        storage_cost = int(monthly_storage_gb * 0.12)
        scylla_cost = 450 if "HighWriteStore" in arch.data_stores else 0
        kafka_cost = 350 if any("Kafka" in c for c in arch.infra_components) else 0

        estimated_monthly_min = base_monthly_cost + compute_cost + scylla_cost + kafka_cost
        estimated_monthly_max = int(estimated_monthly_min * 1.35)

        return {
            "peak_rps": rps,
            "read_qps": read_qps,
            "write_qps": write_qps,
            "network_mbps": network_mbps,
            "daily_bandwidth_gb": bandwidth_gb_day,
            "daily_storage_gb": daily_storage_gb,
            "monthly_storage_gb": monthly_storage_gb,
            "recommended_pods": pods_needed,
            "pod_spec": f"{pods_needed}x Application Pods (2 vCPU, 4GB RAM)",
            "primary_db_tier": db_tier,
            "cache_tier": cache_nodes,
            "estimated_cost_range": f"${estimated_monthly_min:,} - ${estimated_monthly_max:,} / month",
            "cost_min": estimated_monthly_min,
            "cost_max": estimated_monthly_max
        }
