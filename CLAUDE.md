# TRPG Web Console — 專案規則

## 語言

**所有對使用者的回應、DM 敘述、NPC 對話、戰鬥描述、規則裁定、場景描寫，預設一律使用繁體中文（台灣用語）。**

只有以下情況例外，可保留英文原文：
- 角色卡欄位名稱（如 `STR`, `DEX`, `AC`, `HP`）
- 法術 / 物品 / 怪物的官方英文名（首次出現時加註中文翻譯，例如 "Magic Missile（魔法飛彈）"）
- 程式碼、檔案路徑、指令列輸出
- skill 內建的選單選項標籤（這部分由 skill 原始碼控制，不強制翻譯）

使用者若以英文提問，仍以繁體中文回應，除非使用者明確要求改用英文。

## 專案結構

- `base\` — 上游 `claude-dnd-skill` 原始碼，**保持乾淨，禁止修改**（之後可 `git pull` 升級）
- `campaigns\` — 戰役資料（由 `DND_CAMPAIGN_ROOT` 指向）
- `console\` — 我們的 web 控制台中間層（建置中）
- `.claude\skills\dnd\` — junction 指向 `base\skills\dnd\`，讓 Claude Code 自動發現 skill

## 修改 skill 行為的方式

不直接編輯 `base\` 內檔案。需要客製 skill 行為時，透過：
1. 本檔（CLAUDE.md）的專案層級指令
2. `.claude\settings.local.json` 的 env 變數（例如 `DND_CAMPAIGN_ROOT`）
3. `console\` 中間層攔截或包裝
