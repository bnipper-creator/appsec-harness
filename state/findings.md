# Findings Trail

This file is the shared narrative state for the AppSec harness. Agents append to it; they do not overwrite it. Each entry must reference a threat-model ID.

---

## Run Log

| Phase | Timestamp | Agent | Summary | Gate Status |
|---|---|---|---|---|
| — | — | — | Initial empty state | — |

---

## Phase 1 — Threat Model Summary

**Agent:** threat-model  
**Timestamp:** 2026-06-13T00:00:00Z  
**DFD source:** derived-from-source (server.ts, routes/, models/, lib/insecurity.ts, ftp/, encryptionkeys/)

### Application Overview

OWASP Juice Shop v20.0.0 — an intentionally-vulnerable Node.js/Angular e-commerce application. Single Express process serving both the REST API and static Angular SPA on port 3001 (local Docker). Uses SQLite via Sequelize ORM with an in-process MarsDB NoSQL store for product reviews. Auth is JWT-based (RS256) with the signing key hardcoded in source.

### Component Count: 10

| ID | Name | Type |
|---|---|---|
| C-1 | Angular Frontend SPA | process |
| C-2 | Express REST API Server | process |
| C-3 | SQLite Database | datastore |
| C-4 | MarsDB Product Reviews Store | datastore |
| C-5 | Local Filesystem (FTP, uploads, logs, keys) | datastore |
| C-6 | Web Browser (Unauthenticated User) | external_entity |
| C-7 | B2B Client | external_entity |
| C-8 | Prometheus Metrics Collector | service |
| C-9 | External AI Chat Service | external_entity |
| C-10 | Ethereum Blockchain | external_entity |

### Crown Jewels: 4

| ID | Asset | Classification | Why Valuable |
|---|---|---|---|
| CJ-1 | User Credentials and Account Data | confidential | MD5-hashed passwords trivially crackable; admin accounts control the entire app |
| CJ-2 | JWT RSA Private Signing Key | secret | Hardcoded in lib/insecurity.ts:23; possession mints valid admin JWTs without any credential |
| CJ-3 | Payment Card and Wallet Data | confidential | Enables financial fraud and unauthorized purchases |
| CJ-4 | FTP Sensitive Files and Encryption Keys | secret | incident-support.kdbx (credentials DB), acquisitions.md (M&A data), premium.key, coupon backups |

### Entry Points: 11

| ID | Surface | AuthN | Exposure |
|---|---|---|---|
| EP-1 | POST /rest/user/login | none | internet |
| EP-2 | GET /rest/products/search?q= | none | internet |
| EP-3 | POST /file-upload (multipart) | none | internet |
| EP-4 | POST /b2b/v2/orders | JWT Bearer | internet |
| EP-5 | GET /ftp/:file, /encryptionkeys/:file | none | internet |
| EP-6 | POST /rest/user/reset-password | none | internet |
| EP-7 | PUT /rest/products/:id/reviews | none | internet |
| EP-8 | GET /metrics | none | internet |
| EP-9 | POST /api/Users (registration) | none | internet |
| EP-10 | GET /redirect?to= | none | internet |
| EP-11 | GET /support/logs, /support/logs/:file | none | internet |

### Threats: 10 (by STRIDE category)

| STRIDE | Count | Threat IDs |
|---|---|---|
| S — Spoofing | 1 | T-1 |
| T — Tampering | 2 | T-2, T-3 |
| R — Repudiation | 1 | T-4 |
| I — Information Disclosure | 3 | T-5, T-6, T-7 |
| D — Denial of Service | 1 | T-8 |
| E — Elevation of Privilege | 2 | T-9, T-10 |

**Highest-severity threats:**

- **T-1 (S, critical impact):** JWT RSA private key hardcoded in source (lib/insecurity.ts:23) → token forgery for any identity including admin.
- **T-2 (T, critical/critical):** SQLi in login route (login.ts:34) via raw string interpolation → auth bypass.
- **T-9 (E, critical/critical):** Mass assignment on POST /api/Users — attacker self-registers with role=admin.
- **T-10 (E, medium/critical):** RCE via vm.runInContext(safeEval(orderLinesData)) in B2B order route (b2bOrder.ts:22) → OS code execution.
- **T-5 (I, high/high):** XXE in XML upload (libxmljs2 with noent:true at fileUpload.ts:83) → arbitrary local file read.
- **T-6 (I, critical/high):** Unauthenticated FTP and encryption key directory listing → KeePass DB, private keys, M&A docs freely downloadable.

### DFD Gaps
- WebSocket event handler logic (`registerWebsocketEvents`) not fully enumerated.
- Angular frontend routing and client-side security controls not analyzed (out of SAST scope).
- AI chat endpoint data handling and prompt injection surface not deeply analyzed.

---

## Phase 2 — Test Cases

_Populated by the threat-model agent (folded into Phase 1 output)._

### Test Case Summary: 10 total

| Resolution Type | Count | IDs |
|---|---|---|
| static | 1 | TC-3 |
| dynamic | 4 | TC-5, TC-8, TC-9, TC-10 |
| both | 5 | TC-1, TC-2, TC-4, TC-6, TC-7 |

| ID | OWASP Category | Threat(s) | Entry Point(s) | Data Class | Resolution |
|---|---|---|---|---|---|
| TC-1 | A03:2021 Injection — SQLi Auth Bypass | T-2 | EP-1 | confidential | both |
| TC-2 | A03:2021 Injection — SQLi UNION Exfiltration | T-3 | EP-2 | confidential | both |
| TC-3 | A02:2021 Cryptographic Failures — Hardcoded JWT Key | T-1 | EP-1 | secret | static |
| TC-4 | A05:2021 Security Misconfiguration — XXE | T-5 | EP-3 | confidential | both |
| TC-5 | A01:2021 Broken Access Control — Sensitive File Download | T-6 | EP-5 | secret | dynamic |
| TC-6 | A04:2021 Insecure Design — Mass Assignment | T-9 | EP-9 | confidential | both |
| TC-7 | A03:2021 Injection — RCE via VM Sandbox Escape | T-10 | EP-4 | internal | both |
| TC-8 | A05:2021 Security Misconfiguration — YAML Bomb DoS | T-8 | EP-3 | public | dynamic |
| TC-9 | A01:2021 Broken Access Control — Log File Download | T-4 | EP-11 | internal | dynamic |
| TC-10 | A01:2021 Broken Access Control — Metrics Exposure | T-7 | EP-8 | internal | dynamic |

**Gate status (Phase 1 → Phase 2):**
- [x] `state/threat-model.json` schema-valid (all required arrays populated, all ID patterns satisfied)
- [x] ≥1 crown jewel with `why_valuable` populated (4 crown jewels)
- [x] ≥1 entry point with `authn_required` and `exposure` set (11 entry points)
- [x] At least one threat per STRIDE category (S:1, T:2, R:1, I:3, D:1, E:2)
- [x] Every test case has `maps_to_threat`, `maps_to_entry_point`, and `data_classification`
- [x] No ungrounded test cases — all cite specific source file + line references

---

## Phase 3 — SAST Results

**Agent:** sast  
**Timestamp:** 2026-06-13T21:00:00Z  
**Engine:** Semgrep 1.166.0  
**Rules run:** 114 (p/owasp-top-ten) + 74 (p/javascript) = 188 total  
**Targets scanned:** 1114 files (JS/TS; git-tracked)  
**Raw artifacts:** `artifacts/sast/semgrep-owasp-top-ten-20260613T204704.json`, `artifacts/sast/semgrep-javascript-20260613T204743.json`

### Static Findings: 7

| ID | Severity | Title | File:Line | TC | Threat |
|---|---|---|---|---|---|
| F-1 | critical | SQLi Auth Bypass | routes/login.ts:34 | TC-1 | T-2 |
| F-2 | critical | SQLi UNION Exfiltration | routes/search.ts:23 | TC-2 | T-3 |
| F-3 | critical | Hardcoded JWT RSA Key | lib/insecurity.ts:56 | TC-3 | T-1 |
| F-4 | high | Unauthenticated Directory Listing | server.ts:269-281 | TC-5 | T-6 |
| F-5 | medium | Path Traversal in File Serving | routes/fileServer.ts:33 | TC-5 | T-6 |
| F-6 | critical | Eval Injection — User Profile Route | routes/userProfile.ts:61 | TC-11 | T-12 |
| F-7 | medium | Open Redirect — Bypassable Allowlist | routes/redirect.ts:19 | TC-12 | T-11 |

