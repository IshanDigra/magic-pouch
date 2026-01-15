# Enterprise-Grade CI/CD Architecture for Static Web Applications
## A Definitive Technical Reference

---

## Executive Summary

This document outlines a production-grade Continuous Integration/Continuous Deployment (CI/CD) architecture for Single Page Applications (SPAs) deployed via GitHub Pages. The implementation integrates:

- **OIDC Authentication** (replacing deprecated PAT-based approaches)
- **Python-based Secret Injection** (eliminating shell script fragility)
- **Artifact Immutability** (via `upload-pages-artifact`)
- **Supply Chain Security** (SHA-pinned GitHub Actions)
- **Least Privilege Authorization** (permission scoping)
- **Twelve-Factor App Compliance** (environment variable management)

---

## 1. Architectural Overview

### 1.1 The Deployment Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ Developer Push to Main Branch                               │
│ (or Manual workflow_dispatch trigger)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────┐
        │ Job 1: Validate             │
        │ - Check config.json syntax  │
        │ - Verify index.html exists  │
        │ - Validate firewall rules   │
        └────────────┬────────────────┘
                     │
                     ▼
        ┌─────────────────────────────┐
        │ Job 2: Build                │
        │ - Setup Python 3.11         │
        │ - Execute inject_secrets.py │
        │ - Replace __PLACEHOLDERS__  │
        │ - Upload artifact to GH     │
        └────────────┬────────────────┘
                     │
                     ▼
        ┌─────────────────────────────┐
        │ Job 3: Deploy               │
        │ - GitHub Pages Environment  │
        │ - OIDC Authentication       │
        │ - Unpack artifact to CDN    │
        └────────────┬────────────────┘
                     │
                     ▼
   https://IshanDigra.github.io/magic-pouch
   (Live on Fastly CDN globally)
```

### 1.2 Key Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Workflow File** | Orchestrates CI/CD pipeline | GitHub Actions (YAML) |
| **Validation Job** | Pre-deployment checks | Bash scripts |
| **Secret Injection** | Embeds configuration | Python 3.11+ |
| **Artifact Storage** | Immutable build artifacts | GitHub Pages artifact API |
| **Deployment Target** | Production hosting | GitHub Pages (Fastly CDN) |
| **Authentication** | Deployment authorization | OpenID Connect (OIDC) |

---

## 2. The Frontend Configuration Paradox

### 2.1 Problem Statement

Static web applications present a unique challenge: they run in the **user's untrusted browser**, yet require **environment-specific configuration** (API endpoints, Firebase credentials, etc.).

**The Paradox:**
- **Backend applications** read secrets at runtime from environment variables ← Secure
- **Frontend applications** must embed secrets in client-side code ← Inherent exposure

### 2.2 Solution: Distinguishing True Secrets vs. Public Configuration

**True Secrets** (❌ NEVER embed in frontend):
- Database passwords
- Private API keys (with create/delete permissions)
- Admin authentication tokens
- Encryption private keys

**Public Configuration** (✅ Safe to embed):
- API identifiers / project IDs
- Public authentication endpoints
- Rate limit thresholds
- Feature flags

**Firebase Credentials** (🟡 Hybrid):
- `apiKey`, `projectId`, `authDomain` → Public (identifiers)
- `privateKey` → Never in frontend
- `serviceAccountEmail` → Public for read operations

### 2.3 The Injection Strategy

Rather than storing secrets in `.env.production` files (tracked in git), we:

1. **Commit placeholders** to the repository:
   ```json
   {
     "apiKey": "__FIREBASE_API_KEY__",
     "projectId": "__FIREBASE_PROJECT_ID__"
   }
   ```

2. **Store actual values** in GitHub Repository Secrets (encrypted at rest)

3. **Inject at build time** using a Python script that treats the file as a literal string object (not subject to shell escaping issues)

4. **Deploy the final artifact** with real values embedded

---

## 3. Security Model: OpenID Connect (OIDC)

### 3.1 Traditional Approach (Deprecated)

**What we're moving AWAY from:**
```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}  # ⚠️ Long-lived, global scope
```

**Problems:**
- ❌ Token persists for 90+ days
- ❌ If leaked, attacker has full repository access
- ❌ No way to limit permissions to GitHub Pages deployment only
- ❌ Rotation requires manual update

### 3.2 Modern Approach: OIDC (Recommended)

**What we're using NOW:**
```yaml
permissions:
  id-token: write  # GitHub generates short-lived JWT
