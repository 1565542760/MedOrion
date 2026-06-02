
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from time import perf_counter
from types import SimpleNamespace
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.modules.agent_gateway.router import _agent_or_404, _validate_capability
from app.modules.inference.model_service_client import ModelServiceError, infer_with_model_service
from app.modules.orchestrations.persistence import (
    get_run,
    list_conflicts,
    list_invocations,
    list_llm_summaries,
    list_steps,
    now_utc,
    persist_orchestration_bundle,
)
from app.modules.orchestrations.schemas import (
    OrchestrationAgentInvocationItemV1,
    OrchestrationAgentInvocationListResponseV1,
    OrchestrationAgentInvocationV1,
    OrchestrationConflictItemV1,
    OrchestrationConflictListResponseV1,
    OrchestrationConflictV1,
    OrchestrationLlmSummaryItemV1,
    OrchestrationLlmSummaryListResponseV1,
    OrchestrationMode,
    OrchestrationRunDetailResponseV1,
    OrchestrationRunItemV1,
    OrchestrationRunRequestV1,
    OrchestrationRunResponseV1,
    OrchestrationStepItemV1,
    OrchestrationStepListResponseV1,
    OrchestrationStepStatus,
    OrchestrationStepV1,
    OrchestrationStubSummaryV1,
    OrchestrationValidatePlanRequestV1,
    OrchestrationValidatePlanResponseV1,
)

logger = logging.getLogger('app.orchestration')
router = APIRouter()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _emit_audit(message: str, *args: Any) -> None:
    rendered = message % args if args else message
    print(rendered, flush=True)
    logger.log(logging.WARNING, rendered)


class OrchestrationError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(status_code=status_code, detail={'code': code, 'message': message, 'details': details or {}})


def _request_id(request: Request) -> str:
    return getattr(request.state, 'request_id', f'req_{uuid.uuid4().hex}')


def _extract_modalities(modality_refs: dict[str, Any]) -> list[str]:
    if not modality_refs:
        return []
    modalities: list[str] = []
    for key, value in modality_refs.items():
        if isinstance(value, dict):
            candidate = value.get('modality') or value.get('modality_code') or value.get('type') or value.get('kind')
            if candidate:
                modalities.append(str(candidate))
                continue
        if isinstance(value, str):
            modalities.append(value)
            continue
        if value is True:
            modalities.append(str(key))
    if not modalities:
        modalities = [str(key) for key in modality_refs.keys()]
    return modalities


def _normalize_refs(refs: Any) -> dict[str, Any]:
    if isinstance(refs, dict):
        return refs
    if refs is None:
        return {}
    if isinstance(refs, list):
        return {'items': refs}
    return {'value': refs}


def _validate_candidate_agents(mode: OrchestrationMode, candidate_agents: list[str]) -> None:
    if not candidate_agents:
        raise OrchestrationError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code='candidate_agents_missing',
            message='candidate_agents is required',
        )
    if mode == OrchestrationMode.single_agent and len(candidate_agents) != 1:
        raise OrchestrationError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code='single_agent_requires_exactly_one_candidate',
            message='single_agent mode requires exactly one candidate agent',
            details={'candidate_agents': candidate_agents},
        )


def _ensure_supported_agents(agent_codes: list[str], requested_task: str, modalities: list[str]) -> list[Any]:
    agents: list[Any] = []
    for agent_code in agent_codes:
        agent = _agent_or_404(agent_code)
        valid, code = _validate_capability(agent, requested_task, modalities)
        if not valid:
            raise OrchestrationError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code=code or 'unsupported_agent_capability',
                message='Unsupported agent capability request',
                details={'agent_code': agent_code, 'requested_task': requested_task, 'modalities': modalities},
            )
        agents.append(agent)
    return agents


def _build_planned_steps(mode: OrchestrationMode, agents: list[Any]) -> list[OrchestrationStepV1]:
    planned: list[OrchestrationStepV1] = []
    for idx, agent in enumerate(agents, start=1):
        planned.append(
            OrchestrationStepV1(
                step_id=f'step_{uuid.uuid4().hex[:12]}',
                step_type=f'{mode.value}_step_{idx}',
                agent_code=agent.agent_code,
                status=OrchestrationStepStatus.planned,
                summary=f'Planned stub step for {agent.agent_code}',
                details={'runtime_stub': True, 'agent_status': agent.status, 'default_model_version_id': agent.default_model_version_id},
            )
        )
    if not planned:
        planned.append(
            OrchestrationStepV1(
                step_id=f'step_{uuid.uuid4().hex[:12]}',
                step_type=f'{mode.value}_step_1',
                status=OrchestrationStepStatus.planned,
                summary='Planned stub step with no candidate agents',
                details={'runtime_stub': True},
            )
        )
    return planned


