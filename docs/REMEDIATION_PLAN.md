# Q-Shield Remediation Plan

## Purpose

This document records the problems found in the current Q-Shield codebase and provides an implementation guide for fixing them.

**Important:** This is a planning document only. No application code is changed by this document.

The goal is not merely to make the dashboard look more professional. The goal is to make its behavior accurate, auditable, safer to operate, and honest about what it can and cannot prove.

---

## 1. Current product reality

Q-Shield currently is a Streamlit application that:

1. Stores manually entered or uploaded cryptographic asset records.
2. Classifies the declared algorithm using hard-coded substring rules.
3. Calculates a weighted 0–100 prioritization score.
4. Generates generic migration guidance.
5. Tracks a user-entered migration status.
6. Produces CSV and PDF reports.
7. Optionally sends a sanitized assessment summary to Gemini or OpenAI.

It does **not** currently:

- Discover cryptography in live systems.
- Inspect source code, binaries, certificates, HSMs, cloud accounts, or network traffic.
- Verify that an inventory declaration matches runtime behavior.
- Test cryptographic implementations or protocols.
- Prove quantum readiness.
- Prove compliance or certification.
- Perform a migration.

The repaired product should preserve the useful inventory-and-planning workflow while making these boundaries explicit in the data model, interface, reports, tests, and documentation.

---

## 2. Remediation principles

All implementation work should follow these principles:

1. **Fix the model before improving the UI.** A polished report built on ambiguous data is still misleading.
2. **Separate observation from inference.** Store what the user or connector observed separately from what Q-Shield inferred.
3. **Never treat an unknown value as safe.** Unknown, stale, conflicting, and unverified states need explicit handling.
4. **Make every result reproducible.** Store the detector version, scoring configuration, standards-reference version, input snapshot, and assessment timestamp.
5. **Use explicit structured data instead of free-text matching where possible.** Keep free text for notes, not for the primary security classification.
6. **Do not claim capabilities that are not implemented.** Use “declared inventory assessment” unless a real discovery connector exists.
7. **Use human review as a first-class workflow.** Review status, reviewer, decision, evidence, and date should be stored, not just displayed.
8. **Keep external AI advisory.** AI must never silently change detection, scores, asset data, or migration status.
9. **Prefer safe failure.** If data is missing, stale, contradictory, or outside the supported vocabulary, block confident classification and request review.
10. **Test user-visible behavior, not only helper functions.** The critical path is import → assess → review → report.

---

## 3. Problems and best fixes

### 3.1 Inventory is a registry, not discovery

**Current problem**

`qshield/inventory.py` imports user-supplied records and the UI allows manual entry. The application does not discover assets from running systems. Nevertheless, labels such as “Cryptographic Asset Inventory” and “enterprise security” can imply automated discovery.

**Best fix**

- Rename user-facing language to **Declared Cryptographic Inventory** until discovery connectors exist.
- Add an explicit `evidence_source` field, for example:
  - `manual`
  - `csv_upload`
  - `json_upload`
  - `connector`
  - `certificate_scan`
  - `runtime_observation`
- Add `evidence_collected_at`, `evidence_location`, and `evidence_reference` fields.
- Add a separate connector architecture rather than hiding discovery logic in the inventory page.
- If discovery is later added, each connector should produce observations that are normalized into inventory records and retain raw evidence metadata.

**Acceptance criteria**

- Every inventory row visibly states how it was obtained.
- Reports distinguish declared data from observed data.
- The UI does not call manual/uploaded records “discovered.”
- A connector can be added without rewriting detection and scoring logic.

---

### 3.2 One algorithm field cannot represent a real system

**Current problem**

`CryptographicAsset` has one `cryptographic_algorithm` and one `cryptographic_purpose`. A real service can use RSA for certificate signing, ECDHE for key establishment, AES for bulk encryption, SHA-256 for hashing, and RSA or another mechanism for key wrapping at the same time.

The demo data itself exposes this limitation: the AES-256 database notes that RSA is used for key wrapping, but the detector only examines the AES-256 algorithm field.

**Best fix**

Introduce a normalized relationship:

```text
asset
  └── cryptographic_usages[]
        ├── algorithm
        ├── purpose
        ├── key_size_or_parameter_set
        ├── protocol_or_location
        ├── evidence_source
        ├── evidence_confidence
        └── observation_status
```

Recommended migration path:

