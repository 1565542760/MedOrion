
import logging
import uuid
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import settings
from app.modules.inference.model_service_client import ModelServiceError, infer_with_model_service
from app.modules.agent_gateway.schemas import (
    AgentGatewayInferRequestV1,
    AgentGatewayInferResponseV1,
    AgentGatewayValidateInputRequestV1,
    AgentGatewayValidateInputResponseV1,
    AgentRegistryItemV1,
    AgentRegistryListResponseV1,
    AgentRegistryResponseV1,
)

logger = logging.getLogger('app.agent_gateway')
registry_router = APIRouter()
gateway_router = APIRouter()

_SUPPORTED_DISEASES = ['cap', 'cop', 'capcop']
_SUPPORTED_TASKS = ['risk_assessment', 'triage', 'diagnosis_support', 'recommendation_generation']
_SUPPORTED_MODALITIES = ['clinical_table', 'lab_result', 'emr_text', 'ct_image', 'mri_image']
_DEFAULT_MODEL_VERSION_ID = 'capcop_stub_v1'
_CONTRACT_VERSION = 'stage35-agent-contract-v1'
_AGENT_CODE = 'capcop_agent'
_AGENT_NAME = 'CAP/COP Agent Stub'


@dataclass(frozen=True)
class _AgentCapability:
    item: AgentRegistryItemV1


_AGENT_REGISTRY: dict[str, _AgentCapability] = {
    _AGENT_CODE: _AgentCapability(
        item=AgentRegistryItemV1(
            agent_code=_AGENT_CODE,
            agent_name=_AGENT_NAME,
            contract_version=_CONTRACT_VERSION,
            supported_diseases=_SUPPORTED_DISEASES,
            supported_tasks=_SUPPORTED_TASKS,
            supported_modalities=_SUPPORTED_MODALITIES,
            status='stub_active',
            endpoint_url=settings.model_service_url.rstrip('/'),
            health_url=settings.model_service_url.rstrip('/') + '/health',
            default_model_version_id=_DEFAULT_MODEL_VERSION_ID,
        )
    )
}


def _agent_or_404(agent_code: str) -> AgentRegistryItemV1:
    capability = _AGENT_REGISTRY.get(agent_code)
    if capability is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'code': 'agent_not_found', 'message': 'Agent not found'})
    return capability.item


def _validate_capability(agent: AgentRegistryItemV1, requested_task: str, modalities: list[str]) -> tuple[bool, str | None]:
    if requested_task not in agent.supported_tasks:
        return False, 'unsupported_agent_task'
    unsupported_modalities = [modality for modality in modalities if modality not in agent.supported_modalities]
    if unsupported_modalities:
        return False, 'unsupported_modality'
    return True, None


def _agent_status_for_trace() -> str:
    return 'stub_active'


@registry_router.get('', response_model=AgentRegistryListResponseV1)
@registry_router.get('/', response_model=AgentRegistryListResponseV1, include_in_schema=False)
def list_agent_registry() -> AgentRegistryListResponseV1:
    items = [entry.item for entry in _AGENT_REGISTRY.values()]
    return AgentRegistryListResponseV1(items=items, total=len(items))


@registry_router.get('/{agent_code}', response_model=AgentRegistryResponseV1)
def get_agent_registry(agent_code: str) -> AgentRegistryResponseV1:
    item = _agent_or_404(agent_code)
    return AgentRegistryResponseV1(route=f'/api/v1/agent-registry/{agent_code}', item=item)


@gateway_router.post('/validate-input', response_model=AgentGatewayValidateInputResponseV1)
def validate_input(payload: AgentGatewayValidateInputRequestV1) -> AgentGatewayValidateInputResponseV1:
    agent = _agent_or_404(payload.agent_code)
    valid, code = _validate_capability(agent, payload.requested_task, payload.modalities)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                'code': code,
                'message': 'Unsupported agent capability request',
                'agent_code': payload.agent_code,
            },
        )
    return AgentGatewayValidateInputResponseV1(
        route='/api/v1/agent-gateway/validate-input',
        agent_code=agent.agent_code,
        valid=True,
        agent_status=agent.status,
        matched_model_version_id=agent.default_model_version_id,
        runtime_stub=True,
    )


@gateway_router.post('/infer', response_model=AgentGatewayInferResponseV1)
def infer(payload: AgentGatewayInferRequestV1, request: Request) -> AgentGatewayInferResponseV1:
    if not payload.trace_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'code': 'trace_id_missing', 'message': 'trace_id is required'})

    agent = _agent_or_404(payload.agent_code)
    valid, code = _validate_capability(agent, payload.requested_task, payload.modalities)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'code': code, 'message': 'Unsupported agent capability request', 'agent_code': payload.agent_code},
        )

    request_id = getattr(request.state, 'request_id', f'req_{uuid.uuid4().hex}')
    agent_invocation_id = f'agt_{uuid.uuid4().hex[:16]}'
    runtime_stub = True
    endpoint = settings.model_service_url.rstrip('/') + '/infer'
    logger.info(
        'agent_gateway infer start endpoint=%s trace_id=%s agent_code=%s agent_invocation_id=%s runtime_stub=%s',
        endpoint,
        payload.trace_id,
        payload.agent_code,
        agent_invocation_id,
        runtime_stub,
    )

    ms_payload: dict[str, Any] = {
        'trace_id': payload.trace_id,
        'inference_task_id': agent_invocation_id,
        'agent_invocation_id': agent_invocation_id,
        'case_id': payload.case_id,
        'patient_id': payload.patient_id,
        'disease_agent': payload.agent_code,
        'requested_task': payload.requested_task,
        'requested_modalities': payload.modalities,
        'modalities': payload.modalities,
        'clinical_context_refs': {'source': 'agent_gateway_stub'},
        'modality_refs': {'source': 'agent_gateway_stub'},
        'model_version_policy': payload.model_version_policy,
        'inputs': payload.inputs,
        'missing_value_context': payload.inputs.get('missing_value_context', {}),
        'idempotency_key': payload.idempotency_key or f'idem_{uuid.uuid4().hex[:12]}',
        'runtime_options': {'stub': True, 'agent_gateway': True},
    }

    try:
        ms_resp = infer_with_model_service(ms_payload, request_id=request_id, trace_id=payload.trace_id)
    except ModelServiceError as exc:
        logger.warning(
            'agent_gateway infer backend unavailable trace_id=%s agent_code=%s agent_invocation_id=%s endpoint=%s error_code=%s',
            payload.trace_id,
            payload.agent_code,
            agent_invocation_id,
            endpoint,
            exc.code,
        )
        if exc.code in {'model_service_unavailable', 'model_service_timeout'}:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={'code': 'agent_unavailable', 'message': 'Agent backend unavailable or timeout', 'details': {'backend_code': exc.code}},
            ) from exc
        raise HTTPException(
            status_code=exc.status_code,
            detail={'code': exc.code, 'message': exc.message, 'details': exc.details},
        ) from exc

    logger.info(
        'agent_gateway infer success trace_id=%s agent_code=%s agent_invocation_id=%s endpoint=%s runtime_stub=%s model_invocation_id=%s',
        payload.trace_id,
        payload.agent_code,
        agent_invocation_id,
        endpoint,
        runtime_stub,
        ms_resp.get('model_invocation_id'),
    )
    return AgentGatewayInferResponseV1(
        route='/api/v1/agent-gateway/infer',
        trace_id=payload.trace_id,
        agent_invocation_id=agent_invocation_id,
        agent_code=payload.agent_code,
        agent_status='succeeded',
        model_service_response=ms_resp,
        runtime_stub=True,
    )
