
from __future__ import annotations

import logging
import uuid
from time import perf_counter
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from app.modules.agent_gateway.router import _agent_or_404, _validate_capability
from app.modules.inference.model_service_client import ModelServiceError, infer_with_model_service
from app.modules.orchestrations.schemas import (
    OrchestrationAgentInvocationV1,
    OrchestrationConflictV1,
    OrchestrationMode,
    OrchestrationRunRequestV1,
    OrchestrationRunResponseV1,
    OrchestrationStepStatus,
    OrchestrationStepV1,
    OrchestrationStubSummaryV1,
    OrchestrationValidatePlanRequestV1,
    OrchestrationValidatePlanResponseV1,
)

logger = logging.getLogger('app.orchestration')
router = APIRouter()


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


def _invoke_agent_step(*, request: Request, trace_id: str, orchestration_run_id: str, step: OrchestrationStepV1, requested_task: str, patient_id: str, case_id: str, inputs: dict[str, Any], clinical_context_refs: dict[str, Any], modality_refs: dict[str, Any], runtime_options: dict[str, Any], idempotency_key: str | None) -> tuple[OrchestrationStepV1, OrchestrationAgentInvocationV1, dict[str, Any]]:
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


def _build_stub_summary(mode: OrchestrationMode, trace_id: str, requested_task: str, agents: list[str], model_service_responses: list[dict[str, Any]]) -> tuple[OrchestrationStubSummaryV1, OrchestrationStubSummaryV1, list[OrchestrationConflictV1]]:
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
def run_orchestration(payload: OrchestrationRunRequestV1, request: Request) -> OrchestrationRunResponseV1:
    if not payload.trace_id:
        raise OrchestrationError(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code='trace_id_missing', message='trace_id is required')
    _validate_candidate_agents(payload.orchestration_mode, payload.candidate_agents)

    request_id = _request_id(request)
    orchestration_run_id = f'orc_{uuid.uuid4().hex[:16]}'
    modalities = _extract_modalities(payload.modality_refs)
    agents = _ensure_supported_agents(payload.candidate_agents, payload.requested_task, modalities)
    planned_steps = _build_planned_steps(payload.orchestration_mode, agents)

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

    try:
        completed_steps: list[OrchestrationStepV1] = []
        invocations: list[OrchestrationAgentInvocationV1] = []
        model_service_responses: list[dict[str, Any]] = []

        agent_sequence = planned_steps if payload.orchestration_mode != OrchestrationMode.single_agent else planned_steps[:1]
        for step in agent_sequence:
            completed_step, invocation, ms_resp = _invoke_agent_step(
                request=request,
                trace_id=payload.trace_id,
                orchestration_run_id=orchestration_run_id,
                step=step,
                requested_task=payload.requested_task,
                patient_id=payload.patient_id,
                case_id=payload.case_id,
                inputs=payload.inputs,
                clinical_context_refs=_normalize_refs(payload.clinical_context_refs),
                modality_refs=_normalize_refs(payload.modality_refs),
                runtime_options=payload.runtime_options,
                idempotency_key=payload.idempotency_key,
            )
            completed_steps.append(completed_step)
            invocations.append(invocation)
            model_service_responses.append(ms_resp)

        summary, recommendation, conflicts = _build_stub_summary(
            payload.orchestration_mode,
            payload.trace_id,
            payload.requested_task,
            [inv.agent_code for inv in invocations],
            model_service_responses,
        )

        _emit_audit(
            'orchestration run success request_id=%s trace_id=%s orchestration_run_id=%s mode=%s step_ids=%s agent_codes=%s status=%s runtime_stub=%s',
            request_id,
            payload.trace_id,
            orchestration_run_id,
            payload.orchestration_mode.value,
            [step.step_id for step in completed_steps],
            [inv.agent_code for inv in invocations],
            'completed',
            True,
        )

        return OrchestrationRunResponseV1(
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
                'no persistence to orchestration tables',
                'no case trace_events/evidence writes in this stage',
                'no real multi-agent orchestration or conflict resolution yet',
            ],
        )
    except OrchestrationError:
        _emit_audit(
            'orchestration run failed request_id=%s trace_id=%s orchestration_run_id=%s mode=%s status=%s',
            request_id,
            payload.trace_id,
            orchestration_run_id,
            payload.orchestration_mode.value,
            'failed',
        )
        raise
