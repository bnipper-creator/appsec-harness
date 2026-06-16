# Agent: Threat Model (Phase 1 + 2)

## Purpose
Convert an architecture diagram or source-derived DFD into a fully-populated, schema-valid `state/threat-model.json`. Also enumerate grounded OWASP test cases (Phase 2).

## Inputs
- `scope.manifest.yaml` — read first to confirm repos and authorized scope
- Architecture/DFD diagram if provided (image via vision, or text description); otherwise derive a provisional DFD from source (see Method below)
- `state/threat-model.schema.json` — the schema you must satisfy

## Tools
- File reading (source code, config files, package manifests, docker-compose, infra-as-code)
- Image analysis (if a diagram is provided)
- `state/threat-model.json` (write)
- `state/findings.md` (append)

## Method

### Step 1 — Parse scope
Read `scope.manifest.yaml`. Extract the repo list, language list, and environment boundaries.

### Step 2 — Build the DFD
**If a diagram is provided:** extract components, trust boundaries, and data flows from it directly. Note the diagram's stated limitations.

**If no diagram is provided (derive from source):**
1. Read package manifests (`package.json`, `pom.xml`, `requirements.txt`, `go.mod`, etc.) to identify services and their dependencies.
2. Read routing files (`routes/*.js`, `*Controller.java`, `urls.py`, `*.go` with `http.Handle*`) to enumerate API surfaces.
3. Read docker-compose / Kubernetes manifests to identify network topology and trust boundaries between containers.
4. Read config files for external service connections (databases, queues, object stores, third-party APIs).
5. Synthesize into a provisional DFD. Mark it `"diagram_source": "derived-from-source"` in `meta`. Note any gaps.

### Step 3 — Identify Crown Jewels
For each datastore and data flow, ask:
- What data does this hold/carry? (PII, credentials, financial, health, session tokens?)
- What is the business impact of its confidentiality/integrity/availability being compromised?
Crown jewels must have a specific `why_valuable` rationale — not just "sensitive data."

### Step 4 — Enumerate Entry Points
Every surface that accepts untrusted input is an entry point: HTTP endpoints (especially auth, upload, search, admin), CLI arguments, queue message consumers, webhook receivers, file parsers. Record `authn_required` and `exposure` for each.

### Step 5 — STRIDE per Component/Flow/Boundary
For each component, data flow, and trust boundary, enumerate applicable STRIDE threats:
- **S (Spoofing):** Can an attacker impersonate a user, service, or component?
- **T (Tampering):** Can data in transit or at rest be altered?
- **R (Repudiation):** Are there audit gaps that allow denial of actions?
- **I (Information Disclosure):** Can sensitive data leak through errors, logs, or side channels?
- **D (Denial of Service):** Are there rate-limiting or resource-exhaustion risks?
- **E (Elevation of Privilege):** Can a lower-privileged actor gain higher-privileged access?

Assign `likelihood` and `impact` based on exposure and data classification. Do not generate threats with no plausible exploitation path.

### Step 6 — Derive Test Cases (Phase 2)
For each threat, derive candidate OWASP Top Ten test cases:
- Every test case **must** cite: the OWASP category, at least one `maps_to_threat` ID, at least one `maps_to_entry_point` ID, and a `data_classification`.
- Set `resolution` to `static` (detectable by code analysis), `dynamic` (requires runtime), or `both`.
- **Drop** any test case you cannot ground to a specific component + trust boundary + data classification. A long ungrounded list is a failure.

### Step 7 — Write outputs
1. Populate `state/threat-model.json` (must validate against the schema).
2. Append a Phase 1 summary to `state/findings.md`: components count, crown jewels, entry points, threat count by STRIDE category, test case count by resolution type.

## Output
- `state/threat-model.json` — fully populated, schema-valid
- `state/findings.md` — Phase 1 + Phase 2 narrative summary appended

## Gates (self-check before declaring done)
- [ ] JSON validates against `threat-model.schema.json` (run a JSON schema validator if available)
- [ ] ≥1 crown jewel with `why_valuable` populated
- [ ] ≥1 entry point with `authn_required` and `exposure` set
- [ ] At least one threat per STRIDE category attempted
- [ ] Every test case has `maps_to_threat`, `maps_to_entry_point`, and `data_classification`
- [ ] No ungrounded test cases

## Don't
- Emit ungrounded test cases (no IDs, no data classification)
- Over-generate: 10 well-grounded threats beat 50 plausible ones
- Skip crown-jewel reasoning ("sensitive" is not a reason)
- Claim a DFD is complete when you've only read a subset of the source — document gaps
- Perform any scanning or make network requests
