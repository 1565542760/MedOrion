# Stage 43 MVP Skeleton Acceptance

## Summary
- Stage 43 verified runtime services, auth, patient/case, inference, trace/evidence, missing-values, feedback, quality review, model registry, agent gateway, and orchestration endpoints.
- Dev validation data was created only where necessary; no data was deleted.
- Orchestration audit remains persisted only in orchestration audit tables and is not written into case trace/evidence tables.

## 1. Service Status
- docker compose ps: PASS (200)
  - body: `NAME                       IMAGE                          COMMAND                   SERVICE         CREATED        STATUS                  PORTS medorion-backend-1         medorion/backend:local         "uvicorn app.main:ap…"   backend         12 hours ago   Up 12 hours             127.0.0.1:8000->8000/tcp medorion-minio-1           minio/minio:latest             "/usr/bin/docker-ent…"   minio    `
- frontend dev server on 3000: PASS
- backend on 8000: PASS
- model-service on 8100: PASS
- postgres on 5432: PASS
- redis on 6379: PASS
- minio on 9000/9001: PASS
- nginx disabled/inactive: PASS

## 2. Health Checks
- frontend_health_ready: PASS (200)
  - body: `{"status":"ready","service":"backend","checks":{"config_loaded":true,"database":{"ok":true,"detail":"ok"}}}`
- backend_health_ready: PASS (200)
  - body: `{"status":"ready","service":"backend","checks":{"config_loaded":true,"database":{"ok":true,"detail":"ok"}}}`
- model_health: PASS (200)
  - body: `{"status":"ok","service":"model-service-stub","service_version":"0.1.0-stage02-stub","cpu_mode":true,"default_batch_size":1,"max_concurrency":1,"registered_model_count":2,"timestamp":"2026-06-03T04:00:44.231942+00:00"}`

## 3. Auth
- auth_login: PASS (200)
  - body: `{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0ZDg0NDZlMC1hMjkwLTQ4ZjMtYjc5MC02YzhlYmY2NWQ5ZDIiLCJ1c2VybmFtZSI6ImRldl9kb2N0b3IiLCJyb2xlIjoiZG9jdG9yIiwidHlwIjoiYWNjZXNzIiwiZXhwIjoxNzgwNDYwMTQ0LCJpYXQiOjE3ODA0NTkyNDQsImp0aSI6IjlhMjI2OWY1MTMxYTRkMTY5M2Y3NzJhNTJkZTUyYTQ3In0.Y5ph14yYCNaXZZsQPSMpktcuZIRMPimUEnJGh8KRSZA","refresh_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI`
- auth_me: PASS (200)
  - body: `{"user_id":"4d8446e0-a290-48f3-b790-6c8ebf65d9d2","username":"dev_doctor","display_name":"Dev Doctor","email":"dev_doctor@example.com","role":"doctor","is_active":true}`
- auth_refresh: PASS (200)
  - body: `{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0ZDg0NDZlMC1hMjkwLTQ4ZjMtYjc5MC02YzhlYmY2NWQ5ZDIiLCJ1c2VybmFtZSI6ImRldl9kb2N0b3IiLCJyb2xlIjoiZG9jdG9yIiwidHlwIjoiYWNjZXNzIiwiZXhwIjoxNzgwNDYwMTQ0LCJpYXQiOjE3ODA0NTkyNDQsImp0aSI6ImVhMTk3MzAzYzAwZjRmMWI5YWYzY2FhNWMxN2E2MTYwIn0.0Eyh2XXG5Rht_Vhuzmh0nRq_yNATximYpmFH7Vdc8IQ","refresh_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI`
- auth_logout: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/auth/logout","runtime_stub":true}`
- auth_refresh_after_logout: PASS (401)
  - body: `{"detail":{"code":"refresh_revoked","message":"Refresh token revoked"}}`

## 4. Patient / Case
- patient_id: `a84ca02e-edd0-4488-971e-1d30d6f207e3`
- case_id: `4a47ae8c-5311-49be-a71e-3415f5c3f223`
- case_get: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/cases/4a47ae8c-5311-49be-a71e-3415f5c3f223","item":{"case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","patient_id":"a84ca02e-edd0-4488-971e-1d30d6f207e3","case_no":"STAGE43-DEV-459340","disease_task":"capcop","status":"open","trace_id":"","chief_complaint":"stage43 acceptance case","created_at":"2026-06-03T04:02:20.421916Z","updated_at":"2026-06-03T04:02:20.421916Z"}`

