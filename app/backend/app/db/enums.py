from enum import StrEnum


class PatientConsentStatus(StrEnum):
    UNKNOWN = 'unknown'
    GRANTED = 'granted'
    WITHDRAWN = 'withdrawn'


class CaseStatus(StrEnum):
    DRAFT = 'draft'
    OPEN = 'open'
    IN_REVIEW = 'in_review'
    CLOSED = 'closed'
    ARCHIVED = 'archived'


class ModalityType(StrEnum):
    CT_IMAGE = 'ct_image'
    MRI_IMAGE = 'mri_image'
    CLINICAL_TABLE = 'clinical_table'
    LAB_RESULT = 'lab_result'
    EMR_TEXT = 'emr_text'
    WEARABLE = 'wearable'
    OTHER = 'other'


class InferenceTaskStatus(StrEnum):
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    PARTIAL = 'partial'
    CANCELED = 'canceled'


class RecommendationStatus(StrEnum):
    DRAFT = 'draft'
    ACTIVE = 'active'
    SUPERSEDED = 'superseded'
    RETRACTED = 'retracted'


class FeedbackType(StrEnum):
    ACCEPT = 'accept'
    REJECT = 'reject'
    EDIT = 'edit'
    COMMENT = 'comment'
    FLAG = 'flag'


class ReassessmentTriggerType(StrEnum):
    NEW_INPUT = 'new_input'
    MANUAL_REQUEST = 'manual_request'
    SCHEDULED = 'scheduled'
    QC_REQUEST = 'qc_request'


class ReassessmentStatus(StrEnum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELED = 'canceled'


class ClinicalImportance(StrEnum):
    REQUIRED = 'required'
    RECOMMENDED = 'recommended'
    OPTIONAL = 'optional'


class BlockingLevel(StrEnum):
    BLOCKING = 'blocking'
    DEGRADES_CONFIDENCE = 'degrades_confidence'
    INFORMATIONAL = 'informational'


class MissingValueQueryStatus(StrEnum):
    PENDING = 'pending'
    ANSWERED = 'answered'
    DEFAULT_APPLIED = 'default_applied'
    WAIVED_BY_DOCTOR = 'waived_by_doctor'
    EXPIRED = 'expired'


class ValueSourceType(StrEnum):
    DOCTOR_PROVIDED = 'doctor_provided'
    DEFAULT_APPLIED = 'default_applied'
    WAIVED = 'waived'
    UNKNOWN = 'unknown'


class TraceActorType(StrEnum):
    DOCTOR = 'doctor'
    SYSTEM = 'system'
    ORCHESTRATOR = 'orchestrator'
    DISEASE_AGENT = 'disease_agent'
    SMALL_MODEL = 'small_model'
    LARGE_MODEL = 'large_model'
    QC_AGENT = 'qc_agent'
    ADMIN = 'admin'


class TraceSeverity(StrEnum):
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


class EvidenceNodeType(StrEnum):
    INPUT = 'input'
    CLINICAL_FEATURE = 'clinical_feature'
    LAB_RESULT = 'lab_result'
    IMAGE_FINDING = 'image_finding'
    MODEL_OUTPUT = 'model_output'
    RULE_RESULT = 'rule_result'
    LLM_REASONING_STEP = 'llm_reasoning_step'
    RECOMMENDATION = 'recommendation'
    DOCTOR_FEEDBACK = 'doctor_feedback'


class EvidenceNodeStatus(StrEnum):
    ACTIVE = 'active'
    SUPERSEDED = 'superseded'
    RETRACTED = 'retracted'
    CONFLICTED = 'conflicted'
    DEFAULTED = 'defaulted'


class EvidenceEdgeType(StrEnum):
    SUPPORTS = 'supports'
    CONTRADICTS = 'contradicts'
    DERIVED_FROM = 'derived_from'
    REFERENCES = 'references'
    OVERRIDES = 'overrides'
    MISSING_VALUE_DEFAULTED = 'missing_value_defaulted'


class QualityTargetType(StrEnum):
    RECOMMENDATION = 'recommendation'
    TRACE = 'trace'
    MODEL_OUTPUT = 'model_output'
    MISSING_VALUE_DECISION = 'missing_value_decision'
    REASSESSMENT = 'reassessment'


class QualityReviewStatus(StrEnum):
    OPEN = 'open'
    INVESTIGATING = 'investigating'
    RESOLVED = 'resolved'
    DISMISSED = 'dismissed'


class QualitySeverity(StrEnum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class QualityErrorAttribution(StrEnum):
    DATA_QUALITY = 'data_quality'
    MODEL_ERROR = 'model_error'
    ORCHESTRATION_ERROR = 'orchestration_error'
    MISSING_VALUE_POLICY = 'missing_value_policy'
    HUMAN_FEEDBACK = 'human_feedback'
    SYSTEM_ERROR = 'system_error'


class ModelApprovalState(StrEnum):
    DRAFT = 'draft'
    OFFLINE_EVALUATED = 'offline_evaluated'
    APPROVED = 'approved'
    SHADOW = 'shadow'
    CANARY = 'canary'
    DEFAULT = 'default'
    DEPRECATED = 'deprecated'
    ARCHIVED = 'archived'