def _invoke_agent_step(*, request: Request, trace_id: str, orchestration_run_id: str, step: OrchestrationStepV1, requested_task: str, patient_id: str, case_id: str, inputs: dict[str, Any], clinical_context_refs: dict[str, Any], modality_refs: dict[str, Any], runtime_options: dict[str, Any], idempotency_key: str | None, agent_invocation_id: str | None = None) -> tuple[OrchestrationStepV1, OrchestrationAgentInvocationV1, dict[str, Any]]:
    request_id = _request_id(request)
    agent_invocation_id = f'agt_{uuid.uuid4().hex[:16]}'
    start = perf_counter()
    payload = {
        'trace_id': trace_id,
        'inference_task_id': agent_invocation_id,
        'agent_invocation_id': agent_invocation_id,
        'case_id': case_id,
        'patient_id': patient_id,
        'disease_agent': step.agent_code,
        'requested_task': requested_task,
        'requested_modalities': list(modality_refs.keys()),
        'modalities': _extract_modalities(modality_refs),
        'clinical_context_refs': clinical_context_refs,
        'modality_refs': modality_refs,
        'model_version_policy': {'mode': 'latest_approved', 'pinned_version': None, 'allow_fallback_to_cpu': True, 'allow_fallback_to_rule_baseline': True, 'no_silent_fallback': True},
        'inputs': inputs,
        'missing_value_context': inputs.get('missing_value_context', {}),
        'runtime_options': {'stub': True, 'orchestration_run_id': orchestration_run_id, **runtime_options},
        'idempotency_key': idempotency_key or f'idem_{uuid.uuid4().hex[:12]}',
    }
    _emit_audit(
        'orchestration step start request_id=%s trace_id=%s orchestration_run_id=%s step_id=%s agent_code=%s status=%s duration_ms=%s',
        request_id,
        trace_id,
        orchestration_run_id,
        step.step_id,
        step.agent_code,
        step.status.value,
        0,
    )
    try:
        ms_resp = infer_with_model_service(payload, request_id=request_id, trace_id=trace_id)
    except ModelServiceError as exc:
        duration_ms = int((perf_counter() - start) * 1000)
        _emit_audit(
            'orchestration step failed request_id=%s trace_id=%s orchestration_run_id=%s step_id=%s agent_code=%s status=%s duration_ms=%s error_code=%s',
            request_id,
            trace_id,
            orchestration_run_id,
            step.step_id,
            step.agent_code,
            'failed',
            duration_ms,
            exc.code,
        )
        if exc.code in {'model_service_timeout'}:
            raise OrchestrationError(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                code='orchestration_timeout',
                message='Orchestration timed out while invoking agent backend',
                details={'backend_code': exc.code, 'agent_code': step.agent_code, 'step_id': step.step_id},
            ) from exc
        if exc.code in {'model_service_unavailable'}:
            raise OrchestrationError(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                code='agent_unavailable',
                message='Agent backend unavailable',
                details={'backend_code': exc.code, 'agent_code': step.agent_code, 'step_id': step.step_id},
            ) from exc
        raise OrchestrationError(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details={'backend_code': exc.code, 'agent_code': step.agent_code, 'step_id': step.step_id, **(exc.details or {})},
        ) from exc

    duration_ms = int((perf_counter() - start) * 1000)
    step = step.model_copy(update={
        'status': OrchestrationStepStatus.completed,
        'duration_ms': duration_ms,
        'agent_invocation_id': agent_invocation_id,
        'model_invocation_id': ms_resp.get('model_invocation_id'),
        'summary': f'Agent {step.agent_code} completed stub orchestration step',
        'details': {'runtime_stub': True, 'model_version_id': ms_resp.get('model_version_id'), 'status': ms_resp.get('status')},
    })
    invocation = OrchestrationAgentInvocationV1(
        step_id=step.step_id,
        agent_code=step.agent_code or 'unknown_agent',
        agent_invocation_id=agent_invocation_id,
        status='succeeded',
        duration_ms=duration_ms,
        model_service_response=ms_resp,
    )
    _emit_audit(
        'orchestration step success request_id=%s trace_id=%s orchestration_run_id=%s step_id=%s agent_code=%s status=%s duration_ms=%s agent_invocation_id=%s',
        request_id,
        trace_id,
        orchestration_run_id,
        step.step_id,
        step.agent_code,
        step.status.value,
        duration_ms,
        agent_invocation_id,
    )
    return step, invocation, ms_resp