**Severity distribution:** critical: 3, high: 1, medium: 2

#### F-1 — SQL Injection (Auth Bypass), routes/login.ts:34

Rule `express-sequelize-injection` (CWE-89, A03:2021) confirmed that `req.body.email` is directly interpolated into a raw Sequelize query string at line 34. The string `' OR '1'='1'--` submitted as the email field bypasses the WHERE clause and returns the first database row (typically the admin account). Corroborated by both rulesets (result[13] in OWASP file, result[8] in JS file). TC-1 status → `confirmed-static`.

#### F-2 — SQL Injection (UNION Exfiltration), routes/search.ts:23

Rule `express-sequelize-injection` (CWE-89, A03:2021) confirmed that the `q` URL parameter is truncated to 200 chars then interpolated into a raw SQL LIKE clause. UNION SELECT payloads fit within 200 chars and can exfiltrate the full Users table. Corroborated by both rulesets (result[16] / result[11]). TC-2 status → `confirmed-static`.

Secondary instances of the same SQLi pattern were found in `static/codefixes/dbSchemaChallenge_1.ts:5`, `dbSchemaChallenge_3.ts:11`, `unionSqlInjectionChallenge_1.ts:6`, `unionSqlInjectionChallenge_3.ts:10` — these are educational codefix files (challenge variants), not the primary HTTP handler attack surface. No separate finding entries created.

#### F-3 — Hardcoded JWT RSA Signing Key, lib/insecurity.ts:56

Rule `hardcoded-jwt-secret` (CWE-798, A07:2021) fired at the `jwt.sign(user, privateKey, ...)` call at line 56. The private key itself is a 1024-bit RSA PEM literal at line 23. Any reader of the source code can mint valid admin JWTs without credentials. TC-3 resolution is `static` and the finding is fully confirmed — **no dynamic verification needed**. TC-3 status → `confirmed`.

#### F-4 + F-5 — Directory Listing + Path Traversal in File Serving, server.ts:269-281

Rule `express-check-directory-listing` (CWE-548, A01:2021) fired at four registration points: lines 269, 273, 277, 281. No authentication middleware precedes any of these `serveIndex` registrations. Rule `express-res-sendfile` (CWE-73) additionally fired at the file-serving handlers (`fileServer.ts:33`, `keyServer.ts:14`, `logfileServer.ts:14`, `quarantineServer.ts:14`), indicating user-supplied filenames reach `res.sendFile()` without confirmed boundary enforcement.

Static analysis confirms the **configuration is vulnerable** (missing auth on directory listing, unsanitized path to `sendFile`). TC-5 status → `needs-dynamic-confirmation` (dynamic test needed to confirm actual secret file bytes are returned without auth challenge and that path traversal escapes the intended directory).

#### F-6 — Eval Injection (Bonus), routes/userProfile.ts:61

Rule `code-string-concat` (CWE-95, A03:2021) detected Express request data flowing to `eval()` at `routes/userProfile.ts:61`. This is a **bonus finding not in the original 10-TC scope**. It is a distinct `eval()` call from TC-7's `vm.runInContext` in `b2bOrder.ts`. New threat T-12 (Elevation of Privilege via eval injection) and test case TC-11 created to track. TC-11 status → `confirmed-static`; dynamic test required to determine the exact user-controlled field and confirm exploitability.

#### F-7 — Open Redirect (Bonus), routes/redirect.ts:19

Rule `express-open-redirect` (CWE-601, A01:2021) confirmed user query parameter flows to a redirect at `routes/redirect.ts:19`. The allowlist check in `insecurity.ts:137` uses `url.includes()` substring matching — bypassable by embedding an allowed domain as a query string value of a malicious URL. New threat T-11 (Spoofing via open redirect) and test case TC-12 created. TC-12 status → `confirmed-static`.

### Static-Inconclusive → Dynamic Follow-Up

| TC | Reason | Dynamic test needed |
|---|---|---|
| TC-4 (XXE) | No Semgrep rule covers libxmljs2 `noent:true`; `vm.runInContext` wrapper complicates taint tracking; zero results from 188 rules | Upload malicious XML; confirm entity expanded in 410 error body |
| TC-6 (Mass Assignment) | Finale auto-generated endpoints not detectable by pattern rules; mass assignment requires runtime attribute persistence check | POST `/api/Users` with `role:admin`; confirm JWT shows admin role |
| TC-7 (VM Sandbox Escape) | `vm.runInContext(safeEval(userInput))` pattern not in Semgrep standard JS sinks; eval at `userProfile.ts:61` is a different path (see TC-11) | POST crafted `orderLinesData` to `/b2b/v2/orders`; confirm constructor-chain escape |

### CI/CD Findings (Out of Scope for Running Application)

Semgrep found 5 instances of `run-shell-injection` (CWE-78) in `.github/workflows/` files inside the juiceshop-src repo (`update-challenges-ebook.yml:22`, `update-challenges-www-legacy.yml:27,36`, `update-challenges-www.yml:27,36`). These are GitHub Actions workflows for the upstream Juice Shop project CI/CD pipeline. They affect GitHub's infrastructure, **not the running application at localhost:3001**, and no entry point in the current threat model maps to GitHub Actions. These are documented here for awareness; they should be reported to the upstream project and are not part of the Phase 4 dynamic test plan.

### Updated Test Case Status after Phase 3

| ID | Prior Status | Post-Phase-3 Status | Reason |
|---|---|---|---|
| TC-1 | pending | confirmed-static | F-1: SQLi confirmed by Semgrep |
| TC-2 | pending | confirmed-static | F-2: SQLi confirmed by Semgrep |
| TC-3 | pending | confirmed | F-3: Hardcoded key — fully static; no dynamic needed |
| TC-4 | pending | static-inconclusive | 188 Semgrep rules, zero XXE results |
| TC-5 | pending | needs-dynamic-confirmation | F-4/F-5: directory listing confirmed; exploitation proof dynamic |
| TC-6 | pending | static-inconclusive | Finale mass assignment not pattern-detectable |
| TC-7 | pending | static-inconclusive | vm.runInContext not in Semgrep sinks |
| TC-8 | pending | pending | Dynamic-only; not in Phase 3 scope |
| TC-9 | pending | pending | Dynamic-only; not in Phase 3 scope |
| TC-10 | pending | pending | Dynamic-only; not in Phase 3 scope |
| TC-11 | — | confirmed-static | New TC; F-6 eval injection confirmed by Semgrep |
| TC-12 | — | confirmed-static | New TC; F-7 open redirect confirmed by Semgrep |

### Recommended CodeQL Follow-Ups (if escalation warranted)

Per agent rules: escalate to CodeQL for high/critical TCs where Semgrep was inconclusive.

| TC | Escalation Case | CodeQL Query |
|---|---|---|
| TC-4 (XXE) | High severity; Semgrep zero results; xmljs2 noent:true requires taint tracking | `javascript/ql/src/Security/CWE-611` — XXE in JS |
| TC-7 (VM Escape) | Critical severity; vm.runInContext source→sink requires interprocedural analysis | Custom QL: source=`req.body.*`, sink=`vm.runInContext(…)` |

CodeQL not executed this phase (no database built); escalation deferred to human discretion or Phase 4 pre-flight.

### Phase 3 Gate Status

- [x] Every `static`/`both` TC is either resolved (`confirmed-static`/`confirmed`) or explicitly `static-inconclusive` with a reason
- [x] Every `static-inconclusive` TC has `static_inconclusive_reason` populated in `threat-model.json`
- [x] No finding exists without an `evidence_artifact_path`
- [x] No claim "the code looks fine" without a tool result confirming it
- [x] Maximum 2 SAST engine attempts per test case before forcing `static-inconclusive` (1 attempt per TC; 2 rulesets run simultaneously)
- [x] Schema validation passed (ALL GATES PASSED)

