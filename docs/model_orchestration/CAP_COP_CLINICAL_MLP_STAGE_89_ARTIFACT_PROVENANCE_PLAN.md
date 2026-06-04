# Stage 89: CAP/COP Clinical MLP Fold5 Artifact Provenance Finalization Plan

## 1. Current Blocker

The formal fold5 registry metadata record already exists, but its artifact provenance is still incomplete.

- model_version_id = b12f315a-7f44-491d-bf46-b0da73f6da03
- version_label = v1.0.0-fold5
- artifact_uri = pending
- artifact_hash = pending
- file_size_bytes = pending
- Current decision state: NO-GO
- Current allowlist state: do not add to allowlist

This means the record is suitable as a governed metadata baseline, but not yet ready for shadow enablement.

## 2. Provenance Fields To Finalize

The following fields must be finalized before any future enablement rehearsal:

- artifact_uri
- artifact_hash
- hash_algorithm = sha256
- file_size_bytes
- artifact_type = pth
- adapter_code = clinical_mlp_cap_cop_adapter
- model_version_id
- registered_by
- registered_at
- reviewed_by
- review_note
- provenance_source

## 3. Allowed Future Confirmation Methods

### A. Use an already-authorized hash record

If a prior stage already contains an explicitly authorized fold5 hash/size record, that record may be referenced as the provenance source.

Requirements:
- The source must be explicit and reviewable.
- The provenance trail must explain where the value came from.
- The source must be tied to the same fold5 artifact identity.
- No new file read is required in this path.

### B. Recompute the hash later, only with explicit approval

If the provenance must be finalized by recomputation, the following restrictions apply:
- The main controller must explicitly approve one exact artifact path.
- Only that single file may be checked.
- No directory scan is allowed.
- No adjacent file guessing is allowed.
- No copy or move is allowed.
- No model loading is allowed.
- No torch.load is allowed.
- Only sha256 and file size may be read.

## 4. Explicit Non-Actions

Stage 89 does not do the following:

- No .pth file read
- No hash computation in this stage
- No model loading
- No torch.load
- No training
- No inference
- No allowlist update
- No shadow switch enablement
- No recommendation write
- No trace or evidence write

## 5. If Future Approval Is Given

If the user/main-controller later approves provenance finalization, Stage 90 may do the following:

- Single-file hash verification only
- Exact path only
- sha256 plus file size
- Registry artifact metadata update
- Still no model loading
- Still no allowlist unless separately approved

## 6. If No Approval

If no approval is given:

- Remain NO-GO
- Keep provenance metadata pending
- Do not allowlist
- Do not shadow execute

## 7. Stage 90 Recommendation

- If the exact artifact path is approved: Stage 90 should perform single-file provenance finalization.
- If it is not approved: Stage 90 should remain in governance/documentation only.
