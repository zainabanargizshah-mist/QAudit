# Q-Shield Startup-Readiness, Security, and Enterprise Plan

## Status

**Planning document only. No application code is changed by this document.**

This is the second plan for Q-Shield. It builds on `docs/REMEDIATION_PLAN.md` and
adds the attacker, enterprise buyer, customer, operational, and venture-readiness
perspectives needed to turn the prototype into a credible startup product.

The goal is not to claim that Q-Shield is already enterprise-ready. The goal is to
define the smallest credible path from a declared-inventory prototype to a secure,
evidence-driven enterprise product that judges, design partners, CISOs, and VCs can
trust.

---

## 1. The product we should actually sell

### 1.1 Positioning

Q-Shield should be positioned as:

> **An evidence-backed cryptographic migration intelligence platform that helps
> enterprises discover what they use, prove what is known, prioritize what matters,
> and coordinate a post-quantum migration.**

The differentiator is not “an AI chatbot that knows PQC.” The defensible product is:

1. A canonical cryptographic inventory.
2. Evidence and provenance attached to every observation.
3. A deterministic and explainable assessment engine.
4. A reviewable migration-workflow system.
5. An advisory AI layer that cannot change authoritative security data.
6. An auditable record that can survive procurement, security review, and executive scrutiny.

### 1.2 Product truth today

The current repository is a strong prototype for declared inventory, rule-based
classification, planning scores, generic migration guidance, reports, and optional
LLM assistance. It is not yet a shared enterprise security system because it lacks
identity, tenant isolation, a production authorization model, durable audit controls,
verified discovery, mature evidence handling, and a hardened AI boundary.

That limitation should be treated as a product strength during the pitch: Q-Shield
will not pretend that a manually uploaded CSV is live discovery or that a heuristic
score is a compliance rating.

### 1.3 Promise and non-promise

**Promise:** reduce uncertainty and time-to-decision for PQC migration programs.

**Do not promise yet:** continuous discovery of every cryptographic use, proof of
quantum safety, regulatory certification, automatic migration, or complete prevention
of prompt injection. Prompt injection is a risk class to contain, not a problem that a
stronger system prompt can eliminate.

---

## 2. Attacker-first threat model

### 2.1 Crown jewels

Protect these assets first:

| Asset | Why it matters | Minimum protection target |
|---|---|---|
| Enterprise inventory and evidence | Reveals systems, owners, protocols, certificate details, and dependencies | Tenant isolation, encryption, least privilege, retention controls |
| Assessment results and scores | Can influence remediation budgets and executive decisions | Versioned inputs, deterministic replay, tamper-evident audit |
| Migration plans and approvals | May expose strategic architecture and change windows | Role-based access, approval history, export controls |
| Reports and exports | Can be forwarded outside the platform and mistaken for certification | Scope labels, provenance, signed/versioned output, safe export |
| Provider credentials | A compromise can create cost, data leakage, or account takeover | Secret manager, no logs, rotation, scoped provider access |
| Prompts, retrieved context, and model output | May contain confidential data or attacker-controlled instructions | Data minimization, trust separation, output validation |
| Tenant and user metadata | Enables lateral movement and privacy violations | Strong authorization on every request, not only in the UI |

### 2.2 Adversaries

Plan for:

1. **Unauthenticated internet attacker** probing the deployed app and upload paths.
2. **Malicious or compromised customer user** attempting to read another workspace,
   overwrite findings, poison evidence, or export sensitive data.
3. **Curious insider or over-privileged operator** accessing customer inventories.
4. **Prompt-injection attacker** who places instructions inside asset names, notes,
   uploaded files, certificates, connector output, or retrieved documents.
5. **Compromised dependency or CI credential** attempting supply-chain compromise.
6. **Abusive user** causing denial of service, excessive model spend, or export floods.
7. **Mistaken legitimate user** deleting data, importing duplicate IDs, or approving
   an unverified migration claim.

