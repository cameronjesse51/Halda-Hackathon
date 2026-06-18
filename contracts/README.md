# College recommendation contract

`college-recommendations.v1.schema.json` is the canonical boundary between the
college-search backend and the web client. The backend will emit its payload as
the data of an SSE event named `college_results`.

Contract rules:

- Rates are decimal values from `0` to `1`, not percentages.
- Monetary values are annual USD amounts.
- `budget_difference` is `student_budget - net_price`; positive is under budget.
- `match_score` measures Halda fit and must never be presented as an admission probability.
- Unknown factual data is `null`; unknown program availability is `"unknown"`.
- Every factual card includes at least one source with retrieval time and the fields it supports.
- Reach/target/likely is an estimate and always includes both its reason and its calculation basis.

Breaking changes require a new schema file and `schema_version`. Additive changes
should still be deliberate because the schema rejects unknown properties.