1. Keep the existing fields temporarily for backward compatibility.
2. Add an `asset_crypto_usages` table.
3. Convert the legacy single algorithm field into one usage record during import.
4. Update detection to assess every usage.
5. Calculate asset risk from the highest-relevant exposure plus system context.
6. Mark an asset as fully assessed only when all known usages are reviewed.
7. Deprecate the single algorithm field after migration.

**Acceptance criteria**

- One asset can contain multiple algorithms and purposes.
- RSA key wrapping is not hidden by an AES-256 primary record.
- Reports show all detected cryptographic usages.
- A missing secondary usage is represented as incomplete evidence rather than safety.

---

### 3.3 Detection uses brittle substring matching

**Current problem**

`qshield/detection.py` uses checks such as:

```python
if any(pattern in normalized_algorithm for pattern in patterns)
```

This is transparent but can create false positives, false negatives, and ambiguous matches. It also does not reliably handle vendor-specific identifiers, protocol names, modes, parameter sets, or compound configurations.

**Best fix**

Create a versioned normalization and classification layer:

1. Normalize case, separators, aliases, parameter sets, and vendor prefixes.
2. Parse algorithm identifiers into structured fields where possible.
3. Use exact aliases before fallback pattern rules.
4. Detect ambiguous matches and return `needs_review=true`.
5. Record the matched alias, detector version, and rule ID.
6. Keep a test corpus of supported, unsupported, ambiguous, and maliciously crafted names.
7. Treat unsupported names as `unknown`, never as safe.

The detector should return a richer classification, for example:

```text
classification: vulnerable | pqc | classical-safe-for-quantum | weak-classically | unknown | hybrid
quantum_impact: none | generic-security-reduction | Shor | unknown
classical_status: acceptable | deprecated | broken | unknown
purpose_confidence: high | medium | low
```

**Acceptance criteria**

- Exact supported identifiers classify consistently.
- Ambiguous names do not receive a high-confidence result.
- SHA-1, MD5, and 3DES are reported as classically weak separately from quantum status.
- Compound algorithms are parsed into individual components.
- Every finding includes the detector version and matched rule.

---

### 3.4 Purpose is user-declared and may be wrong

**Current problem**

Migration recommendations depend heavily on `cryptographic_purpose`, but the purpose is normally typed or selected by the user and is not verified against protocol or evidence.

**Best fix**

- Add `purpose_source` and `purpose_confidence`.
- Allow multiple purposes when the same algorithm is reused.
- Validate purpose against protocol and asset type where practical.
- Flag contradictions such as:
  - ML-KEM declared for digital signatures.
  - ML-DSA declared for key establishment.
  - Hashing declared as encryption.
- Require human confirmation before generating a high-confidence migration target.

**Acceptance criteria**

- Contradictory algorithm/purpose combinations become review findings.
- Recommendations say “determine usage context” instead of presenting a definitive target when purpose is uncertain.
- Reports show whether purpose was observed, imported, or manually declared.

---

### 3.5 Risk score is a heuristic but looks authoritative

**Current problem**

`qshield/risk_engine.py` produces a 0–100 score using hand-authored weights and thresholds. The score is useful for prioritization but is not a validated probability, loss estimate, CVSS score, compliance rating, or NIST classification.

**Best fix**

- Rename the concept in the UI and reports to **Migration Priority Score** or **Planning Priority**.
- Keep the 0–100 scale only if its heuristic nature is displayed next to every score.
- Store the scoring configuration version with each assessment.
- Validate that weights sum to 1.0 at startup and in tests.
- Replace integer band gaps with continuous boundaries. For example:
  - Low: `[0, 35)`
  - Medium: `[35, 60)`
  - High: `[60, 80)`
  - Critical: `[80, 100]`
- Add a sensitivity report showing how scores change when weights change.
- Separate “quantum exposure” from “migration complexity” rather than combining them into one apparent security measurement.
- Provide a documented override process with reviewer, reason, timestamp, and evidence.

**Acceptance criteria**

- Every score can be reproduced from stored inputs and configuration.
- No decimal score becomes `Unknown` merely because it falls between integer band endpoints.
- The UI clearly says the score is a planning heuristic.
- Score overrides are auditable.
- Tests cover boundary values such as 34.9, 35.0, 59.9, 60.0, 79.9, and 80.0.

---

### 3.6 Assessment results can become stale

**Current problem**

When an asset changes, its stored assessment can describe the old inventory state. The UI expects the user to rerun assessment, but the database does not enforce or clearly expose freshness.

**Best fix**

