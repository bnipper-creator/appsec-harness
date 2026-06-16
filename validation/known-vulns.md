# Ground Truth: Known Vulnerabilities per Validation App

Use this file to score the harness. After a full run, compare confirmed findings against this list.

**Scoring:**
- True Positive (TP): a known vuln in this list that the harness confirmed
- False Negative (FN): a known vuln in this list that the harness missed
- False Positive (FP): a harness finding that has no corresponding entry here (or is listed as not-present)

---

## OWASP Juice Shop (Node.js / Angular)

Source: Juice Shop's own `/api/Challenges` endpoint lists all challenge categories. These are the security-relevant ones that map to real vulnerability classes.

| ID | OWASP Category | Vulnerability | Location (approx.) | Notes |
|---|---|---|---|---|
| JVS-01 | A01 Broken Access Control | Horizontal privilege escalation — access another user's basket | `routes/basket.js` | IDOR via manipulated basket ID |
| JVS-02 | A01 Broken Access Control | Admin section accessible without admin role | `routes/administration.js` | Missing server-side authz check |
| JVS-03 | A02 Cryptographic Failures | Passwords stored with weak hashing (MD5) | `models/user.js` | Check hash algo in user creation |
| JVS-04 | A03 Injection - SQLi | Login bypass via SQL injection | `routes/login.js` | Classic `' OR 1=1--` in username |
| JVS-05 | A03 Injection - SQLi | Search endpoint SQLi | `routes/search.js` | User-controlled input passed to Sequelize raw query |
| JVS-06 | A03 Injection - XSS (Reflected) | Search results reflect unsanitized input | Frontend Angular template | Check for `bypassSecurityTrustHtml` misuse |
| JVS-07 | A03 Injection - XSS (Stored) | Product review stores and renders unsanitized HTML | `routes/productReviews.js` | Stored XSS in review content |
| JVS-08 | A05 Security Misconfiguration | Exposed `/ftp` directory with sensitive files | Static file serving | No auth on `/ftp` route |
| JVS-09 | A07 Identification & Auth Failures | JWT algorithm confusion (RS256 → HS256 or `alg:none`) | JWT verification middleware | Classic algorithm confusion |
| JVS-10 | A07 Identification & Auth Failures | Password reset via predictable security questions | `routes/securityQuestion.js` | No brute-force protection |
| JVS-11 | A08 Software & Data Integrity | Insecure deserialization — B64-encoded cookie object | `routes/` | Node.js deserialization gadget |
| JVS-12 | A09 Logging Failures | No server-side logging of failed login attempts | `routes/login.js` | Brute force not detectible from logs |
| JVS-13 | A10 SSRF | Order confirmation URL redirect | `routes/` | User-controlled URL fetched server-side |

---

## WebGoat (Java)

Source: WebGoat lesson catalog. Select the lessons that are automated vulnerability classes (not just educational puzzles).

| ID | OWASP Category | Vulnerability | Location (approx.) | Notes |
|---|---|---|---|---|
| WVG-01 | A03 Injection - SQLi | Employee search — classic string concatenation SQLi | `SqlInjectionLesson*.java` | Direct string concat into JDBC query |
| WVG-02 | A03 Injection - SQLi | Blind SQLi — boolean-based | `SqlInjectionAdvanced*.java` | |
| WVG-03 | A03 Injection - XXE | XML External Entity via file upload | `XXE*.java` | Parses user-uploaded XML without disabling external entities |
| WVG-04 | A01 Broken Access Control | IDOR — access another user's profile | `IDOR*.java` | |
| WVG-05 | A02 Cryptographic Failures | Insecure direct object in JWT | `JWT*.java` | `alg:none` accepted |
| WVG-06 | A08 Deserialization | Java deserialization gadget chain | `InsecureDeserialization*.java` | |
| WVG-07 | A03 Injection - Path Traversal | Path traversal in file upload | `PathTraversal*.java` | |

---

## DVWA (PHP)

| ID | OWASP Category | Vulnerability | Location (approx.) | Notes |
|---|---|---|---|---|
| DVA-01 | A03 Injection - SQLi | GET parameter in user lookup | `vulnerabilities/sqli/source/low.php` | Classic `id` param |
| DVA-02 | A03 Injection - SQLi (Blind) | Blind SQLi in user lookup | `vulnerabilities/sqli_blind/` | |
| DVA-03 | A03 Injection - XSS (Reflected) | `name` parameter reflected | `vulnerabilities/xss_r/` | |
| DVA-04 | A03 Injection - XSS (Stored) | Guestbook stored XSS | `vulnerabilities/xss_s/` | |
| DVA-05 | A03 Injection - Command Injection | IP ping field | `vulnerabilities/exec/` | Shell metacharacters in ping target |
| DVA-06 | A01 Broken Access Control | CSRF — change admin password | `vulnerabilities/csrf/` | |
| DVA-07 | A04 Insecure Design | Insecure file upload (no type validation) | `vulnerabilities/upload/` | PHP webshell upload |
| DVA-08 | A01 Broken Access Control | Directory traversal / LFI | `vulnerabilities/fi/` | `page` parameter |

---

## Scoring Template

After a harness run, fill in:

```
App: <Juice Shop | WebGoat | DVWA>
Run date: <date>
Phase 3 (SAST) results:
  TP (SAST detected): [IDs]
  FN (SAST missed): [IDs]
  FP (SAST flagged, not in ground truth): [descriptions]
  SAST precision: __ / __ = __%
  SAST recall: __ / __ = __%

Phase 4 (Dynamic) results:
  TP (Dynamic confirmed): [IDs]
  FN (Dynamic missed): [IDs]
  FP (Dynamic false alarm): [descriptions]
  Dynamic precision: __ / __ = __%
  Dynamic recall: __ / __ = __%

Notes / tuning actions:
```
