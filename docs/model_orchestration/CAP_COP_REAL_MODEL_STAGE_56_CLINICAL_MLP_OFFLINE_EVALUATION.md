# MedOrion Stage 56: CAP/COP Clinical MLP Offline Evaluation

Last updated: 2026-06-03T17:59:18.103728+00:00

## Evaluation Scope
- Internal retrospective check over the approved clinical CSVs
- Read-only access to the original research data
- Not an independent held-out external test set unless separately proven later
- Low evidence grade for clinical deployment claims

## Data Provenance
- CAP.csv: `/home/sygxdg/MRI3DModel/clinical_csv/CAP.csv`
- COP.csv: `/home/sygxdg/MRI3DModel/clinical_csv/COP.csv`
- preprocessing artifact: `/srv/medorion/models/agents/cap_cop_classifier_agent/v1.0.0/clinical_mlp/preprocess_artifacts/clinical_tabular_standardization_v1.json`
- feature count: `36`
- model_input_schema mapping is model-specific; future MedOrion storage must support schema mapping per model family
- CAP/COP clinical MLP requires 36 clinical features
- `Striated_shadow.1` is preserved as part of the historical training schema

## Evaluation Summary
- label counts: CAP=255, COP=127
- best fold by heuristic: `fold5`
- recommended deployment direction: `single_fold` (advisory only, not an activation decision)

## Fold Metrics
### fold1
- model_version_id: `clinical_mlp_cap_cop_classifier@fold1_best`
- SHA256: `29d83ecc10f0eab132e194c3976c0d741f626254bbe7f99542f69ec8e8973f76`
- file_size_bytes: `21177`
- AUC: `0.9107302763625135`
- ACC: `0.8298429319371727`
- sensitivity: `0.8818897637795275`
- specificity: `0.803921568627451`
- confusion_matrix: `[[205, 50], [15, 112]]`
- CAP recall: `0.803921568627451`
- COP recall: `0.8818897637795275`
- CAP precision: `0.9318181818181818`
- COP precision: `0.691358024691358`
- Brier score: `0.13593044205417168`
- ECE: `0.4073593117423473`
- probability distribution: mean=`0.4480890929698944`, std=`0.2543240487575531`, min=`0.029303980991244316`, max=`0.9675847887992859`
- failure cases: `{'false_positive': 50, 'false_negative': 15}`
- note: internal retrospective check over approved clinical CSVs; not an independent held-out test set

### fold2
- model_version_id: `clinical_mlp_cap_cop_classifier@fold2_best`
- SHA256: `eeb28464bc6c0f7d51ef79521090d95e1e30044095cc145c09931bcc7fb1a4ef`
- file_size_bytes: `21177`
- AUC: `0.9174000308784931`
- ACC: `0.8272251308900523`
- sensitivity: `0.84251968503937`
- specificity: `0.8196078431372549`
- confusion_matrix: `[[209, 46], [20, 107]]`
- CAP recall: `0.8196078431372549`
- COP recall: `0.84251968503937`
- CAP precision: `0.9126637554585153`
- COP precision: `0.6993464052287581`
- Brier score: `0.11870653000908968`
- ECE: `0.4637168286202465`
- probability distribution: mean=`0.41656896471977234`, std=`0.30732133984565735`, min=`0.001432131975889206`, max=`0.9759823083877563`
- failure cases: `{'false_positive': 46, 'false_negative': 20}`
- note: internal retrospective check over approved clinical CSVs; not an independent held-out test set

### fold3
- model_version_id: `clinical_mlp_cap_cop_classifier@fold3_best`
- SHA256: `4df2b11ff1cd9a7b1b10718edb9c40e52ad12276f1d7cfbfd4ef5618fdb42ce9`
- file_size_bytes: `21177`
- AUC: `0.9433997220935618`
- ACC: `0.8821989528795812`
- sensitivity: `0.9212598425196851`
- specificity: `0.8627450980392157`
- confusion_matrix: `[[220, 35], [10, 117]]`
- CAP recall: `0.8627450980392157`
- COP recall: `0.9212598425196851`
- CAP precision: `0.9565217391304348`
- COP precision: `0.7697368421052632`
- Brier score: `0.0943059913415294`
- ECE: `0.5872771676632255`
- probability distribution: mean=`0.4020252227783203`, std=`0.4245932996273041`, min=`4.092822081247505e-08`, max=`0.9999980926513672`
- failure cases: `{'false_positive': 35, 'false_negative': 10}`
- note: internal retrospective check over approved clinical CSVs; not an independent held-out test set

