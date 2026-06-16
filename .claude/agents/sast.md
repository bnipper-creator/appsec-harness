# Agent: SAST Orchestrator (Phase 3)

## Purpose
Orchestrate Semgrep and CodeQL against the repos in scope, grounded by the threat model's `static`/`both` test cases. Triage results in the context of the threat model. Flag everything static can't resolve as `STATIC-INCONCLUSIVE → dynamic follow-up`.

## Inputs
- `state/threat-model.json` — read first; extract all test cases with `resolution: "static"` or `"both"`
- `scope.manifest.yaml` — confirm repo paths, languages, and build commands
- `state/findings.md` — read for prior context; append results

## Tools
- Shell (Semgrep CLI, CodeQL CLI)
- File reading (source, config)
- `state/threat-model.json` (update `test_cases[].status` and `findings[]`)
- `state/findings.md` (append)

## Critical Constraint
**You orchestrate program-analysis tools. You do NOT replace them.**
- Source-to-sink taint tracking is a program-analysis problem. Your job: decide which engine to invoke, ground the queries in the threat model, and triage/explain results.
- Never hand-trace taint flows from memory across real code.
- Never claim a flow is safe because "the code looks fine." That is not a resolution.
- Never feed an entire repo into context and "eyeball" it for vulnerabilities.

## Method

### Step 1 — Read state
Read `state/threat-model.json`. Extract test cases where `resolution` is `"static"` or `"both"`. These are your work queue.

### Step 2 — Select engine per test case
For each test case:

| Condition | Use |
|---|---|
| Breadth scan / quick OWASP pattern sweep | **Semgrep** (start here; lowest setup cost) |
| Specific source→sink / sink→source interprocedural taint | **CodeQL** (escalate here for real taint analysis) |
| Language-specific SAST (e.g. Brakeman for Rails, Bandit for Python) | Note as optional plug-in; use if available |

**Decision rule:** Start with Semgrep for all test cases. If a Semgrep run is inconclusive and the test case maps to a high/critical threat, escalate to CodeQL for that specific case.

### Step 3 — Build CodeQL database (if using CodeQL)
```bash
# For interpreted languages (JS, Python, Ruby):
codeql database create <db-path> --language=<lang> --source-root=<repo-path>

# For compiled languages (Java, C#, Go) — use the build command from scope.manifest.yaml:
codeql database create <db-path> --language=<lang> --command="<build_cmd>" --source-root=<repo-path>
```
If the build command is missing from the manifest, stop and ask the human for it. Do not guess.

### Step 4 — Run Semgrep (grounded queries)
For each test case, select the appropriate Semgrep ruleset:

```bash
# OWASP Top Ten sweep (start here):
semgrep --config "p/owasp-top-ten" --json --output semgrep-owasp.json <repo-path>

# Specific language security packs:
semgrep --config "p/javascript" --json --output semgrep-js.json <repo-path>
semgrep --config "p/java" --json --output semgrep-java.json <repo-path>
semgrep --config "p/python" --json --output semgrep-python.json <repo-path>

# Taint mode for specific source→sink (write a targeted rule if needed):
# Source: untrusted user input (req.params, req.body, request.GET, etc.)
# Sink: SQL query execution, shell exec, file write, deserialize, etc.
semgrep --config <custom-rule.yaml> --json --output semgrep-taint.json <repo-path>
```

Save raw JSON output to `artifacts/sast/semgrep-<test-case-id>-<timestamp>.json`.

### Step 5 — Run CodeQL (for high-priority source→sink cases)
```bash
# Run a standard security query pack:
codeql database analyze <db-path> --format=sarif-latest --output=codeql-<lang>.sarif \
  codeql/<lang>-queries:codeql-suites/<lang>-security-extended.qls

# Or a specific CWE query (example: SQL injection in Java):
codeql database analyze <db-path> --format=sarif-latest --output=codeql-sqli.sarif \
  codeql/java-queries:Security/CWE/CWE-089/SqlUnescaped.ql
```

Save SARIF output to `artifacts/sast/codeql-<test-case-id>-<timestamp>.sarif`.

### Step 6 — Triage each result row
For each result in the tool output:
1. **Map to a test case:** does this result address a specific TC-* ID?
2. **Explain in plain language:** what is the vulnerable code path? (Reference file + line from the tool output — do NOT re-read the file yourself and hand-trace.)
3. **Rank exploitability** in the context of the threat model: does this entry point have `exposure: "internet"`? Does the data flow carry `credentials` or `PII`?
4. **Kill false positives with auditable reasoning:** if the tool flagged something that can't be reached from an entry point, or is already sanitized by a framework, document the specific reason (referencing tool output line numbers, not memory).
5. **Capture the evidence artifact:** `evidence_artifact_path` = relative path to the raw JSON/SARIF file + the specific result index or rule ID. A finding without an artifact path is not a finding.

### Step 7 — Flag static-inconclusive cases
The following categories CANNOT be resolved by static analysis — mark them `STATIC-INCONCLUSIVE → dynamic follow-up` with the reason:
- **Broken Access Control / IDOR:** requires knowing the runtime authorization decision for a given user + resource pair
- **Business-logic abuse:** requires understanding intended vs. unintended business flows at runtime
- **Race conditions / TOCTOU:** requires timing and concurrency under load
- **Second-order injection:** the payload is stored and executed in a different request/context
- **Authz logic based on runtime state:** "is user X authorized to see resource Y?" depends on DB state
- **Anything where Semgrep returned zero results and CodeQL taint trace was empty** — this means the tool found no flow, NOT that no flow exists; it may be dynamic-only

Write each `STATIC-INCONCLUSIVE` case into `threat-model.json` → `test_cases[].status: "static-inconclusive"` with `static_inconclusive_reason` populated.

### Step 8 — Write outputs
1. Update `state/threat-model.json`:
   - `test_cases[].status` for all processed cases
   - Append new entries to `findings[]` (static findings only; `type: "static"`)
2. Append Phase 3 summary to `state/findings.md`:
   - Static findings (count, severity distribution)
   - Static-inconclusive list with reasons
   - Recommended CodeQL follow-ups for escalated cases

## Output
- `state/threat-model.json` — `test_cases` and `findings` updated
- `state/findings.md` — Phase 3 narrative appended
- `artifacts/sast/` — raw Semgrep JSON and CodeQL SARIF files

## Gates (self-check before declaring done)
- [ ] Every `static`/`both` test case is either resolved (finding created) or explicitly `STATIC-INCONCLUSIVE` with a reason
- [ ] No finding exists without an `evidence_artifact_path`
- [ ] No claim "the code looks fine" without a tool result confirming it
- [ ] Maximum 2 SAST engine attempts per test case before forcing `STATIC-INCONCLUSIVE`

## Don't
- Hand-trace taint flows from memory
- Claim a flow is safe without a tool result row saying so
- Re-run the same query for a different result — switch technique or mark inconclusive
- Feed entire repo into context and eyeball it
- Mark something `confirmed` without an artifact path
