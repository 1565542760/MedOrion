# Stage 93: Adapter Alias Governance

## Goal
Fix the shadow eligibility TypeError and formalize adapter alias governance for CAP/COP clinical MLP fold5.

## Governance model
- Canonical adapter code remains `clinical_mlp_cap_cop_adapter`.
- Runtime shadow adapter code is a governed compatibility alias.
- `accepted_adapter_codes` is an explicit allowlist, not free-form matching.
- Demo or unknown adapter codes are not accepted.

## Current accepted codes
- `clinical_mlp_cap_cop_adapter`
- `cap_cop_clinical_mlp_fold5_shadow`

## Safety behavior
- `ENABLE_CAP_COP_CLINICAL_MLP_SHADOW` remains `false` by default.
- `CAP_COP_CLINICAL_MLP_SHADOW_ALLOWED_MODEL_VERSION_IDS` remains empty by default.
- Empty allowlist continues to reject all model versions.
- The helper now returns adapter governance fields:
  - `canonical_adapter_code`
  - `runtime_adapter_code`
  - `accepted_adapter_codes`
  - `adapter_match`

## TypeError fix
The Stage 92 rehearsal exposed a TypeError in metadata missing detection. The code now uses a defensive helper that treats `None`, blank strings, and empty containers as missing without relying on set membership over unhashable values.

## Non-actions
- No allowlist update.
- No shadow switch enablement.
- No model load.
- No `torch.load`.
- No inference.
- No recommendation write.
- No case trace/evidence write.
