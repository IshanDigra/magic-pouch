# Enterprise CI/CD Deployment Checklist
## Magic-Pouch (SnippetKeeper)

---

## Phase 1: Pre-Deployment Setup

### 1.1 Repository Configuration

- [ ] Clone repository locally
  ```bash
  git clone https://github.com/IshanDigra/magic-pouch.git
  cd magic-pouch
  ```

- [ ] Verify core files exist
  ```bash
  ls -la config.json index.html .github/workflows/deploy.yml scripts/inject_secrets.py
  ```

- [ ] Validate JSON syntax
  ```bash
  python3 -m json.tool config.json
  ```

### 1.2 GitHub Repository Settings

- [ ] Go to: `https://github.com/IshanDigra/magic-pouch/settings`

- [ ] Navigate to **Pages** section
  - [ ] Source: Select `GitHub Actions`
  - [ ] Custom domain: (optional)
  - [ ] HTTPS: Enabled

- [ ] Navigate to **Environments** section
  - [ ] Create environment: `github-pages`
  - [ ] (Optional) Set deployment branches to `main` only
  - [ ] (Optional) Set required reviewers

### 1.3 GitHub Secrets Configuration

- [ ] Go to: `https://github.com/IshanDigra/magic-pouch/settings/secrets/actions`

- [ ] Create the following secrets:

  **Secret Name:** `FIREBASE_API_KEY`
  ```
  Value: [Your Firebase API Key]
  ```
  - [ ] Created

  **Secret Name:** `FIREBASE_AUTH_DOMAIN`
  ```
  Value: [Your Firebase Auth Domain]
  ```
  - [ ] Created

  **Secret Name:** `FIREBASE_PROJECT_ID`
  ```
  Value: [Your Firebase Project ID]
  ```
  - [ ] Created

  **Secret Name:** `FIREBASE_STORAGE_BUCKET`
  ```
  Value: [Your Firebase Storage Bucket]
  ```
  - [ ] Created

  **Secret Name:** `FIREBASE_MESSAGING_SENDER_ID`
  ```
  Value: [Your Firebase Messaging Sender ID]
  ```
  - [ ] Created

  **Secret Name:** `FIREBASE_APP_ID`
  ```
  Value: [Your Firebase App ID]
  ```
  - [ ] Created

- [ ] Verify all secrets appear in the list (masked with asterisks)

---

## Phase 2: Configuration Validation

### 2.1 Local Testing

- [ ] Verify Python script syntax
  ```bash
  python3 -m py_compile scripts/inject_secrets.py
  ```

- [ ] Test secret injection locally (optional)
  ```bash
  # Create a test copy
  cp config.json config.test.json
  
  # Set test environment variables
  export FIREBASE_API_KEY="test-key"
  export FIREBASE_PROJECT_ID="test-project"
  export FIREBASE_AUTH_DOMAIN="test.firebaseapp.com"
  export FIREBASE_STORAGE_BUCKET="test-bucket"
  export FIREBASE_MESSAGING_SENDER_ID="12345"
  export FIREBASE_APP_ID="test-app"
  
  # Note: Full test requires running inject_secrets.py
  # Clean up
  rm config.test.json
  unset FIREBASE_API_KEY FIREBASE_PROJECT_ID FIREBASE_AUTH_DOMAIN
  ```

### 2.2 GitHub Actions Validation

- [ ] Go to: `https://github.com/IshanDigra/magic-pouch/actions`

- [ ] Check for any existing workflow runs
  - [ ] If failed: Review logs to identify issues
  - [ ] If none exist: Proceed to Phase 3

---

## Phase 3: Deployment Trigger

### 3.1 Automatic Trigger (Git Push)

- [ ] Commit changes
  ```bash
  git add .
  git commit -m "feat: implement enterprise CI/CD deployment"
  ```

- [ ] Push to main branch
  ```bash
  git push origin main
  ```

- [ ] Workflow triggers automatically
  ```
  GitHub detects push to main
  → Workflow starts
  → Check Actions tab for status
  ```

### 3.2 Manual Trigger (workflow_dispatch)

If you prefer not to push changes:

- [ ] Go to: `https://github.com/IshanDigra/magic-pouch/actions`

- [ ] Click **"Production Deployment Pipeline"** workflow

- [ ] Click **"Run workflow"** button

