# GitHub Actions Workflow & Firewall Configuration Setup

## Overview

This document outlines the complete setup for GitHub Actions CI/CD pipeline and firewall security configuration for the magic-pouch project.

## GitHub Actions Workflow

### Workflow File: `.github/workflows/deploy.yml`

The workflow is configured with the following stages:

#### 1. **Triggers**
- Push to `main` branch
- Pull requests to `main` branch
- Manual workflow dispatch

#### 2. **Jobs**

##### Job 1: `validate-config`
- Validates `config.json` structure
- Checks for required Firebase configuration keys
- Verifies firewall settings are properly configured
- **Status**: Must pass before deployment

##### Job 2: `build-and-deploy`
- Depends on successful `validate-config` job
- Setup Node.js environment
- Cache npm dependencies
- Run security and firewall validation checks
- Configure GitHub Pages
- Upload artifacts
- Deploy to GitHub Pages

### Permissions
```yaml
permissions:
  contents: read         # Read repository contents
  pages: write          # Write to GitHub Pages
  id-token: write       # OIDC token generation
  checks: write         # Write check results
  pull-requests: write  # Write PR comments
```

### Running the Workflow

**Automatic Triggers:**
```bash
# Workflow runs automatically on push to main
git push origin main

# Workflow runs on PRs to main
git push origin feature-branch
# Create PR to main
```

**Manual Trigger:**
1. Go to Actions tab
2. Select "build-and-deploy"
3. Click "Run workflow"
4. Select branch
5. Click "Run workflow"

## Firewall Configuration

### Configuration File: `config.json`

#### Firebase Credentials (Required)
```json
{
  "apiKey": "YOUR_API_KEY",
  "authDomain": "YOUR_AUTH_DOMAIN",
  "projectId": "YOUR_PROJECT_ID",
  "storageBucket": "YOUR_STORAGE_BUCKET",
  "messagingSenderId": "YOUR_MESSAGING_SENDER_ID",
  "appId": "YOUR_APP_ID"
}
```

#### Firewall Configuration

##### 1. **Basic Firewall Settings**
```json
"firewall": {
  "enabled": true,  // Enable/disable firewall globally
  "rules": {
    "blockMaliciousPatterns": true,     // Pattern-based filtering
    "validateOrigin": true,              // Validate request origin
    "rateLimitEnabled": true,            // Enable rate limiting
    "corsEnabled": true                  // Enable CORS
  }
}
```

##### 2. **Rate Limiting**
```json
"rateLimiting": {
  "requestsPerMinute": 60,   // 60 requests per minute per IP
  "requestsPerHour": 1000,    // 1000 requests per hour per IP
  "burstLimit": 10            // Allow 10 burst requests
}
```

##### 3. **CORS Configuration**
```json
"cors": {
  "allowedOrigins": [
    "https://IshanDigra.github.io",      // GitHub Pages
    "https://magic-pouch.firebaseapp.com", // Firebase hosting
    "http://localhost:3000",              // Local development
    "http://localhost:5000"               // Alternative local port
  ],
  "allowedMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  "allowCredentials": true                // Allow cookie/auth headers
}
```

##### 4. **Content Security Policy**
```json
"contentSecurity": {
  "allowScripts": true,
  "allowStyles": true,
  "allowFonts": true,
  "blockExternalResources": false,
  "enableSubresourceIntegrity": true    // SRI for external resources
}
```

##### 5. **Security Headers**
```json
"securityHeaders": {
  "strictTransportSecurity": "max-age=31536000; includeSubDomains",
  "contentSecurityPolicy": "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.firebase.com; style-src 'self' 'unsafe-inline'",
  "referrerPolicy": "strict-origin-when-cross-origin",
  "xContentTypeOptions": "nosniff",
  "xFrameOptions": "SAMEORIGIN"
}
```

##### 6. **Whitelisted Domains**
```json
"whitelistedDomains": [
  "magic-pouch.firebaseapp.com",
  "magic-pouch.firebasestorage.app",
  "IshanDigra.github.io"
]
```

##### 7. **Blocklist Patterns**
```json
"blocklistPatterns": [
  "(?i)(eval|script|iframe|onerror|onload)",      // XSS patterns
  "(?i)(union.*select|drop.*table|insert.*into)", // SQL injection
  "(?i)(<script|javascript:|onerror=|onclick=)"  // Malicious HTML
]
```