---

## Phase 4 — Master Test Plan

_Populated by the test-plan agent._

> **⛔ HUMAN GATE — Sub-gate B**
>
> The dynamic-test agent will not send any traffic until you have:
> 1. Reviewed the staged plan below
> 2. Set `dynamic_test_signoff.approved: true` in `scope.manifest.yaml`
> 3. Added your name and the date to `dynamic_test_signoff`

### Staged Plan

**Phase 4a generated: 2026-06-13T00:00:00Z** | Engine: test-plan agent | TCs in: 12 | Closed: 1 | Plan entries: 11

> **⛔ HUMAN GATE — Sub-gate B**
>
> Review every PLAN-NNN entry below. When satisfied:
> 1. Confirm `dynamic_test_signoff.approved: true` in `scope.manifest.yaml` (already set)
> 2. Add your name to `dynamic_test_signoff.approved_by`
> 3. Add today's date (ISO-8601) to `dynamic_test_signoff.approved_date`
>
> Then invoke the dynamic-test agent.

#### Closed — No Dynamic Action Required

| TC | Status | Reason |
|---|---|---|
| TC-3 | `confirmed` | `resolution: static` — hardcoded JWT key fully evidenced by F-3 (Semgrep `hardcoded-jwt-secret` at `insecurity.ts:56`). Static analysis alone is sufficient. No runtime proof needed. |

#### Plan Entries (ordered by impact × likelihood, needs-dynamic-confirmation before dynamic-only within each tier)

---

## [PLAN-001] SQL Injection — Authentication Bypass Exploitability Proof

- **Test case:** TC-1
- **Threat(s):** T-2
- **Finding(s):** F-1 (`artifacts/sast/semgrep-owasp-top-ten-20260613T204704.json#result[13]`)
- **Entry point:** EP-1 — `POST /rest/user/login` (unauthenticated, internet-exposed)
- **Tag:** needs-dynamic-confirmation
- **HUMAN-GATE-REQUIRED:** yes
- **Isolation:** Docker container `juiceshop` on network `appsec-isolated`, host port 3001
- **What to test:**
  Send `POST http://localhost:3001/rest/user/login` with `Content-Type: application/json` and body `{"email":"' OR '1'='1'--","password":"anything"}`. F-1 confirms `req.body.email` is directly interpolated into the raw SQL at `login.ts:34`. This payload terminates the string literal and appends an always-true condition, causing the WHERE clause to match all rows and return the first user (typically admin). A 200 response containing a JWT in `authentication.token` confirms authentication bypass without credentials.
- **Expected artifact:** `artifacts/dynamic/PLAN-001-<timestamp>.txt` — full HTTP request + response
- **Pass condition:** HTTP 200 response body contains `authentication.token` (a non-empty JWT string). Decoding the JWT `data.email` should reveal the admin account (first row in Users table), not the submitted email value.
- **Fail condition:** HTTP 401 or HTTP 500 without a JWT in the response body.

---

## [PLAN-002] Mass Assignment — Self-Register as Admin

- **Test case:** TC-6
- **Threat(s):** T-9
- **Finding(s):** none (static-inconclusive — Finale framework convention, not a code pattern detectable by SAST)
- **Entry point:** EP-9 — `POST /api/Users` (unauthenticated, internet-exposed, Finale auto-generated CRUD)
- **Tag:** dynamic-only
- **HUMAN-GATE-REQUIRED:** yes
- **Isolation:** Docker container `juiceshop` on network `appsec-isolated`, host port 3001
- **What to test:**
  Step 1: `POST http://localhost:3001/api/Users` with `Content-Type: application/json` and body `{"email":"pentest-admin@juice.invalid","password":"P3nt3st!","passwordRepeat":"P3nt3st!","role":"admin"}`.
  Step 2: `POST http://localhost:3001/rest/user/login` with the same `email` and `password` to obtain a JWT.
  Step 3: Base64-decode the JWT middle segment (payload). Inspect the `data.role` claim value.
  Step 4 (confirming step): `GET http://localhost:3001/rest/admin/application-configuration` with `Authorization: Bearer <jwt>`. An admin-only endpoint returning HTTP 200 confirms elevated privilege was actually granted.
- **Expected artifact:** `artifacts/dynamic/PLAN-002-<timestamp>.txt` — registration response + login response + JWT payload (decoded) + admin endpoint request/response
- **Pass condition:** `data.role` in the JWT payload equals `"admin"` AND/OR `GET /rest/admin/application-configuration` returns HTTP 200.
- **Fail condition:** `data.role` equals `"customer"` despite `"role":"admin"` in the registration body; or step 1 returns HTTP 400 rejecting the `role` field entirely.

---

## [PLAN-003] SQL Injection — UNION-based User Data Exfiltration Exploitability Proof

- **Test case:** TC-2
- **Threat(s):** T-3
- **Finding(s):** F-2 (`artifacts/sast/semgrep-owasp-top-ten-20260613T204704.json#result[16]`)
- **Entry point:** EP-2 — `GET /rest/products/search?q=` (unauthenticated, internet-exposed)
- **Tag:** needs-dynamic-confirmation
- **HUMAN-GATE-REQUIRED:** yes
- **Isolation:** Docker container `juiceshop` on network `appsec-isolated`, host port 3001
- **What to test:**
  Send `GET http://localhost:3001/rest/products/search?q=%27%27)%20UNION%20SELECT%20id%2Cemail%2Cpassword%2Crole%2CNULL%2CNULL%2CNULL%2CNULL%2CNULL%20FROM%20Users--` (URL-encoded form of `')) UNION SELECT id,email,password,role,NULL,NULL,NULL,NULL,NULL FROM Users--`). F-2 confirms raw SQL interpolation at `search.ts:23` with a truncation limit of 200 characters. The Products table schema has 9 columns, so the UNION SELECT must match with 9 columns. Verify the payload length is under 200 characters before sending (the example above is ~72 characters).
- **Expected artifact:** `artifacts/dynamic/PLAN-003-<timestamp>.txt` — full HTTP request + response
- **Pass condition:** HTTP 200 response body `data` array contains rows with an `email` field containing `@` and a `password` field containing a 32-character hex string (MD5 hash from the Users table).
- **Fail condition:** HTTP 400/500 without user rows; or `data` array contains only product records with no email/password fields.

---

## [PLAN-004] Broken Access Control — Unauthenticated FTP and Encryption Key File Download

- **Test case:** TC-5
- **Threat(s):** T-6
- **Finding(s):** F-4, F-5 (`artifacts/sast/semgrep-owasp-top-ten-20260613T204704.json#result[18]`, `result[10]`)
- **Entry point:** EP-5 — `GET /ftp`, `/ftp/:file`, `/encryptionkeys/:file` (unauthenticated, internet-exposed)
- **Tag:** needs-dynamic-confirmation
- **HUMAN-GATE-REQUIRED:** yes
- **Isolation:** Docker container `juiceshop` on network `appsec-isolated`, host port 3001
- **What to test:**
  Step 1: `GET http://localhost:3001/ftp` — confirm HTML directory listing is returned without any `Authorization` header.
  Step 2: `GET http://localhost:3001/ftp/incident-support.kdbx` — download the KeePass database. Verify HTTP 200 and non-empty binary body.
  Step 3: `GET http://localhost:3001/encryptionkeys/premium.key` — download the encryption key. Verify HTTP 200 and key content in body.
  Step 4 (path traversal probe per F-5): `GET http://localhost:3001/ftp/..%2F..%2Fpackage.json` — test whether `res.sendFile` at `fileServer.ts:33` allows path traversal outside the `/ftp` root. Note result without pursuing further traversal.
- **Expected artifact:** `artifacts/dynamic/PLAN-004-<timestamp>.txt` — all four request/response pairs
- **Pass condition:** Steps 1–3 all return HTTP 200 without any authentication challenge; file bytes are present in each response body.
- **Fail condition:** HTTP 401/403 on any of steps 1–3; or step 1 returns a login redirect instead of a directory listing.

---

## [PLAN-005] XXE Injection — External Entity File Disclosure via File Upload