- [ ] Select branch: `main`

- [ ] Click **"Run workflow"**

---

## Phase 4: Deployment Monitoring

### 4.1 Workflow Status Tracking

**Monitor in real-time:**

```
https://github.com/IshanDigra/magic-pouch/actions
```

- [ ] Job 1: **Validate** (✅ or ❌)
  - [ ] Check config.json syntax: PASSED
  - [ ] Verify index.html exists: PASSED
  - [ ] Validate firewall rules: PASSED

- [ ] Job 2: **Build** (✅ or ❌)
  - [ ] Setup Python 3.11: PASSED
  - [ ] Configure GitHub Pages: PASSED
  - [ ] Build application: PASSED
  - [ ] Upload Pages artifact: PASSED
  - [ ] Deploy to GitHub Pages: PASSED
  - [ ] Deployment Summary: PASSED

**Expected duration:** 2-5 minutes

### 4.2 Detailed Log Review

- [ ] Click on the workflow run

- [ ] For each job, expand the steps and verify:
  - [ ] No error messages (✅ green checkmarks)
  - [ ] Security checklist passed
  - [ ] Artifact uploaded successfully

**Key output to look for:**
```
═══════════════════════════════════════════════════════
✓ DEPLOYMENT SUCCESSFUL
═══════════════════════════════════════════════════════
Project: magic-pouch (SnippetKeeper)
Deployment Target: GitHub Pages
Live URL: https://IshanDigra.github.io/magic-pouch
```

### 4.3 Pages Deployment Status

- [ ] Go to: `https://github.com/IshanDigra/magic-pouch/settings/pages`

- [ ] Under **"Deployment history"**, verify:
  - [ ] Latest deployment status: **Active** (green)
  - [ ] URL: `https://IshanDigra.github.io/magic-pouch`

---

## Phase 5: Post-Deployment Verification

### 5.1 Site Accessibility

- [ ] Open in browser: `https://IshanDigra.github.io/magic-pouch`

- [ ] Verify application loads
  - [ ] No 404 error
  - [ ] No console errors (open DevTools: F12)
  - [ ] Responsive design works on mobile

- [ ] Test core functionality
  - [ ] Create a folder
  - [ ] Add a note
  - [ ] Verify data persists (refresh page)
  - [ ] Export data
  - [ ] Test sync feature

### 5.2 Security Validation

- [ ] Check HTTPS is active
  ```bash
  curl -I https://IshanDigra.github.io/magic-pouch
  # Should return: HTTP/2 200
  ```

- [ ] Verify security headers (F12 DevTools)
  - [ ] Open Network tab
  - [ ] Click on main document request
  - [ ] Check Response Headers for:
    - `Strict-Transport-Security`
    - `X-Content-Type-Options: nosniff`
    - `X-Frame-Options: SAMEORIGIN`

- [ ] Verify secrets NOT exposed
  - [ ] Open DevTools Console
  - [ ] Inspect `window.__firebase_config` or similar
  - [ ] Confirm actual keys are present (not placeholders like `__FIREBASE_API_KEY__`)

### 5.3 Performance Baseline

- [ ] Check page load performance
  ```
  DevTools → Lighthouse
  → Run analysis
  → Document scores:
    - Performance: ____
    - Accessibility: ____
    - Best Practices: ____
    - SEO: ____
  ```

- [ ] Record metrics for future comparison

---

## Phase 6: Operational Handoff

### 6.1 Team Communication

- [ ] Notify team that deployment is live

- [ ] Share key URLs:
  ```
  Live Site:     https://IshanDigra.github.io/magic-pouch
  Repository:    https://github.com/IshanDigra/magic-pouch
  Actions:       https://github.com/IshanDigra/magic-pouch/actions
  Settings:      https://github.com/IshanDigra/magic-pouch/settings
  ```

### 6.2 Documentation Updates

- [ ] Update README.md with deployment status
  ```markdown
  ## Deployment Status
  
  ✅ **Live**: https://IshanDigra.github.io/magic-pouch
  ✅ **CI/CD**: GitHub Actions (Enterprise-grade)
  ✅ **Last Deploy**: [DATE]
  ✅ **Status**: Production Ready
  ```

- [ ] Document any customizations made

### 6.3 Monitoring Setup

