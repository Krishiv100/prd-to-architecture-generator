# FinTech Checkout & Ledger Platform

## Functional Entities
- Entity: User
- Entity: Account -> User
- Entity: Order -> User
- Entity: Payment -> Order, Account
- Entity: AuditLog -> Payment, User

## Non-Functional Requirements
- Throughput: 12000 req/s
- Latency: 25 ms
- Availability: 99.99%
- Compliance: PII, PCI-DSS, SOC2
- Features: Support realtime payment status notifications via websocket