- **Test case:** TC-4
- **Threat(s):** T-5
- **Finding(s):** none (static-inconclusive — libxmljs2 `noent:true` not covered by Semgrep standard rulesets)
- **Entry point:** EP-3 — `POST /file-upload` (unauthenticated, internet-exposed, `multipart/form-data`)
- **Tag:** dynamic-only
- **HUMAN-GATE-REQUIRED:** yes
- **Isolation:** Docker container `juiceshop` on network `appsec-isolated`, host port 3001
- **What to test:**
  Send `POST http://localhost:3001/file-upload` as `multipart/form-data` with a single file field named `file`, filename `xxe-probe.xml`, MIME type `text/xml`, containing:
  ```
  <?xml version="1.0" encoding="UTF-8"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>
  ```
  The `noent: true` flag confirmed at `fileUpload.ts:83` enables external entity expansion. Per the threat model the 410 error response body includes `xmlString`, which should contain the resolved entity value. If `/etc/passwd` returns empty (non-Linux container), retry with `file:///etc/hostname`.
- **Expected artifact:** `artifacts/dynamic/PLAN-005-<timestamp>.txt` — request + response
- **Pass condition:** Response body (HTTP 410 JSON or raw body) contains `/etc/passwd` Unix-format content (pattern: `root:x:0:0:`) or `/etc/hostname` value — confirming the external entity was expanded and reflected.
- **Fail condition:** Response body does not reflect file contents; entity reference appears verbatim or empty; or libxmljs2 in the running container has patched `noent` behavior.

---

## [PLAN-006] Eval Injection — User Profile Route Exploitability Proof

- **Test case:** TC-11
- **Threat(s):** T-12
- **Finding(s):** F-6 (`artifacts/sast/semgrep-owasp-top-ten-20260613T204704.json#result[17]`)
- **Entry point:** EP-12 — `GET/PUT /profile`, `routes/userProfile.ts` (JWT Bearer required)
- **Tag:** needs-dynamic-confirmation
- **HUMAN-GATE-REQUIRED:** yes
- **Isolation:** Docker container `juiceshop` on network `appsec-isolated`, host port 3001
- **What to test:**
  Step 1: Register a probe user: `POST http://localhost:3001/api/Users` with `{"email":"eval-probe@juice.invalid","password":"Pr0be1!","passwordRepeat":"Pr0be1!"}`.
  Step 2: Login: `POST http://localhost:3001/rest/user/login` with those credentials. Extract JWT from `authentication.token`.
  Step 3: Confirm route path: `routes/userProfile.ts` must be registered in `server.ts`. The route surface in EP-12 is `/profile`. Confirm by reading the route registration if needed before sending.
  Step 4: Baseline probe — `PUT http://localhost:3001/profile` with `Authorization: Bearer <jwt>`, `Content-Type: application/json`, body `{"username":"test_baseline"}`. Capture response.
  Step 5: Injection probe — `PUT http://localhost:3001/profile` with body `{"username":"'+process.version+'"}`. If the eval at `userProfile.ts:61` processes this, the `process.version` expression will be evaluated and may appear in the response or in an error message.
  Step 6: Alternative probe — `PUT http://localhost:3001/profile` with body `{"username":"test'); require('fs').readdirSync('/').join(','); //"}`. Look for a directory listing in the response or error.
- **Expected artifact:** `artifacts/dynamic/PLAN-006-<timestamp>.txt` — baseline + injection probe requests + responses
- **Pass condition:** Response body or error message contains a Node.js version string (`v2x.x.x`), a filesystem path list, a `ReferenceError` or `SyntaxError` from interpreted JavaScript, or any other indicator that the injected expression was executed in an eval context.
- **Fail condition:** Response body treats the username as a sanitized/escaped string with no eval-related error; input is reflected literally or rejected outright.

---

## [PLAN-007] VM Sandbox Escape — B2B Order RCE Proof

- **Test case:** TC-7
- **Threat(s):** T-10
- **Finding(s):** none (static-inconclusive — `vm.runInContext` not modeled as a dangerous sink in Semgrep JS standard rules)
- **Entry point:** EP-4 — `POST /b2b/v2/orders` (JWT Bearer required)
- **Tag:** dynamic-only
- **HUMAN-GATE-REQUIRED:** yes
- **Isolation:** Docker container `juiceshop` on network `appsec-isolated`, host port 3001
- **What to test:**
  Step 1: Obtain a valid JWT via `POST /rest/user/login` with any registered user credentials (including the probe user from PLAN-006 if already registered).
  Step 2: Send the following probes in sequence, capturing each response before sending the next:
  - Probe 1 (baseline — confirm eval path is reached): `POST http://localhost:3001/b2b/v2/orders` with `Authorization: Bearer <jwt>`, `Content-Type: application/json`, body `{"orderLinesData":"1+1"}`. Expect a computed result `2` in response confirming `safeEval` is executed.
  - Probe 2 (constructor-chain sandbox escape): body `{"orderLinesData":"(function(){return this})().constructor.constructor('return process')().version"}`. Targets the vm context's `this` binding to traverse to `Function.constructor` and access `process`.
  - Probe 3 (global access path): body `{"orderLinesData":"global.process.version"}`. Tests direct `global` object access from within the vm context.
  Do not attempt further probes if probe 1 fails — document the failure and stop.
- **Expected artifact:** `artifacts/dynamic/PLAN-007-<timestamp>.txt` — all probe requests + responses
- **Pass condition:** Any probe response body contains a Node.js version string (e.g., `v22.x.x`) or any string indicating the `process` object was accessed outside the sandbox.
- **Fail condition:** All probes return HTTP 400 with a "syntaxError", "forbidden expression", or similar message from `notevil`/the vm guard. Document which guards blocked which probes.

---

## [PLAN-008] YAML Bomb — Denial of Service Proof

- **Test case:** TC-8
- **Threat(s):** T-8
- **Finding(s):** none (dynamic-only)
- **Entry point:** EP-3 — `POST /file-upload` (unauthenticated, internet-exposed)
- **Tag:** dynamic-only
- **HUMAN-GATE-REQUIRED:** yes
- **Isolation:** Docker container `juiceshop` on network `appsec-isolated`, host port 3001. **Warning:** a successful DoS test will degrade or crash the container. Run this entry last in the session or restart the container immediately after.
- **What to test:**
  Pre-check: inspect `appsec-harness/validation/targets/juiceshop-src/package.json` for the `js-yaml` version. js-yaml ≥4.0.0 uses `SAFE_SCHEMA` by default (no alias expansion) — if v4+, the bomb may not trigger; document and record as `inconclusive`.
  If js-yaml version permits alias expansion, send `POST http://localhost:3001/file-upload` as `multipart/form-data` with a file named `bomb.yml` (MIME: `application/x-yaml`) containing:
  ```
  a: &a ["x","x","x","x","x","x","x","x","x"]
  b: &b [*a,*a,*a,*a,*a,*a,*a,*a,*a]
  c: &c [*b,*b,*b,*b,*b,*b,*b,*b,*b]
  d: &d [*c,*c,*c,*c,*c,*c,*c,*c,*c]
  e: &e [*d,*d,*d,*d,*d,*d,*d,*d,*d]
  ```
  Measure wall-clock response time. If the container becomes unresponsive, restart it before running further tests.
- **Expected artifact:** `artifacts/dynamic/PLAN-008-<timestamp>.txt` — request + response (or timeout note) with response time recorded
- **Pass condition:** Response time >2000ms (the vm sandbox timeout in `fileUpload.ts`), server returns HTTP 500 or connection resets, and/or `yamlBombChallenge` is recorded as solved in `GET /api/Challenges`.
- **Fail condition:** Response returns <500ms with a controlled error ("Invalid YAML" or "Unsupported YAML feature"), indicating the safe schema or vm guard blocked expansion. Record js-yaml version and mark as `inconclusive` with note.

---

## [PLAN-009] Broken Access Control — Unauthenticated Access Log Download