- [ ] Subscribe to workflow notifications
  ```
  https://github.com/IshanDigra/magic-pouch/settings/notifications
  → Select: "Send notifications for: Failed workflows only"
  ```

- [ ] Set up alerting (optional):
  - [ ] GitHub mobile app for instant notifications
  - [ ] Email notifications for failures

---

## Phase 7: Troubleshooting

### 7.1 Workflow Fails at "Validate"

**Error:** `config.json has invalid JSON syntax`

**Solution:**
```bash
# Check JSON validity
python3 -m json.tool config.json

# Fix any syntax errors (quotes, commas, brackets)
# Re-push
git add config.json
git commit -m "fix: correct JSON syntax"
git push origin main
```

### 7.2 Workflow Fails at "Deploy"

**Error:** `Deployment failed: artifact not found`

**Solution:**
1. Check that `index.html` exists in repo root
   ```bash
   ls -la index.html
   ```
2. Verify GitHub Pages source is set to "GitHub Actions"
3. Re-run workflow manually

### 7.3 Site Shows 404 Error

**Error:** "There isn't a GitHub Pages site here"

**Solution:**
1. Go to Settings → Pages
2. Verify Source is `GitHub Actions`
3. Wait 2-3 minutes for DNS propagation
4. Clear browser cache (Ctrl+Shift+Del)
5. Try incognito window

### 7.4 Secrets Not Injected

**Error:** `__FIREBASE_API_KEY__` appears in loaded config

**Solution:**
1. Verify all secrets exist in GitHub Settings → Secrets
2. Check secret names match exactly (case-sensitive):
   ```
   FIREBASE_API_KEY (not firebase_api_key)
   FIREBASE_PROJECT_ID (not firebase_project_id)
   ...
   ```
3. Review Python script logs in Actions tab
4. Re-run workflow

---

## Phase 8: Ongoing Maintenance

### 8.1 Regular Checks

**Weekly:**
- [ ] Verify site is accessible
- [ ] Check Actions tab for any failed runs
- [ ] Review any error messages

**Monthly:**
- [ ] Update dependencies (if applicable)
- [ ] Review security logs
- [ ] Check for GitHub platform updates

### 8.2 Secret Rotation

**When rotating secrets:**

1. Go to Settings → Secrets
2. Click secret to update
3. Click "Update" button
4. Enter new value
5. Next workflow run will use new value (no code changes needed)

### 8.3 Performance Monitoring

- [ ] Track page load times
- [ ] Monitor deployment times
- [ ] Review error logs monthly

---

## Phase 9: Rollback Procedure

**If deployment causes issues:**

1. **Identify problematic commit:**
   ```bash
   git log --oneline -10
   # Find the commit before the issue
   ```

2. **Revert to previous version:**
   ```bash
   git revert [bad-commit-sha]
   git push origin main
   # Workflow automatically re-deploys
   ```

3. **Or reset to specific commit:**
   ```bash
   git reset --hard [good-commit-sha]
   git push --force origin main  # ⚠️ Use with caution!
   ```

4. **Monitor rollback:**
   - [ ] Check Actions tab for new workflow run
   - [ ] Wait for deployment to complete
   - [ ] Verify site restored to working state

---

## Sign-Off Checklist

- [ ] **Configuration**: All secrets created and verified
- [ ] **Deployment**: Workflow runs successfully
- [ ] **Validation**: Site loads without errors
- [ ] **Security**: HTTPS active, headers correct, secrets not exposed
- [ ] **Testing**: Core features work as expected
- [ ] **Documentation**: README and guides updated
- [ ] **Monitoring**: Team notified, alerts configured
- [ ] **Maintenance**: Rollback procedure documented and tested

---

## Support Resources

| Issue | Resource |
|-------|----------|
| Workflow Help | [GitHub Actions Docs](https://docs.github.com/en/actions) |
| GitHub Pages | [Pages Documentation](https://docs.github.com/en/pages) |
| Secret Management | [Secrets Docs](https://docs.github.com/en/actions/security-guides/encrypted-secrets) |
| OIDC | [OIDC Documentation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect) |
| Python Scripting | [Python Docs](https://docs.python.org/3/) |

---

**Deployment Date:** _______________  
**Deployed By:** _______________  
**Status:** ✅ Production Ready  
**Last Updated:** January 15, 2026
