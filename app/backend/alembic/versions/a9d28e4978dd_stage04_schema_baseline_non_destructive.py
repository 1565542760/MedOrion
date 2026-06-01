"""stage04_schema_baseline_non_destructive

Revision ID: a9d28e4978dd
Revises:
Create Date: 2026-05-31 23:10:36.808700

Stage-04: non-destructive DDL review migration.
This revision is generated/refined for review only and must not be applied
without controller approval.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a9d28e4978dd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


patient_consent_status = sa.Enum('unknown', 'granted', 'withdrawn', name='patientconsentstatus')
case_status = sa.Enum('draft', 'open', 'in_review', 'closed', 'archived', name='casestatus')
modality_type = sa.Enum('ct_image', 'mri_image', 'clinical_table', 'lab_result', 'emr_text', 'wearable', 'other', name='modalitytype')
inference_task_status = sa.Enum('pending', 'running', 'succeeded', 'failed', 'partial', 'canceled', name='inferencetaskstatus')
recommendation_status = sa.Enum('draft', 'active', 'superseded', 'retracted', name='recommendationstatus')
feedback_type = sa.Enum('accept', 'reject', 'edit', 'comment', 'flag', name='feedbacktype')
reassessment_trigger_type = sa.Enum('new_input', 'manual_request', 'scheduled', 'qc_request', name='reassessmenttriggertype')
reassessment_status = sa.Enum('pending', 'running', 'completed', 'failed', 'canceled', name='reassessmentstatus')
clinical_importance = sa.Enum('required', 'recommended', 'optional', name='clinicalimportance')
blocking_level = sa.Enum('blocking', 'degrades_confidence', 'informational', name='blockinglevel')
missing_value_query_status = sa.Enum('pending', 'answered', 'default_applied', 'waived_by_doctor', 'expired', name='missingvaluequerystatus')
value_source_type = sa.Enum('doctor_provided', 'default_applied', 'waived', 'unknown', name='valuesourcetype')
trace_actor_type = sa.Enum('doctor', 'system', 'orchestrator', 'disease_agent', 'small_model', 'large_model', 'qc_agent', 'admin', name='traceactortype')
trace_severity = sa.Enum('info', 'warning', 'error', 'critical', name='traceseverity')
evidence_node_type = sa.Enum('input', 'clinical_feature', 'lab_result', 'image_finding', 'model_output', 'rule_result', 'llm_reasoning_step', 'recommendation', 'doctor_feedback', name='evidencenodetype')
evidence_node_status = sa.Enum('active', 'superseded', 'retracted', 'conflicted', 'defaulted', name='evidencenodestatus')
evidence_edge_type = sa.Enum('supports', 'contradicts', 'derived_from', 'references', 'overrides', 'missing_value_defaulted', name='evidenceedgetype')
quality_target_type = sa.Enum('recommendation', 'trace', 'model_output', 'missing_value_decision', 'reassessment', name='qualitytargettype')
quality_review_status = sa.Enum('open', 'investigating', 'resolved', 'dismissed', name='qualityreviewstatus')
quality_severity = sa.Enum('low', 'medium', 'high', 'critical', name='qualityseverity')
quality_error_attribution = sa.Enum('data_quality', 'model_error', 'orchestration_error', 'missing_value_policy', 'human_feedback', 'system_error', name='qualityerrorattribution')
model_approval_state = sa.Enum('draft', 'approved', 'deprecated', 'revoked', name='modelapprovalstate')


def upgrade() -> None:
    # enum creation is handled by table DDL to avoid duplicate-create conflicts

    op.create_table(
        'patients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('external_patient_id', sa.String(128), nullable=True),
        sa.Column('patient_display_id', sa.String(128), nullable=True),
        sa.Column('sex', sa.String(32), nullable=True),
        sa.Column('birth_date', sa.Date(), nullable=True),
        sa.Column('demographics_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('consent_status', patient_consent_status, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.UniqueConstraint('external_patient_id', name='uq_patients_external_patient_id'),
    )

    op.create_table(
        'cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('case_no', sa.String(128), nullable=True),
        sa.Column('disease_domain_code', sa.String(64), nullable=True),
        sa.Column('title', sa.String(256), nullable=True),
        sa.Column('status', case_status, nullable=False),
        sa.Column('chief_complaint', sa.Text(), nullable=True),
        sa.Column('context_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.UniqueConstraint('case_no', name='uq_cases_case_no'),
    )

    op.create_table(
        'multimodal_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=True),
        sa.Column('modality_type', modality_type, nullable=False),
        sa.Column('source_type', sa.String(64), nullable=True),
        sa.Column('bucket', sa.String(128), nullable=True),
        sa.Column('object_key', sa.String(512), nullable=True),
        sa.Column('checksum_sha256', sa.String(128), nullable=True),
        sa.Column('content_type', sa.String(128), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('clinical_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trace_ref', sa.String(96), nullable=True),
        sa.Column('quality_flags_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('normalized_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )

    op.create_table(
        'clinical_observations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('observation_code', sa.String(128), nullable=False),
        sa.Column('observation_name', sa.String(256), nullable=True),
        sa.Column('value_numeric', sa.Float(), nullable=True),
        sa.Column('value_text', sa.Text(), nullable=True),
        sa.Column('value_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('unit', sa.String(64), nullable=True),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('multimodal_assets.id'), nullable=True),
        sa.Column('source_type', sa.String(64), nullable=True),
        sa.Column('provenance_level', sa.String(32), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )

    op.create_table(
        'lab_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('lab_panel_code', sa.String(128), nullable=True),
        sa.Column('test_code', sa.String(128), nullable=False),
        sa.Column('test_name', sa.String(256), nullable=True),
        sa.Column('value_numeric', sa.Float(), nullable=True),
        sa.Column('value_text', sa.Text(), nullable=True),
        sa.Column('unit', sa.String(64), nullable=True),
        sa.Column('reference_range_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('abnormal_flag', sa.String(32), nullable=True),
        sa.Column('sampled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reported_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('multimodal_assets.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )

    op.create_table(
        'emr_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('document_type', sa.String(64), nullable=False),
        sa.Column('title', sa.String(256), nullable=True),
        sa.Column('language', sa.String(16), nullable=True),
        sa.Column('bucket', sa.String(128), nullable=True),
        sa.Column('object_key', sa.String(512), nullable=True),
        sa.Column('checksum_sha256', sa.String(128), nullable=True),
        sa.Column('extracted_structured_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('authored_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )

    op.create_table(
        'model_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('model_name', sa.String(128), nullable=False),
        sa.Column('disease_agent', sa.String(64), nullable=False),
        sa.Column('task_type', sa.String(64), nullable=False),
        sa.Column('modality_scope_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('owner_team', sa.String(128), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )

    op.create_table(
        'model_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('model_registry.id'), nullable=False),
        sa.Column('version_label', sa.String(128), nullable=False),
        sa.Column('approval_state', model_approval_state, nullable=False),
        sa.Column('contract_version', sa.String(64), nullable=False),
        sa.Column('artifact_ref_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('input_schema_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('output_schema_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('metrics_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('runtime_constraints_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )

    op.create_table(
        'inference_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('trace_id', sa.String(96), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=True),
        sa.Column('disease_agent', sa.String(64), nullable=False),
        sa.Column('task_type', sa.String(64), nullable=False),
        sa.Column('status', inference_task_status, nullable=False),
        sa.Column('requested_modalities_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('model_version_policy_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('input_refs_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('missing_value_summary_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('idempotency_key', sa.String(160), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_code', sa.String(64), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.UniqueConstraint('trace_id', name='uq_inference_tasks_trace_id'),
    )

    op.create_table(
        'recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('inference_task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inference_tasks.id'), nullable=False),
        sa.Column('trace_id', sa.String(96), nullable=False),
        sa.Column('evidence_chain_id', sa.String(96), nullable=True),
        sa.Column('recommendation_version', sa.Integer(), nullable=False),
        sa.Column('recommendation_type', sa.String(64), nullable=False),
        sa.Column('status', recommendation_status, nullable=False),
        sa.Column('candidate_label', sa.String(64), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('uncertainty_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('limitations_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('evidence_refs_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('content_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_by_type', sa.String(32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )

    op.create_table(
        'doctor_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recommendations.id'), nullable=True),
        sa.Column('inference_task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inference_tasks.id'), nullable=True),
        sa.Column('trace_id', sa.String(96), nullable=False),
        sa.Column('doctor_id', sa.String(128), nullable=True),
        sa.Column('feedback_type', feedback_type, nullable=False),
        sa.Column('decision', sa.String(64), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('clinical_rationale', sa.Text(), nullable=True),
        sa.Column('correction_payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('learning_eligible', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )

    op.create_table(
        'reassessment_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('trace_id', sa.String(96), nullable=False),
        sa.Column('previous_trace_id', sa.String(96), nullable=True),
        sa.Column('previous_snapshot_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('current_snapshot_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('trigger_type', reassessment_trigger_type, nullable=False),
        sa.Column('trigger_ref', sa.String(256), nullable=True),
        sa.Column('status', reassessment_status, nullable=False),
        sa.Column('changed_input_refs_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('comparison_summary_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )

    op.create_table(
        'dynamic_state_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('snapshot_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('trace_id', sa.String(96), nullable=True),
        sa.Column('source_reassessment_job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reassessment_jobs.id'), nullable=True),
        sa.Column('state_summary_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('modality_presence_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('risk_summary_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('uncertainty_summary_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )

    op.create_table(
        'case_missing_value_queries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=True),
        sa.Column('inference_task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inference_tasks.id'), nullable=True),
        sa.Column('trace_id', sa.String(96), nullable=False),
        sa.Column('field_path', sa.String(256), nullable=False),
        sa.Column('field_label', sa.String(256), nullable=True),
        sa.Column('clinical_importance', clinical_importance, nullable=False),
        sa.Column('blocking_level', blocking_level, nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('status', missing_value_query_status, nullable=False),
        sa.Column('doctor_id', sa.String(128), nullable=True),
        sa.Column('doctor_response_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('value_source', value_source_type, nullable=False),
        sa.Column('default_strategy_code', sa.String(128), nullable=True),
        sa.Column('default_value_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('default_reason', sa.Text(), nullable=True),
        sa.Column('policy_version', sa.String(64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )

    op.create_table(
        'trace_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('trace_id', sa.String(96), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=True),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('actor_type', trace_actor_type, nullable=False),
        sa.Column('actor_id', sa.String(128), nullable=True),
        sa.Column('source_module', sa.String(64), nullable=False),
        sa.Column('source_record_type', sa.String(64), nullable=True),
        sa.Column('source_record_id', sa.String(128), nullable=True),
        sa.Column('event_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('parent_event_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('trace_events.id'), nullable=True),
        sa.Column('severity', trace_severity, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'evidence_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('trace_id', sa.String(96), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=True),
        sa.Column('evidence_chain_id', sa.String(96), nullable=False),
        sa.Column('node_type', evidence_node_type, nullable=False),
        sa.Column('source_module', sa.String(64), nullable=False),
        sa.Column('source_record_type', sa.String(64), nullable=True),
        sa.Column('source_record_id', sa.String(128), nullable=True),
        sa.Column('label', sa.String(256), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('uncertainty_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', evidence_node_status, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'evidence_edges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('trace_id', sa.String(96), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('evidence_chain_id', sa.String(96), nullable=False),
        sa.Column('source_node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('evidence_nodes.id'), nullable=False),
        sa.Column('target_node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('evidence_nodes.id'), nullable=False),
        sa.Column('edge_type', evidence_edge_type, nullable=False),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'quality_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('trace_id', sa.String(96), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=True),
        sa.Column('review_target_type', quality_target_type, nullable=False),
        sa.Column('review_target_id', sa.String(128), nullable=False),
        sa.Column('status', quality_review_status, nullable=False),
        sa.Column('severity', quality_severity, nullable=False),
        sa.Column('opened_by_type', trace_actor_type, nullable=False),
        sa.Column('opened_by_id', sa.String(128), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('error_attribution', quality_error_attribution, nullable=True),
        sa.Column('attribution_confidence', sa.Float(), nullable=True),
        sa.Column('findings_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('related_refs_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('resolution_summary', sa.Text(), nullable=True),
        sa.Column('resolved_by_type', trace_actor_type, nullable=True),
        sa.Column('resolved_by_id', sa.String(128), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )

    # Priority trace and workflow indexes
    op.create_index('ix_inference_tasks_trace_id', 'inference_tasks', ['trace_id'], unique=True)
    op.create_index('ix_recommendations_trace_id', 'recommendations', ['trace_id'])
    op.create_index('ix_recommendations_inference_task_id', 'recommendations', ['inference_task_id'])
    op.create_index('ix_case_missing_value_queries_trace_id', 'case_missing_value_queries', ['trace_id'])
    op.create_index('ix_case_missing_value_queries_case_status', 'case_missing_value_queries', ['case_id', 'status'])
    op.create_index('ix_trace_events_trace_time', 'trace_events', ['trace_id', 'event_time'])
    op.create_index('ix_evidence_nodes_trace_type', 'evidence_nodes', ['trace_id', 'node_type'])
    op.create_index('ix_evidence_edges_trace_src_tgt', 'evidence_edges', ['trace_id', 'source_node_id', 'target_node_id'])
    op.create_index('ix_quality_reviews_trace_status', 'quality_reviews', ['trace_id', 'status'])
    op.create_index('ix_dynamic_state_snapshots_case_time', 'dynamic_state_snapshots', ['case_id', 'snapshot_time'])

    op.create_foreign_key(
        'fk_reassessment_previous_snapshot',
        'reassessment_jobs',
        'dynamic_state_snapshots',
        ['previous_snapshot_id'],
        ['id'],
    )
    op.create_foreign_key(
        'fk_reassessment_current_snapshot',
        'reassessment_jobs',
        'dynamic_state_snapshots',
        ['current_snapshot_id'],
        ['id'],
    )


def downgrade() -> None:
    # Non-destructive policy: downgrade order only defined for completeness.
    op.drop_constraint('fk_reassessment_current_snapshot', 'reassessment_jobs', type_='foreignkey')
    op.drop_constraint('fk_reassessment_previous_snapshot', 'reassessment_jobs', type_='foreignkey')
    op.drop_index('ix_dynamic_state_snapshots_case_time', table_name='dynamic_state_snapshots')
    op.drop_index('ix_quality_reviews_trace_status', table_name='quality_reviews')
    op.drop_index('ix_evidence_edges_trace_src_tgt', table_name='evidence_edges')
    op.drop_index('ix_evidence_nodes_trace_type', table_name='evidence_nodes')
    op.drop_index('ix_trace_events_trace_time', table_name='trace_events')
    op.drop_index('ix_case_missing_value_queries_case_status', table_name='case_missing_value_queries')
    op.drop_index('ix_case_missing_value_queries_trace_id', table_name='case_missing_value_queries')
    op.drop_index('ix_recommendations_inference_task_id', table_name='recommendations')
    op.drop_index('ix_recommendations_trace_id', table_name='recommendations')
    op.drop_index('ix_inference_tasks_trace_id', table_name='inference_tasks')

    for table in [
        'quality_reviews', 'evidence_edges', 'evidence_nodes', 'trace_events',
        'case_missing_value_queries', 'dynamic_state_snapshots', 'reassessment_jobs',
        'doctor_feedback', 'recommendations', 'inference_tasks', 'model_versions',
        'model_registry', 'emr_documents', 'lab_results', 'clinical_observations',
        'multimodal_assets', 'cases', 'patients',
    ]:
        op.drop_table(table)

    # enum drop intentionally omitted in baseline downgrade template