##### 8. **Logging Configuration**
```json
"logging": {
  "enabled": true,
  "logLevel": "info",                    // debug, info, warn, error
  "logSecurityEvents": true,              // Log security violations
  "logRateLimitViolations": true         // Log rate limit hits
}
```

#### Environment-Specific Settings

**Production**
```json
"production": {
  "firewall": {
    "strict": true,
    "enabled": true
  },
  "https": true,
  "contentSecurityPolicyStrict": true
}
```

**Development**
```json
"development": {
  "firewall": {
    "strict": false,
    "enabled": true
  },
  "https": false,
  "allowLocalhost": true
}
```

## Implementation Guide

### Step 1: Update config.json
1. Replace Firebase credentials with your actual values
2. Review CORS allowed origins and update if needed
3. Configure rate limiting based on your requirements
4. Enable/disable firewall rules as needed

### Step 2: Test Firewall Configuration
```bash
# Validate config.json syntax
node -e "const config = require('./config.json'); console.log('✓ Valid JSON');"

# Check for required Firebase keys
node -e "const c = require('./config.json'); ['apiKey', 'projectId', 'appId'].forEach(k => {if(!c[k]) throw new Error('Missing: '+k); console.log('✓ ' + k);})"
```

### Step 3: Test Workflow Locally
```bash
# Install act (GitHub Actions runner emulator)
brew install act  # macOS
# or use Docker to run:
docker pull ghcr.io/nektos/act:latest

# Run workflow locally
act -j validate-config
act -j build-and-deploy
```

### Step 4: Deploy
```bash
# Commit changes
git add config.json .github/workflows/deploy.yml
git commit -m "setup: configure GitHub Actions workflow and firewall"

# Push to main
git push origin main

# Monitor workflow in GitHub Actions
# https://github.com/IshanDigra/magic-pouch/actions
```

## Monitoring and Maintenance

### Workflow Health
1. **Actions Tab**: Monitor workflow runs and status
2. **Logs**: Check step-by-step execution logs
3. **Artifacts**: Download deployment artifacts

### Security Monitoring
1. **Rate Limit Violations**: Check logs for repeated 429 status codes
2. **Blocked Requests**: Monitor blocked malicious patterns
3. **CORS Failures**: Track cross-origin request denials

### Best Practices

✓ **Do:**
- Keep Firebase credentials in config.json (add to .gitignore for actual keys)
- Review security headers regularly
- Monitor firewall logs for suspicious patterns
- Test CORS configuration after changes
- Keep allowedOrigins minimal and specific
- Enable rate limiting for public endpoints
- Use HTTPS in production

✗ **Don't:**
- Commit sensitive Firebase keys directly
- Disable firewall in production
- Allow wildcard origins in CORS
- Set extremely high rate limits
- Use inline scripts without CSP nonces
- Ignore security header warnings

## Troubleshooting

### Issue: Workflow Fails at Config Validation
**Solution**: 
```bash
# Validate config.json
node -e "console.log(JSON.stringify(require('./config.json'), null, 2))"
```

### Issue: CORS Errors in Browser
**Solution**: 
1. Check allowed origins in config.json
2. Verify request origin matches whitelist
3. Clear browser cache
4. Test with curl:
```bash
curl -H "Origin: https://example.com" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS https://magic-pouch.firebaseapp.com/api
```

### Issue: Rate Limiting Active
**Solution**: 
1. Check rate limit logs
2. Verify request patterns
3. Increase limits if necessary in config.json
4. Implement exponential backoff in client

## Security Checklist

- [ ] Firebase credentials configured
- [ ] Firewall enabled in production
- [ ] CORS origins whitelisted
- [ ] Security headers configured
- [ ] Rate limiting appropriate
- [ ] Content Security Policy set
- [ ] HTTPS enabled in production
- [ ] Workflow runs successfully
- [ ] Logs monitored for violations
- [ ] Config.json added to .gitignore (for real keys)

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Pages Deployment](https://docs.github.com/en/pages)
- [OWASP Security Headers](https://owasp.org/www-project-secure-headers/)
- [Firebase Security Rules](https://firebase.google.com/docs/firestore/security/get-started)
- [Content Security Policy Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review workflow logs in GitHub Actions tab
3. Verify config.json against template
4. Open an issue with logs and error messages
