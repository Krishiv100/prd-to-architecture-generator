# Boutique Merchant Billing Service

Internal corporate billing and customer checkout application with strict compliance needs.

## Functional Entities
- Entity: Merchant (business_name, registration_no)
- Entity: Customer (full_name, email) -> Merchant
- Entity: BillingAccount (account_number, balance) -> Customer
- Entity: PaymentRecord (charge_amount, card_token, status) -> BillingAccount

## Non-Functional Requirements
- Throughput: 250 req/s
- Latency: 35 ms
- Availability: 99.99%
- Compliance: PCI-DSS, PII
- Features: Standard batch settlement
