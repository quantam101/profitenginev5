# OCI API Credentials Setup for GitHub Actions

## Required for Automated Recovery

The `oci-auto-recovery.yml` workflow needs OCI API credentials to automatically restart the instance. Without these, manual recovery will still be required.

---

## Step 1: Get OCI API Credentials

### 1a. Find Your Credentials
1. Log into **console.oracle.com**
2. Click **Profile** (top-right) → **User Settings**
3. Scroll to **API Keys** section
4. If you have an API key, note the:
   - **Fingerprint** (alphanumeric like `a1:b2:c3:...`)
   - **Private Key** (copy the full PEM content)

### 1b. Generate New API Key (if needed)
1. Same location, click **Add API Key**
2. Select **Generate API Key Pair**
3. **DOWNLOAD** the private key immediately (you can't retrieve it later)
4. Copy the fingerprint from the console

### 1c. Get Your OCIDs
1. Go to **Tenancy Details** (top menu)
2. Copy:
   - **Tenancy OCID** (long string starting with `ocid1.tenancy`)
   - **Region** (e.g., `us-phoenix-1`)

3. Go to **Identity → Users**
4. Click on your username
5. Copy **User OCID** (starts with `ocid1.user`)

6. Go to **Compute → Instances**
7. Click on `profitenginev5-runtime`
8. Copy **Compartment OCID** (starts with `ocid1.compartment`)

---

## Step 2: Add Secrets to GitHub

1. Go to **GitHub repo** → **Settings** → **Secrets and variables** → **Actions**
2. Add these secrets:

| Secret Name | Value | Source |
|-------------|-------|--------|
| `OCI_USER_OCID` | `ocid1.user.oc1...` | User Settings |
| `OCI_TENANCY_OCID` | `ocid1.tenancy.oc1...` | Tenancy Details |
| `OCI_COMPARTMENT_OCID` | `ocid1.compartment.oc1...` | Instance Details |
| `OCI_REGION` | `us-phoenix-1` | Tenancy Details |
| `OCI_FINGERPRINT` | `a1:b2:c3:...` | API Keys section |
| `OCI_PRIVATE_KEY` | `-----BEGIN PRIVATE KEY-----...` | Downloaded PEM file |

### How to Add a Secret:
1. Click **New repository secret**
2. **Name:** `OCI_USER_OCID`
3. **Secret:** Paste the value
4. Click **Add secret**
5. Repeat for all 6 secrets

---

## Step 3: Verify Setup

Test the workflow:
1. Go to **Actions** → **OCI Auto-Recovery — Restart Runtime Instance**
2. Click **Run workflow** → **Dispatch** (with action="status")
3. Wait 30 seconds
4. Should see "Instance ID: ocid1.instance.oc1..." and current state
5. If it shows an error about credentials, check Secret names match exactly

---

## Step 4: Test Auto-Recovery

Once credentials are verified:

### Manual Test (Workflow Dispatch)
1. Go to **Actions** → **OCI Auto-Recovery — Restart Runtime Instance**
2. Click **Run workflow**
3. Choose action: **reboot** (soft restart)
4. Click **Run workflow**
5. Monitor the logs

### Automatic Test (Force Health Check Failure)
For production, you don't do this. But to verify the automation works:
1. The health check runs every 5 minutes
2. When it detects API is down, auto-recovery is triggered
3. Recovery workflow should restart the instance within 30 seconds
4. Instance boots and responds within 2-3 minutes

---

## Troubleshooting

### Secret Not Found
```
Error: The referenced secret does not exist
```
**Fix:** Check secret name matches exactly (case-sensitive):
- `OCI_USER_OCID` (not `OCI_USER_ID` or `OCI_USERID`)

### Authentication Failed
```
Error: Service error: Unauthorized
```
**Fix:** 
1. Verify OCI credentials are correct
2. Verify API key is still active (hasn't expired)
3. Regenerate API key if needed

### Instance Not Found
```
Error: Instance not found
```
**Fix:**
1. Verify instance is named exactly `profitenginev5-runtime`
2. Verify `OCI_COMPARTMENT_OCID` is correct
3. Check instance still exists in console

### Authorization Error (Denied)
```
Error: {iam policy issue, insufficient permissions}
```
**Fix:** Your OCI user needs these permissions. Ask your OCI admin to add policy:
```
allow group <your-group> to manage instances in compartment <compartment-name>
allow group <your-group> to manage compute-instance-family in compartment <compartment-name>
```

---

## Security Notes

⚠️ **Important:**
- Never share or commit these secrets
- The private key is sensitive — keep it safe
- API keys can be rotated if compromised
- Consider using temporary credentials if this is shared infrastructure

---

## Next Steps

Once OCI credentials are configured:

1. ✅ Merge all the automated recovery workflows to `main`
2. ✅ Health check will run every 5 minutes
3. ✅ When Runtime API goes down, auto-recovery triggers automatically
4. ✅ Instance reboots within 30 seconds
5. ✅ API responds within 2-3 minutes
6. ✅ Newsletters/digests resume automatically

---

**Configured by:** [Your Name]
**Date:** [Setup Date]
**Status:** [✅ Working / ⚠️ Pending Credentials]
