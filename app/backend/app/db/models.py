import uuid

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.enums import (
    BlockingLevel,
    CaseStatus,
    ClinicalImportance,
    EvidenceEdgeType,
    EvidenceNodeStatus,
    EvidenceNodeType,
    FeedbackType,
    InferenceTaskStatus,
    MissingValueQueryStatus,
    ModelApprovalState,
    ModalityType,
    PatientConsentStatus,
    QualityErrorAttribution,
    QualityReviewStatus,
    QualitySeverity,
    QualityTargetType,
    ReassessmentStatus,
    ReassessmentTriggerType,
    RecommendationStatus,
    TraceActorType,
    TraceSeverity,
    ValueSourceType,
)


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Patient(Base, TimestampMixin):
    __tablename__ = 'patients'

    id: Mapped[uuid.UUID] = uuid_pk()
    external_patient_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    patient_display_id: Mapped[str | None] = mapped_column(String(128))
    sex: Mapped[str | None] = mapped_column(String(32))
    birth_date: Mapped[Date | None] = mapped_column(Date)
    demographics_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    consent_status: Mapped[PatientConsentStatus] = mapped_column(
        Enum(PatientConsentStatus, values_callable=lambda enum_cls: [item.value for item in enum_cls]), nullable=False, default=PatientConsentStatus.UNKNOWN.value
    )



class Case(Base, TimestampMixin):
    __tablename__ = 'cases'
    __table_args__ = (
        Index('ix_cases_owner_user_id', 'owner_user_id'),
        Index('ix_cases_primary_doctor_id', 'primary_doctor_id'),
        Index('ix_cases_organization_id', 'organization_id'),
        Index('ix_cases_access_policy_status', 'access_policy_status'),
        Index('ix_cases_created_by', 'created_by'),
        Index('ix_cases_updated_by', 'updated_by'),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('patients.id'), nullable=False)
    case_no: Mapped[str | None] = mapped_column(String(128), unique=True)
    disease_domain_code: Mapped[str | None] = mapped_column(String(64))
    title: Mapped[str | None] = mapped_column(String(256))
    status: Mapped[CaseStatus] = mapped_column(Enum(CaseStatus, values_callable=lambda enum_cls: [item.value for item in enum_cls]), nullable=False, default=CaseStatus.OPEN.value)
    chief_complaint: Mapped[str | None] = mapped_column(Text)
    context_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    opened_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id'))
    primary_doctor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id'))
    organization_id: Mapped[str | None] = mapped_column(String(64))
    access_policy_status: Mapped[str | None] = mapped_column(String(32))
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id'))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id'))


class CaseAssignment(Base, TimestampMixin):
    __tablename__ = 'case_assignments'
    __table_args__ = (
        UniqueConstraint('assignment_id', name='uq_case_assignments_assignment_id'),
        Index('ix_case_assignments_case_id', 'case_id'),
        Index('ix_case_assignments_user_id', 'user_id'),
        Index('ix_case_assignments_role_on_case', 'role_on_case'),
        Index('ix_case_assignments_assignment_status', 'assignment_status'),
        Index('ix_case_assignments_case_user_id', 'case_id', 'user_id'),
        Index('ix_case_assignments_case_role_on_case', 'case_id', 'role_on_case'),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    assignment_id: Mapped[str] = mapped_column(String(128), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), nullable=False)
    role_on_case: Mapped[str] = mapped_column(String(64), nullable=False)
    assignment_status: Mapped[str] = mapped_column(String(32), nullable=False, default='active')
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id'))
    assigned_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id'))
    revoked_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str | None] = mapped_column(Text)