### 2.3 Attack paths to test explicitly

| Scenario | Impact | Required design response |
|---|---|---|
| Malicious CSV contains prompt instructions | Model follows attacker content and gives unsafe advice | Treat imported data as untrusted data; never as instructions; isolate context |
| Asset notes attempt to reveal the system prompt | Confidentiality loss and trust damage | Do not expose system prompts; redact secrets; test direct and indirect injection |
| LLM output is rendered as HTML/Markdown | Stored or reflected XSS, misleading report content | Render safely; encode untrusted text; sanitize model output |
| LLM suggests changing an asset or status | Integrity loss | AI remains read-only; all mutations require deterministic application code and human approval |
| User changes an asset after assessment | Stale decision presented as current | Revision/fingerprint invalidation and visible stale state |
| Duplicate import overwrites a critical asset | Data loss or silent tampering | Preview, conflict policy, transaction, rollback, audit event |
| Tenant A guesses Tenant B's asset ID | Cross-tenant disclosure | Authorize by workspace on every read/write/export; never trust object IDs |
| Provider timeout is retried without a budget | Cost spike and availability degradation | Timeouts, bounded retries, per-tenant quotas, circuit breaker |
| Export contains spreadsheet formulas | Formula injection when opened in Excel | Neutralize formula-leading cells and test exported CSVs |
| “Completed” migration is self-reported | False executive confidence | Separate owner claim, verification status, evidence, reviewer, and timestamp |

### 2.4 Trust boundaries

The future architecture should make these boundaries explicit:

```text
Customer browser / SSO
        ↓ authenticated request
Application/API boundary
        ↓ authorization and tenant policy
Canonical data and evidence services
        ↓ versioned, deterministic assessment
Assessment and planning engines
        ↓ sanitized, minimum-necessary context only
LLM provider boundary
        ↓ untrusted response
Output validator and policy gate
        ↓ read-only advisory display or human-approved action
Reports, exports, and integrations
```

No model response should cross from the LLM boundary directly into a database write,
workflow transition, connector action, or external notification.

---

## 3. Security architecture target

### 3.1 Identity and workspace isolation — launch blocker

Before handling real multi-person enterprise data, add:

- OIDC/SAML SSO through the customer's identity provider.
- MFA delegated to the identity provider; no custom password storage in the first release.
- SCIM or an equivalent managed user lifecycle path for larger customers.
- Workspace/tenant IDs on every customer-owned record.
- Server-side authorization checks on every read, write, assessment, report, export,
  and AI request.
- RBAC at minimum: Workspace Owner, Security Analyst, Reviewer, Executive Read-only,
  and Platform Administrator.
- Optional ABAC constraints for business domain, environment, or data classification.
- Short-lived sessions, secure cookies, logout/revocation, and protection against
  session fixation.
- Break-glass administration with explicit reason, time limit, and audit trail.

The UI must never be the security boundary. A user hiding a button must not be the
only control preventing an unauthorized action.

### 3.2 Data protection and privacy

Plan for:

- TLS for all network paths.
- Managed database with encryption at rest and tested backups.
- Central secret management; API keys must never be committed, printed, or included
  in exception text.
- Field classification for inventory data, evidence, owner information, and notes.
- Configurable retention and deletion, including customer-requested workspace deletion.
- Export and access logs for sensitive reports.
- Data minimization before any external model call.
- Customer-facing data processing terms, subprocessors, regions, and deletion behavior.
- A future enterprise option for customer-managed keys or BYOK only after the core
  tenant and key-management model is reliable.

### 3.3 Evidence integrity and auditability

Every important result should be explainable and replayable from:

- Input revision and fingerprint.
- Evidence source and collection time.
- Normalizer/detector version.
- Standards-reference version and verification date.
- Scoring configuration version.
- Recommendation version.
- Human reviewer, decision, reason, and timestamp.
- Actor, workspace, correlation ID, and action outcome.