- Add an `asset_revision` or `asset_updated_at` value to assessment results.
- Store an input fingerprint for the assessed asset and cryptographic usages.
- Mark results as `current`, `stale`, or `invalidated` after edits.
- Automatically invalidate assessment results when relevant fields change.
- Display stale status prominently in every page and report.
- Prevent migration recommendations from appearing current when their assessment is stale.

**Acceptance criteria**

- Editing a relevant asset field marks the assessment stale.
- Reports identify stale or missing assessments.
- The application never silently presents stale results as current.
- Rerunning assessment clears the stale state and records a new assessment version.

---

### 3.7 Migration status is self-reported and not verified

**Current problem**

The planner lets a user select `Completed`, but the application does not verify that the migration occurred. The current page correctly warns about this, but the data model still makes the status look definitive.

**Best fix**

Split status into:

- `migration_stage`: planned workflow stage.
- `implementation_claim`: what the owner says has been done.
- `verification_status`: unverified, partially verified, verified, rejected.
- `verified_by`, `verified_at`, and `verification_evidence`.

Use language such as:

```text
Owner-reported: Completed
Verification: Not verified
```

**Acceptance criteria**

- “Completed” cannot appear as verified without evidence.
- Reports distinguish owner claims from application-verified facts.
- Status changes are audited.

---

### 3.8 Generic recommendations are presented as migration plans

**Current problem**

`qshield/recommendations.py` generates sensible but generic checklists. It does not understand certificate hierarchies, HSM support, protocol versions, vendor dependencies, key ceremonies, regulatory requirements, or application-specific constraints.

**Best fix**

- Rename generic output to **Planning Guidance** unless evidence supports a specific plan.
- Separate:
  - target standard,
  - target algorithm candidate,
  - assumptions,
  - blockers,
  - required evidence,
  - validation tests,
  - rollback requirements.
- Make recommendations depend on structured usage and protocol data.
- Add a human approval step before a recommendation is labeled “approved plan.”
- Add an extension point for organization-specific policies and vendor constraints.

**Acceptance criteria**

- Every recommendation lists its assumptions.
- Unsupported context results in a conditional recommendation.
- The report never implies that displaying a target algorithm equals performing migration.

---

### 3.9 AI assistant fallback is easy to mistake for real AI

**Current problem**

Without an API key, `AIAssistant` returns keyword-selected canned responses. With an API key, it sends a limited summary to an external provider. The interface should make these modes unmistakable.

**Best fix**

- Label modes explicitly:
  - `Rule-based guidance`
  - `Gemini-generated advisory`
  - `OpenAI-generated advisory`
  - `Unavailable`
- Show the provider, model, prompt/context policy, and timestamp in the response metadata.
- Do not call the fallback an AI response.
- Add a configurable external-data consent control and an organization policy setting.
- Log only non-sensitive provider metadata, never API keys or raw confidential prompts.
- Make the AI output read-only and advisory.
- Add tests for provider-unavailable, timeout, authentication failure, and successful response paths.
- Keep the model names configurable and validate them before use.

**Acceptance criteria**

- Users can tell whether the displayed answer came from a model or fixed rules.
- No raw asset notes, owners, IDs, or uploads are sent unless explicitly authorized.
- AI failure never blocks deterministic assessment.
- AI cannot modify inventory, scores, or migration status.

---

### 3.10 Standards references can become stale

**Current problem**

The project has standards data in more than one place: `models.py`, `ai_assistant.py`, and `data/standards_reference.json`. The JSON records `last_verified` dates from December 1, 2024, and the application does not have a refresh or provenance workflow.

**Best fix**

- Create one canonical standards data source.
- Store:
  - standard identifier,
  - title,
  - official URL,
  - publication date,
  - retrieved/verified date,
  - source checksum or revision identifier,
  - applicability and purpose.
- Add a documented update process.
- Display the reference version and verification date in methodology and reports.
- Do not describe a static reference list as live standards validation.

**Acceptance criteria**

- Standards are not duplicated across modules.
- Reports identify the standards-reference version used.
- Updating standards data does not require editing several Python files.

---

### 3.11 Database and deployment are not enterprise-safe

**Current problem**

The default deployment uses a local SQLite file with no authentication, authorization, tenant isolation, encryption-at-rest design, retention policy, or tamper-evident audit log.

**Best fix**

For the prototype:

- Keep SQLite but document it as single-user/demo storage.
- Add a generated database path and startup diagnostics.
- Add backup/export and restore procedures.
- Add assessment and audit records with immutable IDs and hashes where practical.
- Avoid storing secrets or raw confidential inventories in logs.

