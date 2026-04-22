import { useEffect, useMemo, useState } from "react";
import { BarChart3, ChevronDown, Minus, Plus, Save, Trash2 } from "lucide-react";

import {
  clearEvents,
  fetchConfig,
  saveConfig,
  type DismissMode,
  type FocusConfig
} from "@/api/client";

const BG = "#ECECEC";
const TEXT = "#3A3A3A";
const MUTED = "#A8A8A8";
const SUB = "#7A7A7A";
const SHADOW_OUT = "8px 8px 20px #c9cfd6, -8px -8px 20px #ffffff";
const SHADOW_OUT_SM = "3px 3px 8px #c9cfd6, -3px -3px 8px #ffffff";
const SHADOW_IN_SM = "inset 3px 3px 6px #c9cfd6, inset -3px -3px 6px #ffffff";

const defaultConfig: FocusConfig = {
  idle_threshold_seconds: 300,
  pre_reminder_seconds: 60,
  enable_pre_reminder: true,
  cooldown_seconds: 60,
  dismiss_mode: "activity",
  enable_history: true,
  monitor_enabled: true,
  poll_interval_ms: 1000,
  pre_reminder_message: "你已接近低专注状态，请尝试回到当前任务。",
  fullscreen_message: "请回到当前任务，重启专注状态。",
  fullscreen_topmost: true,
  fullscreen_overlay: true,
  start_minimized_to_tray: true
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
    <h2 className="text-[12px]" style={{ color: TEXT, fontWeight: 500 }}>
      {title}
    </h2>
    <Label>{hint}</Label>
  </div>
);

