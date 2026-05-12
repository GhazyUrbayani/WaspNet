import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'WaspNet — Real-time Onchain Monitoring',
  description: 'PagerDuty for Solana. Monitor wallets, set smart alerts, get notified in real-time via Telegram, email, or in-app.',
  keywords: ['solana', 'blockchain', 'monitoring', 'alerts', 'defi', 'wallet tracker'],
  openGraph: {
    title: 'WaspNet — PagerDuty for Solana',
    description: 'Real-time onchain monitoring and smart alert system',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="icon" href="/favicon.ico" />
        <meta name="theme-color" content="#0a0a1a" />
      </head>
      <body className="min-h-screen bg-surface bg-grid">
        {children}
      </body>
    </html>
  );
}
