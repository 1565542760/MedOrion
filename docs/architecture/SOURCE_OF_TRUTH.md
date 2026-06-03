# MedOrion Architecture Source of Truth

Last updated: 2026-06-02 Asia/Shanghai
Owner thread: MedOrion general architecture collaboration Codex
Remote workspace: /home/sygxdg/MedOrion

## 1. Project Positioning

MedOrion is a multimodal medical intelligent-agent assisted diagnosis platform for doctors. It supports clinical decision support, explanation, evidence aggregation, and follow-up reassessment. It does not replace doctors' diagnosis.

CAP/COP is the first-stage demonstration disease task only. It must not constrain MedOrion into a single-disease system.

## 2. Non-Negotiable Principles

1. Multi-disease extensibility is a first-class architectural requirement.
2. Multimodal input must be supported: CT, MRI, clinical tables, electronic medical records, laboratory indicators, and future dynamic wearable-device data.
3. The system uses disease-specific agents on top of a shared general capability foundation.
4. Small/specialized models handle disease-specific prediction and judgement; large models handle orchestration, explanation, doctor-facing Q&A, and recommendation generation.
5. Every generated suggestion must carry a trace_id and evidence chain.
6. Missing table values must first trigger an active question to the doctor. If the doctor does not resolve them, the system applies a configured default strategy and records that decision in the trace.
7. Continuous learning must not mean automatic real-time training.
8. Dynamic disease feedback means newly added patient data can trigger state reassessment; it does not mean real-time model training.

## 3. Target Architecture Layers

### 3.1 Interaction Layer

Doctor-facing interfaces, patient case workspace, upload/review flows, evidence visualization, Q&A, and recommendation review. Frontend implementation details belong to frontend-specific threads.

### 3.2 Orchestration Layer

The large-model agent layer is responsible for:

- routing tasks to disease agents and shared services;
- deciding which modalities are required or missing;
- asking doctors for missing critical information;
- generating explanations, summaries, Q&A answers, and recommendations;
- enforcing trace_id creation and evidence-chain completeness.

### 3.3 Disease-Agent Layer

Each disease agent owns disease-specific workflow logic, required inputs, specialized models, rules, thresholds, evaluation metrics, and explanation templates.

Initial agent: CAP/COP demonstration agent.

Future agents must follow the same contract rather than forking the platform architecture.

### 3.4 Shared Capability Foundation

Shared services include:

- multimodal data ingestion;
- data normalization and validation;
- image preprocessing adapters;
- clinical table schema management;
- EMR/lab text parsing and retrieval;
- evidence-chain and trace registry;
- model registry and model versioning;
- prompt/template registry;
- audit logging;
- evaluation and feedback datasets;
- doctor feedback collection;
- controlled retraining workflow.

### 3.5 Model Layer

Small/specialized models provide disease-specific outputs, such as classification, risk score, segmentation, abnormality detection, or calibrated probability.

Large models do not silently override specialized model results. They may explain, reconcile, ask for more data, and present uncertainty.

## 4. Core Data Flow

1. Case is created or updated.
2. Inputs are ingested by modality adapters.
3. Validation checks required fields, modality completeness, and quality issues.
4. Missing table values trigger doctor-facing questions.
5. If unresolved, default missing-value strategy is applied and recorded.
6. Orchestrator selects relevant disease agent(s).
7. Disease agent calls specialized model(s) and disease rules.
8. Evidence chain is assembled under a trace_id.
9. Large model generates explanation and recommendation using evidence-bound context.
10. Doctor reviews, accepts, rejects, edits, or requests clarification.
11. Feedback is stored for later evaluation and controlled learning, not automatic real-time training.

## 5. Trace and Evidence Requirements

Every recommendation must include:

- trace_id;
- patient/case identifier reference;
- timestamp;
- data modality references used;
- model names and versions;
- prompt/template version where applicable;
- missing-value handling record;
- intermediate disease-agent outputs;
- generated recommendation;
- uncertainty and caveats;
- doctor feedback status.

## 6. Missing-Value Policy

Default order:

1. identify missing or invalid fields;
2. classify clinical importance;
3. ask the doctor to provide or confirm values;
4. wait according to product workflow policy;
5. if unresolved, apply disease-agent-specific default strategy;
6. record strategy, affected fields, and impact in the trace.

No silent imputation is allowed for doctor-facing recommendations.

## 7. Continuous Learning Policy

Allowed:

- collect doctor feedback;
- collect later outcome labels;
- build versioned evaluation datasets;
- schedule offline retraining or fine-tuning;
- run validation and approval before deployment;
- release new model versions through a registry.

