# E-Commerce Flash Sale & Inventory Platform

High-velocity e-commerce flash sale platform managing inventory locking, shopping carts, and immediate payment processing.

## Functional Entities
- Entity: Customer (email, tier, phone)
- Entity: Product (sku, title, base_price, stock_quantity)
- Entity: InventoryReservation (reserved_until, lock_token) -> Product, Customer
- Entity: Cart (session_id, expires_at) -> Customer
- Entity: OrderItem (quantity, unit_price) -> Cart, Product
- Entity: Payment (amount, currency, status, gateway_txn_id) -> Cart, Customer

## Non-Functional Requirements
- Throughput: 28000 req/s
- Latency: 15 ms
- Availability: 99.999%
- Compliance: PCI-DSS, PII, SOC2
- Features: Realtime stock decrement notifications and countdown stream via websocket