- **Test case:** TC-9
- **Threat(s):** T-4
- **Finding(s):** none (dynamic-only — F-4 covered `/ftp` and `/encryptionkeys`; `/support/logs` is a separate path not yet confirmed at runtime)
- **Entry point:** EP-11 — `GET /support/logs`, `GET /support/logs/:file` (unauthenticated, internet-exposed)
- **Tag:** dynamic-only
- **HUMAN-GATE-REQUIRED:** yes
- **Isolation:** Docker container `juiceshop` on network `appsec-isolated`, host port 3001
- **What to test:**
  Step 1: `GET http://localhost:3001/support/logs` with no `Authorization` header. Confirm an HTML directory listing is returned.
  Step 2: From the listing, identify the most recent `.log` file. Download it: `GET http://localhost:3001/support/logs/<filename>.log`.
  Step 3: Verify the downloaded content contains Morgan Combined Log Format lines (pattern: `<IP> - - [<timestamp>] "<METHOD> <path> HTTP/1.x" <status> <bytes>`).
- **Expected artifact:** `artifacts/dynamic/PLAN-009-<timestamp>.txt` — directory listing request/response + log file request/response
- **Pass condition:** HTTP 200 for both requests; log file body contains Combined Log Format lines with IP addresses and request paths visible.
- **Fail condition:** HTTP 401/403 on step 1 or step 2; no directory listing returned; or log directory exists but is empty.

---

## [PLAN-010] Open Redirect — Allowlist Substring Bypass

- **Test case:** TC-12
- **Threat(s):** T-11
- **Finding(s):** F-7 (`artifacts/sast/semgrep-owasp-top-ten-20260613T204704.json#result[15]`)
- **Entry point:** EP-10 — `GET /redirect?to=` (unauthenticated, internet-exposed)
- **Tag:** needs-dynamic-confirmation
- **HUMAN-GATE-REQUIRED:** yes
- **Isolation:** Docker container `juiceshop` on network `appsec-isolated`, host port 3001
- **What to test:**
  Step 1 (baseline — confirm allowlist is checked): `GET http://localhost:3001/redirect?to=http://evil.example.com` with no `Authorization` header. Expect HTTP 400 "Redirecting to a URL is not allowed" — confirming the allowlist check fires.
  Step 2 (bypass): `GET http://localhost:3001/redirect?to=http://evil.example.com/?ref=https://juice-sh.op`. The `isRedirectAllowed()` check in `insecurity.ts:137` uses `url.includes(allowedUrl)` — a substring match. Since the URL string contains `https://juice-sh.op` as a query parameter, the check evaluates `true` and a 302 redirect to `evil.example.com` should be issued.
  **Do not follow the redirect.** Inspect only the response status and `Location` header. No traffic should go to `evil.example.com`.
- **Expected artifact:** `artifacts/dynamic/PLAN-010-<timestamp>.txt` — baseline + bypass requests + responses (headers only for step 2 is sufficient)
- **Pass condition:** Step 2 returns HTTP 302 with `Location: http://evil.example.com/?ref=https://juice-sh.op` (or similar), confirming the user would be redirected to an attacker-controlled domain.
- **Fail condition:** Step 2 returns HTTP 400 ("Redirecting to a URL is not allowed"), indicating the bypass failed; or the allowlist validation was tightened beyond substring matching.

---

## [PLAN-011] Unauthenticated Prometheus Metrics Exposure

- **Test case:** TC-10
- **Threat(s):** T-7
- **Finding(s):** none (dynamic-only)
- **Entry point:** EP-8 — `GET /metrics` (unauthenticated, internet-exposed)
- **Tag:** dynamic-only
- **HUMAN-GATE-REQUIRED:** yes
- **Isolation:** Docker container `juiceshop` on network `appsec-isolated`, host port 3001
- **What to test:**
  `GET http://localhost:3001/metrics` with no `Authorization` header and no cookies. Inspect the response `Content-Type`, status code, and body format.
- **Expected artifact:** `artifacts/dynamic/PLAN-011-<timestamp>.txt` — request + response
- **Pass condition:** HTTP 200 with `Content-Type: text/plain; version=0.0.4; charset=utf-8` (Prometheus text exposition format) and body containing `# HELP` and `# TYPE` comment lines followed by metric name entries (e.g., `nodejs_heap_size_used_bytes`, `http_requests_total`).
- **Fail condition:** HTTP 401/403 or redirect to login; or response body is not Prometheus exposition format.

---

#### TC Status Summary (post-Phase-4a)

| TC | Prior Status | Phase 4a Tag | Updated Status | Plan Entry |
|---|---|---|---|---|
| TC-1 | confirmed-static | needs-dynamic-confirmation | needs-dynamic-confirmation | PLAN-001 |
| TC-2 | confirmed-static | needs-dynamic-confirmation | needs-dynamic-confirmation | PLAN-003 |
| TC-3 | confirmed | closed | confirmed (no change) | — |
| TC-4 | static-inconclusive | dynamic-only | dynamic-only | PLAN-005 |
| TC-5 | needs-dynamic-confirmation | needs-dynamic-confirmation | needs-dynamic-confirmation | PLAN-004 |
| TC-6 | static-inconclusive | dynamic-only | dynamic-only | PLAN-002 |
| TC-7 | static-inconclusive | dynamic-only | dynamic-only | PLAN-007 |
| TC-8 | pending | dynamic-only | dynamic-only | PLAN-008 |
| TC-9 | pending | dynamic-only | dynamic-only | PLAN-009 |
| TC-10 | pending | dynamic-only | dynamic-only | PLAN-011 |
| TC-11 | confirmed-static | needs-dynamic-confirmation | needs-dynamic-confirmation | PLAN-006 |
| TC-12 | confirmed-static | needs-dynamic-confirmation | needs-dynamic-confirmation | PLAN-010 |

### Phase 4a Gate Status

- [x] Every TC with `resolution: dynamic` or `both` is represented in the plan
- [x] Every plan entry traces to a threat ID and (if available) a finding ID
- [x] Human-gate notice is present and prominent in findings.md
- [x] No plan entry says "test for SQL injection generally" — each names the specific endpoint, parameter, and payload

### Dynamic Test Results

**Phase 4b executed: 2026-06-14T03:30:00Z** | Target: http://localhost:3001 (Docker `juiceshop`, network `appsec-isolated`) | Approved by: Blake (06/13/2026) | Plans executed: 11/11

#### Results Table

| Plan | TC | Threat | Result | Artifact | Notes |
|---|---|---|---|---|---|
| PLAN-001 | TC-1 | T-2 | **confirmed** | `artifacts/dynamic/PLAN-001-20260614T031715Z.txt` | HTTP 200, JWT returned with admin@juice-sh.op, role=admin — auth bypass confirmed |
| PLAN-002 | TC-6 | T-9 | **confirmed** | `artifacts/dynamic/PLAN-002-20260614T031730Z.txt` | HTTP 201 registration with role=admin accepted; admin endpoint HTTP 200 |
| PLAN-003 | TC-2 | T-3 | **confirmed** | `artifacts/dynamic/PLAN-003-20260614T031923Z.txt` | 23 user rows exfiltrated via UNION SELECT; corrected payload (type-compatible literals) |
| PLAN-004 | TC-5 | T-6 | **confirmed** | `artifacts/dynamic/PLAN-004-20260614T031942Z.txt` | /ftp listing (11KB), .kdbx (3246 bytes), premium.key (50 bytes) — all unauthenticated |
| PLAN-005 | TC-4 | T-5 | **confirmed** | `artifacts/dynamic/PLAN-005-20260614T032030Z.txt` | HTTP 410 with /etc/passwd contents reflected — XXE via libxmljs2 noent:true |
| PLAN-006 | TC-11 | T-12 | **inconclusive** | `artifacts/dynamic/PLAN-006-20260614T032207Z.txt` | Eval gated by isChallengeEnabled(usernameXssChallenge); disabledEnv:Docker blocks path |
| PLAN-007 | TC-7 | T-10 | **inconclusive** | `artifacts/dynamic/PLAN-007-20260614T032527Z.txt` | rceChallenge + rceOccupyChallenge both disabledEnv:Docker; else branch ran; no eval |
| PLAN-008 | TC-8 | T-8 | **confirmed** | `artifacts/dynamic/PLAN-008-20260614T032937Z.txt` | 2062ms response (>2000ms threshold); YAML alias expansion occurred; vm sandbox protected |
| PLAN-009 | TC-9 | T-4 | **confirmed** | `artifacts/dynamic/PLAN-009-20260614T032749Z.txt` | HTTP 200 directory listing + log download; CLF entries including pentest session IPs |
| PLAN-010 | TC-12 | T-11 | **confirmed** | `artifacts/dynamic/PLAN-010-20260614T032842Z.txt` | HTTP 302 to evil.example.com; allowlist bypass via ?ref=https://github.com/juice-shop/juice-shop |
| PLAN-011 | TC-10 | T-7 | **confirmed** | `artifacts/dynamic/PLAN-011-20260614T032910Z.txt` | HTTP 200, 26KB Prometheus metrics; file_upload_errors{text/xml}=1 reveals XXE test |

