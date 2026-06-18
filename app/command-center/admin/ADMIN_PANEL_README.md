# Admin Control Panel — Already Here LLC

## Overview

Production-grade admin control panel for managing ProfitEngine v5 trading systems, customer accounts, trading signals, and infrastructure health. All actions are fully audited with real-time logging.

**Access URL**: `https://app.profitengine.alreadyherellc.com/command-center/admin`

## Features

### 1. System Control Tab

**Real-time system management with 2-second emergency shutdown guarantee.**

#### Trading Systems Toggle
- Enable/disable System A (Primary)
- Enable/disable System B (Secondary)
- Live status indicator (green = enabled, red = disabled)
- Instant system-wide control

#### Portfolio Status
- **Total Balance**: Current account equity (real-time)
- **Daily Drawdown**: Current daily loss percentage with risk threshold alerts
- **Open Positions**: Live list of all active positions with symbol, quantity, and market value

#### Risk Management
- **Risk Gate Override**: Temporarily allow higher risk trading (30-min default, configurable)
- **Emergency Shutdown**: Closes all positions within 2 seconds and halts all trading
  - Requires confirmation dialog
  - Fully logged with timestamp and IP
  - Cannot be reversed programmatically (manual reset required)

### 2. Customer Management Tab

**Complete customer lifecycle management with tier management and account controls.**

#### Customer Search & Filter
- Search by email or username (real-time filtering)
- Filter by tier: Free, Hybrid, White-Label, Enterprise
- Sortable columns: Email, Username, Tier, Status, Balance, Win Rate

#### Customer Details Modal
View for each customer:
- **Balance**: Current account equity
- **Win Rate**: Trading success percentage
- **Total Trades**: Lifetime trade count
- **Trading Status**: Paper or Live trading mode
- **Joined Date**: Account creation timestamp

#### Account Actions
- **Tier Upgrade/Downgrade**: Change customer subscription tier instantly
- **Suspend Account**: Pause all trading and lock account access
- **Unsuspend Account**: Re-enable suspended accounts
- **Manual Refund**: Process USD refunds for failed charges
  - Amount input with validation
  - Confirmation and audit trail
  - Reconciles with payment system

### 3. Trading Signals Tab

**Real-time signal evaluation and trading override capability.**

#### Manual Signal Override
- **Symbol Input**: Select which symbol to override
- **Action Selection**: BUY, SELL, or HOLD
- Forces next signal action for specified symbol
- Overrides all strategy recommendations for that action

#### Current Signals Display
- **Signal List**: All signals currently being evaluated
- **Confidence Score**: 0-100% with color-coded severity
- **Strategy Agreement**: Visual progress bar showing strategy consensus
- **Status**: Evaluated, Executed, or Rejected

#### Recent Executed Trades
- **Trade History**: Last 20 executed trades
- **Columns**: Symbol, Action (BUY/SELL), Quantity, Price, P&L, Timestamp
- **P&L Tracking**: Real-time profit/loss with percentage gain/loss
- **Color Coding**: Green for profits, red for losses

### 4. System Health Tab

**Complete infrastructure monitoring and diagnostic tools.**

#### API Status
- **Client API**: Real-time health check
- **Daily Alerts Service**: Alert system availability
- **Runtime Service**: Core trading engine status
- Color-coded status indicators (green = operational, red = down)

#### Database Status
- **Size**: Current database size in MB
- **Record Count**: Total records stored
- **Last Backup**: Most recent backup timestamp

#### Backup Status
- **Status**: Active, Pending, or Failed
- **Last Backup Time**: Previous backup completion
- **Next Backup Time**: Scheduled next backup

#### Robinhood Connection
- **Connection Status**: Connected/Disconnected indicator
- **Account Status**: Current account status and verification
- **Last Sync**: Most recent data sync timestamp

#### Error Log
- **Last 50 Errors**: Full error history with details
- **Severity Levels**: Critical (red), Error (orange), Warning (yellow)
- **Service Info**: Which service generated the error
- **Error Messages**: Full technical details for debugging