## 5. Inference / Trace / Evidence
- inference: PASS (200)
  - body: `{"status":"stub","route":"/api/v1/cases/4a47ae8c-5311-49be-a71e-3415f5c3f223/inference-tasks","task_id":"443117a3-154b-4c7f-8dd5-b7fc6acbf337","trace_id":"trace_stub_51062663bccf","model_invocation_id":"inv_6cbc4b61a9a7","model_version_id":"capcop_stub_v1","confidence":{"score":0.0,"level":"not_applicable_stub"},"uncertainty":{"level":"high","reasons":["stub_service_no_real_model_loaded","not_for_`
- trace_detail: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/traces/trace_stub_51062663bccf","trace_id":"trace_stub_51062663bccf","case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","patient_id":"a84ca02e-edd0-4488-971e-1d30d6f207e3","event_count":5,"evidence_node_count":2,"evidence_edge_count":1}`
- trace_events: PASS (200)
  - body: `{"items":[{"event_id":"bf3f9133-22ae-4b37-adad-554bbe41b4c6","trace_id":"trace_stub_51062663bccf","event_type":"inference_task_created","event_time":"2026-06-03 04:02:20.434913+00","actor_type":"orchestrator","source_module":"backend","severity":"info","parent_event_id":null,"source_record_type":"inference_task","source_record_id":"443117a3-154b-4c7f-8dd5-b7fc6acbf337","payload":{"runtime_stub":tr`
- trace_evidence: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/traces/trace_stub_51062663bccf/evidence-chain","trace_id":"trace_stub_51062663bccf","nodes":[{"node_id":"4f983c0d-7321-4d93-96ce-e54341ceb964","node_type":"model_output","label":"stub_model_output","summary":"model-service stub output","source_module":"model_service","source_record_type":"model_invocation","source_record_id":"inv_6cbc4b61a9a7","confidence":0.0},{"no`
- trace_id: `trace_stub_51062663bccf`
- recommendation_id: `4b62396f-cca3-4db8-9588-6be2f5737e7f`

## 6. Missing Values
- missing_create: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/cases/4a47ae8c-5311-49be-a71e-3415f5c3f223/missing-values","item":{"query_id":"8bf064bb-f185-4a36-82f4-74878b6acd9f","case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","patient_id":"a84ca02e-edd0-4488-971e-1d30d6f207e3","field_name":"serum_k","field_label":"Serum Potassium","modality":"lab_result","reason":"acceptance missing-value flow","question_text":"Please provid`
- missing_list: PASS (200)
  - body: `{"items":[{"query_id":"8bf064bb-f185-4a36-82f4-74878b6acd9f","case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","patient_id":"a84ca02e-edd0-4488-971e-1d30d6f207e3","field_name":"serum_k","field_label":"Serum Potassium","modality":"lab_result","reason":"acceptance missing-value flow","question_text":"Please provide serum potassium.","status":"pending","trace_id":"trace_mv_3dc6e4deb6a1","policy_versio`
