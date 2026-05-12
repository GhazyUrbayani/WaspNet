/**
 * WaspNet — API Client
 * Typed wrapper for Next.js → FastAPI backend communication.
 * SIM: Data flows through backend which calls Dune SIM API.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ─── Types ──────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfile {
  id: string;
  email: string;
  username: string;
  is_verified: boolean;
  tier: string;
}

export interface WatchedWallet {
  id: string;
  address: string;
  network: string;
  label: string | null;
  is_active: boolean;
  last_balance_lamports: number | null;
  created_at: string;
}

export interface AlertCondition {
  condition_type: string;
  threshold: number;
  comparison: string;
  token_mint?: string;
  program_id?: string;
}

export interface AlertRule {
  id: string;
  name: string;
  wallet_id: string;
  conditions: AlertCondition[];
  severity: string;
  delivery_channels: string[];
  is_active: boolean;
  cooldown_minutes: number;
  trigger_count: number;
  last_triggered_at: string | null;
  created_at: string;
}

export interface WalletBalance {
  lamports: number;
  sol: number;
  tokens: Array<{
    mint: string;
    symbol: string;
    amount: number;
    decimals: number;
    usd_value: number;
  }>;
}

export interface Transaction {
  signature: string;
  block_time: number;
  type: string;
  amount: number;
  from: string;
  to: string;
  status: string;
}

// ─── API Client ─────────────────────────────────────────────

class WaspNetAPI {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('waspnet_access_token');
      this.refreshToken = localStorage.getItem('waspnet_refresh_token');
    }
  }

  private async fetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (response.status === 401 && this.refreshToken) {
      // Try to refresh token
      const refreshed = await this.refreshTokens();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.accessToken}`;
        const retryResponse = await fetch(`${API_BASE}${path}`, { ...options, headers });
        if (!retryResponse.ok) throw new APIError(retryResponse.status, await retryResponse.text());
        return retryResponse.json();
      }
    }

    if (!response.ok) {
      const errorText = await response.text();
      throw new APIError(response.status, errorText);
    }

    if (response.status === 204) return {} as T;
    return response.json();
  }

  // ─── Auth ────────────────────────────────────────────────

  setTokens(tokens: TokenResponse) {
    this.accessToken = tokens.access_token;
    this.refreshToken = tokens.refresh_token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('waspnet_access_token', tokens.access_token);
      localStorage.setItem('waspnet_refresh_token', tokens.refresh_token);
    }
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('waspnet_access_token');
      localStorage.removeItem('waspnet_refresh_token');
    }
  }

  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  async register(email: string, username: string, password: string): Promise<TokenResponse> {
    const tokens = await this.fetch<TokenResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, username, password }),
    });
    this.setTokens(tokens);
    return tokens;
  }

  async login(email: string, password: string): Promise<TokenResponse> {
    const tokens = await this.fetch<TokenResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setTokens(tokens);
    return tokens;
  }

  async refreshTokens(): Promise<boolean> {
    try {
      const tokens = await this.fetch<TokenResponse>('/api/v1/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });
      this.setTokens(tokens);
      return true;
    } catch {
      this.clearTokens();
      return false;
    }
  }

  async getProfile(): Promise<UserProfile> {
    return this.fetch<UserProfile>('/api/v1/auth/me');
  }

  // ─── Wallets ─────────────────────────────────────────────

  async addWallet(address: string, network = 'solana', label?: string): Promise<WatchedWallet> {
    return this.fetch<WatchedWallet>('/api/v1/wallets', {
      method: 'POST',
      body: JSON.stringify({ address, network, label }),
    });
  }

  async listWallets(activeOnly = true): Promise<WatchedWallet[]> {
    return this.fetch<WatchedWallet[]>(`/api/v1/wallets?active_only=${activeOnly}`);
  }

  async deleteWallet(walletId: string): Promise<void> {
    await this.fetch(`/api/v1/wallets/${walletId}`, { method: 'DELETE' });
  }

  // ─── Alert Rules ────────────────────────────────────────

  async createAlertRule(data: {
    name: string;
    wallet_id: string;
    conditions: AlertCondition[];
    severity?: string;
    delivery_channels?: string[];
    cooldown_minutes?: number;
  }): Promise<AlertRule> {
    return this.fetch<AlertRule>('/api/v1/alerts', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async listAlertRules(activeOnly = true): Promise<AlertRule[]> {
    return this.fetch<AlertRule[]>(`/api/v1/alerts?active_only=${activeOnly}`);
  }

  async toggleAlertRule(ruleId: string, isActive: boolean): Promise<AlertRule> {
    return this.fetch<AlertRule>(`/api/v1/alerts/${ruleId}?is_active=${isActive}`, {
      method: 'PATCH',
    });
  }

  async deleteAlertRule(ruleId: string): Promise<void> {
    await this.fetch(`/api/v1/alerts/${ruleId}`, { method: 'DELETE' });
  }
}

export class APIError extends Error {
  constructor(public status: number, public body: string) {
    super(`API Error ${status}: ${body}`);
  }
}

// Singleton
export const api = new WaspNetAPI();