#### Notable Observations (Out-of-Plan)

> Per dynamic-test.md §4: Out-of-plan observations are documented here only. No additional requests sent to investigate them. Return to Phase 1/2 to assess.

1. **PLAN-003 correction:** The plan payload used `NULL` for `price` and `deluxePrice` columns (REAL type). SQLite rejected empty NULLs in type-strict context — corrected to `'4'` and `5.0` without changing the vulnerability class or scope.

2. **PLAN-006/007 Docker gating pattern:** Both `usernameXssChallenge` (eval at userProfile.ts:61) and `rceChallenge`/`rceOccupyChallenge` (vm.runInContext at b2bOrder.ts:17) have `disabledEnv: "Docker"` set in `challenges.yml`. The dangerous code paths exist in source but are conditionally bypassed at runtime. **This is significant for any non-Docker deployment of Juice Shop** — the same code would be fully exploitable. Flag for human: if this software were deployed in a non-Docker environment (e.g., bare-metal, VM), TC-7 and TC-11 would be critical RCE vulnerabilities without mitigation.

3. **PLAN-009 — Pentest session visible in logs:** The access log at `/support/logs/access.log.2026-06-14` captured all our pentest requests including login attempts, admin endpoint access, and user registration. An attacker with log access can enumerate our session and potentially reverse-engineer security controls being tested.

4. **PLAN-011 — LLM integration metrics exposed:** The `/metrics` endpoint exposes `juiceshop_llm_input_tokens_total` and `juiceshop_llm_output_tokens_total` counters, revealing that the application integrates with an external LLM API. This out-of-scope surface (C-9, External AI Chat Service) was not covered in Phase 4 but may warrant a separate assessment.

#### TC Status Summary (post-Phase-4b)

| TC | Post-4a Status | Post-4b Status | Plan | Result |
|---|---|---|---|---|
| TC-1 | needs-dynamic-confirmation | **confirmed** | PLAN-001 | SQLi auth bypass exploited |
| TC-2 | needs-dynamic-confirmation | **confirmed** | PLAN-003 | UNION exfil — 23 user rows |
| TC-3 | confirmed | confirmed (no change) | — | Static only |
| TC-4 | dynamic-only | **confirmed** | PLAN-005 | XXE /etc/passwd reflected |
| TC-5 | needs-dynamic-confirmation | **confirmed** | PLAN-004 | Unauth .kdbx + .key downloaded |
| TC-6 | dynamic-only | **confirmed** | PLAN-002 | Admin self-registration |
| TC-7 | dynamic-only | **inconclusive** | PLAN-007 | Docker-gated; no eval executed |
| TC-8 | dynamic-only | **confirmed** | PLAN-008 | 2062ms YAML expansion delay |
| TC-9 | dynamic-only | **confirmed** | PLAN-009 | Unauth log download |
| TC-10 | dynamic-only | **confirmed** | PLAN-011 | Unauth Prometheus metrics |
| TC-11 | needs-dynamic-confirmation | **inconclusive** | PLAN-006 | Docker-gated; eval branch blocked |
| TC-12 | needs-dynamic-confirmation | **confirmed** | PLAN-010 | Open redirect 302 to evil domain |

**Summary:** confirmed: 9, inconclusive: 2, out-of-scope/static-only: 1

#### Phase 4b Gate Status

- [x] `dynamic_test_signoff.approved == true` verified before any traffic
- [x] Every executed plan entry has an artifact file (`artifacts/dynamic/PLAN-00N-*.txt`)
- [x] No finding has `status: "confirmed"` without a request/response artifact
- [x] No request sent to a host not in `scope.manifest.yaml` (all traffic to `http://localhost:3001`)
- [x] Out-of-plan observations noted in §"Notable Observations" above — not acted on
- [x] PLAN-008 (DoS) run last per plan entry warning; container verified healthy after execution

---

## Phase 5 — Adversarial Review

**Agent:** adversarial-reviewer  
**Timestamp:** 2026-06-14T04:00:00Z  
**Reviewed:** 18 findings (7 static, 11 dynamic), 12 test cases, 12 threats, 12 entry points, 4 crown jewels

> **Mandate:** This review independently challenges every finding and coverage claim without deferring to the producing agents' conclusions. All artifact claims were verified by reading the actual artifact files.

### Artifact Verification Summary

All 18 `evidence_artifact_path` values pointed to existing files. Each was independently read and checked:

| Finding | Artifact Check | Result |
|---|---|---|
| F-1 | semgrep JSON result[13] — `express-sequelize-injection`, login.ts:34 | **VERIFIED** |
| F-2 | semgrep JSON result[16] — `express-sequelize-injection`, search.ts:23 | **VERIFIED** |
| F-3 | semgrep JSON result[9] — `hardcoded-jwt-secret`, insecurity.ts:56 | **VERIFIED** |
| F-4 | semgrep JSON result[18] — `express-check-directory-listing`, server.ts:269 | **VERIFIED** |
| F-5 | semgrep JSON result[10] — `express-res-sendfile`, fileServer.ts:33 | **VERIFIED** |
| F-6 | semgrep JSON result[17] — `code-string-concat`, userProfile.ts:61 | **VERIFIED** |
| F-7 | semgrep JSON result[15] — `express-open-redirect`, redirect.ts:19 | **VERIFIED** |
| F-8 | PLAN-001 artifact: HTTP 200 + JWT with `email=admin@juice-sh.op`, `role=admin` | **VERIFIED** |
| F-9 | PLAN-002 artifact: HTTP 201 + JWT `role=admin` + admin endpoint HTTP 200 | **VERIFIED (partial)** — see ACTION-002 |
| F-10 | PLAN-003 artifact: 23 user rows with emails and MD5 hashes | **VERIFIED** |
| F-11 | PLAN-004 artifact: /ftp HTTP 200 listing + .kdbx 3246B + premium.key 50B | **VERIFIED** |
| F-12 | PLAN-005 artifact: HTTP 410 with `/etc/passwd` content in error title | **VERIFIED** |
| F-13 | PLAN-006 artifact: 302 redirect captured + GET /profile rendered without eval | **VERIFIED** |
| F-14 | PLAN-007 artifact: Three probes, all HTTP 200 order numbers; else branch ran | **VERIFIED** |
| F-15 | PLAN-008 artifact: HTTP 410, 2062ms wall-clock time, YAML JSON in body | **VERIFIED** |
| F-16 | PLAN-009 artifact: HTTP 200 directory listing + CLF log with pentest IPs | **VERIFIED** |
| F-17 | PLAN-010 artifact: HTTP 302 `Location: http://evil.example.com/...` | **VERIFIED** |
| F-18 | PLAN-011 artifact: HTTP 200, 25999 bytes, `# HELP`/`# TYPE` in body | **VERIFIED** |

---

### Inconsistencies Found

#### INC-001 — Documentation Error: Open Redirect bypass payload incorrect in TC-12 and F-7

**Type:** ARTIFACT MISMATCH (documentation)  
**Affected:** TC-12 description, F-7 description, PLAN-010 entry in findings.md

The TC-12 description and F-7 description both specify the bypass as embedding `https://juice-sh.op` as a query parameter: `http://evil.com/?ref=https://juice-sh.op`. However, `juice-sh.op` does **not** appear in the actual `redirectAllowlist` in `insecurity.ts:124-131`. The actual bypass required embedding a real allowlisted URL (e.g., `https://github.com/juice-shop/juice-shop`). The Phase 4b dynamic test correctly used the working payload, but the plan description (and F-7 description) remain misleading for any future tester relying on them. A tester following the documented payload would get HTTP 406 and conclude the bypass failed.