Audit records should be append-only from the application perspective, protected from
ordinary workspace users, and shipped to an operational sink in the hosted product.
For high-value reports, store a content hash and report version so a later reader can
detect silent alteration.

### 3.4 Import and connector security

Imports and future discovery connectors are untrusted ingestion channels.

Required controls:

- File type, size, decompression, row, field, and record-count limits.
- Strict schema validation and row-level error reporting.
- Duplicate detection before mutation.
- Atomic import with preview, conflict resolution, and rollback/recovery.
- Safe handling of CSV formula injection and dangerous encodings.
- Malware scanning or quarantine for enterprise-uploaded files where applicable.
- No arbitrary file execution, archive traversal, shell invocation, or dynamic imports.
- Connector credentials scoped read-only and to the smallest possible account/resource set.
- Connector jobs isolated from the web process and cancellable.
- Raw evidence retained separately from normalized records with explicit retention.

Discovery should be added only after evidence, authorization, and provenance are strong
enough to explain what was observed and what remains unknown.

### 3.5 Secure software delivery

Adopt a lightweight secure-development baseline before the first paid pilot:

- Dependency lock/pinning and automated vulnerability review.
- Secret scanning and pre-commit checks.
- SAST, dependency/SCA scanning, and container/image scanning if containerized.
- SBOM generation for each release.
- Protected main branch, required review, and CI checks.
- Reproducible build metadata and signed release artifacts where practical.
- Separate development, staging, and production credentials and data.
- Security regression tests for each fixed issue.
- Vulnerability disclosure and patching process.
- A written incident-response runbook and customer-notification procedure.

---

## 4. LLM security plan: useful, bounded, and non-authoritative

### 4.1 Design principle

The LLM is an **advisory analyst**, not an assessor of record, policy engine, workflow
executor, or source of truth. Deterministic detection, scoring, validation, and status
transitions must remain outside the model.

### 4.2 Prompt and context handling

Use separate structured fields for:

- Trusted application instructions.
- The user's actual question.
- Deterministic assessment facts.
- Untrusted customer content.
- Retrieved standards excerpts.
- Tool results, if tools are ever introduced.

The model must be told that customer content is data to analyze, not instructions to
follow. That statement is helpful but not sufficient; the real boundary is enforced by
permissions, data minimization, output validation, and the absence of privileged tools.

Do not send raw owner names, asset IDs, secrets, credentials, private notes, or full
uploads to a provider unless the customer has explicitly enabled that data path and the
policy allows it. Prefer a redacted, structured summary generated by application code.

### 4.3 No autonomous actions in the first enterprise release

The first production AI surface should support only:

- Explain this finding.
- Summarize this reviewed assessment.
- Identify missing evidence.
- Draft questions for an application owner.
- Compare documented migration options.

It should not:

- Modify assets, scores, or migration status.
- Approve a plan.
- Call cloud, ticketing, email, deployment, or identity APIs.
- Browse arbitrary external sites at runtime.
- Execute code or interpret uploaded files as executable content.
- Retrieve records outside the current authorized workspace.

### 4.4 Output safety

Every model response should pass through application checks for:

- Provider, model, timestamp, and policy mode.
- Required structured sections: conclusion, evidence, assumptions, uncertainty,
  recommended next action, and cited standard/reference.
- Unsupported claims, fabricated citations, compliance/certification language, and
  algorithm-purpose contradictions.
- Cross-tenant or secret-like content.
- Excessive length and suspicious instruction leakage.
- Safe rendering without executable HTML or unsafe links.

If validation fails, show a safe fallback or “unable to provide advisory output” rather
than silently displaying untrusted text.

### 4.5 AI security test suite

Maintain harmless adversarial fixtures covering:

