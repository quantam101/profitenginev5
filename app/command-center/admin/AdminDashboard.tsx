'use client';

import { useState, useEffect } from 'react';
import SystemControlTab from './tabs/SystemControlTab';
import CustomerManagementTab from './tabs/CustomerManagementTab';
import TradingSignalsTab from './tabs/TradingSignalsTab';
import SystemHealthTab from './tabs/SystemHealthTab';

interface AdminSessionData {
  authenticated: boolean;
  email?: string;
  role?: string;
  ipAddress?: string;
}

type TabType = 'system' | 'customers' | 'signals' | 'health';

const AdminDashboard = ({ session }: { session: AdminSessionData }) => {
  const [activeTab, setActiveTab] = useState<TabType>('system');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const tabStyles = {
    container: {
      display: 'flex',
      gap: 12,
      marginBottom: 24,
      borderBottom: '1px solid rgba(125, 211, 252, 0.25)',
      paddingBottom: 0,
    },
    button: (active: boolean) => ({
      padding: '12px 20px',
      background: active ? 'rgba(125, 211, 252, 0.1)' : 'transparent',
      color: active ? '#7dd3fc' : '#a8bed0',
      border: active ? '1px solid rgba(125, 211, 252, 0.5)' : '1px solid transparent',
      borderBottom: active ? '2px solid #7dd3fc' : '1px solid transparent',
      borderRadius: '8px 8px 0 0',
      cursor: 'pointer',
      fontSize: 14,
      fontWeight: 500,
      transition: 'all 0.2s',
    }),
  };

  const tabs: { id: TabType; label: string; icon: string }[] = [
    { id: 'system', label: 'System Control', icon: '⚙️' },
    { id: 'customers', label: 'Customers', icon: '👥' },
    { id: 'signals', label: 'Trading Signals', icon: '📊' },
    { id: 'health', label: 'System Health', icon: '❤️' },
  ];

  return (
    <main
      style={{
        minHeight: '100vh',
        background: '#080b12',
        color: '#e5f7ff',
        fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
        padding: '32px',
      }}
    >
      <section style={{ maxWidth: 1400, margin: '0 auto' }}>
        {/* Header */}
        <header style={{ marginBottom: 36 }}>
          <nav style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
            <a href="/" style={{ color: '#7dd3fc', textDecoration: 'none', fontWeight: 800, fontSize: 18 }}>
              ProfitEngine v5
            </a>
            <div style={{ display: 'flex', alignItems: 'center', gap: 24, fontSize: 12, color: '#a8bed0' }}>
              <div>
                <span style={{ color: '#7dd3fc' }}>Admin:</span> {session.email || 'Unknown'}
              </div>
              <a href="/command-center" style={{ color: '#7dd3fc', textDecoration: 'none' }}>
                ← Back to Command Center
              </a>
            </div>
          </nav>

          <div>
            <p style={{ color: '#7dd3fc', textTransform: 'uppercase', letterSpacing: 2, fontSize: 12, margin: 0 }}>
              Already Here LLC Admin Console
            </p>
            <h1 style={{ fontSize: 'clamp(32px, 5vw, 48px)', lineHeight: 1, margin: '12px 0 0 0' }}>
              System Administration
            </h1>
            <p style={{ color: '#a8bed0', maxWidth: 760, fontSize: 14, lineHeight: 1.6, margin: '12px 0 0 0' }}>
              Manage trading systems, customer accounts, signals, and infrastructure health. All actions are logged for audit compliance.
            </p>
          </div>
        </header>

        {/* Tabs */}
        <div style={tabStyles.container as React.CSSProperties}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setLastUpdate(new Date());
              }}
              style={tabStyles.button(activeTab === tab.id) as React.CSSProperties}
            >
              <span style={{ marginRight: 6 }}>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div style={{ marginTop: 24 }}>
          {activeTab === 'system' && <SystemControlTab session={session} lastUpdate={lastUpdate} />}
          {activeTab === 'customers' && <CustomerManagementTab session={session} lastUpdate={lastUpdate} />}
          {activeTab === 'signals' && <TradingSignalsTab session={session} lastUpdate={lastUpdate} />}
          {activeTab === 'health' && <SystemHealthTab session={session} lastUpdate={lastUpdate} />}
        </div>
      </section>
    </main>
  );
};

export default AdminDashboard;
