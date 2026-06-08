# Coursework Stage C4: CAP/COP Imaging Input API / Data Contract Design

## Verdict
- Current backend has reusable case/model-input/shadow-audit/access-audit plumbing.
- A dedicated imaging ingress contract is still missing.
- The safest course is to define a separate imaging input contract now, without merging it into `case_model_input_snapshot`.
- The contract should be treated as **not-for-diagnosis**, **shadow-ready**, and **separate from the tabular CAP/COP clinical MLP snapshot**.

## Existing Backend Capability Survey

### What is already present in backend
- `assets` module exists in the backend tree (`app/backend/app/modules/assets/*`).
- `cases` module exists and already carries `case_id`, `patient_id`, `trace_id` style linkage used across workflow APIs.
- `model_input` module exists and already supports:
  - model input schema lookup
  - feature requirements lookup
  - case model input preview
  - case model input validation
  - case model input snapshot creation/list/get
  - one-shot clinical MLP shadow invocation
- `shadow_audit` module exists and already supports shadow run and shadow output read/write flows.
- `access_audit` module exists and already supports read-side audit inspection.

### What is not yet verified as a dedicated imaging ingress
- No dedicated imaging upload / imaging-input / case-attachment API was verified in the accessible client surface.
- No backend contract was observed for:
  - DICOM/NIfTI ingress
  - image asset registration
  - image quality gating
  - image provenance reference structure
  - image-to-case linking semantics for the course demo
- No evidence was found in the reviewed client surface that a frontend or API already treats imaging as a first-class input contract.

### Reusable patterns already available
- `case_id` / `patient_id` / `trace_id` are established as first-class linkage keys.
- `not_for_diagnosis` and shadow-only semantics already exist in the clinical MLP flow.
- Access audit and shadow audit already provide a clear separation between:
  - who accessed what
  - what was executed in shadow
  - what was merely read or uploaded

## Gap
- The project does not yet have a dedicated, explicit imaging input contract for the CAP/COP course workflow.
- The model-input snapshot object is tabular and should not be overloaded to carry raw imaging payloads.
- The course needs an ingress contract that can reference a CT/NIfTI object and later feed an imaging runner without becoming a diagnosis or evidence object.

## Recommended Imaging Input Contract

### Core identifiers
- `case_id`
- `patient_id`
- `trace_id`
- `input_asset_id` or `image_input_id`

### Modality and source
- `modality`
  - `CT`
  - `NIfTI`
  - `demo_image`
  - `synthetic_visual_sample`
- `source_type`
  - `real_deidentified`
  - `synthetic`
  - `demo`

### Storage / provenance
- `storage_uri` or managed object reference
- `deidentified = true`
- `not_for_diagnosis = true`
- `provenance_json`
- `quality_flags_json`

### Suggested optional fields
- `content_hash`
- `mime_type`
- `storage_backend`
- `created_at`
- `updated_at`

## Recommended API Surface Draft

### Create / register
- `POST /api/v1/cases/{case_id}/imaging-inputs`

### Read by case
- `GET /api/v1/cases/{case_id}/imaging-inputs`

### Read by resource
- `GET /api/v1/imaging-inputs/{input_asset_id}`

### Suggested request body
```json
{
  "patient_id": "uuid-or-stable-id",
  "trace_id": "trace-stable-id",
  "modality": "CT",
  "source_type": "real_deidentified",
  "storage_uri": "managed://object-store/path-or-uri",
  "deidentified": true,
  "not_for_diagnosis": true,
  "provenance_json": {
    "origin": "coursework-demo",
    "capture_mode": "manual-registration",
    "source_case_link": "case-or-study-reference"
  },
  "quality_flags_json": {
    "artifact_free": true,
    "slice_count_ok": true,
    "orientation_ok": true
  }
}
```

### Suggested response body
```json
{
  "input_asset_id": "img_...",
  "case_id": "uuid",
  "patient_id": "uuid",
  "trace_id": "trace-id",
  "modality": "CT",
  "source_type": "real_deidentified",
  "storage_uri": "managed://...",
  "deidentified": true,
  "not_for_diagnosis": true,
  "provenance_json": {},
  "quality_flags_json": {},
  "created_at": "2026-06-08T00:00:00Z",
  "updated_at": "2026-06-08T00:00:00Z"
}
```

## How a Future Imaging Runner Would Use It
- The imaging runner should consume `input_asset_id` / `storage_uri` plus modality metadata.
- The runner should resolve the object, load only the declared imaging asset, and never scan the directory for other series.
- The imaging input contract should be a reference object, not the image payload itself.
- The future runner should be able to reference a `case_model_input_snapshot` for multimodal combinations, but the imaging ingress and the tabular snapshot must remain separate resources.