## Authentication & Security

### Multi-Factor Authentication (MFA)
- **Requirement**: Always enabled for production access
- **Method**: Time-based One-Time Password (TOTP) via authenticator app
- **Setup**: 
  1. Scan QR code with authenticator app (Google Authenticator, Authy, etc.)
  2. Enter 6-digit code from app to verify
  3. Store backup codes in secure location

### IP Whitelist
- **Configuration**: Set via `ADMIN_ALLOWED_IPS` environment variable
- **Format**: Comma-separated IP addresses
  ```
  ADMIN_ALLOWED_IPS=203.0.113.45,198.51.100.20
  ```
- **Fallback**: If not configured, any IP can attempt access (MFA still required)

### Authorization
- **Admin Email**: Only `dispatch@alreadyherellc.com` can access
- **Session Timeout**: No persistent session (re-verify on each action)
- **HTTPS Only**: All requests must be over HTTPS
- **CORS**: Restricted to same-origin requests only

## Audit Logging

**Every admin action is logged for compliance and debugging.**

### Logged Information
- **Action**: What was executed (e.g., "emergency-shutdown")
- **Admin Email**: Who performed the action
- **Timestamp**: When the action occurred (ISO 8601)
- **IP Address**: Source IP of the request
- **Parameters**: Input values and configuration
- **Result**: Success or failure with error message
- **Duration**: How long execution took

### Audit Log Access
- **Endpoint**: `GET /api/command/admin/execute-action?limit=50`
- **Returns**: JSON array of recent audit log entries
- **Retention**: Last 1000 entries in memory (persist to database in production)

### Example Audit Log Entry
```json
{
  "id": "log_1713456789123_abc123def456",
  "adminEmail": "dispatch@alreadyherellc.com",
  "action": "emergency-shutdown",
  "params": { "reason": "Manual halt" },
  "timestamp": "2024-04-18T14:33:09.123Z",
  "ipAddress": "203.0.113.45",
  "result": "success"
}
```

## API Endpoints

### Authentication
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/command/admin/verify` | POST | Verify admin session |
| `/api/command/admin/verify-mfa` | POST | Submit MFA code |

### System Data
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/command/admin/system-state` | GET | Current system state |
| `/api/command/admin/customers` | GET | Customer list |
| `/api/command/admin/trading-signals` | GET | Signals & trades |
| `/api/command/admin/health` | GET | System health status |

### Actions
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/command/admin/execute-action` | POST | Execute admin action |
| `/api/command/admin/execute-action` | GET | Audit log (50 entries) |

## Configuration

### Environment Variables

```bash
# Admin Access
ADMIN_ALLOWED_IPS=203.0.113.45,198.51.100.20  # Optional IP whitelist

# Runtime API
RUNTIME_API_URL=http://129.146.236.177:8000

# API Keys
CLIENT_API_KEY=your-runtime-api-key

