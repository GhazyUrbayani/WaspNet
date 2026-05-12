/**
 * ChainRadar — Dashboard Page
 * Main watchlist overview with wallet cards, live indicators, and alert feed.
 */

'use client';

import { useState, useCallback } from 'react';
import { useAlertStream } from '@/hooks/useAlertStream';
import Link from 'next/link';

// Mock data for demo (replace with real API calls via TanStack Query)
const DEMO_WALLETS = [
  {
    id: '1',
    address: '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM',
    network: 'solana',
    label: 'Phantom Whale #1',
    balance: 45892.34,
    change24h: 2.4,
    activeRules: 3,
    lastAlert: '2 min ago',
  },
  {
    id: '2',
    address: 'DRpbCBMxVnDK7maPMoGzfnBHGsQrqS4dPjSsaQqzDhVj',
    network: 'solana',
    label: 'Jupiter Treasury',
    balance: 128450.78,
    change24h: -1.2,
    activeRules: 5,
    lastAlert: '15 min ago',
  },
  {
    id: '3',
    address: 'HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH',
    network: 'solana',
    label: 'Raydium Pool',
    balance: 892100.15,
    change24h: 0.8,
    activeRules: 2,
    lastAlert: '1 hr ago',
  },
];

const DEMO_ALERTS = [
  { id: '1', severity: 'critical', rule: 'Large Transfer Alert', wallet: '9WzD...WWM', summary: 'Transfer of 2,500 SOL detected', time: '2 min ago' },
  { id: '2', severity: 'warning', rule: 'Balance Drop Alert', wallet: 'DRpb...DVj', summary: 'Balance dropped below 130,000 SOL', time: '15 min ago' },
  { id: '3', severity: 'info', rule: 'New Token Alert', wallet: 'HN7c...WrH', summary: 'New token BONK appeared in wallet', time: '1 hr ago' },
  { id: '4', severity: 'warning', rule: 'Whale Movement', wallet: '9WzD...WWM', summary: 'Whale moved 1,200 SOL to exchange', time: '2 hr ago' },
];

