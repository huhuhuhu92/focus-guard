import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { RefreshCw } from "lucide-react";

import { fetchDashboard, type DashboardResponse } from "@/api/client";

const BG = "#ECECEC";
const TEXT = "#3A3A3A";
const MUTED = "#A8A8A8";
const SUB = "#7A7A7A";
const ACCENT = "#3A3A3A";
const SOFT = "#B4BCC4";
const SHADOW_OUT = "8px 8px 20px #c9cfd6, -8px -8px 20px #ffffff";
const SHADOW_OUT_SM = "3px 3px 8px #c9cfd6, -3px -3px 8px #ffffff";
const SHADOW_IN_SM = "inset 3px 3px 6px #c9cfd6, inset -3px -3px 6px #ffffff";

type EventRow = {
  triggered_at?: string;
  level?: string;
  idle_seconds?: number;
  media_state?: string;
  dismiss_reason?: string;
  trigger_reason?: string;
  foreground_app?: string;
};

const Card = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <div className={`rounded-[22px] ${className}`} style={{ background: BG, boxShadow: SHADOW_OUT }}>
    {children}
  </div>
);

const Label = ({ children }: { children: React.ReactNode }) => (
  <div className="text-[9px] tracking-[0.22em] uppercase" style={{ color: MUTED }}>
    {children}
  </div>
);

const SectionTitle = ({ title, hint }: { title: string; hint: string }) => (
  <div className="flex items-baseline justify-between mb-3">
    <h3 className="text-[12px]" style={{ color: TEXT, fontWeight: 500 }}>
      {title}
    </h3>
    <Label>{hint}</Label>
  </div>
);

function mapLevelLabel(key: string): string {
  if (key === "fullscreen_reminder") return "强提醒";
  if (key === "pre_reminder") return "轻提醒";
  return key;
}

function mapReasonLabel(key: string): string {
  const labels: Record<string, string> = {
    idle_reached_pre_threshold: "达到轻提醒阈值",
    idle_reached_fullscreen_threshold: "达到强提醒阈值",
    cooldown_pre_reminder: "冷却期轻提醒",
    auto: "自动关闭",
    activity: "输入关闭",
    manual: "手动关闭",
    pending: "待关闭",
    unknown: "未知"
  };
  return labels[key] ?? key;
}

function formatTime(value?: string): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString("zh-CN", { hour12: false });
}

