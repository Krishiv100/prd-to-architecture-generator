import re
from typing import Dict, List, Optional, Set
from src.state.prd_schema import PRDExtraction, EntitySpec

# Curated domain entities dictionary for semantic text discovery
KNOWN_DOMAIN_ENTITIES = {
    # Identity & Access
    "user": "User", "account": "Account", "customer": "Customer", "admin": "Admin",
    "member": "Member", "profile": "Profile", "session": "Session", "organization": "Organization",
    # Transport & Delivery
    "rider": "Rider", "driver": "Driver", "trip": "Trip", "ride": "Ride",
    "vehicle": "Vehicle", "car": "Vehicle", "location": "Location", "route": "Route",
    "fleet": "Fleet", "shipment": "Shipment", "package": "Package", "delivery": "Delivery",
    # E-Commerce & Retail
    "product": "Product", "item": "Item", "order": "Order", "cart": "Cart",
    "inventory": "Inventory", "checkout": "Checkout", "merchant": "Merchant", "catalog": "Catalog",
    # Financial & Payments
    "payment": "Payment", "transaction": "Transaction", "invoice": "Invoice",
    "wallet": "Wallet", "payout": "Payout", "auditlog": "AuditLog", "ledger": "Ledger",
    # Social & Content
    "post": "Post", "tweet": "Tweet", "comment": "Comment", "like": "Like",
    "message": "Message", "chat": "Chat", "notification": "Notification", "feed": "Feed",
    "review": "Review", "rating": "Rating", "article": "Article",
    # Healthcare
    "patient": "Patient", "doctor": "Doctor", "appointment": "Appointment",
    "prescription": "Prescription", "medicalrecord": "MedicalRecord", "record": "MedicalRecord",
    # IoT & Monitoring
    "device": "Device", "sensor": "Sensor", "reading": "SensorReading", "alert": "AlertIncident",
    "telemetry": "SensorReading", "metric": "MetricReading",
    # Project & Productivity
    "project": "Project", "task": "Task", "ticket": "Ticket", "document": "Document"
}

# Common generic words to exclude from auto-detected entities
STOP_NOUNS = {
    "system", "platform", "service", "application", "app", "api", "backend",
    "frontend", "database", "server", "architecture", "requirement", "requirements",
    "nfr", "nfrs", "feature", "features", "scale", "throughput", "latency",
    "availability", "compliance", "standard", "standards", "data", "information",
    "engine", "solution", "framework", "overview", "summary", "spec", "specification",
    "entity", "entities", "model", "models", "table", "tables", "user story", "user stories"
}