For a real shared deployment:

- Add authentication through the deployment platform or an identity provider.
- Add role-based authorization.
- Add tenant/workspace isolation.
- Move persistence to a managed database with migrations and backups.
- Encrypt sensitive data in transit and at rest.
- Define retention and deletion policy.

**Acceptance criteria**

- The application clearly identifies demo versus shared/production mode.
- Sensitive deployment guidance is visible before upload.
- Destructive operations require confirmation and are audited.
- Production deployment is blocked or strongly warned until authentication and isolation exist.

---

### 3.12 Input validation is incomplete

**Current problem**

`qshield/validation.py` checks file types, sizes, required fields, lengths, and some dangerous characters, but it does not fully validate enumerations, dates, duplicate IDs within an upload, or cross-field consistency.

**Best fix**

- Validate all enumerated values against the model enums.
- Validate ISO dates such as certificate expiry.
- Reject duplicate `asset_id` values within a single upload with row-level errors.
- Define whether unknown columns are ignored, rejected, or preserved.
- Validate boolean fields consistently.
- Validate numeric limits and reject values that overflow expected ranges.
- Treat validation as a schema layer shared by file import and manual forms.
- Use output escaping for all values rendered into HTML; avoid relying only on character stripping.

**Acceptance criteria**

- The same validation rules apply to CSV, JSON, and manual forms.
- Invalid enums, dates, duplicates, and cross-field contradictions are reported clearly.
- Import is atomic: either the user-approved valid set is imported, or no partial import occurs.

---

### 3.13 Destructive and duplicate import behavior needs stronger safeguards

**Current problem**

Replace-existing imports can delete all records before import. Upserts can overwrite an existing asset with the same ID. These behaviors are understandable but risky for real data.

**Best fix**

- Preview imports before applying them.
- Show additions, updates, conflicts, and invalid rows.
- Require explicit confirmation for replacement.
- Wrap replacement/import in a database transaction.
- Offer conflict choices:
  - reject duplicate,
  - keep existing,
  - update existing,
  - create a new revision.
- Preserve an import batch record and rollback capability.

**Acceptance criteria**

- A failed import cannot leave the database half-cleared.
- Users see exactly which rows will be created or changed.
- Overwrites are recorded in the audit log.

---

### 3.14 Reports can look more authoritative than the data supports

**Current problem**

The PDF is polished and uses terms such as “security posture” and “assessment report,” while its underlying findings are manually declared and rule-based.

**Best fix**

- Use titles such as **Declared Cryptographic Inventory — Planning Assessment**.
- Put scope and limitations on the cover page, not only at the end.
- Include:
  - inventory coverage,
  - evidence source distribution,
  - stale assessment count,
  - unknown/ambiguous count,
  - detector version,
  - score configuration version,
  - standards-reference version,
  - human review status.
- Clearly separate facts, inferences, owner claims, and recommendations.
- Add a report status: draft, reviewed, approved, or stale.

**Acceptance criteria**

- A reader cannot reasonably mistake the report for a compliance certificate.
- Unassessed, stale, unknown, and self-reported records are visible.
- The report contains enough metadata to reproduce its conclusions.

---

### 3.15 Documentation and runtime requirements are inconsistent

**Current problem**

The README says Python 3.11+, while `requirements.txt`, `.python-version`, and `runtime.txt` specify Python 3.12. The README also lists `data/demo_assets.csv`, but the repository currently relies on the fallback generator because that CSV is not present.

The local test command failed because `pytest` is declared in `requirements-dev.txt` but is not installed in the current environment:

```text
python -m pytest tests/ -q
/usr/bin/python: No module named pytest
```

This failure is an environment/dependency setup issue, not a failure caused by the planning document.

**Best fix**

- Choose Python 3.12 as the supported version, or update all files consistently if 3.11 is required.
- Make the README, runtime, package metadata, and CI use the same version.
- Document the exact setup command:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

- Add a CI job that installs `requirements-dev.txt` before testing.
- Either add the documented demo CSV or update the README to say the data is generated by fallback code.
- Add a startup diagnostic showing application version, Python version, database path, and AI provider availability.

**Acceptance criteria**

- A clean environment can install dependencies and run tests.
- Documentation and runtime files state the same supported Python version.
- CI runs the same test command used in the README.
- Demo-data behavior is documented accurately.

---

### 3.16 Test coverage is too narrow for the critical user flow

**Current problem**

The tests cover many helper functions, but there is limited coverage for:

