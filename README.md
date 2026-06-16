# AppSec Solver Harness

A **Claude Code, multi-agent harness for authorized application-security testing**. It
runs a disciplined, phased loop — architecture diagram → STRIDE threat model → SAST
orchestration → master test plan → human-gated dynamic testing → adversarial review —
and produces **auditable, artifact-backed findings** rather than plausible-looking prose.

It is the AppSec analog of an HTB solver harness, but pointed at *source-available,
authorized* targets: your employer's code, or intentionally-vulnerable practice apps —
never black-box attack of systems you don't own.

> **Authorized use only.** Every host and repo must be declared in `scope.manifest.yaml`.
> Dynamic (active) testing is hard-gated behind explicit human sign-off, and production
> is off-limits without a separate per-run approval. See [Safety model](#safety--authorization-model).

---

## Why it's built this way

The harness orchestrates real tooling instead of asking a model to "look for bugs":

- **The LLM orchestrates tools, it doesn't replace them.** Semgrep and CodeQL do the
  taint analysis; the agent interprets, triages, and traces results — it never claims a
  data flow without a tool result row behind it.
- **The threat model is the spine.** Every finding traces back to a node ID in
  `state/threat-model.json`. No orphan findings.
- **Artifact-backed claims only.** A finding must cite concrete evidence — a Semgrep/CodeQL
  result row, or an HTTP request/response pair. "The model read it and it looks fine" is
  explicitly *not* a valid resolution; it escalates to `STATIC-INCONCLUSIVE`.
- **Grounded test cases.** Every test case cites a threat ID + entry-point ID + data
  classification. Ungrounded hypotheticals are dropped, not carried forward.
- **Human gates on anything active.** The harness stages a dynamic-test plan and *stops*.
  No traffic is sent until a human reviews the plan and signs off in `scope.manifest.yaml`.
- **Adversarial review.** A final agent re-checks every finding against its evidence in a
  fresh context, and lists threat-model nodes with zero coverage as blind spots.

## The phased loop

State lives in three files; subagents read shared state first and write back last, so no
agent ever consumes another's in-progress output.

| Artifact | Purpose | Writer |
|---|---|---|
| `state/threat-model.json` | Typed spine — all IDs live here (validated against `state/threat-model.schema.json`) | threat-model agent |
| `state/findings.md` | Narrative trail + human-readable summaries | all agents (append) |
| `scope.manifest.yaml` | Authorized scope + human sign-off | **human only** |

| Phase | Agent (`.claude/agents/`) | Output & gate |
|---|---|---|
| **1 — Threat Model** | `threat-model.md` | DFD + STRIDE threats; gate requires crown jewels, entry points, ≥1 threat per STRIDE category, schema-valid |
| **2 — Test-Case Derivation** | (folded into threat-model) | Every test case cites a threat ID + entry-point ID + data classification; ungrounded cases dropped |
| **3 — SAST Orchestration** | `sast.md` | Every static test case run through Semgrep/CodeQL with a captured result row, or marked `STATIC-INCONCLUSIVE` with a reason |
| **4a — Master Test Plan** | `test-plan.md` | Plan items tagged `confirmed-static` / `needs-dynamic-confirmation` / `dynamic-only`, each tracing to threat + finding IDs |
| **4b — Dynamic Testing** | `dynamic-test.md` | **HUMAN GATE** — refuses to send traffic until `scope.manifest.yaml` sign-off is present |
| **5 — Review** | `review.md` | Adversarial diff of each finding vs. its evidence; coverage blind-spots listed; ranked action items |

The full orchestration contract (hard rules, gate criteria, anti-loop and stop conditions)
is in [`APPSEC.md`](APPSEC.md). The original prompt that scaffolds this entire harness from
scratch is in [`GENERATOR.md`](GENERATOR.md).

## Safety & authorization model

- **In-scope assets only.** Any host/repo/URL that surfaces in tool output but is *not* in
  `scope.manifest.yaml` halts the run and is surfaced to the human.
- **Dynamic testing is human-gated.** The `dynamic-test` agent reads
  `scope.manifest.yaml → dynamic_test_signoff` and refuses to run without explicit approval.
- **Production is off-limits** without a separate `production_signoff` block per run.
- **Isolated runtimes only.** Targets run in disposable Docker containers on an isolated
  network — never on the engineer's host network.

## Worked example — OWASP Juice Shop

The repo ships a real validation run against [OWASP Juice Shop](https://github.com/juice-shop/juice-shop)
(an intentionally-vulnerable app), so you can see the harness's output, not just its design:

- `state/threat-model.json` — the populated STRIDE threat model (DFD, crown jewels, entry
  points, grounded test cases)
- `state/findings.md` — the narrative trail across phases
- `artifacts/sast/*.json` — raw Semgrep result sets (machine-relative paths)
- `validation/known-vulns.md` — ground-truth vuln list used to score precision/recall

> The 80 MB Juice Shop source clone itself is **not** vendored — it's git-ignored. Clone it
> locally to reproduce (see below).

## Running it

Full prerequisites (Semgrep, CodeQL, Docker, Claude Code) are in [`SETUP.md`](SETUP.md);
the tiered validation targets (DVWA / Juice Shop / WebGoat) and full-chain walkthrough are
in [`validation/README.md`](validation/README.md). Quick start for the Juice Shop run:

```bash
# 1. Tools
pip install semgrep            # CodeQL CLI: github.com/github/codeql-action/releases

# 2. Clone the target source (git-ignored; not vendored here)
git clone https://github.com/juice-shop/juice-shop.git validation/targets/juiceshop-src

# 3. Isolated runtime
docker network create appsec-isolated
docker run -d --name juiceshop --network appsec-isolated \
  -p 127.0.0.1:3000:3000 bkimminich/juice-shop

# 4. Fill in scope.manifest.yaml (repos + hosts), then drive the phases in Claude Code:
#    "Run the threat-model agent on validation/targets/juiceshop-src"   (Phase 1)
#    "Run the SAST agent on validation/targets/juiceshop-src"           (Phase 3)
#    "Run the test-plan agent and stage the dynamic plan"               (Phase 4a)
#    -- review the staged plan, set dynamic_test_signoff.approved: true --
#    "Run the dynamic-test agent against http://localhost:3000"         (Phase 4b)
#    "Run the review agent against the current state"                   (Phase 5)
```

Then score the run against `validation/known-vulns.md` (precision / recall) and iterate on
rule selection and grounding.

## Repository layout

```
APPSEC.md            Orchestrator — phase gates, state model, stop conditions
GENERATOR.md         The prompt that scaffolds this entire harness
SETUP.md             Prerequisites checklist
scope.manifest.yaml  Authorization scope + human sign-off (human-edited only)
.claude/agents/      The 5 phase subagents
state/               threat-model.schema.json + the Juice Shop threat model & findings
artifacts/sast/      Semgrep result sets from the Juice Shop run
validation/          Tiered targets, full-chain walkthrough, ground-truth vuln list
```

## License

[MIT](LICENSE) — use it as you see fit.
