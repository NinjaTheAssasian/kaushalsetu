# Phase 6: Final Integration + SIH Demo Polish

Phase 6 focuses on final product coherence and demo readiness rather than adding a new domain subsystem.

## Included
- Role-aware login links and seeded demo account loading.
- End-to-end demo center with explicit learner → employer → government flow.
- Employer/providing role guards preserved on protected pages.
- Government executive brief, data-freshness indicator, print-friendly reporting view, and aggregate CSV export.
- Learner employment verification-code copy workflow.
- Improved error visibility and demo affordances.
- Aggregate analytics export contains no APAAR identifiers.

## Government export
Authenticated government administrators can download:
`GET /api/v1/admin/analytics/export.csv`

The export includes aggregate overview metrics, skill supply/demand rows, program outcome signals, and regional job counts. It does not include learner names, emails, raw APAAR IDs, or other direct learner identifiers.

## Final demo flow
1. Learner signs in and optionally performs demo APAAR verification.
2. Learner reports employment and copies the one-time verification code.
3. Employer signs in and verifies the employment using the code.
4. Employer submits skill feedback.
5. Learner profile reflects verified evidence and longitudinal outcomes.
6. Government administrator signs in and reviews aggregate intelligence plus Gemini decision support.