- stale assessments,
- import atomicity,
- duplicate IDs,
- multi-algorithm records,
- report correctness,
- AI mode labeling,
- score band boundaries,
- standards-reference versioning,
- Streamlit page behavior,
- output escaping,
- migration status verification.

**Best fix**

Build the test strategy in layers:

1. Unit tests for normalization, classification, scoring, validation, and recommendation logic.
2. Database integration tests for transactions, stale invalidation, audit records, and migrations.
3. End-to-end service tests for import → assess → recommend → report.
4. UI smoke tests for the main pages where feasible.
5. Security tests for malicious input, unsafe output, and secret leakage.
6. Regression fixtures for known algorithms and realistic multi-usage assets.

**Acceptance criteria**

- The full test suite passes in a clean environment.
- Every fixed bug gets a regression test.
- Boundary and negative cases are covered.
- Report generation is tested for both assessed and partially assessed inventories.

---

## 4. Recommended target architecture

The best long-term structure is:

```text
Input sources
  ├── manual forms
  ├── CSV/JSON import
  └── future discovery connectors
          ↓
Evidence and normalization layer
          ↓
Canonical inventory model
  ├── assets
  ├── cryptographic usages
  ├── evidence records
  └── review decisions
          ↓
Versioned detection engine
          ↓
Versioned planning-priority engine
          ↓
Advisory recommendation engine
          ↓
Human review and approval workflow
          ↓
Reports and exports
```

Cross-cutting services should include:

- schema validation,
- audit logging,
- assessment versioning,
- standards-reference versioning,
- provider/AI policy enforcement,
- authentication and authorization for shared deployments.

The Streamlit pages should become presentation layers over these services rather than containing business logic directly.

---

## 5. Implementation phases

### Phase 0 — Establish a clean baseline

**Goal:** Make the project reproducible before changing behavior.

Tasks:

- Align Python-version documentation and runtime files.
- Install development dependencies from `requirements-dev.txt`.
- Run the existing tests and record the baseline.
- Add CI installation and test commands if missing.
- Record current demo behavior and current report output.

Exit criteria:

- A clean environment installs successfully.
- Existing tests run.
- Baseline output is recorded.

---

### Phase 1 — Correct naming, status, and provenance

**Goal:** Stop the UI and reports from implying capabilities the code does not have.

Tasks:

- Rename inventory language to declared inventory.
- Add evidence source and collection metadata.
- Rename risk score to planning priority score in user-facing text.
- Label AI fallback as rule-based guidance.
- Add report scope and limitation warnings to the cover page.
- Distinguish owner-reported migration status from verified status.

Exit criteria:

- All user-visible claims match actual implementation.
- Reports identify declared, observed, inferred, stale, and unverified data.

---

### Phase 2 — Strengthen the canonical data model

**Goal:** Represent real systems without hiding secondary cryptographic usage.

Tasks:

- Add crypto-usage records.
- Add evidence records.
- Add review decisions.
- Add assessment input fingerprints and versions.
- Add standards-reference and detector versions.
- Create database migrations rather than relying on implicit table creation.

Exit criteria:

- One asset can contain multiple usages.
- Old records migrate safely.
- Assessment freshness is computable.

---

### Phase 3 — Replace brittle classification with versioned normalization

**Goal:** Improve correctness while preserving explainability.

Tasks:

- Build canonical algorithm aliases.
- Parse compound configurations.
- Separate quantum impact from classical weakness.
- Add ambiguity handling.
- Add a comprehensive detector fixture suite.

Exit criteria:

- Detector results are deterministic, versioned, and explainable.
- Unsupported or contradictory input results in review, not false confidence.

---

### Phase 4 — Repair scoring and freshness behavior

**Goal:** Make prioritization reproducible and prevent stale results.

Tasks:

- Rename and document the planning score.
- Validate weights.
- Fix continuous band boundaries.
- Store configuration versions.
- Add stale assessment invalidation.
- Add score sensitivity and override audit support.

Exit criteria:

- Scores reproduce exactly from stored inputs.
- Boundary tests pass.
- Edited assets cannot silently retain a current-looking old assessment.

---

### Phase 5 — Improve import safety and validation

**Goal:** Make data ingestion safe and predictable.

Tasks:

- Validate enums, dates, duplicates, ranges, and cross-field consistency.
- Add import preview and conflict resolution.
- Make replace/import transactional.
- Add rollback or import-batch recovery.
- Apply the same schema to files and forms.

Exit criteria:

