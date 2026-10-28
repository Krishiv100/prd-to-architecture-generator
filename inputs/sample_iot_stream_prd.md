# IoT Fleet Telemetry & Anomaly Ingestion

Industrial IoT edge-gateway ingestion platform collecting sensor telemetry across global vehicle fleets.

## Functional Entities
- Entity: Fleet (name, region, operational_status)
- Entity: Device (serial_number, firmware_version, ip_address) -> Fleet
- Entity: SensorReading (metric_type, metric_value, timestamp_epoch) -> Device
- Entity: AlertIncident (severity_level, triggered_rule, acknowledged) -> Device, Fleet

## Non-Functional Requirements
- Throughput: 65000 req/s
- Latency: 10 ms
- Availability: 99.99%
- Compliance: SOC2, ISO27001
- Features: Realtime pubsub streaming telemetry metrics
