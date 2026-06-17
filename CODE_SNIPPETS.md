# Dynamic Risk Adjustment - Code Snippets

Quick reference for the exact code changes made.

## 1. app.py - Import Statement (Line 29)

```python
from dynamic_risk_adjustment import DynamicRiskAdjuster
```

## 2. app.py - Initialization in __init__ (Lines 44-52)

```python
# Initialize Dynamic Risk Adjuster
baseline_loss_limit = self.config['risk']['hard_limits'].get('max_daily_loss_usd', 200.0)
baseline_volatility = self.config['dynamic_risk'].get('baseline_volatility', 0.02)
self.risk_adjuster = DynamicRiskAdjuster(
    baseline_daily_loss_limit=baseline_loss_limit,
    kelly_base_fraction=self.config['dynamic_risk'].get('kelly_base_fraction', 0.05),
    volatility_lookback_periods=self.config['dynamic_risk'].get('volatility_lookback_periods', 20),
    regime_switch_threshold=self.config['dynamic_risk'].get('regime_switch_threshold', 0.95)
)
```

## 3. app.py - Volatility Calculation (Lines 90-96)

```python
# DYNAMIC RISK: Calculate volatility scalar for position sizing
if 'prices' in snapshot and len(snapshot['prices']) > 1:
    price_array = np.array(snapshot['prices'])
    returns = np.diff(np.log(price_array))
    self.risk_adjuster.update_price_data(snapshot['symbol'], returns.tolist())
volatility_scalar = self.risk_adjuster.calculate_volatility_scalar(snapshot['symbol'])
logger.info(f"[{snapshot['symbol']}] Volatility scalar: {volatility_scalar:.3f}")
```

## 4. app.py - Loss Limit Adjustment (Lines 116-119)

```python
# DYNAMIC RISK: Adjust daily loss limit based on volatility regime
realized_loss = float(account_state.daily_pnl)
adjusted_limit, utilization_pct = self.risk_adjuster.adjust_daily_loss_limit(realized_loss)
logger.info(f"[{snapshot['symbol']}] Loss limit: ${adjusted_limit:.2f} (utilization: {utilization_pct:.1f}%)")
```

## 5. app.py - Risk Kernel Call with Dynamic Limit (Lines 122-133)

```python
# STEP 2: Risk evaluation
risk_decision = self.risk_kernel.evaluate(
    proposal,
    {
        'bid': proposal.entry_price,
        'ask': proposal.entry_price,
        'timestamp': datetime.utcnow(),
        **snapshot
    },
    account_state,
    list(self.open_orders.values()),
    adjusted_daily_loss_limit=adjusted_limit  # Pass adjusted limit to risk kernel
)
```

## 6. risk_kernel.py - Updated Initialization (Lines 17-26)

Old:
```python
def __init__(self, hard_limits: Dict):
    self.max_daily_loss = Decimal(str(hard_limits.get('max_daily_loss_usd', 200)))
```

New:
```python
def __init__(self, hard_limits: Dict):
    self.baseline_daily_loss = Decimal(str(hard_limits.get('max_daily_loss_usd', 200)))
    self.max_daily_loss = self.baseline_daily_loss  # Will be overridden by adjusted limit
```

## 7. risk_kernel.py - Updated Method Signature (Lines 29-40)

Old:
```python
def evaluate(self, proposal: TradeProposal, market_snapshot: Dict,
             account_state: AccountState, open_orders: List = None) -> RiskApprovalDecision:
```

New:
```python
def evaluate(self, proposal: TradeProposal, market_snapshot: Dict,
             account_state: AccountState, open_orders: List = None,
             adjusted_daily_loss_limit: float = None) -> RiskApprovalDecision:
    """
    Apply ALL hard gates. ANY gate failure → rejection.
    No override possible; no human negotiation on hard limits.

    Args:
        adjusted_daily_loss_limit: Dynamic risk adjustment from DynamicRiskAdjuster.
            If provided, overrides hardcoded limit for this evaluation.
    """
```

## 8. risk_kernel.py - Dynamic Limit Application (Lines 44-48)

```python
# Use adjusted limit if provided by dynamic risk adjuster, otherwise use baseline
if adjusted_daily_loss_limit is not None:
    self.max_daily_loss = Decimal(str(adjusted_daily_loss_limit))
else:
    self.max_daily_loss = self.baseline_daily_loss
```

## 9. risk_kernel.py - GATE 3 (Daily Loss) - Line 60

Changed comment from:
```python
# GATE 3: Daily loss limit
```

To:
```python
# GATE 3: Daily loss limit (now uses dynamic adjustment)
```

Gate implementation unchanged (still checks `account_state.daily_pnl <= -self.max_daily_loss`):
```python
if account_state.daily_pnl <= -self.max_daily_loss:
    rejections.append(RejectionReason.DAILY_LOSS_HIT)
```

