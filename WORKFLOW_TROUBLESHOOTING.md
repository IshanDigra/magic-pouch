# Workflow Troubleshooting Guide

## Issue: Workflows Stuck in "Queued" Status ❌

### Root Causes & Solutions

### 1. **Missing or Broken Dependencies**

**Symptoms:**
- All runs show "Queued" status indefinitely
- No error messages visible
- Workflow never progresses to "Running"

**Solutions:**
```bash
# Verify config.json exists and is valid
cat config.json

# Validate JSON syntax
python3 -m json.tool config.json

# Check if package-lock.json is needed
ls -la package-lock.json package.json 2>/dev/null || echo "No npm dependencies"
```

✅ **What we fixed:**
- Removed `hashFiles('**/package-lock.json')` that was causing silent failures
- Added explicit timeout values to prevent indefinite waiting
- Simplified validation logic to use only shell/Python (no Node dependency)

---

### 2. **GitHub Pages Configuration Not Set**

**Check your repository settings:**

1. Go to: **Settings → Pages**
2. Verify:
   - [x] **Build and deployment** → Source: `GitHub Actions`
   - [x] **Branch**: `main` (or your default branch)

**If not set:**
```bash
# You may need to manually enable GitHub Pages
# GitHub Actions will auto-configure this, but verify in repo settings
```

---

### 3. **Concurrent Workflow Locks**

**Previous config:**
```yaml
concurrency:
  group: "pages"
  cancel-in-progress: true  # ← This cancels running jobs
```

**Fixed config:**
```yaml
concurrency:
  group: "pages"
  cancel-in-progress: false  # ← Allows jobs to complete
```

💡 **Why this matters:** If previous runs were cancelled abruptly, new runs might get stuck waiting.

---

### 4. **Action Version Conflicts**

**Issue:** Outdated action versions might have bugs

**Verification:**
```yaml
# We use these versions:
uses: actions/checkout@v4           # Latest stable
uses: actions/configure-pages@v5    # Latest stable
uses: actions/upload-pages-artifact@v3  # Latest
uses: actions/deploy-pages@v4       # Latest
```

✅ All pinned to latest major versions

---

## Manual Fix Steps

### Step 1: Clear Workflow Queue

```bash
# Go to Actions tab → build-and-deploy
# Click "..." on any queued run
# Select "Cancel workflow run"

# Or use GitHub CLI:
gh workflow run deploy.yml --ref main
```

### Step 2: Verify Configuration

```bash
# Test locally (requires act - GitHub Actions emulator)
act -j validate
act -j build

# Or manually check:
python3 -m json.tool config.json  # Check JSON syntax
ls -la index.html                 # Verify deployment files exist
```

### Step 3: Trigger New Workflow Run

**Option A: Push a new commit**
```bash
git add .
git commit -m "trigger: workflow rerun"
git push origin main
```

**Option B: Manual dispatch**
1. Go to: **Actions → build-and-deploy**
2. Click **"Run workflow"** button
3. Select branch `main`
4. Click **"Run workflow"**

**Option C: Re-run from GitHub UI**
1. Click on queued workflow run
2. Click **"Re-run all jobs"** or **"Re-run failed jobs"**

---

## Verification Checklist

### Before triggering workflow:
- [ ] `config.json` exists and has valid JSON
- [ ] Firebase keys are present in config.json
- [ ] `index.html` exists in repository root
- [ ] `.github/workflows/deploy.yml` is valid YAML
- [ ] No syntax errors in workflow file

### After workflow runs:
- [ ] "Validate Configuration" job completes with ✓
- [ ] "Build and Deploy" job completes with ✓
- [ ] GitHub Pages URL is accessible:
  - `https://IshanDigra.github.io/magic-pouch`
- [ ] Site loads without 404 errors

---

## Common Errors & Fixes

### Error: "Config file not found"
```bash
# Solution: Ensure config.json exists
cat > config.json << 'EOF'
{
  "apiKey": "AIzaSyD3GZnCEWotlYVHElhh3c5RmCKYjzSdhX8",
  "authDomain": "magic-pouch.firebaseapp.com",
  "projectId": "magic-pouch",
  "storageBucket": "magic-pouch.firebasestorage.app",
  "messagingSenderId": "816300585480",
  "appId": "1:816300585480:web:0ead89292305defb2c97bd"
}
EOF

git add config.json
git commit -m "fix: add config.json"
git push origin main
```

### Error: "Invalid JSON in config.json"
```bash
# Solution: Validate and fix JSON
python3 -m json.tool config.json

# Look for:
# - Missing commas
# - Trailing commas
# - Unquoted keys
# - Invalid escape sequences
```

### Error: "Missing Firebase keys"
```bash
# Solution: Check required keys exist
python3 << 'EOF'
import json
with open('config.json') as f:
    config = json.load(f)
    
required = ['apiKey', 'authDomain', 'projectId', 'storageBucket', 'messagingSenderId', 'appId']
for key in required:
    if key in config:
        print(f"✓ {key}")
    else:
        print(f"✗ MISSING: {key}")
EOF
```

### Error: "Pages artifact upload failed"
```bash
# Solution: Verify deployment files exist
ls -la index.html      # Main site file
ls -la config.json     # Config file
ls -la .github/        # Workflows exist

# If missing, add them:
git add index.html config.json .github/workflows/
git commit -m "fix: add deployment files"
git push origin main
```

---

## Debug: View Workflow Logs

1. Go to: **GitHub repo → Actions tab**
2. Click on the workflow run (build-and-deploy #X)
3. Click on job name (validate or build)
4. Expand each step to see detailed output
5. Look for:
   - ✓ (green checkmark) = Success
   - ✗ (red X) = Failure
   - Yellow ⚠ = Warning

**Key things to check:**
```
Validate Configuration
  └─ Checkout code ..................... ✓ or ✗
  └─ Validate config.json ............ ✓ or ✗

Build and Deploy
  └─ Checkout code ..................... ✓ or ✗
  └─ Configure Pages ................... ✓ or ✗
  └─ Upload artifact ................... ✓ or ✗
  └─ Deploy to GitHub Pages ......... ✓ or ✗
```

---

## Force Reset Workflow State

If nothing works, perform a complete reset:

```bash
# 1. Delete the workflow file temporarily
git rm .github/workflows/deploy.yml
git commit -m "temp: remove workflow"
git push origin main

# Wait 1 minute for GitHub to sync

# 2. Re-add the fixed workflow
git checkout HEAD~1 -- .github/workflows/deploy.yml
git commit -m "fix: restore optimized workflow"
git push origin main
```

---

## Monitoring Going Forward

### Set up notifications:
1. **Settings → Notifications**
2. Enable: "Workflows"
3. Select: "Send notifications for: Failed workflows only" or "All workflows"

### Regular health checks:
- [ ] Check Actions tab weekly
- [ ] Verify deployments succeed
- [ ] Monitor GitHub Pages uptime
- [ ] Review workflow logs for warnings

---

## Still Having Issues?

### Get detailed info:
```bash
# View workflow file
cat .github/workflows/deploy.yml | head -50

# Check repository settings
gh repo view IshanDigra/magic-pouch --json name,isPrivate,hasPages

# View recent commits
git log --oneline -10
```

### Escalation:
1. Check GitHub Status: https://www.githubstatus.com
2. Review GitHub Actions limits: https://docs.github.com/en/actions/learn-github-actions/usage-limits-billing-and-administration
3. Open GitHub issue if service is down

---

**Updated:** Jan 15, 2026
**Last Fix:** Simplified workflow to remove package.json dependency, added explicit timeouts, changed `cancel-in-progress: false`