def _build_stub_summary(mode: OrchestrationMode, trace_id: str, requested_task: str, agents: list[str], model_service_responses: list[dict[str, Any]], failure_count: int = 0) -> tuple[OrchestrationStubSummaryV1, OrchestrationStubSummaryV1, list[OrchestrationConflictV1]]:
    summary = OrchestrationStubSummaryV1(
        title='Stub orchestration summary',
        body=f'Runtime stub orchestration completed in {mode.value} mode for trace {trace_id}.',
        rationale=[f'requested_task={requested_task}', f'candidate_agents={agents}', 'no schema persistence in this stage'],
    )
    recommendation = OrchestrationStubSummaryV1(
        title='Stub recommendation',
        body='Use the returned model-service response as a placeholder for downstream review; no real clinical recommendation is issued.',
        rationale=[
            'runtime_stub=true',
            f'model_service_responses={len(model_service_responses)}',
            f'failure_count={failure_count}',
            'no silent fallback',
        ],
    )
    conflicts: list[OrchestrationConflictV1] = []
    if len(model_service_responses) > 1:
        conflicts.append(
            OrchestrationConflictV1(
                conflict_id=f'conf_{uuid.uuid4().hex[:12]}',
                agents=agents,
                reason='stub conflict-aware summary not yet computing semantic conflicts',
                resolution='stub_summary_only',
                status='stub',
            )
        )
    return summary, recommendation, conflicts



def _build_stub_agent(agent_code: str) -> Any:
    return SimpleNamespace(
        agent_code=agent_code,
        status='stub_active',
        default_model_version_id=None,
        endpoint_id='model-service',
        endpoint_url='http://model-service:8100',
        health_url='http://model-service:8100/health',
        contract_version='stage35-agent-contract-v1',
    )


def _runtime_model_version(agent: Any, ms_resp: dict[str, Any] | None = None) -> str | None:
    candidate = None
    if ms_resp is not None:
        candidate = ms_resp.get('model_version_id')
    if candidate is None:
        candidate = getattr(agent, 'default_model_version_id', None)
    return str(candidate) if candidate is not None else None


def _failure_detail(exc: Exception) -> tuple[int, str, dict[str, Any], str]:
    if isinstance(exc, OrchestrationError):
        detail = exc.detail if isinstance(exc.detail, dict) else {'code': 'orchestration_failed', 'message': str(exc.detail)}
        code = detail.get('code', 'orchestration_failed')
        message = detail.get('message', 'Orchestration failed')
        return exc.status_code, code, detail, message
    if isinstance(exc, HTTPException):
        detail = exc.detail if isinstance(exc.detail, dict) else {'code': 'http_error', 'message': str(exc.detail)}
        code = detail.get('code', 'http_error')
        message = detail.get('message', 'HTTP error')
        return exc.status_code, code, detail, message
    detail = {'code': 'orchestration_internal_error', 'message': str(exc)}
    return status.HTTP_500_INTERNAL_SERVER_ERROR, 'orchestration_internal_error', detail, str(exc)


def _run_item_from_row(row: Any) -> OrchestrationRunItemV1:
    return OrchestrationRunItemV1(
        orchestration_run_id=row.orchestration_run_id,
        trace_id=row.trace_id,
        case_id=str(row.case_id),
        patient_id=str(row.patient_id),
        mode=row.mode,
        status=row.status,
        requested_task=row.requested_task,
        candidate_agents=list(row.candidate_agents_json or []),
        clinical_context_refs=dict(row.clinical_context_refs_json or {}),
        modality_refs=dict(row.modality_refs_json or {}),
        runtime_options=dict(row.runtime_options_json or {}),
        idempotency_key=row.idempotency_key,
        payload_json=dict(row.payload_json or {}),
        result_json=dict(row.result_json or {}),
        runtime_stub=bool(row.runtime_stub),
        started_at=row.started_at.isoformat() if row.started_at else None,
        completed_at=row.completed_at.isoformat() if row.completed_at else None,
        duration_ms=row.duration_ms,
        error_code=row.error_code,
        error_detail_json=dict(row.error_detail_json or {}),
    )


def _step_item_from_row(row: Any) -> OrchestrationStepItemV1:
    return OrchestrationStepItemV1(
        step_id=row.step_id,
        trace_id=row.trace_id,
        case_id=str(row.case_id),
        patient_id=str(row.patient_id),
        orchestration_run_id=row.orchestration_run_id,
        parent_step_id=row.parent_step_id,
        step_type=row.step_type,
        step_name=row.step_name,
        step_index=row.step_index,
        agent_code=row.agent_code,
        agent_version=row.agent_version,
        model_version_id=str(row.model_version_id) if row.model_version_id is not None else None,
        status=row.status,
        payload_json=dict(row.payload_json or {}),
        result_json=dict(row.result_json or {}),
        runtime_stub=bool(row.runtime_stub),
        started_at=row.started_at.isoformat() if row.started_at else None,
        completed_at=row.completed_at.isoformat() if row.completed_at else None,
        duration_ms=row.duration_ms,
        error_code=row.error_code,
        error_detail_json=dict(row.error_detail_json or {}),
    )


