/**
 * ChainRadar — Wallet Data Hook
 * TanStack Query wrapper for SIM data with stale-while-revalidate.
 */

'use client';

import { useQuery } from '@tanstack/react-query';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchWithAuth<T>(path: string): Promise<T> {
  const token = typeof window !== 'undefined' 
    ? localStorage.getItem('chainradar_access_token') 
    : null;

  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}

export function useWalletList(enabled = true) {
  return useQuery({
    queryKey: ['wallets'],
    queryFn: () => fetchWithAuth<any[]>('/api/v1/wallets'),
    enabled,
    staleTime: 30_000, // 30s — matches SIM cache TTL
    refetchInterval: 30_000,
  });
}

export function useWalletBalance(address: string, enabled = true) {
  return useQuery({
    queryKey: ['balance', address],
    queryFn: () => fetchWithAuth<any>(`/api/v1/sim/balances/${address}`),
    enabled: enabled && !!address,
    staleTime: 30_000,
    refetchInterval: 30_000,
  });
}

export function useWalletTransactions(address: string, limit = 10, enabled = true) {
  return useQuery({
    queryKey: ['transactions', address, limit],
    queryFn: () => fetchWithAuth<any>(`/api/v1/sim/transactions/${address}?limit=${limit}`),
    enabled: enabled && !!address,
    staleTime: 300_000, // 5min — matches SIM cache TTL
  });
}

export function useAlertRules(enabled = true) {
  return useQuery({
    queryKey: ['alertRules'],
    queryFn: () => fetchWithAuth<any[]>('/api/v1/alerts'),
    enabled,
    staleTime: 60_000,
  });
}