class MultimodalAsset(Base, TimestampMixin):
    __tablename__ = 'multimodal_assets'

    id: Mapped[uuid.UUID] = uuid_pk()
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('patients.id'))
    modality_type: Mapped[ModalityType] = mapped_column(Enum(ModalityType), nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(64))
    bucket: Mapped[str | None] = mapped_column(String(128))
    object_key: Mapped[str | None] = mapped_column(String(512))
    checksum_sha256: Mapped[str | None] = mapped_column(String(128))
    content_type: Mapped[str | None] = mapped_column(String(128))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    clinical_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    trace_ref: Mapped[str | None] = mapped_column(String(96))
    quality_flags_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    normalized_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class ClinicalObservation(Base, TimestampMixin):
    __tablename__ = 'clinical_observations'

    id: Mapped[uuid.UUID] = uuid_pk()
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('patients.id'), nullable=False)
    observation_code: Mapped[str] = mapped_column(String(128), nullable=False)
    observation_name: Mapped[str | None] = mapped_column(String(256))
    value_numeric: Mapped[float | None] = mapped_column(Float)
    value_text: Mapped[str | None] = mapped_column(Text)
    value_json: Mapped[dict | None] = mapped_column(JSONB)
    unit: Mapped[str | None] = mapped_column(String(64))
    observed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('multimodal_assets.id'))
    source_type: Mapped[str | None] = mapped_column(String(64))
    provenance_level: Mapped[str | None] = mapped_column(String(32))


class LabResult(Base, TimestampMixin):
    __tablename__ = 'lab_results'

    id: Mapped[uuid.UUID] = uuid_pk()
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('patients.id'), nullable=False)
    lab_panel_code: Mapped[str | None] = mapped_column(String(128))
    test_code: Mapped[str] = mapped_column(String(128), nullable=False)
    test_name: Mapped[str | None] = mapped_column(String(256))
    value_numeric: Mapped[float | None] = mapped_column(Float)
    value_text: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(String(64))
    reference_range_json: Mapped[dict | None] = mapped_column(JSONB)
    abnormal_flag: Mapped[str | None] = mapped_column(String(32))
    sampled_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    reported_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    source_asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('multimodal_assets.id'))


class EmrDocument(Base, TimestampMixin):
    __tablename__ = 'emr_documents'

    id: Mapped[uuid.UUID] = uuid_pk()
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('patients.id'), nullable=False)
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str | None] = mapped_column(String(256))
    language: Mapped[str | None] = mapped_column(String(16))
    bucket: Mapped[str | None] = mapped_column(String(128))
    object_key: Mapped[str | None] = mapped_column(String(512))
    checksum_sha256: Mapped[str | None] = mapped_column(String(128))
    extracted_structured_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    authored_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))




class AccessAuditEvent(Base):
    __tablename__ = 'access_audit_events'
    __table_args__ = (
        UniqueConstraint('access_event_id', name='uq_access_audit_events_access_event_id'),
        Index('ix_access_audit_events_actor_user_id', 'actor_user_id'),
        Index('ix_access_audit_events_case_id', 'case_id'),
        Index('ix_access_audit_events_patient_id', 'patient_id'),
        Index('ix_access_audit_events_trace_id', 'trace_id'),
        Index('ix_access_audit_events_resource_type', 'resource_type'),
        Index('ix_access_audit_events_resource_id', 'resource_id'),
        Index('ix_access_audit_events_decision', 'decision'),
        Index('ix_access_audit_events_access_mode', 'access_mode'),
        Index('ix_access_audit_events_created_at', 'created_at'),
        Index('ix_access_audit_events_case_created_at', 'case_id', 'created_at'),
        Index('ix_access_audit_events_actor_created_at', 'actor_user_id', 'created_at'),
        Index('ix_access_audit_events_resource_type_resource_id', 'resource_type', 'resource_id'),
        Index('ix_access_audit_events_decision_created_at', 'decision', 'created_at'),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    access_event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id'))
    actor_type: Mapped[str | None] = mapped_column(String(64))
    actor_role: Mapped[str | None] = mapped_column(String(32))
    access_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(128))
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('cases.id'))
    patient_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('patients.id'))
    trace_id: Mapped[str | None] = mapped_column(String(96))
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    denial_reason: Mapped[str | None] = mapped_column(String(64))
    policy_source: Mapped[str | None] = mapped_column(String(64))
    request_id: Mapped[str | None] = mapped_column(String(128))
    route_path: Mapped[str | None] = mapped_column(String(256))
    method: Mapped[str | None] = mapped_column(String(16))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ModelRegistry(Base, TimestampMixin):
    __tablename__ = 'model_registry'

    id: Mapped[uuid.UUID] = uuid_pk()
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    disease_agent: Mapped[str] = mapped_column(String(64), nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    modality_scope_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    owner_team: Mapped[str | None] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ModelVersion(Base, TimestampMixin):
    __tablename__ = 'model_versions'
    __table_args__ = (
        Index(
            'uq_model_versions_one_default_per_model',
            'model_id',
            unique=True,
            postgresql_where=text("approval_state = 'default'::modelapprovalstate"),
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('model_registry.id'), nullable=False)
    version_label: Mapped[str] = mapped_column(String(128), nullable=False)
    approval_state: Mapped[ModelApprovalState] = mapped_column(
        Enum(ModelApprovalState, values_callable=lambda enum_cls: [item.value for item in enum_cls]),
        nullable=False,
        default=ModelApprovalState.DRAFT.value,
    )
    contract_version: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_ref_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    input_schema_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output_schema_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    metrics_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    runtime_constraints_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id'))
    approved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    promoted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id'))
    promoted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    rollback_from_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('model_versions.id'))
    published_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))