- Direct “ignore previous instructions” prompts.
- Indirect injection in asset names, notes, CSV cells, JSON values, and certificate text.
- Unicode, base64, whitespace, multilingual, and encoded variants.
- Attempts to obtain system prompts, API keys, hidden context, or other tenants' data.
- Attempts to make the model change scores or mark migration complete.
- Fabricated standards and citation tests.
- Long-context truncation and denial-of-service cases.
- Provider timeout, rate-limit, auth failure, empty response, and malformed response.

Success means the authoritative record remains unchanged, no secret or cross-tenant data
is disclosed, the response is labeled correctly, and the event is observable.

---

## 5. Enterprise customer experience

### 5.1 Primary buyers and users

**Economic buyer:** CISO, Deputy CISO, enterprise architecture leader, or risk leader
who owns the PQC program and needs defensible prioritization.

**Operational users:** cryptography engineers, PKI/HSM owners, application security,
platform teams, infrastructure owners, and risk/compliance analysts.

**Executive audience:** CIO, board-risk committee, audit committee, and procurement.

### 5.2 The customer journey we must support

1. **Establish trust** — SSO, data handling disclosure, scope, deployment model,
   security documentation, and a safe synthetic demo.
2. **Create a workspace** — define organization, business domains, environments,
   classification policy, reviewers, and retention policy.
3. **Ingest evidence** — upload a declared inventory or connect a read-only source;
   preview coverage and conflicts before import.
4. **Normalize and assess** — show what was observed, inferred, unknown, stale, or
   contradictory; never hide uncertainty.
5. **Prioritize** — explain the planning priority with factors, assumptions, and
   sensitivity; separate urgency from migration complexity.
6. **Plan** — create conditional migration work items with owners, blockers,
   validation tests, rollback requirements, and target dates.
7. **Review and approve** — require qualified human review for high-impact decisions.
8. **Prove progress** — track evidence-backed status, not only self-reported completion.
9. **Report** — generate executive, engineering, and auditor-friendly views with scope,
   provenance, freshness, limitations, and version metadata.
10. **Monitor** — show new, changed, stale, unverified, and overdue records over time.

### 5.3 UX rules for enterprise trust

- Put scope and limitations at the point of decision, not only in a methodology page.
- Make “unknown,” “stale,” “unverified,” and “needs review” visually prominent.
- Give every score an explanation and a “what would change this?” path.
- Use progressive disclosure: executive summary first, evidence and rule details one
  click away, raw evidence available to authorized technical users.
- Make destructive actions explicit, reversible where possible, and audited.
- Show data-sharing status before the first external AI call.
- Provide export formats that match real workflows: CSV for engineering, PDF for
  governance, and API/webhooks later for ticketing and GRC systems.
- Never use green checkmarks to mean “secure” when the actual state is “not assessed.”

### 5.4 Enterprise objections and product answers

| Buyer objection | Product answer we must demonstrate |
|---|---|
| “How do I know this is not a chatbot demo?” | Deterministic engine, versioned evidence, replayable scores, and AI-independent results |
| “Can it see everything?” | Coverage dashboard showing declared, observed, unknown, stale, and unconnected scope |
| “Can it prove a migration happened?” | Owner claim versus verification workflow with evidence and reviewer history |
| “Will our data train a model?” | Explicit provider policy, minimization, opt-in controls, and documented retention behavior |
| “Can one customer see another customer’s data?” | Workspace authorization tests, isolation evidence, and security review artifacts |
| “Can we integrate it?” | Stable import schema first; documented API and ticket/GRC integrations after core controls |
| “Will it survive procurement?” | Security packet, architecture diagram, subprocessors, incident process, availability targets, and roadmap |

---

## 6. Business and venture readiness

### 6.1 Beachhead market

Start with organizations that have all three characteristics:

1. Long-lived sensitive data or signatures.
2. Large, heterogeneous technology estates.
3. A funded security, architecture, or compliance program but incomplete crypto visibility.

Good design-partner profiles include financial services, payments, healthcare, critical
infrastructure, telecom, government contractors, and large SaaS providers. The first
customer should not require Q-Shield to scan the entire world; it should need a narrow,
high-value inventory and an executive-ready migration decision.