export function Settings({ onOpenStatistics }: { onOpenStatistics: () => void }) {
  const [config, setConfig] = useState<FocusConfig>(defaultConfig);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState("加载中...");

  const closeModes: Array<{ k: DismissMode; label: string }> = useMemo(
    () => [
      { k: "activity", label: "检测到输入即关闭" },
      { k: "manual", label: "手动关闭" }
    ],
    []
  );

  useEffect(() => {
    void loadConfig();
  }, []);

  async function loadConfig() {
    setLoading(true);
    try {
      const data = await fetchConfig();
      setConfig(data);
      setStatus("配置已加载");
    } catch (error) {
      setStatus(`加载失败：${(error as Error).message}`);
    } finally {
      setLoading(false);
    }
  }

  async function onSave() {
    setSaving(true);
    setStatus("保存中...");
    try {
      const saved = await saveConfig(config);
      setConfig(saved);
      setStatus("配置已保存");
    } catch (error) {
      setStatus(`保存失败：${(error as Error).message}`);
    } finally {
      setSaving(false);
    }
  }

  async function onClearEvents() {
    setStatus("清空历史中...");
    try {
      await clearEvents();
      setStatus("历史提醒已清空");
    } catch (error) {
      setStatus(`清空失败：${(error as Error).message}`);
    }
  }

  const NumField = ({
    label,
    value,
    onChange,
    suffix,
    step = 1
  }: {
    label: string;
    value: number;
    onChange: (v: number) => void;
    suffix: string;
    step?: number;
  }) => (
    <div className="flex flex-col gap-1.5">
      <Label>{label}</Label>
      <div
        className="flex items-center justify-between rounded-full px-1 py-1"
        style={{ background: BG, boxShadow: SHADOW_IN_SM }}
      >
        <button
          onClick={() => onChange(Math.max(0, value - step))}
          className="w-6 h-6 rounded-full flex items-center justify-center active:scale-95"
        >
          <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: BG, boxShadow: SHADOW_OUT_SM }}>
            <Minus className="w-2.5 h-2.5" style={{ color: SUB }} />
          </div>
        </button>
        <div className="flex items-baseline gap-1">
          <span className="text-[13px] tabular-nums" style={{ color: TEXT }}>
            {value}
          </span>
          <span className="text-[10px]" style={{ color: MUTED }}>
            {suffix}
          </span>
        </div>
        <button
          onClick={() => onChange(value + step)}
          className="w-6 h-6 rounded-full flex items-center justify-center active:scale-95"
        >
          <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: BG, boxShadow: SHADOW_OUT_SM }}>
            <Plus className="w-2.5 h-2.5" style={{ color: SUB }} />
          </div>
        </button>
      </div>
    </div>
  );

  const Toggle = ({
    checked,
    onChange,
    label
  }: {
    checked: boolean;
    onChange: (v: boolean) => void;
    label: string;
  }) => (
    <button onClick={() => onChange(!checked)} className="flex items-center justify-between w-full gap-3">
      <span className="text-[12px] whitespace-nowrap" style={{ color: TEXT }}>
        {label}
      </span>
      <div className="w-10 h-5 rounded-full relative" style={{ background: BG, boxShadow: SHADOW_IN_SM }}>
        <div
          className="w-4 h-4 rounded-full absolute top-[2px] transition-all duration-300"
          style={{
            left: checked ? "22px" : "2px",
            background: BG,
            boxShadow: "2px 2px 4px #c9cfd6, -1px -1px 3px #ffffff"
          }}
        >
          {checked ? (
            <div
              className="w-1 h-1 rounded-full absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
              style={{ background: TEXT }}
            />
          ) : null}
        </div>
      </div>
    </button>
  );

  const TextField = ({
    label,
    value,
    onChange
  }: {
    label: string;
    value: string;
    onChange: (v: string) => void;
  }) => (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-full px-4 py-2 text-[12px] outline-none"
        style={{ background: BG, boxShadow: SHADOW_IN_SM, color: SUB }}
      />
    </div>
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
      <div className="col-span-1 md:col-span-4">
        <Card className="px-5 py-5 h-full">
          <SectionTitle title="基础设置" hint="THRESHOLD" />
          <div className="grid grid-cols-2 gap-3">
            <NumField
              label="强提醒阈值"
              value={Math.round(config.idle_threshold_seconds / 60)}
              onChange={(v) =>
                setConfig((prev) => ({
                  ...prev,
                  idle_threshold_seconds: Math.max(1, v) * 60
                }))
              }
              suffix="分钟"
            />
            <NumField
              label="轻提醒提前"
              value={config.pre_reminder_seconds}
              onChange={(v) =>
                setConfig((prev) => ({
                  ...prev,
                  pre_reminder_seconds: Math.max(0, v)
                }))
              }
              suffix="秒"
              step={5}
            />
            <NumField
              label="冷却时间"
              value={config.cooldown_seconds}
              onChange={(v) =>
                setConfig((prev) => ({
                  ...prev,
                  cooldown_seconds: Math.max(0, v)
                }))
              }
              suffix="秒"
              step={5}
            />
            <NumField
              label="检查周期"
              value={config.poll_interval_ms}
              onChange={(v) =>
                setConfig((prev) => ({
                  ...prev,
                  poll_interval_ms: Math.max(250, v)
                }))
              }
              suffix="ms"
              step={100}
            />
          </div>
          <div className="mt-4 pt-4" style={{ borderTop: "1px solid rgba(0,0,0,0.04)" }}>
            <Toggle
              checked={config.enable_pre_reminder}
              onChange={(v) => setConfig((prev) => ({ ...prev, enable_pre_reminder: v }))}
              label="启用轻提醒"
            />
          </div>
        </Card>
      </div>

      <div className="col-span-1 md:col-span-2">
        <Card className="px-5 py-5 h-full flex flex-col">
          <SectionTitle title="数据与运行" hint="RUN" />
          <div className="flex-1 grid grid-rows-3 gap-0 items-center">
            <Toggle
              checked={config.monitor_enabled}
              onChange={(v) => setConfig((prev) => ({ ...prev, monitor_enabled: v }))}
              label="启动监控"
            />
            <Toggle
              checked={config.start_minimized_to_tray}
              onChange={(v) => setConfig((prev) => ({ ...prev, start_minimized_to_tray: v }))}
              label="最小化到托盘"
            />
            <Toggle
              checked={config.enable_history}
              onChange={(v) => setConfig((prev) => ({ ...prev, enable_history: v }))}
              label="记录提醒历史"
            />
          </div>
        </Card>
      </div>

      <div className="col-span-1 md:col-span-3">
        <Card className="px-5 py-5 h-full">
          <SectionTitle title="提醒行为" hint="ALERT" />
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label>强提醒关闭方式</Label>
              <div className="rounded-full px-4 py-2 flex items-center justify-between" style={{ background: BG, boxShadow: SHADOW_IN_SM }}>
                <select
                  value={config.dismiss_mode}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      dismiss_mode: e.target.value as DismissMode
                    }))
                  }
                  className="bg-transparent text-[12px] outline-none flex-1 appearance-none cursor-pointer"
                  style={{ color: TEXT }}
                >
                  {closeModes.map((m) => (
                    <option key={m.k} value={m.k}>
                      {m.label}
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-3 h-3" style={{ color: MUTED }} />
              </div>
            </div>
            <Toggle
              checked={config.fullscreen_topmost}
              onChange={(v) => setConfig((prev) => ({ ...prev, fullscreen_topmost: v }))}
              label="强提醒置顶"
            />
            <Toggle
              checked={config.fullscreen_overlay}
              onChange={(v) => setConfig((prev) => ({ ...prev, fullscreen_overlay: v }))}
              label="强提醒全屏遮罩"
            />
          </div>
        </Card>
      </div>

      <div className="col-span-1 md:col-span-3">
        <Card className="px-5 py-5 h-full">
          <SectionTitle title="提醒文案" hint="COPY" />
          <div className="space-y-3">
            <TextField
              label="轻提醒文案"
              value={config.pre_reminder_message}
              onChange={(v) => setConfig((prev) => ({ ...prev, pre_reminder_message: v }))}
            />
            <TextField
              label="强提醒文案"
              value={config.fullscreen_message}
              onChange={(v) => setConfig((prev) => ({ ...prev, fullscreen_message: v }))}
            />
          </div>
        </Card>
      </div>

      <div className="col-span-1 md:col-span-6 flex items-center gap-2 sm:gap-3 flex-wrap">
        <div className="flex items-center gap-2 px-2 shrink-0">
          <div className="w-1.5 h-1.5 rounded-full" style={{ background: loading ? MUTED : TEXT }} />
          <span className="text-[10px] tracking-[0.2em] uppercase" style={{ color: MUTED }}>
            {status}
          </span>
        </div>
        <button
          onClick={onSave}
          disabled={loading || saving}
          className="ml-auto flex items-center justify-center gap-2 px-5 py-3 rounded-full active:scale-[0.99] transition-all shrink-0 disabled:opacity-60"
          style={{ background: BG, boxShadow: SHADOW_OUT, color: TEXT }}
        >
          <Save className="w-3.5 h-3.5" />
          <span className="text-[12px]">{saving ? "保存中..." : "保存配置"}</span>
        </button>
        <button
          onClick={onOpenStatistics}
          className="w-11 h-11 rounded-full flex items-center justify-center active:scale-95 transition-transform shrink-0"
          style={{ background: BG, boxShadow: SHADOW_OUT_SM }}
          title="查看统计"
        >
          <BarChart3 className="w-3.5 h-3.5" style={{ color: SUB }} />
        </button>
        <button
          onClick={onClearEvents}
          className="w-11 h-11 rounded-full flex items-center justify-center active:scale-95 transition-transform shrink-0"
          style={{ background: BG, boxShadow: SHADOW_OUT_SM }}
          title="清空历史"
        >
          <Trash2 className="w-3.5 h-3.5" style={{ color: SUB }} />
        </button>
      </div>
    </div>
  );
}