class ShadowInferenceRun(Base, TimestampMixin):
    __tablename__ = 'shadow_inference_runs'
    __table_args__ = (
        UniqueConstraint('shadow_run_id', name='uq_shadow_runs_shadow_run_id'),
        Index('ix_shadow_runs_trace', 'trace_id'),
        Index('ix_shadow_runs_case', 'case_id'),
        Index('ix_shadow_runs_patient', 'patient_id'),
        Index('ix_shadow_runs_modelver', 'model_version_id'),
        Index('ix_shadow_runs_status', 'status'),
        Index('ix_shadow_runs_started', 'started_at'),
        Index('ix_shadow_runs_case_start', 'case_id', 'started_at'),
        Index('ix_shadow_runs_trace_modelver', 'trace_id', 'model_version_id'),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    shadow_run_id: Mapped[str] = mapped_column(String(96), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('patients.id'), nullable=False)
    model_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('model_versions.id'), nullable=False)
    artifact_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    adapter_code: Mapped[str] = mapped_column(String(64), nullable=False)
    model_input_schema_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    input_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    runtime_env_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    runtime_stub: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    not_for_diagnosis: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(BigInteger)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_detail_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class ShadowInferenceOutput(Base):
    __tablename__ = 'shadow_inference_outputs'
    __table_args__ = (
        UniqueConstraint('output_id', name='uq_shadow_outs_output_id'),
        Index('ix_shadow_outs_trace', 'trace_id'),
        Index('ix_shadow_outs_case', 'case_id'),
        Index('ix_shadow_outs_modelver', 'model_version_id'),
        Index('ix_shadow_outs_shadow_run', 'shadow_run_id'),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    output_id: Mapped[str] = mapped_column(String(96), nullable=False)
    shadow_run_id: Mapped[str] = mapped_column(
        ForeignKey('shadow_inference_runs.shadow_run_id', name='fk_shadow_outs_shadow_run'),
        nullable=False,
    )
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    model_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('model_versions.id'), nullable=False)
    prediction_raw_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    prediction_probability_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    candidate_label: Mapped[str | None] = mapped_column(String(128))
    confidence_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    uncertainty_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    limitations_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    input_quality_flags_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CaseModelInputSnapshot(Base, TimestampMixin):
    __tablename__ = 'case_model_input_snapshots'
    __table_args__ = (
        UniqueConstraint('input_snapshot_id', name='uq_case_model_input_snapshots_input_snapshot_id'),
        Index('ix_case_model_input_snapshots_case_id', 'case_id'),
        Index('ix_case_model_input_snapshots_patient_id', 'patient_id'),
        Index('ix_case_model_input_snapshots_trace_id', 'trace_id'),
        Index('ix_case_model_input_snapshots_model_version_id', 'model_version_id'),
        Index('ix_case_model_input_snapshots_case_created_at', 'case_id', 'created_at'),
        Index('ix_case_model_input_snapshots_trace_model_version', 'trace_id', 'model_version_id'),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    input_snapshot_id: Mapped[str] = mapped_column(String(128), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('patients.id'), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    model_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('model_versions.id'), nullable=False)
    model_input_schema_id: Mapped[str] = mapped_column(String(128), nullable=False)
    disease_task_feature_set_id: Mapped[str] = mapped_column(String(128), nullable=False)
    preprocess_artifact_ref: Mapped[str | None] = mapped_column(String(512))
    mapped_features_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    missing_features_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    defaulted_features_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    doctor_provided_features_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    source_refs_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    validation_status: Mapped[str] = mapped_column(String(64), nullable=False)
    current_assessment_status: Mapped[str] = mapped_column(String(64), nullable=False)
    insufficient_data_for_assessment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    runtime_stub: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    not_for_diagnosis: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)



