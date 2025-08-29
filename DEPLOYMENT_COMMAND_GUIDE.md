# Deployment Command Guide

## ⚠️ CRITICAL: Use the Correct Deployment Script

The error you're encountering is because you're using the **wrong deployment script**.

## ❌ Wrong Command (Causes the Error)
```bash
./deploy.sh -p YOUR_PROJECT_ID
```
**This deploys to Cloud Functions Gen 2 and causes:**
- Container Healthcheck failed
- Missing requirements.txt in build context
- Functions Framework complexity issues

## ✅ Correct Command (Works)
```bash
./deploy-cloudrun.sh -p YOUR_PROJECT_ID
```
**This deploys to Cloud Run and:**
- ✅ Uses standard Docker containers
- ✅ Automatically generates requirements.txt if needed
- ✅ Direct FastAPI deployment without wrapper complexity
- ✅ Proper port binding and health checks

## Quick Verification

Check which script you're using:
```bash
# Wrong (causes errors):
ls -la deploy.sh

# Correct (works):
ls -la deploy-cloudrun.sh
```

## File Structure Comparison

| Cloud Functions (`deploy.sh`) | Cloud Run (`deploy-cloudrun.sh`) |
|------------------------------|----------------------------------|
| Uses Functions Framework | Uses direct FastAPI |
| Requires complex wrappers | Standard container deployment |
| Has build context issues | Robust build process |
| Container health check fails | Standard HTTP health checks |

## To Fix the Error

**Simply change your deployment command from:**
```bash
./deploy.sh -p YOUR_PROJECT_ID
```

**To:**
```bash
./deploy-cloudrun.sh -p YOUR_PROJECT_ID
```

That's it! The Cloud Run approach resolves all the container startup and requirements.txt issues.

## Verification

Both scripts exist in your project:
```bash
$ ls -la deploy*.sh
-rwxrwxr-x  1 user user 12345 date deploy.sh          # ❌ Cloud Functions (problematic)
-rwxrwxr-x  1 user user  5713 date deploy-cloudrun.sh # ✅ Cloud Run (working)
```

Use the **Cloud Run** script for reliable deployment! 🚀