Not allowed:

- automatic real-time training from live doctor edits;
- unversioned model replacement;
- changing recommendation behavior without traceable version records.

## 8. Dynamic Condition Feedback

When new CT/MRI, labs, EMR notes, vitals, wearable data, or doctor observations are added, MedOrion may rerun validation, orchestration, disease-agent judgement, and recommendation generation.

This is patient-state reassessment. It is not model training.

## 9. MVP Scope

MVP should prove the platform pattern with CAP/COP while preserving multi-disease extensibility.

Recommended MVP boundaries:

- one CAP/COP disease agent;
- multimodal case container;
- CT/image input adapter placeholder or initial pipeline;
- clinical table/lab input schema with missing-value workflow;
- EMR text ingestion placeholder or lightweight parsing;
- trace_id evidence chain for every recommendation;
- large-model orchestration and explanation interface contract;
- doctor feedback capture;
- model registry metadata, even if the first model is simple or mocked.

Out of MVP:

- real-time wearable ingestion at production scale;
- automatic online learning;
- full hospital information-system integration;
- broad disease library;
- regulatory-grade clinical deployment claims.

## 10. Naming Conventions

Project name: MedOrion

Recommended module vocabulary:

- disease_agent: disease-specific agent implementation;
- orchestrator: large-model routing and reasoning coordinator;
- modality_adapter: CT, MRI, table, EMR, lab, wearable ingestion adapters;
- evidence_chain: traceable evidence package;
- trace_id: unique recommendation trace identifier;
- model_registry: versioned model metadata;
- feedback_store: doctor and outcome feedback records;
- reassessment: rerun after new patient data;
- continuous_learning: offline, governed learning workflow only.

Avoid naming that implies replacement of doctors, automatic diagnosis authority, or real-time self-training.

## 11. Current Remote Environment Snapshot

Checked on 2026-05-31:

- OS: Ubuntu 24.04.4 LTS
- Kernel: 6.17.0-20-generic
- CPU: AMD Ryzen 7 5800H, 16 logical CPUs
- Memory: 15 GiB RAM, 4 GiB swap
- Root disk: 457 GiB total, 397 GiB available
- Home disk: 469 GiB total, 79 GiB available
- Python: /usr/bin/python3, Python 3.12.3
- pip: 24.0
- python3-venv: available
- Conda: /home/sygxdg/miniconda3, conda 26.1.1
- Existing conda envs: base, DL, MRI3D, hert, intelipress
- Git: 2.43.0
- Docker: 29.1.3, service active and enabled
- Docker Compose: 2.40.3
- Nginx: 1.24.0, installed but inactive and disabled
- Node.js: v22.22.2
- npm: 10.9.7
- ripgrep: 14.1.0
- GPU: NVIDIA GeForce RTX 3050 Laptop GPU, 4 GiB VRAM
- NVIDIA driver: 535.309.01
- CUDA runtime shown by nvidia-smi: 12.2
- Still not installed or not found in PATH: pnpm, uv, nvcc
- Nginx is intentionally stopped; ports 80 and 443 are not listening after foundation install.
- Infra services are running healthy: PostgreSQL on 127.0.0.1:5432, Redis on 127.0.0.1:6379, MinIO API on 127.0.0.1:9000, and MinIO Console on 127.0.0.1:9001.
- sudo channel was resolved for the foundation install. The password was not written to project files or reports.
- /srv/medorion directory structure exists and deployment drafts were copied to /srv/medorion/deploy.

## 12. MVP Deployment Direction

Deployment-specific implementation belongs to the deployment thread, but the following architecture constraints are accepted globally:

- Use Docker Compose as the MVP deployment foundation.
- Keep public exposure disabled until explicit approval.
- Prefer local, bind-to-127.0.0.1 services during stub and MVP phases.

## 13. Stage Snapshot

Current delivery stage: `Stage 42 preparation: MVP skeleton through persistent orchestration audit completed`

Completed capability set:

- Auth/RBAC skeleton.
- Frontend login/proxy flow.
- Formal patient/case creation.
- Model-service stub integration.
- Trace/evidence persistence.
- Missing-value consultation.
- Doctor feedback.
- Quality review.
- Model registry lifecycle skeleton.
- Agent gateway skeleton.
- Multi-agent orchestration skeleton.
- Orchestration audit persistence loop.

Not yet production complete:

- Real model inference and real model loading.
- Public Nginx/HTTPS deployment.
- Full model lifecycle management.
- Automated training.
- Database externalization and restore drills.
- Orchestration audit is not yet automatically mirrored into case trace/evidence tables.

