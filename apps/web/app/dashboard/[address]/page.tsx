/**
 * WaspNet — Wallet Detail Page
 * Shows balance, transaction history, and alert rules for a specific wallet.
 * SIM: Uses all 3 GET endpoints for this view.
 */

'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';

// Demo data
const DEMO_TRANSACTIONS = [
  { sig: '5xR3...kF2', type: 'Transfer', amount: 2500, direction: 'out', time: '2 min ago', status: 'confirmed' },
  { sig: '3mK7...vB9', type: 'Swap', amount: 150, direction: 'in', time: '15 min ago', status: 'confirmed' },
  { sig: '8pQ1...wD4', type: 'Transfer', amount: 45, direction: 'in', time: '1 hr ago', status: 'confirmed' },
  { sig: '2nL5...xE7', type: 'Stake', amount: 1000, direction: 'out', time: '3 hr ago', status: 'confirmed' },
  { sig: '7jH9...yG3', type: 'Transfer', amount: 230, direction: 'out', time: '5 hr ago', status: 'confirmed' },
];

const DEMO_TOKENS = [
  { symbol: 'SOL', amount: 45892.34, usd: 4589234, change: 2.4 },
  { symbol: 'USDC', amount: 125000, usd: 125000, change: 0 },
  { symbol: 'BONK', amount: 8500000, usd: 1275, change: 15.2 },
  { symbol: 'JUP', amount: 15000, usd: 12750, change: -3.1 },
];

export default function WalletDetailPage() {
  const params = useParams();
  const address = params.address as string;
  const shortAddr = address ? `${address.slice(0, 6)}...${address.slice(-4)}` : '';

  return (
    <div className="min-h-screen">
      {/* Top Bar */}
      <header className="border-b border-surface-border/30 bg-surface/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-4">
          <Link href="/dashboard" className="text-white/40 hover:text-white transition-colors">
            ← Back
          </Link>
          <div className="flex items-center gap-3">
            <div className="relative w-8 h-8">
              <div className="absolute inset-0 bg-radar-500 rounded-full opacity-40" />
              <div className="absolute inset-1 bg-radar-400 rounded-full" />
            </div>
            <span className="text-lg font-bold">WaspNet</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Wallet Header */}
        <div className="glass-card p-8 mb-8">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-2xl font-bold">Phantom Whale #1</h1>
                <span className="badge badge-info">solana</span>
                <span className="status-dot live" />
              </div>
              <code className="text-white/40 font-mono text-sm">{address}</code>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-white">45,892.34 SOL</div>
              <div className="text-accent-green text-sm font-medium">↑ 2.4% (24h)</div>
              <div className="text-white/30 text-sm">≈ $4,589,234 USD</div>
            </div>
          </div>

          {/* Network Toggle */}
          <div className="flex items-center gap-2 mt-6 pt-6 border-t border-surface-border/30">
            <button className="px-4 py-2 rounded-lg bg-radar-500/20 text-radar-300 text-sm font-medium border border-radar-500/30">
              Solana
            </button>
            <button className="px-4 py-2 rounded-lg hover:bg-white/5 text-white/40 text-sm font-medium transition-colors">
              EVM Cross-Chain
            </button>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Token Balances */}
          <div className="lg:col-span-1">
            <h2 className="text-lg font-semibold mb-4">Token Balances</h2>
            <div className="space-y-3">
              {DEMO_TOKENS.map((token) => (
                <div key={token.symbol} className="glass-card p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-white">{token.symbol}</div>
                      <div className="text-sm text-white/40">
                        {token.amount.toLocaleString()}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-white">
                        ${token.usd.toLocaleString()}
                      </div>
                      <div className={`text-xs ${token.change >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                        {token.change >= 0 ? '+' : ''}{token.change}%
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Transaction Feed */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Recent Transactions</h2>
              <span className="text-sm text-white/40">SIM: Real-time feed</span>
            </div>

            <div className="glass-card overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-surface-border/30">
                    <th className="text-left text-xs text-white/40 font-medium p-4">Signature</th>
                    <th className="text-left text-xs text-white/40 font-medium p-4">Type</th>
                    <th className="text-right text-xs text-white/40 font-medium p-4">Amount</th>
                    <th className="text-right text-xs text-white/40 font-medium p-4">Time</th>
                    <th className="text-right text-xs text-white/40 font-medium p-4">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {DEMO_TRANSACTIONS.map((tx) => (
                    <tr key={tx.sig} className="border-b border-surface-border/20 hover:bg-white/[0.02] transition-colors">
                      <td className="p-4">
                        <code className="text-sm font-mono text-radar-300">{tx.sig}</code>
                      </td>
                      <td className="p-4 text-sm text-white/60">{tx.type}</td>
                      <td className="p-4 text-right">
                        <span className={`text-sm font-medium ${tx.direction === 'in' ? 'text-accent-green' : 'text-accent-red'}`}>
                          {tx.direction === 'in' ? '+' : '-'}{tx.amount.toLocaleString()} SOL
                        </span>
                      </td>
                      <td className="p-4 text-right text-sm text-white/40">{tx.time}</td>
                      <td className="p-4 text-right">
                        <span className="text-xs px-2 py-1 rounded-full bg-accent-green/20 text-accent-green">
                          {tx.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