export default function DashboardPage() {
  const [showAddWallet, setShowAddWallet] = useState(false);
  const [newAddress, setNewAddress] = useState('');
  const [newLabel, setNewLabel] = useState('');

  const { isConnected, events } = useAlertStream({
    enabled: true,
    onEvent: (event) => {
      if (event.type === 'alert') {
        // Could show toast notification here
        console.log('Alert received:', event.data);
      }
    },
  });

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
            <span className="text-lg font-bold">ChainRadar</span>
          </div>

          <div className="flex items-center gap-6">
            {/* Live indicator */}
            <div className="flex items-center gap-2">
              <span className={`status-dot ${isConnected ? 'live' : 'warning'}`} />
              <span className="text-sm text-white/50">
                {isConnected ? 'Live' : 'Connecting...'}
              </span>
            </div>

            <nav className="flex items-center gap-1">
              <Link href="/dashboard" className="px-4 py-2 rounded-lg bg-white/10 text-white text-sm font-medium">
                Watchlist
              </Link>
              <Link href="/dashboard/alerts" className="px-4 py-2 rounded-lg hover:bg-white/5 text-white/60 text-sm font-medium transition-colors">
                Alert Rules
              </Link>
            </nav>

            <button className="btn-ghost text-sm" onClick={() => {
              if (typeof window !== 'undefined') {
                localStorage.removeItem('chainradar_access_token');
                localStorage.removeItem('chainradar_refresh_token');
                window.location.href = '/login';
              }
            }}>
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Dashboard Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">Watchlist</h1>
            <p className="text-white/40 mt-1">Monitor wallet activity in real-time</p>
          </div>
          <button
            id="add-wallet-btn"
            onClick={() => setShowAddWallet(!showAddWallet)}
            className="btn-primary"
          >
            + Add Wallet
          </button>
        </div>

        {/* Add Wallet Form */}
        {showAddWallet && (
          <div className="glass-card p-6 mb-8 animate-slide-up">
            <h3 className="text-lg font-semibold mb-4">Add Wallet to Watchlist</h3>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm text-white/60 mb-1.5">Wallet Address</label>
                <input
                  id="wallet-address-input"
                  type="text"
                  value={newAddress}
                  onChange={(e) => setNewAddress(e.target.value)}
                  className="input-dark w-full font-mono text-sm"
                  placeholder="Paste Solana address..."
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-1.5">Label (optional)</label>
                <input
                  id="wallet-label-input"
                  type="text"
                  value={newLabel}
                  onChange={(e) => setNewLabel(e.target.value)}
                  className="input-dark w-full"
                  placeholder="e.g. Phantom Whale"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-4">
              <button id="save-wallet-btn" className="btn-primary">Track Wallet</button>
              <button className="btn-ghost" onClick={() => setShowAddWallet(false)}>Cancel</button>
            </div>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Tracked Wallets', value: '3', icon: '👛' },
            { label: 'Active Rules', value: '10', icon: '📋' },
            { label: 'Alerts Today', value: '7', icon: '🔔' },
            { label: 'Avg Response', value: '1.2s', icon: '⚡' },
          ].map((stat) => (
            <div key={stat.label} className="glass-card p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl">{stat.icon}</span>
                <span className="text-2xl font-bold text-white">{stat.value}</span>
              </div>
              <span className="text-sm text-white/40">{stat.label}</span>
            </div>
          ))}
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Wallet Cards */}
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-lg font-semibold text-white/80">Monitored Wallets</h2>
            {DEMO_WALLETS.map((wallet) => (
              <Link
                key={wallet.id}
                href={`/dashboard/${wallet.address}`}
                className="glass-card p-6 block hover:glow-border transition-all duration-300 group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-white group-hover:text-radar-300 transition-colors">
                        {wallet.label}
                      </h3>
                      <span className="badge badge-info text-[10px]">{wallet.network}</span>
                      <span className="status-dot live" />
                    </div>
                    <code className="text-sm text-white/40 font-mono">
                      {wallet.address.slice(0, 8)}...{wallet.address.slice(-6)}
                    </code>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold text-white">
                      {wallet.balance.toLocaleString()} SOL
                    </div>
                    <div className={`text-sm font-medium ${wallet.change24h >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                      {wallet.change24h >= 0 ? '↑' : '↓'} {Math.abs(wallet.change24h)}%
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-6 mt-4 pt-4 border-t border-surface-border/30">
                  <div className="flex items-center gap-2 text-sm text-white/40">
                    <span>📋</span>
                    <span>{wallet.activeRules} active rules</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-white/40">
                    <span>🔔</span>
                    <span>Last alert: {wallet.lastAlert}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          {/* Alert Feed */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white/80">Recent Alerts</h2>
              <span className="status-dot live" />
            </div>

            <div className="space-y-3">
              {DEMO_ALERTS.map((alert) => (
                <div key={alert.id} className="glass-card p-4 animate-fade-in">
                  <div className="flex items-start gap-3">
                    <div className={`status-dot mt-1.5 ${alert.severity}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-white">{alert.rule}</span>
                        <span className={`badge badge-${alert.severity} text-[10px]`}>
                          {alert.severity}
                        </span>
                      </div>
                      <p className="text-sm text-white/50">{alert.summary}</p>
                      <div className="flex items-center gap-2 mt-2 text-xs text-white/30">
                        <code className="font-mono">{alert.wallet}</code>
                        <span>•</span>
                        <span>{alert.time}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Live event stream indicator */}
            {events.length > 0 && (
              <div className="glass-card p-4 glow-border">
                <div className="flex items-center gap-2 mb-2">
                  <span className="status-dot live" />
                  <span className="text-sm font-medium text-radar-300">Live Event Stream</span>
                </div>
                <p className="text-xs text-white/40">
                  {events.length} events received this session
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
