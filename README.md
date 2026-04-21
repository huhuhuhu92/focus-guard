# Focus Reminder Desktop V1.3

专注提醒工具的第三版：在 V1.2 基础上增强媒体识别能力（视频豁免、音频不豁免）。

## 功能覆盖

- 全局输入监听（键盘/鼠标）
- 两级提醒（轻提醒 + 强提醒）
- 强提醒关闭策略（活动关闭 / 手动关闭）
- 配置持久化（JSON）
- 历史事件落库（SQLite）
- 托盘运行与暂停/恢复
- 统计窗口（折线图/柱状图/饼图 + 事件列表）
- 触发原因记录与分类统计
- 基础媒体识别（启发式策略：前台进程 + 标题关键字）
- 视频播放豁免提醒、音频播放不豁免提醒

## 目录结构

```text
focus_reminder/
├─ app/
├─ domain/
├─ infrastructure/
├─ presentation/
├─ resources/
└─ data/
tests/
requirements.txt
```

## 快速启动

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m focus_reminder.app.main
```

如果你使用已验证环境 `my_project_py311`，可直接运行：

```powershell
.\scripts\run_focus_reminder.ps1
```

## 自动化验收

```powershell
.\scripts\acceptance.ps1
```

可选参数：

```powershell
.\scripts\acceptance.ps1 -RunGuiSmoke
.\scripts\acceptance.ps1 -RunPackaging
```

## 打包为 EXE

```bash
pyinstaller focus_reminder/infrastructure/packaging/pyinstaller.spec
```

## 默认规则

- 强提醒阈值：5 分钟
- 轻提醒提前：60 秒
- 轻提醒：开启
- 强提醒关闭方式：检测到输入即关闭
- 冷却时间：60 秒
- 历史记录：开启