def _invocation_item_from_row(row: Any) -> OrchestrationAgentInvocationItemV1:
    return OrchestrationAgentInvocationItemV1(
        agent_invocation_id=row.agent_invocation_id,
        trace_id=row.trace_id,
        case_id=str(row.case_id),
        patient_id=str(row.patient_id),
        orchestration_run_id=row.orchestration_run_id,
        step_id=row.step_id,
        agent_code=row.agent_code,
        agent_version=row.agent_version,
        endpoint_id=row.endpoint_id,
        endpoint_url=row.endpoint_url,
        model_version_id=str(row.model_version_id) if row.model_version_id is not None else None,
        status=row.status,
        payload_json=dict(row.payload_json or {}),
        response_json=dict(row.response_json or {}),
        runtime_stub=bool(row.runtime_stub),
        started_at=row.started_at.isoformat() if row.started_at else None,
        completed_at=row.completed_at.isoformat() if row.completed_at else None,
        duration_ms=row.duration_ms,
        error_code=row.error_code,
        error_detail_json=dict(row.error_detail_json or {}),
    )


def _conflict_item_from_row(row: Any) -> OrchestrationConflictItemV1:
    return OrchestrationConflictItemV1(
        conflict_id=row.conflict_id,
        trace_id=row.trace_id,
        case_id=str(row.case_id),
        patient_id=str(row.patient_id),
        orchestration_run_id=row.orchestration_run_id,
        step_id=row.step_id,
        conflict_type=row.conflict_type,
        status=row.status,
        summary_text=row.summary_text,
        resolution_strategy=row.resolution_strategy,
        resolution_summary=row.resolution_summary,
        payload_json=dict(row.payload_json or {}),
        result_json=dict(row.result_json or {}),
        runtime_stub=bool(row.runtime_stub),
        started_at=row.started_at.isoformat() if row.started_at else None,
        completed_at=row.completed_at.isoformat() if row.completed_at else None,
        duration_ms=row.duration_ms,
        error_code=row.error_code,
        error_detail_json=dict(row.error_detail_json or {}),
    )


def _summary_item_from_row(row: Any) -> OrchestrationLlmSummaryItemV1:
    return OrchestrationLlmSummaryItemV1(
        summary_id=row.summary_id,
        trace_id=row.trace_id,
        case_id=str(row.case_id),
        patient_id=str(row.patient_id),
        orchestration_run_id=row.orchestration_run_id,
        step_id=row.step_id,
        agent_invocation_id=row.agent_invocation_id,
        model_version_id=str(row.model_version_id) if row.model_version_id is not None else None,
        summary_type=row.summary_type,
        status=row.status,
        summary_text=row.summary_text,
        summary_json=dict(row.summary_json or {}),
        payload_json=dict(row.payload_json or {}),
        runtime_stub=bool(row.runtime_stub),
        started_at=row.started_at.isoformat() if row.started_at else None,
        completed_at=row.completed_at.isoformat() if row.completed_at else None,
        duration_ms=row.duration_ms,
        error_code=row.error_code,
        error_detail_json=dict(row.error_detail_json or {}),
    )


def _run_not_found(orchestration_run_id: str) -> OrchestrationError:
    return OrchestrationError(
        status_code=status.HTTP_404_NOT_FOUND,
        code='orchestration_run_not_found',
        message='Orchestration run not found',
        details={'orchestration_run_id': orchestration_run_id},
    )


@router.post('/validate-plan', response_model=OrchestrationValidatePlanResponseV1)
@router.post('/validate-plan/', response_model=OrchestrationValidatePlanResponseV1, include_in_schema=False)
def validate_plan(payload: OrchestrationValidatePlanRequestV1, request: Request) -> OrchestrationValidatePlanResponseV1:
    if not payload.trace_id:
        raise OrchestrationError(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code='trace_id_missing', message='trace_id is required')
    _validate_candidate_agents(payload.orchestration_mode, payload.candidate_agents)

    request_id = _request_id(request)
    orchestration_run_id = f'orc_{uuid.uuid4().hex[:16]}'
    modalities = _extract_modalities(payload.modality_refs)
    agents = _ensure_supported_agents(payload.candidate_agents, payload.requested_task, modalities)
    planned_steps = _build_planned_steps(payload.orchestration_mode, agents)

    _emit_audit(
        'orchestration validate-plan request_id=%s trace_id=%s orchestration_run_id=%s mode=%s requested_task=%s candidate_agents=%s planned_steps=%s',
        request_id,
        payload.trace_id,
        orchestration_run_id,
        payload.orchestration_mode.value,
        payload.requested_task,
        payload.candidate_agents,
        [step.step_id for step in planned_steps],
    )

    return OrchestrationValidatePlanResponseV1(
        route='/api/v1/orchestrations/validate-plan',
        trace_id=payload.trace_id,
        orchestration_run_id=orchestration_run_id,
        mode=payload.orchestration_mode,
        requested_task=payload.requested_task,
        steps=planned_steps,
        limitations=[
            'runtime_stub=true',
            'no persistence to orchestration tables',
            'no case trace_events/evidence writes in this stage',
        ],
        runtime_stub=True,
    )



