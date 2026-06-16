# AppSec Solver Harness — Orchestrator

## Scope (Hard Rules)

- **In-scope assets only.** Every host, repo, and environment must appear in `scope.manifest.yaml`. Any host/repo/URL that surfaces in tool output but is NOT in the manifest → surface it to the human and **stop immediately**.
- **No destructive actions.** No data deletion, schema drops, or state-mutating calls against the target beyond what a read-only probe requires.
- **Active/dynamic testing is human-gated.** The agent stages a plan and halts. A human must approve before any traffic is sent. See Phase 4, Sub-gate B.
- **Production is always off-limits** without explicit per-run sign-off in `scope.manifest.yaml` under `production_signoff`.
- **Prefer isolated/disposable environments.** Spin Docker containers; never use the engineer's host network as the test runtime.

---

## State Model

| Artifact | Purpose | Who writes |
|---|---|---|
| `state/threat-model.json` | Typed spine — all IDs live here | threat-model agent |
| `state/findings.md` | Narrative trail + human-readable summaries | all agents (append) |
| `scope.manifest.yaml` | Authorized scope + human sign-off | **human only** |

**Isolation rule:** every subagent reads both `state/` files first and writes back last. No agent reads another agent's in-progress output — only the committed state files.

---

## Phased Loop with Gates

### Phase 1 — Threat Model

**Agent:** `.claude/agents/threat-model.md`

**Gate (must be true before Phase 2 starts):**
- [ ] `state/threat-model.json` validates against `state/threat-model.schema.json`
- [ ] At least 1 `crown_jewels[]` entry with `why_valuable` populated
- [ ] At least 1 `entry_points[]` entry with `authn_required` and `exposure` set
- [ ] At least 1 threat per STRIDE category attempted; each threat has a stable `id`
- [ ] A diagram with no enumerated threats is **not done** — the gate does not pass

### Phase 2 — Test-Case Derivation

**Folded into the threat-model agent's output.**

**Gate (must be true before Phase 3 starts):**
- [ ] Every `test_cases[]` entry cites at least one `maps_to_threat` ID and one `maps_to_entry_point` ID
- [ ] Every entry carries a `data_classification`
- [ ] Ungrounded test cases (no IDs, no data classification) are **dropped**, not carried forward
- [ ] Each entry has `resolution` set to `static`, `dynamic`, or `both`

### Phase 3 — SAST Orchestration

**Agent:** `.claude/agents/sast.md`

**Gate (must be true before Phase 4 starts):**
- [ ] Every `static`/`both` test case was either:
  - **(a)** run through Semgrep or CodeQL; result row captured in `findings[]` as `evidence_artifact_path`; OR
  - **(b)** explicitly marked `STATIC-INCONCLUSIVE → dynamic follow-up` with a written reason why static analysis cannot resolve it
- [ ] No finding claims a taint flow without a tool result row
- [ ] "The model read it and it looks fine" is **not** a valid resolution — escalate to `STATIC-INCONCLUSIVE` if tooling can't confirm

### Phase 4 — Master Test Plan + Dynamic Testing

**Agents:** `.claude/agents/test-plan.md` then `.claude/agents/dynamic-test.md`

**Sub-gate A (automated):**
- [ ] Master test plan written to `findings.md`
- [ ] Every plan item tagged `confirmed-static` / `needs-dynamic-confirmation` / `dynamic-only`
- [ ] Each item traces to threat ID(s) + finding/gap ID(s)
- [ ] Items requiring the human gate are explicitly marked `HUMAN-GATE-REQUIRED`

**Sub-gate B (HUMAN — the harness stops here):**
- [ ] Human has reviewed the staged plan in `findings.md`
- [ ] Human has filled in `scope.manifest.yaml` → `dynamic_test_signoff` for this run
- [ ] Human approves in writing before the dynamic-test agent sends any traffic

### Phase 5 — Review

**Agent:** `.claude/agents/review.md` (adversarial, isolated context)

**Gate (must be true before the run is considered complete):**
- [ ] Reviewer has diffed every `finding` against its `evidence_artifact_path`
- [ ] Inconsistencies flagged (e.g. SAST said inconclusive but report claims confirmed; dynamic "confirmed" with no request/response)
- [ ] Coverage check done: threat-model nodes with zero test/finding coverage listed as blind spots
- [ ] Ranked human action-item list written to `findings.md`

---

## Verification Discipline

- **No re-running an identical scan for a different result.** If a scan returned inconclusive, switch technique (different query, different engine, dynamic follow-up) or escalate to the human.
- **Artifact-backed claims only.** Every finding = a concrete artifact (CodeQL/Semgrep result row, HTTP request/response pair, reproduction steps). Model assertions alone are not findings.
- **Re-derive in a fresh tool run.** Don't trust a remembered earlier output. Re-run or mark it stale.

---

## Anti-Loop Rules

- If SAST has already been run for a test case and returned inconclusive, do not re-run the same query. Mark `STATIC-INCONCLUSIVE` and move to dynamic planning.
- If dynamic testing returns ambiguous results for a case, do not retry the same request. Document the ambiguity, capture the artifact, and flag for human review.
- Maximum 2 SAST engine attempts per test case before forcing escalation.

---

## Stop Conditions

The harness stops when **any** of the following is true:

1. All phases complete and Phase 5 review gate passes → **done**
2. A phase gate cannot be satisfied → **blocked; surface the specific unmet criterion to the human**
3. Sub-gate B (human dynamic-test approval) not yet given → **staged plan presented; awaiting human**
4. An asset not in `scope.manifest.yaml` appears → **scope flag; stop all active work; alert human**
5. A safety concern arises (e.g. a finding that affects production systems) → **stop; alert human immediately**