```

**How it works:**

```
┌──────────────────────────────────────┐
│ GitHub Actions Runner                │
│ (Ephemeral VM)                       │
└──────────┬───────────────────────────┘
           │
           │ 1. Request JWT Token
           │    (valid for 5-15 minutes)
           │
           ▼
┌──────────────────────────────────────┐
│ GitHub's OIDC Provider               │
│ (signs token with private key)       │
└──────────┬───────────────────────────┘
           │
           │ 2. Return signed JWT
           │    Claims:
           │    - repository: IshanDigra/magic-pouch
           │    - ref: main
           │    - sha: abc123...
           │    - exp: <now + 15 minutes>
           │
           ▼
┌──────────────────────────────────────┐
│ GitHub Pages Service                 │
│ (verifies JWT signature)             │
└──────────┬───────────────────────────┘
           │
           │ 3. If valid: Accept deployment
           │    If invalid: Reject
           │
           ▼
    Artifact deployed to CDN
```

**Benefits:**
- ✅ Token expires in 15 minutes (time-bound)
- ✅ Cryptographically tied to specific repo + commit
- ✅ Cannot be used for anything else (Pages-only scope)
- ✅ Zero additional secrets to manage
- ✅ Audit trail: each deployment is cryptographically signed

---

## 4. Secret Injection: Why Python Over Shell Tools

### 4.1 Comparative Analysis

#### Using `sed` (❌ Fragile)

```bash
# ⚠️ FAILS if secret contains special characters
sed -i "s/__API_KEY__/$API_KEY/g" config.json

# Example: If API_KEY contains "/", "$", or "\""
# API_KEY="path/to/key$123\with\slashes"
# Result: sed fails with "unterminated s command"
```

#### Using `envsubst` (⚠️ Limited)

```bash
# Replaces EVERY ${VAR} in the file indiscriminately
envsubst < config.template.json > config.json

# ⚠️ Problem: If your code has template literals...
# Original: templateString = `Hello ${name}`
# After envsubst (if name isn't set): `Hello `  ← BREAKS CODE
```

#### Using Python (✅ Robust)

```python
# String.replace() treats both strings as LITERAL objects
# No character interpretation: $ is just $, / is just /
content = content.replace("__API_KEY__", secret_value)

# Works with ANY secret content:
# API_KEY = "p@ss/word$123\\complex"
# ✅ Correctly embedded without escaping
```

### 4.2 Python Script Architecture

```python
class SecretInjector:
    def inject_file(self, file_path, token_map):
        # 1. Validation: Does file exist?
        # 2. Read: Load with UTF-8 encoding (Unicode safe)
        # 3. Replace: .replace() method (literal string matching)
        # 4. Atomic Write: Use temp file + rename (prevents partial writes)
        # 5. Verify: Check operation succeeded
```

**Key advantages:**
- Atomic operations (temp file + rename)
- No shell subprocess spawning (no injection vulnerabilities)
- UTF-8 Unicode support (international characters safe)
- Comprehensive error handling
- Audit trail with detailed logging
- Cross-platform (Windows, macOS, Linux)

---

## 5. Least Privilege Permission Model

### 5.1 Explicit Permission Scoping

```yaml
permissions:
  contents: read       # ✅ Checkout code only
  pages: write         # ✅ Deploy to Pages only
  id-token: write      # ✅ Generate OIDC token only
  # All other permissions: REVOKED by default
```

**Defense mechanism:**
If a malicious npm package were installed during `npm ci`, it could:
- ❌ CANNOT modify the repository (no `contents: write`)
- ❌ CANNOT modify issues/PRs (no `issues: write`)
- ❌ CANNOT trigger other workflows (no `actions: write`)
- ✅ CAN only deploy to GitHub Pages

### 5.2 Environment Protection Rules

In GitHub Settings, you can configure:

```
Settings → Environments → github-pages
  ├─ Deployment branches: main only
  ├─ Required reviewers: [team members]
  └─ Deployment secrets: [encrypted vars]
```

**Effect:** Before deploying, GitHub blocks the workflow until approved.

---

## 6. Supply Chain Security: SHA-Pinned Actions

### 6.1 Why Pinning Matters

**Version tag is mutable:**
```yaml
uses: actions/checkout@v4  # v4 tag can be moved by owner
```

**Threat scenario:**
1. Attacker compromises `actions/checkout` repository
2. Moves `v4` tag to malicious commit
3. Your workflow runs the malicious code
4. Your deployment is compromised

### 6.2 SHA Pinning (Immutable Reference)

```yaml
uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
```

**SHA is cryptographically immutable:**
- Cannot be changed without breaking the hash
- Guarantees the exact commit version
- Provides audit trail

**How to pin:**
```bash
# Find the commit SHA for a version
gh api repos/actions/checkout releases --jq '.[].tag_name' | head -5

