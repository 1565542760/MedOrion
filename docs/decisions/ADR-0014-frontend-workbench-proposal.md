# ADR-0014: Frontend Workbench Proposal

Date: 2026-05-31
Status: Proposed, not approved for implementation
Source: Frontend doctor workbench thread report and main-controller environment correction

## Decision

The proposed frontend stack is accepted as a planning proposal, not as approval to initialize or implement the frontend yet.

Proposed stack:

- Next.js
- TypeScript
- Ant Design / ProComponents
- React Flow
- ECharts
- Cornerstone.js / Cornerstone3D reserved for medical imaging

The first frontend stage may use mock data and an API adapter layer, but implementation should wait until backend API stubs, trace query contracts, and migration review are stable enough.

## Corrected Facts

Node.js v22.22.2 and npm 10.9.7 are installed on the remote server. corepack is available. pnpm is not installed or enabled.

/home/sygxdg/MedOrion is not empty; it contains docs and deployment drafts. /srv/medorion/app/frontend does not yet exist.

## Consequences

Frontend should not initialize a project yet. The current active project step remains traceability review of the backend migration draft before database migration finalization.
