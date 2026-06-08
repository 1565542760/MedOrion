# Machine Vision and Digital Twin Course Assignment Brief

Date: 2026-06-08

Source: user-provided DOCX named 《机器视觉与数字孪生技术》期末考核试卷20260608审阅后(1).docx.

## Course Assessment Context

- Course: 机器视觉与数字孪生技术
- Class: 25 电子信息硕
- Assessment form: 实践报告及总结类（课程设计报告）
- Defense time: 2026-06-25 19:00-21:00
- Submission deadline: 2026-06-29
- Submission material: package all source code, data description, report, screenshots, demo video, and PPT.

## Core Assignment Requirement

Design and complete a machine-vision-driven digital twin application system or integrated research project. The project must show a complete chain:

1. Data acquisition.
2. Machine vision analysis.
3. State mapping.
4. Digital twin display.
5. Experimental validation.

The project may target intelligent manufacturing, robotics, smart transportation, smart campus, equipment operation and maintenance, agricultural monitoring, or another defensible scenario. For MedOrion, the defensible scenario is a local-first clinical AI research workbench for CAP/COP pulmonary disease-task exploration.

## Required Technical Capabilities

### Machine Vision Perception

The project must include image or video data acquisition/source description, preprocessing, and at least one core vision task:

- image classification;
- object detection;
- semantic or instance segmentation;
- target tracking;
- pose estimation;
- 3D reconstruction;
- another explicitly justified visual perception task.

### Digital Twin Modeling

The project must construct a digital twin model corresponding to a real object, scene, state, workflow, or process. In MedOrion, the most coherent twin object is a case-level CAP/COP clinical state twin, with lung/imaging state, model provenance, missing-value state, shadow audit state, and quality-review state.

### Twin Visualization and Experimental Validation

The project must map perception outputs to the twin model and provide visual/interactive display. Evaluation should include suitable metrics such as:

- recognition/classification accuracy;
- real-time performance or response time;
- robustness;
- model/twin synchronization error;
- system response latency;
- error analysis.

## Report Requirements

The final report should:

- follow the provided course template;
- be at least 5000 Chinese characters;
- include standard figures and tables;
- include at least 10 references;
- include abstract, keywords, body, conclusion, and references.

Required content:

1. System requirement and overall design.
2. Application scenario, problem definition, system goals, technical route, architecture, and module division.
3. Key technical implementation.
4. Vision algorithm, preprocessing, model training or tuning, twin modeling, and system integration.
5. Experiment test and result analysis.
6. Dataset split, environment, metrics, results, error sources, comparison, and improvement.
7. Application value, feasibility, engineering limits, ethics, and data security.

## Submission Checklist

- Source code.
- Model/config files or exact model-runtime description.
- Data description document.
- Running instructions.
- Digital twin scene or visualization assets.
- UI screenshots.
- Flowchart, architecture diagram, and key algorithm diagram.
- 3-5 minute system demo video.
- Word report and PDF report.
- Defense PPT.

## Grading Rubric Extract

| Area | Score |
| --- | ---: |
| Topic value and innovation | 20 |
| Machine vision algorithm implementation quality | 35 |
| Digital twin modeling and visualization | 15 |
| Report quality and academic standard | 20 |
| System demonstration and defense | 10 |

## MedOrion-Specific Warning

MedOrion currently has a usable CAP/COP clinical MLP shadow baseline, but it is not enough by itself to satisfy the machine vision requirement. The course project must add or explicitly document a machine vision component, such as CT/lung-region visual analysis, imaging ResNet18 provenance/runner work, or a clearly labeled visual simulation if real image/video data are not available.
