# TRPG Console

Web DM 控制台 — 在 `D:\TRPG\base` 的 claude-dnd-skill 之上加一層瀏覽器介面。

## 啟動

```powershell
D:\TRPG\console\run.ps1
```

第一次執行會建立 venv 並安裝依賴；之後直接啟動。瀏覽器開 <http://127.0.0.1:8765>。

## 階段進度

- ✅ Stage 1：骨架（venv、Flask 後端、基礎前端、戰役列表 API）
- ⬜ Stage 2：瀏覽器 ↔ Claude Code 指令通道
- ⬜ Stage 3：戰役/NPC/地點瀏覽器
- ⬜ Stage 4：拖拉上傳 PDF/MD/DOCX
- ⬜ Stage 5：戰鬥控制台
- ⬜ Stage 6：地圖 + 事件時間軸

## 架構原則

- `base/` 永遠保持乾淨；所有客製都在 `console/` 內
- 戰役資料寫入 `D:\TRPG\campaigns\`（由 `DND_CAMPAIGN_ROOT` 環境變數指定）
- 後端用 Flask，前端純 HTML/JS（無建置步驟，疊代成本低）
