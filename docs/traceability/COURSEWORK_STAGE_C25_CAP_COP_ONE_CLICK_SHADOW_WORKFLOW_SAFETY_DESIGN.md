# Coursework Stage C25: CAP/COP One-Click Shadow Workflow Safety Design
## Verdict
- The one-click CAP/COP shadow workflow is safe only when it behaves as a gated orchestration preview, not as a blind clinical action.
- The button may appear only when at least one CAP/COP shadow path is explicitly eligible, the case is in scope, and all hard prerequisites for the selected branch are satisfied.
- The workflow must fail closed, must not silently fall back between model families, and must never write recommendation or case trace/evidence records from the coursework shadow action.
## Files Read
- /home/sygxdg/MedOrion/docs/backend/COURSEWORK_STAGE_C21_DICOM_PREPROCESSING_API_CONTRACT.md
- /home/sygxdg/MedOrion/docs/model_orchestration/COURSEWORK_STAGE_C17_MULTIMODAL_RESNET18_PROVENANCE_AND_RUNNER_PLAN.md
- /home/sygxdg/MedOrion/docs/model_orchestration/COURSEWORK_STAGE_C18_MULTIMODAL_RESNET18_RUNNER_PROTOTYPE.md
- /home/sygxdg/MedOrion/docs/model_orchestration/COURSEWORK_STAGE_C13_IMAGING_RESNET18_REAL_RUNNER_PREFLIGHT.md
- /home/sygxdg/MedOrion/docs/model_orchestration/COURSEWORK_STAGE_C14_IMAGING_RESNET18_REAL_SHADOW_RUNNER_MINIMAL_CANDIDATE.md
- /home/sygxdg/MedOrion/docs/architecture/SOURCE_OF_TRUTH.md
- /home/sygxdg/MedOrion/app/frontend/src/app/cases/[caseId]/shadow-audit/page.tsx
- /home/sygxdg/MedOrion/app/frontend/src/app/cases/[caseId]/model-input/page.tsx
- /home/sygxdg/MedOrion/app/frontend/src/app/cases/[caseId]/page.tsx
## Safety Conclusion
- CAP/COP one-click shadow should be framed as a case-scoped workflow gate.
- The workflow may evaluate clinical MLP, imaging ResNet18, and multimodal ResNet18, but it must not treat one branch as an invisible substitute for another.
- Any branch that lacks its required inputs or approvals must be explicitly disabled and explained.
- Synthetic / demo imaging inputs may be used only when clearly labeled coursework/demo and never as a clinical result.
- Shadow outputs may be shown as audit results and candidate labels only, never as diagnosis, never as formal recommendation.
## Workflow State Machine

- CaseSelected -> AuthChecked -> InputInventoryChecked -> ReadyCheck
- ReadyCheck -> Disabled when no eligible branch remains or a hard gate fails
- ReadyCheck -> Eligible when at least one branch is ready
- Eligible -> ShadowRunning after the user explicitly confirms one-click shadow
- ShadowRunning -> ShadowCompleted when all scheduled branches finish
- ShadowRunning -> ShadowFailed when any branch fails hard

### State meanings
- CaseSelected: user opened a case-level workbench.
- AuthChecked: case-scoped access was verified.
- InputInventoryChecked: clinical snapshot, imaging inputs, preprocessing status, and model registry status were collected.
- ReadyCheck: the system evaluates branch-level readiness.
- Disabled: no eligible branch or a hard safety gate failed.
- Eligible: one or more branches are ready and the button may be shown or enabled.
- ShadowRunning: the explicit one-click action has started a shadow-only execution.
- ShadowCompleted: the scheduled branch results have been written to shadow audit.
- ShadowFailed: execution stopped due to a non-recoverable error; no clinical recommendation is produced.
## Input Readiness Matrix
| Branch | Required inputs | Hard gates | Disabled reasons | Output handling |
|---|---|---|---|---|
| Clinical MLP | case_id, case access, case_model_input_snapshot, validation_status=ready_for_inference, current_assessment_status=ready_for_inference, not_for_diagnosis=true, runtime_stub=true or approved shadow bridge, allowlisted model version, verified schema | schema must be verified; no missing required features; no policy mismatch | clinical_schema_unverified, clinical_input_insufficient, missing_snapshot, model_not_allowlisted, runtime_safety_not_ready | emit shadow audit only; no recommendation; no trace/evidence |
| Imaging ResNet18 | case_id, case access, imaging input reference, preprocessing completed, deidentified input, not_for_diagnosis=true, approved model version, exact artifact provenance | preprocessing must be complete; no raw DICOM pretending to be ready | imaging_preprocessing_pending, imaging_preprocessing_failed, missing_imaging_input, source_not_deidentified, demo_only_input | emit shadow audit only; no recommendation; no trace/evidence |
| Multimodal ResNet18 | all clinical MLP requirements + all imaging ResNet18 requirements + fusion contract ready | both branches must be ready; input references must belong to the same case | clinical_schema_unverified, clinical_input_insufficient, imaging_preprocessing_pending, imaging_preprocessing_failed, modalities_mismatch, demo_only_input | emit shadow audit only; no recommendation; no trace/evidence |
## Disabled State Reasons
- missing_case_access
- missing_snapshot
- clinical_schema_unverified
- clinical_input_insufficient
- missing_imaging_input
- imaging_preprocessing_pending
- imaging_preprocessing_failed
- source_not_deidentified
- demo_only_input
- model_not_allowlisted
- runtime_safety_not_ready
- shadow_switch_disabled
- no_eligible_branch
- quality_review_required
- doctor_review_required
- modalities_mismatch
## Model Execution Order
The workflow should use a fixed evaluation order, but it must not silently fall back between branches.
1. **Case scope and safety gate**
   - Check auth, case access, not_for_diagnosis, and runtime safety configuration.
