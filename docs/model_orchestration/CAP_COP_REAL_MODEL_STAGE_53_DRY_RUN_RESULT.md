# MedOrion Stage 53: Single-Artifact CPU-only Dry-Run Result

Last updated: 2026-06-03T17:38:24.559080+00:00

## Environment
- MRI3D conda env: yes
- Python path: `/home/sygxdg/miniconda3/envs/MRI3D/bin/python`
- Torch version: `2.6.0+cu124`
- CUDA visible (record only): `False`
- CUDA available (record only): `False`
- CPU-only: `True`

## Artifact
- Artifact path: `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/clinical_mlp/weights/fold1_best.pth`
- Artifact type: `pth`
- SHA256: `29d83ecc10f0eab132e194c3976c0d741f626254bbe7f99542f69ec8e8973f76`
- File size bytes: `21177`
- Computed at: `2026-06-03T17:38:24.559080+00:00`
- Computed by: `sygxdg@sygxdg MRI3D-conda`

## Dry-run
- torch.load executed: `True`
- state_dict loaded: `True`
- structure match: `True`
- missing keys: `[]`
- unexpected keys: `[]`
- shape mismatches: `[]`
- dummy forward executed: `True`
- dummy forward shape: `[1, 2]`

## ClinicalMLP Contract
- input dim = 36
- output dim = 2
- expected structure: Linear(36,64) -> ReLU -> Dropout(0.3) -> Linear(64,32) -> ReLU -> Dropout(0.3) -> Linear(32,2)

## Safety Flags
- not_for_diagnosis: `True`
- not_registered_as_default: `True`
- not_enabled_for_live_inference: `True`
- not_training: `True`
- not_real_inference: `True`
- not_scan_dir: `True`
- not_read_neighbor_fold: `True`
- not_copy_or_move: `True`
- not_write_trace_evidence: `True`
- not_db_change: `True`
- not_alembic: `True`
- not_nginx: `True`
- not_frontend: `True`

## Error
- error: `None`