# Environment
NODE_ENV=production  # Enables MFA requirement
```

### .env.local Example (Development)
```bash
RUNTIME_API_URL=http://localhost:8080
CLIENT_API_KEY=dev-key
NODE_ENV=development
```

## Usage Examples

### Emergency Shutdown Flow
1. Click **"EMERGENCY SHUTDOWN"** button in System Control tab
2. Read confirmation dialog carefully
3. Click **"Confirm"** button
4. All positions close within 2 seconds
5. Trading systems halt immediately
6. Action logged with timestamp and IP

### Customer Tier Upgrade
1. Go to **Customer Management** tab
2. Search for customer email
3. Click **"View"** button on customer row
4. Select new tier from dropdown
5. Tier upgrades immediately
6. Customer receives notification
7. Action logged in audit trail

### Override Trading Signal
1. Go to **Trading Signals** tab
2. Enter symbol (e.g., "AAPL")
3. Select action: BUY or SELL
4. Click **"Override Next Signal"**
5. Next signal for that symbol uses your action
6. Strategy recommendations bypassed
7. Logged with timestamp

### Process Customer Refund
1. Go to **Customer Management** tab
2. Find customer and click **"View"**
3. Enter refund amount (USD)
4. Click **"Refund"** button
5. Funds processed to customer's original payment method
6. Transaction appears in payment records
7. Full audit trail maintained

## Mobile Responsive Design

The admin panel is fully responsive and works on:
- **Desktop**: Full-width tabbed interface
- **Tablet**: Stacked layout with optimized touch targets
- **Mobile**: Single-column view with collapsible sections

Perfect for emergency access from any device.

## Dark Theme

All components use a professional dark theme matching the ProfitEngine brand:
- **Background**: #080b12 (deep dark blue)
- **Text**: #e5f7ff (light cyan)
- **Accent**: #7dd3fc (bright cyan)
- **Success**: #4ade80 (green)
- **Error**: #f87171 (red)
- **Warning**: #f59e0b (amber)

## Rate Limiting

To prevent abuse:
- **API calls**: 100 per minute per admin
- **Action execution**: 10 per minute per admin
- **Data fetch**: 30 per minute per admin

Exceeding limits returns HTTP 429 (Too Many Requests).

## Troubleshooting

### "Access Denied" Error
1. Verify email is `dispatch@alreadyherellc.com`
2. Check IP whitelist if configured
3. Verify HTTPS connection (not HTTP)
4. Clear browser cookies and retry

### "MFA Required" But No Code Input
1. Refresh page to see MFA input field
2. Check authenticator app for valid code
3. Ensure system time is synchronized
4. Try code from different authenticator app

### API Connection Failures
1. Check `RUNTIME_API_URL` is correct and reachable
2. Verify `CLIENT_API_KEY` is valid
3. Check network connectivity (VPN, firewall)
4. Review error log in System Health tab

### Slow Dashboard Loading
1. Check System Health tab for service issues
2. Verify no ongoing backup operations
3. Clear browser cache (Ctrl+Shift+Delete)
4. Try different browser

## Best Practices

### System Control
- ✅ Use Emergency Shutdown only when absolutely necessary
- ✅ Always confirm destructive actions before clicking
- ✅ Monitor daily drawdown to stay within risk limits
- ✅ Review Position list regularly for unexpected trades

### Customer Management
- ✅ Document reason for tier changes
- ✅ Notify customers before suspending accounts
- ✅ Keep refund amounts reasonable and documented
- ✅ Use search filters to avoid customer record errors

### Trading Signals
- ✅ Only override signals for specific market conditions
- ✅ Document reason for each manual override
- ✅ Monitor execution results after override
- ✅ Review error patterns in signal evaluation

### Health Monitoring
- ✅ Check system health daily
- ✅ Review error log for recurring issues
- ✅ Verify backups complete within expected time
- ✅ Monitor Robinhood connection status

## Production Checklist

Before deploying to production:

- [ ] MFA enabled and tested
- [ ] IP whitelist configured with correct IPs
- [ ] RUNTIME_API_URL points to production
- [ ] CLIENT_API_KEY is production key
- [ ] NODE_ENV=production
- [ ] HTTPS certificate valid
- [ ] Audit logging directed to persistent storage
- [ ] Error monitoring service configured
- [ ] Backup system tested
- [ ] Admin contact info updated
- [ ] Documentation shared with team
- [ ] Incident response plan reviewed

## Support & Escalation

For admin panel issues:

1. **Initial Check**: Review System Health tab
2. **API Verification**: Test endpoints via curl
3. **Log Review**: Check audit trail for errors
4. **Contact**: dispatch@alreadyherellc.com

## Related Documentation

- [Trading Dashboard](../TradingDashboard.tsx)
- [ProfitEngine Architecture](../../../ARCHITECTURE.md)
- [Security Guidelines](../../../SECURITY.md)
- [API Reference](../../../API_REFERENCE.md)

---

**Last Updated**: June 18, 2024
**Version**: 1.0.0 (Production Ready)
**Status**: All 6 enhancement modules integrated and verified
