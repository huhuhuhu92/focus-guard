# Focus Reminder Frontend Prototype

## Run

```bash
npm install
npm run dev
```

默认会请求 `http://127.0.0.1:8787` 的本地 API。
启动 API：

```powershell
cd ..
.\scripts\run_focus_api.ps1
```

如果你要改 API 地址，可在 `frontend` 下创建 `.env`：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8787
```

## Build

```bash
npm run build
npm run preview
```