@router.post('/run', response_model=OrchestrationRunResponseV1)
@router.post('/run/', response_model=OrchestrationRunResponseV1, include_in_schema=False)
def run_orchestration(payload: OrchestrationRunRequestV1, request: Request, db: Session = Depends(get_db)) -> OrchestrationRunResponseV1:
    if not payload.trace_id:
        raise OrchestrationError(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code='trace_id_missing', message='trace_id is required')
    _validate_candidate_agents(payload.orchestration_mode, payload.candidate_agents)

    request_id = _request_id(request)
    orchestration_run_id = f'orc_{uuid.uuid4().hex[:16]}'
    modalities = _extract_modalities(payload.modality_refs)
    planned_steps = _build_planned_steps(payload.orchestration_mode, [_build_stub_agent(agent_code) for agent_code in payload.candidate_agents])

    _emit_audit(
        'orchestration run start request_id=%s trace_id=%s orchestration_run_id=%s mode=%s requested_task=%s candidate_agents=%s runtime_stub=%s',
        request_id,
        payload.trace_id,
        orchestration_run_id,
        payload.orchestration_mode.value,
        payload.requested_task,
        payload.candidate_agents,
        True,
    )

    started_at = now_utc()
    run_perf = perf_counter()
    completed_steps: list[OrchestrationStepV1] = []
    invocations: list[OrchestrationAgentInvocationV1] = []
    model_service_responses: list[dict[str, Any]] = []
    step_records: list[dict[str, Any]] = []
    invocation_records: list[dict[str, Any]] = []
    failure_records: list[dict[str, Any]] = []
    first_failure: OrchestrationError | HTTPException | None = None

    for idx, step in enumerate(planned_steps, start=1):
        step_started_at = now_utc()
        step_perf = perf_counter()
        agent_invocation_id = f'agt_{uuid.uuid4().hex[:16]}'
        base_step = step.model_copy(update={'step_index': idx, 'status': OrchestrationStepStatus.running, 'agent_invocation_id': agent_invocation_id, 'details': {'runtime_stub': True, 'orchestration_run_id': orchestration_run_id}})
        try:
            agent = _agent_or_404(step.agent_code or '')
            valid, code = _validate_capability(agent, payload.requested_task, modalities)
            if not valid:
                raise OrchestrationError(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code=code or 'unsupported_agent_capability',
                    message='Unsupported agent capability request',
                    details={'agent_code': step.agent_code, 'requested_task': payload.requested_task, 'modalities': modalities},
                )

            runtime_model_version = _runtime_model_version(agent)
            base_step = base_step.model_copy(update={'model_version_id': runtime_model_version})
            completed_step, invocation, ms_resp = _invoke_agent_step(
                request=request,
                trace_id=payload.trace_id,
                orchestration_run_id=orchestration_run_id,
                step=base_step,
                requested_task=payload.requested_task,
                patient_id=payload.patient_id,
                case_id=payload.case_id,
                inputs=payload.inputs,
                clinical_context_refs=_normalize_refs(payload.clinical_context_refs),
                modality_refs=_normalize_refs(payload.modality_refs),
                runtime_options=payload.runtime_options,
                idempotency_key=payload.idempotency_key,
                agent_invocation_id=agent_invocation_id,
            )
            completed_step = completed_step.model_copy(update={'step_index': idx, 'model_version_id': _runtime_model_version(agent, ms_resp)})
            invocation = invocation.model_copy(update={
                'model_version_id': _runtime_model_version(agent, ms_resp),
                'endpoint_id': getattr(agent, 'endpoint_id', step.agent_code),
                'endpoint_url': getattr(agent, 'endpoint_url', None),
            })
            completed_steps.append(completed_step)
            invocations.append(invocation)
            model_service_responses.append(ms_resp)
            step_records.append({
                'step_id': completed_step.step_id,
                'step_type': completed_step.step_type,
                'step_name': None,
                'step_index': completed_step.step_index or idx,
                'agent_code': completed_step.agent_code,
                'agent_version': getattr(agent, 'contract_version', None),
                'model_version_id': completed_step.model_version_id,
                'status': completed_step.status.value,
                'payload_json': {
                    'runtime_stub': True,
                    'trace_id': payload.trace_id,
                    'requested_task': payload.requested_task,
                    'candidate_agents': payload.candidate_agents,
                    'mode': payload.orchestration_mode.value,
                    'step_index': completed_step.step_index or idx,
                },
                'result_json': {'runtime_stub': True, 'model_service_response': ms_resp, 'summary': completed_step.summary, 'details': completed_step.details},
                'runtime_stub': True,
                'started_at': step_started_at,
                'completed_at': now_utc(),
                'duration_ms': completed_step.duration_ms,
                'error_code': None,
                'error_detail_json': {},
                'parent_step_id': None,
            })
            invocation_records.append({
                'agent_invocation_id': invocation.agent_invocation_id,
                'step_id': invocation.step_id,
                'agent_code': invocation.agent_code,
                'agent_version': getattr(agent, 'contract_version', None),
                'endpoint_id': getattr(agent, 'endpoint_id', step.agent_code),
                'endpoint_url': getattr(agent, 'endpoint_url', None),
                'model_version_id': invocation.model_version_id,
                'status': invocation.status,
                'payload_json': {
                    'runtime_stub': True,
                    'trace_id': payload.trace_id,
                    'requested_task': payload.requested_task,
                    'candidate_agents': payload.candidate_agents,
                    'mode': payload.orchestration_mode.value,
                },
                'response_json': {'runtime_stub': True, 'model_service_response': ms_resp},
                'runtime_stub': True,
                'started_at': step_started_at,
                'completed_at': now_utc(),
                'duration_ms': invocation.duration_ms,
                'error_code': None,
                'error_detail_json': {},
            })
        except (OrchestrationError, HTTPException) as exc:
            duration_ms = int((perf_counter() - step_perf) * 1000)
            status_code, error_code, error_detail, message = _failure_detail(exc)
            if first_failure is None:
                first_failure = exc if isinstance(exc, (OrchestrationError, HTTPException)) else OrchestrationError(status.HTTP_500_INTERNAL_SERVER_ERROR, error_code, message, error_detail)
            failed_step = base_step.model_copy(update={
                'status': OrchestrationStepStatus.failed,
                'duration_ms': duration_ms,
                'summary': f'Stub orchestration step failed for {step.agent_code}',
                'details': {'runtime_stub': True, 'error_code': error_code, 'error_detail_json': error_detail},
            })
            failed_invocation = OrchestrationAgentInvocationV1(
                step_id=failed_step.step_id,
                agent_code=step.agent_code or 'unknown_agent',
                agent_invocation_id=agent_invocation_id,
                model_version_id=_runtime_model_version(step),
                status='failed',
                duration_ms=duration_ms,
                model_service_response={'runtime_stub': True, 'error_code': error_code, 'error_detail_json': error_detail, 'status_code': status_code},
            )
            completed_steps.append(failed_step)
            invocations.append(failed_invocation)
            step_records.append({
                'step_id': failed_step.step_id,
                'step_type': failed_step.step_type,
                'step_name': None,
                'step_index': failed_step.step_index or idx,
                'agent_code': failed_step.agent_code,
                'agent_version': getattr(step, 'contract_version', None),
                'model_version_id': failed_step.model_version_id,
                'status': failed_step.status.value,
                'payload_json': {
                    'runtime_stub': True,
                    'trace_id': payload.trace_id,
                    'requested_task': payload.requested_task,
                    'candidate_agents': payload.candidate_agents,
                    'mode': payload.orchestration_mode.value,
                    'step_index': failed_step.step_index or idx,
                },
                'result_json': {'runtime_stub': True, 'error_code': error_code, 'error_detail_json': error_detail},
                'runtime_stub': True,
                'started_at': step_started_at,
                'completed_at': now_utc(),
                'duration_ms': duration_ms,
                'error_code': error_code,
                'error_detail_json': error_detail,
                'parent_step_id': None,
            })
            invocation_records.append({
                'agent_invocation_id': failed_invocation.agent_invocation_id,
                'step_id': failed_invocation.step_id,
                'agent_code': failed_invocation.agent_code,
                'agent_version': getattr(step, 'contract_version', None),
                'endpoint_id': getattr(step, 'endpoint_id', step.agent_code),
                'endpoint_url': getattr(step, 'endpoint_url', None),
                'model_version_id': failed_invocation.model_version_id,
                'status': failed_invocation.status,
                'payload_json': {
                    'runtime_stub': True,
                    'trace_id': payload.trace_id,
                    'requested_task': payload.requested_task,
                    'candidate_agents': payload.candidate_agents,
                    'mode': payload.orchestration_mode.value,
                },
                'response_json': {'runtime_stub': True, 'error_code': error_code, 'error_detail_json': error_detail},
                'runtime_stub': True,
                'started_at': step_started_at,
                'completed_at': now_utc(),
                'duration_ms': duration_ms,
                'error_code': error_code,
                'error_detail_json': error_detail,
            })
            failure_records.append({'step_id': failed_step.step_id, 'agent_code': failed_step.agent_code, 'error_code': error_code, 'error_detail_json': error_detail})
            if payload.orchestration_mode == OrchestrationMode.single_agent:
                break

    if payload.orchestration_mode == OrchestrationMode.parallel_agents and len(completed_steps) > 1:
        conflict_id = f'conf_{uuid.uuid4().hex[:12]}'
        conflict = OrchestrationConflictV1(
            conflict_id=conflict_id,
            trace_id=payload.trace_id,
            case_id=payload.case_id,
            patient_id=payload.patient_id,
            orchestration_run_id=orchestration_run_id,
            step_id=completed_steps[0].step_id if completed_steps else None,
            conflict_type='parallel_agent_summary',
            agents=[step.agent_code or 'unknown_agent' for step in completed_steps],
            reason='stub conflict-aware summary placeholder for parallel orchestration',
            resolution='stub_summary_only',
            status='stub',
            payload_json={'runtime_stub': True, 'agent_codes': [step.agent_code for step in completed_steps], 'failure_count': len(failure_records)},
            result_json={},
            error_code='stub_parallel_conflict',
            error_detail_json={'runtime_stub': True, 'failure_count': len(failure_records)},
        )
        conflicts = [conflict]
    else:
        conflicts = []

    summary, recommendation, _ = _build_stub_summary(
        payload.orchestration_mode,
        payload.trace_id,
        payload.requested_task,
        [step.agent_code or 'unknown_agent' for step in completed_steps],
        model_service_responses,
        failure_count=len(failure_records),
    )
    llm_summary = {
        'summary_id': f'llm_{uuid.uuid4().hex[:12]}',
        'trace_id': payload.trace_id,
        'case_id': payload.case_id,
        'patient_id': payload.patient_id,
        'orchestration_run_id': orchestration_run_id,
        'step_id': completed_steps[-1].step_id if completed_steps else None,
        'agent_invocation_id': invocations[-1].agent_invocation_id if invocations else None,
        'model_version_id': completed_steps[-1].model_version_id if completed_steps else None,
        'summary_type': 'orchestration_summary',
        'status': 'failed' if failure_records and not model_service_responses else 'stub',
        'summary_text': summary.body,
        'summary_json': {
            'summary': summary.model_dump(mode='json'),
            'recommendation': recommendation.model_dump(mode='json'),
            'conflicts': [conflict.model_dump(mode='json') for conflict in conflicts],
            'failure_count': len(failure_records),
            'runtime_stub': True,
        },
        'payload_json': {
            'runtime_stub': True,
            'trace_id': payload.trace_id,
            'requested_task': payload.requested_task,
            'candidate_agents': payload.candidate_agents,
            'mode': payload.orchestration_mode.value,
        },
        'runtime_stub': True,
        'started_at': started_at,
        'completed_at': now_utc(),
        'duration_ms': int((perf_counter() - run_perf) * 1000),
        'error_code': failure_records[0]['error_code'] if failure_records and not model_service_responses else None,
        'error_detail_json': failure_records[0]['error_detail_json'] if failure_records and not model_service_responses else {},
    }

    run_status = 'completed'
    run_error_code = None
    run_error_detail_json: dict[str, Any] = {}
    if failure_records and not model_service_responses:
        run_status = 'failed'
        run_error_code = failure_records[0]['error_code']
        run_error_detail_json = failure_records[0]['error_detail_json']
    elif failure_records:
        run_status = 'completed'
        run_error_detail_json = {'partial_failures': failure_records, 'runtime_stub': True}

    persist_orchestration_bundle(
        db,
        orchestration_run_id=orchestration_run_id,
        trace_id=payload.trace_id,
        case_id=payload.case_id,
        patient_id=payload.patient_id,
        mode=payload.orchestration_mode.value,
        requested_task=payload.requested_task,
        candidate_agents=payload.candidate_agents,
        clinical_context_refs=_normalize_refs(payload.clinical_context_refs),
        modality_refs=_normalize_refs(payload.modality_refs),
        runtime_options=payload.runtime_options,
        idempotency_key=payload.idempotency_key,
        payload_json={
            'request': payload.model_dump(mode='json'),
            'request_id': request_id,
            'runtime_stub': True,
            'agent_gateway_endpoint': 'http://model-service:8100/infer',
        },
        result_json={
            'runtime_stub': True,
            'steps': [step.model_dump(mode='json') for step in completed_steps],
            'agent_invocations': [inv.model_dump(mode='json') for inv in invocations],
            'conflicts': [conflict.model_dump(mode='json') for conflict in conflicts],
            'llm_summary_stub': summary.model_dump(mode='json'),
            'recommendation_stub': recommendation.model_dump(mode='json'),
            'partial_failures': failure_records,
        },
        steps=step_records,
        invocations=invocation_records,
        conflicts=[conflict.model_dump(mode='json') for conflict in conflicts],
        llm_summary=llm_summary,
        status=run_status,
        error_code=run_error_code,
        error_detail_json=run_error_detail_json,
        runtime_stub=True,
        started_at=started_at,
        completed_at=now_utc(),
        duration_ms=int((perf_counter() - run_perf) * 1000),
    )

    _emit_audit(
        'orchestration run success request_id=%s trace_id=%s orchestration_run_id=%s mode=%s step_ids=%s agent_codes=%s status=%s runtime_stub=%s',
        request_id,
        payload.trace_id,
        orchestration_run_id,
        payload.orchestration_mode.value,
        [step.step_id for step in completed_steps],
        [inv.agent_code for inv in invocations],
        run_status,
        True,
    )

    response = OrchestrationRunResponseV1(
        route='/api/v1/orchestrations/run',
        trace_id=payload.trace_id,
        orchestration_run_id=orchestration_run_id,
        mode=payload.orchestration_mode,
        requested_task=payload.requested_task,
        steps=completed_steps,
        agent_invocations=invocations,
        conflicts=conflicts,
        llm_summary_stub=summary,
        recommendation_stub=recommendation,
        runtime_stub=True,
        limitations=[
            'runtime_stub=true',
            'orchestration persisted to audit tables only',
            'no case trace_events/evidence writes in this stage',
            'no real multi-agent orchestration or conflict resolution yet',
        ],
    )

    if first_failure is not None and not model_service_responses:
        raise first_failure
    return response