**Quote from insecurity.ts:124:**
```
export const redirectAllowlist = new Set([
  'https://github.com/juice-shop/juice-shop',
  'https://blockchain.info/address/...',
  ...
  // 'juice-sh.op' does NOT appear
])
```

---

#### INC-002 — Partial Response in F-9 Artifact (PLAN-002, Step 2)

**Type:** UNVERIFIED DYNAMIC CLAIM (partial)  
**Affected:** F-9, `artifacts/dynamic/PLAN-002-20260614T031730Z.txt`

The PLAN-002 artifact for Step 2 (login response) contains the placeholder text `(JWT returned — see Step 3 JWT payload below)` rather than the actual HTTP response body. The Step 3 JWT payload decode IS included and shows `role=admin`. The claim is independently supportable from the decoded JWT and the admin endpoint HTTP 200 in Step 4, but the raw Step 2 login response is not preserved. A strict audit would flag this: the login response body containing the token is not in the artifact.

---

#### INC-003 — TC-5 resolution: "dynamic" inconsistent with static findings F-4, F-5

**Type:** STATUS INCONSISTENCY  
**Affected:** `test_cases[TC-5].resolution`

TC-5 has `resolution: "dynamic"` in `threat-model.json`. However, Phase 3 SAST produced two static findings directly covering TC-5: F-4 (`express-check-directory-listing` at server.ts:269) and F-5 (`express-res-sendfile` at fileServer.ts:33). Both findings have `from_test_case: "TC-5"`. The resolution should have been updated to `"both"` after Phase 3, as it was for other cases where SAST found partial evidence. The resolution field is no longer accurate.

---

#### INC-004 — F-5 "confirmed" but dynamic evidence shows path traversal is blocked

**Type:** ARTIFACT MISMATCH (severity/impact discrepancy)  
**Affected:** F-5 (`type: "static"`, `status: "confirmed"`)

F-5 is a **static** finding, and the SAST claim (Semgrep `express-res-sendfile` fired at fileServer.ts:33) is correctly confirmed. However, PLAN-004 Step 4 showed that the path traversal probe `GET /ftp/..%2F..%2Fpackage.json` returned **HTTP 403 Forbidden** — traversal outside the /ftp root is blocked at runtime by express-serve-static sanitization. F-5's description says "Creates a path traversal risk" without noting the runtime mitigation. The static code pattern exists but the practical exploitability is reduced by express's built-in sanitization. F-5 should note this mitigation finding; readers of the finding without the dynamic artifact would overestimate the exploitability.

---

#### INC-005 — PLAN-003 Executed Payload Differs From Staged Plan

**Type:** ARTIFACT MISMATCH (documentation)  
**Affected:** PLAN-003 entry in findings.md Phase 4 plan; F-10 artifact

The staged PLAN-003 entry specifies: `')) UNION SELECT id,email,password,role,NULL,NULL,NULL,NULL,NULL FROM Users--`

The actual executed payload (as documented in the F-10 artifact) was: `')) UNION SELECT id,email,password,'4',5.0,'',datetime(),datetime(),NULL FROM Users--`

The original payload used `NULL` for the `price` (REAL) and `deluxePrice` (REAL) columns; SQLite rejected type-mismatched NULLs in the UNION and returned 0 rows. The F-10 artifact notes the correction. However, the staged PLAN-003 entry in the master test plan section of findings.md was **not updated** to reflect the actual working payload, creating a discrepancy between the documented test and what was actually run.

---

#### INC-006 — TC-4 resolution: "both" but has zero static findings

**Type:** STATUS INCONSISTENCY (minor)  
**Affected:** `test_cases[TC-4].resolution`

TC-4 has `resolution: "both"` (meaning SAST + dynamic both intended). Phase 3 produced no static findings for TC-4 (it was explicitly `static-inconclusive` — 188 rules, zero results). F-12 is the only finding for TC-4, and it is dynamic. The resolution field is not wrong in principle (a "both" intent that produced static-inconclusive is documented correctly), but the resolution field `"both"` with zero static findings and no `static_inconclusive_reason` in the finding is slightly misleading. The `static_inconclusive_reason` is in `test_cases[TC-4]` — this is correct placement — so the inconsistency is minor.

Similarly TC-6 and TC-7 have `resolution: "both"` with no static findings. Both have `static_inconclusive_reason` documented in the TC entry, which is the correct place for it.

---

### Blind Spots (threat-model nodes with no test coverage)

#### EP-6 — POST /rest/user/reset-password — **ZERO COVERAGE**

No test case maps to EP-6. The password reset surface is a classic attack vector:
- Security question bypass (Juice Shop uses predictable security answers by design)
- Account takeover via security question enumeration
- No rate-limiting or token expiry verification

This is a significant omission: password reset vulnerabilities in Juice Shop are well-documented and the endpoint sits adjacent to the login surface (EP-1) which confirmed SQLi. No threat in `threats[]` covers this endpoint.

#### EP-7 — PUT /rest/products/:id/reviews — **ZERO COVERAGE**

No test case maps to EP-7. Product reviews are stored in MarsDB (an in-process NoSQL store). Known risks:
- NoSQL injection via MarsDB query operators (`$where`, `$regex`)
- Horizontal authorization bypass: update another user's review without owning it
- Persistent XSS via stored review content rendered in the Angular SPA

This endpoint was noted in the DFD under C-4 (MarsDB Product Reviews Store) but was never threat-modeled with a specific threat or test case.

#### CJ-3 — Payment Card and Wallet Data — **No direct test coverage**

CJ-3 (Payment Card / Wallet) is traced by T-9 (mass assignment → admin), T-10 (VM sandbox RCE), and T-12 (eval injection) — all of which require **first achieving privilege escalation**. No test case directly exercises:
- `GET/POST /api/Cards` — payment card CRUD
- `GET /rest/wallet/balance` — wallet balance
- `GET /api/Addresss` — delivery addresses

An attacker who obtains an admin JWT (confirmed via PLAN-001 or PLAN-002) can directly access these endpoints, but the threat model never explicitly tested unauthorized direct access to payment data.

---

### Human Action Items (Ranked)

#### CRITICAL — Must resolve before closing

```
[CRITICAL] ACTION-001: Correct open redirect bypass payload documentation
- Finding/test case: F-7, TC-12, PLAN-010 entry in findings.md
- Issue: Both F-7 description and TC-12 description specify ?ref=https://juice-sh.op as the
  bypass token, but juice-sh.op is NOT in the redirectAllowlist (insecurity.ts:124-131).
  A future tester following these instructions would get HTTP 406 and incorrectly conclude
  the bypass failed. The working payload uses an actual allowlisted URL as the embedded token.
- Recommended action: Update F-7 reviewer_notes and TC-12 description to specify the actual
  allowlist content and the correct bypass technique. Update the PLAN-010 staged entry to
  show the correct payload. Correct the "juice-sh.op" reference everywhere.
```

```
[CRITICAL] ACTION-002: Preserve full login response in F-9/PLAN-002 artifact
- Finding/test case: F-9, artifacts/dynamic/PLAN-002-20260614T031730Z.txt
- Issue: Step 2 response in PLAN-002 artifact is a placeholder ("JWT returned — see Step 3").
  The raw HTTP response body (containing the authentication.token) is not preserved.
  Dynamic test agent instructions require a complete request/response pair for confirmed findings.
- Recommended action: Re-execute PLAN-002 login step and capture the full HTTP response body
  including authentication.token, bid, and umail fields. Append to or replace the artifact.
  Or accept the Step 3 JWT decode + Step 4 admin endpoint as sufficient corroboration.
```

---

#### HIGH — Re-run or verify

```
[HIGH] ACTION-003: Correct TC-5 resolution field
- Finding/test case: TC-5 in threat-model.json
- Issue: TC-5 has resolution: "dynamic" but has two static findings: F-4 (express-check-
  directory-listing, server.ts:269) and F-5 (express-res-sendfile, fileServer.ts:33).
  Both are type: "static", from_test_case: "TC-5". The resolution should be "both".
- Recommended action: Update test_cases[TC-5].resolution from "dynamic" to "both" in
  threat-model.json.
```