export function Statistics() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const dashboard = await fetchDashboard(7, 100);
      setData(dashboard);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const trendData = useMemo(() => data?.trend ?? [], [data]);
  const hourData = useMemo(
    () => (data?.hourly ?? []).map((item) => ({ hour: `${item.hour}h`, count: item.count })),
    [data]
  );
  const levelData = useMemo(
    () =>
      (data?.level_distribution ?? []).map((item, idx) => ({
        name: mapLevelLabel(item.key),
        value: item.count,
        color: idx === 0 ? ACCENT : SOFT
      })),
    [data]
  );
  const reasonData = useMemo(
    () =>
      (data?.trigger_reason_distribution ?? []).map((item, idx) => ({
        name: mapReasonLabel(item.key),
        value: item.count,
        color: idx % 2 === 0 ? ACCENT : SOFT
      })),
    [data]
  );

  const events: EventRow[] = (data?.events as EventRow[]) ?? [];

  const tooltipStyle = {
    background: BG,
    border: "none",
    borderRadius: "12px",
    boxShadow: SHADOW_OUT_SM,
    fontSize: "11px",
    color: TEXT
  };

  const PieBlock = ({
    dataSource,
    title,
    hint
  }: {
    dataSource: Array<{ name: string; value: number; color: string }>;
    title: string;
    hint: string;
  }) => (
    <Card className="px-5 py-5 h-full">
      <SectionTitle title={title} hint={hint} />
      <div className="flex items-center gap-3">
        <div className="w-16 h-16 shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={dataSource} cx="50%" cy="50%" innerRadius={18} outerRadius={30} dataKey="value" nameKey="name" strokeWidth={0} isAnimationActive={false}>
                {dataSource.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="space-y-1.5 flex-1 min-w-0">
          {dataSource.length === 0 ? (
            <div className="text-[11px]" style={{ color: MUTED }}>
              暂无数据
            </div>
          ) : (
            dataSource.map((item) => (
              <div key={item.name} className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: item.color }} />
                <span className="text-[11px] truncate" style={{ color: SUB }}>
                  {item.name}
                </span>
                <span className="text-[11px] ml-auto tabular-nums" style={{ color: MUTED }}>
                  {item.value}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </Card>
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
      <div className="col-span-1 md:col-span-6">
        <Card className="px-6 py-5 flex items-end justify-between">
          <div className="flex items-baseline gap-6">
            <div>
              <Label>今日提醒</Label>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="text-[40px] tabular-nums leading-none" style={{ color: TEXT, fontWeight: 300 }}>
                  {data?.today_count ?? 0}
                </span>
                <span className="text-[11px]" style={{ color: MUTED }}>
                  次
                </span>
              </div>
            </div>
            <div>
              <Label>近 7 天提醒</Label>
              <div className="text-[20px] mt-1 tabular-nums" style={{ color: TEXT, fontWeight: 400 }}>
                {data?.period_count ?? 0}
              </div>
            </div>
          </div>
          <button
            onClick={() => void load()}
            className="flex items-center gap-2 px-4 py-2 rounded-full active:scale-[0.98] transition-all"
            style={{ background: BG, boxShadow: SHADOW_OUT_SM, color: SUB }}
          >
            <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
            <span className="text-[11px]">刷新</span>
          </button>
        </Card>
      </div>

      <div className="col-span-1 md:col-span-4">
        <Card className="px-5 py-4">
          <SectionTitle title="最近 7 天提醒趋势" hint="7 DAYS" />
          <div className="h-24">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData} margin={{ top: 5, right: 5, left: -28, bottom: 0 }}>
                <XAxis dataKey="date" tick={{ fill: MUTED, fontSize: 9 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: MUTED, fontSize: 9 }} axisLine={false} tickLine={false} width={30} />
                <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: SUB }} cursor={{ stroke: MUTED, strokeDasharray: "2 4" }} />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke={ACCENT}
                  strokeWidth={1.5}
                  dot={{ fill: BG, stroke: ACCENT, strokeWidth: 1.5, r: 3 }}
                  activeDot={{ r: 5, fill: ACCENT }}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <div className="col-span-1 md:col-span-2">
        <PieBlock dataSource={levelData} title="提醒等级占比" hint="LEVEL" />
      </div>

      <div className="col-span-1 md:col-span-4">
        <Card className="px-5 py-4">
          <SectionTitle title="今日 24 小时提醒分布" hint="TODAY" />
          <div className="h-24">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={hourData} margin={{ top: 5, right: 5, left: -28, bottom: 0 }}>
                <XAxis dataKey="hour" tick={{ fill: MUTED, fontSize: 9 }} axisLine={false} tickLine={false} interval={2} />
                <YAxis tick={{ fill: MUTED, fontSize: 9 }} axisLine={false} tickLine={false} width={30} />
                <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: SUB }} cursor={{ fill: "rgba(0,0,0,0.03)" }} />
                <Bar dataKey="count" fill={ACCENT} radius={[3, 3, 0, 0]} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <div className="col-span-1 md:col-span-2">
        <PieBlock dataSource={reasonData} title="触发原因占比" hint="REASON" />
      </div>

      <div className="col-span-1 md:col-span-6">
        <Card className="px-5 py-4">
          <SectionTitle title="最近提醒事件" hint={error ? `ERROR: ${error}` : "RECENT"} />
          <div className="rounded-[14px] overflow-hidden" style={{ background: BG, boxShadow: SHADOW_IN_SM }}>
            <div
              className="grid text-[9px] tracking-widest uppercase px-4 py-2.5 whitespace-nowrap"
              style={{
                color: MUTED,
                gridTemplateColumns: "96px 48px 80px 64px 64px 64px 1fr",
                gap: "12px"
              }}
            >
              <span>时间</span>
              <span>等级</span>
              <span>触发</span>
              <span className="text-right">空闲</span>
              <span>媒体</span>
              <span>关闭</span>
              <span>前台进程</span>
            </div>
            <div className="max-h-[180px] overflow-y-auto">
              {events.length === 0 ? (
                <div className="px-4 py-4 text-[11px]" style={{ color: MUTED }}>
                  暂无事件
                </div>
              ) : (
                events.map((e, i) => (
                  <div
                    key={`${e.triggered_at ?? "row"}-${i}`}
                    className="grid items-center text-[11px] px-4 py-2.5 whitespace-nowrap"
                    style={{
                      gridTemplateColumns: "96px 48px 80px 64px 64px 64px 1fr",
                      gap: "12px",
                      borderTop: i === 0 ? "none" : "1px solid rgba(0,0,0,0.04)"
                    }}
                  >
                    <span className="tabular-nums" style={{ color: SUB }}>
                      {formatTime(e.triggered_at)}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <span
                        className="w-1.5 h-1.5 rounded-full"
                        style={{ background: e.level === "fullscreen_reminder" ? ACCENT : SOFT }}
                      />
                      <span style={{ color: TEXT }}>{e.level === "fullscreen_reminder" ? "强" : "轻"}</span>
                    </div>
                    <span className="truncate" style={{ color: MUTED }}>
                      {mapReasonLabel(e.trigger_reason ?? "unknown")}
                    </span>
                    <span className="tabular-nums text-right" style={{ color: SUB }}>
                      {e.idle_seconds ?? 0}s
                    </span>
                    <span style={{ color: MUTED }}>{e.media_state ?? "-"}</span>
                    <span style={{ color: MUTED }}>{mapReasonLabel(e.dismiss_reason ?? "pending")}</span>
                    <span className="truncate" style={{ color: MUTED }}>
                      {e.foreground_app ?? "-"}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
