# Focus Reminder 前端对接文档（交付版）

更新时间：2026-04-21  
适用版本：当前仓库 `D:\Career\Project\alert`

## 1. 目标与范围

这份文档用于你和前端开发同学对齐当前项目的：

- 已有前端结构（桌面前端 + Web 前端原型）
- 已实现接口（HTTP API + 桌面 UI 信号）
- 数据字段契约（配置、统计、事件）
- 本地联调与验收方式

## 2. 当前“前端”有两套实现

### 2.1 桌面前端（当前主线）

技术：`PySide6`  
运行入口：`.\scripts\run_focus_reminder.ps1`  
用途：真正随程序打包到 exe 的桌面 UI

关键文件：

- `focus_reminder/presentation/windows/settings_window.py`
- `focus_reminder/presentation/windows/stats_window.py`
- `focus_reminder/presentation/windows/pre_reminder_popup.py`
- `focus_reminder/presentation/windows/fullscreen_popup.py`
- `focus_reminder/presentation/presenters/notification_presenter.py`
- `focus_reminder/presentation/presenters/fullscreen_presenter.py`
- `focus_reminder/presentation/tray/tray_controller.py`
- `focus_reminder/app/bootstrap.py`（窗口与业务绑定）

### 2.2 Web 前端（原型/联调用）

技术：`React + Vite + TypeScript + Tailwind + Recharts`  
运行入口：`cd frontend && npm run dev`  
用途：用于快速还原高保真样式与接口联调，不是当前桌面主运行入口

关键文件：

- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/components/Settings.tsx`
- `frontend/src/components/Statistics.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/styles/index.css`
- `frontend/vite.config.ts`
- `frontend/.env.example`

## 3. 前端目录结构（可直接给前端）

```text
focus_reminder/
  presentation/
    windows/
      settings_window.py        # 设置页（桌面）
      stats_window.py           # 统计页（桌面）
      pre_reminder_popup.py     # 轻提醒弹窗
      fullscreen_popup.py       # 强提醒全屏弹窗
    presenters/
      notification_presenter.py
      fullscreen_presenter.py
    tray/
      tray_controller.py
frontend/
  src/
    api/
      client.ts                 # Web 请求封装与 TS 类型
    components/
      Settings.tsx              # Web 设置页
      Statistics.tsx            # Web 统计页
    App.tsx                     # Tab 切换
    main.tsx                    # 挂载入口
    styles/
      index.css
      theme.css
      tailwind.css
      fonts.css
```

## 4. 当前可用接口总览

## 4.1 HTTP API（给 Web 前端）

服务文件：`focus_reminder/api/server.py`  
启动方式：`.\scripts\run_focus_api.ps1`  
默认地址：`http://127.0.0.1:8787`

### 4.1.1 GET `/api/health`

响应：

```json
{
  "ok": true,
  "service": "focus-reminder-api"
}
```

### 4.1.2 GET `/api/config`

响应：

```json
{
  "config": {
    "idle_threshold_seconds": 300,
    "pre_reminder_seconds": 60,
    "enable_pre_reminder": true,
    "cooldown_seconds": 60,
    "dismiss_mode": "activity",
    "enable_history": true,
    "monitor_enabled": true,
    "poll_interval_ms": 1000,
    "pre_reminder_message": "你已接近低专注状态，请尝试回到当前任务。",
    "fullscreen_message": "请回到当前任务，重启专注状态。",
    "fullscreen_topmost": true,
    "fullscreen_overlay": true,
    "start_minimized_to_tray": true
  }
}
```

### 4.1.3 PUT `/api/config`

请求体支持两种：

1. `{ "config": { ...FocusConfig } }`
2. 直接 `{ ...FocusConfig }`

响应：

```json
{
  "config": { "...": "保存后（已sanitized）的配置" }
}
```

### 4.1.4 GET `/api/dashboard?days=7&event_limit=100`

查询参数：

- `days`: 1~30（默认 7）
- `event_limit`: 1~500（默认 100）

响应结构：

```json
{
  "today_count": 2,
  "period_days": 7,
  "period_count": 5,
  "trend": [{ "date": "04-21", "count": 2 }],
  "hourly": [{ "hour": "15", "count": 1 }],
  "level_distribution": [{ "key": "pre_reminder", "count": 3 }],
  "trigger_reason_distribution": [{ "key": "idle_reached_pre_threshold", "count": 3 }],
  "dismiss_reason_distribution": [{ "key": "activity", "count": 2 }],
  "events": [{ "...": "最近事件行" }]
}
```

### 4.1.5 GET `/api/events?limit=100`

