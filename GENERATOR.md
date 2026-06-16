# Generator Prompt — "AppSec Solver Harness"

> Hand this entire file to Claude (ideally **Claude Code**, so it can write files and
> invoke tooling). It will scaffold a Brain/Executor multi-agent harness for
> **authorized internal application security work**: diagram → STRIDE threat model →
> SAST orchestration → master test plan → human-gated dynamic testing → report review.
> It ends by emitting a `SETUP.md` listing exactly what you (the human) must provide.
>
> This is the AppSec analog of an HTB solver harness, but for source-available,
> authorized targets — not black-box attack of systems you don't own.

---

## ROLE

You are scaffolding a multi-agent application-security harness for an **internal
application security engineer** working on code and applications **they are authorized
to test** (their employer's source, or intentionally-vulnerable practice apps). You are
generating the harness *files and methodology*, not performing the security work itself
in this turn.

Mirror the proven Brain/Executor pattern: a disciplined **orchestrator** that owns state
and enforces phase gates, plus **isolated subagents** that each read shared state first
and write results back last. Optimize for *trustworthy, auditable output over
impressive-looking output* — in AppSec, a false positive costs engineer trust and a
hallucinated dataflow is worse than no finding.

---

## NON-NEGOTIABLE DESIGN PRINCIPLES (encode these into every file you generate)

1. **The LLM orchestrates program-analysis tools; it does NOT replace them.**
   Source-to-sink / sink-to-source taint tracking is a *program analysis* problem.
   The agent's job is to (a) decide which engine to invoke, (b) ground the queries in
   the threat model, and (c) triage and explain results — **never** to hand-trace
   dataflow across a real codebase from memory. CodeQL/Semgrep produce the soundness;
   the LLM produces the interpretation. Any file that implies the model "reads the code
   and finds the taint flow itself" is wrong — fix it.

2. **The threat model is the connective spine.** It is a first-class *structured*
   artifact (typed JSON/YAML, not prose). Every entry point, crown jewel, test case,
   SAST query, dynamic test, and final finding must **trace back to a node in the threat
   model by ID**. This traceability is simultaneously the noise-reduction mechanism and
   the system's actual differentiator. If a finding can't point to a threat-model node,
   it's either untraced (fix the trace) or out of scope (drop it).

3. **Verification discipline — artifact-backed claims only.** Borrow the rule from the
   HTB harness: *if you can't verify it, you don't have it.* Every claimed
   vulnerability ties to a concrete artifact — a CodeQL/Semgrep result row, an HTTP
   request/response pair, a reproduction step — not a model assertion. Re-derive proof
   in a fresh tool run; don't trust a remembered earlier output.

4. **Noise economics / grounding.** Over-generation is the default failure. Every
   suggested OWASP test case must cite the specific component + trust boundary + data
   classification that motivates it. Rank ruthlessly. A short grounded list beats a long
   plausible one.

5. **Authorization and scope are stricter than a CTF box.** A dynamic-test agent
   pointed at a real application is a categorically different risk surface than an HTB
   box. Hard-code: (a) an explicit authorized-scope manifest (hosts, repos,
   environments), (b) **active/dynamic testing is human-gated** — the agent stages a
   plan and stops, a human approves before any traffic is sent, (c) never test
   production without explicit per-run sign-off, (d) prefer isolated/disposable
   environments. Surface any target not in the manifest and stop.

6. **The reviewer is adversarial and isolated.** The review/critic agent runs in a
   separate context that did **not** produce the findings, so it challenges them rather
   than rationalizing them.

---

## PRE-REQUISITES YOU MUST IDENTIFY (and write into SETUP.md)

Before the harness can run, the human needs these. In `SETUP.md`, list each with a
checkbox, what it's for, and how to obtain/configure it. Detect what's already present
on the system where possible (e.g. `which semgrep codeql docker`) and mark accordingly.

- **Static analysis engines**
  - **Semgrep** (the pragmatic workhorse; taint mode for source→sink; note that
    interprocedural/cross-file taint is stronger in Semgrep Pro). Integrate this first —
    lowest setup cost.
  - **CodeQL CLI + query packs** (the real interprocedural taint engine; the primary
    source-to-sink / sink-to-source tool). Requires building/obtaining a database per
    repo+language.
  - Note language-specific SAST where it's stronger, as optional plug-ins.
- **Source access** — the repo(s) to analyze, languages identified, build instructions
  (CodeQL needs to build compiled languages).
- **A practice target with BOTH source and a runnable instance** (so the static→dynamic
  chain can be validated end to end). Recommend a tiered set — see VALIDATION below.
- **Isolated runtime for dynamic testing** — Docker/compose for disposable, networked
  instances of the practice apps. Never the engineer's host network.
- **Authorization scope manifest** — the file the human fills in to declare what's
  in-scope (repos, hosts, environments) and to sign off on active testing.
- **Architecture input** — an architecture diagram or data-flow diagram (image or
  description) for the threat-model phase, OR a note that the threat-model agent should
  derive a provisional DFD from the source if none is provided.
- **Claude Code with subagents enabled** — confirm `.claude/agents/` discovery.
- **Dynamic toolkit (optional, for phase 4)** — an HTTP proxy/scanner the dynamic agent
  may drive (e.g. an intercepting proxy, a request library), scoped to the manifest.

---

## FILES TO GENERATE

Create this layout. Each file's content spec follows.

```
appsec-harness/
├── APPSEC.md                       # orchestrator: scope, phases, gates, verification
├── SETUP.md                        # prerequisites + human action items (emit LAST)
├── scope.manifest.yaml             # human-filled authorized scope + sign-off
├── state/
│   ├── threat-model.schema.json    # typed schema for the spine
│   ├── threat-model.json           # instance (starts empty/example)
│   └── findings.md                 # shared narrative state / loot trail
├── .claude/agents/
│   ├── threat-model.md             # diagram → STRIDE, crown jewels, entry points, test cases
│   ├── sast.md                     # orchestrate CodeQL/Semgrep, triage, flag dynamic gaps
│   ├── test-plan.md                # fuse threat model + SAST → master test plan
│   ├── dynamic-test.md             # human-gated active testing of flagged cases
│   └── review.md                   # adversarial review + inconsistency detection + follow-ups
└── validation/
    ├── README.md                   # how to spin up practice targets + run the full chain
    └── known-vulns.md              # ground-truth list per app, to score precision/recall
```

### `APPSEC.md` (orchestrator) — must contain

- **Scope (hard rules):** only assets in `scope.manifest.yaml`. Any other host/repo/URL
  that appears in tool output → surface and stop. No destructive actions. Active
  dynamic testing requires the human gate (Phase 4).
- **State model:** `state/threat-model.json` is the typed spine; `state/findings.md` is
  the narrative trail. Subagents are isolated — they read both first, write back last.
- **The phased loop with gates** (define each gate as a concrete, checkable condition):
  - **Phase 1 — Threat model.** Gate: `threat-model.json` validates against the schema
    and contains ≥1 crown jewel, ≥1 entry point, and STRIDE-categorized threats each
    with an ID. A diagram with no enumerated threats is not done.
  - **Phase 2 — Test-case derivation.** (Folded into the threat-model agent's output.)
    Gate: each candidate OWASP test case cites a threat-model node ID + data
    classification. Ungrounded cases are dropped, not carried.
  - **Phase 3 — SAST orchestration.** Gate: every reachable source→sink hypothesis from
    the test cases was either (a) confirmed/refuted by a CodeQL/Semgrep run with the
    result row captured, or (b) explicitly marked **STATIC-INCONCLUSIVE → dynamic
    follow-up** with the reason it can't be resolved statically (e.g. authz logic,
    business-logic, runtime-only state). No "the model read it and it looks fine."
  - **Phase 4 — Master test plan + dynamic testing.** Sub-gate A: the plan is staged and
    every dynamic test traces to a threat-model node + a SAST gap/finding. **Sub-gate B
    (HUMAN):** a person approves the scope and the plan before any active traffic.
    Dynamic results are artifact-backed (request/response).
  - **Phase 5 — Review.** Gate: the reviewer (separate context) has diffed claims
    against artifacts, flagged inconsistencies/unsupported claims, and produced a ranked
    human-action list.
- **Verification discipline** and **anti-loop rules** (don't re-run an identical scan
  for a different result; switch technique or escalate to dynamic).
- **Stop conditions:** plan complete + reviewed, OR blocked awaiting human gate, OR a
  scope/safety flag fires.

### `state/threat-model.schema.json` — the spine

Define a typed schema with stable IDs so everything downstream can reference it.
Minimum node types and fields:

- `components[]` — `{id, name, type (process|datastore|external_entity|...), tech}`
- `trust_boundaries[]` — `{id, name, between:[componentIds]}`
- `data_flows[]` — `{id, from, to, data:[classification], protocol, crosses_boundary:boolean}`
- `crown_jewels[]` — `{id, asset, why_valuable, components:[ids], data_classification}`
- `entry_points[]` — `{id, surface, component, authn_required, exposure (internet|internal|...)}`
- `threats[]` — `{id, stride:(S|T|R|I|D|E), description, target:(componentId|flowId|entryPointId), affected_crown_jewels:[ids], likelihood, impact}`
- `test_cases[]` — `{id, owasp:(A01..A10 / specific), maps_to_threat:[ids], maps_to_entry_point:[ids], data_classification, resolution:(static|dynamic|both), status}`
- `findings[]` — `{id, from_test_case, type:(static|dynamic), severity, evidence_artifact_path, traced_threat:[ids], status:(suspected|confirmed|refuted|inconclusive)}`

Every `test_case`, `finding`, SAST query, and dynamic test **must** carry the IDs it
traces to. The schema is what makes the reviewer able to diff mechanically.

### `.claude/agents/threat-model.md`

- **Inputs:** architecture/DFD diagram (vision) or source-derived provisional DFD; the
  scope manifest.
- **Method:** parse the diagram into `components / trust_boundaries / data_flows`;
  identify **crown jewels** (what's worth stealing/breaking and why) and **entry
  points** (every untrusted-input surface, with authn + exposure); enumerate **STRIDE**
  threats per component/flow/boundary; derive **grounded OWASP Top Ten test cases**,
  each tagged `static` / `dynamic` / `both` and mapped to threat + entry-point IDs.
- **Output:** populate `threat-model.json` (schema-valid) + a narrative summary in
  `findings.md`.
- **Don't:** emit ungrounded test cases; over-generate; skip crown-jewel reasoning.

### `.claude/agents/sast.md`  ← the crux; get this one right

- **Inputs:** the `static`/`both` test cases from the threat model; the repo(s).
- **Method (orchestrate, don't impersonate the engine):**
  1. For each test case, pick the right engine and write/select the right query —
     e.g. "test case TC-07 = SQLi at entry point EP-03 reaching datastore C-09 →
     CodeQL taint query with that source and sink" or a Semgrep taint rule for the OWASP
     pattern. **Start with Semgrep for breadth/speed; escalate to CodeQL for real
     interprocedural source→sink and sink→source.**
  2. Build the CodeQL DB (per language; build compiled langs) / run Semgrep.
  3. **Triage:** for each result row, explain it in plain language, rank by
     exploitability *in the context of the threat model*, and kill false positives with
     auditable reasoning. Capture the raw result row as the evidence artifact.
  4. **Gap-flagging:** anything static can't resolve — broken access control / IDOR,
     business-logic abuse, authz decisions, anything needing runtime state — mark
     `STATIC-INCONCLUSIVE → dynamic follow-up` with the reason. This handoff is a primary
     output, not an afterthought.
- **Output:** `findings[]` (static, artifact-backed) + dynamic-gap list in the threat
  model + `findings.md`.
- **Don't:** hand-trace taint from memory; claim a flow without a tool result row;
  feed an entire repo into context and "eyeball" it.

### `.claude/agents/test-plan.md`

- Fuse `threat-model.json` (test cases) + SAST findings + SAST gaps into a **master
  test plan**: ordered, each item tagged `confirmed-static` (document) /
  `needs-dynamic-confirmation` / `dynamic-only`. Each item traces to threat + finding
  IDs. Mark which items require the human gate.
- Output the plan to `findings.md` and as structured `test_cases[].status` updates.

### `.claude/agents/dynamic-test.md`

- **Hard gate first:** verify the target is in `scope.manifest.yaml` and that the human
  sign-off field for *this run* is present. If not → stage the plan, print exactly what
  it would do, and **stop**.
- **Method:** drive the scoped HTTP toolkit against the flagged cases only, in the
  isolated environment. Confirm/refute each; capture request/response as the evidence
  artifact. Update `findings[]` to `confirmed`/`refuted`.
- **Don't:** touch anything off-manifest; test prod without per-run sign-off; claim a
  result without the request/response pair; chase vectors not in the plan (return to
  orchestrator instead).

### `.claude/agents/review.md` (adversarial, isolated)

- **Method:** independently diff every `finding` against its `evidence_artifact`; flag
  unsupported claims, severity inflation, untraced findings, and **inconsistencies**
  (e.g. SAST said inconclusive but the report claims confirmed; a dynamic "confirmed"
  with no request/response). Check coverage: which threat-model nodes have *no*
  corresponding test/finding (blind spots).
- **Output:** a ranked **human action-item list** — what to re-run, what to manually
  verify, what to accept/reject — written to `findings.md`.
- **Don't:** trust the producing agents' conclusions; soften findings to agree.

### `validation/` — prove the harness works on known-vulnerable apps

The harness must be testable end-to-end on apps that have **both source and a runnable
instance**, with **documented known vulns** as ground truth, so you can score the
pipeline (did the threat model predict it? did SAST catch it? did dynamic confirm it?).
Generate `validation/README.md` with a tiered recommendation and run instructions:

- **DVWA** (PHP) — classic, simple, good first smoke test.
- **OWASP Juice Shop** (Node/Angular) — modern, maps cleanly to the OWASP Top Ten;
  strong for the full chain.
- **OWASP WebGoat** (Java) — excellent CodeQL-Java target for source→sink validation.
- (Optional) **NodeGoat**, **Damn Vulnerable** variants for specific stacks.

For the chosen app(s): provide Docker run instructions (isolated network), point the
repo at the app's source, and run all five phases. Then compare against
`validation/known-vulns.md` (a curated ground-truth list per app) to compute rough
precision/recall and tune the grounding/triage until noise is acceptable.

---

## OUTPUT FORMAT FOR THIS RUN

1. Briefly confirm assumptions (languages, whether a diagram will be provided, which
   practice app to validate against) — state sensible defaults rather than blocking.
2. Generate every file above with complete, usable content (not placeholders), keeping
   each subagent in the tight `purpose / inputs / tools / method / output / gates /
   don't` shape.
3. **End with `SETUP.md`**: a single checklist of everything the human must do or
   provide before a real run — tools to install, the scope manifest to fill in and sign,
   source/diagram to supply, the practice app to bring up, and the explicit point where
   active testing will pause for human approval. Make it copy-pasteable and ordered.

Do not perform any scanning, exploitation, or dynamic testing in this scaffolding run —
only generate the harness and the setup checklist.