class InferenceTask(Base, TimestampMixin):
    __tablename__ = 'inference_tasks'
    __table_args__ = (
        UniqueConstraint('trace_id', name='uq_inference_tasks_trace_id'),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False, unique=True, index=True)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('patients.id'))
    disease_agent: Mapped[str] = mapped_column(String(64), nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[InferenceTaskStatus] = mapped_column(
        Enum(InferenceTaskStatus), nullable=False, default=InferenceTaskStatus.PENDING
    )
    requested_modalities_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    model_version_policy_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    input_refs_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    missing_value_summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(160))
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)


class Recommendation(Base, TimestampMixin):
    __tablename__ = 'recommendations'
    __table_args__ = (
        Index('ix_recommendations_trace_id', 'trace_id'),
        Index('ix_recommendations_inference_task_id', 'inference_task_id'),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    inference_task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('inference_tasks.id'), nullable=False
    )
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    evidence_chain_id: Mapped[str | None] = mapped_column(String(96))
    recommendation_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    recommendation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[RecommendationStatus] = mapped_column(
        Enum(RecommendationStatus), nullable=False, default=RecommendationStatus.DRAFT
    )
    candidate_label: Mapped[str | None] = mapped_column(String(64))
    confidence_score: Mapped[float | None] = mapped_column(Float)
    uncertainty_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    evidence_refs_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    content_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_by_type: Mapped[str] = mapped_column(String(32), nullable=False, default='system')


class DoctorFeedback(Base, TimestampMixin):
    __tablename__ = 'doctor_feedback'

    id: Mapped[uuid.UUID] = uuid_pk()
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('recommendations.id'))
    inference_task_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('inference_tasks.id'))
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    doctor_id: Mapped[str | None] = mapped_column(String(128))
    feedback_type: Mapped[FeedbackType] = mapped_column(Enum(FeedbackType), nullable=False)
    decision: Mapped[str | None] = mapped_column(String(64))
    rating: Mapped[int | None] = mapped_column(Integer)
    clinical_rationale: Mapped[str | None] = mapped_column(Text)
    correction_payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    learning_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ReassessmentJob(Base, TimestampMixin):
    __tablename__ = 'reassessment_jobs'

    id: Mapped[uuid.UUID] = uuid_pk()
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('patients.id'), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    previous_trace_id: Mapped[str | None] = mapped_column(String(96))
    previous_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey('dynamic_state_snapshots.id', name='fk_reassessment_previous_snapshot', use_alter=True),
        nullable=True,
    )
    current_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey('dynamic_state_snapshots.id', name='fk_reassessment_current_snapshot', use_alter=True),
        nullable=True,
    )
    trigger_type: Mapped[ReassessmentTriggerType] = mapped_column(Enum(ReassessmentTriggerType), nullable=False)
    trigger_ref: Mapped[str | None] = mapped_column(String(256))
    status: Mapped[ReassessmentStatus] = mapped_column(
        Enum(ReassessmentStatus), nullable=False, default=ReassessmentStatus.PENDING
    )
    changed_input_refs_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    comparison_summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))