## Boundary With `case_model_input_snapshot`
- `case_model_input_snapshot` is tabular CAP/COP feature provenance.
- Imaging input is volume / image provenance.
- They may reference each other through `case_id`, `patient_id`, and `trace_id`.
- They must **not** be merged into one payload.
- The model-input snapshot should not become a container for raw CT / NIfTI bytes.
- The imaging input contract should not become a surrogate for tabular features.

## Boundary With Access Audit / Shadow Audit / Trace Evidence

### Access audit
- Upload, list, read, or runner-reference operations may warrant access audit entries.
- Access audit should capture who touched the imaging input and which resource was accessed.
- Access audit must not store raw imaging bytes or derived clinical conclusions.

### Shadow audit
- When a future imaging runner executes, its result should go to shadow audit.
- Shadow audit can store output provenance, confidence, and limitations.
- Shadow audit should not be turned into a clinical evidence graph.

### Trace / evidence
- Imaging ingestion itself should not write `trace_events`, `evidence_nodes`, or `evidence_edges`.
- The course workflow should not pretend that upload or read equals clinical evidence.
- If evidence is needed later, it should be a separate, explicitly approved design.

## If We Need Persistence Later

### Likely tables
- `case_imaging_inputs`
- optionally `case_imaging_input_assets` if object-store metadata needs to be split
- optionally `case_digital_twin_states` for derived case-level state

### Likely fields
- `id`
- `input_asset_id` unique
- `case_id` FK
- `patient_id` FK
- `trace_id` indexed
- `modality`
- `source_type`
- `storage_uri`
- `deidentified`
- `not_for_diagnosis`
- `provenance_json`
- `quality_flags_json`
- `content_hash`
- `created_at`
- `updated_at`

### Likely indexes / constraints
- unique `input_asset_id`
- index `case_id`
- index `patient_id`
- index `trace_id`
- index `modality`
- index `source_type`
- index `(case_id, created_at)`
- index `(trace_id, modality)`

### Likely FK guidance
- `case_id -> cases.id`
- `patient_id -> patients.id`
- `trace_id` as query key, not necessarily a hard FK

## Course Demo Fallback If Nothing Is Persisted Yet
- Use a demo-only JSON fixture that carries the imaging contract fields.
- Keep the payload in-memory or in a temporary file under a clearly marked demo path.
- Do not create a false impression that the demo object is a validated clinical imaging record.
- The demo fallback should explicitly label:
  - `source_type = demo`
  - `deidentified = true`
  - `not_for_diagnosis = true`
  - `shadow_only = true` when the runner is invoked

## Digital Twin Relationship
- The course digital twin is a derived case-level state, not the raw imaging object.
- A future digital twin state can reference:
  - `imaging_input_id`
  - `case_model_input_snapshot_id`
  - `shadow_run_id`
- The digital twin state should store summaries and quality flags, not raw pixels or the full volumetric payload.
- The imaging input contract is an input reference; the digital twin is a derived state.

## What We Cannot Claim Yet
- We cannot claim the backend already has a verified imaging ingress API.
- We cannot claim the current backend has a deidentified CT/NIfTI object contract suitable for production use.
- We cannot claim the course imaging workflow is diagnostic.
- We cannot claim any model performance, calibration, or clinical utility from this contract alone.
- We cannot claim the imaging payload is sufficient for a digital twin without a separate runner and validation path.

## Recommended Next Step
- **Recommend backend candidate migration / API skeleton first.**
- Reason: the imaging input contract is the least ambiguous foundation and should be frozen before frontend polish.
- After the backend contract exists, add a frontend digital-twin mock that consumes demo fixtures.
- A runner prototype should wait until the imaging input contract is stabilized.

## File References
- `/home/sygxdg/MedOrion/docs/coursework/COURSEWORK_STAGE_C2_VISION_TASK_AND_IMAGING_READINESS.md`
- `/home/sygxdg/MedOrion/docs/coursework/COURSEWORK_STAGE_C3_IMAGING_RESNET18_PROVENANCE_AND_RUNNER_PLAN.md`
- `/home/sygxdg/MedOrion/docs/coursework/CAP_COP_DIGITAL_TWIN_SCIENTIFIC_PROTOCOL.md`
- `/home/sygxdg/MedOrion/docs/architecture/SOURCE_OF_TRUTH.md`

