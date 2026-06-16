# SETUP.md — AppSec Harness Prerequisites Checklist

Complete every item before running Phase 1. Items marked `[auto-detect]` were checked at scaffold time — verify they are still current.

---

## 1. Static Analysis Engines

### Semgrep (required — start here)

- [ ] **Install Semgrep**
  ```bash
  pip install semgrep
  # or
  brew install semgrep
  ```
  Verify: `semgrep --version`

- [ ] **Pull OWASP Top Ten rules** (happens automatically on first run, but confirm network access)
  ```bash
  semgrep --config "p/owasp-top-ten" --dryrun /dev/null
  ```

- [ ] **(Optional) Semgrep Pro / Team** — enables cross-file interprocedural taint. Required if you need `dataflow` mode across module boundaries. Free tier handles single-file taint.
  Sign in: `semgrep login`

### CodeQL CLI (required for high-priority source→sink analysis)

- [ ] **Download CodeQL CLI bundle** from GitHub:
  `https://github.com/github/codeql-action/releases` → `codeql-bundle-*.tar.gz`
  Extract and add `codeql/` to your `PATH`.
  Verify: `codeql --version`

- [ ] **Download query packs** for your target languages:
  ```bash
  # These are bundled with codeql-bundle; confirm they exist:
  ls $(codeql resolve qlpacks --format=json | python3 -c "import sys,json; [print(v['path']) for v in json.load(sys.stdin).values() if 'security' in v.get('name','')]" 2>/dev/null | head -5)
  ```
  If missing: `codeql pack download codeql/javascript-queries codeql/java-queries codeql/python-queries`

