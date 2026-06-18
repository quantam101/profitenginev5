'use client';

import { useState, useEffect } from 'react';

interface TradingSignalsProps {
  session: any;
  lastUpdate: Date;
}

interface Signal {
  id: string;
  timestamp: string;
  symbol: string;
  action: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  strategies: string[];
  status: 'evaluated' | 'executed' | 'rejected';
  agreedStrategies: number;
  totalStrategies: number;
}

interface RecentTrade {
  id: string;
  symbol: string;
  action: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  timestamp: string;
  pnl?: number;
  pnlPercent?: number;
}

const TradingSignalsTab = ({ session, lastUpdate }: TradingSignalsProps) => {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [recentTrades, setRecentTrades] = useState<RecentTrade[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overrideSymbol, setOverrideSymbol] = useState('');
  const [overrideAction, setOverrideAction] = useState<'BUY' | 'SELL' | 'HOLD'>('HOLD');
  const [overrideLoading, setOverrideLoading] = useState(false);

  const fetchSignals = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/command/admin/trading-signals', {
        cache: 'no-store',
      });

      if (!res.ok) throw new Error(`Failed to fetch signals: ${res.status}`);
      const data = await res.json();
      setSignals(data.signals || []);
      setRecentTrades(data.recentTrades || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch signals');
    } finally {
      setLoading(false);
    }
  };

  const submitSignalOverride = async () => {
    if (!overrideSymbol || overrideAction === 'HOLD') {
      setError('Please select a symbol and action');
      return;
    }

    try {
      setOverrideLoading(true);
      setError(null);
      const res = await fetch('/api/command/admin/execute-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'override-signal',
          params: {
            symbol: overrideSymbol,
            action: overrideAction,
          },
          timestamp: new Date().toISOString(),
        }),
        cache: 'no-store',
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || `Action failed: ${res.status}`);
      }

      setOverrideSymbol('');
      setOverrideAction('HOLD');
      await fetchSignals();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to override signal');
    } finally {
      setOverrideLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 30000);
    return () => clearInterval(interval);
  }, [lastUpdate]);

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#4ade80';
    if (confidence >= 0.6) return '#f59e0b';
    return '#f87171';
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'BUY':
        return '#4ade80';
      case 'SELL':
        return '#f87171';
      default:
        return '#7dd3fc';
    }
  };

  return (
    <div style={{ display: 'grid', gap: 24 }}>
      {error && (
        <div
          style={{
            padding: 16,
            border: '1px solid rgba(248, 113, 113, 0.5)',
            borderRadius: 12,
            background: 'rgba(127, 29, 29, 0.15)',
            color: '#f87171',
            fontSize: 13,
          }}
        >
          {error}
        </div>
      )}

      {/* Signal Override */}
      <div
        style={{
          border: '1px solid rgba(125, 211, 252, 0.25)',
          borderRadius: 12,
          padding: 24,
          background: 'rgba(15, 23, 42, 0.72)',
        }}
      >
        <h2 style={{ margin: '0 0 16px 0', fontSize: 18, color: '#e5f7ff' }}>Manual Signal Override</h2>
        <p style={{ margin: '0 0 16px 0', color: '#a8bed0', fontSize: 13 }}>
          Force the next signal action for a specific symbol
        </p>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: 12,
            alignItems: 'flex-end',
          }}
        >
          <div>
            <label style={{ display: 'block', color: '#a8bed0', fontSize: 11, marginBottom: 6, textTransform: 'uppercase' }}>
              Symbol
            </label>
            <input
              type="text"
              value={overrideSymbol}
              onChange={(e) => setOverrideSymbol(e.target.value.toUpperCase())}
              placeholder="e.g., AAPL"
              style={{
                width: '100%',
                padding: '8px',
                background: 'rgba(15, 23, 42, 0.5)',
                border: '1px solid rgba(125, 211, 252, 0.25)',
                borderRadius: 6,
                color: '#e5f7ff',
                fontSize: 13,
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', color: '#a8bed0', fontSize: 11, marginBottom: 6, textTransform: 'uppercase' }}>
              Action
            </label>
            <select
              value={overrideAction}
              onChange={(e) => setOverrideAction(e.target.value as 'BUY' | 'SELL' | 'HOLD')}
              style={{
                width: '100%',
                padding: '8px',
                background: 'rgba(15, 23, 42, 0.5)',
                border: '1px solid rgba(125, 211, 252, 0.25)',
                borderRadius: 6,
                color: '#e5f7ff',
                fontSize: 13,
              }}
            >
              <option value="HOLD">Select action...</option>
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </select>
          </div>

          <button
            onClick={submitSignalOverride}
            disabled={overrideLoading || !overrideSymbol || overrideAction === 'HOLD'}
            style={{
              padding: '8px 16px',
              background:
                overrideSymbol && overrideAction !== 'HOLD'
                  ? 'rgba(125, 211, 252, 0.1)'
                  : 'rgba(125, 211, 252, 0.05)',
              color: '#7dd3fc',
              border: '1px solid rgba(125, 211, 252, 0.25)',
              borderRadius: 6,
              cursor:
                overrideSymbol && overrideAction !== 'HOLD' && !overrideLoading
                  ? 'pointer'
                  : 'not-allowed',
              fontSize: 12,
              fontWeight: 500,
              opacity:
                overrideSymbol && overrideAction !== 'HOLD' && !overrideLoading ? 1 : 0.5,
            }}
          >
            {overrideLoading ? 'Submitting...' : 'Override Next Signal'}
          </button>
        </div>
      </div>

      {/* Current Signals */}
      <div
        style={{
          border: '1px solid rgba(125, 211, 252, 0.25)',
          borderRadius: 12,
          padding: 24,
          background: 'rgba(15, 23, 42, 0.72)',
        }}
      >
        <h2 style={{ margin: '0 0 16px 0', fontSize: 18, color: '#e5f7ff' }}>Current Trading Signals</h2>

        {loading ? (
          <p style={{ color: '#a8bed0', fontSize: 13, margin: 0 }}>Loading signals...</p>
        ) : signals.length === 0 ? (
          <p style={{ color: '#a8bed0', fontSize: 13, margin: 0 }}>No signals being evaluated at this moment</p>
        ) : (
          <div style={{ display: 'grid', gap: 12 }}>
            {signals.map((signal) => (
              <div
                key={signal.id}
                style={{
                  padding: 16,
                  border: '1px solid rgba(125, 211, 252, 0.15)',
                  borderRadius: 8,
                  background: 'rgba(15, 23, 42, 0.4)',
                }}
              >
                <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 16, marginBottom: 12 }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: 16, color: '#e5f7ff' }}>
                      {signal.symbol}
                      <span
                        style={{
                          marginLeft: 8,
                          padding: '4px 8px',
                          background: getActionColor(signal.action) + '30',
                          color: getActionColor(signal.action),
                          borderRadius: 4,
                          fontSize: 12,
                          fontWeight: 600,
                        }}
                      >
                        {signal.action}
                      </span>
                    </h3>
                    <p style={{ margin: '4px 0 0 0', color: '#a8bed0', fontSize: 11 }}>
                      {new Date(signal.timestamp).toLocaleString()}
                    </p>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <p style={{ margin: 0, color: '#a8bed0', fontSize: 11, textTransform: 'uppercase' }}>
                      Confidence
                    </p>
                    <p
                      style={{
                        margin: '4px 0 0 0',
                        color: getConfidenceColor(signal.confidence),
                        fontSize: 18,
                        fontWeight: 700,
                      }}
                    >
                      {(signal.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>

                <div
                  style={{
                    padding: 12,
                    background: 'rgba(15, 23, 42, 0.5)',
                    borderRadius: 6,
                    marginBottom: 12,
                  }}
                >
                  <p
                    style={{
                      margin: 0,
                      color: '#a8bed0',
                      fontSize: 11,
                      textTransform: 'uppercase',
                      marginBottom: 4,
                    }}
                  >
                    Strategy Agreement
                  </p>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                    }}
                  >
                    <div
                      style={{
                        flex: 1,
                        height: 8,
                        background: 'rgba(125, 211, 252, 0.2)',
                        borderRadius: 4,
                        overflow: 'hidden',
                      }}
                    >
                      <div
                        style={{
                          height: '100%',
                          background: getConfidenceColor(signal.confidence),
                          width: `${(signal.agreedStrategies / signal.totalStrategies) * 100}%`,
                        }}
                      />
                    </div>
                    <span style={{ color: '#7dd3fc', fontSize: 12, fontWeight: 600, minWidth: '60px' }}>
                      {signal.agreedStrategies}/{signal.totalStrategies}
                    </span>
                  </div>
                  <p style={{ margin: '8px 0 0 0', color: '#7dd3fc', fontSize: 11 }}>
                    {signal.strategies.join(', ')}
                  </p>
                </div>

                <div style={{ display: 'flex', gap: 8 }}>
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '4px 8px',
                      background: 'rgba(125, 211, 252, 0.1)',
                      color: '#7dd3fc',
                      borderRadius: 4,
                      fontSize: 10,
                      fontWeight: 600,
                      textTransform: 'uppercase',
                    }}
                  >
                    {signal.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Trades */}
      <div
        style={{
          border: '1px solid rgba(125, 211, 252, 0.25)',
          borderRadius: 12,
          padding: 24,
          background: 'rgba(15, 23, 42, 0.72)',
        }}
      >
        <h2 style={{ margin: '0 0 16px 0', fontSize: 18, color: '#e5f7ff' }}>Recently Executed Trades</h2>

        {recentTrades.length === 0 ? (
          <p style={{ color: '#a8bed0', fontSize: 13, margin: 0 }}>No recent trades</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: 12,
                color: '#e5f7ff',
              }}
            >
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(125, 211, 252, 0.25)' }}>
                  <th style={{ padding: '10px', textAlign: 'left', color: '#7dd3fc', fontWeight: 600 }}>
                    Symbol
                  </th>
                  <th style={{ padding: '10px', textAlign: 'center', color: '#7dd3fc', fontWeight: 600 }}>
                    Action
                  </th>
                  <th style={{ padding: '10px', textAlign: 'right', color: '#7dd3fc', fontWeight: 600 }}>
                    Qty
                  </th>
                  <th style={{ padding: '10px', textAlign: 'right', color: '#7dd3fc', fontWeight: 600 }}>
                    Price
                  </th>
                  <th style={{ padding: '10px', textAlign: 'right', color: '#7dd3fc', fontWeight: 600 }}>
                    P&L
                  </th>
                  <th style={{ padding: '10px', textAlign: 'right', color: '#7dd3fc', fontWeight: 600 }}>
                    Timestamp
                  </th>
                </tr>
              </thead>
              <tbody>
                {recentTrades.map((trade, idx) => (
                  <tr
                    key={trade.id}
                    style={{
                      borderBottom: '1px solid rgba(125, 211, 252, 0.1)',
                      background: idx % 2 === 0 ? 'rgba(15, 23, 42, 0.3)' : 'transparent',
                    }}
                  >
                    <td style={{ padding: '10px' }}>{trade.symbol}</td>
                    <td
                      style={{
                        padding: '10px',
                        textAlign: 'center',
                        color: getActionColor(trade.action),
                        fontWeight: 600,
                      }}
                    >
                      {trade.action}
                    </td>
                    <td style={{ padding: '10px', textAlign: 'right' }}>{trade.quantity}</td>
                    <td style={{ padding: '10px', textAlign: 'right' }}>
                      ${trade.price.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                    </td>
                    <td
                      style={{
                        padding: '10px',
                        textAlign: 'right',
                        color:
                          trade.pnl && trade.pnl > 0
                            ? '#4ade80'
                            : trade.pnl && trade.pnl < 0
                              ? '#f87171'
                              : '#a8bed0',
                      }}
                    >
                      {trade.pnl !== undefined
                        ? `$${trade.pnl.toLocaleString('en-US', { maximumFractionDigits: 2 })} (${trade.pnlPercent?.toFixed(1)}%)`
                        : '—'}
                    </td>
                    <td style={{ padding: '10px', textAlign: 'right', fontSize: 11, color: '#7dd3fc' }}>
                      {new Date(trade.timestamp).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default TradingSignalsTab;
