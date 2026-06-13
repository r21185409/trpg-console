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