### 6.2 Initial product packaging

**Pilot / assessment package**

- One workspace and a defined scope.
- Secure inventory import.
- Evidence coverage and normalization.
- Deterministic assessment and prioritization.
- Human-reviewed migration backlog.
- Executive and technical reports.
- Limited advisory AI, disabled by default until data policy is accepted.

**Enterprise platform package**

- SSO, RBAC, audit export, retention controls, managed connectors, recurring evidence
  refresh, API access, support SLA, and customer security documentation.

**Services-assisted package**

- Q-Shield-led inventory normalization and migration-program design for customers that
  need help interpreting legacy systems. Services should accelerate product adoption,
  not become a permanent substitute for product repeatability.

### 6.3 Metrics that prove customer value

Track metrics that matter to a CISO, not vanity chatbot metrics:

- Time from first upload to a reviewed priority list.
- Percentage of records with evidence source and collection date.
- Percentage of records with known cryptographic purpose.
- Unknown/ambiguous rate and reduction over time.
- Stale-assessment rate.
- Percentage of high-priority assets with an assigned owner and next action.
- Time from finding to approved migration work item.
- Number of prevented duplicate/unsafe overwrites.
- AI advisory acceptance rate after human review, not raw model usage.
- Mean time to revoke a user or connector.
- Security incident and cross-tenant test results.

### 6.4 Defensible moat

The moat should accumulate in:

- A normalized cryptographic-usage and evidence schema.
- Real-world algorithm/protocol/vendor fixture data, with customer permission.
- Explainable rules and assessment history.
- Migration dependency graphs and verified implementation evidence.
- Integrations into enterprise workflows.
- Trust: security posture, honest claims, and audit-ready outputs.

The moat should not depend on a single model vendor or an uninspectable prompt.

---

## 7. Prioritized execution roadmap

This roadmap extends the phases in `docs/REMEDIATION_PLAN.md`. It intentionally puts
truthfulness and security foundations before autonomous features or broad connectors.

### Phase A — Pitch-safe foundation

**Goal:** make the current prototype safe to show without overstating its capability.

Deliverables:

- Product scope statement and threat model.
- Clear demo/prototype versus shared-production mode.
- Synthetic demo dataset and repeatable demo script.
- Baseline test command, CI, dependency inventory, and known-risk register.
- Honest naming: declared inventory, planning priority, planning guidance, advisory AI.
- No secrets in repository, logs, reports, or screenshots.
- Security architecture diagram and data-flow diagram.

**Gate:** a judge can understand exactly what is real, what is simulated, and what is
planned in under five minutes.

### Phase B — Correctness and evidence foundation

**Goal:** make every conclusion traceable.

Deliverables from the remediation plan:

- Multi-usage asset model.
- Evidence/provenance records.
- Versioned normalization and detection.
- Separate quantum exposure, classical weakness, migration complexity, and confidence.
- Assessment fingerprints and stale invalidation.
- Continuous score bands, reproducible configuration, and auditable overrides.
- Transactional imports, preview, conflict handling, and rollback/recovery.
- Review decisions and owner-claim versus verification status.

**Gate:** two reviewers can reproduce the same result from the same input snapshot and
explain every material recommendation.

### Phase C — Secure application core

**Goal:** prevent common compromise and data-integrity failures.

Deliverables:

- Backend/API boundary with server-side authorization.
- Workspace/tenant isolation in schema, queries, tests, and exports.
- OIDC/SAML SSO, MFA via IdP, RBAC, session controls, and admin audit.
- Managed database, migrations, backups, restore drill, retention, and deletion.
- Central secrets management and key rotation.
- Safe rendering, CSP/security headers where applicable, upload hardening, output
  encoding, CSV formula protection, rate limits, and abuse controls.
- Security logging with correlation IDs and no sensitive payloads.