- [ ] **For compiled languages (Java, C#, Go):** confirm your build toolchain is available
  ```bash
  # Java:
  mvn --version   # or gradle --version
  # .NET:
  dotnet --version
  # Go:
  go version
  ```

### Language-specific SAST (optional plug-ins)

- [ ] **Bandit** (Python) — `pip install bandit` — `bandit --version`
- [ ] **Brakeman** (Ruby/Rails) — `gem install brakeman` — `brakeman --version`
- [ ] **NodeJsScan** (Node.js) — `pip install nodejsscan` — optional; Semgrep covers most of this
- [ ] **gosec** (Go) — `go install github.com/securego/gosec/v2/cmd/gosec@latest` — `gosec --version`

---

## 2. Source Access

- [ ] **Clone the repo(s) to be analyzed** to a local path
  ```bash
  git clone <repo-url> <local-path>
  ```

- [ ] **Identify languages** in each repo:
  ```bash
  # Quick language detection:
  find <repo-path> -name "*.java" -o -name "*.js" -o -name "*.ts" -o -name "*.py" -o -name "*.go" | \
    sed 's/.*\.//' | sort | uniq -c | sort -rn | head -10
  ```

- [ ] **Note the build command** for any compiled language (needed for CodeQL database creation):
  - Java/Maven: `mvn -DskipTests clean install`
  - Java/Gradle: `./gradlew build -x test`
  - Go: `go build ./...`
  - .NET: `dotnet build`

- [ ] **Fill in `scope.manifest.yaml`** → `repos[]` section with URL, languages, and build_cmd

---

## 3. Architecture Input

- [ ] **Provide a diagram**, OR let the threat-model agent derive a provisional DFD from source.
  - Accepted formats: image (PNG/JPG/SVG — Claude Code can read these via vision), text description, draw.io XML, Mermaid diagram
  - If providing an image: place it at `state/architecture-diagram.<ext>` and note the path when invoking the threat-model agent
  - If no diagram: the agent will derive a provisional DFD from package manifests, routing files, and docker-compose — note that coverage depends on source completeness

---

## 4. Isolated Runtime for Dynamic Testing

- [ ] **Docker** is installed and running
  ```bash
  docker --version
  docker ps
  ```

- [ ] **Create the isolated network** (do this before spinning up any validation target):
  ```bash
  docker network create appsec-isolated
  ```

- [ ] **For validation/practice runs:** pull a known-vulnerable app image (see `validation/README.md`)
  ```bash
  # Juice Shop (recommended first target):
  docker pull bkimminich/juice-shop
  
  # WebGoat (Java/CodeQL validation):
  docker pull webgoat/webgoat-and-wolf
  
  # DVWA (PHP, quick smoke test):
  docker pull vulnerables/web-dvwa
  ```

- [ ] **For real target testing:** confirm you have a Docker/compose setup for the target app in an isolated environment (not your dev machine's host network, not staging/prod)

---

## 5. Authorization Scope Manifest

- [ ] **Fill in `scope.manifest.yaml`** completely:
  - `meta.engagement_name` — name this engagement
  - `meta.authorized_by` — full name + title of the person who owns this authorization
  - `meta.authorized_date` — ISO-8601 date
  - `meta.engineer` — your name
  - `repos[]` — all repos in scope
  - `hosts[]` — all hosts/environments in scope (keep `environment: "local"` for initial validation runs)

- [ ] **Do NOT set `dynamic_test_signoff.approved: true` yet.** You will do this after reviewing the staged test plan in Phase 4.

- [ ] **If testing production (advanced):** fill in `production_signoff` including the incident runbook URL and rollback plan. Do not do this for initial validation runs.

---

## 6. Claude Code with Subagents

- [ ] **Claude Code CLI is installed**
  ```bash
  claude --version
  ```

- [ ] **Subagent discovery works** — the `.claude/agents/` directory exists and Claude Code can see it:
  ```bash
  ls appsec-harness/.claude/agents/
  # Expected: threat-model.md  sast.md  test-plan.md  dynamic-test.md  review.md
  ```

- [ ] **Sufficient context window / model tier** for multi-phase runs. Claude Sonnet 4.6 or higher is recommended.

---

## 7. HTTP Client for Dynamic Testing (Phase 4)

- [ ] **curl** is available (standard on macOS/Linux; install via Chocolatey on Windows)
  ```bash
  curl --version
  ```

- [ ] **Optional: an intercepting proxy** (e.g. Burp Suite Community, OWASP ZAP) for complex request manipulation. Not required for initial runs — curl suffices.

- [ ] **Create the artifact directory:**
  ```bash
  mkdir -p appsec-harness/artifacts/sast
  mkdir -p appsec-harness/artifacts/dynamic
  ```

---

## 8. Human Gate Checkpoint (Phase 4 — Dynamic Testing)

> **This is a process checkpoint, not a tool to install.**

Before the dynamic-test agent sends any traffic, you must:

1. Run Phases 1–3 to completion (threat model + SAST)
2. Run Phase 4a (test-plan agent) to generate the staged plan in `state/findings.md`
3. **Read the entire staged plan** — every PLAN-NNN entry, every target URL, every parameter
4. Satisfy yourself that:
   - Every target URL is in your authorized scope
   - No production systems are targeted
   - The isolated Docker environment is running
   - You understand what each request will do
5. Set `dynamic_test_signoff.approved: true` and fill in `approved_by` and `approved_date` in `scope.manifest.yaml`
6. Then invoke the dynamic-test agent

**The dynamic-test agent will refuse to run without this sign-off. This is intentional.**

---

## Quick-Start Sequence (Validation Run with Juice Shop)

```bash
# 1. Install tools
pip install semgrep
# Install CodeQL CLI from GitHub releases (see above)

# 2. Clone Juice Shop source
git clone https://github.com/juice-shop/juice-shop.git appsec-harness/validation/targets/juiceshop-src

# 3. Start isolated environment
docker network create appsec-isolated
docker run -d --name juiceshop --network appsec-isolated -p 127.0.0.1:3000:3000 bkimminich/juice-shop

# 4. Fill in scope.manifest.yaml (repos + hosts sections)

# 5. Create artifact dirs
mkdir -p appsec-harness/artifacts/sast appsec-harness/artifacts/dynamic

# 6. In Claude Code, invoke Phase 1:
#    "Run the threat-model agent on the Juice Shop source at appsec-harness/validation/targets/juiceshop-src"

# 7. Verify threat-model.json gate, then invoke Phase 3:
#    "Run the SAST agent on the Juice Shop source"

# 8. Invoke Phase 4a:
#    "Run the test-plan agent and stage the dynamic test plan"

# 9. Review state/findings.md → Staged Plan
#    Set dynamic_test_signoff.approved: true in scope.manifest.yaml

# 10. Invoke Phase 4b:
#     "Run the dynamic-test agent against http://localhost:3000"

# 11. Invoke Phase 5 (fresh context):
#     "Run the review agent against the current state"

# 12. Score results against validation/known-vulns.md
```
