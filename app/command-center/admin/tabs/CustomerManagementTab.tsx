'use client';

import { useState, useEffect } from 'react';

interface CustomerManagementProps {
  session: any;
  lastUpdate: Date;
}

interface Customer {
  id: string;
  email: string;
  username: string;
  tier: 'Free' | 'Hybrid' | 'White-Label' | 'Enterprise';
  status: 'active' | 'suspended' | 'inactive';
  balance: number;
  winRate: number;
  totalTrades: number;
  tradingStatus: 'paper' | 'live';
  joinedDate: string;
}

const CustomerManagementTab = ({ session, lastUpdate }: CustomerManagementProps) => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [filteredCustomers, setFilteredCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [tierFilter, setTierFilter] = useState<string>('all');
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refundAmount, setRefundAmount] = useState('');

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/command/admin/customers', {
        cache: 'no-store',
      });

      if (!res.ok) throw new Error(`Failed to fetch customers: ${res.status}`);
      const data = await res.json();
      setCustomers(data);
      setFilteredCustomers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch customers');
    } finally {
      setLoading(false);
    }
  };

  const executeCustomerAction = async (action: string, params: any = {}) => {
    try {
      setActionLoading(true);
      setError(null);
      const res = await fetch('/api/command/admin/execute-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action,
          params: { ...params, customerId: selectedCustomer?.id },
          timestamp: new Date().toISOString(),
        }),
        cache: 'no-store',
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || `Action failed: ${res.status}`);
      }

      await fetchCustomers();
      setSelectedCustomer(null);
      setRefundAmount('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setActionLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [lastUpdate]);

  useEffect(() => {
    let filtered = customers;

    if (searchTerm) {
      filtered = filtered.filter(
        (c) =>
          c.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.username.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (tierFilter !== 'all') {
      filtered = filtered.filter((c) => c.tier === tierFilter);
    }

    setFilteredCustomers(filtered);
  }, [searchTerm, tierFilter, customers]);

  const tierColors: Record<string, string> = {
    Free: '#a8bed0',
    Hybrid: '#7dd3fc',
    'White-Label': '#f59e0b',
    Enterprise: '#7c3aed',
  };

  const statusColors: Record<string, string> = {
    active: '#4ade80',
    suspended: '#f87171',
    inactive: '#a8bed0',
  };

  if (loading && customers.length === 0) {
    return (
      <div
        style={{
          padding: 24,
          border: '1px solid rgba(125, 211, 252, 0.25)',
          borderRadius: 12,
          background: 'rgba(15, 23, 42, 0.72)',
          textAlign: 'center',
          color: '#a8bed0',
        }}
      >
        Loading customers...
      </div>
    );
  }

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

      {/* Filters */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 16,
        }}
      >
        <div>
          <label style={{ display: 'block', color: '#a8bed0', fontSize: 12, marginBottom: 8, textTransform: 'uppercase' }}>
            Search by email or username
          </label>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search..."
            style={{
              width: '100%',
              padding: '10px',
              background: 'rgba(15, 23, 42, 0.5)',
              border: '1px solid rgba(125, 211, 252, 0.25)',
              borderRadius: 6,
              color: '#e5f7ff',
              fontSize: 13,
            }}
          />
        </div>

        <div>
          <label style={{ display: 'block', color: '#a8bed0', fontSize: 12, marginBottom: 8, textTransform: 'uppercase' }}>
            Filter by tier
          </label>
          <select
            value={tierFilter}
            onChange={(e) => setTierFilter(e.target.value)}
            style={{
              width: '100%',
              padding: '10px',
              background: 'rgba(15, 23, 42, 0.5)',
              border: '1px solid rgba(125, 211, 252, 0.25)',
              borderRadius: 6,
              color: '#e5f7ff',
              fontSize: 13,
            }}
          >
            <option value="all">All Tiers</option>
            <option value="Free">Free</option>
            <option value="Hybrid">Hybrid</option>
            <option value="White-Label">White-Label</option>
            <option value="Enterprise">Enterprise</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
          <button
            onClick={fetchCustomers}
            disabled={loading}
            style={{
              width: '100%',
              padding: '10px',
              background: 'rgba(125, 211, 252, 0.1)',
              color: '#7dd3fc',
              border: '1px solid rgba(125, 211, 252, 0.25)',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: 500,
            }}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Customers Table */}
      <div
        style={{
          border: '1px solid rgba(125, 211, 252, 0.25)',
          borderRadius: 12,
          padding: 20,
          background: 'rgba(15, 23, 42, 0.72)',
          overflowX: 'auto',
        }}
      >
        <p style={{ margin: '0 0 12px 0', color: '#a8bed0', fontSize: 12 }}>
          {filteredCustomers.length} customer{filteredCustomers.length !== 1 ? 's' : ''}
        </p>

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
              <th style={{ padding: '10px', textAlign: 'left', color: '#7dd3fc', fontWeight: 600 }}>Email</th>
              <th style={{ padding: '10px', textAlign: 'left', color: '#7dd3fc', fontWeight: 600 }}>Username</th>
              <th style={{ padding: '10px', textAlign: 'center', color: '#7dd3fc', fontWeight: 600 }}>Tier</th>
              <th style={{ padding: '10px', textAlign: 'center', color: '#7dd3fc', fontWeight: 600 }}>Status</th>
              <th style={{ padding: '10px', textAlign: 'right', color: '#7dd3fc', fontWeight: 600 }}>Balance</th>
              <th style={{ padding: '10px', textAlign: 'right', color: '#7dd3fc', fontWeight: 600 }}>Win Rate</th>
              <th style={{ padding: '10px', textAlign: 'center', color: '#7dd3fc', fontWeight: 600 }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredCustomers.map((customer, idx) => (
              <tr
                key={customer.id}
                style={{
                  borderBottom: '1px solid rgba(125, 211, 252, 0.1)',
                  background: idx % 2 === 0 ? 'rgba(15, 23, 42, 0.3)' : 'transparent',
                }}
              >
                <td style={{ padding: '10px' }}>{customer.email}</td>
                <td style={{ padding: '10px' }}>{customer.username}</td>
                <td style={{ padding: '10px', textAlign: 'center', color: tierColors[customer.tier] }}>
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '4px 8px',
                      background: `${tierColors[customer.tier]}20`,
                      borderRadius: 4,
                      fontSize: 10,
                      fontWeight: 600,
                    }}
                  >
                    {customer.tier}
                  </span>
                </td>
                <td style={{ padding: '10px', textAlign: 'center', color: statusColors[customer.status] }}>
                  <span
                    style={{
                      display: 'inline-block',
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: statusColors[customer.status],
                      marginRight: 4,
                      verticalAlign: 'middle',
                    }}
                  />
                  {customer.status}
                </td>
                <td style={{ padding: '10px', textAlign: 'right' }}>
                  ${customer.balance.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                </td>
                <td style={{ padding: '10px', textAlign: 'right', color: '#4ade80' }}>
                  {(customer.winRate * 100).toFixed(1)}%
                </td>
                <td style={{ padding: '10px', textAlign: 'center' }}>
                  <button
                    onClick={() => setSelectedCustomer(customer)}
                    style={{
                      padding: '6px 12px',
                      background: 'rgba(125, 211, 252, 0.1)',
                      color: '#7dd3fc',
                      border: '1px solid rgba(125, 211, 252, 0.25)',
                      borderRadius: 4,
                      cursor: 'pointer',
                      fontSize: 11,
                      fontWeight: 500,
                    }}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredCustomers.length === 0 && (
          <p style={{ textAlign: 'center', color: '#a8bed0', padding: 20, margin: 0 }}>
            No customers found matching your filters
          </p>
        )}
      </div>

      {/* Customer Details Modal */}
      {selectedCustomer && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 20,
          }}
        >
          <div
            style={{
              background: '#080b12',
              border: '1px solid rgba(125, 211, 252, 0.25)',
              borderRadius: 12,
              padding: 32,
              maxWidth: 500,
              maxHeight: '90vh',
              overflowY: 'auto',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 20 }}>
              <div>
                <h2 style={{ margin: 0, fontSize: 20, color: '#e5f7ff' }}>{selectedCustomer.username}</h2>
                <p style={{ margin: '4px 0 0 0', color: '#a8bed0', fontSize: 12 }}>{selectedCustomer.email}</p>
              </div>
              <button
                onClick={() => setSelectedCustomer(null)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#a8bed0',
                  fontSize: 24,
                  cursor: 'pointer',
                  padding: 0,
                }}
              >
                ×
              </button>
            </div>

            {/* Customer Stats */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 12,
                marginBottom: 20,
              }}
            >
              <div style={{ padding: 12, background: 'rgba(15, 23, 42, 0.4)', borderRadius: 6 }}>
                <p style={{ margin: 0, color: '#a8bed0', fontSize: 10, textTransform: 'uppercase' }}>Balance</p>
                <p style={{ margin: '4px 0 0 0', color: '#4ade80', fontSize: 16, fontWeight: 700 }}>
                  ${selectedCustomer.balance.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                </p>
              </div>
              <div style={{ padding: 12, background: 'rgba(15, 23, 42, 0.4)', borderRadius: 6 }}>
                <p style={{ margin: 0, color: '#a8bed0', fontSize: 10, textTransform: 'uppercase' }}>Win Rate</p>
                <p style={{ margin: '4px 0 0 0', color: '#4ade80', fontSize: 16, fontWeight: 700 }}>
                  {(selectedCustomer.winRate * 100).toFixed(1)}%
                </p>
              </div>
              <div style={{ padding: 12, background: 'rgba(15, 23, 42, 0.4)', borderRadius: 6 }}>
                <p style={{ margin: 0, color: '#a8bed0', fontSize: 10, textTransform: 'uppercase' }}>Total Trades</p>
                <p style={{ margin: '4px 0 0 0', color: '#7dd3fc', fontSize: 16, fontWeight: 700 }}>
                  {selectedCustomer.totalTrades}
                </p>
              </div>
              <div style={{ padding: 12, background: 'rgba(15, 23, 42, 0.4)', borderRadius: 6 }}>
                <p style={{ margin: 0, color: '#a8bed0', fontSize: 10, textTransform: 'uppercase' }}>
                  Trading Status
                </p>
                <p style={{ margin: '4px 0 0 0', color: selectedCustomer.tradingStatus === 'live' ? '#f59e0b' : '#7dd3fc', fontSize: 14, fontWeight: 600 }}>
                  {selectedCustomer.tradingStatus.toUpperCase()}
                </p>
              </div>
            </div>

            {/* Actions */}
            <div style={{ marginBottom: 20 }}>
              <h3 style={{ margin: '0 0 12px 0', fontSize: 14, color: '#e5f7ff' }}>Account Actions</h3>

              <div style={{ display: 'grid', gap: 8 }}>
                {/* Tier Management */}
                <div>
                  <label style={{ display: 'block', color: '#a8bed0', fontSize: 11, marginBottom: 6 }}>
                    Change Tier
                  </label>
                  <select
                    onChange={(e) => {
                      if (e.target.value) {
                        executeCustomerAction('upgrade-tier', { newTier: e.target.value });
                      }
                    }}
                    defaultValue=""
                    style={{
                      width: '100%',
                      padding: '8px',
                      background: 'rgba(15, 23, 42, 0.5)',
                      border: '1px solid rgba(125, 211, 252, 0.25)',
                      borderRadius: 6,
                      color: '#e5f7ff',
                      fontSize: 12,
                    }}
                  >
                    <option value="">Select tier...</option>
                    {['Free', 'Hybrid', 'White-Label', 'Enterprise'].map((tier) => (
                      <option key={tier} value={tier}>
                        {tier}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Suspend/Unsuspend */}
                {selectedCustomer.status === 'active' && (
                  <button
                    onClick={() => executeCustomerAction('suspend-account')}
                    disabled={actionLoading}
                    style={{
                      width: '100%',
                      padding: '8px',
                      background: 'rgba(248, 113, 113, 0.2)',
                      color: '#f87171',
                      border: '1px solid #f87171',
                      borderRadius: 6,
                      cursor: 'pointer',
                      fontSize: 12,
                      fontWeight: 500,
                      opacity: actionLoading ? 0.5 : 1,
                    }}
                  >
                    {actionLoading ? 'Processing...' : 'Suspend Account'}
                  </button>
                )}

                {selectedCustomer.status === 'suspended' && (
                  <button
                    onClick={() => executeCustomerAction('unsuspend-account')}
                    disabled={actionLoading}
                    style={{
                      width: '100%',
                      padding: '8px',
                      background: 'rgba(74, 222, 128, 0.2)',
                      color: '#4ade80',
                      border: '1px solid #4ade80',
                      borderRadius: 6,
                      cursor: 'pointer',
                      fontSize: 12,
                      fontWeight: 500,
                      opacity: actionLoading ? 0.5 : 1,
                    }}
                  >
                    {actionLoading ? 'Processing...' : 'Unsuspend Account'}
                  </button>
                )}

                {/* Refund */}
                <div>
                  <label style={{ display: 'block', color: '#a8bed0', fontSize: 11, marginBottom: 6 }}>
                    Manual Refund (USD)
                  </label>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 8 }}>
                    <input
                      type="number"
                      value={refundAmount}
                      onChange={(e) => setRefundAmount(e.target.value)}
                      placeholder="Amount"
                      min="0"
                      step="0.01"
                      style={{
                        padding: '8px',
                        background: 'rgba(15, 23, 42, 0.5)',
                        border: '1px solid rgba(125, 211, 252, 0.25)',
                        borderRadius: 6,
                        color: '#e5f7ff',
                        fontSize: 12,
                      }}
                    />
                    <button
                      onClick={() => executeCustomerAction('process-refund', { amount: parseFloat(refundAmount) })}
                      disabled={!refundAmount || actionLoading}
                      style={{
                        padding: '8px 16px',
                        background: refundAmount ? 'rgba(245, 158, 11, 0.2)' : 'rgba(125, 211, 252, 0.1)',
                        color: refundAmount ? '#f59e0b' : '#a8bed0',
                        border: `1px solid ${refundAmount ? '#f59e0b' : 'rgba(125, 211, 252, 0.25)'}`,
                        borderRadius: 6,
                        cursor: refundAmount ? 'pointer' : 'not-allowed',
                        fontSize: 11,
                        fontWeight: 500,
                      }}
                    >
                      {actionLoading ? '...' : 'Refund'}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Close Button */}
            <button
              onClick={() => setSelectedCustomer(null)}
              style={{
                width: '100%',
                padding: '10px',
                background: 'rgba(125, 211, 252, 0.1)',
                color: '#7dd3fc',
                border: '1px solid rgba(125, 211, 252, 0.25)',
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 500,
              }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomerManagementTab;
