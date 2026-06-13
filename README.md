# TRPG 控制台

在 [`neuralinitiative/claude-dnd-skill`](https://github.com/neuralinitiative/claude-dnd-skill) 之上加一層瀏覽器 DM 控制台。

## 架構

```
D:\TRPG\
├── base\                    上游 skill 的乾淨 clone（git submodule 風格，獨立 .git）
├── campaigns\               戰役資料（state.md, npcs.md, world.md, session-log.md...）
├── console\                 我們的擴充層
│   ├── server\              Flask 後端 + Claude Code CLI 橋接
│   ├── web\                 純 HTML/JS 前端
│   ├── requirements.txt
│   └── run.ps1              啟動腳本
├── .claude\
│   ├── settings.local.json  專案設定（DND_CAMPAIGN_ROOT、權限）
│   └── skills\dnd\          junction → base\skills\dnd\
├── CLAUDE.md                專案規則（語言、修改 skill 的方式）
└── README.md
```

## 啟動

```powershell
D:\TRPG\console\run.ps1
```

瀏覽器開 <http://127.0.0.1:8765>。

## 階段進度

- [x] Stage 0 — Clone 上游 skill 到 `base\`
- [x] Stage 1 — Console 骨架（venv、Flask、前端基底）
- [x] Stage 2 — 瀏覽器 ↔ Claude Code CLI 雙向橋接（SSE 串流、AskUserQuestion 卡片、markdown 渲染）
- [ ] Stage 3 — 戰役 / NPC / 地點瀏覽器
- [ ] Stage 4 — 拖拉上傳 PDF / MD / DOCX
- [ ] Stage 5 — 戰鬥控制台
- [ ] Stage 6 — 地圖 + 事件時間軸

## 依賴

- Python 3.10+（內含 venv）
- Node.js 18+
- Claude Code CLI（`npm i -g @anthropic-ai/claude-code`）
- 已登入的 Anthropic 帳號

## 換機器 / 災難復原

```powershell
# 1. clone 本 repo
gh repo clone r21185409/trpg-console D:\TRPG
cd D:\TRPG

# 2. clone 上游 skill（base/ 不在本 repo 內）
git clone https://github.com/neuralinitiative/claude-dnd-skill.git base

# 3. 重建 skill junction（讓 Claude Code 找得到 dnd skill）
New-Item -ItemType Junction -Path .claude\skills\dnd -Target D:\TRPG\base\skills\dnd

# 4. 建立 .claude\settings.local.json
@'
{
  "env": { "DND_CAMPAIGN_ROOT": "D:\\TRPG\\campaigns" },
  "permissions": { "defaultMode": "bypassPermissions" }
}
'@ | Set-Content -Encoding UTF8 .claude\settings.local.json

# 5. 啟動（首次會自動建 venv 安裝依賴）
.\console\run.ps1
```

瀏覽器開 <http://127.0.0.1:8765>。

**戰役資料不在 git** — 從你自己的備份還原到 `D:\TRPG\campaigns\`。