# Or manually in GitHub UI:
# 1. Go to GitHub repo
# 2. Click "Releases"
# 3. Find version, click commit hash
# 4. Copy the SHA from the URL
```

---

## 7. Implementation: Configuration Files

### 7.1 `.github/workflows/deploy.yml`

**Key features:**
- Two-job pipeline (validate, build)
- SHA-pinned actions for supply chain security
- OIDC-based GitHub Pages authentication
- Python 3.11 for secret injection
- Comprehensive security checklist in output

### 7.2 `scripts/inject_secrets.py`

**Responsibilities:**
- Read configuration file
- Iterate through token map (placeholders → env vars)
- Replace with literal string matching (Python's `.replace()`)
- Atomic write (temp file + rename)
- Detailed audit logging

### 7.3 `config.json` (Template)

**Structure:**
```json
{
  "apiKey": "__FIREBASE_API_KEY__",        // ← Placeholder
  "projectId": "__FIREBASE_PROJECT_ID__",  // ← Placeholder
  "firewall": { ... }                      // ← Real config
}
```

**Lifecycle:**
1. Developer commits `config.json` with placeholders
2. CI/CD checks out repository
3. Python script replaces placeholders with secrets
4. Build/minify proceeds with real values
5. Final artifact deployed to GitHub Pages

---

## 8. Operational Procedures

### 8.1 Initial Setup

1. **Create GitHub Secrets** (Settings → Secrets and variables → Actions):
   ```
   FIREBASE_API_KEY = xxxxxxx
   FIREBASE_PROJECT_ID = xxxxxxx
   FIREBASE_AUTH_DOMAIN = xxxxxxx
   FIREBASE_STORAGE_BUCKET = xxxxxxx
   FIREBASE_MESSAGING_SENDER_ID = xxxxxxx
   FIREBASE_APP_ID = xxxxxxx
   ```

2. **Enable GitHub Pages** (Settings → Pages):
   - Source: `GitHub Actions`

3. **Push code with placeholders:**
   ```bash
   git add .github/workflows/deploy.yml
   git add scripts/inject_secrets.py
   git add config.json
   git commit -m "ci: implement enterprise CI/CD with secret injection"
   git push origin main
   ```

### 8.2 Monitoring Deployments

**View workflow runs:**
```
https://github.com/IshanDigra/magic-pouch/actions
```

**Check logs:**
1. Click workflow run
2. Click job (validate, build, deploy)
3. Expand steps
4. Look for ✅ or ❌ indicators

**Secret rotation:**
1. Go to Settings → Secrets
2. Update secret value
3. Next workflow run will use new value
4. No code changes required ✅

### 8.3 Troubleshooting

**Workflow fails at validation:**
- Check `config.json` JSON syntax: `python3 -m json.tool config.json`
- Verify `index.html` exists in repo root

**Deployment fails with 404:**
- Verify GitHub Pages enabled (Settings → Pages → Source: GitHub Actions)
- Check artifact uploaded successfully (expand "Upload Pages artifact" step)
- Wait 2-3 minutes for DNS propagation

**Secrets not injected:**
- Verify environment variables exist in GitHub Secrets
- Check Python script logs (expand "Run injection" step)
- Ensure placeholder names match exactly (case-sensitive)

---

## 9. Security Checklist

- [ ] Secrets stored in GitHub Repository Secrets (encrypted at rest)
- [ ] Actions pinned to specific commit SHA (supply chain security)
- [ ] Permissions scoped to read + pages:write + id-token:write only
- [ ] OIDC enabled for Pages deployment (no long-lived tokens)
- [ ] `config.json` tracked in version control (with placeholders)
- [ ] Actual secrets values NEVER committed to git
- [ ] Python injection script prevents shell escape vulnerabilities
- [ ] Artifact immutability enforced by GitHub Pages
- [ ] `.gitignore` includes `*.env*` files
- [ ] Deployment logs do NOT expose secret values (masking active)

---

## 10. Conclusion

This architecture represents the convergence of:
- **Automation** (eliminate manual deployments)
- **Security** (OIDC, least privilege, supply chain hardening)
- **Reliability** (atomic operations, immutable artifacts)
- **Compliance** (Twelve-Factor App, environment variable management)

The result is a production-grade CI/CD pipeline suitable for enterprise web applications.

---

**Document Version:** 1.0  
**Last Updated:** January 15, 2026  
**Status:** Production Ready ✅
