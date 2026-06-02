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
