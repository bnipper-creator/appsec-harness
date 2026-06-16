# Validation — Proving the Harness Works on Known-Vulnerable Apps

Run the full 5-phase harness against a known-vulnerable app and compare results against `known-vulns.md` to score precision/recall. The goal is to tune grounding and triage until noise is acceptable before pointing the harness at real targets.

---

## Recommended Targets (Tiered)

### Tier 1 — Quick Smoke Test: DVWA (PHP)

Classic, simple, fast. Good for verifying the basic pipeline works end to end.

```bash
# Pull and start DVWA in an isolated Docker network
docker network create appsec-isolated

docker run -d \
  --name dvwa \
  --network appsec-isolated \
  -p 127.0.0.1:8080:80 \
  vulnerables/web-dvwa

# DVWA is now available at http://localhost:8080
# Default credentials: admin / password
# Set security level to Low for initial testing
```

Source: `https://github.com/digininja/DVWA`

Clone for SAST:
```bash
git clone https://github.com/digininja/DVWA.git validation/targets/dvwa-src
```

### Tier 2 — Full Chain: OWASP Juice Shop (Node.js / Angular)

Modern stack, maps cleanly to OWASP Top Ten. Strong for validating the complete chain: threat model → SAST → dynamic.

```bash
docker run -d \
  --name juiceshop \
  --network appsec-isolated \
  -p 127.0.0.1:3000:3000 \
  bkimminich/juice-shop

# Juice Shop is now available at http://localhost:3000
```

Source: `https://github.com/juice-shop/juice-shop`

Clone for SAST:
```bash
git clone https://github.com/juice-shop/juice-shop.git validation/targets/juiceshop-src
```

Scope manifest entry:
```yaml
hosts:
  - url: "http://localhost:3000"
    environment: "local"
    isolated_network: true
    notes: "Juice Shop validation instance — Docker network appsec-isolated"
repos:
  - url: "validation/targets/juiceshop-src"
    languages: [javascript, typescript]
    build_cmd: ""
    notes: "Juice Shop source for SAST"
```

### Tier 3 — CodeQL Java Validation: OWASP WebGoat (Java)

Excellent for validating CodeQL interprocedural taint — Java source→sink for SQLi, XXE, deserialization.

```bash
docker run -d \
  --name webgoat \
  --network appsec-isolated \
  -p 127.0.0.1:8081:8080 \
  -p 127.0.0.1:9090:9090 \
  webgoat/webgoat-and-wolf

# WebGoat: http://localhost:8081/WebGoat
# WebWolf: http://localhost:9090/WebWolf
```

Source: `https://github.com/WebGoat/WebGoat`

Clone and build for CodeQL:
```bash
git clone https://github.com/WebGoat/WebGoat.git validation/targets/webgoat-src
# Build command for CodeQL (uses Maven):
# mvn -DskipTests clean install
```

Scope manifest entry:
```yaml
repos:
  - url: "validation/targets/webgoat-src"
    languages: [java]
    build_cmd: "mvn -DskipTests clean install"
    notes: "WebGoat source for CodeQL Java taint validation"
```

---

## Running the Full Chain

For the recommended starting point (Juice Shop):

### 1. Start the isolated environment
```bash
docker network create appsec-isolated 2>/dev/null || true
docker run -d --name juiceshop --network appsec-isolated -p 127.0.0.1:3000:3000 bkimminich/juice-shop
```

### 2. Fill in scope.manifest.yaml
Add the Juice Shop host and repo path. Set `authorized_by`, `authorized_date`, and `engineer`.

### 3. Run Phase 1 (Threat Model)
Invoke the threat-model agent. Provide the Juice Shop source path. Let it derive a DFD if no diagram is available.

**Verify:** `state/threat-model.json` validates, has crown jewels and entry points, and test cases with IDs.

### 4. Run Phase 3 (SAST)
Invoke the SAST agent against `validation/targets/juiceshop-src`.

```bash
# Semgrep sweep (from the harness root):
semgrep --config "p/owasp-top-ten" --json \
  --output artifacts/sast/semgrep-juiceshop-owasp.json \
  validation/targets/juiceshop-src

# Optional: CodeQL for JS (if CodeQL CLI is installed):
codeql database create artifacts/codeql-db/juiceshop \
  --language=javascript \
  --source-root=validation/targets/juiceshop-src

codeql database analyze artifacts/codeql-db/juiceshop \
  --format=sarif-latest \
  --output=artifacts/sast/codeql-juiceshop.sarif \
  codeql/javascript-queries:codeql-suites/javascript-security-extended.qls
```

**Verify:** every static/both test case is resolved or marked STATIC-INCONCLUSIVE with a reason.

### 5. Run Phase 4a (Test Plan)
Invoke the test-plan agent. Review the staged plan in `state/findings.md`.

### 6. Human gate
Review the plan. Set `dynamic_test_signoff.approved: true` in `scope.manifest.yaml`.

### 7. Run Phase 4b (Dynamic Test)
Invoke the dynamic-test agent. It will send requests to `http://localhost:3000`.

### 8. Run Phase 5 (Review)
Invoke the review agent in a fresh context (without prior conversation about this run).

### 9. Score against known-vulns.md
```
Precision = confirmed_true_positives / (confirmed_true_positives + false_positives)
Recall    = confirmed_true_positives / total_known_vulns_in_scope
```

Iterate: tune Semgrep rules, CodeQL query selection, or threat-model grounding until precision and recall are acceptable.

---

## Cleanup

```bash
docker stop juiceshop dvwa webgoat 2>/dev/null
docker rm juiceshop dvwa webgoat 2>/dev/null
docker network rm appsec-isolated 2>/dev/null
```