### fold4
- model_version_id: `clinical_mlp_cap_cop_classifier@fold4_best`
- SHA256: `c8f175ba42c16dce5af108daf9c6035f583db03dc2329664668acc75dff92349`
- file_size_bytes: `21177`
- AUC: `0.9273120271730739`
- ACC: `0.8586387434554974`
- sensitivity: `0.84251968503937`
- specificity: `0.8666666666666667`
- confusion_matrix: `[[221, 34], [20, 107]]`
- CAP recall: `0.8666666666666667`
- COP recall: `0.84251968503937`
- CAP precision: `0.91701244813278`
- COP precision: `0.7588652482269503`
- Brier score: `0.10846651394848067`
- ECE: `0.5666144031613581`
- probability distribution: mean=`0.37142056226730347`, std=`0.3979819715023041`, min=`8.128819839470225e-10`, max=`0.9991452693939209`
- failure cases: `{'false_positive': 34, 'false_negative': 20}`
- note: internal retrospective check over approved clinical CSVs; not an independent held-out test set

### fold5
- model_version_id: `clinical_mlp_cap_cop_classifier@fold5_best`
- SHA256: `0b66192745f6c35d5158596e89db7bd1a2d6292ed66a0de4ca3f28c49fa9426a`
- file_size_bytes: `21177`
- AUC: `0.9567701096186506`
- ACC: `0.8900523560209425`
- sensitivity: `0.937007874015748`
- specificity: `0.8666666666666667`
- confusion_matrix: `[[221, 34], [8, 119]]`
- CAP recall: `0.8666666666666667`
- COP recall: `0.937007874015748`
- CAP precision: `0.9650655021834061`
- COP precision: `0.7777777777777778`
- Brier score: `0.08114830325579807`
- ECE: `0.569265610757141`
- probability distribution: mean=`0.3993084132671356`, std=`0.4086000621318817`, min=`2.9128545975254383e-06`, max=`0.9999954700469971`
- failure cases: `{'false_positive': 34, 'false_negative': 8}`
- note: internal retrospective check over approved clinical CSVs; not an independent held-out test set

## Ensemble Check
- AUC: `0.9506252894858731`
- ACC: `0.8821989528795812`
- sensitivity: `0.9212598425196851`
- specificity: `0.8627450980392157`
- confusion_matrix: `[[220, 35], [10, 117]]`
- CAP recall: `0.8627450980392157`
- COP recall: `0.9212598425196851`
- Brier score: `0.09183188028111125`
- ECE: `0.5066199101439399`

## Evidence Level
- low evidence / internal retrospective check
- not a final clinical performance claim
- not sufficient alone for live inference or default promotion

## Recommendation
- `single_fold` is suggested only as a next-step direction
- best single fold: `fold5`
- reason: single fold is simpler and sufficiently competitive in this retrospective check
- final activation still requires main-controller approval and later gating steps

## Safety and Boundary Checks
- No training was performed.
- No weights were modified.
- No live inference was enabled.
- No database schema changes were made.
- No Alembic migrations were executed.
- No Nginx was enabled.
- No front-end changes were made.
- No病例 trace/evidence was written.
- No data were copied back into the original MRI3DModel tree.

## MedOrion Schema Advice
- yes, MedOrion should define `model_input_schema`
- yes, MedOrion should define `clinical_feature_mapping`
- yes, MedOrion should support model-specific table schemas
- one model family may require a different tabular field mapping than another

## Main-Controller Writeback Summary
- Stage 56 completed a read-only offline evaluation using the approved original research CSVs.
- fold1~fold5 were evaluated without training, live inference, or database changes.
- The results are low-evidence internal retrospective results, not a final clinical deployment claim.
- MedOrion should support schema mapping and clinical feature mapping per model family.