**Gate:** no customer pilot with sensitive data until isolation tests, restore tests,
authorization tests, and an independent security review pass.

### Phase D — Bounded AI layer

**Goal:** provide useful AI without turning it into a privileged attack surface.

Deliverables:

- Provider policy and customer consent.
- Redaction/minimization pipeline.
- Structured context envelope distinguishing trusted instructions from untrusted data.
- Read-only advisory endpoints.
- Output validator, citation/reference checks, safe rendering, and fallback behavior.
- Per-tenant budgets, timeout/circuit-breaker behavior, model allowlist, and kill switch.
- Prompt-injection regression suite and provider-failure tests.
- UI metadata: provider, model, policy mode, timestamp, and “advisory only.”

**Gate:** malicious customer content cannot alter authoritative data, reveal secrets,
cross a workspace boundary, or trigger an external side effect.

### Phase E — Design-partner beta

**Goal:** validate the product with a small number of controlled customers.

Deliverables:

- One narrow read-only connector or a hardened import workflow, not ten integrations.
- Customer onboarding checklist and data-handling agreement.
- Support and incident runbooks.
- Security questionnaire packet and architecture documentation.
- Usage analytics that exclude sensitive payloads.
- SLOs, backup/restore evidence, vulnerability response process, and release notes.
- Feedback loop tied to measurable outcomes from Section 6.3.

**Gate:** at least one design partner completes import → review → plan → report with
documented time saved and no unresolved critical security finding.

### Phase F — Enterprise expansion

**Goal:** make the product procurement-ready and operationally repeatable.

Consider only after the core path is stable:

- More read-only connectors and evidence refresh.
- Dependency graph and program-level planning.
- API, webhooks, ticketing/GRC integrations.
- Customer-managed keys/BYOK and regional deployment options.
- Formal external penetration test.
- SOC 2/ISO 27001 readiness work based on actual controls and customer demand.
- High-availability architecture and tested disaster recovery.

---

## 8. Launch gates and stop-ship conditions

### Stop-ship conditions

Do not market or deploy as an enterprise service if any of these are true:

- No authenticated identity and server-side workspace authorization.
- Shared storage without verified tenant isolation.
- API keys or customer secrets appear in logs, reports, source, or telemetry.
- AI can mutate authoritative data or invoke privileged tools without human approval.
- Imports can silently overwrite or delete data without preview and audit.
- Stale assessments appear current.
- Reports imply certification, compliance, live discovery, or verified migration without evidence.
- Backups exist but restore has not been tested.
- A critical vulnerability is known and has no compensating control or release decision.

### Minimum security-release evidence

For each production release, retain:

- Dependency and secret-scan results.
- Test results, including security regression tests.
- Migration and rollback plan.
- Threat-model changes.
- Release artifact and configuration version.
- Known issues and risk acceptance, if any.
- Security owner approval for material changes.

### Minimum customer trust packet

- Product scope and limitation statement.
- Architecture and data-flow diagrams.
- Data classification and retention policy.
- Identity, authorization, and tenant-isolation description.
- Encryption and secrets-management description.
- Subprocessor/provider list and AI data-use policy.
- Incident response and vulnerability disclosure process.
- Backup/restore and availability summary.
- Pen-test or independent review status.
- Business continuity and exit/deletion procedure.

---

## 9. The judge and VC demonstration

### 9.1 Five-minute narrative

1. Start with the enterprise problem: cryptography is distributed, opaque, and hard to
   prioritize before a quantum deadline or long-lived data exposure.
2. Import a synthetic inventory and show evidence coverage, not a fake “100% secure” score.
3. Show one asset with multiple usages, an unknown item, and a stale assessment.
4. Open a priority result and explain each factor, version, and assumption.
5. Generate planning guidance with owner, blocker, validation test, and rollback fields.
6. Ask the advisory AI to summarize the reviewed result.
7. Inject a malicious instruction into an asset note and show that the AI treats it as
   untrusted content, does not reveal hidden instructions, and cannot change the score.
