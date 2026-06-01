# ADR-0017: Focused Traceability Re-Review Passed

Date: 2026-06-01
Status: Accepted
Source: Traceability and Quality-Control focused re-review report

## Decision

The revised Stage 04 migration candidate passes focused trace/evidence/quality review. No mandatory traceability corrections remain.

Accepted from traceability perspective:

- reassessment previous/current snapshot lineage
- Priority A compound index alignment between ORM and migration
- trace_events.parent_event_id self-reference
- trace_events.source_record_type and source_record_id
- nullable recommendations.evidence_chain_id with MVP service-layer fallback through trace_id plus evidence_refs_json
- compact enum DB type names as non-blocking
- single baseline revision under empty-schema or explicit baseline assumption

## Non-Blocking Follow-Ups

- Add trace_events(source_record_type, source_record_id) index later if source-record lookup becomes frequent.
- Add check/application validation that previous_snapshot_id != current_snapshot_id.
- Document evidence_chain_id fallback invariant in service/API layer.

## Consequences

Migration apply can enter main-controller approval execution, limited to the current development database and only after backend preflight confirms the expected database state.

Backend Docker startup, Nginx enablement, model-service startup, diagnosis logic, model training, automatic real-time training, and .pth file operations remain out of scope.