## 10. config.yaml - New Dynamic Risk Section (Lines 37-40)

Add this section under `risk:` (after `hard_limits:`):

```yaml
  dynamic_risk:
    baseline_volatility: 0.02          # Reference volatility (2% annualized) for volatility scalar calculation
    kelly_base_fraction: 0.05          # Base Kelly fraction (5%) before volatility/regime adjustments
    volatility_lookback_periods: 20    # Number of periods for volatility calculation
    regime_switch_threshold: 0.95      # Confidence threshold (95%) for market regime changes
```

## Configuration Parameters Explained

### baseline_volatility
- **Purpose:** Reference point for volatility scalar calculation
- **Effect:** `scalar = baseline_volatility / current_volatility`
- **Default:** 0.02 (2% annualized)
- **Tuning:**
  - Lower (0.01) → More sensitive to volatility changes
  - Higher (0.03) → Less sensitive (more stable scalar)

### kelly_base_fraction
- **Purpose:** Base Kelly fraction before regime/volatility adjustments
- **Effect:** Multiplied by volatility scalar and regime multiplier
- **Default:** 0.05 (5% Kelly)
- **Note:** Currently calculated but not applied in position sizing (future feature)

### volatility_lookback_periods
- **Purpose:** Rolling window size for volatility calculation
- **Effect:** Number of returns to keep in buffer
- **Default:** 20 periods
- **Tuning:**
  - Larger (30+) → Slower response to volatility spikes
  - Smaller (10-15) → Faster, more reactive adjustments

### regime_switch_threshold
- **Purpose:** Confidence threshold for triggering regime changes
- **Effect:** Minimum confidence required to switch regimes
- **Default:** 0.95 (95% confidence)
- **Tuning:**
  - Higher (0.99) → Fewer regime changes (more stable)
  - Lower (0.85) → More frequent regime changes (more reactive)

## Return Values & Ranges

### calculate_volatility_scalar()
- **Returns:** float in range [0.1, 1.5]
- **Meaning:**
  - 0.1 = Extreme volatility, reduce positions to 10% of normal
  - 1.0 = Baseline volatility, use normal position size
  - 1.5 = Very low volatility, increase positions to 150% of normal

### adjust_daily_loss_limit()
- **Returns:** Tuple of (adjusted_limit_usd, utilization_percentage)
- **Example Return:** (150.0, 80.0)
- **Meaning:**
  - Adjusted limit: $150 (tightened from baseline $200)
  - Utilization: 80% of original limit already lost

## Logging Output Examples

When everything is working:
```
[AAPL] Volatility scalar: 1.234
[AAPL] Loss limit: $215.00 (utilization: 35.0%)
[AAPL] Proposal: BUY @ 150.25
[AAPL] Risk APPROVED (score: 0.42)
[AAPL] FILLED @ 150.26 (slippage: 0.01)
```

During high volatility:
```
[AAPL] Volatility scalar: 0.456
[AAPL] Loss limit: $140.00 (utilization: 75.3%)
[AAPL] Proposal: BUY @ 150.25
[AAPL] Risk REJECTED: DAILY_LOSS_HIT
```

## Integration Flow Diagram

```
┌─────────────────────────────────────┐
│     Market Snapshot Received        │
│  {symbol, bid, ask, prices, ...}    │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Calculate Log Returns from prices   │
│ returns = diff(log(price_array))    │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Update Volatility Buffer            │
│ risk_adjuster.update_price_data()   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Calculate Volatility Scalar         │
│ scalar = 0.02 / current_vol         │
│ scalar in [0.1, 1.5]                │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Adjust Daily Loss Limit             │
│ limit = baseline * regime * util    │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Risk Kernel Evaluation              │
│ evaluate(..., adjusted_limit)       │
│ GATE 3: daily_pnl <= -adjusted_limit│
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ APPROVED or REJECTED                │
└─────────────────────────────────────┘
```

## Common Parameter Adjustments

### Scenario: Market is too reactive to volatility spikes
```yaml
dynamic_risk:
  volatility_lookback_periods: 30    # Increase from 20 to 30
  regime_switch_threshold: 0.98      # Increase from 0.95 to 0.98
```

### Scenario: Want larger positions in low volatility
```yaml
dynamic_risk:
  baseline_volatility: 0.03           # Increase from 0.02 to 0.03
```

### Scenario: Stricter loss limits
```yaml
dynamic_risk:
  baseline_volatility: 0.015          # Decrease from 0.02
  regime_switch_threshold: 0.90       # Decrease from 0.95 (switch faster to tighter regimes)
```

---

**Total Changes Summary:**
- app.py: +27 effective lines of code
- risk_kernel.py: +9 effective lines of code
- config.yaml: +4 parameter lines
- Total: +40 lines to enable full dynamic risk adjustment
