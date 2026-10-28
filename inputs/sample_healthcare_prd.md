# Healthcare Telemedicine & EHR Platform

Secure telehealth consultation platform with electronic health records (EHR), prescription management, and appointment scheduling.

## Functional Entities
- Entity: Patient (mrn, full_name, date_of_birth, emergency_contact)
- Entity: Doctor (license_number, specialty, department)
- Entity: Appointment (scheduled_time, status, video_room_url) -> Patient, Doctor
- Entity: MedicalRecord (diagnosis_codes, clinical_notes, encrypted_data) -> Patient, Doctor
- Entity: Prescription (medication_code, dosage, refills_remaining) -> MedicalRecord, Patient

## Non-Functional Requirements
- Throughput: 1800 req/s
- Latency: 90 ms
- Availability: 99.95%
- Compliance: HIPAA, PII, SOC2
- Features: Realtime patient vital signs streaming via websocket