@router.get('/{orchestration_run_id}', response_model=OrchestrationRunDetailResponseV1)
@router.get('/{orchestration_run_id}/', response_model=OrchestrationRunDetailResponseV1, include_in_schema=False)
def get_orchestration_run(orchestration_run_id: str, db: Session = Depends(get_db)) -> OrchestrationRunDetailResponseV1:
    run = get_run(db, orchestration_run_id)
    if run is None:
        raise _run_not_found(orchestration_run_id)
    steps = list_steps(db, orchestration_run_id)
    invocations = list_invocations(db, orchestration_run_id)
    conflicts = list_conflicts(db, orchestration_run_id)
    summaries = list_llm_summaries(db, orchestration_run_id)
    return OrchestrationRunDetailResponseV1(
        run=_run_item_from_row(run),
        steps=[_step_item_from_row(row) for row in steps],
        agent_invocations=[_invocation_item_from_row(row) for row in invocations],
        conflicts=[_conflict_item_from_row(row) for row in conflicts],
        llm_summaries=[_summary_item_from_row(row) for row in summaries],
        runtime_stub=bool(run.runtime_stub),
    )


@router.get('/{orchestration_run_id}/steps', response_model=OrchestrationStepListResponseV1)
@router.get('/{orchestration_run_id}/steps/', response_model=OrchestrationStepListResponseV1, include_in_schema=False)
def get_orchestration_steps(orchestration_run_id: str, db: Session = Depends(get_db)) -> OrchestrationStepListResponseV1:
    run = get_run(db, orchestration_run_id)
    if run is None:
        raise _run_not_found(orchestration_run_id)
    rows = list_steps(db, orchestration_run_id)
    items = [_step_item_from_row(row) for row in rows]
    return OrchestrationStepListResponseV1(items=items, total=len(items))


