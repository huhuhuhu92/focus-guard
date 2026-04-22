export type DismissMode = "activity" | "manual";

export interface FocusConfig {
  idle_threshold_seconds: number;
  pre_reminder_seconds: number;
  enable_pre_reminder: boolean;
  cooldown_seconds: number;
  dismiss_mode: DismissMode;
  enable_history: boolean;
  monitor_enabled: boolean;
  poll_interval_ms: number;
  pre_reminder_message: string;
  fullscreen_message: string;
  fullscreen_topmost: boolean;
  fullscreen_overlay: boolean;
  start_minimized_to_tray: boolean;
}

export interface DashboardResponse {
  today_count: number;
  period_days: number;
  period_count: number;
  trend: Array<{ date: string; count: number }>;
  hourly: Array<{ hour: string; count: number }>;
  level_distribution: Array<{ key: string; count: number }>;
  trigger_reason_distribution: Array<{ key: string; count: number }>;
  dismiss_reason_distribution: Array<{ key: string; count: number }>;
  events: Array<Record<string, unknown>>;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8787";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    ...init
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }
  return (await res.json()) as T;
}

export async function fetchConfig(): Promise<FocusConfig> {
  const data = await request<{ config: FocusConfig }>("/api/config");
  return data.config;
}

export async function saveConfig(config: FocusConfig): Promise<FocusConfig> {
  const data = await request<{ config: FocusConfig }>("/api/config", {
    method: "PUT",
    body: JSON.stringify({ config })
  });
  return data.config;
}

export async function fetchDashboard(days = 7, eventLimit = 100): Promise<DashboardResponse> {
  return request<DashboardResponse>(
    `/api/dashboard?days=${encodeURIComponent(days)}&event_limit=${encodeURIComponent(eventLimit)}`
  );
}

export async function clearEvents(): Promise<void> {
  await request<{ ok: boolean }>("/api/events", { method: "DELETE" });
}

