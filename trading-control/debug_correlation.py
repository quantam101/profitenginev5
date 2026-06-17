import numpy as np
from decimal import Decimal
from signal_correlation_analyzer import SignalCorrelationAnalyzer
from models import TechnicalSignal, MicrostructureSignal, RegimeSignal, PortfolioSignal, MarketRegime

# Test basic correlation with controlled signals
analyzer = SignalCorrelationAnalyzer(window_size=20)

# Add 25 trades with varying signals
for i in range(1, 26):
    # Create intentionally correlated signals
    base = 0.5 + 0.3 * np.sin(i * 0.3)  # Sinusoidal variation
    
    tech_conf = base + np.random.normal(0, 0.02)
    micro_conf = base + np.random.normal(0, 0.02)  # Correlated with tech
    regime_conf = 0.7 + np.random.normal(0, 0.05)  # Independent
    
    tech_conf = np.clip(tech_conf, 0.3, 0.9)
    micro_conf = np.clip(micro_conf, 0.3, 0.9)
    regime_conf = np.clip(regime_conf, 0.3, 0.9)
    
    technical = TechnicalSignal(
        rsi_oversold_recovery=tech_conf * 0.9,
        macd_bullish_cross=tech_conf * 0.85,
        support_bounce=tech_conf * 0.80,
        trend_alignment=tech_conf * 0.95,
        pattern_score=tech_conf * 0.75,
        confidence=tech_conf
    )
    
    microstructure = MicrostructureSignal(
        bid_ask_imbalance=micro_conf * 0.3,
        smart_money_flow=micro_conf * 0.8,
        liquidity_score=micro_conf * 0.9,
        front_running_risk=0.1,
        time_to_fill=0.5,
        confidence=micro_conf
    )
    
    regime = RegimeSignal(
        regime=MarketRegime.BULL_TRENDING,
        volatility_level=regime_conf * 0.6,
        event_risk=0.05,
        correlation_stress=0.1,
        regime_confidence=regime_conf,
        approved_to_trade=True
    )
    
    portfolio = PortfolioSignal(
        position_size_kelly=0.02,
        max_correlated_exposure=0.15,
        drawdown_forecast=0.02,
        risk_budget_remaining=0.95,
        recommended_action="BUY"
    )
    
    outcome = 1 if np.random.random() < 0.5 else 0
    analyzer.record_trade(technical, microstructure, regime, portfolio, outcome)
    
    print(f"Trade {i:2d}: Tech={tech_conf:.3f}, Micro={micro_conf:.3f}, Regime={regime_conf:.3f}")

# Print recorded signals
print("\nRecorded Technical Signals:")
tech_signals = [s['confidence'] for s in analyzer.signal_history['technical']]
print(tech_signals[:10])

print("\nRecorded Microstructure Signals:")
micro_signals = [s['confidence'] for s in analyzer.signal_history['microstructure']]
print(micro_signals[:10])

# Calculate correlation matrix
corr_matrix = analyzer.calculate_correlation_matrix()
print("\nCorrelation Matrix:")
print(corr_matrix)

print("\nAgent names:", analyzer.agent_names)
print("Tech vs Micro correlation:", corr_matrix[0, 1])
