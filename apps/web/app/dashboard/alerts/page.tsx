/**
 * WaspNet — Alert Rules Page
 * Create, manage, and monitor alert rules.
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';

const CONDITION_TYPES = [
  { value: 'balance_above', label: 'Balance Above', unit: 'SOL' },
  { value: 'balance_below', label: 'Balance Below', unit: 'SOL' },
  { value: 'balance_change', label: 'Balance Change', unit: '%' },
  { value: 'large_transfer', label: 'Large Transfer', unit: 'SOL' },
  { value: 'whale_movement', label: 'Whale Movement', unit: 'SOL' },
  { value: 'token_transfer', label: 'Token Transfer', unit: 'tokens' },
  { value: 'new_token', label: 'New Token Detected', unit: '' },
  { value: 'program_interaction', label: 'Program Interaction', unit: '' },
];

const DEMO_RULES = [
  {
    id: '1', name: 'Large Transfer Alert', wallet: 'Phantom Whale #1',
    conditions: [{ type: 'large_transfer', threshold: 500 }],
    severity: 'critical', channels: ['telegram', 'in_app'],
    isActive: true, triggerCount: 12, lastTriggered: '2 min ago',
  },
  {
    id: '2', name: 'Balance Drop Alert', wallet: 'Jupiter Treasury',
    conditions: [{ type: 'balance_below', threshold: 100000 }],
    severity: 'warning', channels: ['email', 'in_app'],
    isActive: true, triggerCount: 3, lastTriggered: '15 min ago',
  },
  {
    id: '3', name: 'New Token Monitor', wallet: 'Raydium Pool',
    conditions: [{ type: 'new_token', threshold: 0 }],
    severity: 'info', channels: ['in_app'],
    isActive: false, triggerCount: 45, lastTriggered: '1 hr ago',
  },
];

export default function AlertRulesPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [ruleName, setRuleName] = useState('');
  const [conditionType, setConditionType] = useState('large_transfer');
  const [threshold, setThreshold] = useState('500');
  const [severity, setSeverity] = useState('warning');
  const [channels, setChannels] = useState(['in_app']);

  const toggleChannel = (channel: string) => {
    setChannels((prev) =>
      prev.includes(channel) ? prev.filter((c) => c !== channel) : [...prev, channel]
    );
  };

  return (
    <div className="min-h-screen">
      {/* Top Bar */}
      <header className="border-b border-surface-border/30 bg-surface/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative w-8 h-8">
              <div className="absolute inset-0 bg-radar-500 rounded-full opacity-40" />
              <div className="absolute inset-1 bg-radar-400 rounded-full" />
            </div>
            <span className="text-lg font-bold">WaspNet</span>
          </div>
          <nav className="flex items-center gap-1">
            <Link href="/dashboard" className="px-4 py-2 rounded-lg hover:bg-white/5 text-white/60 text-sm font-medium transition-colors">
              Watchlist
            </Link>
            <Link href="/dashboard/alerts" className="px-4 py-2 rounded-lg bg-white/10 text-white text-sm font-medium">
              Alert Rules
            </Link>
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">Alert Rules</h1>
            <p className="text-white/40 mt-1">Configure conditions that trigger notifications</p>
          </div>
          <button
            id="create-rule-btn"
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="btn-primary"
          >
            + Create Rule
          </button>
        </div>

        {/* Create Rule Form */}
        {showCreateForm && (
          <div className="glass-card p-6 mb-8 animate-slide-up">
            <h3 className="text-lg font-semibold mb-6">Create Alert Rule</h3>
            <div className="space-y-5">
              <div>
                <label className="block text-sm text-white/60 mb-1.5">Rule Name</label>
                <input
                  id="rule-name-input"
                  type="text"
                  value={ruleName}
                  onChange={(e) => setRuleName(e.target.value)}
                  className="input-dark w-full"
                  placeholder='e.g. "Alert if transfer > 500 SOL"'
                />
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-white/60 mb-1.5">Condition Type</label>
                  <select
                    id="condition-type-select"
                    value={conditionType}
                    onChange={(e) => setConditionType(e.target.value)}
                    className="input-dark w-full"
                  >
                    {CONDITION_TYPES.map((ct) => (
                      <option key={ct.value} value={ct.value}>{ct.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-white/60 mb-1.5">Threshold</label>
                  <input
                    id="threshold-input"
                    type="number"
                    value={threshold}
                    onChange={(e) => setThreshold(e.target.value)}
                    className="input-dark w-full"
                    placeholder="500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm text-white/60 mb-1.5">Severity</label>
                <div className="flex gap-3">
                  {['critical', 'warning', 'info'].map((s) => (
                    <button
                      key={s}
                      onClick={() => setSeverity(s)}
                      className={`badge ${severity === s ? `badge-${s}` : 'bg-white/5 text-white/40 border border-white/10'} cursor-pointer transition-all`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm text-white/60 mb-1.5">Delivery Channels</label>
                <div className="flex gap-3">
                  {[
                    { key: 'telegram', label: '📱 Telegram', icon: '' },
                    { key: 'email', label: '📧 Email', icon: '' },
                    { key: 'in_app', label: '🔔 In-App', icon: '' },
                    { key: 'webhook', label: '🔗 Webhook', icon: '' },
                  ].map((ch) => (
                    <button
                      key={ch.key}
                      onClick={() => toggleChannel(ch.key)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                        channels.includes(ch.key)
                          ? 'bg-radar-500/20 text-radar-300 border border-radar-500/30'
                          : 'bg-white/5 text-white/40 border border-white/10 hover:bg-white/10'
                      }`}
                    >
                      {ch.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button id="save-rule-btn" className="btn-primary">Create Rule</button>
                <button className="btn-ghost" onClick={() => setShowCreateForm(false)}>Cancel</button>
              </div>
            </div>
          </div>
        )}

        {/* Existing Rules */}
        <div className="space-y-4">
          {DEMO_RULES.map((rule) => (
            <div key={rule.id} className={`glass-card p-6 transition-all duration-300 ${rule.isActive ? '' : 'opacity-50'}`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold text-white">{rule.name}</h3>
                    <span className={`badge badge-${rule.severity}`}>{rule.severity}</span>
                    {rule.isActive && <span className="status-dot live" />}
                  </div>
                  <div className="text-sm text-white/40 mb-3">Wallet: {rule.wallet}</div>

                  <div className="flex flex-wrap gap-2 mb-3">
                    {rule.conditions.map((c, i) => (
                      <span key={i} className="px-3 py-1 rounded-lg bg-surface-elevated text-sm text-white/60 border border-surface-border/30">
                        {c.type.replace('_', ' ')}: {c.threshold > 0 ? `${c.threshold} SOL` : 'Any'}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center gap-4 text-xs text-white/30">
                    <span>📊 {rule.triggerCount} triggers</span>
                    <span>⏱️ Last: {rule.lastTriggered}</span>
                    <span>📬 {rule.channels.join(', ')}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    className={`relative w-12 h-6 rounded-full transition-colors ${
                      rule.isActive ? 'bg-radar-500' : 'bg-surface-border'
                    }`}
                  >
                    <div
                      className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
                        rule.isActive ? 'translate-x-6' : 'translate-x-0.5'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