- Invalid imports are rejected before mutation.
- Import failures leave existing data intact.
- Every overwrite is auditable.

---

### Phase 6 — Make recommendations and AI explicitly advisory

**Goal:** Prevent generic guidance from being mistaken for a verified migration plan.

Tasks:

- Add assumptions and blockers to recommendations.
- Add human approval workflow.
- Label AI provider and response mode.
- Add consent and policy controls for external AI.
- Test provider failures and data minimization.

Exit criteria:

- AI and recommendations cannot mutate authoritative assessment data.
- Users can identify exactly how a recommendation was produced.

---

### Phase 7 — Secure shared deployment

**Goal:** Define what is required before the application can safely handle organizational data.

Tasks:

- Add authentication.
- Add authorization and tenant isolation.
- Use managed database storage with migrations and backups.
- Encrypt data in transit and at rest.
- Define logging, retention, deletion, and incident response.
- Add deployment security checks.

Exit criteria:

- A security review approves the deployment model.
- The UI blocks or warns about sensitive uploads when the deployment is not protected.

---

## 6. Test plan for the repaired system

### Detector tests

- RSA, ECDH/ECDHE, ECDSA, EdDSA, DH, and DSA.
- ML-KEM, ML-DSA, and SLH-DSA aliases and parameter sets.
- AES-128 versus AES-256 quantum impact.
- SHA-1, MD5, and 3DES classical weakness.
- Hybrid combinations with multiple components.
- Unknown and vendor-specific names.
- Ambiguous or contradictory purpose data.
- Case, separator, and whitespace variants.

### Scoring tests

- 0 and 100 extremes.
- Every continuous band boundary.
- Invalid or missing values.
- Weight-sum validation.
- Reproducibility from stored configuration.
- Score changes after inventory edits.

### Inventory and database tests

- Duplicate IDs in one upload.
- Duplicate IDs against existing data.
- Transaction rollback after failed import.
- Replace-existing import safety.
- Assessment invalidation after edits.
- Audit log completeness.
- Migration status verification workflow.

### Report tests

- No assets.
- Assets without assessments.
- Stale assessments.
- Unknown algorithms.
- Multi-usage assets.
- Correct report metadata and disclaimer text.
- PDF generation with long and non-ASCII text.

### AI tests

- No provider configured.
- Missing package.
- Timeout.
- Authentication error.
- Empty response.
- Successful Gemini response.
- Successful OpenAI response.
- Confirmation that raw notes, IDs, owners, and secrets are not sent.

### Security tests

- HTML and script-like input in every free-text field.
- CSV formula injection in exported files.
- SQL injection attempts.
- Oversized files and oversized fields.
- Malformed JSON and CSV.
- Secret leakage in logs, reports, and exceptions.
- Unauthorized access in shared deployment mode.

---

## 7. Definition of done

The remediation should not be considered complete until all of the following are true:

- The README accurately describes the product as declared-inventory assessment and planning software.
- The supported Python version and installation instructions are consistent.
- The full test suite runs in a clean environment.
- Inventory records include provenance and freshness information.
- Multiple cryptographic usages per asset are supported.
- Detection is versioned, structured, and ambiguity-aware.
- Quantum risk and classical weakness are separate classifications.
- Planning scores are reproducible and visibly heuristic.
- Score bands have no decimal gaps.
- Stale assessments are clearly marked.
- Migration status distinguishes owner claims from verification.
- Imports are previewed, transactional, and auditable.
- Reports show scope, evidence quality, versions, and limitations.
- AI output is clearly labeled by provider and mode.
- AI cannot modify authoritative data.
- Production/shared deployment requirements are documented and enforced.
- Every discovered bug has a regression test.

---

## 8. Recommended order of priority

If implementation time is limited, use this order:

1. **Reproducible setup and tests** — fix the environment and establish a baseline.
2. **Truthful product labeling** — remove implied discovery, certification, and verified migration claims.
3. **Assessment freshness and score-boundary bugs** — prevent misleading current-looking results.
4. **Multi-usage data model** — prevent important cryptographic dependencies from being hidden.
5. **Validation and transactional imports** — prevent accidental data loss and invalid records.
6. **Versioned detector and standards references** — make findings auditable.
7. **Recommendation and AI labeling** — make advisory output unmistakable.
8. **Authentication, authorization, and tenant isolation** — required before handling sensitive shared data.
9. **Real discovery connectors** — only after the canonical model and evidence workflow are ready.

This order fixes the highest-risk correctness and honesty problems before adding more integrations or visual polish.