```
[HIGH] ACTION-004: Add runtime mitigation note to F-5 (path traversal blocked)
- Finding/test case: F-5
- Issue: F-5 title is "Path Traversal Risk in File Serving Routes" and status: "confirmed".
  PLAN-004 Step 4 showed GET /ftp/..%2F..%2Fpackage.json → HTTP 403 Forbidden. Express
  serve-static sanitization blocks directory traversal at runtime. The finding description
  does not mention this mitigation. A reader of F-5 alone would overestimate exploitability.
- Recommended action: Add reviewer_notes to F-5: "PLAN-004 Step 4 showed path traversal via
  ..%2F is blocked by HTTP 403 (express-serve-static sanitization). The code pattern
  (user-supplied path to res.sendFile) exists but is mitigated at runtime. Risk is
  reduced from 'path traversal possible' to 'file serving restricted to configured root'
  in the current build."
```

```
[HIGH] ACTION-005: Correct PLAN-003 staged plan entry to reflect actual working payload
- Finding/test case: PLAN-003 entry in findings.md § Staged Plan; F-10
- Issue: The staged PLAN-003 entry documents: "') UNION SELECT id,email,password,role,
  NULL,NULL,NULL,NULL,NULL FROM Users--". F-10 artifact shows the original payload
  returned 0 rows; the working payload used type-compatible literals for numeric columns.
  The plan entry was not updated post-execution.
- Recommended action: Update the PLAN-003 staged plan entry in findings.md to show the
  corrected payload: ')) UNION SELECT id,email,password,'4',5.0,'',datetime(),datetime(),
  NULL FROM Users-- and add a note that the NULL-only payload failed due to SQLite type
  coercion on REAL columns.
```

```
[HIGH] ACTION-006: Assess F-4 severity upgrade to critical
- Finding/test case: F-4 (high), F-11 (high)
- Issue: F-4 describes unauthenticated directory listing at /ftp, /encryptionkeys, /support/logs.
  PLAN-004 confirmed that incident-support.kdbx (KeePass DB, 3246 bytes) and
  premium.key (50 bytes, plaintext "1337133713371337.EA99A61D92D2955B1E9285B55BF2AD42")
  are freely downloadable. Both files are CJ-4 (secret classification). The key value
  is visible in plaintext in the artifact. Standard CWE-548 mapping assigns "high" but
  the direct exposure of a secret-classified crown jewel (encryption key + KeePass
  credentials DB) arguably warrants critical.
- Recommended action: Human reviewer to assess whether direct unauthenticated download of
  the encryption key (crown jewel CJ-4) should be re-classified to critical. If upgraded,
  update F-4 severity and F-11 severity accordingly.
```

```
[HIGH] ACTION-007: Confirm or close T-10 and T-12 outside Docker
- Finding/test case: F-13 (TC-11, inconclusive), F-14 (TC-7, inconclusive)
- Issue: Both vm.runInContext/safeEval (T-10, b2bOrder.ts:17) and eval() (T-12,
  userProfile.ts:61) are gated by isChallengeEnabled() checks with disabledEnv:Docker.
  These are critical-impact threats that could not be confirmed dynamically.
  The code paths exist in production source and are not protected by architectural controls —
  only by a challenge-enabled flag that changes based on deployment environment.
- Recommended action: Either (a) test in a non-Docker environment (bare metal or VM with
  safetyMode set to "disabled"), or (b) formally accept the Docker guard as a deployment
  control and document it in the engagement report. If deploying this application outside
  Docker without this guard, both vulnerabilities are critical RCE risks.
```

---

#### MEDIUM — Extend coverage

```
[MEDIUM] ACTION-008: Add test case for EP-6 (POST /rest/user/reset-password)
- Finding/test case: No TC covers EP-6
- Issue: No threat or test case maps to EP-6 (password reset). Juice Shop's password reset
  uses security questions with predictable answers (mother's maiden name, favorite pet name)
  that can be enumerated or guessed. Account takeover is a direct path to CJ-1.
- Recommended action: Return to Phase 1/2 to add a threat (T-13) for predictable security
  question bypass and a test case (TC-13) for EP-6. Dynamic test: POST
  /rest/user/reset-password with a known security answer for admin@juice-sh.op.
```

```
[MEDIUM] ACTION-009: Add test case for EP-7 (PUT /rest/products/:id/reviews / MarsDB)
- Finding/test case: No TC covers EP-7
- Issue: No threat or test case maps to EP-7. Product reviews are stored in MarsDB
  (in-process MongoDB-compatible NoSQL). MarsDB may be vulnerable to NoSQL injection via
  operator injection ($where, $regex) or horizontal authorization bypass (editing another
  user's review). The threat model identified C-4 (MarsDB) as a component but never
  created a threat for it beyond noting it exists.
- Recommended action: Return to Phase 1/2 to add a threat for NoSQL injection/authorization
  bypass on review endpoints. Add TC mapped to EP-7. Check routes/updateProductReviews.ts
  for user-supplied query operators passed to MarsDB without sanitization.
```

```
[MEDIUM] ACTION-010: Add direct test coverage for CJ-3 payment/wallet endpoints
- Finding/test case: CJ-3 coverage is only indirect (via privilege escalation)
- Issue: CJ-3 (Payment Card and Wallet Data) is only reachable via T-9/T-10/T-12 (which
  require admin or RCE first). No test case directly exercises GET /api/Cards, POST /api/Cards,
  GET /rest/wallet/balance, or GET /api/Addresss under the attacker persona (unauthenticated
  or as a non-admin user). A direct IDOR or authorization bypass test against another user's
  payment data has not been attempted.
- Recommended action: With an admin JWT (obtained via PLAN-001 or PLAN-002), attempt
  GET /api/Cards?UserId=<other user's id> to check for IDOR on payment cards. Also test
  GET /rest/wallet/balance?UserId=<other user's id>. Add findings accordingly.
```

---

#### LOW — Polish

```
[LOW] ACTION-011: Clarify TC-4 and TC-6/TC-7 resolution: "both" with no static findings
- Finding/test case: TC-4, TC-6, TC-7 in threat-model.json
- Issue: TC-4, TC-6, and TC-7 have resolution: "both" but have zero static findings.
  The static_inconclusive_reason is correctly documented in each TC. The resolution field
  is not wrong (SAST was attempted; came back inconclusive), but may mislead future readers
  into expecting to find a static finding for these TCs.
- Recommended action: Add a comment to each TC's static_inconclusive_reason noting:
  "resolution: both — static attempt was made (Phase 3) and was inconclusive; dynamic
  test was the primary confirmation path."
```

```
[LOW] ACTION-012: Document F-15 severity rationale vs T-8 impact discrepancy
- Finding/test case: F-15 (medium) vs T-8 (impact: high)
- Issue: T-8 in threats[] has impact: "high" (description: "exhausting Node.js heap and
  crashing or degrading the process"). F-15 was assigned severity: "medium" because the
  vm sandbox protected the container in the 5-level bomb test (HTTP 410, not crash).
  The discrepancy is defensible but undocumented.
- Recommended action: Add reviewer_notes to F-15 explaining: "Severity assigned medium
  (not high) because the vm sandbox timeout at 2000ms capped the impact to a 2062ms delay
  rather than a crash. A 6-level bomb (9^6 = 531,441 entries) would likely produce a
  reliable 503 and justify high severity. The T-8 threat rating of high reflects the
  theoretical worst case; F-15 reflects the observed impact in this test."
```

---

### Phase 5 Gate Status

- [x] Every finding checked against its artifact (not just described — all 18 artifact files read and independently verified)
- [x] Every threat-model node checked for test coverage (12 threats: all covered; 12 EPs: EP-6 and EP-7 uncovered; 4 CJs: all have threat coverage; CJ-3 lacks direct test)
- [x] Inconsistencies flagged with specific quotes/references (INC-001 through INC-006)
- [x] Human action items ranked and actionable (ACTION-001 through ACTION-012, each with recommended action)
