# Course Deliverables Checklist for MedOrion

## Required Course Materials

- [ ] Source code snapshot or repository package.
- [ ] Configuration and running instructions.
- [ ] Data description document.
- [ ] Machine vision module description and runnable demo.
- [ ] Digital twin visualization screenshots or scene files.
- [ ] System architecture diagram.
- [ ] Pipeline/flowchart diagram.
- [ ] Key algorithm diagram.
- [ ] Experiment metrics and result tables.
- [ ] 3-5 minute demo video.
- [ ] Word report, at least 5000 Chinese characters.
- [ ] PDF report.
- [ ] Defense PPT.
- [ ] At least 10 references.

## MedOrion-Specific Deliverables

- [ ] Explain MedOrion architecture: frontend, backend, model-service, model-runners, database, audit stores.
- [ ] Explain patient/case workflow.
- [ ] Explain model registry and shadow audit boundaries.
- [ ] Explain CAP/COP clinical MLP shadow baseline and Stage 127 feature-contract limitation.
- [ ] Add or document machine vision component.
- [ ] Add digital twin state visualization or mockup.
- [ ] Include frontend screenshots: cases, model input, shadow audit, lineage/trace if relevant.
- [ ] Include governance screenshot or table: not diagnosis, not recommendation, not externally validated.

## Suggested Report Figure List

1. Overall MedOrion CAP/COP digital twin architecture.
2. Data flow: data source -> vision -> snapshot -> shadow audit -> twin visualization.
3. CAP/COP feature/provenance mapping table.
4. Vision algorithm pipeline.
5. Digital twin state model diagram.
6. UI screenshot: case list.
7. UI screenshot: model input or feature contract view.
8. UI screenshot: shadow audit result with warnings.
9. Metrics table.
10. Error analysis examples.

## Recommended Next Stage

For course completion, prioritize:

1. Imaging ResNet18 provenance + runner plan, or another explicit machine vision module.
2. Digital twin state visualization panel.
3. Report/PPT scaffold.
4. Demo video script.

Do not spend the next stage on clinical diagnosis promotion, default/canary model promotion, public deployment, or automatic training.