响应：

```json
{
  "events": [{ "...": "最近事件行" }]
}
```

### 4.1.6 DELETE `/api/events`

响应：

```json
{
  "ok": true
}
```

## 4.2 桌面 UI 信号接口（给桌面前端/Qt开发）

`settings_window.py`：

- `config_saved(FocusConfig)`：点击“保存配置”后发出
- `clear_history_requested()`：点击“清空历史”后发出
- `open_stats_requested()`：点击“查看统计/切换统计tab”后发出

`stats_window.py`：

- `open_settings_requested()`：点击“设置tab”后发出

绑定位置：`focus_reminder/app/bootstrap.py`

- `settings.open_stats_requested -> show_stats_window`
- `stats.open_settings_requested -> show_settings_window`
- `settings.config_saved -> _on_config_saved`
- `settings.clear_history_requested -> _on_clear_history`

## 5. 数据字段契约（前端必须对齐）

## 5.1 FocusConfig

来源：`focus_reminder/domain/models/config.py`，Web 类型同构于 `frontend/src/api/client.ts`

字段：

- `idle_threshold_seconds: number`
- `pre_reminder_seconds: number`
- `enable_pre_reminder: boolean`
- `cooldown_seconds: number`
- `dismiss_mode: "activity" | "manual"`
- `enable_history: boolean`
- `monitor_enabled: boolean`
- `poll_interval_ms: number`
- `pre_reminder_message: string`
- `fullscreen_message: string`
- `fullscreen_topmost: boolean`
- `fullscreen_overlay: boolean`
- `start_minimized_to_tray: boolean`

## 5.2 事件行（dashboard.events / /api/events）

实际字段（由 SQLite 查询返回）：

- `id`
- `level`：`pre_reminder` | `fullscreen_reminder`
- `triggered_at`：ISO 时间字符串
- `idle_seconds`
- `media_state`：`none` | `audio_only` | `video_playing` | `unknown`
- `dismiss_mode`：`activity` | `manual`
- `trigger_reason`
- `dismiss_reason`
- `popup_duration_ms`
- `foreground_app`
- `foreground_title`

## 5.3 枚举建议映射（前端展示）

- `level`
  - `pre_reminder` -> `轻`
  - `fullscreen_reminder` -> `强`
- `trigger_reason`
  - `idle_reached_pre_threshold` -> `达到轻提醒阈值`
  - `idle_reached_fullscreen_threshold` -> `达到强提醒阈值`
  - `cooldown_pre_reminder` -> `冷却期轻提醒`
  - `unknown` -> `未知`
- `dismiss_reason`
  - `activity` -> `输入关闭`
  - `manual` -> `手动关闭`
  - `pending` -> `待关闭`
  - `auto` -> `自动关闭`

## 6. 前端联调启动步骤

## 6.1 桌面端联调（主线）

```powershell
cd D:\Career\Project\alert
.\scripts\run_focus_reminder.ps1
```

## 6.2 Web 前端联调（可选）

终端1启动 API：

```powershell
cd D:\Career\Project\alert
.\scripts\run_focus_api.ps1
```

终端2启动前端：

```powershell
cd D:\Career\Project\alert\frontend
npm install
npm run dev
```

默认 API 地址：`http://127.0.0.1:8787`  
如需修改，在 `frontend/.env` 写：

```env
VITE_API_BASE_URL=http://127.0.0.1:8787
```

## 7. 联调验收清单（给前端）

- 设置页打开后可成功拉取配置（`GET /api/config`）
- 修改任意配置并保存后，刷新仍保持（`PUT /api/config`）
- 统计页可显示今日次数、近7天趋势、24小时柱图、等级占比
- 清空历史后，统计和事件表同步清空（`DELETE /api/events`）
- 错误场景可见提示（接口 4xx/5xx）
- 枚举文案显示与上文映射一致

## 8. 当前已知边界（避免沟通歧义）

- 当前打包运行主入口是桌面前端，不是 Web 前端。
- `run_focus_api.ps1` 只启动 API，不会弹桌面 UI。
- Web 前端现在是可运行原型，便于样式迭代与接口联调；要进生产桌面需回写到 PySide6 组件。
- 接口暂未做鉴权，默认本机回环地址使用。

## 9. 建议前端协作方式

- 如果目标是“最终 exe 里的界面”：前端给出设计 token（字号、间距、阴影、圆角、状态色），由 Qt 实现对齐。
- 如果目标是“先快速迭代视觉”：先在 `frontend/` 出视觉定稿，再按本文字段契约迁移到桌面端。
