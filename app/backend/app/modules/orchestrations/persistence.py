from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    AgentInvocation,
    LlmSummary,
    OrchestrationConflict,
    OrchestrationRun,
    OrchestrationStep,
)


def now_utc() -> datetime:
    return datetime.now(UTC)


def _uuid_or_none(value: Any) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


def _uuid_required(value: Any, field_name: str) -> UUID:
    parsed = _uuid_or_none(value)
    if parsed is None:
        raise ValueError(f'{field_name}_invalid')
    return parsed


def persist_orchestration_bundle(
    db: Session,
    *,
    orchestration_run_id: str,
    trace_id: str,
    case_id: str,
    patient_id: str,
    mode: str,
    requested_task: str,
    candidate_agents: list[str],
    clinical_context_refs: dict[str, Any],
    modality_refs: dict[str, Any],
    runtime_options: dict[str, Any],
    idempotency_key: str | None,
    payload_json: dict[str, Any],
    result_json: dict[str, Any],
    steps: list[dict[str, Any]],
    invocations: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    llm_summary: dict[str, Any] | None,
    status: str,
    error_code: str | None = None,
    error_detail_json: dict[str, Any] | None = None,
    runtime_stub: bool = True,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    duration_ms: int | None = None,
) -> None:
    case_uuid = _uuid_required(case_id, 'case_id')
    patient_uuid = _uuid_required(patient_id, 'patient_id')
    run_uuid = uuid4()
    started_at = started_at or now_utc()
    completed_at = completed_at or started_at

    run = OrchestrationRun(
        id=run_uuid,
        orchestration_run_id=orchestration_run_id,
        trace_id=trace_id,
        case_id=case_uuid,
        patient_id=patient_uuid,
        mode=mode,
        status=status,
        requested_task=requested_task,
        candidate_agents_json=candidate_agents,
        clinical_context_refs_json=clinical_context_refs,
        modality_refs_json=modality_refs,
        runtime_options_json=runtime_options,
        idempotency_key=idempotency_key,
        payload_json=payload_json,
        result_json=result_json,
        runtime_stub=runtime_stub,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=duration_ms,
        error_code=error_code,
        error_detail_json=error_detail_json or {},
    )
    db.add(run)
    db.flush()

    for idx, step in enumerate(steps, start=1):
        db.add(
            OrchestrationStep(
                id=uuid4(),
                step_id=step['step_id'],
                trace_id=trace_id,
                case_id=case_uuid,
                patient_id=patient_uuid,
                orchestration_run_id=orchestration_run_id,
                parent_step_id=step.get('parent_step_id'),
                step_type=step['step_type'],
                step_name=step.get('step_name'),
                step_index=step.get('step_index', idx),
                agent_code=step.get('agent_code'),
                agent_version=step.get('agent_version'),
                model_version_id=_uuid_or_none(step.get('model_version_id')),
                status=step.get('status', 'planned'),
                payload_json=step.get('payload_json') or {},
                result_json=step.get('result_json') or {},
                runtime_stub=step.get('runtime_stub', runtime_stub),
                started_at=step.get('started_at'),
                completed_at=step.get('completed_at'),
                duration_ms=step.get('duration_ms'),
                error_code=step.get('error_code'),
                error_detail_json=step.get('error_detail_json') or {},
            )
        )

    db.flush()

    for invocation in invocations:
        db.add(
            AgentInvocation(
                id=uuid4(),
                agent_invocation_id=invocation['agent_invocation_id'],
                trace_id=trace_id,
                case_id=case_uuid,
                patient_id=patient_uuid,
                orchestration_run_id=orchestration_run_id,
                step_id=invocation['step_id'],
                agent_code=invocation['agent_code'],
                agent_version=invocation.get('agent_version'),
                endpoint_id=invocation.get('endpoint_id'),
                endpoint_url=invocation.get('endpoint_url'),
                model_version_id=_uuid_or_none(invocation.get('model_version_id')),
                status=invocation.get('status', 'pending'),
                payload_json=invocation.get('payload_json') or {},
                response_json=invocation.get('response_json') or {},
                runtime_stub=invocation.get('runtime_stub', runtime_stub),
                started_at=invocation.get('started_at'),
                completed_at=invocation.get('completed_at'),
                duration_ms=invocation.get('duration_ms'),
                error_code=invocation.get('error_code'),
                error_detail_json=invocation.get('error_detail_json') or {},
            )
        )

    db.flush()

    for conflict in conflicts:
        db.add(
            OrchestrationConflict(
                id=uuid4(),
                conflict_id=conflict['conflict_id'],
                trace_id=trace_id,
                case_id=case_uuid,
                patient_id=patient_uuid,
                orchestration_run_id=orchestration_run_id,
                step_id=conflict.get('step_id'),
                conflict_type=conflict['conflict_type'],
                status=conflict.get('status', 'stub'),
                summary_text=conflict.get('summary_text'),
                resolution_strategy=conflict.get('resolution_strategy'),
                resolution_summary=conflict.get('resolution_summary'),
                payload_json=conflict.get('payload_json') or {},
                result_json=conflict.get('result_json') or {},
                runtime_stub=conflict.get('runtime_stub', runtime_stub),
                started_at=conflict.get('started_at'),
                completed_at=conflict.get('completed_at'),
                duration_ms=conflict.get('duration_ms'),
                error_code=conflict.get('error_code'),
                error_detail_json=conflict.get('error_detail_json') or {},
            )
        )

    if llm_summary is not None:
        db.add(
            LlmSummary(
                id=uuid4(),
                summary_id=llm_summary['summary_id'],
                trace_id=trace_id,
                case_id=case_uuid,
                patient_id=patient_uuid,
                orchestration_run_id=orchestration_run_id,
                step_id=llm_summary.get('step_id'),
                agent_invocation_id=llm_summary.get('agent_invocation_id'),
                model_version_id=_uuid_or_none(llm_summary.get('model_version_id')),
                summary_type=llm_summary['summary_type'],
                status=llm_summary.get('status', 'stub'),
                summary_text=llm_summary.get('summary_text'),
                summary_json=llm_summary.get('summary_json') or {},
                payload_json=llm_summary.get('payload_json') or {},
                runtime_stub=llm_summary.get('runtime_stub', runtime_stub),
                started_at=llm_summary.get('started_at'),
                completed_at=llm_summary.get('completed_at'),
                duration_ms=llm_summary.get('duration_ms'),
                error_code=llm_summary.get('error_code'),
                error_detail_json=llm_summary.get('error_detail_json') or {},
            )
        )

    db.commit()


