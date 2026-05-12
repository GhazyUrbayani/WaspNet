/**
 * ChainRadar — Landing Page
 * Premium hero section with radar animation and feature overview.
 */

import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="min-h-screen relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 bg-gradient-to-b from-radar-950/50 via-transparent to-transparent" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-radar-500/5 rounded-full blur-3xl" />

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10">
            <div className="absolute inset-0 bg-radar-500 rounded-full opacity-20 animate-ping" />
            <div className="absolute inset-1 bg-radar-500 rounded-full opacity-40" />
            <div className="absolute inset-2 bg-radar-400 rounded-full" />
            <div className="absolute inset-0 w-full h-full radar-sweep">
              <div className="absolute top-1/2 left-1/2 w-1/2 h-0.5 bg-gradient-to-r from-radar-400 to-transparent origin-left -translate-y-1/2" />
            </div>
          </div>
          <span className="text-xl font-bold text-white">ChainRadar</span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="btn-ghost text-sm">Dashboard</Link>
          <Link href="/login" className="btn-primary text-sm">Get Started</Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 flex flex-col items-center justify-center min-h-[80vh] px-6 text-center">
        <div className="animate-fade-in">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-radar-500/10 border border-radar-500/20 mb-8">
            <span className="status-dot live" />
            <span className="text-sm text-radar-300">Powered by Dune SIM API</span>
          </div>

          <h1 className="text-5xl sm:text-7xl font-extrabold leading-tight mb-6 max-w-4xl">
            <span className="text-gradient">PagerDuty</span>{' '}
            <span className="text-white">for</span>{' '}
            <span className="text-gradient">Solana</span>
          </h1>

          <p className="text-xl text-white/60 max-w-2xl mx-auto mb-10 leading-relaxed">
            Real-time onchain monitoring and smart alert system. 
            Track wallets, set custom rules, get notified via Telegram, email, or in-app — instantly.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4 justify-center">
            <Link href="/login" className="btn-primary text-lg px-8 py-3">
              Start Monitoring →
            </Link>
            <Link href="#features" className="btn-ghost text-lg px-8 py-3">
              How It Works
            </Link>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-8 mt-20 animate-slide-up">
          {[
            { label: 'Wallets Tracked', value: '10K+' },
            { label: 'Alerts Delivered', value: '1M+' },
            { label: 'Avg Latency', value: '<2s' },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-3xl font-bold text-white">{stat.value}</div>
              <div className="text-sm text-white/40 mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative z-10 max-w-7xl mx-auto px-6 py-24">
        <h2 className="text-3xl font-bold text-center mb-16">
          Built for <span className="text-gradient">Protocol Teams, DAOs & Traders</span>
        </h2>

        <div className="grid md:grid-cols-3 gap-6">
          {[
            {
              icon: '🛡️',
              title: 'Drain Detection',
              desc: 'Alert when liquidity drains from your protocol pools. Real-time SIM webhook monitoring.',
              tag: 'Protocol Teams',
            },
            {
              icon: '🐋',
              title: 'Whale Tracking',
              desc: 'Know when whale addresses start dumping your treasury token. Set threshold alerts.',
              tag: 'DAO Treasuries',
            },
            {
              icon: '📊',
              title: 'Smart Alerts',
              desc: 'Custom rules: balance changes, large transfers, program interactions. Delivered instantly.',
              tag: 'Traders',
            },
          ].map((feature) => (
            <div key={feature.title} className="glass-card p-8 hover:glow-border transition-all duration-300 group">
              <div className="text-4xl mb-4">{feature.icon}</div>
              <div className="badge badge-info mb-4">{feature.tag}</div>
              <h3 className="text-xl font-semibold text-white mb-3 group-hover:text-radar-300 transition-colors">
                {feature.title}
              </h3>
              <p className="text-white/50 leading-relaxed">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture Preview */}
      <section className="relative z-10 max-w-5xl mx-auto px-6 py-16">
        <div className="glass-card p-8">
          <h3 className="text-lg font-semibold text-radar-300 mb-6">Data Pipeline</h3>
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-center">
            {[
              { step: '1', label: 'Dune SIM API', sub: 'Balances + Transactions + Webhooks' },
              { step: '2', label: 'Rule Engine', sub: 'Evaluate conditions in real-time' },
              { step: '3', label: 'Alert Delivery', sub: 'Telegram / Email / In-App' },
            ].map((item, i) => (
              <div key={item.step} className="flex items-center gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 rounded-full bg-radar-500/20 border border-radar-500/40 flex items-center justify-center text-radar-300 font-bold">
                    {item.step}
                  </div>
                  <div className="mt-3 font-medium text-white">{item.label}</div>
                  <div className="text-sm text-white/40 mt-1">{item.sub}</div>
                </div>
                {i < 2 && (
                  <div className="hidden md:block text-radar-500/40 text-2xl">→</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-surface-border/30 py-8 px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-sm text-white/30">
          <span>© 2024 ChainRadar. Built for Dune SIM Hackathon.</span>
          <div className="flex gap-4">
            <a href="https://github.com" className="hover:text-white/60 transition-colors">GitHub</a>
            <a href="https://docs.dune.com" className="hover:text-white/60 transition-colors">Dune Docs</a>
          </div>
        </div>
      </footer>
    </main>
  );
}
