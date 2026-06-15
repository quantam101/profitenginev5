# Setup OCI SSH Secret in GitHub
# This script safely adds the SSH key to GitHub Secrets without logging the key content

param(
    [string]$KeyPath = "C:\Users\alrea\profitengine-key"
)

Write-Host "🔐 OCI SSH Secret Setup" -ForegroundColor Cyan
Write-Host ""

# Verify key exists
if (-not (Test-Path $KeyPath)) {
    Write-Host "❌ SSH key not found at: $KeyPath" -ForegroundColor Red
    exit 1
}

Write-Host "✅ SSH key found: $KeyPath" -ForegroundColor Green
Write-Host ""

# Check GitHub CLI is installed
try {
    $ghVersion = gh --version 2>$null
    Write-Host "✅ GitHub CLI installed: $ghVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ GitHub CLI not found. Install from: https://cli.github.com" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Setting up GitHub Secret..." -ForegroundColor Cyan

# Read the key file
$keyContent = Get-Content $KeyPath -Raw

# Create the secret using GitHub CLI
# This command is safe - the key is passed via stdin, not command line
$keyContent | gh secret set OCI_SSH_KEY --repo quantam101/profitengine-v5 2>&1 | Select-String "Secret updated" -ErrorAction SilentlyContinue | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Secret added successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Testing SSH connection..." -ForegroundColor Cyan

    # Test SSH connection
    ssh -i $KeyPath -o StrictHostKeyChecking=no -o ConnectTimeout=10 opc@129.146.167.73 "uptime" 2>$null

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ SSH authentication verified!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next: Run the recovery workflow to test" -ForegroundColor Cyan
        Write-Host "  gh workflow run oci-auto-recovery.yml -f action=status" -ForegroundColor Yellow
    } else {
        Write-Host ""
        Write-Host "⚠️ SSH test failed. Check that the key is authorized on the OCI instance." -ForegroundColor Yellow
        Write-Host "Manual fix: Add the public key to OCI Console → Instance → Edit → SSH Keys" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Failed to set secret. Make sure you're authenticated to GitHub:" -ForegroundColor Red
    Write-Host "  gh auth login" -ForegroundColor Yellow
    exit 1
}