- missing_answer: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/cases/4a47ae8c-5311-49be-a71e-3415f5c3f223/missing-values/8bf064bb-f185-4a36-82f4-74878b6acd9f/answer","item":{"query_id":"8bf064bb-f185-4a36-82f4-74878b6acd9f","case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","patient_id":"a84ca02e-edd0-4488-971e-1d30d6f207e3","field_name":"serum_k","field_label":"Serum Potassium","modality":"lab_result","reason":"acceptance missin`
- missing_create_default: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/cases/4a47ae8c-5311-49be-a71e-3415f5c3f223/missing-values","item":{"query_id":"57abb803-fdfd-4d65-a0aa-a9c3dbc4ca9d","case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","patient_id":"a84ca02e-edd0-4488-971e-1d30d6f207e3","field_name":"serum_na","field_label":"Serum Sodium","modality":"lab_result","reason":"acceptance missing-value flow","question_text":"Please provide `
- missing_default: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/cases/4a47ae8c-5311-49be-a71e-3415f5c3f223/missing-values/57abb803-fdfd-4d65-a0aa-a9c3dbc4ca9d/apply-default","item":{"query_id":"57abb803-fdfd-4d65-a0aa-a9c3dbc4ca9d","case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","patient_id":"a84ca02e-edd0-4488-971e-1d30d6f207e3","field_name":"serum_na","field_label":"Serum Sodium","modality":"lab_result","reason":"acceptance m`

## 7. Feedback
- feedback_create: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/feedback","item":{"feedback_id":"47d6d097-c772-47ff-8577-f4574d0876a0","case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","trace_id":"trace_stub_51062663bccf","recommendation_id":"4b62396f-cca3-4db8-9588-6be2f5737e7f","feedback_type":"accept","feedback_text":"stage43 acceptance","doctor_decision":"accept","rating":5,"doctor_id":"stub_doctor","learning_eligible":true,"`
- feedback_list: PASS (200)
  - body: `{"items":[{"feedback_id":"47d6d097-c772-47ff-8577-f4574d0876a0","case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","trace_id":"trace_stub_51062663bccf","recommendation_id":"4b62396f-cca3-4db8-9588-6be2f5737e7f","feedback_type":"accept","feedback_text":"stage43 acceptance","doctor_decision":"accept","rating":5,"doctor_id":"stub_doctor","learning_eligible":true,"created_at":"2026-06-03T04:07:33.148057`
- case_feedback_list: PASS (200)
  - body: `{"items":[{"feedback_id":"47d6d097-c772-47ff-8577-f4574d0876a0","case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","trace_id":"trace_stub_51062663bccf","recommendation_id":"4b62396f-cca3-4db8-9588-6be2f5737e7f","feedback_type":"accept","feedback_text":"stage43 acceptance","doctor_decision":"accept","rating":5,"doctor_id":"stub_doctor","learning_eligible":true,"created_at":"2026-06-03T04:07:33.148057`
- feedback_id: `47d6d097-c772-47ff-8577-f4574d0876a0`