class DynamicStateSnapshot(Base, TimestampMixin):
    __tablename__ = 'dynamic_state_snapshots'
    __table_args__ = (Index('ix_dynamic_state_snapshots_case_time', 'case_id', 'snapshot_time'),)

    id: Mapped[uuid.UUID] = uuid_pk()
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('patients.id'), nullable=False)
    snapshot_time: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String(96))
    source_reassessment_job_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('reassessment_jobs.id'))
    state_summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    modality_presence_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    risk_summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    uncertainty_summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class CaseMissingValueQuery(Base, TimestampMixin):
    __tablename__ = 'case_missing_value_queries'
    __table_args__ = (
        Index('ix_case_missing_value_queries_trace_id', 'trace_id'),
        Index('ix_case_missing_value_queries_case_status', 'case_id', 'status'),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('patients.id'))
    inference_task_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('inference_tasks.id'))
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    field_path: Mapped[str] = mapped_column(String(256), nullable=False)
    field_label: Mapped[str | None] = mapped_column(String(256))
    clinical_importance: Mapped[ClinicalImportance] = mapped_column(
        Enum(ClinicalImportance), nullable=False, default=ClinicalImportance.RECOMMENDED
    )
    blocking_level: Mapped[BlockingLevel] = mapped_column(
        Enum(BlockingLevel), nullable=False, default=BlockingLevel.INFORMATIONAL
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[MissingValueQueryStatus] = mapped_column(
        Enum(MissingValueQueryStatus), nullable=False, default=MissingValueQueryStatus.PENDING
    )
    doctor_id: Mapped[str | None] = mapped_column(String(128))
    doctor_response_json: Mapped[dict | None] = mapped_column(JSONB)
    value_source: Mapped[ValueSourceType] = mapped_column(
        Enum(ValueSourceType), nullable=False, default=ValueSourceType.UNKNOWN
    )
    default_strategy_code: Mapped[str | None] = mapped_column(String(128))
    default_value_json: Mapped[dict | None] = mapped_column(JSONB)
    default_reason: Mapped[str | None] = mapped_column(Text)
    policy_version: Mapped[str] = mapped_column(String(64), nullable=False, default='v1')
    expires_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))


class TraceEvent(Base):
    __tablename__ = 'trace_events'
    __table_args__ = (Index('ix_trace_events_trace_time', 'trace_id', 'event_time'),)

    id: Mapped[uuid.UUID] = uuid_pk()
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('patients.id'))
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_type: Mapped[TraceActorType] = mapped_column(Enum(TraceActorType), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(128))
    source_module: Mapped[str] = mapped_column(String(64), nullable=False)
    source_record_type: Mapped[str | None] = mapped_column(String(64))
    source_record_id: Mapped[str | None] = mapped_column(String(128))
    event_time: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    parent_event_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('trace_events.id'))
    severity: Mapped[TraceSeverity] = mapped_column(
        Enum(TraceSeverity), nullable=False, default=TraceSeverity.INFO
    )
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EvidenceNode(Base):
    __tablename__ = 'evidence_nodes'
    __table_args__ = (Index('ix_evidence_nodes_trace_type', 'trace_id', 'node_type'),)

    id: Mapped[uuid.UUID] = uuid_pk()
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('patients.id'))
    evidence_chain_id: Mapped[str] = mapped_column(String(96), nullable=False)
    node_type: Mapped[EvidenceNodeType] = mapped_column(Enum(EvidenceNodeType), nullable=False)
    source_module: Mapped[str] = mapped_column(String(64), nullable=False)
    source_record_type: Mapped[str | None] = mapped_column(String(64))
    source_record_id: Mapped[str | None] = mapped_column(String(128))
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    confidence: Mapped[float | None] = mapped_column(Float)
    uncertainty_json: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[EvidenceNodeStatus] = mapped_column(
        Enum(EvidenceNodeStatus), nullable=False, default=EvidenceNodeStatus.ACTIVE
    )
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EvidenceEdge(Base):
    __tablename__ = 'evidence_edges'
    __table_args__ = (Index('ix_evidence_edges_trace_src_tgt', 'trace_id', 'source_node_id', 'target_node_id'),)

    id: Mapped[uuid.UUID] = uuid_pk()
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    evidence_chain_id: Mapped[str] = mapped_column(String(96), nullable=False)
    source_node_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('evidence_nodes.id'), nullable=False)
    target_node_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('evidence_nodes.id'), nullable=False)
    edge_type: Mapped[EvidenceEdgeType] = mapped_column(Enum(EvidenceEdgeType), nullable=False)
    weight: Mapped[float | None] = mapped_column(Float)
    rationale: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class QualityReview(Base, TimestampMixin):
    __tablename__ = 'quality_reviews'
    __table_args__ = (Index('ix_quality_reviews_trace_status', 'trace_id', 'status'),)

    id: Mapped[uuid.UUID] = uuid_pk()
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('patients.id'))
    review_target_type: Mapped[QualityTargetType] = mapped_column(Enum(QualityTargetType), nullable=False)
    review_target_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[QualityReviewStatus] = mapped_column(
        Enum(QualityReviewStatus), nullable=False, default=QualityReviewStatus.OPEN
    )
    severity: Mapped[QualitySeverity] = mapped_column(
        Enum(QualitySeverity), nullable=False, default=QualitySeverity.MEDIUM
    )
    opened_by_type: Mapped[TraceActorType] = mapped_column(Enum(TraceActorType), nullable=False)
    opened_by_id: Mapped[str | None] = mapped_column(String(128))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    error_attribution: Mapped[QualityErrorAttribution | None] = mapped_column(Enum(QualityErrorAttribution))
    attribution_confidence: Mapped[float | None] = mapped_column(Float)
    findings_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    related_refs_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    resolution_summary: Mapped[str | None] = mapped_column(Text)
    resolved_by_type: Mapped[TraceActorType | None] = mapped_column(Enum(TraceActorType))
    resolved_by_id: Mapped[str | None] = mapped_column(String(128))
    resolved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))