class RequirementAnalyzerAgent:
    """Parses structured, semi-structured, or completely unstructured natural language PRDs
    into a validated PRDExtraction state."""

    def _infer_fields_for_entity(self, name: str) -> List[str]:
        """Provides contextually rich default fields based on entity semantics."""
        base = ["id UUID PRIMARY KEY", "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"]
        n_low = name.lower()

        if any(w in n_low for w in ["user", "customer", "rider", "driver", "doctor", "patient"]):
            return base + [
                "email VARCHAR(255) UNIQUE NOT NULL",
                "full_name VARCHAR(255) NOT NULL",
                "status VARCHAR(50) DEFAULT 'ACTIVE'"
            ]
        elif any(w in n_low for w in ["payment", "transaction", "invoice", "payout"]):
            return base + [
                "amount NUMERIC(12, 2) NOT NULL",
                "currency VARCHAR(10) DEFAULT 'USD'",
                "status VARCHAR(50) NOT NULL",
                "provider_txn_id VARCHAR(255)"
            ]
        elif any(w in n_low for w in ["order", "trip", "ride", "checkout", "shipment"]):
            return base + [
                "status VARCHAR(50) NOT NULL",
                "total_amount NUMERIC(12, 2) NOT NULL"
            ]
        elif any(w in n_low for w in ["product", "item", "inventory"]):
            return base + [
                "name VARCHAR(255) NOT NULL",
                "price NUMERIC(12, 2) NOT NULL",
                "sku VARCHAR(100) UNIQUE",
                "stock_quantity INT DEFAULT 0"
            ]
        elif any(w in n_low for w in ["message", "comment", "post", "tweet"]):
            return base + [
                "content TEXT NOT NULL",
                "status VARCHAR(50) DEFAULT 'PUBLISHED'"
            ]
        elif any(w in n_low for w in ["device", "sensor", "reading", "metric"]):
            return base + [
                "metric_name VARCHAR(100) NOT NULL",
                "metric_value DOUBLE PRECISION NOT NULL"
            ]
        elif any(w in n_low for w in ["appointment", "booking"]):
            return base + [
                "scheduled_time TIMESTAMP NOT NULL",
                "status VARCHAR(50) DEFAULT 'PENDING'"
            ]
        elif any(w in n_low for w in ["audit", "log"]):
            return base + [
                "action VARCHAR(100) NOT NULL",
                "details JSONB"
            ]
        else:
            return base + ["status VARCHAR(50) DEFAULT 'ACTIVE'"]

    def _infer_relationships(self, entities: Dict[str, EntitySpec], raw_text: str) -> None:
        """Discovers domain relationships between entities based on text hints and known patterns."""
        names = set(entities.keys())

        # 1. Textual preposition hints: "X belongs to Y", "X for Y", "X references Y", "X of Y"
        for name, spec in entities.items():
            for other in names:
                if other == name:
                    continue
                pattern = rf"\b{re.escape(name)}s?\s+(?:belongs to|references|placed by|submitted by|associated with|has|for|of)\s+{re.escape(other)}s?\b"
                if re.search(pattern, raw_text, re.IGNORECASE):
                    if other not in spec.relations:
                        spec.relations.append(other)

        # 2. Semantic domain graph heuristics if explicit relations are omitted
        relationship_heuristics = [
            ("Payment", ["Order", "Trip", "Ride", "Invoice", "User", "Account"]),
            ("Order", ["User", "Customer"]),
            ("OrderItem", ["Order", "Product"]),
            ("Trip", ["Driver", "Rider", "Vehicle", "User"]),
            ("Ride", ["Driver", "Rider", "Vehicle", "User"]),
            ("Rating", ["Driver", "Rider", "Product", "User"]),
            ("Review", ["Product", "Driver", "User"]),
            ("Cart", ["User", "Customer"]),
            ("InventoryReservation", ["Product", "Order"]),
            ("AuditLog", ["Payment", "Order", "User"]),
            ("Appointment", ["Patient", "Doctor"]),
            ("MedicalRecord", ["Patient", "Doctor"]),
            ("Prescription", ["MedicalRecord", "Patient", "Doctor"]),
            ("Comment", ["Post", "Tweet", "Article", "User"]),
            ("Like", ["Post", "Tweet", "Comment", "User"]),
            ("SensorReading", ["Device", "Sensor"]),
            ("AlertIncident", ["Device", "Fleet"]),
            ("Account", ["User", "Customer"])
        ]

        for child, potential_parents in relationship_heuristics:
            if child in entities:
                for parent in potential_parents:
                    if parent in entities and parent not in entities[child].relations:
                        entities[child].relations.append(parent)

    def analyze(self, raw_prd: str) -> PRDExtraction:
        raw_clean = raw_prd.strip()

        # 1. Project Title Extraction
        title_match = re.search(r"^\s*#\s+([^\n#]+)$", raw_clean, re.MULTILINE)
        if not title_match:
            title_match = re.search(r"(?:Title|Project|Application|System):\s*([^\n]+)", raw_clean, re.IGNORECASE)

        if title_match:
            project_name = title_match.group(1).strip()
        else:
            first_line = raw_clean.splitlines()[0].strip() if raw_clean else ""
            if first_line and len(first_line) < 60 and not first_line.endswith("."):
                project_name = first_line.replace("#", "").strip()
            else:
                project_name = "DistributedSystemArchitecture"

        # 2. Extract Description/Summary
        desc_match = re.search(r"^\s*#\s+.+\n\n([^#\n]+(?:\n[^\n#]+)*)", raw_clean, re.MULTILINE)
        description = desc_match.group(1).strip() if desc_match else f"{project_name} Architecture Specification"

        # 3. Entity Extraction
        entity_map: Dict[str, EntitySpec] = {}

        # Pass A: Explicit Syntax -> Entity: Name [(fields)] [-> Target1, Target2]
        entity_pattern = re.compile(
            r"Entity:\s*([A-Za-z0-9_]+)(?:\s*\(([^)]+)\))?(?:\s*->\s*([A-Za-z0-9_,\s]+))?",
            re.IGNORECASE
        )
        for match in entity_pattern.finditer(raw_clean):
            name = match.group(1).strip()
            custom_fields_raw = match.group(2)
            targets_raw = match.group(3)
            targets = [t.strip() for t in targets_raw.split(",") if t.strip()] if targets_raw else []

            default_fields = ["id UUID PRIMARY KEY", "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"]
            if custom_fields_raw:
                extracted_fields = []
                for f in custom_fields_raw.split(","):
                    f = f.strip()
                    if f:
                        if " " in f:
                            extracted_fields.append(f)
                        elif "id" in f.lower() and f.lower() != "id":
                            extracted_fields.append(f"{f} UUID")
                        elif "email" in f.lower():
                            extracted_fields.append(f"{f} VARCHAR(255) UNIQUE NOT NULL")
                        elif "amount" in f.lower() or "price" in f.lower():
                            extracted_fields.append(f"{f} NUMERIC(12, 2) NOT NULL")
                        elif "status" in f.lower() or "state" in f.lower():
                            extracted_fields.append(f"{f} VARCHAR(50) NOT NULL")
                        else:
                            extracted_fields.append(f"{f} VARCHAR(255)")
                fields = default_fields + [f for f in extracted_fields if not f.startswith("id ")]
            else:
                fields = default_fields

            entity_map[name] = EntitySpec(name=name, fields=fields, relations=targets)

        # Pass B: Bullet lists like "- User -> Account" or "- User: email, name"
        if len(entity_map) < 2:
            bullet_matches = re.finditer(r"^\s*[-*•]\s*(?:Entity:\s*)?([A-Z][a-zA-Z0-9_]+)(?:\s*\(([^)]+)\))?(?:\s*(?:->|belongs to|references)\s*([A-Za-z0-9_,\s]+))?", raw_clean, re.MULTILINE)
            for bm in bullet_matches:
                b_name = bm.group(1).strip()
                if b_name.lower() in STOP_NOUNS:
                    continue
                targets = [t.strip() for t in bm.group(3).split(",") if t.strip()] if bm.group(3) else []
                if b_name not in entity_map:
                    entity_map[b_name] = EntitySpec(
                        name=b_name,
                        fields=self._infer_fields_for_entity(b_name),
                        relations=targets
                    )

        # Pass C: Unstructured / Natural Text Domain Keyword Extraction
        # ONLY activated when no explicit 'Entity:' declarations were present in the document
        if not entity_map:
            words = re.findall(r"\b[A-Za-z0-9_]+\b", raw_clean)
            found_semantic_entities: Set[str] = set()

            for w in words:
                w_norm = w.lower()
                # check singular form
                if w_norm in KNOWN_DOMAIN_ENTITIES:
                    found_semantic_entities.add(KNOWN_DOMAIN_ENTITIES[w_norm])
                # check plural form (e.g. users, drivers, orders, items)
                elif w_norm.endswith("s") and w_norm[:-1] in KNOWN_DOMAIN_ENTITIES:
                    found_semantic_entities.add(KNOWN_DOMAIN_ENTITIES[w_norm[:-1]])
                elif w_norm.endswith("ies") and (w_norm[:-3] + "y") in KNOWN_DOMAIN_ENTITIES:
                    found_semantic_entities.add(KNOWN_DOMAIN_ENTITIES[w_norm[:-3] + "y"])

            for canonical_name in found_semantic_entities:
                if canonical_name not in entity_map and canonical_name.lower() not in STOP_NOUNS:
                    entity_map[canonical_name] = EntitySpec(
                        name=canonical_name,
                        fields=self._infer_fields_for_entity(canonical_name),
                        relations=[]
                    )

        # Pass D: Fallback if still minimal entities (< 2)
        if len(entity_map) < 2:
            capitalized_words = re.findall(r"\b([A-Z][a-z0-9]{2,15})\b", raw_clean)
            for cw in capitalized_words:
                if cw.lower() not in STOP_NOUNS and cw not in entity_map and len(entity_map) < 6:
                    entity_map[cw] = EntitySpec(
                        name=cw,
                        fields=self._infer_fields_for_entity(cw),
                        relations=[]
                    )

        # Fallback safeguard: guarantee at least Core entities
        if not entity_map:
            entity_map["User"] = EntitySpec(name="User", fields=self._infer_fields_for_entity("User"))
            entity_map["Resource"] = EntitySpec(name="Resource", fields=self._infer_fields_for_entity("Resource"), relations=["User"])

        # Infer relationships across detected entities
        self._infer_relationships(entity_map, raw_clean)

        # 4. Numerical NFR Extraction
        # Throughput
        rps = 1000  # default baseline
        
        # Check pattern: 30k rps / 30,000 req/s / 25k requests per second
        rps_match = re.search(
            r"([\d,]+(?:\.\d+)?)\s*(k|m|million|thousand)?\s*(?:req/s|rps|qps|requests?\s+per\s+second|concurrent\s+requests?)",
            raw_clean,
            re.IGNORECASE
        )
        if not rps_match:
            # Check pattern: Throughput: 30k / Load: 15000 / Scale: 20k
            rps_match = re.search(
                r"(?:throughput|scale|rps|qps|load|traffic)\s*(?:is|of|at|around|exceeding|targeting|[:<~=])?\s*([\d,]+(?:\.\d+)?)\s*(k|m|million|thousand)?",
                raw_clean,
                re.IGNORECASE
            )

        if rps_match:
            num_str = rps_match.group(1).replace(",", "")
            unit = rps_match.group(2).lower() if rps_match.group(2) else ""
            multiplier = 1000 if unit in ["k", "thousand"] else (1000000 if unit in ["m", "million"] else 1)
            try:
                val = int(float(num_str) * multiplier)
                if val > 0:
                    rps = val
            except Exception:
                pass

        # Latency
        latency = 100  # default baseline
        lat_match = re.search(
            r"(?:latency\s*(?:is|under|below|of|budget|[:<~=])?\s*(\d+)\s*(?:ms|milliseconds)|(?:sub\s*|under\s*|<|p99\s*|latency\s*)?(\d+)\s*ms)",
            raw_clean,
            re.IGNORECASE
        )
        if lat_match:
            val_str = lat_match.group(1) if lat_match.group(1) else lat_match.group(2)
            if val_str:
                latency = int(val_str)
        elif re.search(r"\b(sub-50ms|sub-millisecond|ultra-low latency|instant)\b", raw_clean, re.IGNORECASE):
            latency = 25

        # Availability SLA
        sla = "99.9%"  # default
        sla_match = re.search(r"\b(99\.\d+%)", raw_clean)
        if sla_match:
            sla = sla_match.group(1)
        elif re.search(r"\b(four nines|high availability|ha|zero downtime|critical)\b", raw_clean, re.IGNORECASE):
            sla = "99.99%"
        elif re.search(r"\b(five nines)\b", raw_clean, re.IGNORECASE):
            sla = "99.999%"

        # 5. Compliance Frameworks
        compliance: List[str] = []
        all_standards = ["PII", "PCI-DSS", "HIPAA", "SOC2", "GDPR", "ISO27001", "FERPA"]
        for tag in all_standards:
            if re.search(rf"\b{re.escape(tag)}\b", raw_clean, re.IGNORECASE):
                compliance.append(tag)

        # Contextual compliance heuristics
        if any(w in raw_clean.lower() for w in ["credit card", "pci", "cardholder", "stripe", "payment processing", "checkout"]):
            if "PCI-DSS" not in compliance:
                compliance.append("PCI-DSS")
            if "PII" not in compliance:
                compliance.append("PII")

        if any(w in raw_clean.lower() for w in ["patient", "doctor", "health", "ehr", "medical", "phi", "telehealth"]):
            if "HIPAA" not in compliance:
                compliance.append("HIPAA")
            if "PII" not in compliance:
                compliance.append("PII")

        if any(w in raw_clean.lower() for w in ["gdpr", "personal data", "right to erasure", "privacy", "consent"]):
            if "GDPR" not in compliance:
                compliance.append("GDPR")
            if "PII" not in compliance:
                compliance.append("PII")

        if any(w in raw_clean.lower() for w in ["soc2", "soc 2", "audit log", "siem", "least privilege", "rbac"]):
            if "SOC2" not in compliance:
                compliance.append("SOC2")

        # 6. Realtime / Streaming Indicator
        realtime = bool(re.search(
            r"\b(websocket|websockets|realtime|real-time|sse|stream|streaming|live|pubsub|telemetry|gps|location tracking|chat|instant updates|push notifications)\b",
            raw_clean,
            re.IGNORECASE
        ))

        return PRDExtraction(
            project_name=project_name,
            description=description,
            entities=list(entity_map.values()),
            expected_rps=rps,
            max_latency_ms=latency,
            availability_sla=sla,
            compliance=compliance,
            realtime_features=realtime,
        )