2. **Clinical readiness gate**
   - If the product-side clinical schema is verified and the snapshot is ready, the clinical MLP branch becomes eligible.
   - If clinical_schema_unverified, skip the branch and record the disabled reason.
3. **Imaging readiness gate**
   - If imaging input exists and preprocessing is completed, the imaging ResNet18 branch becomes eligible.
   - If only raw DICOM exists, preprocessing must finish first.
4. **Multimodal readiness gate**
   - Multimodal is eligible only when both clinical and imaging branches are ready and belong to the same case.
5. **Branch scheduling**
   - The one-click workflow may schedule only the branches that are already eligible.
   - A disabled branch must stay disabled; the system must not silently substitute another model family.
### Recommended ordering policy
- For a conservative coursework one-click workflow, use: **multimodal first when fully ready**, otherwise **the explicitly eligible unimodal branch**.
- If the UX wants comparison mode, schedule multiple eligible branches in a declared list, but keep each branch isolated and explicitly labeled.
- Never treat a failed multimodal branch as permission to auto-run another branch without user-visible policy.
## Readiness Rules by Input Type
### 1. Clinical schema unverified
- Skip clinical MLP.
- Show the branch as disabled with a clear reason.
- If imaging is ready, imaging may still be eligible.
- If multimodal depends on that clinical schema, multimodal stays disabled.
### 2. Only DICOM series available
- Raw DICOM is not enough.
- Preprocessing must complete first.
- The workflow must not pretend the case is model-ready.
### 3. Synthetic NIfTI only
- May be used only as coursework/demo.
- Must be labeled demo_only_input or equivalent.
- Must not be presented as a clinical case input.
- Must not enable any clinical recommendation language.
### 4. Multimodal requirements
- Both clinical and imaging inputs must exist.
- Both must be case-scoped and provenance-linked.
- Both must have compatible readiness status.
- Both must be explicitly approved for the same shadow workflow.
## Allowed Output Language
Use language such as:
- shadow candidate label
- CAP/COP 倾向
- 旁路评估
- 审计结果
- 未校准概率
- 需要医生复核
- 需要质控复核
- 预处理完成 / 待补齐
- 仅供 shadow 审计和复核参考
- demo / coursework input
## Forbidden Output Language
Do not use language such as:
- diagnosis / 诊断 / 临床确诊
- formal recommendation / 正式推荐
- treatment advice / 治疗建议
- prescribe / 处方 / 用药建议
- model says the patient has CAP/COP
- substitute for a doctor
- definitive certainty
- canary / default / production-ready
- clinically validated if not actually validated
## Audit / Shadow Audit Rules
- The one-click action should create an access audit record for the user-visible click and policy decision.
- Each executed branch should create shadow audit records only.
- Shadow audit may store candidate label, confidence, uncertainty, limitation markers, and provenance references.
- Shadow audit must not write recommendation, trace events, evidence nodes, or evidence edges.
- If a branch is blocked, the audit should capture the disabled reason instead of rerouting to another branch.
- Audit writes must never be allowed to create a clinical conclusion by accident.
## Failure Handling
- Hard gate failures must fail closed.
- Transient infrastructure failures may be retried only on the same declared branch and with the same trace / case scope.
- Do not retry by switching to another model family.
- Do not hide a failure behind a successful-looking shadow result.
- If no eligible branch remains, the workflow stays disabled and explains why.
- If a branch times out or is unavailable, the result must remain a shadow failure, not a recommendation.
## User-Facing Safety Wording
Recommended copy for the page and workflow button:
- Shadow only
- Not for diagnosis
- Not a formal recommendation
- Requires doctor review
- Requires quality review before clinical use
- Probability is uncalibrated
- Extreme probability is not clinical certainty
- Demo inputs are coursework only
- Disabled until inputs and approvals are complete
The button label should be something like:
- 一键 CAP/COP Shadow
- or 评估 CAP/COP Shadow 候选
Avoid labels such as:
- 开始诊断
- 生成推荐
- 提交治疗方案
- 自动评估并确诊
## Failure / Disabled State Copy
When disabled, show the reason explicitly, for example:
- clinical schema 未验证
- DICOM preprocessing pending
- 仅有 synthetic/demo 输入
- model version 未批准
- 不是 shadow-enabled 状态
- 缺少病例级访问权限
## Recommended Next Implementation Stage
### Recommendation: C26
Implement a **read-only shadow workflow readiness skeleton** before any new one-click execution wiring.
C26 should focus on:
- a readiness matrix endpoint or service helper,
- explicit disabled reason calculation,
- case-scoped authorization checks,
- frontend button enable/disable states,
- and visible safety messaging.
Do **not** move straight to a broader execution button if the readiness contract is still evolving.
## Compliance Boundary
- Read-only review and documentation only.
- No code changes.
- No database changes.
- No Alembic upgrade, stamp, or downgrade.
- No model loading.
- No DICOM/NIfTI reads.
- No scanning, copying, or moving model files.
- No training.
- No recommendation writes.
- No trace/evidence writes.
- No shadow audit writes.
- No real clinical diagnosis language.
- No default/canary/production promotion.