## 8. Quality Review
- quality_create: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/quality-reviews","item":{"review_id":"eced7363-0619-43a7-a563-fbedf196c831","case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","trace_id":"trace_stub_51062663bccf","target_type":"recommendation","target_id":"4b62396f-cca3-4db8-9588-6be2f5737e7f","status":"open","attribution":"human_feedback","severity":"medium","summary":"stage43 acceptance review","related_feedback_i`
- quality_list: PASS (200)
  - body: `{"items":[{"review_id":"eced7363-0619-43a7-a563-fbedf196c831","case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","trace_id":"trace_stub_51062663bccf","target_type":"recommendation","target_id":"4b62396f-cca3-4db8-9588-6be2f5737e7f","status":"open","attribution":"human_feedback","severity":"medium","summary":"stage43 acceptance review","related_feedback_id":"47d6d097-c772-47ff-8577-f4574d0876a0","act`
- case_quality_list: PASS (200)
  - body: `{"items":[{"review_id":"eced7363-0619-43a7-a563-fbedf196c831","case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","trace_id":"trace_stub_51062663bccf","target_type":"recommendation","target_id":"4b62396f-cca3-4db8-9588-6be2f5737e7f","status":"open","attribution":"human_feedback","severity":"medium","summary":"stage43 acceptance review","related_feedback_id":"47d6d097-c772-47ff-8577-f4574d0876a0","act`
- quality_review_id: `None`

## 9. Model Registry
- model_registry_list: PASS (200)
  - body: `{"items":[{"model_id":"5956cd95-dcc7-44c3-9f7e-16ae72984b5c","model_name":"frontend-demo-capcop-model-2","disease_agent":"capcop_agent","task_type":"risk_assessment","modality_scope":["ct","labs"],"owner_team":"diagnostics","description":"frontend model registry lifecycle verification 2","is_active":true,"created_at":"2026-06-02T12:01:49.289737Z","updated_at":"2026-06-02T12:01:49.289737Z"},{"model`
- model_registry_create: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/model-registry","item":{"model_id":"e5ac7797-69ae-49d5-8220-2f9fc071259e","model_name":"Stage43 Demo Model","disease_agent":"capcop_agent","task_type":"risk_assessment","modality_scope":["clinical_table"],"owner_team":"MedOrion","description":"acceptance demo","is_active":true,"created_at":"2026-06-03T04:00:44.361083Z","updated_at":"2026-06-03T04:00:44.361083Z","ver`
- model_registry_detail: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/model-registry/e5ac7797-69ae-49d5-8220-2f9fc071259e","item":{"model_id":"e5ac7797-69ae-49d5-8220-2f9fc071259e","model_name":"Stage43 Demo Model","disease_agent":"capcop_agent","task_type":"risk_assessment","modality_scope":["clinical_table"],"owner_team":"MedOrion","description":"acceptance demo","is_active":true,"created_at":"2026-06-03T04:00:44.361083Z","updated_a`
- model_version_create: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/model-registry/e5ac7797-69ae-49d5-8220-2f9fc071259e/versions","item":{"version_id":"a92e3190-9624-47ca-b860-2f11129f0522","model_id":"e5ac7797-69ae-49d5-8220-2f9fc071259e","version_label":"v43.0","approval_state":"draft","contract_version":"v1","artifact_ref":"s3://demo/model-v43.onnx","input_schema":{"fields":["a"]},"output_schema":{"fields":["b"]},"metrics":{"auc"`
- model_version_approve: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/model-versions/a92e3190-9624-47ca-b860-2f11129f0522/approve","item":{"version_id":"a92e3190-9624-47ca-b860-2f11129f0522","model_id":"e5ac7797-69ae-49d5-8220-2f9fc071259e","version_label":"v43.0","approval_state":"approved","contract_version":"v1","artifact_ref":"s3://demo/model-v43.onnx","input_schema":{"fields":["a"]},"output_schema":{"fields":["b"]},"metrics":{"au`
- model_version_promote: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/model-versions/a92e3190-9624-47ca-b860-2f11129f0522/promote","item":{"version_id":"a92e3190-9624-47ca-b860-2f11129f0522","model_id":"e5ac7797-69ae-49d5-8220-2f9fc071259e","version_label":"v43.0","approval_state":"default","contract_version":"v1","artifact_ref":"s3://demo/model-v43.onnx","input_schema":{"fields":["a"]},"output_schema":{"fields":["b"]},"metrics":{"auc`
- model_version_rollback: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/model-versions/a92e3190-9624-47ca-b860-2f11129f0522/rollback","item":{"version_id":"a92e3190-9624-47ca-b860-2f11129f0522","model_id":"e5ac7797-69ae-49d5-8220-2f9fc071259e","version_label":"v43.0","approval_state":"default","contract_version":"v1","artifact_ref":"s3://demo/model-v43.onnx","input_schema":{"fields":["a"]},"output_schema":{"fields":["b"]},"metrics":{"au`
- model_version_evaluations: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/model-versions/a92e3190-9624-47ca-b860-2f11129f0522/evaluations","item":{"version_id":"a92e3190-9624-47ca-b860-2f11129f0522","model_id":"e5ac7797-69ae-49d5-8220-2f9fc071259e","approval_state":"default","artifact_ref":"s3://demo/model-v43.onnx","metrics":{"auc":0.9},"runtime_constraints":{"cpu":"1","notes":"stage43 acceptance"},"notes":"stage43 acceptance","published`
- model_id: `e5ac7797-69ae-49d5-8220-2f9fc071259e`
- version_id: `a92e3190-9624-47ca-b860-2f11129f0522`

## 10. Agent Gateway
- agent_validate: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/agent-gateway/validate-input","agent_code":"capcop_agent","valid":true,"agent_status":"stub_active","matched_model_version_id":"capcop_stub_v1","unsupported_reason":null,"runtime_stub":true}`
- agent_infer: PASS (200)
  - body: `{"status":"ok","route":"/api/v1/agent-gateway/infer","trace_id":"trace_stub_51062663bccf","agent_invocation_id":"agt_3b60ea80094840fb","agent_code":"capcop_agent","agent_status":"succeeded","model_service_response":{"trace_id":"trace_stub_51062663bccf","inference_task_id":"agt_3b60ea80094840fb","model_invocation_id":"inv_acf08c514101","model_id":"capcop_stub_classifier","model_version_id":"capcop_`

## 11. Orchestrations
- orch_validate: PASS (200)
  - body: `{"status":"validated","route":"/api/v1/orchestrations/validate-plan","trace_id":"trace_stub_51062663bccf","orchestration_run_id":"orc_3fb72665393644f8","mode":"single_agent","requested_task":"risk_assessment","steps":[{"step_id":"step_e7e3c8c2271a","step_type":"single_agent_step_1","step_index":null,"agent_code":"capcop_agent","model_version_id":null,"status":"planned","duration_ms":null,"agent_in`
- orch_run: PASS (200)
  - body: `{"status":"completed","route":"/api/v1/orchestrations/run","trace_id":"trace_stub_51062663bccf","orchestration_run_id":"orc_9dcf8bee553347ae","mode":"parallel_agents","requested_task":"risk_assessment","steps":[{"step_id":"step_3e083f503268","step_type":"parallel_agents_step_1","step_index":1,"agent_code":"capcop_agent","model_version_id":"capcop_stub_v1","status":"completed","duration_ms":1,"agen`
- orch_detail: PASS (200)
  - body: `{"run":{"orchestration_run_id":"orc_9dcf8bee553347ae","trace_id":"trace_stub_51062663bccf","case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","patient_id":"a84ca02e-edd0-4488-971e-1d30d6f207e3","mode":"parallel_agents","status":"completed","requested_task":"risk_assessment","candidate_agents":["capcop_agent"],"clinical_context_refs":{},"modality_refs":{},"runtime_options":{},"idempotency_key":"stage`
- orch_steps: PASS (200)
  - body: `{"items":[{"step_id":"step_3e083f503268","trace_id":"trace_stub_51062663bccf","case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","patient_id":"a84ca02e-edd0-4488-971e-1d30d6f207e3","orchestration_run_id":"orc_9dcf8bee553347ae","parent_step_id":null,"step_type":"parallel_agents_step_1","step_name":null,"step_index":1,"agent_code":"capcop_agent","agent_version":"stage35-agent-contract-v1","model_versi`
- orch_invocations: PASS (200)
  - body: `{"items":[{"agent_invocation_id":"agt_b73788b79ec94e87","trace_id":"trace_stub_51062663bccf","case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","patient_id":"a84ca02e-edd0-4488-971e-1d30d6f207e3","orchestration_run_id":"orc_9dcf8bee553347ae","step_id":"step_3e083f503268","agent_code":"capcop_agent","agent_version":"stage35-agent-contract-v1","endpoint_id":"capcop_agent","endpoint_url":"http://model-`
- orch_conflicts: PASS (200)
  - body: `{"items":[],"total":0}`
- orch_summaries: PASS (200)
  - body: `{"items":[{"summary_id":"llm_95597b83c525","trace_id":"trace_stub_51062663bccf","case_id":"4a47ae8c-5311-49be-a71e-3415f5c3f223","patient_id":"a84ca02e-edd0-4488-971e-1d30d6f207e3","orchestration_run_id":"orc_9dcf8bee553347ae","step_id":"step_3e083f503268","agent_invocation_id":"agt_b73788b79ec94e87","model_version_id":null,"summary_type":"orchestration_summary","status":"stub","summary_text":"Run`
- orchestration_run_id: `orc_9dcf8bee553347ae`

## 12. Frontend Route Probe
- /login: PASS (200)
- /dashboard: PASS (200)
- /cases: PASS (200)
- /models: PASS (200)
- /cases/4a47ae8c-5311-49be-a71e-3415f5c3f223/missing-consultation: PASS (200)
- /feedback: PASS (200)
- /quality-reviews: PASS (200)
- /lineage: PASS (200)

## 13. Risks / Follow-Up
- `/feedback`, `/quality-reviews`, and `/lineage` are now top-level entry pages that route doctors into a case-selection flow before entering the workflow.
- Case-level pages such as `/cases/{case_id}/feedback`, `/cases/{case_id}/quality-reviews`, and `/cases/{case_id}/lineage` remain the actual workflow entry points for a specific case.
- Orchestration audit is still limited to orchestration audit tables and is not mirrored into case trace/evidence tables.
- No schema changes or Alembic operations were performed for this acceptance run.
- Nginx remains disabled; access continues through the SSH tunnel to frontend port 3000.
- If the goal is a polished user-facing review, the next step is an orchestration audit viewer or an MVP acceptance checklist page rather than real model onboarding.