def get_run(db: Session, orchestration_run_id: str) -> OrchestrationRun | None:
    return db.execute(
        select(OrchestrationRun).where(OrchestrationRun.orchestration_run_id == orchestration_run_id)
    ).scalar_one_or_none()


def list_steps(db: Session, orchestration_run_id: str) -> list[OrchestrationStep]:
    return db.execute(
        select(OrchestrationStep)
        .where(OrchestrationStep.orchestration_run_id == orchestration_run_id)
        .order_by(OrchestrationStep.step_index.asc(), OrchestrationStep.started_at.asc(), OrchestrationStep.id.asc())
    ).scalars().all()


def list_invocations(db: Session, orchestration_run_id: str) -> list[AgentInvocation]:
    return db.execute(
        select(AgentInvocation)
        .where(AgentInvocation.orchestration_run_id == orchestration_run_id)
        .order_by(AgentInvocation.started_at.asc(), AgentInvocation.id.asc())
    ).scalars().all()


def list_conflicts(db: Session, orchestration_run_id: str) -> list[OrchestrationConflict]:
    return db.execute(
        select(OrchestrationConflict)
        .where(OrchestrationConflict.orchestration_run_id == orchestration_run_id)
        .order_by(OrchestrationConflict.started_at.asc(), OrchestrationConflict.id.asc())
    ).scalars().all()


def list_llm_summaries(db: Session, orchestration_run_id: str) -> list[LlmSummary]:
    return db.execute(
        select(LlmSummary)
        .where(LlmSummary.orchestration_run_id == orchestration_run_id)
        .order_by(LlmSummary.started_at.asc(), LlmSummary.id.asc())
    ).scalars().all()
