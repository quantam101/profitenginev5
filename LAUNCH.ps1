# ProfitEngine v5 - Autonomous Trading System Launcher (PowerShell)
# Handles Unicode encoding and launches the trading system

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "================================================================================"
Write-Host "PROFITENGINE v5 - AUTONOMOUS TRADING SYSTEM"
Write-Host "================================================================================"
Write-Host ""
Write-Host "Launching Master Orchestrator AI..."
Write-Host "Paper Trading: \$100 -> \$1000"
Write-Host "11 Strategies | 6 Risk Gates | 100% Autonomous"
Write-Host ""

# Set UTF-8 encoding to handle special characters
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Check for Finnhub API key
$finnhubKey = $env:FINNHUB_API_KEY
if ($finnhubKey) {
    Write-Host "Finnhub API Key: Found ($(($finnhubKey).Substring(0,10))...)"
} else {
    Write-Host "Finnhub API Key: Not set (using Yahoo Finance for slower data)"
    Write-Host "Tip: Get free key from https://finnhub.io/register"
}

Write-Host ""
Write-Host "Starting system..."
Write-Host ""

# Run the trading system
python LAUNCH_AUTONOMOUS_TRADING.py 2>&1 | ForEach-Object {
    # Filter out emoji encoding errors but show all other output
    if ($_ -notlike "*UnicodeEncodeError*" -and $_ -notlike "*charmap*") {
        $_
    }
}

Write-Host ""
Write-Host "================================================================================"
Write-Host "Trading system has stopped."
Write-Host "================================================================================"
