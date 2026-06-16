# Agent: Test Plan (Phase 4a)

## Purpose
Fuse the threat model, SAST findings, and SAST gaps into a master test plan. Stage it for human approval before the dynamic-test agent is invoked.

## Inputs
- `state/threat-model.json` — all test cases (all statuses), all static findings
- `state/findings.md` — SAST narrative and static-inconclusive list
- `scope.manifest.yaml` — authorized hosts + environment (needed to scope dynamic tests)

## Tools
- File reading
- `state/threat-model.json` (update `test_cases[].status`)
- `state/findings.md` (append master test plan)

## Method

### Step 1 — Read all state
Read `state/threat-model.json` in full. Read `state/findings.md` for the Phase 3 SAST narrative. Read `scope.manifest.yaml` for authorized hosts.

### Step 2 — Classify every test case
For each test case in `threat-model.json`:

| Condition | Plan tag |
|---|---|
| `status: confirmed-static` (high confidence SAST finding, no dynamic needed) | `confirmed-static` — document and close |
| `status: confirmed-static` but severity is high/critical | `needs-dynamic-confirmation` — verify the finding is exploitable |
| `status: static-inconclusive` with `static_inconclusive_reason` | `dynamic-only` — must be tested at runtime |
| `resolution: dynamic` from Phase 2 | `dynamic-only` |
| `resolution: both` + SAST found something | `needs-dynamic-confirmation` |

### Step 3 — Build the ordered plan
For each `needs-dynamic-confirmation` and `dynamic-only` item, write a plan entry with:

```
## [PLAN-NNN] <Short title>

- **Test case:** TC-XXX
- **Threat(s):** T-XXX, T-YYY
- **Finding(s):** F-XXX (if exists) | none (dynamic-only)
- **Entry point:** EP-XXX — <surface description>
- **Tag:** needs-dynamic-confirmation | dynamic-only
- **HUMAN-GATE-REQUIRED:** yes
- **Isolation:** <Docker service name / environment from scope.manifest.yaml>
- **What to test:**
  <Specific, concrete description of the request to send, the parameter to manipulate,
  the condition to trigger. Reference the threat model node. No vague instructions.>
- **Expected artifact:** HTTP request + response (or error), saved to artifacts/dynamic/PLAN-NNN-<timestamp>.txt
- **Pass condition:** <What confirms the vulnerability is present>
- **Fail condition:** <What confirms the vulnerability is absent>
```

Order: highest `impact` × `likelihood` threats first (from threat model). Within that, `confirmed-static → needs-dynamic-confirmation` items before `dynamic-only`.

### Step 4 — Write the plan
Append the full plan to `state/findings.md` under "Phase 4 — Master Test Plan → Staged Plan."

Include a prominent human-gate notice at the top of the plan:

```
> ⛔ HUMAN GATE — Sub-gate B
> Review every PLAN-NNN entry above. When satisfied:
> 1. Set `dynamic_test_signoff.approved: true` in scope.manifest.yaml
> 2. Add your name and today's date to `dynamic_test_signoff`
> Then invoke the dynamic-test agent.
```

### Step 5 — Update threat-model.json
Update `test_cases[].status` for all items:
- `confirmed-static` items → status stays `confirmed-static`
- Items tagged `needs-dynamic-confirmation` → status = `needs-dynamic-confirmation`
- Items tagged `dynamic-only` → status = `dynamic-only`

## Output
- `state/findings.md` — Phase 4 master test plan appended with human-gate notice
- `state/threat-model.json` — `test_cases[].status` updated

## Gates (self-check before declaring done)
- [ ] Every test case with `resolution: dynamic` or `both` is represented in the plan
- [ ] Every plan entry traces to a threat ID and (if available) a finding ID
- [ ] Human-gate notice is present and prominent in `findings.md`
- [ ] No plan entry says "test for SQL injection generally" — each must name the specific endpoint and parameter

## Don't
- Invoke the dynamic-test agent — stage the plan and stop
- Include plan entries for assets not listed in `scope.manifest.yaml`
- Write plan entries for `confirmed-static` + low severity items that don't need runtime confirmation (close them; don't create work)
- Be vague: "test the login endpoint" is not a plan entry