@router.get('/{orchestration_run_id}/invocations', response_model=OrchestrationAgentInvocationListResponseV1)
@router.get('/{orchestration_run_id}/invocations/', response_model=OrchestrationAgentInvocationListResponseV1, include_in_schema=False)
def get_orchestration_invocations(orchestration_run_id: str, db: Session = Depends(get_db)) -> OrchestrationAgentInvocationListResponseV1:
    run = get_run(db, orchestration_run_id)
    if run is None:
        raise _run_not_found(orchestration_run_id)
    rows = list_invocations(db, orchestration_run_id)
    items = [_invocation_item_from_row(row) for row in rows]
    return OrchestrationAgentInvocationListResponseV1(items=items, total=len(items))


@router.get('/{orchestration_run_id}/conflicts', response_model=OrchestrationConflictListResponseV1)
@router.get('/{orchestration_run_id}/conflicts/', response_model=OrchestrationConflictListResponseV1, include_in_schema=False)
def get_orchestration_conflicts(orchestration_run_id: str, db: Session = Depends(get_db)) -> OrchestrationConflictListResponseV1:
    run = get_run(db, orchestration_run_id)
    if run is None:
        raise _run_not_found(orchestration_run_id)
    rows = list_conflicts(db, orchestration_run_id)
    items = [_conflict_item_from_row(row) for row in rows]
    return OrchestrationConflictListResponseV1(items=items, total=len(items))


@router.get('/{orchestration_run_id}/llm-summaries', response_model=OrchestrationLlmSummaryListResponseV1)
@router.get('/{orchestration_run_id}/llm-summaries/', response_model=OrchestrationLlmSummaryListResponseV1, include_in_schema=False)
def get_orchestration_llm_summaries(orchestration_run_id: str, db: Session = Depends(get_db)) -> OrchestrationLlmSummaryListResponseV1:
    run = get_run(db, orchestration_run_id)
    if run is None:
        raise _run_not_found(orchestration_run_id)
    rows = list_llm_summaries(db, orchestration_run_id)
    items = [_summary_item_from_row(row) for row in rows]
    return OrchestrationLlmSummaryListResponseV1(items=items, total=len(items))