8. Show the audit trail and report disclaimer.
9. Close with the roadmap: evidence-backed inventory first, read-only discovery next,
   enterprise integrations after trust foundations.

### 9.2 Claims to avoid in the pitch

- “We automatically discover all cryptography.”
- “Our score is a security rating or compliance certification.”
- “The LLM is secure against prompt injection.”
- “The platform proves an organization is quantum-safe.”
- “Migration is complete because the status says completed.”
- “We are SOC 2/ISO certified” unless that certification actually exists.

### 9.3 Stronger proof points

- “Every finding has provenance and a reproducible assessment version.”
- “Unknown and stale data are first-class risk states.”
- “The model cannot edit the authoritative record.”
- “A prompt-injection fixture leaves the score, inventory, and workflow unchanged.”
- “The report separates observed facts, inferences, owner claims, and recommendations.”
- “We sell decision velocity and evidence quality, not chatbot novelty.”

---

## 10. Definition of startup readiness

Q-Shield is ready for a controlled enterprise pilot when:

- The product scope is truthful and visible.
- The canonical model supports multiple usages and evidence provenance.
- Results are deterministic, versioned, reproducible, and freshness-aware.
- Imports are previewed, validated, transactional, and auditable.
- SSO, RBAC, tenant isolation, encryption, backups, deletion, and audit controls exist.
- The AI layer is opt-in, minimized, read-only, bounded, observable, and tested against
  direct and indirect prompt injection.
- Reports clearly separate facts, inference, claims, verification, and guidance.
- CI, dependency, secret, vulnerability, and regression checks run on every release.
- A restore drill, authorization test, security review, and incident tabletop have passed.
- At least one design partner has completed the core workflow and confirmed measurable value.

Q-Shield is ready to scale beyond pilots when those controls are repeatable across
customers, operational metrics are stable, and procurement/security documentation can
be produced without founder heroics.

---

## 11. Recommended immediate decisions

1. Keep the first paid product as a **secure assessment and migration-intelligence
   system**, not an autonomous remediation agent.
2. Make **evidence quality and workflow verification** the core product metric.
3. Treat **identity, tenant isolation, and auditability** as product features, not
   infrastructure work to postpone.
4. Keep LLM features **opt-in and read-only** until the trust boundary is proven.
5. Use the existing remediation plan as the engineering backlog, and this document as
   the security, enterprise, and go-to-market gate.
6. Build one excellent design-partner workflow before adding broad discovery coverage.

The next implementation plan should be created only after the team accepts these
boundaries and chooses the first design-partner scope.

---

## 12. External framework alignment to keep current

Use recognized frameworks as a control checklist, not as marketing decoration:

- **NIST Secure Software Development Framework (SP 800-218) plus SP 800-218A:**
  secure design, implementation, verification, vulnerability response, release
  evidence, and AI-specific secure development practices.
- **NIST AI Risk Management Framework, Generative AI Profile, and the 2026 critical-
  infrastructure profile work:** governance, measurement, human oversight, privacy,
  security, and documented risk treatment for the advisory model layer.
- **OWASP Top 10 for LLM Applications (2026 edition, current as of October 24, 2026):**
  use the current risk categories and mappings for prompt injection, sensitive
  information disclosure, supply chain, data/model poisoning, improper output handling,
  excessive agency, system-prompt leakage, vector/embedding weaknesses,
  misinformation, and unbounded consumption.
- **OWASP Application Security Verification Standard:** authentication, access
  control, validation, session security, logging, and secure configuration.
- **CISA Secure by Design principles:** make safe behavior the default, reduce the
  security burden on customers, and make security outcomes measurable.

Before each major release, assign an owner to verify the current editions and any
sector-specific requirements. Standards and model-provider behavior change; the
application must store the reference version and verification date rather than implying
that a static document is live compliance validation.