class User(Base, TimestampMixin):
    __tablename__ = 'users'
    __table_args__ = (
        Index('ix_users_username', 'username'),
        Index('ix_users_email', 'email'),
        CheckConstraint(
            "role IN ('doctor', 'admin', 'model_reviewer', 'qa_reviewer', 'super_admin')",
            name='ck_users_role_valid',
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    username: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(String(128))
    email: Mapped[str | None] = mapped_column(String(256), unique=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default='doctor')
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'
    __table_args__ = (
        Index('ix_refresh_tokens_user_expires', 'user_id', 'expires_at'),
        Index('ix_refresh_tokens_token_hash', 'token_hash'),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrchestrationRun(Base, TimestampMixin):
    __tablename__ = 'orchestration_runs'
    __table_args__ = (
        UniqueConstraint('orchestration_run_id', name='uq_orchestration_runs_orchestration_run_id'),
        Index('ix_orchestration_runs_trace_id', 'trace_id'),
        Index('ix_orchestration_runs_case_id', 'case_id'),
        Index('ix_orchestration_runs_patient_id', 'patient_id'),
        Index('ix_orchestration_runs_status_started_at', 'status', 'started_at'),
        Index('ix_orchestration_runs_started_at', 'started_at'),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    orchestration_run_id: Mapped[str] = mapped_column(String(96), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('patients.id'), nullable=False)
    mode: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_task: Mapped[str] = mapped_column(String(128), nullable=False)
    candidate_agents_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    clinical_context_refs_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    modality_refs_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    runtime_options_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(160))
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    runtime_stub: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_detail_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class OrchestrationStep(Base, TimestampMixin):
    __tablename__ = 'orchestration_steps'
    __table_args__ = (
        UniqueConstraint('step_id', name='uq_orchestration_steps_step_id'),
        Index('ix_orchestration_steps_trace_id', 'trace_id'),
        Index('ix_orchestration_steps_case_id', 'case_id'),
        Index('ix_orchestration_steps_orchestration_run_id', 'orchestration_run_id'),
        Index('ix_orchestration_steps_run_step_index', 'orchestration_run_id', 'step_index'),
        Index('ix_orchestration_steps_agent_code', 'agent_code'),
        Index('ix_orchestration_steps_model_version_id', 'model_version_id'),
        Index('ix_orchestration_steps_status_started_at', 'status', 'started_at'),
        Index('ix_orchestration_steps_started_at', 'started_at'),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    step_id: Mapped[str] = mapped_column(String(96), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('patients.id'), nullable=False)
    orchestration_run_id: Mapped[str] = mapped_column(
        ForeignKey('orchestration_runs.orchestration_run_id'), nullable=False
    )
    parent_step_id: Mapped[str | None] = mapped_column(
        ForeignKey('orchestration_steps.step_id'),
    )
    step_type: Mapped[str] = mapped_column(String(64), nullable=False)
    step_name: Mapped[str | None] = mapped_column(String(128))
    step_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    agent_code: Mapped[str | None] = mapped_column(String(64))
    agent_version: Mapped[str | None] = mapped_column(String(128))
    model_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('model_versions.id'))
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    runtime_stub: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_detail_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class AgentInvocation(Base, TimestampMixin):
    __tablename__ = 'agent_invocations'
    __table_args__ = (
        UniqueConstraint('agent_invocation_id', name='uq_agent_invocations_agent_invocation_id'),
        Index('ix_agent_invocations_trace_id', 'trace_id'),
        Index('ix_agent_invocations_case_id', 'case_id'),
        Index('ix_agent_invocations_orchestration_run_id', 'orchestration_run_id'),
        Index('ix_agent_invocations_step_id', 'step_id'),
        Index('ix_agent_invocations_agent_code', 'agent_code'),
        Index('ix_agent_invocations_model_version_id', 'model_version_id'),
        Index('ix_agent_invocations_status_started_at', 'status', 'started_at'),
        Index('ix_agent_invocations_started_at', 'started_at'),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    agent_invocation_id: Mapped[str] = mapped_column(String(96), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('patients.id'), nullable=False)
    orchestration_run_id: Mapped[str] = mapped_column(
        ForeignKey('orchestration_runs.orchestration_run_id'), nullable=False
    )
    step_id: Mapped[str] = mapped_column(ForeignKey('orchestration_steps.step_id'), nullable=False)
    agent_code: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_version: Mapped[str | None] = mapped_column(String(128))
    endpoint_id: Mapped[str | None] = mapped_column(String(96))
    endpoint_url: Mapped[str | None] = mapped_column(String(512))
    model_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('model_versions.id'))
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    response_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    runtime_stub: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_detail_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class OrchestrationConflict(Base, TimestampMixin):
    __tablename__ = 'orchestration_conflicts'
    __table_args__ = (
        UniqueConstraint('conflict_id', name='uq_orchestration_conflicts_conflict_id'),
        Index('ix_orchestration_conflicts_trace_id', 'trace_id'),
        Index('ix_orchestration_conflicts_case_id', 'case_id'),
        Index('ix_orchestration_conflicts_orchestration_run_id', 'orchestration_run_id'),
        Index('ix_orchestration_conflicts_status_started_at', 'status', 'started_at'),
        Index('ix_orchestration_conflicts_started_at', 'started_at'),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    conflict_id: Mapped[str] = mapped_column(String(96), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('patients.id'), nullable=False)
    orchestration_run_id: Mapped[str] = mapped_column(
        ForeignKey('orchestration_runs.orchestration_run_id'), nullable=False
    )
    step_id: Mapped[str | None] = mapped_column(ForeignKey('orchestration_steps.step_id'))
    conflict_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    summary_text: Mapped[str | None] = mapped_column(Text)
    resolution_strategy: Mapped[str | None] = mapped_column(String(64))
    resolution_summary: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    runtime_stub: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_detail_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class LlmSummary(Base, TimestampMixin):
    __tablename__ = 'llm_summaries'
    __table_args__ = (
        UniqueConstraint('summary_id', name='uq_llm_summaries_summary_id'),
        Index('ix_llm_summaries_trace_id', 'trace_id'),
        Index('ix_llm_summaries_case_id', 'case_id'),
        Index('ix_llm_summaries_orchestration_run_id', 'orchestration_run_id'),
        Index('ix_llm_summaries_model_version_id', 'model_version_id'),
        Index('ix_llm_summaries_status_started_at', 'status', 'started_at'),
        Index('ix_llm_summaries_started_at', 'started_at'),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    summary_id: Mapped[str] = mapped_column(String(96), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('cases.id'), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('patients.id'), nullable=False)
    orchestration_run_id: Mapped[str] = mapped_column(
        ForeignKey('orchestration_runs.orchestration_run_id'), nullable=False
    )
    step_id: Mapped[str | None] = mapped_column(ForeignKey('orchestration_steps.step_id'))
    agent_invocation_id: Mapped[str | None] = mapped_column(
        ForeignKey('agent_invocations.agent_invocation_id')
    )
    model_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('model_versions.id'))
    summary_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    summary_text: Mapped[str | None] = mapped_column(Text)
    summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    runtime_stub: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_detail_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

